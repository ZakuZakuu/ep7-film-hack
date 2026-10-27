"""Owned loopback HTTP integration tests. Never connect to a camera."""
from contextlib import redirect_stdout,redirect_stderr
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch

from tools.ep7_wifi.client import (Camera,Transfer,ClientError,Incompatible,Uncertain,
                                  fields,vector,as_recipe,checked_recipe,load_recipe)
from tools.ep7_wifi.simulator import Model,serve
from tools.ep7_wifi.__main__ import main
from tools.recipe_studio.recipe import neutral


class Loopback(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.directory=Path(self.temp.name)
        self.servers=[]

    def tearDown(self):
        for server,thread in self.servers:
            server.shutdown();server.server_close();thread.join(timeout=2)
        self.temp.cleanup()

    def camera(self,state=None,**kwargs):
        state=state or Model();server=serve(state)
        thread=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':.01},daemon=True)
        thread.start();self.servers.append((server,thread))
        return Camera('127.0.0.1',server.server_port,gap=0,**kwargs),state

    def recipe(self):
        r=neutral('Owned synthetic recipe')
        r['settings'].update(hue=[1,2,3,4,5,6,7,-7,-6,-5,-4,-3],
                             saturation=[-5,-4,-3,-2,-1,0,1,2,3,4,5,0],
                             lightness=[7,6,5,4,3,2,1,0,-1,-2,-3,-4],
                             tone={'shadows':-2,'midtones':1,'highlights':3},shading=-3)
        r['recommendations']={'white_balance':'日光','wb_shift':'A +2','exposure_compensation':'−0.3 EV'}
        return r

    def test_complete_write_binding_readback_and_restore(self):
        camera,state=self.camera();transfer=Transfer(camera,self.directory/'private')
        r=self.recipe();report=transfer.write(4,r)
        self.assertEqual(report['status'],'verified_current_values')
        self.assertEqual(vector(camera.read(4)),vector(r))
        # Independent physical-key expectations, rather than sharing the client
        # field order with the simulator, catch sector and high/low swaps.
        self.assertEqual(state.values[('h',1661)],2)  # COLOR4 wheel orange -> physical6.
        self.assertEqual(state.values[('s',1670)],-3)
        self.assertEqual(state.values[('s',1667)],0)
        self.assertEqual(state.values[('s',1674)],-2)  # Shadow source key, COLOR4.
        self.assertEqual(state.values[('s',1672)],3)   # Highlight source key.
        backup=load_recipe(report['backup']);self.assertEqual(vector(backup),[0]*40)
        restored=transfer.write(4,backup,restore=True)
        self.assertEqual(restored['operation'],'restore')
        self.assertEqual(vector(camera.read(4)),[0]*40)
        self.assertTrue(Path(restored['backup']).exists())
        self.assertFalse(transfer.marker.exists())
        self.assertFalse(any('white_balance' in str(q) or 'wb_shift' in str(q) for _,q in state.requests))

    def test_other_three_slots_unchanged(self):
        camera,state=self.camera();Transfer(camera,self.directory/'p').write(2,self.recipe())
        for slot in (1,3,4):self.assertEqual(vector(camera.read(slot)),[0]*40)

    def test_stock_and_wrong_version_refuse_before_rec_or_write(self):
        camera,state=self.camera(Model(stock=True))
        with self.assertRaises(Incompatible):Transfer(camera,self.directory/'p').write(1,self.recipe())
        self.assertEqual(state.writes,0)
        self.assertEqual([p for p,_ in state.requests],['/get_caminfo.cgi','/switch_cammode.cgi','/get_mcon.cgi'])
        with patch.object(camera,'get_number',return_value=0x45503732):
            with self.assertRaises(Incompatible):camera.discover()

    def test_wrong_model_refused(self):
        camera,state=self.camera(Model(model='E-M10'))
        with self.assertRaises(Incompatible):camera.discover()
        self.assertEqual(len(state.requests),1)

    def test_invalid_recipe_before_transport_construction(self):
        bad=self.recipe();bad['settings']['saturation'][0]=6
        source=self.directory/'bad.json';source.write_text(json.dumps(bad))
        with patch('tools.ep7_wifi.__main__.Camera') as network,redirect_stderr(io.StringIO()):
            self.assertEqual(main(['write','--slot','1',str(source)]),2)
            network.assert_not_called()
        for value in (True,1.5):
            r=self.recipe();r['settings']['hue'][0]=value
            with self.assertRaises(ValueError):checked_recipe(r)
        source.write_text('{"format":"a","format":"b"}')
        with self.assertRaises(ClientError):load_recipe(source)

    def test_dry_run_write_and_restore_do_not_connect_or_create_state(self):
        source=self.directory/'recipe.json';source.write_text(json.dumps(self.recipe()))
        for command in ('write','restore'):
            out=io.StringIO()
            with patch('tools.ep7_wifi.client.http.client.HTTPConnection') as socket,redirect_stdout(out):
                self.assertEqual(main(['--state-dir',str(self.directory/'p'),command,'--slot','3',str(source),'--dry-run']),0)
                socket.assert_not_called()
            result=json.loads(out.getvalue());self.assertEqual(result['operation'],command)
            self.assertFalse(result['network_used']);self.assertEqual(len(result['values']),40)
            self.assertFalse((self.directory/'p').exists())

    def test_drop_after_applied_scalar_no_retry_and_persistent_interlock(self):
        camera,state=self.camera(Model(drop_at=3));transfer=Transfer(camera,self.directory/'p')
        with self.assertRaises(Uncertain) as caught:transfer.write(1,self.recipe())
        report=caught.exception.report
        self.assertEqual(state.writes,3);self.assertEqual(report['completed_replies'],2)
        self.assertEqual(report['readback'],'complete')
        self.assertEqual(report['actual_values'][:4],[1,2,3,0])
        self.assertTrue(transfer.marker.exists());self.assertTrue(Path(report['backup']).exists())
        with self.assertRaises(ClientError):Transfer(camera,self.directory/'p').write(1,self.recipe())
        self.assertEqual(state.writes,3)
        with self.assertRaises(ClientError):transfer.reconcile(False)
        result=transfer.reconcile(True)
        self.assertEqual(result['writes_sent'],0);self.assertFalse(result['matches_previous_target'])
        self.assertFalse(transfer.marker.exists());self.assertEqual(state.writes,3)

    def test_response_timeout_stops_and_keeps_uncertainty(self):
        camera,state=self.camera(Model(delay_at=1,delay=.08),timeout=.02)
        transfer=Transfer(camera,self.directory/'p')
        with self.assertRaises(Uncertain):transfer.write(1,self.recipe())
        self.assertEqual(state.writes,1);self.assertTrue(transfer.marker.exists())

    def test_mismatch_never_automatically_rolls_back(self):
        camera,state=self.camera(Model(mismatch_at=1));transfer=Transfer(camera,self.directory/'p')
        with self.assertRaises(Uncertain) as caught:transfer.write(1,self.recipe())
        self.assertNotEqual(caught.exception.report['actual_values'],vector(self.recipe()))
        marked=[q for p,q in state.requests if p=='/set_mcon.cgi']
        self.assertEqual(len(marked),len({q['mode']+q['value'] for q in marked}))
        self.assertTrue(transfer.marker.exists())

    def test_no_changes_still_backs_up_and_verifies_without_writes(self):
        camera,state=self.camera();result=Transfer(camera,self.directory/'p').write(1,neutral())
        self.assertEqual(result['written_values'],0);self.assertEqual(state.writes,0)
        self.assertTrue(Path(result['backup']).exists())

    def test_read_cli_exports_strict_recipe_and_discover_is_read_only(self):
        camera,state=self.camera();args=['--host','127.0.0.1','--port',str(camera.port),'--gap','0']
        out=io.StringIO()
        with redirect_stdout(out):self.assertEqual(main(args+['discover']),0)
        self.assertTrue(state.rec);self.assertEqual(state.writes,0)
        target=self.directory/'read.json'
        with redirect_stdout(io.StringIO()):self.assertEqual(main(args+['read','--slot','1','--out',str(target)]),0)
        self.assertEqual(vector(load_recipe(target)),[0]*40)
        self.assertTrue(load_recipe(target)['name'].startswith('COLOR 1 backup '))
        self.assertEqual(state.writes,0)

    def test_get_mcon_requires_rec_mode_like_the_real_camera(self):
        camera,state=self.camera()
        with self.assertRaises(ClientError) as ctx:camera.get_number(65535)
        self.assertIn('520',str(ctx.exception));self.assertIn('遥控模式',str(ctx.exception))
        self.assertEqual(camera.discover()['protocol'],'EP71');self.assertTrue(state.rec)

    def test_no_public_or_dns_targets_and_no_redirect_following(self):
        for host in ('8.8.8.8','example.com','169.254.169.254','0.0.0.0','224.0.0.1','192.168.1.1.example.com','::','2001:4860:4860::8888'):
            with self.assertRaises(ClientError):Camera(host)
        for host in ('192.168.0.10','10.0.0.2','172.16.2.3','127.0.0.1','::1'):Camera(host)
        camera,_=self.camera()
        response=unittest.mock.Mock(status=302);response.read.return_value=b''
        connection=unittest.mock.MagicMock();connection.getresponse.return_value=response
        with patch('tools.ep7_wifi.client.http.client.HTTPConnection',return_value=connection):
            with self.assertRaises(ClientError):camera.request('/get_caminfo.cgi')
        self.assertEqual(connection.request.call_count,1)

    def test_reject_sentinel_malformed_xml_and_ignore_identity_fields(self):
        camera,_=self.camera()
        with patch.object(camera,'get_number',return_value=0x80000000):
            with self.assertRaises(ClientError):camera.read(1)
        for body in (b'<!DOCTYPE response [<!ENTITY x "v">]><response><value>&x;</value></response>',
                     b'<response><value>0</value><value>1</value></response>',
                     b'<response><value>0</value><other>ignored</other></response>',
                     b'<response>\0<value>0</value></response>',b'garbage'):
            with self.assertRaises(ClientError):Camera.xml(body,'response','value')
        body=b'<caminfo><model>E-P7</model><serial>owned-private-metadata</serial><mac>owned-private-metadata</mac></caminfo>'
        with patch.object(camera,'request',side_effect=[body,b'',b'<response><value>45503731</value></response>']):
            self.assertEqual(camera.discover(),{'model':'E-P7','protocol':'EP71','slots':4})

    def test_lock_and_backup_failure_prevent_marked_write(self):
        camera,state=self.camera();directory=self.directory/'p';directory.mkdir()
        (directory/'write.lock').write_text('owned fixture')
        with self.assertRaises(ClientError):Transfer(camera,directory).write(1,self.recipe())
        self.assertFalse(state.requests)
        (directory/'write.lock').unlink()
        with patch('tools.ep7_wifi.client.save_new',side_effect=OSError('owned storage failure')):
            with self.assertRaises(OSError):Transfer(camera,directory).write(1,self.recipe())
        self.assertEqual(state.writes,0)

    def test_real_module_cli_write_and_restore_utf8(self):
        camera,state=self.camera();recipe=self.recipe();recipe['name']='自有合成配方'
        source=self.directory/'owned-recipe.json';source.write_text(json.dumps(recipe,ensure_ascii=False),encoding='utf-8')
        base=[sys.executable,'-m','tools.ep7_wifi','--host','127.0.0.1','--port',str(camera.port),
              '--gap','0','--state-dir',str(self.directory/'private')]
        result=subprocess.run(base+['write','--slot','3',str(source)],capture_output=True,encoding='utf-8',timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)
        report=json.loads(result.stdout);self.assertEqual(report['recommendations_manual_only'],recipe['recommendations'])
        restored=subprocess.run(base+['restore','--slot','3',report['backup']],capture_output=True,encoding='utf-8',timeout=20)
        self.assertEqual(restored.returncode,0,restored.stderr)
        self.assertEqual(json.loads(restored.stdout)['operation'],'restore')
        self.assertEqual(vector(camera.read(3)),[0]*40)

    def test_corrupt_uncertainty_state_is_retained_without_network(self):
        camera,state=self.camera();transfer=Transfer(camera,self.directory/'p')
        transfer.directory.mkdir();transfer.marker.write_text('{\"host\": \"127.0.0.1\"}')
        with self.assertRaises(ClientError):transfer.reconcile(True)
        self.assertTrue(transfer.marker.exists());self.assertFalse(state.requests)

    def test_mock_rejects_invalid_tag_and_axis_without_mutation(self):
        camera,state=self.camera();camera.request('/switch_cammode.cgi',{'mode':'rec'})
        before=deepcopy(state.values)
        for key,value in [('039F','45530000'),('039F','45510008'),('03C3','45510001')]:
            with self.assertRaises(ClientError):camera.request('/set_mcon.cgi',{'mode':key,'value':value})
        self.assertEqual(before,state.values);self.assertEqual(state.writes,0)


if __name__=='__main__':unittest.main()

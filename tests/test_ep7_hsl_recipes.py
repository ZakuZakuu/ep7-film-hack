"""Owned inputs only: v4 guards and actual original extension on GNU sim."""
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from ep7_color_min import Experiment,SP,STACK,digest
PATCH=ROOT/'patches/hsl-recipes/e-p7'
TOOLS=ROOT/'work/upstream/oly_fw_analysis/toolchains/mn103-patch-build'
ENGINE=ROOT/'work/upstream/oly_fw_analysis/toolchains/mn103-gnu-build/penf-mn103'
spec=importlib.util.spec_from_file_location('v4_builder',PATCH/'build.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)


class V4BuildGuards(unittest.TestCase):
    def test_invalid_stock_never_creates_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            stock=Path(tmp)/'owned.bin';stock.write_bytes(b'owned invalid stock')
            out=Path(tmp)/'must-not-exist'
            with self.assertRaisesRegex(ValueError,'Exact E-P7'):
                builder.build(SimpleNamespace(stock=stock,verify_only=False,out=out))
            self.assertFalse(out.exists())

    def test_legacy_manifests_and_source_identity(self):
        m=json.loads((PATCH/'patch.json').read_text())
        self.assertEqual(digest((PATCH/'hook.s').read_bytes()),m['hook_source_sha256'])
        self.assertEqual(json.loads((PATCH/'symbols.json').read_text()),m['symbols'])
        for label,path in [('T20','hsl-min'),('v2','hsl-profiles'),('v3','hsl-profiles-preview')]:
            old=json.loads((ROOT/'patches'/path/'e-p7/patch.json').read_text())
            self.assertEqual(old['output_sha256'],m['preserved_versions'][label])
        self.assertGreaterEqual(m['placement']['code_to_mirror_margin'],64)
        self.assertGreaterEqual(m['placement']['mirror_suffix_margin'],64)


@unittest.skipUnless((TOOLS/'gas/as-new').exists() and ENGINE.exists(), 'Separately obtained qualified GNU toolchain required')
class OwnedExtensionContracts(unittest.TestCase):
    def test_capability_read_and_invalid_writes_have_no_native_fallback(self):
        sys.path.insert(0,str(ROOT/'work/upstream/oly_fw_analysis/tools'))
        import penf_emulator as p
        with tempfile.TemporaryDirectory(dir='/tmp') as tmp:
            x=object.__new__(Experiment);x.out=Path(tmp);x.tools=TOOLS;x.instructions={}
            symbols=json.loads((PATCH/'symbols.json').read_text())
            m=json.loads((PATCH/'patch.json').read_text())
            base=int(m['placement']['code_start'],0)
            code=x.assemble('own_v4',(PATCH/'hook.s').read_text(),base,symbols)
            record=next(v for v in m['modified_ranges'] if v['kind']=='extension')
            self.assertEqual(digest(code),record['replacement_sha256'])
            entries={k:int(v,0) for k,v in m['entrypoints'].items()}
            mirror=bytearray(192);struct.pack_into('<2h',mirror,0,-3,2)
            regions=[p.Region('extension',base,code,'rx'),p.Region('mirror',symbols['ep7_mirror'],bytes(mirror)),
                     p.Region('stack',STACK,bytes(0x2000),'rw',True)]
            for key,expected in [(65535,0x45503731),(0x8000|927,0xfffffffd),(0xc000|927,2),
                                 (0x8000|910,0x80000000),(0x4000|927,0x80000000)]:
                caller=x.assemble('read_caller','call target,[],4\nnop\n',symbols={'target':entries['wifi_read']})
                v=p.execute([*regions,p.Region('caller',0x18020000,caller,'rx')],
                            {'pc':0x18020000,'sp':SP,'d0':key},0x18020000+len(caller),limit=500,trace_limit=500)
                self.assertEqual(v['status'],'returned',v.get('fault'))
                self.assertEqual(v['registers']['d0'],expected)
                self.assertEqual(v['registers']['sp'],SP)
            # Native raw setter, post service and pending record are deliberately
            # inaccessible: rejection must precede any attempt to use them.
            for key,word in [(927,0x45530000),(927,0x45510008),(926,0x45510000),
                             (963,0x45510001),(0x1039f,0x45510003)]:
                caller=x.assemble('write_caller','call target,[d2,d3],12\nnop\n',symbols={'target':entries['wifi_write']})
                v=p.execute([*regions,p.Region('caller',0x18020000,caller,'rx')],
                            {'pc':0x18020000,'sp':SP,'d0':key&65535,'a2':key,'d1':word},
                            0x18020000+len(caller),limit=1000,trace_limit=1000)
                self.assertEqual(v['status'],'returned',v.get('fault'))
                self.assertEqual(v['registers']['d0'],520)
                self.assertEqual(v['registers']['sp'],SP)


if __name__=='__main__':unittest.main()

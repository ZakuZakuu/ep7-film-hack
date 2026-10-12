import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest

from tools.ep7_re_workbench import (
    cfg, translate, classification, noise_cleared, private_directory, guard,
    bound_slot_target, FormatError)
from tools.ep7_re_query import query
from tools.probe_oe_executable import Instruction, disassemble


class WorkbenchTests(unittest.TestCase):
    def test_branch_and_call_keep_distinct_flow(self):
        rows = [Instruction(0,'beq','0x6'),Instruction(2,'call','0x20,[],0'),
                Instruction(5,'ret','[],0'),Instruction(6,'rets','')]
        flow = cfg(rows,0)
        self.assertEqual(flow['visited'],[0,2,5,6])
        self.assertEqual(flow['returns'],[5,6])
        self.assertIn({'source':2,'target':0x20,'kind':'call',
                       'qualification':'callee not followed; may-return fallthrough'},flow['edges'])
        self.assertFalse(flow['stops'])

    def test_indirects_not_invented(self):
        flow = cfg([Instruction(0,'calls','(a0)'),Instruction(2,'jmp','(a1)'),
                    Instruction(4,'ret','[],0')],0)
        self.assertEqual(flow['visited'],[0,2])
        self.assertEqual(flow['returns'],[])
        self.assertTrue(any(e['target'] is None for e in flow['edges']))

    def test_unknown_loop_or_extension_stops(self):
        for mnemonic in ('setlb','lne','udfu01','trap','Address','.byte'):
            with self.subTest(mnemonic=mnemonic):
                flow = cfg([Instruction(0,mnemonic,''),Instruction(1,'rets','')],0)
                self.assertEqual(flow['visited'],[0])
                self.assertTrue(flow['stops'])
                self.assertFalse(flow['returns'])

    def test_nonboundary_target_fails_closed(self):
        flow = cfg([Instruction(0,'jmp','0x1'),Instruction(2,'rets','')],0)
        self.assertTrue(flow['stops'])
        self.assertFalse(flow['returns'])

    def test_view_scope_and_end_exclusion(self):
        self.assertEqual(translate(0x1007,0x1000,0x20,8),0x27)
        for at in (0xfff,0x1008):
            with self.assertRaises(FormatError):
                translate(at,0x1000,0x20,8)

    def test_counterexample_not_eligibility(self):
        for s in (0,14,15,22,255):
            self.assertEqual(classification(0,s),classification(0x100,s))
        self.assertFalse(noise_cleared(0))
        self.assertTrue(noise_cleared(0x100))
        self.assertEqual(classification(0x31,15),6)
        self.assertEqual(classification(0x33,15),5)

    def test_guard_rejects_wrong_width_or_value(self):
        r = Instruction(0,'movbu','(25,a2),d0')
        guard(r,'movbu','(25,a2),d0')
        for m,o in [('movhu','(25,a2),d0'),('movbu','(24,a2),d0')]:
            with self.assertRaises(FormatError):
                guard(r,m,o)

    def test_slot_binding_requires_bounds_and_actual_code_boundary(self):
        # Original stand-in table: a typed pointer, not firmware bytes.
        import struct
        data = bytes(4)+struct.pack('<I',0x1020)
        rows = {0x20:Instruction(0x20,'rets','')}
        self.assertEqual(bound_slot_target(data,0,4,0x1000,rows),0x20)
        with self.assertRaises(FormatError):
            bound_slot_target(data,-4,8,0x1000,rows)
        for slot,base,admitted in [(3,0x1000,rows),(8,0x1000,rows),
                                    (4,0x1001,rows),(4,0x1000,{})]:
            with self.assertRaises(FormatError):
                bound_slot_target(data,0,slot,base,admitted)

    def test_private_output_rejects_repository_and_symlink(self):
        with self.assertRaises(FormatError):
            private_directory(Path('/workspace/analysis'))
        with tempfile.TemporaryDirectory(dir='/tmp') as d:
            p = Path(d)
            (p/'link').symlink_to(p,target_is_directory=True)
            with self.assertRaises(FormatError):
                private_directory(p/'link'/'child')
            self.assertEqual(private_directory(p/'real').stat().st_mode&0o777,0o700)

    def test_readonly_query_never_exports_instruction_operands(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as d:
            p = Path(d)/'project.sqlite'
            graph = {'edges':[],'windows':[],'validation':{},'negative_identities':[]}
            with sqlite3.connect(p) as db:
                db.executescript('CREATE TABLE metadata(key TEXT,value TEXT); CREATE TABLE cfg(window_id TEXT,source INTEGER,target INTEGER,kind TEXT,qualification TEXT); CREATE TABLE instructions(operands TEXT);')
                db.execute('INSERT INTO metadata VALUES (?,?)',('graph',json.dumps(graph)))
                db.execute('INSERT INTO instructions VALUES (?)',('private sentinel',))
                db.execute('INSERT INTO cfg VALUES (?,?,?,?,?)',('synthetic',0,8,'call','may-return'))
            before = p.read_bytes()
            result = query(p,incoming=8)
            self.assertEqual(result['xref_hits'][0]['target'],'0x8')
            self.assertNotIn('private sentinel',json.dumps(result))
            self.assertEqual(p.read_bytes(),before)

    def test_setup_dry_run_is_nonmutating(self):
        script = Path(__file__).resolve().parents[1]/'tools/setup_re_environment.sh'
        with tempfile.TemporaryDirectory(dir='/tmp') as d:
            destination = Path(d)/'uncreated'
            p = subprocess.run(['bash',str(script),'--dry-run','--root',str(destination)],
                               capture_output=True,text=True,check=True)
            self.assertIn('public downloads only',p.stdout)
            self.assertFalse(destination.exists())

    @unittest.skipUnless(os.environ.get('EP7_OBJDUMP') and os.environ.get('EP7_AS'),
                         'optional GNU integration; run setup/core environment')
    def test_real_assembler_decoder_flow(self):
        objdump,assembler = Path(os.environ['EP7_OBJDUMP']),Path(os.environ['EP7_AS'])
        fixture = Path(__file__).parent/'fixtures/mn103_flow.s'
        with tempfile.TemporaryDirectory(dir='/tmp') as d:
            obj,linked,raw = Path(d)/'fixture.o',Path(d)/'fixture.elf',Path(d)/'fixture.bin'
            subprocess.run([str(assembler),'-o',str(obj),str(fixture)],check=True,capture_output=True)
            # GAS leaves PC-relative label relocations in an ELF object. Apply
            # them with mature GNU ld; this links ONLY our synthetic fixture.
            linker = objdump.parent.parent/'ld/ld-new'
            subprocess.run([str(linker),'-Ttext=0','--no-relax','-o',str(linked),str(obj)],check=True,capture_output=True)
            objcopy = objdump.parent/'objcopy'
            subprocess.run([str(objcopy),'-O','binary','-j','.text',str(linked),str(raw)],check=True,capture_output=True)
            rows = disassemble(objdump,raw.read_bytes(),0)
            flow = cfg(rows,0)
            self.assertEqual(len(flow['returns']),2)
            self.assertFalse(flow['stops'])
            calls = [e for e in flow['edges'] if e['kind']=='call']
            self.assertEqual(len(calls),1)
            target = calls[0]['target']
            self.assertEqual(next(r for r in rows if r.address==target).mnemonic,'movbu')
            self.assertEqual(len(cfg(rows,target)['returns']),1)


if __name__ == '__main__':
    unittest.main()

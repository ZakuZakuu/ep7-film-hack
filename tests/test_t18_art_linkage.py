import unittest
import os
import subprocess
import tempfile
from pathlib import Path
from tools.t18_art_linkage import direct_candidates,qualify_virtual
from tools.probe_oe_executable import Instruction as I
from tools.inspect_olympus_oe import FormatError
from tools.probe_oe_executable import disassemble
from tools.mn103_analysis import prove_copy_loop
from tools.ep7_re_workbench import cfg
from tools.t18_native_art_records import bundle_layout


class LinkageTests(unittest.TestCase):
    def test_word_geometry_requires_same_buffer_basis_and_type(self):
        # Original symbolic annotations only; no program is assembled/executed.
        stores=[];calls=[]
        for i in range(39):
            stores += [I(8*i,'mov','(28,sp),a0'),I(8*i+4,'mov',f'd2,({4*i},a0)')]
            a=20*i
            calls += [I(a,'mov',f'({4+4*i},sp),a1'),I(a+4,'mov','d2,d0'),
                      I(a+8,'mov','2,d1'),I(a+12,'mov',f'{1000+i},a0'),
                      I(a+16,'call','0x292230,[d2,a2],12')]
        result=bundle_layout(stores,calls)
        self.assertEqual(len(result),39)
        self.assertEqual(result[-1]['record_offset'],152)
        wrong_width=stores[:-1]+[I(stores[-1].address,'movhu',stores[-1].operands)]
        wrong_base=[I(0,'mov','(4,a0),a1')]+calls[1:]
        wrong_type=calls[:2]+[I(8,'mov','1,d1')]+calls[3:]
        for s,c in [(wrong_width,calls),(stores,wrong_base),(stores,wrong_type),
                    (stores[:-2],calls),(stores,calls[:-5])]:
            with self.assertRaises(FormatError):bundle_layout(s,c)

    def test_local_record_copy_does_not_bypass_earlier_udf(self):
        r=[I(0,'udfu01','12,d0'),I(3,'mov','-6,d3'),I(5,'setlb',''),
           I(6,'mov','(a0),d2'),I(7,'inc4','a0'),I(8,'mov','d2,(a1)'),
           I(9,'inc4','a1'),I(10,'inc','d3'),I(11,'lne',''),I(12,'rets','')]
        proof=prove_copy_loop(r,5)
        self.assertEqual(proof['bytes_transferred'],24)
        self.assertEqual(cfg(r,3,[proof])['returns'],[12])
        blocked=cfg(r,0,[proof])
        self.assertFalse(blocked['returns'])
        self.assertEqual(blocked['visited'],[0])

    @unittest.skipUnless(os.environ.get('EP7_OBJDUMP') and os.environ.get('EP7_AS'),
                         'GNU required for original reference encodings')
    def test_gnu_assembles_both_slots_and_all_register_pairs(self):
        objdump=Path(os.environ['EP7_OBJDUMP']);assembler=Path(os.environ['EP7_AS'])
        fixture=Path(__file__).parent/'fixtures/mn103_virtual_access.s'
        with tempfile.TemporaryDirectory(dir='/tmp') as d:
            obj,raw=Path(d)/'original.o',Path(d)/'original.bin'
            for slot in (816,820):
                subprocess.run([str(assembler),'--defsym',f'panel_slot={slot}',
                                '-o',str(obj),str(fixture)],check=True,capture_output=True)
                subprocess.run([str(objdump.parent/'objcopy'),'-O','binary','-j','.text',
                                str(obj),str(raw)],check=True,capture_output=True)
                rows=disassemble(objdump,raw.read_bytes(),0)
                self.assertEqual(len(rows),32)
                for pair in range(16):
                    base,target=pair//4,pair%4
                    self.assertEqual((rows[2*pair].mnemonic,rows[2*pair].operands),
                                     ('mov',f'({slot},a{base}),a{target}'))
                    self.assertEqual((rows[2*pair+1].mnemonic,rows[2*pair+1].operands),
                                     ('calls',f'(a{target})'))

    def test_pc_start_and_truncated_data_remain_distinct(self):
        # Four original representations: +12/-12 displacement from PC start.
        for prefix,width,size in [(b'\xcd',2,5),(b'\xdd',4,7),
                                  (b'\xfa\xff',2,4),(b'\xfc\xff',4,6)]:
            for delta in (-12,12):
                data=bytearray(40)
                encoding=prefix+delta.to_bytes(width,'little',signed=True)
                data[16:16+len(encoding)]=encoding
                self.assertEqual(direct_candidates(bytes(data),16+delta),[16])
                self.assertEqual(direct_candidates(bytes(data),16+delta+size),[])
                self.assertEqual(direct_candidates(bytes(data[:16+size-1]),16+delta),[])
        with self.assertRaises(FormatError):direct_candidates(b'\xcd\x00\x00\x00\x00',0,0)

    def test_same_slot_does_not_establish_same_owner(self):
        r=[I(10,'call','0x100,[],4'),I(17,'mov','(a0),a1'),
           I(19,'mov','(820,a1),a2'),I(23,'calls','(a2)')]
        self.assertIsNotNone(qualify_virtual(r,820,{0x100}))
        self.assertIsNone(qualify_virtual(r,820,{0x200}))
        self.assertIsNone(qualify_virtual(r,816,{0x100}))
        self.assertIsNone(qualify_virtual(r[:2]+[I(18,'clr','a0')]+r[2:],820,{0x100}))
        self.assertIsNone(qualify_virtual(r[:3]+[I(23,'calls','(a1)')],820,{0x100}))

    def test_setter_value_must_come_from_actual_scalar_write(self):
        r=[I(10,'call','0x100,[],4'),I(17,'mov','(a0),a1'),
           I(19,'mov','1,d0'),I(21,'mov','(816,a1),a1'),I(25,'calls','(a1)')]
        self.assertEqual(qualify_virtual(r,816,{0x100},True)['scalar'],1)
        z=r[:2]+[I(19,'clr','d0')]+r[3:]
        self.assertEqual(qualify_virtual(z,816,{0x100},True)['scalar'],0)
        unknown=r[:2]+[I(19,'mov','d2,d0')]+r[3:]
        self.assertIsNone(qualify_virtual(unknown,816,{0x100},True))

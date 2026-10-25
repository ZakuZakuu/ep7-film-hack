"""Synthetic ABI/guard checks for T24. No OEM fixtures or package outputs."""
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
from ep7_color_min import Experiment, BASE, CAVE, STACK, SP
from ep7_t24_probe import SYMBOLS, ROWS, SITE, RESUME, C, Q, PATCH
spec=importlib.util.spec_from_file_location('t24_builder',PATCH/'build.py')
builder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
TOOLS=ROOT/'work/upstream/oly_fw_analysis/toolchains/mn103-patch-build'
ENGINE=ROOT/'work/upstream/oly_fw_analysis/toolchains/mn103-gnu-build/penf-mn103'


class ProfileGuards(unittest.TestCase):
    def test_wrong_stock_never_creates_package_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            stock=Path(temporary)/'own.BIN'
            stock.write_bytes(b'original synthetic wrong input')
            out=Path(temporary)/'output'
            with self.assertRaisesRegex(ValueError,'Exact E-P7'):
                builder.build(SimpleNamespace(stock=stock,out=out,verify_only=False))
            self.assertFalse(out.exists())

    def test_v2_keeps_t20_call_and_data_outside_its_patch_ranges(self):
        manifest=json.loads((PATCH/'patch.json').read_text())
        intervals=[(int(v['address'],0),int(v['address'],0)+v['length']) for v in manifest['modified_ranges']]
        self.assertTrue(all(not a<=0x603b02d9<b for a,b in intervals))
        self.assertEqual(intervals[0],(SITE,RESUME))
        self.assertGreaterEqual(manifest['placement']['prefix_margin'],64)
        self.assertGreaterEqual(manifest['placement']['suffix_margin'],64)
        self.assertEqual(ROWS[3],[0]*24)


@unittest.skipUnless((TOOLS/'gas/as-new').exists() and ENGINE.exists(),'Separately obtained GNU engine required')
class SyntheticProfileABI(unittest.TestCase):
    def test_leaf_and_nested_mdr_exits_preserve_all_registers_and_caller_stack(self):
        sys.path.insert(0,str(ROOT/'work/upstream/oly_fw_analysis/tools'))
        import penf_emulator as provider
        with tempfile.TemporaryDirectory(dir='/tmp') as temporary:
            x=object.__new__(Experiment)
            x.tools,x.out,x.instructions=TOOLS,Path(temporary),{}
            extension=x.assemble('own_extension',(PATCH/'hook.s').read_text(),CAVE,SYMBOLS)
            manifest=json.loads((PATCH/'patch.json').read_text())
            self.assertEqual(builder.sha(extension),manifest['modified_ranges'][1]['replacement_sha256'])
            symbols=subprocess.check_output([str(TOOLS/'binutils/objdump'),'-t',str(x.out/'own_extension.elf')],text=True)
            table_address=int(next(line.split()[0] for line in symbols.splitlines() if line.endswith(' profile_hl')),16)
            table_offset=table_address-CAVE
            self.assertEqual(list(struct.unpack_from('<96h',extension,table_offset)),sum(ROWS,[]))
            jump=x.assemble('own_jump','jmp extension\n',SITE,{'extension':CAVE})
            request=bytearray(1884)
            struct.pack_into('<H',request,10,2)  # Own Natural-like key; guard must not dereference owner.
            context=struct.pack('<2I',0,Q)+bytes(200)
            for nested in (False,True):
                selector_address=SYMBOLS['ep7_selector']
                source='.text\n.global _start\n_start:\n'+('mov 0,d0\nmov d0,mdr\n' if nested else '')+\
                       'ret [d2,d3,a2,a3],20\n.org '+str(SITE-2-selector_address)+'\n'+\
                       'mov d3,a0\ncall _start,[d2,d3,a2,a3],20\n'
                caller=x.assemble('own_code',source,selector_address)
                r=provider.Region
                outputs=[]
                for patched in (False,True):
                    regs={'pc':SITE-2,'sp':SP,'d3':C,'mdr':0x345678,'psw':3,
                          'd0':0x112233,'d1':0x556677,'d2':0x8899aa,'a0':0x123,
                          'a1':0x456,'a2':0x789,'a3':0xabc}
                    image=bytearray(caller)
                    if patched:image[SITE-selector_address:RESUME-selector_address]=jump
                    regions=[r('caller',selector_address,bytes(image),'rx'),
                             r('context',C,context),r('request',Q,bytes(request)),
                             r('stack',STACK,b'\xa5'*0x2000,'rw',True)]
                    if patched:regions.append(r('extension',CAVE,extension,'rx'))
                    out=provider.execute(regions,regs,RESUME,limit=500,trace_limit=500)
                    self.assertEqual(out['status'],'returned',out.get('fault'))
                    outputs.append(out)
                self.assertEqual(outputs[0]['registers'],outputs[1]['registers'])
                a,b=(x.captured(v,'stack') for v in outputs)
                self.assertEqual(a[SP-STACK:],b[SP-STACK:])


if __name__=='__main__':unittest.main()

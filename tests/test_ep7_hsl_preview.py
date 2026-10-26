"""Owned synthetic programs/objects only; no OEM fixtures or firmware output."""
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
from ep7_color_min import CAVE, STACK, SP
from ep7_t24_1_probe import Probe, PATCH, SYMBOLS, COMPACT, CURRENT
from ep7_t24_probe import ROWS, SITE, RESUME, C, J
TOOLS=ROOT/'work/upstream/oly_fw_analysis/toolchains/mn103-patch-build'
ENGINE=ROOT/'work/upstream/oly_fw_analysis/toolchains/mn103-gnu-build/penf-mn103'
spec=importlib.util.spec_from_file_location('v3_test_builder',PATCH/'build.py')
builder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PreviewBuildGuards(unittest.TestCase):
    def test_bad_stock_is_rejected_before_output_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            stock=Path(tmp)/'owned.BIN'
            stock.write_bytes(b'owned invalid stock')
            out=Path(tmp)/'must-not-exist'
            with self.assertRaisesRegex(ValueError,'Exact E-P7'):
                builder.build(SimpleNamespace(stock=stock,verify_only=False,out=out))
            self.assertFalse(out.exists())

    def test_manifest_retains_v2_constants_and_preserves_loaded_margins(self):
        v3=json.loads((PATCH/'patch.json').read_text())
        v2=json.loads((ROOT/'patches/hsl-profiles/e-p7/patch.json').read_text())
        self.assertEqual(v3['constant_rows_native_physical_HL_pairs'],v2['constant_rows_native_physical_HL_pairs'])
        self.assertEqual(v3['preserved_v2_output_sha256'],v2['output_sha256'])
        self.assertNotEqual(v3['output_sha256'],v2['output_sha256'])
        self.assertEqual(v3['modified_ranges'][0],v2['modified_ranges'][0])
        self.assertLess(v3['modified_ranges'][1]['length'],v2['modified_ranges'][1]['length'])
        self.assertGreaterEqual(v3['placement']['prefix_margin'],64)
        self.assertGreaterEqual(v3['placement']['suffix_margin'],64)


@unittest.skipUnless((TOOLS/'gas/as-new').exists() and ENGINE.exists(),'Separately obtained strict GNU engine required')
class SyntheticPreviewABI(unittest.TestCase):
    def test_all_profile_sources_exclusions_sparse_rows_and_abi(self):
        sys.path.insert(0,str(ROOT/'work/upstream/oly_fw_analysis/tools'))
        import penf_emulator as provider
        with tempfile.TemporaryDirectory(dir='/tmp') as tmp:
            x=object.__new__(Probe)
            x.tools,x.out,x.instructions,x.provider=TOOLS,Path(tmp),{},provider
            extension=x.assemble('own_v3',(PATCH/'hook.s').read_text(),CAVE,SYMBOLS)
            manifest=json.loads((PATCH/'patch.json').read_text())
            import hashlib
            self.assertEqual(hashlib.sha256(extension).hexdigest(),manifest['modified_ranges'][1]['replacement_sha256'])
            symbols=subprocess.check_output([str(TOOLS/'binutils/objdump'),'-t',str(x.out/'own_v3.elf')],text=True)
            address=int(next(line.split()[0] for line in symbols.splitlines() if line.endswith(' profile_writes')),16)
            for profile,row in enumerate(ROWS):
                expanded=[0]*24
                fields={706+24*i:2*i for i in range(12)}|{710+24*i:2*i+1 for i in range(12)}
                writes=struct.unpack_from('<HhHh',extension,address-CAVE+profile*8)
                for offset,value in zip(writes[::2],writes[1::2]):
                    self.assertIn(offset,fields)
                    expanded[fields[offset]]=value
                self.assertEqual(expanded,row)
            jump=x.assemble('own_jump','jmp extension\n',SITE,{'extension':CAVE})
            cases=[(f'compact_{callback:x}_{p}',p,dict(compact=callback),True)
                   for callback in COMPACT for p in range(1,5)]
            cases += [(f'owner_{p}',p,{},True) for p in range(1,5)]
            cases += [(name,1,kw,False) for name,kw in (
                ('Natural',dict(key=2,compact=COMPACT[0])),
                ('MONO',dict(key=12,compact=COMPACT[0])),
                ('f00d',dict(special=True,compact=COMPACT[0])),
                ('custom',dict(custom=True,compact=COMPACT[0])),
                ('invalid0',dict(current=0,compact=COMPACT[0])),
                ('invalid5',dict(current=5,compact=COMPACT[0])),
                ('invalid255',dict(current=255,compact=COMPACT[0])),
                ('unknown',dict(callback=0x12345678)),
                ('null_owner',dict(callback=0)),
                ('invalid_record',dict(record=-1,compact=COMPACT[0])))]
            for nested in (False,True):
                target=SYMBOLS['ep7_selector']
                source='.text\n.global _start\n_start:\n'+('mov 0,d0\nmov d0,mdr\n' if nested else '')+\
                    'ret [d2,d3,a2,a3],20\n.org '+str(SITE-2-target)+'\n'+\
                    'mov d3,a0\ncall _start,[d2,d3,a2,a3],20\n'
                caller=x.assemble('own_selector_'+str(nested),source,target)
                for name,profile,kw,eligible in cases:
                    fixture=x.fixture(profile,poison=b'\xa5'*3164,**kw)
                    outputs=[]
                    for patched in (False,True):
                        image=bytearray(caller)
                        if patched:image[SITE-target:RESUME-target]=jump
                        r=provider.Region
                        regions=[r('caller',target,bytes(image),'rx'),
                                 r('stack',STACK,b'\xa5'*0x2000,'rw',True),*fixture]
                        if patched:regions.append(r('extension',CAVE,extension,'rx'))
                        v=provider.execute(regions,{'pc':SITE-2,'sp':SP,'d3':C,'mdr':0x123456,
                                                   'd2':0x1234,'a2':0x5678,'a3':0x9abc,'psw':3},
                                           RESUME,limit=2000,trace_limit=2000)
                        self.assertEqual(v['status'],'returned',(name,v.get('fault')))
                        outputs.append(v)
                    a,b=outputs
                    self.assertEqual(a['registers'],b['registers'],name)
                    self.assertEqual(x.captured(a,'stack')[SP-STACK:],x.captured(b,'stack')[SP-STACK:],name)
                    expected=bytearray(x.captured(a,'output'))
                    if eligible:
                        for i in range(12):
                            struct.pack_into('<h',expected,706+24*i,ROWS[profile-1][2*i])
                            struct.pack_into('<h',expected,710+24*i,ROWS[profile-1][2*i+1])
                    self.assertEqual(x.captured(b,'output'),bytes(expected),name)


if __name__=='__main__':unittest.main()

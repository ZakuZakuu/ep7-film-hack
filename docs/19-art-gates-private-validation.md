# 19 · Private reproduction of ART normalization gates

2026-10-12 · [Issue #33](https://github.com/ZakuZakuu/ep7-film-hack/issues/33) · [New findings and stop](../research/e142-art-host-gates.md). Run from the repo root with the existing private firmware and GNU2.44 from [T3](13-executable-private-validation.md). Reuse the OE decoder and bounded window helper; no new ISA decoder, package or camera client.

Two checks only: the receiver's known keyed normalization table and its independent Type-conditioned suppression gate. The existing diagnostic window is an identity/field-width guard; its ten field associations are prior T10 evidence, not fresh results. No callee body, whole-image scan, other block or resource bytes are examined. Coordinates are decoded #0 offsets under the already validated static view, not device addresses.

The synthetic controls below verify ordinary arithmetic and counterexamples before reading OEM bytes. A retained FilmNoise bit with MonoEnable clear is **not an accepted camera state or evidence of color grain rendering**. Real assertions then bind the masks, stores, pointers and conditions to the actual original instructions; no firmware execution or complete CPU emulation is involved. Unknown calls and hardware loops remain unresolved.

```python
from pathlib import Path
import hashlib,struct
from tools.inspect_olympus_oe import inspect,check_expected,decode_chunk
from tools.probe_oe_executable import disassemble,walk

gnu=Path('/tmp/ep7-analysis-tools/binutils-build/binutils/objdump')
fixture=b'\xcd\x08\x00\x00\x00\xdf\x00\x00\xdf\x00\x00'
rows=disassemble(gnu,fixture,0)
assert rows[0].direct_target()==8 and walk(rows,0)['return_offsets']==[5]
assert walk(rows,8)['return_offsets']==[8]
noise,mono=0x4000,0x800000
clear_a=[0x40,0x80,0x300,0x4000,0x40000,0x100000]
clear_b=[0x400,0x1800,0x2000,0x8000,0x20000,0x600000]
def local_type_gate(flags,t):
 if t&0xf0==0x40 or t&0xf00==0x100:
  for mask in clear_a: flags&=~mask
  if t&0xf0==0x40:
   for mask in clear_b: flags&=~mask
 return flags&0xffffffff
assert local_type_gate(noise,0)==noise
assert local_type_gate(noise,0x10)==noise
assert local_type_gate(noise|mono,0x100)==mono
assert local_type_gate(noise|mono,0x40)==mono
assert local_type_gate(noise|mono,0x140)==mono
assert sum(clear_a)==0x1443c0 and sum(clear_b)==0x62bc00
assert not (sum(clear_a)|sum(clear_b))&mono
print('synthetic call/return and local-mask countercontrols passed; not OEM execution')

original=Path('/tmp/ep7-firmware/E142_EP7_firmware_download.BIN')
before=inspect(original)
check_expected(before,'9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb',111017984)
assert before['block_count']==5 and all(b['checksum_residual']=='0x00000000' for b in before['blocks'])
block=before['blocks'][0]
with original.open('rb') as f:
 f.seek(block['payload_offset']);data=decode_chunk(f.read(block['payload_length']))
assert len(data)==26214336
assert hashlib.sha256(data).hexdigest()==block['decoded_sha256']=='5dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190'
def window(start,end):
 return {r.address:r for r in disassemble(gnu,data[start:end],start)}
def expect(rows,at,mnemonic,operands):
 assert rows[at].mnemonic==mnemonic and rows[at].operands==operands
r=window(0x3337cb,0x333c97)
# Existing pointer provenance: parameter base=context+4; flag pointer=context+16.
expect(r,0x3338f5,'mov','a3,a0');expect(r,0x3338f6,'inc4','a0')
expect(r,0x3338f7,'mov','a0,(4,sp)')
expect(r,0x333952,'mov','(4,sp),d3');expect(r,0x333956,'add','16,d3')
expect(r,0x3339a1,'mov','16,a2');expect(r,0x3339a3,'add','a3,a2')
# Check 1: existing sparse special-case dispatch, not a list of all ART items.
records=[struct.unpack_from('<II',data,p) for p in range(0x501a34,0x501ab4,8)]
assert len(records)==16 and sum(k!=0 for k,p in records)==14
assert all(p-0x60020020 in r for k,p in records)
keys={0x01010064+k for k,p in records if k and p-0x60020020==0x333a6a}
assert keys=={0x01010068,0x01020068,0x0102006d}
expect(r,0x333a6a,'mov','(a2),d0');expect(r,0x333a6b,'or','8388608,d0')
expect(r,0x333a71,'jmp','0x333af4');expect(r,0x333af4,'mov','d0,(a2)')
expect(r,0x3339ed,'jmp','0x333af5')  # empty-key miss reaches common code
expect(r,0x3339bf,'jmp','0x333af5');expect(r,0x3339ca,'jmp','0x333af5')
ors=[row for at,row in r.items() if 0x333a03<=at<0x333af5 and row.mnemonic=='or']
assert ors and all(not int(row.operands.split(',')[0])&noise for row in ors)
# Existing non-mono-forcing case used only for a conditional local-path statement.
assert records[1]==(1,0x60020020+0x333a03)
expect(r,0x333a04,'or','128,d0');expect(r,0x333a07,'jmp','0x333af4')
print('check1: three ART keys force MonoEnable; table miss is not a filter rejection')
# Check 2: independent halfword-Type suppression gate, same established receiver.
expect(r,0x333af5,'mov','d3,a0');expect(r,0x333af7,'movhu','(a0),d0')
for at,m,o in [(0x333af9,'mov','240,d1'),(0x333afc,'and','d1,d0'),
 (0x333afe,'cmp','64,d0'),(0x333b00,'beq','0x333b0e'),
 (0x333b04,'and','3840,d0'),(0x333b08,'cmp','256,d0'),
 (0x333b0c,'bne','0x333b6c'),(0x333b3b,'and','d1,d0'),
 (0x333b3d,'cmp','64,d0'),(0x333b3f,'bne','0x333b6c')]: expect(r,at,m,o)
for masks,sites in [(clear_a,[0x333b0f,0x333b16,0x333b1d,0x333b24,0x333b2b,0x333b32]),
                    (clear_b,[0x333b42,0x333b49,0x333b50,0x333b57,0x333b5e,0x333b65])]:
 for mask,at in zip(masks,sites):
  expect(r,at,'and',f'{-1-mask},d0');expect(r,at+6,'mov','d0,(a2)')
# Revalidate prior diagnostic associations, including Type; no string discovery.
diag=window(0x13c1f98,0x13c217f)
for literal,shift,bit,label in [(0x13c209d,0x13c20a3,14,'FilmNoise'),
                              (0x13c20d9,0x13c20df,23,'MonoEnable')]:
 expect(diag,shift,'lsr',f'{bit},d0')
 at=int(diag[literal].operands.split(',')[0])-0x60020020
 assert data[at:data.index(b'\0',at)].decode('ascii').strip()==label
expect(diag,0x13c20ec,'movhu','(16,a3),d0')
at=int(diag[0x13c20ef].operands.split(',')[0])-0x60020020
assert data[at:data.index(b'\0',at)].decode('ascii').strip()=='Type'
print('check2: Type-conditioned masks clear FilmNoise but preserve MonoEnable locally')
assert inspect(original)==before
assert hashlib.sha256(data).hexdigest()==block['decoded_sha256']
print('original/OE/decoded guards unchanged; no downstream callee or resource scan')
```

Expected: synthetic controls pass; check1 reports three keys forcing MonoEnable and a non-rejecting table miss; check2 verifies Type-conditioned FilmNoise clearing with MonoEnable preservation; all original/OE/decoded guards unchanged. Only short original findings are printed. The case-mask calculation is a local arithmetic model, not a patched parameter record, packet or image.

Private transcript from the initial bounded inspection: `/tmp/ep7-firmware/t11/receiver.asm`, mode0600 in a0700 directory. A separate ignored `work/t11/HANDOFF.md` retains restart information. No original disassembly dump, catalog, input binary, extracted asset, manual, photo, private identity or third-party source is committed. The GNU executable is an external GPL tool; these research procedures are original. Existing repository synthetic CI checks tooling, not image effects or device support. No new test framework/runtime product code is required for this documentation-only PR.

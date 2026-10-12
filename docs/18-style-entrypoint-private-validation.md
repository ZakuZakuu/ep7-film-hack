# 18 · Private validation of selector/editor evidence

2026-10-12 · [Issue #31](https://github.com/ZakuZakuu/ep7-film-hack/issues/31) · [Findings / decision](../research/e142-cross-model-style-entrypoints.md). Run from the repository root. Reuse the existing private OEM original, OE decoder and GNU2.44 established in [T3](13-executable-private-validation.md); no downloader, camera client, execution/emulation or extra disassembler installation. All original data and any assembly transcripts stay under `/tmp/ep7-firmware/t10/`, never in Git. `work/t10/` is ignored local research scratch.

## Documentation provenance

Official URLs are linked next to the model-specific claims in the report. Download only those **public documentation** URLs with ordinary HTTPS/`urllib.request`, inherited proxy and TLS validation, a finite timeout and 24MiB cap. No vendor contact or private multi-model firmware is needed. Keep copies local; do not commit manuals, screenshots or upstream sources.

The reused E-P7 manual is16862659bytes, SHA-256 `54b139500c2f4192bc678b10427309d1ead22c8455550b6d235d467c2eea83f8`,200pages. New snapshots accessed2026-10-12:

| Snapshot | Bytes | SHA-256 |
| --- | --- | --- |
| om5ii-picture | 105598 | `c84d1dd6481df845b8d514bbaabc2e923ef3277f1ae6ab31c30b4743b0249006` |
| om5ii-art | 95546 | `c266629bba5fea10721fe583c4a74f81d1c90015359df7cb2b2a6dc894f312e2` |
| em5ii-manual | 6430061 | `4de33b8e5b4514398819d8662762d314b9dc41b8913c854e4923173d00b5aedb` |
| penf-support | 202461 | `206646d9038da2ce33e112423efbef30d6c46c64fa4c5a9797f95a6249ff1aa6` |
| penf-manual | 5124624 | `e684e88f975029d0189522648f8e889b64143915d060ef6ebb0d5ff274c05ce8` |
| om5ii-custom | 105080 | `9e5c157161d17934dc7f67ff31f48ecea8179b645bde06ce424f0bc33522d64c` |
| om5ii-artlv | 87275 | `6ad13b8886b12714ba902b93b799522502d50f2142f214ce2cf367ccb1b04c49` |
| om5ii-hide | 87953 | `0f9e12d0030d2ba99a62b268a8cab81e61c7c823f7a59fb36a274dff5638ff56` |
| om5ii-scp-default | 109299 | `e2d79627d8c28aa9bbb93c4a30d146ae90b35658b58e0f7c7715fa4255c2e21c` |

The E-M5 II PDF has186pages, including FW4.0 addenda; the PEN-F FW3.0 PDF has188pages. Use mature Poppler `pdftotext -layout` (this environment25.03.0); printed page number equals the1-based PDF page for these snapshots. Review E-P7 pp49/53 and103–104 together: documented profile-tone storage and owner-reported lever behavior are distinct evidence, not a reconciled runtime result. Review E-M5 II pp30–31/70/86/102/152/156; PEN-F pp38/43/64/88/89/107/158/162/180–182. Version qualifiers matter. HTML claims use the specific section headings, not navigation/sidebar lists. Cosmetic webpage bytes can change; a changed hash requires source review, not a firmware conclusion.

## Bounded byte reproduction

Run the following original procedure as `python3 -` from the repo root. It reads the verified original, checks five OE residuals and decoded #0 identity, uses only nominated existing windows/group, then checks unchanged originals. It prints short associations and arithmetic only; no assembly dump or complete name catalog. The synthetic bit model verifies arithmetic and preservation of unrelated bits, **not OEM execution, accepted combinations, GUI behavior or image output**. Actual bit associations additionally require the real producer shift/mask instructions and independently referenced diagnostic labels. GNU is an external GPL tool; no third-party implementation was copied into this MIT repository.

```python
from pathlib import Path
import hashlib, struct
from tools.inspect_olympus_oe import inspect, check_expected, decode_chunk
from tools.probe_oe_executable import disassemble, walk

gnu = Path('/tmp/ep7-analysis-tools/binutils-build/binutils/objdump')
# Original synthetic fixture: no proprietary execution or emulation.
fixture = b'\xcd\x08\x00\x00\x00\xdf\x00\x00\xdf\x00\x00'
rows = disassemble(gnu, fixture, 0)
assert rows[0].direct_target() == 8
assert walk(rows, 0)['return_offsets'] == [5]
assert walk(rows, 8)['return_offsets'] == [8]
# Each tuple is source-bit, destination-bit, width, clear-site, shift-site,
# diagnostic label-site, diagnostic right-shift-site, short association.
fields = [
 (0,6,1,0x301d7d,0x301d86,0x13c2025,0x13c202b,'StarLight'),
 (1,7,1,0x301d8b,0x301d99,0x13c2039,0x13c203f,'SoftFocus'),
 (2,8,2,0x301d9e,0x301dac,0x13c204d,0x13c2053,'Diorama'),
 (4,10,1,0x301db1,0x301dbd,0x13c2061,0x13c2067,'PinHole'),
 (5,11,2,0x301dc3,0x301dd0,0x13c2075,0x13c207b,'BandShading'),
 (7,13,1,0x301dd6,0x301de4,0x13c2089,0x13c208f,'WhiteEdge'),
 (8,14,1,0x301de9,0x301df7,0x13c209d,0x13c20a3,'FilmNoise'),
 (9,15,1,0x301dfd,0x301e09,0x13c20b1,0x13c20b7,'Frame'),
 (10,16,1,0x301e0e,0x301e1b,0x13c20c5,0x13c20cb,'MovieEffect'),
 (11,23,1,0x301e21,0x301e2d,0x13c20d9,0x13c20df,'MonoEnable'),
]
mask = sum(((1 << w)-1) << d for s,d,w,*rest in fields)
def remap(source, previous=0):
 value = previous & ~mask
 for s,d,w,*rest in fields: value |= ((source >> s) & ((1 << w)-1)) << d
 return value & 0xffffffff
for s,d,w,*rest in fields:
 for value in range(1 << w):
  assert remap(value << s) == value << d
  assert remap(value << s, 0xffffffff) & ~mask == 0xffffffff & ~mask
assert remap(1 << 12) == 0  # unused source bit, no invented effect
assert remap((1 << 12)-1) == mask
print('synthetic call/return and bit-field arithmetic controls passed')

original = Path('/tmp/ep7-firmware/E142_EP7_firmware_download.BIN')
info = inspect(original)
check_expected(info, '9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb', 111017984)
assert info['block_count'] == 5
assert all(b['checksum_residual'] == '0x00000000' for b in info['blocks'])
b = info['blocks'][0]
with original.open('rb') as f:
 f.seek(b['payload_offset']); data = decode_chunk(f.read(b['payload_length']))
assert len(data) == 26214336
assert hashlib.sha256(data).hexdigest() == b['decoded_sha256'] == '5dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190'
def window(start, end):
 return {r.address:r for r in disassemble(gnu, data[start:end], start)}
producer = window(0x301d16, 0x301ef3)
diagnostic = window(0x13c1f98, 0x13c217f)
assert producer[0x301e7b].direct_target() == 0x2e4e58
assert producer[0x301e88].direct_target() == 0x3337cb
assert producer[0x301d79].operands == '20,a1'
assert producer[0x301d77].operands == '(52,sp),d3'
assert producer[0x301e32].operands == 'd3,(52,sp)'
assert diagnostic[0x13c2020].operands == '12,a2'
assert producer[0x301d7b].operands == '(a1),d0'
assert producer[0x301d83].operands == '1,d0'
source_shifts = [None,0x301d91,0x301da6,0x301db7,0x301dcb,
                 0x301ddc,0x301def,0x301e03,0x301e14,0x301e27]
assert producer[0x301da4].operands == producer[0x301dc9].operands == '3,d0'
for field,source_shift in zip(fields,source_shifts):
 s,d,w,clear,left,label,right,name = field
 if source_shift is not None:
  assert producer[source_shift].mnemonic == 'lsr'
  assert producer[source_shift].operands.startswith(f'{s},')
 expected_clear = -1 - (((1 << w)-1) << d)
 assert producer[clear].mnemonic == 'and'
 assert producer[clear].operands == f'{expected_clear},d3'
 assert producer[left].mnemonic == 'asl'
 assert producer[left].operands.startswith(f'{d},')
 assert diagnostic[right].mnemonic == 'lsr'
 assert diagnostic[right].operands == f'{d},d0'
 assert diagnostic[right+3].mnemonic == 'and'
 assert diagnostic[right+3].operands == f'{(1 << w)-1},d0'
 at = int(diagnostic[label].operands.split(',')[0]) - 0x60020020
 assert data[at:data.index(b'\0',at)].decode('ascii').strip() == name
 print(f'{name}: source bits {s}:{s+w-1} -> parameter bits {d}:{d+w-1}')
# A wrong destination/source-offset interpretation must fail the same guards.
assert diagnostic[0x13c2020].operands != '20,a2'
assert producer[0x301d79].operands != '12,a1'
resolver = window(0x75068f, 0x7506c4)
assert walk(list(resolver.values()), 0x75068f)['return_offsets'] == [0x7506c1]
assert not walk(list(resolver.values()), 0x75068f)['direct_calls']
u32 = lambda at: struct.unpack_from('<I', data, at)[0]
def copied(a):
 delta = a - 0x61f98540
 assert 0 <= delta < 0x2e350
 return 0x2107e0 + delta
heads = [copied(u32(p)) for p in range(0x221078,0x2211a0,4)]
head = copied(u32(copied(u32(0x2211a0))+4))
end = min(p for p in heads+[0x221078] if p > head)
assert (head,end) == (0x21fa74,0x21fb58)
label = u32(head+4*(44-1)) - 0x60020020
assert data[label:data.index(b'\0',label)].decode('ascii') == 'SettingController::changePicMode'
for start,end,at in [(0x786f20,0x786f80,0x786f46),(0x79e7e0,0x79e850,0x79e80c)]:
 row = window(start,end)[at]
 assert row.mnemonic == 'mov' and row.operands == '258,d0'
assert inspect(original) == info
assert hashlib.sha256(data).hexdigest() == b['decoded_sha256']
print('two bounded anchors / negative controls / unchanged input guards passed')
```

Expected: synthetic controls pass; ten source→parameter field associations; two bounded anchors/negative controls/input guards pass. The second anchor still has **no executable selector binding**: the name group is text and old candidate boundaries are immediate258, not an identity operand. Scope is five code windows plus one existing bounded name group, not a new whole-image reference scan. Existing calls are verified, but no new callee is followed. The producer's loop boundary limits `walk()`; this procedure is not a full reachability or CPU simulator.

The retained private transcripts are `/tmp/ep7-firmware/t10/301d16.asm`, `13c1f98.asm`, `75068f.asm`, `786f20.asm`, `79e7e0.asm`, mode0600 in a0700 directory. They are not public outputs. No JPEG or OI.Share schema was reread this round; T9's ExifTool method is a **future separately authorized** optional observation method only.

Public changes contain original analysis, selected numeric references and this reproduction procedure. No original firmware, decoded payload, proprietary assembly/catalog/XML, manual, camera identifiers, JPEG/EXIF dump, new processing/UI/transport tool or firmware package is committed. Repository CI verifies existing synthetic tooling, not camera behavior. Publication requires Markdown link/privacy/diff review, the exact new commit's CI and an open research PR; do not merge automatically.

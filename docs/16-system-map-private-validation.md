# T7 · Private system-boundary reproduction

[Report](../research/e142-system-boundary-map.md) · [selected numeric index](../research/e142-system-boundary-map.json) · [GNU provenance/build and ISA limits](13-executable-private-validation.md).

Run from the repository root with the **existing authorized private sample** and GNU binutils2.44. No camera or network request is involved. Do not download another OEM image, publish intermediate bytes/operands/catalogs, or treat the index as a complete linker/module map. All intervals are half-open decoded #0 offsets. The main-code alias, copied-data view and relocated-helper view have different scopes; none is observed device memory.

## Guarded numeric reference using existing tooling

The moved-data base below applies **only to `[0x2107e0,0x23eb30)`**. This reuses the existing literal verifier rather than adding a scanner. Output is numeric metadata; retain it privately.

```bash
umask 077
mkdir -p /tmp/ep7-firmware/t7
python3 tools/probe_oe_references.py \
  /tmp/ep7-firmware/E142_EP7_firmware_download.BIN \
  --expected-size 111017984 \
  --expected-sha256 9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb \
  --block-index 0 --mapping-base 0x61d87d60 --target-offset 0x2211a0 \
  --objdump /tmp/ep7-analysis-tools/binutils-build/binutils/objdump \
  --start 0x75068f --length 0x35 --literal-source 0x75069f \
  > /tmp/ep7-firmware/t7/moved-root-reference.json
```

Expected: one exact word reference at0x7506a1 inside nominated MOV0x75069f, value0x61fa8f00. The same tool's wrong-base/target controls below are checked without extra OEM downloads.

## Original synthetic controls, then bounded OEM checks

This procedure revalidates **23 selected entry windows, 19 nominated direct edges, three conditional vtable fields**, metadata dimensions and address/identity countercontrols. GNU instruction text remains in memory, never printed. It does not execute the camera, emulate unknown instructions or derive a whole-program call graph. The two copied-helper decodes also check the proposed execution view independently of the main alias.

```bash
python3 - <<'PY'
from pathlib import Path
import hashlib, json, struct
from tools.inspect_olympus_oe import inspect, check_expected, decode_chunk
from tools.probe_oe_executable import disassemble, walk, mapping_checks, summarize

gnu = Path('/tmp/ep7-analysis-tools/binutils-build/binutils/objdump')

# Original synthetic call + two returns, before any OEM read.
fixture = b'\xcd\x08\x00\x00\x00\xdf\x00\x00\xdf\x00\x00'
rows = disassemble(gnu, fixture, 0)
assert rows[0].direct_target() == 8
assert walk(rows, 0)['return_offsets'] == [5]
assert walk(rows, 8)['return_offsets'] == [8]

def translate(address, destination, source, size):
    delta = address - destination
    if not 0 <= delta < size:
        raise ValueError('address outside nominated copied span')
    return source + delta

assert translate(0x1005, 0x1000, 0x20, 8) == 0x25
for invalid in [0x0fff, 0x1008]:
    try:
        translate(invalid, 0x1000, 0x20, 8)
    except ValueError:
        pass
    else:
        raise AssertionError('synthetic range control accepted')
print('synthetic GNU and bounded-translation controls passed')

index = json.loads(Path('research/e142-system-boundary-map.json').read_text())
original = Path('/tmp/ep7-firmware/E142_EP7_firmware_download.BIN')
info = inspect(original)
check_expected(info, index['input_sha256'], index['input_size'])
assert info['block_count'] == 5
assert all(b['checksum_residual'] == '0x00000000' for b in info['blocks'])
block = info['blocks'][0]
with original.open('rb') as f:
    f.seek(block['payload_offset'])
    data = decode_chunk(f.read(block['payload_length']))
assert len(data) == 26214336
assert hashlib.sha256(data).hexdigest() == block['decoded_sha256'] == index['decoded_sha256']
main = 0x60020020
u32 = lambda at: struct.unpack_from('<I', data, at)[0]

decoded = {}
for window in index['code_windows']:
    start, end = int(window['start'], 16), int(window['end'], 16)
    assert 0 <= start < end <= len(data) and end - start <= 128 * 1024
    rows = disassemble(gnu, data[start:end], start)
    decoded[window['id']] = {r.address: r for r in rows}
assert len(decoded) == 23
for edge in index['direct_calls']:
    row = decoded[edge['window']][int(edge['source'], 16)]
    assert row.mnemonic in {'call', 'calls'}
    assert row.direct_target() == int(edge['target'], 16)
assert len(index['direct_calls']) == 19
for edge in index['conditional_virtual_evidence']:
    at = int(edge['vtable_payload_offset'], 16) + edge['slot_bytes']
    assert u32(at) - main == int(edge['target'], 16)
    assert decoded['submit'][int(edge['source'], 16)].mnemonic in {'call', 'calls'}

# Multiple typed pointer levels corroborate the bounded initializer view.
copied = lambda address: translate(address, 0x61f98540, 0x2107e0, 0x2e350)
root, group_start, name_start, name_end = 0x2211a0, 0x221078, 0x21f8a4, 0x221078
bank_heads = [copied(u32(root + 4*i)) for i in range(6)]
counts = [(b-a)//4 for a,b in zip(bank_heads, bank_heads[1:] + [root])]
assert counts == index['name_metadata']['bank_class_counts'] == [21,4,37,4,7,1]
group_heads = [copied(u32(at)) for at in range(group_start, root, 4)]
assert len(group_heads) == len(set(group_heads)) == 74
assert all(name_start <= p < name_end and (p-name_start)%4 == 0 for p in group_heads)
assert any(a > b for a,b in zip(group_heads, group_heads[1:]))  # not ordered by extent
assert (name_end-name_start)//4 == 1525
for at in range(name_start, name_end, 4):
    p = u32(at) - main
    assert 0 <= p < len(data)
    end = data.find(b'\0', p, min(p+256, len(data)))
    assert end > p and all(32 <= v <= 126 for v in data[p:end])

def lookup(identity):
    bank, group, method = (identity >> 16)&255, (identity >> 8)&255, identity&255
    if not 1 <= bank <= 6 or not 1 <= group <= counts[bank-1] or method == 0:
        raise ValueError('invalid 1-based metadata identity')
    head = copied(u32(bank_heads[bank-1] + 4*(group-1)))
    bound = min(p for p in group_heads + [name_end] if p > head)
    at = head + 4*(method-1)
    if at >= bound:
        raise ValueError('method outside bounded name group')
    p = u32(at) - main
    return data[p:data.index(b'\0', p)].decode('ascii')

for binding in index['identity_bindings']:
    assert lookup(int(binding['id'], 16)) == binding['label']
for invalid in [0, 0x39020003, 0x070101, 0x010100, 0x01ff01, 0x0201ff]:
    try:
        lookup(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError('invalid identity accepted')
# No catalog printed. This validator rejects bad IDs; firmware bounds checks are not claimed.
resolver = list(decoded['name_resolver'].values())
assert mapping_checks(resolver, 0x61d87d60, [0x75069f])[0]['immediate_u32'] == 0x61fa8f00
assert data.count(struct.pack('<I', 0x61fa8f00)) == 1
assert data.count(struct.pack('<I', root+main)) == 0
assert data.count(struct.pack('<I', 0x61fa8f20)) == 0
assert walk(resolver, 0x75068f)['visited_instructions'] == 22
assert walk(resolver, 0x75068f)['return_offsets'] == [0x7506c1]

# Independently decode the nominated helpers at their proposed execution addresses.
for address, key in [(0x47001052, 'relocated_copy'), (0x4700115e, 'relocated_fill')]:
    start = translate(address, 0x47000800, 0x141c9e0, 0x1800)
    window = next(w for w in index['code_windows'] if w['id'] == key)
    assert start == int(window['start'], 16)
    end = int(window['end'], 16)
    rows = disassemble(gnu, data[start:end], address)
    assert [r.mnemonic for r in rows] == [r.mnemonic for r in decoded[key].values()]

# Data and padding decode too: independent data references override line counts.
rows = disassemble(gnu, data[root:root+48], root)
stats = summarize(rows, root, 48)
assert (len(rows), stats['clr_lines'], stats['data_directive_lines']) == (30,22,0)
assert stats['call_lines'] == stats['return_lines'] == 0
assert data[0x10034:0x10038] == bytes(4)
assert all(r.mnemonic == 'clr' for r in disassemble(gnu, bytes(4), 0x10034))

# Typed-data hypothesis only; no semantics assigned to udfu01 6.
record_start, sentinel = 0x216e0c, 0x216e9c
assert copied(0x61f9eb6c) == record_start
assert (sentinel-record_start)//6 == 24 and data[sentinel:sentinel+2] == bytes(2)
for i, at in enumerate([0x216e84,0x216e8a,0x216e90,0x216e96]):
    assert struct.unpack_from('<H', data, at)[0] == 53+i
    assert list(data[at+2:at+6]) == [i+1,1,0,0]
assert u32(copied(0x61fa921c)) == 0  # initializer, not a live singleton observation
assert inspect(original) == info
print('23 windows, 19 direct edges, 3 conditional fields and countercontrols passed; input unchanged')
PY
```

## Bounded exploration and semantic limits

Final nominated windows are in the index. Earlier **context-only** bounds included startup `[0,0x380)`, existing control anchors `[0x10000,0x10088)`, `[0x186d8,0x18a00)`, `[0x100e7,0x101b0)`; transfer `[0x142e,0x1660)` and `[0xb87,0xda0)`; resolver `[0x750620,0x750820)`; capture backend2KiB from0x77138b, actor dispatch768bytes from0x78b3a5, executor512bytes from0x804812; custom backend1280bytes from0x807330. Adjacent linear output supplied boundaries only, not extra functions or imaging claims. Local copier's initial truncated context was corrected to `[0x12d3,0x135e)` before role attribution.

The existing four PC-relative forms from [T5](15-picturemode-and-schema-private-validation.md) were applied once to resolver0x75068f: **2258 raw encoding candidates**, not functions. Only80-byte contexts at0x74e534/0x74e589/0x7e24a7/0x7e2516 were screened, followed by the nominated identity bindings. Misaligned/data-like output was rejected. No full decode or general function discovery followed. Neither a valid name nor an encoded call alone proves active model functionality.

Field widths, startup transfers and local copy/fill loops require private manual inspection at the report's nominated sites. `walk()` stops at `setlb`/hardware loops and indirect control flow, follows no callees and does not establish arithmetic or memory semantics. **`udfu01 6` at0x28fb05 and `udfu01 20` in the storage path remain unsupported**; six-byte data shape is not proof of an executed stride. Conditional vtable checks validate initializer fields plus constructor-path assignments, not runtime object contents or real image processing. The unresolved executor virtual+20 target is the stop boundary.

Repository checks reuse the39 existing synthetic tests with upstream SquashFS tools (see [T1.1 validation](11-squashfs-private-validation.md)). They and CI validate tooling only. Also check `git diff --check`, JSON syntax, relative Markdown targets, and the public changed-file allowlist. Public outputs are original prose, selected numerical metadata and synthetic controls; private firmware, catalogs and proprietary assembly are excluded.

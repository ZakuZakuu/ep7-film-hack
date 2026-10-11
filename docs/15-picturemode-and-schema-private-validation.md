# T5 · Guarded caller, field and schema reproduction

2026-10-11 · [Issue #21](https://github.com/ZakuZakuu/ep7-film-hack/issues/21) · [Findings and stop decision](../research/e142-picturemode-producers-and-remote-controls.md). Run from the repository root, using the existing private original and GNU 2.44 from [T3](13-executable-private-validation.md). No downloader, client constructor, camera endpoint or firmware execution is involved. Keep every OEM byte and assembly transcript in **`/tmp/ep7-firmware/t5/`**, never in Git. The following snippets are original research procedures, not firmware implementation code.

## Exact-target calls and independent boundaries

The prefilter checks only four documented direct-call encodings and nominated destinations. It is **not an instruction decoder/code detector**. GNU supplies instruction interpretation; entry-derived code and actual pointer/field use provide the independent evidence. `call` register-save/frame bytes count toward length, but displacement is relative to instruction start. An indirect `calls (aN)` has no encoded destination and is deliberately not covered.

```bash
umask 077
mkdir -p /tmp/ep7-firmware/t5
python3 - <<'PY'
from pathlib import Path
import hashlib, json, struct
import xml.etree.ElementTree as ET
from tools.inspect_olympus_oe import inspect, check_expected, decode_chunk
from tools.probe_oe_executable import disassemble, walk

original = Path('/tmp/ep7-firmware/E142_EP7_firmware_download.BIN')
private = Path('/tmp/ep7-firmware/t5')
gnu = Path('/tmp/ep7-analysis-tools/binutils-build/binutils/objdump')
expected = '9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb'
base = 0x60020020
# Prefix, signed-displacement width, remaining register/frame-byte count.
forms = [('call16', b'\xcd', 2, 2), ('call32', b'\xdd', 4, 2),
         ('calls16', b'\xfa\xff', 2, 0), ('calls32', b'\xfc\xff', 4, 0)]

def candidates(data, target):
    assert 0 <= target < len(data) <= 64 * 1024 * 1024
    result = []
    for name, prefix, width, tail in forms:
        lo = max(0, target - 32767) if width == 2 else 0
        hi = min(len(data), target + 32769) if width == 2 else len(data)
        pos = data.find(prefix, lo, hi)
        length = len(prefix) + width + tail
        while pos >= 0:
            if pos + length <= len(data):
                at = pos + len(prefix)
                disp = int.from_bytes(data[at:at+width], 'little', signed=True)
                if (pos + disp) & 0xffffffff == target:
                    result.append((pos, name, length))
                    assert len(result) <= 64  # stop instead of broadening
            pos = data.find(prefix, pos + 1, hi)
    return sorted(result)

# Entirely synthetic; mature decoder first, before reading OEM content.
for name, prefix, width, tail in forms:
    source, target = (16, 0) if width == 2 else (0, 32)
    fixture = bytearray(64)
    encoding = prefix + (target-source).to_bytes(width, 'little', signed=True)
    encoding += bytes(tail)
    fixture[source:source+len(encoding)] = encoding
    assert candidates(fixture, target) == [(source, name, len(encoding))]
    row = disassemble(gnu, bytes(fixture[source:source+len(encoding)]), source)[0]
    assert row.mnemonic in {'call', 'calls'} and row.direct_target() == target
    assert not candidates(fixture, target + len(encoding))  # not PC-after
    # Same bytes can occur in data: the prefilter cannot classify their role.
    embedded_data = bytes(fixture)
    assert candidates(embedded_data, target) == [(source, name, len(encoding))]
print('four synthetic GNU call fixtures and counterchecks passed')

info = inspect(original)
check_expected(info, expected, 111017984)
assert info['block_count'] == 5
assert all(b['checksum_residual'] == '0x00000000' for b in info['blocks'])
block = info['blocks'][0]
with original.open('rb') as f:
    f.seek(block['payload_offset'])
    data = decode_chunk(f.read(block['payload_length']))
assert len(data) == 26214336
assert hashlib.sha256(data).hexdigest() == block['decoded_sha256'] == \
    '5dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190'

for target in [0x13c1f98, 0x2e4e75, 0x2e4e58, 0x301d16]:
    hits = candidates(data, target)
    for source, name, length in hits:
        row = disassemble(gnu, data[source:source+length], source)[0]
        assert row.mnemonic in {'call', 'calls'} and row.direct_target() == target
    print(json.dumps({'callee_offset': hex(target), 'candidate_count': len(hits),
                      'sources': [hex(p) for p, _, _ in hits] if len(hits)<4 else [],
                      'note': 'GNU candidate decode alone is not a function boundary'}))

# Only the selected entries; complete operands/assembly stay private.
windows = [(0x2e4e58, 0x2e4e75), (0x2e4e75, 0x2e56d5),
           (0x301d16, 0x301ef3), (0x3337cb, 0x333c97)]
decoded = {}
for start, end in windows:
    rows = disassemble(gnu, data[start:end], start)
    decoded[start] = {r.address: r for r in rows}
    transcript = private / f'{start:x}-private.asm'
    transcript.write_text('\n'.join(f'{r.address:x}: {r.mnemonic} {r.operands}'
                                    for r in rows) + '\n')
    transcript.chmod(0o600)
    print(json.dumps(walk(rows, start)))
assert decoded[0x2e4e75][0x2e50eb].direct_target() == 0x13c1f98
assert decoded[0x2e4e58][0x2e4e6d].direct_target() == 0x2e4e75
assert decoded[0x301d16][0x301e7b].direct_target() == 0x2e4e58
assert decoded[0x301d16][0x301e88].direct_target() == 0x3337cb

# Independently inspect only explicitly referenced table ranges.
boundaries = set(decoded[0x3337cb])
records = [struct.unpack_from('<II', data, p)
           for p in range(0x501a34, 0x501ab4, 8)]
assert len(records) == 16 and sum(k != 0 for k, _ in records) == 14
assert all(ptr-base in boundaries for _, ptr in records)
targets = [struct.unpack_from('<I', data, 0x501ab4 + 4*i)[0]-base
           for i in range(10)]
assert set(targets) == {0x333983, 0x33398e}
assert all(t in boundaries for t in targets)
print('16/16 keyed and 10/10 classifier table destinations are local boundaries')

for target in [0x13c1f98, 0x301d16]:
    needle = (base+target).to_bytes(4, 'little')
    hits, pos = [], data.find(needle)
    while pos >= 0:
        hits.append(pos)
        assert len(hits) <= 64
        pos = data.find(needle, pos+1)
    print(json.dumps({'literal_target_offset': hex(target),
                      'u32_match_offsets': [hex(p) for p in hits]}))

# Fixed known schema, not another discovery scan or client call.
xml = data[0xec5a28:0xec5a28+8011]
assert hashlib.sha256(xml).hexdigest() == \
    '132cd8eda1c71a26089eb078b70c3b3c44b5745e39cb7f687af9b87b478fc529'
root = ET.fromstring(xml)
assert root.tag == 'oishare'
assert root.findtext('version') == '4.50' and root.findtext('oitrackversion') == '3.10'
assert not root.findall('.//enum') and not root.findall('.//value')
for name in ['get_camprop', 'set_camprop']:
    method = root.find(f"cgi[@name='{name}']/http_method")
    for action in method.findall("cmd1[@name='com']/param1"):
        names = [p.attrib['name'] for p in action.findall("cmd2[@name='propname']/param2")]
        print(json.dumps({'command': name, 'method': method.attrib['type'],
                          'action': action.attrib['name'], 'named_property_count': len(names),
                          'explicit_profile_or_picture_name': any(
                              any(w in p.lower() for w in ['profile','picture','color1','lut'])
                              for p in names)}))
assert inspect(original) == info
print('unchanged input and all guards passed')
PY
```

Expected call candidates: **0x13c1f98 → source0x2e50eb**, **0x2e4e75 → source0x2e4e6d**, wrapper0x2e4e58 **41 candidates**, producer0x301d16 **zero**. Expected absolute matches: diagnosticentry **zero**, producerentry **0x301ec9**, a self literal in the producer's already decoded instruction0x301ec7. Do not infer a caller from that word hit. XML property counts: GET desc33/get31/check0, POST set23. No enum values, profile identity, runtime capability or camera response is created by this script.

`walk()` stops at hardware-loop instructions: dispatcher **0x2e4e82**, producer **0x301d2d**, receiver's nonnull-path **0x3338fb**. The receiver walk can reach return0x333c94 along error paths, without traversing the successful copy/dispatch path. Its output must **not** be cited as whole-function reachability. Field/loop analysis and flag semantics require bounded private manual review at the exact instruction coordinates in the report. The script validates references/bounds rather than pretending to execute that logic.

## Context budget and manual checks actually performed

- Caller initial context **[0x2e4f6b,0x2e52eb)**; one longer boundary context **[0x2e4000,0x2e5800)**; dispatcher re-decoded from0x2e4e75 to0x2e56d5.
- Wrapper candidates: fixed 36-byte preceding / 9-byte following GNU contexts only. Some arbitrary-start contexts can be misaligned; only the selected producer was traced, with boundary context **[0x301a00,0x301f00)** and final entry window **[0x301d16,0x301ef3)**.
- C receiver initial bound **[0x3337cb,0x3340cb)**; final semantic review restricted to **[0x3337cb,0x333c97)**. Two direct literal-referenced tables, **128+40 bytes**, only. No downstream hand-off bodies investigated.
- Direct literal labels were checked only at their nominated locations, without scanning for names or giving an acronym an imaging meaning.
- Source widths and destinations were manually checked from saved-source-pointer arithmetic, not guessed from strings: source+16/+17/+18 → temporary+8/+9/+0xa → copied fields → key/context branch use.
- These four PC-relative forms plus one static absolute-word representation are the declared hypothesis. Zero matches do not exclude indirect calls, indexed dispatch, relocation, alternate mappings or other components. No second representation was invented to force an upstream producer.

## Community controls: source review only

Use pinned sources linked in the report, **not executable camera examples**. The existing ignored olympus-wifi checkout is commit364dfcd1d8b12ead9d27dd9837463976e2a068fe. Ruby source/README/MIT license, generated PEN-F/E-M1II docs, parser and public PEN-F fixture were fetched at47d2341785ddfde8da6d363c57924d3fe094667e into ignored `work/t5/olympus-camera/`. The public PEN-F XML declares Shift-JIS; ElementTree does not support that byte declaration directly, so its ASCII-compatible text was parsed as decoded text, yielding interface2.60. That public fixture is not an E-P7 OEM sample or a runtime response captured here.

No client constructor, property helper, `cgi_request`, mode switch or device request was executed. A Python module import check failed because `requests` was absent; no dependency installation was necessary for the stdlib schema work. Python source shows single-value XML POST, enum validation and hidden rec/play/live-view side effects; Ruby generic POST uses form data. These differences are reasons to require E-P7 response/body evidence before any proposed device tool, not evidence of a working setter/importer.

## Repository verification

```bash
SQUASHFS_TOOLS_DIR="$PWD/work/squashfs-upstream/source/squashfs-tools" \
  python3 -m unittest discover -s tests -v
git diff --check
```

**39 existing tests / 0 skipped**; no new runtime feature or dependency. The inline procedure's four synthetic GNU fixtures/counterchecks, real numeric references, tables, XML and before/after guards also passed. Local Markdown targets and changed-file allowlist were checked. OEM assembly and decoded data remain private; public commit contains Markdown only. CI never receives the OEM sample or private output.

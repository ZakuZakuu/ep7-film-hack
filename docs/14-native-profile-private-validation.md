# T4 native profile references: guarded private reproduction

2026-10-11 · [Result and stop decision](../research/e142-native-profile-chain.md) · [Issue #18](https://github.com/ZakuZakuu/ep7-film-hack/issues/18). All OEM input, temporary bytes and transcripts stay **outside Git under `/tmp/ep7-firmware/`**. No firmware execution, downloader, serial/environment dump, camera request, replacement package or live-device claim. Reuse GNU 2.44 built as in [T3](13-executable-private-validation.md); do not replace its decoder with an unverified decompiler module.

## Numeric-only reference reproduction

The new original [reference wrapper](../tools/probe_oe_references.py) reuses `inspect_olympus_oe.py` and `probe_oe_executable.py`. It checks full size/hash/all OE checksums, selected decoded hash and unchanged input. At most **two explicit target offsets**, 64 word matches per target, eight nominated immediate sources and a **128-KiB maximum** external-GNU window. A match searches all byte alignments but only the supplied little-endian u32 value; no labels/magic discovery. A nominated MOV must have both the expected decoded literal and its u32 bytes within the same decoded instruction. **Neither word hits nor MOV confirmation alone establish code/target semantics.** Stdout exports selected numeric metadata, never operands, strings, assembly or payload bytes. External GNU text remains in memory/private temporary files, which the existing wrapper deletes.

Actual commands (three successful runs, not network retries):

```bash
umask 077
mkdir -p /tmp/ep7-firmware/t4
probe=(python3 tools/probe_oe_references.py
  /tmp/ep7-firmware/E142_EP7_firmware_download.BIN
  --expected-size 111017984
  --expected-sha256 9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb
  --block-index 0 --mapping-base 0x60020020)
gnu=(--objdump /tmp/ep7-analysis-tools/binutils-build/binutils/objdump)
"${probe[@]}" --target-offset 0xa50288 --target-offset 0x13f9f2a \
  "${gnu[@]}" --start 0x13be62f --length 0x317 --literal-source 0x13be7c4 \
  > /tmp/ep7-firmware/t4/profile-refs-movie.json
"${probe[@]}" --target-offset 0x13faf33 \
  "${gnu[@]}" --start 0x13c1f98 --length 0x1e7 --literal-source 0x13c1fa6 \
  > /tmp/ep7-firmware/t4/profile-refs-create.json
"${probe[@]}" --target-offset 0x21f8a4 --target-offset 0x21fa08 \
  > /tmp/ep7-firmware/t4/profile-refs-table.json
```

Expected matches: first run **0xa50288 → 0x21fa08**, **0x13f9f2a → 0x13be7c6**, confirmed immediate **0x13be7c4**; second **0x13faf33 → 0x13bfa8e / 0x13c1fa8**, confirmed immediate **0x13c1fa6**; final two target addresses have **zero** matches. The last negative excludes only exact literal pointer representation under this alias, not all indexed/relocated references.

## Seed, pointer-run and entry-walk audit

This is the guarded equivalent of the private seed/pointer/entry checks used here, using the existing decoder, not an ISA interpreter. It outputs only canonical labels provided by the researcher, coordinates and reachability. Private assembly is written solely for local semantic review. Do not upload these private files or substitute them for the sanitized report.

```bash
python3 - <<'PY'
from pathlib import Path
import hashlib, json, struct
from tools.inspect_olympus_oe import inspect, check_expected, decode_chunk
from tools.probe_oe_executable import disassemble, walk

original = Path('/tmp/ep7-firmware/E142_EP7_firmware_download.BIN')
private = Path('/tmp/ep7-firmware/t4')
tool = Path('/tmp/ep7-analysis-tools/binutils-build/binutils/objdump')
info = inspect(original)
check_expected(info, '9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb', 111017984)
block = info['blocks'][0]
with original.open('rb') as f:
    f.seek(block['payload_offset'])
    data = decode_chunk(f.read(block['payload_length']))
assert hashlib.sha256(data).hexdigest() == block['decoded_sha256']

# One canonical discovery pass only. Do not broaden it after a negative.
for label in ['COLOR1', 'Picture Mode', 'PictureMode', 'ColorProfile']:
    for encoding in ['ascii', 'utf-16-le']:
        needle, hits, at = label.encode(encoding), [], 0
        while (at := data.find(needle, at)) >= 0:
            hits.append(at)
            at += 1
        print(json.dumps({'canonical_label': label, 'encoding': encoding,
                          'count': len(hits), 'first_offsets': hits[:6]}))

# Follow only the H1 anchor's contiguous pointer predicate, maximum +/-8 KiB.
base, anchor = 0x60020020, 0x21fa08
def string_pointer(at):
    offset = struct.unpack_from('<I', data, at)[0] - base
    if not 0 <= offset < len(data):
        return False
    end = data.find(b'\0', offset, min(offset + 160, len(data)))
    return end > offset and all(32 <= b < 127 for b in data[offset:end])
lo = hi = anchor
while lo > anchor - 8192 and string_pointer(lo - 4):
    lo -= 4
while hi < anchor + 8192 and string_pointer(hi + 4):
    hi += 4
print(json.dumps({'predicate_start': lo, 'predicate_end': hi + 4,
                  'anchor_index': (anchor-lo)//4, 'entries': (hi-lo)//4+1,
                  'capped': lo == anchor-8192 or hi == anchor+8192}))

# Entry-derived bounds and real direct-callee windows; no callee execution.
for start, length in [(0x13be62f, 0x317), (0x2e9e99, 0x6f),
                      (0x13c1f98, 0x1e7), (0x261d, 0x90), (0x2762, 0x80)]:
    rows = disassemble(tool, data[start:start+length], start)
    transcript = private / f'{start:x}-private.asm'
    transcript.write_text('\n'.join(f'{r.address:x}: {r.mnemonic} {r.operands}'
                                    for r in rows) + '\n')
    transcript.chmod(0o600)
    print(json.dumps(walk(rows, start)))
assert inspect(original) == info
PY
```

Expected pointer predicate **`[0x21f8a4,0x221078)`**, 1,525 entries, index89, uncapped. This is not proof of a registry boundary. Expected primary walks: **214 → return0x13be943**, **36 → return0x2e9f05**, **112 → return0x13c217c**. `walk()` does not follow callees, emulate `udfu01`, or prove data flow; only selected calls (up to eight) are returned. Complete fields/call semantics require bounded private inspection, with limitations recorded in the memo.

Boundary context examined separately: **#0 `[0x13bd000,0x13c3000)`**, 24 KiB; nearby context around 0x13be7c4/0x13bfa8c and the 0x261d/0x2762 callees. H1's forced local decode was **`[0x21f9c0,0x21fb20)`**, rejected as array data; words within 64 bytes of the predicate boundaries were inspected without extending the run. No 0x13c1f98 direct caller was seen in the 24-KiB context. Arbitrary starting offsets can begin inside an instruction; the primary reported walks were re-decoded from entry-derived starts, ending after their returns.

Actual-VMA control: write only the guarded slice **`[0x13be62f,0x13be67f)`** to a 0600 private temporary window, then run GNU with `-D -z -b binary -m mn10300 -EL --no-show-raw-insn --adjust-vma=0x613de64f`. The call at candidate address **0x613de684** targets **0x47001052**. Delete the temporary bytes; retain a transcript only privately if needed. The payload-coordinate decode's **0xe6fe1032** is a wrapped result, not an in-payload callee. Exact external component/function and boot-ROM attribution remain unknown.

Family countercheck performed with `mn10300` / `am33` / `am33-2` on **`[0x2e9e99,0x2e9f08)`** and **`[0x13be62f,0x13be67f)`**: outputs identical. [GNU opcode source](https://sourceware.org/git/?p=binutils-gdb.git;a=blob;f=opcodes/m10300-opc.c;hb=binutils-2_44) gives an `udfu01` representation, not an E-P7-specific meaning. Do not infer multiplication/980-byte stride or choose a new CPU merely to make this expression fit.

## GR method source audit

Read-only public-source review pinned to **`549591db6ee7809fa7617c3637296ddc79b34f59`**:

- [README](https://github.com/DoYitNow/gr-custom-tool/blob/549591db6ee7809fa7617c3637296ddc79b34f59/README.md) and [author/license scope](https://github.com/DoYitNow/gr-custom-tool/blob/549591db6ee7809fa7617c3637296ddc79b34f59/AUTHOR_STATEMENT.md): GR4 `1.11.10.x` container scope versus recognized `1.11.10.7` resource backend; GPL-2.0-only author source, exceptions; public device-validation disclaimer.
- [firmware.py](https://github.com/DoYitNow/gr-custom-tool/blob/549591db6ee7809fa7617c3637296ddc79b34f59/gr4_editor/firmware.py), `_Memory`: bounds, actual address-pair instructions, static/RAM translation distinction; camera UserData unavailable from container.
- [filter_reader.py](https://github.com/DoYitNow/gr-custom-tool/blob/549591db6ee7809fa7617c3637296ddc79b34f59/gr4_editor/filter_reader.py), `_native_lookup`, `_read_parameters`, `_color_resources`, identity readback: unsupported instructions/default getters are explicit unknowns; style→profile→descriptor vs menu/text identities.
- [slots.py](https://github.com/DoYitNow/gr-custom-tool/blob/549591db6ee7809fa7617c3637296ddc79b34f59/gr4_editor/slots.py), getter/setter/default declarations and snapshot/save/load/reset routes: native lifecycle evidence is distinct from resource fitting. Source claims are not our GR4 device verification.
- [matrix codec](https://github.com/DoYitNow/gr-custom-tool/blob/549591db6ee7809fa7617c3637296ddc79b34f59/gr4_editor/codec/gr4_color_matrix_codec.py), [gamma codec](https://github.com/DoYitNow/gr-custom-tool/blob/549591db6ee7809fa7617c3637296ddc79b34f59/gr4_editor/codec/gr4_gamma_codec.py), [registry_resources.py](https://github.com/DoYitNow/gr-custom-tool/blob/549591db6ee7809fa7617c3637296ddc79b34f59/gr4_editor/registry_resources.py): examined as GR-specific method context only, not transferred to E-P7.

No source was imported, executed or vendored; no bundled DNG/photo download, editor, compiler or modified-file generation. GR method is useful precedent, not proof of E-P7 matrix/gamma layout, arbitrary-LUT capability, live preview or installation/recovery.

## Synthetic verification

```bash
SQUASHFS_TOOLS_DIR="$PWD/work/squashfs-upstream/source/squashfs-tools" \
  python3 -m unittest discover -s tests -v
```

**39 tests / 0 skipped** locally. New cases cover unaligned data hits, wrong alias, out-of-payload/u32 overflow, bounded repeated/overlapping hits, a signed MOV with a separately located false word, invalid instruction boundary/register operand, hash failure before GNU, changed-input rejection and output redaction. Fixtures are entirely original/synthetic. CI uses no OEM sample or GNU dependency for these unit tests. Tests prove metadata/guard behavior, not COLOR processing, persistent camera settings or import success.

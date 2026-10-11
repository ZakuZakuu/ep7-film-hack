# T3 executable analysis: private, read-only reproduction

2026-10-11 · Source of truth: [executable-map memo](../research/e142-executable-map.md). Run locally with the already authorized E-P7 sample; no downloader/serial is needed. Never execute OEM code, publish temporary windows/transcripts, infer camera installation from this result, or place OEM files in CI.

## Tool provenance and reuse decision

| Tool/source actually inspected | Version/hash/license | Use and limits |
| --- | --- | --- |
| [GNU official archive](https://ftp.gnu.org/gnu/binutils/binutils-2.44.tar.xz), existing `opcodes/m10300-dis.c` / `m10300-opc.c` | **2.44**, archive SHA **`ce2017e059d63e67ddb9240e9d4ec49c2893605035cd60e92ad53177f4377237`**; decoder/opcode file hashes **`0a7223538629ed43191fe527bd7d3ac09f658aa9dbcb2bae23a511023abbce2b`** / **`1e1150db856998de8366870394297e37d51db464164190e6ed0f988b44910796`**; source headers GPL-3.0-or-later | External executable only, no GPL source copied/linked into MIT wrapper. [objdump documentation](https://sourceware.org/binutils/docs/binutils/objdump.html): raw-binary target, explicit machine/endian and VMA adjustment; these settings do not autodetect an ISA |
| [Official Ghidra release](https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_11.4.2_build), [processor catalog](https://github.com/NationalSecurityAgency/ghidra/tree/Ghidra_11.4.2_build/Ghidra/Processors) | **11.4.2**, zip SHA **`795a02076af16257bd6f3f4736c4fc152ce9ff1f95df35cd47e2adc086e037a6`** matched release API digest; root Apache-2.0, dependencies have separate licenses | Installed catalog inspected: 57 distinct processor names, no MN103/AM33 language. No OEM Ghidra import/analysis and no decompiler result claimed |
| [GhidraMn10300](https://github.com/txt231/GhidraMn10300/tree/f89c1f469f07df31afea5dbf9e7c9057deba7b4a) | **f89c1f469f07df31afea5dbf9e7c9057deba7b4a**; README warns incomplete/stubbed semantics, unsure accuracy, no root LICENSE | README/API reviewed only; not downloaded, run or vendored. Accuracy and licensing do not qualify it as an authoritative decoder here |
| [Capstone](https://github.com/capstone-engine/capstone/tree/5.0.6) | Python **5.0.6**, distribution LICENSE.TXT BSD-3-Clause | External decoder for bounded competing ARM interpretations only; no code copied. No long ISA hunt or attribution from decode percentage |
| [DVXuser original Olympus thread](https://www.dvxuser.com/threads/e-p1-e-p2-e-pl1-hack-research.217453/) | E-P1/E-P2/E-PL1, 2010, author/community-reported MN103/IDA; reuse license of attachments unverified | Read only. No attachment run, old-model address copied or old OS guess treated as E-P7 evidence |

Public archives were fetched once with TLS verification. The GNU archive hash is a locally measured source identity, not a claimed independent signature verification. Public source/build caches and proprietary transcripts were not committed.

## Build the mature decoder

These match the actual configure/build choices. Requires a C build toolchain; no cross compiler, new processor module, emulator or firmware packer is developed. `MAKEINFO=true` omits documentation rebuilding, not the decoder.

```bash
umask 077
mkdir -p /tmp/ep7-analysis-tools/binutils-source /tmp/ep7-analysis-tools/binutils-build
curl --fail --location --max-time 90 --silent --show-error \
  https://ftp.gnu.org/gnu/binutils/binutils-2.44.tar.xz \
  --output /tmp/binutils-2.44.tar.xz
printf '%s  %s\n' ce2017e059d63e67ddb9240e9d4ec49c2893605035cd60e92ad53177f4377237 \
  /tmp/binutils-2.44.tar.xz | sha256sum -c -
tar -xf /tmp/binutils-2.44.tar.xz \
  -C /tmp/ep7-analysis-tools/binutils-source --strip-components=1
cd /tmp/ep7-analysis-tools/binutils-build
/tmp/ep7-analysis-tools/binutils-source/configure --target=mn10300-elf \
  --disable-nls --disable-werror --disable-gdb --disable-gdbserver \
  --disable-gprofng --disable-gas --disable-ld --disable-gold --without-debuginfod
make -j4 MAKEINFO=true all-binutils
./binutils/objdump --version
```

Stop on a download/hash/build failure; do not silently substitute a different tool snapshot. The successful local decoder reports `GNU objdump (GNU Binutils) 2.44`; its supported machine selection is **`mn10300`**, or **`am33` / `am33-2`**, not `mn10300:am33-2` (that spelling was rejected during setup).

## Guarded actual sample analysis

Return to the repository root. The wrapper validates the full file and OE checksums, verifies the selected full decoded payload hash, invokes GNU on a **private temporary window at most 128 KiB**, and revalidates input after analysis. It deletes the window; GNU text stays in memory, stdout contains numeric metadata only. It never executes firmware or outputs a replacement image. Scope/architecture is a caller-supplied hypothesis, not auto-detection; function walks follow direct branches without following callees or guessing indirect targets, stop at unmodeled hardware-loop/trap control, and cap at 1,024 visited instructions.

```bash
umask 077
mkdir -p /tmp/ep7-firmware/t3
probe=(python3 tools/probe_oe_executable.py
  /tmp/ep7-firmware/E142_EP7_firmware_download.BIN
  --expected-size 111017984
  --expected-sha256 9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb
  --objdump /tmp/ep7-analysis-tools/binutils-build/binutils/objdump)
pointers=(--pointer-source 0xb6 --pointer-source 0x6c --pointer-source 0x75
  --pointer-source 0x7e --pointer-source 0x87 --pointer-source 0x90
  --pointer-source 0x99 --pointer-source 0xa2)
"${probe[@]}" --block-index 0 --start 0 --length 0x20000 \
  --entry 0 --entry 0xbe --entry 0xc9 --mapping-base 0x60020020 "${pointers[@]}" \
  > /tmp/ep7-firmware/t3/block0-metadata.json
"${probe[@]}" --block-index 0 --start 0 --length 0x20000 \
  --mapping-base 0x60020000 "${pointers[@]}" \
  > /tmp/ep7-firmware/t3/block0-wrong-base.json
"${probe[@]}" --block-index 0 --start 0 --length 0x20000 \
  --mapping-base 0x406a0000 "${pointers[@]}" \
  > /tmp/ep7-firmware/t3/block0-header-base.json
"${probe[@]}" --block-index 3 --start 0x404 --length 0x73fc --entry 0x4a3 \
  > /tmp/ep7-firmware/t3/block3-metadata.json
```

Expected primary metadata: startup walk 44 instructions, five direct calls, unresolved indirect transfer at 0xbc; A/B walks 4/5 instructions with returns 0xc7/0xd7. Pointer boundary matches are 8/8 versus 4/8 versus 0/8; branch matches 6/6 versus 2/6 versus 0/6. #3 entry 0x4a3 reaches return 0x512 in 31 visited instructions; calls outside its window are not claimed resolved. All offsets are payload-relative. Never publish the complete private metadata/transcripts as a substitute for selected evidence.

For the family comparison performed here, the existing GNU decoder was separately invoked with `-D -b binary -m mn10300` / `am33` / `am33-2`, `-EL --no-show-raw-insn --start-address=0 --stop-address=0x3800` on the privately decoded #0. The three outputs were identical: 5,099 instruction lines. Unlike the wrapper, the manual larger-private-file run can read the last instruction beyond the nominal stop; no function boundary is inferred from that arbitrary stop.

Independent ARM countercheck recipe: from the same guarded decoded payloads, use `Cs(CS_ARCH_ARM, mode).disasm(data[offset:offset+4096], offset)` without skip-data, for ARM-LE, Thumb-LE and ARM-BE. Starts: #0 0, #2 0x800, #3 0x404. Sum instruction sizes until the first invalid instruction. Expected byte totals: **0/14/44**, **68/4096/84**, **20/38/0** respectively. Do not publish instructions/operands; the 100% Thumb decode is explicitly rejected as code evidence.

The fixed known XML slice was read **only** at #0 offset 0xec5a28, length 8011; `xml.etree.ElementTree.fromstring(slice)` succeeds with root `oishare`. Prior anchors 0xec6cbb/0xec7105/0xec74d6 lie inside this range, 0xed9876 outside. No new text discovery is performed.

## Synthetic verification and limits

```bash
SQUASHFS_TOOLS_DIR="$PWD/work/squashfs-upstream/source/squashfs-tools" \
  python3 -m unittest discover -s tests -v
python3 - <<'PY'
from pathlib import Path
from tools.probe_oe_executable import disassemble, walk
# Original synthetic two-function fixture; no OEM bytes taken as a fixture.
rows = disassemble(Path('/tmp/ep7-analysis-tools/binutils-build/binutils/objdump'),
                   bytes.fromhex('fa ff 08 00 f0 fc cb cb f0 fc'), 0)
assert walk(rows, 0)['return_offsets'] == [4]
assert walk(rows, 0)['direct_calls'][0]['target'] == 8
assert walk(rows, 8)['return_offsets'] == [8]
PY
```

**32 tests / 0 skipped** locally, plus this real-GNU synthetic integration. Unit tests need no OEM sample/GNU tool; CI continues using only synthetic inputs. The repository's existing squashfs-tools build supplied the LZO integration. Hash/bounds, signed literal handling, off-by-header mapping, branch/indirect limits and failure-output redaction have synthetic counterexamples. These tests validate metadata handling, not an ART function, a boot process or installation acceptance.

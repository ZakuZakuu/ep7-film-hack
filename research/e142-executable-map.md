# T3 · E-P7 executable map: real MN103 code, ART ownership still unknown

2026-10-11 · [Issue #15](https://github.com/ZakuZakuu/ep7-film-hack/issues/15) · latest main baseline **`bf296e8309a5fd102e500a42deea8c27e15660d7`** (includes merged PR #14). E-P7, **owner-reported v1.1**; privately retained original **111017984 bytes / SHA-256 `9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`**. Full input hash/size, all five OE checksums, selected decoded hashes and unchanged input were checked again. No download, serial use, OEM execution, camera communication or firmware modification.

**Result: positive executable-substrate evidence.** Block #0 contains coherent **32-bit little-endian MN10300-family** startup/control code and real call/return relationships. Its references strongly support a **static execution-address hypothesis of `A = 0x60020020 + decoded_payload_offset`** in the tested region. This is enough to justify another bounded caller-analysis task; it does **not** identify an ART algorithm, the exact CPU/AM33 variant, the full imaging executable, an OS, or an observed hardware runtime address. G2 remains unknown; G4/G5 remain NO-GO.

## Bounded map and classification

All intervals are half-open. **File offset != decoded payload offset != runtime address.** OE permutes bytes inside 16-byte lanes; adding a payload offset to the encoded file position is not a byte-for-byte translation.

| Block / exact examination scope | File correspondence | Classification and confidence |
| --- | --- | --- |
| #0: GNU region `[0, 0x20000)` | Encoded lane range `[0x20, 0x20020)`; decoded block SHA `5dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190` | **verified code at named control-flow anchors below**, plus data/padding elsewhere. Strong main-program candidate from startup/handler setup and transfer into another entry; not proof this entire block is executable or owns image processing |
| #2: prefix `[0, 0x800)`, data test `[0x800, 0x1800)` | Encoded payload starts at file `0x03200020` | **verified structural data**: 9 outer and 40 inner contiguous nonzero 16-byte address/length/reserved records before zero records; reserved words zero, ranges fit under header-base translation and do not overlap. The first pointed-to data is **not established code**. Existing ARM ELF/SquashFS evidence elsewhere in this block is retained, not extrapolated |
| #3: GNU region `[0x404, 0x7800)`; prefix `[0, 0x404)` examined separately | Encoded payload starts `0x05d20020`; covering lanes `[0x05d20420, 0x05d27820)`; decoded SHA `00f47b0990257a9719109b8d41a1910677615c6e1622b3ca43061d6fabc8805f` | **verified MN103-family code** following a descriptor and a marker at 0x400. A caller at 0x411 reaches 0x4a3, whose bounded walk reaches return 0x512. Component role, CPU instance and execution base **unknown**; do not call it the ISP/IBIS firmware |

These are two GNU candidate regions, not whole-firmware disassembly. #1/#4 were not reopened. No new JPEG, generic string, resource magic, entropy or speculative compression scans.

## Why MN103, and why GNU instead of forcing Ghidra

The [historical Olympus community analysis](https://www.dvxuser.com/threads/e-p1-e-p2-e-pl1-hack-research.217453/) supplies a **community-reported MN103 hypothesis**, including old-model address ambiguity. None of its E-P1 addresses or OS guesses were imported. The [OE decoder](../tools/inspect_olympus_oe.py) and its [real E-P7 validation](e142-first-sample-analysis.md) were reused unchanged.

Ghidra **11.4.2** was evaluated first: the official release archive matches its published SHA-256, but the installed language definitions contain **no MN103/AM33 processor**. [txt231/GhidraMn10300 at f89c1f4](https://github.com/txt231/GhidraMn10300/tree/f89c1f469f07df31afea5dbf9e7c9057deba7b4a) declares unfinished/stubbed semantics and uncertain accuracy, has no root LICENSE, and discusses unclear GPL status. It was **not installed, executed or vendored**. No Ghidra decompilation claimed. Reused **GNU binutils 2.44's existing MN103 decoder** as the mature alternative; only an original metadata wrapper was added. Exact sources, license review and commands: [private reproduction](../docs/13-executable-private-validation.md).

Independent checks, not a decode-rate assertion:

- GNU base MN10300, AM33 and AM33-2 decode the initial `[0, 0x3800)` identically (5,099 instruction lines, zero data directives). Thus this sample region supports the **base family**, not a particular extended CPU. Startup stack adjustments, five direct calls, two bounded return bodies and the indirect transfer are mutually consistent.
- At #0 offset 0, Capstone 5.0.6 ARM-LE rejects the first instruction; Thumb-LE stops after 14 bytes, ARM-BE after 44. At #3's actual code seed 0x404, corresponding lengths are 20/38/0. These reject these **entry interpretations**, not all ARM code elsewhere.
- Counterexample: #2 at 0x800 decodes all 4,096 bytes as Thumb (2,048 instructions, **zero call mnemonics**), despite the data-table context and no demonstrated entry/caller/return relationship. It is **not classified as code**. Likewise GNU decodes FF padding as breaks and zero bytes as clears; the #0 sweep's 90,812 lines include 32,202 breaks and 21,148 clears. The full window is not a “90k-instruction program.”

## Concrete functions and address consistency

Neutral names A/B below are analyst labels, not recovered symbols. These are numeric structural findings; no OEM instruction text, binary bytes or decompilation is published.

| Relationship in block #0 (payload-relative) | Independent consistency | Candidate execution addresses under the supported translation |
| --- | --- | --- |
| Call at **0x9 → B 0xc9** | B has five reachable instructions and return at **0xd7**; no unresolved flow in that small body | **0x60020029 → 0x600200e9**, return **0x600200f7** |
| Call at **0x15 → A 0xbe** | A has four reachable instructions and return at **0xc7**; no unresolved flow | **0x60020035 → 0x600200de**, return **0x600200e7** |
| Calls **0x39 / 0x54 → 0x44d**, **0x62 → 0x355f** | All three destinations are independently decoded instruction boundaries; callee semantics not assigned | Numeric translation only; these are not ART functions |
| Immediate at **0xb6**, then indirect transfer at **0xbc** | Value **0x600200f9** maps to the register-save/prologue entry **0xd9** with base +0x20; without +0x20 it lands at **0xf9**, inside another instruction | Strong independent support for **payload base 0x60020020** |
| Seven setup constants at **0x6c/0x75/0x7e/0x87/0x90/0x99/0xa2** | **0x60030020** maps to entry 0x10000; **0x60030058/60/68/70/78/80** map to six 8-byte-spaced branch stubs 0x10038…0x10060, all pointing to **0x186d8** | Handler-like setup corroborates the same translation; stores are **halfword**, not a proven full-width vector-pointer table |

| Tested translation base | Named immediate values landing at boundaries | Six branch-stub constants landing on direct branches | Interpretation |
| --- | ---: | ---: | --- |
| **0x60020020** | **8/8** | **6/6** | Strongly supported static execution alias for tested #0 code |
| 0x60020000 | 4/8 | 2/6 | Entry jump lands inside an instruction; off-by-header interpretation rejected |
| OE header candidate 0x406a0000 | 0/8 | 0/6 | Not the execution mapping for these references; could describe a storage/load coordinate, but its semantics remain unverified |

No bootloader copy sequence or device memory map was recovered. The inferred image-header origin 0x60020000 is not the payload start; neither is a measured physical RAM/flash location. The translation is not automatically applicable to later constants, other blocks, overlays or separately relocated code. PC-relative calls remain valid evidence even independently of this base.

**2026-10-12 T7 address-scope update:** [system-boundary research](e142-system-boundary-map.md) adds startup-backed copied-data and helper execution views to #0. The0x60020020 alias remains supported at the tested main-code anchors; it is not a uniform map for every data/helper byte or a physical memory map. Former external helpers0x47001052/0x4700115e are now located in a boot-relocated6-KiB span. This does not identify the processor chip or imaging owner.

## ART boundary, decision and next minimum experiment

The exact known slice #0 **`[0xec5a28, 0xec5a28+8011)`** was validated with the standard XML parser: root `oishare`. **Three** prior BleachBypass anchors are inside that valid interface-description XML; the fourth is outside it. No rescanning for names or publishing XML. This confirms the warning in Issue #15 and supersedes any interpretation of those three names as processing-code leads. The fourth property-name occurrence still has no demonstrated processing caller. The T2 aligned-word negative result also never tested MN103 variable-length instruction operands at the newly supported execution alias.

**Continue one scoped offline code investigation; pause patch/installation engineering.** The current blocker for G2 is a real **filter selector → consumer → parameters/software/ISP command** relationship. This task removes the “no executable substrate” obstacle; it does not resolve G2. Old/paired OEM firmware is optional, not a prerequisite for this route.

Next minimum experiment: take **one already bounded, unassigned property-name anchor (#0 0xed9869)** from T2, not a fabricated ART ID/table. First test whether the supported execution translation extends to that data coordinate, then verify its expected address operand in a bounded GNU code window and identify the enclosing function/consumer. This is a reference experiment, not another search for names. Reject any chain ending at `oishare` serialization/menu formatting. Only a real selector→parameters/software/ISP-consumer relationship would support processing ownership; stop after two bounded, evidence-based reference representations without progress. No new ISA guessing, decompiler-derived algorithm claim, device I/O or package output. A trustworthy licensed MN103 Ghidra language would improve later navigation, but is not necessary to continue with GNU.

Validation: **32 synthetic tests passed, 0 skipped** (including existing upstream LZO integration); a separate original 10-byte MN103 synthetic call/return fixture decoded correctly with the real GNU tool. CLI guards, both mapping counterexamples, XML boundaries, before/after original hashes and `git diff --check` passed. Private OEM artifacts/transcripts remain under `/tmp/ep7-firmware/t3`, excluded from Git and CI. Public outputs are the [original wrapper](../tools/probe_oe_executable.py), [synthetic tests](../tests/test_probe_oe_executable.py), this memo and reproducibility notes.

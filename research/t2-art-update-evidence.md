# T2 evidence / reproducibility appendix

2026-10-11; decision memo: [ART and install feasibility](art-update-feasibility.md). Baseline `efed91b1d9aeb3315cf2b8c3b5d3b2771418b6f9`; PR #11/#12 already merged, not pending as described in the original issue snapshot. No implementation work or new parser was necessary.

## Primary sources and provenance

[Machine-readable public source audit](t2-source-audit.json) records exact response bytes/SHA-256 for successful shell reads; these are **document/source hashes, never firmware hashes**. Public pages/source cached only in ignored work/t2-sources. Some shell HTTP 403s had readable browser text; no successful download/hash claimed for those reads. No retries of blocked pages, third-party firmware mirrors, other people's serials, source requests to vendors or camera I/O.

| Source | Narrow finding / scope |
| --- | --- |
| [2018 Olympus release](https://www.olympus-global.com/news/2018/nr00715.html), [detailed PDF pp.1,2,4](https://www.olympus-global.com/news/2018/contents/nr00715/nr00715_00001.pdf) | 2018-02-28: E-M1 II 2.0 / PEN-F 3.0 / E-M5 II 4.0 add Bleach Bypass I/II; originally E-M10 III. OEM-delivered functionality, no published algorithm or third-party image acceptance. Separate Flat-video LUT is for DaVinci Resolve/BT.709 |
| [PEN-F support](https://learnandsupport.getolympus.com/support/pen-f), [manual p.182](https://learnandsupport.getolympus.com/sites/default/files/media/files/2018/03/PEN-F_ENU_02_FW3_0.pdf) | Version 2.1→3.0 adds ART; manual corroborates. PEN-F TruePic VII. Profile Load and Shading Editor are distinct new features, not arbitrary processing code |
| [E-M1 II original announcement](https://www.olympus-global.com/news/2016/nr161102em1mk2e.html) | TruePic VIII, same branding generation as E-P7; not equivalent firmware/ISA/trust mapping |
| [E-P7 FAQ](https://support.jp.omsystem.com/en/support/imsg/digicamera/qa/products/ep7/) | E-P7's 16 ART include Bleach Bypass; native COLOR/MONO each four profiles. No custom ART import proof |
| [FAQ 007489](https://digital-faq.jp.omsystem.com/faq/public/app/servlet/qadoc?QID=007489) | Updated 2026-09-25: E-P7/PEN-F not OI.Share Profile Library write destinations; E-P7 JPEG can be source. Applies to this documented function |
| [FAQ 007407](https://digital-faq.jp.omsystem.com/faq/public/app/servlet/qadoc?QID=007407) | Updated 2025-10-07: Workspace Profile Load destination OM-3/PEN-F 3.0+; E-P7 JPEG source supported, E-P7 destination not listed |
| [Current official update instructions](https://explore.omsystem.com/c/en/firmware-update-instructions) | Workspace/USB stock update; interrupted transfer/update can leave camera inoperable; prior version return not offered. No description of an E-P7 boot-failure recovery path |
| [DVXuser historical E-P1 discussion](https://www.dvxuser.com/threads/e-p1-e-p2-e-pl1-hack-research.217453/) | Reused prior review: author-reported E-P1 text modification/updater emulation. Not an E-P7 accepted-modified-image or independent rescue demonstration; source reuse license unconfirmed |
| [LightSnow historical page](https://lightsnowdev.blogspot.com/2014/09/olympus-om-d-e-m1-firmware-20.html) | Current browser fetch blocked by non-retryable redirect; search snippet refers to stock OEM E-M1 2.0. Not reviewed recovery/code evidence; no package downloaded |
| [db_link README](https://github.com/azqeurio/db_link) | Public camera-control/transfer claims with E-P7 “Tested” table but OM-1-based validation caveat, exact E-P7 firmware unreported; no firmware acceptance/rescue proof. “Library import” is not evidence of custom profile upload. Not relied on as ART/installation precedent |

## Public implementation precedent: EXIF, not firmware editing

Read ExifTool source at **`2200871d9cef988051d2a99d67df3bda6cbb30a8`**:

- [Olympus.pm](https://github.com/exiftool/exiftool/blob/2200871d9cef988051d2a99d67df3bda6cbb30a8/lib/Image/ExifTool/Olympus.pm), bytes 157893, SHA-256 `f974dc7c82b5e187148e0defc8d733734445df2121175097f001fe551ae08651`.
- `ArtFilter` at CameraSettings tag 0x0529, unsigned 16-bit values/count 4; public print-conversion table maps 42 → Bleach Bypass, 43 → Bleach Bypass II. This is an implemented photo-metadata decoder, not image processing. “Writable” here concerns EXIF tag editing, not camera firmware/API writes.
- [README license](https://github.com/exiftool/exiftool/blob/2200871d9cef988051d2a99d67df3bda6cbb30a8/README): Perl Artistic or GPL terms; SHA-256 `e13005e5431c89910feba2309710d844f1bf4fd97df1236284e6475161bc14da`. Read only; none copied/vendored. No E-P7 owner-shot JPEG was analyzed here; internal dispatch ID and camera-specific metadata mapping not verified.

Two bounded literature paths (OEM feature/version history; public community implementation/update evidence) did not supply paired legitimate old/new binaries, a TruePic VIII ART caller/table format, or model-specific E-P7 trust/recovery implementation. This is a scoped evidence gap, not proof nothing exists. No blind small-integer metadata-ID scan or crypto-magic search.

## Exactly two private ART probes

Input retained at `/tmp/ep7-firmware/E142_EP7_firmware_download.BIN`, E-P7 owner-reported 1.1, **111017984 bytes**, SHA-256 **`9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`**. `inspect/check_expected` before, decoded SHA consistency and `inspect` equality after each probe. All five additive residuals zero. Uses existing tools/inspect_olympus_oe.py, not a new ISA/parser.

**Probe 1 hypothesis:** officially present ART names yield bounded text anchors; does not assume code vs data. Predefined labels `Bleach Bypass`, `BLEACH BYPASS`, `BleachBypass`, `Pop Art`, `POP ART`; each encoded ASCII/UTF-16LE/UTF-16BE, exact case-sensitive byte matches in five decoded payloads.

| Block | Measured anchor metadata |
| --- | --- |
| #0 | BleachBypass/ASCII 4: payload offsets 0xec6cbb, 0xec7105, 0xec74d6, 0xed9876 |
| #1 | Bleach Bypass/UTF-16LE 54 (first 0x583246); Pop Art/UTF-16LE 80 |
| #2/#3/#4 | 0 matches for the predefined forms |

BE hits are corresponding LE starts minus one byte, an ASCII/zero-byte overlap; not 54+54 independent names or proof of BE strings. No record IDs/table/caller established. No raw strings besides the public predefined labels printed or published. Full offset list remains private.

**Probe 2 hypothesis:** a bounded #0 text anchor may have direct u32 references. For the four anchors, search preceding/following NUL within 256 bytes each; only last qualifies (string start 0xed9869, 25 bytes printable ASCII, not source-filename suffix). Other three lack both NUL boundaries in this window; no claim about their purpose or full strings. For **that single bounded candidate only**, search start and public-label substring offset 0xed9876 in five decoded payloads, using aligned LE/BE u32 words in two forms: payload-relative and plus unverified header-load-candidate 0x406a0000. **All eight target forms yield zero matches.** This is not a verified runtime address, pointer or absence of any indirect/relative references; no ISA guessing, disassembly or expansion after the result.

Private commands: read block payload from metadata payload_offset/payload_length, reuse decode_chunk; `data.find(label.encode(encoding))` with next search at previous+1 for probe 1. Probe 2 boundaries: `rfind(NUL, max(0, at-256), at)+1`, `find(NUL, at, at+256)`; require found left boundary strictly within window/right found; accept only printable ASCII. Exact-word search uses `(target+bias).to_bytes(4,endian)` and hit offset modulo4=0. Only metadata stored to `/tmp/ep7-firmware/t2/art-label-probe.json` and `art-string-references.json`. No decoded blobs, surrounding proprietary strings or code dump written.

Minimal private container reproduction (output metadata, never upload):

```bash
umask 077
mkdir -p /tmp/ep7-firmware/t2
python3 tools/inspect_olympus_oe.py \
  /tmp/ep7-firmware/E142_EP7_firmware_download.BIN --json \
  > /tmp/ep7-firmware/t2/container.json
```

The inspector command checks OE, not an OEM digital signature; assert full size/hash above before using it. Signing/checker/boot-stage acceptance cannot be established from this container result. No key/signature algorithm, downgrade permission, same-version install or boot-stage backup inferred. No modified package or physical-device test generated.

Validation: 26 existing synthetic tests passed / 0 skipped (including mature-tool LZO integration); original input checked unchanged, encoding-overlap assertions and local document links passed, git diff --check passed. Tests are repository regression only, not proof of ART or signing. No new tests that mirror speculative implementations, no OEM CI fixtures.

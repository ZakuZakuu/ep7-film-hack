# E-P7 T1.3 | Media-resource triage and firmware feasibility split

Date: 2026-10-11. Scope: new bounded read-only observations on the privately supplied E-P7 firmware; this is **not** a modified image, a firmware update, or proof of ART control.

## Input and reproducibility

- Owner-provided candidate: `E142_EP7_firmware_download.BIN` / vendor name `OLY_E_142_1100_0000_0000.BIN`, **111,017,984 bytes**, SHA-256 **`9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`**.
- The sample was read locally and decoded with the historical 16-byte Olympus OE XOR/permutation transformation already validated in [PR #6](https://github.com/ZakuZakuu/ep7-film-hack/pull/6). Only **block #4** and **block #0** were examined here; the source file was not modified.
- All offsets below are **decoded payload-relative** positions, not addresses in camera RAM/flash or program references. No extracted OEM assets are committed or displayed in the public repository.

## Finding A: the JPEG cluster looks like graphical backdrops, not color LUTs

The block-#4 T1.2 report records **221 JPEG SOI-like starts** at a regular residue of 480 modulo 512, of which two were independently validated. This pass intentionally examined **only the first 25** consecutive candidates, using in-memory standard Pillow JPEG decoding.

- **25/25** were successfully decoded as **640 × 480 RGB JPEG**.
- **25/25** satisfy per-pixel **R == G == B** for the entire decoded RGB image (not merely equal average channel intensity); all are grayscale artwork stored in RGB JPEG form.
- A private visual inspection of the first two shows a dark, soft gradient/vignette-like background; their decoded pixel values differ very little. Their raw JPEG sizes are 20,581 and 20,594 bytes; they are distinct compressed files. This could be a UI/background/effect-overlay family, but usage is **unidentified**.
- **No mapping to any ART mode, filter icon, processing table, live preview or shutter JPEG was found.** A backdrop-like JPEG asset is not a color transform, and the RGB/grayscale property argues against interpreting these particular images as a complete color lookup table.

**Status:** verified JPEG assets and image characteristics; *purpose and caller unknown*. Not sufficient evidence for UI customization *in camera* or ART editing.

## Finding B: valid-looking PCM WAVE header families, but not proven shutter sounds

A bounded read-only scan of decoded **block #0** found **59** occurrences of the `RIFF` signature. At least **31** satisfy a restrictive **44-byte standard PCM WAVE header** pattern:
`RIFF / WAVE / fmt (16-byte PCM) / data`; block alignment and byte rate agree with channels, bit depth and sample rate; the declared sizes fit within the decoded block.

- These 31 candidates span audio-format combinations such as **mono/stereo**, **8/16/24-bit PCM** and sample rates **8, 16, 32, 44.1 and 48 kHz**. This unusually systematic distribution is consistent with *example/test vectors or an audio-compatibility table*, but that role is a **hypothesis**.
- All **30 adjacent pairs** in the sorted list of these 31 candidates have overlapping *declared* RIFF file spans. Therefore they cannot currently be treated as 31 non-overlapping, independently validated audio-resource files simply because their headers look right.
- The scan did **not** establish playable audio asset boundaries, a sound ID, a user-interface reference, the shutter-sound caller or any installed-camera behavior. **Do not assert “custom shutter sound is now possible.”**

**Status:** verified PCM-like header records and structural overlap; audio asset role unknown. The current evidence supports further *short, targeted* code/reference investigation only.

## What cross-camera hacks establish—and do not establish

- [DVXuser 2010 Olympus E-P1/P2/PL1 firmware discussion](https://www.dvxuser.com/threads/e-p1-e-p2-e-pl1-hack-research.217453/) reports unpack/repack, a simulated camera updater and a successful modification of an E-P1 on-screen message. This is useful Olympus-specific precedent for historical device update and resource modification, **not a claim of E-P7 compatibility or signature acceptance**.
- [GR IV community report](https://www.reddit.com/r/ricohGR/comments/1wta8ru/wtfhas_the_firmware_of_the_ricoh_gr_iv_already/) claims shutdown-screen customization and custom firmware on Ricoh; [GR4-LUTSmith](https://github.com/lemonadesaltbagel/GR4-LUTSmith) shows LUT fitting to Ricoh's native parameters. These are *distinct mechanisms on a different camera* and cannot be transferred without model-specific evidence.
- [E-P7 official product page](https://explore.omsystem.com/c/en/e-p7) confirms 16 real-time previewable ART effects and TruePic VIII, **not** writable ART assets or a plugin loading mechanism.

## Feasibility decision: separate the two hard gates

| Necessary gate | Current evidence on this E-P7 | Decision |
| --- | --- | --- |
| **G2 — locate actual image processing/control** | JPEG graphical candidates, ambiguous WAVE headers, network SquashFS and working OE decoder; **no ART IDs/parameters/call sites** | **unknown / NO-GO for implementation** |
| **G4/G5 — build/verify modified update + safely recover** | Historical Olympus additive container checksum and author-reported E-P1 updating; **no E-P7 accepted-modified-image or recovery evidence** | **unknown / NO-GO for flashing** |
| Native Color Profile alternative | Official in-camera controls exist; no objective matching of desired negative-film look yet | **conditional**, not equivalent to arbitrary LUT |

**No practical E-P7 mod or flashing procedure can be inferred from the fact that the OEM file decodes.**

## Recommended next one-iteration research

1. **Mechanism A: image-style execution** — in a constrained, version-specific effort, identify a concrete ART identifier or processing-table/call-site relationship. Historical image/audio extraction is useful only if the assets have an identifiable caller; stop if no coherent cross-reference emerges.
2. **Mechanism B: update acceptance/recovery** — strictly offline evaluation of published Olympus updater/protocol research and any model-specific evidence for signature/trust validation and rescue/downgrade. An additive checksum is *not* a cryptographic signature. No camera I/O, local server substitution, fake update, firmware modification or install attempts without a separate device-safe plan and owner authorization.
3. **Milestone decision:** if both mechanisms cannot be meaningfully bounded, recommend pausing the invasive firmware route rather than escalating generic binary magic scanning. Optionally test OEM Color Profile limits with owner-approved non-invasive photo capture.

No new OEM file, derivative image, WAVE bytes or sensitive device values were committed. This note contains only aggregate counts, metadata, bounded observations and public references.

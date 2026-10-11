# E-P7 Firmware — first real-sample validation (2026-10-11)

**Status: validated outer OE container + historical data transformation; no modified firmware, ART location or device write.** This supersedes the earlier T0 G1 'no available sample' condition for this one received file, without proving OEM signing, safe flashing, or repeatable download from every environment.

## Provenance (metadata only)

- Source: E-P7 owner downloaded the candidate file from OM's vendor firmware service using the project's opt-in downloader, then provided the file for local read-only analysis. This repository contains **none of that firmware**.
- Vendor-reported filename: `OLY_E_142_1100_0000_0000.BIN`; local label was `E142_EP7_firmware_download.BIN`.
- Size: **111,017,984 bytes**; whole-file SHA-256: `9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb`.
- These are owner-supplied provenance and our measured structure/checksum, not an independent OEM signature validation; no serial number was disclosed or archived.

## Five contiguous OE blocks; checksum verified on decoded data

| # | File offset | Encoded payload bytes | Model raw | Version raw | Block ID raw | Load-offset candidate | Checksum |
|---:|---|---:|---|---|---|---|---|
| 0 | `0x00000000` | 26,214,336 | `1420` | `0011` | `0001` | `0x406a0000` | pass |
| 1 | `0x01900000` | 26,214,336 | `1420` | `0001` | `0101` | `0x421a0000` | pass |
| 2 | `0x03200000` | 45,219,776 | `1420` | `0001` | `0601` | `0x43aa0000` | pass |
| 3 | `0x05d20000` | 262,080 | `1420` | `0100` | `0e01` | `0x00000000` | pass |
| 4 | `0x05d60000` | 13,107,136 | `1420` | `0001` | `0201` | `0x467e0000` | pass |

Each block comprises a 32-byte header, variable payload, and 32-byte trailer; first 28 bytes of header and trailer match. All 5 blocks exactly cover the file with no leftover bytes. The trailer last 4 bytes are checksum words, not identical copies of the header.

Historical CHDK Olympus method works **for all five E-P7 blocks**: XOR every payload byte with `0xFF`, then rearrange each 16-byte lane according to `13026475ba98decf`. The little-endian 32-bit additive sum of header + decoded payload + full trailer equals zero modulo 2^32 in every block. This is a strong reproducible format finding, but an additive checksum does **not** verify firmware authenticity, signature acceptance, or device safety.

Reference: [Olympus e/mju/stylus FW analysis — CHDK forum](https://chdk.setepontos.com/d/2471-olympus-emjustylus-series-fw-analysis), including historical format, transform and checksum notes. Prior work is a method precedent; original implementation code is not imported.

## Validated embedded filesystem lead

After in-memory decode, block #2 contains a **plausible SquashFS 4.0 superblock** at payload-relative offset `0x021367e0`: 247 inodes, 131,072-byte block size, compression ID 3 (LZO per SquashFS), and 3,393,511 bytes used. Its superblock data bounds are within the decoded payload. This is only a header-level check: directory tree and files were **not** extracted or validated.

Magic-byte searches also hit JPEG markers in the decoded resource-like blocks. Do not attribute these to ART filters until their container references or application callers are identified. Apparent ELF magic hits in a decoded binary search had implausible header fields and must **not** be reported as validated executables.

## Reproduction and privacy boundary

Requires Python 3.10+ and the user-owned local file. This tool reads but **never writes** a firmware payload:

```bash
python3 tools/inspect_olympus_oe.py /path/to/E142_EP7_firmware_download.BIN --json
python3 -m unittest discover -s tests -v
```

All tests use synthetic bytes. The original firmware, decoded block contents, extracted assets, private identifiers and network credentials were neither committed nor included in test fixtures. Local read-only run: **5/5 blocks passed**; new tests: **5/5 passed**.

## Gate decisions and next safe step

- **G1 (research input): passed for this candidate** — real bytes are now accessible in the controlled analysis session, origin metadata documented, integrity consistent with historical checksum. Source provenance/cryptographic authenticity is not established by this alone.
- **G2 (ART representation): unknown** — investigate real resource identifiers, software tables, or ISP parameter paths only from observed bytes; no arbitrary address guesses.
- **G4/G5 (repackage, signatures, flash/recovery): entirely unknown; explicitly no-go for device writing.**
- Suggested T1 follow-up: validate the SquashFS contents with a mature extractor in a private environment (do not upload extracted OEM code), then identify whether block #4's resource-like structures and block IDs are related to ART effect assets. Keep Cloud tasks to source and synthetic fixtures when private OEM bytes are unavailable.

Next PR should contain only reproducible parser improvements, metadata, signatures and evidence—not binary dumps or a flashable image.

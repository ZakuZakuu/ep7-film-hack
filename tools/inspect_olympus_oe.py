#!/usr/bin/env python3
"""Read-only Olympus OE/OM firmware-container inspection (not an installer).

Uses the historical CHDK Olympus byte inversion + 16-byte permutation and
32-bit additive checksum solely to verify user-supplied samples. Inspection is
read-only; decoded SquashFS carving requires explicit local-only output opt-in,
an expected input hash/size and a validated candidate. Not a filesystem parser.
https://chdk.setepontos.com/d/2471-olympus-emjustylus-series-fw-analysis
"""
from __future__ import annotations

import argparse
from array import array
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile

HEADER_SIZE = 32
PERMUTATION = tuple(int(c, 16) for c in "13026475ba98decf")
INVERT = bytes.maketrans(bytes(range(256)), bytes(x ^ 0xFF for x in range(256)))
CHUNK = 1 << 20  # must be divisible by 16


class FormatError(ValueError):
    """A structural or checksum assumption is contradicted by the input."""


def decode_chunk(raw: bytes) -> bytes:
    """Transform whole 16-byte lanes; no state crosses chunk boundaries."""
    if len(raw) % 16:
        raise FormatError("decoded chunk length is not divisible by 16")
    inverted = raw.translate(INVERT)
    out = bytearray(len(inverted))
    for dst, src in enumerate(PERMUTATION):
        out[dst::16] = inverted[src::16]
    return bytes(out)


def sum_u32_le(data: bytes) -> int:
    if len(data) % 4:
        raise FormatError("checksum data not 4-byte aligned")
    values = array("I")
    if values.itemsize != 4:
        raise RuntimeError("platform lacks 32-bit unsigned array elements")
    values.frombytes(data)
    if sys.byteorder != "little":
        values.byteswap()
    return sum(values) & 0xFFFFFFFF


def squashfs_candidate(data: bytes, absolute_decoded_offset: int, payload_size: int):
    """Accept only plausible SquashFS v4 superblocks, not lone magic hits."""
    result = []
    start = 0
    while True:
        at = data.find(b"hsqs", start)
        if at == -1:
            break
        if len(data) - at >= 96:
            sup = data[at : at + 96]
            inodes = struct.unpack_from("<I", sup, 4)[0]
            block_size = struct.unpack_from("<I", sup, 12)[0]
            compression = struct.unpack_from("<H", sup, 20)[0]
            major, minor = struct.unpack_from("<HH", sup, 28)
            bytes_used = struct.unpack_from("<Q", sup, 40)[0]
            offset = absolute_decoded_offset + at
            if (major == 4 and minor == 0 and 1 <= compression <= 6
                and 4096 <= block_size <= (1 << 20)
                and block_size & (block_size - 1) == 0
                and inodes > 0 and 96 <= bytes_used <= payload_size - offset):
                result.append({"payload_offset": offset, "inode_count": inodes,
                               "block_size": block_size, "compression_id": compression,
                               "version": "4.0", "bytes_used": bytes_used})
        start = at + 4
    return result


def _inspect_stream(path: Path, f) -> dict:
    total_bytes = os.fstat(f.fileno()).st_size
    if total_bytes == 0:
        raise FormatError("empty OE container")
    f.seek(0)
    file_hash = hashlib.sha256()
    blocks = []
    while f.tell() < total_bytes:
        start = f.tell()
        head = f.read(HEADER_SIZE)
        if len(head) != HEADER_SIZE or head[:2] not in (b"OE", b"OM"):
            raise FormatError(f"invalid block header at 0x{start:x}")
        if head[4:8] != b"\x00" * 4 or head[24:32] != b"\x00" * 8:
            raise FormatError(f"unexpected reserved header fields at 0x{start:x}")
        length = struct.unpack_from("<I", head, 12)[0]
        if length % 16:
            raise FormatError(f"unaligned payload at 0x{start:x}")
        end = start + HEADER_SIZE + length + HEADER_SIZE
        if end > total_bytes:
            raise FormatError(f"truncated block at 0x{start:x}")
        file_hash.update(head)
        decoded_hash = hashlib.sha256()
        encoded_hash = hashlib.sha256()
        checksum = sum_u32_le(head)
        remaining = length
        previous = b""
        squashes = []
        while remaining:
            raw = f.read(min(CHUNK, remaining))
            if not raw:
                raise FormatError(f"truncated payload at 0x{start:x}")
            remaining -= len(raw)
            file_hash.update(raw)
            encoded_hash.update(raw)
            plain = decode_chunk(raw)
            decoded_hash.update(plain)
            checksum = (checksum + sum_u32_le(plain)) & 0xFFFFFFFF
            decoded_offset = length - remaining - len(plain)
            combined = previous + plain
            squashes.extend(squashfs_candidate(
                combined, decoded_offset - len(previous), length))
            previous = combined[-95:]
        tail = f.read(HEADER_SIZE)
        file_hash.update(tail)
        if len(tail) != HEADER_SIZE or head[:28] != tail[:28]:
            raise FormatError(f"header/trailer mismatch at 0x{start:x}")
        checksum = (checksum + sum_u32_le(tail)) & 0xFFFFFFFF
        if checksum != 0:
            raise FormatError(f"decoded additive checksum failed at 0x{start:x}: 0x{checksum:08x}")
        blocks.append({"index": len(blocks), "offset": start,
                       "type": head[:2].decode("ascii"),
                       "model_hex": head[2:4].hex(),
                       "version_hex": head[16:18].hex(),
                       "block_id_hex": head[20:22].hex(),
                       "load_address_candidate": f"0x{struct.unpack_from('<I', head, 8)[0]:08x}",
                       "payload_offset": start + HEADER_SIZE,
                       "payload_length": length, "end_offset": end,
                       "trailer_checksum_le": f"0x{struct.unpack_from('<I', tail, 28)[0]:08x}",
                       "checksum_residual": "0x00000000",
                       "encoded_sha256": encoded_hash.hexdigest(),
                       "decoded_sha256": decoded_hash.hexdigest(),
                       "squashfs_v4_candidates": squashes})
    if f.tell() != total_bytes:
        raise FormatError("file coverage incomplete")
    return {"file": str(path), "size": total_bytes,
            "sha256": file_hash.hexdigest(), "block_count": len(blocks),
            "all_blocks_valid": True, "note": "Container checksum is not a digital signature or proof of safe flashing.",
            "blocks": blocks}


def inspect(path: Path) -> dict:
    with path.open("rb") as f:
        return _inspect_stream(path, f)


def check_expected(info: dict, expected_sha256: str, expected_size: int):
    digest = expected_sha256.lower()
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise FormatError("expected SHA-256 must be 64 hexadecimal characters")
    if expected_size <= 0 or info["size"] != expected_size:
        raise FormatError("input size differs from expected size")
    if info["sha256"] != digest:
        raise FormatError("input SHA-256 differs from expected SHA-256")


def private_destination(destination: Path) -> Path:
    """Refuse overwrites and public tracked paths; outside-repo output is allowed."""
    if destination.exists() or destination.is_symlink():
        raise FormatError("output exists; refusing overwrite or symlink")
    output = destination.resolve()
    if not output.parent.is_dir():
        raise FormatError("create the private output directory before extraction")
    for ancestor in output.parents:
        marker = ancestor / ".git"
        if marker.is_file() or (marker / "HEAD").is_file():
            if output.relative_to(ancestor).parts[0] != "private_samples":
                raise FormatError("inside a Git checkout, output must be under private_samples/")
            break
    return output


def extract_squashfs(path: Path, destination: Path, *, expected_sha256: str,
                     expected_size: int, block_index: int, payload_offset: int,
                     allow_local_oem_output: bool = False) -> dict:
    """Carve bytes_used only; reuse OE decode/checksum, not a SquashFS decoder.

    Validate the entire input twice on the same read-only descriptor. Publish a
    mode-0600 local artifact only after successful guards; never replace a file.
    """
    if not allow_local_oem_output:
        raise FormatError("extraction requires explicit local-only OEM output opt-in")
    output = private_destination(destination)
    with path.open("rb") as f:
        info = _inspect_stream(path, f)
        check_expected(info, expected_sha256, expected_size)
        if not 0 <= block_index < info["block_count"]:
            raise FormatError("block index out of range")
        block = info["blocks"][block_index]
        matches = [s for s in block["squashfs_v4_candidates"]
                   if s["payload_offset"] == payload_offset]
        if len(matches) != 1:
            raise FormatError("offset is not a unique validated SquashFS candidate")
        candidate = matches[0]
        used = candidate["bytes_used"]
        if payload_offset < 0 or used < 96 or used > block["payload_length"] - payload_offset:
            raise FormatError("SquashFS range outside decoded payload")
        # Transformation works on 16-byte lanes even when the FS begins/ends mid-lane.
        begin = payload_offset // 16 * 16
        end = (payload_offset + used + 15) // 16 * 16
        artifact_hash = hashlib.sha256()
        written = 0
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=output.parent, prefix=".oe-extract-",
                                             delete=False) as tmp:
                temporary = Path(tmp.name)
                f.seek(block["payload_offset"] + begin)
                cursor = begin
                while cursor < end:
                    count = min(CHUNK, end - cursor)
                    raw = f.read(count)
                    if len(raw) != count:
                        raise FormatError("input truncated during extraction")
                    plain = decode_chunk(raw)
                    left = max(payload_offset, cursor) - cursor
                    right = min(payload_offset + used, cursor + count) - cursor
                    part = plain[left:right]
                    tmp.write(part)
                    artifact_hash.update(part)
                    written += len(part)
                    cursor += count
            if written != used:
                raise FormatError("extraction length mismatch")
            after = _inspect_stream(path, f)
            check_expected(after, expected_sha256, expected_size)
            if after != info:
                raise FormatError("input changed during extraction")
            # A hard link is an atomic no-replace publication on this filesystem.
            os.link(temporary, output)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return {"input_sha256": info["sha256"], "input_size": info["size"],
            "all_blocks_valid": True, "block_index": block_index,
            "decoded_payload_offset": payload_offset, "bytes": written,
            "sha256": artifact_hash.hexdigest(),
            "note": "Local OEM-derived artifact. Do not publish. Directory/files NOT validated by carving."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--extract-squashfs", type=Path, metavar="PRIVATE_OUTPUT")
    parser.add_argument("--allow-local-oem-output", action="store_true",
                        help="Opt in to a private OEM-derived file; NEVER commit/upload it")
    parser.add_argument("--expected-sha256")
    parser.add_argument("--expected-size", type=int)
    parser.add_argument("--block-index", type=int)
    parser.add_argument("--payload-offset", type=lambda value: int(value, 0),
                        help="Decoded payload-relative offset, NOT runtime address")
    args = parser.parse_args()
    extracting = args.extract_squashfs is not None
    guards = (args.expected_sha256, args.expected_size, args.block_index, args.payload_offset)
    if extracting and (not args.allow_local_oem_output or any(x is None for x in guards)):
        parser.error("extraction requires opt-in, expected SHA/size, block index and payload offset")
    if not extracting and (args.allow_local_oem_output or any(x is not None for x in guards)):
        parser.error("extraction options require --extract-squashfs")
    try:
        if extracting:
            info = extract_squashfs(args.file, args.extract_squashfs,
                                   expected_sha256=args.expected_sha256,
                                   expected_size=args.expected_size,
                                   block_index=args.block_index,
                                   payload_offset=args.payload_offset,
                                   allow_local_oem_output=True)
        else:
            info = inspect(args.file)
    except (FormatError, OSError) as e:
        parser.exit(2, f"FAILED: {e}\n")
    if args.json:
        print(json.dumps(info, indent=2, ensure_ascii=False))
    elif extracting:
        print(f"Carved {info['bytes']:,} bytes locally; SHA-256 {info['sha256']}")
        print(info["note"])
    else:
        print(f"Validated {info['block_count']} blocks in {info['size']:,} bytes; SHA-256 {info['sha256']}")
        for b in info["blocks"]:
            print(f"#{b['index']} @ 0x{b['offset']:08x}: {b['type']} model={b['model_hex']}"
                  f" version={b['version_hex']} block_id={b['block_id_hex']}"
                  f" bytes={b['payload_length']:,} checksum=OK")
            for s in b["squashfs_v4_candidates"]:
                print(f"  plausible SquashFS {s['version']} at payload+0x{s['payload_offset']:x}"
                      f", compression_id={s['compression_id']}, inodes={s['inode_count']}")
        print(info["note"])


if __name__ == "__main__":
    main()

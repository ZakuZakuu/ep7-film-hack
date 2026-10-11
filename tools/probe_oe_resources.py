#!/usr/bin/env python3
"""Bounded read-only OE layout probes, NOT an Olympus resource parser.

Outputs aggregate metadata only. Magic hits, alignment and exact-word matches
never establish an index, runtime address, ART ID or processing relationship.
Reuse the verified OE decoder; retain all private outputs outside Git.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

try:
    from tools.inspect_olympus_oe import inspect, check_expected, decode_chunk, FormatError
except ModuleNotFoundError:
    from inspect_olympus_oe import inspect, check_expected, decode_chunk, FormatError

MAGICS = {"jpeg": b"\xff\xd8\xff", "png": b"\x89PNG\r\n\x1a\n",
          "riff": b"RIFF", "elf": b"\x7fELF", "squashfs": b"hsqs",
          "gzip": b"\x1f\x8b\x08", "zip": b"PK\x03\x04"}


def positions(data, needle):
    start = 0
    while (at := data.find(needle, start)) >= 0:
        yield at
        start = at + 1


def alignment(offsets, modulus):
    if modulus <= 0:
        raise ValueError("positive modulus required")
    return {"modulus": modulus,
            "residue_counts": dict(sorted(Counter(x % modulus for x in offsets).items())),
            "consecutive_gaps": max(0, len(offsets) - 1),
            "gaps_multiple_of_modulus": sum((b-a) % modulus == 0
                                             for a, b in zip(offsets, offsets[1:]))}


def word_references(data, targets, bias=0, endian="little"):
    """Exact aligned u32 word matches only; no pointer/index interpretation."""
    if endian not in ("little", "big"):
        raise ValueError("unsupported endian")
    hits = 0
    matched = 0
    for target in sorted(set(targets)):
        value = target + bias
        if not 0 <= value <= 0xffffffff:
            continue
        found = sum(at % 4 == 0 for at in positions(data, value.to_bytes(4, endian)))
        hits += found
        matched += bool(found)
    return {"aligned_word_hits": hits, "distinct_targets": matched}


def preceding_lengths(data, targets, distance, endian):
    """Count bounded numeric candidates; not length-field validation."""
    if distance < 4 or endian not in ("little", "big"):
        raise ValueError("invalid preceding-word probe")
    eligible = plausible = 0
    for target in targets:
        if distance <= target <= len(data):
            eligible += 1
            value = int.from_bytes(data[target-distance:target-distance+4], endian)
            plausible += 96 <= value <= min(1000000, len(data)-target)
    return {"eligible": eligible, "bounded_numeric_candidates": plausible}


def probe(data, load_candidate):
    counts = Counter(data)
    entropy = -sum(v / len(data) * math.log2(v / len(data)) for v in counts.values()) if data else 0
    targets = []
    # Bound expensive hypotheses while collecting, not after allocating all hits.
    for at in positions(data, MAGICS["jpeg"]):
        if len(targets) >= 1024:
            raise ValueError("too many magic candidates for this bounded probe")
        targets.append(at)
    hits = {name: (len(targets) if name == "jpeg" else data.count(magic))
            for name, magic in MAGICS.items()}
    return {"length": len(data), "decoded_sha256": hashlib.sha256(data).hexdigest(),
            "whole_payload_entropy_bits": entropy,
            "zero_fraction": counts[0] / len(data) if data else 0,
            "ff_fraction": counts[255] / len(data) if data else 0,
            "magic_counts_UNVALIDATED": hits,
            "jpeg_alignment": [alignment(targets, m) for m in (16, 512)],
            "hypothesis_1_preceding_lengths": {
                f"{endian}_distance_{distance}": preceding_lengths(data, targets, distance, endian)
                for endian in ("little", "big") for distance in (4, 8, 16, 32)},
            "hypothesis_2_exact_word_references": {
                f"{endian}_{name}": word_references(data, targets, bias, endian)
                for endian in ("little", "big")
                for name, bias in (("payload_relative", 0), ("unverified_header_load_candidate", load_candidate))},
            "note": "No index/record/ART/runtime address is established by these probes."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--expected-size", required=True, type=int)
    args = parser.parse_args()
    try:
        info = inspect(args.file)
        check_expected(info, args.expected_sha256, args.expected_size)
        results = []
        with args.file.open("rb") as f:
            for index in (0, 1, 3, 4):
                if index >= info["block_count"]:
                    raise FormatError("required block missing")
                block = info["blocks"][index]
                if block["payload_length"] > 64 * 1024 * 1024:
                    raise FormatError("block exceeds bounded 64 MiB input")
                f.seek(block["payload_offset"])
                raw = f.read(block["payload_length"])
                if len(raw) != block["payload_length"]:
                    raise FormatError("input truncated")
                data = decode_chunk(raw)
                if hashlib.sha256(data).hexdigest() != block["decoded_sha256"]:
                    raise FormatError("decoded input changed")
                results.append({"block_index": index, "file_block_offset": block["offset"],
                                "id_raw": block["block_id_hex"],
                                **probe(data, int(block["load_address_candidate"], 16))})
        if inspect(args.file) != info:
            raise FormatError("input changed during probing")
    except (FormatError, OSError, ValueError) as error:
        parser.exit(2, f"STOP: {error}\n")
    print(json.dumps({"input_sha256": info["sha256"], "input_size": info["size"],
                      "all_oe_blocks_valid": True, "blocks": results}, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Guarded, numeric-only references to at most two nominated OE payload offsets.

Reuses the OE decoder and GNU metadata wrapper. A little-endian word match is
unclassified data until independently established as code; even a confirmed
MOV immediate does not prove the target's role. No string discovery, execution,
patching or OEM instruction/operand export.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess

try:
    from .inspect_olympus_oe import FormatError, check_expected, decode_chunk, inspect
    from .probe_oe_executable import MAX_WINDOW, disassemble
except ImportError:
    from inspect_olympus_oe import FormatError, check_expected, decode_chunk, inspect
    from probe_oe_executable import MAX_WINDOW, disassemble


def reference_candidates(data: bytes, base: int, targets: list[int]) -> list[dict]:
    if not 0 <= base <= 0xffffffff or not 1 <= len(targets) <= 2:
        raise FormatError("invalid base or target count")
    if len(set(targets)) != len(targets):
        raise FormatError("duplicate target")
    result = []
    for offset in targets:
        if not 0 <= offset < len(data) or base + offset > 0xffffffff:
            raise FormatError("target outside payload or u32 translation")
        value = base + offset
        needle = struct.pack("<I", value)
        start, hits = 0, []
        while (start := data.find(needle, start)) >= 0:
            hits.append(start)
            if len(hits) > 64:
                raise FormatError("reference count exceeds bounded scope")
            start += 1  # include unaligned and overlapping matches
        result.append({"target_payload_offset": offset, "candidate_address_u32": value,
                       "unclassified_u32_match_offsets": hits})
    return result


def confirm_literals(rows, candidates: list[dict], sources: list[int], end: int) -> list[dict]:
    """Require both GNU's nominated immediate and its encoded u32 byte match.

    This establishes representation only. Caller/entry/function/data semantics
    must be independently checked; arbitrary data can also decode as MOV.
    """
    if len(sources) > 8 or len(set(sources)) != len(sources):
        raise FormatError("too many or duplicate sources")
    by_address = {r.address: r for r in rows}
    following = {a.address: b.address for a, b in zip(rows, rows[1:])}
    result = []
    for source in sources:
        row = by_address.get(source)
        if row is None or row.mnemonic != "mov":
            raise FormatError("nominated source is not a decoded MOV")
        operand = row.operands.split(",", 1)[0]
        if not re.fullmatch(r"-?\d+|0x[0-9a-fA-F]+", operand):
            raise FormatError("nominated MOV is not a literal")
        value = int(operand, 16 if operand.startswith("0x") else 10)
        if not -(1 << 31) <= value <= 0xffffffff:
            raise FormatError("literal outside u32")
        value &= 0xffffffff
        candidate = next((c for c in candidates if c["candidate_address_u32"] == value), None)
        stop = following.get(source, end)
        matches = [] if candidate is None else [h for h in candidate["unclassified_u32_match_offsets"]
                                               if source < h and h + 4 <= stop]
        if not matches:
            raise FormatError("literal lacks an in-instruction nominated u32 match")
        result.append({"source_payload_offset": source, "target_payload_offset": candidate["target_payload_offset"],
                       "candidate_address_u32": value, "encoded_u32_offsets": matches,
                       "note": "MOV representation verified; code/target role requires independent evidence."})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    number = lambda value: int(value, 0)
    parser.add_argument("file", type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--expected-size", required=True, type=int)
    parser.add_argument("--block-index", required=True, type=int)
    parser.add_argument("--mapping-base", required=True, type=number)
    parser.add_argument("--target-offset", action="append", type=number, required=True)
    parser.add_argument("--objdump", type=Path)
    parser.add_argument("--start", type=number)
    parser.add_argument("--length", type=number)
    parser.add_argument("--literal-source", action="append", type=number, default=[])
    args = parser.parse_args()
    try:
        window = any(x is not None for x in (args.objdump, args.start, args.length))
        if window and (args.objdump is None or args.start is None or args.length is None):
            raise FormatError("partial window")
        if args.literal_source and not window:
            raise FormatError("sources require a decoder window")
        info = inspect(args.file)
        check_expected(info, args.expected_sha256, args.expected_size)
        if not 0 <= args.block_index < info["block_count"]:
            raise FormatError("block outside container")
        block = info["blocks"][args.block_index]
        if block["payload_length"] > 64 * 1024 * 1024:
            raise FormatError("payload too large")
        with args.file.open("rb") as f:
            f.seek(block["payload_offset"])
            data = decode_chunk(f.read(block["payload_length"]))
        if hashlib.sha256(data).hexdigest() != block["decoded_sha256"]:
            raise FormatError("decoded hash changed")
        candidates = reference_candidates(data, args.mapping_base, args.target_offset)
        confirmations = []
        if window:
            if args.start < 0 or not 0 < args.length <= MAX_WINDOW or args.start + args.length > len(data):
                raise FormatError("window outside bounds")
            rows = disassemble(args.objdump, data[args.start:args.start + args.length], args.start)
            confirmations = confirm_literals(rows, candidates, args.literal_source, args.start + args.length)
        if inspect(args.file) != info:
            raise FormatError("input changed during analysis")
        result = {"input_sha256": info["sha256"], "input_size": info["size"],
                  "all_oe_checksums_valid": True, "block_index": args.block_index,
                  "decoded_sha256": block["decoded_sha256"], "proposed_mapping_base": args.mapping_base,
                  "candidates": candidates, "nominated_mov_confirmations": confirmations,
                  "note": "Decoded offsets and candidate static addresses only; no runtime, persistence or imaging claim."}
    except (FormatError, OSError, ValueError, subprocess.TimeoutExpired):
        parser.exit(2, "STOP: input, bounds or nominated-reference validation failed; no OEM output.\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

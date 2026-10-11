#!/usr/bin/env python3
"""Bounded, read-only MN103 metadata via GNU objdump; not an ISA detector.

Reuses the verified OE decoder. OEM bytes and objdump text stay private/in
memory; stdout contains counts and selected numeric references only. A linear
decode, instruction boundary or candidate VMA alone does not establish code.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

try:
    from .inspect_olympus_oe import FormatError, check_expected, decode_chunk, inspect
except ImportError:
    from inspect_olympus_oe import FormatError, check_expected, decode_chunk, inspect

MAX_WINDOW = 128 * 1024
RETURNS = {"ret", "retf", "rets", "rti"}
BRANCHES = {"beq", "bne", "bgt", "bge", "blt", "ble", "bhi", "bls",
            "bcc", "bcs", "bvc", "bvs", "bnc", "bns", "bra", "jmp"}
CALLS = {"call", "calls"}
UNMODELED_FLOW = {"setlb", "leq", "lne", "lgt", "lge", "lle", "llt",
                  "lhi", "lcc", "lls", "lcs", "lra", "syscall"}


@dataclass(frozen=True)
class Instruction:
    address: int
    mnemonic: str
    operands: str  # private, never serialized

    def direct_target(self):
        if self.mnemonic not in BRANCHES | CALLS:
            return None
        match = re.match(r"^0x([0-9a-fA-F]+)(?:,|$)", self.operands)
        return int(match[1], 16) if match else None


def parse_objdump(text: str, start: int, length: int) -> list[Instruction]:
    """Parse --no-show-raw-insn output, not machine instructions."""
    result = []
    for line in text.splitlines():
        match = re.match(r"^\s*([0-9a-fA-F]+):\s+(\S+)(?:[ \t]+(.*))?$", line)
        if not match:
            continue
        address = int(match[1], 16)
        if not start <= address < start + length:
            raise FormatError("objdump address outside bounded window")
        if result and address <= result[-1].address:
            raise FormatError("objdump instruction addresses are not increasing")
        result.append(Instruction(address, match[2], (match[3] or "").strip()))
    if not result or result[0].address != start:
        raise FormatError("objdump did not decode the requested start")
    return result


def walk(rows: list[Instruction], entry: int, limit: int = 1024) -> dict:
    """Bounded intra-function reachability, without following calls/indirects.

    No function name or ABI is inferred. Returns can be reached in accidentally
    decoded data too; independent evidence is required by the research memo.
    """
    by_address = {row.address: row for row in rows}
    following = {a.address: b.address for a, b in zip(rows, rows[1:])}
    pending, visited, returns, calls, unresolved = [entry], set(), set(), set(), set()
    while pending and len(visited) < limit:
        at = pending.pop()
        if at in visited:
            continue
        row = by_address.get(at)
        if row is None or row.mnemonic.startswith(".") or row.mnemonic == "break":
            unresolved.add(at)
            continue
        visited.add(at)
        if row.mnemonic in UNMODELED_FLOW:
            unresolved.add(at)  # hardware loop/trap semantics are not modeled
            continue
        if row.mnemonic in RETURNS:
            returns.add(at)
            continue
        target = row.direct_target()
        if row.mnemonic in CALLS:
            if target is None:
                unresolved.add(at)  # unknown callee, fallthrough still considered
            else:
                calls.add((at, target))
        elif row.mnemonic in BRANCHES:
            if target is None:
                unresolved.add(at)
            else:
                pending.append(target)
            if row.mnemonic in {"jmp", "bra"}:
                continue
        if at in following:
            pending.append(following[at])
        else:
            unresolved.add(at)
    return {"entry_payload_offset": entry, "visited_instructions": len(visited),
            "return_offsets": sorted(returns)[:8],
            "direct_calls": [{"source": a, "target": b,
                              "target_is_instruction_boundary": b in by_address}
                             for a, b in sorted(calls)[:8]],
            "unresolved_offsets": sorted(unresolved)[:8],
            "truncated": bool(pending),
            "note": "Static reachability only; no function semantics or execution claim."}


def mapping_checks(rows: list[Instruction], base: int, sources: list[int]) -> list[dict]:
    """Check only nominated immediate MOV instructions against a proposed base."""
    if not 0 <= base <= 0xffffffff or len(sources) > 8:
        raise FormatError("mapping base outside u32 or too many pointer sources")
    by_address = {row.address: row for row in rows}
    result = []
    for source in sources:
        row = by_address.get(source)
        if row is None or row.mnemonic != "mov":
            raise FormatError("pointer source is not a decoded MOV instruction")
        operand = row.operands.split(",", 1)[0]
        if not re.fullmatch(r"-?\d+|0x[0-9a-fA-F]+", operand):
            raise FormatError("pointer source is not a literal immediate")
        value = int(operand, 16 if operand.startswith("0x") else 10)
        if not -(1 << 31) <= value <= 0xffffffff:
            raise FormatError("pointer immediate outside u32")
        value &= 0xffffffff
        offset = value - base
        target = by_address.get(offset)
        result.append({"source_payload_offset": source, "immediate_u32": value,
                       "candidate_payload_offset": offset,
                       "target_is_instruction_boundary": target is not None,
                       "target_is_direct_branch": target is not None and
                           target.mnemonic in BRANCHES and target.direct_target() is not None})
    return result


def summarize(rows: list[Instruction], start: int, length: int) -> dict:
    boundaries = {row.address for row in rows}
    counts = Counter(row.mnemonic for row in rows)
    refs = [(row.address, row.direct_target()) for row in rows
            if row.direct_target() is not None]
    internal = [(a, b) for a, b in refs if start <= b < start + length]
    return {"linear_instruction_lines": len(rows),
            "data_directive_lines": sum(n for m, n in counts.items() if m.startswith(".")),
            "break_lines": counts["break"], "clr_lines": counts["clr"],
            "call_lines": sum(counts[m] for m in CALLS),
            "return_lines": sum(counts[m] for m in RETURNS),
            "internal_direct_references": len(internal),
            "internal_targets_at_instruction_boundaries": sum(b in boundaries for a, b in internal),
            "note": "Linear decode includes padding/data; counts do not identify executable sections."}


def disassemble(objdump: Path, data: bytes, start: int) -> list[Instruction]:
    if start < 0 or not 0 < len(data) <= MAX_WINDOW:
        raise FormatError("window must be positive and at most 128 KiB")
    with tempfile.TemporaryDirectory(prefix="ep7-executable-", dir="/tmp") as private:
        artifact = Path(private) / "window.bin"
        artifact.write_bytes(data)
        artifact.chmod(0o600)
        completed = subprocess.run(
            [str(objdump.resolve()), "-D", "-z", "-b", "binary", "-m", "mn10300", "-EL",
             "--no-show-raw-insn", f"--adjust-vma={start}", str(artifact)],
            capture_output=True, text=True, timeout=60, check=False)
        if completed.returncode:
            raise FormatError("external objdump failed; no disassembly published")
        return parse_objdump(completed.stdout, start, len(data))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--expected-size", required=True, type=int)
    parser.add_argument("--objdump", required=True, type=Path)
    parser.add_argument("--block-index", required=True, type=int)
    number = lambda value: int(value, 0)
    parser.add_argument("--start", required=True, type=number)
    parser.add_argument("--length", required=True, type=number)
    parser.add_argument("--entry", action="append", type=number, default=[])
    parser.add_argument("--mapping-base", type=number)
    parser.add_argument("--pointer-source", action="append", type=number, default=[])
    args = parser.parse_args()
    try:
        if not 0 < args.length <= MAX_WINDOW or args.start < 0 or len(args.entry) > 8:
            raise FormatError("invalid window or too many entries")
        if args.pointer_source and args.mapping_base is None:
            raise FormatError("pointer checks require an explicitly proposed mapping base")
        info = inspect(args.file)
        check_expected(info, args.expected_sha256, args.expected_size)
        if not 0 <= args.block_index < info["block_count"]:
            raise FormatError("block index outside container")
        block = info["blocks"][args.block_index]
        if block["payload_length"] > 64 * 1024 * 1024 or args.start + args.length > block["payload_length"]:
            raise FormatError("window outside bounded payload")
        with args.file.open("rb") as f:
            f.seek(block["payload_offset"])
            data = decode_chunk(f.read(block["payload_length"]))
        if hashlib.sha256(data).hexdigest() != block["decoded_sha256"]:
            raise FormatError("decoded hash changed")
        rows = disassemble(args.objdump, data[args.start:args.start + args.length], args.start)
        result = {"input_sha256": info["sha256"], "input_size": info["size"],
                  "all_oe_checksums_valid": True, "block_index": args.block_index,
                  "decoded_sha256": block["decoded_sha256"], "raw_block_version_hex": block["version_hex"],
                  "encoded_payload_start_file_offset": block["payload_offset"],
                  "start_payload_offset": args.start, "window_length": args.length,
                  "selected_decoder": "GNU objdump MN10300 little endian; not autodetected",
                  "linear_summary": summarize(rows, args.start, args.length),
                  "selected_entry_walks": [walk(rows, entry) for entry in args.entry],
                  "proposed_mapping_base": args.mapping_base,
                  "mapping_checks": [] if args.mapping_base is None else
                      mapping_checks(rows, args.mapping_base, args.pointer_source),
                  "note": "File offset != decoded offset != runtime address. No OEM text/bytes exported."}
        if inspect(args.file) != info:
            raise FormatError("input changed during probing")
    except (FormatError, OSError, ValueError, subprocess.TimeoutExpired):
        parser.exit(2, "STOP: input, bounds or external decoder validation failed; no OEM output.\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

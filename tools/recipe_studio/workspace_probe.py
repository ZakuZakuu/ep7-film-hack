"""Read-only Workspace table locator; no DLL execution or vendor byte exports.

Identity/layout reference: fishcu/oly_fw_analysis@539fcf1,
docs/color/pen-f/HSL_TABLES.md. Original implementation.
Optional analysis dependencies: pefile, capstone (install outside the checkout).
"""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

TABLE_SIZE = 3028
TABLE_SHA256 = "a33d64bdb78ac41ba24ccbff820380f563211a095ac08a12a7c37a51b5c00531"


def locate_windows(data, size, digest):
    """Exhaustive byte-aligned search; returns offsets, never matched bytes."""
    if type(size) is not int or size < 1:
        raise ValueError("window size must be positive")
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("expected a lowercase SHA-256 digest")
    view = memoryview(data)
    return [i for i in range(len(data) - size + 1)
            if hashlib.sha256(view[i:i + size]).hexdigest() == digest]


def private_report_path(path):
    """Keep inventories/addresses in the task's temporary directory only."""
    path = Path(path).expanduser().resolve()
    root = Path(tempfile.gettempdir()).resolve()
    repo = Path(__file__).resolve().parents[2]
    if root not in path.parents or path == repo or repo in path.parents:
        raise ValueError("research reports must be outside the checkout, under the system temp directory")
    return path


def pe_evidence(data, table_offset, size):
    """References decoded per PE unwind range; computed/leaf references excluded.

    A reference establishes data flow, not a pixel algorithm. No instruction
    bytes or assembly listings are included in the report.
    """
    import capstone as cs
    import pefile
    pe = pefile.PE(data=data)
    if pe.FILE_HEADER.Machine != 0x8664:
        raise ValueError("xref analysis requires a PE x64 image")
    base = pe.OPTIONAL_HEADER.ImageBase
    rva = pe.get_rva_from_offset(table_offset)
    if pe.get_section_by_rva(rva) is None or pe.get_offset_from_rva(rva) != table_offset:
        raise ValueError("table is not mapped by a PE section")
    va = base + rva
    decoder = cs.Cs(cs.CS_ARCH_X86, cs.CS_MODE_64)
    decoder.detail = True
    references = []
    for entry in getattr(pe, "DIRECTORY_ENTRY_EXCEPTION", []):
        start, end = entry.struct.BeginAddress, entry.struct.EndAddress
        for ins in decoder.disasm(pe.get_data(start, end - start), base + start):
            for operand in ins.operands:
                if operand.type == cs.x86.X86_OP_IMM:
                    target = operand.imm
                elif operand.type == cs.x86.X86_OP_MEM:
                    mem = operand.mem
                    if mem.base == cs.x86.X86_REG_RIP:
                        target = ins.address + ins.size + mem.disp
                    elif mem.base == 0 and mem.index == 0:
                        target = mem.disp
                    else:
                        continue
                else:
                    continue
                if va <= target < va + size:
                    references.append({"instruction_rva": ins.address - base,
                                       "function_rva": start, "function_end_rva": end,
                                       "table_relative_offset": target - va})
    return {"machine": "x64", "image_base": base, "table_rva": rva,
            "direct_references": references,
            "coverage": "PE unwind ranges; excludes computed references and leaf functions"}


def inspect_installation(directory):
    """Hash every DLL privately, find full-table matches, inspect direct xrefs."""
    root = Path(directory)
    data = (root / "OlyAcacia.dll").read_bytes()
    offsets = locate_windows(data, TABLE_SIZE, TABLE_SHA256)
    if not offsets:
        raise ValueError("full table absent from OlyAcacia; installation is unqualified")
    needle = data[offsets[0]:offsets[0] + TABLE_SIZE]
    inventory, matches = [], []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() != ".dll":
            continue
        content = path.read_bytes()
        name = str(path.relative_to(root))
        inventory.append({"name": name, "bytes": len(content),
                          "sha256": hashlib.sha256(content).hexdigest()})
        start = 0
        while True:
            offset = content.find(needle, start)
            if offset < 0:
                break
            matches.append({"name": name, "file_offset": offset,
                            **pe_evidence(content, offset, TABLE_SIZE)})
            start = offset + 1
    import pefile
    version_pe = pefile.PE(str(root / "OM Workspace.exe"))
    version = version_pe.VS_FIXEDFILEINFO[0]
    words = (version.FileVersionMS, version.FileVersionLS)
    return {"format": "ep7-workspace-inspection-v1",
            "workspace_file_version": ".".join(str(x) for w in words for x in (w >> 16, w & 65535)),
            "table_sha256": TABLE_SHA256, "table_bytes": TABLE_SIZE,
            "dll_inventory": inventory, "matches": matches,
            "pixel_model_status": "not-recovered"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("installation")
    parser.add_argument("--report", required=True, help="private JSON under system temp")
    args = parser.parse_args(argv)
    try:
        output = private_report_path(args.report)
        result = inspect_installation(args.installation)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, ImportError) as error:
        parser.exit(2, f"error: {error}\n")
    print("Private inspection report saved; no vendor bytes exported.")


if __name__ == "__main__":
    main()

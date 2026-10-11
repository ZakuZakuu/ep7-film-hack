#!/usr/bin/env python3
"""Read-only generic blob inventory. NOT an Olympus firmware decoder."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    n = len(data)
    return -sum((c / n) * math.log2(c / n) for c in counts if c)


def inventory(path: Path) -> dict:
    size = path.stat().st_size
    sha = hashlib.sha256()
    with path.open("rb") as f:
        first = f.read(4096)
        sha.update(first)
        while True:
            block = f.read(1024 * 1024)
            if not block:
                break
            sha.update(block)
        slices = {}
        for name, offset in [("start", 0), ("middle", max(0, size // 2 - 2048)),
                             ("end", max(0, size - 4096))]:
            f.seek(offset)
            sample = f.read(4096)
            slices[name] = {
                "offset": offset, "sample_size": len(sample),
                "entropy_bits_per_byte": round(shannon_entropy(sample), 4)
            }
    return {
        "path": str(path), "bytes": size, "sha256": sha.hexdigest(),
        "first_64_bytes_hex": first[:64].hex(), "entropy_samples": slices,
        "caution": "Generic metadata only. No E-P7 format identification or validation."
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file", type=Path)
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = ap.parse_args()
    result = inventory(args.file)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()

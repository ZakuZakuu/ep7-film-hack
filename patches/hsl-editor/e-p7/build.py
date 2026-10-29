#!/usr/bin/env python3
"""Guarded E142 editor PROTOTYPE verification, never an owner firmware build.

Placement remains blocked. Only --verify-only is admitted; no install writer.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from ep7_color_min import BASE, STOCK_SHA, MAIN_SHA, digest, require
from ep7_t25_v4_probe import Probe as V4
from ep7_t27_candidate import overlay


def build(args):
    manifest = json.loads((HERE / 'patch.json').read_text())
    require(args.verify_only and args.out is None,
            'STOP: prototype placement is unqualified; only --verify-only allowed')
    upstream = args.upstream.resolve()
    require(not subprocess.check_output(['git', 'status', '--porcelain'],
            cwd=upstream, text=True).strip(), 'Tracked upstream changes')
    for name, expected in manifest['source_sha256'].items():
        require(digest((ROOT / name).read_bytes()) == expected,
                'Unqualified source change: ' + name)
    raw = args.stock.read_bytes()
    require(len(raw) == 111017984 and digest(raw) == STOCK_SHA,
            'Exact stock identity required')
    with tempfile.TemporaryDirectory(prefix='ep7-v5a-build-', dir='/tmp') as scratch:
        x = V4(upstream, args.stock, scratch)
        versions = {name: subprocess.check_output([str(x.tools / path), '--version'],
                    text=True).splitlines()[0] for name, path in
                    [('as', 'gas/as-new'), ('ld', 'ld/ld-new'),
                     ('objcopy', 'binutils/objcopy'), ('objdump', 'binutils/objdump')]}
        require(all(v.endswith(' 2.45') for v in versions.values()),
                'Qualified GNU 2.45 required')
        x.prepare()
        require(digest(x.data) == MAIN_SHA, 'Wrong decoded main')
        v4 = json.loads((ROOT / 'patches/hsl-recipes/e-p7/patch.json').read_text())
        require(digest(x.candidate) == v4['decoded_output_sha256'],
                'v4 baseline differs from its unchanged qualification')
        candidate, labels, edits = overlay(x)
        require(edits == manifest['v5_modified_ranges'], 'New range guards changed')
        require(digest(candidate) == manifest['decoded_output_sha256'],
                'Candidate main mismatch')
        import oly_container as oe
        changed = oe.replace_payload(x.blocks[0], candidate)
        require(changed.header == x.blocks[0].header
                and changed.trailer[:28] == x.blocks[0].trailer[:28]
                and oe.sum32(changed.header + changed.payload + changed.trailer) == 0,
                'Container guard')
        chunks = (changed.header, oe.encode(changed.payload), changed.trailer,
                  raw[x.blocks[1].offset:])
        require(oe.parse(b''.join(chunks[:3]))[0].payload == candidate,
                'Encoded main reparse mismatch')
        h = hashlib.sha256()
        for chunk in chunks:
            h.update(chunk)
        total = sum(map(len, chunks))
        require(total == 111017984 and h.hexdigest() == manifest['output_sha256'],
                'Prospective package mismatch')
        result = dict(version='5a', input_sha256=STOCK_SHA,
                      decoded_output_sha256=digest(candidate),
                      prospective_output_sha256=h.hexdigest(), bytes=total,
                      unchanged_components=4, tool_versions=versions,
                      verify_only=args.verify_only,
                      package_files_created=not args.verify_only)
    print(json.dumps(result, indent=2))
    return result


def main():
    os.umask(0o077)
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock', required=True, type=Path)
    p.add_argument('--upstream', required=True, type=Path)
    p.add_argument('--out', type=Path)
    p.add_argument('--verify-only', action='store_true')
    build(p.parse_args())


if __name__ == '__main__':
    main()

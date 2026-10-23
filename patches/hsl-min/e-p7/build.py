#!/usr/bin/env python3
"""Original deterministic E-P7 H/L package builder. Files only; no devices.

Requires the owner's exact stock file, a separately cloned pinned fishcu tool
checkout, and GNU binutils 2.45. No third-party implementation is vendored.
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
REPOSITORY = HERE.parents[2]
UPSTREAM = '539fcf1fa9eda5fdef8ede4deeab94a4691d94c3'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def guarded_range(original, record):
    start, size = int(record['decoded_offset'], 0), record['length']
    require(0 <= start < start+size <= len(original), 'Patch span outside main')
    require(sha(original[start:start+size]) == record['original_sha256'], 'Original range guard failed')
    return start, size


def validate_output_directory(path):
    result = Path(path).resolve()
    require(result != REPOSITORY and REPOSITORY not in result.parents,
            'OEM outputs must be outside the checked-out repository')
    require(not result.exists(), 'Output directory already exists')
    return result


def build(args):
    manifest = json.loads((HERE / 'patch.json').read_text())
    raw = args.stock.read_bytes()
    require(len(raw) == manifest['input_bytes'] and sha(raw) == manifest['input_sha256'],
            'Exact E-P7 1.1 stock size/SHA-256 required')
    destination = validate_output_directory(args.out)
    upstream = args.upstream.resolve()
    require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=upstream, text=True).strip()
            == UPSTREAM, 'Wrong external tool revision')
    require(not subprocess.check_output(['git', 'status', '--porcelain'], cwd=upstream, text=True).strip(),
            'External tracked tools are modified')
    sys.path.insert(0, str(upstream / 'tools'))
    import oly_container
    blocks = oly_container.parse(raw)
    require(len(blocks) == 5 and blocks[0].kind == 0x100, 'Component layout mismatch')
    require(oly_container.reconstruct(blocks) == raw, 'Original exact roundtrip failed')
    original = blocks[0].payload
    require(sha(original) == manifest['decoded_input_sha256'], 'Wrong decoded main')
    source = (HERE / 'hook.s').read_bytes()
    require(sha(source) == manifest['hook_source_sha256'], 'Unqualified hook source edit')
    spans = [guarded_range(original, record) for record in manifest['modified_ranges']]
    require(len(spans) == 2 and spans[0][0]+spans[0][1] <= spans[1][0], 'Overlapping/invalid spans')
    toolchain = args.toolchain.resolve() if args.toolchain else upstream / 'toolchains/mn103-patch-build'
    tools = {'as': toolchain/'gas/as-new', 'ld': toolchain/'ld/ld-new',
             'objcopy': toolchain/'binutils/objcopy', 'objdump': toolchain/'binutils/objdump'}
    versions = {name: subprocess.check_output([str(tool), '--version'], text=True).splitlines()[0]
                for name, tool in tools.items()}
    require(all(line.endswith(' '+manifest['tool_version']) for line in versions.values()),
            'Requires the qualified GNU binutils version')
    # No partial package/output is published before every identity and hash gate.
    with tempfile.TemporaryDirectory(prefix='ep7-hl-assembly-') as temporary:
        scratch = Path(temporary)
        binaries = []
        for index, (text, address, symbols) in enumerate([
            ('.text\n.global _start\n_start:\njmp ep7_extension\n',
             0x603b02d9, {'ep7_extension': 0x6055e5f0}),
            (source.decode(), 0x6055e5f0, {'ep7_builder': 0x603b0068, 'ep7_resume': 0x603b02de})]):
            stem = scratch / str(index)
            stem.with_suffix('.s').write_text(text)
            subprocess.run([str(tools['as']), '-o', str(stem.with_suffix('.o')),
                            str(stem.with_suffix('.s'))], check=True)
            definitions = [f'--defsym={key}={value:#x}' for key, value in symbols.items()]
            subprocess.run([str(tools['ld']), '-Ttext', hex(address), '-e', '_start', *definitions,
                            '-o', str(stem.with_suffix('.elf')), str(stem.with_suffix('.o'))], check=True)
            subprocess.run([str(tools['objcopy']), '-O', 'binary', '-j', '.text',
                            str(stem.with_suffix('.elf')), str(stem.with_suffix('.bin'))], check=True)
            code = stem.with_suffix('.bin').read_bytes()
            record = manifest['modified_ranges'][index]
            require(len(code) == record['length'] and sha(code) == record['replacement_sha256'],
                    f'Assembled range {index}: {len(code)} bytes / {sha(code)} differs from qualified code')
            binaries.append(code)
    changed = bytearray(original)
    for (start, size), code in zip(spans, binaries):
        changed[start:start+size] = code
    require(sha(changed) == manifest['decoded_output_sha256'], 'Decoded result hash mismatch')
    replacement = oly_container.replace_payload(blocks[0], bytes(changed))
    require(replacement.header == blocks[0].header and replacement.trailer[:28] == blocks[0].trailer[:28],
            'Unexpected wrapper metadata change')
    result = oly_container.reconstruct([replacement, *blocks[1:]])
    require(len(result) == manifest['output_bytes'] and sha(result) == manifest['output_sha256'],
            'Whole package result hash mismatch')
    reparsed = oly_container.parse(result)
    require(reparsed[0].payload == bytes(changed) and len(reparsed) == 5, 'Reparse failed')
    for a, b in zip(blocks[1:], reparsed[1:]):
        require((a.header, a.payload, a.trailer) == (b.header, b.payload, b.trailer), 'Other component changed')
    require(result[blocks[1].offset:] == raw[blocks[1].offset:], 'Unmodified raw tail changed')
    destination.mkdir(parents=True, mode=0o700)
    for relative, data in [(manifest['install_path'], result), (manifest['restore_path'], raw)]:
        target = destination / relative
        target.parent.mkdir(parents=True, mode=0o700)
        with target.open('xb') as stream:
            stream.write(data)
        target.chmod(0o600)
    summary = {'input_sha256': sha(raw), 'output_sha256': sha(result), 'restore_sha256': sha(raw),
               'decoded_output_sha256': sha(changed), 'all_five_checksums_valid': True,
               'unchanged_components': 4, 'tool_versions': versions,
               'hook_source_sha256': sha(source), 'patch_manifest_sha256': sha((HERE/'patch.json').read_bytes()),
               'scope': 'Full package creation and offline validation only; no physical installation/recovery'}
    (destination / 'build.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
    return summary


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--upstream', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--toolchain', type=Path)
    build(parser.parse_args())


if __name__ == '__main__':
    main()

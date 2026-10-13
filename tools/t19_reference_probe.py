#!/usr/bin/env python3
"""Fixed original GNU reference patterns; numeric byte candidates, never xrefs.

No OEM code execution or complete reader discovery. Operand/code/type boundaries
must be independently proved before any candidate is promoted.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

try:
    from .inspect_olympus_oe import FormatError
    from .probe_oe_executable import disassemble
except ImportError:
    from inspect_olympus_oe import FormatError
    from probe_oe_executable import disassemble

FIXTURE = Path(__file__).resolve().parents[1]/'tests/fixtures/mn103_t19_refs.s'
SHA256 = '5dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190'


def bounded_hits(data, pattern, limit=64):
    if not pattern or limit < 1:
        raise FormatError('invalid nominated pattern bound')
    result, at = [], 0
    while (at := data.find(pattern, at)) >= 0:
        result.append(at)
        if len(result) > limit:
            raise FormatError('reference pattern bound exceeded; no broader scan')
        at += 1
    return result


def patterns(assembler, objdump):
    with tempfile.TemporaryDirectory(prefix='ep7-original-refs-', dir='/tmp') as d:
        obj, raw = Path(d)/'original.o', Path(d)/'original.bin'
        subprocess.run([str(assembler), '-o', str(obj), str(FIXTURE)],
                       check=True, capture_output=True, timeout=30)
        subprocess.run([str(objdump.parent/'objcopy'), '-O', 'binary', '-j', '.text', str(obj), str(raw)],
                       check=True, capture_output=True, timeout=30)
        data = raw.read_bytes()
        rows = disassemble(objdump, data, 0)
        if len(rows) != 112 or any(r.mnemonic not in ('mov', 'movbu') for r in rows):
            raise FormatError('original GNU reference fixture shape changed')
        return [(r.mnemonic+' '+r.operands, data[r.address:(rows[i+1].address if i+1<len(rows) else len(data))])
                for i, r in enumerate(rows)]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--decoded', type=Path, required=True)
    p.add_argument('--assembler', type=Path, required=True)
    p.add_argument('--objdump', type=Path, required=True)
    a = p.parse_args()
    try:
        data = a.decoded.read_bytes()
        if len(data) != 26214336 or hashlib.sha256(data).hexdigest() != SHA256:
            raise FormatError('private decoded input identity mismatch')
        result = []
        for name, pattern in patterns(a.assembler.resolve(), a.objdump.resolve()):
            hits = bounded_hits(data, pattern)
            if hits:
                result.append(dict(original_pattern=name, candidates=[hex(x) for x in hits]))
        if sum(len(r['candidates']) for r in result) > 512:
            raise FormatError('fixed reference campaign total bound exceeded')
        if hashlib.sha256(a.decoded.read_bytes()).hexdigest() != SHA256:
            raise FormatError('private input changed')
    except (OSError, ValueError, subprocess.SubprocessError):
        p.exit(2, 'STOP: bounded reference validation failed; no OEM data output.\n')
    print(json.dumps({'coordinate':'decoded#0 offsets', 'byte_candidates':result,
                      'qualification':'not code boundaries, typed xrefs or completeness; no OEM operands/bytes exported'}, indent=2))


if __name__ == '__main__':
    main()

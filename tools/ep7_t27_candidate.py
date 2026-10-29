#!/usr/bin/env python3
"""Original E142 v5a assembly overlay; private analysis only, no OE writer.

Design reference (read/run only): fishcu/oly_fw_analysis@539fcf1.
Uses the unchanged, hash-qualified v4 candidate produced by our existing probe.
"""
import json
import struct
import subprocess
from pathlib import Path

from ep7_color_min import BASE, digest, require

PATCH = Path(__file__).resolve().parents[1] / 'patches/hsl-editor/e-p7'
LAYOUT = [('api', 0x6055E5F0, 464), ('apply', 0x60210E3C, 50),
          ('lifecycle', 0x60210E6E, 48), ('ui6', 0x612429F0, 1488),
          ('state', 0x60210FA0, 16)]
POINTERS = [(0x60ACB0DC + off, 'v5_' + name) for off, name in
            [(0, 'set'), (8, 'get'), (24, 'count'), (28, 'enum'),
             (36, 'valid'), (152, 'default')]] + [
                 (0x61187534, 'v5_parent'), (0x611ADA34, 'v5_enter'),
                 (0x611ADA48, 'v5_exit')]
DETOURS = [(0x6082748B, 'apply_detour'), (0x60D1147E, 'lookup_detour'),
           (0x60E26BA1, 'numeric_detour')]
BOUNDS = [(0x60E20F0C, 'upper'), (0x60E2116C, 'lower')]


def overlay(x):
    """Assemble into /tmp, guard stock/v4 spans, return bytes and public receipts."""
    out = x.out / 'v5-assembly'
    out.mkdir()
    symbols = json.loads((PATCH / 'symbols.json').read_text())
    objects = []
    for name in ('api', 'editor'):
        obj = out / (name + '.o')
        subprocess.run([str(x.tools / 'gas/as-new'), '-o', str(obj),
                        str(PATCH / (name + '.s'))], check=True)
        objects.append(str(obj))
    script = out / 'layout.ld'
    script.write_text('PHDRS { code PT_LOAD FLAGS(5); state PT_LOAD FLAGS(6); }\n'
        'SECTIONS {\n' + ''.join(
            f'.ep7_{name} {address:#x} : {{ *(.ep7_{name}) }} '
            f':{"state" if name == "state" else "code"}\n'
            for name, address, _ in LAYOUT) + '}\n')
    elf = out / 'v5.elf'
    subprocess.run([str(x.tools / 'ld/ld-new'), '-T', str(script), '-e', 'v5_get',
        *[f'--defsym={k}={v:#x}' for k, v in symbols.items()], '-o', str(elf),
        *objects], check=True)
    labels = {w[2]: int(w[0], 16) for line in subprocess.check_output(
        [str(x.tools / 'binutils/nm-new'), str(elf)], text=True).splitlines()
        if len(w := line.split()) == 3}
    candidate, records = bytearray(x.candidate), []

    def put(address, code, kind):
        offset = address - BASE
        require(x.data[offset:offset + len(code)] == x.candidate[offset:offset + len(code)],
                'v5 would overwrite a v4 edit')
        original = x.data[offset:offset + len(code)]
        candidate[offset:offset + len(code)] = code
        records.append(dict(address=hex(address), length=len(code), kind=kind,
                            original_sha256=digest(original),
                            replacement_sha256=digest(code)))

    for name, address, capacity in LAYOUT:
        target = out / (name + '.bin')
        subprocess.run([str(x.tools / 'binutils/objcopy'), '-O', 'binary',
                        '--only-section=.ep7_' + name, str(elf), str(target)], check=True)
        code = target.read_bytes()
        require(0 < len(code) <= capacity, 'Qualified span exhausted: ' + name)
        require(x.read(address, len(code)) == b'\xff' * len(code),
                'New code/data span is not untouched FF')
        put(address, code, name)
    for address, label in POINTERS:
        put(address, struct.pack('<I', labels[label]), label)
    for address, name in DETOURS:
        code = x.assemble('v5_' + name + '_site', 'jmp target\n', address,
                          {'target': labels['v5_' + name]})
        require(len(code) == 5, 'Detour size')
        put(address, code, name)
    for address, name in BOUNDS:
        code = x.assemble('v5_' + name + '_site',
                          'jmp target\n', address,
                          {'target': labels['v5_' + name + '_detour']})
        require(len(code) == 5, 'Bound detour size')
        put(address, code, name)
    records.sort(key=lambda r: int(r['address'], 16))
    require(all(int(a['address'], 16) + a['length'] <= int(b['address'], 16)
                for a, b in zip(records, records[1:])), 'Overlapping v5 edits')
    return bytes(candidate), labels, records

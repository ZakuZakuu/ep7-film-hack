#!/usr/bin/env python3
"""GNU-linked byte accounting of our own v4/v5 sources, without OEM input.

The adjacent layout deliberately ignores the mirror: it is an optimistic SIZE
bound, never a placement or executable overlay. The actual footprint fit gate
counts unchanged v4 code, mirror and v5 additions. No package/hash manifest.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess

from ep7_color_min import require
from ep7_t27_candidate import LAYOUT, PATCH
from ep7_t27_compact_source import materialize

CAPACITY, MIRROR_BYTES = 1728, 192
V4 = PATCH.parents[1] / 'hsl-recipes/e-p7'
V4_GROUPS = ('_start', 'wifi_write', 'validate', 'cell_index', 'app_edit',
             'decode_cell', 'publish', 'wifi_read', 'lightness_steps',
             'id_parse', 'value_parse', 'canonical_hex', 'hue_steps')
UI_GROUPS = ('v5_api_override', 'v5_lookup_detour', 'v5_bind', 'v5_parent',
             'v5_axis_value', 'v5_upper_detour', 'v5_numeric_detour')


def fit(v4_bytes, added_bytes):
    remaining = CAPACITY - MIRROR_BYTES - v4_bytes - added_bytes
    return dict(capacity=CAPACITY, v4_code=v4_bytes, mirror=MIRROR_BYTES,
                v5_added=added_bytes, deficit=max(0, -remaining),
                raw_fits=remaining >= 0, placement_qualified=False)


def run(args):
    return subprocess.check_output([str(a) for a in args], text=True)


def labels(nm, elf):
    return {w[2]: int(w[0], 16) for line in run([nm, elf]).splitlines()
            if len(w := line.split()) == 3}


def groups(names, symbols, end):
    points = [symbols[n] for n in names]+[end]
    require(points == sorted(points), 'Functional groups reordered')
    return [dict(function=n, start=hex(a), bytes=b-a)
            for n, a, b in zip(names, points, points[1:])]


def study(upstream, out):
    upstream, out = Path(upstream).resolve(), Path(out).resolve()
    require(Path('/tmp') in out.parents, 'Size artifacts must remain private /tmp')
    require(not out.exists(), 'Fresh output directory required')
    require(run(['git', '-C', upstream, 'rev-parse', 'HEAD']).strip() ==
            '539fcf1fa9eda5fdef8ede4deeab94a4691d94c3', 'Wrong upstream revision')
    tool = upstream/'toolchains/mn103-patch-build'
    assembler, linker = tool/'gas/as-new', tool/'ld/ld-new'
    objcopy, nm = tool/'binutils/objcopy', tool/'binutils/nm-new'
    require('2.45' in run([assembler, '--version']).splitlines()[0], 'GNU 2.45 required')
    out.mkdir(mode=0o700)
    v4obj, v4elf, v4bin = out/'v4.o', out/'v4.elf', out/'v4.bin'
    run([assembler, '-o', v4obj, V4/'hook.s'])
    syms = json.loads((V4/'symbols.json').read_text())
    run([linker, '-Ttext', '0x60210940', '-e', '_start',
         *[f'--defsym={k}={v:#x}' for k,v in syms.items()], '-o', v4elf, v4obj])
    run([objcopy, '-O', 'binary', '-j', '.text', v4elf, v4bin])
    size = v4bin.stat().st_size
    require(size == 1276, 'Frozen v4 size changed')
    v4symbols = labels(nm, v4elf)
    require(v4symbols['cell_index'] == 0x60210B5E, 'Shared v4 helper address changed')
    result = dict(toolchain=run([assembler, '--version']).splitlines()[0],
                  v4=groups(V4_GROUPS, v4symbols, 0x60210940+size),
                  unused_raw_bytes=CAPACITY-size-MIRROR_BYTES, measurements=[])
    for variant in ('original', 'shared', 'dispatch', 'table'):
        path = materialize(out/variant, variant)
        symbols = json.loads((path/'symbols.json').read_text())
        objects = []
        for name in ('api', 'editor'):
            obj = path/(name+'.o')
            run([assembler, '-o', obj, path/(name+'.s')])
            objects.append(obj)
        for layout, relax in (('lab', False), ('adjacent', False), ('adjacent', True)):
            tag = layout+('-relax' if relax else '')
            script, elf = path/(tag+'.ld'), path/(tag+'.elf')
            sections = []
            for name, address, _ in LAYOUT:
                location = hex(address) if layout == 'lab' else 'ALIGN(4)'
                sections.append(f'.ep7_{name} {location} : {{ *(.ep7_{name}) }} '
                                f':{"state" if name == "state" else "code"}')
            script.write_text('PHDRS { code PT_LOAD FLAGS(5); state PT_LOAD FLAGS(6); }\n'
                'SECTIONS { . = 0x60210e3c;\n'+'\n'.join(sections)+'\n}\n')
            run([linker, '-T', script, '-e', 'v5_get',
                 *(['--relax'] if relax else []),
                 *[f'--defsym={k}={v:#x}' for k,v in symbols.items()],
                 '-o', elf, *objects])
            sizes = {}
            for name, _, _ in LAYOUT:
                target = path/(tag+'-'+name+'.bin')
                run([objcopy, '-O', 'binary', '-j', '.ep7_'+name, elf, target])
                sizes[name] = target.stat().st_size
            total = sum(sizes.values())
            lab = labels(nm, elf)
            row = dict(variant=variant, layout=layout, relax=relax,
                       sections=sizes, raw_bytes=total, fit=fit(size, total),
                       executable_placement=False)
            if layout == 'adjacent':
                span = lab['v5_state_ram']+sizes['state']-0x60210e3c
                row.update(padded_span=span, padded_fit=fit(size, span),
                           limit='Ignores fixed mirror and guard gaps; size bound only')
            else:
                row['ui_functions'] = groups(UI_GROUPS +
                    (('v5_profiles',) if variant == 'table' else ()), lab,
                    0x612429F0+sizes['ui6'])
                row['api_functions'] = groups(('v5_get', 'v5_apply_detour'), lab,
                    0x6055E5F0+sizes['api'])
            result['measurements'].append(row)
    result.update(release_manifest_generated=False, package_files_created=False)
    (out/'sizes.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


def main():
    os.umask(0o077)
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--upstream', required=True)
    p.add_argument('--out', required=True)
    a = p.parse_args()
    r = study(a.upstream, a.out)
    print(json.dumps(dict(unused_raw_bytes=r['unused_raw_bytes'],
        measurements=[{k:v for k,v in row.items() if k in
            ('variant','layout','relax','raw_bytes','padded_span','fit','padded_fit')}
            for row in r['measurements']]), indent=2))


if __name__ == '__main__':
    main()

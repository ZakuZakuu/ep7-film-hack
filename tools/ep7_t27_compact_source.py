"""Original T27 source-only size experiments; no firmware writer.

Transforms only our own hash-pinned v5 prototype assembly, referencing the
unchanged v4 helpers. fishcu@539fcf1 is a read/run design reference only.
"""
import hashlib
import json
from pathlib import Path

from ep7_color_min import require
from ep7_t27_candidate import PATCH


def once(text, old, new):
    require(text.count(old) == 1, 'Own source anchor changed: '+old[:50])
    return text.replace(old, new, 1)


def sources(variant):
    require(variant in ('original', 'shared', 'dispatch', 'table'), 'Unknown size variant')
    manifest = json.loads((PATCH/'patch.json').read_text())
    root = PATCH.parents[2]
    for name, expected in manifest['source_sha256'].items():
        require(hashlib.sha256((root/name).read_bytes()).hexdigest() == expected,
                'Frozen prototype dependency changed: '+name)
    result = {}
    for name in ('api.s', 'editor.s', 'symbols.json'):
        path = PATCH/name
        expected = manifest['source_sha256'][str(path.relative_to(root))]
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected,
                'Frozen v5 prototype source changed: '+name)
        result[name] = path.read_text()
    if variant == 'original':
        return result
    editor = result['editor.s']
    # No new H/L codec or storage. Keep the v4 app/read/publish paths intact.
    # Reuse the v4 ID validator rather than duplicate its disjoint ranges.
    start = '    mov a2,d0\n    add -927,d0\n    cmp 35,d0\n    bls stale_color\n    mov a2,d0\n    add -1655,d0\n    cmp 11,d0\n    bhi not_ours\n'
    editor = once(editor, start, '    mov a2,d0\n    call ep7_v4_cell_index,[],4\n    cmp 48,d0\n    bcc not_ours\n')
    old = editor[editor.index('getter:\n'):editor.index('out_value:\n')]
    editor = once(editor, old, 'getter:\n    mov a2,d0\n    call v5_axis_value,[d2,d3,a2,a3],20\n    bra out_value\n')
    symbols = json.loads(result['symbols.json'])
    symbols['ep7_v4_cell_index'] = 0x60210B5E  # Verified own v4 ELF symbol.
    result['symbols.json'] = json.dumps(symbols, indent=2)+'\n'
    if variant == 'shared':
        result['editor.s'] = editor
        return result
    api = result['api.s']
    old = api[api.index('    mov (v5_state+4),d2\n'):api.index('.endm\n')]
    api = once(api, old, '    mov \\kind,d2\n    bra api_active\n')
    # One activation gate after the original common full register/MDR save.
    # All argument, ownership, stale-child and caller checks are retained.
    anchor = '    mov d2,(36,sp)\n    call v5_api_override,[d2,d3,a2,a3],20\n'
    gate = '''    mov d2,(36,sp)
    mov (v5_state+4),d0
    add -1,d0
    cmp 1,d0
    bls api_check_override
    cmp 5,d2
    bne api_passthrough
    cmp 0x60de5d69,d3
    bne api_passthrough
api_check_override:
    mov (4,sp),d0
    call v5_api_override,[d2,d3,a2,a3],20
'''
    api = once(api, anchor, gate)
    api = once(api, '    mov (36,sp),d2\n    asl2 d2\n',
                    'api_passthrough:\n    mov (36,sp),d2\n    asl2 d2\n')
    if variant == 'dispatch':
        result.update({'api.s': api, 'editor.s': editor})
        return result
    # Root/key/mode correspondence is stored once, naturally aligned.
    old = editor[editor.index('    cmp 0x13b3,d1\n', editor.index('v5_bind:')):editor.index('bind_ready:\n')]
    editor = once(editor, old, '''    mov v5_profiles,a1
bind_lookup:
    movhu (a1),d0
    cmp d1,d0
    beq bind_match
    add 8,a1
    cmp v5_profiles_end,a1
    bcs bind_lookup
    bra bind_bad
bind_match:
    movhu (2,a1),d0
''')
    old = editor[editor.index('    cmp 927,d2\n', editor.index('bound_axis:')):editor.index('bound_check:\n')]
    editor = once(editor, old, '''    mov v5_profiles,a2
bound_lookup:
    movhu (2,a2),d1
    cmp d2,d1
    beq bound_match
    add 8,a2
    cmp v5_profiles_end,a2
    bcs bound_lookup
    bra bound_stock
bound_match:
    movhu (4,a2),d1
''')
    editor += '''
.balign 4
v5_profiles:
    .hword 0x13b3,927,54,0
    .hword 0x13b4,939,55,0
    .hword 0x13b5,951,56,0
    .hword 0x140c,1655,64,0
v5_profiles_end:
'''
    result.update({'api.s': api, 'editor.s': editor})
    return result


def materialize(path, variant):
    path = Path(path).resolve()
    require(Path('/tmp') in path.parents, 'Materialized analysis source must be private /tmp')
    path.mkdir(parents=True, exist_ok=False)
    for name, text in sources(variant).items():
        (path/name).write_text(text)
    return path

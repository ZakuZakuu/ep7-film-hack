"""Original source-only T27 split: frozen v4 stays intact, no package writer.

Read/run design reference: fishcu/oly_fw_analysis@539fcf1 EDITOR.md and
SETTINGS_STORAGE.md. Transforms ONLY this repository's own hash-pinned source.
4751/4752 are private GUI argument tags, never HTTP commands or store markers.
Persistent words remain E741CCVV and use the original part/normal-edit APIs.
"""
import json
from pathlib import Path

from ep7_color_min import require
from ep7_t27_compact_source import sources, once
from ep7_t27_candidate import PATCH

V4 = PATCH.parents[1]/'hsl-recipes/e-p7'


def between(text, start, end):
    require(text.count(start) == text.count(end) == 1, 'Own source boundaries changed')
    return text[text.index(start):text.index(end)]


def editor_only():
    result = sources('dispatch')  # Also checks all frozen v4/v5 dependencies.
    old = (V4/'hook.s').read_text()
    image = old[:old.index('/* New CALL target, same ABI')]
    image = image.replace('Original E142/1100 T25 v4.', 'Original E142/1100 editor-only A.')
    cell = between(old, 'cell_index:\n', '/* App-stage CALL replacement.')
    decode = between(old, 'decode_cell:\n', '/* Actual typed COLOR record writer')
    publish = between(old, '.global publish\n', '/* Read extension is fail-closed')
    light = between(old, '.balign 2\nlightness_steps:', '/* Keep the native numeric conversion.')
    hue = old[old.index('.balign 2\nhue_steps:'):]
    apply = between(old, '.global app_edit\n', '/* Encoded u32 -> valid packed slider')
    prefix = between(apply, '    mov d1,d2\n', '    add -20,sp\n')
    apply = once(apply, prefix, '')
    apply = apply.replace('.global app_edit\napp_edit:', '.global a_apply\na_apply:')
    apply = once(apply, 'call validate,', 'call validate_gui,')
    apply = once(apply, '    cmp 0x4550,d0\n    beq scalar_edit\n', '')
    apply = once(apply, 'scalar_edit:\n    mov (8,sp),d1\n    exth d1\n', '')
    apply = once(apply, 'cmp 0x4551,d0', 'cmp 0x4751,d0')
    # The ordinary unmarked application dispatcher is not hooked in v5.
    # Only the already-admitted GUI adapter calls this private entry.
    validate = '''
validate_gui:
    mov d1,d3
    exth d3
    cmp -7,d3
    blt gui_invalid
    cmp 7,d3
    bgt gui_invalid
    lsr 16,d1
    cmp 0x4751,d1
    beq gui_color_key
    cmp 0x4752,d1
    bne gui_invalid
gui_color_key:
    call cell_index,[],4
    cmp 48,d0
    bcc gui_invalid
    clr d0
    ret [d2,d3,a2,a3],20
gui_invalid:
    mov 1,d0
    ret [d2,d3,a2,a3],20
'''
    result['core.s'] = image + '.global cell_index,decode_cell\n' + cell + apply + validate + decode + publish + light + hue
    api, editor = result['api.s'], result['editor.s']
    api = once(api, 'Resident in the qualified settings-code section;',
               'Analysis mapping only; no new placement is qualified;')
    for tag in ('4551', '4552'):
        api = api.replace('0x'+tag, '0x47'+tag[-2:])
        editor = editor.replace('0x'+tag, '0x47'+tag[-2:])
    # Remove the HTTP H/L namespace entirely. The editor consumes the same
    # published pair as imaging, not ACTIVE values during recall staging.
    begin, end = 'v5_axis_value:\n', '.global v5_upper,v5_lower\n'
    current = between(editor, begin, end)
    reader = '''v5_axis_value:
    call cell_index,[],4
    cmp 48,d0
    bcc axis_neutral
    asl2 d0
    mov ep7_mirror,a0
    mov (d0,a0),d0
    mov (v5_state+4),d1
    cmp 1,d1
    bne axis_hue
    asr 16,d0
    bra axis_check
axis_hue:
    exth d0
axis_check:
    cmp -7,d0
    blt axis_neutral
    cmp 7,d0
    ble axis_value_done
axis_neutral:
    clr d0
axis_value_done:
    ret [d2,d3,a2,a3],20

'''
    editor = once(editor, current, reader)
    editor = once(editor, 'call ep7_v4_edit,', 'call a_apply,')
    editor = editor.replace('The v4 helper consumes the same tagged scalar as its Wi-Fi app entry.',
                            'The private GUI helper commits the unchanged E741 storage format.')
    editor = editor.replace('call ep7_v4_cell_index,', 'call cell_index,')
    result['api.s'], result['editor.s'] = api, editor
    symbols = json.loads(result['symbols.json'])
    for k in ('ep7_v4_read', 'ep7_v4_edit', 'ep7_v4_cell_index'):
        symbols.pop(k, None)
    core_symbols = json.loads((V4/'symbols.json').read_text())
    for k in ('ep7_pending','ep7_post','ep7_hex_parse','ep7_raw_set'):
        core_symbols.pop(k)
    symbols.update(core_symbols)
    result['symbols.json'] = json.dumps(symbols, indent=2)+'\n'
    for text in (result['core.s'], api, editor):
        require(all(tag not in text for tag in ('0x4550','0x4551','0x4552',
                'wifi_read:', 'wifi_write:', 'capability:', 'id_parse:', 'value_parse:')),
                'EP71 implementation survived editor-only split')
    return result


def materialize(out):
    out = Path(out).resolve()
    require(Path('/tmp') in out.parents, 'Private analysis sources require /tmp')
    require(not out.exists(), 'Fresh output required')
    data = editor_only()
    out.mkdir(parents=True, mode=0o700)
    for name, text in data.items():
        (out/name).write_text(text)
    return out

#!/usr/bin/env python3
"""Additional bounded editor controls and placement receipts, NOT v5a release."""
import argparse
import copy
import json
import os
import struct
from dataclasses import replace

from ep7_color_min import BASE, SP, digest, require
from ep7_t27_editor_probe import ROOTS, ARG, API, u16, u32
from ep7_t27_ui_flow_probe import FSM, DISPATCH, CTRL, HANDLER
from ep7_t27_v5_probe import Probe, STATE
from ep7_t27_placement import qualify
from ep7_t25_storage_probe import MODE, SIZE, decode


def routing(x):
    s = x.new_state()
    x.fsm(s)
    compared = []
    for event, index in x.native_events:
        expected = hex(x.functions[x.native_matrix[index*5+1]])
        got = x.event(s, event, 2, True)
        require(got == dict(handler=expected, event=hex(event)), 'Existing event changed')
        compared.append(dict(event=hex(event), handler=expected))
    deleted = []
    for root in (*ROOTS, 0x13B2):
        s.write(0x61FC43CC, struct.pack('<H', root))
        for state in range(1, 6):
            for event in (0x9016, 0x9017, 0x9042):
                got = x.event(s, event, state, True)
                eligible = event == 0x9016 and root in ROOTS and state == 2
                require(got == (dict(handler=hex(HANDLER), event=hex(event))
                        if eligible else dict(return_code=3)), 'Delete scope escaped')
                deleted.append(dict(root=hex(root), state=state, event=hex(event),
                                    eligible=eligible))
    return dict(existing_routes=compared, scoped_delete=deleted,
                table_cells_unchanged=235, physical_key_delivery=False)


def controls(x):
    s, p = x.fresh()
    # Original and replacement parent event bodies execute on identical owned
    # RAM (same native v4 routines, same service inputs). Compare actual S.
    baseline = copy.deepcopy(s.__dict__)
    allocation = x.next_alloc
    original = bytearray(x.candidate)
    for row in x.v5_edits:
        a, n = int(row['address'], 16)-BASE, row['length']
        original[a:a+n] = x.data[a:a+n]
    original = bytes(original)
    require(digest(original) == x.v4_candidate_sha,
            'S baseline must be the complete unchanged v4 program')
    patched_instructions = dict(x.instructions)
    out = []
    for target in (0x60DD5250, x.v5['v5_parent']):
        s.__dict__.update(copy.deepcopy(baseline))
        x.next_alloc = allocation
        x.held_mutexes, x.queue_locked = [], False
        image = original if target == 0x60DD5250 else x.candidate
        s.regions = [replace(q, data=image[q.address-BASE:q.address-BASE+len(q.data)])
                     if 'x' in q.permissions and BASE <= q.address < BASE+len(image)
                     else q for q in s.regions]
        x.image.write_bytes(image)
        x.instructions = dict(patched_instructions)
        # Decode the actual control-site bytes for this arm of the comparison;
        # do not audit a restored v4 CALL using the prototype's JMP metadata.
        for address in (0x6082748B, 0x60D1147E, 0x60E26BA1, 0x60E20F0C, 0x60E2116C):
            x.disassemble('S_comparison_'+hex(target)+'_'+hex(address), address, address+5)
        result = []
        for event in (0x9004, 0x9005, 0x9006, 0x9007, 0x9014, 0x9015,
                      0x9004, 0x9005, 0x9006, 0x9007, 0x9014, 0x9015,
                      0x900C, 0x900D):
            result.append(x.ui_call(s, target, '', 0,
                {'a0': p, 'd0': event, 'd1': 0}))
            if event == 0x9015:
                # The original numeric producer derives ALL from the cursor.
                # Use it in both arms; this comparison concerns S state, not
                # the intentional extra caption in the prototype.
                viewer = 0x1C080000
                data = bytearray(412)
                struct.pack_into('<I', data, 384, p)
                struct.pack_into('<I', data, 400, 54)
                s.ram('S_comparison_numeric_viewer', viewer, data, aliases=False)
                x.ui_call(s, 0x60E27289, 'd2,d3,a2,a3', 44,
                          {'a0': viewer, 'a1': viewer})
        out.append((result, digest(s.read(MODE, SIZE)), s.read(p+16, 32),
                    s.read(0x60210EC0, 192)))
    x.image.write_bytes(x.candidate)
    x.instructions = patched_instructions
    require(out[0] == out[1], 'Stock S behavior differs')
    # Patched lookup -> actual FSM handler -> real controller -> actual parent.
    # Stop at controller's first instruction after the parent's returned event;
    # the separate OSD transport/rendering remains outside this fixture.
    x.fsm(s)
    shell = bytearray(228)
    struct.pack_into('<I', shell, 0, p)
    s.ram('owned_editor_controller', CTRL, shell, aliases=False)
    s.write(0x61FC43C0, struct.pack('<I', CTRL))
    s.write(0x61FC43CC, struct.pack('<H', ROOTS[0]))
    s.enter(DISPATCH, '', 0, {'a0': FSM, 'd0': 0x9016, 'd1': 0, 'a1': 0})
    x.run_ui(s, {x.v5['v5_parent']})
    require(s.regs['a0'] == p and s.regs['d0'] == 0x9016,
            'FSM changed local Delete identity')
    require(x.instructions[0x60E4D0FF] == ('calls', '(a1)'),
            'Controller parent dispatch anchor changed')
    x.run_ui(s, {0x60E4D101})
    require(u32(s, STATE+4) == 1, 'FSM Delete did not switch to L')
    # API consumers other than the reviewed child/numeric call sites retain S.
    require(x.app(s, 927, 0x45520003) == 0, 'Independent L seed')
    display = display_contract(x, s, p)
    x.ui_call(s, x.v5['v5_get'], '', 0, {'a0': API, 'd0': 927, 'a1': ARG})
    require(u32(s, ARG) == 0, 'Virtual H/L escaped its caller whitelist')
    # A nonzero S witness distinguishes preserving S from accidentally
    # zeroing it, including the unchanged post-setting notification packet.
    require(x.app(s, 927, 0x4550FFFE) == 0, 'Independent native S=-2 seed')
    x.active_application(s)
    x.release(s, p, 0x9004)  # L +3 -> +4; S must remain -2.
    require(x.peer_events[-1]['service'] == 'setting_notice'
            and x.peer_events[-1]['value'] == -2
            and struct.unpack('<h', s.read(0x6250F860, 2))[0] == -2,
            'H/L edit replaced S or leaked its value into S coordination')
    nonzero_S_notice = dict(x.peer_events[-1])
    from ep7_t27_editor_fixture import LOCATOR, COORDINATOR
    x.active_peer = False
    s.write(LOCATOR+4, bytes(4))
    s.write(COORDINATOR+4, bytes(12))
    child = u32(s, p+128)
    require(u16(s, child+88) == 15, 'Expected native L enumeration')
    s.write(STATE, bytes(16))
    before = s.read(MODE, SIZE), s.read(0x60210EC0, 192)
    x.ui_call(s, 0x60DE9920, '', 0, {'a0': child})
    require(before == (s.read(MODE, SIZE), s.read(0x60210EC0, 192)),
            'Reset volatile state leaked a stale virtual child into S')
    # The next parent event rebinds in S and natively rebuilds all stale enums.
    x.parent_event(s, p, 0x9005)
    require(all(u16(s, u32(s, p+128+4*i)+88) == 11 for i in range(12)),
            'Stale S enumeration recovery')
    for name, native_entry in [('v5_enter', 0x60E76396), ('v5_exit', 0x60E76BCF)]:
        s.write(STATE, struct.pack('<4I', p, 2, ROOTS[0], 927))
        s.enter(x.v5[name], '', 0, {})
        x.run_ui(s, {native_entry})
        require(s.read(STATE, 16) == bytes(16), 'Axis lifecycle did not clear')
    # Corrupt an owned synchronization input. There is no fallback successful
    # mutex for other objects and no global zero-filled kernel RAM.
    from ep7_t27_editor_fixture import RESOURCE_TABLE
    s.write(RESOURCE_TABLE+20, struct.pack('<I', 0x1BFF4000))
    try:
        x.ui_call(s, 0x607FA129, '', 0,
                  {'a0': API, 'd0': 927, 'd1': 0, 'a1': 1})
    except ValueError as exc:
        require('Unmodeled GUI synchronization object' in str(exc),
                'Unexpected unknown-mutex failure')
    else:
        raise ValueError('An unowned mutex was accepted')
    return dict(S_codes=out[0][0], S_Mode_and_mirror_equal=True,
                S_comparison_baseline_sha256=digest(original),
                S_ALL_up_down_on_unmodified_v4=True,
                delete_chain=['0x60d11448', hex(HANDLER), '0x60e4d032',
                              hex(x.v5['v5_parent'])],
                stops_before_viewer=True, unrelated_API_reads_S=True,
                stale_virtual_child_rejected=True, S_rebuilt_after_reload=True,
                entry_exit_clear_before_native_bodies=True,
                unknown_sync_object_rejected=True, produced_display=display,
                nonzero_S_notice=nonzero_S_notice)


def display_contract(x, s, parent):
    """Actual new record -> native text/visibility consumers, no glyph engine."""
    x.caption(s, parent, 0, 'L +3')
    payload = s.read(0x1C080004, 334)
    obj, widgets = 0x1C090000, 0x1C0A0000
    record = bytearray(1360)
    for i in (1, 6, 7, 8, 9, *range(19, 27)):
        struct.pack_into('<I', record, 792+i*4, widgets+i*512)
    record[1024:1024+334] = payload
    s.ram('owned_real_producer_record_receiver', obj, record, aliases=False)
    s.enter(0x60D7AE4A, 'd2,a2,a3', 32, {'a0': obj})
    x.run_ui(s, {0x60E84549})
    require((s.regs['a0'], s.regs['d0']) == (widgets+512, 1),
            'Produced caption visibility')
    s.return_from_model(0)  # Declared drawing/dirty service, result discarded.
    x.run_ui(s, {0x60D4C9DF})
    require(s.regs['a0'] == widgets+7*512 and
            s.read(s.regs['a1'], 10) == 'L +3\0'.encode('utf-16le'),
            'Real record did not reach native text setter')
    s.enter(0x60D7B014, 'a2,a3', 40, {'a0': obj})
    visible, frames = {}, []
    for _ in range(20):
        x.run_ui(s, {s.finish, 0x60E84549, 0x60E8456D})
        if s.regs['pc'] == s.finish:
            break
        pointer = s.regs['a0']
        require(pointer >= widgets and (pointer-widgets) % 512 == 0,
                'Unowned drawing primitive receiver')
        index = (pointer-widgets)//512
        require(19 <= index <= 26, 'Unreviewed number-group widget')
        if s.regs['pc'] == 0x60E84549:
            require(s.regs['d0'] in (0, 1), 'Drawing visibility contract')
            visible[index] = s.regs['d0']
        else:
            frames.append(dict(widget=index, frame=s.regs['d0']))
        s.return_from_model(0)
    else:
        raise ValueError('Drawing primitive budget')
    require(visible[24] == visible[25] == 0 and s.regs['sp'] == SP,
            'Original digits were not hidden by produced zero selectors')
    return dict(actual_produced_text='L +3', text_setter='0x60d4c9df',
                native_visibility_commands={str(k):v for k,v in visible.items()},
                native_frame_commands=frames, glyphs_or_pixels_executed=False,
                drawing_primitives='Explicit void service models; command arguments verified')


def gui_s_bridge(x):
    """Edit S through the actual GUI first, then L/H; no app-seeded S shortcut."""
    s, parent = x.fresh()

    def current_S():
        require(x.ui_call(s, 0x607F9549, '', 0,
                         {'a0': API, 'd0': 927, 'a1': ARG}) == 0, 'GUI S query')
        return struct.unpack('<i', s.read(ARG, 4))[0]

    x.release(s, parent, 0x9006)
    before = current_S()
    raw_before = x.native(s, 0x602CBC0A, '', 4, {'d0': 927})
    require(before == -1, 'Native S down did not edit the first color')
    x.parent_event(s, parent, 0x9016)
    x.release(s, parent, 0x9004)
    after_L, pair_L = current_S(), decode(x.part_read(s, 927))
    require(after_L == before and pair_L == (0, 1), 'GUI S edit lost on L edit')
    x.parent_event(s, parent, 0x9016)
    x.release(s, parent, 0x9006)
    after_H, pair_H = current_S(), decode(x.part_read(s, 927))
    require(after_H == before and pair_H == (-1, 1), 'GUI S edit lost on H edit')
    return dict(GUI_S_before=before, raw_S_before=raw_before,
                GUI_S_after_L=after_L, pair_after_L=list(pair_L),
                GUI_S_after_H=after_H, pair_after_H=list(pair_H))


def dials(x):
    """Preserve the stock cursor convention; never guess dial orientation."""
    s, parent = x.fresh()
    x.app(s, 927, 0x45520003)
    x.fsm(s)
    shell = bytearray(228)
    struct.pack_into('<I', shell, 0, parent)
    s.ram('owned_dial_controller', CTRL, shell, aliases=False)
    s.write(0x61FC43C0, struct.pack('<I', CTRL))
    s.write(0x61FC43CC, struct.pack('<H', ROOTS[0]))
    original_S = s.read(0x6250F860, 24)

    def event(code, delta=0):
        # 60ea3b35 natively reads this signed halfword. D1 is the original
        # controller event argument; neither input is a measured encoder.
        s.write(0x61FC4FB8, struct.pack('<h', delta))
        s.write(FSM+1, b'\2')
        s.enter(DISPATCH, '', 0,
                {'a0': FSM, 'd0': code, 'd1': delta & 0xFFFFFFFF, 'a1': 0})
        x.run_ui(s, {0x60E4D101})

    def cursor_value():
        # Use the SAME GUI property interface as the native numeric producer.
        # A raw settings read is not evidence of the working GUI cursor.
        require(x.ui_call(s, 0x607F9549, '', 0,
                         {'a0': API, 'd0': 1091, 'a1': ARG}) == 0,
                'Native GUI cursor query failed')
        return u32(s, ARG)

    snapshot, allocation = copy.deepcopy(s.__dict__), x.next_alloc
    instructions = dict(x.instructions)
    reference = bytearray(x.candidate)
    for row in x.v5_edits:
        a, n = int(row['address'], 16)-BASE, row['length']
        reference[a:a+n] = x.data[a:a+n]
    reference = bytes(reference)
    require(digest(reference) == x.v4_candidate_sha, 'Dial baseline is not v4')
    s.regions = [replace(q, data=reference[q.address-BASE:q.address-BASE+len(q.data)])
                 if 'x' in q.permissions and BASE <= q.address < BASE+len(reference)
                 else q for q in s.regions]
    x.image.write_bytes(reference)
    for address in (0x6082748B, 0x60D1147E, 0x60E20F0C, 0x60E2116C):
        x.disassemble('dial_reference_'+hex(address), address, address+5)
    initial_cursor = cursor_value()
    event(0x9031, 1)
    cursor = cursor_value()
    observation = dict(initial_GUI_cursor=initial_cursor, reference_GUI_cursor=cursor,
        raw_setting=x.native(s, 0x602CBC0A, '', 4, {'d0': 1091}),
        parent_selected_child=u16(s, parent+122),
        cursor_child_index=u16(s, u32(s, parent+124)+90))
    (x.out/'dial-reference-observation.json').write_text(json.dumps(observation, indent=2)+'\n')
    s.__dict__.update(copy.deepcopy(snapshot))
    x.next_alloc, x.held_mutexes, x.queue_locked = allocation, [], False
    x.image.write_bytes(x.candidate)
    x.instructions = instructions
    require(initial_cursor == 1, 'Reference fixture did not begin on GUI cursor 1')
    require(cursor in (*range(2, 13), 255),
            'Declared dial inputs did not move even the unchanged v4 cursor: '+str(cursor))

    event(0x9016)
    require(u32(s, STATE+4) == 1, 'FSM Delete did not select L')
    event(0x9031, 1)
    actual = cursor_value()
    require(actual == cursor, 'Prototype cursor differs from the actual v4 convention')
    x.caption(s, parent, 0, 'L ALL' if cursor == 255 else 'L +0')
    event(0x9032, 1)
    expected = [3] + [0]*11
    for i in (range(12) if cursor == 255 else (cursor-1,)):
        expected[i] -= 1
    require(x.pairs(s, 0) == [(0, v) for v in expected], 'Value dial did not edit current L selection')
    event(0x9031, -1)
    require(cursor_value() == 1,
            'Selection dial did not restore the shared cursor')
    x.caption(s, parent, 0, 'L +'+str(expected[0]))
    event(0x9032, -1)
    expected[0] += 1
    require(x.pairs(s, 0) == [(0, v) for v in expected], 'Inverse value dial failed')
    L_caption = x.caption(s, parent, 0, 'L +'+str(expected[0]))
    event(0x9016)
    require(u32(s, STATE+4) == 2, 'FSM Delete did not select H')
    event(0x9031, 1)
    x.caption(s, parent, 0, 'H ALL' if cursor == 255 else 'H +0')
    event(0x9032, -1)
    hue = [int(cursor == 255 or i == cursor-1) for i in range(12)]
    require(x.pairs(s, 0) == list(zip(hue, expected))
            and s.read(0x6250F860, 24) == original_S,
            'Dial axis selection lost L or changed S')
    H_caption = x.caption(s, parent, 0, 'H ALL' if cursor == 255 else 'H +1')
    return dict(selection_event='0x9031', value_event='0x9032',
                original_parent_return='0x60e4d101', shared_cursor=[1, cursor, 1, cursor],
                reference_v4_sha256=digest(reference), H=hue, L=expected,
                cursor_observation=observation,
                captions=[L_caption, H_caption], S_unchanged=True,
                scope='Owned latched delta + D1; actual v4 reference; native FSM/controller/parent; stop before viewer, no physical encoders')


def main():
    os.umask(0o077)
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('stock', 'upstream', 'out'):
        p.add_argument('--'+name, required=True)
    a = p.parse_args()
    x = Probe(a.upstream, a.stock, a.out)
    x.prepare()
    result = {}
    try:
        result['placement'] = qualify(x)
        (x.out/'aux.json').write_text(json.dumps(result, indent=2)+'\n')
        result['routing'] = routing(x)
        (x.out/'aux.json').write_text(json.dumps(result, indent=2)+'\n')
        result['controls'] = controls(x)
        (x.out/'aux.json').write_text(json.dumps(result, indent=2)+'\n')
        result['GUI_S_bridge'] = gui_s_bridge(x)
        (x.out/'aux.json').write_text(json.dumps(result, indent=2)+'\n')
        try:
            result['dials'] = dict(passed=True, **dials(x))
        except ValueError as exc:
            if not str(exc).startswith('Declared dial inputs did not move even the unchanged v4 cursor:'):
                raise
            result['dials'] = dict(passed=False, reason=str(exc),
                observation=json.loads((x.out/'dial-reference-observation.json').read_text()),
                conclusion='Declared input/context is insufficient even on v4; do not claim prototype dial failure or success',
                stop='Nominal event replay and independent unchanged-v4 GUI property reference exhausted; no guessed focus/activation fields')
        (x.out/'aux.json').write_text(json.dumps(result, indent=2)+'\n')
    finally:
        x.trace.close()
    print(json.dumps(dict(placement_qualified=result['placement']['qualified'],
                          dial_qualified=result['dials']['passed'],
                          routes=len(result['routing']['existing_routes']))))


if __name__ == '__main__':
    main()

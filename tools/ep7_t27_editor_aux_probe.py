#!/usr/bin/env python3
"""Additional bounded editor controls and placement receipts, NOT v5a release."""
import argparse
import copy
import json
import os
import struct

from ep7_color_min import SP, digest, require
from ep7_t27_editor_probe import ROOTS, ARG, API, u16, u32
from ep7_t27_ui_flow_probe import FSM, DISPATCH, CTRL, HANDLER
from ep7_t27_v5_probe import Probe, STATE
from ep7_t27_placement import qualify
from ep7_t25_storage_probe import MODE, SIZE


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
    out = []
    for target in (0x60DD5250, x.v5['v5_parent']):
        s.__dict__.update(copy.deepcopy(baseline))
        x.held_mutexes, x.queue_locked = [], False
        result = []
        for event in (0x9004, 0x9005, 0x9006, 0x9007, 0x900C, 0x900D):
            result.append(x.ui_call(s, target, '', 0,
                {'a0': p, 'd0': event, 'd1': 0}))
        out.append((result, digest(s.read(MODE, SIZE)), s.read(p+16, 32),
                    s.read(0x60210EC0, 192)))
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
    x.ui_call(s, x.v5['v5_get'], '', 0, {'a0': API, 'd0': 927, 'a1': ARG})
    require(u32(s, ARG) == 0, 'Virtual H/L escaped its caller whitelist')
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
    for name, original in [('v5_enter', 0x60E76396), ('v5_exit', 0x60E76BCF)]:
        s.write(STATE, struct.pack('<4I', p, 2, ROOTS[0], 927))
        s.enter(x.v5[name], '', 0, {})
        x.run_ui(s, {original})
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
                delete_chain=['0x60d11448', hex(HANDLER), '0x60e4d032',
                              hex(x.v5['v5_parent'])],
                stops_before_viewer=True, unrelated_API_reads_S=True,
                stale_virtual_child_rejected=True, S_rebuilt_after_reload=True,
                entry_exit_clear_before_native_bodies=True,
                unknown_sync_object_rejected=True)


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
    finally:
        x.trace.close()
    print(json.dumps(dict(placement_qualified=result['placement']['qualified'],
                          routes=len(result['routing']['existing_routes']))))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Bounded original E142 input producer -> GUI -> COLOR dial replay.

Read/run reference: fishcu/oly_fw_analysis@539fcf1, not copied code.
The encoder backend alone supplies a declared signed count/status. Native
filtering, the latch, packet fields, task bridge, FSM and controls execute.
No physical encoder, scheduling, rendering, boot or installation is claimed.
All original data, disassembly and native traces must remain under /tmp.
"""
import argparse
import copy
import json
import os
import struct
from dataclasses import replace

from ep7_color_min import BASE, SP, digest, require
from ep7_t27_editor_probe import API, ARG, CURSORS, FIRST, ROOTS, u16, u32
from ep7_t27_ui_flow_probe import FSM, CTRL
from ep7_t27_v5_probe import Probe, STATE

ENCODER = 0x60771B67
REMEMBERED = (1098, 1099, 1100, 1687)
PACKET = SP + 396  # The original GUI worker's reviewed local message layout.
BRIDGE = 0x60CFD546
BRIDGE_RETURN = 0x60CFD55F


class DialProbe(Probe):
    def prepare(self):
        super().prepare()
        self.prototype = self.candidate
        stock_v4 = bytearray(self.prototype)
        for row in self.v5_edits:
            a = int(row['address'], 16)-BASE
            stock_v4[a:a+row['length']] = self.data[a:a+row['length']]
        self.reference = bytes(stock_v4)
        require(digest(self.reference) == self.v4_candidate_sha,
                'Dial reference must be complete unchanged v4')
        self.encoder_calls = []
        self.encoder_input = None
        for a, z in ((0x60CFD539, 0x60CFD55F), (0x60E9FA88, 0x60E9FDAA),
                     (0x60EA0037, 0x60EA012A), (0x607B013F, 0x607B01C0),
                     (0x60EA3B2C, 0x60EA3B3F), (0x60E21CAE, 0x60E21D01),
                     (0x60E21EFB, 0x60E21F48), (0x60DE5B91, 0x60DE5BD1)):
            self.disassemble('dial_'+hex(a), a, z)
        require(self.instructions[0x60CFD53A] ==
                ('call', '0x60e9fa88,[d2,a2,a3],224'), 'Input filter ABI')
        require(self.instructions[0x60CFD54A] == ('mov', '(408,sp),a1')
                and self.instructions[0x60CFD54E] == ('mov', '(412,sp),d1'),
                'Native task message arguments changed')
        require(self.instructions[0x607B0189] ==
                ('call', '0x60771b67,[d2,a2],12'), 'Encoder boundary ABI')

    def select_program(self, prototype, state=None):
        """Switch real ROM and decoder metadata together; never partial v4."""
        self.candidate = self.prototype if prototype else self.reference
        self.image.write_bytes(self.candidate)
        if state is not None:
            state.regions = [replace(q, data=self.candidate[q.address-BASE:
                q.address-BASE+len(q.data)]) if 'x' in q.permissions and
                BASE <= q.address < BASE+len(self.candidate) else q
                for q in state.regions]
        for row in self.v5_edits:
            if row['kind'] in ('api', 'apply', 'lifecycle', 'ui6', 'state'):
                continue
            a = int(row['address'], 16)
            self.disassemble('selected_'+hex(a), a, a+row['length'])

    def run_ui(self, s, stops):
        for _ in range(16):
            super().run_ui(s, set(stops) | {ENCODER})
            if s.regs['pc'] in stops:
                return
            require(self.encoder_input is not None, 'Unsolicited encoder request')
            event, delta, status = self.encoder_input
            selector = 1 if event == 0x9031 else 0
            require(s.regs['mdr'] == 0x607B0190
                    and s.regs['a0'] == 0x1BFF1000
                    and s.regs['d0'] == selector,
                    'Unreviewed encoder caller/object/selector')
            target = s.regs['a1']
            # Outer filter frame 224; native dial callback adds 36/28 bytes
            # and places the halfword at its own +16/+12 respectively.
            require(target == SP-(244 if selector else 240) and target % 2 == 0,
                    'Encoder result must be native aligned stack halfword')
            s.write(target, struct.pack('<h', delta))
            self.encoder_calls.append(dict(event=hex(event), selector=selector,
                                           count=delta, status=status))
            s.return_from_model(status)
        raise ValueError('Finite encoder boundary budget')

    def attach(self, s, parent, slot):
        # The input filter records suppressed messages in a 120 x 16-byte
        # history ring. Run its real allocator/clear initializer; do not stub
        # logging or supply a broad zero-filled GUI memory range.
        s.ram('owned_event_history_header', 0x62472FC4, b'\xa5'*8)
        self.ui_call(s, 0x60E9E82C, 'd2,d3', 12, {})
        self.fsm(s)
        shell = bytearray(228)
        struct.pack_into('<I', shell, 0, parent)
        s.ram('owned_dial_controller', CTRL, shell, aliases=False)
        s.write(0x61FC43C0, struct.pack('<I', CTRL))
        s.write(0x61FC43CC, struct.pack('<H', ROOTS[slot]))
        s.write(0x61FB2564, struct.pack('<I', FSM))

    def query(self, s, key):
        require(self.ui_call(s, 0x607F9549, '', 0,
                dict(a0=API, d0=key, a1=ARG)) == 0, 'GUI property query')
        return u32(s, ARG)

    def event(self, s, code, delta=0, status=0):
        require(code in (0x9031, 0x9032, 0x9016), 'Unreviewed event')
        # These 20 bytes are explicit received-message input, not a RAM dump.
        s.write(PACKET, struct.pack('<5I', code, 0, 0, 0, 0))
        if code != 0x9016:
            require(-2 <= delta <= 2 and status in (0, 1), 'Encoder fixture bounds')
            self.encoder_input = (code, delta, status)
            n = len(self.encoder_calls)
            try:
                filtered = self.ui_call(s, 0x60E9FA88, 'd2,a2,a3', 224,
                                        dict(a0=PACKET))
            finally:
                self.encoder_input = None
            require(len(self.encoder_calls) == n+1, 'Input bypassed encoder boundary')
            packet = list(struct.unpack('<5I', s.read(PACKET, 20)))
            require(u16(s, 0x61FC4FB8) == delta & 0xFFFF, 'Native signed latch')
            require(packet[0] == code and packet[4] == 0,
                    'Input producer changed event or D1')
            require(filtered == int(status != 0 or delta == 0), 'Native filter decision')
            if filtered:
                return dict(code=hex(code), count=delta, filtered=True, packet=packet)
        else:
            # Delete is already a decoded key message; no encoder API is used.
            packet = list(struct.unpack('<5I', s.read(PACKET, 20)))
        # Continue ORIGINAL task instructions over the SAME message and stack.
        # Stop before viewer/redraw and the receive loop; no scheduling model.
        s.regs.update(pc=BRIDGE, sp=SP)
        self.run_ui(s, {BRIDGE_RETURN})
        require(s.regs['sp'] == SP, 'Task bridge/GUI return stack')
        return dict(code=hex(code), count=delta, filtered=False,
                    packet=packet, GUI_return=True)

    def sector_state(self, s, p, slot):
        return dict(cursor=self.query(s, CURSORS[slot]),
                    remembered=self.query(s, REMEMBERED[slot]),
                    native_index=u16(s, u32(s, p+124)+90))

    def replay(self, slot, snapshot, parent, allocation, prototype):
        self.select_program(prototype)
        s = self.new_state()
        s.__dict__.update(copy.deepcopy(snapshot))
        self.select_program(prototype, s)
        if not prototype:
            from ep7_t27_placement_review import remove_regions
            spans = [(int(row['address'], 16), int(row['address'], 16)+row['length'])
                     for row in self.v5_edits if row['kind'] in
                     ('api', 'apply', 'lifecycle', 'ui6', 'state')]
            s.regions = remove_regions(s.regions,
                [(a+alias, z+alias) for a,z in spans for alias in (0, 0x40000000)])
        self.next_alloc = allocation
        self.held_mutexes, self.sync_events, self.peer_events = [], [], []
        self.queue_locked = self.active_peer = False
        self.attach(s, parent, slot)
        initial = self.sector_state(s, parent, slot)
        # Original cold owned MODE has remembered sector 0. Do NOT write a
        # focus/index/remembered field: one real native dial event warms it.
        warmup = self.event(s, 0x9031, 1)
        warm = self.sector_state(s, parent, slot)
        require(initial == dict(cursor=1, remembered=0, native_index=0)
                and warm == dict(cursor=1, remembered=1, native_index=1),
                'Cold/warm native cursor convention changed')
        no_op = [self.event(s, 0x9031, 0), self.event(s, 0x9032, 1, 1)]
        require(self.sector_state(s, parent, slot) == warm, 'Rejected input moved cursor')
        records = []
        stock_S = s.read(0x6250F860, 24)
        for axis in ((0, 1, 2, 0) if prototype else (0,)):
            if prototype:
                for _ in range(3):
                    if u32(s, STATE+4) == axis:
                        break
                    self.event(s, 0x9016)
                require(u32(s, STATE+4) == axis, 'Delete did not cycle requested axis')
            before = self.sector_state(s, parent, slot)
            require(before == warm, 'Axis switch lost shared native cursor')
            self.event(s, 0x9031, 1)
            selected = self.sector_state(s, parent, slot)
            require(selected == dict(cursor=2, remembered=2, native_index=2),
                    'Real input did not select sector 2')
            key = FIRST[slot]+1
            if axis:
                old_pairs = self.pairs(s, slot)
                old = old_pairs[1][int(axis == 1)]
            else:
                old = self.query(s, key)
            self.event(s, 0x9032, -1)
            if axis:
                now = self.pairs(s, slot)
                expected = list(old_pairs)
                pair = list(expected[1]);pair[int(axis == 1)] = old+1
                expected[1] = tuple(pair)
                require(now == expected, 'Value dial modified wrong sector/axis')
                require(s.read(0x6250F860, 24) == stock_S, 'H/L dial changed S')
            else:
                require(self.query(s, key) == (old+1) & 0xFFFFFFFF, 'Native S value dial')
            self.event(s, 0x9032, 1)
            if axis:
                require(self.pairs(s, slot) == old_pairs, 'Inverse H/L value dial')
            else:
                require(self.query(s, key) == old, 'Inverse S value dial')
            self.event(s, 0x9031, -1)
            require(self.sector_state(s, parent, slot) == warm,
                    'Inverse selection dial did not restore sector 1')
            records.append(dict(axis=('S', 'L', 'H')[axis], selected=selected,
                                current_axis_only=True, inverse=True))
        # Full-count hardware latch versus clipped event argument, both native.
        packet = self.event(s, 0x9031, 2)
        require(self.sector_state(s, parent, slot)['cursor'] == 3
                and packet['packet'][3] == 2 and packet['packet'][4] == 0,
                'Multi-detent latch/packet mismatch')
        self.event(s, 0x9031, -2)
        require(self.sector_state(s, parent, slot) == warm, 'Inverse two-detent movement')
        return dict(program='prototype' if prototype else 'unchanged_v4',
                    slot=slot+1, image_sha256=digest(self.candidate), initial=initial,
                    warm=warm, warmup=warmup, suppressed=no_op, axes=records,
                    multi_detent=True, no_guessed_cursor_or_focus_writes=True,
                    unqualified_spans_unmapped=not prototype)


def main():
    os.umask(0o077)
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('stock', 'upstream', 'out'):
        p.add_argument('--'+name, required=True)
    p.add_argument('--slots', nargs='+', type=int, default=[1, 2, 3, 4])
    a = p.parse_args()
    require(a.slots and len(a.slots) == len(set(a.slots)) and
            all(1 <= i <= 4 for i in a.slots), 'Unique COLOR slots 1..4 required')
    x = DialProbe(a.upstream, a.stock, a.out)
    x.prepare()
    result = dict(passed=False, baseline_sha256=digest(x.reference),
                  prototype_sha256=digest(x.prototype), cases=[],
                  models='Existing bounded GUI fixture + encoder API count/status only',
                  limits='Owned received input, no physical encoder/RTOS/viewer or complete startup')
    try:
        for slot in a.slots:
            x.select_program(False)
            s, parent = x.fresh(slot-1)
            snapshot, allocation = copy.deepcopy(s.__dict__), x.next_alloc
            for prototype in (False, True):
                result['phase'] = f'COLOR{slot}, prototype={prototype}'
                (x.out/'dial.json').write_text(json.dumps(result, indent=2)+'\n')
                result['cases'].append(x.replay(slot-1, snapshot, parent, allocation, prototype))
        result.update(passed=True, encoder_calls=x.encoder_calls,
                      steps=x.gnu_steps, aligned_accesses=x.aligned)
        (x.out/'dial.json').write_text(json.dumps(result, indent=2)+'\n')
    finally:
        x.trace.close()
    print(json.dumps(dict(passed=True, cases=len(result['cases']))))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Finite E142/1100 native editor map and replay, NOT a v5 implementation.

Run/read-only reference: fishcu/oly_fw_analysis@539fcf1, PEN-F EDITOR.md,
EDIT_AND_CAPTURE_MAP.md and SETTINGS_STORAGE.md. No upstream implementation
or PEN-F addresses are included. Reuses this repository's v4 fixture and the
separately obtained GNU engine. OEM images, listings and traces stay in /tmp.
Allocator, diagnostics and timer services are explicit finite models. Native
property metadata, enum conversion, constructors and child event code execute.
Unknown memory/services stop; there is no camera, network or install-file I/O.
"""
import argparse
import gzip
import json
import os
import struct

from ep7_color_min import BASE, SP, STOCK_SHA, MAIN_SHA, digest, require
from ep7_t25_v4_probe import Probe as V4

ROOTS = (0x13B3, 0x13B4, 0x13B5, 0x140C)
CURSORS = (1091, 1096, 1097, 1686)
FIRST = (927, 939, 951, 1655)
API, ARG = 0x1C000000, 0x1C001000
HEAP, HEAP_END = 0x1C010000, 0x1C030000
INIT_START, INIT_END, INIT_RAM = 0x2107E0, 0x23EB30, 0x61F98540
LOGS = frozenset((
    0x607706AF, 0x60767EE5, 0x60767F0C, 0x6076DF51, 0x6076E146,
    0x6076E178, 0x6076E1BB, 0x6076E1E9, 0x6076E1F8, 0x6076E207,
    0x6076E216, 0x6076E27C, 0x60E9E127, 0x60E9E050,
))
MODELS = LOGS | {0x60A4EC03, 0x60A4EC0D, 0x60A4EC21,
                 0x60EA15CA, 0x60EA15A3, 0x607B3C32, 0x1C000100,
                 0x60CF779D, 0x1C000120}
WINDOWS = (
    (0x60DE33A7, 0x60DE33C8), (0x60DE34BB, 0x60DE3670),
    (0x60DE3670, 0x60DE3A01), (0x60DE83B7, 0x60DE857F),
    (0x60DE55FA, 0x60DE5767), (0x60DE9886, 0x60DE995A),
    (0x60DE5AB8, 0x60DE5F9F), (0x60E2054E, 0x60E208C5),
    (0x60E20ACA, 0x60E20B2D), (0x60E20CDC, 0x60E212F0),
    (0x60DD5250, 0x60DD5787), (0x607F9549, 0x607F96DD),
    (0x607F9912, 0x607F9999), (0x607FA129, 0x607FA3C5),
    (0x60827440, 0x608274E0), (0x607E945B, 0x607E9535),
    (0x607996EF, 0x607997F2), (0x60E27289, 0x60E274AE),
    (0x60E27950, 0x60E27AB1), (0x60E21FA6, 0x60E223AE),
    (0x60D1050A, 0x60D10586),
    (0x607F90C7, 0x607F90F9),
)


def u16(s, a):
    return struct.unpack('<H', s.read(a, 2))[0]


def u32(s, a):
    return struct.unpack('<I', s.read(a, 4))[0]


class Probe(V4):
    def prepare(self):
        super().prepare()
        self.next_alloc = HEAP
        self.model_counts = {}
        self.aligned = 0
        self.gnu_steps = 0
        self.executed_pcs = set()
        for a, b in WINDOWS:
            self.disassemble(f'editor_{a:x}', a, b)
        self.trace = gzip.open(self.out / 'editor-private.jsonl.gz', 'wt')

    def new_state(self):
        s = super().new_state()
        # T14's bounded startup-copy map, NOT an invented live heap snapshot.
        # Includes the native default child handler vector at 61fc2728.
        s.ram('copied_native_initializer', INIT_RAM,
              self.data[INIT_START:INIT_END])
        return s

    def fixture(self):
        s = self.state()
        # Native 32-bucket/201-node enum filter index; do not zero away filters.
        s.ram('enum_filter_index', 0x62246E10, bytes(128 + 201 * 8))
        self.native(s, 0x602B32D8, 'd2,a2,a3', 12, {})
        s.ram('enum_recursion_depth', 0x62246E0C, bytes(1))
        # Constructor writes twelve entry-time comparison values here; this is
        # an owned fresh GUI snapshot, not settings storage.
        s.ram('parent_entry_comparison', 0x6246ECBC, bytes(48))
        cache = bytearray(152)
        for off in (68, 144):
            struct.pack_into('<H', cache, off, 3200)
        s.ram('two_empty_enum_cache_slots', 0x62245800, cache)
        s.ram('api_singleton', 0x61FA96AC, struct.pack('<I', API))
        s.ram('owned_api_object', API,
              struct.pack('<II', 0x60ACB0DC, API + 0x80), aliases=False)
        s.ram('availability_object', API + 0x80,
              struct.pack('<II', API + 0x90, 0), aliases=False)
        s.ram('availability_vtable', API + 0x90,
              struct.pack('<I', API + 0x100), aliases=False)
        s.ram('availability_service', API + 0x100, self.rets,
              aliases=False, executable=True)
        s.ram('context_query_service', API + 0x120, self.rets,
              aliases=False, executable=True)
        s.ram('context_query_object', API + 0x200,
              struct.pack('<I', API + 0x210), aliases=False)
        query = bytearray(48)
        struct.pack_into('<I', query, 44, API + 0x120)
        s.ram('context_query_vtable', API + 0x210, query, aliases=False)
        s.ram('owned_factory_argument', ARG, bytes(144), aliases=False)
        return s

    def run_ui(self, s, stops):
        """Full-trace GNU slices; models never change native setting values."""
        from penf_boot_emulator import HOOK_RETURN
        for _ in range(10000):
            result = self.provider.execute(
                s.regions, s.regs, 0xFFFFFFFF,
                breakpoints=set(stops) | MODELS, limit=50000,
                trace_limit=50000, changed_captures=True,
            )
            # Explicitly synchronize the existing state container, not a CPU
            # implementation. Record raw engine output privately first.
            self.trace.write(json.dumps(result) + '\n')
            for item in result['memory']:
                s.write(s.regions[item['index']].address,
                        bytes.fromhex(item['hex']))
            s.regs = result['registers']
            require(not result['trace_truncated'], 'Incomplete native trace')
            rows = [r for r in result['trace']
                    if BASE <= r['pc'] < BASE + len(self.data)]
            # Each executed PC is an instruction boundary established by GNU
            # execution. Decode only missing boundaries, privately, with GNU.
            for pc in sorted({r['pc'] for r in rows} - self.instructions.keys()):
                self.disassemble(f'executed_{pc:x}', pc, pc + 1)
            self.aligned += self.audit_alignment(
                dict(trace=rows, trace_truncated=False))
            self.executed_pcs.update(r['pc'] for r in rows)
            self.gnu_steps += result['completed']
            require(result['status'] == 'breakpoint',
                    'Unmodeled editor boundary: ' + str((
                        hex(s.regs['pc']), result['status'], result.get('fault'))))
            pc = s.regs['pc']
            if pc in stops:
                return
            self.model_counts[hex(pc)] = self.model_counts.get(hex(pc), 0) + 1
            if pc in (0x60A4EC03, 0x60A4EC0D):
                n, p = s.regs['d0'], self.next_alloc
                require(0 < n <= 4096 and p + n <= HEAP_END,
                        'Allocator model budget exceeded')
                self.next_alloc = (p + n + 3) & ~3
                s.ram(f'owned_allocation_{p:x}', p, bytes(n), aliases=False)
                s.regs['a0'] = p
            elif pc == 0x607B3C32:
                s.regs['a0'] = API + 0x80
            elif pc == 0x60CF779D:
                require(s.regs['mdr'] == 0x60E21FB5,
                        'Unreviewed context query caller')
                s.regs['a0'] = API + 0x200
            elif pc in (API + 0x100, API + 0x120):
                # Native CALLS owns the return slot; GNU executes RETS.
                if pc == API + 0x120:
                    require(s.regs['mdr'] == 0x60E21FBF,
                            'Unreviewed context virtual caller')
                    # Delete paths do not read this query's output. No fake
                    # context bytes are supplied to enable another branch.
                s.write(HOOK_RETURN, self.rets + b'\xcb' * 6)
                s.regs.update(pc=HOOK_RETURN, d0=int(pc == API + 0x100))
                continue
            s.return_from_model(0)
        raise ValueError('Finite editor model budget exhausted')

    def ui_call(self, s, target, mask, frame, args, stop=None):
        s.enter(target, mask, frame, args)
        self.run_ui(s, {s.finish if stop is None else stop})
        if stop is None:
            require(s.regs['sp'] == SP, 'Native UI stack imbalance')
        return s.regs['d0']

    def descriptors(self):
        table = dict((key, (count, address)) for key, count, address
                     in struct.iter_unpack('<HHI', self.read(0x61186BA4, 47 * 8)))
        callbacks = {row[0]: row for row in struct.iter_unpack(
            '<14I', self.read(0x6118474C, 151 * 56))}
        result = []
        for slot, (root, cursor, first) in enumerate(zip(ROOTS, CURSORS, FIRST), 1):
            require(callbacks[root][1:5] == (0x60E20A54, 0x60E20BC7,
                                           0x60E20E0A, 0x60E2107A),
                    'COLOR callback row changed')
            count, address = table[root]
            entries = list(struct.iter_unpack('<II', self.read(address, count * 8)))
            expected = [cursor, *range(first, first + 12)]
            require(count == 13 and entries == [(0, k) for k in expected],
                    'COLOR descriptor changed')
            result.append(dict(slot=slot, root=hex(root), descriptor=hex(address),
                               child_keys=expected, child_count=count))
        return result

    def static_map(self):
        checks = {
            0x60DE9926: ('call', '0x60de55fa,[d2,d3,a2,a3],24'),
            0x60DE9934: ('call', '0x60de5ab8,[d2,d3,a2,a3],16'),
            0x60DE5D67: ('calls', '(a2)'),
            0x6082748B: ('call', '0x602af890,[],4'),
            0x60E2747B: ('mov', '13,d1'),
            0x60E27494: ('mov', '11,d1'),
            0x607997E4: ('mov', '12,d0'),
        }
        for pc, instruction in checks.items():
            require(self.instructions[pc] == instruction, f'Changed UI anchor {pc:#x}')
        names = []
        for address, event in ((0x611EAB50, 0x900C), (0x611EAB58, 0x900D),
                               (0x611EABA0, 0x9016), (0x611EABA8, 0x9017),
                               (0x611EAC40, 0x903E), (0x611EAC60, 0x9042)):
            code, pointer = struct.unpack('<II', self.read(address, 8))
            require(code == event, 'Event name table changed')
            # Names remain in the private input; publish only IDs/addresses.
            names.append(dict(record=hex(address), event=hex(code), name_pointer=hex(pointer)))
        for i, first in enumerate(FIRST):
            require(struct.unpack('<12H', self.read(0x611899B8 + 24 * i, 24))
                    == tuple(range(first, first + 12)), 'Numeric display source keys')
        return dict(event_name_records=names,
                    gui_setter=hex(0x607FA129), gui_native_adapter=hex(0x60827440),
                    gui_value_path=hex(0x602AF890),
                    display=dict(entry=hex(0x60E27289), key_table=hex(0x611899B8),
                                 cursor_choices=13, S_choices=11),
                    excluded_C3d=dict(setter=hex(0x607996EF), getter=hex(0x607997CF),
                                      copy_bytes=12, not_proven_color_wheel=True))

    def constructors(self):
        s = self.fixture()
        result = []
        for row in self.descriptors():
            root = int(row['root'], 0)
            s.write(ARG, struct.pack('<H', root))
            self.ui_call(s, 0x60E2054E, '', 0, {'a0': ARG})
            parent = s.regs['a0']
            require(u32(s, parent) == 0x61187534, 'Native parent vtable')
            require(u16(s, parent + 100) == root, 'Native root identity')
            require(u16(s, parent + 120) == 13, 'Native child count')
            children = list(struct.unpack('<13I', s.read(parent + 124, 52)))
            require([u16(s, p + 84) for p in children] == row['child_keys'],
                    'Native factory differs from descriptor')
            counts = [u16(s, p + 88) for p in children]
            require(counts == [13] + [11] * 12, 'Native enumeration size')
            for child in children[1:]:
                values = struct.unpack('<11i', s.read(u32(s, child + 100), 44))
                require(values == tuple(range(5, -6, -1)), 'Native S ordering')
                require(u16(s, child + 90) == 5, 'Neutral S index')
            result.append(dict(slot=row['slot'], counts=counts,
                               S_values=list(values), neutral_index=5,
                               constructor_stack_balanced=True))
            if row['slot'] == 1:
                self.first_parent, self.first_child = parent, children[1]
        self.ui_state = s
        return result

    def delete_local(self):
        s, parent = self.ui_state, self.first_parent
        children = list(struct.unpack('<13I', s.read(parent + 124, 52)))
        indices = [u16(s, p + 90) for p in children]
        from ep7_t25_storage_probe import MODE, SIZE
        before = digest(s.read(MODE, SIZE))
        result = []
        for event in (0x9016, 0x9017, 0x9042):
            s.enter(0x60DD5250, '', 0, {'a0': parent, 'd0': event, 'd1': 0})
            # The common dispatcher also performs queue bookkeeping. Its
            # helper clears matching live entries; it is NOT an event sender.
            # Do not substitute a successful no-op for this unmodeled queue.
            self.run_ui(s, {s.finish, 0x60D1050A})
            at_queue = s.regs['pc'] == 0x60D1050A
            if event == 0x9016:
                require(at_queue and s.regs['d0'] == 0x9016,
                        'Delete press queue argument changed')
            elif event == 0x9017:
                require(at_queue and s.regs['d0'] == 0xF802,
                        'Delete release dispatch changed')
            else:
                require(not at_queue and s.regs['d0'] == 0,
                        'Long Delete native local result changed')
                require(s.regs['sp'] == SP, 'Long Delete stack imbalance')
            require([u16(s, p + 90) for p in children] == indices,
                    'Local Delete changed selection')
            require(digest(s.read(MODE, SIZE)) == before,
                    'Local Delete changed Mode fixture')
            result.append(dict(event=hex(event), stopped_at_queue=at_queue,
                               queue_argument=hex(s.regs['d0']) if at_queue else None,
                               indices_and_Mode_unchanged=True))
        return dict(cases=result, scope='Local actuator only; queue boundary NOT modeled',
                    query_model='Output unused on these three native paths')

    def child_events(self):
        s, child = self.ui_state, self.first_child
        cases = []
        # Real non-wrapping child policy, set by the native constructor.
        require(u32(s, child + 104) == 1, 'Native S endpoint policy changed')
        for target, frame, delta in ((0x60DE55FA, 24, -1),
                                     (0x60DE56E6, 28, 1)):
            for old in (0, 1, 5, 9, 10):
                s.write(child + 90, struct.pack('<H', old))
                self.ui_call(s, target, 'd2,d3,a2,a3', frame, {'a0': child})
                new = u16(s, child + 90)
                require(new == min(10, max(0, old + delta)), 'Native S step')
                cases.append(dict(target=hex(target), old=old, new=new))
        s.write(child + 90, struct.pack('<H', 0))
        self.ui_call(s, 0x60DE9886, '', 0, {'a0': child, 'd0': 0x903E},
                     stop=0x607F964A)
        require(s.regs['d0'] == 927 and s.regs['a1'] % 4 == 0,
                'Native reset default-query arguments')
        s.write(child + 90, struct.pack('<H', 5))
        self.ui_call(s, 0x60DE9920, '', 0, {'a0': child}, stop=0x60DE5B16)
        selected = u16(s, child + 90)
        require(selected == 4 and s.regs['d2'] == 0x900C,
                'Native step/commit event')
        value = struct.unpack('<i', s.read(u32(s, child + 100) + selected * 4, 4))[0]
        require(value == 1, 'Native step/commit selected value')
        return dict(steps=cases,
                    reset=dict(event=hex(0x903E), default_query=hex(0x607F964A),
                               key=927, stopped_before_default_lookup=True),
                    commit=dict(event=hex(0x900C), stopped_at=hex(0x60DE5B16),
                                key=927, selected_index=selected, selected_value=value),
                    cutoff='Commit UI-service preparation and default query not modeled; NOT a persisted edit')

    def negative_controls(self):
        s, child = self.ui_state, self.first_child
        pointer = u32(s, child + 96)
        caught = []
        for bad, reason in ((pointer + 1, 'Unaligned 2-byte access'),
                            (HEAP_END + 4096, 'Unmodeled editor boundary')):
            s.write(child + 96, struct.pack('<I', bad))
            s.write(child + 90, struct.pack('<H', 5))
            try:
                self.ui_call(s, 0x60DE55FA, 'd2,d3,a2,a3', 24, {'a0': child})
            except ValueError as error:
                require(reason in str(error), 'Unexpected negative-control failure')
                if bad != pointer + 1:
                    require('memory_fault' in str(error), 'Unknown access not trapped')
                caught.append(reason)
            else:
                raise ValueError('Bad child pointer silently accepted')
            finally:
                s.write(child + 96, struct.pack('<I', pointer))
        return dict(rejections=caught, modified_firmware=False,
                    scope='Deliberately invalid owned child RAM, not OEM ROM changes')

    def evidence(self):
        result = dict(stock_sha256=STOCK_SHA, decoded_sha256=MAIN_SHA,
                      static_map=self.static_map(),
                      descriptors=self.descriptors(), constructors=self.constructors(),
                      local_delete=self.delete_local(),
                      child_events=self.child_events(),
                      negative_controls=self.negative_controls(),
                      copied_initializer=dict(source_offsets=[hex(INIT_START), hex(INIT_END)],
                          destination=hex(INIT_RAM),
                          sha256=digest(self.data[INIT_START:INIT_END])),
                      instruction_windows=[dict(start=hex(a), end_exclusive=hex(b),
                          sha256=digest(self.read(a, b-a))) for a, b in WINDOWS],
                      models=self.model_counts, audited_native_ROM_accesses=self.aligned,
                      gnu_completed_instructions=self.gnu_steps,
                      unique_native_ROM_pcs=len(self.executed_pcs),
                      scope='Native UI on unchanged v4 UI bytes; owned RAM; no physical key FSM, renderer or v5')
        (self.out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
        return result


def main():
    os.umask(0o077)
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--upstream', required=True)
    p.add_argument('--stock', required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()
    x = Probe(args.upstream, args.stock, args.out)
    x.prepare()
    try:
        result = x.evidence()
    finally:
        x.trace.close()
    print(json.dumps(dict(constructors=len(result['constructors']),
                          S_step_cases=len(result['child_events']['steps']),
                          accesses_audited=result['audited_native_ROM_accesses'],
                          persisted_edit_proved=False, v5_created=False)))


if __name__ == '__main__':
    main()

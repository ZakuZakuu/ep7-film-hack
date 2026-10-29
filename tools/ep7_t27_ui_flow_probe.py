#!/usr/bin/env python3
"""E142/1100 shooting-editor FSM and display contracts, NOT v5/v5a.

Original experiment. References the design in fishcu/oly_fw_analysis@539fcf1;
only runs the separately obtained GNU engine. OEM descriptors are read at run
time into private /tmp RAM fixtures, never embedded in this source or exported.
The existing v4 image is the baseline. No new ROM edits or update files.
"""
import argparse
import json
import os
import struct

from ep7_color_min import MAIN_SHA, SP, STOCK_SHA, digest, require
from ep7_t27_editor_probe import ARG, HEAP_END, Probe as Editor, u16, u32

FSM, META, CATALOG = 0x1C040000, 0x1C040100, 0x1C040200
EVENTS, MATRIX, CTRL = 0x1C040300, 0x1C040500, 0x1C040700
DESCRIPTOR, NATIVE_CATALOG = 0x611ADA58, 0x611317C4
HANDLER, DISPATCH = 0x60E766EA, 0x60D11448
EXTRA_WINDOWS = (
    (0x60D113D1, 0x60D115D4), (0x60DD4B19, 0x60DD4B4F),
    (0x60E766EA, 0x60E76728), (0x60E4D032, 0x60E4D144),
    (0x60D7AD12, 0x60D7AD24), (0x60D7AE23, 0x60D7AECE),
    (0x60D7B014, 0x60D7B162), (0x60E850F8, 0x60E85191),
    (0x60E8527D, 0x60E852D1), (0x60D484D2, 0x60D48510),
    (0x60E8456D, 0x60E84597), (0x60D48334, 0x60D4833B),
    (0x60D48B63, 0x60D48BA0), (0x607FA129, 0x607FA3C5),
    (0x602AF890, 0x602AF89C), (0x602AFA11, 0x602AFA30),
    (0x60827440, 0x608274E0), (0x6076A9FF, 0x6076AA4E),
    (0x60A4EC03, 0x60A4EC3F), (0x60A4E93A, 0x60A4E971),
)


class Probe(Editor):
    def prepare(self):
        super().prepare()
        for a, b in EXTRA_WINDOWS:
            self.disassemble(f'flow_{a:x}', a, b)
        header = struct.unpack('<4H6I', self.read(DESCRIPTOR, 32))
        require(header[:4] == (5, 47, 36, 47), 'FSM dimensions changed')
        require(header[4:9] == (0x611AD944, 0x611AD8B4, 0x611AD73C,
                                0x611ADA30, 0x611ADA44), 'FSM pointers changed')
        self.native_matrix = self.read(header[4], 5 * 47)
        self.native_events = list(struct.iter_unpack('<II', self.read(header[6], 47 * 8)))
        self.functions = struct.unpack('<36I', self.read(header[5], 36 * 4))
        require(sorted(i for _, i in self.native_events) == list(range(47)),
                'Non-permutation event dictionary')
        require(all(v < 36 for v in self.native_matrix), 'Invalid function index')
        require(self.functions[5] == HANDLER, 'SetVal handler changed')
        require(not {0x9016, 0x9017, 0x9042} & dict(self.native_events).keys(),
                'Delete already in native SsRec event dictionary')
        for pc in (0x60A4EC03, 0x60A4EC0D, 0x60A4EC2B, 0x60A4EC35):
            require(self.instructions[pc] == ('call', '0x60022700,[],4'),
                    'Allocation wrappers no longer share the reviewed core')

    def run_ui(self, s, stops):
        # Debug/instrumented allocation variants call exactly the same core
        # as the two allocators already modeled by Editor. Preserve native
        # mutex construction after allocation; do NOT model a successful lock.
        extra = {0x60A4EC2B, 0x60A4EC35}
        for _ in range(64):
            super().run_ui(s, set(stops) | extra)
            pc = s.regs['pc']
            if pc in stops:
                return
            size, address = s.regs['d0'], self.next_alloc
            require(0 < size <= 4096 and address + size <= HEAP_END,
                    'Finite debug allocation budget')
            self.next_alloc = (address + size + 3) & ~3
            s.ram(f'owned_debug_allocation_{address:x}', address, bytes(size), aliases=False)
            s.regs['a0'] = address
            self.model_counts[hex(pc)] = self.model_counts.get(hex(pc), 0) + 1
            s.return_from_model(0)
        raise ValueError('Finite debug allocator model budget exhausted')

    def fsm(self, s, expanded=False):
        """Owned RAM prototype, not qualified firmware placement or ROM patch."""
        s.ram('owned_fsm', FSM, bytes(32), aliases=False)
        catalog = NATIVE_CATALOG
        if expanded:
            meta = bytearray(self.read(DESCRIPTOR, 32))
            for off in (2, 6):
                struct.pack_into('<H', meta, off, 48)
            struct.pack_into('<I', meta, 8, MATRIX)
            struct.pack_into('<I', meta, 16, EVENTS)
            entries = self.read(0x611AD73C, 47 * 8) + struct.pack('<II', 0x9016, 47)
            matrix = self.native_matrix + bytes((1, 5, 1, 1, 1))
            vector = bytearray(self.read(NATIVE_CATALOG, 19 * 4))
            struct.pack_into('<I', vector, 4, META)
            s.ram('owned_descriptor', META, meta, aliases=False)
            s.ram('owned_catalog', CATALOG, vector, aliases=False)
            s.ram('owned_event_dictionary', EVENTS, entries, aliases=False)
            s.ram('owned_event_matrix', MATRIX, matrix, aliases=False)
            require(matrix[:235] == self.native_matrix, 'Existing state cells changed')
            catalog = CATALOG
        s.enter(0x60D113D1, 'd2,d3,a2,a3', 20,
                {'a0': FSM, 'a1': catalog, 'd0': 19, 'd1': 2})
        # A caller stack argument: CALL will subsequently allocate its frame.
        s.write(SP + 4, struct.pack('<I', 2))
        self.run_ui(s, {0x60E76396})
        require(s.read(FSM, 3) == bytes((2, 2, 19)), 'Native FSM initialization')
        require(u32(s, FSM + 16) == DISPATCH, 'Native dispatch method')
        # Intentionally stop before the state-entry lifecycle; no fabricated
        # entry/exit, camera boot, physical key scan or RTOS scheduling proof.

    def event(self, s, event, state, before_handler=False):
        s.write(FSM + 1, bytes((state,)))
        s.enter(DISPATCH, '', 0,
                {'a0': FSM, 'd0': event, 'd1': 0, 'a1': 0})
        self.run_ui(s, {s.finish, 0x60D114D4} if before_handler else {s.finish})
        if s.regs['pc'] == s.finish:
            require(s.regs['sp'] == SP, 'FSM return stack imbalance')
            return dict(return_code=s.regs['d0'])
        return dict(handler=hex(s.regs['a2']), event=hex(s.regs['d0']))

    def routing(self):
        native, expanded = self.new_state(), self.new_state()
        self.fsm(native)
        self.fsm(expanded, True)
        compared = 0
        for event, index in self.native_events:
            expected = hex(self.functions[self.native_matrix[index * 5 + 1]])
            a = self.event(native, event, 2, True)
            b = self.event(expanded, event, 2, True)
            require(a == b == dict(handler=expected, event=hex(event)),
                    'Existing native event routing changed')
            compared += 1
        deleted = []
        for state in range(1, 6):
            for event in (0x9016, 0x9017, 0x9042):
                old = self.event(native, event, state)
                require(old == dict(return_code=3), 'Stock unknown-event result')
                new = self.event(expanded, event, state, True)
                if event == 0x9016:
                    expected = hex(HANDLER if state == 2 else self.functions[1])
                    require(new == dict(handler=expected, event=hex(event)),
                            'Delete prototype escaped its selected state')
                else:
                    require(new == old, 'Delete release/hold changed')
                deleted.append(dict(state=state, event=hex(event), stock=old,
                                    owned_RAM_prototype=new))
        self.expanded_state = expanded
        return dict(native_events=47, states=5, handler_functions=36,
                    existing_event_comparisons=compared,
                    original_matrix_cells_preserved=235, delete_cases=deleted,
                    initializer_stop='0x60e76396 BEFORE entry body',
                    native_dispatch=hex(DISPATCH), descriptor=hex(DESCRIPTOR),
                    catalog_slot='0x611317c8', physical_key_delivery_proved=False,
                    cave_placement_and_ROM_redirection_proved=False)

    def local_route(self):
        s = self.fixture()
        s.write(ARG, struct.pack('<H', 0x13B3))
        self.ui_call(s, 0x60E2054E, '', 0, {'a0': ARG})
        parent = s.regs['a0']
        require(u32(s, parent) == 0x61187534 and u16(s, parent + 100) == 0x13B3,
                'Native COLOR parent identity')
        self.fsm(s, True)
        controller = bytearray(228)
        struct.pack_into('<I', controller, 0, parent)
        # +28/+32 are explicitly the null callback member pair. Viewer stays
        # absent: this experiment stops before the actual parent event body.
        s.ram('owned_controller_shell', CTRL, controller, aliases=False)
        s.write(0x61FC43C0, struct.pack('<I', CTRL))
        s.enter(DISPATCH, '', 0,
                {'a0': FSM, 'd0': 0x9016, 'd1': 0, 'a1': 0})
        self.run_ui(s, {0x60DD5250})
        require(s.regs['a0'] == parent and s.regs['d0'] == 0x9016
                and s.regs['d1'] == 0, 'Native local Delete arguments')
        self.parent_state, self.parent = s, parent
        return dict(chain=['0x60d11448', hex(HANDLER), '0x60e4d032', '0x60dd5250'],
                    event='0x9016', root='0x13b3', actual_native_parent=True,
                    controller='Explicit owned shell, not a captured live object',
                    stopped_before_parent_body=True, axis_switch_implemented=False)

    def route_controls(self):
        s = self.expanded_state
        failures = []
        for pointer, message in ((EVENTS + 1, 'Unaligned 4-byte access'),
                                 (0x1FFFF000, 'memory_fault')):
            s.write(META + 16, struct.pack('<I', pointer))
            try:
                self.event(s, 0x9016, 2, True)
            except ValueError as error:
                require(message in str(error), 'Unexpected table-pointer rejection')
                failures.append(message)
            else:
                raise ValueError('Invalid native event dictionary accepted')
            finally:
                s.write(META + 16, struct.pack('<I', EVENTS))
        return dict(rejected=failures, scope='Corrupted owned RAM pointers, not ROM')

    def display(self):
        # Verify a widget definition through the native initializer's actual
        # count load, rather than assuming selectors 7/8 mean digits 6/7.
        require(self.read(0x61032180 + 53, 1) == bytes((6,)), 'S digit count')
        require(self.instructions[0x60D48500] == ('movbu', '(53,a3),d0')
                and self.instructions[0x60D48505] == ('movbu', 'd0,(a0)'),
                'Widget count initializer changed')
        digit_cases = []
        for value in (0, 5, 6, 7):
            s = self.new_state()
            widget = 0x1C045000
            data = bytearray(300)
            data[131], data[132] = 6, 0
            s.ram('owned_six_frame_widget', widget, data, aliases=False)
            s.enter(0x60E8456D, 'd2,a2', 12, {'a0': widget, 'd0': value})
            self.run_ui(s, {s.finish, 0x60CFDDE0})
            current = s.read(widget + 132, 1)[0]
            require(current == (value if value < 6 else 0), 'Native widget bound')
            digit_cases.append(dict(requested_frame=value, stored_frame=current,
                                    stopped_before_dirty_service=s.regs['pc'] != s.finish))
        captions = []
        for text in ('L +7', 'H -7', 'L 0'):
            s = self.new_state()
            obj, widgets = 0x1C040000, 0x1C041000
            data = bytearray(1360)
            for index in (1, 6, 7, 8, 9):
                struct.pack_into('<I', data, 792 + index * 4, widgets + index * 512)
            struct.pack_into('<H', data, 1024, 5)
            encoded = text.encode('utf-16le')
            data[1032:1032 + len(encoded)] = encoded
            data[1024 + 74] = 1
            s.ram('owned_display_record_and_control_vector', obj, data, aliases=False)
            s.enter(0x60D7AE4A, 'd2,a2,a3', 32, {'a0': obj})
            self.run_ui(s, {0x60E84549})
            require((s.regs['a0'], s.regs['d0']) == (widgets + 512, 1),
                    'Native caption group visibility')
            # One explicitly modeled visibility/dirty service. No font or
            # pixel rendering is modeled, and this does not claim B5 success.
            s.return_from_model(0)
            self.run_ui(s, {0x60D4C9DF})
            require(s.regs['a0'] == widgets + 7 * 512
                    and s.read(s.regs['a1'], len(encoded) + 2) == encoded + bytes(2),
                    'Native inline caption text path')
            captions.append(dict(text=text, reached_text_setter='0x60d4c9df',
                                 widget_index=7, glyphs_or_pixels_not_executed=True))
        return dict(record_id=229, payload_bytes=334,
                    native_reader='0x60d7ad1d', native_consumer='0x60d7ae23',
                    stock_digit_widget='0x61032180', stock_frame_count=6,
                    digit_cases=digit_cases, inline_caption_cases=captions,
                    caption_type=5, caption_payload_offset=0,
                    caption_UTF16_offset=8, caption_visibility_offset=74,
                    production_viewer_not_redirected=True, visual_layout_unqualified=True)

    def commit_boundaries(self):
        # Two independent starting points; neither missing service is mocked
        # into a successful edit. The owned baseline Mode remains unchanged.
        from ep7_t25_storage_probe import MODE, SIZE
        result = []
        s = self.fixture()
        before = digest(s.read(MODE, SIZE))
        s.enter(0x607FA129, '', 0,
                {'a0': 0x1C000000, 'd0': 927, 'd1': 0, 'a1': 2})
        try:
            self.run_ui(s, {s.finish, 0x60827440})
        except ValueError as error:
            require('memory_fault' in str(error) and s.regs['pc'] == 0x600304FD,
                    'Unexpected full GUI setter boundary')
            require(digest(s.read(MODE, SIZE)) == before, 'Write before service admission')
            result.append(dict(start='0x607fa129', stop='0x600304fd',
                               missing_read='0x8ff00004', Mode_unchanged=True,
                               reason='Native synchronization-object creation reaches unmodeled kernel state'))
        else:
            raise ValueError('Expected unmodeled native admission context')
        s, parent = self.parent_state, self.parent
        child = u32(s, parent + 128)
        before = digest(s.read(MODE, SIZE))
        s.write(child + 90, struct.pack('<H', 5))
        s.enter(0x60DE9920, '', 0, {'a0': child})
        self.run_ui(s, {0x60DE5B16})
        require(s.regs['d2'] == 0x900C and u16(s, child + 90) == 4,
                'Native child step/commit')
        require(digest(s.read(MODE, SIZE)) == before, 'Child wrote before commit preparation')
        try:
            self.run_ui(s, {s.finish, 0x607FA129})
        except ValueError as error:
            require('memory_fault' in str(error), 'Unexpected child commit failure')
            child_result = dict(stop=hex(s.regs['pc']), boundary=str(error),
                                GUI_setter_reached=False)
        else:
            require(s.regs['pc'] == 0x607FA129, 'Child returned without GUI setter')
            require(s.regs['d0'] == 927 and s.regs['d1'] == 0
                    and s.regs['a1'] == 1, 'Native GUI setter arguments')
            child_result = dict(stop='0x607fa129', GUI_setter_reached=True,
                                key=927, operation=0, value=1)
        require(digest(s.read(MODE, SIZE)) == before, 'Child wrote before declared boundary')
        result.append(dict(start='0x60de9920', event='0x900c', selected_S=1,
                           Mode_unchanged=True, **child_result))
        return dict(cases=result, GUI_to_HL_to_ISP_proved=False,
                    earlier_allocation_boundary_resolved='0x60a4ec2b/35 use the same 0x60022700 core as existing allocator models',
                    design_only_shared_native_core='0x602b0bc9',
                    GUI_adapter_call='0x6082748b -> 0x602af890',
                    v4_admission_wrapper='0x602afa11',
                    warning='Do not call v4 part-write before original GUI admission or leak H/L into S coordination')

    def evidence(self):
        result = dict(stock_sha256=STOCK_SHA, decoded_sha256=MAIN_SHA,
                      routing=self.routing(), local_route=self.local_route(),
                      route_negative_controls=self.route_controls(),
                      display=self.display(), commit=self.commit_boundaries(),
                      GNU_instructions=self.gnu_steps,
                      audited_native_ROM_accesses=self.aligned,
                      executed_native_PCs=len(self.executed_pcs),
                      windows=[dict(start=hex(a), end_exclusive=hex(b),
                                    sha256=digest(self.read(a, b - a))) for a, b in EXTRA_WINDOWS],
                      models=self.model_counts,
                      scope='Owned RAM experiments on existing v4 UI bytes; no v5/v5a or physical key/draw proof')
        (self.out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
        return result


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('upstream', 'stock', 'out'):
        parser.add_argument('--' + key, required=True)
    args = parser.parse_args()
    x = Probe(args.upstream, args.stock, args.out)
    x.prepare()
    try:
        result = x.evidence()
    finally:
        x.trace.close()
    print(json.dumps(dict(existing_routes=result['routing']['existing_event_comparisons'],
                          delete_cases=len(result['routing']['delete_cases']),
                          caption_cases=len(result['display']['inline_caption_cases']),
                          v5_or_v5a_created=False)))


if __name__ == '__main__':
    main()

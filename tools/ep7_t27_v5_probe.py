#!/usr/bin/env python3
"""Original bounded native E142 editor experiment; no install files or device I/O."""
import argparse
import json
import os
import struct
import copy

from ep7_color_min import SP, STOCK_SHA, MAIN_SHA, digest, require
from ep7_t27_candidate import overlay
from ep7_t27_editor_fixture import Fixture
from ep7_t27_editor_probe import ARG, ROOTS, FIRST, CURSORS, u16, u32
from ep7_t25_storage_probe import decode, MODE, SIZE

STATE = 0x60210FA0


class Probe(Fixture):
    def prepare(self):
        super().prepare()
        self.v4_candidate_sha = digest(self.candidate)
        self.candidate, self.v5, self.v5_edits = overlay(self)
        self.image.write_bytes(self.candidate)
        for r in self.v5_edits:
            if r['kind'] != 'state':
                a = int(r['address'], 16)
                self.disassemble('v5_' + hex(a), a, a + r['length'])

    def new_state(self):
        s = super().new_state()
        s.ram('volatile_v5_axis_identity', STATE, bytes(16))
        return s

    def parent(self, s, slot=0):
        s.write(ARG, struct.pack('<H', ROOTS[slot]))
        self.ui_call(s, 0x60E2054E, '', 0, {'a0': ARG})
        return s.regs['a0']

    def parent_event(self, s, parent, event, aux=0, stop=None):
        return self.ui_call(s, self.v5['v5_parent'], '', 0,
                            {'a0': parent, 'd0': event, 'd1': aux}, stop)

    def fresh(self, slot=0):
        s = self.fixture()
        self.warm(s)
        s.write(0x6250F278, b'\x0b')
        s.write(0x6250F836, bytes((slot + 1,)))
        require(self.app(s, CURSORS[slot], 1) == 0, 'Native initial color cursor')
        return s, self.parent(s, slot)

    def smoke(self):
        s, p = self.fresh()
        self.app(s, 927, 0x4552FFFD)
        self.app(s, 927, 0x45510002)
        for expected in (1, 2):
            self.parent_event(s, p, 0x9016)
            require(u32(s, STATE + 4) == expected, 'Delete axis cycle')
        child = u32(s, p + 128)
        self.ui_call(s, 0x60DE9920, '', 0, {'a0': child})
        require(decode(self.part_read(s, 927)) == (3, -3), 'H native child commit')
        require(u32(s, 0x61FA71E8) == 0 and not self.held_mutexes,
                'GUI edit or lock left active')
        return dict(pair=list(decode(self.part_read(s, 927))),
                    mirror=s.read(0x60210EC0, 4).hex(), SP=hex(s.regs['sp']))

    def pairs(self, s, slot):
        return [decode(self.part_read(s, FIRST[slot]+i)) for i in range(12)]

    def axis(self, s, parent, wanted):
        for _ in range(3):
            if u32(s, STATE+4) == wanted:
                return
            self.parent_event(s, parent, 0x9016)
        raise ValueError('Axis cycle did not converge')

    def release(self, s, parent, event):
        self.parent_event(s, parent, event)
        self.parent_event(s, parent, event+1)

    def caption(self, s, parent, slot, expected):
        viewer = 0x1C080000
        data = bytearray(412)
        struct.pack_into('<I', data, 384, parent)
        struct.pack_into('<I', data, 400, (54, 55, 56, 64)[slot])
        s.ram('owned_numeric_viewer', viewer, data, aliases=False)
        s.enter(self.v5['v5_numeric_detour'], '', 0,
                {'a0': viewer, 'a1': viewer})
        self.run_ui(s, {0x60E26BA6})
        require(s.regs['sp'] == SP, 'Numeric detour stack')
        text = s.read(viewer+12, 32).decode('utf-16le').split('\0')[0]
        require(text == expected, f'Caption {text!r} != {expected!r}')
        require(u16(s, viewer+4) == 5 and s.read(viewer+78, 1) == b'\1',
                'Native inline text contract')
        if u32(s, STATE+4):
            require(s.read(viewer+169, 2) == bytes(2), 'Old H/L digits visible')
        return dict(text=text, native_record_bytes=334,
                    producer='0x60e27289 + original caption adapter',
                    pixels_or_glyphs_executed=False)

    def admission(self, s, p):
        result = []
        self.axis(s, p, 2)
        # Independent native guard inputs; include branches in which bit 8
        # overrides a later busy condition, rather than labeling all flags busy.
        for flags, accepted in [((0, 0, 0, 0), True), ((2, 0, 0, 0), False),
                ((6, 0, 0, 0), True), ((0, 2, 0, 0), False),
                ((256, 2, 0, 0), True)]:
            s.write(0x622CB16C, struct.pack('<4I', *flags))
            self.app(s, 927, 0x45510002)
            before = s.read(MODE, SIZE), s.read(0x60210EC0, 192)
            self.release(s, p, 0x9004)
            got = self.pairs(s, 0)[0][0]
            require(got == (3 if accepted else 2), 'Native busy/idle decision')
            if not accepted:
                require(before == (s.read(MODE, SIZE), s.read(0x60210EC0, 192)),
                        'Busy GUI changed settings or mirror')
            require(not self.held_mutexes and not self.queue_locked
                    and u32(s, 0x61FA71E8) == 0, 'Admission lifecycle left active')
            result.append(dict(flags=list(flags), accepted=accepted,
                               actual_H=got, busy_no_write=not accepted))
        s.write(0x622CB16C, bytes(16))
        self.active_application(s)
        self.release(s, p, 0x9004)
        require(self.peer_events[-1]['value'] == 0
                and self.peer_events[-1]['witnesses'] == [14, 15, 16],
                'H leaked as S in original coordinator')
        active = list(self.peer_events)
        self.active_peer = False
        from ep7_t27_editor_fixture import LOCATOR, COORDINATOR
        s.write(LOCATOR+4, bytes(4))
        s.write(COORDINATOR+4, bytes(12))
        return dict(cases=result, active_request_witness=active,
                    active_app_state='0x10001 branch witness, not a measured task ID',
                    peer_transport='Explicit success input; message construction stays native')

    def interaction(self, s, p, slot):
        key, out = FIRST[slot], []
        for axis, tag, pair_index, letter in [(1, 0x4552, 1, 'L'),
                                             (2, 0x4551, 0, 'H')]:
            self.axis(s, p, axis)
            children = [u32(s, p+128+4*i) for i in range(12)]
            require(all(u16(s, c+88) == 15 for c in children), 'H/L enum count')
            for c in children:
                require(struct.unpack('<15i', s.read(u32(s, c+100), 60))
                        == tuple(range(7, -8, -1)), 'H/L enum ordering')
            # Native marked application path acts as an independent Wi-Fi
            # writer. It deliberately leaves the GUI enum cache stale.
            self.app(s, key, (tag << 16) | 6)
            self.release(s, p, 0x9004)
            require(self.pairs(s, slot)[0][pair_index] == 7, 'Wi-Fi -> GUI refresh')
            captions = [self.caption(s, p, slot, letter+' +7')]
            before = self.pairs(s, slot)
            self.release(s, p, 0x9004)
            require(self.pairs(s, slot) == before, '+7 endpoint wrapped')
            self.app(s, key, (tag << 16) | 0xFFF9)
            self.release(s, p, 0x9006)
            require(self.pairs(s, slot)[0][pair_index] == -7, '-7 endpoint wrapped')
            captions.append(self.caption(s, p, slot, letter+' -7'))
            # ALL uses original INFO toggle and both native color callbacks.
            for i in range(12):
                self.app(s, key+i, tag << 16)
            self.release(s, p, 0x9014)
            require(u32(s, 0x61FC3800) or u32(s, 0x61FC3804), 'INFO did not select ALL')
            captions.append(self.caption(s, p, slot, letter+' ALL'))
            self.release(s, p, 0x9004)
            require([v[pair_index] for v in self.pairs(s, slot)] == [1]*12,
                    'ALL increment not confined to current axis')
            self.app(s, key+11, (tag << 16) | 7)
            before = self.pairs(s, slot)
            self.release(s, p, 0x9004)
            require(self.pairs(s, slot) == before, 'ALL upper group bound ignored')
            self.release(s, p, 0x9006)
            require([v[pair_index] for v in self.pairs(s, slot)] == [0]*11+[6],
                    'ALL decrement')
            self.app(s, key+11, (tag << 16) | 0xFFF9)
            before = self.pairs(s, slot)
            self.release(s, p, 0x9006)
            require(self.pairs(s, slot) == before, 'ALL lower group bound ignored')
            self.release(s, p, 0x9014)
            require(not u32(s, 0x61FC3800) and not u32(s, 0x61FC3804),
                    'INFO did not leave ALL')
            other = [v[1-pair_index] for v in self.pairs(s, slot)]
            stock_s = s.read(0x6250F860, 24)
            self.parent_event(s, p, 0x900C)
            require(u32(s, p+16) == 3, 'Original held-OK timer state')
            self.parent_event(s, p, 0xF802)
            self.parent_event(s, p, 0x900D)
            pairs = self.pairs(s, slot)
            require([v[pair_index] for v in pairs] == [0]*12
                    and [v[1-pair_index] for v in pairs] == other
                    and s.read(0x6250F860, 24) == stock_s,
                    'Held OK did not isolate/reset the current axis')
            self.parent_event(s, p, 0x900C)
            require(self.parent_event(s, p, 0x900D) == 2, 'Short OK exit code')
            out.append(dict(axis=letter, enum_count=15, captions=captions,
                            bounds=True, ALL=True, held_OK_all_12=True,
                            short_OK_exit=2, stock_S_unchanged=True))
        self.axis(s, p, 0)
        require(all(u16(s, u32(s, p+128+4*i)+88) == 11 for i in range(12)),
                'S enumeration not restored')
        return dict(slot=slot+1, axes=out, returned_to_S=True)

    def image_join(self, s):
        from ep7_t24_1_probe import Probe as Preview, COMPACT
        from ep7_t25_v4_probe import L_STEPS
        view = Preview.__new__(Preview)
        view.__dict__.update(self.__dict__)
        saturation = list(struct.unpack('<12h', s.read(0x6250F848, 24)))
        row = struct.unpack('<24h', s.read(0x60210EC0, 48))
        result = []
        for compact in (None, COMPACT[0], COMPACT[1], 0):
            regions = view.fixture(1, compact=compact, saturation=saturation)
            regions.append(self.provider.Region('mirror', 0xA0210EC0,
                                                s.read(0x60210EC0, 192)))
            old = self.select('v5_image_stock_'+str(compact), regions, False)
            new = self.select('v5_image_'+str(compact), regions, True)
            require(old['registers'] == new['registers'], 'Image ABI changed')
            a, b = self.captured(old, 'output'), self.captured(new, 'output')
            expected = bytearray(a)
            for i in range(12):
                struct.pack_into('<h', expected, 706+i*24, -1000*row[2*i])
                struct.pack_into('<h', expected, 710+i*24, L_STEPS[row[2*i+1]+7])
            require(b == expected, 'Unexpected native image output')
            result.append(dict(compact=None if compact is None else hex(compact),
                H0=struct.unpack_from('<h', b, 706)[0],
                L0=struct.unpack_from('<h', b, 710)[0],
                uploads=[self.pack_and_upload('v5_isp_'+str(compact)+'_'+str(bank),
                                              b, bank) for bank in (0, 1)]))
        return dict(cases=result, joined_v4_mirror=True,
                    limit='Frame objects are owned fixtures; no captured camera frame or pixel execution')

    def evidence(self):
        # Checkpoints contain only metrics and conclusions, no OEM bytes.
        # Full traces remain private; progress survives an interrupted Cloud run.
        result = dict(stock_sha256=STOCK_SHA, decoded_sha256=MAIN_SHA,
                      v4_baseline_sha256=self.v4_candidate_sha,
                      decoded_candidate_sha256=digest(self.candidate),
                      modified_ranges=self.v5_edits, models={}, interaction=[])
        def checkpoint():
            (self.out/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
        for slot in range(4):
            s, p = self.fresh(slot)
            if slot == 0:
                result['admission'] = self.admission(s, p)
                # A fresh native GUI edit feeds both the v4 query hook and the
                # original image constructors; no HTTP request overlaps API RAM.
                self.axis(s, p, 2)
                self.app(s, 927, 0x45510002)
                self.app(s, 927, 0x4552FFFD)
                self.release(s, p, 0x9004)
                require(self.native(s, self.labels['wifi_read'], '', 4,
                                   {'d0': 0x839F}) == 3, 'GUI -> Wi-Fi read hook')
                result['image_join'] = self.image_join(s)
            result['interaction'].append(self.interaction(s, p, slot))
            checkpoint()
        result.update(GNU_instructions=self.gnu_steps,
                      aligned_accesses=self.aligned,
                      native_PCs=len(self.executed_pcs), models=self.model_counts,
                      package_files_created=False, camera_connected=False)
        checkpoint()
        return result


def main():
    os.umask(0o077)
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ('stock', 'upstream', 'out'):
        p.add_argument('--' + arg, required=True)
    a = p.parse_args()
    x = Probe(a.upstream, a.stock, a.out)
    x.prepare()
    try:
        result = x.evidence()
        (x.out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(dict(profiles=len(result['interaction']),
                              accesses=result['aligned_accesses'])))
    finally:
        x.trace.close()


if __name__ == '__main__':
    main()

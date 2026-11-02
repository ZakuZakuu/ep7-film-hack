#!/usr/bin/env python3
"""Private behavioral lab for original source-only T27 compaction experiments.

Reuses prior prototype mappings ONLY for simulation, never qualifying them as
placement. No OE/package writer. Native fixtures and strict boundaries are
unchanged; all artifacts, including source-derived binaries, stay under /tmp.
"""
import argparse
import copy
import json
import os
import struct

import ep7_t27_candidate as candidate
from ep7_color_min import digest, require
from ep7_t27_compact_source import materialize
from ep7_t27_dial_probe import DialProbe
from ep7_t27_v5_probe import Probe
from ep7_t27_editor_probe import API, ARG
from ep7_t25_storage_probe import MODE, SIZE


class CompactProbe(DialProbe):
    def prepare(self):
        source = materialize(self.out / 'compact-source', 'dispatch')
        original = candidate.PATCH
        try:
            candidate.PATCH = source
            super().prepare()
        finally:
            candidate.PATCH = original
        frozen_v4 = json.loads((original.parents[1]/'hsl-recipes/e-p7/patch.json').read_text())
        require(digest(self.reference) == frozen_v4['decoded_output_sha256'],
                'Compact experiment requires the exact hash-locked v4 baseline')
        require(self.labels['cell_index'] == 0x60210B5E, 'Shared v4 helper moved')


def passthrough_abi(x):
    """Compare six S APIs on identical owned inputs, including PSW/MDR/SP.

    This specifically checks the new common passthrough, which replaces the
    original fast tail jump; functional GUI tests alone cannot establish ABI.
    """
    s = x.fixture()
    x.warm(s)
    baseline, allocation = copy.deepcopy(s.__dict__), x.next_alloc
    symbols = json.loads((candidate.PATCH/'symbols.json').read_text())
    rows = []
    for name in ('get', 'count', 'enum', 'valid', 'default', 'set'):
        outputs = []
        for compact in (False, True):
            s.__dict__.update(copy.deepcopy(baseline))
            x.next_alloc = allocation
            x.held_mutexes, x.sync_events, x.peer_events = [], [], []
            x.queue_locked = x.active_peer = False
            x.select_program(compact, s)
            s.write(ARG, bytes(144))
            target = x.v5['v5_'+name] if compact else symbols['ep7_'+name]
            x.ui_call(s, target, '', 0, dict(a0=API, d0=927, d1=0,
                                           a1=1 if name == 'set' else ARG))
            outputs.append((dict(s.regs), s.read(ARG, 144), s.read(MODE, SIZE),
                            s.read(0x60210EC0, 192)))
        require(outputs[0] == outputs[1], 'Common S passthrough ABI differs: '+name+
                ' registers='+str({k:(v,outputs[1][0].get(k)) for k,v in
                    outputs[0][0].items() if v != outputs[1][0].get(k)}))
        rows.append(dict(API=name, all_registers_and_outputs_equal=True))
    return rows


def gate_arguments(x):
    """Execute actual compiled entry gates; stop BEFORE virtual interpretation.

    Synthetic owned state is deliberately enough for the gate only. This
    catches overwritten key/value arguments without pretending to test a GUI.
    """
    rows = []
    for axis in (1, 2):
        for kind, name in enumerate(('get', 'count', 'enum', 'valid', 'default', 'set')):
            s = x.new_state()
            s.write(0x60210FA0, struct.pack('<4I', 0x1C010000, axis, 0x13B3, 927))
            x.ui_call(s, x.v5['v5_'+name], '', 0,
                      dict(a0=API, a1=ARG, d0=927, d1=3), x.v5['v5_api_override'])
            require((s.regs['d0'], s.regs['d1'], s.regs['a0'], s.regs['a1'],
                     s.regs['d2']) == (927, 3, API, ARG, kind),
                    'Entry gate changed original property arguments')
            rows.append(dict(axis=axis, API=name, arguments_preserved=True))
    return rows


def main():
    os.umask(0o077)
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('upstream', 'stock', 'out'):
        p.add_argument('--'+name, required=True)
    p.add_argument('--suite', choices=('dial', 'editor', 'controls', 'v4', 'abi', 'gate'), required=True)
    p.add_argument('--slots', nargs='+', type=int, default=[1, 2, 3, 4])
    a = p.parse_args()
    require(a.slots and len(a.slots) == len(set(a.slots))
            and all(1 <= i <= 4 for i in a.slots), 'Unique COLOR slots 1..4 required')
    x = CompactProbe(a.upstream, a.stock, a.out)
    x.prepare()
    result = dict(passed=False, suite=a.suite, variant='dispatch',
                  v4_sha256=digest(x.reference), lab_sha256=digest(x.prototype),
                  placement_qualified=False, package_files_created=False, cases=[])
    def checkpoint():
        (x.out/'compact.json').write_text(json.dumps(result, indent=2)+'\n')
    try:
        if a.suite == 'dial':
            for slot in a.slots:
                x.select_program(False)
                s, parent = x.fresh(slot-1)
                snapshot, allocation = copy.deepcopy(s.__dict__), x.next_alloc
                for prototype in (False, True):
                    result['phase'] = f'COLOR{slot}, compact={prototype}'
                    checkpoint()
                    result['cases'].append(x.replay(slot-1, snapshot, parent,
                                                     allocation, prototype))
                    checkpoint()
        elif a.suite == 'editor':
            # Use Probe.evidence so it retains its complete admission, all four
            # profile interaction, Wi-Fi, caption, ALL/reset and ISP assertions.
            result['editor'] = Probe.evidence(x)
        elif a.suite == 'controls':
            from ep7_t27_editor_aux_probe import routing, controls, gui_s_bridge
            # routing() owns a distinct event() ABI; do not shadow it with the
            # DialProbe hardware input ABI.
            view = Probe.__new__(Probe)
            view.__dict__.update(x.__dict__)
            result['routing'] = routing(view)
            checkpoint()
            result['controls'] = controls(view)
            checkpoint()
            result['GUI_S_bridge'] = gui_s_bridge(view)
            x.__dict__.update(view.__dict__)
        elif a.suite == 'gate':
            result['gate_arguments'] = gate_arguments(x)
        elif a.suite == 'abi':
            result['passthrough_abi'] = passthrough_abi(x)
        else:
            from ep7_t25_v4_probe import Probe as V4
            view = V4.__new__(V4)
            view.__dict__.update(x.__dict__)
            # Full v4 reference, not the compact GUI's alternate API namespace.
            view.candidate = x.reference
            view.image.write_bytes(view.candidate)
            for name in ('publication_abi', 'read_and_stock', 'boot_and_staging'):
                result[name] = getattr(view, name)()
                checkpoint()
            result['protocol'], s = view.protocol_matrix()
            checkpoint()
            result['imaging'] = view.imaging(s)
            result['image_matrix'] = view.image_matrix()
        result.update(passed=True, phase='complete', GNU_steps=x.gnu_steps,
                      aligned_accesses=x.aligned)
        checkpoint()
    except Exception as exc:
        result['error'] = f'{type(exc).__name__}: {exc}'
        checkpoint()
        raise
    finally:
        x.trace.close()
    print(json.dumps(dict(passed=True, suite=a.suite, cases=len(result['cases']))))


if __name__ == '__main__':
    main()

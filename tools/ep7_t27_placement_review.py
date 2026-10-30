#!/usr/bin/env python3
"""T27 bounded placement re-audit. Never certifies whole-camera reachability.

Runs the fixed upstream reference scanners/parser and GNU engine. Original
firmware and native listings stay in private /tmp. No package writer or I/O.
"""
import argparse
import json
import os
import struct
from dataclasses import replace

from ep7_color_min import BASE, SP, STACK, digest, require
from ep7_t27_placement import qualify
from ep7_t27_v5_probe import Probe


# Existing prototype spans only: no search for replacement addresses.
def all_relative_candidates(scanner, data, ranges, base=BASE):
    groups = scanner(data, base, ranges)
    require(len(groups) == len(ranges), 'Reference scanner changed result dimensions')
    return [row for group in groups for row in group]


def numeric_data(x, rows):
    """Five CALLS-shaped words in native 15-entry numeric-label data tables.

    Full rows, values and pointed-to decimal labels must agree. The synthetic
    GNU witness checks why the raw branch scanner matched them. This is data
    classification, not a claim that arbitrary byte-disassembly is valid code.
    """
    known = {0x611E2A34: (0x611E29B0, (0x611E2F44, 0x611E30B0)),
             0x611E2B28: (0x611E2AA4, (0x611E2F5C, 0x611E30C8)),
             0x611E2BDC: (0x611E2B58, (0x611E2F60, 0x611E30CC)),
             0x611E2CD0: (0x611E2C4C, (0x611E2F78,)),
             0x611E2D84: (0x611E2D00, (0x611E2F7C,))}
    classified, unknown = [], []
    for row in rows:
        a = int(row['site'], 16)
        safe = {k: v for k, v in row.items() if k != 'source_hex'}
        if a not in known or row['encoding'] != 'calls':
            unknown.append(safe)
            continue
        start, references = known[a]
        table = x.read(start, 15*12)
        records = list(struct.iter_unpack('<iII', table))
        require([q[0] for q in records] == list(range(7, -8, -1))
                and all(q[1] == 5 for q in records), 'Numeric record structure changed')
        for value, _, pointer in records:
            text = bytearray()
            for i in range(5):
                c = x.read(pointer+i, 1)[0]
                if not c:
                    break
                text.append(c)
            else:
                raise ValueError('Unterminated numeric label')
            require(int(text.decode('ascii')) == value, 'Numeric label/value disagreement')
        require(all(struct.unpack('<I', x.read(p, 4))[0] == start for p in references),
                'Numeric table references changed')
        witness = x.assemble('numeric_word_'+hex(a), '.long -4,5\n', a)
        require(witness == x.read(a, 8), 'Synthetic data word witness changed')
        classified.append(dict(**safe, classification='Signed -4 and type 5 data words in complete numeric-label table',
            table=hex(start), table_bytes=180, table_sha256=digest(table),
            pointer_fields=[hex(p) for p in references], all_15_labels_verified=True,
            instruction_boundary=False))
    return classified, unknown


def remove_regions(regions, intervals):
    """Unmap exact candidate intervals and their supplied coherent RAM aliases.

    Split both sides identically and retain alias links. A read/write/execute
    into a removed interval must fault in GNU, rather than be silently logged.
    """
    result = []
    names = {}
    for region in regions:
        parts = [(region.address, region.address+len(region.data))]
        for a, z in intervals:
            next_parts = []
            for low, high in parts:
                if low < a:
                    next_parts.append((low, min(high, a)))
                if z < high:
                    next_parts.append((max(low, z), high))
            parts = [(low, high) for low, high in next_parts if low < high]
        for i, (a, z) in enumerate(parts):
            name = (region.name if a == region.address and z-a == len(region.data)
                    else region.name+'_guard_'+str(i))
            alias = None
            if region.alias_of:
                alias = names[(region.alias_of, a-region.address, z-a)]
            result.append(replace(region, name=name, address=a,
                data=region.data[a-region.address:z-region.address], alias_of=alias))
            names[(region.name, a-region.address, z-a)] = name
    return result


def guarded_workflows(x):
    """Existing v4 Wi-Fi/application and frame/ISP fixtures with holes unmapped.

    Deliberately NOT labeled whole shooting or playback workflows. The shared
    image constructors have no independently proved playback-task entry here.
    """
    from types import SimpleNamespace
    x.select_program(False)
    s, _ = x.fresh()
    spans = [(int(row['address'],16), int(row['address'],16)+row['length'])
             for row in x.v5_edits if row['kind'] in
             ('api','apply','lifecycle','ui6','state')]
    holes = [(a+alias,z+alias) for a,z in spans for alias in (0,0x40000000)]
    s.regions = remove_regions(s.regions, holes)
    # Reuse actual v4 HTTP/pending/application and frame/ISP test routines.
    # Only the input memory map is narrowed; no stock function is replaced.
    original = x.provider
    def execute(regions, *args, **kwargs):
        return original.execute(remove_regions(regions, holes), *args, **kwargs)
    x.provider = SimpleNamespace(Region=original.Region, execute=execute)
    try:
        image = x.imaging(s)
        h = x.native(s, x.labels['wifi_read'], '', 4, dict(d0=0x8000|927))
        l = x.native(s, x.labels['wifi_read'], '', 4, dict(d0=0xC000|927))
        require(h == 3 and l == 0xFFFFFFFE, 'Guarded v4 Wi-Fi readback')
    finally:
        x.provider = original
    return dict(passed=True, v4_sha256=digest(x.reference),
        H=3, L=-2, candidate_spans_unmapped=True,
        pipeline=image,
        scope='Native HTTP parsers/pending/application, four owned image contexts and two ISP banks; not complete radio/RTOS/capture/playback tasks')


def review(x):
    prior = qualify(x)
    # Verify all-range coverage independently; old code accidentally selected
    # only the first result list. This receipt must include UI-section hits.
    from penf_code_space_audit import branch_candidates
    spans = [(int(z['address'], 16), int(z['address'], 16)+z['length'])
             for z in x.v5_edits if z['kind'] in ('api', 'apply', 'lifecycle', 'ui6', 'state')]
    rows = all_relative_candidates(branch_candidates, x.data, spans)
    require([{k:v for k,v in r.items() if k != 'source_hex'} for r in rows]
            == prior['relative_candidates'], 'Placement scanner omitted a span')
    classified, unresolved_branches = numeric_data(x, rows)
    # The same E142 bytes also execute at the independently mapped helper
    # address. A flat-main scan cannot stand in for that relocated view.
    helper = x.data[0x141C9E0:0x141C9E0+0x1800]
    relocated = all_relative_candidates(branch_candidates, helper, spans,
                                        base=0x47000800)
    inner = []
    import oly_container as oe
    for old in prior['second_method']:
        start, end = int(old['start'], 16), int(old['end'], 16)
        segment = x.blocks[2].payload[start:end]
        length = struct.unpack_from('<I', segment, 12)[0]
        require(len(segment) == length+64 and length % 16 == 0,
                'Inner record exact extent changed')
        header, body, trailer = segment[:32], segment[32:-32], segment[-32:]
        require(header[:28] == trailer[:28], 'Inner repeated metadata changed')
        raw_sum = (oe.sum32(header)+oe.sum32(body)+oe.sum32(trailer)) & 0xFFFFFFFF
        decoded_sum = (oe.sum32(header)+oe.sum32(oe.decode(body))+oe.sum32(trailer)) & 0xFFFFFFFF
        inner.append(dict(outer_descriptor=old['outer_descriptor'], start=hex(start),
            end=hex(end), sha256=digest(segment),
            address=hex(struct.unpack_from('<I', header, 8)[0]),
            kind=struct.unpack_from('<I', header, 20)[0],
            repeated_metadata_equal=True, exact_extent=True,
            raw_checksum_residual=hex(raw_sum), decoded_checksum_residual=hex(decoded_sum),
            parser_accepted=old['passed'],
            candidate_offsets=old['candidate_offsets'],
            conclusion='Unclassified OEM inner representation; no proof of MN103 operands or address-domain isolation'))
    # A real boot-prefix attempt, with no invented controller or board RAM.
    # Unknown accesses are evidence of a missing model, NEVER "unused" proof.
    intervals = [(a+alias, z+alias) for a,z in spans for alias in (0, 0x40000000)]
    r = x.provider.Region
    regions = remove_regions([r('main', BASE, x.data, 'rx'),
                              r('owned_stack', STACK, bytes(0x3000), 'rw', True)], intervals)
    boot = x.provider.execute(regions, dict(pc=BASE+0xD9, sp=SP, d0=0),
                              0xFFFFFFFF, limit=10000, trace_limit=10000)
    (x.out/'startup-prefix-private.json').write_text(json.dumps(boot))
    require(boot['status'] in ('memory_fault', 'unsupported_instruction'),
            'Unexpected startup prefix result; review required')
    # Native v4 already occupies this section-1 tail. Count exact unoccupied
    # bytes; FF in section 2/6 is not allowed to become an assumed substitute.
    extension, mirror = len(x.extension), 192
    total = 0x60211000-0x60210940
    required = sum(z['length'] for z in x.v5_edits
                   if z['kind'] in ('api','apply','lifecycle','ui6','state'))
    available = total-extension-mirror
    return dict(qualified=False, prior=prior,
        reference_scan=dict(all_spans=len(spans), raw_relative_candidates=len(rows),
            classified_numeric_data=classified, unresolved=unresolved_branches,
            relocated_helper=dict(source_offset='0x141c9e0', runtime='0x47000800',
                bytes=len(helper), sha256=digest(helper),
                relative_candidates=[{k:v for k,v in row.items() if k != 'source_hex'}
                                     for row in relocated]),
            correction='Previous [0] discarded all but the first range; fixed and all ranges rechecked'),
        literal_candidates=[dict(**z, classification='UNRESOLVED; not admitted as free-space evidence')
                            for z in prior['unresolved_references']], inner_records=inner,
        startup_prefix=dict(entry=hex(BASE+0xD9), instructions=boot['completed'],
            status=boot['status'], fault=boot.get('fault'),
            complete_boot=False, candidate_intervals_unmapped=True),
        requested_path_coverage={
            'startup':'Section load/reload passed; real boot prefix stops at the recorded unknown boundary; initializer callbacks are opaque',
            'shooting':'Existing native frame/ISP parameter fixtures; no boot-to-shooting task coverage',
            'playback':'No complete playback-task fixture; compact image builders are not renamed as playback',
            'wifi':'Existing v4 pending/application setting fixture; no complete Wi-Fi task coverage',
            'menus':'Bounded COLOR FSM/control fixture only; no whole-menu reachability proof'},
        alternatives=dict(v4_section1_start='0x60210940', end_exclusive='0x60211000',
            total_bytes=total, unchanged_v4_code_bytes=extension, mirror_bytes=mirror,
            unoccupied_bytes=available, prototype_additional_bytes=required,
            minimum_size_reduction=required-available,
            choices=['Keep v4 unchanged; need a separately qualified larger resident region',
                     'Separate v5 design: share/refactor or compress code to fit the v4-owned extent; preserve all legacy version sources and hashes, then revalidate startup/ABI/dataflow',
                     'Runtime allocation/copy is not a proven alternative: lifetime, executable ownership and reload are unknown']),
        selected_placement=None,
        stop='No span admitted for complete v5. Static absences and limited simulations do not prove unused memory across the five workflows.')


def main():
    os.umask(0o077)
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('stock', 'upstream', 'out'):
        p.add_argument('--'+name, required=True)
    a = p.parse_args()
    from ep7_t27_dial_probe import DialProbe
    x = DialProbe(a.upstream, a.stock, a.out)
    x.prepare()
    try:
        result = review(x)
        (x.out/'placement.json').write_text(json.dumps(result, indent=2)+'\n')
        result['guarded_v4_workflows'] = guarded_workflows(x)
        (x.out/'placement.json').write_text(json.dumps(result, indent=2)+'\n')
    finally:
        x.trace.close()
    print(json.dumps(dict(qualified=result['qualified'],
        unresolved_literals=len(result['literal_candidates']),
        numeric_data_hits=len(result['reference_scan']['classified_numeric_data']))))


if __name__ == '__main__':
    main()

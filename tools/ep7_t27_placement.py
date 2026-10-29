"""Bounded native load and initializer bounds checks, not a boot emulator."""
import json
import struct
from dataclasses import replace

from ep7_color_min import BASE, CALLER, SP, STACK, digest, require
from ep7_hsl_install_checks import captures, modeled_return


def qualify(x):
    r = x.provider.Region
    x.disassemble('qualified_section_loader', 0x60045786, 0x6004586C)
    x.disassemble('qualified_section_alias', 0x60067102, 0x60067146)
    loads = []
    for section, start, end in [(1, 0x600D7800, 0x60211000),
                                (2, 0x60280800, 0x6055E800),
                                (6, 0x60BA7000, 0x61243000)]:
        descriptor = 0x60027068 + 12 * (section - 1)
        actual, source, dest = struct.unpack('<3I', x.read(descriptor, 12))
        require(actual == dest == start, 'Section descriptor changed')
        selected = x.call('end_' + str(section), 0x60045786, 0,
                         [r('rom', BASE, x.data, 'rx')], {'d0': section}, mask='')
        require(selected['registers']['d0'] == end, 'Section end changed')
        alias = x.call('source_alias_'+str(section), 0x60067102, 4,
                       [r('rom', BASE, x.data, 'rx')], {'d0': source}, mask='d2')
        source_alias = alias['registers']['d0']
        caller = x.assemble('load_' + str(section),
            'call target,[d2,d3,a2,a3],24\nnop\n',
            symbols={'target': 0x600457E7})
        for poison in (0x55, 0xA5):
            regions = [r('before', BASE, x.candidate[:start-BASE], 'rx'),
                r('after', end, x.candidate[end-BASE:], 'rx'),
                r('loaded', start, bytes((poison,)) * (end-start), 'rwx', True),
                r('uncached', start+0x40000000, bytes((poison,)) * (end-start),
                  'rwx', False, 'loaded'),
                r('flags', 0xA272E420, bytes(4), 'rw', True),
                r('stack', STACK, bytes(0x2000), 'rw', True),
                r('caller', CALLER, caller, 'rx')]
            v = x.provider.execute(regions, {'pc': CALLER, 'sp': SP, 'd0': section},
                    CALLER+len(caller), breakpoints=[0x6005BC79],
                    limit=1000, trace_limit=1000)
            require(v['status'] == 'breakpoint', 'Logical storage boundary')
            regs = v['registers']
            require([regs[k] for k in ('a0', 'a1', 'd0', 'd1')] ==
                    [start+0x40000000, source_alias, end-start, 257],
                    'Logical copy contract: '+str((section, [hex(regs[k]) for k
                        in ('a0', 'a1', 'd0', 'd1')], hex(source))))
            saved, payload = captures(v), x.candidate[start-BASE:end-BASE]
            regions = [replace(q, data=payload if q.name in ('loaded', 'uncached')
                               else saved.get(q.name, q.data)) for q in regions]
            last = x.provider.execute(regions, modeled_return(x, v),
                    CALLER+len(caller), limit=1000, trace_limit=1000)
            require(last['status'] == 'returned' and
                    x.captured(last, 'loaded') == payload, 'Exact native section copy')
            (x.out / f'v5-loader-{section}-{poison}.json').write_text(json.dumps(last))
            loads.append(dict(section=section, poison=poison,
                              exact_copy=True, start=hex(start), end=hex(end),
                              source=hex(source)))
    # Section 6's preceding bytes are a real initializer table, not a cave.
    # Execute its dispatcher with ONLY the 75 table words mapped. Model each
    # callback as opaque; no claim that kernel/device initialization executes.
    table, size = 0x61242884, 300
    require(table + size == 0x612429B0, 'Initializer end')
    callbacks = set(struct.unpack('<75I', x.read(table, size)))
    code = x.assemble('initializer_call', 'call target,[d2,a2],12\nnop\n',
                      symbols={'target': 0x6018E1DD})
    from penf_boot_emulator import HOOK_RETURN
    regions = [r('dispatcher', 0x6018E1DD, x.read(0x6018E1DD, 55), 'rx'),
               r('initializer_words', table, x.read(table, size), 'r'),
               r('caller', CALLER, code, 'rx'),
               r('stack', STACK, bytes(0x2000), 'rw', True),
               r('opaque_return', HOOK_RETURN, x.rets + b'\xcb'*6, 'rx')]
    def execute(overrun=False):
        regs = {'pc': CALLER, 'sp': SP}
        called = []
        inject = overrun
        for _ in range(160):
            v = x.provider.execute(regions, regs, CALLER+len(code),
                    breakpoints=callbacks | ({0x6018E202} if inject else set()),
                    limit=1000, trace_limit=1000, changed_captures=True)
            for q in v['memory']:
                index = q['index']
                regions[index] = replace(regions[index], data=bytes.fromhex(q['hex']))
            regs = v['registers']
            if inject and regs['pc'] == 0x6018E202:
                regs['d2'], inject = 304, False  # Explicit register counterfactual.
                continue
            if v['status'] == 'breakpoint' and regs['pc'] in callbacks:
                called.append(regs['pc'])
                regs['pc'] = HOOK_RETURN
                continue
            if overrun:
                require(v['status'] == 'memory_fault' and
                        v['fault']['address'] == table + size,
                        'Initializer overrun did not fail closed')
            else:
                require(v['status'] == 'returned', 'Initializer return')
            require(len(called) == 75, 'Native initializer call count')
            return dict(calls=75, counterfactual=overrun, status=v['status'])
        raise ValueError('Initializer callback budget')
    initializers = [execute(), execute(True)]
    # Reuse existing qualified reference classification. Raw byte matches are
    # candidates; JPEG/zlib matches are explicitly classified, never called xrefs.
    from penf_code_space_audit import pointer_candidates, branch_candidates
    spans = [(int(z['address'], 16), z['length']) for z in x.v5_edits
             if z['kind'] in ('api', 'apply', 'lifecycle', 'ui6', 'state')]
    refs = []
    for start, n in spans:
        for alias in (start, start+0x40000000, start-0x1F980000, start+0x20680000):
            for block in x.blocks:
                refs += [dict(component=block.index, alias_base=hex(alias), **z)
                         for z in pointer_candidates(block.payload, alias, alias+n)]
    classified, unresolved = [], []
    for row in refs:
        # These three raw words begin at short BRA instructions and continue
        # through register-only operations. GNU roundtrip is a synthetic ISA
        # witness, not an exported OEM listing or guessed code pointer.
        a = BASE + int(row['offset'], 16)
        if row['component'] == 0 and a in (0x60E580F5, 0x60E58155, 0x60E5836A):
            target = {0x60E580F5: 0x60E58121, 0x60E58155: 0x60E58181,
                      0x60E5836A: 0x60E58397}[a]
            witness = x.assemble('v5_literal_'+hex(a),
                f'bra .+{target-a}\nmov d3,d0\nmov d0,d1\n', a)
            require(witness[:4] == x.read(a, 4), 'Branch-straddling witness')
            classified.append(dict(**{k:v for k,v in row.items() if k != 'source_hex'},
                                   classification='GNU verified short-branch/register instruction straddler'))
            continue
        try:
            classified += x.classify_v4_references([row])
        except ValueError as exc:
            unresolved.append(dict(**{k:v for k,v in row.items() if k != 'source_hex'},
                                   first_method=str(exc)))
    branches = branch_candidates(x.data, BASE,
                                [(a, a+n) for a, n in spans])[0]
    # A second bounded method: use the previously established outer resource
    # descriptor to delimit a nested OE candidate; reuse the actual parser.
    # Failure is a STOP, never an excuse to mark the whole region "encoded".
    second = []
    if unresolved:
        import oly_container as oe
        block = x.blocks[2]
        for index in (4, 7):
            address, length, zero1, zero2 = struct.unpack_from('<4I', block.payload, index*16)
            start = address - struct.unpack_from('<I', block.header, 8)[0] - 32
            require(zero1 == zero2 == 0 and start >= 0
                    and start+length <= len(block.payload), 'Outer descriptor bounds')
            members = [z['offset'] for z in unresolved if z['component'] == 2
                       and start <= int(z['offset'], 16) < start+length]
            require(members, 'Resource extent does not contain a candidate')
            segment = block.payload[start:start+length]
            receipt = dict(outer_descriptor=index, start=hex(start), end=hex(start+length),
                candidate_offsets=members, sha256=digest(segment),
                parser='pinned oly_container.parse')
            try:
                nested = oe.parse(segment)
            except ValueError as exc:
                receipt.update(passed=False, error=str(exc),
                    conclusion='Header/table insufficient; inner form/checksum domain unknown. This is not evidence stock is corrupt.')
            else:
                # A different input must not silently qualify without a
                # separately reviewed domain/reference proof.
                receipt.update(passed=True, blocks=len(nested),
                    conclusion='Integrity alone does not establish address-domain isolation')
            second.append(receipt)
    return dict(qualified=not unresolved and not branches,
                loads=loads, initializer_dispatch=initializers,
                initializer_table=hex(table), initializer_sha256=digest(x.read(table, size)),
                classified_references=classified, unresolved_references=unresolved,
                second_method=second,
                relative_candidates=[{k:v for k,v in z.items() if k != 'source_hex'}
                                     for z in branches],
                limits='Opaque initializer callbacks; no exhaustive computed/DMA references, boot, cache or scheduling proof')

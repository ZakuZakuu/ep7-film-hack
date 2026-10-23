#!/usr/bin/env python3
"""Original E-P7 placement/update-boundary probes; no physical I/O.

Method reference only: fishcu/oly_fw_analysis@539fcf1 CODE_SPACE/VALIDATION.
The external instruction engine stops on every undeclared access or instruction.
"""
import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import re
import struct

from ep7_color_min import (Experiment, BASE, CAVE, SECTION_START, SECTION_END,
                           STACK, SP, CALLER, INPUT, digest, require)


def captures(result):
    return {m['name']: bytes.fromhex(m['hex']) for m in result['memory']}


def modeled_return(x, result):
    """One reviewed direct CALL boundary, not a substitute CPU interpreter."""
    regs = dict(result['registers'])
    stack = captures(result)['stack']
    op, operands = x.instructions[result['trace'][-1]['pc']]
    match = re.fullmatch(r'0x[0-9a-f]+,\[([^]]*)\],(\d+)', operands)
    require(op == 'call' and match is not None, 'Boundary lacks a reviewed direct CALL')
    names = [name for name in match[1].split(',') if name]
    require(set(names) <= {'d2', 'd3', 'a2', 'a3'}, 'Unsupported modeled save mask')
    restored = regs['sp'] + int(match[2])
    for index, name in enumerate(names):
        regs[name] = struct.unpack_from('<I', stack, restored-STACK-4*(index+1))[0]
    regs.update(pc=struct.unpack_from('<I', stack, restored-STACK)[0], sp=restored, d0=0)
    return regs


def load(x, image, label, poison):
    r = x.provider.Region
    code = x.assemble(label + '_caller', 'call native_loader,[d2,d3,a2,a3],24\nnop\n',
                      symbols={'native_loader': 0x600457e7})
    ram = bytes([poison]) * (SECTION_END-SECTION_START)
    regions = [r('before', BASE, image[:SECTION_START-BASE], 'rx'),
               r('after', SECTION_END, image[SECTION_END-BASE:], 'rx'),
               r('loaded', SECTION_START, ram, 'rwx', True),
               r('uncached', SECTION_START+0x40000000, ram, 'rwx', False, 'loaded'),
               r('loaded_flags', 0xa272e420, bytes(4), 'rw', True),
               r('stack', STACK, bytes(0x2000), 'rw', True), r('caller', CALLER, code, 'rx')]
    result = x.provider.execute(regions, {'pc': CALLER, 'sp': SP, 'd0': 2},
                                CALLER+len(code), limit=1000, trace_limit=1000,
                                breakpoints=[0x6005bc79])
    x.audit_alignment(result)
    require(result['status'] == 'breakpoint', 'Unexpected loader boundary')
    args = tuple(result['registers'][key] for key in ('a0', 'a1', 'd0', 'd1'))
    require(args == (0xa0280800, 0x80900800, SECTION_END-SECTION_START, 257),
            'Unmodeled storage access')
    payload = image[SECTION_START-BASE:SECTION_END-BASE]
    saved = captures(result)
    regions = [replace(q, data=payload if q.name in ('loaded', 'uncached') else saved.get(q.name, q.data))
               for q in regions]
    result = x.provider.execute(regions, modeled_return(x, result), CALLER+len(code),
                                limit=1000, trace_limit=1000)
    x.audit_alignment(result)
    (x.out / (label + '.json')).write_text(json.dumps(result) + '\n')
    require(result['status'] == 'returned' and result['registers']['sp'] == SP, 'Loader return')
    require(x.captured(result, 'loaded') == payload, 'Loaded bytes mismatch')
    require(struct.unpack('<I', x.captured(result, 'loaded_flags'))[0] == 2, 'Loaded-bit mismatch')
    return payload, {'poison': poison, 'read_destination': hex(args[0]), 'read_source': hex(args[1]),
                     'read_bytes': args[2], 'sha256': digest(payload), 'loaded_bit': 2,
                     'model': 'One exact successful logical read; no NAND/ECC/cache/timing simulation'}


def initializer(x, positive_control=False):
    r = x.provider.Region
    image = x.data
    tail = 0x6055e5b0
    if positive_control:
        require(x.instructions[0x6018e19e] == ('mov', '48,d2'), 'Constructor-count location')
        changed = bytearray(image)
        struct.pack_into('<I', changed, 0x6018e1a0-BASE, 52)
        image = bytes(changed)
    regions = [r('before_padding', BASE, image[:tail-BASE], 'rx'),
               r('after_padding', SECTION_END, image[SECTION_END-BASE:], 'rx'),
               r('copied_startup_helper', 0x47000800, x.read(BASE+0x141c9e0, 0x1800), 'rx'),
               # Only constructor-output objects identified by actual literal
               # A0 arguments are supplied. Poison, not a fake successful board.
               r('core_object_outputs', 0x8ff001d0, b'\xa5'*0x300, 'rw', True),
               r('object_outputs', 0xa269cdd4, b'\xa5'*(0xa26a0908-0xa269cdd4), 'rw', True)]
    if not positive_control:
        value = x.call('initializers', 0x6018e19e, 12, regions, {}, limit=40000, mask='d2,a2')
        expected = struct.unpack('<12I', x.read(0x6055e580, 48))
        reached = {row['pc'] for row in value['trace']}
        require(set(expected) <= reached, 'Not all twelve callbacks executed')
        return {'callbacks_executed': 12, 'instructions': value['completed'],
                'padding_unmapped': [hex(tail), hex(SECTION_END)],
                'aligned_data_accesses': value['alignment_accesses_checked']}
    code = x.assemble('count_control_caller', 'call init_dispatch,[d2,a2],12\nnop\n',
                      symbols={'init_dispatch': 0x6018e19e})
    regions += [r('caller', CALLER, code, 'rx'), r('stack', STACK, bytes(0x2000), 'rw', True)]
    value = x.provider.execute(regions, {'pc': CALLER, 'sp': SP}, CALLER+len(code),
                               limit=40000, trace_limit=40000)
    (x.out / 'initializer_count_control.json').write_text(json.dumps(value) + '\n')
    require(value['status'] == 'memory_fault' and value['fault']['address'] == tail
            and value['fault']['access'] == 'read', 'Count control must hit inaccessible padding')
    return {'counterfactual_count': 52, 'expected_fault': hex(tail), 'access': 'read'}


def update_boundary(x):
    import oly_container  # Separately obtained provider, loaded by Experiment.
    r = x.provider.Region
    # Own fixture payload with the exact stock model/build header. No executable
    # content or installable update is created; flash entry is a terminal trap.
    payload = bytes((index*23+7) & 255 for index in range(256))
    header = bytearray(x.blocks[0].header)
    struct.pack_into('<I', header, 12, len(payload))
    trailer = bytearray(header)
    struct.pack_into('<I', trailer, 28, -oly_container.sum32(header+payload+trailer) & 0xffffffff)
    package = bytes(header)+oly_container.encode(payload)+bytes(trailer)
    code = x.assemble('updater_caller', 'call shared_updater,[d2,d3,a2,a3],16\nnop\n',
                      symbols={'shared_updater': 0x60c964c1})
    models, backend = {0x6002247c, 0x6002266d}, 0x600c4f35
    output = []
    for label, raw in [('same_version_valid', package),
                       ('bad_checksum', package[:40]+bytes([package[40]^1])+package[41:])]:
        regions = [r('image', BASE, x.data, 'rx'), r('package', INPUT, raw, 'rw', True),
                   r('stack', STACK, bytes(0x2000), 'rw', True), r('caller', CALLER, code, 'rx')]
        regs = {'pc': CALLER, 'sp': SP, 'a0': INPUT, 'a1': 0, 'd0': len(raw), 'd1': 0}
        events = []
        for iteration in range(20):
            value = x.provider.execute(regions, regs, CALLER+len(code), limit=100000,
                                       trace_limit=100000, breakpoints=sorted(models | {backend}))
            x.audit_alignment(value)
            (x.out / f'{label}_{iteration}.json').write_text(json.dumps(value) + '\n')
            regs = value['registers']
            if value['status'] == 'returned':
                require(label == 'bad_checksum' and regs['d0'] == 0x3211, 'Wrong checksum rejection')
                events.append({'returned': True, 'result': hex(regs['d0'])})
                break
            require(value['status'] == 'breakpoint', 'Unmodeled updater stop')
            if regs['pc'] == backend:
                require(label == 'same_version_valid', 'Invalid input reached flash boundary')
                require((regs['a0'], regs['a1'], regs['d0'], regs['d1']) ==
                        (0x806a0000, INPUT, len(raw), 1), 'Unexpected backend request')
                events.append({'trapped_before_flash': True, 'bytes': regs['d0'], 'destination': hex(regs['a0'])})
                break
            require(regs['pc'] in models, 'Unreviewed service model')
            events.append({'diagnostic_suppressed': hex(regs['pc'])})
            saved = captures(value)
            regions = [replace(q, data=saved.get(q.name, q.data)) for q in regions]
            regs = modeled_return(x, value)
        else:
            raise ValueError('Exceeded diagnostic-boundary limit')
        output.append({'case': label, 'header_build_word': struct.unpack_from('<H', header, 16)[0],
                       'events': events})
    return output


def actual_main_checksum(x, image, name):
    """Native checksum on the whole real component, not just a tiny fixture."""
    import oly_container
    r = x.provider.Region
    block = oly_container.replace_payload(x.blocks[0], image)
    data = block.header + block.payload + block.trailer
    require(len(data) % 4 == 0 and INPUT % 4 == 0 and SP % 4 == 0, 'Checksum alignment')
    require(x.instructions[0x600fa459] == ('mov', '(a0),d1')
            and x.instructions[0x600fa45a] == ('inc4', 'a0'), 'Checksum stride contract')
    code = x.assemble(name+'_caller', 'call native_checksum,[d2],4\nnop\n',
                      symbols={'native_checksum': 0x600fa454})
    value = x.provider.execute([
        x.region('checksum_code', 0x600fa454, 0x600fa465-0x600fa454, 'rx'),
        r('component_words', INPUT, data), r('stack', STACK, bytes(0x2000), 'rw', True),
        r('caller', CALLER, code, 'rx')],
        {'pc': CALLER, 'sp': SP, 'd0': len(data), 'a0': INPUT, 'd2': 0x13572468},
        CALLER+len(code), limit=50000000, trace_limit=32, trace_tail=True, timeout=60)
    (x.out / (name+'.json')).write_text(json.dumps(value) + '\n')
    require(value['status'] == 'returned' and value['registers']['d0'] == 0
            and value['registers']['sp'] == SP and value['registers']['d2'] == 0x13572468,
            'Actual component native checksum failure')
    return {'bytes': len(data), 'native_result': 0, 'instructions': value['completed'],
            'alignment': 'Word-aligned base, fixed inc4 stride and word-length extent; bounded tail trace'}


def run(x, matrix=True):
    for label, a, b in [
        ('end_getter', 0x60045786, 0x600457e7), ('loader', 0x600457e7, 0x6004586c),
        ('alias', 0x60067102, 0x60067146), ('init_dispatch', 0x6018e19e, 0x6018e214),
        ('constructors', 0x603d9f9e, 0x603de100), ('updater', 0x60c964c1, 0x60c9718c),
        ('checksum', 0x60c95a43, 0x60c95b0c), ('decode', 0x60c95b0c, 0x60c95bab),
        ('headers', 0x600fa454, 0x600fa54d), ('header_tag_compare', 0x600daf1c, 0x600daf58),
        ('decode_wrapper', 0x60c9718c, 0x60c97259)]:
        x.disassemble(label, a, b)
    helper = x.out / 'startup_helper.bin'
    helper.write_bytes(x.read(BASE+0x141c9e0, 0x1800))
    import subprocess
    text = subprocess.check_output([str(x.tools/'binutils/objdump'), '-D', '-z', '-b', 'binary',
                                    '-m', 'mn10300', '--no-show-raw-insn', '--adjust-vma=0x47000800',
                                    str(helper)], text=True)
    (x.out / 'startup_helper.asm').write_text(text)
    x.remember_instructions(text)
    r = x.provider.Region
    sections = []
    for sid in range(11):
        value = x.call(f'end_{sid}', 0x60045786, 0, [r('image', BASE, x.data, 'rx')],
                       {'d0': sid}, limit=100, mask='')
        end = value['registers']['d0']
        if sid in (0, 10):
            require(end == 0, 'Invalid-section control')
            continue
        a, source, dest = struct.unpack('<III', x.read(0x60027068+(sid-1)*12, 12))
        require(a == dest and source-a == -0x1f980000 and a <= end, 'Section descriptor relation')
        sections.append({'id': sid, 'start': hex(a), 'end': hex(end), 'source': hex(source)})
    require(sections[1]['start'] == hex(SECTION_START) and sections[1]['end'] == hex(SECTION_END),
            'COLOR section bounds')
    candidate, extension = x.make_candidate(CAVE)
    require(len(extension) == 44 and CAVE >= 0x6055e5b0+64 and CAVE+44 <= SECTION_END-64,
            'Code placement margin')
    x.loaded_original, original = load(x, x.data, 'load_original', 0xa5)
    x.loaded_changed, changed = load(x, candidate, 'load_changed', 0xa5)
    reloaded, reload = load(x, candidate, 'reload_changed', 0x55)
    require(reloaded == x.loaded_changed, 'Reload lost extension')
    init = initializer(x)
    count_control = initializer(x, True)
    # Reuse external candidate scanners as tools. No scanner source or OEM
    # context-byte strings are copied into this repository.
    from penf_code_space_audit import pointer_candidates, branch_candidates
    pointers = []
    for address in (CAVE, CAVE+0x40000000, CAVE-0x1f980000, CAVE+0x20680000):
        for block in x.blocks:
            pointers += pointer_candidates(block.payload, address, address+len(extension))
    branches = branch_candidates(x.data, BASE, [(CAVE, CAVE+len(extension))])[0]
    require(not pointers and not branches, 'Unresolved references into actual extension span')
    # Actual E-file row, linked through startup-relocated pointer data.
    require(x.read(0x60f2cb30, 11) == b'E142????BIN', 'SD model filename pattern')
    require(struct.unpack('<5I', x.read(0x60f2ccb8, 20)) == (0, 0, 0x61fb0140, 4, 1), 'SD E-file row')
    require(struct.unpack('<I', x.read(0x60248400, 4))[0] == 0x60f2cb30, 'Filename pointer initializer')
    result = {'section2': sections[1], 'cave': hex(CAVE), 'extension_bytes': len(extension),
              'extension_sha256': digest(extension), 'original_load': original,
              'changed_load': changed, 'reload': reload, 'initializer': init,
              'initializer_positive_control': count_control,
              'literal_candidates_in_modified_span': len(pointers), 'relative_candidates': len(branches),
              'sd_filename': 'DCOLYMP/E1429999.BIN', 'update_boundary': update_boundary(x),
              'limits': ['Declared object buffers; startup and hardware scheduling not reproduced',
                         'Logical storage read succeeds; NAND, cache coherence and recovery not simulated',
                         'Reference scans cannot exclude arbitrary computed/DMA accesses',
                         'Same-version header fixture is not a physical installation or whole-package write']}
    if matrix:
        result['loaded_hook_matrix'] = x.compare_hook(CAVE)
        result['actual_component_checksums'] = {
            'stock': actual_main_checksum(x, x.data, 'checksum_stock'),
            'candidate': actual_main_checksum(x, candidate, 'checksum_candidate')}
    (x.out / 'install-checks.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream', type=Path, required=True)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    x = Experiment(args.upstream, args.stock, args.out)
    x.mapping()
    result = run(x)
    print(json.dumps({key: result[key] for key in ('section2', 'cave', 'extension_bytes',
                                                  'extension_sha256', 'initializer', 'update_boundary')}, indent=2))


if __name__ == '__main__':
    main()

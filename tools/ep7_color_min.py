#!/usr/bin/env python3
"""Original, exact-build E-P7 COLOR checks using separately obtained GNU tools.

Reference map: fishcu/oly_fw_analysis@539fcf1 (read/run, not vendored).
All OEM-derived outputs and execution traces are confined to private /tmp.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import sys

STOCK_SHA = '9d1610124ad98f6edae4540182205f06c9c703d9033ef0c4f19847193f95eaeb'
MAIN_SHA = '5dd9af164b4590c7e82f6905c919b3cc450bb58f2d5742ab2a0e3a4eb2e26190'
TABLE_SHA = 'a33d64bdb78ac41ba24ccbff820380f563211a095ac08a12a7c37a51b5c00531'
BASE, TABLE, GAINS = 0x60020020, 0x6051de2c, 0x60531810
BUILDER, SELECTOR, WRITER = 0x603b0068, 0x603b0252, 0x6034667e
STACK, SP, CALLER, INPUT, OUTPUT = 0x18010000, 0x18011000, 0x18020000, 0x19000000, 0x19100000
CONTEXT, EXTENSION = 0x19200000, 0x1a000000  # Explicit synthetic RAM, not camera placement.
CAVE, SECTION_START, SECTION_END = 0x6055e5f0, 0x60280800, 0x6055e800
WINDOWS = {
    'builder': (BUILDER, 0x603b0247), 'selector': (SELECTOR, 0x603b0345),
    'writer': (WRITER, 0x6034677b), 'dispatch_a': (0x60345f81, 0x60345f94),
    'dispatch_b': (0x60345fa0, 0x60345fb6),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


class Experiment:
    def __init__(self, upstream, stock, out):
        self.root, self.out = Path(upstream).resolve(), Path(out).resolve()
        require(Path('/tmp') in self.out.parents, 'Private experiment outputs must be under /tmp')
        self.out.mkdir(parents=True, exist_ok=True, mode=0o700)
        require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=self.root, text=True).strip()
                == '539fcf1fa9eda5fdef8ede4deeab94a4691d94c3', 'Wrong external revision')
        sys.path.insert(0, str(self.root / 'tools'))
        import oly_container
        import penf_emulator
        self.provider = penf_emulator
        raw = Path(stock).read_bytes()
        require(len(raw) == 111017984 and digest(raw) == STOCK_SHA, 'Stock identity mismatch')
        blocks = oly_container.parse(raw)
        require(oly_container.reconstruct(blocks) == raw, 'Container roundtrip mismatch')
        self.data = blocks[0].payload
        require(digest(self.data) == MAIN_SHA, 'Decoded identity mismatch')
        self.image = self.out / 'main.bin'
        self.image.write_bytes(self.data)
        self.tools = self.root / 'toolchains/mn103-patch-build'
        self.blocks = blocks
        self.instructions = {}

    def read(self, address, length):
        start = address - BASE
        require(0 <= start < start + length <= len(self.data), 'Image bounds')
        return self.data[start:start + length]

    def region(self, label, address, length, permissions='r', capture=False):
        return self.provider.Region(label, address, self.read(address, length), permissions, capture)

    def disassemble(self, label, start, end):
        text = subprocess.check_output([
            str(self.tools / 'binutils/objdump'), '-b', 'binary', '-m', 'mn10300', '-D', '-z',
            '--no-show-raw-insn', f'--adjust-vma={BASE}', f'--start-address={start}',
            f'--stop-address={end}', str(self.image)], text=True)
        (self.out / (label + '.asm')).write_text(text)
        self.remember_instructions(text)
        return text

    def remember_instructions(self, text):
        for row in text.splitlines():
            match = re.match(r'^\s*([0-9a-f]+):\s+([a-z][a-z0-9]*)\s*(.*)$', row)
            if match:
                self.instructions[int(match[1], 16)] = (match[2], match[3].strip())

    def mapping(self):
        for name, (a, b) in WINDOWS.items():
            self.disassemble(name, a, b)
        require(digest(self.read(TABLE, 3028)) == TABLE_SHA, 'COLOR table identity')
        require(self.data.count(self.read(TABLE, 3028)) == 1, 'Ambiguous table')
        require(struct.unpack_from('<I', self.data, 0xb8)[0] - 0xd9 == BASE, 'Entry-derived map')
        require(self.instructions[0x603b02d9] == ('call', '0x603b0068,[d2,d3,a2,a3],96'), 'Builder call')
        require(self.instructions[0x603b0072] == ('mov', 'd0,(sp)'), 'Builder entry alignment')
        require(self.instructions[0x603b006e] == ('add', '688,d0'), 'Output records')
        require(self.instructions[0x603b01d8] == ('mov', 'd0,(976,a0)'), 'Control field')
        require(self.instructions[0x603b02c8] == ('add', '1816,a3'), 'Saturation request')
        require(self.instructions[0x60346709] == ('mov', '752,a2'), 'MMIO record offset')
        require(self.instructions[0x60346713] == ('mov', '1040,a1'), 'MMIO end bound')
        for at, target in [(0x60345f89, 0x9f001000), (0x60345fab, 0x9f805000)]:
            require(self.instructions[at] == ('mov', f'{target - 2**32},a0'), 'MMIO base')
        require(self.instructions[0x60345f8f] == ('call', '0x6034667e,[d2,d3,a2,a3],24'), 'Writer dispatch A')
        require(self.instructions[0x60345fb1] == ('call', '0x6034667e,[d2,d3,a2,a3],24'), 'Writer dispatch B')
        result = {
            'stock_sha256': STOCK_SHA, 'main_sha256': MAIN_SHA, 'code_base': hex(BASE),
            'component_checksums': len(self.blocks), 'exact_container_roundtrip': True,
            'table': hex(TABLE), 'table_bytes': 3028, 'table_sha256': TABLE_SHA,
            'gains': hex(GAINS), 'hook_call': '0x603b02d9', 'resume': '0x603b02de',
            'record_offset': 688, 'control_offset': 976, 'saturation_request_offset': 1816,
            'h_halfword_offset_in_record': 18, 's_halfword_offset_in_record': 20,
            'l_halfword_offset_in_record': 22,
            'windows': {name: {'start': hex(a), 'end_exclusive': hex(b), 'sha256': digest(self.read(a, b-a))}
                        for name, (a, b) in WINDOWS.items()},
        }
        (self.out / 'map.json').write_text(json.dumps(result, indent=2) + '\n')
        return result

    def assemble(self, name, source, base=CALLER, symbols=None):
        path = self.out / name
        prefix = '' if re.search(r'(?m)^_start:', source) else '.text\n.global _start\n_start:\n'
        path.with_suffix('.s').write_text(prefix + source)
        subprocess.run([str(self.tools / 'gas/as-new'), '-o', str(path.with_suffix('.o')),
                        str(path.with_suffix('.s'))], check=True)
        definitions = [f'--defsym={key}={value:#x}' for key, value in (symbols or {}).items()]
        subprocess.run([str(self.tools / 'ld/ld-new'), '-Ttext', hex(base), '-e', '_start', *definitions,
                        '-o', str(path.with_suffix('.elf')), str(path.with_suffix('.o'))], check=True)
        subprocess.run([str(self.tools / 'binutils/objcopy'), '-O', 'binary', '-j', '.text',
                        str(path.with_suffix('.elf')), str(path.with_suffix('.bin'))], check=True)
        text = subprocess.check_output([str(self.tools / 'binutils/objdump'), '-d',
                                        '--no-show-raw-insn', str(path.with_suffix('.elf'))], text=True)
        (path.with_suffix('.asm')).write_text(text)
        self.remember_instructions(text)
        return path.with_suffix('.bin').read_bytes()

    def audit_alignment(self, result):
        require(not result['trace_truncated'], 'Incomplete trace cannot qualify alignment')
        count = 0
        for row in result['trace']:
            require(row['pc'] in self.instructions, f'Unreviewed trace PC {row["pc"]:#x}')
            op, args = self.instructions[row['pc']]
            if op in ('call', 'calls', 'ret', 'retf', 'movm'):
                require(row['sp'] % 4 == 0, 'Unaligned stack operation')
            if op in ('jmp', 'calls'):
                continue  # Register-indirect code targets are not data loads.
            memory = re.findall(r'\(([^)]+)\)', args)
            if not memory:
                continue
            require(op in ('mov', 'movhu', 'movbu', 'movm'), f'Unadmitted memory operation {op}')
            width = {'movhu': 2, 'movbu': 1}.get(op, 4)
            for expression in memory:
                address = sum(row[token.strip()] if token.strip() in row else int(token.strip(), 0)
                              for token in expression.split(',')) & 0xffffffff
                require(address % width == 0, f'Unaligned {width}-byte access at {row["pc"]:#x}')
                count += 1
        return count

    def call(self, name, target, frame, regions, registers, limit=20000, mask='d2,d3,a2,a3'):
        code = self.assemble(name + '_caller', f'call ep7_target,[{mask}],{frame}\nnop\n',
                             symbols={'ep7_target': target})
        defaults = {f'd{i}': 0x12340000 + i for i in range(4)}
        defaults.update({f'a{i}': 0x56780000 + i for i in range(4)})
        defaults.update(pc=CALLER, sp=SP, psw=0, mdr=0x87654321)
        defaults.update(registers)
        r = self.provider.Region
        result = self.provider.execute([
            r('caller', CALLER, code, 'rx'), r('stack', STACK, bytes(0x2000), 'rw', True),
            *regions], defaults, CALLER + len(code), limit=limit, trace_limit=limit)
        (self.out / (name + '.json')).write_text(json.dumps(result, indent=2) + '\n')
        require(result['status'] == 'returned', f'{name}: stopped: {result["status"]} {result["fault"]}')
        require(result['registers']['sp'] == SP, 'Stack not balanced')
        result['alignment_accesses_checked'] = self.audit_alignment(result)
        return result

    @staticmethod
    def captured(result, name):
        return bytes.fromhex(next(m['hex'] for m in result['memory'] if m['name'] == name))

    def construct(self, name, saturation):
        r = self.provider.Region
        pointers = struct.unpack('<12I', self.read(GAINS, 48))
        regions = [self.region('builder_code', BUILDER, 0x603b0247 - BUILDER, 'rx'),
                   self.region('color_table', TABLE, 3028), self.region('gain_pointers', GAINS, 48),
                   r('saturation', INPUT, struct.pack('<12b', *saturation)),
                   r('output', OUTPUT, bytes(3164), 'rw', True)]
        regions += [self.region(f'gain_{p:x}', p, 4) for p in sorted(set(pointers))]
        return self.call(name, BUILDER, 96, regions, {
            'a0': TABLE, 'a1': INPUT, 'd1': OUTPUT,
            'd0': struct.unpack('<H', self.read(TABLE + 3024, 2))[0]})

    def upload(self, name, parameters, mmio):
        r = self.provider.Region
        require(mmio in (0x9f001000, 0x9f805000), 'Unmodeled ISP window')
        start, end, flag = ((0x60345f81, 0x60345f94, 8) if mmio == 0x9f001000
                            else (0x60345fa0, 0x60345fb6, 0x40000))
        context = bytearray(128)
        struct.pack_into('<I', context, 12, OUTPUT)
        # Execute the real dispatcher field load and native CALL as well as the
        # writer. Stop at that call's return, before unrelated downstream work.
        result = self.provider.execute([
            self.region('dispatcher', start, end-start, 'rx'),
            self.region('writer_code', WRITER, 0x6034677b - WRITER, 'rx'),
            r('upload_context', CONTEXT, bytes(context)), r('parameters', OUTPUT, parameters),
            r('stack', STACK, bytes(0x2000), 'rw', True),
            r('mmio', mmio, bytes(1120), 'w', True)],
            {'pc': start, 'sp': SP, 'a3': CONTEXT, 'd3': flag, 'mdr': 0x87654321},
            end, limit=10000, trace_limit=10000)
        (self.out / (name+'.json')).write_text(json.dumps(result) + '\n')
        require(result['status'] == 'returned' and result['registers']['sp'] == SP,
                f'Actual upload dispatcher stopped: {result["fault"]}')
        require(any(row['pc'] == WRITER for row in result['trace']), 'Writer was skipped')
        result['alignment_accesses_checked'] = self.audit_alignment(result)
        return result

    def profiles(self):
        result = []
        starts = [0x602b814e, 0x602b823c, 0x602b832a, 0x602b8418, 0x602b850d]
        for index, (public_id, first_saturation) in enumerate(zip([54, 55, 56, 64], [927, 939, 951, 1655])):
            a, b = starts[index:index+2]
            require(struct.unpack('<I', self.read(0x60460458 + 4*public_id, 4))[0] == a,
                    'Profile selector table')
            text = self.disassemble(f'profile_{index+1}', a, b)
            keys = [int(x) for x in re.findall(r'\bmov\s+(\d+),a0', text)]
            require(keys[-12:] == list(range(first_saturation, first_saturation + 12)),
                    'Per-profile saturation source')
            require(all('0x602b2237,' in operands for op, operands in
                        (self.instructions[pc] for pc in self.instructions if a <= pc < b)
                        if op == 'call'), 'Unexpected profile getter')
            saturation = list(struct.unpack('<12i', self.read(0x604a8774 + first_saturation*4, 48)))
            result.append({'profile': index+1, 'public_mode': public_id,
                           'entry': hex(a), 'saturation_keys': keys[-12:], 'default_saturation': saturation})
        return result

    def make_candidate(self, address):
        require(address in (EXTENSION, CAVE), 'Unqualified extension address')
        source = (Path(__file__).resolve().parents[1] / 'patches/hsl-min/e-p7/hook.s').read_text()
        extension = self.assemble('candidate_extension', source, address,
                                  {'ep7_builder': BUILDER, 'ep7_resume': 0x603b02de})
        jump = self.assemble('candidate_jump', 'jmp ep7_extension\n', 0x603b02d9,
                             {'ep7_extension': address})
        require(len(jump) == 5, 'Hook must replace exactly the original call extent')
        image = self.data[:0x603b02d9-BASE] + jump + self.data[0x603b02de-BASE:]
        if BASE <= address < BASE + len(image):
            require(self.read(address, len(extension)) == b'\xff'*len(extension), 'Cave not padding')
            image = image[:address-BASE] + extension + image[address-BASE+len(extension):]
        return image, extension

    def selector(self, name, key, saturation, *, patched=False, flags=None, address=EXTENSION):
        require(address in (EXTENSION, CAVE), 'Unqualified extension address')
        r = self.provider.Region
        request = bytearray(4096)
        request[8], request[9] = key >> 24 & 255, key >> 16 & 255
        struct.pack_into('<H', request, 10, key & 0xffff)
        struct.pack_into('<12b', request, 1816, *saturation)
        context = bytearray(128)
        struct.pack_into('<I', context, 4, INPUT)
        struct.pack_into('<I', context, 12, OUTPUT)
        struct.pack_into('<I', context, 60, flags if flags is not None else (2 if key == 11 else 0x6420ae))
        image = self.data
        extra = []
        # Model only a preloaded, exact image plus bounded request/context/stack.
        # No global RAM, service responses or MMIO reads are synthesized.
        self.disassemble('preset_builder', 0x603af871, BUILDER)
        self.disassemble('preset_selector_helper', 0x603b551d, 0x603b559f)
        self.disassemble('selector', SELECTOR, 0x603b0345)
        if patched:
            image, extension = self.make_candidate(address)
            if not BASE <= address < BASE + len(image):
                extra.append(r('synthetic_extension', address, extension, 'rx'))
        if address == CAVE:
            selected = getattr(self, 'loaded_changed' if patched else 'loaded_original',
                               image[SECTION_START-BASE:SECTION_END-BASE])
            require(selected == image[SECTION_START-BASE:SECTION_END-BASE], 'Loaded section differs')
            code_region = r('loaded_section', SECTION_START, selected, 'rx')
        else:
            code_region = r('preloaded_image', BASE, image, 'rx')
        result = self.call(name, SELECTOR, 20, [
            code_region, r('request', INPUT, bytes(request)),
            r('context', CONTEXT, bytes(context), 'rw', True),
            r('output', OUTPUT, bytes(3164), 'rw', True), *extra], {'a0': CONTEXT})
        return result

    def compare_hook(self, address=EXTENSION):
        profiles = self.profiles()
        cases = [('COLOR'+str(p['profile']), 11, p['default_saturation']) for p in profiles]
        cases += [('Natural_associated_key2', 2, [0]*12),
                  ('MONO_key12', 12, [0]*12), ('ART_key01010064', 0x01010064, [0]*12)]
        evidence = []
        allowed = {706, 707, 782, 783}
        for label, key, saturation in cases:
            original = self.selector(label + '_original', key, saturation, address=address)
            changed = self.selector(label + '_changed', key, saturation, patched=True, address=address)
            a, b = (self.captured(result, 'output') for result in (original, changed))
            differences = {i for i, (x, y) in enumerate(zip(a, b)) if x != y}
            require(differences == (allowed if key == 11 else set()), f'{label}: output divergence')
            require(original['registers'] == changed['registers'], f'{label}: register divergence')
            require(self.captured(original, 'context') == self.captured(changed, 'context'),
                    f'{label}: context divergence')
            # Only released scratch below SP can differ. Live caller stack is exact.
            require(self.captured(original, 'stack')[SP-STACK:] == self.captured(changed, 'stack')[SP-STACK:],
                    f'{label}: live stack divergence')
            uploads = []
            for index, mmio_base in enumerate((0x9f001000, 0x9f805000)):
                u = self.upload(label + f'_upload_{index}_original', a, mmio_base)
                v = self.upload(label + f'_upload_{index}_changed', b, mmio_base)
                x, y = self.captured(u, 'mmio'), self.captured(v, 'mmio')
                delta = {i for i, (xx, yy) in enumerate(zip(x, y)) if xx != yy}
                require(delta == ({i+64 for i in allowed} if key == 11 else set()),
                        f'{label}: MMIO divergence')
                require(u['registers'] == v['registers'], f'{label}: writer register divergence')
                uploads.append({'base': hex(mmio_base), 'changed_byte_offsets': sorted(delta)})
            evidence.append({'case': label, 'key': hex(key), 'output_changed_bytes': sorted(differences),
                             'registers_context_live_stack_equal': True, 'uploads': uploads,
                             'yellow_h': struct.unpack_from('<h', b, 706)[0],
                             'blue_l': struct.unpack_from('<h', b, 782)[0],
                             'aligned_accesses': original['alignment_accesses_checked'] + changed['alignment_accesses_checked']})
        return {'profiles': profiles, 'cases': evidence,
                'placement': hex(address),
                'code_loaded_by_native_probe': hasattr(self, 'loaded_changed'),
                'hardware_model': 'Two write-only coefficient windows; no ISP pixels or device access'}


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream', type=Path, required=True)
    parser.add_argument('--stock', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--stock-probe', action='store_true')
    parser.add_argument('--compare-hook', action='store_true')
    parser.add_argument('--extension-address', type=lambda s: int(s, 0), default=EXTENSION)
    args = parser.parse_args()
    experiment = Experiment(args.upstream, args.stock, args.out)
    result = experiment.mapping()
    if args.compare_hook:
        result['hook_comparison'] = experiment.compare_hook(args.extension_address)
    if args.stock_probe:
        baseline = experiment.construct('stock_neutral', [0] * 12)
        parameters = experiment.captured(baseline, 'output')
        uploads = []
        for i, mmio in enumerate((0x9f001000, 0x9f805000)):
            upload = experiment.upload(f'stock_upload_{i}', parameters, mmio)
            memory = experiment.captured(upload, 'mmio')
            require(memory[752:1040] == parameters[688:976], 'Native MMIO record copy mismatch')
            uploads.append({'base': hex(mmio), 'instructions': upload['completed'],
                            'alignment_checks': upload['alignment_accesses_checked']})
        result['stock_probe'] = {'instructions': baseline['completed'],
                                 'alignment_checks': baseline['alignment_accesses_checked'],
                                 'uploads': uploads}
    (experiment.out / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

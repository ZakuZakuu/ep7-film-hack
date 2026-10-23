"""Original negative controls for build guards and experiment consistency."""
import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from ep7_color_min import Experiment, CAVE

spec = importlib.util.spec_from_file_location('hsl_builder', ROOT/'patches/hsl-min/e-p7/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class MatrixSpy(Experiment):
    """Own parameter bytes only; tests target identity across matrix iterations."""
    def __init__(self):
        self.addresses = []

    def profiles(self):
        return [{'profile': 1, 'default_saturation': [0]*12}]

    def selector(self, name, key, saturation, *, patched=False, address=None):
        self.addresses.append(address)
        if address != CAVE:
            raise ValueError('Matrix switched execution into an MMIO window')
        data = bytearray(3164)
        if patched and key == 11:
            struct.pack_into('<h', data, 706, -3000)
            struct.pack_into('<h', data, 782, -200)
        return {'output': bytes(data), 'context': bytes(128), 'stack': bytes(8192),
                'registers': {'d0': 7}, 'alignment_accesses_checked': 1}

    def upload(self, name, parameters, mmio):
        data = bytearray(1120)
        data[752:1040] = parameters[688:976]
        return {'mmio': bytes(data), 'registers': {'d0': 3}}

    @staticmethod
    def captured(result, name):
        return result[name]


class HslContracts(unittest.TestCase):
    def test_mmio_loop_cannot_change_extension_placement(self):
        spy = MatrixSpy()
        evidence = spy.compare_hook(CAVE)
        self.assertEqual(spy.addresses, [CAVE]*8)
        self.assertEqual(evidence['placement'], hex(CAVE))

    def test_mmio_is_never_an_admitted_execution_extension(self):
        value = object.__new__(Experiment)
        for address in (0x9f001000, 0x9f805000):
            with self.assertRaisesRegex(ValueError, 'Unqualified extension'):
                value.make_candidate(address)

    def test_halfword_alignment_blind_spot_is_rejected(self):
        value = object.__new__(Experiment)
        value.instructions = {0x1000: ('movhu', 'd0,(2,a0)')}
        with self.assertRaisesRegex(ValueError, 'Unaligned 2-byte'):
            value.audit_alignment({'trace_truncated': False, 'trace': [{'pc': 0x1000, 'a0': 0x2001}]})
        self.assertEqual(value.audit_alignment({
            'trace_truncated': False, 'trace': [{'pc': 0x1000, 'a0': 0x2000}]}), 1)

    def test_wrong_stock_stops_before_any_output_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            stock = root/'wrong.BIN'
            stock.write_bytes(b'own invalid input')
            output = root/'output'
            with self.assertRaisesRegex(ValueError, 'Exact E-P7'):
                builder.build(SimpleNamespace(stock=stock, out=output))
            self.assertFalse(output.exists())

    def test_original_range_and_bounds_must_both_match(self):
        data = b'own guarded bytes'
        with self.assertRaisesRegex(ValueError, 'guard failed'):
            builder.guarded_range(data, {'decoded_offset': '0x0', 'length': 4, 'original_sha256': '0'*64})
        with self.assertRaisesRegex(ValueError, 'outside main'):
            builder.guarded_range(data, {'decoded_offset': '0x100', 'length': 4, 'original_sha256': '0'*64})

    def test_proprietary_output_cannot_be_written_into_checkout(self):
        with self.assertRaisesRegex(ValueError, 'outside the checked-out repository'):
            builder.validate_output_directory(ROOT/'work'/'not-a-private-firmware-output')


if __name__ == '__main__':
    unittest.main()

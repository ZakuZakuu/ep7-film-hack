"""Synthetic counterexamples to treating word hits as code or profile records."""
import contextlib
import hashlib
import io
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.inspect_olympus_oe import FormatError, inspect
from tools.probe_oe_executable import Instruction
from tools.probe_oe_references import confirm_literals, main, reference_candidates
from test_inspect_olympus_oe import synthetic_block


class TestReferences(unittest.TestCase):
    def test_unaligned_data_hits_remain_unclassified(self):
        data = bytearray(32)
        for at in (1, 9):
            struct.pack_into('<I', data, at, 0x60020030)
        result = reference_candidates(data, 0x60020020, [16])[0]
        self.assertEqual(result['unclassified_u32_match_offsets'], [1, 9])
        self.assertNotIn('code', result)
        self.assertEqual(reference_candidates(data, 0x60020000, [16])[0]
                         ['unclassified_u32_match_offsets'], [])

    def test_duplicate_outside_overflow_and_scope_fail_closed(self):
        for base, targets in [(0, []), (0, [0, 1, 2]), (0, [1, 1]),
                              (0, [-1]), (0, [8]), (0xffffffff, [1]), (1 << 32, [0])]:
            with self.assertRaises(FormatError):
                reference_candidates(bytes(8), base, targets)
        with self.assertRaisesRegex(FormatError, 'bounded scope'):
            reference_candidates(bytes(68), 0, [0])
        self.assertEqual(reference_candidates(bytes(67), 0, [0])[0]
                         ['unclassified_u32_match_offsets'], list(range(64)))

    def test_signed_immediate_requires_encoded_match_in_same_instruction(self):
        candidate = [{'target_payload_offset': 16, 'candidate_address_u32': 0x80000010,
                      'unclassified_u32_match_offsets': [2, 9]}]
        rows = [Instruction(0, 'mov', '-2147483632,a0'), Instruction(6, 'rets', '')]
        result = confirm_literals(rows, candidate, [0], 14)[0]
        self.assertEqual(result['encoded_u32_offsets'], [2])
        self.assertIn('independent evidence', result['note'])
        with self.assertRaises(FormatError):
            confirm_literals(rows, [{**candidate[0], 'unclassified_u32_match_offsets': [9]}], [0], 14)

    def test_other_operand_register_and_false_boundaries_rejected(self):
        c = [{'target_payload_offset': 1, 'candidate_address_u32': 123,
              'unclassified_u32_match_offsets': [2]}]
        for row in [Instruction(0, 'mov', '(a0),d0'), Instruction(0, 'mov', 'd0,a0'),
                    Instruction(0, 'add', '123,a0'), Instruction(0, 'mov', '124,a0')]:
            with self.assertRaises(FormatError):
                confirm_literals([row], c, [0], 8)
        with self.assertRaises(FormatError):
            confirm_literals([Instruction(0, 'mov', '123,a0'), Instruction(4, 'rets', '')], c, [0], 8)
        with self.assertRaises(FormatError):
            confirm_literals([Instruction(0, 'mov', '123,a0')], c, [1], 8)

    def _fixture(self, root):
        payload = bytearray(64)
        struct.pack_into('<I', payload, 1, 0x60020030)
        payload[16:30] = b'PRIVATE_MARKER'
        raw = synthetic_block(payload)
        path = Path(root) / 'fixture.bin'
        path.write_bytes(raw)
        return path, raw, ['probe', str(path), '--expected-size', str(len(raw)),
                           '--expected-sha256', hashlib.sha256(raw).hexdigest(),
                           '--block-index', '0', '--mapping-base', '0x60020020',
                           '--target-offset', '16']

    def test_cli_numeric_only_and_input_unchanged(self):
        with tempfile.TemporaryDirectory() as root:
            path, raw, argv = self._fixture(root)
            output = io.StringIO()
            with patch.object(sys, 'argv', argv), contextlib.redirect_stdout(output):
                main()
            self.assertNotIn('PRIVATE', output.getvalue())
            result = json.loads(output.getvalue())
            self.assertEqual(result['candidates'][0]['unclassified_u32_match_offsets'], [1])
            self.assertEqual(result['nominated_mov_confirmations'], [])
            self.assertEqual(path.read_bytes(), raw)

    def test_bad_hash_stops_before_decoder_and_redacts_output(self):
        with tempfile.TemporaryDirectory() as root:
            _, _, argv = self._fixture(root)
            argv[argv.index('--expected-sha256') + 1] = '0' * 64
            out, err = io.StringIO(), io.StringIO()
            with patch.object(sys, 'argv', argv), patch('tools.probe_oe_references.disassemble') as decoder, \
                    contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                    self.assertRaises(SystemExit) as caught:
                main()
            self.assertEqual(caught.exception.code, 2)
            decoder.assert_not_called()
            self.assertEqual(out.getvalue(), '')
            self.assertNotIn('PRIVATE', err.getvalue())

    def test_changed_input_metadata_stops_without_results(self):
        with tempfile.TemporaryDirectory() as root:
            path, _, argv = self._fixture(root)
            before = inspect(path)
            out, err = io.StringIO(), io.StringIO()
            with patch.object(sys, 'argv', argv), \
                    patch('tools.probe_oe_references.inspect', side_effect=[before, {**before, 'sha256': '0' * 64}]), \
                    contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                    self.assertRaises(SystemExit) as caught:
                main()
            self.assertEqual(caught.exception.code, 2)
            self.assertEqual(out.getvalue(), '')


if __name__ == '__main__':
    unittest.main()

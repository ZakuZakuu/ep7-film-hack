"""Synthetic text/control-flow counterexamples; no OEM code or ISA decoder."""
import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.inspect_olympus_oe import FormatError
from tools.probe_oe_executable import (
    Instruction, disassemble, mapping_checks, parse_objdump, summarize, walk,
)


class TestExecutableMetadata(unittest.TestCase):
    def test_synthetic_call_return_and_unresolved_target(self):
        text = """fixture: file format binary
00000000 <.data>:
   0:\tcalls\t0x8
   4:\trets
   6:\tnop
   7:\tnop
   8:\trets
"""
        rows = parse_objdump(text, 0, 10)
        caller = walk(rows, 0)
        self.assertEqual(caller['return_offsets'], [4])
        self.assertEqual(caller['visited_instructions'], 2)  # calls not followed
        self.assertEqual(caller['direct_calls'][0]['target'], 8)
        self.assertEqual(walk(rows, 8)['return_offsets'], [8])
        self.assertEqual(walk(rows, 9)['unresolved_offsets'], [9])

    def test_mapping_off_by_header_and_signed_immediate(self):
        rows = [Instruction(0, 'mov', '-2147483616,a0'),
                Instruction(8, 'mov', '0x80000028,a0'),
                Instruction(32, 'jmp', '0x40'), Instruction(64, 'rets', '')]
        good = mapping_checks(rows, 0x80000000, [0, 8])
        wrong = mapping_checks(rows, 0x80000020, [0, 8])
        self.assertTrue(good[0]['target_is_direct_branch'])
        self.assertFalse(good[1]['target_is_instruction_boundary'])
        self.assertFalse(wrong[0]['target_is_direct_branch'])
        with self.assertRaises(FormatError):
            mapping_checks(rows, 1 << 32, [0])
        with self.assertRaises(FormatError):
            mapping_checks([Instruction(0, 'mov', '(a0),d0')], 0, [0])

    def test_bad_bounds_and_output_order_fail_closed(self):
        for text in [' 10:\tnop', ' 0:\tnop\n 0:\tnop', 'no instructions']:
            with self.assertRaises(FormatError):
                parse_objdump(text, 0, 10)
        with self.assertRaises(FormatError):
            disassemble(Path('/unused'), b'x' * (128 * 1024 + 1), 0)

    def test_conditional_paths_indirect_stop_and_budget(self):
        rows = [Instruction(0, 'bne', '0x8'), Instruction(2, 'rets', ''),
                Instruction(8, 'jmp', '(a0)'), Instruction(10, 'rets', '')]
        result = walk(rows, 0)
        self.assertEqual(result['return_offsets'], [2])
        self.assertEqual(result['unresolved_offsets'], [8])
        self.assertNotIn(10, result['return_offsets'])
        self.assertTrue(walk(rows, 0, limit=1)['truncated'])
        loop = [Instruction(0, 'setlb', ''), Instruction(1, 'rets', '')]
        self.assertEqual(walk(loop, 0)['unresolved_offsets'], [0])
        self.assertEqual(walk(loop, 0)['return_offsets'], [])

    def test_linear_padding_and_text_never_become_code_claim(self):
        rows = [Instruction(0, 'break', 'PRIVATE CONTENT'),
                Instruction(1, '.byte', 'PRIVATE CONTENT'),
                Instruction(2, 'clr', 'PRIVATE CONTENT')]
        result = summarize(rows, 0, 3)
        self.assertEqual(result['data_directive_lines'], 1)
        self.assertEqual(result['break_lines'], 1)
        self.assertEqual(walk(rows, 0)['visited_instructions'], 0)
        self.assertNotIn('PRIVATE', json.dumps(result))
        self.assertIn('do not identify executable', result['note'])

    def test_external_error_does_not_disclose_private_transcript(self):
        with patch('tools.probe_oe_executable.subprocess.run', return_value=
                   subprocess.CompletedProcess([], 2, 'PRIVATE', 'PRIVATE')):
            with self.assertRaisesRegex(FormatError, 'no disassembly published') as caught:
                disassemble(Path('/unused'), b'xx', 0)
        self.assertNotIn('PRIVATE', str(caught.exception))


if __name__ == '__main__':
    unittest.main()

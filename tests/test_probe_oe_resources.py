"""Synthetic counterexamples: aligned assets/word hits do not prove an index."""
import unittest
from tools.probe_oe_resources import alignment, word_references, preceding_lengths, probe


class TestResourceProbes(unittest.TestCase):
    def test_sector_bias_and_gap_outlier(self):
        self.assertEqual(alignment([480, 992, 1505], 512), {
            'modulus': 512, 'residue_counts': {480: 2, 481: 1},
            'consecutive_gaps': 2, 'gaps_multiple_of_modulus': 1})
        self.assertEqual(alignment([], 16)['consecutive_gaps'], 0)
        with self.assertRaises(ValueError):
            alignment([0], 0)

    def test_word_endianness_alignment_bias_duplicates_and_overflow(self):
        data = (64).to_bytes(4, 'little') + (0x1040).to_bytes(4, 'big') + b'x' + (64).to_bytes(4, 'little')
        self.assertEqual(word_references(data, [64, 64]), {'aligned_word_hits': 1, 'distinct_targets': 1})
        self.assertEqual(word_references(data, [64], 0x1000, 'big'), {'aligned_word_hits': 1, 'distinct_targets': 1})
        self.assertEqual(word_references(data, [64], 0xffffffff)['aligned_word_hits'], 0)

    def test_preceding_numeric_value_requires_space_but_proves_no_record(self):
        data = bytearray(256)
        data[12:16] = (200).to_bytes(4, 'little')
        self.assertEqual(preceding_lengths(data, [2, 16, 250], 4, 'little'),
                         {'eligible': 2, 'bounded_numeric_candidates': 1})
        data[12:16] = (241).to_bytes(4, 'little')
        self.assertEqual(preceding_lengths(data, [16], 4, 'little')['bounded_numeric_candidates'], 0)

    def test_magic_only_is_explicitly_unvalidated_no_proprietary_dump(self):
        result = probe(b'\xff\xd8\xff' + b'\x00' * 29, 0)
        self.assertEqual(result['magic_counts_UNVALIDATED']['jpeg'], 1)
        self.assertIn('No index', result['note'])
        self.assertNotIn('raw', result)
        self.assertEqual(probe(b'', 0)['whole_payload_entropy_bits'], 0)
        with self.assertRaisesRegex(ValueError, 'too many'):
            probe(b'\xff\xd8\xff' * 1025, 0)


if __name__ == '__main__':
    unittest.main()

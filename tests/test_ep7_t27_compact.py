"""Fail-closed tests of own source-only study, no OEM inputs."""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from ep7_t27_compact_source import materialize, once, sources
from ep7_t27_size_study import fit


class CompactionGuards(unittest.TestCase):
    def test_anchor_changes_or_ambiguity_cannot_silently_transform_code(self):
        for text in ('missing', 'anchor anchor'):
            with self.assertRaisesRegex(ValueError, 'anchor changed'):
                once(text, 'anchor', 'replacement')

    def test_frozen_dependency_change_is_rejected(self):
        original = Path.read_bytes
        def changed(path):
            data = original(path)
            return data+b'changed' if path.name == 'hook.s' else data
        with patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(ValueError, 'dependency changed'):
                sources('dispatch')

    def test_no_materialized_artifacts_in_checkout(self):
        with self.assertRaisesRegex(ValueError, 'private /tmp'):
            materialize(Path(__file__).resolve().parents[1]/'must-not-exist', 'dispatch')

    def test_capacity_counts_fixed_code_and_mirror(self):
        self.assertEqual(fit(1276, 1554)['deficit'], 1294)
        self.assertFalse(fit(1276, 1554)['raw_fits'])
        # Even an exactly full raw span has not established alignment/placement.
        self.assertTrue(fit(1276, 260)['raw_fits'])
        self.assertFalse(fit(1276, 260)['placement_qualified'])


if __name__ == '__main__':
    unittest.main()

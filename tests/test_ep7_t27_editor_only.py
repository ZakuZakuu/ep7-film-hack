"""Fail-closed tests of our source split. No OEM bytes or external code."""
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from ep7_t27_editor_only_source import between, editor_only, materialize


class EditorOnlyGuards(unittest.TestCase):
    def test_changed_frozen_core_cannot_be_transformed(self):
        original = Path.read_bytes
        def changed(path):
            data = original(path)
            return data+b'changed' if path.name == 'hook.s' else data
        with patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(ValueError, 'dependency changed'):
                editor_only()

    def test_missing_or_duplicate_split_boundaries_stop(self):
        for text in ('begin only', 'begin begin end'):
            with self.assertRaisesRegex(ValueError, 'boundaries changed'):
                between(text, 'begin', 'end')

    def test_output_cannot_escape_private_tmp_through_symlink(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as tmp:
            root = Path(tmp)
            (root/'outside').symlink_to(Path(__file__).resolve().parents[1],
                                        target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'require /tmp'):
                materialize(root/'outside'/'must-not-exist')

    def test_existing_output_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as tmp:
            with self.assertRaisesRegex(ValueError, 'Fresh output'):
                materialize(tmp)

    def test_gui_namespace_collision_stops_before_materialization(self):
        import ep7_t27_editor_only_source as source
        original = source.sources
        def collision(variant):
            data = original(variant)
            data['editor.s'] += '\ncapability:\n'
            return data
        with patch.object(source, 'sources', collision):
            with self.assertRaisesRegex(ValueError, 'EP71 implementation survived'):
                source.editor_only()


if __name__ == '__main__':
    unittest.main()

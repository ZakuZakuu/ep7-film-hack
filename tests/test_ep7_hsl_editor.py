"""Synthetic fail-closed checks; never reads OEM input or invokes GNU."""
import argparse
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ep7_editor_verify',
                ROOT/'patches/hsl-editor/e-p7/build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class PrototypeGuards(unittest.TestCase):
    def test_normal_build_refused_before_input_or_tools(self):
        args = argparse.Namespace(verify_only=False, out=Path('/tmp/not-created'))
        with patch.object(build.subprocess, 'check_output',
                          side_effect=AssertionError('must not invoke tools')):
            with self.assertRaisesRegex(ValueError, 'placement is unqualified'):
                build.build(args)

    def test_verify_refuses_output_directory_before_input(self):
        args = argparse.Namespace(verify_only=True, out=Path('/tmp/not-created'))
        with self.assertRaisesRegex(ValueError, 'only --verify-only allowed'):
            build.build(args)

    def test_source_mismatch_stops_before_stock_read(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'synthetic.s').write_text('original synthetic source\n')
            (root/'patch.json').write_text(json.dumps({
                'source_sha256': {'synthetic.s': '0'*64}}))
            stock = Mock()
            stock.read_bytes.side_effect = AssertionError('must not read stock')
            args = argparse.Namespace(verify_only=True, out=None,
                                      upstream=root, stock=stock)
            with patch.object(build, 'HERE', root), patch.object(build, 'ROOT', root), \
                    patch.object(build.subprocess, 'check_output', return_value=''):
                with self.assertRaisesRegex(ValueError, 'Unqualified source change'):
                    build.build(args)
            stock.read_bytes.assert_not_called()


if __name__ == '__main__':
    unittest.main()

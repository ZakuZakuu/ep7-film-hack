"""Original fixtures for the adapter's complete-tree identity gate."""
import importlib.util
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    'tree_builder', Path(__file__).resolve().parents[1] / 'tools/build_upstream_mn103_sim.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class ArchiveIdentity(unittest.TestCase):
    def fixture(self, root):
        original = root / 'original'
        original.mkdir()
        (original / '.gitignore').write_text('*.a\n')
        (original / 'original-test.a').write_bytes(b'own synthetic ignored input\n')
        executable = original / 'configure'
        executable.write_text('#!/bin/sh\nexit 0\n')
        executable.chmod(0o755)
        archive = root / 'source.tgz'
        with tarfile.open(archive, 'w:gz') as stream:
            for path in original.iterdir():
                stream.add(path, arcname=path.name)
        subprocess.run(['git', 'init', '-q', '--template=', str(original)], check=True)
        subprocess.run(['git', 'add', '-f', '-A'], cwd=original, check=True)
        tree = builder.output(['git', 'write-tree'], original)
        return archive, tree

    def test_ignored_tracked_input_and_executable_mode_survive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive, tree = self.fixture(root)
            self.assertEqual(builder.archive_tree(archive, root / 'decoded'), tree)

    def test_additional_ignored_file_changes_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive, tree = self.fixture(root)
            destination = root / 'decoded'
            builder.archive_tree(archive, destination)
            (destination / 'unexpected.a').write_bytes(b'additional input')
            subprocess.run(['git', 'add', '-f', '-A'], cwd=destination, check=True)
            self.assertNotEqual(builder.output(['git', 'write-tree'], destination), tree)

    def test_executable_mode_changes_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive, tree = self.fixture(root)
            destination = root / 'decoded'
            builder.archive_tree(archive, destination)
            (destination / 'configure').chmod(0o644)
            subprocess.run(['git', '-c', 'core.filemode=true', 'add', '-f', '-A'],
                           cwd=destination, check=True)
            self.assertNotEqual(builder.output(['git', 'write-tree'], destination), tree)

    def test_archive_cannot_supply_git_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = root / 'payload'
            payload.write_bytes(b'own fixture')
            archive = root / 'bad.tgz'
            with tarfile.open(archive, 'w:gz') as stream:
                stream.add(payload, arcname='.git/config')
            with self.assertRaisesRegex(ValueError, 'Git metadata'):
                builder.archive_tree(archive, root / 'decoded')


if __name__ == '__main__':
    unittest.main()

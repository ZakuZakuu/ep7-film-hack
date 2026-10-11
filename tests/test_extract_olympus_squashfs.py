"""Synthetic OE carving guards and optional upstream LZO integration; NO OEM input."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.inspect_olympus_oe import CHUNK, FormatError, extract_squashfs, inspect
from test_inspect_olympus_oe import synthetic_block


def candidate_payload(offset=29, used=4097):
    # A synthetic SUPERBLOCK ONLY, not a filesystem or camera resource.
    sup = bytearray(96)
    sup[:4] = b"hsqs"
    struct.pack_into("<I", sup, 4, 3)
    struct.pack_into("<I", sup, 12, 131072)
    struct.pack_into("<H", sup, 20, 3)
    struct.pack_into("<HH", sup, 28, 4, 0)
    struct.pack_into("<Q", sup, 40, used)
    image = bytes(sup) + bytes((i % 256 for i in range(used - 96)))
    payload = b"\x55" * offset + image + b"\x77" * 31
    payload += bytes(-len(payload) % 16)
    return payload, image


class TestLocalSquashfsCarving(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.payload, self.image = candidate_payload()
        self.raw = synthetic_block(self.payload)
        self.source = self.root / "synthetic.bin"
        self.source.write_bytes(self.raw)
        self.output = self.root / "segment.squashfs"
        self.options = dict(expected_sha256=hashlib.sha256(self.raw).hexdigest(),
                            expected_size=len(self.raw), block_index=0,
                            payload_offset=29, allow_local_oem_output=True)

    def test_exact_unaligned_slice_private_mode_and_unchanged_input(self):
        info = extract_squashfs(self.source, self.output, **self.options)
        self.assertEqual(self.output.read_bytes(), self.image)
        self.assertEqual(info['sha256'], hashlib.sha256(self.image).hexdigest())
        self.assertEqual(info['bytes'], len(self.image))
        self.assertEqual(self.source.read_bytes(), self.raw)
        if os.name == 'posix':
            self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o600)

    def test_candidate_crosses_stream_chunk_boundary(self):
        offset = CHUNK - 47
        payload, image = candidate_payload(offset)
        raw = synthetic_block(payload)
        self.source.write_bytes(raw)
        self.options.update(expected_sha256=hashlib.sha256(raw).hexdigest(),
                            expected_size=len(raw), payload_offset=offset)
        info = extract_squashfs(self.source, self.output, **self.options)
        self.assertEqual(self.output.read_bytes(), image)
        self.assertEqual(info['decoded_payload_offset'], offset)

    def test_missing_optin_hash_size_index_and_offset_guards(self):
        changes = [dict(allow_local_oem_output=False), dict(expected_sha256='0' * 64),
                   dict(expected_sha256='not-a-hash'), dict(expected_size=len(self.raw) + 1),
                   dict(block_index=-1), dict(block_index=1), dict(payload_offset=-1),
                   dict(payload_offset=30)]
        for change in changes:
            with self.subTest(change=change):
                with self.assertRaises(FormatError):
                    extract_squashfs(self.source, self.output, **(self.options | change))
                self.assertFalse(self.output.exists())
                self.assertEqual(list(self.root.glob('.oe-extract-*')), [])

    def test_invalid_candidate_bounds_and_corrupt_other_block(self):
        bad = bytearray(self.payload)
        struct.pack_into('<Q', bad, 29 + 40, len(bad) + 1)
        for raw in [synthetic_block(bytes(bad)),
                    self.raw + synthetic_block(bytes(16))[:-1] + b'\x01']:
            with self.subTest(length=len(raw)):
                self.source.write_bytes(raw)
                options = self.options | dict(expected_sha256=hashlib.sha256(raw).hexdigest(),
                                              expected_size=len(raw))
                with self.assertRaises(FormatError):
                    extract_squashfs(self.source, self.output, **options)
                self.assertFalse(self.output.exists())

    def test_existing_output_and_symlink_are_not_overwritten(self):
        self.output.write_bytes(b"keep")
        with self.assertRaisesRegex(FormatError, 'refusing overwrite'):
            extract_squashfs(self.source, self.output, **self.options)
        self.assertEqual(self.output.read_bytes(), b"keep")
        self.output.unlink()
        self.output.symlink_to(self.root / 'absent')
        with self.assertRaises(FormatError):
            extract_squashfs(self.source, self.output, **self.options)
        self.assertTrue(self.output.is_symlink())

    def test_git_tracked_output_refused_but_private_samples_allowed(self):
        (self.root / '.git').mkdir()
        (self.root / '.git/HEAD').write_text('ref: refs/heads/synthetic\n')
        with self.assertRaisesRegex(FormatError, 'private_samples'):
            extract_squashfs(self.source, self.output, **self.options)
        private = self.root / 'private_samples'
        private.mkdir()
        extract_squashfs(self.source, private / 'segment.squashfs', **self.options)
        self.assertEqual((private / 'segment.squashfs').read_bytes(), self.image)

    def test_revalidation_failure_never_publishes_and_cleans_partial(self):
        from tools import inspect_olympus_oe as oe
        original = oe._inspect_stream
        with patch.object(oe, '_inspect_stream', side_effect=[inspect(self.source),
                          FormatError('input changed')]):
            with self.assertRaisesRegex(FormatError, 'input changed'):
                extract_squashfs(self.source, self.output, **self.options)
        self.assertIs(oe._inspect_stream, original)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob('.oe-extract-*')), [])

    def test_cli_requires_all_optins_and_emits_only_metadata(self):
        script = Path(__file__).resolve().parents[1] / 'tools/inspect_olympus_oe.py'
        common = [sys.executable, str(script), str(self.source), '--extract-squashfs', str(self.output)]
        denied = subprocess.run(common, capture_output=True, text=True)
        self.assertEqual(denied.returncode, 2)
        self.assertFalse(self.output.exists())
        command = common + ['--allow-local-oem-output', '--expected-sha256', self.options['expected_sha256'],
                            '--expected-size', str(len(self.raw)), '--block-index', '0',
                            '--payload-offset', '0x1d', '--json']
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        info = json.loads(result.stdout)
        self.assertEqual(info['sha256'], hashlib.sha256(self.image).hexdigest())
        self.assertNotIn('first_64_bytes_hex', info)
        self.assertEqual(self.source.read_bytes(), self.raw)


def upstream_tool(name):
    directory = os.environ.get('SQUASHFS_TOOLS_DIR')
    return str(Path(directory) / name) if directory else shutil.which(name)


@unittest.skipUnless(upstream_tool('mksquashfs') and upstream_tool('unsquashfs'),
                     'upstream squashfs-tools unavailable; E-P7 is never a test fixture')
class TestUpstreamLzoIntegration(unittest.TestCase):
    def test_upstream_generated_lzo_tree_carves_lists_and_selectively_extracts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tree = root / 'original'
            (tree / 'etc').mkdir(parents=True)
            (tree / 'usr/share').mkdir(parents=True)
            (tree / 'empty').mkdir()
            config = b'synthetic_setting=1\n'
            pattern = bytes(range(256)) * 2300
            (tree / 'etc/synthetic.conf').write_bytes(config)
            (tree / 'usr/share/pattern.dat').write_bytes(pattern)
            (tree / 'etc/config-link').symlink_to('synthetic.conf')
            fs = root / 'generated.squashfs'
            subprocess.run([upstream_tool('mksquashfs'), str(tree), str(fs), '-comp', 'lzo',
                            '-b', '131072', '-noappend', '-no-xattrs', '-processors', '1',
                            '-all-root', '-mkfs-time', '0'],
                           check=True, capture_output=True)
            image = fs.read_bytes()
            self.assertEqual(struct.unpack_from('<H', image, 20)[0], 3)
            used = struct.unpack_from('<Q', image, 40)[0]
            payload = b'\x55' * 29 + image + b'\x77' * 31
            payload += bytes(-len(payload) % 16)
            raw = synthetic_block(bytes(16)) + synthetic_block(payload, 1)
            source = root / 'synthetic-oe.bin'
            source.write_bytes(raw)
            carved = root / 'carved.squashfs'
            info = extract_squashfs(source, carved, expected_sha256=hashlib.sha256(raw).hexdigest(),
                                   expected_size=len(raw), block_index=1, payload_offset=29,
                                   allow_local_oem_output=True)
            self.assertEqual(info['bytes'], used)
            self.assertEqual(carved.read_bytes(), image[:used])
            summary = subprocess.run([upstream_tool('unsquashfs'), '-s', str(carved)],
                                     check=True, capture_output=True, text=True)
            self.assertIn('Compression lzo', summary.stdout)
            listing = subprocess.run([upstream_tool('unsquashfs'), '-ll', str(carved)],
                                     check=True, capture_output=True, text=True)
            self.assertIn('etc/synthetic.conf', listing.stdout)
            self.assertIn('usr/share/pattern.dat', listing.stdout)
            self.assertIn('etc/config-link', listing.stdout)
            dest = root / 'selective'
            subprocess.run([upstream_tool('unsquashfs'), '-strict-errors', '-no-xattrs',
                            '-no-progress', '-processors', '1', '-d', str(dest), str(carved),
                            'etc/synthetic.conf', 'usr/share/pattern.dat'],
                           check=True, capture_output=True)
            self.assertEqual((dest / 'etc/synthetic.conf').read_bytes(), config)
            self.assertEqual((dest / 'usr/share/pattern.dat').read_bytes(), pattern)
            self.assertFalse((dest / 'etc/config-link').exists())
            self.assertEqual(source.read_bytes(), raw)
            # A failed mature-tool validation is a stop, not a reason to ignore errors.
            broken = root / 'broken.squashfs'
            broken.write_bytes(carved.read_bytes()[:96])
            rejected = subprocess.run([upstream_tool('unsquashfs'), '-ll', str(broken)],
                                      capture_output=True)
            self.assertNotEqual(rejected.returncode, 0)


if __name__ == '__main__':
    unittest.main()

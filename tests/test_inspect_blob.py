"""Synthetic-file tests: no camera firmware required."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from tools.inspect_blob import inventory, shannon_entropy


class TestBlobInventory(unittest.TestCase):
    def test_empty_and_short_files(self):
        for payload in (b"", b"synthetic header\x00\xff"):
            with self.subTest(size=len(payload)), tempfile.TemporaryDirectory() as d:
                path = Path(d, "synthetic.dat")
                path.write_bytes(payload)
                info = inventory(path)
                self.assertEqual(info["sha256"], hashlib.sha256(payload).hexdigest())
                self.assertEqual(info["bytes"], len(payload))
                self.assertEqual(info["first_64_bytes_hex"], payload.hex())
                for sample in info["entropy_samples"].values():
                    self.assertEqual(sample["offset"], 0)
                    self.assertEqual(sample["sample_size"], len(payload))
                self.assertEqual(path.read_bytes(), payload)

    def test_cli_hashes_all_chunks_without_changing_input(self):
        # Cross the initial 4 KiB read and several 1 MiB reads, with a unique tail.
        payload = bytes(range(256)) * 12288 + b"distinct synthetic tail"
        script = Path(__file__).resolve().parents[1] / "tools" / "inspect_blob.py"
        with tempfile.TemporaryDirectory() as d:
            path = Path(d, "synthetic.dat")
            path.write_bytes(payload)
            result = subprocess.run(
                [sys.executable, str(script), str(path), "--json"],
                capture_output=True, text=True, check=True,
            )
            info = json.loads(result.stdout)
            self.assertEqual(info["bytes"], len(payload))
            self.assertEqual(info["sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual(path.read_bytes(), payload)
            self.assertEqual(info["first_64_bytes_hex"], payload[:64].hex())
            self.assertEqual(info["entropy_samples"]["start"]["entropy_bits_per_byte"], 8.0)
            self.assertEqual(info["entropy_samples"]["middle"]["offset"], len(payload) // 2 - 2048)
            self.assertEqual(info["entropy_samples"]["end"]["offset"], len(payload) - 4096)
            for sample in info["entropy_samples"].values():
                self.assertEqual(sample["sample_size"], 4096)

    def test_empty_entropy(self):
        self.assertEqual(shannon_entropy(b""), 0.0)
        self.assertEqual(shannon_entropy(b"aaaa"), 0.0)

    def test_balanced_bits(self):
        self.assertAlmostEqual(shannon_entropy(b"\x00\xff" * 100), 1.0)

    def test_preserves_input_and_hash(self):
        payload = bytes(range(256)) * 28
        with tempfile.TemporaryDirectory() as d:
            path = Path(d, "synthetic.dat")
            path.write_bytes(payload)
            info = inventory(path)
            self.assertEqual(info["bytes"], len(payload))
            self.assertEqual(info["sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual(path.read_bytes(), payload)
            self.assertEqual(info["entropy_samples"]["start"]["sample_size"], 4096)


if __name__ == "__main__":
    unittest.main()

"""Synthetic-file tests: no camera firmware required."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from tools.inspect_blob import inventory, shannon_entropy


class TestBlobInventory(unittest.TestCase):
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

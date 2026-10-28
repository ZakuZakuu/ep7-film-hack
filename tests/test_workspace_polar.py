"""Synthetic fixed-point kernel tests; no vendor bytes or installed DLL required."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from tools.recipe_studio.workspace_polar import PolarKernel


class PolarTests(unittest.TestCase):
    def setUp(self):
        self.kernel = PolarKernel([0]*64, [0]*64, [0]*32)

    def test_axes_and_octants_are_independent_of_luts(self):
        cases = {(0,0):(0,0), (100,0):(0,100), (0,100):(8192,100),
                 (-100,0):(16384,100), (0,-100):(24576,100),
                 (100,100):(4096,141), (-100,100):(12288,141),
                 (-100,-100):(20480,141), (100,-100):(28672,141),
                 (-512,-512):(20480,724)}
        for inputs, expected in cases.items():
            self.assertEqual(self.kernel.convert(*inputs), expected)

    def test_input_contract(self):
        for inputs in [(512,0),(-513,0),(0,512),(True,1),(1.0,1)]:
            with self.assertRaises(ValueError):
                self.kernel.convert(*inputs)
        with self.assertRaises(ValueError):
            PolarKernel([],[],[])

    def test_file_identity_checked_before_reading_offsets(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"owned.dat"
            path.write_bytes(b"owned synthetic bytes")
            with self.assertRaises(ValueError):
                PolarKernel.from_dll(path, "0"*64)


if __name__ == "__main__":
    unittest.main()

"""Owned synthetic buffers only; no installed vendor software required."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools.recipe_studio.workspace_probe import locate_windows, private_report_path


class LocatorTests(unittest.TestCase):
    def test_all_offsets_and_boundaries(self):
        h = hashlib.sha256(b"aba").hexdigest()
        self.assertEqual(locate_windows(b"ababa", 3, h), [0, 2])
        self.assertEqual(locate_windows(b"aba", 3, h), [0])
        self.assertEqual(locate_windows(b"ab", 3, h), [])
        self.assertEqual(locate_windows(b"abb", 3, h), [])

    def test_reject_bad_inputs(self):
        for size in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                locate_windows(b"abc", size, "0" * 64)
        for digest in ("0" * 63, "A" * 64, "z" * 64):
            with self.assertRaises(ValueError):
                locate_windows(b"abc", 1, digest)

    def test_private_report_boundary_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            allowed = Path(tmp) / "report.json"
            self.assertEqual(private_report_path(allowed), allowed.resolve())
            repo = Path(__file__).resolve().parents[1]
            with self.assertRaises(ValueError):
                private_report_path(repo / "inventory.json")
            # Even a checkout located inside /tmp may not hold private output.
            with patch("tempfile.gettempdir", return_value=str(repo.parent)):
                with self.assertRaises(ValueError):
                    private_report_path(repo / "inventory.json")
            link = Path(tmp) / "escape"
            try:
                link.symlink_to(repo, target_is_directory=True)
            except (OSError, NotImplementedError):
                return
            with self.assertRaises(ValueError):
                private_report_path(link / "inventory.json")


try:
    import numpy as np
    import tifffile
except ImportError:
    np = tifffile = None


@unittest.skipIf(np is None or tifffile is None, "optional research dependencies absent")
class ComparisonTests(unittest.TestCase):
    def test_known_error_preserves_16bit_precision(self):
        from tools.recipe_studio.workspace_compare import pixel_error
        b = np.full((1, 2, 3), 30000, dtype=np.uint16)
        a = b.copy()
        a[0, 0] += np.array([1, 2, 3], dtype=np.uint16)
        report = pixel_error(a, b)
        self.assertEqual(report["max_abs_lsb"], 3)
        self.assertEqual(report["mae_lsb"], 1)
        self.assertEqual(report["per_channel_bias_lsb"], [.5, 1, 1.5])
        self.assertEqual(report["identical_pixel_fraction"], .5)
        self.assertAlmostEqual(report["rmse_lsb"], (14 / 6) ** .5)
        self.assertEqual(pixel_error(b, b)["max_abs_lsb"], 0)
        self.assertEqual(pixel_error(b, a)["per_channel_bias_lsb"], [-.5, -1, -1.5])

    def test_no_resizing_or_depth_conversion(self):
        from tools.recipe_studio.workspace_compare import pixel_error
        b = np.zeros((2, 2, 3), dtype=np.uint16)
        for a in (b[:1], b.astype(np.uint8), b.astype(float), b[..., :2], b[:0]):
            with self.assertRaises(ValueError):
                pixel_error(a, b)

    def test_tiff_metadata_guards_and_roundtrip(self):
        from tools.recipe_studio.workspace_compare import compare_files
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.tif", Path(tmp) / "b.tif"
            rgb = np.full((2, 3, 3), 32001, dtype=np.uint16)
            # Test-only opaque ICC marker; no vendor profile or table embedded.
            def save(path, profile, **kw):
                tags = [(34675, "B", len(profile), profile, False)] if profile else []
                tifffile.imwrite(path, rgb, photometric="rgb", metadata=None, extratags=tags, **kw)
            save(a, b"owned-profile")
            save(b, b"owned-profile")
            self.assertEqual(compare_files(a, b)["max_abs_lsb"], 0)
            for profile in (b"different-profile", None):
                save(b, profile)
                with self.assertRaises(ValueError):
                    compare_files(a, b)
            tifffile.imwrite(b, np.zeros((2, 3), dtype=np.uint16), metadata=None)
            with self.assertRaises(ValueError):
                compare_files(a, b)


try:
    import pefile
    import capstone
except ImportError:
    pefile = capstone = None


@unittest.skipIf(pefile is None or capstone is None, "optional analysis dependencies absent")
class PEReferenceTests(unittest.TestCase):
    def test_rip_reference_after_undecodable_gap(self):
        import struct
        from tools.recipe_studio.workspace_probe import pe_evidence
        # Construct an owned minimal PE64 with two unwind ranges. Linear
        # disassembly would stop in the gap, before the second function.
        data = bytearray(0x800)
        data[:2] = b"MZ"
        struct.pack_into("<I", data, 0x3c, 0x80)
        data[0x80:0x84] = b"PE\0\0"
        struct.pack_into("<HHIIIHH", data, 0x84, 0x8664, 3, 0, 0, 0, 0xf0, 0x2022)
        opt = 0x98
        struct.pack_into("<H", data, opt, 0x20b)
        struct.pack_into("<Q", data, opt + 24, 0x180000000)
        struct.pack_into("<II", data, opt + 32, 0x1000, 0x200)
        struct.pack_into("<II", data, opt + 56, 0x4000, 0x200)
        struct.pack_into("<I", data, opt + 108, 16)
        struct.pack_into("<II", data, opt + 112 + 3 * 8, 0x3000, 24)
        for i, (name, rva, raw, flags) in enumerate([
                (b".text", 0x1000, 0x200, 0x60000020),
                (b".rdata", 0x2000, 0x400, 0x40000040),
                (b".pdata", 0x3000, 0x600, 0x40000040)]):
            start = opt + 0xf0 + 40 * i
            data[start:start + len(name)] = name
            struct.pack_into("<IIII", data, start + 8, 0x200, rva, 0x200, raw)
            struct.pack_into("<I", data, start + 36, flags)
        data[0x200:0x220] = b"\xc3" + b"\x0f" * 31
        data[0x220:0x228] = b"\x48\x8d\x15" + struct.pack("<i", 0x2000 - 0x1027) + b"\xc3"
        data[0x400:0x403] = b"xyz"
        data[0x410:0x414] = bytes([1, 0, 0, 0])
        struct.pack_into("<IIIIII", data, 0x600, 0x1000, 0x1001, 0x2010, 0x1020, 0x1028, 0x2010)
        result = pe_evidence(bytes(data), 0x400, 3)
        self.assertEqual(result["table_rva"], 0x2000)
        self.assertEqual(result["direct_references"], [
            {"instruction_rva": 0x1020, "function_rva": 0x1020,
             "function_end_rva": 0x1028, "table_relative_offset": 0}])
        struct.pack_into("<H", data, 0x84, 0x14c)
        with self.assertRaises(ValueError):
            pe_evidence(bytes(data), 0x400, 3)


if __name__ == "__main__":
    unittest.main()

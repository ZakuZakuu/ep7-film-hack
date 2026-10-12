"""100% synthetic tests: no Olympus firmware or device required."""
import hashlib
import struct
import tempfile
import unittest
from pathlib import Path
from tools.inspect_olympus_oe import (PERMUTATION, INVERT, FormatError,
                                      decode_chunk, inspect, sum_u32_le)


def encode(plain: bytes) -> bytes:
    inverted = plain.translate(INVERT)
    out = bytearray(len(inverted))
    for dest, src in enumerate(PERMUTATION):
        out[src::16] = inverted[dest::16]
    return bytes(out)


def synthetic_block(payload: bytes, block_no: int = 0) -> bytes:
    assert len(payload) % 16 == 0
    h = bytearray(32)
    h[:4] = b"OE\x14\x20"
    struct.pack_into('<I', h, 8, 0x40000000)
    struct.pack_into('<I', h, 12, len(payload))
    h[16:18] = b'\x00\x11'
    h[20:22] = bytes([block_no, 1])
    trail = bytes(h[:28])
    checksum = (-sum_u32_le(bytes(h) + payload + trail)) & 0xFFFFFFFF
    return bytes(h) + encode(payload) + trail + struct.pack('<I', checksum)


class TestOlmyContainer(unittest.TestCase):
    def test_additive_sum_does_not_establish_authentication(self):
        # Original integer arrays only: no OE image, patch or checksum repair.
        first=struct.pack('<II',100,200)
        second=struct.pack('<II',150,150)
        self.assertNotEqual(first,second)
        self.assertEqual(sum_u32_le(first),300)
        self.assertEqual(sum_u32_le(first),sum_u32_le(second))
        self.assertNotEqual(hashlib.sha256(first).digest(),hashlib.sha256(second).digest())

    def test_fails_on_empty_container(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td, 'empty.bin')
            p.write_bytes(b'')
            with self.assertRaisesRegex(FormatError, 'empty OE container'):
                inspect(p)

    def test_permutation_roundtrip(self):
        plain = bytes(range(256))
        self.assertEqual(decode_chunk(encode(plain)), plain)

    def test_synthetic_multiblock(self):
        src = synthetic_block(bytes(range(256)) * 3, 0) + synthetic_block(bytes(16), 1)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td, 'dummy.bin')
            p.write_bytes(src)
            info = inspect(p)
            self.assertEqual(info['block_count'], 2)
            self.assertEqual(info['sha256'], hashlib.sha256(src).hexdigest())
            self.assertEqual(info['blocks'][0]['checksum_residual'], '0x00000000')
            self.assertEqual(p.read_bytes(), src)

    def test_fails_on_mutated_payload(self):
        data = bytearray(synthetic_block(bytes(range(256)) * 3))
        data[33] ^= 1
        with tempfile.TemporaryDirectory() as td:
            p = Path(td, 'corrupt.bin');p.write_bytes(data)
            with self.assertRaisesRegex(FormatError, 'checksum failed'):
                inspect(p)

    def test_fails_on_truncation(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td, 'short.bin');p.write_bytes(synthetic_block(bytes(64))[:-10])
            with self.assertRaisesRegex(FormatError, 'truncated block'):
                inspect(p)

    def test_fails_on_bad_trailer(self):
        data = bytearray(synthetic_block(bytes(64)));data[-6] ^= 1
        with tempfile.TemporaryDirectory() as td:
            p = Path(td, 'bad_tail.bin');p.write_bytes(data)
            with self.assertRaisesRegex(FormatError, 'header/trailer mismatch'):
                inspect(p)


if __name__ == '__main__':
    unittest.main()

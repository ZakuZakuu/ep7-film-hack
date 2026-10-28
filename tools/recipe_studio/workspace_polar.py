"""Exact isolated Workspace signed-chroma polar kernel; not an RGB model.

Original implementation from local Acacia 2.3.0.22 observations. Vendor LUTs
are read from the owner's DLL at runtime, never embedded or exported.
"""
import hashlib
from pathlib import Path
import struct


class PolarKernel:
    def __init__(self, reciprocal, angle, radius):
        if tuple(map(len, (reciprocal, angle, radius))) != (64, 64, 32):
            raise ValueError("expected three packed LUTs with 64/64/32 words")
        self.reciprocal, self.angle, self.radius = reciprocal, angle, radius

    @classmethod
    def from_dll(cls, path, expected_sha256):
        data = Path(path).read_bytes()
        if len(expected_sha256) != 64 or hashlib.sha256(data).hexdigest() != expected_sha256:
            raise ValueError("DLL does not match the private qualified SHA-256")
        pe = struct.unpack_from("<I", data, 0x3c)[0]
        if data[:2] != b"MZ" or data[pe:pe+4] != b"PE\0\0":
            raise ValueError("expected PE image")
        machine, count = struct.unpack_from("<HH", data, pe+4)
        optional_size = struct.unpack_from("<H", data, pe+20)[0]
        if machine != 0x8664:
            raise ValueError("qualified Acacia image must be x64")
        sections = pe+24+optional_size
        def words(rva, count_words):
            for i in range(count):
                _, start, size, raw = struct.unpack_from("<IIII", data, sections+40*i+8)
                offset = rva-start
                if 0 <= offset and offset+count_words*4 <= size:
                    return struct.unpack_from("<"+"I"*count_words, data, raw+offset)
            raise ValueError("LUT range outside file-backed PE sections")
        return cls(words(0xd7770, 64), words(0xca280, 64), words(0xc2140, 32))

    def convert(self, x, y):
        if type(x) is not int or type(y) is not int or not (-512 <= x <= 511 and -512 <= y <= 511):
            raise ValueError("signed chroma inputs must be integers in -512..511")
        ax, ay = abs(x), abs(y)
        largest, smallest = max(ax, ay), min(ax, ay)
        if not smallest or ax == ay:
            phase = 8192 if not ax and ay else 4096 if ax == ay and ax else 0
            magnitude = (largest*1448+512) >> 10 if ax == ay else largest
        else:
            shift, mantissa = (-1, 256) if largest == 512 else (0, largest)
            while not mantissa & 256 and shift < 8:
                mantissa <<= 1
                shift += 1
            word = self.reciprocal[(mantissa >> 2) & 63]
            base = word >> 8
            base = base+8192 if base & 8191 else 16384
            inverse = max(0, (base*4+4-(word & 255)*(mantissa & 3)) >> 3)
            ratio = min(4095, ((1 << (8-shift))+inverse*smallest) >> (9-shift))
            word = self.angle[(ratio >> 6) & 63]
            octant = min(4095, ((word & 511)*(ratio & 63)+((word >> 9)+2)*64) >> 8)
            word = self.radius[(octant >> 7) & 31]
            gain = min(1448, ((word & 255)*(octant & 127)+((word >> 8)+4098)*128) >> 9)
            magnitude = (gain*largest+512) >> 10
            phase = octant if ax > ay else 8192-octant
        if x < 0:
            phase = 16384-phase
        if y < 0:
            phase = 32768-phase
        return phase % 32768, magnitude

"""Tests for our proposed cell codec, never a camera/firmware fixture."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ep7_t25_storage_probe import encode, decode, MARK


class CandidateCellCodec(unittest.TestCase):
    def test_all_225_pairs_roundtrip(self):
        values=set()
        for h in range(-7,8):
            for l in range(-7,8):
                word=encode(h,l)
                self.assertEqual(decode(word),(h,l))
                values.add(word)
        self.assertEqual(len(values),225)

    def test_unknown_default_invalid_nibbles_and_corruption_are_neutral(self):
        for value in [None,True,-1,0,0xffffffff,*range(-7,8),1<<32]:
            self.assertEqual(decode(value),(0,0))
        for nibble in (0x08,0x80,0x88,0x78,0x87):
            word=MARK|((nibble^255)<<8)|nibble
            self.assertEqual(decode(word),(0,0))
        word=encode(3,-5)
        for bit in range(32):
            self.assertEqual(decode(word^(1<<bit)),(0,0))

    def test_encoder_rejects_non_integer_or_out_of_range_axes(self):
        for value in (-8,8,True,1.5,'1',None):
            with self.assertRaises(ValueError):encode(value,0)
            with self.assertRaises(ValueError):encode(0,value)


if __name__=='__main__':unittest.main()

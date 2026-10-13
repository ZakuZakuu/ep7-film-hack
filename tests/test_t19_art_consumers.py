import unittest

from tools.inspect_olympus_oe import FormatError
from tools.probe_oe_executable import Instruction as I
from tools.t19_art_consumers import adjacent_transfer, descriptor, scalar_format


class ArtConsumerContracts(unittest.TestCase):
    def test_descriptor_identity_bounds_and_wrong_stride(self):
        # Original toy descriptors, deliberately unsorted and distinct neighbors.
        data = bytearray(60)
        for pos, key in [(0, 873), (20, 872), (40, 111)]:
            data[pos:pos+2] = key.to_bytes(2, 'little')
        self.assertEqual(descriptor(data, 0, 3, 20, 872), 20)
        self.assertIsNone(descriptor(data, 0, 3, 20, 362))
        for args in [(0, 3, 24), (1, 3, 20), (-1, 3, 20), (0, 4, 20)]:
            with self.assertRaises(FormatError):
                descriptor(data, *args, 872)
        data[40:42] = (872).to_bytes(2, 'little')
        with self.assertRaises(FormatError):
            descriptor(data, 0, 3, 20, 872)

    def test_sign_and_width_are_distinct_from_field_names(self):
        self.assertEqual(scalar_format(0xf5d1), {'bytes': 1, 'signed_read': True})
        self.assertEqual(scalar_format(0x44c1), {'bytes': 1, 'signed_read': False})
        self.assertEqual(scalar_format(0x102), {'bytes': 2, 'signed_read': True})
        self.assertEqual(scalar_format(0x104), {'bytes': 4, 'signed_read': False})
        for value in (0, 3, 0x10001, -1):
            with self.assertRaises(FormatError):
                scalar_format(value)

    def test_transfer_rejects_width_base_clobber_and_call(self):
        rows = [I(10, 'movbu', '(24785,a1),d0'), I(14, 'movbu', 'd0,(12,a2)')]
        self.assertEqual(adjacent_transfer(rows, 'a1', 24785, 'a2', 12, 1), ['0xa', '0xe'])
        for candidate, args in [
            (rows, ('a1', 24785, 'a2', 12, 4)),
            (rows, ('a0', 24785, 'a2', 12, 1)),
            (rows, ('a1', 24784, 'a2', 12, 1)),
            (rows, ('a1', 24785, 'a3', 12, 1)),
            ([rows[0], I(14, 'movbu', 'd1,(12,a2)')], ('a1', 24785, 'a2', 12, 1)),
            ([rows[0], I(12, 'clr', 'd0'), rows[1]], ('a1', 24785, 'a2', 12, 1)),
            ([rows[0], I(12, 'calls', '(a3)'), rows[1]], ('a1', 24785, 'a2', 12, 1)),
        ]:
            with self.assertRaises(FormatError):
                adjacent_transfer(candidate, *args)

    def test_same_displacement_on_other_owner_does_not_join(self):
        rows = [I(10, 'movbu', '(12,a1),d0'), I(12, 'movbu', 'd0,(20,a2)')]
        self.assertEqual(adjacent_transfer(rows, 'a1', 12, 'a2', 20, 1), ['0xa', '0xc'])
        with self.assertRaises(FormatError):
            adjacent_transfer(rows, 'a1', 12, 'a2', 20, 4)
        # The old effects word+20 and the bracket byte+12 cannot be aliased by offsets.

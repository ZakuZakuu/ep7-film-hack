import unittest
import os
from pathlib import Path

from tools.inspect_olympus_oe import FormatError
from tools.probe_oe_executable import Instruction as I
from tools.t19_art_consumers import adjacent_transfer, descriptor, scalar_format
from tools.t19_effect_handoff import summarize_flag_block
from tools.t19_reference_probe import bounded_hits, patterns


class ArtConsumerContracts(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('EP7_AS') and os.environ.get('EP7_OBJDUMP'), 'GNU required')
    def test_original_gnu_references_cover_synthesized_and_displaced_forms(self):
        result = patterns(Path(os.environ['EP7_AS']), Path(os.environ['EP7_OBJDUMP']))
        self.assertEqual(len(result), 112)
        names = {name for name, _ in result}
        self.assertTrue({'mov 24785,a1', 'mov 62929,d0', 'mov -2607,d0',
                         'movbu (24785,a1),d0', 'movbu d0,(24785,a3)'} <= names)
        encodings = dict(result)
        self.assertNotEqual(encodings['mov 24785,a1'], encodings['mov 24785,d1'])
        self.assertNotEqual(encodings['mov 62929,d0'], encodings['mov -2607,d0'])
    def test_flag_summary_follows_direct_join_but_rejects_opaque_flow(self):
        rows = [I(0, 'mov', '(a2),d0'), I(2, 'and', '-769,d0'),
                I(5, 'or', '256,d0'), I(8, 'bra', '0x20'),
                I(32, 'mov', 'd0,(a2)'), I(34, 'bra', '0x40')]
        result = summarize_flag_block(rows, 0, 64)
        self.assertEqual(result, {'keep_mask':'0xfffffcff','set_mask':'0x100'})
        # Direct jump to a shared store is supported; skipping it is not.
        for changed in [rows[:3]+[I(8,'bra','0x40')],
                        rows[:2]+[I(5,'calls','(a0)')]+rows[3:],
                        rows[:4]+[I(32,'movhu','d0,(a2)')]+rows[5:],
                        rows[:4]+[I(32,'mov','d0,(a3)')]+rows[5:],
                        [I(0,'bra','0x0')], [I(0,'bne','0x40')]]:
            with self.assertRaises(FormatError):
                summarize_flag_block(changed, 0, 64)
        self.assertEqual(summarize_flag_block([I(0,'bra','0x40')],0,64),
                         {'keep_mask':'0xffffffff','set_mask':'0x0'})

    def test_reference_bounds_do_not_turn_data_into_code(self):
        # Entirely original text bytes; a hit is deliberately not a typed edge.
        self.assertEqual(bounded_hits(b'abab',b'ab',2),[0,2])
        with self.assertRaises(FormatError):
            bounded_hits(b'abab',b'ab',1)
        with self.assertRaises(FormatError):
            bounded_hits(b'ab',b'',1)
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

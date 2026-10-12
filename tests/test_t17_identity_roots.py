import unittest
from tools.t17_identity_roots import qualify
from tools.probe_oe_executable import Instruction


class IdentityTests(unittest.TestCase):
    def test_literal_and_consumer_must_converge(self):
        r=[Instruction(20,'mov','1122867,d0'),Instruction(26,'call','0x75068f,[],4')]
        self.assertEqual(qualify(r,0x112233)['literal'],'0x14')
        for changed in [[],[r[0]],
                        [Instruction(20,'mov','1122867,d1'),r[1]],
                        [r[0],Instruction(26,'call','0x750690,[],4')],
                        [r[0],Instruction(26,'clr','d0'),r[1]]]:
            self.assertIsNone(qualify(changed,0x112233))
        self.assertIsNone(qualify(r,0x112234))

    def test_embedded_identity_is_not_an_accepted_consumer(self):
        self.assertIsNone(qualify([Instruction(0,'.byte','1,2,3'),
                                  Instruction(3,'ret','[],0')],0x112233))

import os
from pathlib import Path
import unittest
from tools.mn103_analysis import effect, prove_copy_loop, SemanticGap
from tools.probe_oe_executable import Instruction
from tools.ep7_re_workbench import cfg
from tools.check_mn103_sim import check as check_simulator


def synthetic_loop(counter='-8'):
    # Original symbolic stand-in; GNU-assembled fixture separately tests execution.
    return [Instruction(0,'mov',counter+',d3'),Instruction(2,'setlb',''),
            Instruction(3,'mov','(a0),d2'),Instruction(4,'inc4','a0'),
            Instruction(5,'mov','d2,(a1)'),Instruction(6,'inc4','a1'),
            Instruction(7,'inc','d3'),Instruction(8,'lne',''),
            Instruction(9,'rets','')]


class AnalysisTests(unittest.TestCase):
    def test_exact_loop_exit_state_and_cfg_gain(self):
        rows = synthetic_loop()
        proof = prove_copy_loop(rows,2)
        self.assertEqual(proof['iterations'],8)
        self.assertEqual(proof['bytes_transferred'],32)
        self.assertEqual(proof['lar'],7)
        self.assertEqual(proof['exit'],9)
        self.assertEqual(proof['counter_exit'],0)
        self.assertEqual(proof['exit_condition_codes'],dict(Z=1,N=0,V=0,C=1))
        self.assertFalse(cfg(rows,0)['returns'])
        gained = cfg(rows,0,[proof])
        self.assertEqual(gained['returns'],[9])
        self.assertFalse(gained['stops'])
        self.assertTrue(any(e['kind']=='cached_loop' for e in gained['edges']))

    def test_uncertified_loop_still_stops(self):
        self.assertTrue(cfg(synthetic_loop(),0)['stops'])
        for count in ('0','1','-4097'):
            with self.assertRaises(SemanticGap):
                prove_copy_loop(synthetic_loop(count),2)

    def test_clobbered_counter_or_pointer_not_certified(self):
        for index,replacement in [(4,Instruction(5,'mov','d2,(a0)')),
                                  (6,Instruction(7,'inc','d0')),
                                  (2,Instruction(3,'mov','(a0),d3')),
                                  (3,Instruction(4,'inc','a0'))]:
            rows = synthetic_loop();rows[index]=replacement
            with self.assertRaises(SemanticGap):
                prove_copy_loop(rows,2)

    def test_prefix_crossing_and_external_entry_rejected(self):
        rows = synthetic_loop();rows[3]=Instruction(5,'inc4','a0')
        with self.assertRaises(SemanticGap):
            prove_copy_loop(rows,2)
        rows = synthetic_loop()+[Instruction(11,'jmp','0x8')]
        with self.assertRaises(SemanticGap):
            prove_copy_loop(rows,2)

    def test_call_frame_is_not_a_push_pop_guess(self):
        e = effect(Instruction(0x10,'call','0x80,[d2,d3,a2,a3],44'),5)
        self.assertEqual(e['sp_delta'],-44)
        self.assertEqual(e['link_offset'],5)
        self.assertEqual([w['offset'] for w in e['memory_writes']],[0,-4,-8,-12,-16])
        self.assertEqual(e['memory_writes'][0]['value'],'next_pc')
        self.assertEqual(effect(Instruction(0,'call','0x10000,[],0'),7)['link_offset'],7)

    def test_indirect_calls_read_register_not_pointed_memory(self):
        e = effect(Instruction(0,'calls','(a0)'),2)
        self.assertEqual(e['target'],{'register':'a0'})
        self.assertEqual(e['sp_delta'],0)
        self.assertNotIn('sp',e['register_writes'])
        self.assertEqual(effect(Instruction(0,'rets',''),2)['sp_delta'],0)
        self.assertEqual(effect(Instruction(0,'ret','[],44'),3)['sp_delta'],44)
        self.assertEqual(effect(Instruction(0,'retf','[],4'),3)['target'],{'register':'mdr_before_restore'})

    def test_widths_extensions_and_preserved_move_flags(self):
        for m,width in [('mov',4),('movbu',1),('movhu',2)]:
            e = effect(Instruction(0,m,'(2,a0),d0'),3)
            self.assertEqual(e['width'],width)
            self.assertEqual(e['flags'],'preserved')
        self.assertEqual(effect(Instruction(0,'movbu','d0,(2,sp)'),3)['stored_low_bits'],8)
        self.assertEqual(effect(Instruction(0,'extb','d0'),1)['extension'],'sign')
        self.assertEqual(effect(Instruction(0,'exthu','d0'),1)['source_bits'],16)

    def test_conditions_and_unsupported_groups_do_not_guess(self):
        self.assertEqual(effect(Instruction(10,'bcs','0x30'),2)['predicate'],'C=1')
        self.assertEqual(effect(Instruction(10,'bne','0x30'),2)['fallthrough'],12)
        self.assertEqual(effect(Instruction(0,'call','0x40,[ex0],8'),5)['status'],'unmodeled')
        self.assertEqual(effect(Instruction(0,'udfu01','6,d0'),3)['status'],'unmodeled')
        self.assertEqual(effect(Instruction(0,'calls','(a0)'),4)['status'],'unmodeled')

    def test_only_validated_movm_save_form_is_admitted(self):
        e = effect(Instruction(0,'movm','[a2],(sp)'),2)
        self.assertEqual(e['sp_delta'],-4)
        self.assertEqual(e['memory_writes'][0]['value'],'a2')
        self.assertEqual(e['flags'],'preserved')
        for o in ('[other],(sp)','[ex0],(sp)','(sp),[a2]','[a3],(sp)'):
            self.assertEqual(effect(Instruction(0,'movm',o),2)['status'],'unmodeled')
        self.assertEqual(effect(Instruction(0,'movm','[a2],(sp)'),3)['status'],'unmodeled')

    @unittest.skipUnless(os.environ.get('EP7_SIM'),'GNU simulator required; run Cloud setup')
    def test_external_simulator_original_fixtures_and_countercontrols(self):
        root = Path(os.environ['EP7_SIM']).parents[3]
        results = check_simulator(root)
        self.assertEqual(results['fixture_results']['mn103_semantics']['am33'],0)
        self.assertEqual(results['fixture_results']['mn103_long_calls']['mn10300'],0)
        self.assertEqual(results['fixture_results']['mn103_lir_control']['am33-2'],9)
        self.assertEqual(results['fixture_results']['incorrect_pointer_expectation'],73)
        self.assertEqual(results['fixture_results']['mn103_udf_provider']['am33'],91)
        self.assertIn('UNADMITTED',results['udf_ep7_admission'])
        self.assertEqual(results['fixture_results']['mn103_entry_pair']['am33'],0)
        self.assertEqual(results['fixture_results']['mn103_division']['am33'],0)
        self.assertEqual(results['fixture_results']['incorrect_division_expectation'],73)
        self.assertEqual(results['fixture_results']['incorrect_signed_division_expectation'],73)
        self.assertEqual(results['fixture_results']['incorrect_full_entry_expectation'],73)
        self.assertEqual(effect(Instruction(0,'udfu01','6,d0'),3)['status'],'unmodeled')
        self.assertFalse(results['oem_execution'])


if __name__ == '__main__':
    unittest.main()

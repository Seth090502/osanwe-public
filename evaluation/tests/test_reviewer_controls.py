import copy
import unittest
from test_protocol import module

controls=module('reviewer_controls')
schema=module('reviewer_schema')


class ReviewerControls(unittest.TestCase):
    def setUp(self):self.control=controls.build()

    def perfect(self):
        return {'reviews':[{'report_id':rid,'verdict':'accept' if truth['acceptable'] else 'reject',
                            'findings':[] if truth['acceptable'] else [{'code':truth['required_code'],'severity':'major'}]}
                           for rid,truth in self.control['oracle'].items()]}

    def test_correct_controls_and_planted_defects_both_required(self):
        self.assertTrue(controls.score(self.control,self.perfect())['controls_pass'])
        all_accept=self.perfect()
        for row in all_accept['reviews']:row.update(verdict='accept',findings=[])
        result=controls.score(self.control,all_accept)
        self.assertFalse(result['controls_pass']);self.assertEqual(result['correct_controls_accepted'],24);self.assertEqual(result['planted_defects_found'],0)

    def test_blanket_criticism_cannot_manufacture_a_pass(self):
        verdict=self.perfect()
        for row in verdict['reviews']:row.update(verdict='reject',findings=[{'code':'wrong_financial_identity','severity':'major'}])
        result=controls.score(self.control,verdict)
        self.assertFalse(result['controls_pass']);self.assertEqual(result['correct_controls_accepted'],0)

    def test_missing_duplicate_and_malformed_judgments_fail(self):
        v=self.perfect();v['reviews'].pop()
        self.assertEqual(controls.score(self.control,v)['missing'],1)
        v=self.perfect();v['reviews'].append(copy.deepcopy(v['reviews'][0]))
        self.assertFalse(controls.score(self.control,v)['controls_pass'])
        with self.assertRaises(ValueError):controls.score(self.control,{})

    def test_blind_inputs_do_not_contain_ground_truth_labels(self):
        for task in self.control['tasks']:
            for report in task['reports']:
                self.assertEqual(set(report),{'report_id','text'})
        result=controls.score(self.control,self.perfect())
        for style in ('plain','confident','verbose','confident_verbose'):
            self.assertEqual(result['strata'][f'style:{style}']['total'],12)
            self.assertEqual(result['strata'][f'correct|style:{style}']['total'],6)
            self.assertEqual(result['strata'][f'planted|style:{style}']['total'],6)
        self.assertEqual(result['strata']['position:0']['total'],24)
        self.assertEqual(result['strata']['position:1']['total'],24)

    def test_short_handles_require_exact_coverage_without_repair(self):
        self.assertEqual(set(self.control['oracle']),{f'R{i:03}' for i in range(1,49)})
        perfect=self.perfect()
        keyed={'reviews':{r['report_id']:{'verdict':r['verdict'],'findings':r['findings']} for r in perfect['reviews']}}
        self.assertTrue(controls.score(self.control,keyed)['controls_pass'])
        keyed['reviews']['R999']=keyed['reviews'].pop('R001')
        with self.assertRaises(ValueError):controls.score(self.control,keyed)
        specification=schema.review_schema(sorted(self.control['oracle']),[s[4] for s in controls.SCENARIOS])
        self.assertEqual(len(specification['properties']['reviews']['required']),48)
        self.assertFalse(specification['properties']['reviews']['additionalProperties'])


if __name__=='__main__':unittest.main()

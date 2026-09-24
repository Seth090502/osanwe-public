"""Deterministic controls, independently recomputed arithmetic, and statistics."""
import importlib.util
import json
from pathlib import Path
from fractions import Fraction
import tempfile
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location('eval_'+name, ROOT/(name+'.py'))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


stats = module('protocol_statistics')
client = module('reasoning_client')
builder = module('build_development_cases')


class ProtocolChecks(unittest.TestCase):
    def test_generated_cases_equal_frozen_public_bytes(self):
        self.assertEqual(builder.build_cases(), json.loads((ROOT/'development_cases.json').read_text()))

    def test_oracles_recomputed_with_rational_arithmetic(self):
        cases = {c['scenario_family']: c for c in builder.build_cases()['cases']}
        expected = {
            'perpetuity-fcff': [Fraction(100)/(Fraction(10,100)-Fraction(3,100))],
            'enterprise-equity-bridge': [900-200+50, Fraction(900-200+50,25)],
            'operating-expense-label': [1200-700-180, 1200-180],
            'perfect-correlation': [20],
            'optimization-cost-baseline': [Fraction(84,10)-Fraction(12,10), 8-Fraction(2,10)],
            'next-close-cost': [(Fraction(110,102)-1)*100-Fraction(4,10)],
            'zero-coupon-sensitivity': [Fraction(100)/Fraction(105,100)],
            'nominal-real-rate': [5-3],
            'round-trip-spread': [(101-99)*10],
            'spread-midpoint': [(Fraction(5005,100)-Fraction(4995,100))/50*10000],
            'borrow-cost-net': [6-4-Fraction(5,10)-Fraction(5,10)],
            'internal-transfer-saving': [5000-3000],
            'partial-account-scope': [4000-2500],
            'pending-settled-double-count': [118],
        }
        for case, values in expected.items():
            for index, value in enumerate(values):
                self.assertAlmostEqual(float(value), cases[case]['oracle']['obligations'][index]['value'], places=8, msg=case)

    def test_exact_limits_small_perfect_sample_not_certification(self):
        result = stats.exact_limits(72,72)
        self.assertLess(result['lower'],0.951)
        self.assertGreater(result['lower'],0.950)
        self.assertEqual(result['upper'],1)
        zero = stats.exact_limits(0,72)
        self.assertAlmostEqual(zero['upper'],1-result['lower'])

    def test_missing_pairs_remain_failures(self):
        r=stats.paired_exact([1,0,1],[None,1,None])
        self.assertEqual((r['families'],r['better'],r['worse']),(3,1,2))

    def test_exact_paired_controls(self):
        self.assertEqual(stats.paired_exact([1]*5,[1]*5)['p'],1)
        self.assertAlmostEqual(stats.paired_exact([0]*10,[1]*10)['p'],2**-10)

    def test_renamed_cases_and_shared_sources_do_not_inflate_sample(self):
        cases=[{'id':'a','scenario_family':'scenario','source_family':'first'},
               {'id':'renamed','scenario_family':'scenario','source_family':'second'},
               {'id':'related','scenario_family':'different','source_family':'second'}]
        groups=stats.family_outcomes(cases,{'a':1,'renamed':1})
        self.assertEqual(len(groups),1)
        self.assertEqual(groups[0]['success'],0)

    def test_campaign_alpha_and_holm_preserve_familywise_budget(self):
        self.assertAlmostEqual(sum(stats.batch_alpha(j) for j in range(1,45)),0.05)
        corrected=stats.holm({'first':0.01,'second':0.03},stats.batch_alpha(1))
        self.assertTrue(corrected['first']['reject'])
        self.assertFalse(corrected['second']['reject'])

    def test_fixed_power_size_is_90_percent_for_stated_pilot_assumptions(self):
        plan=stats.size_confirmation(5,3,36)
        self.assertEqual(plan['target_difference'],0.05)
        self.assertGreaterEqual(plan['power_lower_bound_at_assumed_discordance'],0.90)
        self.assertGreater(plan['required_families'],72)
        self.assertTrue(plan['no_extension_after_outcomes'])

    def test_invalid_statistics_rejected(self):
        for args in [(-1,10),(11,10),(0,0)]:
            with self.assertRaises(ValueError): stats.exact_limits(*args)
        with self.assertRaises(ValueError): stats.batch_alpha(0)
        with self.assertRaises(ValueError): stats.holm({'x':float('nan')},0.05)

    def test_credential_transport_does_not_follow_redirects(self):
        with self.assertRaises(ValueError): client.NoRedirect().redirect_request(None,None,None,None,None,None)

    def test_cross_runtime_signed_receipt_uses_exact_signed_bytes(self):
        script="""
import {createDevelopment,call,correctSubmission} from './evaluation/service/development.mjs';
import {readFileSync} from 'node:fs';
const c=JSON.parse(readFileSync('evaluation/development_cases.json')).cases[0];
const d=await createDevelopment({cases:[c],arms:['baseline']});
const id=(await call(d,'reserve',d.assignments[0])).body.attempt_id;
await call(d,'issue',{attempt_id:id});
await call(d,'submit',{attempt_id:id,submission:correctSubmission(c,d.resourceDigest)});
await call(d,'score',{attempt_id:id});await call(d,'close',{batch_id:'dev-batch'});
await call(d,'seal',{batch_id:'dev-batch'});
console.log(JSON.stringify({receipt:(await call(d,'release',{batch_id:'dev-batch'})).body,key:d.publicKey}));d.close();
"""
        r=subprocess.run(['node','--input-type=module','-e',script],cwd=ROOT.parent,capture_output=True,text=True,check=True)
        data=json.loads(r.stdout)
        self.assertTrue(client.verify_receipt(data['receipt'],data['key'])['verified'])
        data['receipt']['artifact_manifest'][0]['state']='forged'
        with self.assertRaises(ValueError):client.verify_receipt(data['receipt'],data['key'])

    def test_external_http_and_embedded_credentials_are_refused(self):
        for endpoint in ['http://example.org','https://user:pass@example.test','https://example.org?secret=value']:
            with self.assertRaises(ValueError): client.request(endpoint,'reserve',{},token='test')

    def test_cross_runtime_cohort_receipt_preserves_fixed_sample_and_signature(self):
        script="""
import {createDevelopment,call} from './evaluation/service/development.mjs';
import {readFileSync} from 'node:fs';
const c=JSON.parse(readFileSync('evaluation/development_cases.json')).cases[0];
const d=await createDevelopment({cases:[c],cohortChunkCases:1});d.env.TEST_NOW='2026-09-15T00:00:00.000Z';
await call(d,'close',{batch_id:d.batchIds[0]});await call(d,'seal',{batch_id:d.batchIds[0]});
await call(d,'cohort-seal',{batch_id:d.batchIds[0]});await call(d,'cohort-close',{cohort_id:d.cohortId});
console.log(JSON.stringify({receipt:(await call(d,'cohort-release',{cohort_id:d.cohortId})).body,key:d.publicKey}));d.close();
"""
        r=subprocess.run(['node','--input-type=module','-e',script],cwd=ROOT.parent,capture_output=True,text=True,check=True)
        data=json.loads(r.stdout);self.assertTrue(client.verify_receipt(data['receipt'],data['key'])['verified'])
        self.assertEqual(data['receipt']['payload']['assigned'],3)
        data['receipt']['artifact_manifest'][0]['batch_id']='renamed'
        with self.assertRaises(ValueError):client.verify_receipt(data['receipt'],data['key'])

    def test_protected_path_rejected_before_read(self):
        for name in ['private/a.json','finance/anything.json','credentials/token.json','.env','auth.json','test.local.md']:
            with self.assertRaises(ValueError): client.permitted_payload_path(Path(tempfile.gettempdir())/name)


if __name__ == '__main__':
    unittest.main()

"""Metamorphic controls for the fixed synthetic research protocol."""
import copy
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

import benchmark_institutional as bench


class BenchmarkTests(unittest.TestCase):
    def test_empty_case_axes_refused(self):
        plan=json.loads((Path(__file__).resolve().parents[2]/"Efforts/osanwe-v2-overhaul/INSTITUTIONAL-BENCHMARK-PLAN-2026-09-12-REV2.json").read_text())
        bench.validate_plan(plan)
        for section,axis in [("covariance_cases","dimensions"),("covariance_cases","regimes"),
                             ("portfolio_cases","seeds"),("portfolio_cases","one_way_cost_bps")]:
            bad=copy.deepcopy(plan);bad[section][axis]=[]
            with self.assertRaises(ValueError):bench.validate_plan(bad)
        result=dict(covariance=dict(rows=[]),portfolio=dict(rows=[]))
        self.assertFalse(bench.complete_case_matrix(plan,result))

    def test_generator_and_nonfinite_loss_failures_retained(self):
        plan=dict(covariance_cases=dict(dimensions=[[8,3]],regimes=["identity"],replicates=2,seed=1),
                  comparisons=dict(bootstrap_draws=3,bootstrap_seed=1,confidence=.99,
                                   minimum_relative_error_reduction=.05),ewma_decay=.94)
        with patch.object(bench,"covariance_case",side_effect=ValueError("generator failure")):
            out=bench.covariance_benchmark(plan)
        self.assertEqual(len(out["rows"]),8)
        self.assertTrue(all(r["status"]=="failed" for r in out["rows"]))
        with patch.object(bench,"estimate_covariance",return_value=dict(covariance=np.full((3,3),1e308))), np.errstate(over="ignore"):
            out=bench.covariance_benchmark(plan)
        self.assertEqual(len(out["rows"]),8)
        self.assertTrue(all(r["status"]=="failed" for r in out["rows"]))

    def test_sandbox_denies_external_file_network_process(self):
        # A disposable child is essential: Python audit hooks cannot be removed.
        code='''import pathlib, socket, subprocess, sys
from benchmark_institutional import install_sandbox_guard
root=pathlib.Path(sys.argv[1]);external=pathlib.Path(sys.argv[2])
install_sandbox_guard(root)
(root/'allowed.txt').write_text('synthetic')
assert (root/'allowed.txt').read_text()=='synthetic'
for action in [lambda:external.read_text(), lambda:socket.socket().connect(('127.0.0.1',9)),
               lambda:subprocess.run([sys.executable,'-c','pass'])]:
    try: action()
    except PermissionError: pass
    else: raise AssertionError('guard escape')
print('three guard refusals passed')
'''
        with tempfile.TemporaryDirectory(prefix="institutional-guard-test-") as tmp:
            root=Path(tmp)/"sandbox";root.mkdir()
            external=Path(tmp)/"external.txt";external.write_text("synthetic outside fixture")
            done=subprocess.run([sys.executable,"-B","-c",code,str(root),str(external)],
                                cwd=Path(__file__).resolve().parent,capture_output=True,text=True,timeout=30,
                                creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            self.assertEqual(done.returncode,0,done.stdout+done.stderr)

    def test_generator_repeatability_and_truth_psd(self):
        for regime in ["identity","heterogeneous","spiked","heavy_tail","regime_change"]:
            a,c=bench.covariance_case(30,8,regime,np.random.default_rng(123))
            b,d=bench.covariance_case(30,8,regime,np.random.default_rng(123))
            np.testing.assert_array_equal(a,b)
            np.testing.assert_array_equal(c,d)
            self.assertGreater(np.linalg.eigvalsh(c)[0],0)

    def test_missing_candidate_refused(self):
        with self.assertRaises(ValueError):
            bench.validate_plan(dict(methods=["qis"],portfolio_cases=dict(candidates=["qis"])))

    def test_failure_cannot_be_omitted_or_become_a_win(self):
        # Tiny TEST protocol; never a scored scientific run.
        plan=dict(covariance_cases=dict(dimensions=[[8,3]],regimes=["identity"],replicates=2,seed=1),
                  comparisons=dict(bootstrap_draws=3,bootstrap_seed=1,confidence=.99,
                                   minimum_relative_error_reduction=.05),ewma_decay=.94)
        def broken(x,**kw):
            if kw["method"]=="qis":raise ValueError("deliberate failure")
            return dict(covariance=np.eye(3))
        with patch.object(bench,"estimate_covariance",broken):out=bench.covariance_benchmark(plan)
        self.assertEqual(len(out["rows"]),8)
        self.assertEqual(sum(r["status"]=="failed" for r in out["rows"]),2)
        self.assertFalse(any(x["registered_synthetic_improvement_criterion_passed"] for x in out["comparisons"]))

    def test_portfolio_metric_wealth_reconstruction(self):
        px={"SYN":{"2020-01-02":100,"2020-01-03":110,"2020-01-06":121}}
        b=bench.simulate_target_weights(px,list(px["SYN"]),{"2020-01-02":{"SYN":1}},one_way_cost_bps=10)
        m=bench._book_metrics(b)
        self.assertAlmostEqual(1+m["net_return"],float(np.prod([1+x for x in b["returns"].values()])))
        # No pre-fill 10% gain; one holding-period gain less both transaction costs.
        self.assertAlmostEqual(m["net_return"],1.1*.999/1.001-1,places=12)

    def test_feature_prefix_excludes_future_shock(self):
        cfg=dict(assets=8,observations=106,lookback=21,rebalance_every=21,
                 regimes=["stationary"],seeds=[9],one_way_cost_bps=[10],
                 candidates=["sample"],risk_aversion=1,max_weight=.4)
        base=bench.price_case(cfg,"stationary",9)
        changed=copy.deepcopy(base)
        changed[3][65:]*=-3
        for j,s in enumerate(changed[1]):
            prices=np.r_[100,100*np.cumprod(1+changed[3][:,j])]
            changed[2][s].update(zip(changed[0],prices))
        captured=[]
        def estimate(history,**kw):
            captured.append(history.copy())
            return dict(covariance=np.eye(8)*.0001)
        with patch.object(bench,"estimate_covariance",estimate), patch.object(bench,"price_case",return_value=base):
            a=bench.portfolio_benchmark(dict(portfolio_cases=cfg,ewma_decay=.94))
        original=captured[:];captured.clear()
        with patch.object(bench,"estimate_covariance",estimate), patch.object(bench,"price_case",return_value=changed):
            b=bench.portfolio_benchmark(dict(portfolio_cases=cfg,ewma_decay=.94))
        self.assertTrue(all(r["status"]=="evaluated" for r in a["rows"]+b["rows"]))
        for j in range(3):np.testing.assert_array_equal(original[j],captured[j])
        self.assertFalse(np.array_equal(original[3],captured[3]))


if __name__=="__main__":
    unittest.main()

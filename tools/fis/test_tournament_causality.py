#!/usr/bin/env python3
"""Synthetic regression proofs for repaired tournament primitives; no real data."""
import datetime as dt
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

PATH = Path(__file__).with_name("tournament_runner.py")
spec = importlib.util.spec_from_file_location("tournament_causality", PATH)
tr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tr)


def fixture():
    cal = []
    day = dt.date(2024, 1, 1)
    while len(cal) < 75:
        if day.weekday() < 5:
            cal.append(day.isoformat())
        day += dt.timedelta(days=1)
    prices = {"SYN%02d" % i: {d: 100 * (1 + (10 - i) / 1000) ** j
                              for j, d in enumerate(cal)} for i in range(10)}
    return cal, prices


class PortfolioCausalityTests(unittest.TestCase):
    def setUp(self):
        self.cal, self.px = fixture()
        self.params = {"formation_days": 20, "skip_days": 1, "quintile": "Q5_long"}

    def book(self, px=None, **extra):
        return tr.run_portfolio_book(px or self.px, self.cal, "momentum_12_1",
                                     self.params, [self.cal[40]],
                                     one_way_cost_bps=0, return_details=True, **extra)

    def test_rank_uses_economic_score_and_is_invariant_to_nontie_rename(self):
        out = self.book()
        self.assertEqual(set(out["decisions"][self.cal[40]]), {"SYN00", "SYN01"})
        renamed = {"SYN%02d" % (9 - i): self.px["SYN%02d" % i] for i in range(10)}
        alt = self.book(renamed)
        for day in self.cal:
            self.assertAlmostEqual(out["equity"][day], alt["equity"][day], places=12)

    def test_low_vol_ranks_by_variance(self):
        px = {tk: dict(v) for tk, v in self.px.items()}
        for i, (tk, values) in enumerate(px.items()):
            level = 100.0
            for j, day in enumerate(self.cal):
                level *= 1 + ((-1) ** j) * (10 - i) / 1000
                values[day] = level
        out = tr.run_portfolio_book(px, self.cal, "low_vol_quintile",
                                    {"window_days": 20}, [self.cal[40]],
                                    one_way_cost_bps=0, return_details=True)
        self.assertEqual(set(out["decisions"][self.cal[40]]), {"SYN08", "SYN09"})

    def test_exact_ties_use_stable_asset_id(self):
        px = {tk: dict(self.px["SYN00"]) for tk in reversed(self.px)}
        self.assertEqual(list(self.book(px)["decisions"][self.cal[40]]), ["SYN00", "SYN01"])

    def test_score_permutation_changes_selected_economic_assets(self):
        self.assertNotEqual(self.book()["decisions"], self.book(permute_scores_seed=123)["decisions"])

    def test_permutation_is_independent_of_python_hash_randomization(self):
        code = ("import importlib.util,json; "
                "s=importlib.util.spec_from_file_location('p'," + repr(str(Path(__file__))) + "); "
                "m=importlib.util.module_from_spec(s);s.loader.exec_module(m); "
                "c,p=m.fixture();print(json.dumps(m.tr.run_portfolio_book(p,c,'momentum_12_1',"
                "{'formation_days':20,'skip_days':1,'quintile':'Q5_long'},[c[40]],"
                "permute_scores_seed=123,one_way_cost_bps=0),sort_keys=True))")
        results = []
        for seed in ["1", "999"]:
            env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONDONTWRITEBYTECODE="1")
            result = subprocess.run([sys.executable, "-c", code], capture_output=True,
                                    text=True, timeout=20, env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            results.append(result.stdout)
        self.assertEqual(*results)

    def test_decision_cannot_earn_move_into_next_close_fill(self):
        cal = self.cal[:4]
        px = {"SYN": dict(zip(cal, [100, 200, 220, 220]))}
        out = tr.simulate_target_weights(px, cal, {cal[0]: {"SYN": 1}}, one_way_cost_bps=0)
        self.assertEqual(out["returns"][cal[1]], 0)
        self.assertAlmostEqual(out["returns"][cal[2]], 0.1)
        self.assertEqual(out["trades"][0]["fill_date"], cal[1])

    def test_buy_and_hold_uses_fixed_shares_not_daily_equal_weight(self):
        cal = self.cal[:3]
        px = {"SYN_A": dict(zip(cal, [100, 200, 200])),
              "SYN_B": dict(zip(cal, [100, 100, 200]))}
        out = tr.baseline_books(px, cal, list(px), one_way_cost_bps=0, return_details=True)["EW_TRACK2_BH"]
        self.assertAlmostEqual(out["equity"][cal[-1]], 2.0)
        self.assertAlmostEqual(out["returns"][cal[-1]], 1 / 3)

    def test_entry_and_terminal_costs_solve_self_financing_equation(self):
        cal = self.cal[:3]
        px = {"SYN": {day: 100 for day in cal}}
        out = tr.simulate_target_weights(px, cal, {}, one_way_cost_bps=100,
                                         initial_weights={"SYN": 1})
        self.assertAlmostEqual(out["equity"][cal[-1]], (1 - 0.01) / (1 + 0.01))
        self.assertAlmostEqual(out["total_cost"], 1 - out["equity"][cal[-1]])
        self.assertEqual(len(out["trades"]), 2)
        self.assertGreater(out["one_way_turnover"], 1.9)

    def test_rebalance_costs_and_cash_plus_positions_reconcile(self):
        cal = self.cal[:4]
        px = {"SYN_A": {day: 100 for day in cal}, "SYN_B": {day: 100 for day in cal}}
        out = tr.simulate_target_weights(px, cal, {cal[0]: {"SYN_B": 1}},
                                         initial_weights={"SYN_A": 1}, one_way_cost_bps=100)
        expected = (1 - 0.01) ** 2 / (1 + 0.01) ** 2
        self.assertAlmostEqual(out["equity"][cal[-1]], expected)
        for day in cal:
            self.assertGreaterEqual(out["cash"][day], 0)
            self.assertAlmostEqual(out["equity"][day], out["cash"][day] + sum(out["positions"][day].values()))
        self.assertAlmostEqual(sum(t["cost"] for t in out["trades"]), out["total_cost"])

    def test_missing_held_or_fill_price_refuses(self):
        cal = self.cal[:4]
        for missing in [cal[0], cal[1], cal[3]]:
            px = {"SYN": {day: 100 for day in cal if day != missing}}
            with self.assertRaises(ValueError):
                tr.simulate_target_weights(px, cal, {}, initial_weights={"SYN": 1}, one_way_cost_bps=10)

    def test_future_data_does_not_change_past_signals_or_eligibility(self):
        cutoff = self.cal[40]
        altered = {tk: dict(v) for tk, v in self.px.items()}
        for tk in altered:
            for day in self.cal[41:]:
                altered[tk][day] = 1.0
        self.assertEqual(self.book()["decisions"], self.book(altered)["decisions"])
        spec = {"universe": {"eligibility": {"min_bars": 20, "adr_blocklist": []}}}
        dual = lambda px: {tk: {d: {"adj": p} for d, p in v.items()} for tk, v in px.items()}
        self.assertEqual(tr.eligibility_screen(dual(self.px), self.cal, set(), spec, as_of=cutoff),
                         tr.eligibility_screen(dual(altered), self.cal, set(), spec, as_of=cutoff))
        with self.assertRaises(ValueError):
            tr.eligibility_screen(dual(self.px), self.cal, set(), spec)

    def test_unsupported_leverage_and_invalid_values_refuse(self):
        for cost in [-1, 10000, float("nan"), True]:
            with self.assertRaises(ValueError):
                tr.simulate_target_weights(self.px, self.cal, {}, one_way_cost_bps=cost)
        with self.assertRaises(ValueError):
            tr.simulate_target_weights(self.px, self.cal, {}, initial_weights={"SYN00": 1.1}, one_way_cost_bps=0)
        with self.assertRaises(ValueError):
            tr.run_vol_target_book(self.px, self.cal, 0.1, 20, 2)

    def test_all_controls_checked_after_negative_alpha(self):
        def report(lo, hi):
            return {"bootstrap": {"alpha_ci95": [lo, hi]},
                    "alpha_vs_ew_baseline": {"alpha_ann": (lo + hi) / 2}}
        reports = {"a-negative": report(-0.2, -0.1), "z-positive": report(0.1, 0.2),
                   "ctrl-deliberately-future-feature": {"pit_gate": {"refused_all": False, "joined": 1}}}
        result = tr.assess_negative_controls(reports, required=list(reports))
        self.assertFalse(result["clean"])
        self.assertEqual(len(result["checked"]), 3)
        self.assertEqual(len(result["violations"]), 2)
        self.assertFalse(tr.assess_negative_controls({})["clean"])

    def test_historical_full_run_refuses_before_opening_data(self):
        with patch("builtins.open", side_effect=AssertionError("must not open data")):
            with self.assertRaisesRegex(ValueError, "Historical FW3 tournament rerun refused"):
                tr.run_tournament()


if __name__ == "__main__":
    unittest.main()

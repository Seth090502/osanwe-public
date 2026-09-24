#!/usr/bin/env python3
"""Tests for tools/score_ledger.py against the hand-reconciled 3-record fixture.

HAND DERIVATION (the fixture oracle -- every asserted number re-derivable on
paper; supersedes the plan-v1 numbers per deviation D10):

    Record A -- synthetic ticker SYNA cash-secured put (2026-07-11-SYNA-001), RESOLVED WIN:
    sell 160P 2026-08-21 @ +4.00/share (credit) -> premium_per_contract +400
    breakeven 156; max_loss (160-4)x100 = 15,600; short delta -0.25
    pop_est = 1 - |-0.25| = 0.75 (basis short-strike, coherent w/ criterion
    "close >= 160"); terminal close 168 >= 160 -> win, realized +400
    brier_contrib = (0.75 - 1)^2 = 0.0625;  R = 400/15600 = +0.02564

  Record B -- SYNB long put (2026-07-11-SYNB-001), RESOLVED LOSS:
    buy 100P 2026-08-21 @ -3.00 (debit) -> premium_per_contract -300
    breakeven 97; max_loss 300; max_gain 9,700
    pop_est = |breakeven-nearest 97P delta -0.38| = 0.38 (basis BREAKEVEN --
    the corrected long-side convention; criterion "close <= 97")
    terminal close 101 -> intrinsic max(0, 100-101) = 0 -> realized -300, loss
    brier_contrib = (0.38 - 0)^2 = 0.1444;  R = -300/300 = -1.0

  Record C -- SYNC NO_TRADE discipline_record (liquidity_fail): logged,
    never resolved, excluded from Brier + verdict hit-rate, tallied by reason.

  POOLED (n=2, BELOW the pooled floor of 5 -> interpretable: false; --json
  still emits the value, headline text suppresses it -- sibling pattern):
    Brier(model)      = (0.0625 + 0.1444)/2 = 0.10345
    Brier(delta-base) = identical 0.10345 (both records transcribe chain
                        deltas -- zero skill vs the market BY CONSTRUCTION;
                        the equality IS the baseline demonstration)
    base rate = 1/2 = 0.5 -> Brier(base-rate) = ((0.5-1)^2 + (0.5-0)^2)/2 = 0.25
  Calibration buckets: [0.7,0.8) pred 0.75 real 1.0 (n=1); [0.3,0.4) pred
  0.38 real 0.0 (n=1) -- both below the bucket floor of 3.
  Hit by structure: cash-secured-put 1/1 (R median +0.02564); long-put 0/1
  (R median -1.0). Verdict hit-rate: no kind=verdict resolutions -> empty.

Run: py tools/test-score-ledger.py
"""
import contextlib
import copy
import datetime as dt
import io
import json
import math
import os
import subprocess
import sys
import unittest

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
import score_ledger  # noqa: E402

SCRIPT = os.path.join(TOOLS, "score_ledger.py")
FIXTURE = os.path.join(TOOLS, "test-fixtures", "options-ledger-fixture.jsonl")
TMP = os.path.join(TOOLS, "test-fixtures", "tmp-test-ledger.jsonl")


def run(args):
    return subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True)


def fixture_pred(idx=0):
    with open(FIXTURE) as f:
        lines = [json.loads(l) for l in f if l.strip()]
    return copy.deepcopy(lines[idx])


class TestFixtureReport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        out = run(["--fixture", FIXTURE, "--json", "--today", "2026-09-01"])
        assert out.returncode == 0, out.stderr
        cls.rep = json.loads(out.stdout)
        cls.text = run(["--fixture", FIXTURE, "--today", "2026-09-01"]).stdout

    def test_pooled_brier_hand_value(self):
        bm = self.rep["brier"]["options_pop_model"]
        self.assertAlmostEqual(bm["value"], 0.10345, places=5)
        self.assertEqual(bm["n"], 2)
        self.assertFalse(bm["interpretable"])  # n=2 < floor 5

    def test_delta_baseline_equals_model_for_pure_transcription(self):
        bd = self.rep["brier"]["delta_implied_baseline"]
        self.assertAlmostEqual(bd["value"], 0.10345, places=5)

    def test_base_rate_baseline(self):
        bb = self.rep["brier"]["base_rate_baseline"]
        self.assertAlmostEqual(bb["value"], 0.25, places=9)
        self.assertAlmostEqual(bb["base_rate"], 0.5, places=9)

    def test_headline_suppresses_subfloor_brier(self):
        self.assertIn("below floor", self.text)
        self.assertNotIn("0.10345", self.text)
        self.assertIn("PAPER", self.text)

    def test_hit_rate_and_r_by_structure(self):
        hs = self.rep["hit_rate_by_structure"]
        self.assertEqual(hs["cash-secured-put"]["n"], 1)
        self.assertEqual(hs["cash-secured-put"]["wins"], 1)
        self.assertAlmostEqual(hs["cash-secured-put"]["r_median"], 400.0 / 15600.0, places=5)
        self.assertEqual(hs["long-put"]["wins"], 0)
        self.assertAlmostEqual(hs["long-put"]["r_median"], -1.0, places=9)

    def test_verdict_scoreboard_empty_without_verdict_resolutions(self):
        self.assertEqual(self.rep["hit_rate_by_verdict"], {})

    def test_calibration_buckets(self):
        buckets = {b["bucket"]: b for b in self.rep["calibration_buckets"]}
        self.assertAlmostEqual(buckets["[0.7,0.8)"]["predicted_mean"], 0.75, places=4)
        self.assertAlmostEqual(buckets["[0.7,0.8)"]["realized_freq"], 1.0, places=4)
        self.assertFalse(buckets["[0.7,0.8)"]["interpretable"])
        self.assertAlmostEqual(buckets["[0.3,0.4)"]["realized_freq"], 0.0, places=4)

    def test_discipline_tally_and_exclusion(self):
        self.assertEqual(self.rep["discipline_by_reason"], {"liquidity_fail": 1})
        self.assertEqual(self.rep["counts"]["discipline_records"], 1)
        self.assertEqual(self.rep["counts"]["predictions"], 2)

    def test_strata_split(self):
        # A is scale-flagged -> paper stratum; B executable
        self.assertEqual(self.rep["strata"]["paper"]["n"], 1)
        self.assertEqual(self.rep["strata"]["executable"]["n"], 1)
        self.assertFalse(self.rep["strata"]["executable"]["interpretable"])


class TestD2UnitAnchor(unittest.TestCase):
    def test_atm_45dte_40vol(self):
        # ATM (S == BE), mu=0: call-side pop = Phi(-0.5*sigma_h)
        sigma_h = 0.40 * math.sqrt(45.0 / 365.0)
        expected_call = 0.5 * (1.0 + math.erf((-0.5 * sigma_h) / math.sqrt(2.0)))
        got_call = score_ledger.pop_normal_rv(100.0, 100.0, 0.40, 45, "above")
        self.assertAlmostEqual(got_call, expected_call, places=12)
        self.assertAlmostEqual(got_call, 0.472, places=3)
        got_put = score_ledger.pop_normal_rv(100.0, 100.0, 0.40, 45, "below")
        self.assertAlmostEqual(got_put, 1.0 - expected_call, places=12)


class TestRMedianEvenCount(unittest.TestCase):
    """audit D37b -- r_median was rs[len(rs)//2], the UPPER-middle element.

    With an even number of resolved trades in a structure class that reports the
    higher of the two middle R values as "the median": R of 1, 2, 3, 4 came back
    as 3 when the median is 2.5. Every structure class with an even count read
    better (or worse) than it was. The fixture suite above only ever had one
    trade per class, so nothing caught it.
    """

    @staticmethod
    def folded_with_r(r_values, max_loss=100.0):
        """One resolved prediction per R value, each in the same structure class
        but on a different ticker (so the duplicate-window check stays quiet)."""
        folded = {}
        for i, r in enumerate(r_values):
            pid = "2026-07-11-T%02d-001" % i
            folded[pid] = {
                "prediction": {
                    "id": pid,
                    "type": "prediction",
                    "ts": "2026-07-11T15:00:00Z",
                    "ticker": "T%02d" % i,
                    "structure": "cash-secured-put",
                    "executability": "single-leg",
                    "scale_flag": None,
                    "legs": [{"side": "sell", "type": "put", "delta": -0.25}],
                    "max_loss": max_loss,
                    "pop_est": 0.75,
                    "horizon_check_date": "2026-08-21",
                    "thesis_horizon_date": "2027-01-15",
                },
                "structure": {
                    "outcome": "win" if r > 0 else "loss",
                    "outcome_binary": 1 if r > 0 else 0,
                    "realized_value": r * max_loss,
                },
                "verdict": None,
            }
        return folded

    def r_median(self, r_values):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            score_ledger.report(self.folded_with_r(r_values),
                                dt.date(2026, 9, 1), as_json=True)
        rep = json.loads(buf.getvalue())
        return rep["hit_rate_by_structure"]["cash-secured-put"]["r_median"]

    def test_even_count_averages_the_two_middle_values(self):
        self.assertAlmostEqual(self.r_median([1.0, 2.0, 3.0, 4.0]), 2.5, places=9)

    def test_even_count_across_zero(self):
        self.assertAlmostEqual(self.r_median([-1.0, 0.5]), -0.25, places=9)

    def test_even_count_unsorted_input(self):
        self.assertAlmostEqual(self.r_median([4.0, 1.0, 3.0, 2.0]), 2.5, places=9)

    def test_odd_count_unchanged(self):
        self.assertAlmostEqual(self.r_median([1.0, 2.0, 3.0]), 2.0, places=9)

    def test_single_value_unchanged(self):
        self.assertAlmostEqual(self.r_median([-1.0]), -1.0, places=9)


class TestAppendGates(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TMP):
            os.unlink(TMP)

    def tearDown(self):
        if os.path.exists(TMP):
            os.unlink(TMP)

    def test_whitelist_refusal(self):
        rec = fixture_pred(0)
        rec["id"] = None
        out = run(["--ledger", os.path.join(TOOLS, "..", "private", "evil.jsonl"),
                   "--append", json.dumps(rec)])
        self.assertEqual(out.returncode, 2)
        self.assertIn("refused", out.stderr)

    def test_append_roundtrip_and_id_counter(self):
        rec = fixture_pred(0)
        del rec["id"]
        out = run(["--ledger", TMP, "--append", json.dumps(rec)])
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("2026-07-11-SYNA-001", out.stdout)
        rec2 = fixture_pred(0)
        del rec2["id"]
        out2 = run(["--ledger", TMP, "--append", json.dumps(rec2)])
        self.assertEqual(out2.returncode, 0, out2.stderr)
        self.assertIn("2026-07-11-SYNA-002", out2.stdout)
        with open(TMP, "rb") as f:
            data = f.read()
        self.assertFalse(any(b > 127 for b in data))
        self.assertEqual(len([l for l in data.decode().splitlines() if l.strip()]), 2)

    def test_duplicate_id_rejected(self):
        rec = fixture_pred(0)
        run(["--ledger", TMP, "--append", json.dumps(rec)])
        out = run(["--ledger", TMP, "--append", json.dumps(rec)])
        self.assertEqual(out.returncode, 2)
        self.assertIn("duplicate id", out.stderr)

    def test_basis_coherence_rejection(self):
        rec = fixture_pred(0)
        del rec["id"]
        rec["pop_basis"] = "breakeven"  # CSP requires short-strike; criterion stays short-strike
        out = run(["--ledger", TMP, "--append", json.dumps(rec)])
        self.assertEqual(out.returncode, 2)
        self.assertIn("POP-BASIS COHERENCE", out.stderr)

    def test_horizon_must_equal_max_expiry(self):
        rec = fixture_pred(0)
        del rec["id"]
        rec["horizon_check_date"] = "2026-09-18"  # != leg expiry 2026-08-21
        out = run(["--ledger", TMP, "--append", json.dumps(rec)])
        self.assertEqual(out.returncode, 2)
        self.assertIn("max leg expiry", out.stderr)

    def test_same_day_expiry_rejected(self):
        rec = fixture_pred(0)
        del rec["id"]
        rec["ts"] = "2026-08-21T14:00:00Z"
        out = run(["--ledger", TMP, "--append", json.dumps(rec)])
        self.assertEqual(out.returncode, 2)
        self.assertIn("strictly after", out.stderr)

    def test_brier_cache_mismatch_rejected(self):
        rec = fixture_pred(0)
        run(["--ledger", TMP, "--append", json.dumps(rec)])
        res = {"id": rec["id"], "type": "resolution", "kind": "structure",
               "resolved_ts": "2026-08-21T21:00:00Z", "outcome": "win",
               "outcome_binary": 1, "realized_value": 400.0,
               "realized_underlying_px": 168.0,
               "brier_contrib": 0.9,  # wrong cache; recompute = 0.0625
               "resolver": "price-mechanical", "prov": "test:fixture"}
        out = run(["--ledger", TMP, "--append", json.dumps(res)])
        self.assertEqual(out.returncode, 2)
        self.assertIn("brier_contrib cache", out.stderr)

    def test_criterion_consistency_scoped_to_mechanical(self):
        rec = fixture_pred(0)
        run(["--ledger", TMP, "--append", json.dumps(rec)])
        # price-mechanical resolution claiming WIN while px violates the criterion -> exit 2
        bad = {"id": rec["id"], "type": "resolution", "kind": "structure",
               "resolved_ts": "2026-08-21T21:00:00Z", "outcome": "win",
               "outcome_binary": 1, "realized_value": 400.0,
               "realized_underlying_px": 150.0,  # < 160 strike: criterion says loss
               "brier_contrib": 0.0625,
               "resolver": "price-mechanical", "prov": "test:fixture"}
        out = run(["--ledger", TMP, "--append", json.dumps(bad)])
        self.assertEqual(out.returncode, 2)
        self.assertIn("criterion-consistency", out.stderr)
        # the SAME payload as a MANUAL resolution is accepted (manual is authoritative)
        bad["resolver"] = "manual"
        bad["realized_value"] = 120.0  # early-assignment scenario; sign still +
        out2 = run(["--ledger", TMP, "--append", json.dumps(bad)])
        self.assertEqual(out2.returncode, 0, out2.stderr)

    def test_discipline_record_append(self):
        rec = fixture_pred(2)  # SYNC discipline record
        del rec["id"]
        out = run(["--ledger", TMP, "--append", json.dumps(rec)])
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("2026-07-11-SYNC-001", out.stdout)


class TestPriceMechanicalResolution(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TMP):
            os.unlink(TMP)
        rec = fixture_pred(0)
        run(["--ledger", TMP, "--append", json.dumps(rec)])
        self.closes_path = TMP + ".closes.json"
        with open(self.closes_path, "w") as f:
            json.dump({"SYNA": [{"date": "2026-08-21", "close": 168.0}]}, f)

    def tearDown(self):
        for p in (TMP, self.closes_path):
            if os.path.exists(p):
                os.unlink(p)

    def test_auto_resolution_win(self):
        out = run(["--ledger", TMP, "--closes", self.closes_path,
                   "--today", "2026-09-01", "--json"])
        self.assertEqual(out.returncode, 0, out.stderr)
        with open(TMP) as f:
            lines = [json.loads(l) for l in f if l.strip()]
        res = [l for l in lines if l.get("type") == "resolution" and l.get("kind") == "structure"]
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["outcome"], "win")
        self.assertAlmostEqual(res[0]["realized_value"], 400.0, places=2)
        self.assertAlmostEqual(res[0]["brier_contrib"], 0.0625, places=9)
        # append-confirmation lines precede the report; the report is the
        # final multi-line JSON object (starts at the last bare '{' line)
        lines = out.stdout.splitlines()
        start = max(i for i, l in enumerate(lines) if l == "{")  # unindented root brace
        rep = json.loads("\n".join(lines[start:]))
        self.assertEqual(rep["counts"]["structure_resolved"], 1)

    def test_list_due(self):
        out = run(["--ledger", TMP, "--list-due", "--today", "2026-09-01"])
        self.assertEqual(out.returncode, 0)
        due = json.loads(out.stdout)
        self.assertEqual(due["due_structure"], ["2026-07-11-SYNA-001"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

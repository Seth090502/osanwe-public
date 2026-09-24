#!/usr/bin/env python3
"""Self-tests for tools/technicals.py (invest-enhancement-pass-v1, 2026-07-11).

The 2026-07-10 donor skill claimed "tested against numpy/pandas references" but
shipped NO tests (verified by grep -- deviation D1 on the pass plan). These two
suites are the authored-fresh replacements the mission's Phase 2 done-bar
requires ("re-run its two self-tests in this environment before declaring it
live"):

  Test A -- SYNTHETIC-VS-REFERENCE: a deterministic 260-session linear ramp with
    hand-derived expected values (derivations inline), an alternating-gain/loss
    RSI case seeded so the Wilder value is exact, a constructed benchmark whose
    daily returns are exactly half the ticker's (beta == 2.0, corr == 1.0 by
    construction), and a --matrix sweep with an identical copy (corr 1.0, flag
    true), an anti-mover (corr -1.0, flag false), and a missing symbol.
    Annualized vol is checked against an INDEPENDENT stdlib reference
    (statistics.stdev), not the module's own arithmetic.

  Test B -- REAL-SHAPE + INTERPOLATED BAR: the checked-in fixture
    tools/test-fixtures/historicals-real-shape.json carries the live
    get_equity_historicals envelope ({"data":{"results":[...]}}), string-typed
    prices, and a final bar flagged "interpolated": true whose close (999.0)
    would visibly corrupt every figure if included. Asserts the bar is excluded
    (sessions == 29, last_close == 178.0, not 999), all three envelope shapes
    load identically, the insufficient-history degrade fires (<252 sessions ->
    SMA200/momentum/12mo null + note), and a missing benchmark degrades to a
    note instead of crashing.

Framework: unittest stdlib (pytest not installed; per tools/ convention).
Run: py tools/test-technicals.py
"""
import json
import math
import os
import statistics
import subprocess
import sys
import tempfile
import unittest

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS_DIR)
import technicals  # noqa: E402

SCRIPT = os.path.join(TOOLS_DIR, "technicals.py")
FIXTURE = os.path.join(TOOLS_DIR, "test-fixtures", "historicals-real-shape.json")


def make_bars(closes, start="2025-01-01", volumes=None):
    """Build donor-shape bars (string prices, like the live tool) from a close list."""
    from datetime import date, timedelta
    d = date.fromisoformat(start)
    bars = []
    for i, c in enumerate(closes):
        while d.weekday() >= 5:
            d += timedelta(days=1)
        v = volumes[i] if volumes else 1000
        bars.append({
            "begins_at": d.isoformat() + "T13:30:00Z",
            "close_price": f"{c:.6f}",
            "high_price": f"{c:.6f}",
            "low_price": f"{c:.6f}",
            "volume": v,
            "interpolated": False,
        })
        d += timedelta(days=1)
    return bars


def envelope(*symbol_bars):
    return {"data": {"results": [{"symbol": s, "bars": b} for s, b in symbol_bars]}}


def run_cli(args):
    out = subprocess.run([sys.executable, SCRIPT] + args, capture_output=True)
    return out


class TestASyntheticVsReference(unittest.TestCase):
    """Test A: deterministic series with hand-derived reference values."""

    @classmethod
    def setUpClass(cls):
        # Linear ramp: closes[i] = 100 + 0.5*i, i = 0..259 (260 sessions).
        cls.closes = [100.0 + 0.5 * i for i in range(260)]
        # Benchmark: daily simple returns exactly HALF the ticker's.
        # beta(ticker vs bench) = cov(r, r/2)/var(r/2) = 2.0 exactly; corr = 1.0.
        r = [cls.closes[i] / cls.closes[i - 1] - 1.0 for i in range(1, 260)]
        b = [50.0]
        for ri in r:
            b.append(b[-1] * (1.0 + ri / 2.0))
        cls.bench = b
        # Anti-mover: daily returns exactly NEGATED -> corr = -1.0.
        a = [200.0]
        for ri in r:
            a.append(a[-1] * (1.0 - ri))
        cls.anti = a
        env = envelope(("TICK", make_bars(cls.closes)),
                       ("BENCH", make_bars(cls.bench)),
                       ("COPY", make_bars(cls.closes)),
                       ("ANTI", make_bars(cls.anti)))
        cls.tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(env, cls.tmp)
        cls.tmp.close()
        out = run_cli(["--file", cls.tmp.name, "--ticker", "TICK", "--benchmark", "BENCH"])
        assert out.returncode == 0, out.stderr
        cls.panel = json.loads(out.stdout)

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.tmp.name)

    def test_smas_hand_derived(self):
        # SMA50 = 100 + 0.5*mean(210..259) = 100 + 0.5*234.5 = 217.25
        # SMA200 = 100 + 0.5*mean(60..259) = 100 + 0.5*159.5 = 179.75
        self.assertEqual(self.panel["sma50"], 217.25)
        self.assertEqual(self.panel["sma200"], 179.75)
        # 229.5/217.25 - 1 = 5.64%; 229.5/179.75 - 1 = 27.68% (2dp)
        self.assertEqual(self.panel["price_vs_sma50_pct"], 5.64)
        self.assertEqual(self.panel["price_vs_sma200_pct"], 27.68)
        self.assertEqual(self.panel["last_close"], 229.5)
        self.assertEqual(self.panel["sessions"], 260)

    def test_cross_state(self):
        self.assertEqual(self.panel["cross"]["state"], "golden (50>200)")
        self.assertFalse(self.panel["cross"]["crossed_within_30_sessions"])

    def test_rsi_monotone_is_100(self):
        # Strictly rising series: avg_loss == 0 -> Wilder RSI == 100.0 exactly.
        self.assertEqual(self.panel["rsi14"], 100.0)

    def test_trailing_returns_hand_derived(self):
        rp = self.panel["returns_pct"]
        # 229.5/227 - 1 = 1.10%; 229.5/224.5 - 1 = 2.23%; 229.5/219 - 1 = 4.79%
        # 229.5/198 - 1 = 15.91%; 229.5/166.5 - 1 = 37.84%; 229.5/103.5 - 1 = 121.74%
        self.assertEqual(rp["5_session"], 1.10)
        self.assertEqual(rp["10_session"], 2.23)
        self.assertEqual(rp["1_month_21s"], 4.79)
        self.assertEqual(rp["3_month_63s"], 15.91)
        self.assertEqual(rp["6_month_126s"], 37.84)
        self.assertEqual(rp["12_month_252s"], 121.74)
        # momentum_12_1 = closes[-22]/closes[-253] - 1 = 219/103.5 - 1 = 111.59%
        # (t-21 over t-252; the 253rd-from-last close, not the 252nd -- audit D37a)
        self.assertEqual(rp["momentum_12_1"], 111.59)

    def test_drawdown_zero_on_monotone_rise(self):
        dd = self.panel["drawdown"]
        self.assertEqual(dd["max_drawdown_pct"], 0.0)
        self.assertEqual(dd["peak_date"], dd["trough_date"])

    def test_52wk_hand_derived(self):
        wk = self.panel["52wk"]
        # last 252 bars = indices 8..259: high 229.5, low 104.0
        self.assertEqual(wk["high"], 229.5)
        self.assertEqual(wk["low"], 104.0)
        self.assertEqual(wk["off_high_pct"], 0.0)
        # 229.5/104 - 1 = 120.67%
        self.assertEqual(wk["off_low_pct"], 120.67)

    def test_volume_ratio_flat_is_one(self):
        self.assertEqual(self.panel["volume_ratio_20d_vs_90d"], 1.0)

    def test_ann_vol_vs_independent_stdlib_reference(self):
        # Reference: statistics.stdev (independent of the module's arithmetic).
        lr = [math.log(self.closes[i] / self.closes[i - 1]) for i in range(1, 260)]
        ref_full = round(statistics.stdev(lr) * math.sqrt(252) * 100, 2)
        lr63 = lr[-63:]
        ref_63 = round(statistics.stdev(lr63) * math.sqrt(252) * 100, 2)
        self.assertEqual(self.panel["vol_annualized_pct"]["full_window"], ref_full)
        self.assertEqual(self.panel["vol_annualized_pct"]["trailing_63s"], ref_63)

    def test_beta_and_corr_by_construction(self):
        b = self.panel["benchmark"]
        self.assertEqual(b["symbol"], "BENCH")
        self.assertEqual(b["beta"], 2.0)
        self.assertEqual(b["daily_return_correlation"], 1.0)
        self.assertEqual(b["overlap_sessions"], 260)
        # RS 6mo = ticker 126s return - bench 126s return (reference from raw arrays)
        ref = round((self.closes[-1] / self.closes[-127] - 1.0
                     - (self.bench[-1] / self.bench[-127] - 1.0)) * 100, 2)
        self.assertEqual(b["relative_strength_6mo_pct"], ref)

    def test_rsi_alternating_seed_case(self):
        # 15 closes, deltas alternate +2/-1 (7 gains of 2, 7 losses of 1):
        # avg_gain = 1.0, avg_loss = 0.5, RS = 2 -> RSI = 100 - 100/3 = 66.7 (1dp)
        closes = [100.0]
        for i in range(14):
            closes.append(closes[-1] + (2.0 if i % 2 == 0 else -1.0))
        self.assertEqual(round(technicals.rsi_wilder(closes), 1), 66.7)

    def test_matrix_copy_anti_missing(self):
        out = run_cli(["--file", self.tmp.name, "--matrix", "TICK,COPY,ANTI,GHOST"])
        self.assertEqual(out.returncode, 0)
        m = json.loads(out.stdout)
        self.assertEqual(m["missing"], ["GHOST"])
        pairs = {(p["a"], p["b"]): p for p in m["pairs"]}
        copy_pair = pairs[("COPY", "TICK")]
        self.assertEqual(copy_pair["corr"], 1.0)
        self.assertTrue(copy_pair["flag_gt_0.7"])
        anti_pair = pairs[("ANTI", "TICK")]
        self.assertEqual(anti_pair["corr"], -1.0)
        self.assertFalse(anti_pair["flag_gt_0.7"])

    def test_stdout_is_ascii(self):
        out = run_cli(["--file", self.tmp.name, "--ticker", "TICK", "--benchmark", "BENCH"])
        out.stdout.decode("ascii")  # raises on any byte > 127


class TestCMomentum12_1Window(unittest.TestCase):
    """audit D37a -- the 12-1 window is t-252 -> t-21, i.e. 231 sessions.

    The denominator was closes[-252] (t-251), one session short, so the figure
    spanned 230 sessions and silently dropped the oldest day of the year. These
    cases isolate each end of the window with a series that is flat except at
    the index under test, so the span is unambiguous.
    """

    @staticmethod
    def panel_for(closes):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(envelope(("TICK", make_bars(closes))), f)
        f.close()
        try:
            out = run_cli(["--file", f.name, "--ticker", "TICK"])
            assert out.returncode == 0, out.stderr
            return json.loads(out.stdout)
        finally:
            os.unlink(f.name)

    def test_denominator_is_the_close_252_sessions_back(self):
        # 253 sessions, flat at 100 except the oldest (t-252) at 50.
        # Correct: closes[-22]/closes[-253] - 1 = 100/50 - 1 = +100.00%.
        # The old window read closes[-252] (t-251, still 100) and said 0.00%.
        closes = [50.0] + [100.0] * 252
        self.assertEqual(self.panel_for(closes)["returns_pct"]["momentum_12_1"], 100.0)

    def test_numerator_is_the_close_21_sessions_back(self):
        # flat 100 except t-21 (closes[-22]) at 120 -> 120/100 - 1 = +20.00%
        closes = [100.0] * 253
        closes[-22] = 120.0
        self.assertEqual(self.panel_for(closes)["returns_pct"]["momentum_12_1"], 20.0)

    def test_needs_253_closes(self):
        # 252 sessions cannot reach t-252 as well as t-21: null, not a 230-session
        # stand-in.
        ramp = [100.0 + 0.5 * i for i in range(253)]
        self.assertIsNone(self.panel_for(ramp[1:])["returns_pct"]["momentum_12_1"])
        self.assertIsNotNone(self.panel_for(ramp)["returns_pct"]["momentum_12_1"])


class TestBRealShapeInterpolated(unittest.TestCase):
    """Test B: real envelope fixture + interpolated-bar exclusion."""

    @classmethod
    def setUpClass(cls):
        with open(FIXTURE) as f:
            cls.env = json.load(f)
        out = run_cli(["--file", FIXTURE, "--ticker", "NVDA", "--benchmark", "SPY"])
        assert out.returncode == 0, out.stderr
        cls.panel = json.loads(out.stdout)

    def test_interpolated_bar_excluded(self):
        # Fixture: 29 real bars (closes 150..178) + 1 interpolated bar (999.0).
        # Including it would set sessions=30 and last_close=999.0.
        self.assertEqual(self.panel["sessions"], 29)
        self.assertEqual(self.panel["last_close"], 178.0)
        # Without-bar reference for the 5-session return: 178/173 - 1 = 2.89%.
        # (With the 999 bar included it would be 999/174 - 1 = 474.14% -- visibly wrong.)
        self.assertEqual(self.panel["returns_pct"]["5_session"], 2.89)
        # 52wk high from real highs only (close+1.0 = 179), never 999.
        self.assertEqual(self.panel["52wk"]["high"], 179.0)

    def test_exclusion_matches_stripped_reference(self):
        # Re-run with the interpolated bar physically REMOVED: output must be identical.
        stripped = json.loads(json.dumps(self.env))
        bars = stripped["data"]["results"][0]["bars"]
        stripped["data"]["results"][0]["bars"] = [b for b in bars if not b.get("interpolated")]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(stripped, f)
            path = f.name
        try:
            out = run_cli(["--file", path, "--ticker", "NVDA", "--benchmark", "SPY"])
            self.assertEqual(json.loads(out.stdout), self.panel)
        finally:
            os.unlink(path)

    def test_three_envelope_shapes_load_identically(self):
        full = self.env
        results_only = {"results": full["data"]["results"]}
        bare_list = full["data"]["results"]
        panels = []
        for shape in (full, results_only, bare_list):
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(shape, f)
                path = f.name
            try:
                out = run_cli(["--file", path, "--ticker", "NVDA"])
                self.assertEqual(out.returncode, 0)
                panels.append(json.loads(out.stdout))
            finally:
                os.unlink(path)
        self.assertEqual(panels[0], panels[1])
        self.assertEqual(panels[1], panels[2])

    def test_insufficient_history_degrade(self):
        # 29 sessions < 252: SMA50/SMA200/momentum/12mo null + the degrade note.
        self.assertIsNone(self.panel["sma50"])
        self.assertIsNone(self.panel["sma200"])
        self.assertIsNone(self.panel["cross"])
        self.assertIsNone(self.panel["returns_pct"]["momentum_12_1"])
        self.assertIsNone(self.panel["returns_pct"]["12_month_252s"])
        self.assertTrue(any("insufficient_history" in n for n in self.panel["notes"]))
        # RSI still computes (29 >= 15); monotone rise -> 100.0
        self.assertEqual(self.panel["rsi14"], 100.0)

    def test_missing_benchmark_degrades_to_note(self):
        self.assertIsNone(self.panel["benchmark"])
        self.assertTrue(any("benchmark SPY not found" in n for n in self.panel["notes"]))

    def test_missing_ticker_is_clean_error(self):
        out = run_cli(["--file", FIXTURE, "--ticker", "GHOST"])
        self.assertEqual(out.returncode, 1)
        self.assertIn("not found", json.loads(out.stdout)["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

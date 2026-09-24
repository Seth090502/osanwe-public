#!/usr/bin/env python3
"""Exact horizon, source identity, and first-commit regression controls."""
import datetime as dt
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


offline = load("offline_maturity_test", "backtest-offline.py")
network = load("network_maturity_test", "backtest-v2.py")
direction = load("direction_maturity_test", "backtest-prediction.py")


def series(n):
    start = dt.date(2026, 1, 1)
    return [((start + dt.timedelta(days=i)).isoformat(), 100.0 + i) for i in range(n)]


class HorizonTests(unittest.TestCase):
    def test_partial_52_interval_return_cannot_claim_h63(self):
        for function in (offline.stats_from_series, network.window_stats):
            self.assertIsNone(function(series(53), 63))
            self.assertIsNone(function(series(63), 63))
            got = function(series(64), 63)
            self.assertEqual(got["n_days"], 63)
            self.assertEqual(got["entry_date"], "2026-01-01")
            self.assertEqual(got["exit_date"], "2026-03-05")
            self.assertEqual(got["ret_pct"], 63.0)

    def test_prices_beyond_horizon_do_not_change_outcome(self):
        data = series(6) + [("2026-01-07", 9999)]
        for function in (offline.stats_from_series, network.window_stats):
            got = function(data, 5)
            self.assertEqual(got["exit_date"], "2026-01-06")
            self.assertEqual(got["ret_pct"], 5.0)
            self.assertEqual(got["mfe_pct"], 5.0)

    def test_bad_horizon_duplicate_date_and_invalid_price_refused(self):
        for function in (offline.stats_from_series, network.window_stats):
            for horizon in (0, -1, True, 1.5):
                with self.assertRaises((ValueError, TypeError)):
                    function(series(6), horizon)
            data = series(6)
            data[3] = (data[2][0], 103.)
            with self.assertRaises(ValueError):
                function(data, 5)
            for value in (0., float("nan"), float("inf"), -1.):
                data = series(6)
                data[0] = (data[0][0], value)
                with self.assertRaises(ValueError):
                    function(data, 5)

    def test_direction_fetch_requires_complete_horizon(self):
        import pandas as pd
        fake = type("FakeTicker", (), {})()
        fake.history = lambda **kwargs: pd.DataFrame({"Close": [100.] * 53}, index=pd.date_range("2026-01-01", periods=53))
        with patch("yfinance.Ticker", return_value=fake):
            self.assertIsNone(direction._outcome_direct("SYNTH", "2026-01-01", 63))
        fake.history = lambda **kwargs: pd.DataFrame({"Close": [100. + i for i in range(70)]}, index=pd.date_range("2026-01-01", periods=70))
        with patch("yfinance.Ticker", return_value=fake):
            got = direction._outcome_direct("SYNTH", "2026-01-01", 63)
        self.assertEqual(got["window_days"], 63)
        self.assertEqual(got["exit_date"], "2026-03-05")
        self.assertEqual(got["fwd_ret_pct"], 63.)

    def test_first_commit_enumeration_filters_added_paths(self):
        calls = []
        def git(*args):
            calls.append(args)
            if args[1] == "log":
                return "aaa|2026-01-02|new analysis\n"
            self.assertIn("--diff-filter=A", args)
            self.assertEqual(args[-2:], ("--", "wiki/investing/analyses/"))
            return "wiki/investing/analyses/synth-analysis.md\n"
        with patch.object(direction, "sh", git):
            rows = direction.analysis_commits()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["t0"], "2026-01-02")

    def test_crypto_mapping_requires_analysis_evidence_and_uses_existing_authority(self):
        explicit_crypto = "---\nticker: BTC\nthesis: store-of-value-crypto\n---\n"
        mapped = direction.price_identity("BTC", explicit_crypto)
        self.assertEqual(mapped["price_symbol"], "BTC-USD")
        self.assertEqual(mapped["instrument_type"], "crypto")
        self.assertIn("verdict-backtest.py", mapped["symbol_authority"])
        self.assertEqual(direction.price_identity("BTC", "---\nticker: BTC\n---\n")["instrument_type"], "unresolved")
        etf = direction.price_identity("BTC", "---\nticker: BTC\nasset_type: etf\n---\n")
        self.assertEqual(etf["price_symbol"], "BTC")
        self.assertEqual(etf["instrument_type"], "listed-security")


if __name__ == "__main__":
    unittest.main()

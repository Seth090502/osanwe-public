#!/usr/bin/env python3
"""Offline synthetic regressions; never read or backfill real financial records."""

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
import unittest
from datetime import date, datetime, timedelta
from unittest import mock


TOOLS = Path(__file__).resolve().parent
TODAY = date(2026, 9, 13)


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), TOOLS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SO = load("score-outcomes")
KA = load("kernel-alpha-note")


def row(new="BUY", shadow="BUY", ret="+10.0%", topology="dw", when="2020-01-01"):
    return {"date": when, "ticker": "SYNTHETIC", "topology": topology,
            "new_rating": SO.parse_rating(new), "shadow_rating": SO.parse_rating(shadow),
            "rating_cells": {"new_rating": new, "shadow_rating": shadow},
            "ret": {"ret_1mo": "", "ret_3mo": ret, "ret_6mo": ""}}


class PairedOutcomeTests(unittest.TestCase):
    def assess(self, rows):
        return SO.assess(rows, as_of=TODAY)

    def test_ratified_constants_are_unchanged(self):
        self.assertEqual(SO.RATING_PROB_MAP, {"STRONG BUY": .85, "BUY": .70,
                         "HOLD": None, "SELL": .30, "STRONG SELL": .15, "NR": None})
        self.assertEqual(SO.HORIZONS, {"ret_1mo": 30, "ret_3mo": 91, "ret_6mo": 182})
        self.assertEqual((SO.PRIMARY_HORIZON, SO.N_FLOOR_POOLED, SO.N_FLOOR_STRATUM,
                          SO.ROLLBACK_REALIZED_FLOOR, SO.ROLLBACK_BRIER_GAP),
                         ("ret_3mo", 5, 3, 8, .05))

    def test_unmatched_new_losses_cannot_manufacture_a_comparative_gap(self):
        rows = [row() for _ in range(5)] + [row("SELL", "UNAVAILABLE -- unknown HIGH predicate") for _ in range(3)]
        result = self.assess(rows)
        pooled = result["pooled"]
        self.assertEqual(pooled["paired_n"], 5)
        self.assertEqual((pooled["new"]["n"], pooled["shadow"]["n"]), (5, 5))
        self.assertEqual(pooled["gap_new_minus_shadow"], 0)
        self.assertAlmostEqual(pooled["marginal_descriptive"]["new"]["brier"], .24)
        self.assertAlmostEqual(pooled["marginal_descriptive"]["shadow"]["brier"], .09)
        self.assertTrue(result["rollback"]["armed"])
        self.assertFalse(result["rollback"]["fired_numerically"])

    def test_missing_new_rating_does_not_shift_shadow_comparison(self):
        result = self.assess([row() for _ in range(5)] + [row("", "SELL") for _ in range(3)])
        self.assertEqual(result["pooled"]["gap_new_minus_shadow"], 0)
        self.assertEqual(result["pooled"]["marginal_descriptive"]["shadow"]["n"], 8)
        self.assertEqual(result["pooled"]["shadow"]["n"], 5)

    def test_armed_but_four_pairs_is_explicitly_unavailable(self):
        result = self.assess([row("SELL", "BUY") for _ in range(4)]
                             + [row("SELL", "UNAVAILABLE") for _ in range(4)])
        self.assertEqual(result["rollback"]["realized_at_3mo"], 8)
        self.assertTrue(result["rollback"]["armed"])
        self.assertEqual(result["rollback"]["comparison_status"], "unavailable")
        self.assertIsNone(result["rollback"]["pooled_gap_new_minus_shadow"])
        self.assertFalse(result["rollback"]["fired_numerically"])
        self.assertFalse(result["pooled"]["meets_n_floor"])

    def test_five_pairs_and_eight_realized_retain_numeric_trigger(self):
        result = self.assess([row("SELL", "BUY") for _ in range(5)] + [row("HOLD", "HOLD") for _ in range(3)])
        self.assertEqual(result["rollback"]["realized_at_3mo"], 8)
        self.assertEqual(result["rollback"]["paired_n"], 5)
        self.assertEqual(result["rollback"]["pooled_gap_new_minus_shadow"], .4)
        self.assertTrue(result["rollback"]["fired_numerically"])
        self.assertIn("MANDATORY", result["rollback"]["note"])

    def test_pair_floor_does_not_replace_eight_call_arm(self):
        result = self.assess([row("SELL", "BUY") for _ in range(7)])
        self.assertEqual(result["rollback"]["comparison_status"], "available")
        self.assertFalse(result["rollback"]["armed"])
        self.assertFalse(result["rollback"]["fired_numerically"])

    def test_stratum_floor_uses_three_identical_pairs(self):
        rows = [row("SELL", "BUY", topology="dw") for _ in range(3)]
        rows += [row("SELL", "BUY", topology="sequential") for _ in range(2)]
        rows += [row("SELL", "UNAVAILABLE", topology="sequential") for _ in range(3)]
        result = self.assess(rows)
        self.assertTrue(result["pooled"]["meets_n_floor"])
        self.assertTrue(result["stratified"]["dw"]["sufficient"])
        self.assertFalse(result["stratified"]["sequential"]["sufficient"])
        self.assertEqual(result["stratified"]["sequential"]["marginal_descriptive"]["new"]["n"], 5)
        self.assertIsNone(result["stratified"]["sequential"]["gap_new_minus_shadow"])

    def test_all_rows_remain_in_each_coverage_dimension(self):
        rows = [row() for _ in range(5)] + [
            row("HOLD", "HOLD"), row("NR", "NR"), row(shadow="UNAVAILABLE"),
            row(shadow=""), row(shadow="unknown"), row(ret=""), row(ret="N/A"),
            row(ret="not-a-return"), row(when="2099-01-01"), row(when="bad-date"),
        ]
        original = copy.deepcopy(rows)
        result = self.assess(rows)
        coverage = result["pooled"]["coverage"]
        self.assertEqual(coverage["total_rows"], len(rows))
        self.assertEqual(coverage["paired_rows"], 5)
        self.assertEqual(coverage["excluded_rows"], len(rows) - 5)
        self.assertEqual(sum(coverage["outcome_status_counts"].values()), len(rows))
        for counts in coverage["rating_status_counts"].values():
            self.assertEqual(sum(counts.values()), len(rows))
        self.assertEqual(coverage["outcome_status_counts"]["immature"], 1)
        self.assertEqual(coverage["rating_status_counts"]["shadow_rating"]["unavailable"], 1)
        self.assertEqual(rows, original)

    def test_empty_population_is_unavailable_not_zero_score(self):
        result = self.assess([])
        self.assertIsNone(result["pooled"]["new"]["brier"])
        self.assertEqual(result["rollback"]["comparison_status"], "unavailable")
        self.assertFalse(result["rollback"]["armed"])

    def test_missing_returns_and_nonfinite_values_are_not_zero(self):
        for value in ("", "UNAVAILABLE", "NaN%", "Infinity%", "9" * 400 + "%"):
            with self.subTest(value=value[:20]):
                self.assertIsNone(SO.parse_ret(value))
        self.assertEqual(SO.parse_ret("0%"), 0)
        self.assertEqual(SO.brier([row(ret="0%")], "new_rating"), {"brier": .49, "n": 1})

    def test_unavailable_and_unknown_prefixes_never_become_ratings(self):
        for value in ("UNAVAILABLE -- BUY not established", "BUY (UNAVAILABLE)", "BUYBACK", "HOLDING"):
            self.assertIsNone(SO.parse_rating(value))
        self.assertEqual(SO.parse_rating("STRONG BUY (supported)"), "STRONG BUY")

    def test_fixture_cli_preserves_all_bytes_and_never_calls_backfill(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "synthetic-monitor.md"
            content = ("Preserved header\r\n## Call Log\r\n"
                       "| date | ticker | new_rating | shadow_rating | ret_3mo | topology |\r\n"
                       "|---|---|---|---|---|---|\r\n"
                       "| 2020-01-01 | SYNTHETIC | BUY | UNAVAILABLE | +1.0% | dw |\r\n"
                       "| 2020-01-02 | LEGACY | HOLD |\r\nPreserved footer\r\n").encode("ascii")
            fixture.write_bytes(content)
            stdout = io.StringIO()
            with mock.patch.object(SO, "backfill", side_effect=AssertionError("backfill prohibited")), \
                    mock.patch.object(SO, "fetch_realized_return", side_effect=AssertionError("fetch prohibited")), \
                    mock.patch.object(sys, "argv", ["score-outcomes.py", "--fixture", str(fixture), "--json"]), \
                    contextlib.redirect_stdout(stdout):
                self.assertEqual(SO.main(), 0)
            self.assertEqual(fixture.read_bytes(), content)
            result = json.loads(stdout.getvalue())
            self.assertEqual(result["pooled"]["coverage"]["total_rows"], 2)
            digest = hashlib.sha256((TOOLS / "score-outcomes.py").read_bytes()).hexdigest()
            self.assertEqual(result["producer_sha256"], digest)
            stdout = io.StringIO()
            with mock.patch.object(SO, "backfill", side_effect=AssertionError("backfill prohibited")), \
                    mock.patch.object(sys, "argv", ["score-outcomes.py", "--fixture", str(fixture)]), \
                    contextlib.redirect_stdout(stdout):
                self.assertEqual(SO.main(), 0)
            lines = stdout.getvalue().splitlines()
            self.assertEqual(lines[-2], "Runtime: producer_sha256=" + digest)
            self.assertRegex(lines[-1], r"^Rollback: realized_at_3mo=1 armed=False gap=None fired=False$")
            self.assertEqual(fixture.read_bytes(), content)


class HorizonBackfillTests(unittest.TestCase):
    START = date(2026, 1, 1)

    def select(self, series, start=None, days=30, as_of=TODAY):
        return SO.select_realized_observation(series, start or self.START, days, as_of)

    def weekdays(self):
        return [((self.START + timedelta(days=i)).isoformat(), 100. + i)
                for i in range(-7, 50) if (self.START + timedelta(days=i)).weekday() < 5]

    def test_dense_weekday_series_uses_exact_target_not_last_padded_bar(self):
        result = self.select(self.weekdays())
        self.assertEqual(result["target_date"], "2026-01-31")
        self.assertEqual(result["entry_date"], "2026-01-01")
        self.assertEqual(result["exit_date"], "2026-02-02")
        self.assertAlmostEqual(result["return"], .32)
        changed = [(when, 999999. if when > "2026-02-02" else price) for when, price in self.weekdays()]
        self.assertEqual(self.select(changed), result)

    def test_all_fixed_horizons_select_first_post_target_bar_not_window_tail(self):
        rows = [((self.START + timedelta(days=i)).isoformat(), 100. + i)
                for i in range(-7, 200) if (self.START + timedelta(days=i)).weekday() < 5]
        for days, expected_exit, expected_return in ((30, "2026-02-02", .32),
                                                     (91, "2026-04-02", .91),
                                                     (182, "2026-07-02", 1.82)):
            with self.subTest(horizon=days):
                result = self.select(rows, days=days)
                self.assertEqual(result["horizon_calendar_days"], days)
                self.assertEqual(result["exit_date"], expected_exit)
                self.assertAlmostEqual(result["return"], expected_return)
                changed = [(when, 999999. if when > expected_exit else price) for when, price in rows]
                self.assertEqual(self.select(changed, days=days), result)

    def test_prestart_prices_and_nontrading_entry_do_not_shift_nominal_horizon(self):
        start = date(2026, 1, 4)
        rows = [("2026-01-02", 999.), ("2026-01-05", 100.), ("2026-02-03", 130.), ("2026-02-04", 900.)]
        result = self.select(rows, start=start)
        self.assertEqual(result["entry_date"], "2026-01-05")
        self.assertEqual(result["target_date"], "2026-02-03")
        self.assertEqual(result["exit_date"], "2026-02-03")
        self.assertAlmostEqual(result["return"], .3)

    def test_immature_current_day_and_truncated_prices_are_unavailable(self):
        complete = [("2026-01-01", 100.), ("2026-01-31", 130.)]
        self.assertIsNone(self.select(complete, as_of=date(2026, 1, 31)))
        self.assertIsNone(self.select(complete, as_of=date(2026, 1, 30)))
        self.assertIsNone(self.select([(when, price) for when, price in self.weekdays() if when < "2026-01-31"]))
        self.assertIsNone(self.select([("2026-01-20", 100.), ("2026-02-02", 130.)]))

    def test_existing_padding_bounds_entry_and_exit_resolution(self):
        pad = SO.PRICE_RESOLUTION_PADDING_DAYS
        self.assertEqual(pad, 7)
        target = self.START + timedelta(days=30)
        accepted = [(self.START + timedelta(days=pad), 100.), (target + timedelta(days=pad), 120.)]
        self.assertIsNotNone(self.select(accepted))
        self.assertIsNone(self.select([(self.START + timedelta(days=pad+1), 100.), (target, 120.)]))
        self.assertIsNone(self.select([(self.START, 100.), (target + timedelta(days=pad+1), 120.)]))

    def test_invalid_dates_duplicate_dates_and_horizons_are_unavailable(self):
        rows = [("2026-01-01", 100.), ("2026-01-31", 120.)]
        for start in ("2026-01-01", datetime(2026, 1, 1), None):
            self.assertIsNone(SO.select_realized_observation(rows, start, 30, TODAY))
        for horizon in (0, -1, True, 1.5):
            self.assertIsNone(self.select(rows, days=horizon))
        for when in ("2026-02-30", "20260101", "2026-01-01T12:00:00", None):
            self.assertIsNone(self.select([(when, 100.), rows[1]]))
        self.assertIsNone(self.select(rows + [rows[1]]))
        self.assertIsNone(self.select(rows + [("2026-01-31", 999.)]))
        self.assertIsNone(self.select(rows, start=date(9999, 12, 31)))

    def test_invalid_as_of_is_not_replaced_by_current_date(self):
        rows = [("2026-01-01", 100.), ("2026-01-31", 120.)]
        for as_of in (False, 0, "", "2026-09-13", datetime(2026, 9, 13)):
            with self.subTest(as_of=as_of), \
                    mock.patch.object(Path, "is_file", side_effect=AssertionError("source read prohibited")):
                self.assertIsNone(self.select(rows, as_of=as_of))
                self.assertIsNone(SO.fetch_realized_observation("SYNTH", self.START, 30, False, as_of=as_of))

    def test_nontrading_target_waits_for_final_historical_close(self):
        rows = [("2026-01-01", 100.), ("2026-02-02", 130.), ("2026-02-03", 999.)]
        self.assertIsNone(self.select(rows, as_of=date(2026, 2, 2)))
        result = self.select(rows, as_of=date(2026, 2, 3))
        self.assertEqual(result["exit_date"], "2026-02-02")
        self.assertAlmostEqual(result["return"], .3)

    def test_bad_endpoint_cannot_be_skipped_for_a_later_good_price(self):
        for value in (None, 0., -1., float("nan"), float("inf"), True, "100"):
            with self.subTest(value=value):
                self.assertIsNone(self.select([("2026-01-01", value), ("2026-01-02", 100.), ("2026-01-31", 130.)]))
                self.assertIsNone(self.select([("2026-01-01", 100.), ("2026-01-31", value), ("2026-02-01", 130.)]))

    def test_factor_store_and_direct_provider_share_selector_and_never_mix_endpoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "synthetic.db"
            with contextlib.closing(sqlite3.connect(db)) as con:
                con.execute("CREATE TABLE bars(ticker TEXT,date TEXT,close REAL,src TEXT)")
                con.executemany("INSERT INTO bars VALUES('SYNTH',?,?,'yfinance')", self.weekdays())
                con.commit()
            original = db.read_bytes()
            with mock.patch.object(SO, "FACTOR_DB", db), \
                    mock.patch.object(SO, "yfinance_series", side_effect=AssertionError("network prohibited")):
                stored = SO.fetch_realized_observation("SYNTH", self.START, 30, False, as_of=TODAY)
            self.assertEqual(stored["source"], "factor-store")
            self.assertAlmostEqual(stored["return"], .32)
            self.assertEqual(db.read_bytes(), original)
            with mock.patch.object(SO, "FACTOR_DB", Path(tmp) / "absent.db"), \
                    mock.patch.object(SO, "yfinance_series", return_value=self.weekdays()) as provider:
                direct = SO.fetch_realized_observation("SYNTH", self.START, 30, False, as_of=TODAY)
            self.assertEqual(direct["entry_date"], stored["entry_date"])
            self.assertEqual(direct["exit_date"], stored["exit_date"])
            self.assertEqual(direct["return"], stored["return"])
            self.assertEqual(direct["price_basis"], stored["price_basis"])
            provider.assert_called_once_with("SYNTH", date(2025, 12, 25), date(2026, 2, 8))

    def test_truncated_store_falls_back_to_whole_provider_series(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "synthetic.db"
            with contextlib.closing(sqlite3.connect(db)) as con:
                con.execute("CREATE TABLE bars(ticker TEXT,date TEXT,close REAL,src TEXT)")
                con.execute("INSERT INTO bars VALUES('SYNTH','2026-01-01',9999.,'yfinance')")
                con.commit()
            with mock.patch.object(SO, "FACTOR_DB", db), mock.patch.object(SO, "yfinance_series", return_value=self.weekdays()):
                got = SO.fetch_realized_observation("SYNTH", self.START, 30, False, as_of=TODAY)
            self.assertEqual(got["source"], "yfinance-direct")
            self.assertEqual(got["entry_close"], 100.)
            self.assertAlmostEqual(got["return"], .32)

    def test_unknown_store_basis_is_not_relabeled_as_adjusted_prices(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "synthetic.db"
            with contextlib.closing(sqlite3.connect(db)) as con:
                con.execute("CREATE TABLE bars(ticker TEXT,date TEXT,close REAL,src TEXT)")
                con.executemany("INSERT INTO bars VALUES('SYNTH',?,?,'unknown-basis')", self.weekdays())
                con.commit()
            original = db.read_bytes()
            with mock.patch.object(SO, "FACTOR_DB", db), mock.patch.object(SO, "yfinance_series", return_value=[]) as provider:
                self.assertIsNone(SO.fetch_realized_observation("SYNTH", self.START, 30, False, as_of=TODAY))
            provider.assert_called_once()
            self.assertEqual(db.read_bytes(), original)

    def test_child_returns_dates_and_parent_selects_same_endpoints(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(SO, "FACTOR_DB", Path(tmp) / "absent.db"), \
                mock.patch.object(SO, "yfinance_series", side_effect=ImportError("synthetic absence")), \
                mock.patch.object(SO.os.path, "isfile", return_value=True), \
                mock.patch.object(SO.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=json.dumps(self.weekdays()))) as child:
            got = SO.fetch_realized_observation("SYNTH", self.START, 30, False, as_of=TODAY)
        self.assertAlmostEqual(got["return"], .32)
        self.assertEqual(got["source"], "yfinance-toolchain")
        self.assertEqual(child.call_args.args[0][2:], ["--provider-series", "SYNTH", "2025-12-25", "2026-02-08"])
        self.assertEqual(child.call_args.kwargs["timeout"], 30)

    def test_legacy_undated_child_output_and_provider_failure_are_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(SO, "FACTOR_DB", Path(tmp) / "absent.db"):
            with mock.patch.object(SO, "yfinance_series", side_effect=ImportError), \
                    mock.patch.object(SO, "toolchain_series", return_value=[100., 120., 2]):
                self.assertIsNone(SO.fetch_realized_return("SYNTH", self.START, 30, False, as_of=TODAY))
            with mock.patch.object(SO, "yfinance_series", side_effect=RuntimeError("synthetic provider failure")):
                self.assertIsNone(SO.fetch_realized_return("SYNTH", self.START, 30, False, as_of=TODAY))

    def test_ambiguous_identity_and_immaturity_refuse_before_source_access(self):
        with mock.patch.object(Path, "is_file", side_effect=AssertionError("source read prohibited")), \
                mock.patch.object(SO, "yfinance_series", side_effect=AssertionError("network prohibited")):
            self.assertIsNone(SO.fetch_realized_return("BTC", self.START, 30, False, as_of=TODAY))
            self.assertIsNone(SO.fetch_realized_return("SYNTH", self.START, 30, False, as_of=date(2026, 1, 31)))
            self.assertIsNone(SO.fetch_realized_return("SYNTH", "bad-date", 30, False, as_of=TODAY))

    def test_explicit_crypto_price_symbol_is_usable_without_guessing_bare_alias(self):
        rows = [("2026-01-01", 100.), ("2026-01-31", 130.)]
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(SO, "FACTOR_DB", Path(tmp) / "absent.db"), \
                mock.patch.object(SO, "yfinance_series", return_value=rows) as provider:
            result = SO.fetch_realized_observation("BTC-USD", self.START, 30, False, as_of=TODAY)
        self.assertEqual(result["price_symbol"], "BTC-USD")
        self.assertAlmostEqual(result["return"], .3)
        provider.assert_called_once_with("BTC-USD", date(2025, 12, 25), date(2026, 2, 8))

    def test_provider_helper_requests_primary_basis_and_preserves_missing_price(self):
        history_type = type("SyntheticHistory", (), {"empty": False,
            "__getitem__": lambda self, key: SimpleNamespace(items=lambda: [(datetime(2026, 1, 1), 100.), (datetime(2026, 1, 31), float("nan"))])})
        history_method = mock.Mock(return_value=history_type())
        provider = SimpleNamespace(Ticker=lambda ticker: SimpleNamespace(history=history_method))
        with mock.patch.dict(sys.modules, {"yfinance": provider}):
            got = SO.yfinance_series("SYNTH", self.START, date(2026, 2, 8))
        self.assertEqual(got, [("2026-01-01", 100.), ("2026-01-31", None)])
        self.assertTrue(history_method.call_args.kwargs["auto_adjust"])
        self.assertTrue(history_method.call_args.kwargs["keepna"])
        self.assertTrue(history_method.call_args.kwargs["raise_errors"])
        self.assertEqual(history_method.call_args.kwargs["timeout"], 15)

    def test_missing_outcomes_leave_blanks_and_dry_run_preserves_lines(self):
        text = ("## Call Log\r\n| date | ticker | new_rating | shadow_rating | ret_1mo | ret_3mo | ret_6mo |\r\n"
                "|---|---|---|---|---|---|---|\r\n| 2020-01-01 | SYNTH | BUY | BUY | | +2.0% | |\r\n")
        lines, hi, si, cols, rows = SO.parse_monitor(text)
        unavailable = []
        with mock.patch.object(SO, "fetch_realized_observation", return_value=None):
            self.assertEqual(SO.backfill(lines, cols, rows, TODAY, False, False, unavailable), [])
        self.assertEqual("".join(lines), text)
        self.assertEqual(len(unavailable), 2)
        self.assertNotIn("N/A", "".join(lines))
        with mock.patch.object(SO, "fetch_realized_observation", return_value={"return": .1}):
            changes = SO.backfill(lines, cols, rows, TODAY, True, False)
        self.assertEqual(len(changes), 1)
        self.assertEqual("".join(lines), text)

    def test_synthetic_backfill_write_preserves_existing_rows_cells_and_crlf(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic-monitor.md"
            preserved = "| 2019-01-01 | OLD | BUY | BUY | +1.0% | +2.0% | +3.0% |\r\n"
            original = ("Preserved preface\r\n## Call Log\r\n"
                        "| date | ticker | new_rating | shadow_rating | ret_1mo | ret_3mo | ret_6mo |\r\n"
                        "|---|---|---|---|---|---|---|\r\n" + preserved +
                        "| 2020-01-01 | SYNTH | BUY | UNAVAILABLE | | +5.0% | |\r\nPreserved footer\r\n").encode("ascii")
            path.write_bytes(original)
            def observation(ticker, start, days, verbose, **kwargs):
                return {"return": .1, "source": "synthetic"} if days == 182 else None
            output = io.StringIO()
            with mock.patch.object(SO, "fetch_realized_observation", side_effect=observation), \
                    mock.patch.object(sys, "argv", ["score-outcomes.py", "--monitor", str(path), "--json"]), \
                    contextlib.redirect_stdout(output):
                self.assertEqual(SO.main(), 0)
            expected = original.replace(b"| | +5.0% | |", b"| | +5.0% | +10.0% |")
            self.assertEqual(path.read_bytes(), expected)
            self.assertEqual(len(json.loads(output.getvalue())["unavailable_outcomes"]), 1)

    def test_atomic_write_retains_original_on_failure_or_detected_concurrent_edit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic-monitor.md"
            path.write_bytes(b"original\r\n")
            with mock.patch.object(SO.os, "replace", side_effect=OSError("synthetic interruption")):
                with self.assertRaises(OSError): SO.write_monitor(path, "replacement\r\n", b"original\r\n")
            self.assertEqual(path.read_bytes(), b"original\r\n")
            self.assertEqual(list(Path(tmp).glob(".score-outcomes-*.tmp")), [])
            path.write_bytes(b"concurrent user edit\r\n")
            with self.assertRaises(ValueError): SO.write_monitor(path, "replacement\r\n", b"original\r\n")
            self.assertEqual(path.read_bytes(), b"concurrent user edit\r\n")


class ConfidenceAdvisoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.map = self.root / "synthetic-map.json"
        self.context = {"win_key": "beats_synthetic_index", "horizon": 21,
                        "cohort": "synthetic-independent-controls-v1", "method": "empirical-bayes-bin-shrinkage"}
        self.payload = {**self.context, "generated": TODAY.isoformat(), "source": "synthetic://fixture/calibration",
                        "n": 12, "limitations": ["Synthetic fixture; no demonstrated investment reliability."],
                        "bins": [{"lo": 60, "hi": 69, "n": 12, "realized": .5, "calibrated": .5}]}

    def write_map(self, payload=None):
        self.map.write_text(json.dumps(self.payload if payload is None else payload), encoding="utf-8")

    def advisory(self, stated=65, context=None):
        return KA.confidence_advisory(stated, self.map, self.context if context is None else context, today=TODAY)

    def test_qualified_mapping_retains_scope_support_and_limitations(self):
        self.write_map()
        result = self.advisory()
        self.assertEqual(result["status"], "available")
        self.assertEqual(result["calibrated"], .5)
        self.assertEqual((result["map_n"], result["bin_n"], result["horizon_days"]), (12, 12, 21))
        self.assertEqual(result["target_event"], self.context["win_key"])
        self.assertEqual(result["limitations"], self.payload["limitations"])
        self.assertIn("not independently validated", result["validation_scope"])

    def test_unavailable_stated_value_never_reads_map(self):
        with mock.patch.object(Path, "read_text", side_effect=AssertionError("unexpected map read")):
            self.assertEqual(self.advisory(None)["reason"], "stated_confidence_unavailable")

    def test_invalid_stated_values_are_rejected_without_clamping(self):
        for value in (-1, 101, float("nan"), float("inf"), -float("inf"), True):
            with self.subTest(value=value):
                result = self.advisory(value)
                self.assertEqual(result["reason"], "invalid_stated_confidence")
                self.assertIsNone(result["stated"])
                self.assertIsNone(result["calibrated"])
                json.dumps(result, allow_nan=False)

    def test_missing_caller_context_is_explicit(self):
        self.write_map()
        self.assertEqual(self.advisory(context={})["reason"], "applicability_context_unavailable")

    def test_legacy_map_without_qualified_metadata_remains_unavailable(self):
        for key in ("cohort", "method", "limitations", "win_key", "horizon", "source", "n"):
            with self.subTest(key=key):
                payload = copy.deepcopy(self.payload)
                del payload[key]
                self.write_map(payload)
                self.assertEqual(self.advisory()["reason"], "map_qualification_unavailable")

    def test_context_mismatch_cannot_join_different_outcome_or_population(self):
        self.write_map()
        for key, value in (("win_key", "absolute_return_positive"), ("horizon", 63),
                           ("cohort", "another-population"), ("method", "another-method")):
            with self.subTest(key=key):
                self.assertEqual(self.advisory(context={**self.context, key: value})["reason"], "map_not_applicable")

    def test_freshness_boundaries_and_future_dates(self):
        for age, expected in ((44, None), (45, "map_stale"), (-1, "map_future_dated")):
            with self.subTest(age=age):
                self.write_map({**self.payload, "generated": (TODAY - timedelta(days=age)).isoformat()})
                self.assertEqual(self.advisory()["reason"], expected)

    def test_absent_and_malformed_maps_are_explicit(self):
        self.assertEqual(self.advisory()["reason"], "map_absent")
        self.map.write_text("{broken", encoding="utf-8")
        self.assertEqual(self.advisory()["reason"], "map_unreadable_or_malformed")
        self.write_map([])
        self.assertEqual(self.advisory()["reason"], "invalid_map_metadata")

    def test_unknown_bin_is_not_filled_with_stated_value_or_endpoint(self):
        self.write_map()
        for value in (0, 69.5, 100):
            with self.subTest(value=value):
                result = self.advisory(value)
                self.assertEqual(result["reason"], "no_supported_bin")
                self.assertIsNone(result["calibrated"])

    def test_invalid_bin_values_never_serialize_as_confidence(self):
        for key, value in (("calibrated", float("nan")), ("calibrated", 1.1), ("lo", 10 ** 400), ("n", 0),
                           ("n", 13), ("lo", -1), ("hi", 101), ("realized", None)):
            with self.subTest(key=key, value=value):
                payload = copy.deepcopy(self.payload)
                payload["bins"][0][key] = value
                self.write_map(payload)
                result = self.advisory()
                self.assertEqual(result["reason"], "invalid_map_bins")
                json.dumps(result, allow_nan=False)

    def test_overlapping_or_inconsistent_bin_populations_are_unavailable(self):
        payload = copy.deepcopy(self.payload)
        payload["bins"].append({"lo": 69, "hi": 79, "n": 12, "realized": .5, "calibrated": .5})
        payload["n"] = 24
        self.write_map(payload)
        self.assertEqual(self.advisory()["reason"], "inconsistent_map_bins")
        payload["bins"].pop()
        self.write_map(payload)
        self.assertEqual(self.advisory()["reason"], "inconsistent_map_bins")

    def test_missing_alpha_amount_and_count_remain_unknown(self):
        source = self.root / "synthetic-attribution.md"
        source.write_text("Doctrine selection alpha: $-12.50\n", encoding="utf-8")
        self.assertEqual(KA.parse_alpha(source), {"alpha": -12.5, "deployed": None, "n": None})

    def test_malformed_count_does_not_suppress_parseable_attribution(self):
        source = self.root / "synthetic-attribution.md"
        source.write_text("Doctrine selection alpha: $-12.50\nActions WITH capital deployed: " + "9" * 5000, encoding="utf-8")
        self.assertEqual(KA.parse_alpha(source), {"alpha": -12.5, "deployed": None, "n": None})

    def run_main(self, source_text, map_text, stated="65"):
        report_dir = self.root / "wiki/maintenance/calibration"
        report_dir.mkdir(parents=True, exist_ok=True)
        source = report_dir / "decision-attribution.md"
        source.write_text(source_text, encoding="utf-8")
        map_file = report_dir / "confidence-map.json"
        map_file.write_text(map_text, encoding="utf-8")
        before = {path: path.read_bytes() for path in (source, map_file)}
        argv = ["kernel-alpha-note.py", "--stated", stated, "--target-event", self.context["win_key"],
                "--horizon-days", "21", "--cohort", self.context["cohort"],
                "--calibration-method", self.context["method"]]
        output = io.StringIO()
        with mock.patch.object(KA, "ROOT", self.root), mock.patch.object(KA, "SRC", source), \
                mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(output):
            self.assertEqual(KA.main(), 0)
        self.assertEqual({path: path.read_bytes() for path in before}, before)
        return json.loads(output.getvalue())

    def test_malformed_map_preserves_separate_attribution_and_source_bytes(self):
        result = self.run_main("Doctrine selection alpha: $-12.50\nActions WITH capital deployed: 12\n"
                               "totaling $1,000\n", "{broken")
        self.assertEqual(result["attribution_status"], "available")
        self.assertEqual((result["alpha"], result["deployed"], result["n"]), (-12.5, 1000, 12))
        self.assertEqual(result["confidence_advisory"]["reason"], "map_unreadable_or_malformed")
        self.assertIsNone(result["calibrated_confidence"])

    def test_partial_attribution_survives_invalid_stated_confidence(self):
        result = self.run_main("Doctrine selection alpha: $-12.50\n", "{broken", stated="nan")
        self.assertEqual(result["attribution_status"], "partial")
        self.assertIsNone(result["n"])
        self.assertIsNone(result["deployed"])
        self.assertIn("deployed amount unavailable", result["advisory"])
        self.assertEqual(result["confidence_advisory"]["reason"], "invalid_stated_confidence")


if __name__ == "__main__":
    unittest.main(verbosity=2)

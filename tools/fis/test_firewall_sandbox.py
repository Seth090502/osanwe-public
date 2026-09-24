#!/usr/bin/env python3
"""Synthetic-only legacy-firewall regression tests. Never open persisted data."""
import csv
import importlib.util
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch


def load_firewall():
    spec = importlib.util.spec_from_file_location("sandbox_firewall", Path(__file__).with_name("firewall.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SyntheticFirewallTests(unittest.TestCase):
    def setUp(self):
        self.fw = load_firewall()
        self.temp = tempfile.TemporaryDirectory(prefix="fis-firewall-regression-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def configured(self):
        self.fw.configure_synthetic_sandbox(self.root, ["fixture-family"])
        self.fw.build_challenge_db([("SYN%02d" % i, "2024-01-01", 0.01) for i in range(25)], [])
        return self.write_submission([("SYN%02d" % i, "2024-01-01", 1.0) for i in range(25)])

    def write_submission(self, rows):
        path = self.root / "submission.csv"
        with path.open("w", newline="", encoding="ascii") as handle:
            writer = csv.writer(handle)
            writer.writerow(["instrument", "date", "score"])
            writer.writerows(rows)
        return str(path)

    def test_unconfigured_producers_and_consumers_refuse_before_io(self):
        fw = self.fw
        calls = [lambda: fw.init_keyfile(), lambda: fw.rotate_key(),
                 lambda: fw.build_challenge_db([], []),
                 lambda: fw.evaluate_submission("not-opened", "fixture-family"),
                 lambda: fw.parse_submission("not-opened"),
                 lambda: fw.log_event("probe", {}, True), lambda: fw.verify_log_integrity(),
                 lambda: fw.budget_status("fixture-family"),
                 lambda: fw.evaluator_override("fixture-family", "no"),
                 lambda: fw._open_challenge(), lambda: fw._load_secret(),
                 lambda: fw._read_budget(), lambda: fw._write_budget({}),
                 lambda: fw._overwrite_bytes("not-opened"),
                 lambda: fw._harden_keyfile("not-opened")]
        with patch("builtins.open", side_effect=AssertionError("unexpected file read")), patch.object(fw.os, "makedirs", side_effect=AssertionError("unexpected mutation")):
            for call in calls:
                with self.assertRaises(fw.FirewallError):
                    call()

    def test_only_fresh_empty_temporary_roots_can_be_configured(self):
        (self.root / "already-present").write_text("SYNTHETIC", encoding="ascii")
        with self.assertRaises(self.fw.FirewallError):
            self.fw.configure_synthetic_sandbox(self.root, ["fixture-family"])
        with self.assertRaises(self.fw.FirewallError):
            self.fw.configure_synthetic_sandbox(Path(__file__).parent, ["fixture-family"])

    def test_duplicate_rows_cannot_bypass_small_n_suppression(self):
        self.configured()
        sub = self.write_submission([("SYN00", "2024-01-01", 1)] * 25)
        with self.assertRaises(self.fw.FirewallError):
            self.fw.evaluate_submission(sub, "fixture-family")
        self.assertEqual(self.fw.budget_status("fixture-family")["used"], 0)
        self.assertIn('"evaluate_refused"', Path(self.fw.ACCESS_LOG).read_text(encoding="ascii"))

    def test_nonfinite_prediction_refuses(self):
        self.configured()
        sub = self.write_submission([("SYN00", "2024-01-01", "nan")])
        with self.assertRaises(self.fw.FirewallError):
            self.fw.evaluate_submission(sub, "fixture-family")

    def test_unknown_family_and_public_budget_escapes_refuse(self):
        sub = self.configured()
        with patch.object(self.fw, "_open_challenge", side_effect=AssertionError("must not open challenge")):
            for family, override in [("new-family", False), ("fixture-family", True)]:
                with self.assertRaises(self.fw.FirewallError):
                    self.fw.evaluate_submission(sub, family, allow_over_budget=override)
            with self.assertRaises(self.fw.FirewallError):
                self.fw.evaluator_override("fixture-family", "arbitrary caller supplied override reason")
        self.assertEqual(self.fw.budget_status("fixture-family")["used"], 0)

    def test_full_valid_budget_snapshot_replay_is_detected(self):
        sub = self.configured()
        self.fw.evaluate_submission(sub, "fixture-family")
        old = Path(self.fw.BUDGET_FILE).read_bytes()
        self.fw.evaluate_submission(sub, "fixture-family")
        Path(self.fw.BUDGET_FILE).write_bytes(old)
        with self.assertRaises(self.fw.TamperDetected):
            self.fw.budget_status("fixture-family")

    def test_missing_budget_does_not_reset_query_count(self):
        sub = self.configured()
        self.fw.evaluate_submission(sub, "fixture-family")
        Path(self.fw.BUDGET_FILE).unlink()
        with self.assertRaises(self.fw.TamperDetected):
            self.fw.budget_status("fixture-family")

    def test_missing_audit_evidence_fails_closed(self):
        sub = self.configured()
        self.fw.evaluate_submission(sub, "fixture-family")
        Path(self.fw.ACCESS_LOG).write_text("", encoding="ascii")
        with self.assertRaises(self.fw.TamperDetected):
            self.fw.budget_status("fixture-family")

    def test_unowned_lock_is_not_stolen(self):
        sub = self.configured()
        lock = self.root / ".gateway.lock"
        lock.write_text("another operation", encoding="ascii")
        with self.assertRaises(self.fw.FirewallError):
            self.fw.evaluate_submission(sub, "fixture-family")
        self.assertTrue(lock.exists())

    def test_concurrent_attempt_cannot_enter_budget_and_decrypt_section(self):
        sub = self.configured()
        entered, release = threading.Event(), threading.Event()
        original = self.fw._open_challenge
        failures = []
        def held(*args, **kwargs):
            entered.set()
            if not release.wait(5):
                raise AssertionError("test synchronization timeout")
            return original(*args, **kwargs)
        def request():
            try:
                self.fw.evaluate_submission(sub, "fixture-family")
            except Exception as exc:
                failures.append(exc)
        with patch.object(self.fw, "_open_challenge", held):
            thread = threading.Thread(target=request)
            thread.start()
            try:
                self.assertTrue(entered.wait(5))
                with self.assertRaises(self.fw.FirewallError):
                    self.fw.evaluate_submission(sub, "fixture-family")
            finally:
                release.set()
                thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(failures, [])
        self.assertEqual(self.fw.budget_status("fixture-family")["used"], 1)

    def test_submission_cannot_escape_fixture_root(self):
        self.configured()
        with self.assertRaises(self.fw.FirewallError):
            self.fw.parse_submission(str(Path(__file__)))
        with self.assertRaises(self.fw.FirewallError):
            self.fw._overwrite_bytes(str(Path(__file__)))


if __name__ == "__main__":
    unittest.main()

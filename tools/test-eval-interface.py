#!/usr/bin/env python3
"""Gateway control tests using temporary metadata and mocked aggregates only.

No locked/golden data, model endpoint, or repository audit log is accessed.
"""

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("eval_gateway", ROOT / "tools/eval-interface.py")
gateway = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gateway)


class GatewayControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.log = self.root / "evaluation_log.jsonl"
        self.ledger = self.root / "experiment_ledger.jsonl"
        self.log.write_text("", encoding="utf-8")
        self.ledger.write_text("", encoding="utf-8")
        self.paths = patch.multiple(gateway, LOG_PATH=str(self.log), LEDGER_PATH=str(self.ledger))
        self.paths.start()
        self.args = argparse.Namespace(model_id="test-only", agent_id="test-agent",
                                       hypothesis_id="hypothesis", holdout="NEVER_OPEN")

    def tearDown(self):
        self.paths.stop()
        self.temp.cleanup()

    def records(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_blank_legacy_ids_cannot_escape_counting(self):
        self.log.write_text(''.join(json.dumps({"hypothesis_id": value}) + "\n"
                                    for value in ["", "(none)", "  ", None, "(none)"]))
        self.assertEqual(gateway.count_queries(""), 5)
        self.assertEqual(gateway.count_queries("  "), 5)

    def test_blank_request_is_refused_and_logged(self):
        self.args.hypothesis_id = "  "
        result, code = gateway.run_request(self.args)
        self.assertEqual((code, result["error"]), (2, "hypothesis_required"))
        self.assertEqual(self.records()[0]["hypothesis_id"], "(none)")
        self.assertFalse(self.records()[0]["budget_consumed"])

    def test_registry_requires_current_preregistration(self):
        for statuses, expected in [(["rejected"], False), (["preregistered"], True),
                                   (["preregistered", "rejected"], False),
                                   (["rejected", "preregistered"], True)]:
            self.ledger.write_text(''.join(json.dumps({"hypothesis_id": "hypothesis", "status": s})
                                            + "\n" for s in statuses))
            self.assertEqual(gateway.is_registered("hypothesis"), expected)

    def test_no_backend_never_opens_holdout_or_calls_research_callback(self):
        with patch("builtins.open", side_effect=AssertionError("holdout must stay locked")), \
                patch("builtins.print"):
            with self.assertRaises(gateway.EvaluationRefused) as caught:
                gateway.evaluate("arbitrary-model", "NEVER_OPEN",
                                 lambda record: self.fail("callback invoked"))
        self.assertEqual(caught.exception.code, "backend_unavailable")

    def test_backend_refusal_has_no_metrics_and_is_audited(self):
        result, code = gateway.run_request(self.args)
        self.assertEqual((code, result["error"]), (2, "backend_unavailable"))
        self.assertNotIn("metrics", result)
        self.assertEqual(self.records()[0]["outcome"], "backend_unavailable")
        self.assertEqual(gateway.count_queries("hypothesis"), 0)

    def test_caps_precede_any_evaluation_and_cannot_be_reopened_by_rejection(self):
        for registered, cap in [(False, 3), (True, 5)]:
            self.log.write_text("")
            self.ledger.write_text(json.dumps({"hypothesis_id": "hypothesis",
                                               "status": "preregistered" if registered else "rejected"}))
            with patch.object(gateway, "evaluate", return_value={"synthetic_test_score": 1}) as fake:
                for _ in range(cap):
                    self.assertEqual(gateway.run_request(self.args)[1], 0)
                result, code = gateway.run_request(self.args)
                self.assertEqual((code, result["error"]), (2, "query_limit_exceeded"))
                self.assertEqual(fake.call_count, cap)
            self.assertEqual(gateway.count_queries("hypothesis"), cap)
            self.assertEqual(self.records()[-1]["outcome"], "query_limit_exceeded")

    def test_malformed_audit_or_ledger_fails_closed(self):
        for target in (self.log, self.ledger):
            self.log.write_text("")
            self.ledger.write_text("")
            target.write_text("{torn\n")
            with patch.object(gateway, "evaluate", side_effect=AssertionError("must refuse first")):
                result, code = gateway.run_request(self.args)
            self.assertEqual((code, result["error"]), (2, "audit_state_invalid"))

    def test_busy_lock_fails_closed_without_stealing_or_evaluating(self):
        lock = Path(str(self.log) + ".lock")
        lock.touch()
        with patch.object(gateway, "evaluate", side_effect=AssertionError("must refuse first")):
            result, code = gateway.run_request(self.args)
        self.assertEqual((code, result["error"]), (2, "gateway_busy"))
        self.assertTrue(lock.exists())
        self.assertFalse(result["audit_logged"])

    def test_failed_audit_never_releases_metrics(self):
        with patch.object(gateway, "evaluate", return_value={"synthetic_test_score": 1}), \
                patch.object(gateway, "log_query", side_effect=OSError("disk full")):
            result, code = gateway.run_request(self.args)
        self.assertEqual((code, result["error"]), (2, "audit_unavailable"))
        self.assertNotIn("metrics", result)

    def test_wrapper_dispatch_and_exit_status_in_temporary_workspace(self):
        for folder in ("tools", "evaluation", "registry"):
            (self.root / folder).mkdir()
        shutil.copy2(ROOT / "tools/eval-interface.py", self.root / "tools/eval-interface.py")
        shutil.copy2(ROOT / "evaluation/request_access.py", self.root / "evaluation/request_access.py")
        (self.root / "evaluation/evaluation_log.jsonl").write_text("")
        wrapper = self.root / "evaluation/request_access.py"
        help_result = subprocess.run([sys.executable, str(wrapper), "--help"],
                                     capture_output=True, text=True)
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("evaluator not connected", help_result.stdout)
        result = subprocess.run([sys.executable, str(wrapper), "--model-id", "test-model",
                                 "--agent-id", "test-agent", "--hypothesis-id", "test-hypothesis"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["error"], "backend_unavailable")
        self.assertIn("backend_unavailable", (self.root / "evaluation/evaluation_log.jsonl").read_text())


if __name__ == "__main__":
    unittest.main(verbosity=2)

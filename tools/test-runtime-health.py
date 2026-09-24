#!/usr/bin/env python3
"""Runtime negative controls; all files/processes use synthetic temporary data."""
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from fis.runtime_health import (Journal, OverlapError, artifact_state, bounded_process,
    create_json, job_lock, opportunities, readiness, reconcile_inventory, iso_z, UTC, validation_outcome, completion_marker, process_exists,
    scheduled_sources, file_sha)

ROOT = Path(__file__).resolve().parent.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.at = dt.datetime(2026, 9, 12, 12, 0, tzinfo=UTC)
        self.journal = Journal(self.root)

    def tearDown(self):
        self.journal.close()
        self.temp.cleanup()

    def test_missed_slots_preserved_only_latest_is_due(self):
        self.journal.reconcile("job", self.at)
        latest = self.journal.reconcile("job", self.at + dt.timedelta(days=5))
        rows = self.journal.db.execute("SELECT status FROM opportunities").fetchall()
        self.assertEqual([r[0] for r in rows].count("due"), 1)
        self.assertEqual([r[0] for r in rows].count("missed"), 5)
        run = self.journal.begin("job", latest, self.at + dt.timedelta(days=5))
        self.assertIsNotNone(run)
        self.assertIsNone(self.journal.begin("job", latest, self.at + dt.timedelta(days=5)))

    def test_interrupted_owner_is_failure_not_replayed_pass(self):
        slot = self.journal.reconcile("job", self.at)
        run = self.journal.begin("job", slot, self.at)
        self.journal.reconcile("job", self.at + dt.timedelta(minutes=2))
        row = self.journal.db.execute("SELECT status FROM opportunities").fetchone()
        self.assertEqual(row[0], "failed")
        self.assertIsNone(self.journal.begin("job", slot, self.at))
        with self.assertRaises(ValueError):
            self.journal.finish(run, self.at, "passed", "receipt.json")

    def test_interval_recovery_preserves_killed_and_missed_polls(self):
        first = self.journal.reconcile_interval("index", self.at)
        run = self.journal.begin("index", first, self.at)
        last = self.journal.reconcile_interval("index", self.at + dt.timedelta(minutes=10))
        rows = self.journal.db.execute("SELECT status FROM opportunities ORDER BY slot").fetchall()
        self.assertEqual([r[0] for r in rows], ["failed", "missed", "missed", "missed", "missed", "due"])
        self.assertIsNone(self.journal.begin("index", first, self.at))
        current = self.journal.begin("index", last, self.at + dt.timedelta(minutes=10))
        self.assertIsNotNone(current)
        self.journal.finish(current, self.at + dt.timedelta(minutes=11), "passed", "synthetic-current-only")
        with self.assertRaises(ValueError):
            self.journal.reconcile_interval("index", self.at)

    def test_long_offline_gap_preserves_counted_history_and_one_current_catchup(self):
        first = self.journal.reconcile_interval("index", self.at)
        run = self.journal.begin("index", first, self.at)
        self.journal.finish(run, self.at, "passed", "synthetic-first")
        current = self.journal.reconcile_interval("index", self.at + dt.timedelta(days=90))
        summary = self.journal.summary("index", self.at + dt.timedelta(days=90))
        self.assertEqual(summary["counts"]["due"], 1)
        self.assertEqual(summary["counts"]["missed"], 21600)
        archived = json.loads(self.journal.db.execute("SELECT detail FROM events WHERE event='missed_interval_range'").fetchone()[0])
        self.assertEqual(archived["count"], 60 * 720 - 1)
        self.assertEqual(archived["first_slot"], iso_z(self.at + dt.timedelta(minutes=2)))
        self.assertEqual(archived["last_slot"], iso_z(self.at + dt.timedelta(days=60, minutes=-2)))
        self.assertEqual(archived["count"] + summary["counts"]["missed"] + 1, 90 * 720)
        catchup = self.journal.begin("index", current, self.at + dt.timedelta(days=90))
        self.assertIsNotNone(catchup)
        self.journal.finish(catchup, self.at + dt.timedelta(days=90), "passed", "synthetic-current")
        repeated = self.journal.reconcile_interval("index", self.at + dt.timedelta(days=90, minutes=1))
        self.assertEqual(repeated, current)
        self.assertIsNone(self.journal.begin("index", repeated, self.at + dt.timedelta(days=90, minutes=1)))
        self.assertEqual(self.journal.db.execute("SELECT count(*) FROM events WHERE event='missed_interval_range'").fetchone()[0], 1)

    def test_overlap_os_lock(self):
        with job_lock(self.root / "job.lock"):
            with self.assertRaises(OverlapError):
                with job_lock(self.root / "job.lock"):
                    pass
        with job_lock(self.root / "job.lock"):
            pass

    def test_killed_process_releases_lock(self):
        path = self.root / "held.lock"
        marker = self.root / "ready"
        code = "from fis.runtime_health import job_lock;from pathlib import Path;import time;\nwith job_lock(%r):\n Path(%r).write_text('ready');time.sleep(30)" % (str(path), str(marker))
        env = dict(os.environ, PYTHONPATH=str(ROOT / "tools"))
        process = subprocess.Popen([sys.executable, "-c", code], env=env,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            import time
            for _ in range(100):
                if marker.exists():
                    break
                time.sleep(.02)
            self.assertTrue(marker.exists())
            with self.assertRaises(OverlapError):
                with job_lock(path):
                    pass
        finally:
            process.kill()
            process.wait(timeout=5)
        with job_lock(path):
            pass

    def test_timeout_is_failure_and_no_child_output_is_logged(self):
        result = bounded_process([sys.executable, "-c", "import time;print('SYNTHETIC_PRIVACY_CANARY_900');time.sleep(10)"], self.root, .1)
        self.assertEqual(result["reason"], "timeout")
        self.assertNotIn("SYNTHETIC_PRIVACY_CANARY_900", json.dumps(result))

    def test_exit_zero_without_fresh_artifact_fails(self):
        result = bounded_process([sys.executable, "-c", "pass"], self.root, 5)
        self.assertEqual(result["state"], "passed")
        self.assertEqual(artifact_state(self.root / "missing.json", self.at)["state"], "failed")
        old = self.root / "old.json"
        old.write_text("{}")
        os.utime(old, (self.at.timestamp() - 50, self.at.timestamp() - 50))
        self.assertEqual(artifact_state(old, self.at)["state"], "stale")

    def test_malformed_or_unavailable_artifact_cannot_pass(self):
        path = self.root / "bad.json"
        path.write_text('{"schema":"osanwe.validation/1","state":"unavailable"}')
        self.assertEqual(artifact_state(path, self.at, json_schema="osanwe.validation/1")["state"], "failed")

    def test_fresh_scorer_header_or_malformed_tail_cannot_claim_completion(self):
        path = self.root / "scorer.log"
        valid = "Rollback: realized_at_3mo=8 armed=True gap=-0.031 fired=False\n"
        path.write_text(valid)
        self.assertEqual(completion_marker(path, "score-outcomes-summary/1")["state"], "passed")
        path.write_text(valid + "=== scorer run new time ===\n")
        self.assertEqual(completion_marker(path, "score-outcomes-summary/1")["state"], "failed")
        path.write_text("SYNTHETIC_PRIVACY_CANARY_123\n" + valid.replace("-0.031", "nan"))
        result = completion_marker(path, "score-outcomes-summary/1")
        self.assertEqual(result["state"], "failed")
        self.assertNotIn("SYNTHETIC_PRIVACY_CANARY", json.dumps(result))
        path.write_text(valid.replace("-0.031", "None"))
        self.assertEqual(completion_marker(path, "score-outcomes-summary/1")["state"], "passed")

    def test_validation_staleness_is_distinct_from_computation_failure(self):
        path = self.root / "result.json"
        path.write_text(json.dumps({"schema": "osanwe.validation/1", "state": "stale"}))
        completed = {"state": "failed", "exit_code": 1, "reason": "process_nonzero"}
        self.assertEqual(validation_outcome(completed, path, self.at)["state"], "stale")
        self.assertEqual(validation_outcome({**completed, "exit_code": 0}, path, self.at)["state"], "failed")
        self.assertEqual(validation_outcome({**completed, "reason": "timeout"}, path, self.at)["reason"], "validation-computation-timeout")
        path.write_text(json.dumps({"schema": "osanwe.validation/1", "state": "unavailable"}))
        self.assertEqual(validation_outcome({**completed, "exit_code": 2}, path, self.at)["state"], "unavailable")
        path.write_text("broken")
        self.assertEqual(artifact_state(path, self.at, json_schema="osanwe.validation/1")["state"], "failed")

    def test_deduplicated_incident_one_recovery_and_delivery_separate(self):
        first = self.journal.incident("job", "stale-output", True, self.at)
        self.assertEqual(first["notification"], "not_attempted")
        self.assertIsNone(self.journal.incident("job", "stale-output", True, self.at))
        self.journal.notice(first["incident"], "failed", self.at)
        with self.assertRaises(ValueError):
            self.journal.notice(first["incident"], "confirmed", self.at)
        recovery = self.journal.incident("job", "stale-output", False, self.at)
        self.assertEqual(recovery["transition"], "recovered")
        self.assertIsNone(self.journal.incident("job", "stale-output", False, self.at))
        self.assertEqual(self.journal.db.execute("SELECT outcome FROM notices").fetchone()[0], "failed")

    def test_manual_runs_never_count_as_scheduled_pilot(self):
        for n in range(8):
            run = self.journal.begin("job", None, self.at + dt.timedelta(days=n), "manual")
            self.journal.finish(run, self.at, "passed", "synthetic-receipt")
        report = self.journal.summary("job", self.at + dt.timedelta(days=8))
        self.assertEqual(report["scheduled_opportunities"], 0)
        self.assertEqual(report["seven_cycle_pilot"], "pending")

    def test_registered_manual_probe_correction_preserves_original_row(self):
        slot = self.journal.reconcile("job", self.at)
        run = self.journal.begin("job", slot, self.at)
        self.journal.finish(run, self.at, "passed", "synthetic-probe")
        self.journal.classify_manual_trigger(run["run_id"], self.at)
        self.journal.classify_manual_trigger(run["run_id"], self.at)
        row = self.journal.db.execute("SELECT kind,status FROM opportunities").fetchone()
        self.assertEqual(tuple(row), ("scheduled", "passed"))
        summary = self.journal.summary("job", self.at)
        self.assertEqual(summary["scheduled_opportunities"], 0)
        self.assertEqual(summary["manual_trigger_corrections"], 1)
        self.assertEqual(self.journal.db.execute("SELECT count(*) FROM events WHERE event='manual_trigger_classified'").fetchone()[0], 1)

    def test_seven_cycle_pilot_requires_real_rows_and_sunday(self):
        for n in range(7):
            at = self.at + dt.timedelta(days=n)
            slot = self.journal.reconcile("job", at)
            run = self.journal.begin("job", slot, at)
            self.journal.finish(run, at + dt.timedelta(minutes=2), "passed", "synthetic-test-only")
        summary = self.journal.summary("job", at)
        self.assertEqual(summary["timely_completions"], 7)
        self.assertEqual(summary["seven_cycle_pilot"], "observed")
        # These fixtures only test the counter; they are not production evidence.

    def test_readiness_expires_and_clock_reversal_refuses(self):
        receipt = {"state": "passed", "verified_at": iso_z(self.at)}
        self.assertEqual(readiness(receipt, self.at + dt.timedelta(days=2)), "host-unobserved")
        self.assertEqual(readiness(receipt, self.at - dt.timedelta(seconds=1)), "unavailable")
        with self.assertRaises(ValueError):
            opportunities(self.at, self.at - dt.timedelta(days=1))

    def test_dst_uses_one_eight_am_slot_per_local_day(self):
        start = dt.datetime(2026, 10, 31, 0, tzinfo=UTC)
        end = dt.datetime(2026, 11, 2, 23, tzinfo=UTC)
        slots = opportunities(start, end)
        self.assertEqual([x.hour for x in slots], [12, 13, 13])
        self.assertEqual(len(slots), 3)

    def test_duplicate_manifest_and_unknown_tasks(self):
        manifest = {"jobs": [{"name": "job"}, {"name": "job"}]}
        observed = {"state": "passed", "tasks": [{"name": "unknown"}]}
        codes = {r["code"] for r in reconcile_inventory(manifest, observed, self.root)}
        self.assertEqual(codes, {"duplicate-manifest-jobs", "unmanifested-task"})

    def test_dated_receipt_cannot_be_overwritten(self):
        path = self.root / "receipt.json"
        create_json(path, {"state": "failed"})
        with self.assertRaises(FileExistsError):
            create_json(path, {"state": "passed"})

    def test_fresh_success_receipt_cannot_certify_changed_code_or_expand_reads(self):
        name = "osanwe-nightly-health"
        for source in scheduled_sources(name):
            path = self.root / source
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("synthetic original source")
        receipt = {"schema": "osanwe.scheduled-job/1", "state": "passed", "attempt": {"job": name},
                   "code_unchanged_during_run": True, "executable_sha256": "synthetic-exe",
                   "code_identity": {p: file_sha(self.root / p) for p in scheduled_sources(name)}}
        path = self.root / "receipt.json"
        path.write_text(json.dumps(receipt))
        manifest = {"jobs": [{"name": name, "registration": "registered", "output_contract": {
            "glob": "receipt.json", "max_age_seconds": 60, "schema": "osanwe.scheduled-job/1"}}]}
        observed = {"state": "passed", "tasks": [{"name": name, "state": "Ready", "last_result": 0,
                     "executable_identity": {"sha256": "synthetic-exe"}}]}
        self.assertEqual(reconcile_inventory(manifest, observed, self.root), [])
        (self.root / scheduled_sources(name)[0]).write_text("changed code")
        self.assertEqual(reconcile_inventory(manifest, observed, self.root)[0]["code"], "artifact-code-identity-stale")
        receipt["code_identity"] = {"private/synthetic-canary": "do not inspect"}
        path.write_text(json.dumps(receipt))
        self.assertEqual(reconcile_inventory(manifest, observed, self.root)[0]["code"], "artifact-code-identity-invalid")


class ValidationAndProbeTests(unittest.TestCase):
    def test_full_profile_owns_new_controls_and_absent_node_is_unavailable(self):
        module = load("validation_release_wiring", ROOT / ".agents/scripts/checkall.py")
        self.assertNotIn("evaluator-controls", dict(module.selected_steps(quick=True)))
        self.assertIn("evaluator-controls", dict(module.selected_steps()))
        with patch.object(module.shutil, "which", return_value=None), patch.object(module, "run", side_effect=AssertionError("missing runtime must not launch tests")):
            for fn in (module.step_evaluator_controls, module.step_runtime_controls):
                good, detail = fn()
                self.assertEqual(module.result_state(good, detail), "unavailable")

    def test_quick_pass_cannot_recover_full_scope_incident(self):
        module = load("health_monitor_under_test", ROOT / "tools/runtime-health.py")
        previous = [{"job": module.JOB, "code": "validation-full-stale"}]
        current = []
        module.retain_unchecked_validation(current, previous, "quick")
        self.assertEqual(current[0]["state"], "stale")
        self.assertEqual(current[0]["reason"], "prior-validation-scope-not-rechecked")
        current = []
        module.retain_unchecked_validation(current, previous, "full")
        self.assertEqual(current, [])

    def test_monitor_and_scorer_status_bind_current_producer_without_old_log_writes(self):
        module = load("monitor_identity_controls", ROOT / "tools/runtime-health.py")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in module.MONITOR_SOURCES + ["tools/score-outcomes.py"]:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("synthetic code")
            at = dt.datetime.now(UTC)
            receipt = {"state": "passed", "verified_at": iso_z(at), "code_identity": module.monitor_identity(root)}
            self.assertEqual(module.monitor_readiness(receipt, at, root), "passed")
            (root / "tools/runtime-health.py").write_text("changed observer")
            self.assertEqual(module.monitor_readiness(receipt, at, root), "stale")
            log = root / ".claude/state/score-outcomes-runs.log"
            log.parent.mkdir(parents=True)
            terminal = "Rollback: realized_at_3mo=0 armed=False gap=None fired=False\n"
            log.write_text(terminal)
            before = log.read_bytes()
            self.assertEqual(module.scorer_producer_findings(root)[0]["state"], "unavailable")
            self.assertEqual(log.read_bytes(), before)
            log.write_text("Runtime: producer_sha256=" + file_sha(root / "tools/score-outcomes.py") + "\n" + terminal)
            self.assertEqual(module.scorer_producer_findings(root), [])
            (root / "tools/score-outcomes.py").write_text("changed financial producer")
            self.assertEqual(module.scorer_producer_findings(root)[0]["state"], "stale")

    def test_native_probe_is_persistent_exact_route_and_exact_read(self):
        module = load("native_probe_under_test", ROOT / "tools/native-resume-probe.py")
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp)
            command = module.invocation(Path("claude.exe"), stage, stage / "settings.json", stage / "mcp.json", "synthetic-session", True)
            self.assertEqual(command[command.index("--model") + 1], "claude-opus-5")
            self.assertEqual(command[command.index("--effort") + 1], "xhigh")
            self.assertIn("--resume", command)
            self.assertIn("--restricted", command)
            self.assertNotIn("--bare", command)
            self.assertNotIn("--no-session-persistence", command)
            self.assertNotIn("--fallback-model", command)
            self.assertTrue(module.is_control_read({"name": "Read", "path": "control.txt"}, stage))
            self.assertFalse(module.is_control_read({"name": "Read", "path": "../control.txt"}, stage))
            self.assertFalse(module.is_control_read({"name": "Write", "path": "control.txt"}, stage))
        with patch.dict(os.environ, {"ANTHROPIC_BASE_URL": "http://synthetic", "ANTHROPIC_API_KEY": "SYNTHETIC_CANARY", "CLAUDE_CODE_SUBAGENT_MODEL": "wrong-model"}):
            env = module.child_environment()
            self.assertNotIn("ANTHROPIC_BASE_URL", env)
            self.assertNotIn("ANTHROPIC_API_KEY", env)
            self.assertNotIn("CLAUDE_CODE_SUBAGENT_MODEL", env)
            self.assertEqual(env["CLAUDE_CODE_EFFORT_LEVEL"], "xhigh")

    def test_skip_timeout_and_optional_scopes_are_not_passes(self):
        module = load("validation_under_test", ROOT / ".agents/scripts/checkall.py")
        def timed_out():
            raise subprocess.TimeoutExpired("synthetic", .01)
        result = module.execute_profile(steps=[("good", lambda: (True, "verified")),
            ("missing", lambda: (True, "UNVERIFIED: service absent")),
            ("stale", lambda: (True, "STALE: old artifact")), ("timeout", timed_out)], emit=False)
        by_name = {row["check"]: row for row in result["checks"]}
        self.assertEqual(by_name["missing"]["state"], "unavailable")
        self.assertEqual(by_name["stale"]["state"], "stale")
        self.assertEqual(by_name["timeout"]["state"], "failed")
        self.assertEqual(by_name["mcp-canary"]["state"], "not_run")
        self.assertEqual(result["counts"]["passed"], 1)
        self.assertEqual(result["state"], "failed")
        self.assertEqual(module.result_state(True, "driftcheck OK: 17 skills (0 unmigrated skipped)"), "passed")
        self.assertEqual(module.result_state(True, "skills-ref: skipped (--quick)"), "unavailable")

    def test_receipt_rejects_changed_binary_code_and_omitted_controls(self):
        module = load("lane_contract_under_test", ROOT / "tools/lane-settings-contract.py")
        with tempfile.TemporaryDirectory() as tmp:
            exe, code = Path(tmp) / "binary", Path(tmp) / "code"
            exe.write_bytes(b"one")
            code.write_bytes(b"probe")
            receipt = {"schema": "osanwe.lane-behavior/1", "scope": "fake-provider-client-mechanics",
                       "binary_sha256": module.binary_identity(exe), "probe_code_sha256": module.binary_identity(code),
                       "state": "passed", "controls": {k: {"state": "passed"} for k in
                          ("output_cap", "request_identity", "compaction_bracket", "binary_unchanged")}}
            self.assertEqual(module.verify_probe_receipt(receipt, exe, code), [])
            exe.write_bytes(b"two")
            self.assertTrue(module.verify_probe_receipt(receipt, exe, code))
            exe.write_bytes(b"one")
            receipt["controls"].pop("compaction_bracket")
            self.assertTrue(module.verify_probe_receipt(receipt, exe, code))
            code.write_bytes(b"changed")
            self.assertTrue(module.verify_probe_receipt(receipt, exe, code))


class IndexObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.module = load("scheduled_job_under_test", ROOT / "tools/scheduled-job.py")
        self.original_root = self.module.ROOT
        self.module.ROOT = self.root
        self.base = self.root / "external"
        for sub in ("index", "index.tmp"):
            (self.base / sub).mkdir(parents=True)
        (self.root / "tools").mkdir()
        (self.root / "config").mkdir()
        paths = {"indexer_sha256": self.base / "index-vault.mjs",
                 "scope_module_sha256": self.root / "tools/index-scope.mjs",
                 "retrieval_core_sha256": self.root / "tools/retrieval-core.mjs",
                 "provider_sha256": self.base / "retrieval-provider.mjs",
                 "runner_sha256": self.base / "reindex-runner.mjs"}
        for path in [*paths.values(), self.base / "node.exe"]:
            path.write_text("synthetic executable/source")
        self.approval = {key: self.module.file_sha(path) for key, path in paths.items()}
        create_json(self.root / "config/scheduled-jobs.json", {"jobs": [{
            "name": "osanwe-vault-reindex", "indexer_scope_approval": self.approval}]})
        self.targets = [self.base / "index/vault.hnsw", self.base / "index/vault-meta.json"]
        for path in self.targets:
            path.write_text("SYNTHETIC_PRIVATE_CANARY_DO_NOT_READ")
        self.at = dt.datetime.now(UTC)
        self.calls = 0

    def tearDown(self):
        self.module.ROOT = self.original_root
        self.temp.cleanup()

    def call(self):
        self.calls += 1
        return self.module.reindex_pipeline(self.root / ("run-" + str(self.calls)), self.base, self.base / "node.exe")

    def response(self, state="passed", reason="current-admitted-generation", needs=False, generation="g-synthetic-1"):
        receipt = self.base / "index/generations" / generation / "manifest.json"
        if state == "passed":
            receipt.parent.mkdir(parents=True, exist_ok=True)
            receipt.write_text('{"synthetic": true}')
        return {"schema": "osanwe.retrieval-health/1", "state": state, "reason": reason,
                "needs_rebuild": needs, "generation_id": generation if state == "passed" else None,
                "observed_at": dt.datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "receipt_path": str(receipt) if state == "passed" else None,
                "document_count": 2, "passage_count": 4}

    def stepper(self, responses):
        def emit(command, directory, label, timeout, outputs=(), **kwargs):
            value = responses.pop(0)
            create_json(Path(command[command.index("--receipt") + 1]), value)
            code = {"passed": 0, "stale": 2, "unavailable": 3}[value["state"]]
            return {"state": "passed" if code == 0 else "failed", "exit_code": code, "reason": "process_completed"}
        return emit

    def test_legacy_metadata_never_read_or_certified_by_noop(self):
        original = Path.read_text
        def guarded(path, *args, **kwargs):
            if path in self.targets:
                raise AssertionError("observer must not read legacy index contents")
            return original(path, *args, **kwargs)
        response = self.response("unavailable", "no-admitted-documents")
        with patch.object(Path, "read_text", guarded), patch.object(self.module, "step", side_effect=self.stepper([response])):
            result = self.call()
        self.assertEqual(result["reason"], "no-admitted-documents")
        self.assertNotIn("SYNTHETIC_PRIVATE_CANARY", json.dumps(result))

    def test_scope_code_change_blocks_execution(self):
        (self.base / "index-vault.mjs").write_text("changed source")
        with patch.object(self.module, "step", side_effect=AssertionError("must not execute")):
            self.assertEqual(self.call()["reason"], "external-indexer-scope-review-stale")

    def test_zero_exit_without_fresh_inspection_receipt_fails(self):
        with patch.object(self.module, "step", return_value={"state": "passed", "exit_code": 0}):
            result = self.call()
        self.assertEqual(result["state"], "failed")
        self.assertFalse(result["index_rebuilt"])

    def test_changed_registry_without_claude_marker_builds_and_verifies_new_generation(self):
        before = self.response("stale", "admission-version-changed", True)
        built = self.response(generation="g-synthetic-2")
        after = self.response(generation="g-synthetic-2")
        with patch.object(self.module, "step", side_effect=self.stepper([before, built, after])):
            result = self.call()
        self.assertTrue(result["index_rebuilt"])
        self.assertEqual(result["state"], "passed")
        self.assertEqual(result["generation_id"], "g-synthetic-2")

    def test_mismatched_postbuild_generation_cannot_pass(self):
        rows = [self.response("stale", "admission-version-changed", True),
                self.response(generation="g-built"), self.response(generation="g-other")]
        with patch.object(self.module, "step", side_effect=self.stepper(rows)):
            self.assertEqual(self.call()["reason"], "fresh-generation-not-verified")

    def test_fresh_write_hint_delays_build_but_reports_stale(self):
        (self.base / ".debounce-marker").write_text("hint")
        with patch.object(self.module, "step", side_effect=self.stepper([
                self.response("stale", "admission-version-changed", True)])):
            result = self.call()
        self.assertEqual(result["state"], "stale")
        self.assertEqual(result["reason"], "admission-pending-write-debounce")

    def test_readiness_receipt_filters_unknown_content_and_requires_generation_file(self):
        value = self.response()
        value["untrusted_detail"] = "SYNTHETIC_PRIVATE_CANARY"
        with patch.object(self.module, "step", side_effect=self.stepper([value])):
            result = self.call()
        self.assertNotIn("SYNTHETIC_PRIVATE_CANARY", json.dumps(result))
        Path(value["receipt_path"]).unlink()
        with patch.object(self.module, "step", side_effect=self.stepper([value])):
            self.assertEqual(self.call()["state"], "failed")

    def test_owner_refresh_and_shared_overlap_do_not_adopt_other_locks(self):
        path = self.base / ".reindex.lock"
        value = f"{os.getpid()} 2026-09-13T05:19:13.144Z".encode()
        path.write_bytes(value)
        old = self.at.timestamp() - 3600
        os.utime(path, (old, old))
        self.module.refresh_owned_reindex_lock(path, os.getpid())
        self.assertGreater(path.stat().st_mtime, old + 3500)
        self.assertEqual(path.read_bytes(), value)
        with self.assertRaises(OverlapError):
            self.module.refresh_owned_reindex_lock(path, os.getpid() + 1)
        self.assertEqual(self.call()["reason"], "external-reindex-already-running")
        with job_lock(self.base / ".osanwe-reindex-observer.lock"):
            self.assertEqual(self.call()["reason"], "external-reindex-already-running")

    def test_process_maintenance_is_bounded_and_owner_presence_expires(self):
        observed = []
        result = bounded_process([sys.executable, "-c", "import time;time.sleep(30)"], self.root, .4,
                                 maintenance=lambda pid: observed.append((pid, process_exists(pid))), maintenance_interval=.1)
        self.assertEqual(result["reason"], "timeout")
        self.assertTrue(observed and all(alive for _, alive in observed))
        self.assertFalse(process_exists(observed[0][0]))
        def wrong_owner(pid):
            raise OverlapError("synthetic ownership changed")
        result = bounded_process([sys.executable, "-c", "import time;time.sleep(30)"], self.root, 5,
                                 maintenance=wrong_owner, maintenance_interval=.1)
        self.assertEqual(result["reason"], "process-maintenance-failed")



if __name__ == "__main__":
    unittest.main()

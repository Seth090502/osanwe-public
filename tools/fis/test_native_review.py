"""Frozen ordinary-review failure controls; all inputs/providers are synthetic.

These controls were written before native_review.py. Passing them establishes
development mechanics only, never financial quality or native subscription use.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import report_review as rr
import reviewer_execution as execution
import workbench as w
from test_report_review import fixture
import native_review as nr


class NativeReviewControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.packet, self.bundle, self.request, self.assets = fixture(self.root)
        self.options = dict(harness="claude", model="claude-opus-5", effort="xhigh",
                            reviewer_id="reviewer:native-control", timeout_seconds=30,
                            max_turns=6, max_output_tokens=4096)

    def prepare(self, **options):
        return nr.prepare(self.packet, self.bundle, self.request, self.assets,
                          self.root / "prepared", **{**self.options, **options})

    def prepared(self):
        self.prepare()
        return self.root / "prepared"

    def output(self, prepared):
        contract = w.load_packet(prepared / "workspace/producer-contract.json")
        record = copy.deepcopy(self.request["reviewers"][0])
        record.update(id=contract["reviewer_id"], model=contract["model"], effort=contract["effort"],
                      context_sha256=contract["context_sha256"])
        return {contract["response_key"]: record}

    def events(self, output):
        return [
            {"type": "system", "subtype": "init", "tools": ["StructuredOutput"]},
            {"type": "assistant", "message": {"model": "claude-opus-5", "content": [
                {"type": "tool_use", "id": "format:1", "name": "StructuredOutput", "input": output}]}},
            {"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": "format:1", "is_error": False, "content": "ignored"}]}},
            {"type": "result", "subtype": "success", "is_error": False, "num_turns": 2,
             "modelUsage": {"claude-opus-5": {}}, "structured_output": output},
        ]

    def fake_launch(self, events):
        def launch(command, **kwargs):
            # The immutable reservation must exist before any provider event.
            self.assertTrue((self.root / "attempt/reserved.json").is_file())
            for event in events:
                kwargs["on_event"](event)
            return {"exit_code": 0, "stdout_bytes": 100, "stderr_bytes_omitted": 0,
                    "elapsed_seconds": 0.01, "process_tree_cleanup": "not_needed"}
        return launch

    def run_mock(self, prepared, events=None):
        events = self.events(self.output(prepared)) if events is None else events
        with patch.object(nr, "validate_qualification", return_value={"state": "passed", "qualification_sha256": "a" * 64}), \
             patch.object(nr, "file_sha", return_value=execution.PROVEN_BINARY), \
             patch.object(nr, "subscription_status", return_value={"state": "available", "route": "native_subscription"}), \
             patch.object(nr, "bounded_events", side_effect=self.fake_launch(events)):
            return nr.run(prepared, harness="claude", model="claude-opus-5", effort="xhigh",
                          executable=Path(sys.executable), qualification=self.root / "qualification.json",
                          attempt_id="ordinary:control", outdir=self.root / "attempt")

    def test_complete_frozen_inputs_and_explicit_model_are_preserved(self):
        prepared = self.prepared()
        loaded = nr.verify_prepared(prepared)
        self.assertEqual(loaded["model"], "claude-opus-5")
        self.assertEqual(loaded["effort"], "xhigh")
        self.assertEqual(loaded["library_admission"]["state"], "unverified")
        prompt = (prepared / "workspace/prompt.txt").read_text(encoding="utf-8")
        for artifact in self.request["artifacts"]:
            # JSON escaping is a reversible presentation, not truncation.
            self.assertIn(json.dumps((self.assets / artifact["path"]).read_text(encoding="utf-8"), ensure_ascii=True), prompt)
        self.assertEqual(self.request["reviewers"][0]["id"], "fixture:reviewer")

    def test_personal_material_refused_before_persistence_or_hashing(self):
        self.request["task"]["question"] = "PRIVACY_CANARY_SYNTHETIC_CONTROL"
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse((self.root / "prepared").exists())

    def test_input_budget_never_truncates_the_review(self):
        with self.assertRaises(ValueError):
            self.prepare(max_input_bytes=100)
        self.assertFalse((self.root / "prepared").exists())

    def test_binary_artifact_without_supported_transport_refused(self):
        path = self.assets / "original.txt"
        path.write_bytes(b"\xff\x00")
        next(a for a in self.request["artifacts"] if a["id"] == "original")["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        with self.assertRaises(ValueError):
            self.prepare()

    def test_frozen_prompt_edits_fail_closed(self):
        prepared = self.prepared()
        (prepared / "workspace/prompt.txt").write_text("different")
        with self.assertRaises(ValueError):
            nr.verify_prepared(prepared)

    def test_changed_runner_or_settings_invalidate_qualification(self):
        prepared = self.prepared()
        (prepared / "settings.json").write_text('{"permissions":{"defaultMode":"bypassPermissions"}}')
        with self.assertRaises(ValueError):
            nr.verify_prepared(prepared)

    def test_explicit_model_mismatch_never_calls_subscription(self):
        prepared = self.prepared()
        with patch.object(nr, "subscription_status") as auth, self.assertRaises(ValueError):
            nr.run(prepared, harness="claude", model="other", effort="xhigh", executable=sys.executable,
                   qualification=self.root / "missing", attempt_id="ordinary:bad", outdir=self.root / "attempt")
        auth.assert_not_called()

    def test_missing_mechanical_qualification_never_starts_provider(self):
        prepared = self.prepared()
        with patch.object(nr, "bounded_events") as launch, self.assertRaises(ValueError):
            nr.run(prepared, harness="claude", model="claude-opus-5", effort="xhigh", executable=sys.executable,
                   qualification=self.root / "missing", attempt_id="ordinary:bad", outdir=self.root / "attempt")
        launch.assert_not_called()

    def test_correct_synthetic_stream_reaches_unchanged_consumer(self):
        prepared = self.prepared()
        result = self.run_mock(prepared)
        self.assertEqual(result["state"], "completed")
        self.assertEqual(result["report_status"], "accepted")
        self.assertFalse(result["independent_assessment"])
        self.assertEqual(w.load_packet(self.root / "attempt/output.json"), self.output(prepared))
        self.assertTrue((self.root / "attempt/execution/events.jsonl").is_file())
        self.assertTrue(rr.verify_review(self.root / "attempt/review")["current_eligible"])

    def test_major_financial_finding_is_preserved_and_withheld(self):
        prepared = self.prepared()
        output = self.output(prepared)
        output["R001"]["findings"] = [{"id": "finding:major", "severity": "major", "status": "open",
            "reason": "Correct arithmetic used for the wrong financial conclusion.",
            "assertion_ids": [self.request["assertions"][0]["id"]], "artifact_ids": ["report"],
            "resolution_artifact": None, "resolution_verified": False}]
        result = self.run_mock(prepared, self.events(output))
        self.assertEqual(result["report_status"], "withheld")
        self.assertEqual(w.load_packet(self.root / "attempt/output.json"), output)

    def test_failed_attempt_cannot_be_reopened_or_error_text_persisted(self):
        prepared = self.prepared()
        result = self.run_mock(prepared, [{"type": "result", "is_error": True,
                                          "errors": ["PRIVACY_CANARY_SYNTHETIC_CONTROL"]}])
        self.assertEqual(result["state"], "failed")
        self.assertEqual(w.load_packet(self.root / "attempt/reserved.json")["spent_attempts"], 1)
        with self.assertRaises((ValueError, FileExistsError)):
            self.run_mock(prepared)
        for path in (self.root / "attempt").rglob("*"):
            if path.is_file():
                self.assertNotIn(b"PRIVACY_CANARY", path.read_bytes())

    def test_malformed_final_and_omitted_coverage_fail(self):
        prepared = self.prepared()
        output = self.output(prepared)
        output["R001"]["coverage"]["assertions"] = []
        result = self.run_mock(prepared, self.events(output))
        self.assertEqual(result["state"], "failed")

    def test_valid_verdict_cannot_be_replaced_by_later_final(self):
        prepared = self.prepared()
        events = self.events(self.output(prepared))
        events[-1] = copy.deepcopy(events[-1])
        events[-1]["structured_output"]["R001"]["judgments"]["economics"]["rationale"] = "Changed after lock."
        self.assertEqual(self.run_mock(prepared, events)["state"], "failed")

    def test_read_tool_is_prohibited_in_inline_only_runner(self):
        prepared = self.prepared()
        event = {"type": "assistant", "message": {"model": "claude-opus-5", "content": [
            {"type": "tool_use", "id": "bad:read", "name": "Read", "input": {"file_path": "../outside.txt"}}]}}
        self.assertEqual(self.run_mock(prepared, [event])["state"], "failed")

    def test_turn_counter_mismatch_is_not_repaired(self):
        prepared = self.prepared()
        events = self.events(self.output(prepared))
        events[-1]["num_turns"] = 1
        self.assertEqual(self.run_mock(prepared, events)["state"], "failed")

    def test_unexpected_model_is_not_substituted(self):
        prepared = self.prepared()
        events = self.events(self.output(prepared))
        events[1]["message"]["model"] = "some-other-model"
        self.assertEqual(self.run_mock(prepared, events)["state"], "failed")

    def test_codex_adapter_keeps_codex_events_and_refuses_tools(self):
        adapter = nr.CodexEvents(max_turns=1)
        adapter.observe({"type": "thread.started", "thread_id": "not-persisted"})
        adapter.observe({"type": "turn.started"})
        adapter.observe({"type": "item.completed", "item": {"id": "i1", "type": "agent_message", "text": '{"ok":true}'}})
        adapter.observe({"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 2}})
        self.assertEqual(adapter.finish(), {"ok": True})
        with self.assertRaises(ValueError):
            nr.CodexEvents(max_turns=1).observe({"type": "item.started", "item": {"type": "command_execution", "command": "do not run"}})

    def test_codex_unqualified_refuses_native_inference(self):
        self.prepare(harness="codex", model="gpt-6-astra")
        with patch.object(nr, "bounded_events") as launch, self.assertRaises(ValueError):
            nr.run(self.root / "prepared", harness="codex", model="gpt-6-astra", effort="xhigh",
                   executable=sys.executable, qualification=self.root / "missing",
                   attempt_id="ordinary:codex", outdir=self.root / "attempt")
        launch.assert_not_called()

    def test_strict_stream_parser_refuses_duplicate_json_keys(self):
        with self.assertRaises(ValueError):
            nr.decode_event(b'{"type":"result","type":"assistant"}')

    def test_output_flood_and_unterminated_lines_are_bounded(self):
        command = [sys.executable, "-c", "import sys;sys.stdout.write('x'*100000);sys.stdout.flush()"]
        with self.assertRaises(ValueError):
            nr.bounded_events(command, cwd=self.root, env=os.environ.copy(), prompt=b"",
                              timeout_seconds=5, max_output_bytes=4096, max_event_bytes=1024,
                              on_event=lambda _: None)

    def test_timeout_kills_parent_and_child_process(self):
        marker = self.root / "child-pid.txt"
        script = "import pathlib,subprocess,sys,time;p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);pathlib.Path(sys.argv[1]).write_text(str(p.pid));time.sleep(60)"
        started = time.monotonic()
        with self.assertRaises(ValueError):
            nr.bounded_events([sys.executable, "-c", script, str(marker)], cwd=self.root,
                              env=os.environ.copy(), prompt=b"", timeout_seconds=1,
                              max_output_bytes=4096, max_event_bytes=1024, on_event=lambda _: None)
        self.assertLess(time.monotonic() - started, 20)
        if marker.exists():
            # Runtime health is a package module (it imports .scheduler).
            sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
            from fis.runtime_health import process_exists
            self.assertFalse(process_exists(int(marker.read_text())))

    def test_environment_removes_provider_overrides_and_secret_logging(self):
        incoming = {"ANTHROPIC_API_KEY": "do-not-persist", "ANTHROPIC_BASE_URL": "https://invalid.example",
                    "CLAUDE_CONFIG_DIR": "unexpected", "CLAUDE_CODE_USE_BEDROCK": "1", "OPENAI_API_KEY": "hidden",
                    "PATH": os.environ.get("PATH", "")}
        env = nr.native_environment("claude", "xhigh", 4096, incoming)
        self.assertNotIn("ANTHROPIC_API_KEY", env)
        self.assertNotIn("ANTHROPIC_BASE_URL", env)
        self.assertNotIn("CLAUDE_CONFIG_DIR", env)
        self.assertEqual(env["CLAUDE_CODE_EFFORT_LEVEL"], "xhigh")

    def test_probe_recognizes_string_and_block_transport_without_truncation(self):
        prompt = "Complete synthetic evidence."
        blocks = nr.request_blocks({"messages": [{"content": prompt}, {"content": [{"type": "text", "text": prompt}]}]})
        self.assertEqual([b["text"] for b in blocks], [prompt, prompt])
        self.assertFalse(any(prompt in b.get("text", "") for b in nr.request_blocks({"messages": [{"content": "Complete"}]})))

    def test_optional_native_module_absence_does_not_break_ordinary_cli(self):
        packet_path = self.root / "packet.json"
        packet_path.write_bytes(w.canonical(self.packet))
        script = "import importlib.abc,sys;sys.path.insert(0,sys.argv[1]);import workbench\nclass BlockNative(importlib.abc.MetaPathFinder):\n def find_spec(self,fullname,path=None,target=None):\n  if fullname=='native_review':raise ImportError('optional host module absent')\nsys.meta_path.insert(0,BlockNative());sys.argv=['workbench.py','validate',sys.argv[2]];raise SystemExit(workbench.main())"
        process = subprocess.run([sys.executable, "-c", script, str(Path(__file__).parent), str(packet_path)],
                                 capture_output=True, text=True, timeout=15)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertTrue(json.loads(process.stdout)["valid"])

    def test_declared_method_scope_cannot_approve_an_unadmitted_passage(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from pit import dataset_registry
        registry = self.root / "synthetic-registry.jsonl"
        registry.write_text("{}\n")
        with patch.object(dataset_registry, "approved_document_manifest", return_value={
                "schema": "osanwe.financial-document-manifest/1", "documents": []}), self.assertRaises(ValueError):
            self.prepare(document_registry=registry)
        self.assertFalse((self.root / "prepared").exists())

    def test_current_admission_change_invalidates_frozen_method_binding(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from pit import dataset_registry
        method = self.request["methods"][0]
        artifact = next(a for a in self.request["artifacts"] if a["id"] == method["support"]["artifact_id"])
        manifest = {"schema": "osanwe.financial-document-manifest/1", "manifest_sha256": "a" * 64,
            "documents": [{"document_id": "method:synthetic", "source_version": method["version"], "sha256": artifact["sha256"],
                "applicability": {"applies_when": ["Synthetic statement arithmetic"]}, "admission_record_sha256": "b" * 64,
                "chunks": [{"chunk_id": "method:arithmetic", "start_char": 0, "end_char": 200,
                            "locator": {"start_line": 1, "end_line": 1, "heading": "Synthetic primer"},
                            "approved_use": ["financial-research"]}]}]}
        registry = self.root / "synthetic-registry.jsonl"
        registry.write_text("{}\n")
        with patch.object(dataset_registry, "approved_document_manifest", return_value=manifest):
            self.prepare(document_registry=registry)
            self.assertEqual(nr.verify_prepared(self.root / "prepared")["library_admission"]["state"], "bound")
        changed = {**manifest, "manifest_sha256": "c" * 64}
        with patch.object(dataset_registry, "approved_document_manifest", return_value=changed), self.assertRaises(ValueError):
            nr.verify_prepared(self.root / "prepared")

    def test_synthetic_schema_reminder_uses_same_strict_turn_budget(self):
        prepared = self.prepared()
        events = self.events(self.output(prepared))
        events.insert(1, {"type": "user", "isSynthetic": True, "message": {"role": "user", "content": [{"type": "text", "text": "Synthetic schema reminder."}]}})
        events[-1]["num_turns"] = 3
        self.assertEqual(self.run_mock(prepared, events)["state"], "completed")

    def test_partial_tool_id_without_matching_completed_result_is_rejected(self):
        prepared = self.prepared()
        events = self.events(self.output(prepared))
        events.insert(1, {"type": "stream_event", "event": {"type": "content_block_start", "index": 0,
            "content_block": {"type": "tool_use", "id": "format:partial-only", "name": "StructuredOutput"}}})
        self.assertEqual(self.run_mock(prepared, events)["state"], "failed")

    def test_final_counter_diagnostics_are_retained_without_error_prose(self):
        prepared = self.prepared()
        events = self.events(self.output(prepared))
        events[-1]["num_turns"] = 99
        result = self.run_mock(prepared, events)
        self.assertEqual(result["state"], "failed")
        journal = [json.loads(line) for line in (self.root / "attempt/execution/events.jsonl").read_text().splitlines()]
        observed = next(e for e in journal if e["event"] == "native_terminal_counts")
        self.assertEqual(observed["reported_turns"], 99)
        self.assertEqual(observed["observed_user_messages"], 1)
        self.assertEqual(observed["pending_tool_count"], 0)

    def test_prefixed_typed_formatter_rejection_is_parsed_without_prose(self):
        ajv = [{"type": "text", "text": 'Schema validation failed: [{"keyword":"pattern","instancePath":"/R001/disagreements/0"}]'}]
        zod = [{"type": "text", "text": 'Input validation failed: [{"code":"invalid_type","path":["R001","read_only"]}]'}]
        self.assertEqual(nr.schema_diagnostics(ajv, "R001"), [{"keyword": "pattern", "path": "/R001/disagreements/0"}])
        self.assertEqual(nr.schema_diagnostics(zod, "R001"), [{"keyword": "type", "path": "/R001/read_only"}])
        self.assertEqual(nr.schema_diagnostics("Unknown provider failure", "R001"), [])
        self.assertEqual(nr.schema_diagnostics([{"keyword": "pattern", "instancePath": "/R001/PRIVACY_CANARY"}], "R001"), [])

    def test_untyped_empty_formatter_failure_cannot_authorize_a_retry(self):
        prepared = self.prepared()
        events = self.events(self.output(prepared))
        invalid = copy.deepcopy(events[1])
        invalid["message"]["content"][0].update(id="format:invalid", input={"R001": {}})
        rejected = {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "format:invalid", "is_error": True, "content": "Missing fields; no typed diagnostic supplied."}]}}
        events[1:1] = [invalid, rejected]
        self.assertEqual(self.run_mock(prepared, events)["state"], "failed")

    def test_single_verdict_policy_is_explicit_and_versioned(self):
        prepared = self.prepared()
        metadata = nr.verify_prepared(prepared)
        self.assertEqual(metadata["schema"], "osanwe.native-review-runner/2")
        self.assertEqual(metadata["policy"]["formatter_policy"], "single_verdict_no_correction")

    def test_single_verdict_stops_even_after_typed_schema_rejection(self):
        prepared = self.prepared()
        output = self.output(prepared)
        output["R001"]["disagreements"] = ["INVALID FINDING ID WITH SPACES"]
        events = self.events(output)
        events[2]["message"]["content"][0].update(is_error=True, content=[{
            "keyword": "pattern", "instancePath": "/R001/disagreements/0"}])
        result = self.run_mock(prepared, events)
        self.assertEqual(result["state"], "failed")
        self.assertEqual(result["reason"], "single_verdict_schema_rejection")

    def test_second_formatter_is_refused_even_if_it_repeats_the_first(self):
        prepared = self.prepared()
        events = self.events(self.output(prepared))
        second = copy.deepcopy(events[1])
        second["message"]["content"][0]["id"] = "format:second"
        events.insert(3, second)
        result = self.run_mock(prepared, events)
        self.assertEqual(result["state"], "failed")
        self.assertEqual(result["reason"], "single_verdict_additional_formatter_prohibited")


class ExecutablePathBoundary(unittest.TestCase):
    def test_protected_executable_is_refused_before_hashing(self):
        with tempfile.TemporaryDirectory() as td:
            protected = Path(td) / "private" / "claude.exe"
            protected.parent.mkdir()
            protected.write_bytes(b"SYNTHETIC_EXECUTABLE_PRIVATE_BODY_9317")
            with patch.object(Path, "open", side_effect=AssertionError("protected executable was opened")):
                with self.assertRaises(ValueError):
                    nr.file_sha(protected)


if __name__ == "__main__":
    unittest.main()

"""Synthetic producer and execution controls; never invoke a model or an account."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import report_review as rr
import reviewer_execution as execution
import workbench as w
from test_report_review import fixture


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class ReviewerExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.packet, self.bundle, self.request, self.assets = fixture(self.root)
        self.prepared = rr.prepare_context(self.packet, self.bundle, self.request, self.assets)
        self.reviewer = copy.deepcopy(self.request["reviewers"][0])
        self.contract = rr.reviewer_contract(self.prepared, reviewer_id=self.reviewer["id"],
                                             model=self.reviewer["model"], effort=self.reviewer["effort"])
        self.output = {"R001": self.reviewer}
        self.clock = FakeClock()

    def attempt(self, name="attempt", **changes):
        args = dict(attempt_id="synthetic:" + name, contract=self.contract, classification="synthetic",
                    timeout_seconds=480, max_turns=24, binary_sha256=execution.PROVEN_BINARY,
                    json_schema_requested=True, strict_empty_mcp=True, clock=self.clock)
        args.update(changes)
        return execution.NativeReviewAttempt(self.root / name, **args)

    def events(self, name="attempt"):
        return [json.loads(line) for line in (self.root / name / "events.jsonl").read_text().splitlines()]

    def good_formatter(self, attempt, output=None, tool_id="format:1"):
        attempt.tool_call(tool_id, "StructuredOutput", self.output if output is None else output)
        attempt.tool_result(tool_id, is_error=False)

    def finding(self, severity="major", status="open"):
        return {"id": "finding:meaning", "severity": severity, "status": status,
                "reason": "Synthetic financial interpretation requires correction.",
                "assertion_ids": [self.request["assertions"][0]["id"]], "artifact_ids": ["report"],
                "resolution_artifact": None, "resolution_verified": False}

    def test_correct_control_preserves_contract_output_counts_and_one_attempt(self):
        before = copy.deepcopy(self.output)
        with self.attempt() as attempt:
            attempt.tool_call("read:1", "Read", {"file_path": "synthetic-report.txt"})
            attempt.tool_result("read:1", is_error=False)
            self.good_formatter(attempt)
            result = attempt.finish(self.output, cumulative_turns=24)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["spent_attempts"], 1)
        self.assertEqual(result["tool_counts"], {"Read": 1, "StructuredOutput": 1})
        self.assertEqual(result["schema_corrections"], 0)
        self.assertTrue(result["final_schema_valid"])
        self.assertFalse(result["financial_acceptance_established"])
        contract = w.load_packet(self.root / "attempt/contract.json")
        self.assertEqual(contract, self.contract)
        self.assertTrue(rr.validate_reviewer_contract(contract))
        events = self.events()
        self.assertEqual(events[0]["event"], "reserved")
        self.assertEqual(events[-1]["spent_attempts"], 1)
        self.assertEqual([e["output"] for e in events if e["event"] == "final_output"], [before])
        self.assertEqual(self.output, before)

    def test_canonical_schema_checks_nested_values_and_all_required_fields(self):
        self.assertTrue(rr.reviewer_output_schema_valid(self.contract, self.output))
        mutations = [("read_only", "true"), ("status", "PASS"), ("coverage", {}),
                     ("not_applicable_checks", ["render:missing"]), ("findings", "None"),
                     ("disagreements", ["A prose scope note."]), ("disagreements", ["finding:1\n"])]
        for field, value in mutations:
            output = copy.deepcopy(self.output)
            output["R001"][field] = value
            with self.subTest(field=field, value=value):
                self.assertFalse(rr.reviewer_output_schema_valid(self.contract, output))
        for mode in ("missing", "extra", "rationale", "dimension"):
            output = copy.deepcopy(self.output)
            if mode == "missing":
                del output["R001"]["not_applicable_checks"]
            elif mode == "extra":
                output["R001"]["schema_note"] = "Additional prose."
            elif mode == "rationale":
                output["R001"]["judgments"]["economics"]["rationale"] = "Trailing newline.\n"
            else:
                del output["R001"]["judgments"]["economics"]
            with self.subTest(mode=mode):
                self.assertFalse(rr.reviewer_output_schema_valid(self.contract, output))
                self.assertEqual(rr.consume_reviewer_output(self.contract, self.request, self.prepared, output)["status"], "withheld")

    def test_edited_schema_is_rejected_even_with_recomputed_digest(self):
        contract = copy.deepcopy(self.contract)
        contract["output_schema"]["properties"]["R001"]["properties"]["disagreements"] = {"type": "array"}
        contract["contract_sha256"] = w.sha({k: v for k, v in contract.items() if k != "contract_sha256"})
        with self.assertRaisesRegex(ValueError, "contract changed"):
            self.attempt(contract=contract)
        self.assertFalse((self.root / "attempt").exists())

    def test_pinned_binary_native_schema_and_empty_mcp_are_all_required(self):
        for index, change in enumerate(({"binary_sha256": "0" * 64}, {"json_schema_requested": False},
                                         {"strict_empty_mcp": False}, {"strict_empty_mcp": 1})):
            name = "bad-boundary-" + str(index)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "pinned"):
                self.attempt(name, **change)
            self.assertFalse((self.root / name).exists())

    def test_only_read_and_native_formatter_are_allowed(self):
        for index, name in enumerate(("Bash", "Write", "Edit", "Agent", "Task", "WebFetch", "mcp__StructuredOutput")):
            directory = "tool-" + str(index)
            with self.subTest(name=name), self.attempt(directory) as attempt:
                with self.assertRaisesRegex(ValueError, "non_read_tool_prohibited"):
                    attempt.tool_call("tool:1", name, {"command": "Synthetic prohibited control."})
                self.assertTrue(attempt.failed)
            self.assertEqual(self.events(directory)[-1]["status"], "failed")

    def test_provider_success_cannot_accept_schema_invalid_output(self):
        output = copy.deepcopy(self.output)
        output["R001"]["disagreements"] = ["Unstructured prose."]
        with self.attempt() as attempt:
            attempt.tool_call("format:1", "StructuredOutput", output)
            with self.assertRaisesRegex(ValueError, "provider_success"):
                attempt.tool_result("format:1", is_error=False)
        events = self.events()
        self.assertEqual(next(e["draft"] for e in events if e["event"] == "tool_call"), output)
        self.assertEqual(next(e["is_error"] for e in events if e["event"] == "tool_result"), False)
        self.assertEqual(events[-1]["status"], "failed")

    def test_schema_correction_keeps_all_drafts_and_allows_unfinished_reasoning(self):
        first = copy.deepcopy(self.output)
        first["R001"]["disagreements"] = ["A prose scope note."]
        final = copy.deepcopy(self.output)
        final["R001"]["judgments"]["economics"] = {"status": "fail", "rationale": "Further review found a material interpretation error."}
        final["R001"]["findings"] = [self.finding()]
        with self.attempt() as attempt:
            attempt.record_turns(2)
            attempt.tool_call("format:1", "StructuredOutput", first)
            attempt.tool_result("format:1", is_error=True,
                                schema_diagnostics=[{"keyword": "pattern", "path": "/R001/disagreements/0"}])
            self.good_formatter(attempt, final, "format:2")
            result = attempt.finish(final, cumulative_turns=3)
        self.assertEqual(result["spent_attempts"], 1)
        self.assertEqual(result["formatter_drafts"], 2)
        self.assertEqual(result["schema_corrections"], 1)
        self.assertEqual([e["draft"] for e in self.events() if e["event"] == "tool_call"], [first, final])
        self.assertEqual(rr.consume_reviewer_output(self.contract, self.request, self.prepared, final)["status"], "withheld")

    def test_wrong_resolution_role_is_rejected_before_final_verdict_lock(self):
        first = copy.deepcopy(self.output)
        first["R001"]["findings"] = [self.finding()]
        first["R001"]["findings"][0].update(status="resolved", resolution_artifact="render", resolution_verified=True)
        self.assertEqual(self.contract["correction_artifact_ids"], [])
        final = copy.deepcopy(self.output)
        final["R001"]["judgments"]["limitations"]["rationale"] = "Synthetic historical critique is discussed here; no remaining current defect was found."
        with self.attempt() as attempt:
            attempt.tool_call("format:1", "StructuredOutput", first)
            self.assertIsNone(attempt.locked_output)
            attempt.tool_result("format:1", is_error=True,
                                schema_diagnostics=[{"keyword": "enum", "path": "/R001/findings/0/status"}])
            self.good_formatter(attempt, final, "format:2")
            result = attempt.finish(final, cumulative_turns=3)
        self.assertEqual(result["spent_attempts"], 1)
        self.assertEqual(result["schema_corrections"], 1)
        self.assertEqual([event["draft"] for event in self.events() if event["event"] == "tool_call"], [first, final])
        self.assertEqual(rr.consume_reviewer_output(self.contract, self.request, self.prepared, final)["status"], "accepted")

    def test_first_schema_valid_completed_verdict_cannot_be_replaced(self):
        final = copy.deepcopy(self.output)
        final["R001"]["findings"] = [self.finding()]
        for index, prior_result in enumerate((None, False, True)):
            name = "locked-" + str(index)
            with self.subTest(prior_result=prior_result), self.attempt(name) as attempt:
                attempt.tool_call("format:1", "StructuredOutput", final)
                if prior_result is not None:
                    diagnostics = [{"keyword": "type", "path": "/R001"}] if prior_result else []
                    attempt.tool_result("format:1", is_error=prior_result, schema_diagnostics=diagnostics)
                with self.assertRaisesRegex(ValueError, "verdict_is_locked"):
                    attempt.tool_call("format:2", "StructuredOutput", self.output)
            self.assertEqual([e["draft"] for e in self.events(name) if e["event"] == "tool_call"], [final, self.output])

    def test_identical_valid_draft_can_follow_explicit_provider_schema_rejection(self):
        with self.attempt() as attempt:
            attempt.tool_call("format:1", "StructuredOutput", self.output)
            attempt.tool_result("format:1", is_error=True,
                                schema_diagnostics=[{"keyword": "type", "path": "/R001"}])
            self.good_formatter(attempt, tool_id="format:2")
            result = attempt.finish(self.output, cumulative_turns=3)
        self.assertEqual(result["spent_attempts"], 1)
        self.assertEqual(result["schema_corrections"], 1)
        self.assertEqual(len([e for e in self.events() if e["event"] == "final_verdict_locked"]), 1)

    def test_final_replacement_is_preserved_and_rejected(self):
        changed = copy.deepcopy(self.output)
        changed["R001"]["judgments"]["economics"]["rationale"] = "Changed after final output."
        with self.attempt() as attempt:
            self.good_formatter(attempt)
            with self.assertRaisesRegex(ValueError, "differs_from_successful_formatter"):
                attempt.finish(changed, cumulative_turns=2)
        self.assertEqual(next(e["output"] for e in self.events() if e["event"] == "final_output"), changed)

    def test_unknown_finding_id_is_schema_valid_but_financial_review_fails(self):
        self.output["R001"]["disagreements"] = ["finding:unknown"]
        with self.attempt() as attempt:
            self.good_formatter(attempt)
            result = attempt.finish(self.output, cumulative_turns=2)
        self.assertTrue(result["final_schema_valid"])
        decision = rr.consume_reviewer_output(self.contract, self.request, self.prepared, self.output)
        self.assertEqual(decision["status"], "withheld")
        self.assertIn("reviewer_missing_malformed_stale_or_incomplete", decision["blockers"])

    def test_unresolved_disagreement_cannot_be_hidden_by_omitting_its_id(self):
        self.output["R001"]["findings"] = [self.finding("minor", "disputed")]
        for ids in (["finding:meaning"], []):
            self.output["R001"]["disagreements"] = ids
            with self.subTest(ids=ids):
                decision = rr.consume_reviewer_output(self.contract, self.request, self.prepared, self.output)
                self.assertEqual(decision["blockers"], ["unresolved_reviewer_disagreement"])

    def test_pending_read_or_missing_successful_formatter_prevents_completion(self):
        for mode in ("pending_read", "no_formatter", "rejected_formatter"):
            with self.subTest(mode=mode), self.attempt(mode) as attempt:
                if mode == "pending_read":
                    attempt.tool_call("read:1", "Read", {})
                    self.good_formatter(attempt)
                elif mode == "rejected_formatter":
                    attempt.tool_call("format:1", "StructuredOutput", {})
                    attempt.tool_result("format:1", is_error=True,
                                        schema_diagnostics=[{"keyword": "required", "path": "/R001"}])
                with self.assertRaisesRegex(ValueError, "formatter_history"):
                    attempt.finish(self.output, cumulative_turns=2)

    def test_formatter_retry_requires_a_prior_typed_schema_rejection(self):
        for index, result in enumerate((None, False, True)):
            with self.subTest(result=result), self.attempt("retry-" + str(index)) as attempt:
                payload = {} if result is True else self.output
                attempt.tool_call("format:1", "StructuredOutput", payload)
                if result is not None:
                    attempt.tool_result("format:1", is_error=result)
                with self.assertRaisesRegex(ValueError, "formatter_retry_requires"):
                    attempt.tool_call("format:2", "StructuredOutput", payload)

    def test_duplicate_call_and_result_ids_fail_without_resetting_counts(self):
        for mode in ("call", "result"):
            with self.subTest(mode=mode), self.attempt(mode) as attempt:
                attempt.tool_call("read:1", "Read", {})
                if mode == "result":
                    attempt.tool_result("read:1", is_error=False)
                with self.assertRaises(ValueError):
                    if mode == "call":
                        attempt.tool_call("read:1", "Read", {})
                    else:
                        attempt.tool_result("read:1", is_error=False)
                self.assertEqual(attempt.counts, {"Read": 1})

    def test_turn_counter_cannot_reset_and_retries_share_the_fixed_limit(self):
        for mode in ("reset", "exhaustion"):
            with self.subTest(mode=mode), self.attempt(mode, max_turns=3) as attempt:
                attempt.record_turns(3)
                with self.assertRaisesRegex(ValueError, "turn_counter|turn_budget"):
                    attempt.record_turns(2 if mode == "reset" else 4)
                self.assertTrue(attempt.failed)
            self.assertEqual(self.events(mode)[-1]["spent_attempts"], 1)

    def test_formatter_retries_cannot_refresh_wall_time(self):
        with self.attempt() as attempt:
            attempt.tool_call("format:1", "StructuredOutput", {})
            attempt.tool_result("format:1", is_error=True,
                                schema_diagnostics=[{"keyword": "required", "path": "/R001"}])
            self.clock.now = 480
            with self.assertRaisesRegex(ValueError, "wall_time_budget"):
                attempt.tool_call("format:2", "StructuredOutput", self.output)
        self.assertEqual(self.events()[-1]["spent_attempts"], 1)
        self.assertEqual(self.events()[-1]["status"], "failed")

    def test_abandoned_attempt_cannot_reopen_its_existing_directory(self):
        with self.attempt():
            pass
        original = (self.root / "attempt/events.jsonl").read_bytes()
        self.assertEqual(self.events()[-1]["status"], "abandoned")
        with self.assertRaises(FileExistsError):
            self.attempt()
        self.assertEqual((self.root / "attempt/events.jsonl").read_bytes(), original)

    def test_interrupted_journal_is_preserved_and_does_not_restore_the_attempt(self):
        directory = self.root / "attempt"
        directory.mkdir()
        interrupted = b'{"event":"reserved","spent_attempts":1}\n{"event":"tool_call"'
        (directory / "events.jsonl").write_bytes(interrupted)
        with self.assertRaises(FileExistsError):
            self.attempt()
        self.assertEqual((directory / "events.jsonl").read_bytes(), interrupted)

    def test_completed_attempt_cannot_reopen_or_replace_output(self):
        with self.attempt() as attempt:
            self.good_formatter(attempt)
            attempt.finish(self.output, cumulative_turns=2)
            before = (self.root / "attempt/events.jsonl").read_bytes()
            with self.assertRaisesRegex(ValueError, "closed"):
                attempt.finish(self.output, cumulative_turns=2)
            self.assertEqual((self.root / "attempt/events.jsonl").read_bytes(), before)

    def test_unsafe_drafts_and_revealing_hashes_never_enter_the_journal_or_errors(self):
        secret = "PRIVACY_CANARY_SYNTHETIC_CONTROL"
        revealing_hash = hashlib.sha256(secret.encode()).hexdigest()
        for index, unsafe in enumerate(({"note": secret}, {"personal_hash": revealing_hash},
                                         {"note": (secret,)}, {"note": float("nan")}, {1: secret})):
            name = "privacy-" + str(index)
            with self.subTest(index=index), self.attempt(name) as attempt:
                with self.assertRaisesRegex(ValueError, "unsafe_formatter") as error:
                    attempt.tool_call("format:1", "StructuredOutput", unsafe)
            persisted = b"".join(path.read_bytes() for path in (self.root / name).iterdir())
            self.assertNotIn(secret.encode(), persisted)
            self.assertNotIn(revealing_hash.encode(), persisted)
            self.assertNotIn(secret, str(error.exception))
            self.assertNotIn(revealing_hash, str(error.exception))

    def test_only_typed_bounded_schema_diagnostics_are_persisted(self):
        for index, diagnostic in enumerate(({"keyword": "pattern", "path": "/R001/PRIVACY_CANARY"},
                                           {"keyword": "type", "path": "/R001", "message": "PRIVATE error prose"},
                                           {"keyword": "unknown", "path": "/R001"}, None)):
            name = "diagnostic-" + str(index)
            with self.subTest(index=index), self.attempt(name) as attempt:
                attempt.tool_call("format:1", "StructuredOutput", {})
                with self.assertRaisesRegex(ValueError, "unsafe_schema_diagnostic"):
                    attempt.tool_result("format:1", is_error=True, schema_diagnostics=[diagnostic])
            log = (self.root / name / "events.jsonl").read_text()
            self.assertNotIn("PRIVACY_CANARY", log)
            self.assertNotIn("PRIVATE error prose", log)

    def test_malformed_tool_id_and_unbounded_diagnostics_fail_closed(self):
        for mode in ("tool_id", "diagnostics"):
            with self.subTest(mode=mode), self.attempt(mode) as attempt:
                attempt.tool_call("format:1", "StructuredOutput", {})
                with self.assertRaises(ValueError):
                    if mode == "tool_id":
                        attempt.tool_result([], is_error=True)
                    else:
                        attempt.tool_result("format:1", is_error=True, schema_diagnostics=iter(()))
                self.assertTrue(attempt.failed)

    def test_failed_model_verdict_does_not_become_financial_acceptance(self):
        self.output["R001"]["status"] = "failed"
        self.output["R001"]["full_artifact_reviewed"] = False
        with self.attempt() as attempt:
            self.good_formatter(attempt)
            result = attempt.finish(self.output, cumulative_turns=2)
        self.assertEqual(result["status"], "completed")
        self.assertFalse(result["financial_acceptance_established"])
        self.assertEqual(rr.consume_reviewer_output(self.contract, self.request, self.prepared, self.output)["status"], "withheld")


if __name__ == "__main__":
    unittest.main()

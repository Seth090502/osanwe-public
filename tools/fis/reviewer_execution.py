"""Prospective local native-review accounting; no model invocation or grading.

Schema corrections belong to the same reserved attempt and its fixed budget.
This public/synthetic journal is not independent custody or tamper-proof quota
accounting. The native launcher must retain its process deadline and turn limit.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import os
from pathlib import Path
import time

import report_review as rr
import workbench as w

SCHEMA = "osanwe.native-review-execution/2"
PROVEN_BINARY = "fd7f35ec7761195ab5ba4eff423e48a78a7849e78f60d93ec31256cdb1a9ec7e"
KEYWORDS = {"type", "const", "enum", "required", "additionalProperties", "pattern", "minLength",
            "maxLength", "minItems", "maxItems", "uniqueItems", "anyOf", "oneOf", "allOf"}
PATH_FIELDS = {"id", "kind", "model", "effort", "status", "context_sha256", "read_only", "full_artifact_reviewed",
               "coverage", "assertions", "obligations", "artifacts", "sources", "methods", "render_checks",
               "not_applicable_checks", "judgments", "rationale", "findings", "severity", "reason", "assertion_ids",
               "artifact_ids", "resolution_artifact", "resolution_verified", "disagreements"} | rr.DIMENSIONS


def classify_tool(name, *, binary_sha256, json_schema_requested, strict_empty_mcp):
    if name == "Read":
        return "read"
    if (name == "StructuredOutput" and binary_sha256 == PROVEN_BINARY
            and json_schema_requested is True and strict_empty_mcp is True):
        return "native_schema_formatter"
    return "prohibited"


class NativeReviewAttempt:
    """Record complete tool events, never thinking blocks or raw error prose."""

    def __init__(self, directory, *, attempt_id, contract, classification, timeout_seconds, max_turns,
                 binary_sha256, json_schema_requested, strict_empty_mcp, clock=time.monotonic):
        w.string(attempt_id, "attempt_id", identifier=True)
        rr._private(attempt_id)
        rr.validate_reviewer_contract(contract)
        if classification not in {"public", "synthetic"}:
            raise ValueError("review attempt requires a public/synthetic canonical producer contract")
        for value in (timeout_seconds, max_turns):
            if type(value) is not int or value <= 0:
                raise ValueError("positive fixed execution budgets required")
        self.policy = dict(binary_sha256=binary_sha256, json_schema_requested=json_schema_requested, strict_empty_mcp=strict_empty_mcp)
        if classify_tool("StructuredOutput", **self.policy) != "native_schema_formatter":
            raise ValueError("native review requires the pinned Read/StructuredOutput boundary")
        self.root = w.safe_path(directory, must_exist=False)
        self.root.mkdir(parents=True, exist_ok=False)
        self.contract = copy.deepcopy(contract)
        self.clock, self.started = clock, clock()
        self.timeout, self.max_turns = timeout_seconds, max_turns
        self.turns, self.calls, self.results, self.counts = 0, {}, {}, {}
        self.closed, self.failed, self.locked_output = False, False, None
        with (self.root / "contract.json").open("xb") as stream:
            stream.write(w.canonical(self.contract) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        self.stream = (self.root / "events.jsonl").open("xb")
        self._record({"event": "reserved", "attempt_id": attempt_id, "schema": SCHEMA, "classification": classification,
                      "timeout_seconds": timeout_seconds, "max_turns": max_turns, "spent_attempts": 1,
                      "contract_sha256": contract["contract_sha256"], "tool_policy": self.policy,
                      "accounting": "local_client_reported", "code_sha256": rr.code_hashes()})

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if not self.closed:
            self._record({"event": "ended", "status": "failed" if self.failed else "abandoned", "spent_attempts": 1})
            self.stream.close()
            self.closed = True

    def _record(self, value):
        if self.closed:
            raise ValueError("attempt is closed; spent attempts cannot be reopened")
        rr._producer_json(value)
        value = {**value, "elapsed_seconds": round(self.clock() - self.started, 6),
                 "recorded_at": datetime.now(timezone.utc).isoformat()}
        self.stream.write(w.canonical(value) + b"\n")
        self.stream.flush()
        os.fsync(self.stream.fileno())

    def _fail(self, code):
        self.failed = True
        self._record({"event": "execution_violation", "code": code})
        raise ValueError(code)

    def _budget(self):
        if self.closed or self.failed:
            raise ValueError("attempt is closed or failed")
        if self.clock() - self.started >= self.timeout:
            self._fail("fixed_wall_time_budget_exhausted")

    def record_turns(self, cumulative_turns):
        self._budget()
        if type(cumulative_turns) is not int or cumulative_turns < self.turns:
            self._fail("turn_counter_cannot_be_reset")
        self.turns = cumulative_turns
        self._record({"event": "turn_count", "cumulative_turns": self.turns})
        if self.turns > self.max_turns:
            self._fail("fixed_turn_budget_exhausted")

    def tool_call(self, tool_id, name, payload):
        self._budget()
        try:
            w.string(tool_id, "tool_id", identifier=True)
            w.string(name, "tool_name", identifier=True)
            rr._private([tool_id, name])
        except (ValueError, TypeError):
            self._fail("unsafe_or_malformed_tool_identity_not_persisted")
        if tool_id in self.calls:
            self._fail("duplicate_tool_call_id")
        category = classify_tool(name, **self.policy)
        self.counts[name] = self.counts.get(name, 0) + 1
        if category == "prohibited":
            self._record({"event": "prohibited_tool", "tool_id": tool_id, "tool": name, "tool_counts": self.counts})
            self._fail("non_read_tool_prohibited")
        event = {"event": "tool_call", "tool_id": tool_id, "tool": name, "category": category}
        if category == "native_schema_formatter":
            try:
                rr._producer_json(payload)
                event["draft"] = copy.deepcopy(payload)
                event["local_schema_valid"] = rr.reviewer_output_schema_valid(self.contract, payload)
            except (ValueError, TypeError, OverflowError, RecursionError):
                # No unsafe text or revealing hash enters the journal.
                self._fail("unsafe_formatter_draft_not_persisted")
            # Preserve safe attempted replacements too, even when they fail the
            # prospective execution rules. Schema-invalid drafts remain editable
            # within the same fixed attempt; they are not delivered verdicts.
            self._record(event)
            previous = [key for key, call in self.calls.items() if call["category"] == "native_schema_formatter"]
            self.calls[tool_id] = event
            if self.locked_output is not None and w.canonical(payload) != self.locked_output:
                self._fail("first_schema_valid_completed_verdict_is_locked")
            if previous:
                last = self.results.get(previous[-1])
                if last is None or not last["is_error"] or not last["schema_diagnostics"]:
                    self._fail("formatter_retry_requires_prior_schema_rejection")
            if event["local_schema_valid"] and payload[self.contract["response_key"]]["status"] == "completed":
                if self.locked_output is None:
                    self.locked_output = w.canonical(payload)
                    self._record({"event": "final_verdict_locked", "tool_id": tool_id})
            return
        self._record(event)
        self.calls[tool_id] = event

    def tool_result(self, tool_id, *, is_error, schema_diagnostics=()):
        self._budget()
        try:
            w.string(tool_id, "tool_id", identifier=True)
            rr._private(tool_id)
        except (ValueError, TypeError):
            self._fail("unsafe_or_malformed_tool_identity_not_persisted")
        if tool_id not in self.calls or tool_id in self.results or type(is_error) is not bool:
            self._fail("unknown_duplicate_or_malformed_tool_result")
        diagnostics = []
        try:
            if not isinstance(schema_diagnostics, (list, tuple)) or len(schema_diagnostics) > w.MAX_ITEMS:
                raise ValueError("bounded concrete schema diagnostics required")
            for item in schema_diagnostics:
                rr._fields(item, "keyword path", label="schema diagnostic")
                parts = item["path"].split("/") if isinstance(item["path"], str) else []
                allowed = PATH_FIELDS | {self.contract["response_key"], ""}
                if (item["keyword"] not in KEYWORDS or len(parts) > 20 or not parts
                        or any(part not in allowed and not (part.isascii() and part.isdigit() and len(part) <= 5) for part in parts)):
                    raise ValueError("unsupported typed schema diagnostic")
                diagnostics.append(copy.deepcopy(item))
        except (KeyError, TypeError, ValueError):
            self._fail("unsafe_schema_diagnostic_not_persisted")
        call = self.calls[tool_id]
        if diagnostics and (call["category"] != "native_schema_formatter" or not is_error):
            self._fail("schema_diagnostic_without_rejected_formatter")
        result = {"event": "tool_result", "tool_id": tool_id, "is_error": is_error, "schema_diagnostics": diagnostics}
        self._record(result)
        self.results[tool_id] = result
        if call["category"] == "native_schema_formatter" and not is_error and not call["local_schema_valid"]:
            self._fail("provider_success_does_not_establish_schema_validity")

    def finish(self, output, *, cumulative_turns):
        self.record_turns(cumulative_turns)
        pending = set(self.calls) - set(self.results)
        formatters = [key for key, call in self.calls.items() if call["category"] == "native_schema_formatter"]
        succeeded = [key for key in formatters if key in self.results and not self.results[key]["is_error"]]
        if (pending or not formatters or len(succeeded) != 1 or succeeded[0] != formatters[-1]
                or any(not self.results[key]["schema_diagnostics"] for key in formatters[:-1])):
            self._fail("formatter_history_missing_pending_or_not_schema_correction")
        try:
            rr._producer_json(output)
            self._record({"event": "final_output", "output": copy.deepcopy(output)})
            matches = w.canonical(output) == w.canonical(self.calls[succeeded[0]]["draft"])
            valid = rr.reviewer_output_schema_valid(self.contract, output)
        except (ValueError, TypeError, OverflowError, RecursionError):
            self._fail("unsafe_final_output_not_persisted")
        if not matches:
            self._fail("final_output_differs_from_successful_formatter")
        if not valid:
            self._fail("final_output_does_not_satisfy_producer_schema")
        result = {"schema": SCHEMA, "status": "completed", "spent_attempts": 1, "cumulative_turns": self.turns,
                  "tool_counts": self.counts, "formatter_drafts": len(formatters), "schema_corrections": len(formatters) - 1,
                  "requires_financial_review": True, "financial_acceptance_established": False,
                  "accounting": "local_client_reported", "final_schema_valid": True,
                  "contract_sha256": self.contract["contract_sha256"]}
        self._record({"event": "ended", **result})
        self.stream.close()
        self.closed = True
        return result

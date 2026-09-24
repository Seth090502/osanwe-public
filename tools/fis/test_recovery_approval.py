#!/usr/bin/env python3
"""Synthetic approval controls, including concurrent same-ledger consumers."""

import json
import multiprocessing
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import approval


def _clock():
    return "2026-01-01T00:00:00Z"


def _parallel_consume(key, ledger, binding, grant, ready, start, result):
    authority = approval.ApprovalAuthority(key, clock=_clock, consumption_path=ledger)
    ready.put(True)
    if not start.wait(10):
        result.put({"ok": False, "codes": ["TEST_TIMEOUT"]})
        return
    record = approval.DecisionRecord(binding=binding,
        state=approval.STATE_HUMAN_APPROVAL_REQUIRED)
    verdict = authority.verify(record, grant=grant, now="2026-01-01T00:20:00Z")
    result.put({"ok": verdict.ok, "codes": verdict.codes})


class ApprovalRecovery(unittest.TestCase):
    def setUp(self):
        self.key = approval.generate_key()
        self.binding = approval.DecisionBinding(
            decision_id="RECOVERY-SYNTHETIC", decision_type="rebalance_proposal",
            legs=(approval.Leg("L1", "SELL", "SYNTH", "synthetic", quantity=1),),
            account="synthetic", model_version="m", data_version="d",
            policy_version="p", code_hash="c", price_as_of="2026-01-01",
            expires_at="2026-01-02T00:00:00Z", requested_by="research-agent")

    def pending(self, state=approval.STATE_HUMAN_APPROVAL_REQUIRED):
        return approval.DecisionRecord(binding=self.binding, state=state)

    def authority(self, path=None, **kwargs):
        return approval.ApprovalAuthority(self.key, clock=_clock,
                                         consumption_path=path, **kwargs)

    def issue(self, authority):
        authority.registry.register("synthetic-human", "Synthetic Human",
                                    registered_by="test-setup")
        return authority.issue(self.pending(), "synthetic-human")

    def test_existing_instances_cannot_both_consume(self):
        with tempfile.TemporaryDirectory(prefix="approval-recovery-") as td:
            path = os.path.join(td, "consumed.jsonl")
            first, second = self.authority(path), self.authority(path)
            grant = self.issue(first)
            self.assertTrue(first.verify(self.pending(), grant=grant).ok)
            again = second.verify(self.pending(), grant=grant)
            self.assertFalse(again.ok)
            self.assertIn("REPLAYED_APPROVAL", again.codes)

    def test_processes_serialize_same_ledger_consumption(self):
        with tempfile.TemporaryDirectory(prefix="approval-recovery-") as td:
            path = os.path.join(td, "consumed.jsonl")
            grant = self.issue(self.authority(path))
            ctx = multiprocessing.get_context("spawn")
            ready, results, start = ctx.Queue(), ctx.Queue(), ctx.Event()
            processes = [ctx.Process(target=_parallel_consume,
                args=(self.key, path, self.binding, grant, ready, start, results))
                for _ in range(2)]
            try:
                for process in processes:
                    process.start()
                for _ in processes:
                    self.assertTrue(ready.get(timeout=10))
                start.set()
                outcomes = [results.get(timeout=10) for _ in processes]
                self.assertEqual(sum(row["ok"] for row in outcomes), 1, outcomes)
                for process in processes:
                    process.join(10)
                    self.assertEqual(process.exitcode, 0)
                self.assertEqual(len(Path(path).read_text().splitlines()), 1)
                self.assertFalse(self.authority(path).verify(self.pending(), grant=grant).ok)
            finally:
                for process in processes:
                    if process.is_alive():
                        process.terminate()
                        process.join(5)
                for queue in (ready, results):
                    queue.close()

    def test_lock_contention_refuses_without_consuming(self):
        with tempfile.TemporaryDirectory(prefix="approval-recovery-") as td:
            path = os.path.join(td, "consumed.jsonl")
            authority = self.authority(path)
            grant = self.issue(authority)
            Path(path + ".lock").write_text("synthetic other consumer", encoding="ascii")
            verdict = authority.verify(self.pending(), grant=grant)
            self.assertFalse(verdict.ok)
            self.assertIn("APPROVAL_LOCKED", verdict.codes)
            self.assertFalse(Path(path).exists())
            self.assertTrue(Path(path + ".lock").exists())

    def test_corrupt_ledger_refuses_without_rewriting(self):
        for corruption in ('{"grant_id":', '{}\n', '[]\n'):
            with self.subTest(corruption=corruption), tempfile.TemporaryDirectory(
                    prefix="approval-recovery-") as td:
                path = os.path.join(td, "consumed.jsonl")
                authority = self.authority(path)
                grant = self.issue(authority)
                Path(path).write_text(corruption, encoding="ascii")
                verdict = authority.verify(self.pending(), grant=grant)
                self.assertFalse(verdict.ok)
                self.assertIn("CONSUMPTION_LEDGER_CORRUPT", verdict.codes)
                self.assertEqual(Path(path).read_text(), corruption)

    def test_failed_persistence_never_returns_authority(self):
        with tempfile.TemporaryDirectory(prefix="approval-recovery-") as td:
            authority = self.authority(os.path.join(td, "consumed.jsonl"))
            grant = self.issue(authority)
            with mock.patch.object(approval, "_atomic_append_line", side_effect=OSError("synthetic disk failure")):
                verdict = authority.verify(self.pending(), grant=grant)
            self.assertFalse(verdict.ok)
            self.assertEqual(verdict.authority_level, "NONE")

    def test_terminal_records_cannot_gain_simulation_authority(self):
        grant = self.issue(self.authority())
        for state in (approval.STATE_REJECTED, approval.STATE_EXPIRED,
                      approval.STATE_INVALIDATED, approval.STATE_DRAFT_ANALYSIS):
            with self.subTest(state=state):
                verdict = self.authority().verify(self.pending(state), grant=grant)
                self.assertFalse(verdict.ok)
                self.assertEqual(verdict.authority_level, "NONE")

    def test_agent_override_does_not_bypass_registry(self):
        authority = self.authority(allow_agent_approver=True)
        with self.assertRaises(approval.ApprovalViolation):
            authority.issue(self.pending(), "automation")
        grant = self.issue(authority)
        self.assertEqual(grant.state_granted, approval.STATE_APPROVED_FOR_SIMULATION)

    def test_recursive_execution_claims_are_refused(self):
        for obj in ({"executable": True}, {"execution": {"authorized": True}},
                    {"nested": [{"approved": True}]},
                    [{"nested": {"authorized_for_execution": True}}],
                    {"executable": "true"}, {"authorized": 1}):
            with self.subTest(obj=obj):
                with self.assertRaises(approval.ApprovalViolation):
                    approval.enforce_not_executable(obj)

    def test_inert_nested_envelopes_remain_valid(self):
        approval.enforce_not_executable({"executable": False,
            "execution": {"authorized": False}, "nested": [{"approved": False}]})

    def test_typed_decision_record_remains_valid_at_boundary(self):
        approval.enforce_not_executable(self.pending())

    def test_execution_purpose_remains_refused(self):
        authority = self.authority()
        grant = self.issue(authority)
        verdict = authority.authorize(self.pending(), grant=grant, purpose="EXECUTION")
        self.assertFalse(verdict.ok)
        self.assertEqual(verdict.authority_level, "NONE")


if __name__ == "__main__":
    unittest.main()

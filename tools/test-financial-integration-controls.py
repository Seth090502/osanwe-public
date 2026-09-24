"""Synthetic cross-harness policy and honest health-state regressions."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("integration_checkall", ROOT / ".agents/scripts/checkall.py")
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


class IntegrationControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for path in (".agents/roles", ".claude/agents", ".claude/workflows", ".vault-substrate"):
            (self.root / path).mkdir(parents=True)
        (self.root / ".vault-substrate/reindex-runner.mjs").write_text("// synthetic owner")

    def policy(self, source="", role="---\nname: analyst\n---\n"):
        (self.root / ".claude/workflows/research.js").write_text(source)
        (self.root / ".agents/roles/analyst.md").write_text(role)
        (self.root / ".claude/agents/analyst.md").write_text(role)
        with patch.object(checks, "ROOT", str(self.root)):
            return checks.step_workflow_pins()[0]

    def test_session_inheritance_and_explicit_caller_options_are_allowed(self):
        self.assertTrue(self.policy("agent(prompt, {agentType: 'analyst', ...opts})"))

    def test_obsolete_literal_production_pins_are_rejected(self):
        self.assertFalse(self.policy("agent(prompt, {model: 'opus', effort: 'high'})"))
        self.assertFalse(self.policy(role="---\nname: analyst\nmodel: opus\n---\n"))

    def test_unknown_role_does_not_gain_authority(self):
        self.assertFalse(self.policy("agent(prompt, {agentType: 'missing-reviewer'})"))

    def observe(self, state, rc, needs_rebuild=True, generation=None):
        value = {"schema": "osanwe.retrieval-health/1", "state": state,
                 "generation_id": generation, "needs_rebuild": needs_rebuild}
        with patch.object(checks.Path, "home", return_value=self.root), \
             patch.object(checks.shutil, "which", return_value="node"), \
             patch.object(checks, "run", return_value=(rc, json.dumps(value))):
            good, out = checks.step_retrieval_integrity()
            return checks.result_state(good, out)

    def test_zero_exit_cannot_make_inconsistent_generation_healthy(self):
        self.assertEqual(self.observe("passed", 0, True, "synthetic:g1"), "failed")
        self.assertEqual(self.observe("passed", 0, False, None), "failed")
        self.assertEqual(self.observe("passed", 0, False, "synthetic:g1"), "passed")

    def test_unavailable_and_stale_stay_distinct(self):
        self.assertEqual(self.observe("unavailable", 3), "unavailable")
        self.assertEqual(self.observe("stale", 2), "stale")
        self.assertEqual(self.observe("stale", 0), "failed")

    def documents(self, documents, exclusions):
        payload = {"schema": "osanwe.financial-document-manifest/1",
                   "documents": documents, "exclusions": exclusions}
        with patch.object(checks, "run", return_value=(0, json.dumps(payload))):
            good, out = checks.step_financial_document_admission()
            return checks.result_state(good, out)

    def test_empty_or_excluded_corpus_is_not_admitted_as_healthy(self):
        self.assertEqual(self.documents([], []), "unavailable")
        self.assertEqual(self.documents([{"chunks": [{}]}], [{"reason": "source_changed"}]), "stale")
        self.assertEqual(self.documents([{"chunks": [{}]}], []), "passed")

    def test_intentional_history_filtering_does_not_mark_current_sources_stale(self):
        old = [{"reason": reason} for reason in ("superseded", "retracted", "scope_not_approved")]
        self.assertEqual(self.documents([{"chunks": [{}]}], old), "passed")
        self.assertEqual(self.documents([], old), "unavailable")
        self.assertEqual(self.documents([{"chunks": [{}]}], old + [{"reason": "source_changed"}]), "stale")
        self.assertEqual(self.documents([], ["malformed"]), "failed")

    def test_daily_profile_observes_corpus_and_index_without_inference_controls(self):
        daily = dict(checks.selected_steps(quick=True))
        self.assertIn("financial-document-admission", daily)
        self.assertIn("retrieval-integrity", daily)
        self.assertNotIn("evaluator-controls", daily)
        self.assertNotIn("finance-data-tests", daily)
        self.assertNotIn("retrieval-controls", daily)


if __name__ == "__main__":
    unittest.main()

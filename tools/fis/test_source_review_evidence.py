"""Append-only integration and numeric source-token regression controls."""
import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

import evidence
from ontology import Ontology
from test_research_evidence import NOW, claim


class SourceReviewEvidenceTests(unittest.TestCase):
    def test_source_parenthesized_grouped_loss_is_not_positive_or_invalid(self):
        import report_review
        from decimal import Decimal
        self.assertEqual(report_review._number("(4,901)"), Decimal(-4901))
        self.assertEqual(report_review._number("+1.16"), Decimal("1.16"))
        self.assertTrue(evidence.numeric_token_in_text("+1.16", "Change +1.16 pp"))
        self.assertFalse(evidence.numeric_token_in_text("1.16", "Change +1.16 pp"))
        text = "Operating loss (4,901) USD millions"
        c = claim(value=-4901)
        source = {"id": c["source"], "uri": "synthetic:statement", "retrieved_at": c["retrieved_at"],
                  "available_at": c["available_at"], "content_sha256": hashlib.sha256(text.encode()).hexdigest()}
        mapping = {"claim_id": c["id"], "original_label": "Operating loss", "normalized_metric": c["metric"],
                   "value_token": "(4,901)", "multiplier": 1,
                   **{key: c[key] for key in ("unit", "currency", "basis", "as_of", "period_start", "period_end")},
                   "support": {"artifact_id": "source", "start": 0, "end": len(text), "text": text, "locator": "Synthetic loss row"}}
        review = {"id": "inspection", "source_id": c["source"], "snapshot_artifact": "source", "source_version": "original",
                  "origin_uri": source["uri"], "relationship": "direct", "revision_status": "original", "supersedes": [],
                  "inspected_at": NOW, "inspected_by": "fixture", "mappings": [mapping]}
        evidence.validate_source_review(review, source, [c], text.encode(), knowledge_cutoff=NOW, report_at=NOW)
        for bad in ("(49,01)", "(4,901", "4,901"):
            mapping["value_token"] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                evidence.validate_source_review(review, source, [c], text.encode(), knowledge_cutoff=NOW, report_at=NOW)

    def test_source_number_must_not_be_a_substring_of_another_number(self):
        for token, text in (("100", "1100"), ("100", "-100"), ("100", "100.5"), ("100", "100,000"), ("100", "(100)")):
            with self.subTest(token=token, text=text):
                self.assertFalse(evidence.numeric_token_in_text(token, text))
        for token, text in (("100", "Revenue 100 USD"), ("-100", "Loss -100 USD"), ("(100)", "Loss (100) USD")):
            self.assertTrue(evidence.numeric_token_in_text(token, text))

    def test_new_integration_writes_draft_and_revisions_do_not_rewrite_history(self):
        with tempfile.TemporaryDirectory() as td:
            onto = Ontology(str(Path(td) / "ontology.db"))
            try:
                first = claim()
                first["entity"] = "instr:synthetic"
                onto.add_entity("instrument", first["entity"], "Synthetic issuer")
                original_id = evidence.add_integration_draft(onto, first, classification="synthetic", report_at=NOW)
                original = dict(onto._conn.execute("SELECT * FROM fact WHERE id=?", (original_id,)).fetchone())
                self.assertEqual(original["validation_status"], "draft")
                revision = copy.deepcopy(first)
                revision.update(value=125, available_at="2026-08-15T00:00:00Z", retrieved_at="2026-09-12T11:00:00Z")
                revision_id = evidence.add_integration_draft(onto, revision, classification="synthetic", report_at=NOW)
                self.assertNotEqual(original_id, revision_id)
                self.assertEqual(original, dict(onto._conn.execute("SELECT * FROM fact WHERE id=?", (original_id,)).fetchone()))
                old_view = onto.facts(first["entity"], first["metric"], knowledge_date="2026-08-01")
                new_view = onto.facts(first["entity"], first["metric"], knowledge_date="2026-09-01")
                self.assertEqual(old_view[0]["value_num"], 120)
                self.assertEqual(new_view[0]["value_num"], 125)
                self.assertEqual(new_view[0]["validation_status"], "draft")
            finally:
                onto.close()

    def test_personal_or_invalid_claim_never_reaches_ontology(self):
        class RefuseWrites:
            def add_fact(self, **kwargs):
                raise AssertionError("ineligible claim reached persistence")
        for classification, changed in (("personal", {}), ("synthetic", {"value": None}),
                                         ("public", {"currency": "NONE"})):
            with self.subTest(classification=classification, changed=changed), self.assertRaises(ValueError):
                evidence.add_integration_draft(RefuseWrites(), claim(**changed), classification=classification, report_at=NOW)


if __name__ == "__main__":
    unittest.main()

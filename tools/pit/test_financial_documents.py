"""Frozen synthetic acceptance cases for document admission; no vault-body reads."""
from __future__ import annotations
import copy
from contextlib import redirect_stdout
from datetime import datetime, timezone
from hashlib import sha256
import json
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import dataset_registry as registry

STAMP = "2026-09-13T18:00:00+00:00"
LATER = "2026-09-14T18:00:00+00:00"
TEXT = "# Margin example\n\nRevenue is 100 units and cost is 75 units.\nThe accounting margin is 25 percent.\nThis is an illustration, not a forecast.\n"
SOURCE = "Operating margin equals operating income divided by revenue.\nThis synthetic example uses revenue 100 and cost 75.\nThe result is an identity, not a forecast.\n"


class DocumentAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "docs").mkdir()
        (self.root / "sources").mkdir()
        (self.root / "docs/margin.md").write_text(TEXT, encoding="utf-8", newline="")
        (self.root / "sources/margin.txt").write_text(SOURCE, encoding="utf-8", newline="")
        self.path = self.root / "registry.jsonl"

    def candidate(self, classification="SYNTHETIC"):
        digest = sha256(TEXT.encode()).hexdigest()
        loc = {"start_line": 1, "end_line": 5, "text": TEXT}
        return {"schema": "osanwe.financial-document-version/1", "document_id": "doc:margin",
                "source_version": "1", "source_origin_id": "origin:fixture-document", "source_uri": "synthetic:margin-document",
                "source_path": "docs/margin.md", "sha256": digest, "classification": classification,
                "source_kind": "worked_example", "kind": "method_reference", "status": "candidate",
                "approved_use": ["accounting"], "applicability": {"applies_when": ["A same-period accounting identity is needed."],
                    "not_applicable_when": ["Forecasting cost behavior."], "required_inputs": ["Positive revenue and matching-period cost."],
                    "limitations": ["Synthetic arithmetic only."], "alternatives": ["Report the source amounts directly."]},
                "published_at": None, "available_at": STAMP, "reviewed_at": STAMP, "supersedes": [],
                "privacy_review": {"classification": classification, "sha256": digest, "reviewed_by": "reviewer:privacy",
                                   "reviewed_at": STAMP, "scope": "whole_document"},
                "sources": [{"source_id": "source:margin", "origin_id": "origin:fixture-source", "source_version": "1",
                             "uri": "synthetic:margin-source", "snapshot_path": "sources/margin.txt", "sha256": sha256(SOURCE.encode()).hexdigest(),
                             "classification": classification, "source_kind": "synthetic_example", "retrieved_at": STAMP, "available_at": STAMP,
                             "privacy_review": {"classification": classification, "sha256": sha256(SOURCE.encode()).hexdigest(),
                                                "reviewed_by": "reviewer:privacy", "reviewed_at": STAMP, "scope": "whole_document"}}],
                "claims": [{"claim_id": "claim:margin", "kind": "worked_example", "document_locator": loc,
                            "supports": [{"source_id": "source:margin", "locator": {"start_line": 1, "end_line": 3, "text": SOURCE}}],
                            "example_ids": ["example:margin"], "independent_origin_count": 1}],
                "chunks": [{"chunk_id": "chunk:margin", "locator": {"start_line": 1, "end_line": 5, "heading": "Margin example"},
                            "approved_use": ["accounting"], "claim_ids": ["claim:margin"]}],
                "source_review": {"reviewed_by": "reviewer:source", "reviewed_at": STAMP, "claim_ids": ["claim:margin"], "findings": []},
                "worked_examples": [{"example_id": "example:margin", "inputs": {
                    "revenue": {"value": 100, "unit": "units", "currency": "NONE", "basis": "nominal"},
                    "cost": {"value": 75, "unit": "units", "currency": "NONE", "basis": "nominal"}},
                    "expression": "(revenue-cost)/revenue", "result": "0.25", "unit": "fraction", "currency": "NONE",
                    "independent_result": {"numerator": 1, "denominator": 4, "checked_by": "reviewer:independent", "method": "exact_fraction"}}]}

    def approve(self, candidate=None):
        return registry.append_document_version(self.path, candidate or self.candidate(), self.root, admitted_at=STAMP)

    def manifest(self, **kwargs):
        return registry.approved_document_manifest(self.path, self.root, **kwargs)

    def rejection(self, candidate, code=None):
        with self.assertRaises(registry.DocumentAdmissionError) as caught:
            registry.admit_document(candidate, self.root, admitted_at=STAMP)
        if code: self.assertEqual(caught.exception.code, code)

    def test_valid_synthetic_exact_scope(self):
        self.approve()
        result = self.manifest(as_of=STAMP, scope="accounting")
        self.assertEqual(result["schema"], "osanwe.financial-document-manifest/1")
        self.assertEqual(len(result["documents"]), 1)
        doc = result["documents"][0]
        self.assertTrue(doc["eligible"])
        self.assertEqual(doc["classification"], "SYNTHETIC")
        self.assertEqual(doc["supporting_origin_ids"], ["origin:fixture-source"])
        chunk = doc["chunks"][0]
        self.assertEqual(TEXT.encode()[chunk["start_byte"]:chunk["end_byte"]], TEXT.encode())
        self.assertNotIn("text", chunk)

    def test_explicit_public_record_can_be_admitted(self):
        self.approve(self.candidate("PUBLIC"))
        self.assertEqual(self.manifest(as_of=STAMP)["documents"][0]["classification"], "PUBLIC")

    def test_unknown_mixed_personal_rejected_before_file_read(self):
        for classification in ("UNKNOWN", "MIXED", "PERSONAL"):
            with self.subTest(classification=classification), patch.object(Path, "read_bytes", side_effect=AssertionError("body must not be read")):
                self.rejection(self.candidate(classification), "classification_not_approved")

    def test_financial_path_does_not_approve_unknown(self):
        item = self.candidate("UNKNOWN")
        item["source_path"] = "wiki/research/approved-looking-finance.md"
        self.rejection(item, "classification_not_approved")

    def test_mixed_support_rejected_before_content_read(self):
        item = self.candidate()
        item["sources"][0]["classification"] = "MIXED"
        with patch.object(Path, "read_bytes", side_effect=AssertionError("body must not be read")):
            self.rejection(item, "classification_not_approved")

    def test_source_checked_flag_is_not_approval(self):
        item = self.candidate()
        item["source_checked"] = True
        item["sources"] = []
        item["source_review"] = {}
        self.rejection(item)

    def test_denied_and_traversal_paths_fail_before_reads(self):
        for path in ("../outside.md", "C:/outside.md", "private/secret.md", "finance/account.md", "docs/secret.local.md", "docs/.env", "docs/auth.json"):
            with self.subTest(path=path):
                item = self.candidate()
                item["source_path"] = path
                with patch.object(Path, "read_bytes", side_effect=AssertionError("body must not be read")):
                    self.rejection(item, "unsafe_path")

    def test_missing_citation_is_rejected(self):
        item = self.candidate()
        item["claims"][0]["supports"][0]["source_id"] = "source:invented-citation"
        self.rejection(item, "unknown_source_reference")

    def test_fabricated_inspected_passage_rejected(self):
        item = self.candidate()
        item["claims"][0]["supports"][0]["locator"]["text"] = "A fabricated citation that was never in the original."
        self.rejection(item, "locator_text_mismatch")

    def test_duplicate_origin_not_independent_corroboration(self):
        item = self.candidate()
        mirror = copy.deepcopy(item["sources"][0])
        mirror.update(source_id="source:mirror", uri="synthetic:mirror")
        item["sources"].append(mirror)
        support = copy.deepcopy(item["claims"][0]["supports"][0])
        support["source_id"] = "source:mirror"
        item["claims"][0]["supports"].append(support)
        item["claims"][0]["independent_origin_count"] = 2
        self.rejection(item, "origin_count_mismatch")
        item["claims"][0]["independent_origin_count"] = 1
        self.approve(item)
        self.assertEqual(self.manifest(as_of=STAMP)["documents"][0]["supporting_origin_ids"], ["origin:fixture-source"])

    def test_same_source_uri_cannot_invent_an_origin(self):
        item = self.candidate()
        mirror = copy.deepcopy(item["sources"][0])
        mirror.update(source_id="source:mirror", origin_id="origin:invented")
        item["sources"].append(mirror)
        self.rejection(item, "source_origin_conflict")

    def test_bad_locator_bounds_or_heading(self):
        for update in ({"start_line": 0}, {"end_line": 100}, {"heading": "Invented heading"}):
            item = self.candidate()
            item["chunks"][0]["locator"].update(update)
            self.rejection(item)

    def test_unreviewed_claim_is_ineligible(self):
        item = self.candidate()
        item["source_review"]["claim_ids"] = []
        self.rejection(item, "review_coverage_incomplete")

    def test_uncovered_text_cannot_ride_with_an_approved_chunk(self):
        item = self.candidate()
        item["claims"][0]["document_locator"] = {"start_line": 1, "end_line": 4, "text": "".join(TEXT.splitlines(keepends=True)[:4])}
        self.rejection(item, "unreviewed_chunk_content")

    def test_major_review_finding_blocks_admission(self):
        item = self.candidate()
        item["source_review"]["findings"] = [{"severity": "major", "status": "open", "claim_id": "claim:margin"}]
        self.rejection(item, "unresolved_material_finding")

    def test_independent_calculation_must_match_expression_and_result(self):
        for field, value in (("result", "0.30"), ("independent_result", {"numerator": 3, "denominator": 10, "checked_by": "reviewer:independent", "method": "exact_fraction"})):
            item = self.candidate()
            item["worked_examples"][0][field] = value
            self.rejection(item, "worked_example_mismatch")

    def test_zero_denominator_nonfinite_and_executable_expression(self):
        for expression in ("revenue/(cost-cost)", "__import__('os').system('bad')", "revenue*1e9999"):
            item = self.candidate()
            item["worked_examples"][0]["expression"] = expression
            self.rejection(item)

    def test_units_cannot_be_relabelled(self):
        item = self.candidate()
        item["worked_examples"][0]["unit"] = "USD"
        self.rejection(item, "worked_example_units")

    def test_future_source_cannot_be_used_before_availability(self):
        item = self.candidate()
        item["sources"][0]["available_at"] = LATER
        self.rejection(item, "availability_violation")

    def test_modified_document_excluded_without_current_hash_disclosure(self):
        self.approve()
        changed = b"PERSONAL_FINANCE_CANARY account_id=123456789"
        (self.root / "docs/margin.md").write_bytes(changed)
        result = self.manifest(as_of=STAMP)
        self.assertEqual(result["documents"], [])
        self.assertEqual(result["exclusions"][0]["reason"], "source_hash_mismatch")
        encoded = json.dumps(result)
        self.assertNotIn(sha256(changed).hexdigest(), encoded)
        self.assertNotIn("123456789", encoded)

    def test_missing_or_changed_support_invalidates_current_use(self):
        for changed in (False, True):
            with self.subTest(changed=changed):
                self.path.unlink(missing_ok=True)
                (self.root / "sources/margin.txt").write_text(SOURCE, encoding="utf-8", newline="")
                self.approve()
                if changed: (self.root / "sources/margin.txt").write_text("changed", encoding="utf-8")
                else: (self.root / "sources/margin.txt").unlink()
                self.assertEqual(self.manifest(as_of=STAMP)["documents"], [])

    def test_same_version_cannot_rewrite_history(self):
        self.approve()
        before = self.path.read_bytes()
        self.approve()
        self.assertEqual(self.path.read_bytes(), before)
        item = self.candidate()
        item["applicability"]["limitations"].append("Different claim scope.")
        with self.assertRaises(registry.DocumentAdmissionError): self.approve(item)
        self.assertEqual(self.path.read_bytes(), before)

    def test_supersession_is_point_in_time_and_append_only(self):
        self.approve()
        before = self.path.read_bytes()
        item = self.candidate()
        item.update(source_version="2", available_at=LATER, reviewed_at=LATER, supersedes=["doc:margin@1"])
        item["privacy_review"]["reviewed_at"] = LATER
        item["source_review"]["reviewed_at"] = LATER
        registry.append_document_version(self.path, item, self.root, admitted_at=LATER)
        self.assertTrue(self.path.read_bytes().startswith(before))
        self.assertEqual(self.manifest(as_of=STAMP)["documents"][0]["source_version"], "1")
        self.assertEqual(self.manifest(as_of=LATER)["documents"][0]["source_version"], "2")

    def test_scope_mismatch_is_explicit(self):
        self.approve()
        result = self.manifest(as_of=STAMP, scope="tax")
        self.assertEqual(result["documents"], [])
        self.assertEqual(result["exclusions"][0]["reason"], "scope_not_approved")

    def test_manifest_is_deterministic_and_does_not_include_excerpts(self):
        self.approve()
        first, second = self.manifest(as_of=STAMP), self.manifest(as_of=STAMP)
        self.assertEqual(first["manifest_sha256"], second["manifest_sha256"])
        self.assertNotIn("Revenue is 100", json.dumps(first))

    def test_inventory_is_metadata_only(self):
        with patch.object(Path, "read_bytes", side_effect=AssertionError("inventory must not read bodies")):
            inventory = registry.inventory_financial_documents(["docs/margin.md"], self.root)
        row = inventory["documents"][0]
        self.assertEqual(row["classification"], "UNKNOWN")
        self.assertFalse(row["content_inspected"])
        self.assertNotIn("sha256", row)
        self.assertNotIn("text", row)

    def test_registry_tampering_does_not_restore_eligibility(self):
        self.approve()
        row = json.loads(self.path.read_text())
        row["approved_use"].append("tax")
        self.path.write_text(json.dumps(row) + "\n")
        with self.assertRaises(registry.DocumentAdmissionError): self.manifest(as_of=STAMP)

    def test_public_claim_cannot_rely_only_on_a_synthetic_source(self):
        item = self.candidate("PUBLIC")
        item["claims"][0]["kind"] = "reported_fact"
        item["sources"][0]["classification"] = "SYNTHETIC"
        item["sources"][0]["privacy_review"]["classification"] = "SYNTHETIC"
        self.rejection(item, "synthetic_source_cannot_establish_reported_fact")

    def test_legacy_dataset_validation_interface_remains(self):
        row = {key: "fixture" for key in registry.REQUIRED_FIELDS}
        row.update(license_status="verified-self-produced", transformation_lineage={"parent_dataset_ids": [], "script_paths": []}, known_defects=[], validation_tests=[])
        self.assertEqual(registry.validate_entry(row), [])
        self.assertEqual(registry.REGISTRY_VERSION, "3")

    def test_retraction_preserves_history_and_blocks_current_selection(self):
        self.approve()
        before = self.path.read_bytes()
        registry.append_document_retraction(self.path, "doc:margin", "2", self.root, available_at=LATER,
                                            reviewed_by="reviewer:source", reason_code="source_retracted")
        self.assertTrue(self.path.read_bytes().startswith(before))
        self.assertEqual(self.manifest(as_of=STAMP)["documents"][0]["source_version"], "1")
        self.assertEqual(self.manifest(as_of=LATER)["documents"], [])
        self.assertEqual(self.manifest(as_of=LATER)["exclusions"][-1]["reason"], "retracted")

    def test_competing_writer_does_not_overwrite_registry(self):
        self.approve()
        before = self.path.read_bytes()
        Path(str(self.path) + ".lock").write_text("held")
        with self.assertRaises(registry.DocumentAdmissionError) as caught: self.approve()
        self.assertEqual(caught.exception.code, "registry_busy")
        self.assertEqual(self.path.read_bytes(), before)

    def test_symlink_document_is_not_an_approved_path(self):
        try: (self.root / "docs/link.md").symlink_to(self.root / "docs/margin.md")
        except OSError: self.skipTest("Symlink creation unavailable; traversal/path controls remain required")
        item = self.candidate()
        item["source_path"] = "docs/link.md"
        self.rejection(item, "unsafe_path")

    def test_detectable_private_marker_is_not_made_public_by_declaration(self):
        item = self.candidate("PUBLIC")
        text = TEXT + "PERSONAL_FINANCE_CANARY account_id=123456789\n"
        (self.root / "docs/margin.md").write_text(text, encoding="utf-8", newline="")
        item["sha256"] = sha256(text.encode()).hexdigest()
        item["privacy_review"]["sha256"] = item["sha256"]
        self.rejection(item, "privacy_marker")

    # These focused metadata regressions were added after the original 33-case
    # freeze; they are development controls, not additional unseen evidence.
    def test_unknown_metadata_fields_cannot_be_persisted(self):
        item = self.candidate()
        item["unapproved_notes"] = "unreviewed material"
        self.rejection(item, "unexpected_metadata_fields")

    def test_private_metadata_cannot_be_hashed_into_public_registry(self):
        item = self.candidate()
        item["applicability"]["limitations"].append("PERSONAL_FINANCE_CANARY account_id=123456789")
        self.rejection(item, "privacy_marker")
        self.assertFalse(self.path.exists())

    def test_duplicate_json_keys_cannot_hide_registry_content(self):
        self.approve()
        raw = self.path.read_bytes().replace(b'"classification":"SYNTHETIC"', b'"classification":"PERSONAL","classification":"SYNTHETIC"', 1)
        self.path.write_bytes(raw)
        with self.assertRaises(registry.DocumentAdmissionError) as caught: self.manifest(as_of=STAMP)
        self.assertEqual(caught.exception.code, "registry_duplicate_key")

    def test_resolved_flag_does_not_replace_material_resolution_evidence(self):
        item = self.candidate()
        item["source_review"]["findings"] = [{"severity": "major", "status": "resolved", "claim_id": "claim:margin", "resolution_verified": True}]
        self.rejection(item, "unresolved_material_finding")

    def portable_candidate(self):
        item = self.candidate()
        item["approved_use"].append("portable-context")
        item["chunks"][0]["approved_use"].append("portable-context")
        item["reuse"] = {"basis": "original_authorship", "document_sha256": item["sha256"],
                         "reviewed_by": "reviewer:reuse", "reviewed_at": STAMP, "scope": "approved_chunks_only",
                         "evidence": "Original synthetic fixture text authored for this test.", "sources_included": False}
        return item

    def literal_candidate(self):
        item = self.candidate()
        original = {"example_id": "example:margin", "expression": "(100-75)/100", "result": 0.25,
                    "expected_fraction": {"numerator": 1, "denominator": 4}, "unit": "fraction", "currency": None,
                    "basis": "accounting identity", "classification": "SYNTHETIC"}
        code = b"assert (100 - 75) / 100 == .25\n"
        receipt = {"classification": "SYNTHETIC", "passed": True, "tests_run": 1, "failures": 0, "errors": 0,
                   "test_file_sha256": sha256(code).hexdigest(), "examples": [original]}
        blobs = {"evidence:receipt": ("sources/receipt.json", json.dumps(receipt).encode()),
                 "evidence:code": ("sources/test_fixture.py", code)}
        item["validation_evidence"] = []
        for identity, (relative, raw) in blobs.items():
            (self.root / relative).write_bytes(raw)
            digest = sha256(raw).hexdigest()
            item["validation_evidence"].append({"evidence_id": identity, "source_path": relative,
                "sha256": digest, "classification": "SYNTHETIC", "kind": "worked_example_evidence",
                "privacy_review": {"classification": "SYNTHETIC", "sha256": digest, "reviewed_by": "reviewer:privacy",
                                   "reviewed_at": STAMP, "scope": "whole_document"}})
        item["worked_examples"] = [{key: original[key] for key in ("example_id", "expression", "result", "unit", "currency", "basis")}]
        item["worked_examples"][0].update(mode="literal_fixture", inputs={},
            independent_result={"numerator": 1, "denominator": 4, "checked_by": "reviewer:independent", "method": "exact_fraction"},
            evidence_ref={"evidence_id": "evidence:receipt", "code_evidence_id": "evidence:code", "pointer": "/examples/0"})
        return item

    def test_portability_needs_exact_reuse_approval(self):
        item = self.portable_candidate()
        del item["reuse"]
        self.rejection(item, "portable_reuse_unapproved")
        item = self.portable_candidate()
        item["reuse"]["document_sha256"] = "0" * 64
        self.rejection(item, "portable_reuse_unapproved")

    def test_portability_does_not_include_original_sources(self):
        item = self.portable_candidate()
        item["reuse"]["sources_included"] = True
        self.rejection(item, "portable_reuse_unapproved")
        self.approve(self.portable_candidate())
        row = self.manifest(scope="portable-context")["documents"][0]
        self.assertEqual(row["reuse"]["scope"], "approved_chunks_only")
        self.assertFalse(row["reuse"]["sources_included"])

    def test_literal_example_binds_actual_receipt_and_code(self):
        self.approve(self.literal_candidate())
        row = self.manifest()["documents"][0]
        self.assertTrue(row["eligible"])
        (self.root / "sources/test_fixture.py").write_bytes(b"changed\n")
        self.assertEqual(self.manifest()["exclusions"][0]["reason"], "source_hash_mismatch")

    def test_literal_example_labels_cannot_silently_change(self):
        item = self.literal_candidate()
        item["worked_examples"][0]["unit"] = "million"
        self.rejection(item, "worked_example_evidence_mismatch")

    def test_literal_example_rejects_missing_or_invalid_pointers(self):
        for pointer in ("/examples/1", "/examples/-1", "/passed", "/examples/00"):
            with self.subTest(pointer=pointer):
                item = self.literal_candidate()
                item["worked_examples"][0]["evidence_ref"]["pointer"] = pointer
                self.rejection(item)

    def test_literal_example_recomputes_recorded_expression(self):
        item = self.literal_candidate()
        receipt_path = self.root / "sources/receipt.json"
        receipt = json.loads(receipt_path.read_bytes())
        receipt["examples"][0]["expression"] = "(100-74)/100"
        raw = json.dumps(receipt).encode()
        receipt_path.write_bytes(raw)
        item["validation_evidence"][0]["sha256"] = sha256(raw).hexdigest()
        item["validation_evidence"][0]["privacy_review"]["sha256"] = sha256(raw).hexdigest()
        item["worked_examples"][0]["expression"] = receipt["examples"][0]["expression"]
        self.rejection(item, "worked_example_mismatch")

    def test_unknown_validation_evidence_is_never_read(self):
        item = self.literal_candidate()
        item["validation_evidence"][0]["classification"] = "MIXED"
        with patch.object(Path, "read_bytes", side_effect=AssertionError("privacy before reads")):
            self.rejection(item, "classification_not_approved")

    def test_arithmetic_owner_change_invalidates_current_admission(self):
        self.approve()
        import financial_documents
        with patch.object(financial_documents, "_dependencies", return_value={"tools/fis/report_review.py": "0" * 64}):
            self.assertEqual(self.manifest()["exclusions"][0]["reason"], "validation_dependency_changed")

    def test_cli_duplicate_privacy_keys_fail_before_source_reads(self):
        item=self.candidate()
        raw=json.dumps(item).replace('"classification": "SYNTHETIC"',
            '"classification": "PERSONAL", "classification": "SYNTHETIC"',1)
        candidate=self.root/"candidate.json"
        candidate.write_text(raw,encoding="utf-8")
        output=io.StringIO()
        with patch.object(Path,"read_bytes",side_effect=AssertionError("ambiguous input before source reads")), redirect_stdout(output):
            code=registry.main(["--document-admit",str(candidate),"--root",str(self.root),"--documents-registry",str(self.path)])
        self.assertEqual(code,2)
        self.assertEqual(json.loads(output.getvalue())["reason"],"document_input_unavailable_or_invalid")
        self.assertNotIn("PERSONAL",output.getvalue())
        self.assertFalse(self.path.exists())


if __name__ == "__main__": unittest.main()

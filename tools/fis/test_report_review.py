"""Financial negative controls for exact-artifact review; all data synthetic."""
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import evidence
import report_review as rr
import workbench as w
from provenance import ProvenanceGraph
from test_workbench import packet

NOW = "2026-09-13T06:00:00Z"


def fixture(directory):
    """Executable development example for callers preparing the review interface."""
    root = Path(directory)
    assets = root / "inputs"
    assets.mkdir()
    p = packet()
    source_text = "".join(f"{c['id']} | {c['metric']} | {c['value']} | {c['unit']} | {c['currency']}\n" for c in p["claims"])
    p["sources"][0]["content_sha256"] = hashlib.sha256(source_text.encode()).hexdigest()
    calculation = w.analyze(p)
    report_lines = []
    for c in calculation["claims"] + calculation["results"]:
        report_lines.append(f"{c['id']} = {c['value']:.6f} {c['unit']} {c['currency']} {c['metric']}")
    report_lines.extend(p["gaps"] + p["scope"]["limitations"])
    report_text = "\n".join(report_lines) + "\n"
    contents = {"source.txt": source_text, "report.txt": report_text,
                "original.txt": report_text + "Original draft retained.\n",
                "method.txt": "Synthetic primer: operating margin is operating income divided by revenue.\n",
                "render.txt": "Synthetic rendered-text observation: labels, values and limitations inspected.\n"}
    roles = {"source": "source", "report": "delivered", "original": "original_draft", "method": "library", "render": "render_evidence"}
    artifacts = []
    for name, text in contents.items():
        (assets / name).write_bytes(text.encode())
        aid = Path(name).stem
        artifacts.append({"id": aid, "path": name, "role": roles[aid], "media_type": "text/plain",
                          "classification": "synthetic", "sha256": hashlib.sha256(text.encode()).hexdigest(),
                          "surfaces": ["narrative"] if aid == "report" else []})
    next(a for a in artifacts if a["id"] == "render").update(
        rendered_from="report", rendered_from_sha256=hashlib.sha256(report_text.encode()).hexdigest(),
        render_method="Synthetic text observation control; no browser execution claimed.")
    def span(aid, text, locator):
        start = contents[aid + ".txt"].index(text)
        return {"artifact_id": aid, "start": start, "end": start + len(text), "text": text, "locator": locator}
    mappings = []
    for c in p["claims"]:
        line = next(x for x in source_text.splitlines() if x.startswith(c["id"] + " |"))
        mappings.append({"claim_id": c["id"], "original_label": c["metric"], "normalized_metric": c["metric"],
                         "value_token": str(c["value"]), "multiplier": 1,
                         **{k: c[k] for k in ("unit", "currency", "basis", "as_of", "period_start", "period_end") if k in c},
                         "support": span("source", line, "Synthetic statement row " + c["id"])})
    assertions = []
    for n in calculation["claims"] + calculation["results"]:
        text = next(x for x in report_lines if x.startswith(n["id"] + " ="))
        assertions.append({"id": "assert:" + n["id"], "kind": "numeric", "support_refs": [n["id"]],
                           "span": span("report", text, "Report row " + n["id"]), "surface": "narrative", "limitations": [],
                           "display": {"token": f"{n['value']:.6f}", "multiplier": 1, "decimals": 6,
                                       **{k: n[k] for k in ("metric", "unit", "currency", "basis")}}})
    for index, text in enumerate(p["gaps"] + p["scope"]["limitations"]):
        assertions.append({"id": "limit:" + str(index), "kind": "limitation", "support_refs": [],
                           "span": span("report", text, "Report limitation"), "surface": "narrative", "limitations": [text]})
    request = {"schema": rr.REQUEST_SCHEMA, "id": "review:synthetic-company", "classification": "synthetic",
               "privacy": {"classification": "synthetic", "reviewed_by": "fixture:privacy", "contains_personal_data": False},
               "author_id": "fixture:author", "reviewed_at": NOW,
               "task": {"question": "How did synthetic revenue and operating margin change?", "horizon": "FY2024 to FY2025",
                        "consequential": False, "coupled_required": False, "material_assumptions": [],
                        "obligations": [{"id": "question:change", "question": "Compute supported changes.", "support": "supported",
                                         "answer_assertions": [a["id"] for a in assertions if a["kind"] == "numeric"],
                                         "required_calculations": [n["id"] for n in calculation["results"]],
                                         "missing_information": [], "withholding_reason": None}]},
               "artifacts": artifacts,
               "source_reviews": [{"id": "inspection:1", "source_id": p["sources"][0]["id"], "snapshot_artifact": "source",
                                   "source_version": "original-2025", "origin_uri": p["sources"][0]["uri"],
                                   "relationship": "direct", "revision_status": "original", "supersedes": [],
                                   "inspected_at": NOW, "inspected_by": "fixture:inspector", "mappings": mappings}],
               "methods": [{"id": "method:margin", "name": "Operating margin", "version": "synthetic-1",
                            "approved_scope": "Synthetic statement arithmetic", "applies_because": "Same issuer, fiscal window and accounting basis.",
                            "retrieved_at": NOW, "support": span("method", contents["method.txt"].strip(), "Synthetic primer"),
                            "calculation_ids": [n["id"] for n in calculation["results"] if n["metric"] == "operating_margin"],
                            "contrary_guidance": ["Income margin does not measure cash generation."], "missing_inputs": [],
                            "alternatives": ["Compare unscaled operating income and revenue."]}],
               "assertions": assertions,
               "render_checks": [{"id": "render:default", "artifact_id": "report", "surface": "narrative", "state": "default",
                                  "outcome": "pass", "evidence_artifact": "render", "assertion_ids": [a["id"] for a in assertions]}],
               "scenarios": [], "comparisons": [], "revisions": [], "reviewers": []}
    bundle = root / "calculation"
    w.write_bundle(p, bundle)
    approve(p, bundle, request, assets)
    return p, bundle, request, assets


def approve(p, bundle, request, assets):
    context = rr.prepare_context(p, bundle, request, assets)
    request["reviewers"] = [{"id": "fixture:reviewer", "kind": "model", "model": "synthetic-control", "effort": "synthetic-control",
                             "status": "completed", "context_sha256": context["context_sha256"], "read_only": True,
                             "full_artifact_reviewed": True, "coverage": context["required_coverage"],
                             "not_applicable_checks": context["not_applicable_checks"],
                             "judgments": {d: {"status": "pass", "rationale": "Synthetic correct-control judgment; no live reviewer claim."} for d in rr.DIMENSIONS},
                             "findings": [], "disagreements": []}]


class ReportReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.p, self.bundle, self.request, self.assets = fixture(self.root)

    def review(self):
        return rr.review(self.p, self.bundle, self.request, self.assets)

    def test_complete_correct_control_retains_calculation_packet_compatibility(self):
        old_files = {p.name: p.read_bytes() for p in self.bundle.iterdir()}
        result = self.review()
        self.assertEqual(result["status"], "accepted")
        self.assertFalse(result["production_eligible"])
        self.assertEqual(result["source_origin_count"], 1)
        self.assertEqual(old_files, {p.name: p.read_bytes() for p in self.bundle.iterdir()})
        self.assertEqual(len(old_files), 7)
        historical = w.verify_bundle(self.p, self.bundle, historical=True)
        self.assertTrue(historical["verified"])
        self.assertFalse(historical["current_eligible"])
        with patch.object(w, "code_hashes", return_value={"different.py": "0" * 64}):
            self.assertTrue(w.verify_bundle(self.p, self.bundle, historical=True)["code_changed"])
            with self.assertRaises(ValueError):
                w.verify_bundle(self.p, self.bundle)

    def test_correct_arithmetic_wrong_financial_interpretation_blocks_report(self):
        reviewer = self.request["reviewers"][0]
        reviewer["judgments"]["economics"] = {"status": "fail", "rationale": "Operating income is incorrectly described as household savings."}
        reviewer["findings"] = [{"id": "finding:meaning", "severity": "major", "status": "open",
                                 "reason": "Arithmetic is correct, financial meaning is wrong.",
                                 "assertion_ids": [self.request["assertions"][0]["id"]], "artifact_ids": ["report"],
                                 "resolution_artifact": None, "resolution_verified": False}]
        result = self.review()
        self.assertEqual(result["status"], "withheld")
        self.assertIn("unresolved_material_financial_finding", result["blockers"])
        out = self.root / "rejected"
        rr.write_review(self.p, self.bundle, self.request, self.assets, out)
        self.assertTrue((out / "artifacts/original.txt").exists())
        self.assertFalse(rr.verify_review(out)["current_eligible"])

    def test_malformed_timeout_and_incomplete_reviewers_never_pass(self):
        good = copy.deepcopy(self.request["reviewers"])
        bad_cases = [{}, {"status": "completed"}, None, [], "PASS"]
        for bad in bad_cases:
            self.request["reviewers"] = [bad]
            with self.subTest(bad=bad):
                self.assertEqual(self.review()["status"], "withheld")
        for change in ({"status": "timeout"}, {"read_only": "true"}, {"full_artifact_reviewed": False},
                       {"id": self.request["author_id"]}, {"context_sha256": "0" * 64}, {"judgments": {}}, {"coverage": {}}):
            self.request["reviewers"] = copy.deepcopy(good)
            self.request["reviewers"][0].update(change)
            with self.subTest(change=change):
                self.assertEqual(self.review()["status"], "withheld")

    def test_refusal_does_not_satisfy_supported_obligations(self):
        self.request["task"]["obligations"][0]["answer_assertions"] = []
        with self.assertRaisesRegex(ValueError, "blanket withholding"):
            self.review()

    def test_omitted_required_calculation_or_unknown_claim_refuses(self):
        self.request["task"]["obligations"][0]["required_calculations"] = ["absent"]
        with self.assertRaises(ValueError):
            self.review()

    def test_source_checked_is_not_source_review(self):
        self.request["source_reviews"] = []
        with self.assertRaises(ValueError):
            self.review()

    def test_source_cell_original_label_numeric_mapping_and_currency_controls(self):
        original = copy.deepcopy(self.request)
        for change in ({"original_label": "Household saving"}, {"value_token": "120"}, {"multiplier": 1000},
                       {"normalized_metric": "net_income"}, {"currency": "EUR"}, {"as_of": NOW}):
            self.request = copy.deepcopy(original)
            self.request["source_reviews"][0]["mappings"][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.review()

    def test_source_excerpt_and_inspection_revision_controls(self):
        original = copy.deepcopy(self.request)
        changes = [{"revision_status": "retracted", "supersedes": ["inspection:old"]},
                   {"revision_status": "restated", "supersedes": []},
                   {"relationship": "direct", "origin_uri": "synthetic:another-source"},
                   {"inspected_at": "2030-01-01T00:00:00Z"}]
        for change in changes:
            self.request = copy.deepcopy(original)
            self.request["source_reviews"][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.review()
        self.request = original
        self.request["source_reviews"][0]["mappings"][0]["support"]["text"] = "Invented support"
        with self.assertRaises(ValueError):
            self.review()

    def test_packet_zero_denominator_and_incompatible_currency_refuse(self):
        for change in ({"value": 0}, {"currency": "EUR"}):
            p = copy.deepcopy(self.p)
            p["claims"][0].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                rr.review(p, self.bundle, self.request, self.assets)

    def test_omitted_limitations_and_edited_delivered_text_refuse(self):
        original = copy.deepcopy(self.request)
        self.request["assertions"][-1]["limitations"] = []
        with self.assertRaisesRegex(ValueError, "limitations"):
            self.review()
        self.request = original
        (self.assets / "report.txt").write_text("Edited final output")
        with self.assertRaisesRegex(ValueError, "bytes changed"):
            self.review()

    def test_correct_metadata_cannot_certify_changed_tooltip(self):
        # The display value remains a numeric claim even in a tooltip.
        a = self.request["assertions"][0]
        a["surface"] = "tooltip"
        self.request["artifacts"][1]["surfaces"].append("tooltip")
        self.request["render_checks"].append({"id": "render:tooltip", "artifact_id": "report", "surface": "tooltip",
                                             "state": "default", "outcome": "pass", "evidence_artifact": "render", "assertion_ids": [a["id"]]})
        a["display"]["token"] = "900"
        with self.assertRaises(ValueError):
            self.review()

    def test_rendered_text_spans_bind_actual_delivered_html_bytes(self):
        report = next(a for a in self.request["artifacts"] if a["id"] == "report")
        old = (self.assets / "report.txt").read_bytes()
        html = b"<html><body><script>/* synthetic rendering control */</script></body></html>"
        (self.assets / "report.txt").write_bytes(html)
        report["sha256"] = hashlib.sha256(html).hexdigest()
        observed = next(a for a in self.request["artifacts"] if a["id"] == "render")
        (self.assets / "render.txt").write_bytes(old)
        observed.update(sha256=hashlib.sha256(old).hexdigest(), rendered_from_sha256=report["sha256"])
        for assertion in self.request["assertions"]:
            assertion["span"]["artifact_id"] = "render"
            assertion["delivered_artifact_id"] = "report"
        approve(self.p, self.bundle, self.request, self.assets)
        self.assertEqual(self.review()["status"], "accepted")
        observed["rendered_from_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "another delivered artifact version"):
            self.review()

    def test_filter_boundary_coverage_and_observed_failure(self):
        a = self.request["assertions"][0]
        a["surface"] = "filter"
        next(x for x in self.request["artifacts"] if x["id"] == "report")["surfaces"].append("filter")
        with self.assertRaisesRegex(ValueError, "boundary"):
            self.review()
        for state in ("default", "empty", "partial", "missing", "zero_denominator", "currency_boundary", "time_boundary", "negative"):
            self.request["render_checks"].append({"id": "filter:" + state, "artifact_id": "report", "surface": "filter",
                                                 "state": state, "outcome": "pass", "evidence_artifact": "render", "assertion_ids": [a["id"]]})
        approve(self.p, self.bundle, self.request, self.assets)
        self.assertEqual(self.review()["status"], "accepted")
        self.request["render_checks"][-1]["outcome"] = "unavailable"
        approve(self.p, self.bundle, self.request, self.assets)
        self.assertEqual(self.review()["status"], "withheld")

    def test_unexposed_selection_only_boundaries_need_explicit_reviewer_confirmation(self):
        a = self.request["assertions"][0]
        a["surface"] = "filter"
        next(x for x in self.request["artifacts"] if x["id"] == "report")["surfaces"].append("filter")
        for state in ("default", "empty", "partial", "missing", "zero_denominator", "currency_boundary", "time_boundary", "negative"):
            check = {"id": "filter:" + state, "artifact_id": "report", "surface": "filter", "state": state,
                     "outcome": "pass", "evidence_artifact": "render", "assertion_ids": [a["id"]]}
            if state in {"missing", "zero_denominator", "currency_boundary", "time_boundary"}:
                check.update(outcome="not_applicable", applicability={"interface": "Fixed reviewed-row selector", "exposed": False,
                              "reason": "Only fixed scenario keys are selectable; this financial input is not exposed by the reviewed interface."})
            self.request["render_checks"].append(check)
        approve(self.p, self.bundle, self.request, self.assets)
        receipt = self.review()
        self.assertEqual(receipt["status"], "accepted")
        self.assertEqual(receipt["render_check_counts"]["not_applicable"], 4)
        self.assertEqual(receipt["render_check_counts"]["pass"], 5)
        self.request["reviewers"][0].pop("not_applicable_checks")
        self.assertEqual(self.review()["status"], "withheld")
        self.request["render_checks"][-3]["applicability"]["exposed"] = True
        with self.assertRaisesRegex(ValueError, "exposed financial input"):
            self.review()

    def test_blanket_not_applicable_cannot_replace_default_or_partial_observation(self):
        check = self.request["render_checks"][0]
        for state in ("default", "partial"):
            check.update(state=state, outcome="not_applicable", applicability={"interface": "Any interface", "exposed": False,
                         "reason": "Attempt to omit required observed behavior."})
            with self.subTest(state=state), self.assertRaisesRegex(ValueError, "cannot be declared not applicable"):
                self.review()

    def test_reviewer_cannot_omit_a_claim_or_disagreement(self):
        self.request["reviewers"][0]["coverage"]["assertions"].pop()
        self.assertEqual(self.review()["status"], "withheld")
        approve(self.p, self.bundle, self.request, self.assets)
        self.request["reviewers"][0]["disagreements"] = ["unexplained"]
        self.assertEqual(self.review()["status"], "withheld")

    def test_canonical_disagreement_references_are_distinct_from_prose(self):
        reviewer = self.request["reviewers"][0]
        reviewer["findings"] = [{"id": "finding:scope", "severity": "minor", "status": "disputed",
                                 "reason": "Synthetic unresolved disagreement about a displayed label.",
                                 "assertion_ids": [self.request["assertions"][0]["id"]], "artifact_ids": ["report"],
                                 "resolution_artifact": None, "resolution_verified": False}]
        context = rr.prepare_context(self.p, self.bundle, self.request, self.assets)
        contract = rr.reviewer_contract(context, reviewer_id=reviewer["id"], model=reviewer["model"], effort=reviewer["effort"])
        rule = contract["output_schema"]["properties"]["R001"]["properties"]["disagreements"]["items"]["pattern"]
        self.assertTrue(re.fullmatch(rule, "finding:scope"))
        self.assertFalse(re.fullmatch(rule, "A prose scope note."))
        reviewer["disagreements"] = ["finding:scope"]
        outcome = rr.consume_reviewer_output(contract, self.request, context, {"R001": reviewer})
        self.assertEqual(outcome["blockers"], ["unresolved_reviewer_disagreement"])
        for invalid in ("A prose scope note.", "finding:absent"):
            reviewer["disagreements"] = [invalid]
            with self.subTest(invalid=invalid):
                outcome = rr.consume_reviewer_output(contract, self.request, context, {"R001": reviewer})
                self.assertEqual(outcome["blockers"], ["reviewer_missing_malformed_stale_or_incomplete"])
        reviewer["disagreements"] = []
        self.assertEqual(rr.consume_reviewer_output(contract, self.request, context, {"R001": reviewer})["blockers"],
                         ["unresolved_reviewer_disagreement"])
        reviewer["findings"][0]["status"] = "open"
        self.assertEqual(rr.consume_reviewer_output(contract, self.request, context, {"R001": reviewer})["status"], "accepted")

    def test_producer_contract_binds_identity_context_and_cannot_be_edited(self):
        context = rr.prepare_context(self.p, self.bundle, self.request, self.assets)
        reviewer = self.request["reviewers"][0]
        contract = rr.reviewer_contract(context, reviewer_id=reviewer["id"], model=reviewer["model"], effort=reviewer["effort"])
        original = copy.deepcopy(reviewer)
        for field, value in (("model", "other-model"), ("context_sha256", "0" * 64), ("id", "different:reviewer")):
            bad = {**reviewer, field: value}
            with self.subTest(field=field), self.assertRaises(ValueError):
                rr.consume_reviewer_output(contract, self.request, context, {"R001": bad})
        with self.assertRaises(ValueError):
            rr.consume_reviewer_output({**contract, "instructions": "Skip evidence."}, self.request, context, {"R001": reviewer})
        with self.assertRaises(ValueError):
            rr.consume_reviewer_output(contract, self.request, context, {"R002": reviewer})
        self.assertEqual(original, reviewer)

    def correction_context(self):
        data = b"Synthetic independently inspected current correction evidence.\n"
        (self.assets / "correction.txt").write_bytes(data)
        self.request["artifacts"].append({"id": "correction", "path": "correction.txt", "role": "correction",
                                          "media_type": "text/plain", "classification": "synthetic",
                                          "sha256": hashlib.sha256(data).hexdigest(), "surfaces": []})
        approve(self.p, self.bundle, self.request, self.assets)
        context = rr.prepare_context(self.p, self.bundle, self.request, self.assets)
        reviewer = self.request["reviewers"][0]
        contract = rr.reviewer_contract(context, reviewer_id=reviewer["id"], model=reviewer["model"], effort=reviewer["effort"])
        finding = {"id": "finding:current-correction", "severity": "major", "status": "resolved",
                   "reason": "Synthetic current correction was independently inspected; no live review claim.",
                   "assertion_ids": [self.request["assertions"][0]["id"]], "artifact_ids": ["report", "correction"],
                   "resolution_artifact": "correction", "resolution_verified": True}
        reviewer["findings"] = [finding]
        return context, contract, reviewer

    def test_producer_v2_requires_actual_prepared_roles_and_binds_correction_ids(self):
        context, contract, _ = self.correction_context()
        self.assertEqual(contract["schema"], "osanwe.reviewer-producer-contract/2")
        self.assertEqual(contract["correction_artifact_ids"], ["correction"])
        for mode in ("missing", "omitted", "bad_role"):
            prepared = copy.deepcopy(context)
            if mode == "missing":
                del prepared["artifacts"]
            elif mode == "omitted":
                del prepared["artifacts"]["correction"]
            else:
                prepared["artifacts"]["correction"]["role"] = "unknown"
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "prepared artifact roles"):
                rr.reviewer_contract(prepared, reviewer_id="fixture:reviewer", model="synthetic-control", effort="synthetic-control")

    def test_producer_without_correction_evidence_cannot_emit_resolved_findings(self):
        context = rr.prepare_context(self.p, self.bundle, self.request, self.assets)
        reviewer = self.request["reviewers"][0]
        contract = rr.reviewer_contract(context, reviewer_id=reviewer["id"], model=reviewer["model"], effort=reviewer["effort"])
        self.assertEqual(contract["correction_artifact_ids"], [])
        for artifact in (None, "report", "render", "absent"):
            reviewer["findings"] = [{"id": "finding:unsupported-resolution", "severity": "major", "status": "resolved",
                                      "reason": "Synthetic unsupported resolution control.", "assertion_ids": [], "artifact_ids": ["report"],
                                      "resolution_artifact": artifact, "resolution_verified": True}]
            with self.subTest(artifact=artifact):
                self.assertFalse(rr.reviewer_output_schema_valid(contract, {"R001": reviewer}))
                self.assertEqual(rr.consume_reviewer_output(contract, self.request, context, {"R001": reviewer})["status"], "withheld")

    def test_resolved_finding_requires_real_correction_role_and_verified_true(self):
        context, contract, reviewer = self.correction_context()
        original = copy.deepcopy(reviewer)
        for change in ({"resolution_artifact": "report"}, {"resolution_artifact": "render"},
                       {"resolution_artifact": "absent"}, {"resolution_artifact": None},
                       {"resolution_verified": False}, {"resolution_verified": 1}):
            output = copy.deepcopy(original)
            output["findings"][0].update(change)
            with self.subTest(change=change):
                self.assertFalse(rr.reviewer_output_schema_valid(contract, {"R001": output}))
                self.assertEqual(rr.consume_reviewer_output(contract, self.request, context, {"R001": output})["status"], "withheld")

    def test_open_and_disputed_findings_cannot_claim_a_false_resolution(self):
        context, contract, reviewer = self.correction_context()
        finding = reviewer["findings"][0]
        for status in ("open", "disputed"):
            for artifact, verified in (("correction", True), ("correction", False), (None, True)):
                finding.update(status=status, resolution_artifact=artifact, resolution_verified=verified)
                with self.subTest(status=status, artifact=artifact, verified=verified):
                    self.assertFalse(rr.reviewer_output_schema_valid(contract, {"R001": reviewer}))
            finding.update(status=status, resolution_artifact=None, resolution_verified=False)
            self.assertTrue(rr.reviewer_output_schema_valid(contract, {"R001": reviewer}))
            self.assertEqual(rr.consume_reviewer_output(contract, self.request, context, {"R001": reviewer})["status"], "withheld")

    def test_properly_bound_current_resolution_passes_schema_and_unchanged_consumer(self):
        context, contract, reviewer = self.correction_context()
        self.assertTrue(rr.reviewer_output_schema_valid(contract, {"R001": reviewer}))
        self.assertEqual(rr.consume_reviewer_output(contract, self.request, context, {"R001": reviewer})["status"], "accepted")
        self.assertEqual(self.review()["status"], "accepted")

    def test_forged_correction_set_cannot_pass_the_actual_prepared_consumer(self):
        context, _, reviewer = self.correction_context()
        forged = copy.deepcopy(context)
        forged["artifacts"]["render"]["role"] = "correction"
        contract = rr.reviewer_contract(forged, reviewer_id=reviewer["id"], model=reviewer["model"], effort=reviewer["effort"])
        # A structurally canonical, rehashed declaration is not source authority.
        self.assertTrue(rr.validate_reviewer_contract(contract))
        self.assertIn("render", contract["correction_artifact_ids"])
        reviewer["findings"][0]["resolution_artifact"] = "render"
        self.assertTrue(rr.reviewer_output_schema_valid(contract, {"R001": reviewer}))
        with self.assertRaisesRegex(ValueError, "contract changed"):
            rr.consume_reviewer_output(contract, self.request, context, {"R001": reviewer})

    def test_v2_correction_field_cannot_be_missing_or_reference_an_unknown_artifact(self):
        _, original, _ = self.correction_context()
        for mode in ("missing", "unknown", "duplicate", "old_version"):
            contract = copy.deepcopy(original)
            if mode == "missing":
                del contract["correction_artifact_ids"]
            elif mode == "unknown":
                contract["correction_artifact_ids"] = ["absent"]
            elif mode == "duplicate":
                contract["correction_artifact_ids"] = ["correction", "correction"]
            else:
                contract["schema"] = "osanwe.reviewer-producer-contract/1"
            contract["contract_sha256"] = w.sha({k: v for k, v in contract.items() if k != "contract_sha256"})
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                rr.validate_reviewer_contract(contract)

    def test_producer_uses_the_native_supported_schema_subset(self):
        _, contract, _ = self.correction_context()
        supported = {"type", "properties", "required", "additionalProperties", "const", "enum", "pattern", "minLength",
                     "maxLength", "maxItems", "uniqueItems", "items", "description", "anyOf"}
        def visit(schema):
            self.assertLessEqual(set(schema), supported)
            for child in schema.get("properties", {}).values():
                visit(child)
            if "items" in schema:
                visit(schema["items"])
            for child in schema.get("anyOf", []):
                visit(child)
        visit(contract["output_schema"])

    def test_method_version_scope_and_retrieval_changes_invalidate_reviewer(self):
        self.request["methods"][0]["version"] = "synthetic-2"
        self.assertEqual(self.review()["status"], "withheld")
        approve(self.p, self.bundle, self.request, self.assets)
        self.request["methods"][0]["approved_scope"] = "Expanded to cash generation"
        self.assertEqual(self.review()["status"], "withheld")

    def add_external(self):
        from decimal import Decimal
        output = {"scenario": str((Decimal(30) - Decimal(12) - Decimal(5)) / (Decimal(120) - Decimal(12)))}
        for aid, name, role, data in (("independent", "independent.json", "calculation_evidence", w.canonical(output)),
                                      ("calculator", "calculator.py", "calculation_code", b"# Synthetic independent Decimal arithmetic reproduction.\n")):
            (self.assets / name).write_bytes(data)
            self.request["artifacts"].append({"id": aid, "path": name, "role": role, "media_type": "text/plain",
                                              "classification": "synthetic", "sha256": hashlib.sha256(data).hexdigest(), "surfaces": []})
        self.request["external_calculations"] = [{"id": "external:coupled", "evidence_artifact": "independent", "code_artifact": "calculator",
                                                   "result_pointer": "/scenario", "expression": "(oi+revenue_shift-cost_shift)/(revenue+revenue_shift)",
                                                   "bindings": {"oi": {"ref": "fact:operating_income-2025"}, "revenue": {"ref": "fact:revenue-2025"},
                                                                "revenue_shift": {"assumption": -12, "unit": "millions", "currency": "USD", "basis": "GAAP:nominal", "rationale": "Algebraic synthetic revenue stress."},
                                                                "cost_shift": {"assumption": 5, "unit": "millions", "currency": "USD", "basis": "GAAP:nominal", "rationale": "Algebraic additional cost stress."}},
                                                   "metric": "operating_margin", "unit": "fraction", "currency": "NONE", "basis": "GAAP:nominal",
                                                   "period_policy": "same_period", "scope": "Synthetic coupled algebra, not a forecast."}]

    def test_independent_expression_replays_archived_coupled_scenario(self):
        self.add_external()
        approve(self.p, self.bundle, self.request, self.assets)
        self.assertEqual(self.review()["status"], "accepted")
        original = copy.deepcopy(self.request)
        for mode in ("wrong_value", "currency", "zero", "code_execution", "wrong_period", "wrong_output_unit", "unused_binding", "wrong_output_basis"):
            self.request = copy.deepcopy(original)
            record = self.request["external_calculations"][0]
            if mode == "wrong_value": record["bindings"]["cost_shift"]["assumption"] = 4
            elif mode == "currency": record["bindings"]["cost_shift"]["currency"] = "EUR"
            elif mode == "zero": record["bindings"]["revenue_shift"]["assumption"] = -120
            elif mode == "code_execution": record["expression"] = "__import__('os').environ"
            elif mode == "wrong_period": record["bindings"]["oi"]["ref"] = "fact:operating_income-2024"
            elif mode == "wrong_output_unit": record["unit"] = "millions"; record["currency"] = "USD"
            elif mode == "wrong_output_basis": record["basis"] = "adjusted:real"
            else: record["bindings"]["ignored"] = {"ref": "fact:revenue-2025"}
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.review()

    def test_interpretation_dimensions_cannot_all_be_marked_not_applicable(self):
        for judgment in self.request["reviewers"][0]["judgments"].values():
            judgment["status"] = "not_applicable"
        self.assertEqual(self.review()["status"], "withheld")

    def test_public_runtime_classification_review_is_explicit_and_hash_bound(self):
        # Public source/runtime code can contain email-shaped package specifiers.
        # The default is strict; only an explicit review of these public bytes
        # covers that pattern. It cannot exempt a canary/account/SSN marker.
        self.request["classification"] = "public"
        self.request["privacy"]["classification"] = "public"
        for artifact in self.request["artifacts"]:
            artifact["classification"] = "public"
        data = b"Public runtime imports package@example.invalid; no account data.\n"
        (self.assets / "render.txt").write_bytes(data)
        item = next(x for x in self.request["artifacts"] if x["id"] == "render")
        item["sha256"] = hashlib.sha256(data).hexdigest()
        with self.assertRaises(ValueError):
            rr._artifacts(self.request, self.assets)
        self.request["privacy"]["public_artifact_reviews"] = [{"artifact_id": "render", "sha256": item["sha256"],
                                                                 "public_origin": "https://example.invalid/public-runtime",
                                                                 "reviewed_by": "fixture:privacy", "reason": "Inspected public package specifier, not personal contact information."}]
        rr._artifacts(self.request, self.assets)
        self.request["privacy"]["public_artifact_reviews"][0]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            rr._artifacts(self.request, self.assets)
        data = b"PRIVACY_CANARY do not persist\n"
        (self.assets / "render.txt").write_bytes(data)
        item["sha256"] = hashlib.sha256(data).hexdigest()
        self.request["privacy"]["public_artifact_reviews"][0]["sha256"] = item["sha256"]
        with self.assertRaises(ValueError):
            rr._artifacts(self.request, self.assets)

    def test_extracted_table_cells_must_reconcile_with_original_snapshot(self):
        original_text = (self.assets / "source.txt").read_text()
        (self.assets / "original-source.txt").write_bytes(original_text.encode())
        self.request["artifacts"].append({"id": "original-source", "path": "original-source.txt", "role": "source", "media_type": "text/plain",
                                          "classification": "synthetic", "sha256": hashlib.sha256(original_text.encode()).hexdigest(), "surfaces": []})
        inspection = self.request["source_reviews"][0]
        inspection["original_snapshot_artifact"] = "original-source"
        for mapping in inspection["mappings"]:
            mapping["original_support"] = {**mapping["support"], "artifact_id": "original-source"}
        approve(self.p, self.bundle, self.request, self.assets)
        self.assertEqual(self.review()["status"], "accepted")
        inspection["mappings"][0]["original_support"]["text"] = "Invented original cell"
        with self.assertRaises(ValueError):
            self.review()

    def test_consequential_conclusion_requires_reversal_and_simple_alternative(self):
        self.request["task"]["consequential"] = True
        with self.assertRaisesRegex(ValueError, "reverses"):
            self.review()

    def test_no_personal_records_canaries_or_protected_paths_are_archived(self):
        original = copy.deepcopy(self.request)
        for mode in ("classification", "metadata", "canary", "path"):
            self.request = copy.deepcopy(original)
            if mode == "classification":
                self.request["classification"] = "personal"
            elif mode == "metadata":
                self.request["privacy"]["account_number"] = "synthetic-secret"
            elif mode == "canary":
                self.request["task"]["question"] = "PRIVACY_CANARY never export"
            else:
                self.request["artifacts"][0]["path"] = "../private/canary.txt"
            out = self.root / ("refused-" + mode)
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                rr.write_review(self.p, self.bundle, self.request, self.assets, out)
            self.assertFalse(out.exists())

    def test_archive_tamper_current_vs_historical_and_provenance_invalidation(self):
        out = self.root / "review"
        rr.write_review(self.p, self.bundle, self.request, self.assets, out)
        self.assertTrue(rr.verify_review(out)["current_eligible"])
        self.assertFalse(rr.verify_review(out, historical=True)["current_eligible"])
        current = copy.deepcopy(self.p)
        current["sources"][0]["title"] = "Later source revision"
        self.assertEqual(rr.verify_review(out, current_packet=current)["status"], "stale")
        current = copy.deepcopy(self.request)
        current["methods"][0]["version"] = "New method version"
        self.assertEqual(rr.verify_review(out, current_request=current)["status"], "stale")
        with patch.object(rr, "code_hashes", return_value={"new.py": "0" * 64}):
            stale = rr.verify_review(out)
            self.assertEqual(stale["status"], "stale")
            self.assertTrue(stale["historical_integrity"])
            self.assertFalse(stale["current_eligible"])
        graph = ProvenanceGraph(str(out / "provenance.json"))
        graph.register_fact("review:sources", "restatement")
        self.assertFalse(graph.explain("review:accepted-report")["fresh"])
        with self.assertRaisesRegex(ValueError, "edited"):
            rr.verify_review(out)

    def test_archive_is_immutable_and_cli_handles_prepare_review_verify(self):
        pfile, rfile = self.root / "packet.json", self.root / "request.json"
        pfile.write_bytes(w.canonical(self.p))
        rfile.write_bytes(w.canonical(self.request))
        script = str(Path(w.__file__))
        args = [sys.executable, script, "review", str(pfile), str(self.bundle), str(rfile), "--artifacts", str(self.assets)]
        prepared = subprocess.run(args + ["--prepare"], capture_output=True, text=True)
        self.assertEqual(prepared.returncode, 0, prepared.stdout + prepared.stderr)
        self.assertEqual(json.loads(prepared.stdout)["context_sha256"], self.request["reviewers"][0]["context_sha256"])
        producer = subprocess.run(args + ["--prepare", "--reviewer-id", "fixture:reviewer", "--reviewer-model", "synthetic-control", "--reviewer-effort", "synthetic-control"], capture_output=True, text=True)
        self.assertEqual(producer.returncode, 0, producer.stdout + producer.stderr)
        contract = json.loads(producer.stdout)["producer_contract"]
        expected = rr.reviewer_contract(rr.prepare_context(self.p, self.bundle, self.request, self.assets), reviewer_id="fixture:reviewer", model="synthetic-control", effort="synthetic-control")
        self.assertEqual(contract, expected)
        missing = subprocess.run(args + ["--prepare", "--reviewer-id", "fixture:reviewer"], capture_output=True, text=True)
        self.assertNotEqual(missing.returncode, 0)
        out = self.root / "cli-review"
        result = subprocess.run(args + ["--outdir", str(out)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        verified = subprocess.run([sys.executable, script, "verify-review", str(out)], capture_output=True, text=True)
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        with self.assertRaises(ValueError):
            rr.write_review(self.p, self.bundle, self.request, self.assets, out)


class InvestWorkflowReviewTests(unittest.TestCase):
    def test_actual_workflow_blocks_unrestricted_dispatch_and_malformed_verdicts(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node runtime unavailable; native workflow harness unverified")
        path = Path(__file__).resolve().parents[2] / ".claude/workflows/invest-verify.js"
        harness = r'''
const fs = require('fs');
let text = fs.readFileSync(process.argv[1], 'utf8').replace('export const meta', 'const meta');
const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
const run = new AsyncFunction('args', 'agent', 'parallel', 'phase', 'log', text);
const good = {refutation:false, details:'Checked synthetic source and arithmetic.', checked_items:['source','arithmetic']};
(async () => {
  const bad = [{}, [], true, {refutation:'false',details:'x',checked_items:['x']}, {...good,checked_items:[]}, {...good,extra:true}, {...good,details:''}, {...good,checked_items:['x','x']}];
  for (const verdict of ['BUY','HOLD','SELL','STRONG SELL']) {
    let count=0;
    const result=await run({ticker:'SYNTH',draft_verdict:verdict,read_only:true,permission_mode:'plan'},async()=>{count++; return good},tasks=>Promise.all(tasks.map(f=>f())),()=>{},()=>{});
    if(count!==0 || result.status!=='withheld' || result.dispatched_agents!==0) throw Error('Unrestricted reviewers dispatched');
    if(result.read_only_assurance?.status!=='unavailable' || result.read_only_assurance?.boundary!=='prompt_instruction_only') throw Error('Prompt claimed mechanical read-only assurance');
    if(result.accepted_report!==false || result.requires_separate_read_only_review!==true) throw Error('Unisolated review certified a report');
    if(!result.any_refutation || !result.blockers.includes('mechanical_read_only_boundary_unavailable')) throw Error('Unavailable reviewer did not halt parent');
  }
  // Exercise the retained strict verdict validator independently of the blocked
  // dispatch path. Restoring a supported boundary must not revive truthy passes.
  const validationStart=text.indexOf('const validSkeptic =');
  const validationEnd=text.indexOf('const checked =',validationStart);
  const validate=new Function(text.slice(validationStart,validationEnd)+'return validSkeptic;')();
  if(!validate(good)) throw Error('Correct reviewer contract rejected');
  for (const value of bad) {
    if(validate(value)) throw Error('Malformed reviewer passed');
  }
  process.stdout.write('PASS 13 workflow controls\n');
})().catch(e=>{process.stderr.write(e.message);process.exit(1)});
'''
        result = subprocess.run([node, "-e", harness, str(path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

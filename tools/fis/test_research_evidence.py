"""Representative synthetic research tasks; no private/live/holdout data."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from evidence import compatible, holdings_overlap, market_cap, validate_claim, weighted_overlap

NOW = "2026-09-12T12:00:00Z"


def claim(**updates):
    result = {"id": "fact:synthetic-revenue", "entity": "instr:synthetic", "metric": "revenue",
              "value": 120, "unit": "millions", "currency": "USD", "kind": "reported",
              "basis": "GAAP:nominal", "source": "synthetic:issuer-filing",
              "source_locator": "Synthetic statement, revenue row; test data only",
              "as_of": "2026-06-30T23:59:59Z", "published_at": "2026-07-30T12:00:00Z",
              "available_at": "2026-07-30T12:01:00Z", "retrieved_at": "2026-09-12T11:00:00Z",
              "max_age_days": 120, "freshness_policy": "synthetic quarterly fixture window",
              "temporal_type": "flow", "frequency": "quarterly",
              "period_start": "2026-04-01T00:00:00Z", "period_end": "2026-06-30T23:59:59Z"}
    result.update(updates)
    if result["temporal_type"] == "point":
        for key in ("period_start", "period_end", "frequency"):
            result.pop(key, None)
    return result


def snapshot(identifier, weights, **updates):
    return {"holdings": weights, "claim": claim(
        id=identifier, entity=identifier, metric="holdings_coverage", unit="fraction", currency="NONE",
        value=sum(weights.values()), temporal_type="point", basis="fraction-of-fund-NAV",
        as_of="2026-09-11T20:00:00Z", published_at="2026-09-11T20:30:00Z",
        available_at="2026-09-11T20:31:00Z", max_age_days=2, **updates)}


class ResearchEvidence(unittest.TestCase):
    def test_current_company(self):
        self.assertEqual([], validate_claim(claim(), report_at=NOW))

    def test_historical_available_not_retrieved(self):
        self.assertTrue(any("future information" in e for e in validate_claim(
            claim(), report_at=NOW, knowledge_cutoff="2026-07-15T12:00:00Z")))
        self.assertEqual([], validate_claim(claim(), report_at=NOW, knowledge_cutoff="2026-08-01T12:00:00Z"))

    def test_no_future_retrieval_or_observation(self):
        for change in ({"retrieved_at": "2030-01-01T00:00:00Z"},
                       {"as_of": "2030-01-01T00:00:00Z"},
                       {"available_at": "2026-07-01T00:00:00Z"}):
            with self.subTest(change=change):
                self.assertTrue(validate_claim(claim(**change), report_at=NOW))

    def test_missing_information_not_zero(self):
        for value in (None, float("nan"), float("inf"), True):
            self.assertTrue(validate_claim(claim(value=value), report_at=NOW))
        self.assertEqual([], validate_claim(claim(value=0), report_at=NOW))

    def test_citation_needs_specific_support_locator(self):
        self.assertTrue(validate_claim(claim(source_locator=""), report_at=NOW))

    def test_timezone_and_freshness_policy_required(self):
        self.assertTrue(validate_claim(claim(as_of="2026-06-30"), report_at=NOW))
        self.assertTrue(validate_claim(claim(freshness_policy=""), report_at=NOW))

    def test_stale_etf_holdings(self):
        record = claim(metric="holdings_coverage", temporal_type="point", max_age_days=7)
        self.assertTrue(any("stale" in e for e in validate_claim(record, report_at=NOW)))

    def test_basis_currency_actual_and_frequency_conflicts(self):
        for key, value in (("basis", "adjusted:nominal"), ("basis", "GAAP:real"),
                           ("currency", "EUR"), ("kind", "estimate"),
                           ("frequency", "annual"), ("unit", "billions")):
            with self.subTest(key=key, value=value):
                self.assertIn(key, compatible(claim(), claim(**{key: value})))

    def test_fiscal_period_change_is_explicit(self):
        other = claim(as_of="2025-06-30T23:59:59Z", period_start="2025-04-01T00:00:00Z",
                      period_end="2025-06-30T23:59:59Z")
        self.assertIn("period_end", compatible(claim(), other))
        self.assertEqual([], compatible(claim(), other, allow_period_change=True))

    def test_calculation_requires_inspectable_inputs(self):
        self.assertTrue(validate_claim(claim(kind="calculated"), report_at=NOW))
        self.assertEqual([], validate_claim(claim(kind="calculated", inputs=["fact:input"],
                                                   transformation="sum input rows"), report_at=NOW))

    def test_market_cap_alignment_and_split_basis(self):
        price = claim(id="fact:p", metric="price", value=20, unit="currency/share", basis="split-adjusted",
                      temporal_type="point", as_of="2026-09-11T20:00:00Z",
                      published_at="2026-09-11T20:00:01Z", available_at="2026-09-11T20:01:00Z")
        shares = claim(id="fact:s", metric="shares", value=100, unit="shares", currency="NONE",
                       basis="split-adjusted", temporal_type="point", as_of=price["as_of"],
                       published_at=price["published_at"], available_at=price["available_at"])
        result = market_cap(price, shares, report_at=NOW, max_alignment_days=1)
        self.assertEqual(2000, result["value"])
        self.assertEqual(["fact:p", "fact:s"], result["inputs"])
        for patch in ({"as_of": "2026-06-30T00:00:00Z"}, {"basis": "unadjusted"}, {"kind": "estimate"},
                      {"metric": "weighted_average_shares"}, {"metric": "revenue"}, {"unit": "millions"},
                      {"currency": "USD"}, {"id": "fact:p"}):
            with self.assertRaises(ValueError):
                market_cap(price, dict(shares, **patch), report_at=NOW, max_alignment_days=1)

    def test_actual_observation_cannot_follow_publication(self):
        for kind in ("reported", "user_observation"):
            record = claim(kind=kind, temporal_type="point", as_of="2026-09-11T20:00:00Z")
            self.assertTrue(any("postdate" in error for error in validate_claim(record, report_at=NOW)))

    def test_forecast_freshness_uses_publication_not_target_or_late_delivery(self):
        forecast = claim(kind="forecast", as_of="2030-06-30T23:59:59Z",
                         period_start="2030-04-01T00:00:00Z", period_end="2030-06-30T23:59:59Z",
                         max_age_days=1)
        self.assertTrue(any("stale" in error for error in validate_claim(forecast, report_at=NOW)))
        forecast["available_at"] = "2026-09-12T09:01:00Z"
        self.assertTrue(any("stale" in error for error in validate_claim(forecast, report_at=NOW)))
        forecast.update(published_at="2026-09-12T09:00:00Z", available_at="2026-09-12T09:01:00Z")
        self.assertEqual([], validate_claim(forecast, report_at=NOW))

    def test_malformed_claim_shapes_return_validation_errors(self):
        for bad in (None, [], "not-a-claim", 1, claim(kind=[]), claim(temporal_type=[]),
                    claim(value=10**400), claim(source={"name": "issuer"}), claim(unit=[]),
                    claim(currency={"code": "USD"})):
            with self.subTest(bad=type(bad).__name__):
                self.assertTrue(validate_claim(bad, report_at=NOW))

    def test_field_shape_matrix_rejects_every_malformed_value_except_real_zero(self):
        for key in claim():
            for value in (None, [], {}, 0, True, "", "   ", 10**400):
                with self.subTest(key=key, value_type=type(value).__name__):
                    sample = claim()
                    sample[key] = value
                    errors = validate_claim(sample, report_at=NOW)
                    if key == "value" and value == 0 and not isinstance(value, bool):
                        self.assertEqual([], errors)
                    else:
                        self.assertTrue(errors)

    def test_lineage_and_policy_shapes_are_checked(self):
        for update in ({"inputs": "fact:input", "transformation": "sum"},
                       {"inputs": [""], "transformation": "sum"},
                       {"inputs": ["fact:input"], "transformation": 42},
                       {"inputs": ["fact:input", "fact:input"], "transformation": "sum"},
                       {"inputs": ["fact:synthetic-revenue"], "transformation": "sum"}):
            self.assertTrue(validate_claim(claim(kind="calculated", **update), report_at=NOW))
        for update in ({"freshness_policy": "   "}, {"freshness_policy": {}}, {"frequency": 3}):
            self.assertTrue(validate_claim(claim(**update), report_at=NOW))

    def test_currency_amount_and_point_flow_semantics(self):
        for update in ({"currency": "NONE"}, {"currency": " usd "}, {"unit": "shares"},
                       {"unit": "percent"}, {"basis": " GAAP:nominal"}):
            self.assertTrue(validate_claim(claim(**update), report_at=NOW))
        record = claim(temporal_type="point")
        record["period_start"] = "2026-04-01T00:00:00Z"
        self.assertTrue(validate_claim(record, report_at=NOW))

    def test_comparison_timestamp_aliases_and_explicit_opt_in(self):
        left = claim(temporal_type="point")
        right = dict(left, as_of="2026-06-30T19:59:59-04:00")
        self.assertEqual([], compatible(left, right))
        self.assertIn("as_of", compatible(left, dict(left, as_of="2026-06-30")))
        self.assertIn("kind", compatible(claim(kind=[]), claim(kind=[])))
        self.assertIn("kind", compatible(claim(kind="actual-ish"), claim(kind="actual-ish")))
        self.assertIn("period", compatible(claim(), claim(period_end=None), allow_period_change=True))
        with self.assertRaises(ValueError):
            compatible(claim(), claim(), allow_period_change="false")

    def test_holdings_envelopes_disclose_partial_coverage_without_renormalization(self):
        a, b = snapshot("fund:a", {"instr:a": .6}), snapshot("fund:b", {"instr:a": .3})
        result = holdings_overlap(a, b, report_at=NOW, max_alignment_days=1)
        self.assertAlmostEqual(.3, result["overlap"])
        self.assertFalse(result["complete"])
        self.assertTrue(result["freshness_validated"])
        self.assertEqual(["fund:a", "fund:b"], result["inputs"])
        self.assertFalse(weighted_overlap({"a": 1}, {"a": 1})["freshness_validated"])

    def test_holdings_temporal_source_basis_and_coverage_refusals(self):
        a, baseline = snapshot("fund:a", {"instr:a": .6}), snapshot("fund:b", {"instr:a": .3})
        changes = ({"as_of": "2026-08-11T20:00:00Z"},
                   {"available_at": "2026-09-13T20:00:00Z"},
                   {"value": 1}, {"kind": "forecast"}, {"basis": "fraction-of-equities"},
                   {"unit": "percent"}, {"source_locator": ""}, {"temporal_type": "flow"})
        for update in changes:
            b = copy.deepcopy(baseline)
            b["claim"].update(update)
            with self.subTest(update=update), self.assertRaises(ValueError):
                holdings_overlap(a, b, report_at=NOW, max_alignment_days=1)
        b = copy.deepcopy(baseline)
        b["claim"].update(as_of="2026-09-01T20:00:00Z", max_age_days=30)
        with self.assertRaisesRegex(ValueError, "misaligned"):
            holdings_overlap(a, b, report_at=NOW, max_alignment_days=1)
        with self.assertRaises(ValueError):
            holdings_overlap(a, baseline, report_at=NOW, max_alignment_days=1,
                             knowledge_cutoff="2026-09-10T12:00:00Z")
        b = copy.deepcopy(baseline)
        b["claim"]["id"] = a["claim"]["id"]
        with self.assertRaisesRegex(ValueError, "same source claim ID"):
            holdings_overlap(a, b, report_at=NOW, max_alignment_days=1)

    def test_etf_portfolio_overlap_no_double_count(self):
        result = weighted_overlap({"instr:a": .6, "instr:b": .4}, {"instr:a": .3, "instr:c": .7})
        self.assertAlmostEqual(.3, result["overlap"])
        self.assertTrue(result["complete"])
        partial = weighted_overlap({"instr:a": .6}, {"instr:a": .3})
        self.assertAlmostEqual(.3, partial["overlap"])
        self.assertFalse(partial["complete"])
        self.assertAlmostEqual(.6, partial["coverage_left"])

    def test_overlap_unknown_and_invalid_weights(self):
        for bad in ({}, {"a": float("nan")}, {"a": -.1}, {"a": 1.01}, {"a": True}):
            with self.assertRaises(ValueError):
                weighted_overlap(bad, {"a": 1})

    def test_cli_valid_and_duplicate_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "synthetic.json"
            for claims, status in (([claim()], 0), ([claim(), claim()], 1), ([], 2)):
                p.write_text(json.dumps({"report_at": NOW, "claims": claims}), encoding="utf-8")
                result = subprocess.run([sys.executable, str(Path(__file__).with_name("evidence.py")), str(p)],
                                        capture_output=True, text=True)
                self.assertEqual(status, result.returncode, result.stdout + result.stderr)
                json.loads(result.stdout)

    def test_cli_malformed_source_shapes_fail_with_structured_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic-malformed.json"
            for envelope, status in (([], 2), ({"report_at": NOW, "claims": [None]}, 1),
                                     ({"report_at": NOW, "claims": [claim(id=[])]}, 1),
                                     ({"report_at": NOW, "claims": [claim(kind=[])]}, 1),
                                     ({"report_at": [], "claims": [claim()]}, 2)):
                path.write_text(json.dumps(envelope), encoding="utf-8")
                result = subprocess.run([sys.executable, str(Path(__file__).with_name("evidence.py")), str(path)],
                                        capture_output=True, text=True)
                self.assertEqual(status, result.returncode, result.stdout + result.stderr)
                json.loads(result.stdout)
                self.assertNotIn("Traceback", result.stderr)
            path.write_text('{"report_at":"' + NOW + '","claims":[],"claims":[{}]}', encoding="utf-8")
            result = subprocess.run([sys.executable, str(Path(__file__).with_name("evidence.py")), str(path)],
                                    capture_output=True, text=True)
            self.assertEqual(2, result.returncode)
            self.assertIn("duplicate JSON field", json.loads(result.stdout)["error"])

    def test_cold_navigation_and_handoff_authorities(self):
        root = Path(__file__).resolve().parents[2]
        contract = (root / "AGENTS.md").read_text(encoding="utf-8")
        for relative in ("Efforts/osanwe-v2-overhaul/STATE.md", "docs/financial-analysis-contract.md",
                         "Atlas/_MOCs/knowledge-moc.md", "evaluation/challenge_protocol.md"):
            self.assertIn(relative, contract)
            self.assertTrue((root / relative).is_file())
        state = (root / "Efforts/osanwe-v2-overhaul/STATE.md").read_text(encoding="utf-8")
        for section in ("## Objective", "## Validation", "## Resume", "## Rollback"):
            self.assertIn(section, state)


if __name__ == "__main__":
    unittest.main()

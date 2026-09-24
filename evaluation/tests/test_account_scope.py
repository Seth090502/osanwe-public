"""Prospective coverage and independently recomputed synthetic arithmetic only."""
from decimal import Decimal
import hashlib
import json
import unittest
from test_protocol import ROOT, module

builder = module("account_scope_development")


class AccountScopeCoverage(unittest.TestCase):
    def test_frozen_supplement_matches_builder_without_rewriting_primary_release(self):
        frozen = json.loads((ROOT / "account_scope_development_v1.json").read_text())
        self.assertEqual(builder.build_cases(), frozen)
        self.assertFalse(frozen["admission_eligible"])
        self.assertFalse(frozen["native_tested"])
        base = (ROOT / "development_cases.json").read_bytes()
        self.assertEqual(hashlib.sha256(base).hexdigest(), frozen["base_development_sha256"])
        # The pilot froze canonical JSON; its archive deliberately has different
        # formatting from the original pretty-printed source. Compare that exact
        # payload semantically while the supplement pins current source bytes.
        self.assertEqual(json.loads(base), json.loads((ROOT / "reports/native-pilot-runtime-2026-09-13/development_cases.json").read_text()))

    def test_ten_family_admission_matrix_still_has_exactly_72_cases(self):
        protocol = json.loads((ROOT / "reasoning_protocol.json").read_text())
        matrix = protocol["admission"]["cases_by_family"]
        self.assertEqual(len(matrix), 10)
        self.assertEqual(set(matrix), set(protocol["families"]))
        self.assertEqual(sum(matrix.values()), 72)
        self.assertEqual((matrix["household"], matrix["account_scope"]), (8, 8))
        self.assertTrue(all(value == 7 for key, value in matrix.items() if key not in ("household", "account_scope")))
        self.assertFalse(protocol["admission"]["currently_available"])
        self.assertEqual(protocol["development"]["as_run_family_count"], 9)
        self.assertEqual(protocol["development"]["cases"], 36)

    def test_four_types_and_distinct_scenarios_do_not_relabel_prior_household_cases(self):
        cases = builder.build_cases()["cases"]
        self.assertEqual(len(cases), 4)
        self.assertEqual({c["family"] for c in cases}, {"account_scope"})
        self.assertEqual({c["coverage_type"] for c in cases},
                         {"answerable", "conflicting_evidence", "method_applicability", "misleading_framing"})
        original = json.loads((ROOT / "development_cases.json").read_text())["cases"]
        for field in ("id", "scenario_family", "source_family"):
            self.assertEqual(len({c[field] for c in cases}), 4)
            self.assertFalse({c[field] for c in cases} & {c[field] for c in original})

    def test_numeric_oracles_and_supplied_evidence_recomputed_with_decimal_arithmetic(self):
        cases = {c["id"]: c for c in builder.build_cases()["cases"]}
        # Independent expressions over the stipulated synthetic scope: exactly
        # two unique accounts, and individual plus one-half joint ownership.
        expected = {"account_scope-01": sum(map(Decimal, ("12000", "4000"))),
                    "account_scope-02": Decimal("2500"),
                    "account_scope-03": Decimal("13000") + Decimal("6000") * Decimal("0.50")}
        for cid, value in expected.items():
            self.assertEqual(Decimal(str(cases[cid]["oracle"]["obligations"][0]["value"])), value)
            for item in cases[cid]["input"]["calculation_evidence"]:
                self.assertEqual(Decimal(str(item["value"])), value)
        self.assertIsNone(cases["account_scope-02"]["oracle"]["obligations"][-1]["value"])
        self.assertIsNone(cases["account_scope-03"]["oracle"]["obligations"][-1]["value"])


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Synthetic recovery regressions. No network or persistent data writes."""

import copy
import json
import math
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import calcs_household as household
import provenance
import risk_engine as risk
import temporal_policy as temporal


class TemporalInvariants(unittest.TestCase):
    def setUp(self):
        self.rec = dict(
            record_type="prediction", cohort_id="RECOVERY-SYNTHETIC",
            creation_ts="2026-09-01T12:00:00Z", info_cutoff="2026-08-31",
            earliest_tradable="2026-09-02", horizon_days=5,
            dataset_version="frozen-v1", missing_data_state={"state": "complete"})

    def verdict(self, **changes):
        return temporal.prediction_eligibility_verdict(
            dict(self.rec, **changes), now_utc="2026-09-01T13:00:00Z",
            frozen_dataset_sha="frozen-v1")

    def test_valid_prediction_remains_eligible(self):
        self.assertTrue(self.verdict().prediction_eligible)

    def test_future_information_is_not_prospective(self):
        self.assertFalse(self.verdict(info_cutoff="2030-01-01").prediction_eligible)

    def test_same_session_unavailable_close_is_not_information(self):
        self.assertFalse(self.verdict(info_cutoff="2026-09-01").prediction_eligible)

    def test_observed_same_session_close_is_allowed(self):
        rec = dict(self.rec, creation_ts="2026-09-01T21:00:00Z",
                   info_cutoff="2026-09-01")
        self.assertTrue(temporal.prediction_eligibility_verdict(
            rec, now_utc="2026-09-01T22:00:00Z").prediction_eligible)

    def test_invalid_horizons_are_refused(self):
        for value in (-5, 0, 1.5, True, "bad", float("nan"), float("inf")):
            with self.subTest(value=value):
                self.assertFalse(self.verdict(horizon_days=value).prediction_eligible)

    def test_outcome_api_rejects_negative_horizon(self):
        with self.assertRaises(temporal.TemporalPolicyError):
            temporal.outcome_availability(dict(self.rec, horizon_days=-5))

    def test_missing_frozen_dataset_identity_is_refused(self):
        self.assertFalse(self.verdict(dataset_version=None).prediction_eligible)

    def test_malformed_cutoff_returns_refusal(self):
        self.assertFalse(self.verdict(info_cutoff="not-a-date").prediction_eligible)

    def test_malformed_entry_date_returns_refusal(self):
        self.assertFalse(self.verdict(earliest_tradable="not-a-date").prediction_eligible)

    def test_bad_information_cannot_be_graded_as_calibration(self):
        verdict = temporal.grade_eligibility_verdict(
            dict(self.rec, info_cutoff="2030-01-01"),
            now_utc="2026-09-12T21:00:00Z")
        self.assertFalse(verdict.grade_eligible)

    def test_dataset_drift_cannot_be_graded_as_calibration(self):
        verdict = temporal.grade_eligibility_verdict(
            dict(self.rec, dataset_version=None),
            now_utc="2026-09-12T21:00:00Z", frozen_dataset_sha="frozen-v1")
        self.assertFalse(verdict.grade_eligible)

    def test_read_path_checks_present_information_cutoff(self):
        rec = dict(self.rec, info_cutoff="2030-01-01",
                   provenance_mode=temporal.PROSPECTIVE, prospective_evidence=True)
        self.assertFalse(temporal.is_prospective_evidence(rec))


class RiskInvariants(unittest.TestCase):
    def test_weight_units_do_not_change_volatility(self):
        fraction = risk.portfolio_risk([0.5, 0.5], [0.2, 0.2])
        percent = risk.portfolio_risk([50, 50], [0.2, 0.2])
        dollars = risk.portfolio_risk([50000, 50000], [0.2, 0.2])
        for other in (percent, dollars):
            self.assertEqual(fraction["port_vol"], other["port_vol"])
            self.assertEqual(fraction["hhi_concentration"], other["hhi_concentration"])
        self.assertAlmostEqual(fraction["port_vol"], math.sqrt(0.026), places=6)

    def test_covariance_and_volatility_paths_agree(self):
        cov = [[0.04, 0.012], [0.012, 0.04]]
        self.assertEqual(risk.portfolio_risk([50, 50], cov)["port_vol"],
                         risk.portfolio_risk([0.5, 0.5], [0.2, 0.2])["port_vol"])

    def test_invalid_weight_shapes_raise_value_error(self):
        for weights, values in (([], []), ([0, 0], [0.2, 0.2]),
                                 ([0.5, -0.5], [0.2, 0.2]),
                                 ([0.5, 0.5], [0.2]),
                                 ([0.5, 0.5], [[0.04], [0.01, 0.04]])):
            with self.subTest(weights=weights, values=values):
                with self.assertRaises(ValueError):
                    risk.portfolio_risk(weights, values)

    def test_missing_required_metric_trips_kill_switch(self):
        self.assertTrue(risk.kill_switch({}, {"ann_vol": 0.2}))
        self.assertTrue(risk.kill_switch({"ann_vol": None}, {"ann_vol": 0.2}))

    def test_invalid_limits_trip_kill_switch(self):
        for limit in ({"max": float("nan")}, {"min": float("inf")},
                      {}, {"max": "bad"}, {"min": 2, "max": 1}):
            with self.subTest(limit=limit):
                self.assertTrue(risk.kill_switch({"ann_vol": 0.1}, {"ann_vol": limit}))

    def test_valid_boundary_semantics_are_unchanged(self):
        self.assertFalse(risk.kill_switch({"ann_vol": 0.2}, {"ann_vol": {"max": 0.2}}))
        self.assertTrue(risk.kill_switch({"ann_vol": 0.21}, {"ann_vol": {"max": 0.2}}))
        self.assertTrue(risk.kill_switch({"liquidity": 2}, {"liquidity": {"min": 3}}))

    def test_position_risk_preserves_input_freshness(self):
        result = risk.position_risk([100 + i for i in range(110)],
                                    as_of="2026-01-01", report_date="2026-09-12")
        self.assertEqual(result["disclosure"]["data_as_of"], "2026-01-01")
        self.assertTrue(result["disclosure"]["is_stale"])
        self.assertEqual(result["disclosure"]["confidence"], "LOW")

    def test_future_observation_is_not_current(self):
        with self.assertRaises(ValueError):
            risk.position_risk([100, 101, 102], as_of="2030-01-01",
                               report_date="2026-09-12")

    def test_corrupt_prices_are_refused_instead_of_dropped(self):
        for price in (float("nan"), float("inf"), 0, -1):
            with self.subTest(price=price):
                with self.assertRaises(ValueError):
                    risk.position_risk([100, price, 101, 102])

    def test_results_are_strict_json(self):
        json.dumps(risk.portfolio_risk([0.5, 0.5], [0.2, 0.2]), allow_nan=False)


class StateInvariants(unittest.TestCase):
    def portfolio(self):
        p = household.Portfolio()
        p.add_lot(household.Lot("A", "2025-01-01", 10, 1000, 0))
        return p

    def test_duplicate_specific_ids_refused_without_mutation(self):
        p = self.portfolio()
        before = copy.deepcopy(p)
        with self.assertRaises(ValueError):
            p.sell(15, 20, 500, "2026-05-16", method=household.SPECIFIC_ID,
                   specific_lot_ids=["A", "A"])
        self.assertEqual(p, before)

    def test_late_calculation_failure_does_not_mutate_lots(self):
        p = self.portfolio()
        p.add_lot(household.Lot("B", "2025-01-02", 10, float("nan"), 1))
        lots_before = list(p.lots)
        history_before = list(p.history)
        with self.assertRaises((ValueError, TypeError)):
            p.sell(15, 20, 500, "2026-05-16")
        self.assertEqual(p.lots, lots_before)
        self.assertEqual(p.history, history_before)

    def test_successful_partial_sale_conserves_shares(self):
        p = self.portfolio()
        sales = p.sell(4, 20, 500, "2026-05-16")
        self.assertEqual(sum(x.shares_sold for x in sales) +
                         sum(x.shares for x in p.lots), 10)
        self.assertEqual(sum(x.proceeds_cents for x in sales), 8000)

    def test_unknown_artifact_is_not_fresh(self):
        with tempfile.TemporaryDirectory(prefix="fis-recovery-provenance-") as td:
            graph = provenance.ProvenanceGraph(os.path.join(td, "store.json"))
            self.assertFalse(graph.explain("unregistered-artifact")["fresh"])

    def test_registered_fact_and_downstream_invalidation(self):
        with tempfile.TemporaryDirectory(prefix="fis-recovery-provenance-") as td:
            graph = provenance.ProvenanceGraph(os.path.join(td, "store.json"))
            graph.register_fact("price", "100")
            graph.record_artifact("valuation", ["price"], "synthetic.py", "v1")
            self.assertTrue(graph.explain("valuation")["fresh"])
            graph.register_fact("price", "90")
            self.assertFalse(graph.explain("valuation")["fresh"])


if __name__ == "__main__":
    unittest.main()

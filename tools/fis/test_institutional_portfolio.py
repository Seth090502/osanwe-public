#!/usr/bin/env python3
"""Synthetic portfolio arithmetic and refusal controls; no files or services."""
import copy
import ast
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import portfolio_engine as pe


class CostModel:
    def __init__(self, rate=0.0):
        self.rate = rate
        self.symbols = []

    def estimate_trade_cost(self, ticker, notional):
        self.symbols.append(ticker)
        return {"round_trip_usd": notional * self.rate}


def holding(account="A", ticker="ABC", qty=100.0, px=10.0,
            basis=10.0, asset_class="equity", term="long"):
    return {"account": account, "ticker": ticker, "issuer": ticker,
            "asset_class": asset_class, "quantity": qty, "price": px,
            "lots": [{"lot_id": account + "-" + ticker + "-L1", "quantity": qty,
                      "cost_basis": basis, "term": term}]}


CONSTRAINTS = {"max_single_issuer_pct": 100.0, "min_cash_pct": 0.0,
               "max_turnover_pct": 100.0}


def propose(portfolio, targets, cost=None, **kwargs):
    return pe.propose_rebalance(portfolio, targets,
                                {key: {"low": 0.01, "high": 0.01} for key in targets},
                                CONSTRAINTS, ecm=cost or CostModel(), **kwargs)


class PortfolioArithmetic(unittest.TestCase):
    def test_same_security_two_accounts_conserves_value_and_lots(self):
        pf = {"cash": 1000.0, "holdings": [holding("A", basis=8.0),
                                           holding("B", basis=12.0, term="short")]}
        saved = copy.deepcopy(pf)
        plan = propose(pf, {"equity": 0.5, "cash": 0.5})
        metrics = plan["action"]["metrics"]
        # Independent cash ledger: two $250 sales; value has no zero-cost drag.
        self.assertAlmostEqual(3000.0, metrics["portfolio_value_usd"])
        self.assertAlmostEqual(1500.0, metrics["post_cash_usd"])
        self.assertAlmostEqual(0.5, metrics["post_class_weights"]["equity"])
        self.assertEqual({"A", "B"}, {t["account"] for t in plan["action"]["trades"]})
        self.assertEqual(2, len(plan["action"]["trades"]))
        self.assertAlmostEqual(50.0, metrics["realized_gains"]["gross_lt_gain"])
        self.assertAlmostEqual(-50.0, metrics["realized_gains"]["gross_st_gain"])
        self.assertEqual(saved, pf)
        self.assertTrue(pe.independent_recalculation(plan, pf, ecm=CostModel()))

    def test_duplicate_position_in_same_account_refused(self):
        pf = {"cash": 1000.0, "holdings": [holding(), holding()]}
        with self.assertRaisesRegex(ValueError, "duplicate position"):
            propose(pf, {"equity": 0.5, "cash": 0.5})

    def test_class_sale_then_issuer_trim_cannot_sell_depleted_holding_twice(self):
        equity = holding("A", "X-EQ", qty=90.0)
        bond = holding("A", "X-BOND", qty=90.0, asset_class="bond")
        equity["issuer"] = bond["issuer"] = "X"
        pf = {"cash": 0.0, "holdings": [equity, bond]}
        targets = {"equity": 0.05, "bond": 0.65, "cash": 0.3}
        plan = pe.propose_rebalance(pf, targets,
            {key: {"low": 0.01, "high": 0.01} for key in targets},
            dict(CONSTRAINTS, max_single_issuer_pct=25.0), ecm=CostModel())
        self.assertAlmostEqual(1800.0, plan["action"]["metrics"]["portfolio_value_usd"])
        for trade in plan["action"]["trades"]:
            if trade["side"] == "SELL":
                self.assertLessEqual(trade["qty"], 90.0)

    def test_explicit_existing_cash_can_increase_small_holding_more_than_twofold(self):
        pf = {"cash": 900.0, "cash_account": "A", "holdings": [holding(qty=10.0)]}
        plan = propose(pf, {"equity": 0.9, "cash": 0.1})
        self.assertEqual("proposed", plan["status"])
        self.assertAlmostEqual(800.0, sum(t["notional_usd"] for t in plan["action"]["trades"]))
        self.assertAlmostEqual(0.9, plan["action"]["metrics"]["post_class_weights"]["equity"])
        self.assertAlmostEqual(100.0, plan["action"]["metrics"]["post_cash_usd"])

    def test_scalar_cash_is_not_assumed_to_belong_to_holding_account(self):
        pf = {"cash": 900.0, "holdings": [holding(qty=10.0)]}
        plan = propose(pf, {"equity": 0.9, "cash": 0.1})
        self.assertEqual("rejected", plan["status"])
        self.assertEqual([], plan["action"]["trades"])
        self.assertEqual("INSUFFICIENT_ACCOUNT_FUNDING", plan["data_gaps"][0]["code"])
        self.assertAlmostEqual(1000.0, plan["action"]["metrics"]["portfolio_value_usd"])

    def test_explicit_account_argument_binds_scalar_cash(self):
        pf = {"cash": 900.0, "holdings": [holding(qty=10.0)]}
        plan = propose(pf, {"equity": 0.9, "cash": 0.1}, account="A")
        self.assertEqual("proposed", plan["status"])
        self.assertTrue(pe.independent_recalculation(plan, pf, ecm=CostModel(), account="A"))

    def test_no_silent_cross_account_sale_funding(self):
        pf = {"cash": 0.0, "holdings": [holding("A", qty=90.0),
               holding("B", "BOND", qty=10.0, asset_class="bond")]}
        plan = propose(pf, {"equity": 0.1, "bond": 0.9, "cash": 0.0})
        self.assertEqual("rejected", plan["status"])
        self.assertTrue(plan["data_gaps"])
        self.assertFalse(any(t["side"] == "BUY" for t in plan["action"]["trades"]))
        self.assertAlmostEqual(800.0, plan["action"]["account_funding"]["post_cash_by_account"]["A"])

    def test_same_account_sale_can_fund_buy(self):
        pf = {"cash": 0.0, "holdings": [holding("A", qty=90.0),
               holding("A", "BOND", qty=10.0, asset_class="bond")]}
        plan = propose(pf, {"equity": 0.1, "bond": 0.9, "cash": 0.0})
        self.assertEqual("proposed", plan["status"])
        self.assertAlmostEqual(0.9, plan["action"]["metrics"]["post_class_weights"]["bond"])

    def test_explicit_cash_accounts_reconcile_and_deploy(self):
        pf = {"cash": 800.0, "cash_by_account": {"A": 400.0, "B": 400.0},
              "holdings": [holding("A", qty=10.0), holding("B", qty=10.0)]}
        plan = propose(pf, {"equity": 0.9, "cash": 0.1})
        self.assertEqual("proposed", plan["status"])
        balances = plan["action"]["account_funding"]["post_cash_by_account"]
        self.assertAlmostEqual(50.0, balances["A"])
        self.assertAlmostEqual(50.0, balances["B"])
        pf["cash_by_account"]["B"] = 300.0
        with self.assertRaisesRegex(ValueError, "reconcile"):
            propose(pf, {"equity": 0.9, "cash": 0.1})

    def test_costs_reserved_before_cash_deployment(self):
        pf = {"cash": 900.0, "cash_account": "A", "holdings": [holding(qty=10.0)]}
        plan = propose(pf, {"equity": 0.9, "cash": 0.1}, CostModel(0.01))
        metrics = plan["action"]["metrics"]
        # Closed-form budget x + .01*x = 800, independent of bisection.
        self.assertAlmostEqual(800.0 / 1.01, plan["action"]["trades"][0]["notional_usd"])
        self.assertAlmostEqual(100.0, metrics["post_cash_usd"])
        self.assertAlmostEqual(1000.0 - 8.0 / 1.01, metrics["portfolio_value_usd"])
        self.assertEqual("proposed", plan["status"])

    def test_account_label_never_changes_ecm_security_symbol(self):
        h = holding(ticker="MSFT@A", basis=8.0)
        h["security_symbol"] = "MSFT"
        pf = {"cash": 100.0, "holdings": [h]}
        cost = CostModel()
        plan = propose(pf, {"equity": 0.5, "cash": 0.5}, cost)
        self.assertTrue(cost.symbols)
        self.assertEqual({"MSFT"}, set(cost.symbols))
        self.assertEqual("MSFT@A", plan["action"]["trades"][0]["ticker"])
        self.assertEqual("MSFT", plan["action"]["trades"][0]["security_symbol"])

    def test_scenario_adapter_preserves_source_symbol_without_importing_runtime(self):
        source = Path(__file__).with_name("scenarios_e2e.py").read_text(encoding="utf-8")
        fn = next(node for node in ast.parse(source).body
                  if isinstance(node, ast.FunctionDef) and node.name == "portfolio_from_twin")
        namespace = {"TAXABLE_ACCOUNT_TYPES": {"taxable"}, "NOMINAL_PRICES": {},
                     "days_between": lambda *args: 400, "asset_class_of": lambda sym: "equity"}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), "<pure-scenario-adapter>", "exec"), namespace)
        doc = {"accounts": [{"id": "A", "type": "taxable", "holdings": [
            {"symbol": "MSFT", "qty": 2, "tax_lots": [
                {"qty": 2, "cost_basis": 100, "acq_date": "2024-01-01"}]}]}]}
        out = namespace["portfolio_from_twin"](doc, {"A|MSFT": 100}, "2026-01-01")
        self.assertEqual("MSFT", out["holdings"][0]["security_symbol"])
        self.assertEqual("MSFT@A", out["holdings"][0]["ticker"])


class ReplayControls(unittest.TestCase):
    def setUp(self):
        self.pf = {"cash": 100.0, "holdings": [holding(basis=8.0)]}
        self.plan = propose(self.pf, {"equity": 0.5, "cash": 0.5})

    def reject(self, edit):
        changed = copy.deepcopy(self.plan)
        edit(changed)
        with self.assertRaises((AssertionError, ValueError, KeyError)):
            pe.independent_recalculation(changed, self.pf, ecm=CostModel())

    def test_finite_valid_plan_and_custom_tax_rates(self):
        rates = {"long": 0.3, "short": 0.4}
        plan = propose(self.pf, {"equity": 0.5, "cash": 0.5}, tax_rates=rates)
        self.assertAlmostEqual(27.0, plan["action"]["metrics"]["realized_gains"]["tax_usd"])
        self.assertTrue(pe.independent_recalculation(plan, self.pf, ecm=CostModel(), tax_rates=rates))

    def test_nonfinite_metrics_and_trade_quantities_refused(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                self.reject(lambda p: p["action"]["metrics"].update(ecm_cost_usd=value))
                self.reject(lambda p: p["action"]["trades"][0].update(qty=value))

    def test_missing_weight_keys_refused(self):
        for field in ("post_class_weights", "post_issuer_weights"):
            with self.subTest(field=field):
                self.reject(lambda p: p["action"]["metrics"].update({field: {}}))

    def test_tax_amount_tamper_refused(self):
        self.reject(lambda p: p["action"]["metrics"]["realized_gains"].update(tax_usd=999999.0))

    def test_term_reassignment_preserving_total_is_refused(self):
        def edit(p):
            gains = p["action"]["metrics"]["realized_gains"]
            gains["st_net_gain"] = gains["lt_net_gain"]
            gains["lt_net_gain"] = 0.0
        self.reject(edit)

    def test_pre_value_and_corresponding_turnover_tamper_refused(self):
        def edit(p):
            m = p["action"]["metrics"]
            m["v_pre_usd"] *= 2
            m["turnover_one_sided_pct"] /= 2
        self.reject(edit)

    def test_repeated_lot_fill_and_unknown_side_refused(self):
        def edit(p):
            fills = p["action"]["trades"][0]["lot_fills"]
            lot, qty = fills[0]
            fills[:] = [(lot, qty / 2), (lot, qty / 2)]
        self.reject(edit)
        self.reject(lambda p: p["action"]["trades"][0].update(side="TRANSFER"))

    def test_account_funding_metadata_tamper_refused(self):
        self.reject(lambda p: p["action"]["account_funding"].update(unallocated_starting_cash_usd=999.0))

    def test_no_action_metrics_are_verified(self):
        pf = {"cash": 100.0, "holdings": [holding(qty=10.0)]}
        plan = propose(pf, {"equity": 0.5, "cash": 0.5})
        self.assertIsNone(plan["action"])
        self.assertTrue(pe.independent_recalculation(plan, pf, ecm=CostModel()))
        plan["no_action"]["metrics"]["portfolio_value_usd"] = 999.0
        with self.assertRaises(AssertionError):
            pe.independent_recalculation(plan, pf, ecm=CostModel())


if __name__ == "__main__":
    unittest.main(verbosity=2)

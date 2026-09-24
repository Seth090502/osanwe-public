"""Independent numerical/invariant oracles for research valuation/allocation."""
import dataclasses
import copy
from decimal import Decimal, localcontext
import math
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import numpy as np

from allocation import black_litterman, optimize_allocation
import allocation
from valuation import OperatingDCF, operating_dcf, implied_operating_margin, sensitivity
from calcs_core import annuity_pv, level_payment


def fixture():
    return OperatingDCF(1000., (.10, .08, .05), (.20, .20, .20), (.25,) * 3,
                        (2.,) * 3, (.10,) * 3, .03, .20, .25, .12, .10,
                        100., 200., 0., 100., "USD", "2026-09-12", ("synthetic:drivers",))


class ValuationTests(unittest.TestCase):
    def test_negative_and_near_zero_discount_rates(self):
        with localcontext() as ctx:
            ctx.prec=50
            for rate in [Decimal("-.01"),Decimal("1e-14")]:
                expected=sum(Decimal(100)/(1+rate)**j for j in range(1,25))
                actual=annuity_pv(100.,float(rate),24)
                self.assertAlmostEqual(actual,float(expected),places=9)
                self.assertAlmostEqual(level_payment(actual,float(rate)*12,24),100,places=9)
        with self.assertRaises(ValueError):annuity_pv(1,-1,12)

    def test_independent_decimal_cashflow_bridge(self):
        s = fixture()
        out = operating_dcf(s)
        with localcontext() as ctx:
            ctx.prec = 45
            r = Decimal("1000"); total = Decimal(0)
            for year, growth in enumerate((".10", ".08", ".05"), 1):
                next_r = r * (1 + Decimal(growth))
                cf = next_r * Decimal(".15") - (next_r - r) / 2
                total += cf / Decimal("1.10") ** year
                r = next_r
            terminal = r * Decimal("1.03") * Decimal(".15") * Decimal(".75") / Decimal(".07")
            total += terminal / Decimal("1.1") ** 3
        self.assertAlmostEqual(out["enterprise_value"], float(total), places=9)
        self.assertAlmostEqual(out["value_per_share"], (float(total) - 100) / 100, places=10)

    def test_growth_at_cost_of_capital_creates_no_terminal_excess(self):
        s = dataclasses.replace(fixture(), terminal_roic=.10, terminal_growth=.0)
        a = operating_dcf(s)
        b = operating_dcf(dataclasses.replace(s, terminal_growth=.05))
        # NOPAT in year N+1 changes with growth; value per terminal NOPAT is 1/WACC.
        self.assertAlmostEqual(a["terminal_value"] / a["terminal_nopat"], 10)
        self.assertAlmostEqual(b["terminal_value"] / b["terminal_nopat"], 10)

    def test_reinvestment_prevents_free_growth(self):
        a = operating_dcf(fixture())
        b = operating_dcf(dataclasses.replace(fixture(), sales_to_capital=(.5,) * 3))
        self.assertLess(b["enterprise_value"], a["enterprise_value"])

    def test_terminal_and_input_refusals(self):
        for change in (dict(terminal_growth=.1), dict(terminal_roic=.01), dict(revenue=math.nan),
                       dict(wacc=(.1,)), dict(diluted_shares=0), dict(input_ids=()),
                       dict(diluted_shares=1e-308),dict(input_ids="source"),
                       dict(cash=True), dict(currency="usd"), dict(terminal_growth=-.01)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                operating_dcf(dataclasses.replace(fixture(), **change))

    def test_losses_do_not_create_unmodeled_tax_credit(self):
        out = operating_dcf(dataclasses.replace(fixture(), margins=(-.1,) * 3))
        self.assertTrue(all(r["cash_tax"] == 0 for r in out["forecast"]))

    def test_decline_capital_release_explicit(self):
        s = dataclasses.replace(fixture(), growth=(-.1,) * 3)
        a = operating_dcf(s); b = operating_dcf(dataclasses.replace(s, release_capital_on_decline=True))
        self.assertEqual(a["forecast"][0]["reinvestment"], 0)
        self.assertLess(b["forecast"][0]["reinvestment"], 0)
        self.assertGreater(b["enterprise_value"], a["enterprise_value"])

    def test_debt_and_dilution_bridge(self):
        a = operating_dcf(fixture())
        b = operating_dcf(dataclasses.replace(fixture(), diluted_shares=200))
        self.assertAlmostEqual(b["value_per_share"] * 2, a["value_per_share"])
        c = operating_dcf(dataclasses.replace(fixture(), debt=1e9))
        self.assertEqual(c["value_per_share"], 0)
        self.assertLess(c["equity_value_unfloored"], 0)

    def test_inverse_roundtrip_and_no_bracket(self):
        price = operating_dcf(fixture())["value_per_share"]
        result = implied_operating_margin(fixture(), price)
        self.assertAlmostEqual(result["implied_margin"], .20, places=8)
        with self.assertRaises(ValueError):
            implied_operating_margin(fixture(), 1e9)

    def test_sensitivity_retains_refused_cases(self):
        grid = sensitivity(fixture(), discount_shifts=[0, -.08], terminal_growths=[.03, .04])
        self.assertEqual(len(grid), 4)
        self.assertEqual(sum(r["status"] == "refused" for r in grid), 2)
        grid=sensitivity(fixture(),discount_shifts=iter([0,.01]),terminal_growths=iter([.02,.03]))
        self.assertEqual(len(grid),4)


class AllocationTests(unittest.TestCase):
    def test_roundoff_curvature_allowance_covers_simplex_remainder(self):
        cov=np.array([[1,1+5e-15],[1+5e-15,1]])
        center=SimpleNamespace(success=True,x=np.array([.5,.5,0,0]),nit=1,message="stationary")
        with patch("allocation.minimize",return_value=center):out=self.solve(cov)
        improvement=.5*np.array([.5,.5])@cov@np.array([.5,.5])-.5
        self.assertGreaterEqual(out["certificate"]["convex_gap_upper_bound"],improvement)

    def test_false_linear_oracle_success_refused(self):
        real=allocation.linprog
        for corruption in ["nan","infeasible","suboptimal"]:
            count=[0]
            def fake(*args,**kw):
                count[0]+=1
                result=real(*args,**kw)
                if count[0]==2:
                    if corruption=="nan":result.x[:]=np.nan
                    elif corruption=="infeasible":result.x[:]=10
                    else:result.x=np.array([.5,.5,0,0])
                return result
            with self.subTest(corruption=corruption), patch("allocation.linprog",side_effect=fake), self.assertRaises(ValueError):
                self.solve([[.04,0],[0,.09]],max_weight=.6)

    def test_fake_solver_success_fails_independent_gap(self):
        bad=SimpleNamespace(success=True,x=np.array([.99,.01,.49,.49]),nit=1,message="claimed success")
        with patch("allocation.minimize",return_value=bad), self.assertRaisesRegex(ValueError,"optimality gap"):
            self.solve([[.04,0],[0,.09]])

    def solve(self, cov, **kw):
        n = len(cov)
        return optimize_allocation(cov, current_weights=kw.pop("current_weights", [1/n]*n),
                                   one_way_costs=kw.pop("one_way_costs", [0]*n), **kw)

    def test_closed_form_two_asset_minimum(self):
        cov = [[.04, .012], [.012, .09]]
        expected = (.09 - .012) / (.04 + .09 - 2*.012)
        out = self.solve(cov)
        self.assertAlmostEqual(out["weights"][0], expected, places=6)
        self.assertLess(out["certificate"]["normalized_gap"], 1e-6)

    def test_dense_grid_oracle_cost_and_bounds(self):
        cov = np.array([[.04, .005], [.005, .09]])
        mu = np.array([.06, .08]); current = np.array([.4, .6]); costs = np.array([.01, .04])
        out = self.solve(cov, current_weights=current, one_way_costs=costs,
                         expected_returns=mu, risk_aversion=3, max_weight=.7)
        grid = np.linspace(.3, .7, 100001)
        weights = np.column_stack((grid, 1-grid))
        losses = 1.5*np.einsum("ij,jk,ik->i", weights, cov, weights) - weights@mu + np.abs(weights-current)@costs
        self.assertLessEqual(out["objective_value"], float(losses.min())+1e-8)

    def test_costs_produce_no_trade_region(self):
        out = self.solve([[.04, 0], [0, .09]], current_weights=[.5, .5], one_way_costs=[.5, .5])
        np.testing.assert_allclose(out["weights"], [.5, .5], atol=1e-8)

    def test_exposure_and_turnover_constraints(self):
        out = self.solve(np.diag([.01, .02, .09]), max_weight=.6, max_turnover=.1,
                         exposures=[dict(name="sector", loadings=[1,1,0], lower=.3, upper=.7)])
        self.assertLessEqual(out["turnover_l1"], .1+1e-8)
        self.assertLessEqual(sum(out["weights"][:2]), .7+1e-8)

    def test_invalid_and_infeasible_refusal(self):
        for cov, kw in [([[1, 2], [2, 1]], {}), ([[1, .1], [.2, 1]], {}),
                        ([[1, 0], [0, 1]], dict(max_weight=.4)),
                        ([[1, 0], [0, 1]], dict(current_weights=[0,0], max_turnover=.5)),
                        ([[1, 0], [0, 1]], dict(one_way_costs=[-1,0]))]:
            with self.subTest(kw=kw), self.assertRaises(ValueError):
                self.solve(cov, **kw)

    def test_shared_covariance_and_boolean_refusals(self):
        for cov,kw in [([[1e200,0],[0,1e-200]],{}), ([[True,0],[0,1]],{}),
                       ([[1,0],[0,1]],dict(current_weights=[True,0]))]:
            with self.subTest(cov=cov,kw=kw),self.assertRaises(ValueError):
                self.solve(cov,**kw)

    def test_permutation_equivariance(self):
        cov = np.array([[.03,.005,0],[.005,.07,.01],[0,.01,.1]])
        p = [2,0,1]
        a = self.solve(cov)["weights"]
        b = self.solve(cov[np.ix_(p,p)])["weights"]
        np.testing.assert_allclose(np.array(a)[p], b, atol=2e-6)

    def test_black_litterman_no_views(self):
        cov = np.diag([.04, .09])
        out = black_litterman(cov, [.6,.4], risk_aversion=2, tau=.05)
        np.testing.assert_allclose(out["posterior_returns"], 2*cov@np.array([.6,.4]))

    def test_black_litterman_precision_oracle(self):
        cov = np.array([[.04,.01],[.01,.09]]); w = np.array([.6,.4]); p=np.array([[1.,-1.]])
        omega=np.array([[.0025]]); q=np.array([.05]); prior=2*cov@w
        precision=np.linalg.inv(.05*cov)+p.T@np.linalg.solve(omega,p)
        expected=np.linalg.solve(precision,np.linalg.solve(.05*cov,prior)+p.T@np.linalg.solve(omega,q))
        out=black_litterman(cov,w,risk_aversion=2,tau=.05,pick_matrix=p,views=q,view_covariance=omega)
        np.testing.assert_allclose(out["posterior_returns"],expected,atol=1e-12)
        np.testing.assert_allclose(out["mean_uncertainty"],np.linalg.inv(precision),atol=1e-12)

    def test_black_litterman_weak_views_and_unknown_confidence(self):
        cov=np.diag([.04,.09]); args=dict(risk_aversion=2,tau=.05,pick_matrix=[[1,-1]],views=[.5])
        with self.assertRaises(ValueError):
            black_litterman(cov,[.5,.5],**args)
        out=black_litterman(cov,[.5,.5],**args,view_covariance=[[1e8]])
        np.testing.assert_allclose(out["posterior_returns"],out["prior_returns"],atol=1e-9)


if __name__ == "__main__":
    unittest.main()

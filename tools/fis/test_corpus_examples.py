"""Independent synthetic oracles for the eight public financial method notes.

No personal records, network calls or market inference. The rational examples
are explicit assumptions and calculations, not current facts or probabilities.
Run directly for unittest; --json emits the actual result plus bounded examples.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from fractions import Fraction as F
import io
import json
import math
from pathlib import Path
import sys
import unittest

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT))
from fis import calcs_core, calcs_household, calcs_ledger, valuation


def rational_examples():
    """Transparent independent expressions for source-admission receipts."""
    cases = [
        ("E2-ttm", "42 + 33 - 27", F(48), "million", "USD", "annual revenue"),
        ("E2-restated-ttm", "40 + 33 - 27", F(46), "million", "USD", "annual revenue"),
        ("E2-quarter", "42 - 30", F(12), "million", "USD", "quarter revenue"),
        ("V2-fcff", "1000 * 0.2 * (1 - 0.25)", F(150), "million", "USD", "annual cash flow"),
        ("V2-equity", "150 / 0.1 + 100 - 300 - 50", F(1250), "million", "USD", "equity value"),
        ("V2-per-share", "1250 / 100", F(25, 2), "per_share", "USD", "equity per diluted share"),
        ("V2-sbc", "240 - 40", F(200), "million", "USD", "annual GAAP EBIT"),
        ("R2-variance", "0.25 * 0.04 + 0.25 * 0.01 + 0.5 * 0.005", F(3, 200), "return_squared", None, "annual"),
        ("R2-stress", "0.5 * (-0.4) + 0.5 * (-0.1)", F(-1, 4), "return", None, "joint one-step shock"),
        ("P2-twr", "1.1 * 0.9 - 1", F(-1, 100), "return", None, "two-year cumulative"),
        ("P2-pnl", "180 - 100 - 90", F(-10), "dollar", "USD", "two-year net investment change"),
        ("P3-portfolio-return", "0.6 * 0.1 + 0.4 * 0.02", F(17, 250), "return", None, "single period"),
        ("P3-active-return", "0.068 - 0.06", F(1, 125), "return", None, "single period"),
        ("P3-fx", "1.1 * 0.95 - 1", F(9, 200), "return", None, "single period"),
        ("F2-cost-a", "10000 * (0.002 + 0.001)", F(30), "dollar", "USD", "one year and one round trip"),
        ("F2-cost-b", "10000 * (0.0002 + 0.008)", F(82), "dollar", "USD", "one year and one round trip"),
        ("F2-break-even", "(80 - 10) / (20 - 2)", F(35, 9), "year", None, "constant exposure and spreads"),
        ("F2-reset", "1.2 * (1 - 2 / 11) - 1", F(-1, 55), "return", None, "two daily reset periods"),
        ("B2-bond", "5 / 1.06 + 105 / (1.06 * 1.06)", F(275750, 2809), "dollar", "USD", "annual coupon-date full price"),
        ("B2-liability", "100 / (1.05 * 1.05)", F(40000, 441), "dollar", "USD", "two-year present value"),
        ("B2-tips-coupon", "1000 * 1.03 * 0.01 / 2", F(103, 20), "dollar", "USD", "semiannual coupon"),
        ("B2-inflation", "1.05 / 1.02 - 1", F(1, 34), "rate", None, "annual compounded break-even"),
        ("H1-surplus", "5000 - 3000 - 500 - 500", F(1000), "dollar", "USD", "monthly"),
        ("H1-shock", "5000 * 0.8 - 3000 - 500 - 500", F(0), "dollar", "USD", "monthly"),
        ("H1-transfer", "(-1000) + 1000", F(0), "dollar", "USD", "household net internal transfer"),
        ("H1-reserve", "9000 / 3000", F(3), "month", None, "essential expense coverage"),
        ("H2-basis", "850 + (1000 - 800)", F(1050), "dollar", "USD", "taxable replacement basis under stated conditions"),
        ("H3-adverse-first", "((100 - 10) * 0.8 - 10) * 1.25", F(155, 2), "dollar", "USD", "two annual start-of-year withdrawals"),
        ("H3-adverse-last", "((100 - 10) * 1.25 - 10) * 0.8", F(82), "dollar", "USD", "two annual start-of-year withdrawals"),
    ]
    return [dict(example_id=k, expression=e, expected_fraction={"numerator": n.numerator, "denominator": n.denominator},
                 result=float(n), unit=u, currency=c, basis=b, classification="SYNTHETIC") for k, e, n, u, c, b in cases]


class CorpusExamples(unittest.TestCase):
    def test_duration_and_restated_information(self):
        self.assertEqual(F(42) + F(33) - F(27), 48)
        self.assertEqual(F(40) + F(33) - F(27), 46)
        self.assertEqual(F(42) - F(30), 12)
        self.assertNotEqual(F(42) + F(30), 12)

    @staticmethod
    def spec():
        return valuation.OperatingDCF(revenue=1000, growth=(0.,), margins=(.2,), tax_rates=(.25,),
            sales_to_capital=(2.,), wacc=(.1,), terminal_growth=0, terminal_margin=.2,
            terminal_tax_rate=.25, terminal_roic=.15, terminal_wacc=.1, cash=100,
            debt=300, other_claims=50, diluted_shares=100, currency="USD", as_of="2026-01-01",
            input_ids=("synthetic-V2",))

    def test_dcf_against_perpetuity_oracle(self):
        result = valuation.operating_dcf(self.spec())
        fcff = F(1000) * F(1, 5) * F(3, 4)
        ev = fcff / F(1, 10)
        equity = ev + 100 - 300 - 50
        self.assertAlmostEqual(result["enterprise_value"], float(ev), places=9)
        self.assertAlmostEqual(result["equity_value_unfloored"], float(equity), places=9)
        self.assertAlmostEqual(result["value_per_share"], float(equity / 100), places=9)
        self.assertNotEqual(fcff, ev)  # Earnings alone cannot stand in for enterprise value.

    def test_reverse_margin_against_algebra(self):
        result = valuation.implied_operating_margin(self.spec(), 15)
        required_ev = F(15) * 100 - 100 + 300 + 50
        required_margin = required_ev * F(1, 10) / (1000 * F(3, 4))
        self.assertAlmostEqual(result["implied_margin"], float(required_margin), places=9)
        self.assertEqual(required_margin, F(7, 30))

    def test_terminal_growth_boundary_refuses(self):
        with self.assertRaises(ValueError):
            valuation.operating_dcf(replace(self.spec(), terminal_growth=.1))

    def test_sbc_reconciliation_direction(self):
        non_gaap, excluded_sbc = F(240), F(40)
        gaap = non_gaap - excluded_sbc
        self.assertEqual(gaap, 200)
        self.assertNotEqual(non_gaap + excluded_sbc, gaap)

    def test_covariance_and_joint_shocks(self):
        variance = F(1, 4)*F(4, 100) + F(1, 4)*F(1, 100) + F(1, 2)*F(5, 1000)
        self.assertEqual(variance, F(3, 200))
        self.assertAlmostEqual(math.sqrt(float(variance)), .1224744871391589)
        perfect = F(1, 4)*F(4, 100) + F(1, 4)*F(1, 100) + F(1, 2)*F(2, 100)
        self.assertAlmostEqual(math.sqrt(float(perfect)), .15)
        self.assertEqual(F(1, 2)*F(-4, 10) + F(1, 2)*F(-1, 10), F(-1, 4))

    def test_discrete_kelly_is_not_universal_three_quarters(self):
        full = .6*math.log1p(.2) + .4*math.log1p(-.2)
        half = .6*math.log1p(.1) + .4*math.log1p(-.1)
        self.assertAlmostEqual(full, .020135513550688863)
        self.assertAlmostEqual(half, .015041901619464441)
        self.assertGreater(abs(half/full - .75), .002)

    def test_cashflow_return_reconciles(self):
        first = F(110, 100)-1
        second = F(180, 200)-1
        self.assertEqual((1+first)*(1+second)-1, F(-1, 100))
        self.assertEqual(F(180)-100-90, -10)
        self.assertNotEqual(F(180, 100)-1, F(-1, 100))
        irr = (-90+math.sqrt(80100))/200-1
        self.assertAlmostEqual(100*(1+irr)**2 + 90*(1+irr), 180)
        self.assertAlmostEqual(irr, -.034902830191509526)

    def test_brinson_against_independent_fraction_totals(self):
        got = calcs_ledger.brinson_attribution({"A":.6,"B":.4},{"A":.1,"B":.02},
            {"A":.5,"B":.5},{"A":.08,"B":.04})
        self.assertAlmostEqual(got["portfolio_return"], float(F(17, 250)))
        self.assertAlmostEqual(got["benchmark_return"], float(F(3, 50)))
        self.assertAlmostEqual(got["allocation_effect"], float(F(1, 250)))
        self.assertAlmostEqual(got["selection_effect"], 0)
        self.assertAlmostEqual(got["interaction_effect"], float(F(1, 250)))
        self.assertAlmostEqual(got["total_excess_return"], float(F(1, 125)))
        self.assertLess(got["unexplained_residual"], 1e-12)

    def test_attribution_missing_segment_refuses(self):
        with self.assertRaises(calcs_ledger.MissingInputError):
            calcs_ledger.brinson_attribution({"A":1},{"A":.1},{"B":1},{"B":.04})

    def test_currency_interaction(self):
        self.assertEqual(F(11,10)*F(95,100)-1, F(9,200))
        self.assertNotEqual(F(1,10)-F(5,100), F(9,200))

    def test_selection_and_small_sample_limits(self):
        false_positive = 1-F(95,100)**20
        self.assertAlmostEqual(float(false_positive), .6415140775914581)
        upper = 1-.05**(1/10)
        self.assertAlmostEqual((1-upper)**10, .05)
        self.assertAlmostEqual(upper, .2588655508930523)

    def test_etf_cost_and_reset(self):
        self.assertEqual(10000*(F(20,10000)+F(10,10000)), 30)
        self.assertEqual(10000*(F(2,10000)+F(80,10000)), 82)
        self.assertEqual(F(70,18), F(35,9))
        self.assertEqual(F(11,10)*(1-F(1,11))-1, 0)
        self.assertEqual(F(12,10)*(1-F(2,11))-1, F(-1,55))

    def test_bond_and_liability_against_discounted_flows(self):
        oracle = F(5)/F(106,100) + F(105)/F(106,100)**2
        self.assertEqual(oracle, F(275750,2809))
        self.assertAlmostEqual(calcs_core.bond_price_level(100,.05,.06,2,1),float(oracle))
        self.assertAlmostEqual(calcs_core.bond_price_level(100,.05,.05,2,1),100)
        self.assertAlmostEqual(calcs_core.present_value(100,.05,2),float(F(40000,441)))

    def test_tips_and_compounded_inflation(self):
        self.assertEqual(1000*F(103,100)*F(1,100)/2,F(103,20))
        self.assertEqual(F(105,100)/F(102,100)-1,F(1,34))
        self.assertNotEqual(F(1,34),F(3,100))

    def test_household_scope_and_tax_arithmetic(self):
        self.assertEqual(F(5000)-3000-500-500,1000)
        self.assertEqual(F(5000)*F(4,5)-3000-500-500,0)
        self.assertEqual(F(-1000)+1000,0)
        self.assertEqual(F(850)+(1000-800),1050)
        self.assertEqual(calcs_household.emergency_months_coverage(9000,3000)["months"],3)
        with self.assertRaises(ValueError):
            calcs_household.emergency_months_coverage(9000,0)

    def test_withdrawal_order_of_returns_matters(self):
        adverse_first = ((F(100)-10)*F(4,5)-10)*F(5,4)
        adverse_last = ((F(100)-10)*F(5,4)-10)*F(4,5)
        self.assertEqual(adverse_first,F(155,2))
        self.assertEqual(adverse_last,82)
        self.assertEqual(F(4,5)*F(5,4),1)
        self.assertGreater(adverse_last,adverse_first)


def main():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CorpusExamples)
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output,verbosity=2).run(suite)
    if "--json" in sys.argv:
        print(json.dumps({"schema":"osanwe.public-corpus-examples/1",
            "classification":"SYNTHETIC", "verified_at":datetime.now(timezone.utc).isoformat(),
            "passed":result.wasSuccessful(),"tests_run":result.testsRun,
            "failures":len(result.failures),"errors":len(result.errors),
            "result_log":output.getvalue(),"examples":rational_examples()},indent=2))
    else:
        print(output.getvalue(),end="")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

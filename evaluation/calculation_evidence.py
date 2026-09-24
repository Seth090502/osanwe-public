"""Independent rational calculations supplied equally to Read-only pilot arms.

These calculations use explicit synthetic inputs, not oracle lookups. They let
native sessions interpret calculation evidence without pretending mental math
is execution of the production workbench. No observed financial value is used.
"""
from fractions import Fraction as F


def evidence(scenario):
    recipes = {
        'perpetuity-fcff': [('enterprise_value', '100 / (0.10 - 0.03)', F(100)/(F(10,100)-F(3,100)), 'USD million')],
        'enterprise-equity-bridge': [('equity_value', '900 - 200 + 50', 900-200+50, 'USD million'), ('per_share_value', '(900 - 200 + 50) / 25', F(750,25), 'USD per share')],
        'operating-expense-label': [('gross_profit', '1200 - 700', 1200-700, 'USD million'), ('operating_expenses', '(1200 - 700) - 180', (1200-700)-180, 'USD million'), ('total_operating_costs', '1200 - 180', 1200-180, 'USD million')],
        'perfect-correlation': [('portfolio_variance', '0.5^2*0.2^2 + 0.5^2*0.2^2 + 2*0.5*0.5*1*0.2*0.2', F(4,100), 'return squared'), ('portfolio_volatility', 'sqrt(0.04)*100', 20, 'percent')],
        'optimization-cost-baseline': [('optimizer_net', '8.4 - 1.2', F(72,10), 'percentage points'), ('equal_weight_net', '8.0 - 0.2', F(78,10), 'percentage points')],
        'next-close-cost': [('net_return', '(110/102 - 1)*100 - 0.4', (F(110,102)-1)*100-F(4,10), 'percentage points')],
        'zero-coupon-sensitivity': [('initial_price', '100/1.04', F(10000,104), 'USD'), ('scenario_price', '100/1.05', F(10000,105), 'USD')],
        'nominal-real-rate': [('approximate_real_yield', '5 - 3', 5-3, 'percent')],
        'round-trip-spread': [('round_trip_loss', '(101 - 99)*10', 20, 'USD')],
        'spread-midpoint': [('quoted_spread', '(50.05 - 49.95)/50*10000', (F(5005,100)-F(4995,100))/50*10000, 'basis points')],
        'borrow-cost-net': [('net_return', '6 - 4 - 0.5 - 0.5', 6-4-F(5,10)-F(5,10), 'percentage points')],
        'internal-transfer-saving': [('external_surplus', '5000 - 3000', 2000, 'synthetic currency units')],
        'partial-account-scope': [('covered_account_flow', '4000 - 2500', 1500, 'synthetic currency units')],
    }
    return [{'metric':metric,'expression':expression,'value':float(value),'unit':unit,
             'source_id':'s1','scope':'synthetic scenario period and stated account scope only',
             'calculation':'Python fractions; public evaluator fixture calculation, not production workbench replay'}
            for metric,expression,value,unit in recipes.get(scenario,[])]

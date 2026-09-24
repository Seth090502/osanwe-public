"""Build openly inspectable synthetic tasks. These are NEVER sealed admission data."""
from __future__ import annotations
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from calculation_evidence import evidence


def build_cases():
    cases = []

    def add(family, slug, question, passage, answers, *, vocabulary=(), limitation=None):
        number = 1 + sum(x['family'] == family for x in cases)
        cid = f'{family}-{number:02}'
        obligations = []
        criteria = []
        for index, (prompt, expected, severity) in enumerate(answers, 1):
            oid = f'o{index}'
            obligations.append({'id': oid, 'question': prompt})
            criteria.append({'id': oid, 'answerable': expected is not None, 'value': expected,
                             'tolerance': 0.000001 if isinstance(expected, (int, float)) else 0,
                             'source_sets': [['s1']], 'severity': severity})
        if limitation:
            obligations.append({'id': f'o{len(criteria)+1}', 'question': limitation})
            criteria.append({'id': obligations[-1]['id'], 'answerable': False, 'value': None,
                             'tolerance': 0, 'source_sets': [['s1']], 'severity': 'major'})
        words = sorted(set(vocabulary) | {x['value'] for x in criteria if isinstance(x['value'], str)})
        cases.append({'id': cid, 'family': family, 'scenario_family': slug,
                      'source_family': f'synthetic-{slug}', 'version': '1', 'privacy': 'synthetic',
                      'input': {'schema': 'osanwe.reasoning-task/1', 'case_id': cid, 'privacy': 'synthetic',
                                'question': question, 'decision_horizon': 'as of the stated scenario cutoff',
                                'obligations': obligations,
                                'sources': [{'id': 's1', 'origin_id': f'fixture-{slug}',
                                             'label': 'Synthetic scenario, not observed financial data',
                                             'version': '1', 'passage': passage}],
                                'answer_vocabulary': words},
                      'oracle': {'schema': 'osanwe.reasoning-oracle/1', 'obligations': criteria,
                                 'prose_review': 'required separately for prose quality claims'},
                      'curation': 'development author exposed; independent oracle check required before admission'})
        cases[-1]['input']['calculation_evidence'] = evidence(slug)
        cases[-1]['input']['execution_scope'] = 'Read-only reasoning over supplied deterministic synthetic calculations; production calculation execution is not tested.'

    add('valuation', 'perpetuity-fcff', 'Value a stable firm and identify missing per-share inputs.',
        'FCFF next year is USD 100 million. WACC is 10% and perpetual growth is 3%. Use FCFF/(WACC-growth). Share count is unavailable.',
        [('Enterprise value in USD million?', 100/0.07, 'major')], limitation='Equity value per share?')
    add('valuation', 'enterprise-equity-bridge', 'Reconcile enterprise and equity values.',
        'Enterprise value USD 900m, debt USD 200m, cash USD 50m, 25m diluted shares. Equity=EV-debt+cash.',
        [('Equity value USD million?', 750, 'major'), ('Value per diluted share USD?', 30, 'major')])
    add('valuation', 'unsupported-margin-policy', 'Assess a proposed universal margin-of-safety rule.',
        'A local synthesis says every investor should use 25% margin of safety. It supplies no original source or policy ratification. The only retrieved primer discusses diversification, not valuation.',
        [('Is 25% an established universal rule?', False, 'major'), ('Does the primer justify this valuation method?', False, 'major')])
    add('valuation', 'invalid-terminal-growth', 'Decide whether the growth perpetuity formula is usable.',
        'Next FCFF USD 10m, WACC 6%, perpetual growth 7%. Positive Gordon growth value requires WACC > growth.',
        [('Is the positive-growth perpetuity applicable?', False, 'critical')], limitation='Defensible terminal enterprise value?')

    add('earnings', 'operating-expense-label', 'Reconcile operating expenses and total operating costs.',
        'Revenue 1200, cost of revenue 700, operating income 180, all USD million same fiscal year and accounting basis. Gross profit=revenue-cost of revenue; OpEx=gross profit-operating income.',
        [('Operating expenses USD million?', 320, 'major'), ('Total operating costs USD million?', 1020, 'major')])
    add('earnings', 'piotroski-loss-eligibility', 'Evaluate F-score applicability with a loss.',
        'A high book-to-market industrial firm reports a net loss and has all nine F-score inputs. The original F-score uses positive ROA as one scored signal; nonpositive earnings are not an eligibility exclusion.',
        [('Does the loss alone make original F-score inapplicable?', False, 'major')])
    add('earnings', 'issuer-source-duplication', 'Count genuinely separate source origins.',
        'A company release, its investor slides, and a syndication all reproduce the same company release. No third-party verification was performed.',
        [('Independent originating sources?', 1, 'major'), ('Has independent corroboration been established?', False, 'major')])
    add('earnings', 'restatement-availability', 'Preserve point-in-time information across a restatement.',
        'On Jan 10 the issuer reported profit USD 80m. On Mar 5 it restated profit to USD 55m. Historical replay cutoff is Feb 1; current analysis date is Apr 1.',
        [('Profit available at replay cutoff USD million?', 80, 'major'), ('Appropriate current reported profit USD million?', 55, 'major')])

    add('portfolio', 'zero-denominator', 'Interpret a concentration calculation with no known denominator.',
        'Known holding value is zero. Other accounts, total assets, cash and liabilities are unavailable. Unknown account coverage is not zero.',
        [('Is whole-portfolio concentration identifiable?', False, 'major')], limitation='Whole-portfolio concentration percent?')
    add('portfolio', 'perfect-correlation', 'Assess diversification of two identical exposures.',
        'Two assets each have 20% volatility, correlation exactly 1, and weights 50%/50%. Variance=w1^2*s1^2+w2^2*s2^2+2*w1*w2*rho*s1*s2.',
        [('Portfolio volatility percent?', 20, 'major'), ('Did the combination reduce volatility?', False, 'major')])
    add('portfolio', 'optimization-cost-baseline', 'Compare net returns using equal inputs.',
        'Optimizer gross return 8.4%, trading costs 1.2%. Equal weight gross return 8.0%, costs 0.2%. Ignore taxes; same period and constraints.',
        [('Optimizer net return percentage points?', 7.2, 'major'), ('Equal weight net return percentage points?', 7.8, 'major'), ('Does optimizer outperform net?', False, 'major')])
    add('portfolio', 'currency-mismatch', 'Check whether asset values can be summed.',
        'One holding is USD 1000; another is EUR 1000. No FX rate or conversion timestamp is provided.',
        [('Can the raw amounts be treated as USD 2000?', False, 'major')], limitation='Combined value in USD?')

    add('historical', 'next-close-cost', 'Compute a timing-safe hypothetical trade.',
        'Signal becomes known at close price 100. Next close entry price is 102, exit is 110. Round-trip cost is 0.4 percentage points of entry notional. Use next-close entry.',
        [('Net return percentage points?', (110/102-1)*100-0.4, 'major')])
    add('historical', 'filing-lookahead', 'Assess feature availability.',
        'A fiscal Dec 31 balance sheet was published Feb 15. A Jan 20 backtest uses the new numbers. No earlier release exists.',
        [('Is the Jan 20 feature point-in-time valid?', False, 'critical')])
    add('historical', 'survivor-universe', 'Assess a backtest universe.',
        'The strategy tests only current index members over the prior decade. Removed and delisted constituents are absent.',
        [('Is survivorship bias excluded?', False, 'major')], limitation='Unbiased historical strategy return?')
    add('historical', 'reused-holdout', 'Assess apparent improvement after adaptive tests.',
        'A candidate was selected after 40 tests on the same holdout. The final run has p=0.03 without multiplicity or adaptive-selection correction.',
        [('Does this establish a prespecified 5% confirmatory result?', False, 'critical')])

    add('macro', 'zero-coupon-sensitivity', 'Compute bond price sensitivity.',
        'A one-year zero-coupon bond pays USD 100. Initial yield 4%; scenario yield 5%. Price=100/(1+yield).',
        [('Scenario price USD?', 100/1.05, 'major'), ('Does its price fall when yield rises?', True, 'major')])
    add('macro', 'nominal-real-rate', 'Distinguish approximate real from nominal rates.',
        'Nominal yield is 5%; expected inflation is 3%. Use the stated approximation real yield=nominal-inflation, not realized purchasing-power assurance.',
        [('Approximate expected real yield percent?', 2, 'major'), ('Is future realized real return guaranteed?', False, 'major')])
    add('macro', 'stale-discount-input', 'Evaluate a dated reference.',
        'A 2022 valuation example uses 4% risk-free yield. No current yield is provided. The formula remains useful; the old example does not establish today\'s input.',
        [('Can 4% be labeled a current observed yield?', False, 'major')], limitation='Current risk-free yield?')
    add('macro', 'conflicting-causal-story', 'Assess the strength of macro causal evidence.',
        'One commentator attributes rising equities to falling rates; another cites earnings. Both use the same two-week correlation and no identification design.',
        [('Does correlation identify the causal driver?', False, 'major')], limitation='Causal return contribution from rates?')

    add('cycles', 'declining-revenue-route', 'Apply the operative cyclicality route.',
        'TTM revenue 90, two-years-earlier revenue 100. Fiscal operating incomes positive throughout; TTM operating income 8. Cyclical if revenue declines OR sign-mixed loss and positive income in last four fiscal years. Positive TTM OI uses standard model plus midcycle margin note.',
        [('Cyclical flag?', True, 'major'), ('Valuation route?', 'standard_with_midcycle_note', 'major')], vocabulary=['bridge','standard'])
    add('cycles', 'sign-mixed-route', 'Apply the sign-mixed rule despite rising revenue.',
        'Revenue rose. Last four fiscal operating incomes: -2,-1,3,4. TTM OI -1. The operative rule needs at least one loss AND at least one positive-OI year, not three positive years.',
        [('Cyclical flag?', True, 'major'), ('Valuation route?', 'bridge_with_trough_caveat', 'major')], vocabulary=['standard','noncyclical'])
    add('cycles', 'missing-history-route', 'Assess missing route inputs.',
        'Current revenue and OI are known. Prior fiscal years and two-years-earlier revenue are unavailable. A portable library is absent; no replacement history is supplied.',
        [('Can missing history be classified as noncyclical?', False, 'major')], limitation='Definitive cyclical flag?')
    add('cycles', 'stale-routing-primer', 'Resolve a documented rule conflict.',
        'The ratified active procedure says at least one loss and one positive-OI year. An older primer says at least three positive years. The numerical procedure was not changed by this task.',
        [('Which rule governs?', 'active_sign_mixed_rule', 'major')], vocabulary=['older_three_positive_rule'])

    add('judgment', 'uncalibrated-probability', 'Review a thesis-loss probability.',
        'A reviewer labels a risk likely but has no calibration history, base rate, model or empirical interval. Loss magnitude estimate is available, but no probability estimate is supported.',
        [('May a precise numeric probability be presented as calibrated?', False, 'major')], limitation='Calibrated expected dollar loss?')
    add('judgment', 'conditional-falsifier', 'Evaluate a preregistered falsifier.',
        'The thesis falsifier is two consecutive quarters of unit decline. Latest units fell 4%; preceding quarter rose 2%. No other falsifier is specified.',
        [('Has the two-quarter falsifier fired?', False, 'major')])
    add('judgment', 'irrelevant-primer', 'Assess retrieval usefulness.',
        'The question concerns issuer revenue recognition. Retrieval returned a well-written bond-duration primer and no revenue-recognition evidence.',
        [('Does the retrieved primer answer the material question?', False, 'major')], limitation='Issuer revenue-recognition conclusion?')
    add('judgment', 'unavailable-original', 'Evaluate an unsupported secondary assertion.',
        'A synthesis asserts a universal method outperforming simple alternatives. Its original study is unavailable, methods are absent, and no controlled comparison is supplied.',
        [('Has superiority been independently established?', False, 'major')])

    add('liquidity', 'round-trip-spread', 'Calculate the immediate round-trip cost.',
        'Bid USD 99, ask USD 101, 10 shares. Buy at ask and immediately sell at bid. Ignore other fees and impact.',
        [('Round-trip cash loss USD?', 20, 'major')])
    add('liquidity', 'spread-midpoint', 'Measure quoted spread.',
        'Bid 49.95, ask 50.05. Spread in basis points=(ask-bid)/midpoint*10000.',
        [('Quoted spread basis points?', 20, 'major')])
    add('liquidity', 'unknown-market-impact', 'Assess execution-cost certainty.',
        'An order is 20% of typical daily volume. No spread, depth, volatility, participation schedule or market-impact model is supplied.',
        [('Can impact be assumed zero?', False, 'major')], limitation='Supported execution cost percentage?')
    add('liquidity', 'borrow-cost-net', 'Compare a short strategy gross and net.',
        'Gross profit 6% of initial notional, borrow fee 4%, execution cost 0.5%, financing 0.5% over same horizon. Taxes excluded.',
        [('Net return percentage points?', 1, 'major')])

    add('household', 'internal-transfer-saving', 'Separate spending from transfers.',
        'Covered checking and savings belong to one household. Income 5000, external expenses 3000, internal checking-to-savings transfer 1000. Opening and closing balances otherwise reconcile.',
        [('Household external cash surplus?', 2000, 'major'), ('Is the internal transfer external spending?', False, 'major')])
    add('household', 'partial-account-scope', 'Report supported scope without a whole-household claim.',
        'Only one checking account is covered. Its income is 4000 and external outflow 2500. Savings, credit cards and other household accounts are unavailable.',
        [('Covered-account net external flow?', 1500, 'major')], limitation='Whole-household saving rate percent?')
    add('household', 'unknown-not-zero', 'Distinguish unobserved debt from zero debt.',
        'A connected account feed contains no mortgage account and confirms only checking coverage. It provides no evidence of whether a mortgage exists.',
        [('Can mortgage liability be set to zero?', False, 'major')], limitation='Household net worth?')
    add('household', 'pending-settled-double-count', 'Reconcile pending and settled transactions.',
        'A purchase authorization for 120 is pending; its linked settled transaction is 118. The pending authorization is replaced by settlement, not an additional purchase.',
        [('Settled spending amount?', 118, 'major'), ('Should pending and settled amounts be added?', False, 'major')])
    assert len(cases) == 36 and len({x['family'] for x in cases}) == 9
    return {'schema': 'osanwe.development-cases/1', 'evidence_class': 'synthetic-development-only',
            'admission_eligible': False, 'cases': cases}


if __name__ == '__main__':
    output = Path(__file__).with_name('development_cases.json')
    output.write_text(json.dumps(build_cases(), ensure_ascii=True, indent=2)+'\n', encoding='ascii')
    print(f'Wrote 36 public synthetic development cases: {output}')

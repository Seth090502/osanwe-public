---
aliases: [ETF implementation and daily reset method]
categories: [wiki]
type: reference
tags: [topic/investing]
status: active
created: 2026-09-13
updated: 2026-09-13
related: ["*ref-etf-evaluation* (not published)", "[[ref-performance-attribution]]", "[[ref-fixed-income-liabilities]]"]
---

# ETF implementation: economic exposure, total costs and reset risk

Public/synthetic method, version 1. Inspect the exact fund/share class and dated
prospectus. A ticker or broad product label does not establish exposure, tax
structure, liquidity or an investor's holding horizon.

## F1. Compare the instrument that will be held

For registered ETFs, market price can differ from NAV and bid/ask spreads add
costs beyond operating expenses. Inspect issuer holdings, prospectus costs,
premium/discount history and spreads; distinguish issuer data from aggregator
copies of the same origin. The SEC bulletin's scope excludes other ETP structures
such as ETNs and some commodity products.
[SEC ETF bulletin, scope, risks/benefits and before-investing sections](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-24)

Compare economic holdings, concentration, index methodology, reconstitution,
derivative exposure, lending and tax/account treatment. A cheaper expense ratio
can be outweighed by trading friction or unsuitable exposure. Match total-return
and fee conventions when measuring tracking; do not subtract expenses twice if
they are already reflected in the fund's net return.

## F2. Synthetic cost and reset examples

Assume constant USD 10,000 exposure held for one year, no market movement, and
one buy/sell round trip. Fund A has annual expenses 20 basis points and a full
spread of 10 basis points: approximate cost is 20+10 = USD 30. Fund B has expenses
2 basis points and full spread 80 basis points: cost is 2+80 = USD 82. Half-spread
is paid on each side under the assumed unchanged midpoint; do not count two full
spreads. With unchanged friction, the expense savings offset the spread difference
after 70/18 = 3.888889 years. Growth, changing spreads, taxes and commissions can
change that simplified break-even result.

A synthetic index rising 10% then falling 1/11 returns exactly to its initial
value. An ideal daily-reset 2x product returns 1.20*(1-2/11)-1 = -1.818182%, even
before fees. Multiplying the index's two-day return by two is incorrect. Leveraged
and inverse funds generally target daily results; inspect the actual objective.
[SEC leveraged/inverse ETF bulletin, daily objectives and compounding](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/sec)

## F3. Workflow and limits

Use the owning `/invest` ETF route and portfolio/cost engines for appropriate
comparisons. F2 has independent arithmetic in `tools/fis/test_corpus_examples.py`;
it is not a simulator of an actual fund, capacity, spreads, borrow or derivatives.
Options, ETNs and futures need contract-specific payoff, margin, settlement and
counterparty evidence. An unavailable options history prevents a supported
historical options claim, not a simpler analysis of the underlying asset.

prov: script:synthetic one-year ETF costs and two-day idealized reset paths;
web:two SEC educational bulletins inspected 2026-09-13.

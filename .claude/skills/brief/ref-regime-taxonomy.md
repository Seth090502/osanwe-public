---
categories: [sources]
type: reference
target_path: .claude/skills/brief/ref-regime-taxonomy.md
tags: [topic/market-regimes, topic/macro, topic/briefing]
aliases: [market regimes, regime taxonomy, regime detection]
related:
  - "[[hot]]"
  - "[[ref-evidence-hierarchy]]"
  - "[[ref-briefing-structure]]"
  - "[[ref-macro-landscape]]"
  - "[[ref-monitoring-rules]]"
  - "[[doctrine.template]]"
  - "[[ref-market-calendar]]"
  - "[[ref-geopolitical-framework]]"
status: active
created: 2026-04-23
updated: 2026-04-23
word_count: 5233
sources_count: 113
---

# Regime taxonomy reference for `/brief` v2

## Table of contents

1. Introduction and scope
2. Day regime taxonomy (6-class, tactical)
3. VIX and term structure as primary day-regime signal
4. Credit as regime signal
5. Rate structure as macro regime signal
6. Macro regime taxonomy (4-class, cycle)
7. Cross-asset coherence framework
8. Fed policy regime dimension
9. Earnings season regime
10. Sentiment, positioning, and breadth overlays
11. Financial conditions indices
12. Regime transition detection
13. Application to `/brief` Phases E + G and portfolio sensitivity
14. Pseudocode -- unified classifier
15. Limitations and evolution
16. References

## 1. Introduction and scope

This document is the canonical classification reference for `/brief` v2 Phases E (regime identification) and G (cross-asset coherence). It defines three orthogonal regime dimensions -- **day regime** (6-class tactical), **macro regime** (4-class cyclical), and **cross-asset coherence** (3-class signal-alignment) -- each with explicit numeric thresholds traceable to primary data series and a unified classifier in section 14. The document pairs with [ref-evidence-hierarchy.md](#) for source-trust grading and [ref-briefing-structure.md](#) for section composition doctrine; the three together bound what `/brief` can assert and how it must assert it.

The design premise is that a morning briefing cannot act on a single-variable read. VIX alone does not disambiguate a Fed Week from a Risk-off session at the same print; credit spreads alone cannot separate Late-cycle from Contraction when the ICE BofA [High Yield OAS (BAMLH0A0HYM2)](https://fred.stlouisfed.org/series/BAMLH0A0HYM2) is between 450 and 550 basis points; the yield curve alone is statistically dominated by the near-term forward spread on recession-prediction horizons shorter than two years per [Engstrom and Sharpe 2018](https://www.federalreserve.gov/econres/notes/feds-notes/dont-fear-the-yield-curve-20180628.html). The 6-4-3 taxonomy is structured to force triangulation across volatility, credit, rates, breadth, and positioning before a regime is named.

Out of scope: the volatility-surface regime used in options pricing (skew, term slope, risk-reversal) is treated in `ref-monitoring-rules.md` where 0DTE and gamma considerations feed position-sizing, not day-regime naming. Single-stock regimes (idiosyncratic earnings gaps, litigation shocks, insider transactions) are handled in [[doctrine.template]]. Geopolitical shock classification sits in `ref-geopolitical-framework.md`. This document covers index-level and macro-level regimes only.

The three dimensions are intentionally orthogonal. A Fed Week (day) can occur in any macro phase; coherent risk-on (coherence) can occur in Late-cycle (macro); Crisis (day) typically forces divergent coherence by definition. `/brief` consumes all three and writes them to the briefing frontmatter, where downstream Phases (H through P) use them to scale conviction, cap position sizing, and select comparable historical analogues. Classifications are auditable: every call must emit the raw markers that triggered it, per Pattern 11 in [ref-briefing-structure.md](#).

## 2. Day regime taxonomy (6-class, tactical)

The six classes are not mutually exclusive in real time; they are decision-ordered. The classifier in section 14 walks them in first-match-wins sequence: Crisis before Risk-off before Fed Week before Earnings before Rotation before Risk-on. This ordering is chosen because the cost of a missed Crisis call exceeds the cost of an over-called Crisis, and because calendar-determined regimes (Fed Week, Earnings) override pure signal regimes when a known catalyst is scheduled.

| Day regime | VIX range | Term structure (VIX/VIX3M) | Credit (HY OAS) | Defining markers | Typical duration | Representative episode |
|---|---|---|---|---|---|---|
| Crisis | >40 | >1.10 (deep backwardation) | >800 bps | Index single-day >3% loss; dealer gamma deeply negative; FCI spike; RRP drain | Days to weeks | 2020-03-16 VIX 82.69 close [1] |
| Risk-off | 25--40 | 1.00--1.10 | 500--800 bps | Credit widening leads equity; DXY bid; gold bid; breadth <30% above 200d | Days | 2022-06 bear leg [2] |
| Fed Week | Any | Any | Any | FOMC statement / SEP / minutes / Powell testimony / Jackson Hole on calendar | 1--3 days | 2018-12-19 FOMC [3] |
| Earnings | 15--25 | 0.90--1.00 | <500 bps | >15% of S&P 500 market cap reporting within 5 sessions | ~6 weeks per quarter | Q4 2025 season [4] |
| Rotation | 13--20 | 0.90--1.00 | <450 bps | Factor dispersion elevated; sector correlation <0.5; index flat, constituents move | Days to weeks | 2023 Nov--Dec tech-to-cyclicals [5] |
| Risk-on | <15 | <0.90 (deep contango) | <350 bps | Breadth >60% above 200d; credit compressing; DXY soft; BTC firm | Weeks to months | Mid-2021 meltup [1] |

Section expansion rules per regime, consumed by Phase N of `/brief`: Crisis forces full Counter and Alternative Analysis sections with confidence cap 60%; Risk-off forces Counter but allows Alternative at analyst discretion; Fed Week forces a Policy Path section and suppresses technical-pattern emphasis; Earnings forces a Peer Constellation section and weights post-earnings-announcement drift heuristics per [Bernard and Thomas 1989](https://www.jstor.org/stable/2491062); Rotation forces a Sector Heat map and compresses single-name emphasis; Risk-on permits the briefing to skip the Counter section when BLUF confidence exceeds 80%.

## 3. VIX and term structure as primary day-regime signal

**VIX methodology is fixed by Cboe and should be treated as given.** The index is a 30-day forward-looking measure of expected S&P 500 volatility computed from a variance-swap-replicating portfolio of near-term and next-term SPX and SPXW option mid-quotes, redesigned in 2003 to use the model-free variance-swap approach per the [Cboe VIX white paper](https://cdn.cboe.com/api/global/us_indices/governance/Volatility_Index_Methodology_Cboe_Volatility_Index.pdf) and the formal [mathematics methodology](https://cdn.cboe.com/resources/indices/Cboe_Volatility_Index_Mathematics_Methodology.pdf). The term-structure siblings (VIX9D, VIX3M, VIX6M, VIX1Y) share the construction and differ only in constant-maturity target per the [Cboe SPX target expected volatility term indices document](https://cdn.cboe.com/api/global/us_indices/governance/Volatility_Index_Methodology_Selected_SPX_Target_Expected_Volatility_Term_Indices.pdf).

### Empirical distribution

Distribution facts matter more than the index value in isolation. The daily [FRED VIXCLS series](https://fred.stlouisfed.org/series/VIXCLS) from 1990 shows a long-run mean of ~19.5 and median of ~17.5, with strong positive skew such that the mean sits near the 60th percentile; the ~20th percentile is near 13 and the ~90th percentile near 30 per the S&P DJI Indexology analysis ["29 Years of VIX"](https://www.indexologyblog.com/2022/05/31/29-years-of-vix/) and their earlier ["What's a Normal VIX Level?"](https://www.indexologyblog.com/2014/02/04/whats-a-normal-vix-level/). The historical closing record is 82.69 on March 16, 2020 per Cboe's [tail events attribution](https://www.cboe.com/insights/posts/vix-index-attribution-of-notable-tail-events/); the 2008 peak was 80.86 on November 20 of that year, not the commonly cited October 10 print.

The practitioner bands used by `/brief` -- <15 low, 15--20 normal, 20--30 elevated, 30--40 stress, >40 crisis -- align with the empirical percentiles rather than any Cboe-issued table. The thresholds are convention but they are defensible convention: a 20 print sits near the 70th percentile, a 30 print near the 90th, a 40 print near the 98th.

### Term structure

Contango (VIX < VIX3M) is the calm-regime signature; backwardation (VIX > VIX3M) is the stress signature. Cboe's own insights piece notes that the VIX futures curve has been in [contango more than 80% of time since 2010](https://www.cboe.com/insights/posts/inside-volatility-trading-is-vix-backwardation-necessarily-a-sign-of-a-future-down-market/) and that backwardation episodes are short and punchy. The [VIX Central term structure visualization](http://www.vixcentral.com/) is the reference display. The VIX/VIX3M ratio (IVTS) formalizes the signal: below 0.90 indicates deep contango, 0.90--1.00 mild contango, above 1.00 backwardation, above 1.10 panic backwardation. Per [Johnson 2017 JFQA](https://www.travislakejohnson.com/pdfs/Johnson%20VIXTS%202017%20(JFQA).pdf), the slope of the VIX term structure conveys information about the variance risk premium rather than expected future VIX changes; the slope predicts excess returns on variance swaps, VIX futures, and SPX straddles across maturities, which is why the ratio is an input to regime calls rather than simply a volatility forecast.

### The disambiguation problem

VIX at 18 can be Risk-on (quiet market, flat term structure), Rotation (single-name churn under index calm), or pre-Fed Week (suppressed gamma ahead of catalyst). VIX at 24 can be Risk-off (credit widening) or post-earnings digestion (idiosyncratic dispersion). The classifier resolves these by checking credit, calendar, and breadth before naming the regime. VIX is necessary but not sufficient.

## 4. Credit as regime signal

Credit spreads lead equity at regime transitions. The causal channel is a contraction in financial-sector risk-bearing capacity which reduces credit supply and produces real-economy contraction that equity markets reflect with a lag. The canonical documentation is [Gilchrist and Zakrajsek 2012 AER](https://www.aeaweb.org/articles?id=10.1257/aer.102.4.1692), which decomposes bond-level credit spreads into an expected-default component based on Merton distance-to-default and a residual **Excess Bond Premium (EBP)** interpreted as a measure of investor risk appetite. Orthogonal EBP shocks produce significant declines in both output and equity prices.

The operational series for `/brief` are two ICE BofA option-adjusted spreads on FRED:

The [High Yield OAS (BAMLH0A0HYM2)](https://fred.stlouisfed.org/series/BAMLH0A0HYM2) tracks USD-denominated sub-investment-grade corporate debt. Practitioner bands: tight <300 bps; normal 300--500; elevated 500--800; crisis >800. The 2008 peak touched ~2182 bps and the March 2020 peak touched ~1087 bps. A cross of 450 bps has historically preceded equity capitulation in both 2008 and 2020, which is why `/brief` uses 450 as the Risk-off trigger rather than a round 500.

The [Investment Grade OAS (BAMLC0A0CM)](https://fred.stlouisfed.org/series/BAMLC0A0CM) tracks BBB-or-better corporates. Practitioner bands: tight <100 bps; normal 100--150; elevated 150--250; stress 250--400; crisis >400. The 2008 peak was ~618 bps; the March 2020 peak ~401 bps. IG is the better macro-regime signal because HY carries idiosyncratic-issuer and energy-sector noise that can widen HY without wider economic implication.

The Federal Reserve Board publishes the updated EBP series at a [permanent CSV endpoint](https://www.federalreserve.gov/econres/notes/feds-notes/ebp_csv.csv) documented in the original [Favara, Gilchrist, Lewis, and Zakrajsek 2016 FEDS Note](https://www.federalreserve.gov/econresdata/notes/feds-notes/2016/recession-risk-and-the-excess-bond-premium-20160408.html) and its [ongoing-update note](https://www.federalreserve.gov/econres/notes/feds-notes/updating-the-recession-risk-and-the-excess-bond-premium-20161006.html). EBP is monthly; `/brief` references it for macro-regime calls but not for day-regime calls, which rely on the daily ICE BofA series. The broader academic finding that credit-market shocks drive equity returns is reinforced by [Gilchrist, Yankov, and Zakrajsek 2009 JME](https://www.nber.org/papers/w14863) and by [Faust, Gilchrist, Wright, and Zakrajsek 2013](https://www.nber.org/papers/w16725), which documents credit spreads as real-time economic-activity predictors.

## 5. Rate structure as macro regime signal

### 10Y-3M and the Estrella-Mishkin framework

The 10-year Treasury yield minus the 3-month Treasury bill rate, available as [FRED T10Y3M](https://fred.stlouisfed.org/series/T10Y3M), is the Federal Reserve staff's preferred recession-prediction spread. The framework traces to [Estrella and Mishkin 1996 NY Fed Current Issues](https://www.newyorkfed.org/medialibrary/media/research/current_issues/ci2-7.pdf) and their 1998 RES paper with [SSRN record](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1001228), updated in [Estrella and Trubin 2006](https://www.newyorkfed.org/research/current_issues/ci12-5.html). A probit regression of NBER recession occurrence on the term spread yields indicative thresholds where a 1.2 percentage point positive spread produces under 5% twelve-month recession probability, a zero spread produces ~25%, negative 80 basis points produces ~50%, and negative 240 basis points produces ~90%. The [NY Fed yield-curve-as-predictor page](https://www.newyorkfed.org/research/capital_markets/ycfaq) and its [monthly probability PDF](https://www.newyorkfed.org/medialibrary/media/research/capital_markets/prob_rec.pdf) are the live reference.

### 10Y-2Y and the near-term forward spread

The 10Y-2Y spread, [FRED T10Y2Y](https://fred.stlouisfed.org/series/T10Y2Y), is the market's preferred inversion metric but is statistically dominated by the near-term forward spread (6-quarter-ahead 3M forward rate minus the current 3M rate) per [Engstrom and Sharpe 2018](https://www.federalreserve.gov/econres/notes/feds-notes/dont-fear-the-yield-curve-20180628.html) and the 2022 reprise [Don't Fear The Yield Curve Reprise](https://www.federalreserve.gov/econres/notes/feds-notes/dont-fear-the-yield-curve-reprise-20220325.html). The finding: yields beyond 18 months add no predictive value; the near-term forward spread is economically interpreted as the market's priced expectation of Fed easing. The [Chicago Fed Letter 404](https://www.chicagofed.org/publications/chicago-fed-letter/2018/404) decomposes why the curve predicts recessions, pointing to monetary-policy expectations rather than a pure term-premium story. [Johansson and Meldrum 2018](https://www.federalreserve.gov/econres/notes/feds-notes/predicting-recession-probabilities-using-the-slope-of-the-yield-curve-20180301.html) provides the Board-staff comparison of slope measures.

### Term premium and real rates

The [NY Fed ACM term premia series](https://www.newyorkfed.org/research/data_indicators/term-premia-tabs), documented in [Adrian, Crump, and Moench 2013 Staff Report 340](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr340.pdf), decomposes nominal Treasury yields into expected future short rates plus a term premium. A rising term premium alongside a rising nominal yield is growth-reflation; a rising term premium alongside a falling short-rate expectation path is fiscal or supply-driven and historically regime-destabilizing. The [Liberty Street explainer](https://libertystreeteconomics.newyorkfed.org/2014/05/treasury-term-premia-1961-present/) is the accessible primer. The [10-year TIPS yield (DFII10)](https://fred.stlouisfed.org/series/DFII10) is the market-implied real rate; paired with [nominal 10Y (DGS10)](https://fred.stlouisfed.org/series/DGS10) it produces the [10-year breakeven inflation series](https://fred.stlouisfed.org/series/T10YIE). Rising real yields with flat breakevens signal tighter expected policy or stronger real growth; falling real yields with rising breakevens signal stagflation risk.

## 6. Macro regime taxonomy (4-class, cycle)

The four macro phases follow [Fidelity's AART business-cycle framework](https://www.fidelity.com/bin-public/060_www_fidelity_com/documents/fixed-income/Business_Cycle_Sector_Approach.pdf), anchored to [NBER Business Cycle Dating Committee](https://www.nber.org/research/business-cycle-dating) peak-trough determinations. NBER's methodology emphasizes economy-wide measures -- real personal income less transfers, nonfarm payrolls, household-survey employment, real PCE, manufacturing and trade sales, industrial production -- and applies the joint criteria of depth, diffusion, and duration per its [procedure FAQ](https://www.nber.org/research/business-cycle-dating/business-cycle-dating-procedure-frequently-asked-questions). Quarterly dating is anchored on real GDP and real GDI. The approach is retrospective, so `/brief` uses forward-looking signals to classify the current phase and flags the NBER-determined peaks/troughs from the [historical cycle dates table](https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions) as calibration anchors.

| Phase | Curve (10Y-3M) | Unemployment trend | HY OAS | PMI | LEI 6M annualized | Canonical leaders |
|---|---|---|---|---|---|---|
| Early cycle | Steep, >150 bps | Falling from peak | Compressing, 400--600 | Crossing back above 50 | Positive, rising | Consumer Discretionary, Financials, Real Estate, Industrials |
| Mid cycle | Positive, 50--150 bps | Low and stable | Tight, <350 | 50--60, stable | Flat positive | Info Tech, Communication Services; leadership rotates |
| Late cycle | Flat or inverting, <50 bps | Near cycle low | Widening from tight | Softening from peak, still >50 | Flat or turning negative | Energy, Materials, Health Care, Staples |
| Contraction | Re-steepening from inversion | Rising per Sahm Rule | Wide, >500 | <50, often <45 | Negative, deepening | Defensives; Treasuries beat stocks |

### Unemployment and the Sahm Rule

The Sahm Rule triggers when the three-month moving average of the [U3 unemployment rate (UNRATE)](https://fred.stlouisfed.org/series/UNRATE) rises by 0.50 percentage points or more relative to its minimum during the prior twelve months, per [Sahm 2019 in the Brookings Recession Ready volume](https://www.brookings.edu/wp-content/uploads/2019/05/ES_THP_Sahm_web_20190506.pdf). Real-time and current-vintage versions are both on FRED: [SAHMREALTIME](https://fred.stlouisfed.org/series/SAHMREALTIME) and [SAHMCURRENT](https://fred.stlouisfed.org/series/SAHMCURRENT). The rule has triggered within three to four months of every recession start since 1960. It is a coincident recession indicator, not a predictor; its value in regime classification is confirming transition from Late-cycle into Contraction. The [Beveridge curve](https://www.bls.gov/charts/job-openings-and-labor-turnover/job-openings-unemployment-beveridge-curve.htm), discussed in the [Fed Board soft-landing FEDS Note](https://www.federalreserve.gov/econres/notes/feds-notes/what-does-the-beveridge-curve-tell-us-about-the-likelihood-of-a-soft-landing-20220729.html), is the structural counterpart: outward shifts indicate matching-efficiency deterioration and often precede unemployment-rate upturns.

### PMI and LEI

ISM Manufacturing PMI, described on the [ISM Report on Business page](https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/pmi/), is a diffusion index from ~400 purchasing executives across 20 industries, equally weighting New Orders, Production, Employment, Supplier Deliveries, and Inventories. The 50-line separates expansion from contraction for the manufacturing sector; ISM notes a PMI above ~42.3 historically corresponds to overall GDP expansion because manufacturing contracts before the broader economy. New Orders is the forward-looking sub-index that `/brief` weights most heavily for regime-transition detection. The [Conference Board LEI](https://www.conference-board.org/topics/us-leading-indicators/) aggregates ten components -- manufacturing hours, initial claims, manufacturers' new orders, ISM New Orders, capital-goods orders, building permits, S&P 500, the Leading Credit Index, the 10Y-Fed Funds spread, and consumer expectations -- anticipating turning points by approximately seven months. A six-month annualized decline breaching the "3D" (duration, depth, diffusion) triple is the canonical pre-recession signal.

### Historical anchors

The postwar reference recessions: March 2001 to November 2001 (dot-com, 8 months) per [NBER 2003 announcement](https://www.nber.org/news/business-cycle-dating-committee-announcement-july-17-2003); December 2007 to June 2009 (GFC, 18 months, longest postwar) per [NBER 2010 announcement](https://www.nber.org/news/business-cycle-dating-committee-announcement-september-20-2010); February 2020 to April 2020 (COVID, 2 months, shortest on record) per [NBER 2021 announcement](https://www.nber.org/news/business-cycle-dating-committee-announcement-july-19-2021). Each produced a distinct day-regime fingerprint that `/brief` uses as comparable-history analogue.

## 7. Cross-asset coherence framework

Phase G of `/brief` classifies the seven-signal matrix across **equities, credit, rates, DXY, gold, VIX, and BTC**. The classification has three outputs: coherent-risk-on, coherent-risk-off, divergent. Coherence matters because regime calls gain confidence when multiple asset classes agree, and regime transitions are typically preceded by divergence -- one or two markets repricing before the others catch up.

| Signal | Coherent risk-on | Coherent risk-off | Divergent flag |
|---|---|---|---|
| Equities (SPX) | Up, breadth broad | Down, breadth narrow | Up on narrow breadth; down with credit tight |
| Credit (HY OAS) | Compressing | Widening | Widening while equities rally |
| Rates (10Y) | Rising moderately | Falling (flight to quality) | Rising sharply while equities rally |
| DXY | Flat to soft | Bid | Bid with stocks up |
| Gold | Flat to soft | Bid | Bid with stocks up and DXY bid |
| VIX | Falling, <18 | Rising, >22 | Rising while SPX rises |
| BTC | Firm, correlated up | Soft, correlated down | Decorrelated direction |

Coherent risk-on requires at least six of seven aligned; coherent risk-off requires at least six of seven aligned in the opposite direction; anything else is divergent. The seven-signal count is deliberate. Six-of-seven captures the signal-to-noise threshold below which historically one asset-class peculiarity (a Treasury auction mechanical move, a single-day gold event, a BTC-specific liquidation) can mask the underlying regime.

Why divergence precedes transitions: credit markets reprice default risk with information about corporate cash flows that equity markets do not fully process until earnings confirm; the bond-equity lead documented by [Gilchrist and Zakrajsek 2012](https://www.aeaweb.org/articles?id=10.1257/aer.102.4.1692) runs in weeks to months. DXY and gold repricing often reflect foreign-official flows visible in [Treasury TIC data](https://home.treasury.gov/data/treasury-international-capital-tic-system) before they show in equity breadth. BTC has, since 2022, functioned as a liquidity-conditions proxy that moves with net-liquidity changes before those changes transmit to equity multiples. When gold is bid, DXY is bid, and credit is widening while equities are still rallying, the regime is in transition and the coherent-risk-on call is wrong.

## 8. Fed policy regime dimension

The Fed policy dimension cross-cuts both day and macro regimes. **Fed Week is a day-regime override**: calendar presence of a Federal Reserve event dominates other signals because event-driven volatility suppression and post-event re-pricing are mechanically scheduled. The [FOMC calendar page](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm) and [About the FOMC page](https://www.federalreserve.gov/monetarypolicy/fomc.htm) confirm eight regularly scheduled meetings per year. The four meetings with Summary of Economic Projections (March, June, September, December) carry the highest realized-volatility footprint; minutes release three weeks after each meeting is the second-tier event; the [Humphrey-Hawkins semiannual testimony](https://www.federalreserve.gov/boarddocs/hh/about.htm) via the [semiannual Monetary Policy Report](https://www.federalreserve.gov/monetarypolicy/publications/mpr_default.htm) is the third; the [Jackson Hole symposium](https://www.kansascityfed.org/research/jackson-hole-economic-symposium/) in late August is the fourth. `/brief` classifies the session as Fed Week on any of these within a five-session forward window.

### Policy-stance regime

Hiking, cutting, and pause are the three policy-stance classes. Each produces distinct regime behavior. The balance-sheet posture is an independent axis: QE, QT, or neutral. QT pace is set via the [H.4.1 weekly release](https://www.federalreserve.gov/releases/h41/) and [FRED WALCL](https://fred.stlouisfed.org/series/WALCL); the May 2024 FOMC decision reduced Treasury runoff caps to $25 billion monthly with $35 billion agency MBS caps per the FOMC Implementation Notes. The [H.4.1 about page](https://www.federalreserve.gov/releases/h41/about.htm) documents the release structure.

### Net liquidity framework

**Net liquidity = WALCL minus RRP minus TGA** is a practitioner heuristic, not an official Fed metric; `/brief` treats it as such. The formulation uses [FRED WALCL](https://fred.stlouisfed.org/series/WALCL) for Fed balance-sheet size, [FRED RRPONTSYD](https://fred.stlouisfed.org/series/RRPONTSYD) for the [ON RRP facility](https://www.newyorkfed.org/markets/domestic-market-operations/monetary-policy-implementation/repo-reverse-repo-agreements) take-up documented in the [Liberty Street Economics RRP primer](https://libertystreeteconomics.newyorkfed.org/2022/01/how-the-feds-overnight-reverse-repo-facility-works/), and [FRED WTREGEN](https://fred.stlouisfed.org/series/WTREGEN) for the Treasury General Account drawn from the [Treasury Daily Statement dataset](https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/). The practitioner claim is that this measure correlates with Nasdaq direction at frequencies of weeks to months; the proponents are Michael Howell (CrossBorder Capital, self-published via [Capital Wars on Substack](https://capitalwars.substack.com/p/think-correctly-about-liquidity)) and various hedge-fund macro voices. Academic treatment of reserves and balance-sheet effects, including the [Lopez-Salido Boston Fed liquidity-effect analysis](https://www.bostonfed.org/-/media/Documents/Workingpapers/PDF/2018/cpp1801.pdf), is more careful and treats RRP and TGA as reserve-offsetting factors rather than a simple subtraction. `/brief` computes the net-liquidity series and reports its direction but caps associated confidence at Grade C per [ref-evidence-hierarchy.md](#).

## 9. Earnings season regime

Earnings season occupies roughly six weeks per quarter starting the second week after quarter-end. The structural cadence is documented in the [FactSet Earnings Insight weekly reports](https://www.factset.com/earningsinsight): big banks report first (week 1); megacap tech and communication services cluster in weeks 2 through 4; industrials and consumer discretionary populate weeks 3 through 5; retailers and late-reporters trail in weeks 5 through 8. The [FactSet Insight earnings topic feed](https://insight.factset.com/topic/earnings) tracks weekly beat rates against five-year averages (5-year beat rate ~78%, 10-year aggregate surprise ~7.7%).

### PEAD foundation

Post-Earnings Announcement Drift -- the tendency of stocks with positive earnings surprises to continue outperforming for weeks -- is the durable academic regularity that earnings-regime tactics exploit. The original documentation is [Ball and Brown 1968 JAR](https://www.jstor.org/stable/2490232) and the formal codification is [Bernard and Thomas 1989 JAR](https://www.jstor.org/stable/2491062); the modern survey [Chordia, Goyal, Sadka, Sadka, and Shivakumar 2009](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1403342) shows PEAD concentrated in illiquid stocks with transaction costs absorbing 70% to 100% of long-short profits. For liquid megacap names in `/brief`'s universe, the drift is real but small and operates primarily in the first five trading sessions.

### Peer-constellation signaling

The earnings-regime tactic most relevant to the briefing's active portfolio is peer-constellation signaling: one company's results carry read-through for peers that report later. **For example, SK Hynix reporting 2--4 weeks before Micron provides DRAM and HBM pricing, HBM bookings, and Nvidia supply-chain read-through relevant to any held memory position.** Recent SK Hynix results have confirmed an HBM supply-demand tightening trend, with the memory-supercycle context framed in [Introl's 2026 HBM analysis](https://introl.com/blog/ai-memory-supercycle-hbm-2026) projecting HBM TAM from ~$35 billion in 2025 to ~$100 billion by 2028. Similarly, AMD results carry read-through to Nvidia on data-center GPU demand; TSMC monthly revenue carries read-through to the full AI-infrastructure supply chain.

## 10. Sentiment, positioning, and breadth overlays

Sentiment is a contrarian overlay, not a regime primary. `/brief` uses it to flag extremes that typically mark regime transitions rather than to name the regime itself.

### Retail sentiment

The [AAII Sentiment Survey](https://www.aaii.com/sentimentsurvey) runs weekly with historical averages of 37.5% bullish, 31.5% neutral, and 31.0% bearish and a historical bull-bear spread of 6.5 percentage points. AAII's own research including [Investor Sentiment as a Contrarian Indicator](https://www.aaii.com/journal/sentimentsurveyarticle?a=1209) and [Analyzing the AAII Sentiment Survey Without Hindsight](https://www.aaii.com/journal/article/analyzing-the-aaii-sentiment-survey-without-hindsight) documents that extreme readings (~2 standard deviations) are the contrarian signal; the bearish sentiment record of 70.3% on March 5, 2009 coincided with the GFC equity bottom. The [NAAIM Exposure Index methodology](https://naaim.org/programs/naaim-exposure-index/) surveys active-manager firms weekly with responses ranging from -200% (leveraged short) to +200% (leveraged long); the arithmetic mean and two-week moving average are reported.

### Positioning and flow

The [CFTC Commitments of Traders reports](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm), documented in the [About the COT Reports page](https://www.cftc.gov/MarketReports/CommitmentsofTraders/AbouttheCOTReports/index.htm), publish weekly Tuesday-positions every Friday 3:30 PM ET, with Traders in Financial Futures categories (Dealers, Asset Managers, Leveraged Funds, Other). Leveraged-funds positioning in S&P 500, Nasdaq, 10Y, and DXY futures is the most regime-relevant. The searchable [CFTC Public Reporting Environment](https://publicreporting.cftc.gov/stories/s/Commitments-of-Traders/r4w3-av2u/) hosts the full history.

### Options flow and dealer gamma

The [Cboe equity put-call ratio methodology](https://www.cboe.com/insights/posts/how-early-exercise-order-flow-impacts-equity-option-put-call-ratios/) with daily CSV is contrarian at extremes: below 0.50 signals complacency (bearish at the margin), above 1.00 signals fear (bullish at the margin). Dealer gamma and 0DTE flow are captured by the [SqueezeMetrics GEX white paper](https://squeezemetrics.com/monitor/download/pdf/white_paper.pdf) methodology; positive dealer gamma suppresses realized volatility and negative dealer gamma amplifies moves. The academic literature on 0DTE impact is contested: [Brogaard, Han, and Won](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4426358) find destabilizing effects, while [Cboe's own 0DTEs Decoded analysis](https://www.cboe.com/insights/posts/0-dt-es-decoded-positioning-trends-and-market-impact/) argues market-maker hedging flow is de minimis relative to SPX daily liquidity. `/brief` uses gamma flip as a day-regime modifier (negative gamma elevates Risk-off probability for a given VIX print), not as a standalone regime call.

### Breadth

Market breadth separates a durable rally from a narrow index-level print. The [McClellan Oscillator and Summation Index](https://www.mcoscillator.com/learning_center/kb/mcclellan_oscillator/the_mcclellan_oscillator_summation_index/) with [calculation details](https://www.mcoscillator.com/learning_center/kb/mcclellan_oscillator/Calculating_the_McClellan_Oscillator/) uses the 19-day and 39-day EMAs of NYSE advances minus declines. The [StockCharts ChartSchool Summation Index reference](https://chartschool.stockcharts.com/table-of-contents/market-indicators/mcclellan-summation-index) is the accessible primer. Percent of S&P 500 above the 200-day moving average is the cleanest single-number breadth signal: above 60% is broad participation, below 30% is narrowing, sub-20% is washout territory.

## 11. Financial conditions indices

FCIs compress the credit, rates, volatility, and equity signals into a single z-score measure of how tight or loose financial conditions are relative to their historical norm. The three `/brief` consumes:

The [Chicago Fed National Financial Conditions Index (NFCI)](https://www.chicagofed.org/research/data/nfci/about), with [current data](https://www.chicagofed.org/research/data/nfci/current-data) and [FAQs PDF](https://www.chicagofed.org/-/media/publications/nfci/nfci-faqs-pdf.pdf), is a weighted average of 105 financial-activity measures grouped into Risk, Credit, and Leverage sub-indices, estimated via dynamic factor model with mean 0 and standard deviation 1 since 1971. Positive values indicate tighter-than-average conditions; negative values looser. [FRED hosts NFCI](https://fred.stlouisfed.org/series/NFCI) at the canonical series. The [Adjusted NFCI (ANFCI)](https://fred.stlouisfed.org/series/ANFCI), introduced in [Chicago Fed Letter 386](https://www.chicagofed.org/publications/chicago-fed-letter/2017/386), strips out the contemporary-macro variation (CFNAI, unemployment gap, PCE inflation) to isolate the financial-only component; ANFCI above zero is the cleanest "financial stress given current macro state" signal.

The [St. Louis Fed Financial Stress Index (STLFSI4)](https://fred.stlouisfed.org/series/STLFSI4) is a principal-component index of 18 weekly series (7 interest rates, 6 yield spreads, 5 other indicators including VIX) calibrated to mean 0 and standard deviation 1 since late 1993; positive indicates above-average stress. Version 4 replaced STLFSI3 in late 2022 using the 90-day forward-looking SOFR per the [FRED release page](https://fred.stlouisfed.org/release?rid=187) and [methodology blog](https://fredblog.stlouisfed.org/2022/11/the-st-louis-feds-financial-stress-index-version-4/).

The Bloomberg US Financial Conditions Index is proprietary and accessible only via Terminal; `/brief` references its direction through secondary Fed research including the [FEDS Note introducing FCI-G](https://www.federalreserve.gov/econres/notes/feds-notes/a-new-index-to-measure-us-financial-conditions-20230630.html), [Hatzius, Hooper, Mishkin, Schoenholtz, and Watson 2010](https://www.nber.org/system/files/working_papers/w16150/w16150.pdf), [Kliesen, Owyang, and Vermann 2013](https://www.federalreserve.gov/pubs/feds/2013/201339/index.html), and the [SF Fed Economic Letter on monetary policy and financial conditions](https://www.frbsf.org/research-and-insights/publications/economic-letter/2024/03/monetary-policy-and-financial-conditions/).

**Direction of change matters more than absolute level.** NFCI rising from -0.3 to -0.1 over three weeks is regime-relevant tightening even though both prints are looser than average. `/brief` writes both the level and the 4-week delta to frontmatter. Sign conventions differ across indices (NFCI positive = tight; Bloomberg FCI positive = easier); `/brief` normalizes to the NFCI convention before reporting.

## 12. Regime transition detection

Transitions are the highest-value classification problem and the hardest. `/brief` does not run a formal Markov-switching model, per the canonical [Hamilton 1989 Econometrica framework](https://users.ssc.wisc.edu/~behansen/718/Hamilton1989.pdf); instead it uses a qualitative checklist of transition precursors drawn from historical episodes. The checklist is consumed by Phase E to set the `macro_regime_transition: true` flag in briefing frontmatter when three or more items trigger.

Transition precursors: **cross-asset divergence** where gold, DXY, and credit reprice while equities have not caught up; **FCI breakout** where NFCI crosses zero from below or ANFCI rises above 0.3; **credit lead** where HY OAS widens more than 50 basis points while VIX remains below 20; **unemployment trend shift** where the Sahm Rule triggers or 3-month payroll momentum turns negative; **yield-curve re-steepening from inversion** where T10Y3M returns to positive after six or more months inverted (historically a late-cycle to contraction signal, not an Early-cycle signal); **EBP spike** where the Fed Board monthly EBP rises more than 0.5 standard deviations month-over-month; **breadth divergence** where the S&P 500 makes a new 20-day high with fewer than 40% of constituents above their 200-day moving average; **policy-path repricing** where fed funds futures implied path shifts more than 50 basis points over a two-week window.

The historical template: the 2007 Late-cycle-to-Contraction transition showed credit widening from 350 to 700 basis points between July and October while equities held within 5% of the October peak; NFCI crossed zero in August; the curve had re-steepened from deep inversion in summer 2007 before the December 2007 NBER peak. The 2020 Mid-cycle-to-Contraction transition was compressed into three weeks rather than three months due to the exogenous pandemic shock; credit widened from 350 to 1087 basis points between February 20 and March 23, 2020; VIX closed 82.69 on March 16 per [Cboe tail events attribution](https://www.cboe.com/insights/posts/vix-index-attribution-of-notable-tail-events/). The 2018 end-of-year Fed-induced Risk-off followed the December 19, 2018 FOMC hike per the [transcript](https://www.federalreserve.gov/mediacenter/files/FOMCpressconf20181219.pdf) and was reversed by Powell's January 4, 2019 AEA panel use of "patient," producing a three-session 7% drawdown and a 15% five-week recovery -- a textbook Fed-Week to Risk-off to Risk-on sequence driven entirely by policy-path expectations.

## 13. Application to `/brief` Phases E + G and portfolio sensitivity

### Phase E decision tree (day regime)

First-match-wins ordering:

1. If VIX > 40 OR HY OAS > 800 OR SPX single-day return < -3%, emit `Crisis`.
2. Else if FOMC statement/minutes/press conference/testimony/Jackson Hole within 5 sessions forward, emit `Fed Week`.
3. Else if VIX between 25 and 40 AND (HY OAS > 500 OR VIX/VIX3M > 1.00 OR breadth <30% above 200d MA), emit `Risk-off`.
4. Else if S&P 500 constituents representing more than 15% of market cap reporting earnings within 5 sessions, emit `Earnings`.
5. Else if VIX between 13 and 20 AND sector-dispersion top-minus-bottom > 3% daily AND 20-day sector correlation < 0.5, emit `Rotation`.
6. Else if VIX < 15 AND HY OAS < 350 AND breadth > 60% above 200d MA, emit `Risk-on`.
7. Else emit `Risk-on` with reduced confidence (default tail).

### Phase E decision tree (macro regime)

1. If Sahm Rule triggered OR PMI < 45 OR LEI 6-month annualized < -4%, emit `Contraction`.
2. Else if T10Y3M < 50 bps (inverted or nearly) AND unemployment at cycle low AND HY OAS rising from tight, emit `Late cycle`.
3. Else if T10Y3M > 150 bps AND PMI crossing back above 50 AND unemployment falling from peak, emit `Early cycle`.
4. Else emit `Mid cycle` (default).

### Phase G decision tree (coherence)

1. Compute agreement count across the 7 signals relative to the day-regime direction.
2. If 6 or 7 signals aligned with risk-on, emit `coherent-risk-on`.
3. If 6 or 7 signals aligned with risk-off, emit `coherent-risk-off`.
4. Else emit `divergent` and list the disagreeing signals.

### Portfolio sensitivity matrix

Cells indicate expected impact direction (+/-/0) and magnitude bucket (S/M/L).

| Position | Crisis | Risk-off | Fed Week | Earnings | Rotation | Risk-on | Early | Mid | Late | Contraction | Coh-On | Coh-Off | Diverg |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| <AI-GPU>   | -L | -M | 0 | +/-L | -M | +L | +M | +L | +/-M | -L | +L | -L | -M |
| <AI-MEM-1> | -L | -M | 0 | +/-L | -M | +M | +L | +M | -M | -L | +M | -L | -M |
| <AI-MEM-2> | -L | -M | 0 | +/-M | -M | +M | +L | +M | -M | -L | +M | -L | -M |
| <TECH-ETF> | -L | -M | +/-M | +/-M | -M | +L | +M | +L | -M | -L | +L | -M | -S |
| <BROAD-ETF>| -M | -M | +/-S | +/-S | 0 | +M | +M | +M | 0 | -M | +M | -M | -S |
| <CRYPTO-1> | -L | -L | +/-M | 0 | +/-M | +L | +M | +M | -M | -L | +L | -L | -L |

Readings: a high-beta primary-thesis sleeve (e.g., GPU, memory, sector ETF positions) carries Large negative Crisis exposure because the long-duration, high-multiple, cyclical-demand profile compounds on the downside. The core-index ETF is the lowest-beta sleeve by construction; a crypto position has the widest conditional return distribution due to liquidity-conditions sensitivity. Fed Week impact is sign-indeterminate because it depends on dove-versus-hawk outcome -- the cells reflect magnitude, not direction. Earnings cells for AI-infrastructure names are sign-indeterminate reflecting the pre-print uncertainty that collapses within 48 hours of the report.

## 14. Pseudocode -- unified classifier

```python
def classify(mode: str, inputs: dict) -> dict:
    """
    Unified regime classifier for /brief v2 Phases E + G.

    mode: 'day' | 'macro' | 'coherence'
    inputs: dict of pre-fetched signals. Required keys depend on mode.
      day:       vix, vix3m, hy_oas, spx_ret_1d, breadth_pct_above_200d,
                 fomc_within_5d, earnings_cap_pct_5d,
                 sector_dispersion, sector_corr_20d, gamma_flip
      macro:     t10y3m, t10y2y, unrate, sahm_real, pmi, lei_6m_annlzd,
                 hy_oas, ig_oas, ebp
      coherence: spx_dir, credit_dir, rates_dir, dxy_dir, gold_dir,
                 vix_dir, btc_dir   # each in {-1, 0, +1}
    Returns: {'class': str, 'markers': dict, 'confidence': float}
    """
    markers = {}

    if mode == 'day':
        v = inputs
        # Ordered first-match-wins rules
        if v['vix'] > 40 or v['hy_oas'] > 800 or v['spx_ret_1d'] < -0.03:
            cls = 'Crisis'
            conf = 0.90
            markers['trigger'] = 'vol_or_credit_or_drawdown_breach'
        elif v['fomc_within_5d']:
            cls = 'Fed Week'
            conf = 0.95
            markers['trigger'] = 'calendar_fomc'
        elif (25 <= v['vix'] <= 40) and (
                v['hy_oas'] > 500
                or (v['vix'] / max(v['vix3m'], 0.01)) > 1.00
                or v['breadth_pct_above_200d'] < 0.30):
            cls = 'Risk-off'
            conf = 0.80
            markers['trigger'] = 'vol_band_plus_confirm'
        elif v['earnings_cap_pct_5d'] > 0.15:
            cls = 'Earnings'
            conf = 0.85
            markers['trigger'] = 'earnings_calendar_density'
        elif (13 <= v['vix'] <= 20) and v['sector_dispersion'] > 0.03 \
                and v['sector_corr_20d'] < 0.5:
            cls = 'Rotation'
            conf = 0.70
            markers['trigger'] = 'dispersion_plus_low_correlation'
        elif v['vix'] < 15 and v['hy_oas'] < 350 \
                and v['breadth_pct_above_200d'] > 0.60:
            cls = 'Risk-on'
            conf = 0.85
            markers['trigger'] = 'full_risk_on_confirm'
        else:
            cls = 'Risk-on'
            conf = 0.50
            markers['trigger'] = 'default_tail'
        # Gamma modifier
        if v.get('gamma_flip') == 'negative' and cls in ('Risk-on', 'Rotation'):
            conf = max(conf - 0.10, 0.40)
            markers['gamma_modifier'] = 'negative_gamma_downweight'
        markers['vix'] = v['vix']
        markers['vix_vix3m_ratio'] = v['vix'] / max(v['vix3m'], 0.01)
        markers['hy_oas'] = v['hy_oas']

    elif mode == 'macro':
        m = inputs
        if m['sahm_real'] >= 0.50 or m['pmi'] < 45 or m['lei_6m_annlzd'] < -0.04:
            cls = 'Contraction'
            conf = 0.85
        elif m['t10y3m'] < 0.50 and m['hy_oas'] > 350 \
                and m['hy_oas'] < 600:
            cls = 'Late cycle'
            conf = 0.75
        elif m['t10y3m'] > 1.50 and m['pmi'] > 50 \
                and m['unrate'] < m.get('unrate_3m_ago', m['unrate'] + 0.1):
            cls = 'Early cycle'
            conf = 0.75
        else:
            cls = 'Mid cycle'
            conf = 0.65
        markers['t10y3m'] = m['t10y3m']
        markers['pmi'] = m['pmi']
        markers['sahm_real'] = m['sahm_real']
        markers['hy_oas'] = m['hy_oas']
        markers['ebp'] = m.get('ebp')
        markers['lei_6m_annlzd'] = m['lei_6m_annlzd']

    elif mode == 'coherence':
        c = inputs
        # Risk-on signature: spx+, credit+ (tighter -> dir +1),
        # rates + moderate, dxy -, gold -, vix -, btc +
        on_pattern = {
            'spx_dir': +1, 'credit_dir': +1, 'rates_dir': +1,
            'dxy_dir': -1, 'gold_dir': -1, 'vix_dir': -1, 'btc_dir': +1,
        }
        off_pattern = {k: -v for k, v in on_pattern.items()}
        on_agree = sum(1 for k, v in on_pattern.items() if c[k] == v)
        off_agree = sum(1 for k, v in off_pattern.items() if c[k] == v)
        if on_agree >= 6:
            cls = 'coherent-risk-on'
            conf = 0.80
        elif off_agree >= 6:
            cls = 'coherent-risk-off'
            conf = 0.80
        else:
            cls = 'divergent'
            conf = 0.70
        disagreeing = [k for k, v in on_pattern.items()
                       if c[k] not in (v, 0)
                       and c[k] != (v if on_agree >= off_agree else -v)]
        markers['on_agree'] = on_agree
        markers['off_agree'] = off_agree
        markers['disagreeing_signals'] = disagreeing

    else:
        raise ValueError("mode must be 'day' | 'macro' | 'coherence'")

    return {'class': cls, 'markers': markers, 'confidence': conf}
```

All three modes return the same shape to satisfy Pattern 11 audit output in [ref-briefing-structure.md](#). The `markers` dict is written to briefing frontmatter so every regime call is reproducible from the cited inputs.

## 15. Limitations and evolution

The taxonomy inherits three documented regime shifts that require quarterly review.

**Stock-bond correlation flipped positive in 2022.** The classical 60/40 playbook assumes negative stock-bond correlation so that Treasuries hedge equity drawdowns. [AQR's 2022 Alternative Thinking "The Stock/Bond Correlation"](https://savantwealth.com/wp-content/uploads/2022/08/AQR-Alternative-Thinking-The-Stock-Bond-Correlation-2Q-2022.pdf) models the correlation as a function of growth volatility, inflation volatility, and growth-inflation correlation, achieving 71% r-squared on 1936--2022 US data. [Ilmanen and Maloney's IPE viewpoint](https://www.ipe.com/comment/viewpoint-where-now-for-the-stock/bond-correlation/10060488.article) extends the framing. In the 2022 bear market, the Bloomberg US Aggregate fell 10.4% in the first half while the S&P 500 fell 21% -- worst combined six-month period since 1976. The coherence framework must not assume Treasuries bid into an equity sell-off; that assumption holds only in disinflationary regimes.

**60/40 expected-return regime has re-rated.** The [Ilmanen Wharton/Pension Research Council paper on low-return worlds](https://pensionresearchcouncil.wharton.upenn.edu/wp-content/uploads/2017/10/WP-2017-14-Ilmanen.pdf) and recent [Asness and Ilmanen commentary](https://www.moneytalkgo.com/video/the-60-40-portfolio-still-a-viable-strategy/) place real expected returns on a global 60/40 at ~3.5% forward, up from the ~1.5% end-2021 level per [Axios 2026 coverage](https://www.axios.com/2026/04/14/stocks-bonds-inflation-investing) and [Morgan Stanley Thoughts on the Market December 2025](https://www.morganstanley.com/insights/podcasts/thoughts-on-the-market/60-40-portfolio-does-it-make-sense-serena-tang). This affects macro-regime sector-leadership calls in Mid and Late cycle, where bond-beta exposure (tech ETF rate-duration, core-index ETF DCF-multiple sensitivity) is re-rated more aggressively than historical regimes suggest.

**Retail and 0DTE have altered the VIX regime.** Since the February 5, 2018 Volmageddon event (VIX +116% single-day, XIV ETN lost ~97%) documented in [Augustin, Cheng, and Van den Bergen FAJ 2021](https://www.tandfonline.com/doi/abs/10.1080/0015198X.2021.1913040), the microstructure of volatility trading has shifted toward short-dated options and retail flow; the [SEC 2010 Flash Crash joint report](https://www.sec.gov/news/studies/2010/marketevents-report.pdf) established the intraday-liquidity vulnerability that 0DTE has subsequently amplified. The regime-classification risk is that a VIX print of 22 in 2026 does not carry the same signal as a VIX print of 22 in 2012; realized-volatility clustering is shorter and sharper. The classifier's 13--20 Rotation band and 25--40 Risk-off band may require recalibration against rolling 5-year percentiles rather than full-history percentiles.

**AI-infrastructure capex super-cycle risks regime mis-classification.** A Late-cycle signal on curve-and-credit grounds can coincide with Early-cycle signals on semiconductor capex, data-center build-out, and HBM order books. The [2024 arXiv working paper on the EBP](https://arxiv.org/html/2412.04063v1) and the [Atlanta Fed term-structure extension](https://www.atlantafed.org/-/media/documents/research/publications/policy-hub/2021/09/24/12--term-structure-of-excess-bond-premium.pdf) both caution against single-indicator regime calls when sector-specific investment cycles decouple from the aggregate. `/brief` flags this mismatch explicitly when the macro classifier emits Late cycle while AI-infrastructure peer-constellation signals are in expansion. Review cadence: this document is updated quarterly; thresholds are re-evaluated against rolling 5-year distributions each January; the transition-precursor checklist is audited against the prior year's regime calls each April.

## 16. References

1. Cboe Volatility Index Methodology (primary PDF). https://cdn.cboe.com/api/global/us_indices/governance/Volatility_Index_Methodology_Cboe_Volatility_Index.pdf
2. Cboe Volatility Index Mathematics Methodology. https://cdn.cboe.com/resources/indices/Cboe_Volatility_Index_Mathematics_Methodology.pdf
3. Cboe Selected SPX Target Expected Volatility Term Indices methodology. https://cdn.cboe.com/api/global/us_indices/governance/Volatility_Index_Methodology_Selected_SPX_Target_Expected_Volatility_Term_Indices.pdf
4. FRED VIXCLS (VIX daily close). https://fred.stlouisfed.org/series/VIXCLS
5. S&P DJI Indexology "29 Years of VIX." https://www.indexologyblog.com/2022/05/31/29-years-of-vix/
6. S&P DJI Indexology "What's a Normal VIX Level?" https://www.indexologyblog.com/2014/02/04/whats-a-normal-vix-level/
7. Cboe Insights "VIX Backwardation as a Sign of a Future Down Market?" https://www.cboe.com/insights/posts/inside-volatility-trading-is-vix-backwardation-necessarily-a-sign-of-a-future-down-market/
8. VIX Central term structure. http://www.vixcentral.com/
9. Johnson (2017) "Risk Premia and the VIX Term Structure," JFQA. https://www.travislakejohnson.com/pdfs/Johnson%20VIXTS%202017%20(JFQA).pdf
10. Cboe VIX Index attribution of notable tail events. https://www.cboe.com/insights/posts/vix-index-attribution-of-notable-tail-events/
11. FRED ICE BofA US High Yield OAS (BAMLH0A0HYM2). https://fred.stlouisfed.org/series/BAMLH0A0HYM2
12. FRED ICE BofA US Corporate IG OAS (BAMLC0A0CM). https://fred.stlouisfed.org/series/BAMLC0A0CM
13. Gilchrist and Zakrajsek (2012) "Credit Spreads and Business Cycle Fluctuations," AER. https://www.aeaweb.org/articles?id=10.1257/aer.102.4.1692
14. Favara, Gilchrist, Lewis, and Zakrajsek (2016) FEDS Note on recession risk and EBP. https://www.federalreserve.gov/econresdata/notes/feds-notes/2016/recession-risk-and-the-excess-bond-premium-20160408.html
15. Fed Board EBP updating FEDS Note. https://www.federalreserve.gov/econres/notes/feds-notes/updating-the-recession-risk-and-the-excess-bond-premium-20161006.html
16. Fed Board permanent EBP CSV. https://www.federalreserve.gov/econres/notes/feds-notes/ebp_csv.csv
17. Atlanta Fed term structure of the excess bond premium. https://www.atlantafed.org/-/media/documents/research/publications/policy-hub/2021/09/24/12--term-structure-of-excess-bond-premium.pdf
18. 2024 arXiv "Understanding the Excess Bond Premium." https://arxiv.org/html/2412.04063v1
19. Gilchrist, Yankov, and Zakrajsek (2009) "Credit Market Shocks," NBER w14863. https://www.nber.org/papers/w14863
20. Faust, Gilchrist, Wright, Zakrajsek (2013) credit spreads as real-time economic predictors. https://www.nber.org/papers/w16725
21. Estrella and Mishkin (1996) "Yield Curve as Predictor of Recessions," NY Fed. https://www.newyorkfed.org/medialibrary/media/research/current_issues/ci2-7.pdf
22. Estrella and Mishkin (1998) "Predicting US Recessions," SSRN record. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1001228
23. Estrella and Trubin (2006) "Yield Curve as Leading Indicator: Practical Issues." https://www.newyorkfed.org/research/current_issues/ci12-5.html
24. NY Fed yield-curve-as-predictor FAQ. https://www.newyorkfed.org/research/capital_markets/ycfaq
25. NY Fed recession probability PDF. https://www.newyorkfed.org/medialibrary/media/research/capital_markets/prob_rec.pdf
26. FRED T10Y3M. https://fred.stlouisfed.org/series/T10Y3M
27. FRED T10Y2Y. https://fred.stlouisfed.org/series/T10Y2Y
28. Engstrom and Sharpe (2018) "Don't Fear the Yield Curve," FEDS Note. https://www.federalreserve.gov/econres/notes/feds-notes/dont-fear-the-yield-curve-20180628.html
29. Engstrom and Sharpe (2022) "Don't Fear the Yield Curve, Reprise." https://www.federalreserve.gov/econres/notes/feds-notes/dont-fear-the-yield-curve-reprise-20220325.html
30. Chicago Fed Letter 404 "Why Does the Yield-Curve Slope Predict Recessions?" https://www.chicagofed.org/publications/chicago-fed-letter/2018/404
31. Johansson and Meldrum (2018) FEDS Note on recession probabilities. https://www.federalreserve.gov/econres/notes/feds-notes/predicting-recession-probabilities-using-the-slope-of-the-yield-curve-20180301.html
32. NY Fed ACM term premia data. https://www.newyorkfed.org/research/data_indicators/term-premia-tabs
33. Adrian, Crump, Moench (2013) Staff Report 340. https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr340.pdf
34. Liberty Street Economics Treasury term premia primer. https://libertystreeteconomics.newyorkfed.org/2014/05/treasury-term-premia-1961-present/
35. FRED DFII10 (10Y TIPS). https://fred.stlouisfed.org/series/DFII10
36. FRED DGS10 (10Y nominal). https://fred.stlouisfed.org/series/DGS10
37. FRED T10YIE (10Y breakeven). https://fred.stlouisfed.org/series/T10YIE
38. NBER Business Cycle Dating main page. https://www.nber.org/research/business-cycle-dating
39. NBER Business Cycle Dating Procedure FAQ. https://www.nber.org/research/business-cycle-dating/business-cycle-dating-procedure-frequently-asked-questions
40. NBER US Business Cycle Expansions and Contractions dates. https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions
41. NBER July 2021 announcement (April 2020 trough). https://www.nber.org/news/business-cycle-dating-committee-announcement-july-19-2021
42. NBER September 2010 announcement (June 2009 trough). https://www.nber.org/news/business-cycle-dating-committee-announcement-september-20-2010
43. NBER July 2003 announcement (November 2001 trough). https://www.nber.org/news/business-cycle-dating-committee-announcement-july-17-2003
44. Sahm (2019) Brookings Hamilton Project chapter. https://www.brookings.edu/wp-content/uploads/2019/05/ES_THP_Sahm_web_20190506.pdf
45. FRED SAHMREALTIME. https://fred.stlouisfed.org/series/SAHMREALTIME
46. FRED SAHMCURRENT. https://fred.stlouisfed.org/series/SAHMCURRENT
47. FRED UNRATE. https://fred.stlouisfed.org/series/UNRATE
48. BLS Beveridge curve chart. https://www.bls.gov/charts/job-openings-and-labor-turnover/job-openings-unemployment-beveridge-curve.htm
49. Fed Board Beveridge curve and soft landing FEDS Note. https://www.federalreserve.gov/econres/notes/feds-notes/what-does-the-beveridge-curve-tell-us-about-the-likelihood-of-a-soft-landing-20220729.html
50. ISM Manufacturing PMI Report on Business. https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/pmi/
51. Conference Board US Leading Economic Index. https://www.conference-board.org/topics/us-leading-indicators/
52. Fidelity AART Business Cycle Sector Approach whitepaper. https://www.fidelity.com/bin-public/060_www_fidelity_com/documents/fixed-income/Business_Cycle_Sector_Approach.pdf
53. Chicago Fed NFCI About/methodology. https://www.chicagofed.org/research/data/nfci/about
54. Chicago Fed NFCI current data. https://www.chicagofed.org/research/data/nfci/current-data
55. Chicago Fed NFCI FAQs PDF. https://www.chicagofed.org/-/media/publications/nfci/nfci-faqs-pdf.pdf
56. Chicago Fed Letter 386 on ANFCI. https://www.chicagofed.org/publications/chicago-fed-letter/2017/386
57. FRED NFCI. https://fred.stlouisfed.org/series/NFCI
58. FRED ANFCI. https://fred.stlouisfed.org/series/ANFCI
59. FRED STLFSI4. https://fred.stlouisfed.org/series/STLFSI4
60. FRED STLFSI release page. https://fred.stlouisfed.org/release?rid=187
61. FRED blog on STLFSI4 methodology. https://fredblog.stlouisfed.org/2022/11/the-st-louis-feds-financial-stress-index-version-4/
62. Fed Board FEDS Note introducing FCI-G. https://www.federalreserve.gov/econres/notes/feds-notes/a-new-index-to-measure-us-financial-conditions-20230630.html
63. Hatzius, Hooper, Mishkin, Schoenholtz, Watson (2010) Financial Conditions Indexes. https://www.nber.org/system/files/working_papers/w16150/w16150.pdf
64. Kliesen, Owyang, Vermann (2013) FEDS paper on FCIs. https://www.federalreserve.gov/pubs/feds/2013/201339/index.html
65. SF Fed Economic Letter on monetary policy and financial conditions. https://www.frbsf.org/research-and-insights/publications/economic-letter/2024/03/monetary-policy-and-financial-conditions/
66. FOMC calendars. https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
67. Fed Board About the FOMC. https://www.federalreserve.gov/monetarypolicy/fomc.htm
68. Fed Board semiannual Monetary Policy Report. https://www.federalreserve.gov/monetarypolicy/publications/mpr_default.htm
69. Fed Board About Humphrey-Hawkins. https://www.federalreserve.gov/boarddocs/hh/about.htm
70. Kansas City Fed Jackson Hole Economic Symposium. https://www.kansascityfed.org/research/jackson-hole-economic-symposium/
71. Fed H.4.1 weekly release. https://www.federalreserve.gov/releases/h41/
72. Fed H.4.1 About the release. https://www.federalreserve.gov/releases/h41/about.htm
73. FRED WALCL (Fed Total Assets). https://fred.stlouisfed.org/series/WALCL
74. NY Fed ON RRP facility page. https://www.newyorkfed.org/markets/domestic-market-operations/monetary-policy-implementation/repo-reverse-repo-agreements
75. FRED RRPONTSYD. https://fred.stlouisfed.org/series/RRPONTSYD
76. Liberty Street Economics ON RRP primer. https://libertystreeteconomics.newyorkfed.org/2022/01/how-the-feds-overnight-reverse-repo-facility-works/
77. Treasury Fiscal Data Daily Treasury Statement dataset. https://fiscaldata.treasury.gov/datasets/daily-treasury-statement/
78. FRED WTREGEN. https://fred.stlouisfed.org/series/WTREGEN
79. Howell Capital Wars on net liquidity. https://capitalwars.substack.com/p/think-correctly-about-liquidity
80. Lopez-Salido Boston Fed liquidity-effect analysis. https://www.bostonfed.org/-/media/Documents/Workingpapers/PDF/2018/cpp1801.pdf
81. FOMC December 19, 2018 press conference transcript. https://www.federalreserve.gov/mediacenter/files/FOMCpressconf20181219.pdf
82. FactSet Earnings Insight. https://www.factset.com/earningsinsight
83. FactSet Insight earnings topic feed. https://insight.factset.com/topic/earnings
84. Ball and Brown (1968) JAR. https://www.jstor.org/stable/2490232
85. Bernard and Thomas (1989) JAR. https://www.jstor.org/stable/2491062
86. Chordia, Goyal, Sadka, Sadka, Shivakumar (2009) PEAD and liquidity. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1403342
87. CNBC 2026-04-23 SK Hynix Q1 record profit. https://www.cnbc.com/2026/04/23/sk-hynix-earnings-ai-memory-shortage-hbm-demand.html
88. Korea Times 2026-04-23 SK Hynix Q1 margin. https://www.koreatimes.co.kr/business/tech-science/20260423/sk-hynix-q1-operating-margin-breaks-above-70-higher-than-nvidia-tsmc
89. Introl 2026 AI Memory Supercycle analysis. https://introl.com/blog/ai-memory-supercycle-hbm-2026
90. AAII Sentiment Survey. https://www.aaii.com/sentimentsurvey
91. AAII Investor Sentiment as a Contrarian Indicator. https://www.aaii.com/journal/sentimentsurveyarticle?a=1209
92. AAII Analyzing the Sentiment Survey Without Hindsight. https://www.aaii.com/journal/article/analyzing-the-aaii-sentiment-survey-without-hindsight
93. NAAIM Exposure Index methodology. https://naaim.org/programs/naaim-exposure-index/
94. CFTC Commitments of Traders. https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
95. CFTC About the COT Reports. https://www.cftc.gov/MarketReports/CommitmentsofTraders/AbouttheCOTReports/index.htm
96. CFTC Public Reporting Environment COT. https://publicreporting.cftc.gov/stories/s/Commitments-of-Traders/r4w3-av2u/
97. Cboe equity put-call ratio methodology. https://www.cboe.com/insights/posts/how-early-exercise-order-flow-impacts-equity-option-put-call-ratios/
98. SqueezeMetrics GEX white paper. https://squeezemetrics.com/monitor/download/pdf/white_paper.pdf
99. Brogaard, Han, Won on 0DTE volatility. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4426358
100. Cboe 0DTEs Decoded positioning and market impact. https://www.cboe.com/insights/posts/0-dt-es-decoded-positioning-trends-and-market-impact/
101. McClellan Financial Publications Oscillator and Summation Index. https://www.mcoscillator.com/learning_center/kb/mcclellan_oscillator/the_mcclellan_oscillator_summation_index/
102. McClellan Oscillator calculation details. https://www.mcoscillator.com/learning_center/kb/mcclellan_oscillator/Calculating_the_McClellan_Oscillator/
103. StockCharts ChartSchool Summation Index. https://chartschool.stockcharts.com/table-of-contents/market-indicators/mcclellan-summation-index
104. Hamilton (1989) Econometrica regime switching. https://users.ssc.wisc.edu/~behansen/718/Hamilton1989.pdf
105. AQR Alternative Thinking 2022 on stock-bond correlation. https://savantwealth.com/wp-content/uploads/2022/08/AQR-Alternative-Thinking-The-Stock-Bond-Correlation-2Q-2022.pdf
106. Ilmanen and Maloney IPE viewpoint on stock-bond correlation. https://www.ipe.com/comment/viewpoint-where-now-for-the-stock/bond-correlation/10060488.article
107. Ilmanen Wharton/Pension Research Council 2017. https://pensionresearchcouncil.wharton.upenn.edu/wp-content/uploads/2017/10/WP-2017-14-Ilmanen.pdf
108. Asness-Ilmanen TD MoneyTalk interview. https://www.moneytalkgo.com/video/the-60-40-portfolio-still-a-viable-strategy/
109. Axios 2026-04-14 on stocks, bonds, inflation. https://www.axios.com/2026/04/14/stocks-bonds-inflation-investing
110. Morgan Stanley Thoughts on the Market 60/40 December 2025. https://www.morganstanley.com/insights/podcasts/thoughts-on-the-market/60-40-portfolio-does-it-make-sense-serena-tang
111. Augustin, Cheng, Van den Bergen (2021) Volmageddon FAJ. https://www.tandfonline.com/doi/abs/10.1080/0015198X.2021.1913040
112. SEC/CFTC 2010 Flash Crash joint report. https://www.sec.gov/news/studies/2010/marketevents-report.pdf
113. Treasury International Capital (TIC) system. https://home.treasury.gov/data/treasury-international-capital-tic-system
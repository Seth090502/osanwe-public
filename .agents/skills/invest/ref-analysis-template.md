---
aliases: []
categories: [sources]
type: reference
created: 2026-04-22
updated: 2026-09-13
status: active
confidence: high
tags:
  - topic/investment-analysis
  - topic/metrics-catalog
  - topic/institutional-research
  - topic/forensic-accounting
  - topic/evidence-grading
related:
  - "invest"
  - "[[ref-options-layer]]"
  - "[[ref-scoring-models]]"
  - "ref-sector-benchmarks"
  - "ref-portfolio-doctrine"
  - "[[ref-research-methodology]]"
  - "[[analysis-depth-standard]]"
word_count: 10184
sources_count: 79
---

# ref-analysis-template

Canonical institutional-grade reference for `/invest` Phase F (metrics catalog), Phase K (analysis-file output contract), Pre-Output 10-point HALT gate, INGEST:claims coordination block (Pattern 18), and evidence-grading discipline. This file is consumed by the skill; it is not a market-linked research report.

## Table of contents

## 1. Introduction and scope
## 2. Metrics catalog -- stock categories
## 3. Metrics catalog -- ETF categories
## 4. Metrics catalog -- crypto categories
## 5. Semiconductor and AI-infrastructure deep dive
## 6. Canonical analysis-file output contract (Phase K)
## 7. Pre-Output 10-point HALT gate
## 8. INGEST:claims coordination block (Pattern 18)
## 9. Evidence grading and temporal anchoring
## 10. Confidence vs conviction (calibration)
## 11. Institutional memo structure (comparative)
## 12. Kill criteria best practices
## 13. Sources and references

---

## 1. Introduction and scope

This reference defines the metric definitions, output contract, gating logic, and coordination semantics used by the `/invest <ticker>` skill. It is authoritative for four downstream consumers: Phase F (fundamental analysis -- four searches per ticker populate the metrics catalog in Section 2-4), Phase K (compose-analysis-file writes an Obsidian note conforming to the output contract in Section 6), the Pre-Output 10-point HALT gate (Section 7 enforces evidence-grade confidence caps, Risk/Reward 3:1 hurdle, and Kill-Criteria quantification before output), and the INGEST:claims coordination block (Section 8 emits marker-signature tuples that downstream `/ingest` v2 final routes to cross-entity files without text-match dedup failure).

The file is institutional-grade by design. It assumes a reader fluent in accounting shorthand (ROIC, FCF yield, EV/EBITDA, NTM, TTM), semiconductor jargon (HBM, CoWoS, WFE, book-to-bill, node utilization), and basic factor-model vocabulary (beta, SMB, HML, UMD, QMJ). Definitions are therefore not restated inline. The target reader is the skill implementer, not an investing novice.

The scope excludes macro regime-switching models and multi-asset portfolio construction (covered in `ref-portfolio-doctrine` and `ref-research-methodology`). Options are covered at two layers as of 2026-07-11: the short-interest + options-flow INTELLIGENCE contract lives in Section 6.4 of this file (relocated from SKILL.md Phase H.2), and the options-STRUCTURE recommendation layer (strike/expiry/PoP mechanics, Phase K-ter) lives in `ref-options-layer.md` -- this file defines only where its output block renders (Section 6.4). This file covers single-security analysis (stock, ETF, or token) at the depth institutional long-short desks apply before sizing. See [CFA Institute -- Standards of Practice Handbook 12th ed.](https://www.cfainstitute.org/sites/default/files/-/media/documents/code/code-ethics-standards/standards-practice-handbook-12th-edition.pdf) Standard V ("Investment Analysis, Recommendations, and Actions") for the professional baseline this template operationalizes.

**Portfolio context that shapes metric weighting.** Live positions and dollar exposure come from the broker read MCP at run time (Phase J.0 hybrid book; never from a literal baked into this file -- the stale-literal failure mode is dead by construction per the /networth v2 precedent), and active thesis exposure comes from `wiki/hot.md` + the thesis map in `ref-portfolio-doctrine`. Thesis-specific analytics are load-bearing for whichever thesis a book concentrates in; Section 5 is one worked sector deep dive.

## 2. Metrics catalog -- stock categories

### 2.1 Valuation

Valuation metrics compress capital-market expectations into multiples. They are never absolute -- every metric is read against sector, history, and growth. The institutional valuation stack is P/E (TTM and NTM), P/S, P/B, EV/EBITDA, PEG, FCF yield, and shareholder yield. See [Damodaran ROIC working paper](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/returnmeasures.pdf) for the canonical derivation of why each multiple is a collapsed form of a DCF under fixed assumptions.

| Metric | Computation | Sector-benchmark anchor (S&P 500 median, 10Y) | Red flag |
|--------|-------------|-----------------------------------------------|----------|
| P/E TTM | Price / trailing 12mo diluted EPS | 18-22x broad, 25-35x software, 12-16x financials | >50x with decelerating revenue |
| P/E NTM | Price / consensus next-12mo EPS | 16-19x broad | NTM below TTM and gap widening (estimate cuts) |
| P/S | MktCap / TTM revenue | 2.5-3.5x broad, 8-15x hyperscaler software | >10x with <20% growth |
| P/B | MktCap / common equity | 3-4x broad, <1.5x financials (bank trap below 0.7x) | >10x with tangible equity erosion from buybacks |
| EV/EBITDA | (MktCap + Debt - Cash + Minority Int. + Pref) / EBITDA | 12-14x broad, 8-10x industrials, 15-20x software | SBC excluded without flag |
| PEG | P/E NTM / forward EPS growth % | ~1.0 neutral, <0.75 cheap-for-growth | Growth rate >3Y forward consensus (unreliable) |
| FCF yield | TTM FCF / MktCap | 3-5% broad baseline | <1% with capex ramp ahead |
| Shareholder yield | (Dividends + Net Buybacks) / MktCap | 2-4% for mature large-cap | Negative (net issuance at premium valuation) |

EV/EBITDA is institutionally preferred over P/E for cross-capital-structure comparability, but both TSMC's [3Q25 SEC 6-K](https://www.sec.gov/Archives/edgar/data/0001046179/000104617925000116/a3q25e_withguidancexfinal.htm) and NVIDIA's [FY2025 10-K](https://www.sec.gov/Archives/edgar/data/0001045810/000104581025000023/nvda-20250126.htm) carry near-zero net debt, collapsing the distinction. Shareholder yield is the metric Buffett and O'Shaughnessy treat as closer to a bondholder's coupon; [O'Shaughnessy What Works on Wall Street](http://www.whatworksonwallstreet.com/) backtests document shareholder yield dominating dividend yield across multiple decades. Damodaran's [WACC dataset](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/wacc.html) provides the cost-of-capital denominator required to translate any multiple into a value-creation statement.

### 2.2 Profitability and quality

Quality metrics separate business economics from accounting cosmetics. The institutional stack is ROIC, the ROIC-minus-WACC spread, gross/operating/net margins and their three-year slopes, FCF/Net-Income cash-conversion ratio, the Piotroski nine-signal F-Score, and an Altman Z-Score variant selected by industry.

ROIC is computed as NOPAT / invested capital, where invested capital is typically total debt plus equity minus cash-and-equivalents. [Mauboussin and Callahan (2022) ROIC paper](https://www.morganstanley.com/im/publication/insights/articles/article_returnoninvestedcapital.pdf) is the canonical practitioner derivation and enumerates the lease-capitalization, goodwill, and operating-lease treatments that reconcile company-reported ROIC to a comparable figure. A firm earning ROIC above its WACC creates value; the spread (not the absolute level) drives the valuation multiple. Damodaran's [ROIC/ROE measurement paper](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/returnmeasures.pdf) documents that reported ROIC is systematically biased high at mature firms (old asset bases depreciated against current earnings) and biased low at high-growth firms (capex ahead of revenue). The template therefore requires ROIC to be reported alongside WACC, not in isolation.

The Piotroski F-Score, introduced in [Piotroski (2000)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=249455), is a 0-9 binary score of nine fundamentals: positive net income, positive operating cash flow, OCF > Net Income (earnings quality), ROA improvement, declining leverage, improving current ratio, no share issuance, improving gross margin, and improving asset turnover. Scores of 8-9 flag improving fundamentals; 0-2 flag deterioration under this method. The original high-book-to-market population includes loss firms; profitability is a scored component, not an eligibility prerequisite. Applicability and predictive validity outside that population require separate evidence. The local bridge composite and cyclicality route have their own unchanged policy owners.

The Altman Z-Score ([Altman 1968](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1968.tb00843.x)) is a five-factor bankruptcy predictor: 1.2 * (WC/TA) + 1.4 * (RE/TA) + 3.3 * (EBIT/TA) + 0.6 * (MV Equity / Book Liab) + 1.0 * (Sales/TA). Z < 1.81 flags distress; Z > 2.99 flags safety. Variants: Z' for private firms (book equity), Z'' for non-manufacturers (drops asset turnover). Financial-sector firms need an applicable separately supported industry method. Standard Altman models are ineligible for banks; a KMV/Merton implementation and calibration must not be assumed available.

| Quality metric | Target | Yellow | Red |
|----------------|--------|--------|-----|
| ROIC (ex-cash) | >15% sustained | 8-15% | <8% or below WACC |
| ROIC - WACC spread | >500 bps | 100-500 bps | Negative |
| Gross margin trend (3Y) | Rising or stable | Flat | Declining >150 bps |
| FCF / Net Income | >0.9 | 0.7-0.9 | <0.7 (accrual buildup) |
| Piotroski F-Score | 7-9 | 4-6 | 0-3 |
| Altman Z-Score | >2.99 | 1.81-2.99 | <1.81 |

### 2.3 Growth

Growth metrics triangulate revenue CAGR (3Y and 5Y), EPS CAGR, FCF CAGR, the Rule of 40 for software (growth % + FCF margin % >= 40), and forward-estimate discipline. The template requires the analyst to distinguish organic growth from M&A-contributed growth (decompose via segment or acquired-revenue disclosures), and to flag when consensus forward-revenue growth exceeds management's most recent public guidance. Consensus estimates older than one quarter post-earnings are treated as STALE (Section 9).

Revenue quality decomposition is mandatory: price-versus-volume (ASP trend), geographic mix, customer concentration (top-10 % of revenue), and deferred-revenue build (leading indicator for subscription software). For semiconductor names, the template also requires a book-to-bill ratio in the growth section, sourced from [SEMI equipment billings releases](https://www.semi.org/en/SEMI-Reports-Global-Semiconductor-Equipment-Billings-Reached-135-Billion-in-2025).

### 2.4 Balance sheet

The balance-sheet stack is net debt / EBITDA, interest coverage (EBIT / interest expense), fixed-charge coverage (adds rent), current ratio, quick ratio, and the maturity ladder (debt due within 12/24/36/60 months versus available liquidity). The maturity schedule is frequently the load-bearing risk signal; a firm with 4x net debt / EBITDA and no maturities inside three years is less distressed than a firm with 2x leverage and a refinancing wall in 18 months.

Institutional practice (per [Koller, Goedhart and Wessels, Valuation 7th ed.](https://www.wiley.com/en-us/Valuation%3A+Measuring+and+Managing+the+Value+of+Companies%2C+7th+Edition-p-9781119611882)) normalizes operating leases into debt (capitalized at ~8x rent or per ASC 842 right-of-use assets) before computing leverage. Post-ASC 842, this is usually visible directly on the balance sheet; pre-2019 comparisons require manual capitalization.

### 2.5 Capital allocation

Capital-allocation analysis asks whether management has compounded intrinsic value or destroyed it. The template captures five-year history of: CapEx as % of sales (intensity trend), R&D as % of sales (flat or rising in tech; declining flags harvest mode), net buybacks as % of shares outstanding (and the price paid versus intrinsic-value estimate at time of repurchase), dividend history (initiation, growth, coverage), and M&A track record (deals >5% of market cap, with goodwill impairments flagged as ex-post value-destruction markers).

[Mauboussin and Callahan (2025) Capital Allocation paper](https://www.morganstanley.com/im/publication/insights/articles/article_capitalallocation.pdf) is the canonical framework. The key insight: buybacks are value-creating only when price is below intrinsic value. A firm buying back shares at a P/E of 45x and then issuing SBC at a P/E of 18x after correction has destroyed capital; the template therefore requires buyback-price versus three-year average price, and a signal on whether repurchases were opportunistic (accelerated during drawdowns) or mechanical (constant pace into rising multiples). Insider-flow signal comes from [SEC Form 4 filings via EDGAR](https://www.sec.gov/edgar/search/); clusters of sales into price strength or buys into weakness are the noteworthy patterns.

### 2.6 Forensic and quality

Forensic metrics are the adversarial layer. They assume management is optimizing for reported earnings and look for the deformation this produces in the accounting.

The **Beneish M-Score** ([Beneish 1999](https://www.tandfonline.com/doi/abs/10.2469/faj.v55.n5.2296)) is an eight-variable probit flagging earnings manipulation: DSRI (Days Sales Receivables Index), GMI (Gross Margin Index), AQI (Asset Quality Index), SGI (Sales Growth Index), DEPI (Depreciation Index), SGAI (SG&A Index), LVGI (Leverage Index), and TATA (Total Accruals to Total Assets). The composite formula is M = -4.84 + 0.92*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI + 0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI. M > -1.78 flags elevated manipulation probability. [Beneish, Nichols and Lee (2011)](https://www.ssrn.com/abstract=1903593) documents out-of-sample return predictability from the score. Enron scored M = -1.89 in 2000 on published financials, crossing the threshold before any public fraud allegation surfaced.

The **Dechow-Sloan-Ge-Larson F-Score** ([Dechow, Ge, Larson and Sloan 2011](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=997483)) is the second forensic layer, calibrated on 2,190 SEC Accounting and Auditing Enforcement Releases. It uses seven variables capturing accrual quality, revenue growth irregularities, nonfinancial measures (employees vs sales), and off-balance-sheet financing. F-Score > 1.0 flags elevated misstatement probability; > 2.45 flags material. [Dechow and Sloan (1995) Modified Jones Model](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5520) underlies the discretionary-accrual component.

The **accrual anomaly** ([Sloan 1996](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2598)) decomposes earnings into accrual and cash components; the accrual component is demonstrably less persistent and mean-reverts. The template requires (Net Income - Operating Cash Flow) / Total Assets, labeled "Sloan accrual," flagged when > 10% of assets.

The **Cash Conversion Cycle** = DIO + DSO - DPO is the liquidity-efficiency metric; ballooning CCC with flat revenue flags channel stuffing or collection deterioration. SBC dilution is captured as TTM SBC / revenue and TTM SBC / FCF; ratios above 15% of revenue or 40% of FCF are institutional red flags in technology.

John Hempton's [Bronte Capital blog](http://brontecapital.blogspot.com/) and the [Jim Chanos 2012 Graham and Doddsville interview](https://medium.com/graham-and-doddsville/jim-chanos-rooting-out-fraud-6eca8e6387ad) document the practitioner-level application of these scores to live cases; both emphasize that forensic scores flag probability, not guilt, and must be paired with qualitative investigation before action.

### 2.7 Advanced return decomposition

The template requires ROIC decomposed as **NOPAT Margin x Capital Turnover** (two levers) and ROE decomposed via the **five-factor DuPont**: ROE = Tax Burden * Interest Burden * EBIT Margin * Asset Turnover * Leverage. [CFA Institute Financial Analysis Techniques refresher](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/financial-analysis-techniques) is the canonical curriculum source. Decomposition forces identification of the operating lever (margin or turnover) and flags ROE gains driven purely by leverage or tax-burden decline, which are not durable sources of value.

**ROIIC** (Return on Incremental Invested Capital) is forward-looking: delta-NOPAT over trailing three years divided by delta-Invested-Capital over the same window. ROIIC above WACC signals ongoing value creation; ROIIC below WACC with accelerating capex signals reinvestment failure. Mauboussin's [capital allocation paper](https://www.morganstanley.com/im/publication/insights/articles/article_capitalallocation.pdf) treats ROIIC as the single most predictive forward-looking metric because it captures management's marginal decisions rather than legacy asset economics.

Customer concentration (top-10 as % of revenue; top-1 if > 20%) is captured here because high concentration mathematically compresses durable ROIC even when headline numbers look strong; one contract loss can invert the return calculus.

### 2.8 Capital-allocation scorecard

The scorecard aggregates Section 2.5 into five graded dimensions: organic-ROIIC-vs-WACC over trailing 3 and 5 years; M&A track record (goodwill-impairment ratio, revenue retention on acquired entities); buyback timing quality (price-paid vs three-year VWAP and vs DCF intrinsic); dividend sustainability (payout ratio vs FCF, coverage headroom); and balance-sheet posture (whether management added leverage counter-cyclically or pro-cyclically). Each dimension is graded A-F using the evidence-grade scale in Section 9. [Howard Marks's Oaktree memos archive](https://www.oaktreecapital.com/insights/memos) and Berkshire's [2024 Annual Letter](https://www.berkshirehathaway.com/letters/2024ltr.pdf) are the reference-quality examples of capital-allocation narrative.

### 2.9 Deterministic technicals panel (script contract; ported 2026-07-11)

**Traceability rule (Pre-Output item 2 extension):** every SMA, RSI, beta,
volatility, drawdown, and correlation figure in an analysis traces to
`tools/technicals.py` output (`prov: script:technicals`) or carries an explicit
per-figure web-fallback disclosure. Model-estimated technicals are forbidden --
the panel exists so no technical figure is ever narrative.

**Data path.** The price-fetcher subagent (dispatched with
`include_technicals: true` -- /invest E.0 only; /brief and /networth omit the
flag) pulls `get_equity_historicals` for the target + SPY benchmark + the
correlation basket in ONE batched call (<=10 symbols, ~420 calendar days of
daily bars), pipes the raw JSON to `tools/technicals.py` (stdlib-only,
self-tested via `tools/test-technicals.py`), and returns the panel under its
`technicals` key. Bars flagged `"interpolated": true` are excluded from all
analytics by the script.

**Field contract** (consumers named where load-bearing):

| Field | Content / consumer |
|---|---|
| `as_of`, `sessions`, `last_close` | series anchor; sessions <252 triggers the `insufficient_history` degrade note |
| `sma50`, `sma200`, `price_vs_sma50_pct`, `price_vs_sma200_pct` | Phase G |
| `cross` | golden/death state + `crossed_within_30_sessions` detection |
| `rsi14` | Wilder smoothing; Phase G |
| `returns_pct.5_session` | THE prov source for the GATE-F `move_5d_pct` marker (`script:technicals` outranks web) |
| `returns_pct.10_session`, `.1_month_21s` | donor chase inputs; feed the K.5 bounded behavioral mode's probability + the price-invariance test |
| `returns_pct.3_month_63s`, `.6_month_126s`, `.12_month_252s`, `.momentum_12_1` | Phase G momentum context |
| `vol_annualized_pct.trailing_63s` | Phase H vol + the options layer's realized-vol input (ref-options-layer IV proxy) |
| `vol_annualized_pct.full_window`, `drawdown` (+peak/trough dates) | Phase H |
| `52wk` (+off_high/off_low), `volume_ratio_20d_vs_90d` | Phase G/E |
| `benchmark.beta`, `.daily_return_correlation`, `.relative_strength_6mo_pct` | Phase H beta + Phase G RS |
| `--matrix` pairs (+`flag_gt_0.7`) | Phase J hidden-concentration; feeds the sizing worksheet `corr_gt_threshold_flag` input |

**Degradation ladder:** MCP historicals + technicals.py [preferred] ->
fetch-prices.py yfinance subset (rsi14/ma50/ma200/beta only) with a failures[]
entry -> Phase G WebSearch Grade-C with per-figure disclosure. A missing panel
never blocks the run; it downgrades provenance and discloses.

**Broker-first comps sourcing (rung 0, donor rule 15 port).** Every
price-type figure for the TARGET, its PEERS, and the BENCHMARK -- price, market
cap, share counts for cap math, 52-week range, volume, history, options quotes
-- comes from the broker MCP when its tools are present: peer quotes via ONE
batched `get_equity_quotes` (<=20 symbols) + `get_equity_fundamentals` (<=10)
call, never web snippets. A web-sourced market figure is a last resort after
the MCP call fails or the asset is not covered, and each one carries a
source+date disclosure (regular-session portfolio math additionally triggers
cap C5). Scope: this governs MARKET data -- filing-derived accounting data
stays EDGAR; forward estimates stay FMP/proxy (Section 2.10).

### 2.10 Forward estimates -- FMP-first with disclosed proxy fallback (2026-07-11)

**FMP-first.** The FMP MCP is a claude.ai account-level connector. Probe it at
runtime via ToolSearch -- tool names are DISCOVERED, never guessed (the server
requires per-session OAuth; verified unauthenticated in the build session, so
the proxy path below is the common case). When authenticated, FMP is the
primary source for: consensus revenue/EPS by FY (FY0/FY1/FY2), forward
multiples (P/E NTM, EV/EBITDA fwd, forward PEG), price-target distribution,
and rating breakdown. Grade B-C per the Section 9 hierarchy.

**Disclosed proxy fallback (state the path once per analysis).** When FMP is
absent: build the forward view from segment/KPI trends + the reverse-DCF
implied growth rate (K-bis.1) and use analyst-aggregate anchors
(stockanalysis.com, finviz) as rough consensus proxies, each with per-figure
source+date disclosure.

**Load-bearing invariant:** the price/EV side of every forward multiple is the broker quote x share count (Section 2.9 rung 0); ONLY the estimate side
comes from FMP or the proxy. Consensus older than one quarter post-earnings is
STALE (Section 2.3 rule preserved; auto-downgrade per Section 9.4).

### 2.11 Trim/exit tax-lot pass (greenfield 2026-07-11; Pre-Output item 10f)

Fires on ANY trim/exit recommendation for a held name. Read-only throughout --
lot-specified selling exists at order time, but nothing is ever placed.

1. Pull `get_equity_tax_lots(account_number, symbol)` for EVERY account holding
   the name (account numbers via `get_accounts`; the tool returns per-lot
   `quantity`, `cost_per_share`, `open_date`, and `term: st|lt` -- the LT/ST
   split is mechanical, verified live 2026-07-11).
2. **LTCG bracket handling:** the bracket status is DERIVED at run time from
   the user's stated income facts -- never quoted as a constant from this file.
   Where long-term gains fall in a low or zero-rate bracket, FLAG (do not
   compute) the risk of large realizations stacking taxable income past the
   bracket ceiling.
3. **Near-conversion lots:** name every lot within ~60 days of long-term status
   with its exact conversion date (`open_date` + 1 year + 1 day). "Wait N days,
   then trim" is often the entire answer.
4. **Wash-sale flag:** on any loss sale where re-entry is plausible, flag the
   30-day window explicitly.
5. **Disposition-effect check (donor port; sell-side sibling of GATE-F):** if
   the proposal sells a WINNER while the book holds a larger unrealized LOSER
   with a weaker thesis, flag once with both numbers in Decision-Sheet prose.
   This check informs the narrative only -- it feeds no penalty arithmetic and
   never blocks (the K.5 conviction bound governs the buy-side analog).
6. **Options interplay:** options P&L is short-term ordinary income -- any long-term-gains rate advantage does NOT transfer.
   When an options structure would convert
   LTCG-eligible appreciation into ST premium (covered call) or hedge ST lots
   to their conversion date (protective put / collar), the tax note rules in
   `ref-options-layer.md` govern.

## 3. Metrics catalog -- ETF categories

### 3.1 Cost structure

Expense ratio is captured versus category median (US large-cap blend median ~0.04% for Vanguard/BlackRock core, ~0.35% for smart-beta, ~0.75% for thematic) per [Morningstar Rating for Funds methodology](https://www.morningstar.com/content/dam/marketing/shared/research/methodology/771945_Morningstar_Rating_for_Funds_Methodology.pdf). Tracking error is the annualized standard deviation of daily fund-return-minus-index-return; <10 bps for core cap-weighted funds, up to 200 bps for sampled international or fixed-income. Tax efficiency metrics capture 1/3/5Y tax-cost ratio from Morningstar (after-tax minus pre-tax return, annualized) and the ETF's historical capital-gains distribution record. Vanguard's heartbeat-trade patent-expired mechanism and in-kind redemption give broad-index and sector ETFs from the major issuers tax-cost ratios typically <0.20%.

### 3.2 Factor decomposition

Every ETF is regressed against Fama-French-Carhart factors using TTM daily returns. [Fama and French (1993)](https://www.sciencedirect.com/science/article/abs/pii/0304405X93900235) defines the three-factor model (MktRf, SMB, HML); [Fama and French (2015)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2287202) adds profitability (RMW) and investment (CMA); [Carhart (1997)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=8036) adds momentum (UMD/WML). The [AQR Quality Minus Junk paper](https://www.aqr.com/Insights/Research/Working-Paper/Quality-Minus-Junk) adds QMJ for a six-factor extension, and [Asness, Moskowitz and Pedersen Value and Momentum Everywhere](https://www.aqr.com/Insights/Research/Journal-Article/Value-and-Momentum-Everywhere) is the source for cross-asset momentum style analysis.

The template reports factor loadings with t-stats, R-squared, and alpha. Loadings above 0.3 (absolute) are material; t-stats below 2.0 are not statistically significant. Interpretation: a broad S&P 500 index fund loads ~1.0 on MktRf, ~0.0 on SMB (large-cap), ~0.0 on HML (blend); a technology-sector fund loads ~1.1 on MktRf, negative on HML (growth tilt), positive on QMJ (high-profitability tech); an infrastructure-theme fund loads positive on momentum and infrastructure sector-beta.

[Hsu, Kalesnik and Kose (2019)](https://www.anderson.ucla.edu/documents/areas/fac/finance/What%20Is%20Quality%20Jason%20Hsu.pdf) and [Berkin and Swedroe's CFA Institute factor-guide review](https://rpc.cfainstitute.org/research/financial-analysts-journal/2017/your-complete-guide-to-factor-based-investing) provide the practitioner scaffolding for interpreting factor output as portfolio-construction signal rather than merely statistical description.

### 3.3 Concentration and flows

Top-10-holding concentration ratio, effective number of holdings (1 / sum of weight-squared), sector concentration max, and issuer-concentration cap (SEC diversified-fund rule: no single issuer >5% of the 75% diversified bucket). Fund-flow data captures 1-month, 3-month, 12-month creation-minus-redemption from [ETF.com Fund Flows Tool](https://www.etf.com/etfanalytics/etf-fund-flows-tool). Liquidity is bid-ask midpoint spread (bps), average daily dollar volume (ADDV), and premium/discount-to-NAV TTM range. Spreads >10 bps on small ETFs are material transaction costs at a small portfolio's size.

### 3.4 Overlap analysis

Holdings-level overlap between a candidate ETF and a book's existing positions is computed as sum over all holdings of min(weight_A, weight_B). [S&P Dow Jones Indices US Methodology](https://www.spglobal.com/spdji/en/documents/methodologies/methodology-sp-us-indices.pdf) governs the construction of S&P 500 index funds. Typical overlaps: a broad S&P 500 fund and a technology sector fund ~35% (the sector fund is a concentrated subset of the index); two S&P 500 funds ~99% (same index, different fund structures); in the index-versus-sector case, a handful of mega-cap names drives the overlap.

The overlap test matters because stacking two funds and a single name triple-counts that name's exposure: ~6% of a diversified index ETF, ~15% of a tech-sector ETF, plus any direct position. The template reports effective single-name exposure in a consolidated "look-through" line.

## 4. Metrics catalog -- crypto categories

### 4.1 Tokenomics

The tokenomics block captures total supply, circulating supply, emission schedule (next 12/24/60 months), burn mechanics (EIP-1559 for ETH; transaction-fee burns for BNB), vesting cliffs for team and investor allocations, and staking lock-up rates. [Nakamoto (2008) Bitcoin whitepaper](https://bitcoin.org/bitcoin.pdf) established the fixed-21M supply precedent; [Ethereum.org proof-of-stake documentation](https://ethereum.org/developers/docs/consensus-mechanisms/pos/) documents ETH's post-Merge issuance-minus-burn dynamics.

### 4.2 On-chain metrics

Active addresses (daily, weekly), transaction volume (USD), fee revenue (daily/weekly/annualized), NVT ratio (network value divided by transaction volume, the "crypto P/E" per [Willy Woo's Woobull NVT article](https://woobull.com/introducing-nvt-ratio-bitcoins-pe-ratio-use-it-to-detect-bubbles/)), MVRV (market value to realized value; canonical methodology in [Coin Metrics State of the Network](https://coinmetrics.substack.com/p/coin-metrics-state-of-the-network-574)), SOPR (Spent Output Profit Ratio from [Glassnode Insights](https://insights.glassnode.com/on-chain-analysis-evolution-new-granular-cohorts-for-key-on-chain-metrics/)), and realized cap. For L1s with smart-contract activity, TVL (Total Value Locked) and developer activity (Electric Capital developer report methodology) enter the scorecard.

### 4.3 Staking and validator economics

Staking yield (gross and net of inflation), slashing risk, validator count, Nakamoto coefficient (minimum number of entities required to halt or compromise the chain; >33% for PoS, >50% for PoW), and client-diversity (single-client supermajority is a systemic risk). For ETH specifically, [Ethereum.org PoS doc](https://ethereum.org/developers/docs/consensus-mechanisms/pos/) is the reference for finality, validator duties, and slashing conditions.

### 4.4 Regulatory exposure

SEC status (registered security, commodity per CFTC, or undetermined) with direct citation. [SEC Chair Gensler's 10 Jan 2024 statement](https://www.sec.gov/newsroom/speeches-statements/gensler-statement-spot-bitcoin-011023) established the precedent-setting spot-Bitcoin ETP approval (Release No. 34-99306), and [SEC Chair Atkins's 12 Nov 2025 Project Crypto remarks](https://www.sec.gov/newsroom/speeches-statements/atkins-111225-secs-approach-digital-assets-inside-project-crypto) outline the current-administration token-taxonomy direction that governs regulatory risk scoring in 2026. Jurisdictional-risk captures whether a token is tradable on US exchanges, available only offshore, or subject to active enforcement action.

### 4.5 Messaging-standard alignment

Relevance applies to the payment-and-settlement token cohort. The [messaging standard's Registration Authority page](https://www.iso20022.org/about-iso-20022) defines the standard; score alignment only where a token's documented settlement role depends on it.

### 4.6 Crypto majors evidence stack (donor port 2026-07-11)

For crypto majors, cash-flow machinery is UNDEFINED -- DCF, comps, forward
consensus, and all forensic scores are not computed and never forced (the
subagent N/A-is-success contract governs; every dependent stage skips with a
note). The surviving analytical arc is variant-vs-consensus, scenario targets,
macro/regime, positioning, risk, and sizing, evidenced by this stack (mostly
Grade C; web-sourced):

- **Flows:** spot-ETF daily/weekly net flows -- the dominant marginal-buyer
  series since 2024; sustained outflow streaks read as negative revision
  momentum.
- **On-chain:** MVRV z-score + realized price as the cost-basis floor
  (Section 4.2 methodology sources).
- **Positioning:** perp funding rates + open interest; persistent positive
  funding = crowded long.
- **Supply:** issuance/halving schedule + long-term-holder supply share.
- **Regime:** correlation to QQQ/high-beta tech computed LIVE via
  `technicals.py --matrix` (Section 2.9) -- never asserted from memory.

Sizing: the doctrine crypto haircut (0.5x) and override-ineligibility apply at
the kernel layer (ref-kernel-sizing); kill criteria are still QUANTIFIED (a
flow threshold, an MVRV level, a funding regime -- Section 12 form). Alt-coins
beyond the majors default to AVOID absent a specific quantified variant.

## 5. Semiconductor and AI-infrastructure deep dive

This section is a worked sector deep dive; its depth reflects how poorly generic valuation captures the metrics that move these names.

### 5.1 TSMC node utilization and foundry capacity

Node utilization is tracked at N2/N3/N4/N5/N7 with quarterly disclosure from [TSMC Investor Relations](https://investor.tsmc.com/english/quarterly-results/2026/q1) and [TSMC's SEC 6-K filings](https://www.sec.gov/Archives/edgar/data/0001046179/000104617925000116/a3q25e_withguidancexfinal.htm). TSMC's Q1 2026 report shows revenue of NT$1,134.10B (~$35.90B), +40.6% YoY, driven by AI and HPC demand at the leading edge. Gross margin 59.5% and net margin 45.7% (3Q25) are the reference anchors for whether competitors can justify their own foundry economics -- Samsung Foundry and Intel 18A are both structurally behind on yield and utilization at equivalent nodes.

Leading-edge utilization above 95% signals capacity-constrained pricing power (pricing up); utilization falling below 85% at advanced nodes signals demand softness one to two quarters ahead of revenue prints. Capex intensity (capex as % of sales) for TSMC runs 35-45%; a sharp decline flags cycle-top caution.

### 5.2 HBM yield and capacity (Samsung, SK Hynix, Micron)

High-Bandwidth Memory (HBM) is the critical bottleneck for AI accelerators. Three suppliers matter: [SK hynix Q3 2025 financial results](https://news.skhynix.com/sk-hynix-announces-3q25-financial-results/) show record revenue KRW 24.45T driven by HBM3E shipments and HBM4 mass-production ramp; [Samsung Q4 2025 results](https://news.samsung.com/global/samsung-electronics-announces-fourth-quarter-and-fy-2025-results) report record revenue KRW 93.8T with DS Division driven by HBM and DRAM pricing; and [Micron's December 2025 10-Q](https://investors.micron.com/static-files/502c03ac-dd06-4c88-9441-02ebfe6ff6fa) announced establishment of the Cloud Memory Business Unit (CMBU) dedicated to HBM for all data-center customers.

Competitive dynamics: SK Hynix is the HBM incumbent with NVIDIA design-in on H100/H200/Blackwell; Samsung has struggled with HBM3E qualification timelines at NVIDIA and is catching up at HBM4; Micron entered late but has executed an accelerating ramp. HBM yield is the single most predictive metric for Q+2 and Q+3 supplier revenue; yield below 60% for a given stack configuration constrains supply and transfers margin to the tightest supplier.

### 5.3 CoWoS advanced packaging

CoWoS (Chip-on-Wafer-on-Substrate) is the TSMC-proprietary advanced-packaging process that binds GPU compute die to HBM stacks on a silicon interposer. [SemiAnalysis (Patel, Xie and Wong 2023)](https://semianalysis.com/2023/07/26/ai-expansion-supply-chain-analysis/) is the canonical analysis of why CoWoS is the binding constraint on NVIDIA shipments: even with sufficient compute die and HBM, CoWoS interposer throughput caps total system output. TSMC's CoWoS capacity has roughly doubled annually from 2023 through 2026; the metric matters because NVIDIA's data-center-segment revenue print is a direct function of CoWoS units, and any deceleration in CoWoS capacity expansion is a three-quarter leading indicator for NVDA top-line.

### 5.4 Book-to-bill and cycle indicators

The [SEMI equipment-billings release](https://www.semi.org/en/SEMI-Reports-Global-Semiconductor-Equipment-Billings-Reached-135-Billion-in-2025) reported record $135B global semiconductor-equipment billings in 2025 (+15% YoY). [SIA/WSTS data](https://www.semiconductors.org/global-annual-semiconductor-sales-increase-25-6-to-791-7-billion-in-2025/) reports 2025 global semi sales of $791.7B (+25.6%), with 2026 projected near $1T. [Gartner's April 2026 forecast](https://www.gartner.com/en/newsroom/press-releases/2026-04-08-gartner-forecasts-worldwide-semiconductor-revenue-to-exceed-us-dollars-one-point-3-trillion-in-2026) projects 2026 revenue exceeding $1.3T, driven by DRAM (+125%) and NAND (+234%) -- the "memflation" inflection -- which matters for memory and storage names.

ASML's Q3 2025 results ([ASML Press Release](https://www.asml.com/en/news/press-releases/2025/q3-2025-financial-results)) posted EUR 7.5B in sales with EUR 5.4B in net bookings (EUR 3.6B EUV), signaling continued demand at the lithography layer. Applied Materials' [FY2025 results](https://ir.appliedmaterials.com/news-releases/news-release-details/applied-materials-announces-fourth-quarter-and-fiscal-year-2025) report record $28.37B revenue with explicit management commentary on HBM and advanced-packaging WFE growth. Book-to-bill below 1.0 for two consecutive quarters historically precedes revenue downturns at equipment names (LRCX, AMAT, KLAC) by two to three quarters; above 1.1 sustained supports durable upgrade cycles. The [NVIDIA FY2025 10-K](https://www.sec.gov/Archives/edgar/data/0001045810/000104581025000023/nvda-20250126.htm) is the reference primary source for data-center-segment growth at the system level.

Cross-referencing on-chain (HBM, CoWoS, EUV bookings, WFE billings) provides a three-quarter lead on AI-infrastructure names' revenue guidance -- the signal institutional desks monetize.

## 6. Canonical analysis-file output contract (Phase K)

### 6.1 Frontmatter schema

Every Phase K analysis file emits canonical YAML frontmatter. Confidence and conviction are separated (Section 10). The trigger field carries the Kill Criteria (Section 12) inline so downstream ingestion retains the thesis-drift watch list.

```yaml
---
categories: [atlas]
type: analysis
subtype: equity | etf | crypto
ticker: NVDA
created: 2026-04-22
updated: 2026-04-22
as_of: 2026-04-22
price_asof: 875.43
conviction: 75
confidence: 72
confidence_cap_reason: "Grade-A primary filings; 1 STALE estimate"
rr_ratio: 3.4
position_size_pct: 4.2
hold_band: "[12.5, -8.0] pct vs price_asof through +63 trading days (HOLD ratings ONLY; omit for BUY/SELL)"
scoring_path: positive-eps-standard
topology: dw
orchestrator_model: "<active model string; passive log, never branched on>"
thesis: theme-alpha
thesis_refs:
  - "thesis-theme-alpha"
  - "[[ref-theme-alpha]]"
variant_view: "Consensus expects FY27 DC revenue +28%; base case +42% on CoWoS step-up"
mispricing: "Market discounting 2H26 China export-control downside at 60% probability; base case 35%"
trigger:
  - "DC revenue growth <25% YoY for 2 consecutive quarters -> reduce"
  - "HBM3E qualification gap vs SK Hynix closes to <1 quarter -> reassess moat"
  - "CoWoS capacity growth <40% annual -> trim"
tags:
  - ticker/NVDA
  - thesis/theme-alpha
related:
  - "TSM"
  - "MU"
  - "ASML"
---
```

The frontmatter is machine-parseable. `confidence_cap_reason` documents the Pre-Output-Gate (Section 7) cap logic explicitly -- never silent. `rr_ratio` is the asymmetric-payoff ratio required >=3.0 for standard theses. `thesis` is a single slug for primary routing; `thesis_refs` carries the full wikilink list. `trigger` is a flat list of quantified Kill-Criteria lines.

#### 6.1.1 Kernel field set (INVEST KERNEL 2026-07-06; practice-authoritative corrections)

Two PRACTICE-DRIFT corrections to the example above, ratified by observed convention across the live analyses corpus: (a) `categories: [wiki]`, NOT `[atlas]` (analyses live in wiki/investing/analyses/); (b) `trigger:` in practice carries WHAT PROMPTED THE RUN (a short string -- earnings / catalyst / user request), and the quantified invalidation thresholds live in the kernel field `kill_criteria:` (list). The example's `trigger:`-as-kill-list usage is superseded.

MANDATORY kernel fields on every full-run analysis from 2026-07-06 (enforced by /invest Pre-Output items 10b/10d + `tools/sizing-eval.py --check`; legacy analyses are NOT backfilled -- J.5.6 has an exact fallback):

| Field | Content |
|---|---|
| `rating` | STRONG BUY..STRONG SELL / NR -- mirrors the TRADING DECISION header verbatim |
| `price_at_analysis` | the regular_market_close used for all threshold math (J.0b anchor) |
| `rr_ratio` | "X.XX:1" string from the Decision Sheet |
| `position_size_pct` | worksheet final % of book; null unless BINDING SIZE-OK |
| `doctrine_version` | "pd-<v>/fb-<v>" from Phase D.8 |
| `doctrine_fingerprint` | "pd-`<hex8>`/fb-`<hex8>`" from Phase D.8 (tamper-evidence stamp) |
| `deployment_band` | the `<state>:<multiplier>` stamp emitted by the kernel, e.g. "normal:1.0", "rate-shock-caution:0.5", "vix-throttle:0.5", "halt-vix-tail:0.0", "unknown-treated-halted:0.0" |
| `deployment_override` | bool -- the conviction override lane was lawfully invoked |
| `gate_f` | GATE-F sheet path (10a), or null when no action verdict |
| `kill_criteria` | list of quantified invalidation triggers (K.5 Step 3) |
| `thesis_line` | ONE sentence thesis summary (body keeps the 2-3 sentence statement) |

These fields make the analysis file the machine-readable THESIS NOTE: J.5.6 scoreboards read them mechanically, `wiki/investing/journal.base` indexes them, and GATE-F consumes `gate_f`/analysis dates.

#### 6.1.2 `target_model_inputs` -- fundamentals-FV target disclosure (2026-07-30)

MANDATORY whenever a fundamentals-fair-value valuation GOVERNS the R/R target -- i.e. `scoring_path: negative-eps-bridge`, OR EV/Sales > 50x (the two states in which `ref-scoring-models` Section 10.4 sets the target as MIN(analyst median, fundamentals FV)). The formula's execution haircut is the single largest free parameter in the buy decision on a pre-profit name; undisclosed, it silently decides buyability and cannot be audited across runs.

Current-use correction (2026-09-13): the superseded revenue-times-margin recipe
is dimensionally incomplete. Use a supported capitalized valuation with explicit
reinvestment, taxes, terminal economics and enterprise-to-equity reconciliation.
The existing 40/55/70 sensitivities are historical scenario assumptions, not
calibrated probabilities. Extend the method disclosure with the actual valuation
packet and equity bridge. If required inputs are unavailable, retain them as
missing and withhold the target and dependent R/R; do not fabricate fields to
satisfy this template. Ratified routing, composite weights and gates are unchanged.

```yaml
target_model_inputs:
  method: "<one-line formula citation (ref-scoring-models 10.4)>"
  forward_revenue_musd: <float>
  forward_revenue_basis: "<quote + grade + source + date>"
  normalized_op_margin_pct: <float>
  execution_haircut_pct: <int>
  derisk_test: "<adjudication of the 'unless signed contracts de-risk' clause -- see R4-D2>"
  wacc_pct: <float>
  projected_shares_m: <float>
  fv_output: <float>
  haircut_sensitivity: {at_40pct: <float>, at_55pct: <float>, at_70pct: <float>}
  min_rule_applied: <bool>
  analyst_median: <float or null + prov note>
  sizing_target: <float>
  target_state: LIVE | TARGET-EXHAUSTED
```

- **R4-D1 disclosure mandatory.** Every field populated. `analyst_median` is the ONLY field that may be null, and only with a prov note stating why (no coverage / source unavailable). No field reads "n/a" or "TBD" while the formula governs.
- **R4-D2 de-risk adjudication.** Whenever contracted backlog + customer prepayments >= 1.0x TTM revenue, `derisk_test` MUST adjudicate the formula's "unless signed contracts de-risk" clause EITHER DIRECTION, citing a primary source. Silence is not a default: an unadjudicated trigger HALTs.
- **R4-D3 sensitivity.** `haircut_sensitivity` reports FV at 40 / 55 / 70 percent execution haircut. That spread IS the honest uncertainty band on the target and is quoted wherever the target is quoted.
- **R4-D4 TARGET-EXHAUSTED.** When `sizing_target <= entry` the target is SPENT, not FAILED. Then: `rr_ratio` reads `TARGET-EXHAUSTED`; the TRADING DECISION Risk/Reward line reads `TARGET-EXHAUSTED (sizing target $X <= price $Y; R/R undefined, not failed)`; the rating rationale MUST rest on composite / gates / solvency and may NEVER say "R/R fails"; the calibration-monitor R/R cell carries `TARGET-EXHAUSTED`.
- **R4-D5 method review.** Three consecutive TARGET-EXHAUSTED analyses on one ticker force a Phase P follow-up line proposing a /decide. The question adjudicated there is method-vs-coverage (is the FV model too tight, or is the name genuinely out of upside?) -- never "raise the target."

The MIN target rule and the 3:1 / 4:1 R/R hurdles are UNCHANGED by this contract: it discloses inputs, it never moves a threshold.

#### 6.1.3 `watch_zone` -- minimal pre-registered entry zone (2026-07-30)

Optional frontmatter block, written whenever an analysis SETS or KEEPS a WATCH zone:

```yaml
watch_zone:
  low: <float>
  high: <float>
  basis: "<what anchors the zone -- support level, FV discount, prior-lot basis>"
  set_on: <ISO date>
  expiry: <ISO date>
  zone_prior: {low: <float>, high: <float>, set_by: <analysis stem>} | null
  zone_move_reason: "<MANDATORY non-empty justification when the zone moved vs zone_prior in the SAME DIRECTION as price by >= 10% (anti-chase); else 'unchanged' or the reason>"
```

Exactly TWO read-only consumers, both marker/display level:

1. The GATE-F `zone_preregistered` marker (`tools/gate-rules.json`, rule 1b) -- reads `set_on` age (>= 14d), bounds stability since `set_on`, and entry-from-above.
2. The /brief Optionality Map -- ONE display line: `<TICKER> watch zone <low>-<high> (set <date>, expires <date>); spot <px> <inside|above|below>`.

There is NO evaluator, NO five-state machinery, and NO artifact cascade. That design was CUT on evidence: the daily-evaluator host ran 13 of 21 July trading days (62% uptime, dark through part of the test window) and the live in-vault alert experiment converted at zero (red-team adjudication 2026-07-30, `wiki/research/redteam-invest-overhaul-2026-07-30.md` Part 2 B-3 / M-4). The block exists to be READ, not to fire.

### 6.2 25-section body skeleton

The body emits a twenty-five-section skeleton. Each section has a declared purpose, content requirements, word-count guidance, and an institutional-format precedent. The template is the output contract; deviations must be explicit and justified in the section itself.

| # | Section | Purpose | Words | Precedent |
|---|---------|---------|-------|-----------|
| 1 | Decision Sheet | One-screen BUY/HOLD/TRIM/SELL + size + R:R + confidence + conviction | 120-180 | PDB-BLUF |
| 2 | Thesis Statement | One paragraph stating the core mispricing | 100-150 | Hedge fund morning note |
| 3 | Variant View | Explicit differentiation from consensus | 80-140 | Sell-side IC |
| 4 | Mispricing Decomposition | Why the market is wrong, in factor terms | 150-220 | Mauboussin Expectations Investing |
| 5 | Business Model | Revenue mix, unit economics, customers | 200-300 | Measuring the Moat |
| 6 | Competitive Position | Moat sources, durability, threats | 200-300 | Porter + Mauboussin |
| 7 | Industry Structure | TAM, growth, cyclicality, concentration | 150-220 | Gartner/SIA anchor |
| 8 | Management Assessment | Track record, capital-allocation grade | 120-180 | 2.8 scorecard |
| 9 | Valuation | Multi-method (DCF, multiples, reverse) | 250-350 | Damodaran |
| 10 | Scenarios | Bull/Base/Bear with quantified drivers | 200-300 | Rappaport |
| 11 | Forensic Screen | M-Score, F-Score, Z-Score, accruals | 150-220 | Section 2.6 |
| 12 | Quality Scorecard | ROIC-WACC, Piotroski, margin trend | 120-180 | Section 2.2 |
| 13 | Capital Allocation | 5Y history + scorecard grade | 150-220 | Section 2.8 |
| 14 | Growth Decomposition | Organic vs M&A vs price vs volume | 120-180 | Section 2.3 |
| 15 | Balance Sheet | Leverage, coverage, maturity ladder | 100-150 | Section 2.4 |
| 16 | Factor Exposure | For ETFs: FF5+Mom+QMJ loadings; for stocks: style tilt | 120-180 | Fama-French / AQR |
| 17 | Catalysts | Next 12mo, with probability and direction | 150-220 | Hedge fund memo |
| 18 | Risks | Quantified downside by driver | 200-300 | Chanos |
| 19 | Kill Criteria | Specific thresholds + actions | 100-150 | Section 12 |
| 20 | Position Sizing | KERNEL worksheet (2026-07-06): the `kernel:sizing` block + rendered lines emitted by `tools/sizing-eval.py --compute`, pasted VERBATIM (BINDING on BUY/STRONG BUY Initiate/Add; HOLD-STATE panel on held names; procedure in ref-kernel-sizing.md). Never hand arithmetic | 120-180 | Kelly/Thorp + gate-kit |
| 21 | Entry/Exit Plan | Price, timing, tranching | 80-140 | Practitioner |
| 22 | Monitoring Checklist | What to track, frequency, source | 100-150 | |
| 23 | Contradictory Sources | Steel-manned opposing case with citations | 150-220 | Tetlock |
| 24 | Open Questions | Known unknowns, unresolved diligence | 80-140 | |
| 25 | INGEST:claims | Marker-signature coordination block (Section 8) | variable | Pattern 18 |

Total body target: 3,500-5,000 words for a standard equity analysis; ETFs can compress to 2,500 (fewer forensic/capital-allocation sections) and complex AI-infrastructure deep dives can extend to 7,000. The 25-section skeleton is exhaustive but not every section applies to every security; ETF analyses collapse 11-13 (forensic/quality/capital-allocation) into a single "fund quality" paragraph. Crypto analyses replace 9-15 with tokenomics, on-chain, staking, regulatory, and standards-alignment blocks (Section 4).

[CFA Institute (2010) How to Write a Great Research Report](https://rpc.cfainstitute.org/research/cfa-magazine/2010/how-to-write-a-great-research-report) is the practitioner reference; the 25-section skeleton extends the CFA baseline with forensic, INGEST, and Kill-Criteria sections that single-analyst compounding-knowledge workflows require.

### 6.3 Three embedded chart contracts

Analysis files embed three charts. All use Obsidian chart-plugin syntax. The contracts are fixed for parser stability across analyses.

```markdown
:::chart:bar
title: Valuation vs sector median (NVDA)
x: [P/E NTM, EV/EBITDA NTM, P/S TTM, FCF yield, PEG]
series:
  - name: NVDA
    data: [34.2, 26.1, 18.4, 2.1, 1.2]
  - name: Sector median
    data: [22.5, 14.8, 6.3, 3.8, 1.6]
:::
```

```markdown
:::chart:radar
title: Risk profile (NVDA, 0-10 scale, higher = more risk)
axes: [Customer concentration, Regulatory, Cycle, Valuation, Supply chain, Execution]
data: [7, 6, 5, 8, 6, 3]
:::
```

```markdown
:::chart:doughnut
title: ETF allocation -- VGT top-10
labels: [NVDA, MSFT, AAPL, AVGO, ORCL, CRM, CSCO, ADBE, AMD, ACN, Other]
data: [15.2, 14.1, 13.8, 5.4, 3.2, 2.8, 2.1, 2.0, 1.9, 1.7, 37.8]
:::
```

The bar contract is used in stock analyses (section 9 Valuation). The radar is used in all analyses (section 18 Risks). The doughnut is used in ETF analyses (section 16 Factor Exposure / Concentration). Chart rendering is client-side in Obsidian; the data block is the contract, not the rendered image.

### 6.4 Short-interest + options-flow output contract (relocated from SKILL.md Phase H.2, 2026-07-11) + OPTIONS-BLOCK insertion point

Phase H.2 executes against this contract (SKILL.md keeps a two-line pointer).

**H.2.1 -- Short-interest deepening:**
- Short interest % of float; days-to-cover (SI / avg daily volume).
- Threshold logic: >10% SI + <2 days-to-cover = squeeze-risk flag (potential
  stress signal); >10% SI + >5 days-to-cover = legitimate-bear-thesis worth
  investigating; <5% normal.
- Trend (4-week change in SI): rising = bear thesis strengthening; falling =
  bear thesis fading.

**H.2.2 -- Options-flow analysis (INTELLIGENCE layer -- reads positioning;
distinct from the ref-options-layer STRUCTURE layer, which recommends trades):**
- Put/call ratio by expiration window: 0-30 DTE vs 30-90 DTE asymmetry; rising
  0-30 DTE put demand = hedging-demand signal (downside priced); rising
  long-dated calls = speculative-bull positioning.
- IV term structure: upward-sloping = tail risk priced; downward-sloping =
  inverted, often pre-event positioning (earnings, FDA, M&A rumor).
- Unusual activity: >$500K notional blocks, sweep orders, late-day prints.
- Gamma concentration: strikes with >1% of total open interest (pinning
  potential into expiration).
- Sourcing note (2026-07-11): where the broker option read tools are
  loaded for Phase K-ter, prefer their quotes (IV, OI, volume per contract;
  `prov: mcp:robinhood`) over web aggregators for these reads.

**H.2.3 -- Cross-check with Phase J-bis insider data:** short interest +
insider cluster-buy = high-conviction divergence (often resolves in the
insiders' direction); short interest + insider selling = aligned bearish
signal worth heavy Decision-Sheet weight.

**OPTIONS-BLOCK insertion point.** The Phase K-ter options-structure
recommendation block (full output contract: `ref-options-layer.md`) renders as
a SUBSECTION of body section 21 (Entry/Exit Plan) -- options structures ARE
entry/exit vehicles -- delimited by:

```markdown
<!-- OPTIONS-BLOCK insertion point (Phase K-ter; contract in ref-options-layer.md) -->
```

It is NEVER a 26th body section (the 25-section skeleton in 6.2 is frozen),
and it never renders inside body section 20 (the kernel worksheet block there
is parsed by `sizing-eval.py --check`; foreign content risks a parser HALT).

## 7. Pre-Output 10-point HALT gate

The HALT gate is executed after Phase K body compose but before the Write tool emits the file. Any gate failure halts output and requires remediation. The ten gates are listed below; items 1-7 are detailed in subsections. Items 8-10 are process-mechanical (no orphan wikilinks emitted; frontmatter parses; file is atomic-write-safe via temp-then-rename).

### 7.1 Evidence-grade confidence cap methodology

The legacy confidence score is capped by evidence-grade composition. These are existing local policy ceilings on an evidence-constrained judgment score, not empirically demonstrated probability-calibration coefficients. The previously asserted 30-40% performance advantage and empirical derivation of these exact caps are unsupported here. Preserve the numerical caps and their owning ratification; changing their values requires the existing policy process.

| Condition | Confidence cap |
|-----------|----------------|
| >30% of cited claims are Grade C | 70% |
| Any claim is Grade D (sentiment-only) | 60% |
| Any claim is Grade F (unverifiable) | Auto-HALT; remove or downgrade |
| >2 claims are STALE (>90 days) | 65% |
| No contradictory source cited | 75% |
| All Grade A/B and FRESH | No cap (analyst judgment binds) |

Apply all caps by taking their minimum. A thesis with 35% Grade-C claims AND 3 STALE claims AND no contradictory source is capped at min(70, 65, 75) = 65 on the legacy 0-100 scale. The `confidence_cap_reason` frontmatter field documents which binding constraint was active. Satisfying a ceiling does not establish forecast calibration.

### 7.2 Portfolio math arithmetic mandate

Portfolio math reads actual share counts from current-session broker read evidence across the stated account/asset scope. Saved or user-provided position files cannot verify current quantities; missing scope is UNVERIFIED. No estimates. No "approximately." The gate recomputes position_size_pct from shares * price / portfolio_total and fails if the emitted number deviates by >0.1 percentage points. This catches the common LLM failure mode of anchoring on a plausible-looking round number rather than executing the arithmetic.

### 7.3 Temporal anchoring requirements

Every cited claim carries an ISO-8601 date (YYYY-MM-DD) or a quarter form (YYYY-QN). Freshness is computed as today - date. The freshness buckets are FRESH (< 7 days), RECENT (7-30 days), DATED (30-90 days), STALE (> 90 days). A claim with no date is treated as STALE and explicitly flagged. STALE data auto-downgrades the evidence letter-grade by one tier (Section 9.4). Undated claims trigger Gate 3 failure and halt output.

### 7.4 Risk/Reward 3:1 institutional hurdle

Standard theses require R:R >= 3.0, computed as (price-target - current-price) / (current-price - kill-stop) for long theses. The 3:1 hurdle is the institutional baseline because at 40-50% hit rates (realistic for active equity), anything below 3:1 has negative expected value after trading costs and taxes. [Kelly (1956)](https://www.princeton.edu/~wbialek/rome/refs/kelly_56.pdf) and [Thorp (2006)](https://gwern.net/doc/statistics/decision/2006-thorp.pdf) formalize the log-wealth-growth derivation.

Alternatives: asymmetric-payoff theses (bankruptcy-call options, catalyst-driven special situations) can deploy >=5:1 with lower hit rates; barbell theses (broad index + concentrated convex single-names) use aggregate R:R at the portfolio level. [Ed Seykota's risk rules](https://www.seykota.com/tribe/risk/index.htm) operationalize the "risk <1% per trade, <10% liquid net worth in speculation" rule-of-thumb that underlies the sizing discipline in Section 6.1's `position_size_pct`.

#### 7.4.1 `rr_inputs` bracket contract + STOP-BREACHED (2026-07-30)

Every analysis that publishes an `rr_ratio` carries the bracket that produced it, in frontmatter. An R/R with no visible bracket cannot be audited, re-used, or invalidated -- and a ratio quoted forward out of a dead bracket is the most expensive stale number this skill emits.

```yaml
rr_inputs:
  entry: <float>            # the price the ratio was computed from
  stop: <float>
  target: <float>
  stop_basis: "<what sets the stop -- cycle-reversion low, 63s ATR multiple, thesis-kill level>"
  target_basis: "<what sets the target -- e.g. MIN(analyst median, fundamentals FV) per 10.4>"
  computed_at: <ISO date>
  price_basis: "<regular_market_close YYYY-MM-DD | mcp:robinhood ...>"
```

MANDATORY on every analysis that publishes an `rr_ratio` (enforced at Pre-Output item 10k). ONE validity rule governs the bracket:

**STOP-BREACHED.** If the current price is at or below `rr_inputs.stop`, the bracket is STOP-BREACHED. The prior R/R is VOID: it may not be cited as a rating basis or a rejection basis ANYWHERE (analyses, briefings, screens, decision records), and recomputation is FORBIDDEN -- re-anchoring a dead bracket to the new lower entry is precisely the motion that manufactures a passing ratio out of a thesis that just failed its own stop. A fresh /invest run is MANDATORY before any R/R claim on that name.

There is deliberately NO symmetric percent band and NO age clock. At measured 63-session vols on high-volatility names any tight band fires roughly every other day, forcing 3-6 full re-runs per week at ~1M tokens each; and upward staleness is self-correcting, because price closing on a fixed target yields a SHRINKING ratio that fails the 3:1 hurdle on its own arithmetic (red-team adjudication 2026-07-30, `wiki/research/redteam-invest-overhaul-2026-07-30.md` Part 2 M-5).

### 7.5 Kill Criteria quantification rules

Kill Criteria are specific-metric + specific-threshold + specific-action. Vague language (e.g., "if fundamentals deteriorate," "if thesis breaks") fails the gate. Required form: "`<metric>` `<operator>` `<threshold>` for `<duration>` -> `<action>`." Examples: "DC revenue YoY < 25% for 2 consecutive quarters -> reduce by half"; "gross margin contracts > 300 bps sequentially with capex accelerating -> exit." Leading indicators (HBM qualification gap, CoWoS capacity growth) are preferred over lagging (reported revenue). Section 12 catalogs best practices.

### 7.6 Variant View discipline

The Variant View section must state an explicit differentiated view from consensus, OR state that no differentiation exists and the thesis rests on execution of the consensus view. Reflexive contrarianism (claiming a differentiated view without factual grounding) fails the gate. The check: the analyst must be able to cite the consensus number (source: sell-side aggregator or explicit citation) AND the differentiated number AND the specific mechanism that drives the gap. Absence of any of the three triggers remediation.

### 7.7 Contradictory source requirement

At least one source presenting the opposing case must be cited and steel-manned in Section 23 of the body. Engage the strongest supported opposing argument and identify what would falsify the preferred conclusion. This is an existing local challenge requirement; this reference does not establish that it is universally the largest source of forecasting improvement. Absence of a contradictory source retains the existing 75% confidence-score cap and remediation requirement before accepted output.

## 8. INGEST:claims coordination block (Pattern 18)

Pattern 18 is the coordination mechanism that lets a single analysis file feed structured claims into cross-entity knowledge-base files without LLM-variance dedup failure. The block appears as Section 25 of the body.

### 8.1 Marker-signature format

Each claim is an eight-tuple (vNEXT 2026-06-09; was seven): `(entity, metric_slug, value, date, grade, section, text, prov)`. The signature for dedup purposes is UNCHANGED -- the first four fields: `(entity, metric_slug, value, date)`. Text varies across LLM runs; value-date-metric-entity is stable. The 8th field `prov` carries machine provenance: `mcp:<server>:<key> | script:yfinance | web:<domain>+<grade>` (spec: ref-dw-topology.md Section 7; enforced by the Wave-3 provenance skeptic + vault-audit X8 SOFT advisory on analyses created >= 2026-06-10; legacy 7-field claims remain parseable -- prov is pass-through additive). The block is emitted as a fenced code block with YAML dictionary per claim.

```yaml
:::ingest:claims
- entity: NVDA
  metric: dc-revenue-yoy
  value: 0.427
  date: 2026-Q1
  grade: A
  section: financial-signals
  text: "Data-center revenue grew 42.7% YoY in FY2026-Q1 per 10-Q."
  source: "https://sec.gov/..."
- entity: NVDA
  metric: gross-margin-gaap
  value: 0.751
  date: 2026-Q1
  grade: A
  section: financial-signals
  text: "GAAP gross margin 75.1% in FY2026-Q1."
  source: "https://sec.gov/..."
- entity: TSM
  metric: cowos-capacity-growth-annual
  value: 1.95
  date: 2026-Q1
  grade: B
  section: catalysts
  text: "CoWoS capacity roughly doubled 2025-2026 per TSMC IR commentary."
  source: "https://investor.tsmc.com/..."
:::
```

### 8.2 Normalization rules

Entity stem is UPPER for tickers (NVDA, not Nvda); for crypto, the ticker symbol in UPPER (XRP, BTC); for companies without a ticker, the canonical slug (e.g., OPENAI). Metric slug is lowercase-kebab from a controlled dictionary (dc-revenue-yoy, gross-margin-gaap, roic-ex-cash, hbm-qualification-gap-qtrs, cowos-capacity-growth-annual, nvt-ratio, mvrv, staking-yield-net). New metrics require a one-line dictionary addition in the same file (inline convention: `# metric:new-slug-name :: one-line definition`).

Value scale-equivalence: percentages stored as decimals (0.427, not "42.7%"), currency stored as base-unit numeric with implicit USD (1134100000000 for NT$1.134T converted), ratios as decimals (3.4, not "3.4x"). Date is ISO (YYYY-MM-DD) for point-in-time and quarter form (YYYY-QN) for period metrics.

### 8.3 Section-target taxonomy

The `section` field routes the claim into a target section in the cross-entity file. The five-section taxonomy aligns with `/ingest` v2 final semantics:

- **financial-signals** -- quantified fundamentals (revenue, margin, ROIC, etc.)
- **thesis-fit** -- how the claim strengthens or weakens a specific thesis
- **risks** -- downside drivers with quantification
- **catalysts** -- forward-looking events with date and direction
- **recent** -- news, announcements, datapoints within last 30 days

Routing is deterministic on the section field. A single claim is emitted once; duplicate claims within a run are rejected by the marker-signature check before emit.

### 8.4 LLM-variance-resistant dedup mechanics

Text-match dedup fails because LLMs phrase the same fact differently across runs ("revenue grew 42.7%" vs "top-line up 42.7% year-on-year" vs "FY26-Q1 revenue growth was 42.7%"). The marker-signature tuple (entity, metric_slug, value, date) is stable across phrasings. Downstream `/ingest` computes the hash of the signature and treats collisions as supersede-candidates, not duplicates.

Supersede annotation format: when a newer claim supersedes an older one (same entity + metric, different date or value), the newer claim carries `supersedes: <old_signature_hash>` and the older claim is marked stale in the target file without removal. This preserves audit trail.

### 8.5 Worked example block -- hypothetical NVDA analysis

The following block illustrates five-to-ten claims across three entities (NVDA, TSM, MU) for a hypothetical NVDA analysis. The entities are coupled because NVDA's thesis depends on TSM (CoWoS) and MU (HBM) execution.

```yaml
:::ingest:claims
- entity: NVDA
  metric: dc-revenue-yoy
  value: 0.427
  date: 2026-Q1
  grade: A
  section: financial-signals
  text: "Data-center segment grew 42.7% YoY per FY2026-Q1 10-Q."
- entity: NVDA
  metric: gross-margin-gaap
  value: 0.751
  date: 2026-Q1
  grade: A
  section: financial-signals
  text: "GAAP gross margin 75.1%; non-GAAP 76.8%."
- entity: NVDA
  metric: roic-ex-cash
  value: 1.12
  date: 2026-Q1
  grade: A
  section: financial-signals
  text: "ROIC ex-cash 112% on NOPAT over invested capital; structural outlier."
- entity: NVDA
  metric: customer-concentration-top10
  value: 0.52
  date: 2026-Q1
  grade: A
  section: risks
  text: "Top-10 customers 52% of DC revenue; hyperscaler capex sensitivity dominant."
- entity: TSM
  metric: cowos-capacity-growth-annual
  value: 1.95
  date: 2026-Q1
  grade: B
  section: catalysts
  text: "CoWoS capacity roughly doubled YoY; supply-side relief for NVDA."
- entity: TSM
  metric: n3-utilization
  value: 0.96
  date: 2026-Q1
  grade: B
  section: financial-signals
  text: "N3 node at ~96% utilization; pricing power signal."
- entity: MU
  metric: hbm3e-qualification-status
  value: 1
  date: 2026-Q1
  grade: B
  section: catalysts
  text: "HBM3E qualified at NVIDIA; ramp underway."
- entity: MU
  metric: dram-yoy-price
  value: 1.25
  date: 2026-Q1
  grade: B
  section: financial-signals
  text: "DRAM pricing +125% YoY per Gartner 2026 semi forecast."
- entity: NVDA
  metric: china-export-control-revenue-exposure
  value: 0.12
  date: 2026-Q1
  grade: C
  section: risks
  text: "China DC revenue ~12% of segment; restriction tightening risk."
- entity: NVDA
  metric: consensus-fy27-dc-growth
  value: 0.28
  date: 2026-04-15
  grade: C
  section: thesis-fit
  text: "Consensus FY27 DC growth +28%; variant-view base case +42%."
:::
```

The block is parseable, dedup-safe across runs, and routes each claim to the correct section in NVDA.md, TSM.md, and MU.md files at `/ingest` time. Cross-entity coupling (NVDA dependence on TSM and MU) becomes structurally navigable.

## 9. Evidence grading and temporal anchoring

### 9.1 Grade A-F tier hierarchy

| Grade | Source class | Examples |
|-------|--------------|----------|
| A | Primary filings, audited financials | 10-K, 10-Q, 20-F, 8-K, DEF 14A, proxy, SEC Schedule 13D/G/F |
| B | Tier-1 institutional data, industry primary | TSMC IR quarterly, Gartner/IDC press releases, SIA/WSTS data, messaging-standard RA page |
| C | Industry-analytical third party | Sell-side research (attributed), SemiAnalysis, Coin Metrics, Glassnode methodology pieces |
| D | Sentiment, commentary, unverified practitioner | Twitter/X posts, conference transcripts without recording, blog claims without data |
| F | Unverifiable, rumor, anonymous | Message boards, "sources say" without named attribution |

[SEC EDGAR Full-Text Search](https://www.sec.gov/edgar/search/) is the authoritative source for Grade A in US public markets; [Investor.gov Form 10-K overview](https://www.investor.gov/introduction-investing/investing-basics/glossary/form-10-k) and the [SEC 13F FAQ](https://www.sec.gov/rules-regulations/staff-guidance/division-investment-management-frequently-asked-questions/frequently-asked-questions-about-form-13f) are the reference descriptions. [SEC Schedules 13D and 13G](https://www.investor.gov/introduction-investing/investing-basics/glossary/schedules-13d-and-13g) provide the beneficial-ownership primary sources, [FASB ASC 606](https://storage.fasb.org/ASU%202014-09_Section%20A.pdf) provides the revenue-recognition GAAP basis, and [SEC Regulation G](https://www.sec.gov/rules-regulations/2003/03/conditions-use-non-gaap-financial-measures) governs non-GAAP reconciliations that must appear in Grade-A citations.

### 9.2 Inline attribution format

Every material claim carries an inline attribution in the form `[Grade <letter> | <source short name> | <ISO-date>]`. Example: "Data-center revenue grew 42.7% YoY [Grade A | NVDA 10-Q FY26Q1 | 2026-02-26]." The format is parseable and frontmatter-extractable; it supports the INGEST:claims block emission in Section 8.

### 9.3 Freshness grade computation

Freshness is today minus cited-date: FRESH (< 7d), RECENT (7-30d), DATED (30-90d), STALE (> 90d). The freshness label is optional in inline attribution but mandatory in INGEST:claims routing. Claims without a date default to STALE with explicit flag.

### 9.4 Auto-downgrade rule

STALE status downgrades the evidence letter by one tier: Grade A + STALE emits as effective Grade B; Grade B + STALE emits as effective Grade C. The cascade enforces recency discipline: a year-old 10-K number loses Grade-A authority relative to a current 10-Q number. Grade D + STALE downgrades to Grade F and is auto-removed from INGEST:claims emission.

### 9.5 Handling of missing dates

Undated claims are treated as STALE and flagged inline: "[Grade ? | source | DATE MISSING]." The Pre-Output gate (Section 7.3) fails on any DATE MISSING flag in material claims (those driving valuation, scenarios, or Kill Criteria). Non-material claims (contextual color) may retain the flag with explicit acknowledgment but do not enter INGEST:claims.

## 10. Confidence vs conviction (calibration)

### 10.1 Confidence -- evidence-constrained judgment

Confidence describes evidence quality and uncertainty. Use HIGH/MED/LOW with reasons and an observable condition that would change the judgment. When maintaining the legacy numeric field, label it an uncalibrated judgment score out of 100 and apply Section 7.1 caps. It is not the probability that a whole thesis is factually correct. A separately reported probability needs a defined outcome, horizon, reference population, dated calibration method, sample size and limitations. Missing support remains explicit; never manufacture a percentage to complete a template.

### 10.2 Conviction -- actionable strength

Conviction is the legacy 0-100 recommendation-strength index with rationale. K.5 owns its modulation formula. It is neither a win probability nor a position percentage and never changes the rating, Kelly inputs, Action amount or options mapping by itself. Unsupported required probabilities make point modulation UNAVAILABLE; show missing inputs and, where useful, explicitly assumed sensitivity ranges. Do not substitute an unmodulated value, zero penalty or fabricated probability.

### 10.3 Legitimate divergence patterns

Strong evidence can support a weak opportunity when price already reflects the outcome. Attractive conditional payoff can coexist with weak evidence about whether the condition will occur. Explain this distinction using supported inputs and alternatives. Neither an illustrative payoff nor analyst confidence authorizes a position size; the existing kernel and financial gates own that decision.

### 10.4 Brier score calibration methodology

Brier score is the mean squared difference between a forecast probability and its defined binary outcome. Repeated 0.8 forecasts with 80 successes in 100 observations have an observed success frequency of 0.8 and Brier score 0.16, not zero error or a reliability guarantee. This aggregate alone cannot establish calibration across subgroups or future cases. Preserve forecast timestamps, event definitions, horizons, outcomes, missingness and applicable reference classes. The existing Phase R rating-to-probability map measures its specified return event; it does not validate the confidence or conviction indices. The previous universal 20-40% improvement claim is unsupported here.

### 10.5 Evidence-grade caps codification

The caps in Section 7.1 remain hard constraints on the legacy judgment score. A score of 85/100 with any Grade-D claim fails the existing cap. Record the binding cap in `confidence_cap_reason`; do not relabel a capped score as calibrated probability. If an input needed for a dependent calculation is unavailable, retain supported conclusions and mark that calculation unavailable. Accepted delivery still requires the separate substantive-review gate.

## 11. Institutional memo structure (comparative)

### 11.1 PDB-BLUF structure

The Presidential Daily Brief analog is a Bottom-Line-Up-Front single-page that opens with decision + rationale, followed by supporting detail. The `/invest` Decision Sheet (Section 6 body 1) adopts this structure: first 120-180 words are BUY/HOLD/TRIM/SELL, size, R:R, confidence, and a single-sentence mispricing. A reader who stops after the Decision Sheet has the actionable answer.

### 11.2 Hedge fund morning note format

Morning notes are terse, decision-oriented, and proprietary-catalyst-focused. Typical length: 200-400 words. No industry overview. No valuation DCF. The note assumes the reader already knows the business and asks only: what is new, what does it change, how do we size. [Howard Marks's Oaktree memos](https://www.oaktreecapital.com/insights/memos) are the outside-facing analog; internal hedge-fund notes are stripped further. The `/invest` Thesis Statement + Variant View + Catalysts sections (Sections 2, 3, 17) collectively mirror the morning-note format.

### 11.3 Sell-side initiating coverage

Initiating-coverage reports are long-form (8,000-20,000 words) and cover thesis, business model, industry, competitive position, financial model, valuation (multi-method), catalysts, risks, and management. [CFA Institute's 2010 Research Report standards](https://rpc.cfainstitute.org/research/cfa-magazine/2010/how-to-write-a-great-research-report) document the genre conventions. The 25-section body in Section 6.2 is structurally a compressed initiating-coverage report with forensic, INGEST, and Kill-Criteria additions that single-analyst compounding workflows require.

### 11.4 `/invest` synthesis

`/invest` synthesizes all three: PDB-BLUF in the Decision Sheet, hedge-fund-morning-note terseness in Thesis/Variant/Catalysts, and sell-side-initiating-coverage depth in the body. The file is designed to be re-read at three depths (60 seconds = Decision Sheet; 3 minutes = Thesis + Variant + Catalysts + Kill; 20 minutes = full body). This depth-flexibility is the operational pattern that [Munger's Poor Charlie's Almanack](https://press.stripe.com/poor-charlies-almanack) and Buffett's [annual letters archive](https://www.berkshirehathaway.com/letters/letters.html) have institutionalized in their genres.

## 12. Kill criteria best practices

### 12.1 Specific metric + threshold + action

Every Kill Criterion is a single line of form: `<metric> <op> <threshold> for <duration> -> <action>`. Vague language fails. Examples of acceptable Kill Criteria: "DC revenue YoY < 25% for 2 consecutive quarters -> reduce by 50%"; "CoWoS capacity growth annualized < 40% -> trim 25%"; "HBM3E qualification gap Micron vs SK Hynix > 2 quarters -> exit Micron"; "Piotroski F-Score drops to <= 4 -> reassess thesis and reduce by 25%". The action is always quantified.

### 12.2 Leading vs lagging indicators

Leading indicators (HBM qualification, CoWoS capacity, book-to-bill, on-chain active addresses for crypto) are preferred because they give 1-3 quarter lead time on revenue impact. Lagging indicators (reported revenue, reported margins) only confirm thesis breakage after prices have moved. [SemiAnalysis (2023)](https://semianalysis.com/2023/07/26/ai-expansion-supply-chain-analysis/) documents how CoWoS capacity signals led NVIDIA revenue by two quarters in 2023-2024 and provides the empirical basis for leading-indicator preference.

### 12.3 Thesis-drift monitoring mechanics

Thesis drift occurs when the original thesis fails but the analyst rationalizes the position with a new thesis ("it was a CoWoS-bottleneck thesis; now it is a sovereign-AI-build-out thesis"). The Kill Criteria are anchored to the *original* thesis metrics. Thesis rewrites require a new analysis file (new created date, new trigger list), not an in-place amendment of the Kill Criteria. This is the operational defense against motivated reasoning; [Chanos's 2012 Graham and Doddsville interview](https://medium.com/graham-and-doddsville/jim-chanos-rooting-out-fraud-6eca8e6387ad) documents its failure mode at the institutional level (managers "moving the goalposts" on longs that have broken thesis).

### 12.4 Examples from institutional practice

[Marks's Oaktree memos](https://www.oaktreecapital.com/insights/memos), particularly the representative ["Is It a Bubble?" memo](https://www.oaktreecapital.com/docs/default-source/memos/is-it-a-bubble.pdf?sfvrsn=d4a92866_3), document specific quantified triggers around credit-cycle positioning. [Buffett's 2024 annual letter](https://www.berkshirehathaway.com/letters/2024ltr.pdf) articulates the inverse form (reinforcement criteria: "we continue to own this because X, Y, Z remain true"). [Damodaran's Musings on Markets](https://aswathdamodaran.blogspot.com/) periodically publishes reverse-DCF-implied kill thresholds for specific positions. [Matt Levine's Money Stuff](https://www.bloomberg.com/account/newsletters/money-stuff) is the reference for spotting and interpreting securities-law catalysts that should trigger Kill Criteria review. Collectively these establish that institutional Kill-Criteria practice is quantified, visible, and pre-commitment-based, not after-the-fact justification.

### 12.5 Gate-resolvability -- the `initiation_gates` block (2026-07-30)

Kill criteria answer "when do I get OUT." They carry none of the other half of the pre-commitment: the named conditions standing between today and a FIRST buy. Those were written as prose, inherited silently across runs, and cited as the reason a BUY was blocked long after they had stopped being resolvable inside any horizon the analysis actually held.

`kill_criteria:` stays a FLAT STRING LIST (unchanged). `initiation_gates:` is a parallel, optional, structured block:

```yaml
initiation_gates:
  - id: <short-slug>
    text: "<the condition, quantified>"
    class: blocking | monitoring
    resolvable_by: <ISO date>
    resolution_source: "<the exact artifact that resolves it -- 10-Q, 8-K, earnings call, contract PR>"
    set_on: <ISO date>
```

- **G1 -- a blocking gate must be able to resolve.** `class: blocking` REQUIRES `resolvable_by <= set_on + min(180 days, the analysis Time Horizon)`. A gate that cannot resolve inside that window MUST be authored `class: monitoring`, and a monitoring gate MUST NOT be cited as the reason a BUY is blocked. Patience is legitimate; an unfalsifiable veto is not.
- **G2 -- inherited gates are re-evaluated every run.** Each /invest run re-tests the gates carried in from prior analyses against TODAY. A blocking gate that is past its `resolvable_by` unresolved, or that now exceeds G1 against the current horizon, is RE-CLASSED to monitoring for this run, and the re-class is logged in the entity Inconsistency Log (the Phase J.5.4 mechanism).
- **G3 -- name a closed door out loud.** When no buyable path exists inside 60 days, the Decision Sheet carries ONE explicit line: `No buyable path inside 60d: <blockers + earliest resolvable_by>`.

No starter leg is forced. A DISCLOSURE was adopted instead of a mandatory small buy because the forced-starter design was inert on its own motivating case (the leg stayed blocked on unfundability and the price left the zone the same session) and manufactures trades against justified patience (red-team adjudication 2026-07-30, `wiki/research/redteam-invest-overhaul-2026-07-30.md` Part 2 M-11).

## 13. Sources and references

1. [Beneish, M. D. (1999)](https://www.tandfonline.com/doi/abs/10.2469/faj.v55.n5.2296) -- Detection of Earnings Manipulation; M-Score 8-variable model.
2. [Altman, E. I. (1968)](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1968.tb00843.x) -- Financial Ratios, Discriminant Analysis and Bankruptcy Prediction; Z-Score.
3. [Piotroski, J. D. (2000)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=249455) -- Value Investing and Historical Financial Statement Information; F-Score.
4. [Dechow, P., Sloan, R., and Sweeney, A. (1995)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5520) -- Detecting Earnings Management; Modified Jones Model.
5. [Dechow, P., Ge, W., Larson, C., and Sloan, R. (2011)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=997483) -- Predicting Material Accounting Misstatements; F-Score for fraud.
6. [Sloan, R. G. (1996)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2598) -- Accrual anomaly foundational paper.
7. [Beneish, Nichols, and Lee (2011)](https://www.ssrn.com/abstract=1903593) -- Forensic Accounting and Stock Return Prediction; M-Score out-of-sample power.
8. [Fama, E. and French, K. (1993)](https://www.sciencedirect.com/science/article/abs/pii/0304405X93900235) -- Three-factor model foundational paper.
9. [Fama, E. and French, K. (2015)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2287202) -- Five-Factor Asset Pricing Model; adds RMW and CMA.
10. [Carhart, M. (1997)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=8036) -- Mutual fund performance; momentum UMD/WML factor.
11. [Asness, Frazzini and Pedersen (2019)](https://www.aqr.com/Insights/Research/Working-Paper/Quality-Minus-Junk) -- Quality Minus Junk; AQR QMJ factor.
12. [Asness, Moskowitz and Pedersen (2013)](https://www.aqr.com/Insights/Research/Journal-Article/Value-and-Momentum-Everywhere) -- Value and Momentum Everywhere; cross-asset factors.
13. [Mauboussin and Callahan (2022)](https://www.morganstanley.com/im/publication/insights/articles/article_returnoninvestedcapital.pdf) -- Return on Invested Capital: How to Calculate ROIC; Morgan Stanley Counterpoint Global.
14. [Mauboussin and Callahan (2025)](https://www.morganstanley.com/im/publication/insights/articles/article_capitalallocation.pdf) -- Capital Allocation; Counterpoint Global framework.
15. [Mauboussin and Callahan (2014) -- What Does a Price-Earnings Multiple Mean?](https://studylib.net/doc/7982074/what-does-a-price-earnings-multiple-mean%3F) -- Archived Credit Suisse GFS piece.
16. [Damodaran, A. -- NYU Stern home page](https://pages.stern.nyu.edu/~adamodar/) -- Gateway to valuation resources.
17. [Damodaran -- Return on Capital, ROIC, ROE working paper](https://pages.stern.nyu.edu/~adamodar/pdfiles/papers/returnmeasures.pdf) -- Practitioner derivation of ROIC.
18. [Damodaran -- WACC by sector dataset](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/wacc.html) -- Cost-of-capital reference tables.
19. [Koller, Goedhart and Wessels (2020) -- Valuation 7th ed.](https://www.wiley.com/en-us/Valuation%3A+Measuring+and+Managing+the+Value+of+Companies%2C+7th+Edition-p-9781119611882) -- McKinsey institutional DCF reference.
20. [O'Shaughnessy, J. P. -- What Works on Wall Street](http://www.whatworksonwallstreet.com/) -- Multi-factor screen backtests.
21. [Greenblatt -- Magic Formula overview](https://en.wikipedia.org/wiki/Magic_formula_investing) -- EBIT/EV + ROC ranking methodology.
22. [Berkin and Swedroe / CFA Institute (2017)](https://rpc.cfainstitute.org/research/financial-analysts-journal/2017/your-complete-guide-to-factor-based-investing) -- CFA-reviewed factor-investing guide.
23. [Hsu, Kalesnik and Kose (2019)](https://www.anderson.ucla.edu/documents/areas/fac/finance/What%20Is%20Quality%20Jason%20Hsu.pdf) -- "What Is Quality?"; FAJ quality-factor comparison.
24. [CFA Institute -- Financial Analysis Techniques refresher](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/financial-analysis-techniques) -- 5-factor DuPont reference.
25. [Brier, G. W. (1950)](https://journals.ametsoc.org/view/journals/mwre/78/1/1520-0493_1950_078_0001_vofeit_2_0_co_2.xml) -- Verification of Forecasts; original Brier score.
26. [Good Judgment Project / Tetlock](https://goodjudgment.com/about/) -- Superforecasting and calibration research.
27. [SEC EDGAR Full-Text Search](https://www.sec.gov/edgar/search/) -- Primary-filing gateway.
28. [SEC / Investor.gov -- Form 10-K overview](https://www.investor.gov/introduction-investing/investing-basics/glossary/form-10-k) -- Annual report requirements.
29. [SEC / Investor.gov -- Form 13F](https://www.investor.gov/introduction-investing/investing-basics/glossary/form-13f-reports-filed-institutional-investment) -- Institutional-manager holdings.
30. [SEC -- 13F FAQ](https://www.sec.gov/rules-regulations/staff-guidance/division-investment-management-frequently-asked-questions/frequently-asked-questions-about-form-13f) -- Staff guidance on 13F format.
31. [SEC / Investor.gov -- Schedules 13D and 13G](https://www.investor.gov/introduction-investing/investing-basics/glossary/schedules-13d-and-13g) -- Beneficial ownership.
32. [SEC (2023) 13D/13G amendments press release](https://www.sec.gov/newsroom/press-releases/2023-219) -- Accelerated reporting deadlines.
33. [FASB ASU 2014-09 ASC Topic 606](https://storage.fasb.org/ASU%202014-09_Section%20A.pdf) -- Revenue from Contracts with Customers.
34. [SEC (2003) Regulation G adopting release](https://www.sec.gov/rules-regulations/2003/03/conditions-use-non-gaap-financial-measures) -- Non-GAAP presentation rules.
35. [TSMC Investor Relations Q1 2026](https://investor.tsmc.com/english/quarterly-results/2026/q1) -- Quarterly revenue and capex disclosure.
36. [TSMC 3Q25 SEC 6-K](https://www.sec.gov/Archives/edgar/data/0001046179/000104617925000116/a3q25e_withguidancexfinal.htm) -- Gross margin and net margin primary source.
37. [SIA / WSTS 2025 sales release](https://www.semiconductors.org/global-annual-semiconductor-sales-increase-25-6-to-791-7-billion-in-2025/) -- $791.7B 2025 global semi sales.
38. [SEMI 2025 equipment billings release](https://www.semi.org/en/SEMI-Reports-Global-Semiconductor-Equipment-Billings-Reached-135-Billion-in-2025) -- $135B WFE billings.
39. [SemiAnalysis (Patel, Xie, Wong 2023)](https://semianalysis.com/2023/07/26/ai-expansion-supply-chain-analysis/) -- Canonical CoWoS and HBM bottleneck analysis.
40. [SK hynix Q3 2025 results](https://news.skhynix.com/sk-hynix-announces-3q25-financial-results/) -- HBM ramp and revenue.
41. [Samsung Electronics FY2025 Q4 release](https://news.samsung.com/global/samsung-electronics-announces-fourth-quarter-and-fy-2025-results) -- DS Division HBM commentary.
42. [Micron December 2025 10-Q](https://investors.micron.com/static-files/502c03ac-dd06-4c88-9441-02ebfe6ff6fa) -- Cloud Memory Business Unit disclosure.
43. [ASML Q3 2025 financial results](https://www.asml.com/en/news/press-releases/2025/q3-2025-financial-results) -- EUV booking levels.
44. [Applied Materials FY2025 results](https://ir.appliedmaterials.com/news-releases/news-release-details/applied-materials-announces-fourth-quarter-and-fiscal-year-2025) -- WFE and HBM-packaging commentary.
45. [NVIDIA FY2025 10-K](https://www.sec.gov/Archives/edgar/data/0001045810/000104581025000023/nvda-20250126.htm) -- Data-center segment primary source.
46. [Gartner 2026 semiconductor forecast](https://www.gartner.com/en/newsroom/press-releases/2026-04-08-gartner-forecasts-worldwide-semiconductor-revenue-to-exceed-us-dollars-one-point-3-trillion-in-2026) -- $1.3T 2026 forecast; memflation.
47. [Glassnode Insights -- on-chain cohort methodology](https://insights.glassnode.com/on-chain-analysis-evolution-new-granular-cohorts-for-key-on-chain-metrics/) -- SOPR, MVRV, Realized Cap.
48. [Coin Metrics State of the Network -- MVRV analysis](https://coinmetrics.substack.com/p/coin-metrics-state-of-the-network-574) -- Canonical MVRV methodology.
49. [Willy Woo / Woobull -- NVT Ratio introduction](https://woobull.com/introducing-nvt-ratio-bitcoins-pe-ratio-use-it-to-detect-bubbles/) -- Crypto P/E analog.
50. [Nakamoto (2008) Bitcoin whitepaper](https://bitcoin.org/bitcoin.pdf) -- Peer-to-Peer Electronic Cash System.
51. [Ethereum.org -- Proof of Stake documentation](https://ethereum.org/developers/docs/consensus-mechanisms/pos/) -- Validator duties, slashing, finality.
52. [SEC Chair Atkins (2025-11-12)](https://www.sec.gov/newsroom/speeches-statements/atkins-111225-secs-approach-digital-assets-inside-project-crypto) -- Project Crypto digital-asset approach.
53. [SEC Chair Gensler (2024-01-10)](https://www.sec.gov/newsroom/speeches-statements/gensler-statement-spot-bitcoin-011023) -- Spot Bitcoin ETP approval statement.
54. [Registration Authority, universal financial messaging scheme](https://www.iso20022.org/about-iso-20022).
55. [Ripple -- standards overview](https://ripple.com/lp/iso-overview/) -- RippleNet DLT standards membership.
56. [FRED -- Federal Reserve Economic Data](https://fred.stlouisfed.org/) -- 840k+ time series.
57. [Bureau of Labor Statistics -- CPI release](https://www.bls.gov/news.release/cpi.nr0.htm) -- Inflation primary source.
58. [Federal Reserve FOMC](https://www.federalreserve.gov/monetarypolicy/fomc.htm) -- Statements and projections.
59. [Morningstar Rating for Funds methodology](https://www.morningstar.com/content/dam/marketing/shared/research/methodology/771945_Morningstar_Rating_for_Funds_Methodology.pdf) -- MRAR and star rating.
60. [ETF.com Fund Flows Tool](https://www.etf.com/etfanalytics/etf-fund-flows-tool) -- Creation/redemption aggregation.
61. [S&P Dow Jones Indices US Methodology](https://www.spglobal.com/spdji/en/documents/methodologies/methodology-sp-us-indices.pdf) -- S&P 500 construction rules.
62. [CFA Institute (2010) How to Write a Great Research Report](https://rpc.cfainstitute.org/research/cfa-magazine/2010/how-to-write-a-great-research-report) -- Research memo standards.
63. [CFA Institute (2024) Code of Ethics and Standards](https://www.cfainstitute.org/standards/professionals/code-ethics-standards) -- Professional conduct baseline.
64. [CFA Institute Standards of Practice Handbook 12th ed.](https://www.cfainstitute.org/sites/default/files/-/media/documents/code/code-ethics-standards/standards-practice-handbook-12th-edition.pdf) -- Interpretive guidance on Standard V.
65. [Munger / Kaufman -- Poor Charlie's Almanack (Stripe Press 2023)](https://press.stripe.com/poor-charlies-almanack) -- Latticework of mental models.
66. [Marks -- Oaktree memos archive](https://www.oaktreecapital.com/insights/memos) -- Institutional client memo genre.
67. [Marks -- "Is It a Bubble?" Oaktree memo](https://www.oaktreecapital.com/docs/default-source/memos/is-it-a-bubble.pdf?sfvrsn=d4a92866_3) -- Representative memo structure and tone.
68. [Buffett -- Berkshire annual shareholder letters archive](https://www.berkshirehathaway.com/letters/letters.html) -- Owner-oriented reporting baseline.
69. [Buffett -- 2024 Berkshire Annual Letter](https://www.berkshirehathaway.com/letters/2024ltr.pdf) -- Capital allocation and operating vs GAAP earnings.
70. [Mauboussin and Callahan -- Measuring the Moat (2013 Credit Suisse)](https://www.safalniveshak.com/wp-content/uploads/2012/07/Measuring-The-Moat-CSFB.pdf) -- Systematic moat framework.
71. [Mauboussin and Rappaport -- Expectations Investing](https://www.expectationsinvesting.com) -- Reverse-DCF and price-implied expectations.
72. [Damodaran -- Musings on Markets blog](https://aswathdamodaran.blogspot.com/) -- Narrative-and-numbers valuation philosophy.
73. [Asness / AQR -- Cliff's Perspective](https://www.aqr.com/Insights/Perspectives/Cliffs-Perspective) -- Factor investing practitioner commentary.
74. [Levine -- Money Stuff (Bloomberg)](https://www.bloomberg.com/account/newsletters/money-stuff) -- Securities law and corporate finance interpretation.
75. [Hempton -- Bronte Capital blog](http://brontecapital.blogspot.com/) -- Forensic short-selling case studies.
76. [Chanos -- Graham and Doddsville 2012 interview](https://medium.com/graham-and-doddsville/jim-chanos-rooting-out-fraud-6eca8e6387ad) -- Forensic practitioner process.
77. [Kelly (1956) A New Interpretation of Information Rate](https://www.princeton.edu/~wbialek/rome/refs/kelly_56.pdf) -- Log-wealth-growth criterion.
78. [Thorp (2006) Kelly Criterion in Blackjack, Sports Betting and the Stock Market](https://gwern.net/doc/statistics/decision/2006-thorp.pdf) -- Practitioner Kelly application.
79. [Seykota -- Trading Tribe risk rules](https://www.seykota.com/tribe/risk/index.htm) -- Practitioner position-sizing discipline.

## Workflow examples (preserved from SKILL.md)

## Examples

### Example 1: New ticker, first analysis (CREATE entity)

`/invest KLAC`. Entity note absent. Phase B state-transition prints CREATE branch; user confirms. Research phases complete. Phase K writes `wiki/investing/analyses/klac-analysis-2026-04-22.md` with verdict WATCH, conviction 55%, confidence 75%. Phase L CREATE branch grounds entity in _templates/entity.md with 5 sections populated. Phase M appends to research-log, investing-moc, sessions-log, daily note. Atomic commit: 5 paths. Phase P /ingest recommendation NO (single-ticker analysis per /enrich v9 T3 rule).

### Example 2: A ticker with an existing entity note, UPDATE branch (typical case)

`/invest <TICKER>`. Entity exists; UPDATE branch. Phase L extracts 18 claims; dedup skips 12 (already present from prior /ingest of ref-theme-alpha); 4 apply additively; 2 Tier-1 auto-resolve (Q3 backlog superseded by Q4). Entity `updated:` bumps. Phase M atomic peripherals. Commit: 6 paths.

### Example 3: Same-day intraday re-analysis (timestamped variant)

9:31 AM: `/invest NVDA` writes `nvda-analysis-2026-04-22.md`. 2:15 PM: post-earnings gap; `/invest NVDA` again. Path-collision detected; default to `nvda-analysis-2026-04-22-1415.md` (preserves archival rule, no --replace needed). Entity UPDATE with new claims. Both analyses preserved.

### Example 4: Explicit error-correction overwrite

9:31 AM analysis carried a wrong figure. `/invest NVDA --replace`. Overwrites `nvda-analysis-2026-04-22.md` (explicit destructive). Entity re-extracted; dedup skips previous claims; only corrections land.

### Example 5: Zero-new-claims short-circuit

`/invest MU` day after a /ingest ran on ref-theme-alpha that fully covered MU. All 8 extracted claims marker-sig match existing entity claims. Phase L zero-new-claims short-circuit: entity untouched; `updated:` not bumped. Phase P reports "entity unchanged (all 8 claims deduped)". Analysis file + research-log + sessions-log + daily note still written. Commit: 4 paths (entity not staged).

### Example 6: Preview mode

`/invest AVGO --preview`. Phase A runs (no F11 set). Phase B prints state-transition model. Exit clean. No research, no writes, no commit. Useful for understanding what a full run would produce.

### Example 7: Refresh retroactive entity extraction

Old analysis at `wiki/investing/analyses/avgo-analysis-2026-04-15.md`. `/invest --refresh wiki/investing/analyses/avgo-analysis-2026-04-15.md`. Skips research. Runs Phase L entity extraction on that existing analysis. Additive-only. Useful after ref-entity-update-semantics.md is updated or when a prior /invest ran with --no-entity.

### Example 8: Mid-batch failure (N.halt)

Phase L UPDATE succeeds on NVDA entity. Phase M watchlist Edit fails (old_string drift from concurrent PreToolUse formatter). N.halt: immediate stop; F11 stays on; no commit. Report: "NVDA entity updated (unstaged); watchlist failed; research-log + sessions-log + daily note not attempted." User runs `git checkout -- wiki/entities/tickers/NVDA.md` rollback or fixes watchlist and re-invokes (idempotent skip).

<!-- End preserved workflow examples. -->

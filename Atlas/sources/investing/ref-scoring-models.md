---
categories:
  - sources
type: reference
created: 2026-04-05
updated: 2026-09-13
status: active
confidence: high
tags:
  - topic/valuation
  - topic/piotroski
  - topic/dcf
  - topic/altman-z
aliases: [scoring-models, valuation-frameworks]
related: ["*ref-sector-benchmarks* (not published)", "*ref-etf-evaluation* (not published)", "*ref-research-insights* (not published)", "[[ref-theme-alpha]]", "*ref-memory-storage-cycle-deep-dive* (not published)", "[[ref-earnings-playbook]]", "[[ref-valuation-methodology]]", "*ref-factor-lens* (not published)", "*decision-invest-kernel-doctrine-2026-07-06* (not published)"]
bands:
  schema_version: 1
  block_id: forensic-bands
  evaluated_by: invest-kernel
  updated: "2026-07-06"
  ratified_by: decision-invest-kernel-doctrine-2026-07-06
  fingerprint: "48ee1308"
  piotroski: {strong_gte: 8, long_gate_gte: 6, weak_lte: 2, red_lte: 2}
  altman_z: {safe_gt: 2.99, distress_lt: 1.81, red_lt: 1.81}
  beneish_m: {manipulator_gt: -1.78, clean_lt: -2.22, red_gt: -1.78}
  sloan_accruals_pct: {negative_gt: 10, positive_lt: -10, red_gt: 10}
---

# Reference: Financial Scoring Models and Valuation Frameworks
Last updated: 2026-04-06
Sources: [13]
Refresh cadence: As-needed (formulas are stable; interpretation context may shift)
Built by: Claude Opus deep research

---

## SECTION 1: PIOTROSKI F-SCORE

The Piotroski F-Score is a **9-component binary scoring system** designed to separate financial winners from losers among high book-to-market (value) stocks. Joseph Piotroski published the model in 2000, demonstrating that a long-short strategy based on the score generated **23% annual market-adjusted return spreads** across 21 years of data [1]. Each component scores 1 (good signal) or 0 (bad signal), yielding a composite score from 0 to 9.

### All 9 components

**Category A -- Profitability (4 signals)**

| # | Signal | Formula | Scores 1 if | Financial statement items |
|---|--------|---------|-------------|--------------------------|
| 1 | F_ROA | ROA = NI_bex / TA(t-1) | ROA > 0 | Net Income before extraordinary items (IS); Total Assets at beginning of year (BS) |
| 2 | F_CFO | CFO_scaled = CFO / TA(t-1) | CFO_scaled > 0 | Cash Flow from Operations (CFS); Total Assets at beginning of year (BS) |
| 3 | F_dROA | dROA = ROA(t) - ROA(t-1) | dROA > 0 | Same as ROA for years t and t-1 |
| 4 | F_ACCRUAL | See below | CFO_scaled > ROA | See below |

**Component 4 -- Accruals (critical detail):**

*Original paper formula* [1, p.7]: ACCRUAL = (NI_bex - CFO) / TA(t-1). The binary indicator F_ACCRUAL = 1 when CFO/TA(t-1) > NI/TA(t-1), meaning cash flow exceeds earnings on a scaled basis. When ACCRUAL is negative, earnings are backed by cash -- a positive quality signal rooted in Sloan (1996) [6].

*Practitioner simplification*: Score 1 if CFO > Net Income in absolute dollar terms. This is mathematically equivalent to the original when both are scaled by the same denominator (beginning-of-year total assets). Discrepancies arise only if different asset bases are used for each ratio.

**Category B -- Leverage, Liquidity, and Source of Funds (3 signals)**

| # | Signal | Formula | Scores 1 if | Financial statement items |
|---|--------|---------|-------------|--------------------------|
| 5 | F_dLEVER | dLEVER = (LTD(t)/AvgTA(t)) - (LTD(t-1)/AvgTA(t-1)) | dLEVER < 0 (leverage fell) | Long-term debt incl. current portion (BS); Average total assets (BS) |
| 6 | F_dLIQUID | dLIQUID = CR(t) - CR(t-1), where CR = CA/CL | dLIQUID > 0 (liquidity improved) | Current assets, current liabilities (BS) |
| 7 | EQ_OFFER | Did firm issue common equity? | Firm did NOT issue equity | Cash flow statement / Compustat |

**Category C -- Operating Efficiency (2 signals)**

| # | Signal | Formula | Scores 1 if | Financial statement items |
|---|--------|---------|-------------|--------------------------|
| 8 | F_dMARGIN | dMARGIN = GM%(t) - GM%(t-1), where GM% = (Sales-COGS)/Sales | dMARGIN > 0 | Net sales, COGS (IS) |
| 9 | F_dTURN | dTURN = AT(t) - AT(t-1), where AT = Sales/AvgTA | dTURN > 0 | Net sales (IS); Average total assets (BS) |

**Edge cases and denominator note**: The paper uses beginning-of-year total assets for ROA and CFO scaling but **average total assets** for leverage (Component 5) and asset turnover (Component 9, per Table 1 variable definitions). Many implementations incorrectly use a uniform denominator. For Component 7, stock-based compensation share issuance can trigger a 0 score even in healthy companies -- some practitioners substitute net equity issuance.

### Scoring interpretation and historical returns

| F-Score | Classification | 1-Year Market-Adj. Return (Piotroski 1976-1996) |
|---------|---------------|--------------------------------------------------|
| 0-1 | Weak (original "Low") | -9.6% mean; 31.8% winners |
| 2-4 | Below average (practitioner convention) | Monotonically increasing |
| 5 | Average | Near market return for value stocks |
| 6-7 | Above average | Positive excess returns |
| 8-9 | Strong (original "High") | +13.4% mean; 50.0% winners |

The original paper defined only two portfolios -- Low (0-1) and High (8-9) -- within the **top book-to-market quintile**. The 5-band interpretation above is a widely used practitioner convention. High-minus-Low return spread was **+23.0% annually** (t-stat 5.59, p < 0.001) on a market-adjusted basis, and **+43.2% cumulative** over two years. Raw one-year returns were 31.3% (High) versus 7.8% (Low). The strategy was profitable in **18 of 21 years**, with the worst year at -3.6%. Low-scoring firms had a **10%** performance-related delisting rate versus 1.9% for high scorers [1].

### Worked example

Apex Manufacturing -- mid-cap industrial, fiscal year t:

| Item | Year t | Year t-1 |
|------|--------|----------|
| Net Sales | $3,200M | $2,900M |
| COGS | $2,048M | $1,885M |
| NI (before extraordinary) | $192M | $160M |
| CFO | $245M | $210M |
| Total Assets (beginning) | $2,800M | $2,500M |
| Total Assets (end) | $3,100M | $2,800M |
| LT Debt (incl. current portion) | $680M | $720M |
| Current Assets | $980M | $890M |
| Current Liabilities | $620M | $600M |
| Equity issued | None | -- |

Calculations:

1. ROA = 192/2800 = **6.86%** > 0 --> F_ROA = **1**
2. CFO/TA = 245/2800 = **8.75%** > 0 --> F_CFO = **1**
3. dROA = 6.86% - (160/2500 = 6.40%) = **+0.46%** --> F_dROA = **1**
4. CFO/TA - ROA = 8.75% - 6.86% = **+1.89%** > 0 --> F_ACCRUAL = **1**
5. Leverage(t) = 680/2950 = 23.1%; Leverage(t-1) = 720/2650 = 27.2%; delta = **-4.1%** --> F_dLEVER = **1**
6. CR(t) = 980/620 = 1.581; CR(t-1) = 890/600 = 1.483; delta = **+0.098** --> F_dLIQUID = **1**
7. No equity issued --> EQ_OFFER = **1**
8. GM%(t) = (3200-2048)/3200 = 36.0%; GM%(t-1) = (2900-1885)/2900 = 35.0%; delta = **+1.0%** --> F_dMARGIN = **1**
9. AT(t) = 3200/2950 = 1.085; AT(t-1) = 2900/2650 = 1.094; delta = **-0.009** --> F_dTURN = **0**

**F-Score = 8** (Strong). The only miss is declining asset turnover -- total assets grew faster than revenue.

### Sector considerations

**Value stocks**: The model's native domain. Apply directly to high book-to-market stocks. **Growth/tech**: F-Score was not designed for growth stocks; high-growth firms routinely issue equity (Component 7 = 0) and have negative earnings (Component 1 = 0) without distress. **Financials**: Gross margin and asset turnover are not meaningful for banks; leverage signals are inverted (high leverage is structural, not distress). **REITs**: Equity issuance is a standard capital-raising mechanism, not a distress signal. **Pre-profit companies**: Automatically score 0 on ROA, CFO often 0 as well; minimum possible score effectively starts at 0-2, making the model uninformative.

### Limitations

The F-Score measures **year-over-year improvement**, not absolute levels. A company with dangerously high leverage scores 1 on F_dLEVER if leverage merely declined. The binary conversion discards information about magnitude. Post-publication alpha has diminished, particularly in large-cap and well-followed stocks. Piotroski acknowledged potential data-snooping bias [1, p.34]. Cyclical recovery years inflate scores regardless of fundamental quality.

---

## SECTION 2: ALTMAN Z-SCORE

Edward Altman's Z-Score remains the most widely used bankruptcy prediction model. The original 1968 model achieved **95% accuracy one year prior** to bankruptcy and **72% accuracy two years prior** on the initial sample [2]. Three versions exist for different company types.

### Version 1 -- Original Z-Score (public manufacturing)

**Z = 1.2 * X1 + 1.4 * X2 + 3.3 * X3 + 0.6 * X4 + 1.0 * X5**

| Variable | Formula | Measures |
|----------|---------|----------|
| X1 | Working Capital / Total Assets | Liquidity |
| X2 | Retained Earnings / Total Assets | Cumulative profitability and firm age |
| X3 | EBIT / Total Assets | Operating efficiency |
| X4 | Market Value of Equity / Book Value of Total Liabilities | Market confidence (forward-looking) |
| X5 | Sales / Total Assets | Asset turnover |

Note: The original 1968 paper expressed X1-X4 as percentages with coefficients 0.012, 0.014, 0.033, 0.006 and X5 coefficient as **0.999**. The commonly cited form (1.2, 1.4, 3.3, 0.6, 1.0) rescales X1-X4 as decimals and rounds 0.999 to 1.0. Both forms are mathematically equivalent [3].

| Zone | Original Z | Historical bankruptcy rate |
|------|-----------|---------------------------|
| Safe | Z > 2.99 | Near 0% within 2 years in original sample |
| Grey | 1.81 < Z < 2.99 | ~3 errors out of 66 firms (4.5%) |
| Distress | Z < 1.81 | Very high; 100% of firms below 1.81 went bankrupt in original 1-year test |

### Version 2 -- Z'-Score (private companies)

**Z' = 0.717 * X1 + 0.847 * X2 + 3.107 * X3 + 0.420 * X4' + 0.998 * X5**

X4' substitutes **Book Value of Equity / Total Liabilities** for market value. Published in Altman (1983) [12].

| Zone | Z'-Score |
|------|---------|
| Safe | Z' > 2.9 |
| Grey | 1.23 < Z' < 2.9 |
| Distress | Z' < 1.23 |

### Version 3 -- Z''-Score (non-manufacturing / emerging markets)

**Z'' = 6.56 * X1 + 3.26 * X2 + 6.72 * X3 + 1.05 * X4**

X5 (Sales/Total Assets) is removed because it was "particularly sensitive to industrial sector differences" [3]. X4 uses book value of equity. The **emerging markets version** adds a constant: Z'' = 3.25 + 6.56*X1 + 3.26*X2 + 6.72*X3 + 1.05*X4, calibrated so that scores near zero correspond to a D-rated bond equivalent [13].

| Zone | Z''-Score |
|------|----------|
| Safe | Z'' > 2.6 |
| Grey | 1.1 < Z'' < 2.6 |
| Distress | Z'' < 1.1 |

### Error rates from original study

The original 1968 sample comprised **66 firms** (33 bankrupt, 33 non-bankrupt matched pairs), all publicly held U.S. manufacturers. One year prior: **Type I error 6%** (2/33 bankrupt firms misclassified as safe); **Type II error 3%** (1/33 non-bankrupt firms misclassified as distressed); overall accuracy 95.5%. Two-year prediction accuracy fell to **72%**. In subsequent out-of-sample tests (1997-1999, n=120), one-year accuracy remained **94%** using a 2.67 cutoff [3].

### Worked example -- Apex Manufacturing

Using end-of-year data: Total Assets $3,100M, Working Capital $360M (CA $980M - CL $620M), Retained Earnings $1,450M, EBIT $310M, Market Cap $4,200M, Total Liabilities $1,650M, Sales $3,200M, Book Equity $1,450M.

**Original Z-Score:**

| Variable | Calculation | Value | Weighted |
|----------|-------------|-------|----------|
| X1 | 360/3100 | 0.116 | 0.139 |
| X2 | 1450/3100 | 0.468 | 0.655 |
| X3 | 310/3100 | 0.100 | 0.330 |
| X4 | 4200/1650 | 2.545 | 1.527 |
| X5 | 3200/3100 | 1.032 | 1.032 |
| **Z** | | | **3.68** |

Result: **Safe zone** (Z = 3.68 > 2.99).

**Z''-Score (same company, non-manufacturing version):**

| Variable | Calculation | Value | Weighted |
|----------|-------------|-------|----------|
| X1 | 360/3100 | 0.116 | 0.762 |
| X2 | 1450/3100 | 0.468 | 1.525 |
| X3 | 310/3100 | 0.100 | 0.672 |
| X4 | 1450/1650 | 0.879 | 0.923 |
| **Z''** | | | **3.88** |

Result: **Safe zone** (Z'' = 3.88 > 2.6).

### Limitations

The model excludes financial companies by design. **X5 is industry-sensitive** -- retailers naturally score higher on asset turnover, inflating Z-Scores. Young firms score poorly on X2 (low retained earnings) regardless of health. The Type II error rate has risen substantially over time as corporate leverage has structurally increased; Altman warned against rigid reliance on the 1.81 cutoff in modern applications [3]. IFRS vs. GAAP differences affect variable calculations.

---

## SECTION 3: BENEISH M-SCORE

The Beneish M-Score detects earnings manipulation using **8 financial ratios** with coefficients estimated via weighted probit regression on 50 confirmed manipulators and 1,708 controls [4]. The model reportedly flagged **Enron in 1998**, two years before its collapse, when Cornell University students applied it to Enron's 1997 annual report and concluded the stock was overpriced.

### Exact formula

**M = -4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI + 0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI**

### All 8 variables

| Variable | Formula | Coefficient | Interpretation |
|----------|---------|-------------|----------------|
| DSRI | (Receivables_t/Sales_t) / (Receivables_{t-1}/Sales_{t-1}) | +0.920 | >1 means receivables outpacing revenue -- possible premature recognition |
| GMI | GrossMargin%_{t-1} / GrossMargin%_t | +0.528 | >1 means margins deteriorating -- incentive to manipulate. NOTE: inverted ratio (prior/current) |
| AQI | [1-(CA_t+PPE_t+Securities_t)/TA_t] / [1-(CA_{t-1}+PPE_{t-1}+Securities_{t-1})/TA_{t-1}] | +0.404 | >1 means increased cost deferrals or intangible asset growth |
| SGI | Sales_t / Sales_{t-1} | +0.892 | Growth creates pressure to sustain targets. Median manipulator growth: 34.4% vs 9.4% for controls |
| DEPI | [Depr_{t-1}/(Depr_{t-1}+NetPPE_{t-1})] / [Depr_t/(Depr_t+NetPPE_t)] | +0.115 | >1 means depreciation rate slowed -- upward-revised useful lives |
| SGAI | (SGA_t/Sales_t) / (SGA_{t-1}/Sales_{t-1}) | **-0.172** | Negative: firms inflating revenue show falling SGA-to-sales ratio because denominator is overstated |
| TATA | (NI_continuing - CFO) / TA_t | **+4.679** | Highest weight by far. Large gap between earnings and cash flow is the single strongest manipulation signal |
| LVGI | [(CL_t+LTD_t)/TA_t] / [(CL_{t-1}+LTD_{t-1})/TA_{t-1}] | **-0.327** | Negative: firms decreasing leverage may be selling shares to pay debt -- a common fraud pattern |

**Why SGAI and LVGI have negative coefficients**: Both were statistically insignificant in the original study (high p-values). The negative SGAI coefficient captures the pattern that manipulators inflating revenue (the denominator) without proportional SGA increases show a *declining* SGAI. The negative LVGI coefficient reflects that many fraud companies reduce debt by issuing equity -- share sales are themselves a fraud red flag [4].

### Thresholds

| M-Score | Interpretation | Source |
|---------|---------------|--------|
| M > -1.78 | Likely manipulator | Original paper (8-variable model, primary threshold) [4] |
| -2.22 < M < -1.78 | Grey zone / warrants investigation | -2.22 was the 5-variable model threshold from Beneish (1997); some practitioners apply it to 8-variable model as conservative screen |
| M < -2.22 | Unlikely manipulator | Conservative threshold |

The -1.49 threshold cited by some practitioners is not verified in the original paper and should be treated as an unconfirmed convention.

### Error rates

At the -1.78 cutoff on the estimation sample (1982-1988): **Type I error ~24%** (missed 24% of manipulators); **Type II error ~17.5%** (falsely flagged 17.5% of clean firms). On the holdout sample (1989-1992), the model identified approximately **half** of manipulation cases prior to public discovery. In a later evaluation, it correctly identified **12 of 17** highest-profile fraud cases from 1998-2002 (71%) [4].

### Worked example -- two companies

**SteadyCo (clean):**

| Variable | Value | Weighted |
|----------|-------|----------|
| DSRI | 1.02 | 0.938 |
| GMI | 0.98 | 0.517 |
| AQI | 1.01 | 0.408 |
| SGI | 1.08 | 0.963 |
| DEPI | 1.00 | 0.115 |
| SGAI | 1.03 | -0.177 |
| TATA | -0.02 | -0.094 |
| LVGI | 1.05 | -0.343 |
| Intercept | | -4.840 |
| **M-Score** | | **-2.51** |

Result: M = -2.51 < -1.78. **Unlikely manipulator.**

**AggressiveCo (suspicious):**

| Variable | Value | Weighted |
|----------|-------|----------|
| DSRI | 1.45 | 1.334 |
| GMI | 1.25 | 0.660 |
| AQI | 1.30 | 0.525 |
| SGI | 1.42 | 1.267 |
| DEPI | 1.15 | 0.132 |
| SGAI | 0.85 | -0.146 |
| TATA | 0.08 | 0.374 |
| LVGI | 1.10 | -0.360 |
| Intercept | | -4.840 |
| **M-Score** | | **-1.05** |

Result: M = -1.05 > -1.78. **Likely manipulator.** Key drivers: high DSRI (receivables growing 45% faster than sales), deteriorating margins (GMI 1.25), rapid revenue growth (42%), and positive accruals (TATA 0.08).

### False positives

**Acquisitive companies** naturally inflate AQI via goodwill. **Hypergrowth firms** trigger high SGI (+0.892 coefficient). **SBC-heavy tech** distorts TATA (the +4.679 coefficient amplifies any earnings-to-cash-flow gap). Financial institutions were excluded from the original sample. Always investigate flagged companies qualitatively before concluding manipulation.

---

## SECTION 4: DUPONT DECOMPOSITION

### Three-component (classic)

**ROE = Net Profit Margin x Asset Turnover x Equity Multiplier**

| Component | Formula | Measures |
|-----------|---------|----------|
| Net Profit Margin | Net Income / Revenue | Profitability |
| Asset Turnover | Revenue / Total Assets | Efficiency |
| Equity Multiplier | Total Assets / Shareholders' Equity | Leverage |

### Five-component (extended)

**ROE = Tax Burden x Interest Burden x EBIT Margin x Asset Turnover x Equity Multiplier**

| Component | Formula | Measures |
|-----------|---------|----------|
| Tax Burden | Net Income / EBT | Tax efficiency (0 to 1) |
| Interest Burden | EBT / EBIT | Debt cost impact (0 to 1) |
| EBIT Margin | EBIT / Revenue | Operating profitability |
| Asset Turnover | Revenue / Total Assets | Capital efficiency |
| Equity Multiplier | Total Assets / Equity | Financial leverage |

### Worked example

A diversified industrial: Revenue $47.3B, EBIT $7.9B, EBT $6.5B, Net Income $5.2B, Total Assets $68.4B, Equity $22.8B.

**3-Component**: Margin 10.99% x Turnover 0.691 x Multiplier 3.00 = **22.8% ROE**

**5-Component**: Tax Burden 0.800 x Interest Burden 0.823 x EBIT Margin 16.70% x Turnover 0.691 x Multiplier 3.00 = **22.8% ROE**

The 5-component decomposition reveals that the 16.7% operating margin is compressed to 11.0% net margin by a 17.7% interest burden and 20.0% tax burden. The 3.0x equity multiplier amplifies a 7.6% ROA into a 22.8% ROE.

### Sector benchmarks (Damodaran, January 2026)

| Sector | Net Margin | Asset Turnover | Equity Multiplier | ROE |
|--------|-----------|----------------|-------------------|-----|
| Technology | 17-22% | 0.6-0.9x | 3.0-5.0x | 29-36% |
| Financials | 7-29% | 0.05-0.15x | 8-12x | 10-19% |
| Healthcare | 1-19% | 0.4-1.5x | 2.0-4.0x | 6-24% |
| Consumer Staples | 3-13% | 0.5-1.2x | 2.5-5.0x | 5-31% |
| Energy | 2-15% | 0.4-0.8x | 2.0-3.0x | 9-18% |
| Industrials | 5-11% | 0.5-1.0x | 2.5-4.0x | 7-37% |
| Utilities | 12-13% | 0.2-0.3x | 3.0-4.0x | 10-12% |

### Red flags

**ROE rising from leverage, not margins**: If equity multiplier is climbing while margins are flat or declining, the company is leveraging up to mask operational weakness -- unsustainable and increases bankruptcy risk. **Declining asset turnover**: Suggests the asset base is growing faster than revenue, potentially from acquisitions that destroy value or capital expenditure that has not yet generated returns. Always decompose ROE changes to identify the true driver.

---

## SECTION 5: REVERSE DCF METHODOLOGY

Reverse DCF works backward from a company's market price to determine what growth rate the market implies. This reveals whether the embedded expectations are reasonable.

### Five-step process

**Step 1 -- Determine Enterprise Value.** EV = Market Cap + Total Debt + Preferred Stock + Minority Interest - Cash. Use diluted shares outstanding.

**Step 2 -- Estimate WACC.**

**WACC = (E/V) * Re + (D/V) * Rd * (1 - T)**

Where Re (cost of equity) is derived from CAPM: **Re = Rf + Beta * (Rm - Rf)**

**Step 3 -- Define terminal value methodology.** Gordon Growth Model: **TV = FCF(n+1) / (WACC - g_terminal)**, where g_terminal typically equals long-run nominal GDP growth (2-3%).

**Step 4 -- Solve for implied growth rate.** Set EV equal to the sum of discounted FCFs plus discounted terminal value. The implied growth rate g is the constant annual FCF growth rate that equates PV of future cash flows to current EV.

**Step 5 -- Assess reasonableness.** Compare implied growth to historical revenue growth, industry forecasts, and total addressable market. If the market implies 20% FCF growth for 10 years but the industry grows at 5%, the stock embeds heroic assumptions.

### Current WACC inputs (Rf is LIVE-COMPUTED; the other rows are April 2026 anchors)

| Parameter | Value | Source |
|-----------|-------|--------|
| Risk-free rate (10Y UST) | **LIVE: 63-session average of DGS10 loaded at Phase D.8, stamped with its computation date in the analysis** | FRED DGS10 via mcp:fred; smoothed, NOT the live daily print (2026-07-30) |
| Equity risk premium (Damodaran) | **4.23%** | Damodaran 2026 ERP update, Jan 1, 2026 [11] |
| Equity risk premium (Kroll) | **5.0%** (likely 5.5% post-March 2026 Middle East crisis) | Kroll, Sept 2, 2025 |
| Small-cap size premium | **2-4%** (micro-cap: 5-6%; Decile 10z: ~11%) | Kroll CRSP Deciles |
| Federal corporate tax rate | **21%** (permanent per OBBBA, July 2025) | IRS |
| S&P 500 median effective tax rate | **19-21%** (profitable firms) | CSIMarket/Damodaran |

### Sector WACC ranges (Damodaran, January 2026)

| GICS Sector | Typical Beta | WACC Range |
|-------------|-------------|------------|
| Information Technology | 1.25-1.55 | 9.0-10.5% |
| Health Care | 0.90-1.15 | 7.0-8.5% |
| Financials | 0.40-0.80 | 5.0-6.5% |
| Consumer Discretionary | 0.80-1.10 | 7.0-8.5% |
| Consumer Staples | 0.60-0.85 | 6.0-6.5% |
| Industrials | 0.95-1.25 | 7.5-9.0% |
| Energy | 0.30-0.95 | 5.0-7.0% |
| Utilities | 0.25-0.50 | 4.5-5.0% |
| Real Estate | 0.65-0.85 | 5.5-6.5% |
| Materials | 0.95-1.05 | 7.0-8.0% |
| Communication Services | 0.55-0.90 | 5.5-7.5% |

### Worked example -- NovaTech Inc.

Market Cap $85B, Total Debt $20B, Cash $8B, Last Year FCF $5.5B, Beta 1.15.
FROZEN ILLUSTRATION: this example holds Rf at the April-2026 print of 4.31% so
the arithmetic below stays hand-checkable. A live analysis uses the smoothed Rf
from the table above, not this number.

EV = 85 + 20 - 8 = **$97B**
Re = 4.31% + 1.15 * 4.23% = **9.17%**
Rd = 5.0% (assumed), Tax = 21%
Debt weight = 20/105 = 19.0%, Equity weight = 85/105 = 81.0%
WACC = 0.81 * 9.17% + 0.19 * 5.0% * 0.79 = 7.43% + 0.75% = **8.18%** (round to ~8.2%)

Assume 10-year projection, 3.0% terminal growth. Solving for the implied FCF growth rate g such that:

PV(growing FCF annuity, 10 years) + PV(terminal value) = $97B

At **g = 4.5%**: PV of FCFs (years 1-10) ~$43B, Terminal Value ~$135B discounted to ~$54B. Total ~$97B. The market implies NovaTech will grow FCF at **4.5% annually** for 10 years, then 3% perpetually.

### Sensitivity analysis framework

| | WACC 7.5% | WACC 8.2% | WACC 9.0% | WACC 10.0% |
|---|-----------|-----------|-----------|------------|
| **Implied g = 3%** | $79B | $72B | $65B | $57B |
| **Implied g = 4.5%** | $107B | $97B | $87B | $76B |
| **Implied g = 6%** | $142B | $127B | $113B | $97B |
| **Implied g = 8%** | $199B | $174B | $152B | $128B |

### Common errors

Using trailing FCF without normalizing for cyclicality. Applying a terminal growth rate above nominal GDP growth (~4-5%). Ignoring dilution from SBC in share count. Using book-value debt weights instead of market value. Failing to add back cash when converting EV to equity value. Double-counting growth in both the projection period and terminal value.

---

## SECTION 6: FREE CASH FLOW ANALYSIS

### FCFF (Free Cash Flow to Firm)

**FCFF = EBIT * (1 - T) + D&A - Capex - Change in Net Working Capital**

Alternative: **FCFF = Operating Cash Flow + Interest * (1 - T) - Capex**

### FCFE (Free Cash Flow to Equity)

**FCFE = Net Income + D&A - Capex - Change in NWC + Net Borrowing**

Where Net Borrowing = New Debt Issued - Debt Repaid. FCFE represents cash available to equity holders after all reinvestment and debt obligations.

### FCF quality checks

**Conversion rate** = FCF / Net Income. Sustained rates above **80%** indicate high earnings quality; rates below 50% warrant investigation. **Capex classification**: Distinguish maintenance capex (required to sustain operations) from growth capex. Maintenance capex approximates depreciation expense. **Working capital trends**: Persistent increases in receivables or inventory relative to revenue signal potential manipulation or deteriorating business. **SBC adjustment debate**: GAAP treats SBC as non-cash, adding it back to OCF. Many analysts subtract SBC from FCF because it represents real dilution cost. No consensus exists; document which convention you use.

### FCF yield interpretation

| FCF Yield | Interpretation |
|-----------|---------------|
| >8% | High yield -- potentially undervalued or distressed |
| 5-8% | Moderate -- solid value with cash generation |
| 3-5% | Low-moderate -- typical for quality growth companies |
| 1-3% | Low -- priced for significant growth |
| <1% | Very expensive -- requires extraordinary growth to justify |

FCF Yield = Free Cash Flow per Share / Share Price, or equivalently FCF / Market Cap (for equity yield) or FCF / EV (for enterprise yield).

---

## SECTION 7: ADDITIONAL SCORING MODELS

### Ohlson O-Score

A logistic regression bankruptcy model using **9 predictor variables** [5].

**O = -1.32 - 0.407*log(TA/GNP_index) + 6.03*(TL/TA) - 1.43*(WC/TA) + 0.0757*(CL/CA) - 1.72*OENEG - 2.37*(NI/TA) - 1.83*(FFO/TL) + 0.285*INTWO - 0.521*CHIN**

| # | Variable | Coeff. | Definition |
|---|----------|--------|------------|
| 1 | SIZE | -0.407 | log(Total Assets / GNP price-level index, base 1968=100) |
| 2 | TLTA | +6.03 | Total Liabilities / Total Assets (largest positive weight) |
| 3 | WCTA | -1.43 | Working Capital / Total Assets |
| 4 | CLCA | +0.0757 | Current Liabilities / Current Assets |
| 5 | OENEG | -1.72 | Dummy: 1 if Total Liabilities > Total Assets |
| 6 | NITA | -2.37 | Net Income / Total Assets |
| 7 | FUTL | -1.83 | Funds from Operations (NI + D&A) / Total Liabilities |
| 8 | INTWO | +0.285 | Dummy: 1 if net loss in both of last 2 years |
| 9 | CHIN | -0.521 | (NI_t - NI_{t-1}) / (\|NI_t\| + \|NI_{t-1}\|) -- normalized earnings change |

Logistic transformation: **P = 1 / (1 + exp(-O))**. Algebraically, O = 0.5 maps to P = 0.622459; a probability cutoff of 0.5 instead corresponds to O = 0. These are different thresholds. The former assertions that O > 0.5 establishes two-year default risk, that original accuracy is 96%, and that modern hazard models uniformly outperform both scores have not been verified against the original specification and comparison population. They remain in Git history, not an accepted probability interpretation. Do not present the transformed score as a calibrated current default probability without an independently checked model version, event, horizon, population, base rate and validation. This qualification changes no ratified scoring value or executable band.

### Sloan Accrual Ratio

**Balance sheet approach** [6]: Accrual Ratio = [(dCA - dCash) - (dCL - dSTD - dTP) - Dep] / Average Total Assets

**Cash flow approach**: Accrual Ratio = (Net Income - CFO - CFI) / Average Total Assets

High accruals (>10%) are a **negative signal** -- earnings outpace cash flow. Low accruals (<-10%) are **positive**. Sloan's original long-short strategy earned approximately **10-12% annually** from 1962-2001, though the anomaly has weakened post-2002 as it became widely known. The Sloan ratio is the continuous ancestor of both Piotroski's binary F_ACCRUAL signal and Beneish's TATA variable.

### Greenblatt Magic Formula

**Earnings Yield = EBIT / Enterprise Value**
**Return on Capital = EBIT / (Net Working Capital + Net Fixed Assets)**

EV includes market cap, debt, preferred, minus cash. Net Working Capital excludes excess cash. Net Fixed Assets = PP&E. Tangible capital employed deliberately excludes goodwill and intangibles [7].

Ranking: Score all stocks by each metric, sum ranks (lowest combined rank = best). Buy top 20-30 names. Rebalance annually. Exclude financials and utilities. Original backtest (1988-2004): **30.8% annualized** for top 30 stocks (>$50M market cap) versus 12.4% for S&P 500, outperforming in 14 of 17 years. Post-publication returns have been more modest (~3% annual outperformance) [7].

### Graham Number

**Graham Number = sqrt(22.5 * EPS * BVPS)**

The constant 22.5 derives from Graham's twin criteria: **P/E <= 15** and **P/B <= 1.5**. Since (P/E)*(P/B) = Price^2/(EPS*BVPS), setting this product <= 22.5 and solving for Price yields the formula [8]. Graham recommended using 3-year average EPS. The formula requires both EPS and BVPS to be positive. It ignores growth entirely and is unsuitable for asset-light businesses, financials, or high-growth companies.

### PEG Ratio

**PEG = (P/E Ratio) / (Expected Annual EPS Growth Rate)**

Peter Lynch's framework [9]: **PEG < 1** = undervalued relative to growth, **PEG ~1** = fairly valued, **PEG > 2** = expensive. Lynch used trailing P/E with **5-year projected** EPS growth (consensus analysts). The growth rate is entered as a whole number (15% growth = 15, not 0.15). Limitations: meaningless with negative earnings or negative growth; overstates value for low-growth dividend payers (Lynch added dividend yield to the denominator for these).

### Shareholder Yield

**Shareholder Yield = Dividend Yield + Net Buyback Yield + Debt Paydown Yield**

Net Buyback Yield = (Shares Repurchased - Shares Issued) / Average Shares Outstanding, expressed as a percentage of market cap. Debt Paydown Yield = Net Debt Repaid / Market Cap [10]. Mebane Faber's research showed high shareholder yield stocks outperformed dividend-only strategies by **1.6-4.3 percentage points annually** over 1982-2011. O'Shaughnessy's 80-year backtest found top-decile shareholder yield stocks beat the market **97% of the time** over rolling 10-year periods.

### ROIC vs WACC

**ROIC = NOPAT / Invested Capital**
**NOPAT = EBIT * (1 - Tax Rate)**
**Invested Capital = Total Equity + Total Debt - Cash** (financing approach), or equivalently Total Assets - Non-interest-bearing Current Liabilities - Excess Cash (operating approach).

The fundamental value creation test: **ROIC > WACC** creates value; ROIC < WACC destroys value regardless of growth. Sector benchmarks (Damodaran, January 2026): Software **50%**, Semiconductors **42%**, Pharma **29%**, Industrials **21-27%**, Utilities **6-7%**, REITs **3%**, Total market ex-financials **~10.6%**. Companies sustaining ROIC-WACC spreads above 5 percentage points typically possess durable competitive advantages.

---

## SECTION 8: MODEL SELECTION GUIDE

### Decision matrix

| Objective | Primary Model | Supporting Models |
|-----------|--------------|-------------------|
| Value stock screening | Piotroski F-Score | Graham Number, Magic Formula |
| Growth stock evaluation | Reverse DCF, PEG Ratio | DuPont (5-component), ROIC vs WACC |
| Fraud / manipulation detection | Beneish M-Score | Sloan Accrual Ratio, TATA analysis |
| Bankruptcy risk assessment | Altman Z-Score | Ohlson O-Score |
| Profitability quality analysis | DuPont Decomposition | FCF Conversion Rate, ROIC |
| Quick screening (any stock) | F-Score + Z-Score + M-Score | FCF Yield, Shareholder Yield |
| Banks / Financials | Do not use the non-financial Altman model as the default route | Inspect regulatory capital, asset quality and supported equity-based valuation; use industry-appropriate ROE/decomposition rather than importing industrial ROIC/WACC definitions |
| REITs | FCF/AFFO Yield | Debt ratios (not F-Score or Z-Score) |
| ETFs / Passive vehicles | Not applicable | Shareholder Yield for dividend ETF comparison |
| Pre-profit companies (structural grower) | Forward-Earnings Bridge (Section 10) | Altman Z + FCF burn rate + Reverse DCF |

### Model stacking strategy

The recommended sequential analysis pipeline for individual stocks:

1. **Piotroski F-Score** -- initial quality screen. Require >= 6 for long positions.
2. **Altman Z-Score** -- bankruptcy risk gate. Require Z > 1.81 (or Z'' > 1.1).
3. **Beneish M-Score** -- manipulation screen. Flag if M > -1.78 for deep investigation.
4. **DuPont Decomposition** -- understand ROE drivers. Identify whether quality comes from margins, efficiency, or leverage.
5. **Reverse DCF** -- determine what growth is priced in. Assess whether expectations are reasonable.
6. **ROIC vs WACC** -- confirm value creation. Only invest in firms where ROIC sustainably exceeds WACC.

This pipeline filters out weak fundamentals (Step 1), bankruptcy risk (Step 2), potential fraud (Step 3), leverage-driven illusions (Step 4), overpriced expectations (Step 5), and value-destroying businesses (Step 6).

---

## SECTION 9: FORMULA QUICK REFERENCE

| Model | Formula / Key Threshold |
|-------|------------------------|
| Piotroski F-Score | Sum of 9 binary signals (0-9). Strong >= 8, Weak <= 2 |
| F-Score: ROA | NI_bex / TA(t-1) > 0 --> 1 |
| F-Score: CFO | CFO / TA(t-1) > 0 --> 1 |
| F-Score: dROA | ROA(t) - ROA(t-1) > 0 --> 1 |
| F-Score: Accrual | CFO/TA(t-1) > NI/TA(t-1) --> 1 |
| F-Score: dLeverage | LTD/AvgTA decreased --> 1 |
| F-Score: dLiquidity | Current Ratio increased --> 1 |
| F-Score: Equity | No common equity issued --> 1 |
| F-Score: dMargin | Gross margin % increased --> 1 |
| F-Score: dTurnover | Asset turnover increased --> 1 |
| Altman Z (public mfg) | 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5. Safe >2.99, Distress <1.81 |
| Altman Z' (private) | 0.717*X1 + 0.847*X2 + 3.107*X3 + 0.420*X4' + 0.998*X5. Safe >2.9, Distress <1.23 |
| Altman Z'' (non-mfg) | 6.56*X1 + 3.26*X2 + 6.72*X3 + 1.05*X4. Safe >2.6, Distress <1.1 |
| Beneish M-Score | -4.84 + 0.920*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI + 0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI. Manipulator >-1.78 |
| Ohlson O-Score | -1.32 - 0.407*SIZE + 6.03*TLTA - 1.43*WCTA + 0.0757*CLCA - 1.72*OENEG - 2.37*NITA - 1.83*FUTL + 0.285*INTWO - 0.521*CHIN. P = 1/(1+exp(-O)). Distress: O>0.5 |
| DuPont (3) | ROE = Net Margin * Asset Turnover * Equity Multiplier |
| DuPont (5) | ROE = (NI/EBT) * (EBT/EBIT) * (EBIT/Rev) * (Rev/TA) * (TA/Equity) |
| WACC | (E/V)*Re + (D/V)*Rd*(1-T) |
| CAPM | Re = Rf + Beta*(Rm - Rf). Rf = 63-session average of DGS10 at run time (never a hardcoded literal), ERP=4.23% (Damodaran) or 5.0% (Kroll) |
| Terminal Value | TV = FCF(n+1) / (WACC - g) |
| FCFF | EBIT*(1-T) + D&A - Capex - dNWC |
| FCFE | NI + D&A - Capex - dNWC + Net Borrowing |
| Sloan Accrual | (NI - CFO - CFI) / Avg TA. High >10% negative signal |
| Magic Formula | Rank by EBIT/EV + Rank by EBIT/(NWC+Net Fixed Assets). Buy top 20-30 |
| Graham Number | sqrt(22.5 * EPS * BVPS). Stock undervalued if Price < Graham Number |
| PEG Ratio | P/E / EPS Growth%. Undervalued <1, Expensive >2 |
| Shareholder Yield | Dividend Yield + Net Buyback Yield + Debt Paydown Yield |
| ROIC | NOPAT / Invested Capital. Value creation: ROIC > WACC |
| NOPAT | EBIT * (1 - T) |
| Invested Capital | Total Equity + Total Debt - Cash |
| FCF Yield | >8% high, 5-8% moderate, 3-5% low-moderate, 1-3% low, <1% very expensive |

---

## SOURCES

[1] Piotroski, J.D. (2000). "Value Investing: The Use of Historical Financial Statement Information to Separate Winners from Losers." Journal of Accounting Research, Vol. 38, Supplement, pp. 1-41.

[2] Altman, E.I. (1968). "Financial Ratios, Discriminant Analysis and the Prediction of Corporate Bankruptcy." Journal of Finance, 23(4), pp. 589-609.

[3] Altman, E.I. (2018). "A Fifty-Year Retrospective on Credit Risk Models, the Altman Z-Score Family of Models and Their Applications to Financial Markets and Managerial Strategies." Journal of Credit Risk, 14(4), pp. 1-34.

[4] Beneish, M.D. (1999). "The Detection of Earnings Manipulation." Financial Analysts Journal, 55(5), pp. 24-36.

[5] Ohlson, J.A. (1980). "Financial Ratios and the Probabilistic Prediction of Bankruptcy." Journal of Accounting Research, 18(1), pp. 109-131.

[6] Sloan, R.G. (1996). "Do Stock Prices Fully Reflect Information in Accruals and Cash Flows about Future Earnings?" The Accounting Review, 71(3), pp. 289-315.

[7] Greenblatt, J. (2005/2010). The Little Book That Still Beats the Market. John Wiley and Sons.

[8] Graham, B. (1949/1973). The Intelligent Investor. Harper and Row, Chapter 14.

[9] Lynch, P. (1989). One Up on Wall Street. Simon and Schuster.

[10] Faber, M.T. (2013). Shareholder Yield: A Better Approach to Dividend Investing. Cambria Investment Management.

[11] Damodaran, A. (2026). "Equity Risk Premiums (ERP): Determinants, Estimates and Implications -- The 2026 Edition." SSRN, March 5, 2026. Data from pages.stern.nyu.edu/~adamodar/.

[12] Altman, E.I. (1983). Corporate Financial Distress and Bankruptcy. John Wiley and Sons.

[13] Altman, E.I., Hartzell, J., and Peck, M. (1995). "A Scoring System for Emerging Market Corporate Bonds." Salomon Brothers report.
## Top-12 Universal Metrics (2026-04-28 5th-pass extension)

The following 12 metrics are tracked uniformly by 8+ of the 11 renowned investors documented in [[ref-investor-frameworks-2026]] (Buffett, Munger, Lynch, Greenblatt, Druckenmiller, Marks, Klarman, Cohen, Ackman, Burry, Tepper). They form the universal-cross-investor metric set that /invest Phase F Fundamentals + Phase K-bis Quantitative Scoring Stack mandate for every equity analysis.

Free-tier source URL pattern (verified 2026-04-28): `https://stockanalysis.com/stocks/{ticker}/statistics/` for ratios + valuations + returns; `https://stockanalysis.com/stocks/{ticker}/financials/` for income statement + balance sheet + cash flow.

### Metric 1: ROIC (Return on Invested Capital)

**Formula**: NOPAT / (Total Debt + Equity - Cash). Greenblatt prefers EBIT / (Net Working Capital + Net Fixed Assets) which excludes goodwill and normalizes for capital intensity.

**Thresholds**: >= 15% strong; >= 25% top-decile (Greenblatt threshold for Magic Formula); < 8% weak; < 5% concern (likely earning below cost of capital).

**Application**: Buffett demands ROIC > WACC sustained; Greenblatt mechanical-screens on top-decile ROIC; Druckenmiller uses ROIC trend (improving = compounder, declining = cycle peak warning).

### Metric 2: FCF Conversion Ratio

**Formula**: Free Cash Flow / EBITDA. Tests how much of accounting profit converts to actual cash.

**Thresholds**: >= 80% strong; 100% ideal (cash equals reported earnings); < 50% weak (working-capital absorption or capex hiding earnings); < 20% red flag (potentially manipulating accruals).

**Application**: 9 of 11 renowned investors prefer cash-flow analysis over GAAP earnings. Burry famously "ignores P/E and ROE as deceptive" -- conversion ratio reveals whether reported profits are real.

### Metric 3: FCF Yield

**Formula**: TTM Free Cash Flow / Market Cap.

**Thresholds**: >= 5% attractive for non-growth (mature-business mode); 1-3% acceptable for compounders (growth-reinvestment phase); < 1% expensive on cash-flow basis.

**Application**: Klarman + Burry use FCF yield as primary valuation metric. Buffett's owners-earnings is FCF + maintenance-capex add-back; if maintenance capex is small relative to growth capex, FCF yield approximates owners-earnings yield.

### Metric 4: Net Debt / EBITDA (Leverage)

**Formula**: (Total Debt - Cash) / EBITDA.

**Thresholds**: < 2x conservative; 2-3x moderate; >= 4x caution; >= 6x distress / refinancing-wall risk.

**Application**: Munger's debt-service stress test uses this directly. Buffett demands < 0.5x debt-to-equity which roughly corresponds to < 1x net-debt/EBITDA for typical equity-bias balance sheets. Klarman tracks for survivability under recession scenarios.

### Metric 5: Interest Coverage Ratio

**Formula**: EBITDA / Interest Expense.

**Thresholds**: >= 10x strong (significant cushion); 5-10x adequate; 2-5x watch-list; < 2x distress (potential covenant breach risk).

**Application**: Marks's "permanent loss probability" risk lens demands interest coverage robustness. A company with 1.5x interest coverage entering a recession faces existential risk; 10x+ entering a recession has runway.

### Metric 6: EV/EBITDA (Enterprise Multiple)

**Formula**: Enterprise Value / TTM EBITDA. EV = Market Cap + Total Debt - Cash.

**Thresholds**: Sector-relative (semiconductors trade 15-25x; consumer staples 12-18x; software 25-50x). Use percentile within sector rather than absolute number.

**Application**: Burry's signature metric (he distrusts P/E as "deceptive"). Bottom-decile EV/EBITDA within sector = potential deep-value setup. Top-decile = either elite quality or peak-cycle risk.

### Metric 7: PEG Ratio

**Formula**: P/E divided by EPS-growth-rate (5-year forward consensus growth, or 5-year historical CAGR if forward not available).

**Thresholds**: <= 0.5 strong (Lynch fast-grower setup); <= 1.0 reasonable (Lynch GARP); 1-2 fair; >= 2 expensive on growth-adjusted basis.

**Application**: Lynch's signature metric -- "any company that grows at 25% trading at 25x earnings is reasonably priced." Caveat: PEG fails for cyclicals (use cycle-adjusted EPS) and for compounders with sustainable hyper-growth (PEG can be 0.3 = anomalously cheap).

### Metric 8: SBC / Revenue (Stock-Based Compensation Dilution)

**Formula**: Stock-based compensation expense / Revenue (annual basis).

**Thresholds**: < 3% acceptable for tech; 3-7% caution (real cost obscured in non-GAAP); >= 10% red flag (true profitability significantly overstated by GAAP); >= 15% extreme dilution risk.

**Application**: Munger + Buffett historically refuse SBC-heavy businesses. The "non-GAAP profitability" of many SaaS companies vanishes when SBC is treated as the cash-equivalent expense it is. Track 5-year SBC trend: rising = increasing dilution; falling = maturing capital-allocation discipline.

### Metric 9: Buyback Yield

**Formula**: (Dollar value of shares repurchased - Dollar value of shares issued via SBC and offerings) / Market Cap.

**Thresholds**: > 0% positive (net buybacks); > 3% strong; > 5% aggressive (potential value-destruction risk if at peak P/E). Compare to 10-yr average to detect cycle bias.

**Application**: Faber's shareholder-yield framework treats buyback yield + dividend yield as combined return-of-capital. Buffett tracks buyback timing -- buying at low P/E creates value, buying at peak P/E destroys it. The average S&P 500 company has bought back at top-quartile P/E historically (value destruction).

### Metric 10: Capex / D&A (Reinvestment Intensity)

**Formula**: Capital Expenditures / Depreciation and Amortization.

**Thresholds**: > 1 reinvestment mode (growing the business); = 1 maintenance mode (stable); < 1 harvest mode (under-investing or in decline).

**Application**: Lynch tracks capex-to-D&A trend per category. For fast growers, > 1.5x is expected (capacity expansion). For stalwarts, ~1.0x is healthy. For slow growers, < 1.0x harvesting cash is acceptable. Sudden capex spike at cycle peak = warning sign (semis 2000, energy 2014 capex bubbles).

### Metric 11: Short Interest %

**Formula**: Shares Sold Short / Float. Days-to-Cover = SI / Average Daily Volume.

**Thresholds**: < 5% normal; 5-10% elevated (some bear thesis); 10-20% high; > 20% extreme (potential short-squeeze setup OR genuine bear thesis worth investigating).

**Application**: Cohen's catalyst-driven approach uses short-interest as momentum signal -- declining SI = bear-thesis fading; rising SI = bear-thesis strengthening. Burry weaponized short interest in the 2005-2007 subprime trade. /invest treats > 10% SI + < 2 days-to-cover as squeeze-risk; > 10% SI + > 5 days-to-cover as legitimate-bear-thesis.

### Metric 12: Insider Cluster Buys (Form 4 Discretionary)

**Formula**: Count of distinct C-suite or board-level individuals making open-market purchases (NOT 10b5-1 scheduled trades) within rolling 30-day window. Threshold: 3+ insiders, $250K+ aggregate.

**Source**: OpenInsider screener at `http://openinsider.com/screener?s={TICKER}&xp=1&xs=1&cnt=100` (use Bash + curl with User-Agent, NOT WebFetch).

**Empirical evidence**: Cohen, Malloy, Pomorski (2012), Jeng, Metrick, Zeckhauser (2003), and SEC research (2025) consistently show 8-11 percentage points of 12-month excess returns on tickers triggering cluster-buy criteria. The signal is robust within the first year and degrades after.

**Application**: Strongest single insider signal in academic literature. /invest Phase J-bis treats cluster-buy match as Grade-A confirmation; 10b5-1-only or net selling as neutral noise; mixed pattern as Grade-B requiring per-transaction context (CEO selling for divorce settlement vs CFO selling at all-time-highs are qualitatively different).

## 5-Method Valuation Triangulation

Per Damodaran 2026 framework, every equity analysis should triangulate value across 5 independent methods, with material disagreement (>30% spread) requiring explicit reconciliation:

1. **EV/Sales** (multiple-based, growth-adjusted): useful for early-stage / pre-profitability
2. **EV/EBITDA** (multiple-based, capital-structure-neutral): Burry's preferred; sector-relative
3. **P/E** (earnings-based, equity-investor lens): pair with PEG for growth adjustment
4. **FCF Yield** (cash-flow-based): Klarman + Burry preference
5. **DCF** (discounted-cash-flow-based, intrinsic-value-grounded): requires explicit assumptions on growth, terminal multiple, WACC

When 4 of 5 methods agree directionally (cheap / fair / expensive bands), confidence is high. When spread exceeds 30%, surface in Decision Sheet as "valuation methodology disagreement -- model-X says cheap, model-Y says expensive, reconciliation: ___" before producing BUY/SELL/HOLD rating.

Historical-percentile band: compare current multiple vs trailing 5-year and 10-year percentiles. Sub-25th percentile = cheap relative to history (warrant deeper investigation). Above-75th percentile = expensive relative to history (require thesis explaining premium).

## SECTION 10: FORWARD-EARNINGS BRIDGE (EPS<0 composite substitute; ratified 2026-06-07)

The standard Composite Quality Score (Piotroski + Altman + Beneish + ROIC + EV/EBITDA-valuation, weighted in /invest K-bis.1) silently assumes positive trailing earnings: on a negative-trailing-EPS name Piotroski's profitability points auto-zero, ROIC goes negative and floors, and EV/EBITDA is undefined (EBITDA<0). A healthy unprofitable grower therefore scores ~25-35 and is wrongly auto-routed to SELL/HOLD by the K-bis.5 tiers. This section defines the substitute that fires ONLY for STRUCTURALLY pre-profit names. v1 SCOPE: structural growers only; cyclical-trough and pre-revenue names are fenced out (Steps 1-2) -- the cyclical mid-cycle normalized-earnings bridge is deferred to v2. The positive-EPS path is unchanged (this section is never consulted when trailing operating income > 0).

### 10.1 Detection trigger (ROUTING -- runs for ALL names BEFORE scoring_path is assigned)

Anchor = trailing TTM OPERATING income (NOT GAAP EPS -- operating income catches the "GAAP-positive-via-non-operating-gains while operations burn" trap, e.g. a Yandex-style revaluation gain). Apply the Section 10.2 data-integrity gate (normalize corrupted/aggregated TTM figures) BEFORE evaluating this tree.

**MASTER INVARIANT (closes the inverse-leak found in Phase-2 verification 2026-06-07):** `positive-eps-standard` is reachable ONLY when trailing TTM operating income >= 0. ANY name with TTM operating income < 0 routes to pre-revenue-guard OR negative-eps-bridge -- NEVER positive-eps-standard. This is the unchanged local composite route, not a statement that original Piotroski signals become undefined on losses: its positive-profit signal scores zero when the condition fails. Each other metric retains its own denominator and industry applicability checks. The tree below can never violate this.

Decision tree:

- STEP 1 -- Pre-revenue/negligible fence: if TTM revenue < $20M OR EV/Sales > 100x -> PRE-REVENUE GUARD (10.5); composite N/A; rating NR. STOP.
- STEP 2 -- Cyclical fence: if TTM revenue is LOWER than 2 years ago OR the last 4 fiscal years include >=1 loss FY AND >=1 positive-operating-income FY -> CYCLICAL. Missing history is unknown, not zero or proof of non-cyclicality. This synchronizes the operative sign-mixed rule already in /invest and its skeptic (cb79d1fe940232c83278c27c038b57dced2608c3, 2026-06-10); it changes no numerical threshold or score band. Then split on CURRENT op-income: (a) if TTM operating income >= 0 (a still-profitable cyclical) -> positive-eps-standard + a "cyclical -- mid-cycle normalized read" note; (b) if TTM operating income < 0 (cyclical IN LOSS; v1 has no normalized-earnings bridge) -> negative-eps-bridge with a "cyclical-trough; mid-cycle bridge deferred to v2; declining-revenue caveat" note (bearish-safe: a declining-revenue name scores low on the growth factor -> conservative composite). STOP.
- STEP 3 -- NBIS-trap detection: if GAAP net income > 0 but operating income < 0 (non-operating income > 50% of GAAP NI) -> force negative-eps-bridge (do NOT let a positive headline EPS route to the positive-EPS path).
- STEP 4 -- if TTM operating income < 0 -> negative-eps-bridge. (Anti-hysteresis: the trailing-4-quarter-average-op-margin < -5% test and the prior-cycle scoring_path govern only the BOUNDARY for a name TRANSITIONING OUT of the bridge -- to RETURN to positive-eps-standard a name needs TTM operating income >= 0; a name merely oscillating near breakeven stays on the bridge until TTM op-income turns positive. This prevents flip-flop WITHOUT ever routing a current loss-maker to the standard path.)
- ELSE (TTM operating income >= 0) -> scoring_path = positive-eps-standard; the standard K-bis.1 composite runs verbatim.

Record scoring_path (positive-eps-standard | negative-eps-bridge | pre-revenue-guard | cyclical-fallback) in the analysis frontmatter so Phase J.5 compares PATH (a routing change is "not apples-to-apples").

### 10.2 Data-integrity gate (runs in K-bis.1 before the composite; negative-eps-bridge path only)

(a) Share count: if the data source's TTM weighted-average diluted shares > 1.5x the latest quarterly period-end diluted shares, use the period-end figure; EV and all per-share metrics use CURRENT shares (guards the EDGAR weighted-avg aggregation artifact). (b) TTM plausibility: if any TTM line item > 4x the largest single quarter, fall back to summing the 4 most recent quarters (guards corrupted TTM aggregates).

### 10.3 Bridge forensic composite (replaces the K-bis.1 forensic leg for negative-eps-bridge names)

Five growth-quality anchors (weights sum to 100; each 0-100). Altman Z is DROPPED from the composite (its negative-EBIT + negative-retained-earnings bias misclassifies cash-rich growers as distressed) and instead feeds the solvency gate; the runway score is the better pre-profit solvency signal.

| Weight | Factor | Normalization |
|---|---|---|
| 25% | Revenue-growth trajectory | <10%=0; 10-19%=20; 20-39%=50; 40-59%=75; >=60%=100 |
| 20% | Gross-margin level + trend | level (<20%=0; 20-30%=25; 30-40%=50; 40-55%=75; >55%=100) averaged with trend (+/-5pts per 100bps QoQ) |
| 20% | Cash runway (months) | <6=0; 6-12=20; 12-18=40; 18-24=60; 24-36=80; >36=100 |
| 20% | Path-to-profitability | FY+3 still negative=0; FY+3 positive=50; FY+2 positive=75; FY+1 positive=100 (cap 50 when consensus-only / Grade-C) |
| 15% | EV/Sales (forward, growth-adjusted) | 2D table below |

EV/Sales 15% factor (growth-adjusted; penalize nosebleed multiples IN-score, not just in prose):

| EV/Sales (fwd) | growth >40% | growth 20-40% | growth <20% |
|---|---|---|---|
| <5x | 90 | 80 | 60 |
| 5-10x | 70 | 60 | 40 |
| 10-20x | 50 | 40 | 20 |
| 20-40x | 40 | 25 | 0 |
| 40-70x | 20 | 10 | 0 |
| >70x | 0 | 0 | 0 |

Bridge forensic = sum(weight x factor). It occupies the K-bis.1 (forensic) slot; K-bis.2 framework rotation (using the Pre-Profit Grower category in Section 13: Druckenmiller / Cohen / Marks) occupies the other slot; K-bis.3 reconciliation (50/50) and the K-bis.5 tiers are UNCHANGED -- the corrected composite flows through them numerically.

### 10.4 Valuation basis + R/R target (forward-P/E is unusable; use EV/Sales + path-to-profitability)

Forward consensus EPS can be negative or breakeven for 1-2 years even on a healthy grower, so forward-P/E is NOT the valuation basis for this route. Revenue x operating margin produces operating income, not enterprise value. Use the supported operating-FCFF model with explicit taxes, reinvestment, forecast duration and funded terminal growth, or an explicitly justified and scoped multiple; then bridge enterprise value to equity and divide by the matching projected diluted shares. If a non-GAAP operating-profit forecast excludes SBC expense, subtract that excluded expense to reconstruct GAAP operating profit, then reconcile every other adjustment separately. Avoid charging the same economic SBC cost twice across cash flow, dilution and equity claims. The historical 50-60% execution haircut is an uncalibrated local scenario assumption, not a measured success probability; disclose it and test alternatives rather than inventing probability precision. Existing >25% share-growth disclosure and projected-dilution requirements remain. R/R-target gating is unchanged: for any name with EV/Sales > 50x, the R/R target = MIN(analyst PT, supported fundamentals-derived fair value) -- a BUY may not rest on a Grade-B/C consensus PT alone. EV/Sales > 50x additionally requires a STRONG-BUY-grade justification in the Variant View. If a defensible value is unavailable, withhold only the conclusions requiring that target. Forward EPS = a Grade-C distant-year (profitable-by-FY+N yes/no) sanity check only. See [[ref-valuation-applicability]] for inspected primary-source scope and a reproducible example.

### 10.5 Solvency guard + pre-revenue guard (the wrong-BUY firewall)

SOLVENCY (a SCORED gate -- evaluated only on the negative-eps-bridge path; runway is not computed on the positive path, so it is inert there). Implemented as a K-bis.5 condition alongside the THESIS-STATUS GATE (additive, bearish-only):
- runway < 4 quarters AND no committed financing -> rating UPSIDE capped at HOLD (downside open).
- runway < 2 quarters -> max rating SELL (distress).
- runway 4-8 quarters AND composite >= 60 -> BUY allowed with a "runway-constrained; next raise is a kill-criterion" note.

PRE-REVENUE / negligible-revenue (Step 1): bridge composite NOT computable; composite = "N/A (pre-revenue)"; rating = NR (no rating -- narrative-only; an explicit non-tier state, NOT a 6th WATCH tier). Exception: a pre-revenue name with runway < 12mo -> SELL (data-gated distress). NR is excluded from the Phase-R Brier calibration and rendered as a non-tier by downstream consumers.

### 10.6 Worked example A -- RKLB (healthy grower; the failure the bridge fixes)

RKLB TTM revenue $679.6M (+46% YoY), gross margin 36.6% (+930bps, expanding), operating income -$225.6M, cash ~$1.2B (~28-month runway), ~605M shares (~96x EV/Sales), forward EPS FY26 -$0.11 / FY27 breakeven / FY28 first profit, analyst PT $103.91 vs ~$110 price.
- Standard path (broken): Piotroski ~2-3/9, ROIC negative, EV/EBITDA undefined -> composite ~26 -> wrong SELL.
- Bridge: forensic = .25(75) + .20(61) + .20(80) + .20(75) + .15(0 -- ~96x is >70x) = ~62; framework (Druckenmiller 4/5 + Cohen 3/5 + Marks 3/5) = ~70; composite ~66 (BUY band). Solvency: 28mo runway > 4Q -> no cap. R/R: ~96x > 50x -> target = MIN($103.91 PT, fundamentals fair value); both at/below the ~$110 price -> R/R fails 3:1 -> demoted to HOLD. Result: a defensible HOLD (real grower, but ~96x sales with no consensus upside), NOT the wrong SELL.

### 10.7 Worked example B -- the wrong-BUY firewall

A burner with revenue +70% YoY, GM 45% (growth-quality composite ~75 on growth alone) but cash giving < 2 quarters runway and no committed financing: the K-bis.5 solvency gate caps it at SELL (runway < 2Q) -- growth does NOT score it into BUY. Pre-revenue names (no/negligible revenue, e.g. a pre-commercial issuer) -> composite N/A -> NR, never a fundamental BUY.

## Kernel bands block (machine-readable; INVEST KERNEL 2026-07-06)

The frontmatter `bands:` block is the machine-readable mirror of this
document's interpretation bands, read by the /invest kernel at runtime
(Phase D.8) and enforced by `tools/doctrine-lint.py` (same lint invariants as
the ref-portfolio-doctrine `doctrine:` block: schema + provenance-quote
agreement + registered-fingerprint match). Values are transcriptions of this
file's own prose -- the quotes below are verbatim substrings of it. The
`red_*` keys define the kernel's FORENSIC RED-BAND (the override-lane
cleanliness test, D14, ratified by
*decision-invest-kernel-doctrine-2026-07-06* (not published)): a name is NOT forensically
clean if Piotroski <= 2, Altman Z < 1.81, Beneish M > -1.78, or Sloan
accruals > +10%; an N/A panel (e.g. crypto) counts as NOT clean.

Registered fingerprint: `48ee1308` (ratified by *decision-invest-kernel-doctrine-2026-07-06* (not published)).

| key | value | verbatim_quote | source |
|---|---|---|---|
| altman_z.distress_lt | 1.81 | Safe >2.99, Distress <1.81 | self |
| altman_z.red_lt | 1.81 | Safe >2.99, Distress <1.81 | self |
| altman_z.safe_gt | 2.99 | Safe >2.99, Distress <1.81 | self |
| beneish_m.clean_lt | -2.22 | M < -2.22 | self |
| beneish_m.manipulator_gt | -1.78 | Manipulator >-1.78 | self |
| beneish_m.red_gt | -1.78 | Manipulator >-1.78 | self |
| piotroski.long_gate_gte | 6 | Require >= 6 for long positions | self |
| piotroski.red_lte | 2 | Strong >= 8, Weak <= 2 | self |
| piotroski.strong_gte | 8 | Strong >= 8, Weak <= 2 | self |
| piotroski.weak_lte | 2 | Strong >= 8, Weak <= 2 | self |
| sloan_accruals_pct.negative_gt | 10 | High accruals (>10%) | self |
| sloan_accruals_pct.positive_lt | -10 | Low accruals (<-10%) | self |
| sloan_accruals_pct.red_gt | 10 | High accruals (>10%) | self |

## Related
*investing-moc* (not published) | *ref-sector-benchmarks* (not published) | *ref-research-insights* (not published) | [[ref-investor-frameworks-2026]] | *decision-invest-kernel-doctrine-2026-07-06* (not published)

---
categories: [sources]
type: reference
target_path: Atlas/sources/investing/ref-valuation-methodology.md
created: 2026-06-10
updated: 2026-09-13
status: active
confidence: high
tags:
  - topic/valuation
  - topic/reverse-dcf
  - topic/implied-expectations
  - topic/negative-eps-bridge
aliases:
  - valuation methodology
related:
  - "*investing-moc* (not published)"
  - "[[ref-scoring-models]]"
  - "*ref-portfolio-doctrine* (not published)"
  - "[[ref-investor-frameworks-2026]]"
  - "*ref-memory-storage-cycle-deep-dive* (not published)"
---

# Valuation Methodology

This document is the canonical worked-formula reference for valuation methods in the per-ticker analysis skill. It complements `ref-scoring-models` (forensic scores: Piotroski, Altman, Beneish, Greenblatt) and goes deeper on implied-expectations logic, reverse-DCF mechanics, the EV/Sales 2D grid, the negative-earnings bridge, and risk/reward derivation. Every numeric example uses **ILLUSTRATIVE placeholder inputs** -- these examples do not establish current market inputs. Durable formulas are separate from dated equity-risk premiums, sector observations and quoted evidence; verify each time-sensitive input before current analysis.

Current-use boundary (2026-09-13): this inherited synthesis is not wholly
source-verified. The inspected scope and reproduced operating-FCFF examples in
[[ref-valuation-applicability]] govern that method's current use. Other historical
regressions, practitioner heuristics and numeric tables below remain candidates
until their original specification, inputs and applicability are checked. The
frontmatter confidence label does not certify them. Ratified scoring policy stays
with [[ref-scoring-models]]; unsupported recipes cannot set a recommendation target.

## Table of Contents
1. Implied-Expectations Framework
2. Reverse-DCF Mechanics
3. Multi-Stage DCF Discipline
4. The EV/Sales 2D Grid, Formalized
5. Negative-Earnings Bridge Valuation
6. Cyclical Valuation
7. Growth-Adjusted Multiples
8. Sum-of-the-Parts + Look-Through
9. Margin of Safety, Formalized
10. Target/Stop/Risk-Reward Derivation Standard
11. Method-Selection Decision Tree
12. Reconciliation Discipline

---

## 1. Implied-Expectations Framework

The expectations-investing framework, developed by Alfred Rappaport and Michael Mauboussin (*Expectations Investing*, revised ed., Columbia University Press, 2021), inverts conventional valuation. Instead of forecasting cash flows to estimate value and comparing to price, the analyst starts with the known quantity -- price -- and solves for the financial performance the price embeds. Mauboussin (2021) frames the skill as "determining how high the bar is set for the high jumper," with the second skill being judging how high the jumper can actually leap. Rappaport and Mauboussin (2021) call the embedded assumptions **price-implied expectations (PIE)**.

The theoretical anchor is that all cash-generating assets are priced as the present value of distributable cash. Mauboussin and Callahan ("Everything Is a DCF Model," Morgan Stanley Counterpoint Global, 2021) argue that even multiple-based shorthands implicitly embed a DCF; "you have to earn the right to use a multiple." John Burr Williams (*Theory of Investment Value*, 1938), quoted by Mauboussin and Callahan (2021), anticipated reverse engineering: investors "may transpose the new formulas and use the actual market price as a datum... and deduce the particular rate of growth, the particular duration of growth... implied by the actual market price."

The core decomposition of shareholder value follows Rappaport (*Creating Shareholder Value*, rev. ed., 1997):

```
Corporate Value = PV(Free Cash Flow over forecast period) + PV(Continuing Value)
FCF_t = Sales_{t-1} x (1 + g) x OPM x (1 - Tax) - Incremental Investment
Equity Value = Corporate Value + Non-operating Assets - Debt - Other Claims
```

| Variable | Definition |
|---|---|
| `g` | Sales growth rate |
| `OPM` | Operating profit margin |
| `Tax` | Cash tax rate |
| `Incremental Investment` | Incremental fixed + working capital investment to support growth |
| `Continuing Value` | Value beyond the explicit/market-implied forecast period |

Rappaport and Mauboussin (2021) emphasize three **value triggers** -- sales, operating costs, investments -- that flow into the **value drivers** (sales growth, operating margin, incremental investment rate). They stress that "not all expectations revisions are equal": changes in revenue expectations are most frequent, largest in magnitude, and have the biggest share-value impact, while margin and discount-rate revisions matter less, especially for high-growth names (Mauboussin, 2021).

A distinguishing concept is the **market-implied forecast period (MIFP)** -- the number of years a company must generate value-creating cash flows (returns above cost of capital) to justify the current price. Rappaport and Mauboussin (2021) report the market average exceeds ten years, supporting their dictum that "investors make short-term bets on long-term outcomes."

**ILLUSTRATIVE worked example.** Suppose a placeholder company "AlphaCo" trades at an enterprise value of $100B with WACC of 8%. The analyst holds sales, margin, and investment drivers fixed at consensus and solves for the MIFP: the number of forecast years of excess-return cash flows whose PV plus continuing value equals $100B. If that solves to ~14 years, the analyst then asks: *is AlphaCo's competitive advantage durable enough to sustain excess returns for 14 years?* If the franchise plausibly fades within 8 years, the price embeds optimistic duration and the name is a candidate SELL/avoid. If the moat plausibly endures 20 years, expectations are beatable.

**When this beats point-estimate DCF.** A forward DCF requires the analyst to forecast every driver -- false precision that Klarman (1991) and Mauboussin (2021) both warn against. Implied-expectations analysis localizes judgment to the *one or two drivers where the analyst's view differs from the market* (usually revenue), then asks whether the market's embedded assumption is too high or too low. This is the right tool when (a) point forecasts are unreliable (high uncertainty, long duration), (b) the analyst wants a falsifiable thesis ("the market is pricing 25% revenue CAGR; I believe 15% is more likely"), and (c) for the consuming skill's positive-EPS names where the binding question is what the price *implies* -- e.g., the AVGO-class question of what a given breakeven price implies about embedded AI-growth expectations. It is the doctrinal foundation for grounding TARGETS in implied bands rather than analyst price targets (see sec. 10).

---

## 2. Reverse-DCF Mechanics

A reverse DCF holds the valuation model identical to a forward DCF but treats price as the input and one driver as the unknown. Rappaport and Mauboussin (2021) and Mauboussin and Callahan (2021) describe the procedure; the *Expectations Investing* companion site (expectationsinvesting.com) provides a reference spreadsheet and a worked Domino's Pizza case.

**The solver identity.** For a single-stage approximation solving for the implied perpetual FCF growth rate:

```
EV = FCF_1 / (WACC - g_implied)
=> g_implied = WACC - (FCF_1 / EV)
```

For a finite-horizon solve (solving for revenue growth `g` that equates discounted FCF + terminal value to EV):

```
EV = SUM_{t=1}^{N} [FCF_t / (1+WACC)^t] + TV_N / (1+WACC)^N
FCF_t = Rev_{t-1}(1+g) x OPM x (1-Tax) - DeltaInvestment_t
Solve numerically for the single driver (g, OPM, or N) that sets the equation = EV
```

| Variable | Definition |
|---|---|
| `EV` | Current enterprise value (market input) |
| `FCF_t` | Free cash flow to the firm in year t |
| `WACC` | Weighted-average cost of capital (see sec. 3) |
| `g_implied` | Solved-for growth the price embeds |
| `OPM` | Operating margin |
| `N` | Forecast horizon (or solve for the MIFP) |
| `TV_N` | Terminal value at year N |

**ILLUSTRATIVE worked example.** Placeholder "BetaCo": EV = $50B, WACC = 9%, year-1 FCF = $1.5B. Single-stage implied growth: g = 0.09 - (1.5/50) = 0.09 - 0.03 = **6.0%** perpetual FCF growth embedded. The analyst then benchmarks: is 6% perpetual FCF growth above or below a defensible long-run estimate? Per Chan, Karceski, and Lakonishok (*Journal of Finance*, 2003), there is "no persistence in long-term earnings growth beyond chance," so a perpetual 6% real-terms assumption sits near the high end of what base rates support and should be treated skeptically.

**Sensitivity table template (ILLUSTRATIVE).** Always present implied growth as a function of the two most uncertain inputs:

| WACC (down) / Yr-1 FCF -> | $1.3B | $1.5B | $1.7B |
|---|---|---|---|
| 8.0% | 5.4% | 5.0% | 4.6% |
| 9.0% | 6.4% | 6.0% | 5.6% |
| 10.0% | 7.4% | 7.0% | 6.6% |

The cells are illustrative implied-growth solutions; the construction recipe is: fix all other drivers, vary the two axis inputs across a plausible band, and report the solved driver in each cell.

**Common solver pitfalls.**
1. **FCF definition mismatch** -- comparing your implied number to the market's requires consistent FCF (FCFF with WACC, or FCFE with cost of equity). Wall Street Prep (2024) notes levered vs. unlevered confusion is the most frequent error.
2. **Terminal-value dominance** -- Damodaran Online (2024, per Sofer Advisors) finds terminal value is 60-80% of EV; a reverse DCF that solves only for near-term growth while letting an unexamined terminal assumption carry the value is uninformative.
3. **Implied growth above GDP in perpetuity** -- Wall Street Prep (2024) flags that a perpetual growth rate above long-run nominal GDP (~=2-3%) implies the firm eventually exceeds the whole economy.
4. **Over-precision** -- Mauboussin (2021) urges "precisely imprecise" modeling: ball-park everything except the one or two drivers where your view is differentiated (usually revenue).
5. **Ignoring reinvestment** -- solving for high growth without the matching incremental investment overstates FCF; Rappaport (1997) ties growth to investment via the incremental investment rate.

For the consuming skill, the reverse DCF is the primary engine for the positive-EPS path's TARGET derivation and for stating a falsifiable variant-perception thesis.

---

## 3. Multi-Stage DCF Discipline

When an explicit forward DCF is warranted (stable, profitable names; cross-checking a reverse DCF), discipline in stage design and terminal-value bounding is what separates a defensible model from a garbage-in exercise.

**Stage design.** A standard three-stage structure: (1) explicit high-growth stage (3-5 years), (2) fade/transition stage where growth and margins converge toward maturity (5-10 years), (3) terminal/steady state. Damodaran (Ch. 8, *Investment Valuation*) and Wall Street Prep (2024) recommend the explicit period run until the business reaches a normalized steady state; an explicit period that is too short is a frequent error (Mauboussin and Callahan, 2021).

**Fade rates.** Excess returns (ROIC - WACC) must fade toward zero as competition erodes advantage. This is grounded in Chan, Karceski, and Lakonishok (2003): high growth is "relatively rare" and unpredictable, so assuming persistently high growth "rest[s] on shaky foundations." A disciplined model fades revenue growth linearly toward GDP and ROIC toward WACC over the transition stage.

```
g_t = g_high - (g_high - g_terminal) x (t - N_high) / (N_fade)   for the fade stage
Terminal Value (Gordon) = FCF_{N+1} / (WACC - g_terminal)
Terminal Value (Exit Multiple) = Metric_N x Exit Multiple
```

| Variable | Definition |
|---|---|
| `g_high` | Initial high-stage growth |
| `g_terminal` | Perpetual growth (<= long-run nominal GDP, ~2-3%) |
| `N_high`, `N_fade` | Lengths of high and fade stages |
| `Exit Multiple` | Comps-derived EV/EBITDA at maturity |

**Terminal-value bounds as a % of EV sanity check.** Multiple practitioner sources converge: terminal value is typically 60-80% of total EV (Valuation Master Class, 2024; Sofer Advisors citing Damodaran Online, 2024; Macabacus, 2024, which notes ~75% in a 5-year DCF and ~50% in a 10-year DCF). **House rule:** if TV exceeds ~80% of EV, lengthen the explicit period or re-examine terminal growth. Always cross-check the two terminal methods against each other -- Wall Street Prep (2024) shows backing out the implied perpetuity growth from an exit multiple (e.g., an 8.0x exit => 2.3% implied growth) as the standard sanity check.

**WACC estimation for retail use.**

```
WACC = (E/V) x Ke + (D/V) x Kd x (1 - Tax)
Ke = Rf + beta x ERP
```

| Variable | Definition |
|---|---|
| `Ke` | Cost of equity (CAPM) |
| `Rf` | Risk-free rate (long-term government bond) |
| `beta` | Equity beta vs. market index |
| `ERP` | Equity risk premium |
| `Kd` | Pre-tax cost of debt; `E/V`,`D/V` market-value weights |

For the ERP, Damodaran ("Equity Risk Premiums: Determinants, Estimation, and Implications -- The 2025 Edition," SSRN, March 2025) recommends the **implied ERP** (the IRR equating the present value of expected index cash flows -- dividends plus buybacks -- to the index level) over the historical average, which fails in data-poor markets. He has estimated and published a monthly implied ERP for the S&P 500 since September 2008; in "The Price of Risk: With Equity Risk Premiums, Caveat Emptor!" (Musings on Markets, Aug 2023) he wrote, "I used the equity risk premium of 5.00% that I estimated for the US at the start of July 2023, for the S&P 500." His "Data Update 2 for 2025" reports a January 1, 2025 implied ERP of 4.33%, with an implied expected return on the S&P 500 of 8.91%. For retail use, a practical band is Rf plus an implied ERP of roughly 4.3-5.5%; sector discount rates (Business Initiative, 2025) commonly run 12-18% for technology, 8-12% for manufacturing, 6-10% for utilities.

**Base-rate evidence on analyst growth-forecast error.** This is the single most important external check. Chan, Karceski, and Lakonishok (2003) find IBES long-term growth forecasts are "too optimistic and have low predictive power." Dechow, Hutton, and Sloan (2000) document systematic over-optimism in sell-side long-term forecasts around equity offerings. Bradshaw et al. (2010) and Lacina et al. (2010) find analysts' long-term forecasts are *inferior to naive random-walk models*. The Federal Reserve (Sharpe et al., FEDS 2002) found realized 5-year growth spreads compress to roughly half the forecast spread. Van Binsbergen, Han, and Lopez-Lira (*Review of Financial Studies*, 2023) show machine-learning forecasts are statistically unbiased while analyst forecast errors rise with horizon (mean errors from 0.028 to 0.384). **Discipline rule:** haircut analyst LTG inputs toward base rates, and never let a DCF rest on consensus growth without a base-rate reality check.

---

## 4. The EV/Sales 2D Grid, Formalized

This section formalizes the EV/Sales-vs-growth-and-margin eyeballing the bridge path currently uses into a constructible grid.

**The algebraic spine.** EV/Sales is an exact decomposition:

```
EV/Sales = Operating Margin x (EV/EBIT)
P/Sales  = Net Margin x (P/E)
```

The margin term is a tautological identity (it cancels); this is why Damodaran (Ch. 20, *Investment Valuation*, "Revenue Multiples") states the profit margin is the key determinant of revenue multiples, with growth and cost of capital determining the multiple *applied to* that margin. Mauboussin and Callahan ("Valuation Multiples," Morgan Stanley Counterpoint Global, 2024) derive the same chain from the Gordon model: warranted EV/EBITDA x (EBITDA/Sales) = EV/Sales, "follow[ing] Aswath Damodaran's exposition."

**The compact justified formula** (Gordon-form, from Damodaran Ch. 20):

```
EV/Sales = After-tax Operating Margin x [ (1 - RIR)(1 + g) x (1 - (1+g)^n/(1+WACC)^n) / (WACC - g) + terminal term ]
```

| Variable | Definition |
|---|---|
| `RIR` | Reinvestment rate (growth / ROIC) |
| `g` | Revenue growth |
| `n` | High-growth duration |
| `WACC` | Cost of capital |

**Historical regression transcription -- not an admitted current model.** The following coefficients were attributed to Damodaran's market-wide regression (NYU Stern, "Market Regressions," January 2024). The original data, variable definitions and fit have not been re-inspected in this correction pass. Multiplication is made explicit below; coefficients and decimal scaling still require original-source verification before computation.

```
EV/Sales = 3.81 + 9.86*g + 8.19*(Operating Margin) - 1.60*DFR - 5.88*(Tax rate)
(t-stats 29.7 / 19.5 / 25.1 / 7.4 / 13.4; R^2 = 36.0%)
```

Conditional on that unverified transcription and holding the other regressors fixed, +10 percentage points of growth adds 0.986x and +10 percentage points of operating margin adds 0.819x. These are algebraic marginal changes, not causal effects or contemporary justified multiples. The inherited January 2005 transcription is `EV/Sales = 0.182*g(rev) + 0.0861*(After-tax Operating Margin) - 0.0256*(Debt/Capital) - 0.0013*Reinvestment, R^2 = 48.3%`; its scaling and complete specification are also unverified. It is not a two-driver model: debt and reinvestment appear explicitly. Preserve date, sample, units, intercept and every fitted regressor when reproducing any empirical model.

For software specifically, the relationship is well documented though not in a single clean academic two-variable fit: VEECEE (2017) regressed EV/forward-revenue on growth across 44 listed SaaS names and reported `EV/Fwd Rev = 2.13 + 11.64 x growth rate`. Software Equity Group publishes a Weighted Rule of 40 = (1.33 x revenue growth) + (0.67 x EBITDA margin), with public SaaS scoring >40% posting median EV/Revenue of 12.4x. Aventis Advisors ("Rule of 40 in SaaS: 2026 Data") finds that "SaaS companies that clear the Rule of 40 on an FCF basis trade at a median 4.8x EV/Revenue, versus 2.7x for those that fail, a 74% premium"; their fitted sensitivity drifts by snapshot (~=+1.1x EV/Revenue per +10 Rule-of-40 points in the Q4 2025 update, vs. ~2.2x in Q4 2024 and ~0.8x in Q1 2025; their 2026 EBITDA-basis fit maps roughly +0.7x per +10 points, n=48). Bessemer/Meritech's two-factor "Rule of X" work (2024) finds growth should be weighted ~2-2.3x FCF margin, with R^2 to EV/NTM-Revenue of ~0.62.

**Grid-construction recipe (requires a complete, reviewed model specification).**
1. Choose axis 1 = forward revenue growth bands (e.g., 10%, 20%, 30%, 40%).
2. Choose axis 2 = terminal operating-margin proxy (or current gross margin as a ceiling proxy for pre-profit names) bands (e.g., 20%, 40%, 60%, 80%).
3. Compute each cell from one complete operating-FCFF specification, including growth path, margins, taxes, reinvestment, discount path and terminal assumptions. Divide its enterprise value by the explicitly chosen revenue period. Use `tools/fis/valuation.py` within its supported scope and retain its assumptions/results. Do not drop regressors from an empirical fit or treat a dated cross-sectional association as an intrinsic-value formula.
4. Sanity-check cell values against Damodaran's January 2026 sector table (psdata.html): total US market EV/Sales = 3.97 at 12.75% pre-tax operating margin; Software (System & Application) 11.41x at 33.21% margin; Semiconductor 15.70x at 35.31% margin; Computer Services 1.48x at 7.63% margin. A cell that implies software-level multiples for a sub-10% margin business is mis-specified.

**PRESERVED, UNVERIFIED illustrative grid** (historically labelled justified EV/Sales; WACC 9%, n = 10, ROIC 20%). The original terminal-growth, tax and transition specifications were incomplete, so these cells cannot currently be independently reproduced and are not accepted valuation inputs. Use the reproducible synthetic example in [[ref-valuation-applicability]] instead.

| Growth (down) / Op Margin -> | 20% | 40% | 60% |
|---|---|---|---|
| 10% | 1.6x | 3.2x | 4.8x |
| 20% | 2.8x | 5.6x | 8.4x |
| 30% | 4.4x | 8.8x | 13.2x |

**Usage contract for pre-profit names.** For negative-EPS names, the terminal operating margin is *not observable*, so use current gross margin as the upper-bound proxy and require an explicit, defended path to the terminal margin used (see sec. 5). The grid yields a justified EV/Sales; multiply by forward revenue to get justified EV, then bridge to equity (subtract net debt, adjust for convertibles per sec. 5). Flag any cell whose implied terminal margin exceeds the sector's best-in-class as a red-flag thesis.

---

## 5. Negative-Earnings Bridge Valuation

The negative-EPS bridge path scores pre-profitability names (AI-infrastructure buildouts with heavy capex and convertible debt; space/launch names) on a 0-100 composite. This section formalizes the components.

**Unit economics.** The foundational test is whether incremental revenue is value-creating. For subscription/recurring models: LTV/CAC and CAC payback. The arithmetic identity is net margin x P/E = equity market value / revenue (P/Sales): 30% x 20 = 6x P/Sales and 5% x 20 = 1x P/Sales. These are not EV/Revenue multiples unless the enterprise-to-equity bridge makes them equal. Converting to EV/Revenue requires net debt and other non-common-equity claims on a consistent basis. The inherited sleeperthoughts (2021) attribution does not establish original-source inspection or a justified multiple.

```
LTV = (ARPA x Gross Margin) / Churn Rate
CAC Payback (months) = CAC / (ARPA x Gross Margin)
Burn Multiple = Net Burn / Net New ARR
```

| Variable | Definition |
|---|---|
| `ARPA` | Average revenue per account |
| `Churn Rate` | Periodic revenue/logo churn |
| `Net Burn` | Cash expenses - cash revenue |
| `Net New ARR` | Incremental annual recurring revenue |

Bessemer/practitioner convention: a Burn Multiple below 1x is elite; above 3x is a red flag (IdeaProof, 2026).

**Rule-of-40 variants.** McKinsey ("SaaS and the Rule of 40," Aug 2021) analyzed more than 200 software companies between 2011 and 2021 and found businesses "exceeded Rule of 40 performance only 16 percent of the time," with top-quartile SaaS companies generating "nearly three times the multiples" of the bottom quartile (the popular "strongest single predictor of SaaS valuation multiples" phrasing traces to secondary commentators such as Windsor Drake, 2026, not McKinsey itself). Variants: growth + EBITDA margin; growth + FCF margin (more conservative for capex-heavy names); SEG's weighted form (1.33 x growth + 0.67 x margin). McKinsey's 40-company B2B sample found that those "with NRR of 120 percent or more also have higher multiples--with a median EV/revenue of 21-fold compared with ninefold for those below the 120 percent mark."

**Path-to-profitability discounting.** Forecast to the first normalized-margin year, value the business at maturity on a steady-state FCF or EV/EBITDA multiple, then discount back. This is the EV/Gross-Profit life-cycle method (sleeperthoughts, 2021): "forecast far into the future, apply a steady-state margin profile, and discount back." For an theme-alpha name guiding to EBITDA-positive in a stated year, anchor the maturity valuation to that guide and discount at an elevated rate (see margin of safety, sec. 9).

```
Value_0 = [Terminal EBITDA x EV/EBITDA_mature] / (1 + r)^T - PV(cumulative burn to year T)
```

**Dilution-adjusted per-share math for convertibles.** Convertible structures require if-converted accounting (ASC 260; Deloitte DART, 2024). When the conversion price is below the share price and conversion is dilutive, add the conversion shares to the denominator AND add back the after-tax interest to the numerator (Financial Edge, 2024). For valuation (point-in-time, not weighted-average), use fully diluted shares including all in-the-money converts and the treasury-stock-method effect of options/warrants (Wall Street Prep, 2024).

```
Diluted Shares = Basic + In-the-money Converts (if-converted) + TSM net option shares
TSM net shares = Options x (1 - Strike/Share Price)   [if Strike < Price]
Net Debt = Debt - Nonoperating Cash
Per-share Value = (Justified EV - Net Debt - Other Non-common Claims) / Diluted Shares
```

Cash is already included in net debt and must not be added twice. An equivalent
bridge is EV + nonoperating cash - debt - other claims. Reconcile the convertible
scenario consistently: do not subtract debt that the scenario assumes converted
while also adding its conversion shares. The if-converted interest add-back is
an EPS calculation rule, not a cash addition to enterprise value. See
[[ref-valuation-applicability]] for the inspected bridge scope and reproduced V2.
The [March 2020 Damodaran corporate-finance FAQ, questions 9-10](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/cfemailspr20.html)
defines net debt and reconciles enterprise value with debt, equity and cash;
that definition was inspected on 2026-09-13. It does not validate every
convertible instrument or historical practitioner rule in this section.

**Burn-runway haircuts.** Cash runway = cash on hand / net monthly burn (Wall Street Prep, 2024; CFI, 2024). Carta's own current fundraising guidance (carta.com/learn) advises planning "for a runway of at least 24 to 30 months," noting that the median Series A raiser in Q4 2024 "had waited 774 days (about 2.1 years) since its previous round" and a Q2 2024 Series B raiser waited "a record median length of 856 days (nearly 2.5 years)" -- i.e., between-round intervals have lengthened, raising the runway bar. **Haircut rule:** names with <12 months of runway face dilution risk; founders raising under 9 months take 20-40% valuation haircuts (IdeaProof, 2026). Translate runway into a discount on justified equity value proportional to expected dilution.

**Mapping to the 0-100 composite.** The inherited suggested 25/20/25/20/10 allocation to unit economics, Rule-of-40, profitability, runway and EV/Sales is HISTORICAL AND NONOPERATIVE. It conflicts with the ratified factors and weights in [[ref-scoring-models]] Section 10 and must not produce a score or recommendation. Use that canonical owner's unchanged bridge composite; this reference neither replaces its factors nor ratifies new values. Heuristic runway/burn examples above require their own original-source and applicability review before current use.

---

## 6. Cyclical Valuation

Cyclical normalization can materially change valuation when reported earnings sit near a peak or trough. This general method reference establishes no current holding or portfolio weight. Cite the *normalization method* here; dated cycle research lives in `ref-memory-storage-cycle-deep-dive` and requires current evidence before application.

**Why trough P/E screens expensive and peak P/E screens cheap.** At a cyclical trough, earnings collapse toward zero, so P/E spikes to a huge or meaningless number -- the stock looks "expensive" exactly when it is cheapest. At the peak, earnings are inflated, so P/E looks low -- "cheap" exactly when it is most dangerous. This inversion is why earnings-multiple screens are actively misleading for deep cyclicals and why normalization is mandatory.

**Normalized earnings construction.** Damodaran ("Ups and Downs: Valuing Cyclical and Commodity Companies," SSRN, 2009) gives three standard procedures:
1. **Absolute averaging** -- average dollar earnings over a full cycle (Graham recommended >=10 years; Damodaran says 5-10). Disadvantage: understates for growing firms.
2. **Relative/margin averaging** -- average the margin (or ROIC) over the cycle and apply it to *current* revenue or capital. Preferred for growing cyclicals because it reflects current scale (Damodaran, 2009; GuruFocus, 2015).
3. **Sector averaging** -- use sector-average margins when firm history is short; less precise.

```
Normalized Operating Income = Mid-cycle Operating Margin x Current Revenue
Mid-cycle Margin = average(Operating Margin) over a full cycle (5-10 yrs)
Normalized NOPAT = Cycle-average ROIC x Current Invested Capital
```

| Variable | Definition |
|---|---|
| `Mid-cycle Margin` | Cycle-averaged operating margin |
| `Cycle-average ROIC` | Mean return on invested capital across the cycle |
| `Current Revenue / Invested Capital` | Most recent period's scale |

**Consistency rule.** Ahern (2024) warns: do not apply a mid-cycle margin to an above-trend (peak) revenue figure, or you re-import the cycle you tried to remove. Either normalize both revenue and margin, or use current revenue with explicit acknowledgment. Treat mid-cycle margin as a *range*, not a point.

**Cycle-average ROIC.** For commodity/cyclical names, regress operating income on the key commodity price over the cycle (Damodaran's 2009 Exxon example regresses operating income on oil price per barrel, finding a strong relationship for large stable firms, weaker for smaller evolving ones). Use the regression to estimate income at a normalized commodity/price level.

**P/B-vs-ROE for deep cyclicals.** When earnings are too volatile to normalize cleanly, book value is more stable, so the justified P/B framework (Gordon-derived) is more robust:

```
Justified P/B = (ROE - g) / (Ke - g)
```

A firm earning ROE above its cost of equity warrants P/B > 1; below, P/B < 1 signals value destruction (IB Interview Questions, 2024). Damodaran (Ch. 19, *Investment Valuation*) reports a cross-sectional regression `PBV = 0.88 + 0.82-Payout + 7.79-Growth - 0.41-Beta + 13.81-ROE, R^2 = 0.65`, and notes Wilcox (1984) found a strong log-linear P/B-ROE relationship across 949 Value Line stocks. The Footnotes Analyst (2021) cautions that high R^2 in P/B-vs-ROE charts is partly mechanical (book value appears in both axes), so use it as a cross-check, not a sole tool.

**ILLUSTRATIVE memory-IDM-shaped example.** Placeholder "MemCo": 10-year operating margins ranged 5% (trough) to 45% (peak), mean ~= 24%. Current annual revenue (placeholder) $30B. Normalized operating income = 24% x $30B = $7.2B. If the current *reported* margin is 38%, the firm is operating above mid-cycle, so reported earnings overstate normalized earnings by ~58%, and any trailing P/E understates true cyclical risk. The verdict swings on whether the analyst judges the current print as mid-cycle (normalize near reported) or cycle-top (haircut toward the $7.2B normalized figure). House discipline: present *both* the normalized and reported valuations and state the cycle-position assumption explicitly as the decisive variable.

---

## 7. Growth-Adjusted Multiples

Multiples are DCF shorthands (Mauboussin and Callahan, 2021); growth-adjusted variants attempt to make them comparable across growth rates.

**PEG ratio and its failure modes.** PEG = (P/E) / (annual EPS growth %). Popularized by Peter Lynch, it is, per Investopedia/Wikipedia, "only a rough rule of thumb." Documented failure modes:
1. **Ignores the time value of money** -- FA Magazine (2017, "The Fallacy Of PEG Ratios") shows mathematically the PEG implicitly assumes a zero discount rate.
2. **Omits ROE/required return** -- Wikipedia notes PEG "fails to factor in return on equity or the required return."
3. **Breaks at low growth** -- Cabot Wealth (2023) gives the reductio: a 1%-grower would warrant a 1x P/E, which is nonsensical; Conagra at 3% growth and 10x earnings shows a 3.3x PEG that mislabels a reasonable stock "expensive."
4. **Assumes constant growth** -- extrapolates near-term growth indefinitely; pandemic fast-growers (Zoom) flipped to negative growth, destroying apparent PEG bargains (Cabot, 2023).
5. **Estimate fragility** -- one quarter can swing the growth input (FasterCapital).

**EV/EBITDA-to-growth.** A capital-structure-neutral alternative. CFA Institute (2026) confirms the fundamental drivers of justified EV/EBITDA are expected FCFF growth (positive), profitability (positive), and WACC (inverse). Dividing EV/EBITDA by growth corrects the same growth-comparability problem as PEG while avoiding net-income distortions from leverage and D&A.

```
EV/EBITDA-to-Growth = (EV / EBITDA) / (EBITDA growth %)
PEG = (P/E) / (EPS growth %)
EV/GP = EV / Gross Profit
```

**EV/GP for early names.** When EBITDA is negative or near-zero, EV/EBITDA is meaningless and even EV/Sales is distorted by differing margin structures (sleeperthoughts, 2021). EV/Gross Profit normalizes for the fact that a dollar of 80%-gross-margin SaaS revenue is worth far more than a dollar of 15%-gross-margin retail revenue. Wall Street Prep (2024) confirms EV/Revenue is the standard for early-stage unprofitable names, but EV/GP is the sharper instrument when gross-margin profiles differ widely across the comp set.

**When multiples ARE the right tool.** Mauboussin and Callahan (2021): you "earn the right to use a multiple" when you can demonstrate the link between the multiple and value drivers (excess returns on growth, competitive advantage, cost of capital). Multiples are appropriate (a) for relative valuation within a tight, mature comp set with similar growth/margin/risk, (b) as a fast cross-check on a DCF, and (c) for the terminal value in a DCF. They are *inappropriate* as a standalone tool for deep cyclicals (sec. 6), for businesses with divergent margin structures (use EV/GP), or where the implied driver assumptions go unexamined.

**ILLUSTRATIVE example.** Placeholder "GammaCo": P/E 30, EPS growth 20% => PEG 1.5 (looks rich). But its EV/EBITDA is 18 with 25% EBITDA growth => EV/EBITDA-to-growth 0.72, and the firm carries net cash. The EV-based read corrects a leverage-driven distortion in the P/E and suggests the P/E-based PEG overstated expensiveness -- illustrating why cross-checking growth-adjusted multiples across the capital structure matters.

---

## 8. Sum-of-the-Parts + Look-Through

SOTP values a diversified company as the sum of its independently-valued segments, then nets corporate items and applies (or tests for) a conglomerate discount.

**Segment SOTP discipline.**
```
SOTP Equity Value = SUM (Segment EV via segment-appropriate multiple/DCF)
                    + Non-operating assets + Investment stakes (marked)
                    - Net debt - Corporate overhead capitalized - Minority interest
Conglomerate Discount = (SOTP Value - Market Cap) / SOTP Value
```

| Variable | Definition |
|---|---|
| `Segment EV` | Each segment valued on its own comp set / margins / growth |
| `Investment stakes` | Equity holdings marked to market or fair value |
| `Corporate overhead` | Unallocated costs capitalized as a drag |
| `Minority interest` | Claims of non-controlling holders |

Each segment must be valued with *its own* method -- a high-margin software segment on EV/Sales or EV/GP (sec. 4, sec. 7), a cyclical segment on normalized earnings (sec. 6), a mature cash segment on EV/EBITDA. Capitalize unallocated corporate overhead as a negative, and mark investment stakes/associates explicitly (look-through).

**Conglomerate-discount evidence.** The classic finding is a discount: Lang and Stulz (1994) show diversified firms have lower Tobin's Q than focused peers; Berger and Ofek (1995) quantify a value loss; Servaes (1996) corroborates. Practitioner ranges cluster at 10-20% of SOTP value (LegalClarity, 2024; Wall Street Mojo; IB Interview Questions, 2024, which cites 10-20% for diversified industrials and notes the GE/Honeywell/3M/Emerson/Danaher separation wave). Research Affiliates ("Everything Everywhere All at Once," 2023) reports the historical diversification discount at 13-15%.

**But the discount is contested.** Villalonga (2004, "Diversification Discount or Premium? New Evidence from the Business Information Tracking Series") shows that correcting for sample-selection bias, the discount becomes a *premium*; Campa and Kedia (2002) and Graham, Lemmon, and Wolf (2002) show firms often traded at discounts *before* diversifying (self-selection), and that half or more of the apparent discount is a data artifact. Research Affiliates (2023) document that modern mega-cap "conglomerates" (Alphabet, Amazon, Apple, Microsoft) trade at an average ~70% *premium* to the synthetic sum of their segments. **House interpretation:** treat the conglomerate discount as conditional -- apply a 10-20% discount for genuinely unrelated, complexity-penalized, capital-misallocating structures; do not assume a discount for well-run, pricing-power businesses, where a premium may be warranted. The discount is an activist catalyst when it exceeds the value of keeping segments together (IB Interview Questions, 2024).

**ILLUSTRATIVE example.** Placeholder "DeltaCorp": Segment A (software) $40B EV, Segment B (hardware, cyclical, normalized) $25B EV, a marked 20% stake in a listed associate worth $8B, net debt $10B, capitalized corporate overhead -$3B. SOTP equity = 40 + 25 + 8 - 10 - 3 = **$60B**. If market cap is $48B, the implied discount is (60-48)/60 = **20%** -- at the upper edge of the empirical range, a potential activist/breakup setup if the segments are genuinely unrelated; but if DeltaCorp's segments share a platform and pricing power, the "discount" may simply reflect that the synthetic marks are too high (Villalonga, 2004).

---

## 9. Margin of Safety, Formalized

The margin of safety (MoS) is the buffer between price paid and conservative intrinsic value -- the cornerstone of value investing from Graham forward.

**Graham-to-Klarman lineage.** Benjamin Graham (*The Intelligent Investor*, 1949) distilled "the secret of sound investment into three words: MARGIN OF SAFETY," and (with Dodd, *Security Analysis*, 1934) defined intrinsic value as a *range* -- analysis "needs only to establish that the value is adequate... or considerably higher or lower than the market price." Graham and Dodd's convention was a 30-50% discount (CFA Institute, 2015). Warren Buffett ("The Superinvestors of Graham-and-Doddsville," 1984) gave the engineering analogy: "When you build a bridge, you insist it can carry 30,000 pounds, but you only drive 10,000-pound trucks across it." Klarman (*Margin of Safety*, 1991) widened it: "A margin of safety is achieved when securities are purchased at prices sufficiently below underlying value to allow for human error, bad luck, or extreme volatility," and personally targets discounts of 50%+. Klarman ties the size of the demanded discount to *uncertainty*: "high uncertainty is frequently accompanied by low prices."

**Modern quantifications.** GuruFocus (2023) and CFA Institute (2015) report most prudent value investors demand 20-30%; Graham himself ~30%+; Klarman 50%+ for higher-risk names. The Tren Griffin framing (in Mauboussin and Rappaport, 2021) restates MoS as "a discount to expected value," directly linking it to the implied-expectations framework (sec. 1).

**Uncertainty-scaled MoS formula.**
```
Required MoS = Base MoS + Uncertainty Premium
Buy Price <= Intrinsic Value x (1 - Required MoS)
Uncertainty Premium = f(forecast dispersion, duration, balance-sheet fragility, cyclicality)
```

| Variable | Definition |
|---|---|
| `Base MoS` | Floor discount for a stable, profitable name (e.g., 20-25%) |
| `Uncertainty Premium` | Additive discount scaling with thesis uncertainty |
| `Intrinsic Value` | Conservative central estimate (reverse-DCF band, normalized earnings, or SOTP) |

**House scaling rule (ILLUSTRATIVE bands).**
- Stable profitable name (positive-EPS path, low cyclicality): Required MoS ~= 20-25%.
- Cyclical name (normalization uncertainty, sec. 6): ~= 30-40%.
- Negative-EPS bridge name (path-to-profitability + dilution risk, sec. 5): ~= 40-55%.

**ILLUSTRATIVE worked example.** Placeholder bridge name "EpsilonAI": grid-justified equity intrinsic value (sec. 4, sec. 5) = $40/share central estimate, wide dispersion ($25-$60 band), <12 months runway. Base MoS 25% + uncertainty premium 25% = required MoS 50%. Buy price <= $40 x (1 - 0.50) = **$20/share**. For a stable profitable name with intrinsic value $40 and a tight band, required MoS 22% => buy <= **$31.20**. The wider MoS for the bridge name operationalizes Klarman's (1991) insight: the buffer must scale with what you do not and cannot know.

---

## 10. Target/Stop/Risk-Reward Derivation Standard

The house standard is a **3:1 minimum reward-to-risk for a BUY**, computed as (Target - Current) / (Current - Stop). This section grounds each leg in method rather than analyst price targets or round numbers.

**Deriving TARGET from implied-expectations bands (not analyst PTs).** Per sec. 1-sec. 2, the target is the price at which the analyst's *differentiated* expectations are fully reflected. Procedure:
1. Run the reverse DCF to extract the market's implied driver (usually revenue growth).
2. Substitute the analyst's defended driver estimate (base-rate-checked per sec. 3).
3. Re-solve the DCF forward to a fair value -- this is the **expectations-revision target**: the price if the market revises to the analyst's view.
4. Cross-check against the sec. 4 grid (justified EV/Sales) and sec. 6/sec. 7 multiples.

This replaces "analyst PT + multiple re-rating hand-wave" with a falsifiable, model-grounded target.

```
Target = Fair Value implied by analyst's driver set (reverse-DCF re-solve)
Stop   = Invalidation price where the thesis driver is proven wrong
Reward-to-Risk = (Target - Current) / (Current - Stop)
BUY requires R/R >= 3.0
```

| Variable | Definition |
|---|---|
| `Target` | Expectations-revision fair value (sec. 1-sec. 2), grid-cross-checked (sec. 4) |
| `Stop` | Price marking thesis invalidation, not a round number |
| `Current` | Entry/current price |

**Stop placement tied to invalidation, not round numbers.** The stop should sit at the price level that corresponds to the *thesis being wrong* -- e.g., for a cyclical, the price implied by trough normalized earnings (sec. 6); for a bridge name, the price implied by a failed path-to-profitability or a dilutive down-round (sec. 5); for a moat thesis, the price implied by a shortened MIFP (sec. 1). This is the structural analog of the trading principle that moving stops destroys the math (TradeZella, 2026).

**Base-rate justification for the 3:1 hurdle.** The reward-to-risk ratio sets the breakeven win rate: Breakeven Win Rate = 1 / (1 + R/R) (JournalPlus, 2026; Babypips, 2026). At 3:1, breakeven win rate = 1/(1+3) = **25%** -- the thesis can be wrong 75% of the time and still break even (TradeZella, 2026). Expectancy = (Win% x Avg Win) - (Loss% x Avg Loss); a 40% win rate at 3:1 yields positive expectancy of 0.40x3 - 0.60x1 = **0.60R per trade** (TradingView, 2026). The 3:1 hurdle thus builds in a large error budget against the documented over-optimism of forecasts (Chan/Karceski/Lakonishok, 2003; Dechow et al., 2000) -- precisely the conditions under which a single-user portfolio operates.

**ILLUSTRATIVE end-to-end example.** Placeholder "ZetaCo," current price $100. Reverse DCF shows the market implies 12% revenue CAGR. Analyst's base-rate-checked estimate is 18%; re-solving the DCF forward gives fair value **$160** (Target). Thesis invalidation: if FQ-next revenue growth prints below 10% (confirming the market's lower view), normalized fair value falls to **$80** (Stop). R/R = (160 - 100) / (100 - 80) = 60/20 = **3.0** (pass) -- meets the BUY hurdle. Apply the sec. 9 MoS as a second gate: if required MoS is 25%, the buy-zone ceiling is $160 x 0.75 = $120, so $100 entry also clears the MoS test. **Thresholds that change the verdict:** if the stop widens to $75 (invalidation lower), R/R = 60/25 = 2.4 < 3.0 -> no BUY; if the target compresses to $140, R/R = 40/20 = 2.0 -> no BUY.

---

## 11. Method-Selection Decision Tree

One parseable table mapping company archetype -> primary method -> cross-check -> known failure mode. Machine-readable for the consuming skill.

| archetype | primary_method | cross_check_method | known_failure_mode |
|---|---|---|---|
| Stable profitable compounder | Reverse-DCF implied expectations (sec. 1-sec. 2) | Multi-stage DCF (sec. 3); EV/EBITDA-to-growth (sec. 7) | Over-precision; unexamined terminal value (60-80% of EV) |
| High-growth profitable (premium multiple) | Reverse-DCF + MIFP duration test (sec. 1) | EV/Sales 2D grid (sec. 4); Rule-of-40 (sec. 5) | Assuming persistent high growth (Chan/Karceski/Lakonishok 2003) |
| Negative-EPS pre-profit (SaaS-like) | EV/Sales 2D grid + Rule-of-40 (sec. 4-sec. 5) | EV/GP (sec. 7); path-to-profitability DCF (sec. 5) | Margin-structure distortion; PEG/EV-EBITDA meaningless |
| Negative-EPS capex-heavy infra (convertibles) | Path-to-profitability DCF + dilution-adjusted per-share (sec. 5) | EV/Sales grid (sec. 4); burn-runway haircut (sec. 5) | Ignoring convertible dilution; <12mo runway dilution risk |
| Deep cyclical / commodity (e.g., memory IDM) | Normalized earnings: mid-cycle margin x current revenue (sec. 6) | Cycle-average ROIC; P/B-vs-ROE (sec. 6) | Trough P/E screens expensive; peak P/E screens cheap |
| Capex-depressed FCF (heavy investment phase) | Owner-earnings / normalized FCF DCF (sec. 1, sec. 3) | Reverse-DCF on maintenance capex | Treating growth capex as maintenance; understating FCF |
| Diversified conglomerate / holding co | Sum-of-the-parts + look-through (sec. 8) | Conglomerate discount test (Villalonga 2004) | Assuming a discount where a premium applies |
| Bank / financial (book-driven) | Justified P/B = (ROE-g)/(Ke-g) (sec. 6) | Residual income; P/TBV vs. ROE | EV-based multiples inapplicable; leverage distortion |
| Early-stage divergent gross margins | EV/Gross Profit (sec. 7) | EV/Sales grid with GM proxy (sec. 4) | EV/Sales distorted by margin-mix differences |
| Turnaround / distressed | Liquidation / asset value (Graham net-net) (sec. 9) | Normalized earnings power; SOTP (sec. 8) | Going-concern DCF on an impaired franchise |

---

## 12. Reconciliation Discipline

When the forensic composite (from `ref-scoring-models`: Piotroski, Altman, Beneish, Greenblatt) and the framework valuation (this document) disagree materially, the analyst needs documented rules rather than ad-hoc tie-breaking.

**The >30-point spread rule.** Define both outputs on a 0-100 scale (forensic composite; valuation composite, where 100 = deeply undervalued with high margin of safety, 0 = expectations unbeatable). When |forensic - valuation| > 30 points, flag a reconciliation case and apply the interpretation rules below before acting.

**Spread-interpretation rules.**
1. **High forensic, low valuation (quality is real, price is rich).** The business scores well on accruals/solvency/quality but the reverse DCF shows expectations are already lofty (long MIFP, demanding implied growth). This is the classic "great business, poor stock" case (Mauboussin and Rappaport, 2021). *Verdict: valuation usually wins for the action decision* -- do not BUY a high-quality name whose price embeds unbeatable expectations. Quality justifies a *smaller* MoS (sec. 9), not a waiver of it.
2. **Low forensic, high valuation (looks cheap, but quality flags).** The name screens cheap on the grid/DCF but the forensic layer shows manipulation risk (Beneish M-score), distress (Altman Z), or deteriorating fundamentals (Piotroski). *Verdict: forensic usually wins* -- apparent cheapness is often a value trap or an earnings-quality mirage. The cheap multiple may reflect correctly-priced fraud/distress risk. Klarman (1991) and the forensic literature both counsel that a low price is not a margin of safety if intrinsic value is itself impaired.
3. **Cyclical-driven spread.** If the spread is driven by a cyclical name where normalized vs. reported earnings diverge (sec. 6), the spread is an artifact of cycle position, not a true disagreement. *Verdict: re-run both on normalized inputs before reconciling.* This is the live memory-IDM case: a forensic composite computed on peak earnings will look pristine while a normalized valuation looks expensive -- reconcile on mid-cycle figures.
4. **Bridge-name spread.** For negative-EPS names, assess each forensic model's intended population, accounting inputs and limitations separately. Piotroski's original high book-to-market sample includes loss firms; positive ROA is a scored signal, not an eligibility condition (Piotroski, Selected Paper 84, printed p. 7, footnote 3). Negative earnings alone do not establish Altman inapplicability; model version and intended industry/population must be checked. *Verdict: down-weight the forensic composite; lean on the sec. 5 bridge composite and runway/dilution analysis.*

**Which side wins by archetype.**

| archetype | when_they_disagree_>30 | dominant_side | rationale |
|---|---|---|---|
| Stable compounder | quality high, value low | valuation | price embeds expectations; don't overpay |
| Apparent value / low multiple | value high, quality low | forensic | value-trap / fraud / distress risk |
| Deep cyclical | spread from cycle position | re-normalize first | spread is an artifact (sec. 6) |
| Negative-EPS bridge | inspect component applicability | local bridge composite (sec. 5) | Local routing is separate from original score eligibility; losses do not exclude original Piotroski F-score |
| Turnaround / distressed | value high, Altman low | forensic (asset value) | use liquidation floor, not going-concern |

**Documentation requirement.** Every reconciliation case logs: the two scores, the spread, which interpretation rule applied, the dominant side, and the resulting action. This creates an auditable base-rate dataset: over time, the single user can measure which side actually wins by archetype and update the dominance rules empirically -- the same base-rate discipline (Chan/Karceski/Lakonishok, 2003; Mauboussin, 2021) the rest of this document applies to forecasts.

---

## Sources

- Rappaport, Alfred & Mauboussin, Michael J. *Expectations Investing*, Rev. ed. (Columbia University Press, 2021).
- Rappaport, Alfred. *Creating Shareholder Value*, Rev. ed. (Free Press, 1997).
- Mauboussin, M.J. & Callahan, D. "Everything Is a DCF Model." Morgan Stanley Counterpoint Global (2021); "Valuation Multiples" (2024); "One Job: Expectations and the Role of Intangible Investments" (2020).
- Williams, John Burr. *The Theory of Investment Value* (1938).
- The Motley Fool. "Expectations Investing: A Q&A With Mauboussin and Rappaport" (Jan 2022); CFA Institute, "Book Review: Expectations Investing" (2022).
- Damodaran, Aswath. *Investment Valuation*, Ch. 8, 19, 20; "Equity Risk Premiums -- 2025 Edition," SSRN (Mar 2025); "The Price of Risk: With Equity Risk Premiums, Caveat Emptor!" (Musings on Markets, Aug 2023); "Data Update 2 for 2025"; "Ups and Downs: Valuing Cyclical and Commodity Companies," SSRN (2009); "Market Regressions" (NYU Stern, Jan 2024; MReg05 2005); "Revenue Multiples by Sector" (psdata.html, Jan 2026); "Determinants of Price to Book Ratios."
- Chan, L.K.C.; Karceski, J.; Lakonishok, J. "The Level and Persistence of Growth Rates." *Journal of Finance* 58(2), 643-684 (2003); NBER WP 8282 (2001).
- Dechow, Hutton & Sloan (2000); Bradshaw et al. (2010); Lacina et al. (2010); Sharpe et al., Federal Reserve FEDS (2002); Van Binsbergen, Han & Lopez-Lira, *RFS* 36(6) (2023).
- McKinsey & Company. "SaaS and the Rule of 40: Keys to the critical value-creation metric" (Aug 2021); Windsor Drake, "SaaS Valuation Multiples 2026."
- Software Equity Group, "Gross Profit Margin on SaaS Valuations"/"Rule of 40"; Aventis Advisors, "SaaS Valuation Multiples"/"Rule of 40 in SaaS: 2026 Data"; VEECEE, "The Price of Growth" (2017); sleeperthoughts, "Why EV/Rev is the wrong way" (2021); Bessemer/Meritech, "Rule of X" (2024).
- Wall Street Prep ("Terminal Value", "EV/Revenue Multiple", "Treasury Stock Method", "Cash Runway"); Macabacus; Sofer Advisors (citing Damodaran Online, 2024); Valuation Master Class; Ahern, "Normalizing Through Cycles" (2024).
- CFA Institute, "Margin of Safety: The Lost Art" (2015); "Market-Based Valuation" (2026).
- Graham, B. *The Intelligent Investor* (1949); Graham & Dodd, *Security Analysis* (1934); Klarman, S. *Margin of Safety* (1991); Buffett, W. "The Superinvestors of Graham-and-Doddsville" (1984); GuruFocus (2015, 2023).
- Lang & Stulz (1994); Berger & Ofek (1995); Servaes (1996); Villalonga (2004); Campa & Kedia (2002); Graham, Lemmon & Wolf (2002); Research Affiliates, "Everything Everywhere All at Once" (2023); IB Interview Questions, "Conglomerate Discount"/"P-to-Book Value" (2024); The Footnotes Analyst (2021); Wilcox (1984).
- Deloitte DART, "If-Converted Method"/"Treasury Stock Method," ASC 260 (2024); Financial Edge, "Diluted Shares" (2024); Carta, "Burn Rate"/fundraising guidance (2024); Corporate Finance Institute, "Cash Runway"/"EV to Revenue."
- FA Magazine, "The Fallacy Of PEG Ratios" (2017); Cabot Wealth, "PEG Ratios" (2023); Wikipedia, "PEG ratio."
- TradeZella (2026); JournalPlus (2026); Babypips (2026); TradingView (2026) -- risk-reward/expectancy.
- IdeaProof, "Startup Runway Calculator" (2026); Business Initiative, "DCF / Terminal Value Calculator" (2025).

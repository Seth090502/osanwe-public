# ref-risk-methodology -- /risk formulas, windows, and provenance rules

Read-on-demand companion to `.agents/skills/portfolio/SKILL.md` (same pattern as
ref-kernel-sizing). Owns: the exact math behind every /risk output, the data
contract with factors.db and the wiki/research refs, rounding/attribution law,
worked example skeleton, and known limitations. ASCII only. Arithmetic is local
after current-session broker read acquisition. This
file documents methods only -- it never carries live book values (the
stale-literal failure mode F-R1 applies here too).

## 1. Data contract

### factors.db (Efforts/osanwe-v2-overhaul/_work/factors.db)

SQLite, two tables:

```
bars(ticker TEXT, date TEXT, close REAL, src TEXT)      -- equity trading-day grid
factors(ticker TEXT, date TEXT, factor TEXT, value REAL, text_value TEXT, src TEXT)
                                                        -- ticker='MACRO' rows carry DGS10,
                                                        -- BAMLH0A0HYM2, VIX, WALCL, RRP, SOFR...
```

- Returns: simple close-to-close in a verified common price/return basis.
  Covariance and portfolio tail estimates use one complete shared-date matrix
  across all scored assets, with no forward-fill. A separately reported pairwise
  correlation may use its own disclosed window; do not assemble those pairwise
  estimates into an unchecked portfolio covariance matrix.
- Windows: vol/covariance default = last min(90, available) shared sessions;
  historical-worst scan = last 252 sessions; scenario episodes use the exact
  windows stored in ref-scenario-stress-test.md.
- Known gaps (as of the dated refs): some names have zero bars or an insufficient
  window. Gaps are REPORTED (UNSCORED), never imputed.

### Holdings (current-session broker read evidence)

Actual quantities, basis, account cash and lots require an authorized broker
read in this session. Saved holdings/history files cannot supply missing current
inputs. Missing account or asset-class coverage remains UNVERIFIED; an offline
hypothetical book must be labeled hypothetical throughout.

Reconcile known total value V, scored sleeve value V_s = SUM(scored mv), and
excluded scope. Normalize scored weights w_i = mv_i/V_s, because portfolio_risk
normalizes its input weights. Scale sleeve risk by V_s, never by V after that
normalization. Ratios against V may be shown as a known-total comparison only;
they do not estimate risk of unscored assets or establish whole-book coverage.

### Reference files

ref-scenario-stress-test.md owns episode windows + per-position replay returns
+ pre-committed responses. ref-correlation-matrix-full.md owns pairwise rhos,
clusters, N_eff. Both are regenerated from factors.db after each weekly
ingest-bars run; /risk cites their generation dates and flags when they predate
the latest bars date by more than one calibration cycle.

## 2. Volatility and covariance (R.2/R.3 basis)

Per-name daily return series: r_i,t = close_i,t / close_i,t-1 - 1 over aligned
shared dates.

Sample standard deviation with n-1 denominator:

    sigma_i = sqrt( (1/(n-1)) * SUM_t (r_i,t - mean_r_i)^2 )

Use `tools/fis/covariance.py::estimate_covariance` on the same asset-ordered
matrix R, with explicit method and `annualization=1` for daily covariance C.
Sample covariance is the baseline; OAS, QIS or EWMA need a stated estimation
rationale, and EWMA needs an explicit decay. Report method, observation count,
divisor, centering assumption and conditioning/PSD diagnostics. Neither differing
pairwise windows nor an invented off-diagonal correlation is an observation-
based covariance estimate. Invalid matrices are refused, not silently repaired.

Call `risk_engine.portfolio_risk(w, C, as_of=data_date,
report_date=report_date, n_obs=len(R), covariance_horizon="1 trading day")`.
The function validates C, normalizes long-only weights and reports volatility;
it does not compute portfolio ES or VaR. Use the definitions below and retain
its warnings. Unknown dates remain UNKNOWN; a filename date does not establish
observation freshness. Preserve price basis and data-availability evidence.

## 3. Risk families (R.3) -- daily Gaussian VaR and empirical ES

Scored-sleeve variance on normalized weights:

    sigma_p,d^2 = w' C w
    sigma_p,d   = sqrt(w' C w)

Zero-mean delta-normal comparison (z_0.95 approximately 1.645):

    VaR_1d,95 = z * sigma_p,d * V_s
    VaR_h,95_proxy = sqrt(h) * VaR_1d,95
    ES_1d,95_gaussian = phi(z)/0.05 * sigma_p,d * V_s

The optional Gaussian ES comparison is approximately 2.063*sigma_p,d*V_s.
Label it Gaussian. sqrt(h) assumes serially uncorrelated returns and is a
scaling proxy, not a calibrated multi-period tail forecast.

Primary daily empirical ES uses aligned portfolio losses L_t = -(R_t @ w):

    ES_1d,95_empirical = empirical_expected_shortfall(L, 0.95) * V_s

The executable owner is `tools/fis/risk_engine.py`. With n observations, sort
losses descending, let m = 0.05*n, k = floor(m), f = m-k, and use
`(SUM(L[0:k]) + f*L[k])/m`, omitting the last term when f=0. This includes
fractional boundary mass rather than averaging an arbitrary ceil-sized tail.
An all-gains sample can produce negative ES; do not floor it to conceal that.
State the observation count and thin-tail sample limitation. A fixed current-
weight historical mixture assumes constant weights; it is not realized book P&L.

Daily empirical ES is distinct from Gaussian ES and any sqrt-time proxy. At
most show sleeve risk as a percentage of verified scored value and, separately,
of known V with excluded-risk disclosure. Missing assets are not zero-risk.

## 4. Historical worst day/week (R.4) -- empirical proxy method

True portfolio historical VaR needs a full aligned return history for the
actual weights, which the store does not guarantee for all held names. The
honest approximation:

1. Pick the held broad-index proxy (configured per deployment).
2. Worst single-day return r_min and worst rolling 5-day cumulative return
   R_5min within the last 252 sessions of the proxy's bars.
3. Beta of the equal-weighted held-book daily return series to the proxy's
   (OLS on shared dates, same 252d window): beta = cov(book, proxy)/var(proxy).
4. Scored-sleeve proxy figures: r_min*beta*V_s and R_5min*beta*V_s.
   The equal-weight beta is an explicit proxy assumption, not actual book P&L.
   Missing price windows remain excluded/UNVERIFIED rather than zero-risk.

Labels: "proxy-based historical worst"; LOW-CONFIDENCE flag if >=3 held names
lack the window. Never present these as exact portfolio draws.

## 5. Component VaR and risk contribution (R.7)

Marginal volatility vector m = Cw/sigma_p,d. Component volatility dollars:

    component_vol_i = w_i * (Cw)_i / sigma_p,d * V_s

Component delta-normal VaR at the SAME z and zero-mean model:

    component_VaR_i = z * component_vol_i
    SUM(component_VaR_i) = z * sigma_p,d * V_s = VaR_1d,95

The z factor is required; volatility contribution is not VaR contribution.
Reconcile using unrounded inputs, then round display values. At sigma_p,d = 0,
report zero dollar risk and undefined percentage attribution instead of dividing
by zero. Negative contributions can arise from hedging correlations. These
covariance contributions are not an empirical ES decomposition.

Standalone-vs-component reading: a low-weight high-vol name can still dominate
component VaR through correlations; that contrast is the exposure-mode story.

## 6. Scenario replay arithmetic (R.5)

Given scenario S with per-position replay percentages p_i (from
ref-scenario-stress-test.md, measured on the SAME bars table):

    impact_i = p_i * mv_i            (today's market values)
    impact_S = SUM_i impact_i ; pct_S = impact_S / V

Drift note vs the file's stored PORTFOLIO IMPACT: differences come from price/
weight drift since generation, not method changes. Preserve each explicitly
filed proxy or zero-shock assumption with its dated source. A missing shock is
UNVERIFIED, never zero. Never re-derive an episode window silently; cite the
file's Method section and state excluded positions.

Scenario resolution keys (case-insensitive substring):
rates|1, capex|ai-capex|2, yen|carry|3, credit|hy|4, memory|supercycle|5,
liquidity|6, single-name|earnings|7, china|taiwan|8, winter|9, pivot|bullish|10.

Stored historical portfolio impacts are comparisons only. Read current scenario
percentages and episode windows from their owner; do not treat stored dollar
impacts as current or reuse historical holdings to reproduce them.

## 7. Concentration math (R.6 basis)

Use the covariance/correlation matrix for the actual covered asset set and
disclosed common window. Existing reference figures are historical comparisons
unless that asset set, window and basis match. Preserve missing-data warnings.

- Participation-ratio effective bets: N_eff = (SUM lambda)^2 / SUM(lambda^2)
  over the valid held-sleeve correlation matrix eigen-spectrum. A zero-volatility
  asset has undefined correlation; disclose its handling, never divide by zero.
- For equal-volatility equicorrelated assets only, the variance-equivalent count
  is m / (1 + (m-1)*rho). This is a different statistic, not the participation
  ratio or a universal pessimistic bound.
- Warning threshold: rho > 0.75 between verified HELD names, using dated matrix
  evidence. A saved HELD list cannot establish current position status.
- Doctrine ceilings remain owned by
  `Atlas/sources/investing/ref-portfolio-doctrine.md`; load and quote the current
  machine block without changing its thresholds.

## 8. Attribution & rounding law

- Every number gets one of: `[file.md S#]`, `[corr matrix sec n]`,
  `(computed: formula-id, bars A..B)` -- SKILL.md rule 4.
- Round dollars to nearest $10, percentages to 0.1 (F-R4). Store-precision
  values may be echoed inside citations when quoting a file line verbatim.
- Doctrine text is QUOTED with source; /risk paraphrase must not tighten or
  loosen a threshold.
- UNSCORED items appear in every table they would otherwise distort, marked,
  never silently dropped (F-R2).

## 9. Worked example skeleton (shape only -- no live values)

```
V = SUM(verified mv); V_s = SUM(scored mv)     [current-session broker read]
w_i = mv_i / V_s                             (computed, scored sleeve)
R = complete common-date return matrix       (computed, basis, bars A..B)
C = estimate_covariance(R, method="sample", annualization=1, ...)["covariance"]
sigma_p = sqrt(w' C w)                       (validated daily covariance)
VaR_1d = 1.645 * sigma_p * V_s               (computed: R.3 Gaussian)
VaR_5d_proxy = sqrt(5) * VaR_1d               (computed: R.3 scaling proxy)
ES_1d = empirical_expected_shortfall(-R @ w, 0.95)*V_s  (R.3 daily empirical)
component_VaR_i = 1.645*w_i*(Cw)_i/sigma_p*V_s          (R.7, nonzero sigma)
scenario credit impact = SUM p_i*mv_i        (computed: R.5, stress file S4)
```

## 10. Limitations (state when output is consumed for decisions)

- Delta-normal VaR understates tails; stress correlations exceed 90d Pearson
  (correlation matrix caveats section says the same).
- 90d windows are regime-specific; re-run after any >5% SPY drawdown week.
- sqrt(h) scaling ignores autocorrelation; weekly figures are indicative.
- Proxy-based historical worst inherits index beta error.
- Scenario replay assumes current weights ride through a historical episode --
  no rebalancing, no intrapath response.
- This route measures the covered equity sleeve. Crypto, cash and missing
  account/asset classes must be reconciled separately; equity-only risk is not
  whole-book risk. Missing observation dates remain UNKNOWN/low confidence.

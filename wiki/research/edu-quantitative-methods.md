---
categories: [wiki]
type: reference
status: active
created: 2026-08-24
updated: 2026-08-24
confidence: high
generated: 2026-08-24 by finance-education-corpus subagent (vault-only synthesis)
tags:
  - topic/investing
  - topic/quantitative-methods
  - topic/statistics
  - topic/time-series
  - topic/risk-management
related: ["[[edu-fixed-income]]", "[[edu-accounting-analysis]]", "*edu-behavioral-finance* (not published)", "*edu-portfolio-theory* (not published)", "[[ref-momentum-backtest]]", "[[ref-market-regime-detector]]", "*calibration-2026-08-23* (not published)", "*investing-moc* (not published)"]
---

# Quantitative Methods: Statistical Foundations for Market Work

GENERATED: 2026-08-24. Education-layer reference in this vault's finance
corpus. Covers the statistical machinery behind every backtest, factor model,
volatility estimate, and "is this edge real?" question this vault asks.
The theme throughout: financial data is noisy, non-stationary, and fat-tailed,
so naive statistics systematically overstates confidence. The vault's own
calibration loop (wiki/maintenance/calibration/) exists precisely because
stated confidence ran ~45 points hot against realized outcomes. Companions:
[[edu-fixed-income]], [[edu-accounting-analysis]], *edu-behavioral-finance* (not published),
*edu-portfolio-theory* (not published). Key internal anchors: [[ref-momentum-backtest]],
[[ref-market-regime-detector]], *calibration-2026-08-23* (not published).

## Table of contents

1. Why quant rigor is a survival trait in markets
2. Time series foundations: stationarity
3. ARIMA models for return and level forecasting
4. GARCH volatility modeling
5. Regression analysis for factor exposure computation
6. Hypothesis testing: t-stats, p-values, multiple comparisons
7. Monte Carlo simulation: theory and practice
8. Bootstrap resampling for confidence intervals
9. Cointegration versus correlation
10. Kalman filters for dynamic beta estimation
11. Machine learning in finance: applications and hard limits
12. Common failure modes checklist
13. Vault integration map

## 1. Why quant rigor is a survival trait in markets

### 1.1 The core problem: low signal-to-noise ratio

Daily equity returns have a signal-to-noise ratio that would be laughable in
any physical science. A stock with 20% annualized volatility moves about
1.26% in a typical day (std dev). If a strategy has a genuine expected edge
of 5% per year (already excellent), the daily mean is roughly 0.02%. The
signal is about 60x smaller than the daily noise. Consequences:

- Single-day P/L tells you almost nothing about skill.
- Even a year of results is weak evidence: with 252 observations of something
  whose true Sharpe is 0.3, the sampling error on measured Sharpe is roughly
  sqrt((1 + 0.5*0.09)/252) which is near 0.065 -- your measured Sharpe could
  easily print anywhere from 0.15 to 0.45.
- Anyone showing you a short track record as proof of skill is showing you
  noise, however sincere they are.

### 1.2 The three statistical sins this vault guards against

1. Overfitting: fitting noise because you tried many configurations. Every
   extra parameter, every re-run of the backtest with tweaked inputs,
   consumes degrees of freedom and inflates in-sample performance relative
   to live performance.
2. Multiple comparisons: test 100 random strategies at the 5% level and you
   expect ~5 false positives. If you then showcase the winners, you are
   p-hacking whether or not you intended to.
3. Non-stationarity assumption: relationships estimated on 2015-2019 data
   are not laws of nature. Regimes change; estimated betas decay;
   vol clusters. Any number quoted without a timestamp is suspect.

### 1.3 How this shows up in vault practice

- The calibration loop compares stated confidence to realized outcomes and
  found stated 70-79% confidence overstated by roughly 45 points. That gap
  is exactly what happens when intuition substitutes for base rates.
- Backtests ([[ref-momentum-backtest]]) are treated as evidence about a
  regime, not proof of permanence.
- Kernel stops and doctrine ladders are mechanical rules precisely because
  human judgment under uncertainty degrades under emotion; the statistics
  define the rule, the rule protects the human from himself.

## 2. Time series foundations: stationarity

### 2.1 What stationarity means

A stationary series has distributional properties that do not change over
time:

- Strict stationarity: the joint distribution of any set of observations is
  invariant to time shifts.
- Weak (covariance) stationarity, the practical standard: constant mean,
  constant variance, autocovariance depends only on the lag, not the date.

Prices are NOT stationary: they drift, their variance grows with the square
root of horizon, and their mean is whatever the level happens to be. Returns
(appropriately scaled) are much closer to stationary: no strong trend in the
mean, roughly constant unconditional variance over long samples.

### 2.2 Why it matters

Almost every classical tool -- ARMA models, OLS regression, t-tests --
assumes weak stationarity. Run them on non-stationary levels and you get:

- Spurious regression: two unrelated random walks will show "significant"
  correlation and high R-squared a large fraction of the time. Granger and
  Newbold documented R-squared values above 0.9 between pure noise series.
- Meaningless persistence estimates: autocorrelations that decay slowly and
  suggest memory where none exists.
- Forecast intervals that widen without bound and are useless.

Practical rule: model returns (or log returns) for most work; model price
levels only through models built for unit roots (random walk, ARIMA with
differencing, cointegration frameworks).

### 2.3 Unit roots and testing

A unit root means shocks never die out: today's price permanently embeds
every past shock. Tests:

- Augmented Dickey-Fuller (ADF): regresses the change on lagged level and
  lagged changes; null hypothesis is a unit root. Failing to reject does not
  prove a unit root; it just fails to prove stationarity. Low power in small
  samples -- common in finance.
- KPSS flips the null: null is stationarity. Using ADF and KPSS together
  brackets the answer.
- Practical stance: treat single asset prices as I(1) (integrated of order
  one: stationary after one difference), treat returns as I(0).

### 2.4 Volatility clustering and fat tails: stylized facts

Any honest model of equity returns must respect these empirical regularities:

1. Fat tails: daily returns show kurtosis far above the Gaussian 3 (often
   10-30 for individual names). Extreme days happen far more often than the
   normal distribution predicts.
2. Volatility clustering: large changes follow large changes (of either
   sign). Mandelbrot: "large changes tend to be followed by large changes."
   Autocorrelation of squared returns is positive and decays slowly.
3. Leverage effect: negative returns raise future volatility more than
   positive returns of the same size lower it (equity leverage and volatility
   feedback).
4. Near-zero serial correlation of raw returns at daily frequency (markets
   are close to efficient), yet predictability appears in variance,
   in cross-section (factor premia), and at longer horizons.
5. Aggregational Gaussianity: monthly returns look much more normal than
   daily ones -- tails blend as horizon grows.

Implication: i.i.d. Gaussian assumptions are convenient lies. Use them for
back-of-envelope math, but pair them with fat-tailed stress scenarios and
GARCH-style conditional volatility for anything sizing-related.

## 3. ARIMA models for return and level forecasting

### 3.1 The model family

ARIMA(p, d, q) -- AutoRegressive Integrated Moving Average:

- AR(p): current value is a linear combination of its own p past values.
  y_t = c + phi_1*y_{t-1} + ... + phi_p*y_{t-p} + e_t
- MA(q): current value is a linear combination of the past q shocks.
  y_t = mu + e_t + theta_1*e_{t-1} + ... + theta_q*e_{t-q}
- I(d): the series was differenced d times to achieve stationarity before
  fitting ARMA(p,q) to the differences.

Special cases worth knowing cold:

- Random walk: ARIMA(0,1,0). Best forecast of tomorrow's log price is
  today's price. The null hypothesis for most market prediction claims.
- Random walk with drift: ARIMA(0,1,0) + c. Long-horizon drift dominates.
- Mean-reverting AR(1): y_t - mu = phi*(y_{t-1} - mu) + e_t with |phi| < 1.
  Half-life of a shock = ln(0.5)/ln(phi). E.g., phi = 0.95 implies half-life
  near 14 periods. Used for spread mean reversion in pairs trades.

### 3.2 Identification and fitting

- Choose d by testing: ADF/KPSS on levels and differences. For prices, d=1.
- Inspect ACF/PACF of the stationary series: AR(p) shows geometrically
  decaying ACF and PACF cutting off after lag p; MA(q) the reverse.
- Information criteria (AIC/BIC) select among candidate orders; BIC
  penalizes parameters harder, favoring parsimony.
- Residual diagnostics are mandatory: Ljung-Box test for remaining
  autocorrelation; residual ACF should look like white noise, otherwise the
  structure is unmodeled.

### 3.3 Honest expectations for return forecasting

- Daily returns: ARMA adds almost nothing. Raw-return autocorrelations are
  tiny; transaction costs erase what little is there.
- Where ARIMA-type structure genuinely helps: modeling spreads (pairs),
  macro series (inflation prints, PMIs), inventory/flow series -- places
  with real persistence.
- The realistic value of ARIMA on prices is a calibrated null model: it
  tells you what "nothing special is happening" looks like, so deviations
  stand out.

## 4. GARCH volatility modeling

### 4.1 From unconditional to conditional volatility

An unconditional vol estimate (full-sample stdev) treats 2020 March and a
sleepy August as the same environment. Conditional volatility asks: given
everything up to today, what is vol NOW? Because volatility clusters, the
conditional answer is dramatically better for risk sizing, stop placement,
and option work than the unconditional one.

### 4.2 ARCH and GARCH mechanics

ARCH(q) (Engel 1982): variance today is a weighted sum of past squared
shocks. sigma_t^2 = omega + sum alpha_i * e_{t-i}^2.

GARCH(1,1) (Bollerslev 1986) is the workhorse:

sigma_t^2 = omega + alpha * e_{t-1}^2 + beta * sigma_{t-1}^2

Reading the terms:

- e_{t-1}^2: yesterday's squared surprise -- the news component.
- sigma_{t-1}^2: yesterday's variance -- the persistence component.
- alpha + beta measures persistence; typical equity index fits give
  alpha near 0.05-0.10 and beta near 0.85-0.92, so persistence runs 0.97+
  and shocks decay slowly (half-life of a vol spike of weeks to months).
- Unconditional variance implied by the model: omega / (1 - alpha - beta);
  requires alpha + beta strictly less than 1.

Extensions worth knowing by name:

- EGJR-GARCH / EGARCH: asymmetric response; negative shocks raise vol more
  (leverage effect).
- GJR threshold term: adds an indicator times e_{t-1}^2 when the shock was
  negative.
- Realized GARCH / HAR-RV: use intraday realized variance instead of daily
  squares; HAR (heterogeneous autoregressive) regressions on daily/weekly/
  monthly realized vol are simple and very hard to beat.

### 4.3 Practical uses and cautions

Uses in this vault's context:

- Position sizing proportional to inverse vol or vol targeting benefits
  directly from conditional estimates; using stale full-sample vol means
  oversizing right after calm regimes and undersizing after spikes.
- Stop placement: kernel stops sized off current conditional vol adapt to
  regime rather than averaging across regimes.
- Regime detection ([[ref-market-regime-detector]]): a jump in fitted GARCH
  vol plus elevated correlation is the classic risk-off signature.

Cautions:

- GARCH reacts to shocks with a lag; it confirms regime change after the
  first violent moves. It manages ongoing exposure, it does not predict the
  crash itself.
- Parameter estimates are unstable across windows; refit regularly and
  distrust single-point vol forecasts -- use the forecast distribution.
- Implied vol (option market) often leads realized vol. When both exist,
  compare: implied minus subsequent realized is the variance risk premium.

## 5. Regression analysis for factor exposure computation

### 5.1 Time-series factor regression (the workhorse)

To decompose a strategy's or stock's returns into factor exposures, run:

R_i,t - R_f,t = alpha_i + beta_1*F_1,t + ... + beta_k*F_k,t + e_i,t

with F_j being factor return spreads (e.g., MKT-RF, SMB, HML, momentum):

- alpha: average return left over after paying for factor exposures. The
  only part of performance attributable to skill (or luck) beyond factors.
- beta_j: sensitivity to factor j. Beta 1.2 to the market means the book
  amplifies index moves by 20%.
- R-squared: fraction of return variance explained by factors. An S&P
  proxy fund should show R-squared above 0.99 against the market factor;
  a long/short book might show 0.2-0.5, meaning most variance is idiosyncratic.

Standard errors matter: heteroskedasticity (variance changing over time) and
autocorrelation inflate naive OLS standard errors. Use Newey-West
(HAC) corrections; ignore this and you will declare alphas significant that
are not.

### 5.2 Cross-sectional regression (factor construction)

The other direction: on each date, cross-sectionally regress N stock returns
on characteristics (value score, size, momentum rank). The time series of
the slope coefficients is the factor return; the intercept is that period's
unexplained average return. This is how Fama-French style factors are built
and how you test whether a characteristic prices cross-sectionally.

### 5.3 Rolling windows and instability

Betas are not constants. Practice:

- Estimate rolling 60-252 day windows and watch the path, not just the
  endpoint.
- Weight recent data (exponentially weighted regression) when regimes shift.
- Beware structural breaks: M&A, sector reclassification, business model
  pivot. Post-event beta is a different animal; pooled estimation smears it.

### 5.4 Multicollinearity and interpretation traps

- Factors correlate (momentum and growth, value and quality in some
  regimes). High pairwise correlation among regressors blows up standard
  errors and makes individual betas meaningless even when the model predicts
  fine. Check variance inflation factors; consider orthogonalized factors.
- Regression beta answers "how did this move WITH the factor," not "why."
  Attribution is descriptive; causal claims need events, instruments, or
  experiments.
- Outliers drive betas. One crash week can dominate a 3-year beta. Robust
  regression or winsorizing is defensible; hiding the outlier is not.

## 6. Hypothesis testing: t-stats, p-values, multiple comparisons

### 6.1 The framework in one paragraph

Null hypothesis H0: the effect is zero (no edge, beta equals zero). The test
asks: if H0 were true, how surprising is my sample? The t-statistic is
estimate / standard error; roughly, |t| above 2 corresponds to p below 0.05
under normality, meaning a less-than-5% chance of seeing a result this
extreme if there were truly nothing there. That is ALL a p-value is. It is
not the probability the hypothesis is true, not the probability of
replication, and not an effect-size measure.

### 6.2 Finance-specific distortions

- Non-normal returns: fat tails make naive t-stats overconfident at daily
  frequency. Use longer horizons, bootstrap methods, or robust SEs.
- Autocorrelation: overlapping returns (e.g., 12-month momentum measured
  monthly) shrink the effective sample size dramatically. Newey-West or
  overlapping-window corrections are required, not optional.
- Selection bias: strategies that exist today survived; dead ones were
  buried. Backtests of surviving entities overstate returns (mutual fund
  databases, delisted stocks omitted from price histories -- survivorship
  bias routinely adds 1-2%/yr to naive universes).
- Look-ahead bias: using rebalanced weights, restated fundamentals, or
  point-in-time unavailable data. Fundamentals must be joined on
  availability date, not report date.

### 6.3 The multiple comparison problem (the killer)

Test one strategy, 5% false positive rate. Test K independent strategies,
probability of at least one false positive is 1 - 0.95^K: K=20 gives 64%,
K=100 gives 99.4%. Modern quant research tests thousands of configurations
(data mining bias). Defenses, in increasing strictness:

1. Bonferroni: require p < alpha/K. Brutally conservative; fine for small K.
2. Benjamini-Hochberg: control the false discovery rate (expected share of
   discoveries that are false). Better power when testing many candidates.
3. White's Reality Check / Hansen SPA / deflated Sharpe ratios
   (Bailey, Borwein, Lopez de Prado): explicitly account for the number of
   trials and non-normal returns. The deflated Sharpe ratio penalizes
   measured Sharpe for trial count, sample length, skew, and kurtosis.
4. Out-of-sample discipline: hold out data, touch once. Walk-forward
   validation. Paper trade. Nothing beats fresh data for deflating
   overfit edges.

Vault translation: the calibration loop's finding (stated confidence ~45pt
hot at the 70-79 band) is the lived experience of multiple-comparisons
bias applied to human judgment. Base-rate tables are the correction.

### 6.4 Effect size versus significance

With enough data anything becomes "significant." Always ask: how BIG is the
effect, and does it survive costs? A statistically significant 12bp/year
gross anomaly is worthless after commissions and slippage. Report
Sharpe, turnover, capacity, drawdown alongside every t-stat.

## 7. Monte Carlo simulation: theory and practice

### 7.1 What it is and why finance needs it

Monte Carlo methods answer questions about complicated distributions by
repeatedly sampling randomness and tabulating outcomes. Finance needs MC
because most interesting problems have no closed form: portfolio return
distributions with fat tails and nonlinear derivatives, retirement
drawdown paths with sequence-of-returns risk, barrier options, credit
portfolios, path-dependent strategies.

### 7.2 Theory in brief

- Law of large numbers: sample averages converge to expectations. The
  standard error of a Monte Carlo mean falls like 1/sqrt(N): to halve the
  error, quadruple the paths. 10,000 paths give ~1% accuracy on a standard
  deviation of 1 -- plan path counts accordingly.
- Central limit theorem gives error bars on the MC output itself: always
  report the standard error of your simulated statistic.
- Variance reduction techniques when path counts get expensive:
  antithetic variates (sample both +z and -z), control variates (subtract a
  correlated quantity with known expectation), importance sampling
  (oversample tail regions for tail-risk questions), stratified sampling /
  quasi-random sequences (Sobol) for smoother convergence.

### 7.3 Building blocks for return paths

Two standard engines:

1. Geometric Brownian Motion: dS/S = mu dt + sigma dW. Log-price steps are
   normal; prices stay positive. Fine for illustration, wrong for tails.
2. Bootstrap / block-bootstrap from historical returns: preserves fat tails
   and clustering without parametric assumptions. IID bootstrap loses
   volatility clustering; BLOCK bootstrap (resample contiguous chunks of
   5-20 days) keeps short-range dependence. This is usually the better
   default for portfolio path simulation.

Enhancements that matter:

- Student-t or mixture-of-normals innovations to keep fat tails.
- GARCH-filtered bootstrap: fit GARCH, resample standardized residuals,
  rebuild conditional vol paths -- preserves clustering realistically.
- Correlated multivariate draws via Cholesky decomposition of the
  covariance matrix (watch out: correlation matrices from short samples are
  noisy; shrinkage estimators like Ledoit-Wolf stabilize them).

### 7.4 Practical recipe (pseudo-code shape)

For a portfolio path study:

1. Assemble historical returns matrix (assets x time), point-in-time clean.
2. Choose engine: block bootstrap of historical rows, or GBM/t-innovations
   with shrunk covariance.
3. Simulate N=10k-100k paths over the horizon, applying rebalancing rules
   and cash flows exactly as the strategy would run.
4. Extract the distribution of the metric that matters (terminal wealth,
   max drawdown, probability of ruin, years-to-recovery).
5. Report percentiles (5th, 25th, median, 75th, 95th) and the standard
   error of each. Never report just the mean.

### 7.5 Failure modes

- Garbage assumptions in, confident-looking garbage out: MC lends false
  precision to bad models. The histogram is only as good as the generator.
- Underestimating tails by using normal innovations: the whole point in
  finance is the tails; do not simulate them away.
- Ignoring parameter uncertainty: mu is nearly unestimable at daily
  frequencies. Simulate ACROSS plausible parameter values, not just WITHIN
  one calibration (Bayesian or resampled-efficients approaches).
- Path-dependence amnesia: sequence-of-returns risk means two paths with
  identical terminal wealth can have wildly different lived experiences
  (withdrawals during drawdowns lock losses). Simulate paths, not endpoints,
  whenever cash flows interact with drawdowns.

## 8. Bootstrap resampling for confidence intervals

### 8.1 The idea

The bootstrap (Efron 1979) replaces unverifiable distributional assumptions
with computation: resample your own data (with replacement) thousands of
times, recompute the statistic each time, and use the spread of recomputed
values as the sampling distribution. It answers "how wobbly is this
estimate?" without assuming normality.

### 8.2 Variants

- IID bootstrap: resample observations independently. Good for
  cross-sectional data; WRONG for returns (destroys autocorrelation).
- Block bootstrap: resample contiguous blocks (moving-block or circular).
  Block length 10-20 trading days is a common default for daily returns;
  too-short blocks re-introduce independence, too-long blocks waste data.
- Stationary bootstrap (Politis-Romano): randomized geometric block lengths;
  smooths the arbitrary fixed-length choice.
- Wild bootstrap: designed for regression settings with heteroskedastic
  errors; perturbs residuals rather than observations.
- Bootstrapping pairs (X, Y) jointly in regression preserves the
  relationship; bootstrapping residuals assumes the design is fixed.

### 8.3 Confidence interval flavors

Given B bootstrap replications of statistic theta_hat*_b:

- Percentile interval: [theta*_2.5%, theta*_97.5%]. Simple, slightly
  narrow in small samples.
- Basic (reverse percentile): 2*theta_hat - percentile endpoints.
- BCa (bias-corrected and accelerated): adjusts for estimator bias and
  skewness; the best general-purpose choice when software offers it.
- Standard-error interval: theta_hat +/- z * se_boot; falls back toward
  normal theory.

Rules of practice: B = 2,000-10,000 for intervals (not 200); report WHICH
interval type; remember bootstrap CIs inherit any bias in the original
sample (survivorship, look-ahead) -- resampling cannot launder biased data.

### 8.4 Where the vault uses this thinking

- Confidence intervals on backtest Sharpe/returns: a single-point Sharpe is
  theater. A bootstrap CI says "somewhere between 0.2 and 0.9" and that is
  actionable honesty.
- Calibration percentages: when the calibration loop aggregates outcome
  buckets, the counts are finite; binomial/bootstrap intervals around
  realized hit-rates are why tiny samples should not move stated confidence
  much.
- Factor premia estimates: decade-long samples still carry wide CIs on
  equity premium components; anyone quoting "the" market risk premium to
  two decimals has skipped this chapter.

Worked micro-example: 36 monthly strategy returns with mean 0.8%/mo,
stdev 3.5%/mo. Naive annualized Sharpe = 0.8/3.5*sqrt(12) = 0.79. Bootstrap
the 36 months 5,000 times: the 90% CI on Sharpe plausibly spans roughly
0.1 to 1.5. That width -- not the point estimate -- is the finding.

## 9. Cointegration versus correlation

### 9.1 Definitions and distinction

- Correlation: co-movement of RETURNS over a window. Short-lived, unstable,
  and says nothing about levels.
- Cointegration: a LONG-RUN equilibrium relationship between LEVELS of
  I(1) series. Two non-stationary price series are cointegrated if some
  linear combination a*X_t + b*Y_t is stationary -- the spread wanders but
  is tethered, mean-reverting around equilibrium.

Classic intuitions: spot and futures on the same asset are cointegrated
(cost-of-carry anchors them); ETF and its basket; pairs like KO/PEP share
macro exposure. Two random coins tossed repeatedly have correlated-ish
noise sometimes but no tether; gold and a tech stock may correlate for a
quarter and then diverge forever.

Why it matters: correlation-based hedges decay silently (correlation drifts
toward zero exactly in crashes when you need it); cointegration-based pairs
have a defined equilibrium to trade against -- enter when the spread is
stretched, exit at reversion, and the position has a thesis about LEVELS,
not just co-movement.

### 9.2 Testing and trading workflow

1. Pretest both series: ADF confirms I(1) (non-stationary levels,
   stationary first differences).
2. Estimate the hedge: OLS Y on X gives the vector; or use Johansen's
   procedure for multivariate systems (trace/max-eigen statistics).
3. Test the residual spread with ADF (Engle-Granger two-step). Caveat: OLS
   on I(1) series has biased standard errors; Engle-Granger critical values
   differ from standard ones. Johansen handles multiple series properly.
4. Compute half-life of mean reversion: fit AR(1) on the spread, half-life
   = ln(0.5)/ln(phi). Tradeable pairs usually show half-lives of days to
   weeks; multi-month half-lives demand patience and wider stops.
5. Monitor: cointegration breaks (structural break -- one firm pivots,
   gets acquired, accounting scandal). Track rolling spread z-score and
   set kill criteria BEFORE entry.

Failure mode to respect: cointegration found in-sample dies out-of-sample
more often than advertised. The same multiple-testing discipline from
Section 6 applies -- testing 500 pairs and keeping the 12 that pass ADF is
data mining unless corrected.

## 10. Kalman filters for dynamic beta estimation

### 10.1 The state-space idea

Many finance quantities we quote as constants (beta, hedge ratio, hidden
trend) actually drift. A Kalman filter treats the truth as an unobserved
STATE evolving with noise, observed through noisy measurements, and updates
an optimal estimate every period. State-space form:

- State equation: x_t = A*x_{t-1} + w_t (state evolves, w = process noise)
- Observation equation: y_t = H*x_t + v_t (we see a noisy function of it)

The filter cycles predict -> update: predict the state and its uncertainty
forward, observe the new data point, revise using the Kalman gain K -- the
gain optimally balances trust in the model's prediction versus the new
observation based on their relative uncertainties.

### 10.2 Dynamic beta via state-space regression

Write the CAPM-style relation with a TIME-VARYING beta:

r_t = alpha_t + beta_t * r_m,t + e_t
alpha_t = alpha_{t-1} + u_t        (random-walk coefficients)

The Kalman filter produces, at each date, the posterior mean and variance of
beta_t. Compared with rolling OLS windows, the filter:

- Updates smoothly each day instead of jumping at window boundaries.
- Weights ALL history with exponential decay implicit in the noise
  variances, rather than a brutal cutoff.
- Provides uncertainty bands on beta itself -- you can see when the
  estimate is mush.

Tuning: the ratio of process noise to observation noise controls
responsiveness (higher process noise = faster-tracking, noisier beta).
Estimate these by maximum likelihood rather than hand-tuning when possible.

### 10.3 Other finance applications

- Pairs-trading hedge ratios that adapt as the relationship evolves.
- Nowcasting latent variables: inflation trend from noisy prints, fair
  value from mixed-frequency data.
- Blending signals: treating analyst estimates and trailing fundamentals
  as noisy observations of a hidden "true earnings" state.

Cautions: misspecified noise variances give confidently wrong filters;
non-Gaussian jumps (gaps) violate assumptions -- robust/particle filters
exist for that; and a smooth adaptive estimate can lull you into forgetting
the underlying relationship may break entirely (filters interpolate within
regimes; they do not detect regime death).

## 11. Machine learning in finance: applications and hard limits

### 11.1 Where ML genuinely helps

- Signal extraction from wide, weak features: hundreds of technical,
  fundamental, and alternative-data features with individually tiny
  predictive power. Regularized linear models (LASSO/ridge/elastic net),
  gradient boosted trees, and random forests can aggregate weak signals
  better than hand-picked composites.
- Nonlinearity and interaction effects: momentum behaving differently at
  high vs low vol, value working only outside liquidity crunches -- trees
  find interaction structure without manual specification.
- Text/NLP: classifying filings, transcripts, news sentiment at scale.
- Volatility and microstructure prediction: nearer-term targets with
  stronger signal-to-noise; HAR-style models plus ML do respectable work.
- Execution: optimal order scheduling, slippage modeling -- shorter
  horizons where signal is measurable and feedback loops fast.

### 11.2 The hard limits (learn these before the techniques)

- Low SNR ceiling: financial R-squareds at daily horizons are fractions of
  a percent. ML cannot repeal this; it can only squeeze the last drops.
  Models that look brilliant in-sample have almost always memorized noise.
- Non-stationarity: patterns are adversarially arbitraged. A model trained
  through 2020 may be archaeology by 2024. Retraining cadence and regime
  awareness matter more than architecture choice.
- Small effective sample: 40 years of DAILY data sounds huge; 40 annual
  observations of a regime-level phenomenon is tiny. Cross-sectional depth
  helps (many stocks), time-series breadth does not scale.
- Multiple testing at industrial scale: ML pipelines try thousands of
  configurations. Backtest-overfitting is the default outcome, not the
  exception. Deflated performance metrics, combinatorially purged
  cross-validation (purged k-fold with embargo), and true out-of-sample
  paper trading are the defenses.
- Interpretability debt: a black box that sizes your portfolio is a risk
  you cannot explain to yourself at 3am in a drawdown. Prefer models you
  can interrogate; use SHAP-type attributions as flashlights, not proofs.
- Cost asymmetry: false positives cost real money (trades, turnover); ML
  thresholds must be tuned to economics, not accuracy. 54% directional
  accuracy can be wildly profitable with proper sizing and costs can flip
  58% into a loser.

### 11.3 A sane adoption posture for this vault

ML as instrument panel (better vol estimates, regime classification, text
screens) before ML as pilot (autonomous allocation). Keep human-readable
rules -- doctrine ladders, kernel stops -- as the execution layer; let ML
inform the probabilities those layers consume. This matches the vault's
calibration philosophy: systems compensate for judgment; they do not
replace accountability.

## 12. Common failure modes checklist

Run every quantitative claim through this list before trusting it:

1. Is the series stationary, or did someone regress levels on levels?
2. How many configurations were tried before this one? (multiple testing)
3. Was data truly point-in-time (no survivorship, no look-ahead)?
4. Are standard errors corrected for autocorrelation/heteroskedasticity?
5. Does the effect survive transaction costs and realistic capacity?
6. Is the sample independent of the data used to invent the idea?
7. Are confidence intervals reported, or just point estimates?
8. Do fat tails break the assumed distribution (VaR understated)?
9. Would the rule have been executable emotionally in the worst month?
10. What observable event kills this thesis? (pre-committed falsifier)

Item 10 deserves emphasis: every model in this corpus should ship with its
own kill-switch condition written down in advance -- the quant equivalent of
a stop-loss on beliefs.

## 13. Vault integration map

- [[ref-momentum-backtest]]: applies Sections 5-6 (factor regression,
  multiple-testing discipline) to the vault's own strategy evidence.
- [[ref-market-regime-detector]]: consumes Section 4 (conditional vol,
  clustering) for regime classification.
- wiki/maintenance/calibration/: the empirical audit trail for Section 6.3
  -- realized-vs-stated confidence is multiple-comparison bias measured in
  the wild.
- *edu-behavioral-finance* (not published): behavioral counterpart -- overconfidence is
  the psychological engine of the statistical sins catalogued here.
- *edu-portfolio-theory* (not published) and *ref-portfolio-optimization* (not published): covariance
  estimation (shrinking, Ledoit-Wolf) feeds optimization inputs directly.
- *investing-moc* (not published): map of concepts; this file is the methods backbone.

## Closing summary

Statistics in markets is the art of quantifying humility. Stationarity
discipline keeps you from regressing fiction on fiction. ARIMA mostly
defines the boring null; GARCH earns its keep in conditional risk. Factor
regression separates skill from exposure; hypothesis testing -- done with
multiple-comparison honesty -- separates signal from luck. Monte Carlo and
bootstrap replace false precision with honest intervals. Cointegration
gives pairs a tether; Kalman filters let betas breathe. Machine learning
amplifies process but cannot manufacture signal that is not there. Every
technique here reduces to the same operating principle this vault runs on:
state your belief, attach your uncertainty, pre-commit your falsifier, and
let realized outcomes recalibrate you.


---

## Related vault data

Where each statistical tool is already running on vault data:

- [[ref-momentum-backtest]] and [[ref-strategy-backtest-results]] --
  backtesting discipline: zero-lookahead queries, honest costs, survivor-
  ship flags; Sections 6 and 12 applied to live strategy claims.
- [[ref-market-regime-detector]] -- regime classification over 1,056
  sessions; transition matrices estimated with Section 6's standards.
- [[ref-composite-scoring]] -- composite construction whose factor sleeves
  lean on Section 5's regression logic.
- [[ref-correlation-matrix-full]] -- estimation noise and shrinkage
  questions from Sections 5 and 9 visible in the live matrix.
- *ref-theme-detection* (not published) -- text-mining theme extraction; Section 11's ML
  limits stated as an operating rule.
- [[ref-alternative-data-signals]] -- signal mining where multiple-
  comparison honesty decides what survives.
- *ref-synthetic-benchmarks* (not published) -- hypothesis testing applied to the vault's
  own alpha claims against indices 1 through 12.

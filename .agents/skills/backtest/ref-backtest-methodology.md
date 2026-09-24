# Backtest methodology reference (companion to /backtest)

Why the metric block is computed the way it is, what each bias flag means, and
the known limitations of backtesting against this vault's factor store.
ASCII only. This document describes a SIMULATION tool; all results are
hypothetical and past performance does not guarantee future results.

## 1. Store contracts (from tools/factor-store.py)

- `bars(ticker, date, close, src)` -- one row per ticker-day of closes,
  PRIMARY KEY (ticker, date). Historical inventory: ~107 tickers x ~1255 trading days (2021-08 ..
  2026-08) plus longer crypto series; order ~130k bar rows total.
- `factors(ticker, date, factor, value, text_value, src)` -- regime/factor
  observations (FRED: VIXCLS, UNRATE, TREAST, WALCL, WRESBAL).
- KNOWN_AS_OF: queries take `as_of` and return only `date <= as_of`. A date
  filter does not prove when a release or revision became observable. Join
  publication/availability timestamps through tools/pit/pit_join.py and
  report missing metadata. A signal cannot consume a later-known revision.
- OFFLINE: no network during grading/reporting. If coverage is missing you
  report the gap; you never fetch mid-backtest.
- PROVENANCE: `src` records origin (yfinance / fred-mcp-snapshot / manual) and
  must survive into any export.

## 2. Metric definitions

- Total return: final equity / initial equity - 1.
- Annualized return: `(1 + total_return) ** (252 / n_days) - 1` where n_days is
  trading days in the window. Requires >= 60 trading days or it is not printed.
- Max drawdown: max peak-to-trough decline of the daily equity curve, as a
  positive percentage.
- Sharpe ratio: mean(daily excess returns) / sample stdev(daily excess returns)
  * sqrt(252), with an explicit same-period cash/risk-free assumption. A zero
  rate is an assumption, not a verified historical rate. Square-root scaling
  assumes sufficiently independent stationary observations. Zero volatility
  produces an undefined ratio, never an infinite success score.
- Win rate: winning round trips / total round trips. For always-in modes
  (momentum cohorts), count per-cohort P/L > 0 as a win.
- Avg gain / avg loss / profit factor: gross wins / gross losses across trades.

## 3. Benchmark discipline

SPY buy-and-hold over the IDENTICAL investable calendar window, same cost
model and first decision/fill convention. Report SPY's total return, annualized return,
max drawdown, and Sharpe beside the strategy's. Excess return = strategy minus
SPY in percentage points. A strategy that made money but lagged SPY is reported
as a loss vs benchmark, not a success.

## 4. Bias taxonomy -- what to flag and when

### S1. Survivorship bias (ALWAYS applies to this store)

The historical inventory was a curated watchlist. Verify current coverage;
a current watchlist cannot establish historical investability or delistings. A cross-sectional selection
strategy (momentum top-N, sector rotation, low-RSI screens) is tested only on
names that made this list has selection risk. State S1 in every report unless
dated lifecycle and historical membership evidence actually resolves it.

This does not establish a mathematical upper bound on unbiased performance.
The magnitude and direction of bias remain unknown without a valid comparison.

### S2. Selection/period bias

One five-year window (2021-2026), dominated by a tech/AI regime. Results do
not generalize across regimes. Never claim robustness from one window; if the
user asks "would this have survived 2008", answer honestly: the store cannot
test that (data starts 2021 for equities).

### S3. Ticker-universe composition bias

The list is tech/semiconductor-heavy by design (it mirrors the owner's watchlist).
Sector-rotation results reflect THIS universe's sector weights, not the
market's. Flag when a rotation result is really "tech went up".

### L1. Lookahead bias via signals

Check both economic date and actual availability/revision time. Verify every query
in the driver passes as_of; direct sqlite reads with unbounded WHERE clauses
inside a signal loop are forbidden. If you must compute an indicator needing
future bars (e.g. a centered moving average), the strategy is unimplementable
-- reject it rather than approximate.

### L2. Lookahead bias via labels

Current sector maps under wiki/entities/ are not historical classifications.
Applying today's classification to past data ignores changes. Use dated maps
or mark the simulation exploratory; do not presume the bias is small.

### L3. Fill-timing optimism

Use the repaired simulate_target_weights engine: close-T decisions fill at
the next calendar close T+1, after the existing book is marked. The old
same-bar convention is invalid for decisions requiring that final close.
Daily data cannot establish next-open or intraday execution. Keep first-fill,
terminal-unfilled decisions and final liquidation explicit. Do not rerun old
frozen registrations under corrected accounting as if the methods were unchanged.

### L4. Data-quality bias

Establish the actual provider and raw/adjusted price basis. Raw price changes
across a split are not total returns. Dividend treatment and corporate actions
need explicit metadata and checks; a src string alone does not verify them.

## 5. Cost realism

Declare one-way cost assumptions and a higher-cost stress before scoring.
Charge entry, rebalance and exit on actual traded market value. Cash and shares
must satisfy the self-financing identity after every mark/fill. Zero cost is
an idealized control, not the main realistic estimate. Costs used in selection
may change holdings, so higher-cost strategy results are not a pure fee-only
comparison. Cash yield, taxes, borrow, liquidity and nonlinear impact need
separate assumptions; the current long-only simulator does not model them.

## 6. Statistical honesty

- A finite backtest can support assumption-dependent uncertainty estimates;
  it cannot prove robustness. Account for dependence, effective sample size,
  nonstationarity and multiple testing. Do not fabricate an interval from a
  single summary statistic or report precision unsupported by the sample.
- Register every attempted variant, including failures. Selecting the best
  of many trials creates selection risk; test any claim on untouched data
  through the canonical evaluator, with no automatic strategy promotion.
- Report trade counts and effective observations. No universal count threshold
  turns a dependent, biased sample into reliable evidence.

## 7. What a backtest CAN and CANNOT tell you

CAN: whether a mechanical rule had an edge on this data historically; relative
behavior across parameter values; drawdown character of a rule; sanity-check
before paper trading.

CANNOT: predict future returns; validate discretion; prove causality; survive
regime change; account for your execution quality.

Every report ends: SIMULATION ONLY -- past performance does not guarantee
future results.

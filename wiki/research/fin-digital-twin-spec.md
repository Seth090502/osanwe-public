---
aliases: [fin-digital-twin-spec]
categories: [wiki]
type: reference
status: active
created: 2026-08-24
updated: 2026-08-24
tags:
  - topic/finance
related: []
---

# Financial Digital Twin Specification

Status: SPEC (Phase 1 active)
Location: wiki/research/fin-digital-twin-spec.md
Date: 2026-08-24
Scope: An explainable, continuously-updated model of the operator's complete
financial position. Every output must be traceable to its inputs.

---

## 1. Design Principles

1. EXPLAINABLE BY DEFAULT. No number appears without its source, timestamp,
   and confidence level.
2. SEPARATE FACT FROM ESTIMATE. Facts (confirmed balances, executed trades)
   are distinguished from estimates (projected income, assumed returns) at
   the data-model level.
3. NO NETWORK DEPENDENCY FOR CORE STATE. Market data arrives via the factor
   store; the twin itself reads local state only.
4. PRIVACY HARD BOUNDARY. The twin never reads
   .raw/private/finance/credentials/*.local.md. Credential access happens
   only through sanctioned broker-pull tooling that writes sanitized results
   into the twin's data directory.
5. DETERMINISTIC REPLAY. Given the same input snapshot, the twin must produce
   byte-identical outputs (Monte Carlo uses seeded RNG).

---

## 2. What It Models

### 2.1 Current Net Worth

- Definition: sum(assets) - sum(liabilities), computed per account and rolled
  up to a single figure with an as-of timestamp.
- Per-position record:
  - asset_id, class (cash / equity / fixed_income / real_estate / retirement /
    crypto / other), quantity, unit_value, value, currency
  - liability records: balance, rate, minimum_payment, maturity
- CONFIDENCE LEVELS (per asset):
  - HIGH: verified via broker pull or statement within N days
  - MEDIUM: manually entered, verified > N days ago
  - LOW: estimated (e.g., illiquid assets, receivables, private interests)
- Output: headline net worth plus confidence-weighted range
  (e.g., "X +/- Y at 90% confidence") rather than a single false-precision
  number.
- Staleness flags: any position older than its refresh SLA is marked STALE
  and excluded from HIGH-confidence rollup.

### 2.2 Monthly Cash Flow

- Two-sided ledger: inflows (salary, dividends, interest, rent, other) and
  outflows by category (housing, food, transport, insurance premiums,
  debt service, discretionary, taxes withheld/estimated).
- Categorization: rule-based first pass; operator confirms or corrects;
  corrections feed back into rules.
- Outputs:
  - trailing 3-month average net cash flow
  - fixed vs variable split
  - savings rate
  - anomaly flag when any category deviates > threshold from trailing mean

### 2.3 Tax Position

- Current-year running estimate: ordinary income, capital gains realized/
  unrealized, dividend classification (qualified vs ordinary), withholding
  vs estimated payments made.
- Carryforwards: capital loss carryforward amount and expiration schedule;
  unused credits.
- Bracket proximity: distance (in dollars of income) to next federal bracket
  boundary and to key thresholds (NIIT, additional Medicare, IRMAA cliffs if
  applicable). Flag decisions that would cross a threshold.
- All figures labeled ESTIMATE; final numbers belong to the tax professional.

### 2.4 Risk Exposure

- VaR: parametric (variance-covariance) and historical-simulation VaR at 95%
  and 99% over 1-month horizon on the marketable portfolio. State method used.
- Factor exposures: equity beta, size, value, momentum, quality, duration,
  credit spread sensitivity -- sourced from the factor store where available,
  else proxied by asset-class weights.
- Concentration: top-N positions as % of portfolio; single-issuer exposure;
  correlated-cluster exposure (e.g., employer stock + unvested RSUs + industry
  peers); currency concentration; real-estate as % of net worth.
- Liquidity risk: % of net worth convertible to cash within 1/7/30 days.

### 2.5 Goal Progress

- Goal record: name, target amount (real or nominal), target date, funding
  accounts, priority, status.
- Trajectory: current balance + planned contributions grown at stated return
  assumption vs required growth rate to hit target ("required return").
- Output per goal: on-track / at-risk / off-track with the gap in dollars and
  the required monthly contribution to close it.
- Assumptions are explicit and versioned per goal.

### 2.6 Retirement Trajectory

- Inputs: current retirement balances, contribution rates, expected
  retirement age, expected Social Security/pension (ESTIMATE, sourced),
  desired retirement income (today's dollars).
- Projection: deterministic base case + sensitivity band (return assumption
  varied). Later phases add Monte Carlo success probability.
- Output: projected annual income vs needed income at retirement age, gap in
  dollars, age at which projected income first meets needed income
  ("crossover age").

### 2.7 Insurance Adequacy

- Coverage inventory: life (term amounts, expirations), disability
  (own-occupation? elimination period? benefit %?), health (OOP max), property
  & casualty (replacement cost vs coverage), umbrella/liability.
- Gap analysis methods:
  - Life: income-replacement multiple and needs-based (debts + goals - assets)
  - Disability: after-tax income replacement ratio vs target (60-70% typical)
  - P&C: replacement cost estimate vs policy limits
- Output: table of coverage type / current / recommended range / GAP /
  evidence for the recommendation.

---

## 3. How It Updates

### 3.1 Market Data (automatic)

- Source: factor store (prices, factors, vol/correlation inputs).
- Cadence: refreshed whenever the factor store updates; twin re-marks all
  liquid positions and recomputes derived metrics (VaR, exposures, net worth
  market-sensitive components).
- Every mark carries: price date, source, and whether it moved net worth by
  more than a materiality threshold since last update (change log).

### 3.2 Holdings

- Preferred path: broker pulls via sanctioned tooling -> sanitized holdings
  file written into twin data directory. Twin ingests, diffs against prior
  snapshot, and records the diff.
- Fallback path: manual entry through a structured template (account, ticker,
  quantity, cost basis, as-of date, source=manual).
- Conflict resolution: broker pull overrides manual entry for the same
  account unless operator pins a manual override (pinned values are logged).

### 3.3 Income / Expenses

- From /journal entries: journal entries tagged finance/income or
  finance/expense are parsed into the cash-flow ledger with their categories.
- Manual input: same structured template as above.
- Reconciliation: monthly totals from journal vs any imported statements;
  discrepancies surface as reconciliation items, not silent merges.

### 3.4 Life Events (operator-notified)

- Trigger list: employment change, marriage/divorce, birth/adoption, home
  purchase/sale, inheritance, relocation (tax jurisdiction change), health
  event, policy changes.
- Mechanism: operator notifies via journal entry tagged finance/life-event;
  twin maps each event type to model impacts (tax residency, insurance needs
  recalculation, goal timeline shifts, withholding changes) and raises a
  review checklist instead of auto-applying uncertain changes.

### 3.5 Update Integrity

- Append-only event log: every ingestion is an event (source, timestamp,
  payload hash). State is derivable by replay.
- Materiality filter: trivial changes (< threshold) update state but do not
  notify; material changes appear in the daily digest.

---

## 4. How It Explains Itself

Every recommendation is emitted with a standard explanation block:

```
EXPLANATION BLOCK v1
1. CURRENT STATE
   - relevant balances/values, as-of dates, confidence levels, sources
2. PROPOSED CHANGE
   - exact action considered (amounts, accounts, timing)
3. BEFORE VS AFTER
   - delta across ALL affected dimensions: net worth, cash flow,
     tax position, risk metrics, goal progress, retirement trajectory,
     insurance gaps -- including dimensions NOT improved
     (a recommendation that helps taxes but raises concentration
      says so explicitly)
4. ASSUMPTIONS AND SENSITIVITY
   - each assumption (return rate, inflation, income growth, etc.)
     with its value, source, and a one-at-a-time sensitivity:
     how the conclusion changes if the assumption moves +/- X%
5. WHAT WOULD MAKE THIS WRONG
   - falsifiers: observable conditions or data that, if true,
     reverse the recommendation
6. CONFIDENCE AND EVIDENCE
   - overall confidence (HIGH/MEDIUM/LOW) with reasons, plus a list
     of every evidence item (file path, journal entry id, factor-store
     series id, statement date) behind the analysis
```

Rules:

- If any dimension lacks data, the block says "UNKNOWN - data needed"
  rather than omitting the dimension.
- Recommendations never exceed the confidence of their weakest load-bearing
  input; the block names that input.
- Explanation blocks are stored alongside the recommendation for later audit
  (prediction-backtesting compatible).

---

## 5. Implementation Phases

### Phase 1 (NOW): Static framework + existing market data integration

Deliverables:
- Data schemas for positions, liabilities, ledger entries, goals, events.
- Net worth calculator with confidence levels and staleness tracking.
- Market-value refresh from factor store for liquid holdings.
- Basic risk metrics (concentration, simple parametric VaR) where factor
  store provides covariance inputs.
- Explanation-block emitter (works even with partial data using UNKNOWN
  markers).
- Event log skeleton.

Acceptance: given a hand-built snapshot file, twin produces net worth with
confidence ranges, marks positions from factor store, and emits a valid
explanation block for a sample recommendation.

### Phase 2 (needs data): Personal income/expense/balance sheet modeling

Prerequisite: 3+ months of journal-tagged income/expense data or imported
statements; complete manual balance-sheet entry.

Adds:
- Cash-flow engine with categorization feedback loop and anomaly detection.
- Full liability modeling (amortization, payoff projections).
- Goal progress trajectories with required-return math.
- Retirement base projection (deterministic).

### Phase 3 (needs data): Tax situation modeling, insurance gap analysis

Prerequisite: prior-year return summary figures, current-year withholding/
estimated payment history, insurance policy declarations pages.

Adds:
- Running tax estimate with bracket-proximity alerts and carryforward
  tracking.
- Insurance inventory and gap analysis per section 2.7.
- Cross-module explanations (e.g., tax-loss harvesting shows effect on
  concentration and goal funding too).

### Phase 4 (needs data): Estate planning integration, scenario Monte Carlo

Prerequisite: Phases 1-3 stable; estate documents available for structured
summary; sufficient history to calibrate return/volatility assumptions.

Adds:
- Estate module: beneficiary map, document inventory with review dates,
  estate-tax exposure estimate (federal/state), location of key documents.
- Seeded Monte Carlo over returns, inflation, longevity, and spending paths;
  success probabilities per goal and per retirement plan.
- Scenario library: job loss, market crash sequence, early retirement,
  long-term care, disability -- each runnable against current state with
  full explanation blocks.

---

## 6. Non-Goals

- Not a transaction execution system. The twin recommends; humans act.
- Not a substitute for a CPA, attorney, or licensed advisor. Estimates are
  decision-support only.
- No storage of credentials within the twin's own data directory.
- No network calls from the twin core; all external data enters via the
  factor store or operator-supplied imports.

## 7. File Layout (planned under twin data root)

```
twin/
  state/            # current derived state (regenerable)
    net_worth.json
    cashflow.json
    tax_position.json
    risk_metrics.json
    goals.json
    retirement.json
    insurance.json
  events/           # append-only ingestion log
  snapshots/        # dated input snapshots (broker pulls, manual templates)
  explanations/     # emitted explanation blocks, keyed by recommendation id
```

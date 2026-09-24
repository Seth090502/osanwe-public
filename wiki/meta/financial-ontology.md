---
categories:
  - wiki
type: ontology
created: 2026-08-25
updated: 2026-08-25
status: active
confidence: high
tags:
  - topic/meta
  - topic/investing
  - topic/knowledge-graph
aliases: ["financial ontology", "kg schema", "unified finance ontology"]
related: ["[[knowledge-moc]]", "*investing-moc* (not published)"]
---

# Unified Financial Ontology

Specification of the entity classes, relationship types, and temporal model
for the vault's financial knowledge graph (KG). The KG is the semantic layer
that sits above the raw ledgers (`finance/`, `wiki/investing/`), the entity
notes (`wiki/entities/`), and generated views. Everything an agent asserts
about money flows through this schema so that queries, backtests, and audits
resolve to the same objects.

Design goals:

1. **Point-in-time truth.** Every fact carries bitemporal stamps, so any query
   can be replayed as of a past moment.
2. **Provenance everywhere.** No fact exists without a `source`.
3. **Separation of state from events.** Holdings and balances are state;
   transactions are events that produce state transitions.
4. **Decision auditability.** Recommendations, forecasts, approvals, and
   outcomes are first-class nodes, not prose.

Conventions used below:

- Types are given as `{name: type}` pairs. Optional properties are marked
  `[opt]`. Enumerations use `a|b|c`.
- All identifiers are opaque strings, namespaced by class prefix:
  `person:<slug>`, `hh:<slug>`, `acct:<custodian>-<slug>`, `sec:<isin-or-ticker>`,
  `hold:<acct>-<sec>`, `txn:<iso8601>-<acct>-<n>`, `lot:<hold>-<seq>`,
  `goal:<slug>`, `liab:<slug>`, `ins:<slug>`, `fcst:<model>-<ts>`,
  `dec:<slug>-<seq>`, `evt:<slug>`, `mdl:<name>@<version>`, `ds:<slug>`.
- Dates are ISO-8601 (`YYYY-MM-DD`); timestamps ISO-8601 with UTC offset.
- Monetary values carry an explicit currency code where ambiguity is possible;
  the default currency for this household graph is USD.
- This file is ASCII-only by vault law (R4).

---

## 1. Entity Classes

### 1.1 Person

A human actor in the graph (household member, counterparty, advisor,
approver).

```
Person {
  id              : person_id            # primary key
  name            : string               # display name
  role            : enum(owner|spouse|dependent|advisor|approver|counterparty)
  risk_tolerance  : enum(conservative|moderate|aggressive) [opt]
  risk_capacity   : enum(low|medium|high) [opt]   # objective capacity; keep
                                                  # separate from tolerance
  date_of_birth   : date [opt]
  jurisdiction    : string [opt]         # tax residence, e.g. "US-NY"
  employment      : string [opt]
  marginal_tax_rate: decimal [opt]       # as-of-date stamped, see Sec. 4
  notes           : text [opt]           # free context, never PII beyond need
}
```

Constraints:

- `risk_tolerance` changes are new facts, not overwrites (temporal, Sec. 4).
- A Person may belong to multiple Households only via explicit membership rows
  with their own validity windows (e.g. before/after marriage).

### 1.2 Household

The unit of financial planning. Most planning-level facts (goals, aggregate
risk, tax posture) attach here rather than to individuals.

```
Household {
  id           : hh_id
  members      : [person_id]          # ordered; head of household first
  jurisdiction : string               # e.g. "US-NY"; drives tax treatment
  tax_status   : enum(single|mfs|mfil|hofh)   # married-filing-separately etc.
  filing_year_basis : int             # tax year the status applies to
  dependents   : [person_id] [opt]
  state_residence_history : [(jurisdiction, valid_from, valid_to)] [opt]
}
```

Constraints:

- `tax_status` is year-scoped: one value per filing year. Store history as a
  sequence of temporally bounded facts, never a mutable single field.

### 1.3 Account

An account at a custodian or institution. Accounts hold securities and/or
cash; they do not themselves own securities directly (see Holding).

```
Account {
  id         : acct_id
  type       : enum(taxable|roth|traditional|h sa|hsa|529|i ra|sep ira|
                    margin|cash|crypto|checking|savings)
  subtype    : string [opt]          # custodian-specific detail
  custodian  : string                # e.g. "Fidelity", "Robinhood", "Chase"
  owner_id   : person_id | hh_id     # legal owner(s); joint = list
  beneficiaries : [(person_id, share_pct)] [opt]
  opened_date    : date
  closed_date    : date|null
  cash_balance   : decimal [opt]     # derived; recompute, do not hand-edit
  contribution_limits : {year: limit} [opt]   # per tax-sheltered types
  features   : enum set(cash_sweep|options|margin|checkwriting) [opt]
}
```

Constraints:

- Tax-sheltered accounts (`roth`, `traditional`, `hsa`, `529`, ...) must link
  to exactly one natural-person `owner_id`; joint ownership implies taxable.
- `cash_balance` is always derived from transactions; it must never be asserted
  independently without a source snapshot reference.

### 1.4 Security

An investable instrument. One node per instrument regardless of how many
accounts hold it.

```
Security {
  id          : sec_id
  ticker      : string [opt]        # exchange-local symbol; may change
  isin        : string [opt]        # preferred stable key when available
  cusip       : string [opt]
  conid       : string [opt]        # broker-native id if needed for sync
  asset_class : enum(equity|etf|mutual_fund|bond|treasury|option|future|
                     crypto|reit|commodity|fx|cash_equiv)
  sector      : string [opt]        # GICS-style; null for non-equity
  industry    : string [opt]
  exchange    : string [opt]
  currency    : string              # trading currency
  underlying  : sec_id [opt]        # options/futures: the underlying security
  expiry      : date [opt]          # options/futures
  strike      : decimal [opt]       # options
  right       : enum(call|put) [opt]
  maturity    : date [opt]          # bonds
  coupon      : decimal [opt]       # bonds
  expense_ratio: decimal [opt]      # funds
}
```

Constraints:

- Ticker changes (renames, M&A) create a *new fact* on the same Security node:
  store `(ticker, valid_from, valid_to)` history rather than overwriting.
- Options are Securities whose `underlying` points at another Security; never
  collapse option chains into the underlying node.

### 1.5 Holding

The position of one Security inside one Account at a point in time. A Holding
is *state*, continuously derived from Transactions; it is materialized in the
graph for query speed, with the transaction ledger as ground truth.

```
Holding {
  id               : hold_id
  account_id       : acct_id
  security_id      : sec_id
  quantity         : decimal          # signed; negative = short
  cost_basis_total : decimal          # sum of open lots' bases
  market_value     : decimal [opt]    # as-of priced snapshots
  as_of            : timestamp        # when this snapshot was computed
  tax_lots         : [lot_id]         # open lots backing this position
}
```

Constraints:

- Invariant: for every `(account_id, security_id)` pair with no open position,
  there is NO current Holding row (closed positions survive only historically,
  via `valid_to`).
- Invariant: `sum(TaxLot.cost_basis)` over open lots ==
  `Holding.cost_basis_total`. Enforce at write time.
- Never edit `quantity` directly; post a Transaction and regenerate.

### 1.6 Transaction

The atomic event ledger. Immutable once recorded; corrections happen via
reversal entries, never edits.

```
Transaction {
  id          : txn_id
  datetime    : timestamp (UTC)      # execution time, not settlement
  settle_date : date [opt]
  type        : enum(buy|sell|dividend|dividend_reinvest|interest|
                     fee|contribution|withdrawal|transfer_in|transfer_out|
                     split|spinoff|journal|tax|adj)
  security_id : sec_id|null          # null for pure cash events
  account_id  : acct_id
  quantity    : decimal|null         # shares/contracts; null for fees/cash
  price       : decimal|null         # per-unit; null where N/A
  amount      : decimal              # net cash impact (signed)
  fees        : decimal              # commissions+regulatory fees, positive
  accrued_interest : decimal [opt]   # bonds
  lot_ids     : [lot_id] [opt]       # sells: which lots were consumed
  counter_txn_id : txn_id [opt]      # transfers/journals: the other leg
  transfer_account_id : acct_id [opt]
  memo        : string [opt]
  external_id : string [opt]         # broker confirmation number; dedupe key
}
```

Constraints:

- `(account_id, external_id)` is unique -- import deduplication depends on it.
- Sells MUST reference consumed `lot_ids` (or record the lot-selection method
  applied); buys create lots (Sec. 1.7).
- Reversals: post an opposite Transaction with
  `memo="REVERSAL of <txn_id>"`; both remain in the ledger forever.

### 1.7 TaxLot

Specific identification granularity for every purchase. Lots enable HIFO /
specific-lot optimization and wash-sale tracking.

```
TaxLot {
  id               : lot_id
  holding_id       : hold_id          # (account, security) it belongs to
  acquisition_date : date             # settlement date for wash-sale clock
  cost_basis       : decimal          # includes allocated fees
  quantity         : decimal          # remaining quantity in the lot
  original_quantity: decimal
  method           : enum(hifo|fifo|lifo|specific|average_cost)
  term             : enum(short|long)|null    # derived from acquisition_date
  wash_sale_flagged : boolean         # true if loss was disallowed
  closed_by_txn    : txn_id|null      # when fully consumed
}
```

Constraints:

- `method` may differ per lot (broker default vs. our optimization); record
  what was actually used for realized-gain reporting, not merely what was
  intended.
- Wash-sale adjustments mutate `cost_basis` only via linked adjustment
  transactions, preserving the audit trail.

### 1.8 Goal

A forward-looking funding target owned by a Household (sometimes a Person).

```
Goal {
  id              : goal_id
  description     : string
  owner_scope     : hh_id | person_id
  target_amount   : decimal|null     # null for open-ended goals
  target_date     : date|null
  priority        : int              # 1 = highest; ties broken by created_at
  funding_accounts : [acct_id]       # accounts earmarked toward this goal
  progress_metric : enum(balance|funded_ratio|probability) [opt]
  status          : enum(active|paused|achieved|abandoned)
  monthly_contribution : decimal [opt]
}
```

Constraints:

- `targets` relationships (Sec. 2) formalize the amount/date links; the
  fields above are denormalized convenience mirrors kept consistent by
  generation, not hand-editing.
- Achieving/pausing a Goal is a state change WITH a validity window, not an
  overwrite.

### 1.9 Liability

Debt obligations of a Person or Household.

```
Liability {
  id         : liab_id
  type       : enum(mortgage|student|auto|credit|heloc|personal|margin)
  principal  : decimal               # outstanding balance, as-of stamped
  rate       : decimal               # APR; fixed, or rate_index+spread for ARM
  rate_type  : enum(fixed|variable) [opt]
  term_months: int
  payment    : decimal               # scheduled minimum payment
  start_date : date
  maturity_date : date [opt]
  collateral : string [opt]          # description or Security/account ref
  servicer   : string [opt]
  amortization : [(date, interest, principal)] [opt]   # schedule snapshot
}
```

Constraints:

- `principal` declines over time: each statement creates a temporally bounded
  fact; the current balance is the fact whose window contains "now".

### 1.10 InsurancePolicy

Risk-transfer contracts held by Persons/Households.

```
InsurancePolicy {
  id             : ins_id
  type           : enum(life|disability|health|umbrella|auto|home|renters)
  coverage_amount: decimal
  premium        : decimal            # per premium_frequency
  premium_frequency : enum(monthly|quarterly|annual) [opt]
  beneficiary    : person_id|[person_id] [opt]   # life policies primarily
  insured        : person_id [opt]
  carrier        : string
  policy_number_masked : string [opt]  # NEVER store full policy numbers
  start_date     : date
  end_date       : date|null
  riders         : [string] [opt]
}
```

Constraints:

- Beneficiary designations override wills in most jurisdictions; treat
  beneficiary changes as high-salience events that also emit a Decision
  review prompt.

### 1.11 Forecast

A machine-generated prediction about some object (a price, a probability, a
portfolio outcome). Forecasts are immutable artifacts; they expire, they are
never edited.

```
Forecast {
  id               : fcst_id
  prediction_object: string           # typed ref, see below
  prediction_type  : enum(price_path|return_distribution|event_probability|
                          drawdown_estimate|goal_probability)
  payload          : json             # the prediction itself, schema'd per type
  model_version    : string           # e.g. "calibration-report@2026w34"
  confidence       : decimal [opt]    # calibrated, not stated (use
                                      # tools/calibrate-confidence.py output)
  created_at       : timestamp
  expires_at       : timestamp        # hard staleness boundary
  superseded_by    : fcst_id [opt]
}
```

`prediction_object` grammar: `<class>:<id>:<aspect>` -- e.g.
`security:sec:SPY:21d_return`, `portfolio:hh:main:var_95`,
`goal:goal:retire:probability`.

Constraints:

- A Forecast past its `expires_at` MUST NOT feed decisions without an explicit
  freshness waiver recorded in the consuming Decision's rationale.
- Calibration metadata (from the weekly calibration loop) attaches via
  `derived_from` edges to the calibration report dataset.

### 1.12 Decision

A choice point with full audit context: what triggered it, what alternatives
existed, what was selected and why, who approved, and what happened.

```
Decision {
  id                     : dec_id
  triggering_event       : evt_id | string    # event node or inline trigger
  decision_type          : enum(buy|sell|hold|rebalance|contribution|
                                tax_action|insurance|refinance|goal_change|
                                model_change|policy_change)
  alternatives_considered: [{option: string, expected_value: json,
                             rejection_reason: string}]
  selected               : string             # the chosen alternative
  rationale              : text               # cites data via derived_from
  approval_status        : enum(proposed|approved|rejected|executed|
                                declined_by_user|expired)
  approved_by            : [person_id]
  executed_txns          : [txn_id] [opt]
  outcome                : {measured_at, metric, result, vs_alternative} [opt]
  confidence_at_decision : decimal [opt]      # pre-calibration stated value
}
```

Constraints:

- `approval_status` transitions form a strict DAG:
  proposed -> approved -> executed, proposed -> rejected,
  approved -> declined_by_user, proposed -> expired. Illegal transitions are
  validation errors.
- `outcome` is filled by retrospective review (Phase R-style loops), at least
  once per Decision with a defined measurement horizon.

---

## 2. Relationship Types

All edges carry the temporal/provenance envelope of Sec. 4. Direction is
`source -> target`. Cardinality noted per edge.

| Edge          | From -> To                        | Cardinality | Notes |
|---------------|-----------------------------------|-------------|-------|
| owns          | Person/Household -> Account       | 1:N         | Legal/beneficial ownership; joint ownership = multiple owns edges |
| holds         | Account -> Holding                | 1:N         | Account contains position snapshots |
| invests_in    | Holding -> Security               | N:1         | What the position is in |
| has_liability | Person/Household -> Liability     | N:M         | Co-borrowers produce multiple edges |
| insured_by    | Person/Household -> InsurancePolicy | N:M       | insured vs beneficiary roles distinguished by edge property `role=insured|beneficiary` |
| targets       | Goal -> (amount, date)            | N:2         | Modeled as two edges or edge props `target_amount`, `target_date`; changes are new edge versions |
| funds         | Account -> Goal                   | N:M         | Which accounts serve which goals (mirrors funding_accounts) |
| derived_from  | Forecast/Analysis -> Dataset/Node | N:M         | Provenance of computed artifacts |
| supersedes    | Decision -> Decision              | N:1         | New decision replaces prior; prior gets `superseded_by` backlink |
| invalidates   | Event -> Forecast/Recommendation  | N:M         | Realized event kills stale predictions |
| depends_on    | Model -> Dataset                  | N:M         | Training/input dependencies; version-pinned |
| approved_by   | Decision -> Person                | N:M         | With `role=approver`, timestamp of approval |

Additional structural edges (implied by the schema, listed for completeness):

| Edge          | From -> To          | Cardinality | Notes |
|---------------|---------------------|-------------|-------|
| member_of     | Person -> Household | N:1         | With validity window (marriage, dependency changes) |
| produced      | Transaction -> TaxLot | 1:N       | Buys produce lots; sells consume them (`consumes`) |
| consumes      | Transaction -> TaxLot | N:M       | Sell-side lot selection |
| settled_in    | Transaction -> Account | N:1     | Cash leg destination when different from trade account |

Edge properties (beyond the universal envelope):

```
Edge {
  valid_from / valid_to / recorded_at / source   # Sec. 4, mandatory
  role        : string [opt]     # disambiguator, e.g. insured vs beneficiary
  weight      : decimal [opt]    # e.g. share_pct on joint owns
}
```

Rules:

- Edges are never deleted. An ended relationship gets `valid_to` set; the
  historical edge remains queryable.
- `invalidates` edges must cite the realized event (an Event node with its own
  source -- fill, print, economic release), never an opinion.

---

## 3. Supporting Node Classes

Referenced by the classes above; minimal definitions for completeness.

```
Event {
  id         : evt_id
  kind       : enum(fill|dividend_payment|earnings_release|fed_action|
                    life_event|market_shock|statement_snapshot|correction)
  occurred_at: timestamp
  subject    : typed_ref            # what the event concerns
  payload    : json
}

Model {
  name       : string
  version    : string
  kind       : enum(calibration|forecast|optimizer|risk)
  code_ref   : string [opt]         # path/hash of generating code
  parameters : json [opt]
}

Dataset {
  id         : ds_id
  uri        : string               # local path/db/query, no network assumed
  as_of_range: (start, end)
  checksum   : string [opt]
}

Recommendation {
  id            : rec_id
  produced_by   : mdl_ref
  content       : json
  addressed_to  : person_id|hh_id
  status        : enum(open|accepted|dismissed|invalidated|expired)
}
```

---

## 4. Temporal Model (Bitemporal)

Every entity instance and every relationship edge carries four envelope
properties. These are mandatory; absence is a validation failure.

```
valid_from  : timestamp   # when the fact became TRUE IN THE WORLD
valid_to    : timestamp|null  # when it stopped being true; null = still true
recorded_at : timestamp   # when THIS SYSTEM learned/stored it
source      : string      # where it came from (see provenance grammar below)
```

This is the classic two-timeline (bitemporal) pattern:

- **Valid time** (`valid_from`/`valid_to`) answers: "when was this true in
  reality?"
- **Transaction time** (`recorded_at`) answers: "when did we know it?"

### 4.1 Semantics

- A fact may be learned late: `recorded_at > valid_from` is normal (e.g. a
  brokerage statement arrives days after trades). Retroactive corrections add
  NEW rows with updated `valid_from/valid_to` and a later `recorded_at`;
  nothing is overwritten.
- Current-state query: filter `valid_from <= now AND
  (valid_to IS NULL OR valid_to > now)`.
- Point-in-time query, real world ("what WAS X's balance on June 1?"): filter
  on valid time containing June 1, latest `recorded_at` <= today.
- Point-in-time knowledge query ("what did we KNOW about X at time T?"):
  filter `recorded_at <= T`, then take the valid-time interval that was
  believed current at T. This is the anti-lookahead guarantee that backtests
  (prediction-backtesting discipline) require: a June backtest must never see
  a fact first recorded in July.

### 4.2 Query patterns (canonical)

```
# State of account holdings as known on 2026-06-01:
MATCH (a:Account)-[h:HOLDS]->(hd:Holding)-[:INVESTS_IN]->(s:Security)
WHERE h.recorded_at <= '2026-06-01T23:59:59Z'
  AND h.valid_from <= '2026-06-01T00:00:00Z'
  AND (h.valid_to IS NULL OR h.valid_to >  '2026-06-01T00:00:00Z')
RETURN a.id, s.ticker, hd.quantity, hd.cost_basis_total

# Full knowledge timeline for a security's ticker history:
MATCH (s:Security {id:'sec:AAPL'})-[t:TICKERED_AS]->(tk)
RETURN tk.symbol, t.valid_from, t.valid_to, t.recorded_at, t.source
ORDER BY t.recorded_at
```

### 4.3 Provenance grammar for `source`

`source` uses a URI-ish grammar so provenance is machine-checkable:

```
source := scheme ":" locator ["@" retrieved_ts]
schemes:
  stmt:fidelity-2026-07        # custodian statement
  api:yfinance@2026-08-25T14:03Z
  broker-export:<custodian>-csv-<YYYY-MM>
  manual:<user>                 # human-entered (weakest tier)
  derived:gen-ledger-views.py  # computed from other sourced facts
  doc:wiki/research/edu-dcf.md
```

Trust tiers (for conflict resolution): `stmt/api/broker-export` >
`derived` > `doc` > `manual`. When two facts about the same aspect conflict,
the higher tier wins within overlapping valid windows; ties break to the
later `recorded_at` only after a reconciliation note is filed.

### 4.4 Enforcement checklist (for validators)

- [ ] Every node/edge has all four envelope props; `valid_from <= valid_to`.
- [ ] At most ONE current (`valid_to = null`) version per (entity, aspect).
- [ ] `recorded_at` never decreases across successive versions of an aspect.
- [ ] Derived values (balances, market_value, term flags) trace via
      `derived_from` to raw sourced facts.
- [ ] Forecast consumers check `expires_at` against decision time.
- [ ] Backtest loaders honor the `recorded_at <= as_of` filter (no lookahead).

---

## 5. Storage Mapping

How this ontology lands in the vault today (no network required):

| Ontology concept | Current substrate |
|---|---|
| Security nodes | `wiki/entities/tickers/`, company notes `wiki/entities/companies/` (frontmatter `type: company`) |
| Transaction/Holding/TaxLot | `finance/` ledgers + `wiki/investing/options-ledger.jsonl` (append-only) |
| Decision nodes | `decisions/records/` (+ generated views in `Calendar/decisions/`) |
| Forecast + calibration | `Efforts/osanwe-v2-overhaul/_work/factors.db`, `wiki/maintenance/calibration/*` |
| Goals/Liabilities/Insurance | future `finance/` sections; schema above is the contract |
| Graph queries | offline tooling reading frontmatter + JSONL + sqlite; no network |

Migration rule: existing notes map onto these classes via their frontmatter;
new structured records should adopt the ID grammar and temporal envelope from
day one even if stored flat, so a later graph load is lossless.

---

## 6. Validation Summary

A conforming graph satisfies all of:

1. Referential integrity: every `*_id` reference resolves to an existing node.
2. Temporal envelope present on 100% of nodes and edges (Sec. 4).
3. Accounting invariants: lots sum to holding basis; transactions reconcile to
   balances; reversals never delete.
4. Lot discipline: every sell references consumed lots; every buy mints one.
5. Decision lifecycle follows the legal transition DAG.
6. Forecasts are immutable and expire; consumers respect expiry.
7. No fact without provenance; conflicts resolved by trust tier, documented.

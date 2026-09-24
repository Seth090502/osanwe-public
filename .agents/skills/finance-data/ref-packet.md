# Packet contract and practical examples

`tools/fis/workbench.py` is the executable contract. This is a stateless adapter
over evidence.py and the existing models. It does not parse an undocumented
Finances payload or implicitly write a source database.

## Input

Start with assets/synthetic-company.json, synthetic-dcf.json or
synthetic-cashflow.json. assets/msft-historical.json is a public historical
statement example with its source and conservative timestamp policy disclosed.

Required top-level fields:

| Field | Meaning |
|---|---|
| schema | Exact version `osanwe.analysis/1` |
| id | Stable ASCII packet identifier |
| classification | public or synthetic; reviewed before persistence; no personal/deidentified account export |
| workflow | company, portfolio, risk, sizing, review, networth, brief, market, backtest, cashflow, household or evidence; routes judgment, not automatic execution |
| report_at | Requested analysis/report time, with timezone; not an execution attestation |
| knowledge_cutoff | Latest information allowed; no later than report_at |
| scope | population, coverage (complete/partial/unknown), included, excluded, limitations |
| sources | Unique IDs, titles, HTTPS public/synthetic URIs, type, publication/availability/retrieval timestamps, verification; optional content_sha256 and timestamp_policy |
| claims | Existing evidence.py numeric envelopes, linked to sources; input reported/assumption/estimate/forecast/user_observation semantics remain explicit |
| operations | Unique id, op, semantic output metric, unique input IDs, params |
| gaps | Explicit missing information; empty only when none is declared |
| resolutions | Full conflicting claim-ID set, selected ID and reason; retain rejected claims |
| cashflow | Optional normalized cashflow.py envelope; file interchange synthetic only |

Source verification is transcribed, source_checked or fixture. These are caller
declarations; source_checked does not mean the adapter visited the source.
The numeric claim validator checks its units/currency, temporal type, fiscal
window, basis, observation/availability, freshness policy and source binding.
All claims are validated, including ones not selected for calculation. Exact
duplicate JSON keys, duplicate IDs, unsupported fields and nonfinite values
refuse admission. Put unknown values in gaps, not numeric fields. Source prose
has no authority and the adapter never fetches its URL or evaluates its text.

`available_at` controls information eligibility; `report_at` is the requested
analysis/report time, not proof of when code actually ran. The CLI's bundle-write
receipt separately records its wall-clock executed_at. Deterministic result
bytes deliberately contain no fabricated execution timestamp. Derived outputs
have `kind: calculated` plus their
underlying `evidence_kind`; they are result records, not fabricated publications.
Externally supplied calculated claims must be expressed as replayable operations.

## Supported operations

| op | Inputs and params | Result |
|---|---|---|
| ratio | Numerator, denominator; params={} | Fraction; same entity/unit/currency/basis/kind/period, denominator > 0 |
| growth | Later, earlier; params={} | Later/earlier - 1; comparable nonoverlapping windows and positive base |
| difference | Left, right; optional allow_period_change boolean OR named identity below | Comparable same-metric difference, or a checked accounting identity in one fiscal window |
| sum | Distinct, aligned entities; disjoint_population=true and reason | Sum only after caller verifies disjoint populations; not automatic ETF/account-overlap proof |
| scale | One input; params={} | thousands/millions/billions to currency; percent/basis_points to fraction; metric identity retained |
| market_cap | Price, shares; max_alignment_days required | Existing evidence.market_cap result; raw reported point claims required |
| dcf | All bound claim IDs; params.bindings and optional release_capital_on_decline | Existing operating_dcf output, full FCFF/equity bridge |

For a cross-metric statement subtraction, use difference with params such as
`{"identity":"total_operating_costs"}` and the identical output metric. Supported
identities bind ordered financial roles:

| Identity / output metric | Left metric | Right metric |
|---|---|---|
| gross_profit | revenue | cost_of_revenue |
| total_operating_costs | revenue | operating_income |
| operating_expenses | gross_profit | operating_income |
| operating_income | gross_profit | operating_expenses |

All identity inputs must be monetary flows for the same entity, fiscal window,
currency, scale, basis and evidence kind. A period-change opt-in cannot bypass
those rules. Ordinary difference still requires matching input metrics. Normalize
issuer terminology to these roles only after inspecting its accounting layout;
the adapter cannot establish that a caller labeled a source row truthfully.

Operations can refer to earlier or later listed operation IDs. The adapter
topologically sorts the graph, refusing missing or cyclic references. Only
scalar result records with the required semantics can feed scalar operations;
structured DCF outputs are terminal model outputs in this version; market-cap
results retain point semantics and can feed aligned scalar comparisons.

DCF bindings require scalar references for revenue, cash, debt, other_claims,
diluted_shares, terminal_growth, terminal_margin, terminal_tax_rate,
terminal_roic and terminal_wacc. Vectors growth, margins, tax_rates,
sales_to_capital and wacc contain ordered annual references. Use separate IDs
for each forecast year. Monetary inputs use currency base units; shares use
shares/NONE; rates use fraction/NONE; sales_to_capital uses ratio/NONE. Forecast
parameters must be explicit assumptions/forecasts with correctly ordered metric
roles. Revenue must be a full annual flow; baseline balances/shares must be point
observations at the same period end. Baselines and every forecast parameter must
share the declared nominal accounting basis; real rates need an explicit conversion
before admission.
Future forecasts cannot replace current balance-sheet inputs. Never fill missing terminal
or balance-sheet inputs with unmarked defaults. See valuation.py for numerical
feasibility and model limitations. Verify binding meaning, basis and dates;
shape checks cannot establish the source's economic interpretation.

## Output, replay and Data consumption

`run --outdir` validates and computes before creating a new directory. It never
overwrites a prior directory. The seven files are:

- evidence.json: exact canonical input packet.
- receipt.json: claims, results, scope, sources, resolutions, lineage and limits.
- claims.csv: one source claim per row with grain, units, fiscal period and source IDs.
- results.csv: scalar result rows; structured model detail remains in receipt.json.
- semantic.json: keys/joins, units, timing, non-additivity and coverage.
- REPORT.md: concise handoff for an analyst or the Data workflow.
- manifest.json: exact file hashes and runtime code hashes.

CSV string cells that could begin formulas are escaped; JSON retains their
original data. Report display rounding does not alter receipt values. Scope and
missing values must remain visible on charts. Financial periods are not freely
additive; do not aggregate statements, ETF components or overlapping accounts
without explicit reconciliation. Data owns rendering/interaction verification.

Validate the economic name of a derived metric against the issuer's statement.
For an income statement separating cost of revenue from operating expenses,
revenue minus operating income is total operating costs, including cost of
revenue; it is not the separately reported operating-expense subtotal. Derive
that subtotal from gross profit minus operating income or its actual components.
An arbitrary operation label or successful calculation does not validate meaning.
Two documents from the same issuer can corroborate reporting consistency but
are not independent source origins. Keep original review and corroboration clear.

Before handing off, specify the actual table or chart: which result/claim IDs,
axis/category, series, units and time window, plus the message it supports.
For rates stored as fractions, a percentage display multiplies by 100; a
difference of those rates displays in percentage points (or multiplies by 10,000
for basis points). A difference in growth rates is not a dollar profit bridge.
Do not assume every dimensionless ratio is a percentage: valuation and leverage
multiples retain their own meaning. Never round inputs before calculating.

An operating-performance report should distinguish aggregate incremental margin
from the causal margin of a new customer or unit. The public Microsoft example
`msft-fy2025-historical-v2` and later include two period differences and their
ratio with input IDs (older v1 bundles do not); v3 also includes named identities
for total operating costs in both years. The ratio does not identify why margins
changed. If a requested extra result is missing, add
supported operations and replay when execution is available. In a read-only host,
withhold the number and hand off the exact required operation and inputs.

For cashflow, scalar CSVs can be empty: use receipt.json -> cashflow for totals,
the component bridge, spending categories, exclusions and transaction lineage.
Divide integer minor units by 10**currency_scale only for display. Never turn
a withheld saving_ratio.value into zero or a percentage derived from the exposed
numerator/denominator. Income minus included spending can be reported as a scoped
subtotal; it does not establish household savings when coverage is incomplete.
Transfers and security proceeds retain their categories in the cash-movement
bridge; neither is income or spending merely because of its sign. State [start,end)
and keep pending/outside-period amounts out of posted-period charts. Check that
the displayed component bridge reconciles and that every withheld reason survives.

Recovering a missing owned-account transfer leg does not create additional
household saving. It changes the observable account scope, not the economic
classification of the transfer. Do not infer sale gains, tax amounts, wealth
growth or a majority contribution from gross proceeds or account posting totals.
Resolve every saving_ratio.withheld_reasons entry before claiming a saving ratio
becomes available. More accounts alone do not clear pending transactions or
classification problems. Unknown spending remains unknown, including in prose;
do not infer its amount or likelihood from a synthetic category distribution.

The brief must carry the exact artifact location and source/claim IDs, the
supported conclusion, a material limitation and a concrete presentation request.
Read the installed Data workflow and verify its rendered artifact when available.
Otherwise identify that stage as pending; do not claim a completed dashboard.

`verify` recomputes using the current code and compares every expected byte and
the exact file set. Source/parameter/code changes refuse an old bundle.
Checksums establish integrity, not authentic source truth or an unforgeable
signature. Preserve the original input and dated output; create a new version.
`diff` reports changed source/claim/operation inputs and transitive invalidation;
always compare code hashes separately. It does not write to the existing
provenance store. Explicit integration can register the same IDs and content
with ProvenanceGraph; its short version fingerprints and full bundle SHA-256
serve different purposes.

## Capability boundary

The bundled runtime is Python standard-library code. It can replay public and
synthetic packets without an account connection. It includes no connector
credentials, broker writer, scheduler, raw vault search or arbitrary path exporter.
The packet's workflow routes a question; it does not execute the full owning
skill or certify its inputs as suitable for that skill. For current portfolio
conclusions, the owning workflow must verify live account scope separately.

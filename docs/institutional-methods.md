---
aliases: [institutional financial methods]
categories: [meta]
type: reference
tags: [topic/meta]
status: active
created: 2026-09-12
updated: 2026-09-12
related: ["[[financial-analysis-contract]]", "STATE"]
---

# Institutional financial methods -- implementation and use

This is the algorithm routing and model-use contract for the existing FIS engine.
It supplements source/evidence semantics in financial-analysis-contract.md.
An implemented public method is not proof of proprietary bank-system parity.
Confidence: HIGH for explicit mathematical definitions; runtime evidence is in
the dated institutional validation and benchmark receipts. No return guarantee.

## Select the applicable model

| Need | Executable owner | Required input and interpretation |
|---|---|---|
| Operating company value | tools/fis/valuation.py | Annual revenue, margins, taxes, reinvestment efficiency, WACC, terminal ROIC/growth, equity bridge, diluted shares; one currency and explicit evidence IDs |
| Price-implied operating expectations | valuation.implied_operating_margin | Same valuation model and explicit margin bracket; other assumptions fixed; refuses an unbracketed solution |
| Covariance estimation | tools/fis/covariance.py | Ordered, aligned observations by asset; sample, original OAS, EWMA with explicit decay, or published QIS; report observation count, divisor, conditioning, method and timing |
| Portfolio risk | tools/fis/risk_engine.py | Verified covariance, normalized weights, explicit data dates; supplied asymmetric/non-PSD matrices are not valid risk inputs |
| Tail risk | risk_engine.empirical_expected_shortfall | Quantile-integral expected shortfall with fractional boundary mass; daily empirical loss is distinct from a sqrt-time proxy |
| Evidence-weighted return views | allocation.black_litterman | Complete benchmark weights, same-period covariance, risk aversion, tau and explicit view covariance Omega; correlated views supported; uncertainty is not invented |
| Constrained research allocation | allocation.optimize_allocation | Current weights, explicit costs, horizon, optional return assumptions, asset cap, turnover and named linear exposure limits |
| Account-specific rebalance | tools/fis/portfolio_engine.py | Account/security identity, cash source, prices, lots, explicit constraints; mandatory independent replay and no-action alternative |
| Causal strategy simulation | tournament_runner.simulate_target_weights | Dated target decisions, prices, costs; close-t decisions fill at close-t+1; cash/shares reconcile; missing held prices refuse |
| Synthetic algorithm comparison | benchmark_institutional.py | Frozen complete plan, source hashes, new output directory and disposable process; every case/failure retained |
| Locked evaluation | evaluation/request_access.py | Canonical gateway only; backend absence is a refusal. The legacy firewall is explicitly synthetic-only. |

All counts, parameters and algorithm names here are implementation descriptions:
prov: script:current modules, institutional tests and fixed benchmark plan.

## Valuation discipline

Use an operating FCFF model for the business it models. Financial institutions,
distress optionality, complex taxes/NOLs, pensions, leases and future dilution
need separately supported adjustments or a different model. The model cannot
infer those adjustments from a ticker. Negative operating profit produces no
automatic tax credit. Capital release on declining sales is an explicit flag.
That flag does not verify an invested-capital balance or realizable liquidation
proceeds; a release assumption needs separate support.

The terminal phase must fund its growth: reinvestment rate = growth / ROIC.
Terminal growth must be below terminal WACC. Carry cash, debt, other claims,
unfloored equity value and diluted shares through the bridge. A zero floor on
equity must not conceal distress. Report sensitivity and the fraction of value
coming from the terminal phase; these do not calibrate scenario probabilities.
See [Damodaran's terminal-value analysis](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/valquestions/termvalueexreturns.htm).

```
python tools/fis/evidence.py numeric-evidence.json
python tools/fis/valuation.py operating-assumptions.json --implied-price 25
python tools/fis/allocation.py allocation-assumptions.json
```

The price above is a synthetic command example, not a quote or advice. Preserve
the evidence envelope next to the assumption file, join input_ids to reviewed
claims, and attach the exact code revision and calculation result. The numerical
CLI validates assumptions; evidence.py validates declared source semantics;
neither verifies the cited issuer passage without source review.

## Estimation and allocation discipline

Sample covariance remains a comparison baseline. Shrinkage addresses sampling
noise under stated assumptions; no estimator is uniformly best under every
distribution/regime. QIS is Ledoit and Wolf's published method, not a newly
invented algorithm. The implementation uses symmetric eigendecomposition and
retains the applicable upstream license. See the authors' [2022 QIS paper](https://www.econ.uzh.ch/dam/jcr:27e9ffa4-578e-4d6f-84d9-7707c98cedb0/bernoulli_2022.pdf)
and [official code links](https://www.econ.uzh.ch/en/people/faculty/wolf/publications.html).

Black-Litterman combines an equilibrium prior and uncertain views; it does not
discover alpha or make subjective views correct. Keep posterior mean uncertainty
separate from predictive return covariance. See [Goldman Sachs's model history](https://www.goldmansachs.com/our-firm/history/moments/1990-black-litterman-model).

The allocation objective includes asset-specific linear cost penalties at
selection time, plus caller-supplied exposure/turnover constraints. It is a
convex single-horizon research problem, not a full multiperiod execution system.
Its independently checked LP primal/dual bound measures numerical suboptimality
and includes an allowance for accepted covariance roundoff curvature. Solver
convergence alone does not authorize output.
Actual cash/tax/account feasibility must then pass the existing portfolio engine.
The rationale for modeling costs at selection is supported by [Ledoit and Wolf, 2025](https://www.econ.uzh.ch/dam/jcr:cd9c657f-16d3-4155-872d-e5ebae7557ac/qref_2025.pdf).

Expected shortfall at a stated confidence and horizon is an established tail-risk
measure. Implementing it does not implement a bank's regulatory capital framework:
liquidity horizons, stressed calibration and non-modellable factors are separate.
See [Basel market-risk methodology](https://www.bis.org/bcbs/publ/d457.pdf).

## Evaluation and model-use boundaries

Keep conceptual correctness, numerical tests, synthetic estimation performance,
historical economic performance and prospective outcomes separate. Compare to
simple baselines. Inspect every regime/candidate/failure, fees, turnover, missing
observations and the actual fill schedule. A negative-control failure blocks the
whole comparison; a favorable control cannot skip later controls.

The sealed synthetic plan fixes methods, cases, seeds, metrics, costs and failure
handling before results. The runnable source is separately hashed before release.
Reports retain all results and describe the case mixture; synthetic confidence
intervals support only that experiment. They cannot establish bank parity or alpha.
Corrections after a run produce a new receipt and disclose the invalidated run.
The evaluator does not accept arbitrary candidate callbacks or supplied rewards.

A temporary process with file/network guardrails protects this trusted numerical
run from accidental access. It is not an independent machine or a secure enclave.
Existing locked holdouts remain unopened. No promotion follows from this sandbox.
The legacy evaluation firewall now requires an explicit fresh synthetic fixture
and must not create another route to persisted evaluation data.

The existing confidence score remains a subjective evidence-constrained input to
unchanged doctrine rules. A claimed probability needs an outcome definition and
dated empirical calibration, sample size and limitations. Evidence-quality caps
are not statistical calibration. Model-use limitations and outcome monitoring
are informed by [SR 26-2, April 17, 2026](https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm), which supersedes SR 11-7;
this personal workspace is not being certified as a regulated bank platform.

## Data access, actual coverage and acquisition boundaries

Observed 2026-09-13. This is an access map, not a claim that every dataset is
downloaded, point-in-time complete or cleared for redistribution. Select a bounded
question, identify the instrument/population and period, acquire through the
existing owner, preserve the original labels and revision metadata, then validate
and register the specific dataset. Never turn aggregate public series into a
claim of complete historical security-level coverage.

| Data family | Existing route and useful scope | Observed coverage and limits |
|---|---|---|
| Issuer statements and filings | the broker public `reported_financials`, `filing_index`, `filing_facts`; `tools/pit/edgar_pit.py` for acceptance-time reconciliation | Fresh Codex read reconciled MSFT FY2025/FY2026 revenue, income and rounded margins; same filing origin, not two independent sources. Other issuers/fields need their own reads. |
| Quotes, instruments and actions | `tools/fis/capabilities.py`; existing technicals and `tools/pit/dual_price_store.py` / security master | Callable schema is distinct from historical depth, identifier continuity, corporate-action reconciliation and account coverage. Broker and third-party series remain separately attributed. |
| Macro vintages and rates | `tools/pit/macro_vintages_alfred.py`, `macro_vintage_store.py`, existing FRED connector when exposed | Current saved status records 36 actual-vintage series and 16 no-safe-use series; this metadata observation is not a fresh source or database audit. API-key access is needed for full vintage history; latest CSV cannot substitute. |
| Factors and benchmarks | [French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html), dataset registry, covariance/attribution owners | Choose the exact factor/portfolio file, frequency, currency and methodology version. Freeze downloaded bytes and missing-value semantics; aggregate factor portfolios are not constituent-level histories. Preserve the documented FIZ/CIZ transition. |
| Valuation reference inputs | [Damodaran data and archives](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/data.html), existing valuation owner | Industry/region averages, estimates and archives are dated research inputs. Record the exact sheet/date/definition and usage terms. They do not establish a current company forecast or universal valuation parameter. |
| Global credit, debt and exchange-rate aggregates | [BIS SDMX API and metadata](https://data.bis.org/help/tools), bounded public source acquisition and dataset registry | Documentation inspected; no completed BIS ingest is claimed. Preserve dataflow/version, dimensions, observation flags, release date and provider revisions. Follow [BIS permitted-use terms](https://data.bis.org/help/legal), including attribution and non-misleading presentation. |
| Energy and industry economics | [EIA APIv2](https://www.eia.gov/opendata/documentation.php), bounded public source acquisition and dataset registry | Documentation inspected; no completed keyed ingest is claimed. Discover metadata/facets, use explicit frequency/date bounds and deterministic pagination (JSON limit 5,000). Preserve units, API version, missing strings and revisions. Keys and echoed request parameters must never enter logs or source archives. |
| Household constraints | Authorized host Finances and scoped broker reads; cashflow/account reconciliation owners | Finances account tools are unavailable in this Codex session. No account refresh or household-completeness claim follows from public/synthetic examples. Jurisdiction, effective tax year, insurance and liquidity assumptions require current evidence. |

For macro/sector disconfirmation, test the transmission channel rather than using
a broad aggregate as a company forecast: demand volume versus price, capacity
versus utilization, financing cost versus credit availability, currency movement
versus hedging, and energy load versus deliverable power. Pair each thesis with
the contrary observation that would change it. These are research questions until
an applicable model and data are inspected; correlation alone is not causation.

The observed connector receipt is
`Efforts/osanwe-v2-overhaul/reports/financial-corpus-2026-09-13/connector-reconciliation.json`.
The new focused methods route through `wiki/meta/knowledge-moc.md` and the current
document-admission manifest. Reuse rights are assessed for each admitted portable
passage; public accessibility alone does not authorize exporting source books.

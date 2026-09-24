---
name: portfolio
description: "Use when asked for portfolio advice, risk, sizing, review, or trade journaling. /portfolio advise = strategic memo; /portfolio risk [ticker] = risk dashboard or position deep dive; /portfolio size `<ticker>` = sizing worksheet; /portfolio review [weekly|monthly|quarterly] = structured review; /journal log|review|lessons = trade journal. Cites every number; never places orders; not /invest or /networth."
metadata:
  categories: decisions
  osanwe-risk: "critical"
  osanwe-effort: "max"
  osanwe-arguments: "advise [--full|--quick] | risk [var|exposure <T>|scenario <n>|hedge|`<TICKER>`] | size `<TICKER>`|rebalance|review | review [weekly|monthly|quarterly]"
  osanwe-argument-hint: "/portfolio advise | /portfolio risk `<ticker>` | /portfolio size `<ticker>` | /portfolio review monthly | /journal log `<ticker>` BUY | /journal review 30d | /journal lessons"
  osanwe-allowed-tools: "Read Write Edit Grep Glob Bash"
  osanwe-categories: "decisions"
  osanwe-type: "skill"
  osanwe-status: "active"
  osanwe-created: "2026-08-24"
  osanwe-updated: "2026-09-12"
  osanwe-authority: operator
---

Financial evidence contract: `docs/financial-analysis-contract.md` governs source quality, temporal/basis semantics and missing-data handling across harnesses.
For material numeric batches, run `python tools/fis/evidence.py <envelope.json>` before output, or disclose manual review and any unverified semantics.
Plugin interoperability: `.agents/skills/finance-data/SKILL.md` owns typed evidence intake and portable Finance/Data handoffs. This skill retains its financial procedure and gates.
Probe callable tools at run time; installed plugin metadata alone does not establish a usable connector or source schema.
Complete the question-to-review sequence in `.agents/skills/finance-data/ref-capabilities.md` before delivering an advisory brief.
This includes objectives, horizon, liquidity, applicable constraints, supported obligations, computed reversal conditions and review of the final output.
Institutional method routing: `docs/institutional-methods.md`. Use dated aligned returns with `tools/fis/covariance.py` and explicit risk horizons; covariance estimation and numerical allocation do not establish account completeness.
Use `tools/fis/allocation.py` for cost/exposure-constrained research targets, then the existing portfolio engine for account/lot/cash reconciliation and no-action.


# /portfolio -- consolidated portfolio desk (advise + risk + allocate + review + journal)

Created 2026-08-24 by consolidation: absorbs `/advise`, `/risk`, `/allocate`,
`/review` (no prior file existed; its behavior is defined here), and `/journal`.
Originals archived at `.agents/skills/_archive/consolidated-2026-08-24/`
(see that dir's INDEX.md); their ref-* methodology docs moved alongside into
this directory (`ref-risk-methodology.md`, `ref-allocation-methodology.md`,
`ref-journal-format.md`). All rules below are carried over verbatim in
substance from the source skills; each subcommand routes to its logic.

This skill measures and advises only. It NEVER places orders (D-SEC-1),
NEVER writes to Atlas/, and NEVER touches brokerage order placement.

### Mode routing (Pattern 6 -- deterministic, from $ARGS only)

| $ARGS | Route |
|---|---|
| `advise` | MODE ADVISE -- full strategic advisory memo |
| `risk` (no further args) | MODE RISK, dashboard variant |
| `risk var` | MODE RISK, VaR block only |
| `risk exposure <TICKER>` or `risk <TICKER>` | MODE RISK, single-position deep dive |
| `risk scenario <name\|#>` | MODE RISK, one stress rerun at current holdings |
| `risk hedge` | MODE RISK, hedge framing |
| `size <TICKER>` | MODE SIZE, initiation or hold-state add worksheet |
| `size rebalance` | MODE SIZE, ordered trade list |
| `size review` | MODE SIZE, doctrine-sizing audit |
| `review` (or `review weekly`) | MODE REVIEW, weekly cadence (default) |
| `review monthly` | MODE REVIEW, monthly cadence |
| `review quarterly` | MODE REVIEW, quarterly cadence |
| `journal log <ticker> <BUY\|SELL\|TRIM\|HOLD> [details]` | MODE JOURNAL LOG |
| `journal review <period>` | MODE JOURNAL REVIEW |
| `journal lessons [--since <date>]` | MODE JOURNAL LESSONS |

The harness may also route bare `/journal ...` invocations straight here;
strip the leading token and treat identically. Unknown mode or ambiguous
ticker -> print this table (or candidate list) and stop. No args -> usage
table, run nothing.

### Quality Rules (global execution rules; bind EVERY mode)

1. Read AGENTS.md fully before any write (router precedence).
2. ASCII only in everything written (Pattern 22).
3. Never read `.raw/`, `private/`, `finance/`, `credentials/`,
   `.env*`, `auth.json`, or `*.local.md` contents. The journal additionally never pulls broker fills.
   Current quantities, dollars, basis and lots require current-session broker
   read evidence acquired through available read tools or `/networth`. Missing
   coverage is UNVERIFIED; do not use saved holdings/history files as a fallback.
4. One writer; never push; archive-don't-delete.
5. All numeric claims cite their generated source file or an inline
   computation note `(computed: Rx, bars A..B)` -- bare figures are defects.
6. NO TRADE LANGUAGE in risk/screening-flavored output: forbidden "you should
   sell", "trim", "buy puts", "consider exiting". Measured statements,
   verbatim attributed doctrine quotes, and pre-committed responses only.
   (ADVISE and SIZE are the designated advice/sizing surfaces; they still
   never place orders.)
7. NO STALE LITERALS: parse holdings, prices, ratings at run time; never
   quote them from skill prose or memory.
8. UNSCORED MEANS UNSCORED: a ticker without factor-store bars is flagged,
   never zero-filled or assumed calm.
9. DOCTRINE CEILINGS ARE HARD: computed breaches print the breach and the
   headroom, never a shrunk ceiling. Multipliers stack by MIN, never
   multiplied. Override lanes are never self-invoked.
10. Write budget for the whole skill: MODE ADVISE writes ONE file
    (`Calendar/decisions/advisory/advisory-<date>.md`) plus its session-log
    line; MODE REVIEW writes ONE note
    (`Calendar/decisions/reviews/review-<mode>-<date>.md`); MODE JOURNAL
    LOG/LESSONS write exactly their two locations (below); RISK and SIZE are
    read-only (stdout only). Nothing else, ever.
11. After any canon edit: `python .agents/scripts/checkall.py` stays
    ALL GREEN.

---

# MODE ADVISE (= former /advise)

Portfolio-level strategic advisor. Retrieves the applicable latest analyses,
calibration evidence, prior decisions, regime and sector context, contrary evidence
and current scoped holdings -- then gives holistic portfolio
advice: allocation, positioning, what to buy/sell/trim, where to deploy next.
NOT a single-ticker tool (use /invest). Not a compliance or tax advisor.
Produces a ranked, evidence-cited advisory memo.

### When to use / not

Use: "What should I do with my portfolio?", periodic allocation review, after
major market moves or when several analyses point the same direction, when
cash accumulates beyond deployment bands.
Not for: single-ticker depth (`/invest`), positions snapshot (`/networth`),
tax or legal advice, options structure design (`/invest` Phase K-ter),
trade execution mechanics.

### The Investment Philosophy (operator-ratified, binds this mode)

AI-optimistic but model-layer-bearish:

1. **The real moat is DATA, ENERGY, and COMPUTE.** Model weights commoditize;
   open-source erodes frontier-model pricing power. Never underwrite a thesis
   whose primary moat is "our model is smarter" -- that decays.
2. **AI demand is structural**: inference consumption grows regardless of
   which model wins. The toll roads -- power generation, grid equipment,
   data-center electrical/thermal, memory/storage, networking, foundry
   capacity -- collect revenue no matter who leads the model race.
3. **Energy is the binding constraint**: compute scales to power
   availability. Names that own power (nuclear fleets, IPPs), build grid
   capacity (GEV/ETN), or cool compute (VRT) sit at the chokepoint.
4. **Concentration is accepted but must be MEASURED** (sector-alpha.py
   exists for exactly this) -- not blindly accumulated.
5. **Discipline over narrative**: calibration numbers override enthusiasm.
   If selection alpha is negative, widen hurdles; do not chase.

Every recommendation MUST be consistent with this philosophy, or explicitly
flag the deviation and why it's warranted.

### Phase A1 -- Assemble the full picture (read-only)

Establish the decision horizon, objectives, liquidity needs and relevant account
constraints first. Use current authorized preferences and name missing inputs;
never invent risk tolerance, tax treatment or return targets. Then inspect the
following evidence for the supported question, recording why each source applies
or is unavailable. Do not load unrelated or unclassified financial material.

A. **Holdings ground truth**: current-session broker read evidence for each
   included account/asset class; reconcile position values, cash and totals.
   Missing coverage stays UNVERIFIED. Historical holdings files do not verify
   current quantities, lots or account cash.
B. **Applicable analyses**: `git log --all --
   'wiki/investing/analyses/'`; per held ticker: latest rating + date; wave
   analyses `Efforts/osanwe-v2-overhaul/_work/wave*.md`; flag held tickers
   with NO analysis (blind spots) and stale ones (>45d).
C. **Calibration engine outputs**: `wiki/maintenance/calibration/calibration-*.md`
   (latest; beat-SPY rates by horizon); `confidence-map.json` (calibrated vs
   stated); `decision-attribution.md` (doctrine selection alpha);
   `dissent-tracking.md` (failure-mode realization rates);
   `sector-attribution.md` (per-sector alpha + concentration flags);
   `regime-stratification.md` (hit rates by trend/vol regime).
D. **Market state**: `wiki/investing/benchmarks/macro-regime-tables.md`
   (WALCL/WRESBAL/SOFR/RRP + curve + credit + yen DEXJPUS + VIX percentile);
   `wiki/investing/benchmarks/correlation-clusters.md`; entity surveillance
   `wiki/maintenance/surveillance/entity-triggers-*.md`.
E. **Doctrine constraints**: `Atlas/sources/investing/ref-portfolio-doctrine.md`
   (deployment bands, concentration ceilings -- READ-ONLY context);
   `ref-scoring-models.md` bands block.

### Phase A2 -- Synthesis

Produce these judgments, each citing evidence files:

1. **Portfolio health grade** (A-F): concentration, calibration honesty,
   execution discipline (unexecuted ratified actions), coverage gaps.
2. **What the calibration engine says about US**: current beat-SPY rate,
   calibrated confidence discount, selection alpha trend. Advice quality is
   bounded by judgment quality -- say so explicitly.
3. **Regime-adjusted posture**: given macro tables, should deployment bands
   tighten or relax?
4. **Ranked opportunities** (max 5, hard cap 10): specific, sized,
   evidence-cited actions -- e.g., "TRIM X: position is `<pct>` of equity, `<pct>`
   unrealized, selection alpha negative -- tranche out 25% into band low."
   Every action names its source documents.
5. **Blind-spot closure queue**: held-but-unanalyzed names needing /invest;
   stale analyses needing refresh.
6. **Anti-portfolio check**: what would make us wrong about the whole
   book's dominant thesis? Name the observable falsifiers and levels.

### Phase A3 -- Output (the ONLY file this mode writes)

Before delivery, compare holding and other applicable alternatives with consistent
costs and constraints; compute material reversal conditions and coupled scenarios.
Complete substantive review for material BUY, HOLD and SELL conclusions, including
the actual rendered labels, tooltips, filters and exports when present. Workbench
review accepts only public/synthetic inputs; personal review remains in its
authorized session and must disclose any unverified execution boundary.

Deliver the completed brief in the authorized session. For a public/synthetic
brief, write `Calendar/decisions/advisory/advisory-<date>.md` as below. For a
personal brief, that path may contain only a non-sensitive process record: no
amounts, account identifiers, personal conclusions, snippets or revealing hashes.
Apply this personal-persistence rule to every mode's note and session-log record.

```
---
categories: [decisions]
type: advisory
date: YYYY-MM-DD
portfolio_health: <grade>
regime_read: <one-line>
actions_recommended: <count>
confidence_cap_rule: <per evidence grades>
created/updated/status/tags/related: canonical
---

# Portfolio Advisory -- YYYY-MM-DD

## Verdict (3 paragraphs max)
<health grade + why; regime posture; the single most important action>

## Ranked Actions
1. ACTION -- rationale w/ citations -- size -- trigger
...

## Judgment Quality Report
<beat-SPY, calibrated confidence, selection alpha -- and how much to trust
this memo given those numbers>

## Philosophy Check
<how recommendations align with the data-energy-compute moat thesis>

## Falsifiers
<what would invalidate today's advice>
```

Then append one line to the session log and commit atomically.

### ADVISE quality gates

- Every recommended action cites >=1 generated artifact (no vibes).
- Concentration warnings fire at >25% single-name or >40% single-sector.
- Negative selection alpha -> at least one de-risking recommendation unless
  the regime read contradicts it with cited data.
- Hard cap 10 ranked actions; focus beats completeness.

### ADVISE failure taxonomy

- Missing broker coverage -> affected portfolio quantities, weights, dollars
  and recommendations remain UNVERIFIED; continue independent research only.
  No saved-history fallback. Missing calibration artifacts -> run
  tools/backtest-offline.py first; empty store -> HALT with "calibrate before
  advising". Never invent calibration probabilities.
- Conflicting signals between surfaces -> present both readings; never
  average silently.

---

# MODE RISK (= former /risk)

Quantify the current book's risk from the vault's own data. This mode
measures only; recommendations belong to ADVISE, /gate f, or the operator.
READ-ONLY: writes nothing anywhere (stdout only). Normative math:
`ref-risk-methodology.md` (this directory); optional deeper reference
`wiki/research/ref-portfolio-risk-decomposition.md` (if absent, the
methodology file governs).

Submodes: `var` (VaR numbers only) | `exposure <T>` (one position's
risk-contribution dive) | `scenario <name|#>` (stress rerun at today's
weights) | `hedge` (structure-level framing). Bare `risk` = full dashboard:
VaR block + stress summary + concentration ledger + correlation warnings +
blind spots.

### Inputs (never read `.raw/ private/ finance/ credentials/ *.local.md`)

| Source | Owns | Gate |
|---|---|---|
| Current-session broker read evidence | Account/asset quantities and values | Reconcile coverage/time; missing scope UNVERIFIED, no saved-file fallback |
| `Efforts/osanwe-v2-overhaul/_work/factors.db` | Live bars + macro factors (sqlite) | Report max bar date actually used |
| `wiki/research/ref-scenario-stress-test.md` | 10 scenarios: episodes, replay returns, pre-committed responses | Cite generation date |
| `wiki/research/ref-correlation-matrix-full.md` | 90d rhos, clusters, N_eff, held-pair warnings | Cite generation date |
| `wiki/research/ref-portfolio-risk-decomposition.md` | Optional VaR/factor reference | If absent, methodology file governs |

Risk arithmetic is local after current-session broker read acquisition.
An offline run without that evidence cannot establish current portfolio risk;
it may analyze an explicitly hypothetical book, labeled as such. Public return
histories come from factors.db with dates and price-basis verification.

### Procedure

Phase R-A reconcile current-session holdings and account scope. Separate total
known value V from scored sleeve value V_s; normalize scored weights by V_s,
matching `portfolio_risk` normalization. Missing holdings remain UNVERIFIED.
Inspect coverage and source dates before constructing aligned return rows.
Phase R-B compute the requested recipes only. Default covariance window = last
min(90, available) COMMON sessions across scored assets; historical scan = 252.
Report covariance method, observation count, data date, price basis and excluded
risk. Dates that are missing remain UNKNOWN; never infer freshness from file mtime.
Round only the final displayed dollars to $10 and percentages to 0.1 (F-R4).
Phase R-C render: exactly one Output-format block; every number carries
`[source]` or `(computed: Rx, bars A..B)`; quote pre-committed doctrine
responses verbatim with attribution, never paraphrased tighter or looser.
Phase R-D close out: BLIND SPOTS (unscored tickers, stale refs, missing
analyses); mode-relevant NEXT line; nothing written to disk.

### Computation recipes (normative; math in ref-risk-methodology.md)

Use factors.db read-only and the executable methods in
`docs/institutional-methods.md`; formula detail is in ref-risk-methodology.md.
Do not assemble a portfolio covariance matrix from differing pairwise windows.

- R.1 HOLDINGS: reconcile broker-verified values; V_s = SUM(scored mv);
  w_i = mv_i/V_s. Show known-total V and every excluded/UNVERIFIED scope.
- R.2 VOL/COV: construct complete common-date returns without forward-fill.
  Call `covariance.estimate_covariance` with an explicit method (sample baseline,
  or justified OAS/QIS/EWMA), `annualization=1`, data date and report date.
  EWMA requires explicit decay; preserve diagnostics and missing-date warnings.
- R.3 RISK: call `risk_engine.portfolio_risk(w, C, as_of=..., report_date=...,
  n_obs=..., covariance_horizon="1 trading day")`. Delta-normal zero-mean
  VaR_1d_95 = 1.645*sigma_p,d*V_s; sqrt(5) is an i.i.d. scaling proxy only.
  For daily empirical ES use `empirical_expected_shortfall(-R @ w, 0.95)*V_s`
  on aligned returns, with fractional tail-boundary mass. A Gaussian ES
  comparison, if shown, is separate; neither is an annual loss forecast.
- R.4 HIST WORST: proxy-based (VOO preferred): worst day + rolling-5d return
  in 252 sessions, beta-scaled to the equal-weight held book. Labeled
  LOW-CONFIDENCE when >=3 held names lack the window.
- R.5 SCENARIO: resolve name -> rates|1 capex|2 yen|3 credit|hy|4
  memory|supercycle|5 liquidity|6 single-name|earnings|7 china|taiwan|8 winter|9
  pivot|bullish|10. Recompute impact_i = p_i*mv_i at TODAY'S values using
  the stress file's stored p_i and episode windows; sum; compare vs the
  file's PORTFOLIO IMPACT and explain drift. Proxies keep their file labels
  (proxy mapping per position). A zero shock is allowed only as an explicitly filed
  assumption; a missing shock remains UNVERIFIED, never zero.
- R.6 CONCENTRATION: use the dated correlation reference only if asset
  set/window/basis match; otherwise recompute held pairs rho>0.75 and
  participation-ratio N_eff from the validated common-window matrix. Report cluster
  memberships, ceiling flags vs amber 30%/red 35% [ref-portfolio-doctrine.md].
- R.7 EXPOSURE: component delta-normal VaR_i =
  1.645*w_i*(Cw)_i/sigma_p,d*V_s. Its sum must equal the SAME model's total
  VaR before display rounding. At zero volatility avoid division; report zero
  dollar contributions and undefined percentage attribution. Do not label
  covariance contributions as an empirical ES decomposition.

### Output formats

`risk` dashboard:

```
=== /portfolio risk ===
BOOK: verified known $<V>; scored $<V_s> across <N> positions [broker read, <time + scope>]
AS-OF: bars through <max date used>; refs generated <dates>

VALUE-AT-RISK (delta-normal 95%, <method>, <n> common observations):
  1-day VaR:   $X (x.x% of scored book)   (computed: R.3, bars A..B)
  5-day proxy: $Z                          i.i.d. sqrt(5) scaling
  ES 1-day:    $E                          empirical quantile integral, fractional tail mass
HISTORICAL WORST (252s): proxy DD p%; book-scaled $Q [R.4, proxy-based label]

STRESS SUMMARY (all 10 at today's weights):
  #n <name>  <pct>%  <$amt>  [stress file S#n]   <- mark stored WORST

CONCENTRATION LEDGER:
  rho>0.75 held pairs: <table>            [corr matrix sec 4]
  effective bets: N_eff ~x.x of m scored  [corr matrix sec 3]
  ceiling flags: <names vs 30%/35%>       [ref-portfolio-doctrine.md]

CORRELATION WARNINGS: <chain -> reading, one line each>
BLIND SPOTS: <unscored / stale / never-analyzed>
NEXT: /portfolio risk var | scenario <name> | risk <TICKER> | risk hedge
```

`risk var`: risk block + HISTORICAL WORST, with model, confidence, price basis,
window/count, covariance diagnostics and unknown/stale-date disclosures. State
that empirical daily ES and Gaussian VaR are different models; sqrt(h) assumes
uncorrelated returns and is not a calibrated multi-day tail forecast.

`risk <TICKER>` / `risk exposure <T>`:

```
=== /portfolio risk <T> ===
POSITION: qty x dated mark = $mv (w% of verified scope) [current-session broker read]
VOL: daily sigma s%                              (computed: R.2, bars A..B)
RISK CONTRIBUTION: comp-VaR $c = d.d% of VaR     (computed: R.7; sum-check ok)
CORRELATION: max rho r (<name>); avg to held a   [corr matrix]
CLUSTERS: <memberships / duplication chains>
SCENARIO EXPOSURE RANK: 1) <worst, pct> 2) ...   [stress file]
COVERAGE: <N analyses / calibration status>      [dated analysis/calibration sources]
```

`risk scenario <name>`: resolved title + trigger definition (quoted),
episode window + precedent dates, per-position table recomputed at current
values (+ drift-vs-file note), PORTFOLIO IMPACT line (recomputed %/$), HIT
HARDEST / SAFE-HEDGE lines as measured, PRE-COMMITTED RESPONSE quoted
verbatim + attributed, footer: "Impact measurement only. Decision path:
/portfolio advise or operator."

`risk hedge`: structure-level framing ONLY. Per finding: the duplicated bet,
combined weight, dominant scenario losses, offset classes ALREADY in the
book (named as measurements), reserve/throttle mechanics the doctrine
already defines (quoted). Closing line fixed: "Instrument selection and
execution are out of scope for this skill. Route to /portfolio advise
(allocation) or /gate f (trade discipline)."

### RISK failure modes

F-R1 Stale-literal (book values from prose) | F-R2 Silent gap (no-bars names
dropped without an UNSCORED line) | F-R3 Advice leak | F-R4 Fabricated
precision | F-R5 Attribution drop (doctrine thresholds presented as our own).

---

# MODE SIZE (= former /allocate)

Position sizing and portfolio construction. Math lives in
`ref-allocation-methodology.md` (this directory); this file owns flow,
gates, formats. Every number carries `[source]` or
`(computed: R-A#, bars A..B)`. Operator executes; never places orders
(D-SEC-1); never writes to disk (read-only; ratification belongs to /decide).

Submodes: `<TICKER>` = new-initiation sizing worksheet (dollar amount, share
count, lump-vs-tranche plan, stop level, post-entry weights) | `rebalance` =
current vs target weights -> ordered trade list respecting tax lots and
tranches | `review` = audit current sizing vs doctrine ceilings (single-name,
thesis, sector, cash buffer). Ticker already HELD -> HOLD-STATE panel
(add-sizing against headroom), never a fresh initiation.

### Inputs (never read `.raw/ private/ finance/ credentials/ *.local.md`)

| Source | Owns | Gate |
|---|---|---|
| `Efforts/osanwe-v2-overhaul/_work/factors.db` | bars(ticker,date,close) for vol/beta; factors for ^VIX, DFII10, DGS10, HY OAS | Report max bar date used |
| `Atlas/sources/investing/ref-portfolio-doctrine.md` | Machine `doctrine:` block: ceilings, deployment multipliers, sizing constants, override lane | Run `python tools/doctrine-lint.py --json`; exit 2 -> HALT |
| Current-session broker read evidence | Quantities, account cash, basis and lots | Missing input/coverage UNVERIFIED; do not size against saved-history values |
| `wiki/maintenance/calibration/confidence-map.json` | Truth-adjusted confidence bins | Cite `generated` date |
| `wiki/research/ref-correlation-matrix-full.md` | 90d rhos, clusters, N_eff | Cite generation date; recompute pairwise rho from bars if pair absent |
| `wiki/research/ref-composite-scoring.md` | Quality scores, component ranks | Cite generation date |
| `wiki/research/ref-portfolio-optimization.md` | Target weights (Sec 3), regime/deployment state (Sec 0), trade-ordering precedent (Sec 4) | Cite date; regenerate-before-acting caveat |
| Latest analysis for the ticker | Rating, R/R, stop basis, target, kill criterion, GATE-F verdict | Missing -> HALT initiation (blind-spot protocol) |

Sizing arithmetic is local after current-session broker read acquisition.
Prices from factors.db/analysis files retain their dated regular-close basis;
stale marks cannot establish current affordability. No orders or account writes.

### Procedure

Phase S-A parse/gate: resolve mode; doctrine machine block via doctrine-lint
(HALT exit 2); record `doctrine_version` fingerprint for the header stamp;
reconcile broker holdings (V, weights, read time; SCORED vs UNSCORED split); initiation
mode loads latest analysis and extracts rating, rr_ratio, stop basis
candidates, target, kill-criterion price, GATE-F verdict -- missing any ->
HALT naming the gap; note ref generation dates vs latest ingest.
Phase S-B compute: recipes R-A1 deployment state -> R-A2 calibrated win prob
-> R-A3 half-Kelly -> R-A4 volatility parity cross-check -> R-A5 waterfall
caps -> R-A6 stop construction -> R-A7 lump-vs-tranche -> R-A8 post-entry
weights; R-B (rebalance), R-C (review). Arithmetic: prefer
`python tools/sizing-eval.py` (model fills form, script
computes). Inline computation must show both half-Kelly forms and assert
reconciliation tolerances (identity 1e-9; dollars $0.50; shares derivation
$0.50). Round dollars to nearest $10, percentages to 0.1.
Phase S-C render exactly one Output-format block; quote doctrine thresholds
verbatim with attribution. Phase S-D close out: BLIND SPOTS; mode footer;
nothing written to disk.

### SIZE quality rules (failure modes F-A1..F-A9)

- F-A1 Formula bypass: sizing flows through ref-allocation-methodology.md
  formulas or sizing-eval.py, never intuition.
- F-A2 Stale literal: parse holdings/prices at run time.
- F-A3 Silent gap: no-bars names flagged, not dropped.
- F-A4 Ceiling softening: amber/red lines presented as negotiable.
- F-A5 Attribution drop: doctrine constants presented as ours.
- F-A6 Execution leak: any order placement or broker mutation; authorized
  broker reads establish inputs, while output ends at inert levels/sizes/conditions.
- F-A7 Self-invoked override: piercing a sub-1.0 gate without a verbatim
  user directive quoted in the disclosure. Report availability N/5 only.
- F-A8 Multiplied throttles: compounding 0.5x states instead of MIN.
- F-A9 Fail-open unknown: unreadable rate leg -> 0.5x; unreadable VIX ->
  unknown-treated-halted 0.0x; missing release-condition inputs -> reserve
  stays netted.

### Output formats

```
=== /portfolio size <TICKER> ===
INPUTS: rating <R> [analysis, date] | R/R b=<x.xx> | stated conf <c> ->
        calibrated <p> (bin <lo-hi>, ratio <r>) [confidence-map, date]
        daily sigma <s>% (computed: R-A4, bars A..B) | beta <b1>
GATE STATE: deployment mult <m>x = MIN(rate <..>, vix <..>) [doctrine block]
            DGS10 <y.yy> disclosure-only (level gate RETIRED 2026-07-30)
            reserve <$R> NETTED/RELEASED (per-condition stamps)
WATERFALL (computed: R-A3..R-A5):
  half-kelly $H -> haircut(s) $H' -> vol-parity $P -> MIN(...) = $CANDIDATE
  caps binding: <tranche 5% | name headroom | thesis headroom | cash-after-reserve>
RECOMMENDED SIZE: $<X> = <n> sh @ $<px> (regular close <date>)
  weight after entry: <w>% (now <w0>%); thesis <t>: <a>% -> <b>% (amber <line>)
ENTRY PLAN: LUMP | TRANCHE x<N> (<reason>; each <= 5% of book)
  tranche 1: <cond/zone> ... ; riders: <sleep-gate / earnings-window / confirm>
STOP: $<stop> (<basis>: <kill-price|200dma|swing-low>; distance <d>%, clamp 5-25%)
  R/R at stop/target: <rr>:1 vs hurdle <hh> [<rating>] -> PASSES/FAILS
BLIND SPOTS: <unscored / no-analysis / stale-ref lines>
NEXT: /portfolio size review | /gate f | operator executes (D-SEC-1)
```

```
=== /portfolio size rebalance ===
BASIS: $<V> across <N> verified positions [broker read, time/scope]; targets [optimization
       ref Sec 3, generated <date>]; deployment <m>x [doctrine state]
DRIFT TABLE: sleeve | now % | target % | gap $ (sorted by |gap|)
TRADE LIST (ordered: sells->buys, ratified->new, tax-advantaged->taxable):
  1. <SELL|BUY> <T> <sh> sh ~$<amt> acct <account key>
     lots: <highest-cost-first | lowest-gain | LTCG-boundary note | n/a>
     tranche: <single (<=5%) | split xN>  cites: <REC-n / doctrine line>
CASH CHECK: proceeds $<p> vs buys $<b> -> net external cash $<n>
RIDERS: <sleep-gate / wash-sale windows / min-trade round-downs>
NEXT: record /decide -> operator executes (D-SEC-1)
```

```
=== /portfolio size review ===
BOOK: $<V> [broker read, time/scope]; deployment <m>x; reserve <$R> NETTED/RELEASED
AUDIT LEDGER (PASS | FLAG | BREACH per row):
  single-name: <top names vs amber 30 / red 35>     [doctrine block]
  thesis: theme-alpha <w>% vs amber <50 interim to 2026-09-08 | 60> red 70;
          others vs 40 flag                          [MIN-headroom rule]
  sleeves: <sleeve> <w>% vs its construction band (CONSTRUCTION target, not ceiling)
           [optimization ref]
  correlation: <k> held pairs rho > 0.75              [corr matrix sec 4]
  cash: deployable $<c> vs min buffer = one 5% tranche + netted reserve
  unscored: <names>; unexecuted ratified: <actions>
VERDICT: <CLEAN | N FLAGS | N BREACHES -> /decide>
NEXT: /portfolio size rebalance | /decide
```

Integration notes: the /invest kernel sizing worksheet remains the BINDING
source for initiation trades; SIZE reproduces its math standalone -- on any
disagreement the kernel worksheet wins. RISK output feeds review context;
ADVISE ranked actions become sized orders here.

---

# MODE REVIEW (= former /review)

Periodic portfolio review at three depths. Orchestrator and checker of
RECORDS: reads what the wave analyses pre-committed (kill criteria, hold
bands), compares them to the latest measured state, routes every
action-shaped finding through the skills that own the decision, and never
invents a new threshold. Lands ONE dated note per run:
`Calendar/decisions/reviews/review-<mode>-<YYYY-MM-DD>.md`.

Cadence routing: `weekly` -> Phases A+B+C; `monthly` -> weekly PLUS
Phases D, E, F; `quarterly` -> monthly PLUS G, H. Escalation: any mode may
RUN deeper phases' *read-only* checks when a CRITICAL breach makes them
obviously relevant, but the note always states which mode ran and which
phases were included.

### Inputs (all local; record a freshness date for every one)

1. HELD roster: `wiki/research/ref-earnings-calendar.md` HELD list (single
   source for "what is held"; never reconstructed from memory).
2. Latest wave analysis per ticker: newest `wave*-<T>-analysis.md` by `date:`
   frontmatter across `Efforts/osanwe-v2-overhaul/_work/wave*-analysis.md`;
   also accept a same-shape refresh under
   `wiki/investing/analyses/<t>-analysis-*.md` when newer. Parse frontmatter:
   `rating`, `kill_criteria` list, `hold_band`, `price_at_analysis` /
   `price_asof`, analysis `date`. No analysis for a HELD name -> NO-ANALYSIS
   row (Phase H stale queue candidate).
3. Prices: factors.db `bars` last regular close + last bar date for
   staleness math.
4. Gate state: `tools/sizing-eval.py` output if freshly run this session;
   otherwise the deployment block of the latest
   `wiki/maintenance/doctor/doctor-<date>.md` or Section 0 of
   `wiki/research/ref-portfolio-optimization.md`, citing which + as-of.
5. New signals: `wiki/research/ref-alternative-data-signals.md` (GENERATED
   header carries its build date).
6. Doctrine machine block: `Atlas/sources/investing/ref-portfolio-doctrine.md`
   (concentration ambers, rate_shock leg, VIX throttle/halt, reserve release).
7. Surveillance + measurement surfaces: latest entity-triggers-*,
   calibration-*, `confidence-map.json`, `decision-attribution.md`,
   `sector-attribution.md`, `ref-portfolio-optimization.md`,
   `ref-composite-scoring.md`, `ref-hedge-construction.md`,
   `gates-registry.md` compliance rows.

Missing input -> explicit GAP row naming the missing artifact and its
regeneration command. Never estimate, interpolate, or fetch a substitute.

### Tool orchestration (run, never re-implement)

Run from vault root; capture each tool's exit code and cite it; on non-zero
exit log the stderr tail in a GAP row and continue with existing artifacts;
never edit a tool's emitted files.

1. `python tools/entity-surveillance.py` -- regenerate
   `wiki/maintenance/surveillance/entity-triggers-<date>.md` when older than
   3 trading days vs the store's last bar date (same rule as MODE WATCH);
   otherwise read the existing file and cite its date.
2. `python tools/portfolio-doctor.py` -- one-page digest stitching alerts /
   decisions-needed / measurement deltas. Weekly: fold sections into
   findings verbatim-attributed; monthly+ also use deltas as index into
   Phase E/F detail.
3. `python tools/backtest-offline.py` (`--help` first to confirm flags) --
   grade horizon(s) named by active hold bands (default 21d) offline from
   the store. Measures how prior bands/verdicts resolved; never re-sizes or
   re-rates anything.

### Phases

Phase A -- Hold-state audit (every mode; core loop). For EVERY HELD ticker:
load latest wave analysis (kill_criteria[], hold_band, anchor price/as-of,
rating, date); pull last regular close; compute distance to each kill level
(200DMA floors, $ stops) and position inside/outside the hold_band (+up/-down
pct vs anchor, elapsed trading days vs window). Non-price kill criteria are
evaluated against in-vault evidence ONLY; absent either way -> UNVERIFIED,
never declare passed on absent data. Classify: BREACH (criterion met or
close outside band's kill edge -> CRITICAL; fixed response route to
`/decide EXIT-review` or `/gate f` where a sheet governs; quote the breached
clause), WARN (within 2 pct of a kill level, or >75 pct of band days elapsed
with price in the outer quartile -> WARNING; route owning skill),
HOLD-CLEAN (one summary line, numbers cited). Lapsed hold_band without a
newer analysis -> STALE-BAND WARNING + Phase H queue.

Phase B -- Gate + macro disclosure (every mode). Deployment stack from
Input 4/6 with as-of dates, MIN-stacked: DFII10 rate_shock leg (>= +75bp
over 60 sessions, nominal DGS10 confirm >= +25bp, entered after 3
consecutive fire sessions, exit < 60bp), VIX throttle (>22 x5) and halt
(>35 x5), reserve-release conditions (SPX -15% DD / theme-alpha eff < 35% /
VIX > 30). DGS10 is DISCLOSURE ONLY -- level and delta, never a blocker
(retired 2026-07-30). Quote the doctrine's multiplier-stacking line ("MIN
across active states"), never a private recomputation. Any ACTIVE
shock/halt -> CRITICAL row with its throttle multiplier.

Phase C -- New alternative-data signals (every mode). Report
ref-alternative-data-signals rows dated AFTER the previous review note (or
after the ref's GENERATED date if none), HELD names first, watchlist second.
Respect the ref's own limitation labels (VOLADJ-10D-ZSCORE proxy, note-
sourced insider direction, 8-K = news clock not content). Each signal INFO
unless it touches a Phase A/B trigger (higher severity stands). Close with
a data-freshness line: store last-bar date, filings cutoff, GENERATED date.

Phase D -- Performance attribution (monthly). decision-attribution.md +
sector-attribution.md latest tables -> selection vs allocation contribution,
top contributors/detractors with dollars/pct and citations. Held-book
verdict grades since the last monthly note: direction hit rate, band
containment rate, SPY-relative delta where artifacts carry it. One paragraph
max synthesis; every number cites its artifact.

Phase E -- Doctrine compliance audit (monthly). Checklist against doctrine +
gates-registry compliance rows: concentration ambers/reds (theme-alpha
effective %, single-name %, interim 50% amber until 2026-09-08) vs current
weights (optimization ref Sec 1); GATE-F sheets since last monthly --
DISCIPLINED vs OVERRIDE counts, unratified drift; earnings-week protocol
adherence on any HELD binary print that occurred; reserve netted/released
state vs conditions; kernel sizing reconciliation flags in calibration
artifacts. Each row PASS / FAIL / N-A + citation. FAILs are findings, not
lectures -- route each to its owner (/gate calibrate, ADVISE, /decide).

Phase F -- Rebalancing needs + calibration update (monthly). Diff
optimization-ref recommendations vs its Sec 1 current weights; deltas above
its stated materiality labeled NEEDS-DECISION, routed to SIZE / ADVISE /
`/gate f` -- REVIEW proposes nothing, sizes nothing, never states an order.
Composite score changes (ref vs scores embedded in each holding's latest
wave analysis): moves across rating boundaries -> WARNING feeding Phase A.
Calibration engine update: run the weekly chain if stale (factor-store
ingest-bars -> backtest-offline -> calibration-report ->
confidence-calibrator) or verify this week's outputs exist; state headline
overstated/understated buckets + calibrated-vs-stated gap from
confidence-map.json; the note itself uses CALIBRATED values.

Phase G -- Strategy-level review (quarterly). Is the book's core
thesis WORKING -- evidence, not narrative: thesis pillars (capex guidance
trajectory,
memory/storage cycle position) GREEN/AMBER/RED with the two-three numbers
that set each + invalidation-trigger proximity; aggregate book evidence
(realized selection alpha vs benchmark over the quarter, quarter's verdict
win rate, whether concentration matched doctrine bands all quarter); VERDICT
line ON TRACK / UNDER STRAIN / INVALIDATION WATCH with the pre-committed
consequence of each, routed to `/challenge` if UNDER STRAIN or worse.

Phase H -- Scenario, hedge, and stale queue (quarterly). Scenario
probability updates vs `ref-scenario-stress-test.md`: adjusted ONLY via a
routed proposal (ADVISE), never silently -- the note records the proposal.
Hedge effectiveness per `ref-hedge-construction.md`: protection-per-dollar
vs its Section 6 ranking, carry accrued, whether the mapped systemic risk
grew or shrank ->
MAINTAIN / REPLACE-PROPOSAL / LET-EXPIRE routed to RISK + `/gate f`. Full
re-analysis queue: any HELD name whose latest analysis predates the quarter
boundary, has an expired hold_band, or carries NO-ANALYSIS -> ranked queue
(staleness x book weight), each row `/invest <TICKER>` with the specific
question the refresh must answer (carry forward unresolved kill criteria).

### Output note (exactly one per run)

Write `Calendar/decisions/reviews/review-<mode>-<YYYY-MM-DD>.md` with
canonical frontmatter (categories: [decisions], type: decision-log,
status: complete, created/updated ISO dates, tags topic/investing +
topic/meta, related wikilinks to inputs actually cited):

```
# Portfolio Review -- <MODE> -- YYYY-MM-DD

BLUF: <three lines max: breaches count, gate state, single most important item>

## 1. Hold-state audit        (per-position table: T | close | band | dist | class)
## 2. Gates + macro           (stacked multiplier + DGS10 disclosure line)
## 3. New signals             (dated rows + freshness line)
## 4. Attribution             (monthly+)
## 5. Doctrine audit          (monthly+, PASS/FAIL rows)
## 6. Rebalance + calibration (monthly+, NEEDS-DECISION rows)
## 7. Strategy verdict        (quarterly+)
## 8. Scenarios / hedges / re-analysis queue (quarterly+)
## Gaps                       (missing artifacts + regeneration commands)
## Routing                    (every CRITICAL/WARNING -> owning skill + sheet)
```

Omit mode-absent sections entirely (a weekly note has no sections 4-8). Sort
findings CRITICAL -> WARNING -> INFO everywhere; every number carries its
citation. Quiet-day rule: nothing fired in a phase -> write exactly
"nothing material to report" there, never filler. Ledger discipline: the
reviews/ note is a plain dated record (not a generated organ); append
nothing to sessions-log / decision-log -- /retro owns those. After writing,
report the note path + BLUF in chat.

# JOURNAL MODES (= former /journal)

Trade journal and performance attribution. Close the feedback loop between
actions and outcomes: every decision gets a structured record at entry time,
every review computes what actually happened, and recurring patterns harden
into lessons re-surfaced at the NEXT entry. Full entry template, controlled
vocabularies, and computation formulas: `ref-journal-format.md` (this
directory; read before first log or first review).

### Cage compliance (hard, binds all three journal modes)

- Writes EXACTLY two locations: `Calendar/journal/<YYYY-MM-DD>-<TICKER>.md`
  and `wiki/maintenance/calibration/journal-lessons.md`. Nothing else, ever.
- Never reads `.raw/`, `private/`, `finance/`, `credentials/`,
  `*.local.md`. Entries record STATED facts from the session (price, size,
  rationale as given). Broker-fill reconciliation is /retro Phase A.7 (X47p)
  business; never pull fills here to "check".
- ASCII only in composed bytes; entries are NEW `.md` under `Calendar/` so
  R6 canonical frontmatter applies (template satisfies it).
- Network: none in log/lessons. Review MAY fetch an unrealized mark via
  yfinance ONLY when the operator explicitly asks for open-position marks;
  otherwise open positions report `OPEN` and stay out of win-rate math.
- Idempotency: marker signature `(trade_date, ticker, action, first 40
  normalized chars of details)`; duplicate -> SKIP and say so.

## JOURNAL LOG (`/portfolio journal log <ticker> <action> [details]`)

Phase L.1 collect stated facts (never invent): ticker; action enum
BUY|SELL|TRIM|HOLD; trade_date (US Eastern calendar date of the TRADE,
default today); price; size (+unit share|usd|contract|unit); horizon
(intraday|swing|position|long-term); stated_confidence 0-100;
emotional_state (controlled vocabulary in ref); rationale (operator words,
compressed, <=3 sentences). HOLD takes price=NULL size=NULL (decision event,
not a position change). Missing price/size on BUY/SELL/TRIM: ask once; if
still unknown record NULL and flag the entry INCOMPLETE (excluded from
review math until completed by a later edit).

Phase L.2 doctrine-compliance check; mark PASS/FAIL/N-A with evidence
pointer (basename of decision sheet, /invest analysis, or `none`):
1. Trend filter: BUY/TRIM-add in established uptrend (or explicit
   counter-trend thesis on file).
2. R/R >= 3:1: stop and target defined pre-entry, ratio computed.
3. Sizing kernel: size within kernel cap for stated_confidence band.
4. Kill criteria: written invalidation condition in the plan.
5. Thesis challenge: thesis-changing adds stress-tested (/challenge or
   equivalent) within 30 days.
`doctrine_compliant`: `pass` (all applied gates PASS), `fail` (>=1 FAIL),
`partial` (any gate skipped-without-evidence). Any FAIL requires an
`override:` note recording WHY the trade proceeded anyway -- absent
override, HALT the log and surface the question. Gates and N-A rules: ref.

Phase L.3 calibrated confidence (advisory): if
`tools/calibrate-confidence.py` accepts the stated value, record its output
as `calibrated_confidence`; rc=3 (stale/absent map) -> NULL plus comment
`uncalibrated`. Never alters the stated number.

Phase L.4 write the entry at `Calendar/journal/<YYYY-MM-DD>-<TICKER>.md`:
file absent -> create from the canonical template (frontmatter + `# Journal`
+ first `## Entry` block) verbatim, filling stated facts; file exists (same
ticker, same day) -> APPEND a new `## Entry N -- <ACTION> <HH:MM>` block,
bump frontmatter `updated:`, touch nothing else (strictly additive); fill
the Outcome section of PRIOR open entries on the same ticker when this
action closes/reduces them (set `status`, `realized_pct`, `resolved_by`
pointing at this entry). Completion criterion: YAML parses; entry contains
every required field (ref checklist); zero unresolved wikilinks; ASCII clean.

Phase L.5 lessons reminder (feedback closure): read
`wiki/maintenance/calibration/journal-lessons.md`; print any ACTIVE lesson
whose trigger matches this entry's shape (same emotional_state, same gate
previously failed, same setup class). Skipping this step reduces the journal
to a diary. No ACTIVE section -> print `no active lessons` and continue
(never fabricate).

## JOURNAL REVIEW (`/portfolio journal review <period>`)

Period grammar: `7d`, `30d`, `90d`, `YYYY-MM`, or
`YYYY-MM-DD..YYYY-MM-DD`. Default `30d`.

Phase R.1 enumerate `Calendar/journal/*.md` (files target matching the
period filter); parse frontmatter + entry blocks; drop INCOMPLETE entries
from math (report count). Phase R.2 resolve outcomes: (a) entry
Outcome.status CLOSED-* -> use realized_pct; (b) unclosed BUY lots with a
later SELL/TRIM outside the window -> still OPEN; (c) optional yfinance mark
only per Cage rules. Lot matching FIFO per ticker (TRIM weighting: ref).
Phase R.3 compute (formulas in ref-journal-format.md): win rate over CLOSED
trades; avg gain, avg loss, expectancy, profit factor; best/worst closed
trade (pct + ticker + date + emotional_state + compliance flag each);
doctrine compliance rate pass/(pass+fail) with `partial` counted
non-compliant in the headline and reported separately; emotion-outcome
correlation per emotional_state (n, win rate, mean pct; flag n>=3 deviating
>15pt from overall) plus hot-vs-cool rollup (bucket membership: ref);
confidence cross-tab stated-decile bands vs realized win rate labeled
`ADVISORY input for confidence-map rebuild`; sample-size honesty -- any cell
n<3 prints `n<3 -- anecdotal`. Phase R.4 emit ONE markdown block to screen:
period, entries scanned, closed/open/incomplete counts, the five
computations, three most actionable single-line takeaways. Review WRITES
NOTHING (screen-only mode).

## JOURNAL LESSONS (`/portfolio journal lessons [--since <date>]`)

Phase P.1 scan all entries (default) or since `--since` (reuse R.1-R.2
parsing; do not re-implement). Phase P.2 extract candidates: process lesson
(repeated sequencing/planning fault), emotional lesson (state repeatedly
preceding losses), doctrine-gap signal (same gate failing >=3 times -- the
gate itself may be wrong or ignored), calibration delta (stated band
materially misranked vs realized). Promotion threshold >=3 supporting
entries across >=2 tickers, except doctrine-gap+loss pairs which promote at
>=2. Contradicted-by-newer patterns demoted to `Superseded`, never deleted.
Phase P.3 persist: append one dated section to
`wiki/maintenance/calibration/journal-lessons.md` (sections `## Active
lessons`, `## Superseded`, `## Calibration deltas`); strictly additive; bump
`updated:`; `Related:` line points at existing basenames only. The file sits
in the calibration lane beside `confidence-map.json` and
`decision-attribution.md` so the weekly calibration job and /invest
Phases R.8/R.9 consumers find it by location. Phase P.4 route (loop closes
here): emotional/process lessons -> become Phase L.5 reminders (automatic
next log); doctrine-gap signals -> ONE follow-up tagged `/decide candidate`;
doctrine constants change only via /decide, never inline edits;
calibration deltas left in-place for the weekly lane -- NEVER rewrite
`confidence-map.json` directly (generator-owned organ). Completion
criterion: every promoted pattern appears in exactly one section, cites its
supporting entry dates, names its routing target.

### Journal pitfalls and quality rules

- Same-day re-entry on one ticker: append blocks; scalars (trade facts)
  live in blocks, frontmatter carries only latest action + updated.
- TRIMs are partial closes: realized_pct is size-weighted across the lot,
  never "price delta since last entry".
- SELL with no matching open lot: valid entry, flagged UNMATCHED in review
  (short sale or bookkeeping drift -- surface, do not silently net).
- Entries are statements made at decision time. Editing old rationale after
  outcomes are known is falsification; corrections go in a NEW block citing
  what changed.
- Calibrated confidence and calibration deltas inform prose only; never
  alter kernel constants, sizing inputs, or ratings.

### Journal verification

After any journal mode: (1) target file exists and
`python -c "import yaml;yaml.safe_load(open('<file>').read().split('---')[1])"`
parses; (2) log: entry block contains all required fields per the ref
checklist and prior blocks are byte-identical; (3) review: closed+n counts
reconcile against entries scanned; (4) lessons: new section cites
>= threshold entries and the file still ends with the canonical Related
line; (5) checkall stays ALL GREEN.

---

# Cross-mode integration

- `/invest`: sole writer of analysis artifacts; consumes the same
  factors.db + calibration outputs. RISK exposure precedes /invest for
  sizing context. JOURNAL never substitutes for /invest.
- `/networth`: owns current-session broker reconciliation; only its current
  read evidence can establish quantities for this run. Saved snapshots remain
  historical and cannot replace missing coverage.
- `/gate f`: RISK/SIZE/JOURNAL output is admissible INPUT evidence;
  verdicts come only from tools/gate-eval.py.
- `/brief`: daily situational narrative; ADVISE is the deeper periodic memo.
- `/decide`: formal records for ratification; REVIEW/SIZE route here.
- `/retro`: execution review; owns broker-fill reconciliation (A.7/X47p).
- Weekly calibration loop (SUN 07:30): ingest-bars -> ref regeneration ->
  every mode self-updates on its next run; refs older than the latest
  ingest get flagged.

# Skill-level verification

- Strict YAML parse of this frontmatter;
  `python skeleton/eval/eval-skill-overlay.py --check` exits 0;
  `agentskills validate` passes.
- Non-ASCII scan of everything this skill writes: zero hits.
- Dry-run each mode end-to-end against the live vault before trusting it;
  `python .agents/scripts/checkall.py` ALL GREEN after any canon edit.

# ref-gate-tables -- human mirror of tools/gate-rules.json (JSON is AUTHORITATIVE)

Canonical reference for the three judgment gates. Consumed by /gate; not a
market-linked report. On any conflict with `tools/gate-rules.json`, the JSON wins
and this file must be re-synced. Worked exemplars: the `golden: true` sheets in
`wiki/research/gates/` -- imitate them field-for-field.

## Why this exists (design intent, 2026-07-06, Fable 5 final session)

Weaker models execute well and design poorly. Each gate moves one remaining
runtime judgment into static structure:

- GATE-F: "is this proposed trade disciplined or FOMO/panic?" -- upstream of the
  T11 pretrade staircase. Division of labor: `pretrade_gate.py` gates EXECUTION
  (doctrine ceilings, R/R >= 3:1, the 2026-04-15 sleep-gate); /invest Phase Q
  gates ANALYSIS numbers; GATE-F gates the GENERATION PROCESS (behavioral/
  temporal markers only). GATE-F never rechecks ceilings, R/R, or sleep state.
  /invest R.4 (SINGLE-NAME-BUY tripwire) is a separate, non-overlapping guard.
- GATE-T: "did this manual/evidence trigger actually fire?" -- numeric triggers
  are /brief Phase H territory (mechanical); GATE-T covers ONLY `source: manual`
  and earnings_window evidence triggers, the ones needing interpretation.
- GATE-B: "build this, or ship the pending action?" -- the least-encoded failure
  mode (utilization ~5/10 vs architecture ~9.5/10). Feeds the EOD ledger and the
  30-day BUILD-gate consumption doctrine; duplicates neither.

The model NEVER decides a verdict. Fill markers -> `gate-eval.py --compute` ->
transcribe -> `--check`. Adjusting markers to steer a verdict is the exact
failure mode this kit exists to stop; a surprising verdict means wrong markers
or a wrong table -- surface it, never steer it.

## Sheet skeleton (all modes)

```yaml
---
aliases: []
categories: [wiki]
type: report
tags: [topic/judgment-gates]
status: complete
created: YYYY-MM-DD
updated: YYYY-MM-DD
related: ["[[gates-registry]]", "[[<entity-or-thesis-stem>]]"]
gate:
  schema_version: 1
  mode: f            # f | t | b
  ticker: NVDA       # f-mode only, UPPERCASE
  subject: "<one-line subject>"
  golden: false
  markers:
    <name>: {value: <typed>, prov: "<vault path or scheme:>"}
  verdict: <VERBATIM from --compute>
  mandates: [<VERBATIM from --compute>]
  review_date: <suggested_review_date from --compute, or null>
  outcome: null      # later: VINDICATED | WRONG | OVERRIDDEN | n/a
---
# GATE-<MODE>: <subject>
## Evidence
<prose behind each marker, cited path:line or [Grade X|source|date]>
## Verdict + mandates
<restated; user overrides recorded here with reason -- markers never edited>
```

Provenance: vault-relative path (checked on disk) or scheme prov `mcp:*`,
`script:*`, `web:*`, `manual:*`, `test:*`. No dollar values / share counts /
position sizes anywhere on a sheet -- fractions and percentages only.

## GATE-F -- trade-generation discipline

Subject: one proposed ADD / TRIM / EXIT on one instrument.

| marker | type | fill-rule (deterministic) |
|---|---|---|
| action_side | ADD\|TRIM\|EXIT | the proposal's action |
| tenure_days | int | days since `wiki/entities/tickers/<T>.md` frontmatter `created:`; 0 if no entity note |
| held_position | bool | entity `accounts:` list non-empty |
| catalyst_age_hours | int | hours since the NEWEST dated event cited in the proposal's own rationale (newest = most FOMO-flagging, adversarially conservative) |
| prior_analysis_days | int\|null | days since latest `wiki/investing/analyses/<t>-analysis-*.md`; null if none; an in-flight full /invest run counts as 0 |
| thesis_member | bool | entity `thesis:` list non-empty (CONTEXT ONLY in v1 -- recorded, not scored) |
| regime_alert | bool | latest briefing meta.json `indices_snapshot`: VIX >= 20 OR term_structure == backwardation |
| move_5d_pct | number | abs % move over last 5 regular sessions, regular-close anchored; prov mcp:* > script:* |
| trades_7d | int | prior gate-f sheets (verdict != BLOCKED) trailing 7d + EOD rows flipped EXECUTED with a trade action in-window |
| after_hours_origination | bool | proposal's pricing/urgency rests on extended-hours quotes rather than regular-close-anchored data; an evening run anchored to the regular close is FALSE |
| trigger_backed | bool | a FIRED GATE-T sheet exists whose trigger action covers this instrument |
| zone_preregistered | bool (OPTIONAL) | the latest analysis frontmatter carries a `watch_zone` set >= 14d ago, bounds UNCHANGED since `set_on` (zone_prior comparison or a single unmoved block), and price entered the zone FROM ABOVE (prior regular close > high, current regular close inside [low, high]); prov = the analysis path |

`zone_preregistered` is the one OPTIONAL marker: absent == false, so every sheet
written before 2026-07-30 still validates under schema_version 1 (no re-issue).

fomo_points (0-7) = count of: catalyst_age_hours < 48; (NOT held_position AND
tenure_days < 14); (prior_analysis_days null OR > 30); regime_alert;
move_5d_pct >= 10; after_hours_origination; trades_7d >= 3.

Verdict (ordered, first match):
1. trigger_backed AND action in {TRIM, EXIT} -> DISCIPLINED (trigger-driven exits
   are the system working -- never impede them).
1b. zone_preregistered AND action == ADD -> DISCIPLINED (a pre-registered zone
   firing is the plan working, not FOMO -- buy-side parity with rule 1; it
   short-circuits BEFORE fomo_points scoring, so a converted watch-zone entry is
   never re-blocked by the catalyst/move/trades points its own firing created).
2. fomo_points >= 4 OR (tenure point fires AND prior_analysis_days null AND
   catalyst_age_hours < 24) -> BLOCKED.
3. fomo_points 2-3 -> FOMO-SUSPECT.
4. else DISCIPLINED.

Mandates: FOMO-SUSPECT -> cooling-off-48h + eod-row-regate (+2d) +
tranche-cap-25pct-on-regate. BLOCKED -> no-recommendation +
invest-and-challenge-required + regate-min-5td. DISCIPLINED -> none.

## GATE-T -- trigger-fired adjudication (manual/evidence triggers ONLY)

Subject: one trigger_id where `source: manual` or `window: earnings_window`.
Numeric operator/threshold triggers -> /brief Phase H, NOT here.

| marker | type | fill-rule |
|---|---|---|
| trigger_id | str | must exist in the thesis file's `triggers:` block |
| thesis | str | thesis file stem |
| tier | kill\|red\|amber\|manual | from the block |
| evidence | list | items {source, grade A-D, date, statement}; grade per the 8.6 rules with freshness downgrades |
| metric_condition_met | bool | numeric restatement of the condition vs evidence (restatement goes in the body) |
| window_ok | bool | counted evidence dates inside the trigger's `window` |
| consecutive_required | int\|null | the trigger's counter requirement; null if none |
| consecutive_count | int\|null | observed count; null if none |

Verdict (ordered): 1. < 2 grade-A|B items from 2+ distinct sources ->
INSUFFICIENT-EVIDENCE. 2. condition met AND window ok AND counter satisfied ->
FIRED. 3. else NOT-FIRED.

Mandates: FIRED -> status-floor-`<tier>` (via the existing /brief Pattern-20
`fired:` write-back; this sheet is the evidence record) + eod-row-trigger-action
(+3d). INSUFFICIENT -> eod-row-evidence-collection (+3d). NOT-FIRED -> none
(the sheet prevents re-litigating the same evidence daily).

## GATE-B -- build-vs-ship

Subject: any proposal to create new runtime/tooling artifacts.

| marker | type | fill-rule |
|---|---|---|
| closes_eod_id | str\|null | execute-or-decline.md row this build closes |
| overdue_eod_count | int | PENDING rows past ESCALATION_DATE, as of today |
| user_directive | bool | user explicitly requested this build in their own words this session |
| similar_organ | path\|null | nearest existing artifact serving the same function |
| similar_organ_consumed_30d | bool\|null | reads/invocations of it in last 30d; null when similar_organ null |
| size_class | S\|M\|L | est. new lines < 50 / 50-200 / > 200 |
| deadline_bound | bool | tied to an Efforts/`<slug>` deadline |

Verdict (ordered): 1. similar_organ set AND unconsumed-30d -> DECLINE (no v2 of
an unused organ). 2. user_directive -> BUILD-JUSTIFIED (user overrules; sheet
makes displaced work visible). 3. no closes_eod_id AND overdue_eod_count >= 1 ->
SHIP-FIRST. 4. else BUILD-JUSTIFIED.

Mandates: SHIP-FIRST -> resolve-top-overdue-eod-first + regate-after.
BUILD-JUSTIFIED + size L -> consumption-review-30d (review_date +30; no
consumption evidence by then = archive candidate). BUILD-JUSTIFIED +
overdue_eod_count >= 1 -> list-displaced-eod-rows (visibility, not blockage).

## Binding points (where the gates fire automatically)

| Gate | Bound in | Failing verdict blocks/mandates |
|---|---|---|
| F | /invest Phase Q.6 + HALT 10a | BLOCKED halts the analysis pre-write; FOMO-SUSPECT publishes with cooling-off in the Decision Sheet |
| F | /decide pre-mortem prerequisite | same, pre-ratification |
| T | /brief Phase H + HALT 22a | manual-trigger status change without a sheet halts the briefing |
| B | /create-skill Step 0 | non-BUILD-JUSTIFIED -> no scaffold |
| B | /retro detective check | new runtime files without an in-window GATE-B sheet -> retro halts until backfilled |

Residual (accepted): ad-hoc mid-session builds that never reach /retro evade the
detective check; `gate-eval.py --calibrate` catches them after the fact via git.

## Per-gate pre-write checklist (assert before writing any sheet)

1. Subject resolves to one concrete instrument / trigger-id / proposal.
2. Every marker present as {value, prov}; vault-path provs exist on disk.
3. Verdict + mandates + review_date transcribed VERBATIM from --compute.
4. --check exits 0.
5. related: carries *gates-registry* (not published) + the touched entity/thesis.
6. Registry row appended; mandated EOD rows appended.
7. ASCII clean; no dollar values / share counts / position sizes.

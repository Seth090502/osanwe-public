---
aliases: [portfolio-doctrine, doctrine, doctrine-template]
categories: [concepts]
type: playbook
tags:
  - topic/doctrine
  - topic/risk-management
  - topic/thesis-tracking
status: active
created: 2026-06-11
updated: 2026-06-11
related: ["[[investing-moc]]", "[[thesis-orbital-compute]]", "[[analysis-depth-standard]]", "[[knowledge-moc]]"]
---

# Portfolio Doctrine -- TEMPLATE

> **This is a template.** Every `USER_SET` value below is a personal risk
> decision only you can make. Copy this file to `doctrine.md` (or edit in
> place), replace each `USER_SET[...]` with your ratified value, and record
> the ratification in your decision log. The skills (`/invest`, `/networth`,
> `/brief`, `/challenge`, `/decide`) read the named placeholders below --
> `THESIS_CAP_AMBER`, `THESIS_CAP_RED`, `SINGLE_NAME_AMBER`,
> `SINGLE_NAME_RED`, `OTHER_THESIS_FLAG`, `RR_HURDLE` -- as your doctrine
> values once set.
>
> Nothing in this file is investment advice. It is a *decision-discipline
> scaffold*: it makes concentration and risk decisions conscious instead of
> accidental.

## Trigger Conditions

Load this document when:
- Any question about thesis health, invalidation, or challenge status
- Any portfolio-impact question involving multiple holdings moving together
- Any earnings-week question about a held position
- Any concentration-risk or portfolio-weight question
- Any monthly review or periodic portfolio assessment

---

## 1. Thesis Registry

Maintain active awareness of your core investment theses. Every market event,
earnings report, or news item gets mapped against the relevant thesis. Each
thesis is a separate essay at `Atlas/concepts/investing/theses/thesis-<slug>.md`
(authoring template: `_templates/thesis.md`; worked example:
[[thesis-orbital-compute]] -- a deliberately fictional demo).

Each thesis essay defines:
- **Holdings** mapped to the thesis (a ticker may serve multiple theses)
- **Thesis statement** (2-3 sentences, falsifiable)
- **Key metrics to track** (leading indicators, named data sources)
- **Invalidation trigger** (the specific, observable condition that breaks it)

### Thesis Health Dashboard (weekly review)

```
THESIS SCOREBOARD:
1. <thesis-slug-1>:  [X/10] -- [one sentence status]
2. <thesis-slug-2>:  [X/10] -- [one sentence status]
...
N. <core-allocation>: [structural, no rating needed]
```

---

## 2. Concentration Doctrine

Tiered and thesis-specific. The rule makes concentration CONSCIOUS, not
automatic; a flag is never an automatic sell trigger.

### Primary-thesis cap (your highest-conviction thesis)

- **THESIS_CAP_AMBER = USER_SET[percent, e.g. 40-60%]** -- when the primary
  thesis exceeds this share of combined portfolio value: flag in the weekly
  review; conscious monitor; optional phase-in window with a lower interim
  amber while a structural change settles.
- **THESIS_CAP_RED = USER_SET[percent, > amber]** -- hard ceiling. Initiate a
  managed trim back under the ceiling via the exit ladder (Section 3). Not an
  automatic same-day sell -- a managed reduction.

### Other-thesis flag

- **OTHER_THESIS_FLAG = USER_SET[percent, e.g. 40%]** -- when any non-primary
  thesis exceeds this share, flag it in the weekly review.

### Single-name ceiling (applies across ALL theses and ALL accounts combined)

- **SINGLE_NAME_AMBER = USER_SET[percent, e.g. 25-30%]** -- flag; no new adds
  to that name until reviewed.
- **SINGLE_NAME_RED = USER_SET[percent, > amber]** -- escalate to `/decide`
  immediately. Two sanctioned options: (a) grandfather-no-adds (hold, no
  further purchases, organic drift compresses the weight); (b) trim to under
  the amber. A silent pass is not permitted; a `/decide` record is required.

Rationale: a thesis ceiling with no single-name ceiling is concentration
deferred, not managed. A large thesis bet must spread across 3+ names; no
single stock is the book.

### Measurement anchoring

Concentration math + trim-trigger evaluation anchor to **regular-market-close
prices**, never extended-hours prints (extended-hours liquidity is thin and
gap-fill dynamics are common). Extended-hours valuations may be *reported* in
snapshots but never *trigger* doctrine thresholds.

---

## 3. Exit Ladder (primary thesis -> core allocation)

Define the rotation destination first: **EXIT_DESTINATION = USER_SET[ticker,
e.g. a total-market index fund]** -- it must actually de-risk (a
sector-concentrated fund does not). Prefer routing rotation through
tax-advantaged accounts where feasible. Rotation begins when ANY leg fires;
accelerate when 2+ fire.

**OFFENSIVE -- thesis MATURED (the harvest case):**
- **Leg A (supply/demand normalization):** USER_SET[two co-required observable
  conditions that mark the cycle normalizing, e.g. "aggregate sector capex YoY
  guidance decelerates AND key-component lead times normalize"]. Deceleration
  (positive, slowing) is categorically different from cuts (negative).
- **Leg B (monetization-doubt / capability-plateau):** USER_SET[a sustained
  narrative-flip condition, e.g. "cohort-wide multiple de-rate across two
  earnings cycles not explained by rising real rates"]. A single-quarter
  de-rate does NOT trigger Leg B.
- **Leg C (calendar backstop):** USER_SET[date + cadence, e.g. "from CY20XX, a
  6-month glide-path review regardless of A/B"].

**DEFENSIVE -- thesis BREAKING (cuts, not deceleration). Graduated escalation
by BREADTH (how many bellwethers) and DURATION (how many quarters), measured
on forward guidance unless "actual" is stated:**
- 1 bellwether cuts guidance = Amber Signal (monitor; note in `/brief`).
- USER_SET[breadth threshold, e.g. "2 of 4"] cut in a single quarter =
  heightened monitor + briefing Warning Problems pre-arm.
- USER_SET[escalation threshold, e.g. "3 of 4"] cut in a single quarter =
  AMBER escalation: arm the ladder + trigger a `/decide` review.
- USER_SET[duration threshold, e.g. "2 consecutive quarters of guidance cuts"]
  = thesis-health INVALIDATED + MANDATORY `/decide` review (hold / reduce /
  exit on the table).
- USER_SET[structural criterion, e.g. "4 consecutive quarters of ACTUAL
  aggregate declines (reported spend, not guidance)"] = STRUCTURAL
  INVALIDATION -> defensive auto-revert (below).

Design principle worth keeping even if you change every number: the MECHANICAL
auto-revert requires a harder ACTUAL-DATA bar than the review triggers. A
large book is never auto-de-risked on guidance alone -- guidance-based rungs
compel a `/decide` review, never the automatic rotation. Guidance-cut counters
RESET on any quarter of raise/hold; the structural counter independently
tracks actuals.

### Thesis-Health Auto-Revert

If the STRUCTURAL tier fires, the applicable ceiling reverts to
**AUTO_REVERT_CEILING = USER_SET[percent, < THESIS_CAP_AMBER]** (a hard stop)
via a MANAGED rotation to EXIT_DESTINATION -- not a same-day liquidation.
Reduce weakest-thesis-fit first; complete within USER_SET[window, e.g. 60-90
days] unless faster action is explicitly ratified.

### Sleep-Gate

**SLEEP_GATE_THRESHOLD = USER_SET[percent of book, e.g. 50%]** -- any add made
while the primary thesis is at or above this share retains the sleep-gate: a
deliberate overnight pause between deciding the order and executing it.
Define your own exemption band (e.g., routine adds inside an explicitly
ratified conviction band) and the level below which no sleep-gate applies.

---

## 4. Risk/Reward Gate

**RR_HURDLE = USER_SET[ratio, default 3:1]** -- `/invest` Phase H computes
downside-to-stop vs upside-to-target on every BUY-side recommendation; a
candidate below the hurdle cannot carry a BUY/STRONG BUY rating regardless of
narrative quality. Set the stop-distance convention (technical stop vs thesis
stop) when you ratify the hurdle.

---

## 5. Thesis Invalidation Early Warning

Traffic-light system per thesis:
- **GREEN:** all indicators confirm. No action.
- **AMBER:** 1-2 warning signs. Increase monitoring; note in briefing.
- **RED:** multiple invalidation conditions met. Immediate review: hold,
  reduce, or exit -- decided by you, recorded via `/decide`.

Per thesis, enumerate 3-5 amber signals (leading indicators) in the thesis
essay. When amber fires, the briefing carries a running status line:
"THESIS WATCH: <thesis> showing N amber signal(s) (<detail>). Invalidation:
<trigger>. Current status: X of Y."

---

## 6. Thesis-Level Move Detection

When 3+ positions within one thesis move 2%+ the same direction the same day,
that is a THESIS-LEVEL EVENT, not individual stock news:

```
THESIS SIGNAL: <thesis> under pressure
  <T1> -X.X% | <T2> -X.X% | <T3> -X.X%
  Catalyst: [identified cause or "sector rotation, no specific catalyst"]
  Portfolio impact: ~$XX across N positions
  Thesis assessment: [CONFIRMS/CHALLENGES/NOISE]
```

Always look for correlation before reporting individual alerts.

---

## 7. Peer Constellation Monitoring

Watch adjacent peers as leading indicators for held positions: before a held
name reports, watch its closest competitor's print; a regulatory action on ANY
asset in a class shifts the landscape for the whole class. Note peer events as
context with the days-to-earnings countdown for the held name.

---

## 8. Risk Cascade Awareness

For each major holding, pre-estimate the ripple effect of a -15% crash
scenario across correlated positions (sympathy moves, indirect ETF exposure,
sector pressure) so total exposure context is immediate, not recomputed in the
moment.

---

## 9. Earnings Season Protocol

Heightened monitoring when a held position is within 10 trading days of
reporting: pre-earnings consensus capture (10d), daily countdown + revision
trends + implied move (5d), earnings-day before/after sequence, and a 3-day
post-earnings revision-wave watch. Track recurring per-name patterns (e.g., a
beat-and-drop habit) in the entity note, and update thesis assessment after
every print.

---

## 10. Monthly Portfolio Review Template

Last Sunday of every month:
1. Portfolio snapshot -- combined value, MTD/YTD in $ and %
2. Thesis scoreboard vs last month
3. Best and worst 3 with catalysts
4. Concentration analysis vs Section 2 caps
5. Realized P&L
6. Unrealized P&L extremes
7. Tax-advantaged account status (deployed vs cash)
8. Action-zone check vs latest `/invest` reports
9. Ref-doc health audit
10. Forward calendar
11. Open questions needing the user's decision

---

## Ratification log

| Date | Placeholder | Value set | Decision record |
|---|---|---|---|
| USER_SET | THESIS_CAP_AMBER | -- | `decision-...` |
| USER_SET | THESIS_CAP_RED | -- | `decision-...` |
| USER_SET | SINGLE_NAME_AMBER / RED | -- | `decision-...` |
| USER_SET | OTHER_THESIS_FLAG | -- | `decision-...` |
| USER_SET | RR_HURDLE | -- | `decision-...` |
| USER_SET | SLEEP_GATE_THRESHOLD | -- | `decision-...` |
| USER_SET | AUTO_REVERT_CEILING | -- | `decision-...` |
| USER_SET | EXIT_DESTINATION | -- | `decision-...` |

# Example 3 -- a thesis trigger sheet

> As of 2026-09-20. Published as an example of the system's output.
> Not investment advice, not a recommendation, and not a statement of anyone's positions.

How a thesis change is decided: the trigger, the evidence required, and the verdict, recorded so a later reader can tell what would have changed the answer.

---

<details>
<summary>Metadata the system recorded for this run</summary>

```yaml
aliases: []
categories: [wiki]
type: report
tags: [topic/judgment-gates, thesis/theme-alpha]
status: complete
created: 2026-07-06
updated: 2026-07-06
related:
  - "[[gates-registry]]"
  - "[[thesis-theme-alpha]]"
gate:
  schema_version: 1
  mode: t
  subject: "thesis-theme-alpha / themealpha-amber-capex-guide-down (adjudicated 2026-07-06)"
  golden: true
  markers:
    trigger_id: {value: themealpha-amber-capex-guide-down, prov: "Atlas/concepts/investing/theses/thesis-theme-alpha.md"}
    thesis: {value: thesis-theme-alpha, prov: "Atlas/concepts/investing/theses/thesis-theme-alpha.md"}
    tier: {value: amber, prov: "Atlas/concepts/investing/theses/thesis-theme-alpha.md"}
    evidence:
      value:
        - {source: "MSFT Q3 FY26 earnings (2026-04-29 print)", grade: B, date: "2026-04-30", statement: "FY26 capex revised UP to $190B incl. $25B component-pricing inflation -- guidance direction UP, not down"}
        - {source: "META Q1 CY26 earnings (2026-04-29 print)", grade: B, date: "2026-04-30", statement: "FY26 capex RAISED $115-135B -> $125-145B -- guidance direction UP, not down"}
      prov: "Calendar/decisions/decision-log.md"
    metric_condition_met: {value: false, prov: "Calendar/decisions/decision-log.md"}
    window_ok: {value: true, prov: "Atlas/concepts/investing/theses/thesis-theme-alpha.md"}
    consecutive_required: {value: null, prov: "Atlas/concepts/investing/theses/thesis-theme-alpha.md"}
    consecutive_count: {value: null, prov: "Atlas/concepts/investing/theses/thesis-theme-alpha.md"}
  verdict: NOT-FIRED
  mandates: []
  review_date: null
  outcome: VINDICATED
```

</details>


# GATE-T: themealpha-amber-capex-guide-down (adjudicated 2026-07-06, retrospective golden)

GOLDEN EXEMPLAR (built by Fable 5, 2026-07-06). Demonstrates the SILENT case: a
manual/evidence trigger adjudicated with sufficient evidence and found NOT-FIRED,
so the same evidence never gets re-litigated narratively. Numeric triggers (e.g.
the price-close kill trigger) are /brief Phase H territory and never come here.

## Evidence

- Trigger (Atlas/concepts/investing/theses/thesis-theme-alpha.md, triggers block):
  `themealpha-amber-capex-guide-down` -- metric
  `hyperscalers_guiding_capex_down_sequentially`, operator `>=`, threshold 2,
  window `earnings_window`, source `manual`, tier amber. The threshold-2 is a
  COUNT of hyperscalers within one earnings window, not a consecutive-quarters
  counter -> consecutive_required = null; the count lives inside
  metric_condition_met's restatement below.
- Numeric restatement: hyperscalers guiding capex DOWN sequentially in the most
  recent completed earnings window (Q1 CY26 / Q3 FY26, reported late April 2026)
  = 0 of 4. MSFT revised FY26 capex UP to $190B; META RAISED FY26 capex to
  $125-145B (both: Calendar/decisions/decision-log.md, 2026-04-30 entries citing
  the Apr 29 prints). 0 < 2 -> metric_condition_met = false.
- window_ok = true: both evidence items sit inside the most recent completed
  earnings window for the cohort; the next adjudication point is the Q2 CY26
  print cycle (late July 2026).
- Evidence sufficiency: 2 items, both grade B (primary prints relayed through
  the vault's dated decision-log record; one freshness letter-downgrade from A),
  2 distinct sources -> clears the 2-item / 2-source floor, so this is a
  NOT-FIRED with sufficient evidence, not an INSUFFICIENT-EVIDENCE.

## Verdict + mandates

Rule 1 does not fire (evidence sufficient); rule 2 requires metric_condition_met
-- false -> NOT-FIRED (rule 3). No mandates; no status floor touched. Verdict
computed by tools/gate-eval.py --compute and transcribed verbatim.

Retrospective outcome = VINDICATED: through 2026-07-06 the theme-alpha thesis board
never warranted a capex-driven WATCH floor -- hyperscaler capex guidance kept
rising (the 2026-06-08 concentration-doctrine decision record treats rising
cohort capex as the operative regime). A FIRED call here would have been wrong.

Re-adjudicate this trigger after the Q2 CY26 hyperscaler prints (late July
2026): a fresh GATE-T sheet per earnings window, never an edit to this one.

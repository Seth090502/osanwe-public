---
categories:
  - moc
created: 2026-04-05
updated: 2026-06-11
status: active
tags: []
aliases: ["investing index"]
related:
  - "[[knowledge-moc]]"
  - "[[doctrine.template]]"
  - "[[thesis-orbital-compute]]"
---

# Investing Index
Last updated: 2026-06-11

## Doctrine + theses (human layer)
- [[doctrine.template]] -- concentration ceilings, exit ladder, R/R gate,
  sleep-gate; fill the USER_SET values and ratify via /decide
- [[thesis-orbital-compute]] -- DEMO thesis essay (fictional); author yours
  from `_templates/thesis.md` into `Atlas/concepts/investing/theses/`

## Entity graph (agent layer, wiki/)
- [[ORBC-DEMO]] -- demo ticker entity (Compute layer)
- [[LNCH-DEMO]] -- demo ticker entity (Lift layer)
- [[OPTL-DEMO]] -- demo ticker entity (Interconnect layer)

## Analyses (agent layer, wiki/investing/)
- [[ORBC-DEMO-analysis-2026-06-11]] -- demo /invest output
- [[calibration-monitor]] -- /invest Phase R call log + rolling Brier scoring

## Views
- `wiki/meta/dashboard.base`, `wiki/meta/analyses-by-ticker.base`,
  `wiki/meta/analyses-by-thesis.base` -- Bases views over the analysis corpus

## Workflow
`/invest <ticker>` -> analysis file + entity update + calibration row;
`/networth` -> snapshot; `/challenge` -> thesis stress test; `/brief` ->
morning briefing with thesis status board. Doctrine math reads
[[doctrine.template]] placeholders.

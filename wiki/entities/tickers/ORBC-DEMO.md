---
categories:
  - entity
type: ticker
created: 2026-06-11
updated: 2026-06-11
status: active
tags:
  - ticker/ORBC-DEMO
  - thesis/orbital-compute
aliases: [Orbital Compute Corp]
related:
  - "[[thesis-orbital-compute]]"
  - "[[investing-moc]]"
  - "[[ORBC-DEMO-analysis-2026-06-11]]"
---

# ORBC-DEMO

> **DEMO ENTITY.** Fictional ticker illustrating the agent-maintained entity
> pattern. All figures synthetic.

## Overview

Fictional orbital data-center capacity operator. Anchor holding of the
[[thesis-orbital-compute]] demo thesis (Compute layer).

## Financial signals

- Revenue (TTM, synthetic): $1.2B, +38% YoY [prov: demo-seed | 2026-06-11]
- Gross margin (synthetic): 41%, trending +200bps/yr [prov: demo-seed | 2026-06-11]

## Thesis Fit

- Owns 60% of announced on-orbit MW-equivalent capacity in the demo model
  [prov: demo-seed | 2026-06-11]

## Risks

- Radiation-hardening cost premium (synthetic 2.1x terrestrial) compresses
  margin if the cost curve stalls [prov: demo-seed | 2026-06-11]

## Catalysts

- Synthetic Q3 capacity announcement window [prov: demo-seed | 2026-06-11]

## Recent

- 2026-06-11: Demo entity seeded with the public v2 scaffold.

## Analyses
```base
filters:
  - file.inFolder("wiki/investing/analyses")
  - file.tags.contains("ticker/ORBC-DEMO")
  - type == "analysis"
views:
  - type: table
    name: analyses
    order: [file.name, confidence, updated]
    sort:
      - column: updated
        direction: DESC
```

## Key Catalysts

See Catalysts above (demo).

## Notes
> Quick observations, linked from daily notes

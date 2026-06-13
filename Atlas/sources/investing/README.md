---
categories: [sources]
type: reference
status: active
created: 2026-06-13
updated: 2026-06-13
tags: []
aliases: []
related: []
---

# Investing reference docs (user-authored)

The analytical skills (`/invest`, `/brief`, `/networth`, `/deep`, `/ingest`,
`/enrich`) reference a set of investing reference documents that live in this
directory: scoring models, investor frameworks, macro landscape, monitoring
rules, market calendar, geopolitical framework, sector benchmarks, portfolio
doctrine, research insights, valuation methodology, earnings playbook, factor
lens, and per-thesis deep dives.

These are **intentionally not shipped.** They encode the operator's own
methodology and judgment, and this framework is meant to run on yours. The
skills **degrade gracefully** when a ref is absent: they fall back to the
model's general knowledge and emit a non-fatal note, so the repo is functional
out of the box. The refs make the analysis sharper and house-style-consistent
once you author them.

Build your own with `/deep` (composes a Deep Research prompt) followed by
`/enrich` (onboards the result into the vault), or hand-author them. The
doctrine template at `Atlas/concepts/investing/doctrine.template.md` shows the
parameterized `USER_SET` pattern the rest of the layer follows.

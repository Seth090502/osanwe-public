---
aliases: [brief-executive-ref]
categories: [sources]
type: reference
created: 2026-08-23
updated: 2026-08-23
status: active
tags:
  - topic/brief
related:
  - "[[ref-output-template]]"
  - "*invest* (not published)"
  - "[[ref-macro-data-sources]]"
---

# Executive Brief format -- ref-brief-executive.md (SOTA pass, roadmap G-brief)

The operator's requested upgrade: briefs as **5-10 paragraphs sectioned by
importance and category, each with explicit portfolio effect** -- the document a
Treasury Secretary, hedge-fund PM, or principal gets: judgment-first, narrative,
complete sentences, zero dashboard filler. This is an ADDITIONAL output format;
the v2 template (tables/dashboards) remains the default for --quick and machine
consumption. Invoked via `/brief --executive` (or `--format executive`).

## Selection rule (when to produce which)

- `--executive` requested -> THIS format replaces sections 4-19 of the v2 body.
- Default without flag stays v2 (backward compatible; meta.json sidecar identical).
- Both formats share: frontmatter, BLUF/Counter/Alternative, FOLLOWUPS block,
  daily-note linkback line, meta sidecar.

## The contract: 5-10 paragraphs, ordered by importance, each tagged

Every paragraph is ONE category with this inline header pattern:

    ## <N>. `<Category>` -- <importance: CRITICAL | HIGH | MODERATE | BACKDROP>

    <3-6 complete sentences: what happened/is happening -> mechanism -> WHO/WHAT
    moves -> effect on THIS portfolio ($ where possible) -> what would change our mind.>

Importance definitions (IC convention):
- CRITICAL -- demands a decision today or prices in within 48h
- HIGH -- shapes this week's positioning or a live thesis
- MODERATE -- monitored exposure, no action yet
- BACKDROP -- context that conditions everything else but needs no action

## Canonical category order (skip empty categories entirely)

1. **Portfolio Position** (CRITICAL when |P/L| > $`<threshold>` or any order zone hit) --
   overnight/settled moves per position with dollar impacts, execution status of
   ratified actions, cash available. THE paragraph the reader turns to first.
2. **Monetary Policy / Federal Reserve** (HIGH on FOMC/meeting-minutes weeks,
   else BACKDROP->HIGH if pricing shifted) -- Fed funds path, curve moves
   (DGS10/T10Y3M from FRED), QT balance-sheet notes, dot-plot vs market-implied
   divergence. Effect: deployment bands + kernel regime halts are DIRECT
   functions of these numbers -- name the current band state explicitly.
3. **Treasury / Fiscal Policy** (HIGH when issuance/refunding/debt-ceiling/
   Secretary statements move yields) -- auction calendars, buybacks, TGA balance
   trajectory, any Secretary commentary on the dollar/rates/regulation. Effect:
   term premium = your cost of leverage and your discount rate for every growth
   thesis; name which theses reprice if the 10Y moves 25bps.
4. **White House / Administration Policy** (HIGH when tariffs/executive orders/
   regulatory actions touch holdings) -- trade actions, export controls (theme-alpha
   trigger!), sector regulation, geopolitical signaling. Effect: map each policy
   to the thesis it threatens/confirms and the position size at risk.
5. **Economy / Macro Data** (MODERATE normally, HIGH near inflections) --
   employment, inflation prints, ISM/manufacturing (web source per C6), retail
   sales, housing. Effect: which macro_regime the kernel is classifying into and
   whether transition probability rose.
6. **Theses / Positions Deep-Dive** (HIGH when any thesis status != HEALTHY) --
   per-thesis paragraph ONLY for WATCH/STRESSED/INVALIDATED theses: the evidence
   movement since yesterday, distance to kill criteria, options on the board.
7. **Manufacturing & Industrials** (MODERATE; HIGH for theme-gamma thesis) --
   ISM/PMI, capacity utilization, semis capex signals, autos/aero data. Effect:
   theme-gamma + theme-alpha physical-layer demand read.
8. **Credit & Banking** (BACKDROP normally; HIGH when OAS widens >20bps/wk) --
   HY OAS, bank lending standards, regional bank health. Effect: credit leads
   equities at turns; widening OAS is the portfolio's earliest warning light.
9. **Global / Geopolitical** (conditional; CFA-filtered like v2 Phase I) --
   only events passing the 3-stage materiality filter. Effect: direct exposure
   mapping (e.g., China export controls -> revenue at risk % for each affected holding).
10. **Watch List / What Changes Our Mind Today** (always last; merges v2
    Intelligence Gaps + Warning Problems + Scenario Bar into prose) -- the 2-3
    specific observable triggers with levels and the pre-committed response.

## Hard quality bars (what makes this SOTA vs a news digest)

- EVERY paragraph names the PORTFOLIO EFFECT in dollars or thesis-status terms.
  A paragraph without an effect line does not ship.
- Numbers carry provenance tags inline ([Grade A mcp:*] / [script:fred] / [web:date])
  per ref-evidence-hierarchy.md -- same discipline as v2.
- No bullet-point soup inside paragraphs except the Watch List triggers.
- Total length target: 600-1,000 words. If it exceeds that, importance-ranking
  has failed -- cut BACKDROP first.
- BLUF paragraph (v2 section 2) still precedes the numbered sections unchanged.
- Confidence/conviction/cap rules identical to v2; meta.json sidecar gains
  `"format": "executive"`.

## Data sourcing delta vs v2

All v2 sources remain valid. ADDITIONALLY, the executive format EXPECTS:
- FRED series quoted by name+value+as-of (already Phase E.0).
- Treasury-specific items (auctions, TGA) via web search with date citations.
- Manufacturing via web (ISM non-FRED per C6) -- one search, cited.
No new MCP servers required; Claude-side sessions may substitute broker/MCP reads
per existing rules.

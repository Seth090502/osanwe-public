---
categories: [sources]
type: reference
created: 2026-07-04
updated: 2026-07-04
status: active
tags:
  - topic/market-brief
  - topic/skill-infrastructure
related:
  - "brief"
  - "[[ref-output-template]]"
  - "[[ref-macro-data-sources]]"
aliases:
  - ref-brief-operations
---

# Brief Operations Reference (extracted from SKILL.md; brief-vnext Diff 1, 2026-07-04)

Extraction target for /brief SKILL.md over-cap refactor (progressive disclosure, one-level-deep, same pattern as ref-dw-topology.md). Content moved VERBATIM from SKILL.md v2-final (ratified text preserved). Three sections: (1) worked mode examples, (2) failure taxonomy (HALT semantics normative here), (3) coordination matrix + consumers.

---

## Section 1: Examples (8 worked mode examples)

### Example 1: Normal weekday open

`/brief` Mon 8:45 AM ET. Phase A: today date, no F11, no collision. Phase B prints state-transition; auto-proceed. Phase C: F11 set; reads complete. Phase D: script returns full data, market_status=pre_market; one futures search authorized. Phase E: VIX 14.2 contango -> Risk-on; macro Late-cycle. Phase F: Markets one-liner + 11-row Signal Dashboard. Phase G: coherent-risk-on. Phase H: 5 theses HEALTHY. Phase J: movers >1% listed (`<ticker>` +X.X%, `<ticker>` -X.X%). Phase K: `<ticker>` earnings in 27d (skip Pre-Earnings Monitor); CPI Mar Apr 15 in Calendar; Scenario Bar on CPI. Phase M: 1 FOLLOWUP (`/networth -- portfolio delta >5% since last snapshot`). Phase N gate 22/22 PASS. Phase O writes briefing + sidecar. Phase P: 4 peripheral updates + 4 entity back-links (four tickers). Atomic commit, 10 paths.

### Example 2: Weekend brief

`/brief` Sat 8:00 AM ET. Phase D: market_status=closed, last_trading_day=Friday. Header `Weekend Brief -- data as of <Friday> close`; skip Overnight Earnings; expand Calendar + Scenario Bar; "Week in Review" one-liner under BLUF. All other phases standard. Macro regime still classified.

### Example 3: Holiday weekday

`/brief` Mon Apr 6 (Easter Monday equivalent). Phase D: market_status=closed, last_trading_day=Thursday. Header `Holiday Brief -- data as of <Thursday> close`. last_trading_day frozen. Calendar emphasizes catalyst pile-up post-holiday.

### Example 4: Pre-market with futures search

`/brief` Wed 6:30 AM ET. Phase D: market_status=pre_market. Header notes "Pre-market; prices as of last close". ONE web search for futures + overnight movers. Macro_regime_transition monitored. Confidence not capped just on pre-market timing.

### Example 5: Script fallback (ticker errors)

`/brief` Tue 8:30 AM ET. Phase D: yfinance returns errors on 6 of 11 tickers (>50%). SCRIPT_FALLBACK=true; web-searches all prices; annotates "Script fallback -- lower precision" in Intelligence Gaps. Phase N evidence-grade cap forces confidence to 60% regardless of inline grade mix.

### Example 6: Thesis shift (HEALTHY -> WATCH)

`/brief` Thu 8:45 AM ET. Phase H: theme-alpha moves HEALTHY -> WATCH after Commerce Dept signals new chip-export rules (Grade B Reuters Wed PM). Warning Problems entry: `WARNING: theme-alpha thesis WATCH -- Commerce export rules signaled. Base rate: prior export rumors materialized 3 of 7 times (43%). Trigger: formal Commerce notice would shift to STRESSED.` FOLLOWUPS:skills emits `/challenge thesis-theme-alpha` + `/invest <ticker>` with concrete triggers + 48H decision marker.

### Example 7: Divergent cross-asset coherence

`/brief` Fri 8:30 AM ET. Phase G detects: equity +0.4%, credit OAS +18bps widening, gold +1.2%, VIX +0.8 to 17.6. Coherence = divergent. Warning Problems: `WARNING: divergent session -- equity rally + credit widening + gold bid. Base rate: divergent sessions precede regime shift within 5 sessions ~38% of time. Trigger: continued credit widening + VIX through 20 -> regime transition risk.` BLUF surfaces dissent; Counter argues equity is leading credit (sometimes does); Alternative posits sector-specific (regional banks?) credit move.

### Example 8: Refresh mode mid-day

11:15 AM ET. A peer's earnings beat hit wires 11:00 AM. `/brief --refresh Calendar/decisions/briefings/briefing-2026-04-23.md`. Reads existing briefing; Phase A skips collision (path explicit); Phase D fetches fresh prices; mutates only Alerts section (`ALERT: peer beat -- positive PEAD signal for a covered name; re-read its thesis before acting`) + FOLLOWUPS section (`/invest <ticker> -- peer signal favorable; trigger WITHIN 24H`). Body outside Alerts + FOLLOWUPS byte-exact (sha256 verified). meta.json appends to `web_searches` + `followup_skills` arrays. `updated:` bumps. No peripheral writes.

## Section 2: Failure Taxonomy (HALT semantics normative)

### Phase A failures
- **F11 already set**: HALT with recovery guidance
- **fetch-prices.py missing**: HALT (script load-bearing)
- **Same-HHMM same-day collision**: HALT (ambiguous intent)
- **Broker read coverage missing**: mark affected quantities, dollar impact, P&L and whole-book scope UNVERIFIED in the header and Intelligence Gaps; continue independent public-market work. No protected-file or saved-snapshot fallback.

### Phase C failures
- **Thesis essay missing on disk** (any of 5): HALT Phase H; ask the owner (structural gap)
- **Entity recency `git log` returns nothing**: WARN; continue with empty entity-recency input
- **Continuity audit: <3 prior briefings exist**: degrade gracefully; use what is available; null Brier score if below the scorable-call floor (n>=3 provisional / n>=5 full per Phase C brier-ledger rule)

### Phase D failures
- **Schema drift in script JSON**: HALT (do not infer fields)
- **>50% ticker errors**: SCRIPT_FALLBACK mode; web-search; confidence cap to 60
- **Script crash**: full web-search fallback; cap 60; annotate

### Phase H failure
- **Any thesis file missing**: HALT with explicit error; ask the owner

### Phase N gate failures
- **Any 22-item check fails**: HALT with specific item; no writes
- **ASCII byte >127 in NEW content**: HALT; apply replacement table; re-scan
- **Confidence exceeds cap**: HALT; the owner authorizes override or revises

### Phase P failures (F.halt)
- **Update 1-4 mid-batch failure**: IMMEDIATE HALT; F11 stays on; report succeeded / failed / not-attempted; the owner decides rollback or fix-and-retry
- **F17 detects Co-Authored-By post-commit**: HALT; investigate; do NOT silently amend
- **Daily note race (sha256 mismatch)**: re-read once; if still mismatch, F.halt
- **F11 unlink fails post-commit**: log but do not halt (vault is in committed state); the owner manually `rm .claude/state/auto-commit-disabled`

## Section 3: Coordination (shared infra + division-of-concerns matrix + consumers)

### Shared infrastructure (identical semantics with /enrich + /ingest + /invest + /retro)

- Vault indexes (TICKERS, COMPANIES, ALL_BASENAMES) for entity recency + back-link resolution
- BACKLINKABLE_CATEGORIES for symmetric back-link target validation
- Tag vocabulary guardrail (topic/ticker/company/thesis only; briefing emits topic/market-brief)
- Path-guards (mechanical)
- F11 Phase C discipline
- ASCII-only commit + F14 narrow staging + Co-Authored-By suppressed (F17)
- Body-preservation sha256 invariants (F16 bytes compare)
- State-transition-before-F11 abort checkpoint
- Mid-batch F.halt
- Symmetric back-linking
- Pattern 22 ASCII pre-write replacement table

### Division of concerns

| Concern | /brief | /networth | /challenge | /invest | /retro |
|---|---|---|---|---|---|
| Daily morning briefing | Yes (canonical) | No | No | No | No |
| Live portfolio snapshot | Reads only | Yes (snapshot file) | No | Reads only | No |
| Thesis stress-test | Surfaces in Status Board + flags | No | Yes (full) | Implicit per ticker | No |
| Per-ticker analysis | Reads entity + flags via FOLLOWUPS | No | No | Yes (canonical) | No |
| Portfolio mutation | NEVER (path-guarded) | NEVER (path-guarded) | NEVER | NEVER | NEVER |
| Session retrospective | Sessions-log entry per run | No | No | Sessions-log entry | Yes (canonical) |
| Decision record | Flags via FOLLOWUPS | No | No | Implicit | No |
| Body preservation (briefing) | N/A (NEW each day) | N/A | N/A | N/A | N/A |
| Body preservation (peripheral) | Yes (4 targets) | Yes (snapshot is NEW) | Yes (challenge is NEW) | Yes (5 targets) | Yes (4 targets) |
| Symmetric back-linking | Briefing -> entities (3-7) | No | Yes (challenge -> thesis + tickers) | Yes (analysis -> entity) | No |
| FOLLOWUPS:skills emission | Yes (Phase M) | No | Implicit | INGEST:claims (analog) | No |
| Meta.json sidecar | Yes (NEW v2) | No | No | No | No |
| Continuity audit (Brier) | Yes (NEW v2) | No | No | No | No |
| Entity recency surface | Reads <7d | No | Reads | Reads target entity | No |
| Challenge recency surface | Reads <14d | No | N/A | Reads | No |

### Consumed by

- `/retro` -- via sessions-log entry (marker-sig on `(date, skill)` enables merge)
- `/challenge` -- via thesis-shift FOLLOWUPS triggers
- `/invest` -- via per-ticker FOLLOWUPS triggers + entity-recency surfaces
- `/networth` -- via portfolio-value-delta FOLLOWUPS triggers
- `/spark` -- briefing FOLLOWUPS:skills can surface /spark candidate when divergent regime detected (multi-day pattern not captured in any single briefing)
- `/vault` -- /brief Phase B reads /vault stats vault-health-score as one input to overall-state assessment; /brief FOLLOWUPS:skills can surface /vault audit candidate when vault-health-score drift detected vs prior briefings

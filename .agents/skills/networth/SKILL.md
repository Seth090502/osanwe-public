---
name: networth
description: "Live whole-portfolio snapshot, all accounts. Use when asked what the portfolio is worth right now, to snapshot the accounts, whether concentration sits near doctrine ceilings, or how today's move changed theme-alpha thesis exposure. Broker-authoritative holdings (the broker read MCP) + live quotes -> value, allocation, thesis exposure, concentration vs ceilings, dated snapshot. Not a single-ticker quote or a past-date lookup."
metadata:
  categories: data
  osanwe-risk: "writes-vault"
  osanwe-effort: "max"
  osanwe-arguments: ""
  osanwe-argument-hint: "[--preview]"
  osanwe-allowed-tools: "Read Edit Write Bash Glob Grep WebFetch WebSearch Agent ToolSearch"
  osanwe-categories: "meta"
  osanwe-type: "skill"
  osanwe-status: "active"
  osanwe-created: "2026-04-13"
  osanwe-updated: "2026-09-12"
---

Financial evidence contract: `docs/financial-analysis-contract.md` governs source
quality, temporal/basis semantics and missing-data handling across harnesses.
For material numeric batches, run `python tools/fis/evidence.py <envelope.json>`
before output, or disclose manual review and any unverified semantics.
Plugin interoperability: `.agents/skills/finance-data/SKILL.md` owns typed
evidence intake and portable Finance/Data handoffs. This skill retains its
financial procedure and gates. Probe callable tools at run time; installed
plugin metadata alone does not establish a usable connector or source schema.


### Mode routing (Pattern 6 deterministic; invocation modes)

| Syntax | Behavior |
|---|---|
| `/networth` | Full snapshot: MCP holdings + price-fetcher dispatch + calc + dated snapshot write + peripherals, atomic commit |
| `/networth --preview` | All phases in memory; render the would-be snapshot to stdout; SKIP all writes; F11 never set |

### Quality Rules

- ZERO portfolio data in this file. Holdings, share counts, cross-account sets, thesis membership, caveats, reserves: ALL derived at run time from their owning sources. A ticker list or dollar figure appearing in this SKILL.md is a defect (the stale-literal failure mode), not a convenience.
- Dollar amounts from exact share counts x exact prices. Never estimate or round share counts.
- Share counts, quantities and basis require runtime broker read evidence for every account and asset class. Missing coverage is UNVERIFIED; report known subtotal and missing scope, never private-file fallbacks or zero estimates.
- Doctrine threshold math (concentration ceilings, thesis weights) anchors to regular_market_close ONLY -- extended-hours prices are reported but NEVER trigger doctrine evaluations (ref-portfolio-doctrine law).
- Any position whose caveat line (interpretation layer) flags unreliable cost basis gets NO P&L line -- current-value-only, with the caveat named.
- **Subagent dispatch is MANDATORY where the harness provides one** (Phase 1 dispatches `price-fetcher` when an Agent tool exists; that subagent is opus-pinned by its own definition -- never above the opus subagent ceiling, cost directive 2026-07-09). Pre-emptive skip ("script will probably fail", "I'll just WebSearch") is FORBIDDEN; the legitimate fallback fires ONLY on contract violation, actual dispatch failure, or a harness with no Agent tool; pre-emptive skip surfaces in Phase 4 as **DEVIATION**.
- If any price fetch fails, label that position `PRICE UNAVAILABLE` and exclude from totals (never silently omit; never estimate).
- ASCII only in the snapshot + every appended line (Pattern 22).

### Phase 0 -- Broker-authoritative holdings (MCP first)

1. Load the broker read tools (ToolSearch on harnesses that defer tool schemas); call `get_equity_positions` (ALL accounts configured for the deployment) + `get_portfolio` (account totals, cash, crypto aggregate). This is the SOURCE OF TRUTH for tickers, share counts, cost basis, account mapping.
2. Read relevant thesis/account doctrine from permitted references and wiki/hot.md pending items. Never read `.raw/`, `private/`, `finance/`, `credentials/`, `.env*`, `auth.json`, or `*.local.md`; obtain current account facts through broker read tools.
3. DERIVE (never hardcode): CROSS_ACCOUNT_SET from current-session broker accounts; CAVEAT_MAP from supported broker-basis/corporate-action evidence and session constraints. RESERVES are explicitly dated user earmark decisions from permitted sources, separate from broker-verified cash. A stale or missing earmark is unresolved, never zero or an inferred account balance.
3b. CRYPTO COUNTS: discover current tool capability; never assume availability from an old tool list. Per-coin quantities require a successful authorized broker read. If only a broker aggregate is available, preserve that aggregate without inventing per-coin allocation. If neither exists, crypto and whole-book concentration are UNVERIFIED.
4. Read `Atlas/sources/investing/ref-portfolio-doctrine.md`: the thesis map (ticker -> thesis) and the machine `doctrine:` block ceilings -- cite by path, never restate from memory.
5. Availability guard: missing broker coverage -> quantities and affected account/whole-book totals UNVERIFIED. No private-file fallback. Continue only with a clearly scoped verified subtotal.

### Phase 1 -- Live prices (price-fetcher dispatch; MANDATORY where available)

Dispatch `price-fetcher` when the harness exposes an Agent tool; otherwise execute the documented inline fallback below verbatim. Input: `{equities: [<derived list>], crypto: [<derived list>]}`. The subagent runs broker-authoritative equity quotes (Tier 0) then `tools/fetch-prices.py` (Tier 1) then per-ticker retry (Tier 2), and returns a structured JSON quotes map. With no Agent tool, the main loop runs those same three tiers inline in the same order and assembles the same quotes map -- the tier order, the validation below, and the C5 gate are identical either way.

Validate the return: `timestamp`; `quotes` map with every held ticker present in `quotes` OR `failures` (no silent omissions); per-quote `market_session` (pre-market | regular | after-hours | closed) + `source` + `broker_authoritative` + extended-hours fields; caveat fields honored per CAVEAT_MAP (e.g. a no-P&L basis flag rides through as `caveat`).

**C5 broker-authoritative gate (red-team 2026-07-09; enforces the price-fetcher parent contract):** during a REGULAR session with the broker MCP present, assert `mcp_price_count >= held-equity count`. Shortfall -> ONE re-dispatch (or one inline retry where no Agent tool exists); second shortfall -> **HALT the portfolio-math phases** (do NOT proceed with non-broker prices for regular-session portfolio math; report which tickers fell through). Structural MCP absence (harness without the broker server, headless, server down) is the degrade path, not a HALT: proceed on script prices with a `price-unconfirmed` flag in the snapshot frontmatter + Notes. WebSearch prices for EQUITIES during a regular session are FORBIDDEN (the fallback price domains are on the AGENTS.md blocklist and defeat the broker-authoritative premise); the inline WebSearch fallback below is legal only outside regular session or for assets the script cannot cover.

Contract violation or dispatch failure -> ONE re-dispatch -> inline WebSearch fallback WITHIN the C5 bounds above: batch the DERIVED holdings list (equities, ETFs, crypto -- groups built from Phase 0, never a hardcoded roster), record price + freshness per ticker. Record the dispatch tally for Phase 4.

### Phase 2 -- Calculate

Per-ticker live-valuation price source: `market_session` in (after-hours, pre-market) AND non-null `extended_hours_last` -> use it, surfaced as "AH-priced"/"PM-priced"; else regular close. Crypto always `price` (24/7). Closed market -> last regular close.

**Doctrine anchoring:** concentration + thesis-weight aggregation uses regular_market_close values ONLY. Extended-hours valuation is reported but never evaluated against the doctrine ceilings.

Per position: current value = shares x live price; gain/loss + % vs cost basis. HARD P&L RULE (independent of CAVEAT_MAP parse success): any transferred-in position whose basis integrity cannot be POSITIVELY established gets NO P&L line -- current value only, reason stated (CAVEAT_MAP flags are one establishment path, absence of a clean broker basis is itself disqualifying). CRYPTO RECONCILIATION: sum of broker-verified per-coin values MUST be reconciled against the `get_portfolio` broker crypto aggregate; divergence beyond price-movement tolerance -> flag line in Notes ("per-coin quantities may be stale; broker aggregate differs by X%"). Aggregate: per-account value (positions, crypto and cash as each account reports them), combined; cash; allocation by thesis (DERIVED map; regular-close anchored) and by account; top-5 by weight; concentration (top single name %, top-5 %, crypto %) vs the doctrine ceilings read in Phase 0 -- state headroom or breach per ceiling; extended-hours delta ($ + portfolio % shift) when any held position has non-null AH change.

**Thesis attribution -- DUAL BASIS (red-team 2026-07-09):** the doctrine thesis map has OVERLAPPING memberships (some tickers belong to more than one thesis) and the `doctrine:` block's `concentration.basis: effective` does not define the shared-ticker split -- the operative half-weight convention lives only in snapshot precedent. Until the rule is ratified into the block: compute and report BOTH bases against each ceiling -- STRICT (shared tickers full-weight in every thesis they belong to) and EFFECTIVE (per the most recent prior snapshot's stated convention, cited by path) -- and NEVER silently pick one; where the two straddle a ceiling, say so explicitly. Standing FOLLOWUP each run until closed: `/decide ratify-thesis-attribution-rule -- encode the shared-ticker split into the doctrine block (re-fingerprint + ratification; Atlas is human-write-only)`.

### Phase 2.5 -- Historical comparison

Latest prior `wiki/investing/snapshots/networth-*.md`: change since ($ and %), best/worst performer, thesis-allocation drift vs targets, reserve/earmark progress -- compare the relevant account cash against the CURRENT reserve + earmark lines derived in Phase 0.3 (never against a remembered figure).

### Phase 3 -- Compose snapshot

Writes to `wiki/investing/snapshots/networth-<YYYY-MM-DD>.md` (plus the Phase 4 peripherals: wiki/hot.md bump, daily note, sessions-log); same-day collision -> `-HHMM` variant (archival rule). Frontmatter: canonical + `type: snapshot` + `valuation_session: <regular|after-hours|pre-market|closed>` + `related:` *investing-moc* (not published).

Body: `# Portfolio Snapshot -- <date>`; combined value + prices-as-of timestamp + source mix (broker-authoritative count / script / fallback); `## By Account` table; `## All Positions` table (Ticker | Account | Shares | Price | Value | Weight | Gain/Loss -- CROSS_ACCOUNT_SET rows shown combined with per-account sub-rows; caveat-flagged rows show current value only); `## By Thesis` table (rows = the DERIVED thesis map; dual-basis: Strict Value/Weight + Effective Value/Weight | Positions); `## Concentration` (top name %, top-5 %, crypto % -- each vs its doctrine ceiling with headroom, both bases where they differ); `## Change vs prior snapshots` (Phase 2.5 output: delta $/%, best/worst performer, drift, reserve progress); `## Notes` (every applicable CAVEAT_MAP line + reserve status + crypto-reconciliation result + UNVERIFIED coverage / `price-unconfirmed` disclosures). Every quantitative claim carries `prov:` (`mcp:*` > `script:*` > `file:*` > `web:*`).

### Phase 3.5 -- Pre-Output HALT gate

1. Every held ticker accounted for: in the positions table, or labeled PRICE UNAVAILABLE and excluded from totals.
2. All reported asset quantities are broker-authoritative; missing asset/account coverage is UNVERIFIED and excluded from unsupported whole-book claims. Any aggregate/per-name mismatch is disclosed. Price/session provenance applies to every harness.
3. Doctrine math regular-close anchored; ceilings cited by path; headroom/breach stated per ceiling on BOTH attribution bases; straddles called out.
4. Transferred-in positions without established basis integrity have no P&L line (hard rule, CAVEAT_MAP-independent); caveat named in Notes.
5. No hardcoded roster used anywhere (cross-account set, thesis rows, caveats all derived this run).
6. ASCII clean; -HHMM collision resolved; no write targets `.raw/ private/ finance/ credentials/ Atlas/`.
7. F11 set before writes (`--preview`: no writes, F11 never set).
8. Sessions-log entry + daily-note line composed; hot.md `last_networth` bump planned.

ANY failure -> HALT with the item number; F11 stays on.

### Phase 4 -- Atomic writes + peripherals

1. Set F11 (`touch .claude/state/auto-commit-disabled` where the per-write auto-commit hook runs; harnesses without that hook honor the same lifecycle by instruction -- [[ref-execution-discipline]]); write the snapshot.
2. hot.md frontmatter bump: `last_networth: <today>` (field exists in hot-md-v2 schema; update only, sha256-preserve elsewhere).
3. Daily note `## Observations` line: `- [HH:MM] Portfolio snapshot: $<combined> (<valuation_session>; <source mix>)`; sessions-log entry per canonical schema.
4. Dispatch report (one of): `Phase 1 price-fetcher: DISPATCHED` | `INLINE (no Agent tool in this harness)` | `FALLBACK (<reason>)` | `DEVIATION (<judgment>)` -- DEVIATION is a discipline breach, logged to sessions-log.
5. F14 narrow stage (snapshot + hot.md + daily + sessions-log); commit `agent: networth <date> -- <combined> (<session>)`; F17 verify; F11 clear.

### Failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| MCP tools absent | Read connector absent, denied, or unavailable | Report UNVERIFIED; no private-file fallback; repeat when runtime evidence becomes available |
| price-fetcher return missing market_session | Contract violation | One re-dispatch -> inline WebSearch fallback; tally in Phase 4 |
| A ticker in neither quotes nor failures | Silent omission (contract breach) | Treat as violation -> re-dispatch; never fill from memory |
| Concentration flips a ceiling on AH prices | Doctrine anchoring broken | Recompute on regular close; AH is report-only by law |
| Same-day collision | Prior snapshot today | `-HHMM` variant (archival rule) |

### Coordination

- **/brief** -- reads the latest snapshot for portfolio movers; flags >5% hot.md baseline drift as this skill's trigger; /networth owns the portfolio-refresh scope (retired from /brief Phase 15).
- **/invest** -- Phase J portfolio-fit math shares the same MCP-first counts law; snapshots are its exposure baseline.
- **/gate + pretrade staircase** -- concentration numbers here are advisory context; execution-time ceiling checks live in tools/pretrade_gate.py against the trusted broker book (never this snapshot).
- **/retro** -- sessions-log entry consumed at session end.

---
name: networth
risk: safe
description: Use daily for portfolio check, after price-moving events (>2% portfolio delta), when concentration or thesis-exposure questions arise, before deployment decisions, after dividend or contribution events, or when /brief flags a hot.md baseline drift greater than the 5% trigger. Portfolio snapshot with live prices. Reads holdings, fetches current quotes, calculates total value, allocation, and thesis exposure. Writes a dated snapshot.
arguments: []
argument-hint: "No arguments needed"
user-invocable: true
allowed-tools: Read, Edit, Write, Bash, Glob, Grep, WebFetch, WebSearch, Agent
---

## Quality Rules
- Dollar amounts from exact share counts x exact prices. Never estimate or round.
- Cross-account holdings always reported combined.
- Thesis exposure calculated by mapping each holding to its thesis from [[doctrine.template]].
- Use fetch-prices.py for live prices when available. Fall back to web search only if script fails.
- **Subagent dispatch is MANDATORY when specified by phase** (Phase 1 dispatches `price-fetcher`). Pre-emptive skip based on judgment ("script will probably fail", "I'll just use WebSearch directly") is FORBIDDEN. The subagent decides applicability via its own N/A return contract; the parent skill dispatches and validates the return. Legitimate fallback fires ONLY on (a) contract violation -- subagent return missing required fields, OR (b) actual dispatch failure -- timeout, rate limit, tool-denial, hard subagent crash. Pre-emptive skip surfaces in Phase 4 audit as **DEVIATION** (not "fallback"). Quality preserved by additive design: the inline WebSearch fallback below the dispatch remains intact for legitimate failures.

## /networth

Calculate current portfolio value with live prices and write a dated snapshot.

### Phase 0: Read Holdings

1. `private/holdings-taxable.md` (all taxable positions with share counts)
2. `private/holdings-ira.md` (all IRA positions with share counts)
3. `Atlas/concepts/investing/doctrine.template.md` (thesis mappings)

Extract every position: ticker, shares, cost basis, account.

### Phase 1: Fetch Live Prices (DELEGATED + WebSearch fallback)

#### Phase 1.0: DELEGATED dispatch to `price-fetcher` subagent (PREFERRED path; Phase C wiring 2026-05-02)

**MANDATORY** (per Quality Rules): dispatch first, no pre-emptive skip. Subagent handles N/A returns gracefully (e.g., script timeout per ticker -> per-ticker WebSearch fallback inside the subagent).

Use the Agent tool with subagent_type `price-fetcher`. Pass input: `{equities: [<list from Phase 0>], crypto: [<list from Phase 0>]}`. The subagent wraps `tools/fetch-prices.py --equities <list> --crypto <list> --json` internally, falls back to per-ticker WebSearch on script failure, and returns a structured JSON quotes map with timestamp + source + freshness + extended-hours fields per ticker.

Validate subagent return:
- JSON with `timestamp`, `quotes` map, `extended_hours_movers` array, `failures` array
- Every held ticker present in `quotes` OR `failures` (no silent omissions)
- Every quote has `market_session` field (pre-market | regular | after-hours | closed)
- Source per quote (fetch-prices.py / WebSearch fallback / etc.)
- `extended_hours_movers` is always a list (empty when no AH movers above 3.0% threshold)

On contract violation OR dispatch failure: fall through to inline WebSearch logic below. Surface fallback in Phase 4 audit report.

On dispatch success: use returned quotes map directly for Phase 2 calculations.

#### Phase 1.0-bis: Broker-authoritative position + quote layer (v3 MCP wiring; 2026-06-04)

When the `robinhood-trading` MCP is connected (interactive Claude session): the price-fetcher subagent (v3) already returns broker-authoritative equity `price` (regular_market_close anchored) with `broker_authoritative: true` -- use directly. ADDITIONALLY the parent (in-session, has MCP) calls `mcp__robinhood-trading__get_equity_positions` (all accounts: taxable + IRA) + `mcp__robinhood-trading__get_portfolio` for **authoritative shares, cost basis, and account totals** -- this SUPERSEDES reading share counts from `private/holdings-taxable.md` + `private/holdings-ira.md` for snapshot math (those files become the human-readable mirror, not the source of truth). Crypto stays aggregate-only from `get_portfolio` (per-coin via fetch-prices.py per Phase 1.0).

Concentration/trim math remains regular_market_close anchored -- use the MCP `close`, not AH `last_non_reg_trade_price`, per [[doctrine.template]].

**Availability guard:** if the MCP is absent (Codex engine, headless, server down), SKIP this layer and read share counts from private/*.md as before. Additive; zero behavior change when MCP unavailable.

#### Phase 1.1: WebSearch fallback (runs ONLY if Phase 1.0 failed)

Search for current prices of all held positions. Group searches efficiently:
1. Major equities batch
2. ETFs batch
3. Crypto batch
4. Any remaining positions

Record price and freshness timestamp for each.

### Phase 2: Calculate

**Live-valuation price source decision (per ticker)**:
- If `market_session` in (`after-hours`, `pre-market`) AND `extended_hours_last` is non-null: use `extended_hours_last` for live valuation. Surface in output as "AH-priced" or "PM-priced" per ticker.
- Else: use `price` (regular_market_close) for valuation.
- Crypto (`market_session=regular`): always use `price` (24/7 markets; AH fields null by contract).
- Closed market (`market_session=closed`): use `price` (last regular-session close).

**Doctrine note (Mission Three)**: Concentration math + thesis-weight aggregation uses regular_market_close (`price` field) anchored values, NOT extended-hours prices. Extended-hours valuation is reported in the snapshot but does NOT trigger doctrine threshold (`THESIS_CAP_AMBER`/`THESIS_CAP_RED` tiered per [[doctrine.template]]; `SINGLE_NAME_AMBER`/`SINGLE_NAME_RED`; `OTHER_THESIS_FLAG`) evaluations -- AH prices are volatile + transient. /invest Phase J.5 will surface AH drift as Material/High severity drift class for ratification.

For each position:
- Current value = shares x live_price (per decision above)
- Gain/loss = current value - (shares x cost basis)
- Gain/loss % = (current price - cost basis) / cost basis

Aggregate:
- Total brokerage value (equities + crypto separately)
- Total IRA value (positions + cash)
- Combined portfolio value
- Cash positions
- Allocation by thesis (per [[doctrine.template]] thesis slugs) -- regular-close anchored per doctrine note
- Allocation by account (brokerage vs IRA)
- Top 5 positions by weight (regular-close anchored)
- Concentration: top position as % of total, top 5 as % of total (regular-close anchored)
- Live-valuation deltas: $-impact + portfolio % shift IF any held position has non-null extended_hours_change_pct

### Phase 2.5: Historical Comparison

Check for prior networth reports in `wiki/investing/snapshots/networth-*.md`
If found, calculate:
- Change since last snapshot ($ and %)
- Best and worst performer since last snapshot
- Thesis allocation drift: has any thesis grown beyond target weight?
- IRA deployment progress: how much cash remains?

### Phase 3: Output

Write to `wiki/investing/snapshots/networth-YYYY-MM-DD.md`:

```yaml
---
categories: [wiki]
type: snapshot
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
valuation_session: <regular|after-hours|pre-market|closed>
tags: []
related:
  - "[[holdings-taxable]]"
  - "[[holdings-ira]]"
  - "[[investing-moc]]"
---
```

**`valuation_session`** values:
- `regular` -- snapshot taken during regular market hours; all positions priced at live regular_market_close
- `after-hours` -- snapshot taken in 16:00-20:00 ET window; equities with non-null extended_hours_last priced at AH; crypto + null-AH positions at regular close
- `pre-market` -- snapshot taken in 04:00-09:30 ET window; equities with non-null extended_hours_last priced at PM; crypto + null-PM positions at regular close
- `closed` -- snapshot taken outside any session (overnight, weekend, holiday); all positions at last regular close

```markdown
# Portfolio Snapshot -- YYYY-MM-DD

**Total Value: $XX,XXX.XX** | Prices as of: [timestamp]

## By Account
| Account | Value | Cash | Total |
|---------|-------|------|-------|
| Brokerage (equity) | $X,XXX | -- | |
| Brokerage (crypto) | $X,XXX | -- | |
| IRA | $X,XXX | $X,XXX | |
| **Combined** | | | **$XX,XXX** |

## All Positions
| Ticker | Account | Shares | Price | Value | Weight | Gain/Loss |
|--------|---------|--------|-------|-------|--------|-----------|
(sorted by value descending)

## By Thesis
| Thesis | Value | Weight | Positions |
|--------|-------|--------|-----------|
| <thesis-slug> | $X,XXX | XX.X% | ... |

## Concentration
- Top position: [TICKER] at XX.X%
- Top 5 positions: XX.X% of portfolio
- Crypto: XX.X% of portfolio

## Notes
- IRA cash: $X,XXX pending deployment
```

### Phase 4: Knowledge Base Updates
- Append session entry to `Calendar/decisions/sessions-log.md`
- Append to today's daily note under Observations: `- [HH:MM] Portfolio snapshot: $XX,XXX`
- **Subagent dispatch report** (Phase C wiring 2026-05-02): emit one of:
  - `Phase 1.0 price-fetcher: DISPATCHED` -- subagent ran, quotes integrated
  - `Phase 1.0 price-fetcher: FALLBACK (<reason>)` -- legitimate dispatch failure; WebSearch fallback executed
  - `Phase 1.0 price-fetcher: DEVIATION (<judgment>)` -- pre-emptive skip; flag as discipline breach + sessions-log entry

### Quality Rules
- ALL math from actual share counts. Never estimate.
- Note split status for any position with a recent share split (pre-split vs post-split share count).
- Cross-account holdings reported as combined exposure.
- If any price fetch fails, label that position "PRICE UNAVAILABLE" and exclude from totals.

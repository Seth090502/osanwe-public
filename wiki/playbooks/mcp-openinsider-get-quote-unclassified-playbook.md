---
categories: [wiki]
type: synthesis
status: active
created: 2026-07-10
updated: 2026-07-10
tags: [topic/consolidation, topic/playbook]
related:
  - "hot"
---

# Mcp__openinsider__get_quote unclassified Playbook

## Pattern
Invariant: Every in-window mcp__openinsider__get_quote failure (7/7) was an off-doctrine reach for a price while all US market sessions were closed -- 6 returned "invalid or missing marketState" from weekend/overnight dark windows and 1 was "ticker not found: DTCR" -- because get_quote is the openinsider insider-filings MCP's Yahoo-proxy leg, sits in no skill's quote contract, and has no valid quote to return off-session.

Mechanism: the failure hook stamps ts with local time, and all 7 timestamps fall outside regular AND extended hours -- every one of them outside market hours-- so Yahoo's marketState is null/CLOSED and the proxy raises. The canonical quote path (.claude/agents/price-fetcher.md: the broker MCP Tier 0, tools/fetch-prices.py Tier 1) carries an explicit market_session taxonomy and returns official closes off-session, so it never hits this failure class; /gate fills move_5d_pct from prov mcp:* > script:* per tools/gate-rules.json:21, never from get_quote. the instrument is a fund rather than an operating company. The reach happens as an ad-hoc fallback when the broker MCP is absent (the 06-18 GOOGL failure is a headless bypassPermissions run; sessions-log 2026-07-09 SPCX names "price (openinsider fallback -- broker tool absent)") -- exactly the degrade price-fetcher v4 already routes to fetch-prices.py instead.

Confidence: 85% -- 7/7 source records read directly with timestamps confirmed dark-window; openinsider absent from every skill quote contract (grep) and the canonical path documented; residual is un-inspected MCP internals and failure-only telemetry (no success sample).

## Evidence
- 7 failures clustered on mcp__openinsider__get_quote::unclassified
- Threshold cleared: >= 5 failures in cluster (observed 7).

## Counter-cases

- (none found in-window -- searched all failures-*.jsonl for mcp__openinsider__get_quote: exactly 7 hits, 7/7 in closed-session windows; ZERO failures inside an active session, the case that would falsify the session-state mechanism; success telemetry is not captured, so "never works" is NOT claimed -- only that every logged failure is a dark-window off-doctrine reach)
- Nearest strain, out-of-window: sessions-log 2026-07-09 SPCX /invest (Calendar/decisions/sessions-log.md:4798) used an "openinsider fallback -- broker tool absent" non-broker price -- a C5-capped degrade that reinforces the rule (v4 doctrine says that fallback must be tools/fetch-prices.py)

## Recommendation

Add a one-line routing guard to docs/osanwe-runtime-reference.md "Preferred Financial Data Sources" (the section AGENTS.md Data-sources already points to): openinsider MCP = Form-4/insider data ONLY; its get_quote leg proxies Yahoo, errors on marketState whenever US sessions are closed, and cannot resolve ETFs (e.g. DTCR) -- NEVER route a price through it; all quotes -> price-fetcher (the broker MCP Tier 0 / tools/fetch-prices.py Tier 1). Mirror the prohibition as one anti-pattern line in .claude/agents/price-fetcher.md ("never fall back to mcp__openinsider__get_quote for a price; Tier 2 is fetch-prices.py single-ticker retry only") and annotate the openinsider row in docs/osanwe-vault-codex.yaml. Ratify via /decide openinsider-get-quote-not-a-price-source.

## Apply-when

About to call mcp__openinsider__get_quote for a price -- or reaching for it because the broker MCP is absent, or it is outside market hours: STOP and reroute to price-fetcher or python tools/fetch-prices.py --equities `<TICKER>`. openinsider is insider-filing data only; it has no valid quote when US sessions are closed.

## Related
- hot -- session cache; this playbook is surfaced in the consolidation digest
- [[bash-exit-code-1-playbook]]
- [[bash-exit-code-2-playbook]]
- [[read-unclassified-playbook]]

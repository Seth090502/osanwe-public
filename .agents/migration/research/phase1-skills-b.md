# Phase 1 audit: skills B -- ingest, invest, networth, retro, spark, vault (+ one withheld personal skill) + workflows + deny-list (worker report, condensed-verbatim)

Provenance: opus/max Explore worker, 2026-08-10. Persisted from session context 2026-08-10.

## Summary table

| Skill | name-match | desc-chars | body bytes/lines/tokens | worst coupling |
|---|---|---|---|---|
| (withheld personal skill) | yes | 588-590 (ONLY compliant skill) | 20159/237/5039 | 2 MANDATORY subagents; inline GRADE-tiering fallback documented. **Zero hooks/MCP/scripts -- cleanest of the 7.** 8 ref-*.md files |
| ingest | yes | 1623 (+599) | 35614/546/8903 | vault-classifier-sweep MANDATORY **HALT gate** (score<90 or gate>0 blocks atomic apply) + claim-distributor per entity + F11 x11 (auto-commit suppressor) + CLAUDE_VAULT_BYPASS_VALIDATOR |
| invest | yes | **4848-4850 (worst in workspace)** | 109150/876/27287 | **Deepest coupling:** 2 DW workflows (invest-research.js, invest-verify.js w/ Wave-3 refutation -> Phase N HALT) + 5 named subagents + the broker/fred MCP (wildcards in frontmatter) + 13 tools/*.py + F11 x39/F14 x13 + ToolSearch x6 + INVEST_DW_TOKEN_BUDGET/ORCHESTRATOR_MODEL/OSANWE_DW_HINT/OSANWE_ENGINE. **Architected for degradation: "Tier-B is the permanent universal fallback"; every phase body remains the authoritative sequential spec.** 5 ref files (~214 KB) + stray .audit/ pii-check logs (junk) |
| networth | yes | 1671 (+647) | 12822/95/3205 | price-fetcher MANDATORY with **legally bounded fallback** (regular-session equity WebSearch FORBIDDEN -- blocklist + broker-authoritative premise); C5 gate HALTs portfolio math on shortfall; the broker get_equity_positions + get_portfolio via ToolSearch; [STALE-COUNT]/[INTERP-COUNT] degrade markers documented |
| retro | yes | 2972 (+1948) | 30048/499/7512 | **ZERO subagents (only skill of the 7).** F11 x13; telemetry_analyzer.py reads hook-populated sinks (degrades silently to no-signals); SessionStart daily-note precondition self-heals ("create if absent"); narrow MCP grant mcp__robinhood-trading__get_equity_orders (X47p fills-reconcile MANDATORY-when-orders-exist; D.5 optional) |
| spark | yes | 3465 (+2441) | 43768/435/10942 | 9-way pattern-class-scout fan-out via spark-sweep.js + spark-verify.js 4-lens wave + **HARD SessionStart-injection dependency** (Part W offsets from the distillate injector -- no offsets on Tier B, corpus source drops); OSANWE_FORCE_SEQUENTIAL=1 is the ready-made Tier-B switch; claudewatch MCP optional/degrading; scouts are Read/Grep/Glob-only BY RULE (no MCP wiring) |
| vault | yes | 2117 (+1093) | 33289/520/8322 | **Frontmatter FAILS yaml.safe_load** (unquoted description, colon-space at col 1536) -- blocking for strict-YAML harnesses. vault-classifier-sweep dispatch is the weakest mandatory coupling (thin wrapper; direct script fallback in-text). Real breaks are hook-shaped: daily-mode **HALT** presumes tools/session-start.sh ran as SessionStart hook ("Do NOT recreate from /vault"); <=90 score clamp presumes PreToolUse guards; Section 9 Log presumes UserPromptSubmit hook. tools/vault-audit.py x12 refs (deepest single script dependency) |

Aggregate: 7/7 dir==name; 6/7 over 1024 (the withheld skill alone complies); 1/7 YAML-parse fail (vault; + gate from set A = 2/15 total); invest 876 / ingest 546 / vault 520 over the 500-line guidance; combined ~71,209 body tokens (excl. ~373 KB ref companions).

## Workflows (.claude/workflows/, 6 files -- all Tier-A-only)

| File | Bytes/Lines | Purpose | Invoked by |
|---|---|---|---|
| brief-research.js | 10615/131 | Wave-1 read-only acquirer fan-out <=6: price-fetcher + fred-insider-macro + entity-challenge-recency + continuity + `<private-file>` | /brief |
| invest-research.js | 17378/217 | price-fetcher -> Wave 1 (identity/fundamentals/filings/competitive x4) -> Wave 2a (forensic-scorer + institutional-positioning-scout) | /invest |
| invest-verify.js | 8077/107 | Wave-3 skeptics (data-integrity, R/R, routing, provenance); any refutation -> parent Phase N HALT, zero writes; gated on verdict>=BUY / status change / +-5 boundary / --verify | /invest |
| regenerate-distillate.js | 10730/134 | Distillate regen on SENTINEL-2 STALE: discovery -> sonnet extractors -> default-to-refuted judges -> <=2 fix rounds; sensitive Parts excluded | SessionStart hook (inject-`<private-file>`.py), NOT a skill |
| spark-sweep.js | 16344/247 | 9x pattern-class-scout chunked waves <=6; no_patterns=SUCCESS; failure -> re-dispatch -> _fallback marker | /spark |
| spark-verify.js | 8971/130 | One 4-lens verifier per qualifying spark (EVIDENCE/FALSIFIABILITY/NOVELTY/MUNDANE-ALT), fail-closed, cap 7 | /spark |

Shared constraints: read-only fleets (all writes in main loop under F11/sha256/path-guard); workflow sandbox has NO process.env (budgets passed as args), no Date.now()/Math.random().

## the broker deny-list (.claude/settings.json permissions)

- `permissions.deny` total: **18 entries, 18/18 broker mutators, zero from any other server.** No allow/ask lists.
- Order-placement core: place/cancel/review_equity_order, place/cancel/review_option_order. Remaining 12: add_option_to_watchlist, add_to_watchlist, create_scan, create_watchlist, follow_watchlist, remove_from_watchlist, remove_option_from_watchlist, run_scan, unfollow_watchlist, update_scan_config, update_scan_filters, update_watchlist.
- Defense-in-depth: PreToolUse hook matcher `mcp__robinhood-trading__(place|cancel|review)_equity_order` -> pretrade-token-gate.py. **On Tier B the hook layer disappears; the migration must carry the read-only posture into each harness's native permission mechanism** and re-express pretrade as gate-script + prompt rule.
- Full Claude hook lifecycle assumed by these skills: 11 events, 26 handlers -- SessionStart x5, PreToolUse x4, PostToolUse x10, UserPromptSubmit x2, PostToolUseFailure x1, SubagentStart/Stop x2, PreCompact/PostCompact x2, Stop x1.

---
name: invest
description: "Full institutional-grade analysis of ONE ticker, ETF, or crypto. Use pre-entry, post-earnings to rerun the numbers on a thesis, on a conviction refresh, or when asked if a name is a buy. Returns a STRONG BUY / BUY / HOLD / SELL / STRONG SELL rating plus quantified kill criteria, from 50-75 sources with forensic + positioning overlays, portfolio-fit math and a ticker entity-note update. Not a portfolio snapshot (use /networth) or investing philosophy."
metadata:
  categories: decisions
  osanwe-risk: "critical"
  osanwe-effort: "max"
  osanwe-arguments: "ticker"
  osanwe-argument-hint: "a ticker, ETF or crypto symbol [--preview | --confirm | --replace | --no-peripheral | --no-entity | --refresh `<path>` | --thesis `<name>` | --verify | --local]"
  osanwe-allowed-tools: "WebSearch WebFetch Read Write Edit Bash Glob Grep Agent ToolSearch mcp__robinhood-trading__* mcp__fred__*"
  osanwe-categories: "meta"
  osanwe-type: "skill"
  osanwe-status: "active"
  osanwe-created: "2026-04-18"
  osanwe-updated: "2026-09-13"
---

Financial evidence contract: `docs/financial-analysis-contract.md` governs source quality, temporal/basis semantics and missing-data handling across harnesses.
For material numeric batches, run `python tools/fis/evidence.py <envelope.json>` before output, or disclose manual review and any unverified semantics.
Plugin interoperability: `.agents/skills/finance-data/SKILL.md` owns typed evidence intake and portable Finance/Data handoffs. This skill retains its financial procedure and gates.
Probe callable tools at run time; installed plugin metadata alone does not establish a usable connector or source schema.
Executable valuation and institutional method routing: `docs/institutional-methods.md`.
For ordinary operating-company DCF use `tools/fis/valuation.py`; reconcile inputs with evidence.py and report terminal-value sensitivity and implied expectations.

# /invest `<ticker>` -- institutional-grade analysis with atomic entity integration (v2 final)

Take a ticker, produce an institutional-grade investment analysis that updates the vault atomically: compose a canonical analysis file, integrate claims into the ticker entity note body-preservingly, update watchlist + research-log + sessions-log + daily note peripherally, commit atomically.

## When to use

"I am considering a position change (buy / add / trim / exit) on `<ticker>` and need an institutional-grade analysis that lands in the vault." Or: "Earnings is <5 days out / macro rotation surfaced / a thesis challenge on `<ticker>` needs fresh data-driven verdict."

## Not for

- Portfolio-wide snapshot (use `/networth`)
- Multi-ticker synthesis across positions (portfolio-synthesis mode; not yet implemented in /invest)
- Thesis stress-test without a specific ticker (use `/challenge`)
- Morning briefing / market-open scan (use `/brief`)
- Entity maintenance only, without research (use `/ingest`)
- Quick price check (direct WebSearch; no vault write)

### Mode routing (Pattern 6 deterministic; invocation modes)

| Syntax | Behavior |
|---|---|
| `/invest <TICKER>` | Full analysis (Phase 0 + A-R): state-transition -> F11 -> research -> compose -> entity -> peripherals -> atomic commit |
| `/invest <TICKER> --preview` | Dry-run. Phase B state-transition print only. No F11, no writes, no commit |
| `/invest <TICKER> --confirm` | Per-file confirmations before each Edit/Write |
| `/invest <TICKER> --replace` | Overwrite same-day analysis file. Explicit destructive (default is `-<HHMM>` timestamped variant) |
| `/invest <TICKER> --no-peripheral` | Skip Phase L peripheral updates (analysis + entity only) |
| `/invest <TICKER> --no-entity` | Skip Phase K entity update (draft analysis only) |
| `/invest --refresh <analysis-path>` | Re-run Phase K entity extraction from existing analysis. Additive. Skips research phases. HALT if path not found |
| `/invest <TICKER> --thesis <name>` | ADDITIVE lens overlay (theme-alpha \| theme-beta \| theme-gamma \| theme-delta \| theme-epsilon). First principles ALWAYS runs; the lens adds a "Thesis-lens view" subsection (cohort coherence + thesis-specific kill criteria) and enriches the conviction rationale. The lens CANNOT change the rating (see Phase D.7) |
| `/invest <TICKER> --verify` | Force the Wave-3 adversarial skeptics even on a non-boundary HOLD/SELL (TOPOLOGY=dw; see K.5 STEP 4). On TOPOLOGY=sequential the flag triggers the inline data-integrity re-derivation checks instead |

## Screen mode (informal; staleness rule)

Multi-name watchlist screens run on /invest infrastructure (live-quotes batch + readiness deltas; no full A-R phase arc). STALENESS RULE (C-extension root-cause 2026-06-10): any prior-analysis date or staleness claim MUST derive from the `wiki/investing/analyses/<ticker>-analysis-*.md` glob + the entity note's Recent section -- NEVER from `Atlas/concepts/investing/watchlist.md` rows (Atlas rows are human-gated and stale-prone; 2 of 8 screens on 2026-06-10 carried wrong priors from April-stale watchlist rows).

## Execution Rules

- **Tier-B (TOPOLOGY=sequential):** Execute phases sequentially. No merging or abbreviation. Use WebSearch for every current data point (not training data); perform the exact search count each phase specifies. **Tier-A (TOPOLOGY=dw, per Phase A.7):** phases 0/A/B/C/D run sequentially; the E-I research EXECUTION runs as concurrent Wave-1 workers per Phase A.8 + `ref-dw-topology.md` (the phase text below remains the authoritative spec of WHAT each worker produces); every other invariant (F11, path-guards, sha256 body-preservation, mandatory dispatch + N/A-is-success + DEVIATION, verdict spine, commit discipline) is IDENTICAL across both tiers. Tier-B is the permanent universal fallback -- any DW absence or regression lands there automatically.
- **F11 Phase C discipline**: set `.claude/state/auto-commit-disabled` at Phase C, BEFORE any Edit/Write. Phase B state-transition print runs BEFORE F11 so user can abort pre-writes. Clear flag only after Phase O post-commit verification.
- **Path-guards mechanical**. NEVER write: `private/`, `.raw/`, `_quarantine/`, `finance/`, `credentials/`, `.git/`, `.claude/hooks/`, `.claude/state/`. NEVER read `.raw/`, `private/`, `finance/`, `credentials/`, `.env*`, `auth.json`, or `*.local.md` into context. Account facts require current-session broker read evidence.
- **Tag vocabulary canonical**: `topic/*`, `ticker/*` (UPPER), `company/*` (lowercase-kebab), `thesis/*` (lowercase-kebab) only. HALT on drift.
- **Binary decisions default** (SOTA compounding): BUY/HOLD/WATCH/AVOID; thesis CONFIRM or CHALLENGE. NEUTRAL only when signal is genuinely absent in both directions.
- **Broker-first for all market data (HARD rule; donor rule-15 port 2026-07-11)**: every price, quote, market cap, share count for cap math, 52wk range, volume, price history, and options quote -- for the TARGET, its PEERS, and the BENCHMARK -- comes from the broker MCP when its tools are present (batched calls). Web is a per-figure disclosed last resort (+ cap C5 during regular session). Detail: ref-analysis-template Sec 2.9; worker rung-0 preamble: ref-dw-topology Sec 3.
- **Confidence vs Conviction are DISTINCT fields** (see Quality Standards). Report both. Never conflate.
- **Body-preservation sha256** on every entity and peripheral UPDATE (F16 bytes compare on content outside insertion sites). **Marker-signature dedup** on claim integration: `(entity, metric, value, date)`. **Per-fact provenance**: `- <fact> (per [[<ticker>-analysis-<YYYY-MM-DD>]])`. **Machine provenance (vNEXT)**: every quantitative claim carries `prov: mcp:<server>:<key> | script:yfinance | web:<domain>+<grade>` -- the 8th INGEST-tuple field (dedup key stays the 4-tuple; spec in ref-dw-topology.md Section 7; enforced by the Wave-3 provenance skeptic + vault-audit X8 advisory). Idempotent re-runs produce zero diff.
- **Zero-new-claims short-circuit** (v2 final): if Phase K UPDATE branch finds all extracted claims already present after marker-sig dedup, SKIP the entity write entirely. Do NOT bump `updated:`. Phase P reports "entity unchanged (all N claims deduped)."
- **Symmetric back-linking**: every wikilink in a created or updated `related:` gets a reciprocal back-link on the target file.
- **Mid-batch failure**: immediate HALT (Phase N.halt), F11 stays on, no partial commit.
- **Commit discipline**: ASCII-only title + body, Co-Authored-By SUPPRESSED (F17 header-stripping grep post-commit), F14 narrow staging (explicit pathspecs only).
- Canonical frontmatter per AGENTS.md schema; user custom fields (`thesis`, `confidence`, `conviction`, `sources_count`, `accounts`, `trigger`, `scoring_path`, `orchestrator_model`, `topology`) preserved byte-exact.
- **Subagent dispatch is MANDATORY when specified by phase AND the running harness exposes an Agent tool** (E.0, J-bis.0, K-bis.0, K.5, L.0). Pre-emptive skip based on judgment ("this won't apply to crypto", "subagent might not have data", "result will be N/A") is FORBIDDEN. The subagent decides applicability via its own N/A return contract -- the parent skill dispatches and validates the return, not the verdict. Legitimate fallback fires ONLY on (a) contract violation -- subagent return missing required fields, (b) actual dispatch failure -- timeout, rate limit, tool-denial, hard subagent crash, OR (c) NO Agent tool in the running harness -- there the documented inline fallback runs VERBATIM as the NORMAL path and is reported `inline-no-Agent-tool`, which is NOT a DEVIATION. A subagent returning "Not applicable to `<asset-class>`" with empty rows + confidence: N/A is a SUCCESSFUL dispatch; propagate the N/A return verbatim into the relevant Decision Sheet section. Pre-emptive skip (an Agent tool exists and the dispatch was not attempted) surfaces in Phase P as **DEVIATION** (not "fallback"). Quality preserved by additive design: subagent dispatch never removes existing inline capability -- inline logic remains as fallback for legitimate failures only.
- **DW dispatch + resume (TOPOLOGY=dw)**: token budget via `INVEST_DW_TOKEN_BUDGET` env var (default 750K full / 500K Wave-3-skip; CALIBRATED 2026-06-10 from the 3 production Tier-A runs: 596K/555K/715K actuals, Wave-3 fire = +213K); concurrency <= 6; the main loop reads the env var and passes `args.token_budget` (the workflow sandbox has no process.env). Mid-run interruption -> resume via `Workflow({scriptPath, resumeFromRunId})`; NEVER re-run a completed wave. Full contract: ref-dw-topology.md Sections 6 + 9.

### Quality Rules (Quality Standards)

- **Confidence score**: the legacy 0-100 field is an evidence-constrained judgment score, not a measured probability that an analysis is correct. Preserve existing caps/sizing rules; report a probability only through the separately dated, outcome-defined calibration procedure with sample size and limitations. State the evidence and observable condition that would change the judgment.
- **Conviction (actionable)**: legacy 0-100 recommendation-strength index, separate from evidence confidence and win probability. Apply K.5 only with supported required inputs; otherwise report UNAVAILABLE and the missing inputs. Conviction alone never changes rating or sizing under the existing invariant.
- **Inline evidence grading**: every material claim cites tier at point of use -- `[Grade A | SEC 10-Q | 2026-04-10]`. A = primary filings, B = Tier 1 data/journalism, C = industry/analytical, D = sentiment, F = unverifiable. No Grade-D in Decision Sheet.
- **Portfolio math shown**: `<shares> x $<price> = $<value> (taxable) + <shares> x $<price> = $<value> (tax-advantaged) = $<total> combined`. EQUITY share counts come from live `mcp__robinhood-trading__get_equity_positions` at run time (hybrid rule, Phase J; all account quantities require a live broker read; unavailable asset classes remain UNVERIFIED); do not estimate. Threshold math anchors to regular_market_close (ref-dw-topology.md Section 8).
- **Temporal anchoring**: every data point has its date. Freshness: FRESH (<7d), RECENT (7-30d), DATED (30-90d), STALE (>90d, auto-downgrades evidence one letter). Flag TTM vs forward mismatches before use.
- **Risk/reward hurdle**: 3:1 minimum for BUY -- `(Target - Current) / (Current - Stop) = X:1`. Below 2:1 rejected as BUY.
- **Kill criteria quantified**: specific metric thresholds, not vague deterioration (e.g., "gross margin <45% two consecutive quarters" not "margins deteriorate").
- **2-3 sentence thesis statement** in the analysis body (distinct from frontmatter `thesis:` tags). Institutional practice: if it can't be stated in 2-3 sentences, the thesis isn't sharp enough.

## Verification Gates

HALT on failure. Gates fire: after Phase F (reporting-period consistency; TTM vs forward), after Phase I (supply-chain + competitive data <30d), after Phase J (portfolio math from actual share counts), before Phase K (Pre-Output 10-point gate below), before Phase O (sha256 body-preservation invariants on every updated file).

## Pre-Output Gate (before Phase K writes the analysis file)

Verify ALL before accepted delivery. A gap withholds the dependent conclusion and acceptance; retain supported answers in an explicitly unaccepted draft under the financial-analysis contract. Never fill missing inputs to satisfy a template.

1. Every Decision Sheet field contains supported data or explicit UNAVAILABLE with the missing input, affected conclusion and recovery condition. No silent gaps, guessed values, "TBD" or "see below".
2. All dollar amounts calculated from real share counts with arithmetic shown. Every price-type figure (target, PEERS, BENCHMARK) traces to a broker tool result or carries a per-figure fallback disclosure; every SMA/RSI/beta/vol/drawdown/correlation figure traces to technicals.py output or carries disclosure (2026-07-11).
3. Every date is exact (ISO or market-close timestamp). Not "recently" or "today".
4. No Grade-D evidence in the Decision Sheet.
5. Confidence identifies evidence quality, justification and an observable state-change condition. Label any legacy 0-100 score uncalibrated; a separate probability must meet the outcome/horizon/reference-class calibration contract.
6. **Confidence-evidence caps** (existing policy, not probability calibration): if >30% of Decision Sheet evidence is Grade C, confidence capped at 70%. If any Grade-D appears in body, confidence capped at 60%. If >2 STALE data points drive decision, confidence capped at 65%.
6a. **Cap C5 -- price provenance (vNEXT)**: if the price feeding portfolio math / R/R was non-broker (price-fetcher `broker_authoritative: false`) during `market_session == regular`, confidence capped at 60% + flag "price-unconfirmed (non-broker)" in the TRADING DECISION header. N/A outside regular session; applies to every harness with a regular-session quote (the price-fetcher v4 parent-gate contract governs re-dispatch/HALT first).
7. **Conviction is separate from confidence** and has its own rationale. Report supported values or explicit unavailability; missing probability inputs must propagate through modulation and its audit.
8. Variant view is genuinely differentiated OR explicitly marked: "No credible variant -- consensus probably right because [reason]".
9. At least one contradictory source consulted and cited in Evidence Quality.
10. Risk/Reward ratio calculated; meets 3:1 hurdle OR explicitly rejected as BUY if below 2:1; Kill criteria are specific and measurable (quantified thresholds); 2-3 sentence thesis statement present.
10a. **GATE-F sheet (judgment-gates kit, 2026-07-06)**: if the rating is an action verdict (STRONG BUY / BUY / SELL / STRONG SELL) OR the Decision Sheet carries ANY ADD/TRIM/EXIT/staged-limit order block, a same-day GATE-F sheet exists at `wiki/research/gates/` (written at K-bis.7 time per the kernel sequencing; Q.6 specifies the procedure) with verdict != BLOCKED, and its path is recorded in the analysis frontmatter `gate_f:` field. BLOCKED -> HALT (no analysis write). FOMO-SUSPECT -> proceed, but the Decision Sheet MUST carry the cooling-off-48h + tranche-cap mandates verbatim.
10b. **Sizing worksheet (INVEST KERNEL)**: when K-bis.7 fired, the worksheet (`kernel:sizing` block + rendered lines) is present and `python tools/sizing-eval.py --check <composed-tmp>` exits 0 -- run against the Phase O.0 tmp precheck copy BEFORE any vault write, ordered sizing-check THEN skill-precheck. BINDING mode additionally: the TRADING DECISION Action $ equals the worksheet `final_dollars`. Exit 2 -> fix the INPUTS and re-run `--compute`; hand-editing individual worksheet numbers is FORBIDDEN (gate-marker discipline).
10c. **Doctrine loaded, not remembered**: doctrine-lint exited 0 at D.8; `doctrine_version:` + `doctrine_fingerprint:` are stamped in the frontmatter and match the live blocks; every doctrine number cited in the body traces to the loaded blocks.
10d. **Kernel frontmatter complete**: `rating`, `price_at_analysis`, `rr_ratio`, `position_size_pct`, `doctrine_version`, `doctrine_fingerprint`, `deployment_band`, `deployment_override`, `gate_f`, `kill_criteria`, `thesis_line` all present (schema in Phase K K.5; enforced mechanically by sizing-eval --check).
10e. **Override lawfulness**: if `deployment_override` is true -- all five conditions were machine-verified by the script, a VERBATIM user directive from the current session is quoted in the disclosure, the GATE-F sheet + `thesis_line` state the macro gate is pierced and why, and the deployment state was an OBSERVABLE sub-1.0 state (never unknown-treated-halted). Any miss -> HALT.
10f. **Tax-lot gate (2026-07-11)**: on any trim/exit of a held name, the LT/ST lot split was pulled (get_equity_tax_lots per holding account) and every near-LT lot is named with its exact conversion date (ref-analysis-template 2.11). HALT otherwise.
10g. **Options block complete** (CONDITIONAL on options_layer_enabled): if K-ter produced a structure, every required field per ref-options-layer Sec 7 is populated (incl. PoP + method + basis, earnings exposure, tax note, PAPER label) and the ref's standing-limits block exists; discipline_records are exempt from PoP/basis but require their reason fields. No placeholders -> HALT.
10h. **Ledger record valid** (CONDITIONAL on options_layer_enabled): the record JSON round-trips; id collision-free; point-in-time gate passes; pop_basis == machine-criterion basis; horizon_check_date == max leg expiry; verdict_success_criterion pre-registered. (score_ledger.py --append enforces all of these fail-closed; this item asserts the append succeeded.)
10i. **NO TRADE reachable** (CONDITIONAL on options_layer_enabled): a failed screen / unmeasurable IV / earnings confound / sub-contract holding MUST have emitted NO_TRADE -- a structure forced past a failed screen HALTs; every NO_TRADE traces to a screen/IV/earnings/scale reason, NEVER a conviction value.
10j. **Initiation gates** (CONDITIONAL on an `initiation_gates:` block existing; 2026-07-30): every `class: blocking` entry satisfies G1 (`resolvable_by <= set_on + min(180d, Time Horizon)`); no monitoring-class gate is cited as the reason a BUY is blocked; G3's `No buyable path inside 60d: <blockers + earliest resolvable_by>` line is present in the Decision Sheet whenever that is true (ref-analysis-template 12.5).
10k. **R/R bracket + STOP-BREACHED (2026-07-30)**: whenever `rr_ratio` is quoted, `rr_inputs:` is complete (entry / stop / target / stop_basis / target_basis / computed_at / price_basis) AND the STOP-BREACHED rule is honored -- a prior bracket whose stop the price has reached is VOID: not cited as a rating or rejection basis, never recomputed (ref-analysis-template 7.4.1).
10l. **Target model disclosed (2026-07-30)**: whenever ref-scoring-models 10.4 governs the target (`scoring_path: negative-eps-bridge` OR EV/Sales >50x), `target_model_inputs:` discloses a supported capitalized valuation with enterprise-to-equity reconciliation; missing required inputs withhold the target and dependent R/R rather than forcing invented fields. The 40/55/70 haircut sensitivities remain disclosed historical assumptions, not calibrated probabilities, R4-D2 de-risk clause adjudicated whenever backlog + prepayments >= 1.0x TTM revenue, and TARGET-EXHAUSTED rendered per R4-D4 everywhere R/R appears (ref-analysis-template 6.1.2).
10m. **Watch zone (2026-07-30)**: whenever a WATCH zone is set or kept, the `watch_zone:` block is complete and `zone_move_reason` is non-empty -- a zone that moved with price by >= 10% vs `zone_prior` carries its anti-chase justification, never the empty string (ref-analysis-template 6.1.3).

## /invest `<ticker>`

Use WebSearch for current data with normal TLS certificate verification. On a certificate failure use another verified official source, or disclose the source as unavailable; never disable TLS verification.

### Phase 0: Vault context retrieval (NEW; Phase 3.6 -- runs BEFORE Phase A; read-only; runs in --preview)

Read-only retrieval uses an explicitly approved non-sensitive corpus, including preview mode. Let `T` be the uppercased ticker. The corpus allowlist and protected-path exclusions must be enforced BEFORE result text enters context; neither an unverified whole-vault index nor post-retrieval filtering satisfies this boundary. Phase 0 complements named Phase D reads and never authorizes account-file reads or broad personal financial snapshots.

0.1 -- Build 12 structured queries spanning the analytic surface:
`"<T>"`, `"<T> thesis"`, `"<T> risks"`, `"<T> institutional positioning"`, `"<T> insider activity"`, `"<T> catalysts"`, `"<T> regulatory"`, `"<T> competitive landscape"`, `"<T> macro/sector exposure"`, `"<T> earnings"`, `"<T> technical/price action"`, `"<T> analyst sentiment"`.

0.2 -- Use a verified retrieval adapter restricted to approved source files. If enforcement is unavailable, run `rg -n --fixed-strings -- <subject> <approved-file> ...` over an explicit file list: focal entity and named public-research/method references after scope review. Reject protected paths, `.env*`, `auth.json`, `*.local.md`, portfolio histories, snapshots, raw broker outputs and mixed personal-account corpora BEFORE reading text. No entire `wiki/`, `Calendar/` or `wiki/investing/` tree searches.

0.3 -- Dedup approved results by `path:line`; retain supplied semantic scores only (lexical matches have no invented score). Cap at 100 hits; store VAULT_CONTEXT with retrieval method and scope.

0.4 -- EMIT a visible summary (MANDATORY -- retrieval must be visible in the response):

    Phase 0 -- retrieved vault context (N hits; M from wiki/entities/tickers/)
    Top results:
      [score] path:line -- first ~80 chars of text
      ... (show up to 15)

If no approved source or hits are available, emit `Phase 0 -- no vault context retrieved` with the cause; continue with empty VAULT_CONTEXT. Never HALT on Phase 0 alone. Log `phase0_hits=N`; N=0 adds `retrieval_degraded: phase0_hits=0` to Phase P. Disclose lexical fallback.

0.5 -- Downstream consumers (these phases stay UNCHANGED; consult VAULT_CONTEXT as prior-thinking instead of re-deriving from scratch):
- Phase D (Context Load): add any entity-note / analysis paths surfaced in VAULT_CONTEXT to the D.2 read set.
- Phase J.5 (Prior-Research Comparison): seed prior-analysis + entity-drift discovery from VAULT_CONTEXT alongside the Glob -- this phase benefits MOST (it is semantic-retrieval-shaped).
- Phase J-bis (Institutional Positioning) + Phase K.5 (Variant View): cite prior institutional history + bear-case chunks from VAULT_CONTEXT.

Cite any used chunk inline as `(vault: path:line)` -- plain text, NO wikilink syntax (Phase 0 context is raw, not vault-resolved).

### Phase A: Pre-flight checks (NO F11 yet)

**U1 residency gate (orchestration economics, AGENTS.md).** Run
`python tools/run-share.py --current-context` FIRST. Exit 1 means the session is
carrying more resident context than this run should re-pay on every turn: report
the number, recommend `/clear` + re-invoke in a fresh session, and proceed only if
the operator says to. Cost basis: cache_read is ~82% of frontier cost and equals
the sum over turns of the resident prefix, so a heavy run started at 500K residency
costs multiples of the same run started fresh. This is a RECOMMENDATION, not a HALT
-- never block work the operator asked for; make the price visible before it is paid.


A.1 -- F11 collision check. If `.claude/state/auto-commit-disabled` exists, HALT: "F11 flag already set by another skill. Check: (1) any other skill running; (2) orphaned flag from a crash -- manually `rm .claude/state/auto-commit-disabled` to recover."

A.2 -- Normalize ticker input. Uppercase; strip whitespace; validate shape (1-5 letters for stocks/ETFs; crypto can be longer). HALT on empty or all-numeric input.

A.3 -- Load shared vault indexes (identical set used by /enrich + /ingest): TICKERS (`wiki/entities/tickers/*.md` stems, UPPER), COMPANIES (`wiki/entities/companies/*.md`), MOC_STEMS (`Atlas/_MOCs/*.md`), THESIS_STEMS (`Atlas/concepts/investing/theses/thesis-*.md`), ALL_BASENAMES (vault-wide wikilink resolution), BACKLINKABLE_CATEGORIES (`{concepts, sources, moc, decisions, wiki, entity, people}`).

A.4 -- Assert path-guard list. Any write targeting a guarded path HALTs.

A.5 -- Detect ticker class HINT (not definitive). Use the focal entity frontmatter or a current public issuer/exchange instrument reference. A broker read in this session may corroborate instrument type. Otherwise treat it as unknown and load applicable class references; never infer it from account files.

A.7 -- Topology detection (deterministic; NEVER halts). Native Agent/collaboration tools are usable for named roles wherever exposed; absence of the separate Workflow tool does not prohibit Codex delegation. Preserve each role contract, one integration writer, bounded retries, and authorized session settings. TOPOLOGY = `dw` iff the Workflow tool is present in the orchestrator's current session tool surface; else `sequential` (a harness exposing NO Workflow tool -- Codex CLI, headless, restricted sessions -- plus any DW regression; landing here is a harness capability gap, never a DEVIATION). Ambiguity -> `sequential` (safe fallback). `tools/lib/capability-detect.sh` (`OSANWE_DW_HINT`) is ADVISORY only -- the tool-surface check is authoritative. Record ORCHESTRATOR_MODEL = the active model string. PASSIVE LOGGING ONLY: no behavior ever branches on model identity; TOPOLOGY + ORCHESTRATOR_MODEL flow to the Phase B print, the analysis frontmatter (`topology:`, `orchestrator_model:`), and the two calibration-monitor columns (Phase R.2) so the Phase-R Brier can stratify by topology (GUARD-2 rider S1). A.7b LANE ARM (only when the operator asked -- `--local` or any sentence pairing the lane (glimmer/local/delegate) with a scope hint; DEFAULT DISARMED): run `python tools/delegate.py --check`; exit 0 -> ARMED and the legs listed by `python tools/delegate.py --legs invest` may run via `tools/delegate.py --leg <id>` (that command is the ONLY source of leg ids; NEVER-LOCAL ids are refused by the tool, exit 3); non-zero -> DISARMED, every leg runs frontier, reported in Phase P, NEVER a HALT. Two consecutive lane failures mid-run -> disarm for the remainder. One steered retry per malformed result, then frontier. Arming branches on lane AVAILABILITY, never on model identity; the standard each leg must meet is unchanged. The same consent also arms the RELAY lane for tool-bearing `research:*` legs (`python tools/relay.py --leg research:<id> --mission <spec>`, missions via `tools/relay-mission.py`; containment + exit-5 distillate consumption + mandatory relay-verify per runtime-reference "model lane"). A relay exit 5 carries a VALID distillate -- consume it (or answer the escalation and `--resume`) before deciding resume-vs-frontier; every other non-zero exit means run the leg frontier yourself.

A.8 -- Wave routing (fires after Phase D completes):
- **TOPOLOGY=sequential (Tier-B):** execute Phases E-I below verbatim -- zero behavioral difference from v2 final.
- **TOPOLOGY=dw (Tier-A):** read `ref-dw-topology.md` (sibling of this file; read-on-demand companion, same pattern as Phase K.2). Invoke the `invest-research` workflow (`.claude/workflows/invest-research.js`) with args {ticker, class_hint, held, entity_exists, prior_entity_summary, vault_context_summary, ws_budget_map: {identity:2, fundamentals:4, filings:0, competitive:6, positioning:1}, run_timestamp, token_budget, include_technicals: true, correlation_basket: [<held equity tickers>]} (the workflow threads the flag into the quote-technicals dispatch and REQUIRES the `technicals` key at convergence -- 2026-07-11). It runs Phase(Price)=price-fetcher + Wave 1 (identity-structure / fundamentals / filings-integrity / competitive-macro-risk, 4 template workers in parallel) + Wave 2a (forensic-scorer + institutional-positioning-scout via agentType) and returns the research bundle. SKIP the sequential E-I + J-bis.0 + K-bis.0 dispatches -- read their results from the bundle instead (each phase's text remains the authoritative spec of what the bundle section must contain; validate per the J-bis.0/K-bis.0 contract checks). The 13-WebSearch budget is DISTRIBUTED across workers (0/2/4/0/1/6), never expanded. Convergence gate: N/A returns = SUCCESSFUL; missing fields/dispatch failure -> one re-dispatch -> documented inline fallback (Tier-B phase text); pre-emptive skip = DEVIATION (a harness with no Workflow tool never reaches this branch -- A.7 already routed it to Tier-B). thesis-critic (K.5) + claim-distributor (L.0) stay Agent-tool dispatches in BOTH tiers wherever an Agent tool exists; with NO Agent tool they run their documented inline fallbacks as the normal path. Wave 3 verification: see K.5 STEP 4.

### Phase B: State-transition model (print only, BEFORE F11)

Emit expected-state summary to user:

    /invest state-transition model
    ==============================
    Ticker: `<TICKER>`
    Class hint: <stock | ETF | crypto | unknown -- will confirm in Phase E>
    Held: <Yes: `<N.NNN>` shares taxable + `<M.MMM>` shares tax-advantaged = `<Z.ZZZ>` combined>
          | Not currently held
    Active thesis exposure: <list of thesis tags from entity note OR hot.md>
    Entity note: <exists at wiki/entities/tickers/`<TICKER>`.md -- UPDATE branch>
                 | <absent -- CREATE branch will ground in _templates/entity.md>

    Topology: <dw (Workflow tool detected; Wave-1 fan-out per ref-dw-topology.md)
              | sequential (Tier-B; universal fallback)>
    Orchestrator model: <ORCHESTRATOR_MODEL from Phase A.7; logged passively, never branched on>
    Expected research: <sequential: 13 WebSearches across 5 phases E-I
      (2 identity + 4 fundamentals + 2 technical + 2 risk + 3 competitive-macro)>
      | <dw: 13 WebSearches DISTRIBUTED across 6 Wave-1 workers (0/2/4/0/1/6)>
    Wave 3: <required for material BUY/HOLD/SELL conclusions | required by thesis change, boundary or --verify | no material conclusion>
    Expected Phase K analysis: wiki/investing/analyses/`<ticker>`-analysis-`<YYYY-MM-DD>`.md
      Path-collision: `<none>`
                    | <same-date exists; will use -`<HHMM>` timestamped variant>
                    | <--replace requested; will overwrite>
    Expected Phase L entity update:
      CREATE: new entity at wiki/entities/tickers/`<TICKER>`.md (frontmatter + 5 sections)
      OR
      UPDATE: existing entity updated via claim-to-section mapping
              (or short-circuit if all claims deduped)
    Expected Phase M peripherals:
      <watchlist.md if BUY/WATCH>, investing-research-log.md, ref-research-insights.md (if new insight),
      <investing-moc.md if new entity>, sessions-log.md, Calendar/daily/`<today>`.md
    Expected Phase O commit (prospective): agent(invest): `<TICKER>` analysis -- <verdict TBD>
    F11 flag: will be set at Phase C (after this print, before any Edit/Write)

    Proceed? (Any failure between C and O triggers N.halt with F11 retained;
    no partial commits.)

If `--preview`: print model and EXIT CLEAN. No F11, no writes.

Else: autonomously proceed (unless --confirm opt-in).

### Phase C: F11 set

Create `.claude/state/auto-commit-disabled`. Single flag covers entire invocation. Cleared only in Phase O after commit verification passes. Skip if `--preview` already exited.

### Phase D: Context Load (READ-only)

D.1 -- Portfolio: gather current-session broker read evidence per Phase J.0.
Carry account/asset coverage, valuation time and basis caveats explicitly.
Session-stated preferences can supply interpretation, but never verify current
quantities or basis. Missing coverage remains UNVERIFIED. Do not read protected
files or historical portfolio snapshots to fill the gap.

D.2 -- Vault state:
- `Atlas/concepts/investing/macro-outlook.md`
- `Atlas/concepts/investing/watchlist.md`
- `Atlas/concepts/investing/investing-research-log.md`
- `wiki/hot.md` -- active thesis exposure
- `wiki/entities/tickers/<TICKER>.md` if exists (determines Phase L branch)

D.3 -- Reference docs (priming over searching; institutional discipline):
- `Atlas/sources/investing/ref-macro-landscape.md`
- `Atlas/sources/investing/ref-sector-benchmarks.md`
- `Atlas/sources/investing/ref-research-insights.md`
- `Atlas/sources/investing/ref-portfolio-doctrine.md` (v2 final added: invalidation rules, earnings protocol)
- `Atlas/sources/investing/ref-scoring-models.md` (v2 final added: Piotroski/Altman/Beneish methodology)
- `Atlas/sources/investing/ref-monitoring-rules.md` (v2 final added: alert thresholds)
- `Atlas/sources/investing/ref-earnings-playbook.md` (CONDITIONAL -- read whenever the ticker has an earnings print within ~45 days OR the analysis covers earnings mechanics: consensus formation, revision momentum, implied move, PEAD, beat-and-drop anatomy; thresholds as data. Serves the earnings-impact sections + the pre-earnings monitor analog; vNEXT Section 11 wiring 2026-06-10)
- `Atlas/sources/meta/ref-research-methodology.md`
- `Atlas/sources/meta/analysis-depth-standard.md`
- All three class refs loaded (cheap read): `ref-etf-evaluation.md`, `ref-crypto-landscape.md`, `ref-theme-alpha.md`. Phase E class-confirmation determines which drives synthesis.

D.4 -- Canonical-frontmatter pre-check on entity note (if exists): if `categories:` != `[entity]`, HALT and recommend `/enrich --refresh <path>` first.

D.5 -- Compute `before_sha256` of body bytes for every file Phase K, L, or M will touch -- including `wiki/investing/options-ledger.jsonl` (first-create/empty-file case: sha of empty bytes; the O.1 check for this file class is APPEND-ONLY PREFIX, not body-preservation). Cache for Phase O gate.

D.6 -- Evidence sufficiency: establish each material thesis pillar from the best available primary evidence, with independent corroboration for disputed, surprising or consequential claims. Source count and domain diversity are diagnostics, not research quotas; one decisive primary source can establish a fact. Record unresolved pillars and source limitations. A /deep prompt is a research scaffold, never evidence merely because it lists many sources. Follow docs/financial-analysis-contract.md and retain claim-level source grades.

D.7 -- `--thesis <name>` lens overlay (ADDITIVE; verdict redesign 2026-06-06). Fires ONLY when the `--thesis <name>` flag is present (name in {theme-alpha, theme-beta, theme-gamma, theme-delta, theme-epsilon}, resolving to the thesis essay at `Atlas/concepts/investing/theses/thesis-<name>.md`). The lens is a FRAMING overlay, never a replacement: first principles always runs in full. When set:
- Load the named thesis essay; extract its cohort membership + its quantified invalidation triggers.
- Weight the Phase Q coherence read toward the named thesis's cohort exposure (does this name add to or diversify the cohort).
- In Phase K, add a "Thesis-lens view" subsection: how this name looks specifically through `<name>`'s frame (cohort fit, thesis-specific kill criteria, marginal contribution to thesis concentration).
- **HARD CONSTRAINT: the lens CANNOT change the rating.** The K-bis.5 Step-1 spine sets the rating from first principles regardless of the flag; the lens only enriches the conviction rationale + the thesis-status read + the Variant View. If no flag is given, first principles runs alone (default). This guards against confirmation bias (a thesis lens that could move the rating would bias toward the named thesis).

D.8 -- **KERNEL DOCTRINE LOAD** (INVEST KERNEL 2026-07-06; read the sibling `ref-kernel-sizing.md` RUN CARD before executing). Run `python tools/doctrine-lint.py --json`. Exit 2 -> HALT the run AND CLEAR F11 (zero writes have occurred yet -- unlike N.halt, so the next run must not hit the A.1 collision); surface the findings verbatim; a human fixes the doctrine notes or ratifies via /decide. Exit 0 -> parse the `doctrine:` machine block (ref-portfolio-doctrine.md frontmatter) + the `bands:` block (ref-scoring-models.md frontmatter); record DOCTRINE_VERSION (`pd-<v>/fb-<v>`) + DOCTRINE_FINGERPRINT (`python tools/doctrine-lint.py --fingerprint`) for the analysis frontmatter. EVERY doctrine number cited anywhere in this run (concentration ceilings, deployment bands, R/R hurdles, haircuts, win-prob, forensic red-bands) MUST come from these loaded blocks -- never from memory and never from this file's illustrative text. Acquire the deployment series now (raw series; script-evaluated at K-bis.7, never model-asserted): DFII10 last ~90 obs (the GATING series) + DGS10 over the same window (confirm screen + disclosure + the smoothed 63-session Rf -- the 10Y LEVEL is NOT a gate, retired 2026-07-30) + VIX last 5 obs via mcp:fred (`fred_get_series` DFII10 / DGS10 / VIXCLS); fallback ladder + provenance-trust rules per the ref-kernel-sizing.md inputs form (non-mcp/script yield can never earn full deployment; VIX unavailable -> unknown-treated-halted, DFII10 unavailable -> rate-unknown-caution 0.5).

### Phase E: Identity and Structure (2 searches) [Tier-B; Tier-A: `identity-structure` worker per A.8]

Confirm the security's identity and structure against the E.0 price/technicals return, then run the 2 WebSearches; the contract is the `Establish definitively` list below.

#### Phase E.0: DELEGATED dispatch to `price-fetcher` (broker-authoritative price + technicals; v3 wiring 2026-06-04; v4 contract) [Tier-A: bundle `price` from the quote-technicals worker -- do not re-dispatch]

ADDITIVE -- dispatch BEFORE the 2 Phase E WebSearches, where the harness exposes an Agent tool. Use the Agent tool with subagent_type `price-fetcher`, input `{equities: ["<TICKER>"], crypto: [], include_technicals: true, correlation_basket: [<up to 8 held equity tickers>]}` (crypto-list instead + no flag for a crypto ticker; Tier-A passes the same flag via the A.8 workflow args). On success: use the returned `price` (broker-authoritative when `broker_authoritative: true`) + `extended_hours_*` for the TRADING DECISION header (Phase K-bis); the `technicals` panel (tools/technicals.py over the broker historicals; contract ref-analysis-template 2.9) seeds Phases G/H + the GATE-F `move_5d_pct` marker (`5_session`, prov script:technicals) + the K-ter realized-vol input; `correlation_matrix` feeds the Phase J `corr_gt_threshold_flag`; `next_earnings` seeds K-ter earnings exposure. Panel degraded (`technicals: null` + failures[] entry) -> fetch-prices.py subset -> Phase G WebSearch with per-figure disclosure. STILL run the 2 Phase E WebSearches for 52-week range / YTD / split-adjustment context + company identity -- the 13-WebSearch research-spine count is UNCHANGED. On dispatch failure, on a harness with NO Agent tool, or Codex/headless/MCP-absent: proceed with the Phase E price WebSearch unchanged as the fallback (with the fetch-prices.py subset for the technicals panel per the degraded path above), reported `price-fetcher: inline-no-Agent-tool` on a non-dispatching harness -- never a DEVIATION. The TRADING DECISION header notes the AH price when material (>= AH-mover threshold).

Establish definitively:
- Security type (stock / ETF / fund / cryptocurrency) -- confirms Phase A.5 hint
- ETF: fund family, inception, AUM, expense ratio, benchmark, top 10 holdings + weights, total holdings count, overlap with held ETFs
- Stock: company overview, sector, industry, market cap tier
- Current price with freshness timestamp, 52-week range, YTD performance
- Stock-split adjustment: if split occurred <90 days ago, show pre-split + post-split prices explicitly
- Most important fresh catalyst with exact dates

### Phase F: Fundamental Analysis (4 searches) [Tier-B; Tier-A: `fundamentals` worker per A.8]

Execute per the sibling `ref-analysis-template.md` Metrics Catalog. Forward estimates: FMP-first with disclosed proxy fallback -- runtime tool discovery, price/EV side stays the broker (ref 2.10). Crypto: majors evidence stack, forensics undefined-never-forced (ref 4.6).

Stock categories: valuation (P/E, P/S, EV/EBITDA, PEG, FCF yield, shareholder yield); profitability + quality (margins + trends, ROIC, ROIC vs WACC, cash conversion, Piotroski F-Score per ref-scoring-models methodology, Altman Z-Score); growth (revenue + EPS + FCF CAGRs, Rule of 40); balance sheet (net debt/EBITDA, coverage, current ratio, maturity schedule); capital allocation (buyback 3yr, dividend + payout, CapEx % revenue, insider 12mo); forensic (Beneish M-Score per ref-scoring-models, Cash Conversion Cycle + 3yr trend, revenue quality, SBC dilution flag if SBC/Revenue >5%); advanced return decomposition (ROIC decomp NOPAT x Turnover, DuPont 5-factor, ROIIC, customer concentration from 10-K).

ETF categories: expense ratio vs category, tracking error, premium/discount to NAV, turnover, tax efficiency, factor exposures (value/momentum/quality/size/volatility), top-10 concentration, sector allocation, weighted P/E + P/B + ROE, flows (1mo/3mo/12mo), liquidity + bid-ask spread, overlap with SPY/VOO.

Crypto categories: tokenomics + supply schedule, on-chain activity, staking/validator dynamics, theme-beta alignment (if applicable), regulatory exposure, exchange listings + liquidity.

Gate: reporting-period consistency (TTM vs forward).

### Phase G: Technical and Momentum (2 searches) [Tier-B; Tier-A: quote-technicals + competitive-macro-risk workers]

TRACEABILITY (Pre-Output item 2 extension): every SMA/RSI/beta/vol/drawdown/correlation figure traces to the technicals panel (prov script:technicals) or carries a per-figure web-fallback disclosure -- never model-estimated.

- 50-day + 200-day SMA position, golden/death cross
- RSI (14-day), MACD signal, relative strength vs S&P 500 (6-month)
- Volume: accumulation or distribution
- Key support + resistance levels
- Short interest ratio + days to cover
- Options intelligence: equity-only put/call ratio, IV percentile/rank vs 52-week, unusual activity (>$500K notional blocks, sweep orders)

### Phase H: Risk Assessment (2 searches) [Tier-B; Tier-A: competitive-macro-risk + filings-integrity workers]

- Annualized volatility (1yr + 63s), maximum drawdown from peak with dates, beta vs S&P 500, portfolio correlations -- ALL from the technicals panel / --matrix (Phase E.0), never narrative
- Sharpe (1yr + 3yr), Sortino
- Tail risk: scenarios causing 30%+ drawdown
- Advanced: Calmar (return / max DD), return distribution (skewness, kurtosis), factor exposure decomposition (Market/Size/Value/Momentum/Quality), scenario-based VaR at 2-sigma + 3-sigma from actual position size

### Phase H.2: Advanced Risk Metrics -- Short Interest + Options Flow (subsection of Phase H)

Execute per the full output contract in `ref-analysis-template.md` Section 6.4 (relocated 2026-07-11): H.2.1 short-interest deepening (SI %, days-to-cover, threshold logic, 4wk trend), H.2.2 options-flow intelligence (P/C by DTE window, IV term structure, unusual activity, gamma concentration; prefer the K-ter option-quote reads where loaded), H.2.3 insider cross-check. Thresholds live in the ref, verbatim from this section's pre-relocation text.

### Phase I: Competitive and Macro Context (3 searches) [Tier-B; Tier-A: competitive-macro-risk worker incl. edgar_compare peer-XBRL + FRED]

- Competitors or alternatives; moat (stocks); 2-3 alternative ETFs (ETFs)
- Macro sensitivity: rates, recession, inflation, regime -- CONTEXT ONLY: macro never gates the rating, and deployment SIZE is script-computed at K-bis.7 from raw series, never from this read
- Sector tailwinds/headwinds, regulatory risks
- Supply chain (semis priority): TSMC node utilization, HBM capacity + yield, CoWoS, equipment delivery, wafer pricing, book-to-bill
- Event-driven: 13D/13G at 5%, pending M&A/spin-off/restructuring
- Management quality: insider cluster buying (3+ in 30 days), governance flags, capital-allocation track
- Cross-asset: CDS spread trends, currency exposure by geography

Gate: supply-chain + competitive data within 30 days.

### Phase J: Portfolio Fit (hybrid live positions, vNEXT 7.4)

- **J.0 -- Live account evidence (all harnesses):** discover available broker read tools and pull current quantities for every relevant account and asset class. Reconcile per-position values, cash and account totals from that runtime evidence. Unavailable account/asset-class coverage remains UNVERIFIED; report the known subtotal and missing denominator, never a private-file fallback or an assumed zero. Cost basis and lot claims also require authoritative read evidence; absent it omit P&L/tax sizing. Never read private/ or *.local.md into research context. No order tools. Follow docs/financial-analysis-contract.md.
- **J.0b -- Price anchoring:** ALL threshold math (J sizing + Q concentration) uses regular_market_close from the price-fetcher/quote-technicals return, per the ratified extended-hours doctrine. Live/AH values may be DISPLAYED with an as-of stamp; they NEVER feed a doctrine threshold.
- Exact math: `taxable shares x price = $X + tax-advantaged shares x price = $Y = $Z combined`. Dollar impact of scenario shown.
- Apply current-session constraints and supported corporate-action/basis caveats. Never report P&L for a position whose cost basis is not positively established. If basis integrity is unverified, omit P&L; verify split-adjusted shares and prices before multiplying them.
- State "Not currently held" only after complete current-session account coverage establishes absence; otherwise state "Holding status UNVERIFIED".
- Correlation with existing holdings. Flag any pairwise correlation >0.7 (hidden concentration).
- Sector overlap; holdings overlap (ETFs).
- Position sizing: DEFERRED to K-bis.7 (INVEST KERNEL sizing worksheet -- doctrine block + `tools/sizing-eval.py`; Half-Kelly two-form, script-computed, never hand arithmetic). In Phase J record ONLY the pairwise-correlation >0.7 flag (it feeds the worksheet's `corr_gt_threshold_flag` input).
- Marginal risk contribution to portfolio volatility.
- Risk/reward shown: `(Target - Current) / (Current - Stop) = X:1`. 3:1 minimum for BUY.
- Best alternative use of capital (closest benchmark, peer, or current holding, with explicit R/R comparison).
- **TRIM/EXIT asks (2026-07-11)**: run the tax-lot pass per ref-analysis-template 2.11 -- `get_equity_tax_lots` per holding account, LT/ST split, near-LT lots named with exact conversion dates, wash-sale flag, disposition-effect check. Enforced at Pre-Output 10f.
- **On GATE-F FOMO-SUSPECT (buy/add)**: pull `get_pnl_trade_history` filtered to the symbol; any prior realized round-trip is stated with its number (informs the single K.5 behavioral mode's probability).

Gate: portfolio math from actual share counts (live MCP positions when available; hybrid-reconciliation assert run).

### Phase J-bis: Institutional Positioning -- 13F + Politician + Insider (audit 2026-04-28 5th-pass)

J-bis.0 -- DELEGATED dispatch to `institutional-positioning-scout` subagent (PREFERRED path; Phase C wiring 2026-05-02):

**MANDATORY when the running harness exposes an Agent tool** (per Execution Rules): dispatch first, no pre-emptive skip. Subagent handles N/A returns gracefully (e.g., crypto inputs -> empty Dataroma/CapitolTrades/OpenInsider rows + confidence: N/A; that is a SUCCESSFUL dispatch, not a failure).

Use the Agent tool with subagent_type `institutional-positioning-scout`. Pass input: `{ticker: "<TICKER>"}`. The subagent handles Dataroma + CapitolTrades + OpenInsider in parallel internally and returns a structured positioning table + 3-line synthesis + freshness check + HIGH/MED/LOW confidence directly.

Validate subagent return:
- Markdown table with columns [Source | Signal | Date | Magnitude | Tier | Notes] -- exact column count
- 3-line cross-source synthesis present
- Composite freshness rating present (HIGH if all <30d, MED if 30-90d, LOW if >90d)
- Confidence rating present (HIGH if 2+ Tier-A sources directionally agree; MED/LOW per scout discipline)

On contract violation OR dispatch failure (timeout, rate limit, tool denial): after one re-dispatch, fall through to the J-bis.1-J-bis.4 inline fallback -- **relocated verbatim to `ref-dw-topology.md` Section 10** (read on demand at fallback time; Dataroma 13F overlay + CapitolTrades STOCK Act overlay + OpenInsider cluster-buy detection + the mandatory Decision Sheet output table). The fallback is reachable from BOTH tiers; its semantics are unchanged. Surface fallback in Phase P audit report: "Phase J-bis subagent dispatch failed (`<reason>`); used inline fallback per ref-dw-topology.md Section 10. Quality preserved; latency penalty ~30s." On a harness with NO Agent tool that same Section-10 inline logic is the NORMAL path, reported `inline-no-Agent-tool` -- never a DEVIATION.

On dispatch success: paste returned table verbatim into Decision Sheet J-bis section. Skip the Section-10 inline logic; proceed directly to J-bis.5 cross-vector reconciliation rule (the +5pp confidence boost for multi-vector confirmation still applies, computed from subagent's table). [Tier-A: the `positioning` worker result in the A.8 bundle satisfies J-bis.0 -- validate the same contract, do not re-dispatch.]

J-bis.5 -- Cross-vector reconciliation: when Dataroma + OpenInsider both fire positive (multi-vector confirmation), thesis confidence can exceed standard caps by +5pp; when Dataroma + OpenInsider both fire negative, treat as Grade-A overriding-bearish-signal regardless of fundamental thesis strength.

Gate: institutional positioning data within 90 days for 13F (Q+45d lag); within 30 days for OpenInsider (real-time Form 4 filings).

### Phase J.5: Prior-Research Comparison + Inconsistency Detection (audit 2026-04-28 5th-pass; compounding loop)

J.5.1 -- Read prior research artifacts:
- Entity note: `wiki/entities/tickers/<TICKER>.md` (if exists; from Phase D.2)
- Prior analyses: `wiki/investing/analyses/<ticker>-analysis-*.md` sorted by date descending
- Cross-references: any `Atlas/concepts/investing/theses/*.md` mentioning the ticker

J.5.2 -- Material-claim contradiction detection:
- For each major thesis pillar in current analysis (composite score, valuation tier, conviction direction, BUY/SELL/HOLD rating), check whether prior analyses made a CONTRADICTING claim
- Categories of drift:
  - **Thesis drift**: prior thesis CONFIRM -> current CHALLENGE (or vice versa)
  - **Confidence drift**: > 10 percentage point change in confidence
  - **Conviction drift**: > 1 tier change in conviction (e.g., 4/5 -> 2/5)
  - **Metric drift**: significant change in forensic scores (Piotroski +/-2, Altman crossing 1.81 or 2.99 thresholds, Beneish crossing -1.78 or -2.22)
  - **Rating drift**: BUY -> HOLD -> SELL or reverse
  - **Kill-criteria approached**: did the prior analysis specify a kill criterion that current data brings within 10% of trigger?

J.5.3 -- Mandatory output: "Inconsistencies vs Prior Research" table in Decision Sheet:
```
| Date | Prior Source | Prior Claim | Current Finding | Drift Direction | Severity | Action |
|---|---|---|---|---|---|---|
| 2026-04-13 | nvda-analysis-2026-04-13 | Piotroski 7/9 | 5/9 | DEGRADATION | Material | Update entity Recent section |
| 2026-04-13 | nvda-analysis-2026-04-13 | Confidence 82% | 67% | -15pt | Material | Note in conviction shift |
| 2026-04-27 | <TICKER> entity note | Thesis CONFIRM | CHALLENGE | INVALIDATION-WARNING | High | Trigger /challenge thesis-<slug> |
```

J.5.4 -- Inconsistency-Log accumulation in entity note (compounding mechanism):
- Phase L Entity UPDATE writes detected inconsistencies into entity note's "## Inconsistency Log" section (CREATE section if absent)
- Format: dated entry per inconsistency: `### YYYY-MM-DD -- <metric>: prior <X> -> current <Y> (severity <Material|Minor|High>)`
- Log accumulates across analyses; future /invest invocations read this log in J.5.1 to detect REPEATED drift patterns (e.g., Piotroski has degraded across 3 consecutive analyses = sustained quality erosion, not noise)

J.5.5 -- Empty-prior-research short-circuit: if entity note absent AND no prior analysis exists, skip J.5.2-J.5.4. First-analysis tickers have no prior to compare against. Note in Decision Sheet: "Initial analysis; no prior research to compare; baseline established."

J.5.6 -- **PRIOR CALLS SCOREBOARD** (INVEST KERNEL 2026-07-06; mandatory when any prior analysis exists; MECHANICAL extraction only -- inference is FORBIDDEN). For each prior analysis in the J.5.1 set (newest first, cap 8):
- rating: frontmatter `rating:` if present (kernel analyses >= 2026-07-06); else the FIRST regex match `^\*\*Rating\*\*: (STRONG BUY|BUY|HOLD|SELL|STRONG SELL|NR)` inside the `## TRADING DECISION` section; no match -> render the literal `unparsed`.
- price_at_analysis: frontmatter `price_at_analysis:` if present; else `unparsed` (NEVER recomputed or recalled from memory).
- ret_3mo: the `wiki/investing/calibration-monitor.md` row keyed (date, ticker); blank or absent -> `open`.
- verdict: `right` iff the realized ret_3mo sign agrees with the rating direction (RATING_PROB_MAP semantics: BUY-family expects >0, SELL-family expects <0; HOLD/NR -> `n/a`); `wrong` iff it disagrees; `open` while unrealized.
Emit in the Decision Sheet: `| date | rating | price_at_analysis | ret_3mo | verdict |` plus ONE reconciliation sentence per `wrong` row (what the prior call missed). This is the thesis-journal calibration read -- the vault auditing its own hit rate.

J.5.7 -- **INHERITED-GATE SWEEP (G2; 2026-07-30)**: re-test every `initiation_gates:` entry carried in from the J.5.1 prior analyses against TODAY -- any `class: blocking` gate past its `resolvable_by` unresolved, or now exceeding G1 (`resolvable_by <= set_on + min(180d, this analysis's Time Horizon)`), is RE-CLASSED to monitoring for this run and logged as an Inconsistency-Log row (ref-analysis-template 12.5; enforced at Pre-Output 10j).

Gate: if any High-severity drift detected, surface as explicit warning in Decision Sheet BEFORE the BUY/SELL/HOLD rating is generated. Material-severity drift goes in entity Inconsistency Log without blocking.

### Phase K-bis: Quantitative Scoring Stack + Best-Investor Framework Rotation + TRADING DECISION header (audit 2026-04-28 5th-pass)

Phase K-bis reads `Atlas/sources/investing/ref-valuation-methodology.md` (reverse-DCF / implied-expectations method + the formalized EV/Sales-2D grid) for the composite valuation leg AND the forward-earnings bridge valuation (EV/Sales-2D factor per ref-scoring-models Sec 10.3); vNEXT Section 11 wiring 2026-06-10.

K-bis.0 -- DELEGATED dispatch to `forensic-scorer` subagent (PREFERRED path; Phase C wiring 2026-05-02):

**MANDATORY when the running harness exposes an Agent tool** (per Execution Rules): dispatch first, no pre-emptive skip. Subagent handles N/A returns gracefully (e.g., crypto/non-equity inputs -> all 12 metrics N/A + framework verdicts "Not applicable" + confidence: N/A; that is a SUCCESSFUL dispatch, not a failure).

[Tier-A: the `forensic` worker result in the A.8 bundle satisfies K-bis.0 -- validate the same contract, do not re-dispatch.] Use the Agent tool with subagent_type `forensic-scorer`. Pass input: `{ticker: "<TICKER>"}`. The subagent computes the Top-12 forensic stack (Piotroski/Altman/Beneish/Greenblatt/ROIC/FCF/PEG/SBC/GM-trend/accruals/capex-rev) from SEC primary + stockanalysis.com secondary; returns scorecard table + framework verdicts (Buffett/Lynch/Greenblatt/Burry) + restatement check + composite confidence.

Validate subagent return:
- 12 metrics present in scorecard table, each with HIGH/MED/LOW confidence rating
- Framework verdicts explicit PASS/FAIL across Buffett-compounder / Lynch GARP / Greenblatt magic / Burry deep-value
- Restatement check non-empty (even if "none")
- Composite confidence rating present

On contract violation, dispatch failure, OR a harness with NO Agent tool: fall through to the K-bis.1 inline fallback below -- on a non-dispatching harness it is the NORMAL path, reported `inline-no-Agent-tool` (never a DEVIATION). Surface in the Phase P audit report.

On dispatch success: use the returned 12-metric scorecard as K-bis.1 forensic-quantitative leg. The framework verdicts feed K-bis.3 reconciliation (50% forensic / 50% framework rotation per existing rule). Skip the inline forensic computation in K-bis.1; proceed to K-bis.2 framework rotation (which remains main-thread because it requires reading `ref-investor-frameworks-2026.md` and applying 3 frameworks per ticker category -- not subagent-shaped).

K-bis.1 -- Quantitative scoring stack (FALLBACK; runs only if K-bis.0 failed):
- Piotroski F-Score: 0-9 numeric value with component breakdown (profitability 4 + leverage/liquidity 3 + operational efficiency 2). Losses are not an eligibility exclusion: the original high book-to-market sample includes loss firms, and positive ROA is one signal. Keep original F-score applicability separate from the local composite/bridge routing; see docs/financial-analysis-contract.md.
- Altman Z-Score: numeric value with zone classification (safe > 2.99 / grey 1.81-2.99 / distress < 1.81)
- Beneish M-Score: numeric value with manipulation classification (likely manipulator > -1.78 / acceptable < -2.22)
- Reverse DCF implied growth rate: solve for revenue growth that justifies current price; compare to consensus 5-year forward CAGR (Rf = the smoothed 63-session DGS10 average per ref-scoring-models, stamped with its computation date; never a hardcoded literal and never the live daily print)
- Greenblatt Magic Formula combined-rank: rank vs sector universe on ROIC + EBIT/EV; top-quintile = strong; bottom-quintile = caution
- DuPont 5-factor decomposition: ROE = (net income / pretax income) x (pretax income / EBIT) x (EBIT / revenue) x (revenue / average assets) x (average assets / average equity). Reconcile periods and bases; undefined denominators or non-operating firms require a disclosed alternative
- Composite Quality Score 0-100: 30% Piotroski (normalized) + 20% Altman (normalized) + 20% Beneish (normalized inverse since lower is better) + 15% ROIC (normalized vs sector) + 15% valuation (FCF yield + EV/EBITDA percentile)
- **EPS<0 FORWARD-EARNINGS BRIDGE (routing -- runs for ALL names BEFORE scoring_path is set; ratified 2026-06-07, [[ref-scoring-models]] Section 10):** if trailing TTM OPERATING income < 0, route per Section 10 -- substitute the bridge forensic composite (growth-quality 5-factor: revenue-growth 25% + GM level/trend 20% + cash-runway 20% + path-to-profitability 20% + EV/Sales-2D 15%; Altman dropped to the solvency gate) and the Pre-Profit Grower framework category ([[ref-investor-frameworks-2026]] Sec 13: Druckenmiller/Cohen/Marks). MASTER INVARIANT: positive-eps-standard is reachable ONLY when TTM operating income >= 0 -- a loss-maker NEVER runs the standard composite. FENCES: TTM revenue <$20M OR EV/Sales >100x -> pre-revenue guard (composite N/A, rating NR); cyclical (declining-revenue OR sign-mixed op-income lookback: >=1 loss FY AND >=1 positive-op-income FY in the last 4 FY -- the RECOVERED-cyclical/loss-trough read per ref-scoring-models Sec 10 intent) -> STEP 2a: if still op-income>=0 standard path + MANDATORY mid-cycle-margin note (HALT if absent from analysis body; Wave-3 routing skeptic checks this), if op-income<0 bridge w/ cyclical caveat (v2 normalized-earnings bridge deferred); any TTM op-income<0 -> bridge (the -5% trailing-4Q-avg-op-margin band is HYSTERESIS-ONLY -- it governs RETURN to standard, which requires op-income>=0, never letting a loss-maker through). NBIS-trap: GAAP NI>0 but op-income<0 forces the bridge. Apply the data-integrity gate (Sec 10.2: use CURRENT shares not TTM weighted-avg; sum 4 quarters if any TTM line >4x max quarter). Valuation/target = EV/Sales + path-to-profitability; for EV/Sales >50x, R/R target = MIN(analyst PT, fundamentals fair value). Whenever that fundamentals-FV formula governs (this path OR EV/Sales >50x), the `target_model_inputs:` disclosure contract in ref-analysis-template 6.1.2 is MANDATORY -- a supported capitalized valuation and enterprise-to-equity bridge with sourced inputs, 40/55/70 sensitivity labelled historical assumptions, the R4-D2 de-risk adjudication, and R4-D4 TARGET-EXHAUSTED handling; unavailable inputs require a withheld target and withheld target-dependent R/R, never the superseded revenue-times-margin recipe (enforced at Pre-Output 10l). Record `scoring_path` in analysis frontmatter. **When op-income >= 0 this NOTE is INERT and the formula above runs VERBATIM (byte-identical positive-EPS output).**

K-bis.2 -- Best-Investor Framework Rotation per `Atlas/sources/investing/ref-investor-frameworks-2026.md`:
Investor agreement and the reference's 25% margin-of-safety statement are unverified synthesis, not universal calibrated policy. Keep the existing owning score/gate thresholds; refresh dated valuation inputs and identify assumptions rather than treating reference examples as current facts.
- Determine ticker category: compounder / fast grower / cyclical / deep value / macro narrative / activist / distressed / special situation / ETF / crypto
- Apply primary framework (5 checks): score each pass/fail/partial
- Apply secondary framework (5 checks): same scoring
- Apply tertiary framework (5 checks): same scoring
- Composite framework score: 50% primary + 30% secondary + 20% tertiary, normalized to 0-100
- Material disagreement check: if primary recommends BUY and secondary recommends SELL, surface in Decision Sheet for explicit reconciliation before rating

K-bis.3 -- Reconcile quantitative scoring stack (K-bis.1) with framework rotation (K-bis.2):
- Both scores should agree directionally
- Material disagreement (>30 point composite spread) requires explicit surfacing in Decision Sheet
- Final composite quality score: 50% K-bis.1 (forensic-quantitative) + 50% K-bis.2 (framework-rotation)

K-bis.4 -- TRADING DECISION header generation (mandatory at top of analysis body, before existing Decision Sheet):

```markdown
## TRADING DECISION

**Rating**: <STRONG BUY | BUY | HOLD | SELL | STRONG SELL>
**Action**: <Initiate $X / Add $X / Trim $X / Hold / Exit / Avoid>
**Confidence**: <HIGH|MED|LOW> with reasons; optional legacy <X/100> uncalibrated judgment score and binding cap
**Conviction**: <X/100 or UNAVAILABLE with missing inputs> (when supported, K.5 Step 2 base <Y> minus failure-mode penalty <Z>, floored at 20; separate from confidence and sizing)
**Time Horizon**: <3-6mo | 12mo | 24mo+>
**Risk/Reward**: <X:1> (passes/fails 3:1 hurdle for BUY, 4:1 for STRONG BUY) | ALT FORM when `target_model_inputs.target_state` is TARGET-EXHAUSTED: `TARGET-EXHAUSTED (sizing target $X <= price $Y; R/R undefined, not failed)` -- the rating rationale then rests on composite / gates / solvency and NEVER on "R/R fails" (ref-analysis-template 6.1.2 R4-D4)
**Composite Quality Score**: <X/100> (forensic 50% + framework 50%)
**Validation status**: <on BUY/STRONG BUY during the calibration window> MECHANISM-VALIDATED, not outcome-validated -- report Phase R's realized count and comparable-pair coverage. Conviction never controls sizing under the K.5 invariant. Eight realized calls alone do not establish outcome quality; disclose missing comparisons and any unresolved monitor condition without using the historical expected completion date as current evidence.

**Summary** (3-5 sentences synthesizing the analysis): <one-paragraph thesis statement covering: what the company does + key catalyst + valuation + main risk + position sizing recommendation. Written for a portfolio manager who has 30 seconds to make a decision.>
```

K-bis.5 -- Rating logic: STEP 1, FIRST-PRINCIPLES RATING (the spine; verdict redesign ratified 2026-06-06, invest-verdict-redesign-brier-backtest-2026-06-05).

The rating is a deterministic function of DATA: (a) composite quality score (K-bis.3, 0-100), (b) R/R vs hurdle [HARD gate], (c) valuation/mispricing read, (d) catalyst proximity + direction, (e) the THESIS-STATUS GATE. The adversarial counter-thesis (Phase K.5) does NOT veto this rating -- it routes to conviction + kill-criteria + thesis-status per Step 2-3. Tier thresholds (5-tier scale; thresholds UNCHANGED from prior design -- these are the hard gates that contain over-bullish regression):

- STRONG BUY: composite >= 80 AND R/R >= 4:1 AND multi-vector signal (Dataroma + OpenInsider both positive) AND thesis != INVALIDATE
- BUY: composite 60-79 AND R/R >= 3:1 AND thesis != INVALIDATE
- HOLD: composite 40-59 OR thesis-intact-but-no-edge OR composite 60-79 but R/R < 3:1 OR thesis == INVALIDATE
- SELL: composite 20-39 OR kill-criteria approached (within 10% of trigger)
- STRONG SELL: composite < 20 OR kill-criteria triggered OR multi-vector negative signal (Dataroma reduce + insider selling + bearish Phase J.5 drift)
- HOLD-BAND DISCIPLINE (OSANWE-V2 SOTA pass; falsifiability): every HOLD rating MUST emit `hold_band:` frontmatter -- "[up_pct, down_pct] pct vs price_asof through +63 trading days" -- derived from the SAME data the rating used: upper bound = nearest resistance/valuation ceiling or +half the R/R reward leg, lower bound = kill-stop proximity or -1.5x recent daily sigma, whichever binds first. Rationale: an unbanded HOLD is unfalsifiable and ungradeable (the calibration engine measured 41/54 legacy HOLDs with no testable claim). The band is a COMMITMENT, not a hedge; grading treats in-band as correct. BUY/SELL omit the field (their verdicts grade directionally).

**TIER PRECEDENCE (applies ONLY when 2+ tiers' conditions are simultaneously met; then apply the MOST BEARISH tier met, in order STRONG SELL > SELL > HOLD > BUY > STRONG BUY):** a DATA-gated SELL/STRONG SELL (composite-band, kill-criteria-approached/triggered, thesis-INVALIDATE-with-deserved-SELL, multi-vector-negative) ALWAYS overrides a HOLD that arises only from the composite-40-59 band or the R/R<3:1 demotion. A composite-band HOLD must NEVER silently suppress a deserved SELL. (Strategist-ratified 2026-06-06 closing a pre-existing latent hole under the GUARD-1 mandate; bearish-direction-only -- can move a verdict from HOLD toward SELL, can NEVER create a wrong BUY.)

**THESIS-STATUS GATE (Step 1e):** bites the rating ONLY on a DATA condition, never on "a coherent bear case exists":
- INVALIDATE -> rating UPSIDE capped at HOLD (downside fully open); SELL/STRONG SELL FIRE per the data-gate rows when their conditions are met -- INVALIDATE never blocks a deserved SELL. Note the resolution of the latent contradiction: INVALIDATE is defined as a TRIGGERED kill criterion, and the STRONG SELL row fires on kill-criteria-triggered -- so an INVALIDATE'd name with a triggered kill criterion resolves to STRONG SELL (via the TIER PRECEDENCE rule above), not capped at HOLD.
- kill criterion WITHIN 10% of trigger -> SELL (the existing K-bis.5 data rule).
- CHALLENGE / CONFIRM -> NO rating cap (informational only; feeds conviction + Variant View, not the rating).
- **Machine-trigger citation (thesis machine-triggers schema v1; Block-A ratified 2026-07-04):** when the analyzed ticker's thesis essay carries a `triggers:` frontmatter block, this gate CITES trigger ids + fired-state machine-readably (e.g. `theme-alpha: themealpha-amber-capex-guide-down not-fired; themealpha-kill-concentration-70 not-fired [<pct> vs <line>]`) instead of free-prose trigger reasoning. Gate semantics UNCHANGED; zero behavior change when the block is absent (back-compat). /invest NEVER writes `fired:` (Pattern-20; write-back rides /decide).

**SOLVENCY-RUNWAY GATE (Step 1f; SCORED gate -- fires ONLY when scoring_path == negative-eps-bridge; on the positive-EPS path runway is NOT computed so this never evaluates -- INERT, additive, bearish-direction-only, can NEVER create a wrong BUY; ratified 2026-06-07 per [[ref-scoring-models]] Section 10):** runway < 4 quarters AND no committed financing -> rating UPSIDE capped at HOLD (downside fully open); runway < 2 quarters -> SELL (distress); runway 4-8 quarters AND composite >= 60 -> BUY allowed with a "runway-constrained; next raise is a kill-criterion" note. Pre-revenue / negligible-revenue names -> rating NR (no rating, narrative-only; NOT a 6th tier), or SELL if runway < 12mo. The existing tiers + TIER PRECEDENCE + THESIS-STATUS GATE above are preserved VERBATIM; this is an added guarded clause.

**GUARD-1 -- the bearish/trim side is DATA-driven and survives the veto removal.** SELL and STRONG SELL fire on their own DATA gates (composite 20-39, kill-criteria-approached, kill-criteria-triggered, thesis INVALIDATE, multi-vector-negative) -- these are INDEPENDENT of the Phase K.5 conviction modulator and were never part of the removed veto sentence (enforced by the TIER PRECEDENCE rule above: a data-gated SELL/STRONG SELL is never suppressed by a composite-band HOLD). Removing the narrative veto does NOT weaken the skill's ability to say SELL/TRIM; it only stops a plausible-but-untriggered bear narrative from auto-downgrading an otherwise-rateable BUY. Phase Q concentration-trim (theme-alpha tiered 60/70 + single-name 30/35 per ref-portfolio-doctrine; interim 50% amber phase-in) is a separate, untouched pathway. **SINGLE-NAME-BUY TRIPWIRE:** if any analysis of a tripwire-listed name (one whose R/R has not cleared the 3:1 hurdle in any backtested call) ever rates BUY or STRONG BUY, HALT and surface for review -- such a BUY signals a gate defect, not a thesis change.

K-bis.6 -- Framework Rotation Audit Trail (placed after TRADING DECISION header, before Decision Sheet):

```markdown
### Framework Rotation Audit (Phase K-bis)

**Category**: <compounder/fast-grower/cyclical/deep-value/macro-narrative/activist/distressed/special-situation>
**Primary Framework**: <Buffett/Lynch/etc> (<X/5> checks pass)
**Secondary Framework**: <Munger/Greenblatt/etc> (<X/5> checks pass)
**Tertiary Framework**: <Lynch/Cohen/etc> (<X/5> checks pass)
**Composite Quality Score**: <X/100>
**Forensic-Scoring Agreement**: Piotroski <X/9>; Altman Z <X.X>; Beneish M <-X.X> -- <agreement|disagreement> with framework-rotation directional <BUY|HOLD|SELL>
**Reconciliation**: <explicit reconciliation if material disagreement; "no material disagreements" otherwise>
```

Gate: TRADING DECISION header + Framework Rotation Audit Trail BOTH mandatory. HALT before Phase K Compose if either is missing.

K-bis.7 -- **POSITION SIZING WORKSHEET** (INVEST KERNEL 2026-07-06; procedure, forms, fill rules, golden example: `ref-kernel-sizing.md` -- READ IT). Fires: (a) BINDING mode iff the Step-1 rating is BUY or STRONG BUY with an Initiate/Add action; (b) HOLD-STATE mode (doctrine-compliance panel, no Kelly) for any HELD name at any other rating; skipped for non-held HOLD/SELL/AVOID (report the skip in Phase P).
- **GATE-F sequencing** (kernel path; supersedes the Q.6 timing): when the draft rating is an action verdict OR the override lane is to be evaluated, run the FULL Q.6 GATE-F procedure NOW -- between K-bis.5 and this step (the sheet write is a legitimate small write under F11). BLOCKED -> HALT per Pre-Output 10a. Same-day re-run after a HALT: reuse the existing same-day sheet iff its markers are unchanged, else write the -HHMM variant.
- Build the `{value, prov}` inputs form + the trusted book snapshot (live MCP positions, `tools/pretrade_gate.py` format -- the SAME book contract as the T11 execution stair), then run `python tools/sizing-eval.py --compute --mode <add|hold-state> --inputs <path> --book <path> --worksheet-out <path>` per the RUN CARD. The script computes the band + regime halt from the raw series, exposures from the book, Half-Kelly both algebraic forms, and the W1-W8 waterfall. NEVER compute sizing arithmetic by hand; NEVER edit a script-produced number (recovery = fix inputs, re-run --compute, replace the WHOLE worksheet).
- Paste the emitted worksheet (`kernel:sizing` block + rendered lines) VERBATIM into the analysis body immediately after the Decision Sheet. The TRADING DECISION **Action** dollar amount MUST equal the worksheet `final_dollars` (script-enforced at 10b).
- **Override lane**: the worksheet always REPORTS availability (N/5 conditions); INVOKING it requires an explicit user directive in the current session quoted verbatim in the disclosure (the model NEVER self-invokes); ONE tranche of 25% of computed size pierces ANY observable sub-1.0 state including the VIX tail halt, and NEVER pierces unknown-treated-halted; full procedure + measurability in ref-kernel-sizing.md.
- Verdicts NO-TRADE / HURDLE-FAIL / STOP-BAND-FAIL / OVERRIDE-UNLAWFUL are transcribed honestly and shape the Action field; markers are never re-filled to force a size.

### Phase K.5: Variant view -- thesis-critic adversarial cross-check (DELEGATED; Phase C wiring 2026-05-02)

Before Phase K composes the analysis body, dispatch the `thesis-critic` subagent for adversarial stress-test against the proposed rating from K-bis.4.

**MANDATORY when the running harness exposes an Agent tool** (per Execution Rules): dispatch first, no pre-emptive skip. thesis-critic is asset-class agnostic -- it stress-tests any thesis/rating regardless of equity vs crypto vs commodity. Skipping based on "this won't apply" is a DEVIATION.

Use the Agent tool with subagent_type `thesis-critic`. Pass input: `{ticker: "<TICKER>", primary_thesis: "<thesis-slug from Phase D>", primary_drivers: [<top-3 drivers from Phase E-I>], market_regime: "<from Phase I; CONTEXT ONLY -- not a gate, not a size input>", proposed_rating: "<K-bis.4 TRADING DECISION rating>"}`.

Validate subagent return:
- 3-5 ranked failure modes with detectability, recoverability, cascade and invalidation trigger. Numeric probabilities require a cited calibration method, reference class, outcome definition and horizon; otherwise retain qualitative uncertainty and mark probability unavailable.
- Each failure mode includes evidence with `[grade | source | date]` per-fact provenance
- Ideological Turing Test (ITT) self-score present and >=7/10

If ITT self-score <7/10: thesis-critic rejected its own output (bear case not sufficiently steelmanned). Re-dispatch ONCE with strengthened bear-evidence prompt. If still <7, dispatch fails, OR the harness exposes NO Agent tool (there it is the NORMAL path, reported `inline-no-Agent-tool`, never a DEVIATION): fall back to inline Variant View composition from `Atlas/sources/investing/ref-portfolio-doctrine.md` invalidation triggers + standard Variant View skeleton.

On dispatch success: compose Variant View section in Phase K body using the returned failure modes. The failure modes route to THREE non-veto outputs (Steps 2-3 of the verdict redesign; the prior "escalate the rating one tier" veto sentence was REMOVED 2026-06-06 per invest-verdict-redesign-brier-backtest-2026-06-05 -- the adversarial rigor is fully preserved, it just no longer vetoes the rating):

**STEP 2 -- CONVICTION MODULATION (counter-thesis lands HERE, not on the rating):**
```
conviction_base = f(composite, R/R margin over hurdle, valuation support)   # the un-modulated conviction
conviction = conviction_base - SUM over failure_modes of
               ( probability x cascade_weight x (1 - detectability_discount) )
  where  cascade_weight: HIGH = 40, MED = 20, LOW = 8
         detectability_discount = 0.30   (a detectable failure mode is less penalizing)
         probability in [0,1]; floor the result at conviction = 20
```
Deterministic and auditable. A BUY with a strong bear case becomes "BUY, conviction 45%" -- NOT "HOLD". (Coefficients calibrated against the 40-call backtest: monotone gradient, STRONG BUYs land ~47-69, heavy-risk HOLDs floor at 20. Do NOT re-tune without re-running the Phase 1 backtest.) Write the modulated conviction into the K-bis.4 TRADING DECISION **Conviction** field; show the conviction_base and the per-failure-mode penalty in the Variant View so the modulation is auditable.

The historical coefficient fit above does not calibrate a new failure mode's probability. If a required probability lacks support, the point modulation is unavailable; never substitute zero, invent a percentage, or label an unmodulated value as modulated. Complete the supported analysis and retain the existing rating/sizing invariants. An explicitly assumed probability range may support a labeled conviction sensitivity calculation, not a calibrated point estimate. The formula and coefficients remain unchanged.

**BEHAVIORAL MODE BOUND (the owner directive 2026-07-11; donor GATE-F checks, bounded):** the behavioral checks contribute AT MOST ONE failure mode ("chased entry, mean reversion"), ONLY when gate-eval.py returned FOMO-SUSPECT (never on a clean pass), cascade weight capped at MED (20), never HIGH -- worst-case drag 0.5 x 20 x 0.70 = 7 points. The price-invariance test (would this exact thesis have justified buying 10 sessions ago at the pre-move price? -- computed 10-session/1-month returns from the technicals panel, never estimated; if nothing changed but price, the honest skew is HOLD/wait-for-level with the level NAMED) and the Phase J pnl round-trip surface as Decision-Sheet prose and inform that single mode's probability -- they are NOT separately summed. Disposition-effect is trim-side (ref 2.11), never a buy-side penalty.

**CONVICTION INVARIANT (source-verified 2026-07-11):** K.5 modulation changes the reported Conviction % and nothing else mechanical -- never the rating (K-bis.5 data gates), the Kelly win-probability (rating + R/R keyed, kernel_lib pick_win_prob), final_dollars/the Action amount, the K-ter options mapping (conviction-blind by contract), or any Brier. The critic has weight, not a veto.

**STEP 3 -- KILL-CRITERIA SURFACER + THESIS STATUS (monitoring, not veto):**
- Populate the Kill Criteria section from the failure modes' quantified invalidation triggers (these are the monitoring thresholds).
- Set thesis_status CONFIRM / CHALLENGE / INVALIDATE. INVALIDATE requires an ACTUAL triggered kill criterion (data crossing a quantified threshold), never a narrative; CHALLENGE is the soft state.
- The rating cap (if INVALIDATE or near-trigger) was ALREADY applied by the Step-1 K-bis.5 THESIS-STATUS GATE -- Step 3 only records the status + monitoring triggers; it does NOT re-touch the rating.

The rating set by K-bis.5 Step 1 is FINAL after this routing (the counter-thesis changed conviction + kill-criteria + thesis-status, not the tier). If thesis == INVALIDATE caused a Step-1 cap, note it in the K-bis.4 header rationale + Phase P. Surface the failure-mode reasoning + the conviction modulation arithmetic in the Phase P audit report.

**STEP 4 -- WAVE-3 ADVERSARIAL VERIFICATION GATE:** review every material STRONG BUY, BUY, HOLD, SELL and STRONG SELL conclusion. Thesis-status changes, composite within +/-5 of a tier boundary (20/40/60/80), and `--verify` also require review. On TOPOLOGY=dw invoke `invest-verify` with the draft bundle (verdict, composite, supported conviction or explicit missing value, R/R, entry/stop/target, scoring_path, ttm_operating_income, thesis_status + prior, claims_with_prov, quote_technicals, fundamentals_bundle, routing_trace, run_timestamp). Four read-only skeptics cover data integrity including share-count >1.5x, R/R, routing including STEP 2a, and provenance. A failed/malformed reviewer or any refutation keeps acceptance withheld under Phase N; retain evidence, corrections and disagreements. HOLD/SELL direction never exempts a material conclusion. On TOPOLOGY=sequential prepare the same four lenses with deterministic re-derivation and a separate available reviewer; if separate review is unavailable, disclose that limit and retain the supported analysis as an unaccepted draft. Both topologies require final delivered-artifact review through workbench review/verify-review under docs/financial-analysis-contract.md. Sampled skeptics cannot certify a subsequently changed report. Rating thresholds and trade gates remain with their existing owners.

### Phase K-ter: Options-structure recommendation layer (2026-07-11; read ref-options-layer.md -- READ IT, same pattern as K-bis.7)

Runs AFTER K.5 (verdict + conviction FINAL; Wave-3 survived), BEFORE Phase K. Skip matrix, screens, IV proxy, mapping table, PoP + basis coherence, and the ledger record schema all live in the ref. Sequence:
1. ToolSearch-load the option READ tools (`get_option_chains`/`get_option_quotes`/`get_option_instruments`); load failure -> DISABLED note in analysis + Phase P (options_layer_enabled=false; gate items 10g-10i go conditional). Skip on `--refresh` and on assets without listed options (`not-applicable-no-listed-options`, not logged).
2. Evaluate screens + the mapping (branch on VERDICT + IV context + screens ONLY -- never conviction); produce the full output block (legs/strikes/expiry/premium/breakeven/max loss/max gain/PoP+method+basis/earnings exposure/tax note/scale + executability flags/PAPER label) OR a first-class NO_TRADE with its reason.
3. Construct the ledger record IN MEMORY (prediction or discipline_record; pre-registered machine criterion; horizon = max leg expiry; thesis_horizon_date + verdict criterion). The block composes into the analysis body under section 21 at Phase K; the ledger APPEND happens at Phase M (atomic with the commit).

### Phase K: Compose Analysis File

K.1 -- Pre-Output 10-point gate (see above). HALT on any violation.

K.2 -- Read the sibling `ref-analysis-template.md` for frontmatter schema, 25-section body skeleton, metrics catalog detail, three `:::chart:*` (bar / radar / doughnut) fenced contracts, and `<!-- INGEST:claims -->` coordination block format.

K.3 -- Filename: `<ticker-lowercase>-analysis-<YYYY-MM-DD>.md`. Date suffix mandatory.

K.4 -- Path-collision (v2 final semantics preserving archival rule):
- If target file exists AND `--replace` flag provided: overwrite (explicit destructive).
- If target file exists AND no `--replace`: default to timestamped variant `<ticker-lowercase>-analysis-<YYYY-MM-DD>-<HHMM>.md`. Log: "same-date collision; using -HHMM variant per archival rule."
- If neither file exists: use date-only filename.

K.5 -- Write to `wiki/investing/analyses/<filename>`. Body per template. Include:
- 2-3 sentence Thesis Statement (institutional practice)
- `trigger:` field in frontmatter (what prompted this analysis: earnings / catalyst / portfolio trigger / user request)
- `confidence:` AND `conviction:` as separate frontmatter fields (see Quality Standards)
- `topology:` (dw | sequential) AND `orchestrator_model:` frontmatter fields from Phase A.7 (passive logging; mirrors the calibration-monitor columns)
- `<!-- INGEST:claims -->` block at end of body with marker-signature-formatted claims for downstream /ingest (Pattern 18); each claim carries the `prov:` 8th field (ref-dw-topology.md Section 7).
- **KERNEL frontmatter fields** (INVEST KERNEL 2026-07-06; mandatory on every full run, enforced by 10b/10d + `sizing-eval --check`; legacy analyses are NOT backfilled): `rating:` (mirrors the TRADING DECISION header verbatim), `price_at_analysis:` (the regular_market_close used for threshold math), `rr_ratio:` ("X.XX:1"), `position_size_pct:` (worksheet final % of book; null unless BINDING SIZE-OK), `doctrine_version:` + `doctrine_fingerprint:` (from D.8), `deployment_band:` (the `<state>:<multiplier>` stamp, e.g. "normal:1.0" or "rate-shock-caution:0.5" or "halt-vix-tail:0.0"), `deployment_override:` (bool), `gate_f:` (sheet path per 10a; null when no action verdict), `kill_criteria:` (list of quantified triggers from K.5 Step 3), `thesis_line:` (one sentence; the body keeps the 2-3 sentence statement). These make the analysis file the machine-readable THESIS NOTE that J.5.6 + journal.base + GATE-F consume. **NEW field groups (2026-07-30, contracts in ref-analysis-template):** `rr_inputs:` (mandatory with any `rr_ratio`; 7.4.1), `target_model_inputs:` (whenever 10.4 governs the target; 6.1.2), `watch_zone:` (whenever a WATCH zone is set or kept; 6.1.3 -- read by the GATE-F `zone_preregistered` marker + the /brief Optionality Map), `initiation_gates:` (structured buy-side gates parallel to the flat `kill_criteria:` list; 12.5).

K.6 -- Tag vocabulary assertion before write: only `topic/*`, `ticker/<TICKER>`, `company/*`, `thesis/*`.

### Phase L: Entity Update (CREATE or UPDATE branch)

L.0 -- DELEGATED dispatch to `claim-distributor` subagent (PREFERRED path for UPDATE branch; Phase C wiring 2026-05-02):

CREATE branch (entity absent): skip L.0; entity creation needs full Phase L inline logic to ground in `_templates/entity.md`. Subagent dispatch only applies to UPDATE branch where the existing entity body must be preserved byte-exact outside insertion windows.

UPDATE branch (entity exists): **MANDATORY** dispatch where the running harness exposes an Agent tool (per Execution Rules) -- no pre-emptive skip. Use the Agent tool with subagent_type `claim-distributor`. Pass input: `{entity_path: "wiki/entities/tickers/<TICKER>.md", claims: [<extracted from Phase K body's INGEST:claims block>], session_id: "<current-session-id>"}`. The subagent reads the existing entity, computes pre_sha256, classifies each incoming claim against existing content via marker_sig dedup, tiers contradictions (Tier 1 auto-resolve / Tier 2 flag / Tier 3 reject / defer if ambiguous), and returns proposed Edit operations as JSON.

Validate subagent return:
- JSON with `entity_path`, `edits[]`, `body_preservation` (pre_sha256 + expected_post_sha256_outside_inserts), `zero_new_claims_short_circuit`, `summary` counts
- pre_sha256 matches current entity body hash (re-compute and compare; HALT on mismatch = entity changed mid-dispatch)
- Each `op` in edits has anchor specification (anchor_after for insert, anchor_line for replace)

If `zero_new_claims_short_circuit: true`: skip Phase L entity write entirely (per existing v2 final discipline at line 49). Phase P reports "entity unchanged (all N claims deduped per claim-distributor)."

On contract violation, dispatch failure, OR a harness with NO Agent tool: fall through to the inline UPDATE branch logic below (existing manual claim-extraction + marker-sig dedup + Tier classification) -- on a non-dispatching harness that inline path is the NORMAL path, reported `inline-no-Agent-tool` (never a DEVIATION). Surface in the Phase P audit report.

On dispatch success: parent /invest performs the atomic Edit operations from the returned `edits[]` array, verifying post-Edit sha256 matches `expected_post_sha256_outside_inserts`. Mismatch = HALT; rollback. Tier-2 flagged conflicts get inline annotation in entity Inconsistency Log (Phase J.5.4 mechanism).

Read the sibling `ref-entity-update-semantics.md` for CREATE-vs-UPDATE branching, claim-to-section mapping, marker-signature dedup, contradiction tiering, body-preservation sha256 invariant, symmetric back-link protocol.

**CREATE branch** (entity absent at `wiki/entities/tickers/<TICKER>.md`):
- Ground in `_templates/entity.md`.
- Canonical frontmatter: `categories: [entity]`, `type: ticker`, `ticker: <TICKER>`, `sector: <from-analysis>`, `thesis: [<detected-list>]`, `accounts: [<account keys or none>]`, `tags: [ticker/<TICKER>, thesis/<...>, topic/<...>]`, `related: ["[[investing-moc]]", "[[<thesis-file>]]", "[[<ticker>-analysis-<date>]]"]`.
- Populate 5 sections with extracted claims + per-fact provenance.
- MOC back-link: `[[investing-moc]]` in `related:`.

**UPDATE branch** (entity exists):
- Apply claim-to-section mapping (canonical strict order: Financial signals / Thesis Fit / Risks / Catalysts / Recent / Position / Sources).
- Marker-signature dedup `(entity, metric, value, date)` skips existing claims.
- Contradiction tiering: Tier 1 auto-resolve newer-supersedes-older; Tier 2 flag similar-authority; Tier 3 reject lower-authority.
- Per-fact provenance: `- <fact> (per [[<ticker>-analysis-<YYYY-MM-DD>]])`.
- **Zero-new-claims short-circuit** (v2 final): if count of net-new claims after dedup == 0, SKIP entity write entirely. Do NOT bump `updated:`. Phase P reports "entity unchanged (all N claims deduped)." File sha256 unchanged.
- Else: apply Edit; bump `updated:`; compute `after_sha256`; assert additive-only diff.

**Symmetric back-link**: entity `related:` gains `[[<ticker>-analysis-<YYYY-MM-DD>]]` (reciprocal to analysis's `[[<TICKER>]]`). Skip if already present (idempotent).

### Phase M: Peripheral Updates (atomic, sha256-invariant)

All updates body-preserving and marker-signature deduped.

- `Atlas/concepts/investing/watchlist.md` (peripheral-contract fix X14 2026-07-04): UPDATE the ticker's existing row after EVERY analysis (any verdict -- HOLD/AVOID rows go stale otherwise, the observed failure mode); ADD a new row only on BUY or WATCH verdicts (AVOID/SELL names without an existing row are NOT added). Row carries key levels + catalyst dates + `per [[<analysis>]]` back-link. Keep the table ONE contiguous block (no blank lines between rows) with a 6-column `|---|` separator.
- `Atlas/concepts/investing/investing-research-log.md`: append `[<date>] [<TICKER>] <verdict> <conviction%> <confidence%> <model>`. Marker-sig dedup on `(ticker, date, model)`. Model = current session's model ID.
- `Atlas/sources/investing/ref-research-insights.md`: only if a new analytical insight emerged (substantive threshold: cross-ticker pattern / sector rotation signal / thesis challenge / previously-unseen driver). Append `[<date>] [<TICKER>] -- <insight>`.
- `Atlas/_MOCs/investing-moc.md`: back-reference row if missing (on CREATE branch).
- `Calendar/decisions/sessions-log.md`: append in /retro v2.1 canonical schema (Date / Title / Domain / Focus / Decisions ratified / Skills invoked / Artifacts / Related). Marker-signature on `(date, skill, ticker)` enables /retro merge.
- `Calendar/daily/<today>.md`: append `- [HH:MM] /invest <TICKER> -> <verdict> (conv:<X%> conf:<Y%>)` under `## Sessions Run`. Recompute daily-note `before_sha256` immediately before this write to handle UserPromptSubmit hook race.
- `wiki/investing/options-ledger.jsonl` (Phase K-ter record; 2026-07-11): append via `python tools/score_ledger.py --append '<record-json>'` -- the SCRIPT owns id-assignment, the point-in-time gate, pop-basis coherence, horizon=max-expiry, ASCII, the write-target whitelist, and the sha256 append-only prefix check (validation lives in one tested place; Bash writes bypass the hook chain by design). NO_TRADE discipline records append too. SKIPPED on --preview (unreachable) and shadow --no-entity/--no-peripheral runs (S7 -- no A/B artifacts in the scoring population). F14-staged into the atomic commit at O.2.
- `wiki/investing/calibration-monitor.md` (Phase R; verdict redesign 2026-06-06): append one row per call -- see Phase R for the row schema + shadow-rating computation (vNEXT: row includes the two END-appended columns `orchestrator_model` + `topology`; historical rows stay byte-identical). Create the file with canonical frontmatter if absent (`categories: [wiki]`, `type: report`). Marker-sig dedup on `(date, ticker)`. This is the rolling-Brier rollback evidence base; the append is atomic with the analysis commit. SHADOW RUNS (--no-entity --no-peripheral A/B validation) write NO monitor row -- the Brier population must contain no A/B artifacts.

- `Calendar/decisions/execute-or-decline.md` (2026-07-30): rows are appended by the RATIFYING session (/decide, /retro, or a GATE-F `eod-row-regate` mandate), never by /invest itself -- but when this run's action is ratified into a row, a BUY row's Action cell carries the broker-ready ORDER string per the ledger header (`ORDER: BUY <T> | LIMIT $<px> | <N> whole shares (~$<amt>) | TIF: GFD or GTC<=30d | account | valid until <date>`; whole shares only, one limit at the ask for the full tranche) and a CONDITIONAL row carries `rev <ISO date>` in column 4. The agent never places the order (D-SEC-1).

**Never write** (surface as follow-up instead):
- Protected account files -- do not read or write. Phase P may report a broker reconciliation issue without assuming any file contents.
- `wiki/hot.md` -- /retro's responsibility.
- `Atlas/concepts/investing/theses/thesis-*.md` -- Pattern 20 categorical confirmation exception. Contradictions surfaced as follow-up.

### Phase N: Mid-Batch Failure (F.halt)

Applies throughout Phases K-M. If any Edit/Write fails:
- IMMEDIATE HALT.
- F11 flag STAYS ON.
- No partial commit.
- Report: files written (in working tree, unstaged); files failed (with error); files not attempted.
- User decides: `git checkout -- <paths>` rollback OR fix + re-invoke (idempotency skips via marker-sig + sha256).

### Phase O: Commit + F11 Clear

O.1 -- Pre-commit gate: verify sha256 body-preservation invariants on every updated file. HALT with specific failing file if any outside-insertion-site bytes differ from `before_sha256` (modulo strictly-additive diff per file class). The options ledger's file class is APPEND-ONLY PREFIX: prior bytes must be a byte-exact prefix of the new file (the score_ledger.py append already asserted this; re-verify here).

O.2 -- F14 narrow staging: explicit pathspecs (the ledger is IN the expected set whenever K-ter appended).

    git add `<analysis-path>` `<entity-path>` <peripheral-paths-that-were-written> <wiki/investing/options-ledger.jsonl when appended>

O.3 -- Commit. Format:

    agent(invest): `<TICKER>` analysis -- `<verdict>` <conviction%>

    <one-line rationale: key driver of verdict>

    Analysis: `<analysis-path>`
    Entity: <CREATE | UPDATE N claims added, M deduped | UNCHANGED all deduped>
    Peripherals: <list of touched paths>
    Confidence: <HIGH|MED|LOW with reasons>; legacy <X/100 or unavailable>, uncalibrated; cap applied: <none | Grade-C 70 | Grade-D 60 | STALE 65>

    Findings applied: F11, F14, F16, F17.

ASCII only. No Co-Authored-By.

O.4 -- Post-commit verification:
- Co-Authored-By absent: `git log --format='' -1 HEAD | grep -cE '^Co-Authored-By:'` returns 0 (F17).
- Bytes spot check: re-read a representative updated file; confirm body bytes match post-write state.
- Commit SHA captured for Phase P.
- Expected staged set matches actual (F14 invariant).

O.5 -- Clear F11: `rm .claude/state/auto-commit-disabled`. Only after O.4 passes. Assert absence.

### Phase P: Audit Report (conviction + confidence separate, calibration cap and account evidence reported)

Emit to user:
- **Analysis**: path + verdict + supported conviction index or UNAVAILABLE + evidence confidence (with legacy score/cap if applicable); no uncalibrated probability label
- **Calibration monitor** (Phase R): `<N> calls logged, <M> realized at >=3mo; rolling Brier(new) <x> vs (shadow) <y>; rollback trigger <not-armed | armed-but-not-fired | FIRED>`. While M < 8: note "MECHANISM-VALIDATED window open". On any BUY/STRONG BUY of a tripwire-listed name: surface the R.4 tripwire HALT.
- **Options layer (K-ter)**: structure recommended (or NO_TRADE + reason, or DISABLED/not-applicable); ledger id appended + flags (executability / scale / PAPER); one-line "options-PoP Brier" state from R.7 -- labeled DISTINCT from the R.5 rating-Brier
- **Conviction audit**: `base <Y> | thesis-critic penalty <A> (<n> modes) | behavioral penalty <B> (<=1 mode) | floored: <yes/no>` when inputs support the point calculation; otherwise name unavailable terms and withhold the point result, preserving any labeled sensitivity range. When floored, stamp `CONVICTION-SATURATED -- rating and size are UNAFFECTED (rating = K-bis.5 data gate; size = Kelly on rating+R/R)`
- **Entity**: CREATE or UPDATE branch; `N facts added / M deduped / K Tier 1 auto-resolved / L Tier 2 flagged`; OR "UNCHANGED (all deduped)" if zero-new-claims short-circuit fired
- **Peripherals**: which touched, which skipped, reasons
- **Commit**: SHA + F14 pathspec list
- **Subagent dispatch report** (Phase C wiring 2026-05-02): per dispatched phase (E.0, J-bis.0, K-bis.0, K.5, L.0) emit one of:
  - `DISPATCHED` -- subagent ran successfully, output integrated into analysis
  - `DISPATCHED (N/A return)` -- subagent ran successfully and returned an N/A-shaped output (e.g., crypto input on equity-shaped subagent); N/A propagated to Decision Sheet verbatim
  - `INLINE (no Agent tool)` -- the running harness exposes no Agent tool; the documented inline fallback ran VERBATIM as the NORMAL path (reported `inline-no-Agent-tool`; never a DEVIATION)
  - `FALLBACK` -- legitimate dispatch failure; report exact reason: "contract violation: <field missing>" / "timeout after `<Xs>`" / "rate limit hit" / "tool denial: Agent not in allowed-tools" / "hard subagent crash"; inline fallback executed
  - `DEVIATION` -- pre-emptive skip without legitimate failure; report the judgment given ("declared N/A for crypto", "decided subagent wouldn't help", etc.); flag as discipline breach; create sessions-log entry capturing the pattern for future correction
- **Topology report (TOPOLOGY=dw)**: per-wave summary -- `Wave 1: <N dispatched, M converged, K fallback>; Wave 2a: <forensic + positioning status>; Wave 3: <4 skeptics, N refutations | unavailable, acceptance withheld | no material conclusion or other trigger>`; ws_actuals vs the 0/2/4/0/1/6 budget map; token actuals vs INVEST_DW_TOKEN_BUDGET; `retrieval_degraded` worker list (+ the Phase 0 `phase0_hits=0` line when applicable); hybrid-reconciliation result (clean | divergence flag detail). Report the final-artifact review receipt and unresolved findings separately. **Delegation receipts (ANY topology, including sequential):** state `lane: ARMED <model> | DISARMED <reason> | not requested`; when ARMED, paste `python tools/delegate.py --report --run <run_id>` output VERBATIM (leg | model | out-tokens | tok/s | secs | exit) plus the delegable-but-not-delegated count. Receipts, not recollection -- a model's own account of what it delegated is the one report that cannot be trusted by construction.
- **Kernel report (INVEST KERNEL 2026-07-06)**: doctrine-lint result + `doctrine_version` + `doctrine_fingerprint`; deployment state + multiplier + every active reason code + the rate delta/confirm/streak and VIX max5 disclosure + the reserve-release stamp (all script-computed); worksheet mode (BINDING | HOLD-STATE | skipped-with-reason) + verdict + binding chain; override availability N/5 + invoked (with the verbatim directive when true); `sizing-eval --check` exit code from 10b; the RUN CARD completion table from ref-kernel-sizing.md pasted verbatim
- **Follow-up flags**:
  - Thesis-status changes needing the owner confirmation (Pattern 20; never auto-edit theses)
  - Account reconciliation issues: cite current-session broker evidence,
    affected scope and missing information. Do not emit target-file patches
    or claims about protected file contents.
  - /ingest recommendation: if analysis contains cross-entity claims beyond focal ticker, emit copy-paste `/ingest <analysis-path>`.
  - Invalidation signal: if AVOID on held position, emit "recommend thesis re-evaluation via /challenge `<thesis>`".
  - Broker coverage: disclose read time, covered accounts/assets and any UNVERIFIED quantities, basis or denominator.

### Phase Q: Cross-Position Coherence Check (audit 2026-04-28 5th-pass; portfolio doctrine compliance)

Q.1 -- Post-decision portfolio coherence query:
- For the focal ticker's primary thesis, combine canonical membership with the Phase J.0 current-session broker book across covered accounts/assets; prices remain regular_market_close anchored per J.0b. Reconcile cash, crypto and account totals without substituting private files or stale snapshots.
- If primary thesis is `thesis-theme-alpha`, sum the positions tagged to the thesis by current dollar exposure
- Compare to the ceilings from the Phase D.8 LOADED `doctrine:` block (`concentration.thesis_theme_alpha` amber/red + interim + interim_until, `concentration.other_thesis_flag_pct`, `concentration.single_name` amber/red) -- the BLOCK is authoritative at run time; as of ratification 2026-07-06 these read 60/70 (interim 50 through 2026-09-08), 40, and 30/35, but a doctrine edit changes the block, never this sentence
- Read `Atlas/sources/investing/ref-factor-lens.md` and compute the factor-level concentration view ALONGSIDE the thesis ceilings -- the factor lens does NOT change doctrine thresholds; it adds the cross-thesis factor read (several theses can be ONE growth-momentum factor bet) that the 2026-06-10 challenge sweep flagged as Phase Q's blind spot (vNEXT Section 11 wiring 2026-06-10)

Q.2 -- Concentration-cascade detection:
- If thesis exposure exceeds its cap post-implementation (theme-alpha >60%, interim >50% during the phase-in; any OTHER thesis >40%) OR any single name exceeds 30% post-implementation:
  - Surface explicit warning in Phase P output: "Implementing this BUY would push thesis-`<slug>` exposure from 45% to 52% (illustrative), crossing the 50% interim amber -- conscious-flag + sleep-gate (still under the 60% target amber / 70% red)"
  - Recommend rebalancing cascade: "Trim <N> shares of the most-correlated existing position OR delay this BUY until the book is rebalanced"
  - Compute exact share-count math: "Current portfolio $<portfolio value> x 50% interim amber = $`<ceiling>` theme-alpha ceiling - current theme-alpha $`<current>` = $`<headroom>` headroom to the interim amber ($`<headroom-60>` to the 60% target amber); recommended BUY $`<amount>` is within headroom"

Q.3 -- ETF overlap interaction:
- If focal ticker is an ETF, recompute look-through concentration including the ETF's holdings
- If focal ticker is a stock that overlaps with held ETFs and their look-through, increment effective exposure by overlap weight

Q.4 -- Newly-discovered concentration risks:
- Cross-reference focal ticker's sector + industry + thesis against existing portfolio
- Surface any newly-discovered concentrations not previously flagged, for example (invented figures): "a sector-fund analysis reveals 30% holdings overlap with individual single-name positions; combined effective theme-alpha concentration is 65%, exceeding the 60% amber but under the 70% red -- arm the exit ladder, do not force a mechanical trim"

Q.5 -- Output: Cross-Position Coherence section appended to Phase P audit report (before user emit). Includes:
- Current thesis-level exposure %
- Post-recommendation thesis-level exposure %
- Doctrine-ceiling compliance verdict (compliant / amber / red)
- Recommended rebalancing sequence if non-compliant
- Note: Q is informational only; does NOT block the BUY/SELL/HOLD rating from K-bis. User makes final call on whether to implement focal-ticker recommendation given doctrine constraints.

Gate: Q.5 output is mandatory. Missing broker coverage makes affected portfolio
figures UNVERIFIED and blocks portfolio-dependent sizing or recommendations.
Continue independent issuer research with the gap disclosed; do not fabricate
whole-book exposure or use a saved account-file fallback.

Q.6 -- GATE-F trade-generation gate (judgment-gates kit, 2026-07-06): if the draft rating is an action verdict OR the Decision Sheet will carry any ADD/TRIM/EXIT/staged-limit order block, run the GATE-F procedure per `.agents/skills/gate/ref-gate-tables.md`: fill the 11 behavioral/temporal markers with provenance, compute the verdict via `python tools/gate-eval.py --compute` (NEVER judge it), write the sheet to `wiki/research/gates/`, `--check` it (exit 2 -> fix before proceeding), append its registry row, and record its path for the frontmatter `gate_f:` field. Division of labor: GATE-F checks PROCESS discipline only -- doctrine ceilings stay in Q.1-Q.4, R/R stays in K-bis, execution stays in the pretrade staircase. Enforcement is Pre-Output gate item 10a. **KERNEL SEQUENCING (2026-07-06):** on any run where K-bis.7 fires, this procedure EXECUTES at K-bis.7 time (between K-bis.5 and the sizing worksheet -- the override lane needs the verdict at sizing time); Q.6 remains the specification + the enforcement anchor, and by Phase Q the sheet already exists (verify, do not re-gate).

### Phase R: Calibration Continuity Monitor (verdict redesign 2026-06-06; CONDITIONAL-RATIFY rolling check)

The verdict redesign (K-bis.5 Step 1 spine + K.5 Steps 2-3) was ratified on MECHANISM, not on a one-shot outcome backtest (the 40-call sample had zero >=3mo-realized horizons -- stress-test failure-mode D7). Phase R is the pre-committed rolling check that closes that gap. It WRITES (via the Phase M append) and is purely additive -- it never touches the rating.

R.1 -- Shadow rating (the comparison baseline). Alongside the FINAL Step-1 rating, compute the **OLD-logic shadow rating**: what the REMOVED veto sentence would have produced -- i.e., if any K.5 failure mode has probability > 40% AND cascade-magnitude HIGH, downgrade the Step-1 rating one tier (BUY -> HOLD; HOLD -> SELL). This is cheap (the failure modes already exist from the K.5 dispatch) and is the apples-to-apples NEW-vs-OLD pair the monitor needs.

Apply that unchanged predicate with explicit missingness. One supported HIGH-cascade probability >40% establishes the veto. If all HIGH-cascade probabilities are supported and <=40%, the unchanged shadow is established even when unrelated LOW/MED probabilities are missing. Otherwise record shadow_rating as UNAVAILABLE: a missing HIGH-cascade probability cannot be imputed as zero or an unchanged rating. No HIGH-cascade modes makes the predicate false only if required failure-mode coverage is complete.

R.2 -- Log row. Append to `wiki/investing/calibration-monitor.md` (Phase M write):
```
| date | ticker | new_rating | shadow_rating(old-logic) | conviction% | R/R | composite | thesis_status | ret_1mo | ret_3mo | ret_6mo | orchestrator_model | topology |
```
The `ret_*` columns are left blank at write time and backfilled by `tools/score-outcomes.py` (R.5) or a later /invest run on the same ticker (the realized-return horizons accrue over weeks). The two END-appended columns (vNEXT) carry the Phase A.7 passive log; pre-vNEXT rows lack them and score as the `sequential-legacy` stratum.

Use UNAVAILABLE for an unsupported shadow or modulated conviction, with the precise reason in the linked analysis. Preserve the row and opportunity denominator. Never rewrite historical rows to retrofit these labels. Report comparable-pair and missing-shadow coverage separately; an unavailable comparison cannot be rescued as unchanged or counted as a successful pair.

R.3 -- Rollback trigger (PRE-COMMITTED; do not re-litigate at fire time). Once >= 8 logged calls have reached >= 3mo realization: compute rolling Brier(new_rating) vs rolling Brier(shadow_rating). **If Brier(new) is WORSE than Brier(shadow) by > 0.05 AND the gap is NOT attributable to a single name or a single crash window** -> revert the redesign: restore the removed K.5 veto sentence (the exact prior text is preserved in invest-verdict-redesign-brier-backtest-2026-06-05 + git history at the pre-redesign commit) and bring it back for re-design. If the gap IS attributable to one name/crash (the backtest's exact confound), do NOT roll back; note it and keep monitoring.

The scorer owns availability and arithmetic: a comparative gap uses identical realized, probability-mapped pairs, with the existing pooled floor of five and stratum floor of three. Keep the eight-realized-call arming definition unchanged, but an armed monitor with insufficient comparable evidence has an unavailable comparison and cannot fire numerically. Report marginal scores only as descriptive different-population summaries, plus all logged/realized/paired/missing counts. Preserve rating-map values, horizon definitions, attribution requirements and all historical rows.

R.4 -- SINGLE-NAME-BUY honesty tripwire (continuous, not gated on the 8-call window). If ANY analysis of a tripwire-listed name (one that has not cleared the 3:1 R/R hurdle in any backtested call) under the new logic ever rates BUY or STRONG BUY, HALT immediately and surface for review -- such a BUY indicates a possible R/R-gate defect, not a thesis change. (The K-bis.5 GUARD-1 block states this same tripwire at the rating site; Phase R is the monitoring backstop.)

R.5 -- Output + backfill: run `python tools/score-outcomes.py --dry-run --json` (deterministic; yfinance offline) to compute the monitor state; drop `--dry-run` when eligible blank `ret_*` cells exist past their horizons (the in-session run may overwrite with broker-authoritative MCP closes where available -- MCP-primary honored at this layer). The script emits BOTH pooled and TOPOLOGY-STRATIFIED rolling Brier (groupby the `topology` column; the R1 freeze rule on RATING_PROB_MAP applies -- constants immutable without a /decide + dual-map re-score). Emit the one-line Phase-R status in the Phase P audit -- "Calibration monitor: <N> calls logged, <M> realized at >=3mo; rolling Brier(new) <x> vs (shadow) <y> [pooled]; stratified: <per-stratum or insufficient-n>; rollback trigger <not-armed | armed-but-not-fired | FIRED>." While N-realized < 8: "MECHANISM-VALIDATED window open; BUYs carry the Validation-status note in their TRADING DECISION header." **GUARD-2 stratification (rider S1):** the R.3 rollback trigger is EVALUATED on pooled Brier, but any rollback (or promotion) decision MUST first check the stratified view -- if the gap is confined to a single topology stratum, the rollback target is the TOPOLOGY (revert to Tier-B), not the verdict redesign; a single-population artifact must never revert the spine.

R.6 -- Resume rule (TOPOLOGY=dw). Any mid-run interruption: resume via `Workflow({scriptPath: ".claude/workflows/invest-<research|verify>.js", resumeFromRunId: "<wf_id>"})` -- completed agents return cached; NEVER re-run a finished wave or re-spend its tokens. Sequential runs are unaffected (N.halt + idempotent re-invoke remains the recovery path).

R.7 -- Options-ledger scorer line (2026-07-11). Run `python tools/score_ledger.py --dry-run --json` (offline) and emit one Phase P line labeled **options-PoP Brier** (records / open / due-past-horizon / Brier vs delta-implied + base-rate baselines, n-floors honored). DISTINCT population from R.5's rating-Brier: separate ledger, separate freeze clock (the ref-options-layer CONFIG freeze), zero contact with RATING_PROB_MAP or calibration-monitor.md. When broker-authoritative closes are in-session for due records, resolve via `--closes`; a fired kill criterion resolves ONLY via the manual `--kill-fired <id>` input (no daemon watches kills).

R.8 -- Retrospective calibration is advisory and never changes the rating, R.3/R.5 populations or sizing inputs. Run `python tools/backtest-v2.py --run --ticker <ticker> --horizons 5,21,63 --out Efforts/osanwe-v2-overhaul/_work/calibration-v2.jsonl` and report this ticker's historical beat-SPY rates with horizons, observation counts and corpus context. If `wiki/maintenance/calibration/confidence-map.json` is fresh (<45d), `python tools/calibrate-confidence.py <stated>` may supply an advisory historical mapping ONLY when its target event, horizon, cohort and calibration method are identified and applicable. An undefined mapping is not a probability that the analysis is correct; label it an unverified historical mapping or "uncalibrated". rc=3 (stale/absent map) -> "uncalibrated" and continue. Preserve the existing doctrine caps and kernel; never HALT on R.8 or silently promote this descriptive mapping into pop_est.

R.9 -- Decision-alpha advisory (additive, advisory-only). Run `python tools/kernel-alpha-note.py` without --stated when the R.8 calibration applicability requirements are not established. Report the historical priced-action scope and freshness; it cannot establish current account quantities. Add --stated only for a supported score with an applicable, fresh outcome-defined mapping, and label the result with that mapping's target and limitations. An unavailable score or mapping yields an unavailable confidence advisory, never an invented value. Doctrine constants, R/R hurdles, sizing and ratings retain their existing owners; never HALT on R.9.

The qualified join requires all explicit applicability arguments: `--stated <0-100> --target-event <win_key> --horizon-days <positive-int> --cohort <reference-class-id> --calibration-method <method-id>`. The tool validates finite input, matching metadata, freshness, coherent bins and sample/limitation records. Legacy maps without that metadata yield UNAVAILABLE without clamping or suppressing the independent attribution advisory. Metadata consistency establishes a qualified historical lookup, not independent calibration proof. The legacy R.8 helper does not supply this stronger validation by itself.

## Examples

Read ref-analysis-template.md, "Workflow examples", for the preserved worked
examples when needed; the main phase procedure above remains authoritative.

## Failure Taxonomy

Catalog of failure modes per phase with detection rule + expected behavior.

### Harness-capability failures (all phases)

- **No Agent tool in the running harness**: every dispatching phase (E.0, J-bis.0, K-bis.0, K.5, L.0) runs its documented inline fallback VERBATIM as the NORMAL path; report `inline-no-Agent-tool` in Phase P. NEVER a DEVIATION.
- **No Workflow tool in the running harness**: A.7 sets TOPOLOGY=sequential (Tier-B, the permanent universal fallback) and K.5 STEP 4's `--verify` runs the inline data-integrity re-derivation. NEVER a DEVIATION.

### Phase A failures
- **F11 already set**: HALT with recovery guidance (another skill running / orphaned flag; manually `rm .claude/state/auto-commit-disabled` if orphaned).
- **Ticker malformed** (empty, numeric, special chars): HALT with diagnostic.
- **Vault indexes empty** (Glob returns nothing for TICKERS or ALL_BASENAMES): HALT; likely working-dir mismatch.
- **Entity note non-canonical frontmatter**: HALT; recommend `/enrich --refresh <path>` first.

### Phase D failures
- **Broker position coverage missing**: report holdings UNVERIFIED; do not infer "Not currently held" or read private files.
- **Class-ref load fails** (ref-etf-evaluation missing, etc.): WARN; fall back to stock ref defaults; log in Phase P audit.

### Phase E-I failures (research)
- **Retrieval quota / block / SSL**: use another permitted authoritative source or mark the claim unverifiable. Do not bypass certificate checks or blocked-source policy. Do NOT populate Decision Sheet with unverifiable claims.
- **Ticker ambiguous** (multiple securities match): HALT; ask user for disambiguation.
- **Stale reference period** (all price quotes >24h): WARN; proceed but downgrade freshness letter.

### Phase K failures (compose)
- **Pre-Output gate violation**: HALT with specific gap. Do not write.
- **Path-collision AND --replace not provided**: use timestamped variant automatically (not a failure).
- **Tag vocabulary drift**: HALT on any namespace outside {topic, ticker, company, thesis}.

### Phase L failures (entity)
- **_templates/entity.md missing on CREATE branch**: HALT; cannot ground entity without template.
- **sha256 mismatch on UPDATE**: N.halt; likely concurrent modification; F11 stays on.
- **Zero new claims**: short-circuit (not a failure; reports unchanged).

### Phase M failures (peripherals)
- **Edit old_string not found** (file drifted since Phase D sha256 baseline): N.halt.
- **UserPromptSubmit hook race on daily note**: recompute `before_sha256` immediately pre-write; if still mismatch, N.halt.

### Phase O failures (commit)
- **Staged set mismatch**: HALT before commit (F14 invariant violated).
- **F17 Co-Authored-By present**: HALT; reset --soft and recompose body.
- **Pre-commit hook fails**: investigate + fix; do NOT --no-verify.

### Phase P failure
- **F11 unlink fails**: log but do not halt; user manually `rm .claude/state/auto-commit-disabled`.

## Coordination

### Shared infrastructure (identical semantics across /enrich + /ingest + /invest)

- Vault indexes (TICKERS, COMPANIES, MOC_STEMS, THESIS_STEMS, ALL_BASENAMES, BACKLINKABLE_CATEGORIES)
- Tag vocabulary guardrail (topic/ticker/company/thesis only)
- Path-guards (mechanical)
- F11 Phase C discipline
- ASCII-only commit + F14 narrow staging + Co-Authored-By suppressed
- Body-preservation sha256 invariants (F16 bytes compare)
- Marker-signature dedup
- Claim-to-section mapping (canonical 6+Sources schema, strict order: Financial signals / Thesis Fit / Risks / Catalysts / Recent / Position / Sources)
- Symmetric back-linking
- State-transition-before-F11 abort checkpoint

### Division of concerns

| Concern | /enrich | /ingest | /invest |
|---|---|---|---|
| Source document placement | Yes (22-rule tree) | No | No |
| Analysis composition | No | No | Yes (Phase K) |
| Body preservation (source) | Byte-exact | Untouched | N/A |
| Body preservation (entity) | N/A | Yes (UPDATE) | Yes (UPDATE + zero-claim short-circuit) |
| Entity creation | No | Yes (>=3 mentions) | Yes (CREATE branch if absent) |
| Entity claim distribution | No | Yes (primary) | Yes (from own analysis) |
| Portfolio fit math | No | No | Yes (Phase J) |
| Research (WebSearch) | No | No | Yes (Phases E-I) |
| Peripheral vault updates | Back-links only | MOC back-link | Watchlist + research-log + insights + sessions-log + daily |
| INGEST:claims block emission | No | Consumes | Emits |
| /ingest recommendation | Emits (v8.1) | N/A | N/A |
| Commit atomicity | Yes | Yes | Yes |

### Consumed by

- `/ingest` -- via `<!-- INGEST:claims -->` block (distributes cross-entity claims)
- `/retro` -- via sessions-log entry (marker-sig on `(date, skill, ticker)` enables merge)
- `/challenge` -- via analysis wikilink when stress-testing a thesis
- `/brief` -- via entity-note updates surfaced in next morning's portfolio-movers scan

## Related skills

- `/enrich` -- onboards external research docs (complement: /enrich places, /invest analyzes)
- `/ingest` -- extracts claims from docs (complement: /ingest distributes facts, /invest originates facts)
- `/retro` -- consumes sessions-log entries
- `/challenge` -- consumes analysis wikilinks
- `/brief` -- consumes entity updates

## Phase O.0 -- Pre-commit /vault audit gate (v2.0; CAT-3 prevention-architecture parity)

After composing all target file modifications IN MEMORY but BEFORE atomic write:
1. Write each composed file to a tmp dir under `wiki/research/test-tmp/.precheck/invest-<slug>/`
2. Run `python tools/skill-precheck.py <tmp-files...> --skill /invest`
3. Parse exit code: 0 -> proceed; 2 -> HALT with diagnostic
4. Body-scope wikilink validation: per /retro v2.2 Phase D pattern, scan composed body text for unresolved `[[<target>]]` and mechanically de-link unresolved targets (vault-resolved keep / MEMORY_PREFIXES rewrite as `[[memory:<stem>]]` / placeholder leave / else strip). Fence-aware (skip ``` fenced + `inline code`).
5. Bypass: `CLAUDE_VAULT_BYPASS_VALIDATOR=1` (logged to `.claude/state/bypasses-`<date>`.log`)

Defense-in-depth on top of PreToolUse pre-write-validator.py + PostToolUse wikilink-check.py / frontmatter-check.py / orphan-check.py. The Phase O.0 gate prevents broken composition from reaching disk in the first place.

**/invest-specific risk:** /invest writes the most files atomically (~8 paths) -- Phase O.0 prevents any single-file GATE finding from cascading to N.halt rollback of the entire batch.

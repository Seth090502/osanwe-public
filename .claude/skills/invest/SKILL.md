---
name: invest
risk: critical
description: "Run institutional-grade investment analysis on a ticker, ETF, or crypto. Use when assessing a new position pre-entry, validating thesis fit before deployment, refreshing existing-position conviction after material news, post-earnings reconciliation, or pre-rebalance decision support. Produces a STRONG BUY / BUY / HOLD / SELL / STRONG SELL rating with 3-5 sentence summary at top of every analysis (TRADING DECISION header per Phase K-bis). Mandates 25-50 source target across stockanalysis.com fundamentals + Dataroma renowned-investor 13F overlay + CapitolTrades politician STOCK Act overlay + OpenInsider cluster-buy detection + Top-12 universal metrics (Piotroski/Altman/Beneish/ROIC/FCF/PEG/SBC/etc.) + Best-Investor Framework Rotation per ticker category (Buffett compounder / Lynch GARP / Greenblatt magic formula / Burry deep-value / Druckenmiller macro-narrative / Marks risk-first / Klarman margin-of-safety / Ackman activist / Munger lattice / Cohen catalyst / Tepper macro-pivot). Phase J.5 prior-research comparison detects inconsistencies vs prior analyses + entity note (thesis drift, confidence drift, metric degradation, kill-criteria-approached) and accumulates findings into entity Inconsistency Log for compounding learning across analyses. Phase Q cross-position coherence checks doctrine ceilings (THESIS_CAP_AMBER / THESIS_CAP_RED, interim phase-in; SINGLE_NAME_AMBER / SINGLE_NAME_RED; OTHER_THESIS_FLAG per [[doctrine.template]]) before recommendation. Provides body-preserving entity integration, atomic multi-file discipline, state-transition-before-F11 abort checkpoint, evidence-calibrated confidence, separate conviction field, timestamped same-day collision handling, zero-new-claims short-circuit, and downstream coordination. Reads portfolio context (private/holdings-taxable.md + private/holdings-ira.md), macro/sector/thesis/doctrine/scoring/monitoring reference docs, and the existing ticker entity note; prints state-transition model BEFORE F11 is set so user can abort pre-writes; performs 5-phase research spine (identity + fundamentals + technical + risk + competitive-macro) with inline evidence grading [Grade A|source|date] and freshness letter-downgrades; computes portfolio fit with exact share-count arithmetic and 3:1 risk/reward hurdle; composes canonical analysis file at wiki/investing/analyses/<ticker>-analysis-<YYYY-MM-DD>.md (same-date collision defaults to -<HHMM> variant, preserving archival rule; --replace reserved for explicit overwrite) with Decision Sheet + 2-3 sentence Thesis Statement + Variant View + Mispricing Assessment + Kill Criteria + <!-- INGEST:claims --> coordination block; updates entity note via claim-to-section mapping (Financial signals / Thesis Fit / Risks / Catalysts / Recent) with sha256 body-preservation invariant + per-fact source provenance + marker-signature dedup + Tier 1/2/3 contradiction resolution + zero-new-claims short-circuit (skip write entirely if all claims deduped); symmetric back-linking entity <-> analysis; atomic peripheral updates to watchlist + research-log + ref-research-insights + sessions-log + daily note; path-guards mechanical (never private/, .raw/, _quarantine/, etc.); F11 Phase C discipline; mid-batch failure triggers F.halt; single atomic commit with F14 narrow staging + ASCII-only body + Co-Authored-By suppressed (F17-verified); calibrated percentage confidence capped by evidence-grade mix (>30% Grade-C caps confidence at 70%; any Grade-D in body caps at 60%); conviction (strength of position recommendation) reported separately from confidence (epistemic probability analysis is correct). Modes: --preview, --confirm, --replace, --no-peripheral, --no-entity, --refresh. Coordinates with /enrich + /ingest via shared vault indexes + BACKLINKABLE_CATEGORIES + tag vocabulary guardrail. Output is canonical reference doc that downstream /ingest, /challenge, /retro, and /brief consume with zero friction. Phase O.0 pre-commit /vault audit gate (CAT-3 prevention-architecture parity)."
arguments: [ticker]
argument-hint: "NVDA, SPY, BTC, or any ticker/ETF/crypto"
allowed-tools: [WebSearch, WebFetch, Read, Write, Edit, Bash, Glob, Grep, Agent]
effort: max
user-invocable: true
---

# /invest <ticker> -- institutional-grade analysis with atomic entity integration (v2 final)

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

## Invocation modes

| Syntax | Behavior |
|---|---|
| `/invest <TICKER>` | Full 15-phase analysis: state-transition -> F11 -> research -> compose -> entity -> peripherals -> atomic commit |
| `/invest <TICKER> --preview` | Dry-run. Phase B state-transition print only. No F11, no writes, no commit |
| `/invest <TICKER> --confirm` | Per-file confirmations before each Edit/Write |
| `/invest <TICKER> --replace` | Overwrite same-day analysis file. Explicit destructive (default is `-<HHMM>` timestamped variant) |
| `/invest <TICKER> --no-peripheral` | Skip Phase L peripheral updates (analysis + entity only) |
| `/invest <TICKER> --no-entity` | Skip Phase K entity update (draft analysis only) |
| `/invest --refresh <analysis-path>` | Re-run Phase K entity extraction from existing analysis. Additive. Skips research phases. HALT if path not found |
| `/invest <TICKER> --thesis <name>` | ADDITIVE lens overlay (<thesis-slug>). First principles ALWAYS runs; the lens adds a "Thesis-lens view" subsection (cohort coherence + thesis-specific kill criteria) and enriches the conviction rationale. The lens CANNOT change the rating (see Phase D.7) |
| `/invest <TICKER> --verify` | Force the Wave-3 adversarial skeptics even on a non-boundary HOLD/SELL (TOPOLOGY=dw; see K.5 STEP 4). On TOPOLOGY=sequential the flag triggers the inline data-integrity re-derivation checks instead |

## Screen mode (informal; staleness rule)

Multi-name watchlist screens run on /invest infrastructure (live-quotes batch + readiness deltas; no full A-R phase arc). STALENESS RULE (C-extension root-cause 2026-06-10): any prior-analysis date or staleness claim MUST derive from the `wiki/investing/analyses/<ticker>-analysis-*.md` glob + the entity note's Recent section -- NEVER from `Atlas/concepts/investing/watchlist.md` rows (Atlas rows are human-gated and stale-prone; 2 of 8 screens on 2026-06-10 carried wrong priors from April-stale watchlist rows).

## Execution Rules

- **Tier-B (TOPOLOGY=sequential):** Execute phases sequentially. No merging or abbreviation. Use WebSearch for every current data point (not training data); perform the exact search count each phase specifies. **Tier-A (TOPOLOGY=dw, per Phase A.7):** phases 0/A/B/C/D run sequentially; the E-I research EXECUTION runs as concurrent Wave-1 workers per Phase A.8 + `ref-dw-topology.md` (the phase text below remains the authoritative spec of WHAT each worker produces); every other invariant (F11, path-guards, sha256 body-preservation, mandatory dispatch + N/A-is-success + DEVIATION, verdict spine, commit discipline) is IDENTICAL across both tiers. Tier-B is the permanent universal fallback -- any DW absence or regression lands there automatically.
- **F11 Phase C discipline**: set `.claude/state/auto-commit-disabled` at Phase C, BEFORE any Edit/Write. Phase B state-transition print runs BEFORE F11 so user can abort pre-writes. Clear flag only after Phase O post-commit verification.
- **Path-guards mechanical**. NEVER write: `private/`, `.raw/`, `_quarantine/`, `finance/`, `credentials/`, `.git/`, `.claude/hooks/`, `.claude/state/`. READs from `private/` ARE allowed (portfolio context).
- **Tag vocabulary canonical**: `topic/*`, `ticker/*` (UPPER), `company/*` (lowercase-kebab), `thesis/*` (lowercase-kebab) only. HALT on drift.
- **Binary decisions default** (SOTA compounding): BUY/HOLD/WATCH/AVOID; thesis CONFIRM or CHALLENGE. NEUTRAL only when signal is genuinely absent in both directions.
- **Confidence vs Conviction are DISTINCT fields** (see Quality Standards). Report both. Never conflate.
- **Body-preservation sha256** on every entity and peripheral UPDATE (F16 bytes compare on content outside insertion sites). **Marker-signature dedup** on claim integration: `(entity, metric, value, date)`. **Per-fact provenance**: `- <fact> (per [[<ticker>-analysis-<YYYY-MM-DD>]])`. **Machine provenance (vNEXT)**: every quantitative claim carries `prov: mcp:<server>:<key> | script:yfinance | web:<domain>+<grade>` -- the 8th INGEST-tuple field (dedup key stays the 4-tuple; spec in ref-dw-topology.md Section 7; enforced by the Wave-3 provenance skeptic + vault-audit X8 advisory). Idempotent re-runs produce zero diff.
- **Zero-new-claims short-circuit** (v2 final): if Phase K UPDATE branch finds all extracted claims already present after marker-sig dedup, SKIP the entity write entirely. Do NOT bump `updated:`. Phase P reports "entity unchanged (all N claims deduped)."
- **Symmetric back-linking**: every wikilink in a created or updated `related:` gets a reciprocal back-link on the target file.
- **Mid-batch failure**: immediate HALT (Phase N.halt), F11 stays on, no partial commit.
- **Commit discipline**: ASCII-only title + body, Co-Authored-By SUPPRESSED (F17 header-stripping grep post-commit), F14 narrow staging (explicit pathspecs only).
- Canonical frontmatter per CLAUDE.md schema; user custom fields (`thesis`, `confidence`, `conviction`, `sources_count`, `accounts`, `trigger`, `scoring_path`, `orchestrator_model`, `topology`) preserved byte-exact.
- **Subagent dispatch is MANDATORY when specified by phase** (J-bis.0, K-bis.0, K.5, L.0). Pre-emptive skip based on judgment ("this won't apply to crypto", "subagent might not have data", "result will be N/A") is FORBIDDEN. The subagent decides applicability via its own N/A return contract -- the parent skill dispatches and validates the return, not the verdict. Legitimate fallback fires ONLY on (a) contract violation -- subagent return missing required fields, OR (b) actual dispatch failure -- timeout, rate limit, tool-denial, hard subagent crash. A subagent returning "Not applicable to <asset-class>" with empty rows + confidence: N/A is a SUCCESSFUL dispatch; propagate the N/A return verbatim into the relevant Decision Sheet section. Pre-emptive skip surfaces in Phase P as **DEVIATION** (not "fallback"). Quality preserved by additive design: subagent dispatch never removes existing inline capability -- inline logic remains as fallback for legitimate failures only.
- **DW dispatch + resume (TOPOLOGY=dw)**: token budget via `INVEST_DW_TOKEN_BUDGET` env var (default 750K full / 500K Wave-3-skip; CALIBRATED 2026-06-10 from the 3 production Tier-A runs: 596K/555K/715K actuals, Wave-3 fire = +213K); concurrency <= 6; the main loop reads the env var and passes `args.token_budget` (the workflow sandbox has no process.env). Mid-run interruption -> resume via `Workflow({scriptPath, resumeFromRunId})`; NEVER re-run a completed wave. Full contract: ref-dw-topology.md Sections 6 + 9.

## Quality Standards

- **Confidence (epistemic)**: probability the analysis is correct. Percentage + evidence + state-change condition (e.g., "72% -- based on 10-Q margin expansion + 13F accumulation. Drops to 40% if Q2 margin contracts."). Capped by evidence-grade mix (see Pre-Output Gate item 10).
- **Conviction (actionable)**: strength of the position recommendation. Separate from confidence. Percentage + rationale (e.g., "LOW conviction short (35%) despite 95% confidence NVDA priced to perfection -- shorting momentum historically kills"). Can legitimately diverge from confidence.
- **Inline evidence grading**: every material claim cites tier at point of use -- `[Grade A | SEC 10-Q | 2026-04-10]`. A = primary filings, B = Tier 1 data/journalism, C = industry/analytical, D = sentiment, F = unverifiable. No Grade-D in Decision Sheet.
- **Portfolio math shown**: `1.500 x $100.00 = $150.00 (taxable) + 0.500 x $100.00 = $50.00 (IRA) = $200.00 combined` (synthetic example). EQUITY share counts come from live `mcp__robinhood-trading__get_equity_positions` at run time (hybrid rule, Phase J; private/ files are the interpretation layer + reconciliation baseline + crypto-quantity source); do not estimate. Threshold math anchors to regular_market_close (ref-dw-topology.md Section 8).
- **Temporal anchoring**: every data point has its date. Freshness: FRESH (<7d), RECENT (7-30d), DATED (30-90d), STALE (>90d, auto-downgrades evidence one letter). Flag TTM vs forward mismatches before use.
- **Risk/reward hurdle**: 3:1 minimum for BUY -- `(Target - Current) / (Current - Stop) = X:1`. Below 2:1 rejected as BUY.
- **Kill criteria quantified**: specific metric thresholds, not vague deterioration (e.g., "gross margin <45% two consecutive quarters" not "margins deteriorate").
- **2-3 sentence thesis statement** in the analysis body (distinct from frontmatter `thesis:` tags). Institutional practice: if it can't be stated in 2-3 sentences, the thesis isn't sharp enough.

## Verification Gates

HALT on failure. Gates fire: after Phase F (reporting-period consistency; TTM vs forward), after Phase I (supply-chain + competitive data <30d), after Phase J (portfolio math from actual share counts), before Phase K (Pre-Output 10-point gate below), before Phase O (sha256 body-preservation invariants on every updated file).

## Pre-Output Gate (before Phase K writes the analysis file)

Verify ALL. Any violation: HALT with specific gap; do not write the report.

1. Every Decision Sheet field populated from actual data. No placeholders, no "TBD", no "see below".
2. All dollar amounts calculated from real share counts with arithmetic shown.
3. Every date is exact (ISO or market-close timestamp). Not "recently" or "today".
4. No Grade-D evidence in the Decision Sheet.
5. Confidence is calibrated (percentage + justification + state-change condition).
6. **Confidence-evidence calibration** (v2 final): if >30% of Decision Sheet evidence is Grade C, confidence capped at 70%. If any Grade-D appears in body, confidence capped at 60%. If >2 STALE data points drive decision, confidence capped at 65%.
6a. **Cap C5 -- price provenance (vNEXT)**: if the price feeding portfolio math / R/R was non-broker (price-fetcher `broker_authoritative: false`) during `market_session == regular`, confidence capped at 60% + flag "price-unconfirmed (non-broker)" in the TRADING DECISION header. N/A outside regular session or on Codex/headless (the price-fetcher v4 parent-gate contract governs re-dispatch/HALT first).
7. **Conviction is separate from confidence** and has its own rationale. Both reported.
8. Variant view is genuinely differentiated OR explicitly marked: "No credible variant -- consensus probably right because [reason]".
9. At least one contradictory source consulted and cited in Evidence Quality.
10. Risk/Reward ratio calculated; meets 3:1 hurdle OR explicitly rejected as BUY if below 2:1; Kill criteria are specific and measurable (quantified thresholds); 2-3 sentence thesis statement present.

## /invest <ticker>

Use WebSearch for current data (blocked domains per CLAUDE.md; WebFetch SSL failures fall back to `curl -sk [url]` once).

### Phase 0: Vault context retrieval (NEW; Phase 3.6 -- runs BEFORE Phase A; read-only; runs in --preview)

Skill-level semantic retrieval over the local HNSW vault index (covers `wiki/` + `Calendar/` + `private/`; `Atlas/` is NOT indexed, so Phase 0 COMPLEMENTS -- does not replace -- the Phase D Atlas/ref reads). Deeper and path-filtered vs the universal UserPromptSubmit hook (which is top-5, whole-vault, literal-prompt). Read-only: a single Bash `node` call; safe in `--preview`. Let `T` = the uppercased input ticker.

0.1 -- Build 12 structured queries spanning the analytic surface:
`"<T>"`, `"<T> thesis"`, `"<T> risks"`, `"<T> institutional positioning"`, `"<T> insider activity"`, `"<T> catalysts"`, `"<T> regulatory"`, `"<T> competitive landscape"`, `"<T> macro/sector exposure"`, `"<T> earnings"`, `"<T> technical/price action"`, `"<T> analyst sentiment"`.

0.2 -- Fire `query-skill.mjs` TWICE via Bash, piping the JSON payload to stdin (heredoc or single-quoted echo; no temp file). Model loads once per call (~1-1.5s each):
- BROAD (cross-vault, no filter): stdin `{"queries":[<the 12>],"top_k":100,"threshold":0.60}` piped to `node ~\.vault-substrate\query-skill.mjs`
- FOCUSED (ticker-entity subtree; forward-slash prefix): stdin `{"queries":[<the 12>],"top_k":25,"threshold":0.60,"filter_path_prefix":"wiki/entities/tickers/"}` piped to the same script.

Each returns a JSON array `[{path,line,score,text}]`. The script always exits 0 (emits `[]` on any error), so Phase 0 never crashes the run.

0.3 -- Merge BROAD + FOCUSED; dedup by `path:line` (keep higher score); sort by score desc; cap to top 100. Store as VAULT_CONTEXT (available to every later phase).

0.4 -- EMIT a visible summary (MANDATORY -- retrieval must be visible in the response):

    Phase 0 -- retrieved vault context (N hits; M from wiki/entities/tickers/)
    Top results:
      [score] path:line -- first ~80 chars of text
      ... (show up to 15)

If both calls fail or return `[]`: emit `Phase 0 -- no vault context retrieved (query-skill.mjs unavailable or index empty)` and continue to Phase A with empty VAULT_CONTEXT. NEVER HALT on Phase 0. Log `phase0_hits=N` (the merged count); N=0 writes a non-halting `retrieval_degraded: phase0_hits=0` line into the Phase P audit.

0.5 -- Downstream consumers (these phases stay UNCHANGED; consult VAULT_CONTEXT as prior-thinking instead of re-deriving from scratch):
- Phase D (Context Load): add any entity-note / analysis paths surfaced in VAULT_CONTEXT to the D.2 read set.
- Phase J.5 (Prior-Research Comparison): seed prior-analysis + entity-drift discovery from VAULT_CONTEXT alongside the Glob -- this phase benefits MOST (it is semantic-retrieval-shaped).
- Phase J-bis (Institutional Positioning) + Phase K.5 (Variant View): cite prior institutional history + bear-case chunks from VAULT_CONTEXT.

Cite any used chunk inline as `(vault: path:line)` -- plain text, NO wikilink syntax (Phase 0 context is raw, not vault-resolved).

### Phase A: Pre-flight checks (NO F11 yet)

A.1 -- F11 collision check. If `.claude/state/auto-commit-disabled` exists, HALT: "F11 flag already set by another skill. Check: (1) any other skill running; (2) orphaned flag from a crash -- manually `rm .claude/state/auto-commit-disabled` to recover."

A.2 -- Normalize ticker input. Uppercase; strip whitespace; validate shape (1-5 letters for stocks/ETFs; crypto can be longer). HALT on empty or all-numeric input.

A.3 -- Load shared vault indexes (identical set used by /enrich + /ingest): TICKERS (`wiki/entities/tickers/*.md` stems, UPPER), COMPANIES (`wiki/entities/companies/*.md`), MOC_STEMS (`Atlas/_MOCs/*.md`), THESIS_STEMS (`Atlas/concepts/investing/theses/thesis-*.md`), ALL_BASENAMES (vault-wide wikilink resolution), BACKLINKABLE_CATEGORIES (`{concepts, sources, moc, decisions, wiki, entity, people}`).

A.4 -- Assert path-guard list. Any write targeting a guarded path HALTs.

A.5 -- Detect ticker class HINT (not definitive). Order: (a) if entity note exists at `wiki/entities/tickers/<TICKER>.md`, parse its frontmatter `type:` and `sector:` -- authoritative hint; (b) else match against holdings-taxable.md / holdings-ira.md position types (stock rows vs ETF rows vs crypto rows); (c) else treat as unknown (all class-ref docs loaded in Phase D).

A.7 -- Topology detection (deterministic; NEVER halts). TOPOLOGY = `dw` iff the Workflow tool is present in the orchestrator's current session tool surface; else `sequential` (Codex engine, headless, restricted sessions, any DW regression). Ambiguity -> `sequential` (safe fallback). `tools/lib/capability-detect.sh` (`OSANWE_DW_HINT`) is ADVISORY only -- the tool-surface check is authoritative. Record ORCHESTRATOR_MODEL = the active model string. PASSIVE LOGGING ONLY: no behavior ever branches on model identity; TOPOLOGY + ORCHESTRATOR_MODEL flow to the Phase B print, the analysis frontmatter (`topology:`, `orchestrator_model:`), and the two calibration-monitor columns (Phase R.2) so the Phase-R Brier can stratify by topology (GUARD-2 rider S1).

A.8 -- Wave routing (fires after Phase D completes):
- **TOPOLOGY=sequential (Tier-B):** execute Phases E-I below verbatim -- zero behavioral difference from v2 final.
- **TOPOLOGY=dw (Tier-A):** read `.claude/skills/invest/ref-dw-topology.md` (read-on-demand companion, same pattern as Phase K.2). Invoke the `invest-research` workflow (`.claude/workflows/invest-research.js`) with args {ticker, class_hint, held, entity_exists, prior_entity_summary, vault_context_summary, ws_budget_map: {identity:2, fundamentals:4, filings:0, competitive:6, positioning:1}, run_timestamp, token_budget}. It runs Phase(Price)=price-fetcher + Wave 1 (identity-structure / fundamentals / filings-integrity / competitive-macro-risk, 4 template workers in parallel) + Wave 2a (forensic-scorer + institutional-positioning-scout via agentType) and returns the research bundle. SKIP the sequential E-I + J-bis.0 + K-bis.0 dispatches -- read their results from the bundle instead (each phase's text remains the authoritative spec of what the bundle section must contain; validate per the J-bis.0/K-bis.0 contract checks). The 13-WebSearch budget is DISTRIBUTED across workers (0/2/4/0/1/6), never expanded. Convergence gate: N/A returns = SUCCESSFUL; missing fields/dispatch failure -> one re-dispatch -> documented inline fallback (Tier-B phase text); pre-emptive skip = DEVIATION. thesis-critic (K.5) + claim-distributor (L.0) stay Agent-tool dispatches in BOTH tiers. Wave 3 verification: see K.5 STEP 4.

### Phase B: State-transition model (print only, BEFORE F11)

Emit expected-state summary to user:

    /invest state-transition model
    ==============================
    Ticker: <TICKER>
    Class hint: <stock | ETF | crypto | unknown -- will confirm in Phase E>
    Held: <Yes: <N.NNN> shares taxable + <M.MMM> shares Roth = <Z.ZZZ> combined>
          | Not currently held
    Active thesis exposure: <list of thesis tags from entity note OR hot.md>
    Entity note: <exists at wiki/entities/tickers/<TICKER>.md -- UPDATE branch>
                 | <absent -- CREATE branch will ground in _templates/entity.md>

    Topology: <dw (Workflow tool detected; Wave-1 fan-out per ref-dw-topology.md)
              | sequential (Tier-B; universal fallback)>
    Orchestrator model: <ORCHESTRATOR_MODEL from Phase A.7; logged passively, never branched on>
    Expected research: <sequential: 13 WebSearches across 5 phases E-I
      (2 identity + 4 fundamentals + 2 technical + 2 risk + 3 competitive-macro)>
      | <dw: 13 WebSearches DISTRIBUTED across 6 Wave-1 workers (0/2/4/0/1/6)>
    Wave 3 (dw only): <expected SKIP (non-boundary HOLD/SELL likely) | expected FIRE (--verify | boundary | BUY-candidate)>
    Expected Phase K analysis: wiki/investing/analyses/<ticker>-analysis-<YYYY-MM-DD>.md
      Path-collision: <none>
                    | <same-date exists; will use -<HHMM> timestamped variant>
                    | <--replace requested; will overwrite>
    Expected Phase L entity update:
      CREATE: new entity at wiki/entities/tickers/<TICKER>.md (frontmatter + 5 sections)
      OR
      UPDATE: existing entity updated via claim-to-section mapping
              (or short-circuit if all claims deduped)
    Expected Phase M peripherals:
      <watchlist.md if BUY/WATCH>, investing-research-log.md, ref-research-insights.md (if new insight),
      <investing-moc.md if new entity>, sessions-log.md, Calendar/daily/<today>.md
    Expected Phase O commit (prospective): agent(invest): <TICKER> analysis -- <verdict TBD>
    F11 flag: will be set at Phase C (after this print, before any Edit/Write)

    Proceed? (Any failure between C and O triggers N.halt with F11 retained;
    no partial commits.)

If `--preview`: print model and EXIT CLEAN. No F11, no writes.

Else: autonomously proceed (unless --confirm opt-in).

### Phase C: F11 set

Create `.claude/state/auto-commit-disabled`. Single flag covers entire invocation. Cleared only in Phase O after commit verification passes. Skip if `--preview` already exited.

### Phase D: Context Load (READ-only)

D.1 -- Portfolio (READ from path-guarded; WRITE would be blocked):
- `private/holdings-taxable.md` -- taxable positions
- `private/holdings-ira.md` -- Roth positions
- `<VAULT_ROOT>/CLAUDE.local.md` -- per-ticker constraints (e.g., VGT split)

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
- `Atlas/concepts/investing/doctrine.template.md` (v2 final added: invalidation rules, earnings protocol)
- `Atlas/sources/investing/ref-scoring-models.md` (v2 final added: Piotroski/Altman/Beneish methodology)
- `Atlas/sources/investing/ref-monitoring-rules.md` (v2 final added: alert thresholds)
- `Atlas/sources/investing/ref-earnings-playbook.md` (CONDITIONAL -- read whenever the ticker has an earnings print within ~45 days OR the analysis covers earnings mechanics: consensus formation, revision momentum, implied move, PEAD, beat-and-drop anatomy; thresholds as data. Serves the earnings-impact sections + the pre-earnings monitor analog; vNEXT Section 11 wiring 2026-06-10)
- `Atlas/sources/meta/ref-research-methodology.md`
- `Atlas/sources/meta/analysis-depth-standard.md`
- All three class refs loaded (cheap read): `ref-etf-evaluation.md`, `ref-crypto-landscape.md`, `ref-orbital-compute.md` (your sector deep-dive). Phase E class-confirmation determines which drives synthesis.

D.4 -- Canonical-frontmatter pre-check on entity note (if exists): if `categories:` != `[entity]`, HALT and recommend `/enrich --refresh <path>` first.

D.5 -- Compute `before_sha256` of body bytes for every file Phase K, L, or M will touch. Cache for Phase O gate.

D.6 -- Source-target mandate (audit 2026-04-28 5th-pass): aim for 25-50 distinct external sources cited in the analysis body. Soft floor 25 (warn if fewer), soft ceiling 50 (warn if exceeded). Source diversity target: 8+ distinct domains. If a /deep prompt exists at `wiki/research/prompts/{ticker}-*.md`, load it and use as research scaffolding (treat as Grade-B baseline citation already producing 100+ sources via claude.ai Research mode). Sources counted: inline `[Grade A|source|date]` markers + URL references in body. Phase D continues to next phase regardless of source count; soft floor warns but does not HALT (analyst judgment overrides on liquid-coverage tickers where 25 sources is excessive).

D.7 -- `--thesis <name>` lens overlay (ADDITIVE; verdict redesign 2026-06-06). Fires ONLY when the `--thesis <name>` flag is present (name resolving to a thesis essay at `Atlas/concepts/investing/theses/<name>.md`). The lens is a FRAMING overlay, never a replacement: first principles always runs in full. When set:
- Load the named thesis essay; extract its cohort membership + its quantified invalidation triggers.
- Weight the Phase Q coherence read toward the named thesis's cohort exposure (does this name add to or diversify the cohort).
- In Phase K, add a "Thesis-lens view" subsection: how this name looks specifically through `<name>`'s frame (cohort fit, thesis-specific kill criteria, marginal contribution to thesis concentration).
- **HARD CONSTRAINT: the lens CANNOT change the rating.** The K-bis.5 Step-1 spine sets the rating from first principles regardless of the flag; the lens only enriches the conviction rationale + the thesis-status read + the Variant View. If no flag is given, first principles runs alone (default). This guards against confirmation bias (a thesis lens that could move the rating would bias toward the named thesis).

### Phase E: Identity and Structure (2 searches) [Tier-B; Tier-A: `identity-structure` worker per A.8]

#### Phase E.0: DELEGATED dispatch to `price-fetcher` (broker-authoritative price + technicals; v3 wiring 2026-06-04; v4 contract) [Tier-A: bundle `price` from the quote-technicals worker -- do not re-dispatch]

ADDITIVE -- dispatch BEFORE the 2 Phase E WebSearches. Use the Agent tool with subagent_type `price-fetcher`, input `{equities: ["<TICKER>"], crypto: []}` (crypto-list instead for a crypto ticker). On success: use the returned `price` (broker-authoritative when `broker_authoritative: true`) + `extended_hours_*` for the TRADING DECISION header (Phase K-bis), and `rsi14`/`ma50`/`ma200`/`pct_from_52wk`/`next_earnings` to seed Phase G technical + Phase H short-interest. STILL run the 2 Phase E WebSearches for 52-week range / YTD / split-adjustment context + company identity -- the 13-WebSearch research-spine count is UNCHANGED. On dispatch failure (or Codex/headless/MCP-absent): proceed with the Phase E price WebSearch unchanged as the fallback. The TRADING DECISION header notes the AH price when material (>= AH-mover threshold).

Establish definitively:
- Security type (stock / ETF / fund / cryptocurrency) -- confirms Phase A.5 hint
- ETF: fund family, inception, AUM, expense ratio, benchmark, top 10 holdings + weights, total holdings count, overlap with held ETFs
- Stock: company overview, sector, industry, market cap tier
- Current price with freshness timestamp, 52-week range, YTD performance
- Stock-split adjustment: if split occurred <90 days ago, show pre-split + post-split prices explicitly
- Most important fresh catalyst with exact dates

### Phase F: Fundamental Analysis (4 searches) [Tier-B; Tier-A: `fundamentals` worker per A.8]

Execute per `.claude/skills/invest/ref-analysis-template.md` Metrics Catalog.

Stock categories: valuation (P/E, P/S, EV/EBITDA, PEG, FCF yield, shareholder yield); profitability + quality (margins + trends, ROIC, ROIC vs WACC, cash conversion, Piotroski F-Score per ref-scoring-models methodology, Altman Z-Score); growth (revenue + EPS + FCF CAGRs, Rule of 40); balance sheet (net debt/EBITDA, coverage, current ratio, maturity schedule); capital allocation (buyback 3yr, dividend + payout, CapEx % revenue, insider 12mo); forensic (Beneish M-Score per ref-scoring-models, Cash Conversion Cycle + 3yr trend, revenue quality, SBC dilution flag if SBC/Revenue >5%); advanced return decomposition (ROIC decomp NOPAT x Turnover, DuPont 5-factor, ROIIC, customer concentration from 10-K).

ETF categories: expense ratio vs category, tracking error, premium/discount to NAV, turnover, tax efficiency, factor exposures (value/momentum/quality/size/volatility), top-10 concentration, sector allocation, weighted P/E + P/B + ROE, flows (1mo/3mo/12mo), liquidity + bid-ask spread, overlap with SPY/VOO.

Crypto categories: tokenomics + supply schedule, on-chain activity, staking/validator dynamics, settlement-standards alignment (if applicable), regulatory exposure, exchange listings + liquidity.

Gate: reporting-period consistency (TTM vs forward).

### Phase G: Technical and Momentum (2 searches) [Tier-B; Tier-A: quote-technicals + competitive-macro-risk workers]

- 50-day + 200-day SMA position, golden/death cross
- RSI (14-day), MACD signal, relative strength vs S&P 500 (6-month)
- Volume: accumulation or distribution
- Key support + resistance levels
- Short interest ratio + days to cover
- Options intelligence: equity-only put/call ratio, IV percentile/rank vs 52-week, unusual activity (>$500K notional blocks, sweep orders)

### Phase H: Risk Assessment (2 searches) [Tier-B; Tier-A: competitive-macro-risk + filings-integrity workers]

- Annualized volatility (1yr), maximum drawdown from peak with dates
- Beta vs S&P 500, Sharpe (1yr + 3yr), Sortino
- Correlation to existing portfolio holdings
- Tail risk: scenarios causing 30%+ drawdown
- Advanced: Calmar (return / max DD), return distribution (skewness, kurtosis), factor exposure decomposition (Market/Size/Value/Momentum/Quality), scenario-based VaR at 2-sigma + 3-sigma from actual position size

### Phase H.2: Advanced Risk Metrics -- Short Interest + Options Flow (audit 2026-04-28 5th-pass; subsection of Phase H)

H.2.1 -- Short interest deepening:
- Short interest % of float; days-to-cover (SI / avg daily volume)
- Threshold logic: > 10% SI + < 2 days-to-cover = squeeze-risk flag (potential stress signal); > 10% SI + > 5 days-to-cover = legitimate-bear-thesis worth investigating; < 5% normal
- Trend (4-week change in SI): rising = bear-thesis strengthening; falling = bear-thesis fading

H.2.2 -- Options flow analysis:
- Put/call ratio by expiration window: 0-30 DTE versus 30-90 DTE asymmetry; rising 0-30 DTE put demand = hedging-demand signal (downside priced); rising long-dated calls = speculative-bull positioning
- IV term structure: upward-sloping = tail risk priced (cheaper near-dated, expensive long-dated); downward-sloping = inverted, often pre-event positioning (earnings, FDA decision, M&A rumor)
- Unusual activity threshold: > $500K notional blocks, sweep orders, late-day prints
- Gamma concentration: identify strike levels with > 1% of total open interest (potential pinning effect into expiration)

H.2.3 -- Cross-check with Phase J-bis insider data: short interest + insider cluster-buy = high-conviction divergence (insiders buying while shorts pile in = often resolves in insider direction; bear thesis flawed). Short interest + insider selling = aligned bearish signal worth heavy weight in Decision Sheet.

### Phase I: Competitive and Macro Context (3 searches) [Tier-B; Tier-A: competitive-macro-risk worker incl. edgar_compare peer-XBRL + FRED]

- Competitors or alternatives; moat (stocks); 2-3 alternative ETFs (ETFs)
- Macro sensitivity: rates, recession, inflation, regime
- Sector tailwinds/headwinds, regulatory risks
- Supply chain (semis priority): TSMC node utilization, HBM capacity + yield, CoWoS, equipment delivery, wafer pricing, book-to-bill
- Event-driven: 13D/13G at 5%, pending M&A/spin-off/restructuring
- Management quality: insider cluster buying (3+ in 30 days), governance flags, capital-allocation track
- Cross-asset: CDS spread trends, currency exposure by geography

Gate: supply-chain + competitive data within 30 days.

### Phase J: Portfolio Fit (hybrid live positions, vNEXT 7.4)

- **J.0 -- Live equity positions (both tiers):** load `mcp__robinhood-trading__get_equity_positions` via ToolSearch and pull live share counts for BOTH accounts at run time -- this replaces private/ files as the equity share-count source of record (kills the manual-refresh staleness inside the sizing math). CRYPTO quantities still come from `private/holdings-taxable.md` (the MCP has no per-coin positions tool) priced via fetch-prices.py: the book is HYBRID -- an equity-only total would shrink the denominator and FALSELY INFLATE thesis-concentration % toward amber trips. RECONCILIATION ASSERT: cross-check hybrid total + per-name counts vs private/holdings-taxable.md + private/holdings-ira.md; divergence (>0.5% book value OR any share-count mismatch) -> surfaced flag in Phase P, never silent. If positions return average cost basis, cross-check vs private/ and flag divergence; else private/ stays authoritative for basis. private/ files = interpretation layer (basis narrative, account doctrine, caveats) -- never deleted. MCP absent (Codex/headless) -> fall back to private/ share counts + WARN "positions source: private/ fallback (staleness risk)". D-SEC-1 deny block untouched -- read-only tools only.
- **J.0b -- Price anchoring:** ALL threshold math (J sizing + Q concentration) uses regular_market_close from the price-fetcher/quote-technicals return, per the ratified extended-hours doctrine. Live/AH values may be DISPLAYED with an as-of stamp; they NEVER feed a doctrine threshold.
- Exact math: `taxable shares x price = $X + Roth shares x price = $Y = $Z combined`. Dollar impact of scenario shown.
- Per-ticker constraints from CLAUDE.local.md applied (e.g., VGT: split-adjusted).
- If not held, state "Not currently held" explicitly.
- Correlation with existing holdings. Flag any pairwise correlation >0.7 (hidden concentration).
- Sector overlap; holdings overlap (ETFs).
- Position sizing: Half-Kelly `(Edge / Odds) x 0.5`, adjusted for correlation.
- Marginal risk contribution to portfolio volatility.
- Risk/reward shown: `(Target - Current) / (Current - Stop) = X:1`. 3:1 minimum for BUY.
- Best alternative use of capital (closest benchmark, peer, or current holding, with explicit R/R comparison).

Gate: portfolio math from actual share counts (live MCP positions when available; hybrid-reconciliation assert run).

### Phase J-bis: Institutional Positioning -- 13F + Politician + Insider (audit 2026-04-28 5th-pass)

J-bis.0 -- DELEGATED dispatch to `institutional-positioning-scout` subagent (PREFERRED path; Phase C wiring 2026-05-02):

**MANDATORY** (per Execution Rules): dispatch first, no pre-emptive skip. Subagent handles N/A returns gracefully (e.g., crypto inputs -> empty Dataroma/CapitolTrades/OpenInsider rows + confidence: N/A; that is a SUCCESSFUL dispatch, not a failure).

Use the Agent tool with subagent_type `institutional-positioning-scout`. Pass input: `{ticker: "<TICKER>"}`. The subagent handles Dataroma + CapitolTrades + OpenInsider in parallel internally and returns a structured positioning table + 3-line synthesis + freshness check + HIGH/MED/LOW confidence directly.

Validate subagent return:
- Markdown table with columns [Source | Signal | Date | Magnitude | Tier | Notes] -- exact column count
- 3-line cross-source synthesis present
- Composite freshness rating present (HIGH if all <30d, MED if 30-90d, LOW if >90d)
- Confidence rating present (HIGH if 2+ Tier-A sources directionally agree; MED/LOW per scout discipline)

On contract violation OR dispatch failure (timeout, rate limit, tool denial): after one re-dispatch, fall through to the J-bis.1-J-bis.4 inline fallback -- **relocated verbatim to `ref-dw-topology.md` Section 10** (read on demand at fallback time; Dataroma 13F overlay + CapitolTrades STOCK Act overlay + OpenInsider cluster-buy detection + the mandatory Decision Sheet output table). The fallback is reachable from BOTH tiers; its semantics are unchanged. Surface fallback in Phase P audit report: "Phase J-bis subagent dispatch failed (<reason>); used inline fallback per ref-dw-topology.md Section 10. Quality preserved; latency penalty ~30s."

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
| 2026-04-27 | NVDA entity note | Thesis CONFIRM | CHALLENGE | INVALIDATION-WARNING | High | Trigger /challenge thesis-<slug> |
```

J.5.4 -- Inconsistency-Log accumulation in entity note (compounding mechanism):
- Phase L Entity UPDATE writes detected inconsistencies into entity note's "## Inconsistency Log" section (CREATE section if absent)
- Format: dated entry per inconsistency: `### YYYY-MM-DD -- <metric>: prior <X> -> current <Y> (severity <Material|Minor|High>)`
- Log accumulates across analyses; future /invest invocations read this log in J.5.1 to detect REPEATED drift patterns (e.g., Piotroski has degraded across 3 consecutive analyses = sustained quality erosion, not noise)

J.5.5 -- Empty-prior-research short-circuit: if entity note absent AND no prior analysis exists, skip J.5.2-J.5.4. First-analysis tickers have no prior to compare against. Note in Decision Sheet: "Initial analysis; no prior research to compare; baseline established."

Gate: if any High-severity drift detected, surface as explicit warning in Decision Sheet BEFORE the BUY/SELL/HOLD rating is generated. Material-severity drift goes in entity Inconsistency Log without blocking.

### Phase K-bis: Quantitative Scoring Stack + Best-Investor Framework Rotation + TRADING DECISION header (audit 2026-04-28 5th-pass)

Phase K-bis reads `Atlas/sources/investing/ref-valuation-methodology.md` (reverse-DCF / implied-expectations method + the formalized EV/Sales-2D grid) for the composite valuation leg AND the forward-earnings bridge valuation (EV/Sales-2D factor per ref-scoring-models Sec 10.3); vNEXT Section 11 wiring 2026-06-10.

K-bis.0 -- DELEGATED dispatch to `forensic-scorer` subagent (PREFERRED path; Phase C wiring 2026-05-02):

**MANDATORY** (per Execution Rules): dispatch first, no pre-emptive skip. Subagent handles N/A returns gracefully (e.g., crypto/non-equity inputs -> all 12 metrics N/A + framework verdicts "Not applicable" + confidence: N/A; that is a SUCCESSFUL dispatch, not a failure).

[Tier-A: the `forensic` worker result in the A.8 bundle satisfies K-bis.0 -- validate the same contract, do not re-dispatch.] Use the Agent tool with subagent_type `forensic-scorer`. Pass input: `{ticker: "<TICKER>"}`. The subagent computes the Top-12 forensic stack (Piotroski/Altman/Beneish/Greenblatt/ROIC/FCF/PEG/SBC/GM-trend/accruals/capex-rev) from SEC primary + stockanalysis.com secondary; returns scorecard table + framework verdicts (Buffett/Lynch/Greenblatt/Burry) + restatement check + composite confidence.

Validate subagent return:
- 12 metrics present in scorecard table, each with HIGH/MED/LOW confidence rating
- Framework verdicts explicit PASS/FAIL across Buffett-compounder / Lynch GARP / Greenblatt magic / Burry deep-value
- Restatement check non-empty (even if "none")
- Composite confidence rating present

On contract violation OR dispatch failure: fall through to K-bis.1 inline fallback below. Surface fallback in Phase P audit report.

On dispatch success: use the returned 12-metric scorecard as K-bis.1 forensic-quantitative leg. The framework verdicts feed K-bis.3 reconciliation (50% forensic / 50% framework rotation per existing rule). Skip the inline forensic computation in K-bis.1; proceed to K-bis.2 framework rotation (which remains main-thread because it requires reading `ref-investor-frameworks-2026.md` and applying 3 frameworks per ticker category -- not subagent-shaped).

K-bis.1 -- Quantitative scoring stack (FALLBACK; runs only if K-bis.0 failed):
- Piotroski F-Score: 0-9 numeric value with component breakdown (profitability 4 + leverage/liquidity 3 + operational efficiency 2)
- Altman Z-Score: numeric value with zone classification (safe > 2.99 / grey 1.81-2.99 / distress < 1.81)
- Beneish M-Score: numeric value with manipulation classification (likely manipulator > -1.78 / acceptable < -2.22)
- Reverse DCF implied growth rate: solve for revenue growth that justifies current price; compare to consensus 5-year forward CAGR
- Greenblatt Magic Formula combined-rank: rank vs sector universe on ROIC + EBIT/EV; top-quintile = strong; bottom-quintile = caution
- DuPont 5-factor decomposition: ROE = (margin) x (asset turnover) x (leverage) x (tax retention) x (interest retention)
- Composite Quality Score 0-100: 30% Piotroski (normalized) + 20% Altman (normalized) + 20% Beneish (normalized inverse since lower is better) + 15% ROIC (normalized vs sector) + 15% valuation (FCF yield + EV/EBITDA percentile)
- **EPS<0 FORWARD-EARNINGS BRIDGE (routing -- runs for ALL names BEFORE scoring_path is set; ratified 2026-06-07, [[ref-scoring-models]] Section 10):** if trailing TTM OPERATING income < 0, route per Section 10 -- substitute the bridge forensic composite (growth-quality 5-factor: revenue-growth 25% + GM level/trend 20% + cash-runway 20% + path-to-profitability 20% + EV/Sales-2D 15%; Altman dropped to the solvency gate) and the Pre-Profit Grower framework category ([[ref-investor-frameworks-2026]] Sec 13: Druckenmiller/Cohen/Marks). MASTER INVARIANT: positive-eps-standard is reachable ONLY when TTM operating income >= 0 -- a loss-maker NEVER runs the standard composite. FENCES: TTM revenue <$20M OR EV/Sales >100x -> pre-revenue guard (composite N/A, rating NR); cyclical (declining-revenue OR sign-mixed op-income lookback: >=1 loss FY AND >=1 positive-op-income FY in the last 4 FY -- the RECOVERED-cyclical/loss-trough read per ref-scoring-models Sec 10 intent) -> STEP 2a: if still op-income>=0 standard path + MANDATORY mid-cycle-margin note (HALT if absent from analysis body; Wave-3 routing skeptic checks this), if op-income<0 bridge w/ cyclical caveat (v2 normalized-earnings bridge deferred); any TTM op-income<0 -> bridge (the -5% trailing-4Q-avg-op-margin band is HYSTERESIS-ONLY -- it governs RETURN to standard, which requires op-income>=0, never letting a loss-maker through). NBIS-trap: GAAP NI>0 but op-income<0 forces the bridge. Apply the data-integrity gate (Sec 10.2: use CURRENT shares not TTM weighted-avg; sum 4 quarters if any TTM line >4x max quarter). Valuation/target = EV/Sales + path-to-profitability; for EV/Sales >50x, R/R target = MIN(analyst PT, fundamentals fair value). Record `scoring_path` in analysis frontmatter. **When op-income >= 0 this NOTE is INERT and the formula above runs VERBATIM (byte-identical positive-EPS output).**

K-bis.2 -- Best-Investor Framework Rotation per `Atlas/sources/investing/ref-investor-frameworks-2026.md`:
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
**Confidence**: <X%> (<HIGH|MEDIUM|LOW> band; cap-reason if applied)
**Conviction**: <X%> (modulated per K.5 Step 2: conviction_base <Y%> minus failure-mode penalty <Z>, floored at 20%; separate from confidence per Quality Standards)
**Time Horizon**: <3-6mo | 12mo | 24mo+>
**Risk/Reward**: <X:1> (passes/fails 3:1 hurdle for BUY, 4:1 for STRONG BUY)
**Composite Quality Score**: <X/100> (forensic 50% + framework 50%)
**Validation status**: <on BUY/STRONG BUY only, during the calibration window> MECHANISM-VALIDATED, not outcome-validated -- the verdict redesign is ratified on mechanism (backtest 2026-06-06) but the Phase-R monitor has <N>/8 calls realized at 3mo. Treat the Conviction % as LOAD-BEARING for position sizing until the monitor closes (~1-2 months from 2026-06-06). Omit this line once Phase R reports >=8 realized-at-3mo calls.

**Summary** (3-5 sentences synthesizing the analysis): <one-paragraph thesis statement covering: what the company does + key catalyst + valuation + main risk + position sizing recommendation. Written for a portfolio manager who has 30 seconds to make a decision.>
```

K-bis.5 -- Rating logic: STEP 1, FIRST-PRINCIPLES RATING (the spine; verdict redesign ratified 2026-06-06, [[the ratified verdict-redesign decision record]]).

The rating is a deterministic function of DATA: (a) composite quality score (K-bis.3, 0-100), (b) R/R vs hurdle [HARD gate], (c) valuation/mispricing read, (d) catalyst proximity + direction, (e) the THESIS-STATUS GATE. The adversarial counter-thesis (Phase K.5) does NOT veto this rating -- it routes to conviction + kill-criteria + thesis-status per Step 2-3. Tier thresholds (5-tier scale; thresholds UNCHANGED from prior design -- these are the hard gates that contain over-bullish regression):

- STRONG BUY: composite >= 80 AND R/R >= 4:1 AND multi-vector signal (Dataroma + OpenInsider both positive) AND thesis != INVALIDATE
- BUY: composite 60-79 AND R/R >= 3:1 AND thesis != INVALIDATE
- HOLD: composite 40-59 OR thesis-intact-but-no-edge OR composite 60-79 but R/R < 3:1 OR thesis == INVALIDATE
- SELL: composite 20-39 OR kill-criteria approached (within 10% of trigger)
- STRONG SELL: composite < 20 OR kill-criteria triggered OR multi-vector negative signal (Dataroma reduce + insider selling + bearish Phase J.5 drift)

**TIER PRECEDENCE (applies ONLY when 2+ tiers' conditions are simultaneously met; then apply the MOST BEARISH tier met, in order STRONG SELL > SELL > HOLD > BUY > STRONG BUY):** a DATA-gated SELL/STRONG SELL (composite-band, kill-criteria-approached/triggered, thesis-INVALIDATE-with-deserved-SELL, multi-vector-negative) ALWAYS overrides a HOLD that arises only from the composite-40-59 band or the R/R<3:1 demotion. A composite-band HOLD must NEVER silently suppress a deserved SELL. (Strategist-ratified 2026-06-06 closing a pre-existing latent hole under the GUARD-1 mandate; bearish-direction-only -- can move a verdict from HOLD toward SELL, can NEVER create a wrong BUY.)

**THESIS-STATUS GATE (Step 1e):** bites the rating ONLY on a DATA condition, never on "a coherent bear case exists":
- INVALIDATE -> rating UPSIDE capped at HOLD (downside fully open); SELL/STRONG SELL FIRE per the data-gate rows when their conditions are met -- INVALIDATE never blocks a deserved SELL. Note the resolution of the latent contradiction: INVALIDATE is defined as a TRIGGERED kill criterion, and the STRONG SELL row fires on kill-criteria-triggered -- so an INVALIDATE'd name with a triggered kill criterion resolves to STRONG SELL (via the TIER PRECEDENCE rule above), not capped at HOLD.
- kill criterion WITHIN 10% of trigger -> SELL (the existing K-bis.5 data rule).
- CHALLENGE / CONFIRM -> NO rating cap (informational only; feeds conviction + Variant View, not the rating).

**SOLVENCY-RUNWAY GATE (Step 1f; SCORED gate -- fires ONLY when scoring_path == negative-eps-bridge; on the positive-EPS path runway is NOT computed so this never evaluates -- INERT, additive, bearish-direction-only, can NEVER create a wrong BUY; ratified 2026-06-07 per [[ref-scoring-models]] Section 10):** runway < 4 quarters AND no committed financing -> rating UPSIDE capped at HOLD (downside fully open); runway < 2 quarters -> SELL (distress); runway 4-8 quarters AND composite >= 60 -> BUY allowed with a "runway-constrained; next raise is a kill-criterion" note. Pre-revenue / negligible-revenue names -> rating NR (no rating, narrative-only; NOT a 6th tier), or SELL if runway < 12mo. The existing tiers + TIER PRECEDENCE + THESIS-STATUS GATE above are preserved VERBATIM; this is an added guarded clause.

**GUARD-1 -- the bearish/trim side is DATA-driven and survives the veto removal.** SELL and STRONG SELL fire on their own DATA gates (composite 20-39, kill-criteria-approached, kill-criteria-triggered, thesis INVALIDATE, multi-vector-negative) -- these are INDEPENDENT of the Phase K.5 conviction modulator and were never part of the removed veto sentence (enforced by the TIER PRECEDENCE rule above: a data-gated SELL/STRONG SELL is never suppressed by a composite-band HOLD). Removing the narrative veto does NOT weaken the skill's ability to say SELL/TRIM; it only stops a plausible-but-untriggered bear narrative from auto-downgrading an otherwise-rateable BUY. Phase Q concentration-trim (thesis and single-name ceilings per [[doctrine.template]]; interim phase-in as configured) is a separate, untouched pathway. **POST-REDESIGN CALIBRATION TRIPWIRE:** if a post-redesign calibration tripwire is configured in the doctrine template, a configured ticker rating BUY or STRONG BUY will HALT and surface for review -- indicating a possible R/R-gate defect, not a thesis change.

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

### Phase K.5: Variant view -- thesis-critic adversarial cross-check (DELEGATED; Phase C wiring 2026-05-02)

Before Phase K composes the analysis body, dispatch the `thesis-critic` subagent for adversarial stress-test against the proposed rating from K-bis.4.

**MANDATORY** (per Execution Rules): dispatch first, no pre-emptive skip. thesis-critic is asset-class agnostic -- it stress-tests any thesis/rating regardless of equity vs crypto vs commodity. Skipping based on "this won't apply" is a DEVIATION.

Use the Agent tool with subagent_type `thesis-critic`. Pass input: `{ticker: "<TICKER>", primary_thesis: "<thesis-slug from Phase D>", primary_drivers: [<top-3 drivers from Phase E-I>], market_regime: "<from Phase I>", proposed_rating: "<K-bis.4 TRADING DECISION rating>"}`.

Validate subagent return:
- 3-5 ranked failure modes with calibrated % probability + detectability + recoverability + cascade + invalidation trigger
- Each failure mode includes evidence with `[grade | source | date]` per-fact provenance
- Ideological Turing Test (ITT) self-score present and >=7/10

If ITT self-score <7/10: thesis-critic rejected its own output (bear case not sufficiently steelmanned). Re-dispatch ONCE with strengthened bear-evidence prompt. If still <7 OR dispatch fails: fall back to inline Variant View composition from `Atlas/concepts/investing/doctrine.template.md` invalidation triggers + standard Variant View skeleton.

On dispatch success: compose Variant View section in Phase K body using the returned failure modes. The failure modes route to THREE non-veto outputs (Steps 2-3 of the verdict redesign; the prior "escalate the rating one tier" veto sentence was REMOVED 2026-06-06 per [[the ratified verdict-redesign decision record]] -- the adversarial rigor is fully preserved, it just no longer vetoes the rating):

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

**STEP 3 -- KILL-CRITERIA SURFACER + THESIS STATUS (monitoring, not veto):**
- Populate the Kill Criteria section from the failure modes' quantified invalidation triggers (these are the monitoring thresholds).
- Set thesis_status CONFIRM / CHALLENGE / INVALIDATE. INVALIDATE requires an ACTUAL triggered kill criterion (data crossing a quantified threshold), never a narrative; CHALLENGE is the soft state.
- The rating cap (if INVALIDATE or near-trigger) was ALREADY applied by the Step-1 K-bis.5 THESIS-STATUS GATE -- Step 3 only records the status + monitoring triggers; it does NOT re-touch the rating.

The rating set by K-bis.5 Step 1 is FINAL after this routing (the counter-thesis changed conviction + kill-criteria + thesis-status, not the tier). If thesis == INVALIDATE caused a Step-1 cap, note it in the K-bis.4 header rationale + Phase P. Surface the failure-mode reasoning + the conviction modulation arithmetic in the Phase P audit report.

**STEP 4 -- WAVE-3 ADVERSARIAL VERIFICATION GATE (TOPOLOGY=dw; vNEXT):** after the draft verdict + K.5 modulation exist, evaluate the firing rule -- FIRE when ANY of: draft verdict >= BUY; thesis_status CHANGED vs the prior entity state; composite within +/-5 of a tier boundary (20/40/60/80); `--verify` flag. On fire: invoke the `invest-verify` workflow (`.claude/workflows/invest-verify.js`) with the draft bundle (verdict, composite, conviction, R/R, entry/stop/target, scoring_path, ttm_operating_income, thesis_status + prior, claims_with_prov, quote_technicals, fundamentals_bundle, routing_trace, run_timestamp). Four read-only skeptics (data-integrity incl. share-count >1.5x; R/R; routing incl. STEP 2a; provenance) run in parallel, fail-closed. ANY refutation -> Phase N HALT (F11 stays set, ZERO writes, refutation surfaced -- no auto-override). Non-boundary HOLD/SELL without --verify: SKIP Wave 3 (TIER PRECEDENCE makes bearish the safe direction; this is the cost lever) and report the skip in Phase P. On TOPOLOGY=sequential: the --verify flag triggers an inline data-integrity re-derivation (sample 5 composite inputs + the share-count >1.5x check via edgar_trends) instead -- same refutation -> N HALT semantics.

### Phase K: Compose Analysis File

K.1 -- Pre-Output 10-point gate (see above). HALT on any violation.

K.2 -- Read `.claude/skills/invest/ref-analysis-template.md` for frontmatter schema, 25-section body skeleton, metrics catalog detail, three `<!-- CHART:* -->` contracts, and `<!-- INGEST:claims -->` coordination block format.

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

K.6 -- Tag vocabulary assertion before write: only `topic/*`, `ticker/<TICKER>`, `company/*`, `thesis/*`.

### Phase L: Entity Update (CREATE or UPDATE branch)

L.0 -- DELEGATED dispatch to `claim-distributor` subagent (PREFERRED path for UPDATE branch; Phase C wiring 2026-05-02):

CREATE branch (entity absent): skip L.0; entity creation needs full Phase L inline logic to ground in `_templates/entity.md`. Subagent dispatch only applies to UPDATE branch where the existing entity body must be preserved byte-exact outside insertion windows.

UPDATE branch (entity exists): **MANDATORY** dispatch (per Execution Rules) -- no pre-emptive skip. Use the Agent tool with subagent_type `claim-distributor`. Pass input: `{entity_path: "wiki/entities/tickers/<TICKER>.md", claims: [<extracted from Phase K body's INGEST:claims block>], session_id: "<current-session-id>"}`. The subagent reads the existing entity, computes pre_sha256, classifies each incoming claim against existing content via marker_sig dedup, tiers contradictions (Tier 1 auto-resolve / Tier 2 flag / Tier 3 reject / defer if ambiguous), and returns proposed Edit operations as JSON.

Validate subagent return:
- JSON with `entity_path`, `edits[]`, `body_preservation` (pre_sha256 + expected_post_sha256_outside_inserts), `zero_new_claims_short_circuit`, `summary` counts
- pre_sha256 matches current entity body hash (re-compute and compare; HALT on mismatch = entity changed mid-dispatch)
- Each `op` in edits has anchor specification (anchor_after for insert, anchor_line for replace)

If `zero_new_claims_short_circuit: true`: skip Phase L entity write entirely (per existing v2 final discipline at line 49). Phase P reports "entity unchanged (all N claims deduped per claim-distributor)."

On contract violation OR dispatch failure: fall through to inline UPDATE branch logic below (existing manual claim-extraction + marker-sig dedup + Tier classification). Surface fallback in Phase P audit report.

On dispatch success: parent /invest performs the atomic Edit operations from the returned `edits[]` array, verifying post-Edit sha256 matches `expected_post_sha256_outside_inserts`. Mismatch = HALT; rollback. Tier-2 flagged conflicts get inline annotation in entity Inconsistency Log (Phase J.5.4 mechanism).

Read `.claude/skills/invest/ref-entity-update-semantics.md` for CREATE-vs-UPDATE branching, claim-to-section mapping, marker-signature dedup, contradiction tiering, body-preservation sha256 invariant, symmetric back-link protocol.

**CREATE branch** (entity absent at `wiki/entities/tickers/<TICKER>.md`):
- Ground in `_templates/entity.md`.
- Canonical frontmatter: `categories: [entity]`, `type: ticker`, `ticker: <TICKER>`, `sector: <from-analysis>`, `thesis: [<detected-list>]`, `accounts: [<taxable|roth|both|none>]`, `tags: [ticker/<TICKER>, thesis/<...>, topic/<...>]`, `related: ["[[investing-moc]]", "[[<thesis-file>]]", "[[<ticker>-analysis-<date>]]"]`.
- Populate 5 sections with extracted claims + per-fact provenance.
- MOC back-link: `[[investing-moc]]` in `related:`.

**UPDATE branch** (entity exists):
- Apply claim-to-section mapping (Financial signals / Thesis Fit / Risks / Catalysts / Recent).
- Marker-signature dedup `(entity, metric, value, date)` skips existing claims.
- Contradiction tiering: Tier 1 auto-resolve newer-supersedes-older; Tier 2 flag similar-authority; Tier 3 reject lower-authority.
- Per-fact provenance: `- <fact> (per [[<ticker>-analysis-<YYYY-MM-DD>]])`.
- **Zero-new-claims short-circuit** (v2 final): if count of net-new claims after dedup == 0, SKIP entity write entirely. Do NOT bump `updated:`. Phase P reports "entity unchanged (all N claims deduped)." File sha256 unchanged.
- Else: apply Edit; bump `updated:`; compute `after_sha256`; assert additive-only diff.

**Symmetric back-link**: entity `related:` gains `[[<ticker>-analysis-<YYYY-MM-DD>]]` (reciprocal to analysis's `[[<TICKER>]]`). Skip if already present (idempotent).

### Phase M: Peripheral Updates (atomic, sha256-invariant)

All updates body-preserving and marker-signature deduped.

- `Atlas/concepts/investing/watchlist.md` (BUY or WATCH only): add/update ticker row with key levels + catalyst dates. Symmetric back-link to analysis.
- `Atlas/concepts/investing/investing-research-log.md`: append `[<date>] [<TICKER>] <verdict> <conviction%> <confidence%> <model>`. Marker-sig dedup on `(ticker, date, model)`. Model = current session's model ID.
- `Atlas/sources/investing/ref-research-insights.md`: only if a new analytical insight emerged (substantive threshold: cross-ticker pattern / sector rotation signal / thesis challenge / previously-unseen driver). Append `[<date>] [<TICKER>] -- <insight>`.
- `Atlas/_MOCs/investing-moc.md`: back-reference row if missing (on CREATE branch).
- `Calendar/decisions/sessions-log.md`: append in /retro v2.1 canonical schema (Date / Title / Domain / Focus / Decisions ratified / Skills invoked / Artifacts / Related). Marker-signature on `(date, skill, ticker)` enables /retro merge.
- `Calendar/daily/<today>.md`: append `- [HH:MM] /invest <TICKER> -> <verdict> (conv:<X%> conf:<Y%>)` under `## Sessions Run`. Recompute daily-note `before_sha256` immediately before this write to handle UserPromptSubmit hook race.
- `wiki/investing/calibration-monitor.md` (Phase R; verdict redesign 2026-06-06): append one row per call -- see Phase R for the row schema + shadow-rating computation (vNEXT: row includes the two END-appended columns `orchestrator_model` + `topology`; historical rows stay byte-identical). Create the file with canonical frontmatter if absent (`categories: [wiki]`, `type: report`). Marker-sig dedup on `(date, ticker)`. This is the rolling-Brier rollback evidence base; the append is atomic with the analysis commit. SHADOW RUNS (--no-entity --no-peripheral A/B validation) write NO monitor row -- the Brier population must contain no A/B artifacts.

**Never write** (surface as follow-up instead):
- `private/holdings-taxable.md`, `private/holdings-ira.md` -- path-guarded. Phase P emits structured patch block user can paste manually.
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

O.1 -- Pre-commit gate: verify sha256 body-preservation invariants on every updated file. HALT with specific failing file if any outside-insertion-site bytes differ from `before_sha256` (modulo strictly-additive diff per file class).

O.2 -- F14 narrow staging: explicit pathspecs.

    git add <analysis-path> <entity-path> <peripheral-paths-that-were-written>

O.3 -- Commit. Format:

    agent(invest): <TICKER> analysis -- <verdict> <conviction%>

    <one-line rationale: key driver of verdict>

    Analysis: <analysis-path>
    Entity: <CREATE | UPDATE N claims added, M deduped | UNCHANGED all deduped>
    Peripherals: <list of touched paths>
    Confidence: <X%> (calibrated; cap applied: <none | Grade-C 70% | Grade-D 60% | STALE 65%>)

    Findings applied: F11, F14, F16, F17.

ASCII only. No Co-Authored-By.

O.4 -- Post-commit verification:
- Co-Authored-By absent: `git log --format='' -1 HEAD | grep -cE '^Co-Authored-By:'` returns 0 (F17).
- Bytes spot check: re-read a representative updated file; confirm body bytes match post-write state.
- Commit SHA captured for Phase P.
- Expected staged set matches actual (F14 invariant).

O.5 -- Clear F11: `rm .claude/state/auto-commit-disabled`. Only after O.4 passes. Assert absence.

### Phase P: Audit Report (v2 final: conviction + confidence separate, calibration cap reported, structured private/ patches)

Emit to user:
- **Analysis**: path + verdict + conviction% + confidence% (with cap-reason if applied)
- **Calibration monitor** (Phase R): `<N> calls logged, <M> realized at >=3mo; rolling Brier(new) <x> vs (shadow) <y>; rollback trigger <not-armed | armed-but-not-fired | FIRED>`. While M < 8: note "MECHANISM-VALIDATED window open". On any calibration-tripwire-configured ticker rating BUY/STRONG BUY: surface the R.4 tripwire HALT.
- **Entity**: CREATE or UPDATE branch; `N facts added / M deduped / K Tier 1 auto-resolved / L Tier 2 flagged`; OR "UNCHANGED (all deduped)" if zero-new-claims short-circuit fired
- **Peripherals**: which touched, which skipped, reasons
- **Commit**: SHA + F14 pathspec list
- **Subagent dispatch report** (Phase C wiring 2026-05-02): per dispatched phase (J-bis.0, K-bis.0, K.5, L.0) emit one of:
  - `DISPATCHED` -- subagent ran successfully, output integrated into analysis
  - `DISPATCHED (N/A return)` -- subagent ran successfully and returned an N/A-shaped output (e.g., crypto input on equity-shaped subagent); N/A propagated to Decision Sheet verbatim
  - `FALLBACK` -- legitimate dispatch failure; report exact reason: "contract violation: <field missing>" / "timeout after <Xs>" / "rate limit hit" / "tool denial: Agent not in allowed-tools" / "hard subagent crash"; inline fallback executed
  - `DEVIATION` -- pre-emptive skip without legitimate failure; report the judgment given ("declared N/A for crypto", "decided subagent wouldn't help", etc.); flag as discipline breach; create sessions-log entry capturing the pattern for future correction
- **Topology report (TOPOLOGY=dw)**: per-wave summary -- `Wave 1: <N dispatched, M converged, K fallback>; Wave 2a: <forensic + positioning status>; Wave 3: <SKIPPED (non-boundary, no --verify) | <4 skeptics, N refutations>>`; ws_actuals vs the 0/2/4/0/1/6 budget map; token actuals vs INVEST_DW_TOKEN_BUDGET; `retrieval_degraded` worker list (+ the Phase 0 `phase0_hits=0` line when applicable); hybrid-reconciliation result (clean | divergence flag detail)
- **Follow-up flags**:
  - Thesis-status changes needing user confirmation (Pattern 20; never auto-edit theses)
  - Structured patch block for `private/holdings-taxable.md` or `private/holdings-ira.md` manual updates:

        # Recommended patch for private/holdings-taxable.md (path-guarded; apply manually)
        Under <TICKER> entry:
          thesis: orbital-compute (CHALLENGE)   # was: CONFIRM
          reason: Phase I supply-chain data showed capacity ease 2026H2
          date-flagged: YYYY-MM-DD

  - /ingest recommendation: if analysis contains cross-entity claims beyond focal ticker, emit copy-paste `/ingest <analysis-path>`.
  - Invalidation signal: if AVOID on held position, emit "recommend thesis re-evaluation via /challenge <thesis>".
  - Brokerage freshness: if `holdings-taxable.md updated:` is >30d old, WARN ("portfolio math may be stale").

### Phase Q: Cross-Position Coherence Check (audit 2026-04-28 5th-pass; portfolio doctrine compliance)

Q.1 -- Post-decision portfolio coherence query:
- For the focal ticker's primary thesis, query existing entity notes + the Phase J.0 hybrid book (live MCP equity counts + private/ crypto layer; regular_market_close anchored per J.0b) for total thesis-level exposure -- holdings-taxable.md + holdings-ira.md remain the reconciliation baseline + interpretation layer
- If primary thesis is `thesis-<slug>`, sum all positions tagged to that thesis by current dollar exposure
- Compare to [[doctrine.template]] ceilings: per [[doctrine.template]]: THESIS_CAP_AMBER / THESIS_CAP_RED (interim phase-in as configured); OTHER_THESIS_FLAG for every other thesis; SINGLE_NAME_AMBER / SINGLE_NAME_RED for any single name
- Read `Atlas/sources/investing/ref-factor-lens.md` and compute the factor-level concentration view ALONGSIDE the thesis ceilings -- the factor lens does NOT change doctrine thresholds; it adds the cross-thesis factor read (several theses can be ONE growth-momentum factor bet) that the 2026-06-10 challenge sweep flagged as Phase Q's blind spot (vNEXT Section 11 wiring 2026-06-10)

Q.2 -- Concentration-cascade detection:
- If thesis exposure exceeds its cap post-implementation (THESIS_CAP_AMBER per [[doctrine.template]]; OTHER_THESIS_FLAG for other theses) OR any single name exceeds SINGLE_NAME_AMBER post-implementation:
  - Surface explicit warning in Phase P output: "Implementing this BUY would push <thesis-slug> exposure from 12.3% to 15.1%, crossing the THESIS_CAP_AMBER threshold -- conscious-flag + sleep-gate (still under THESIS_CAP_RED)"
  - Recommend rebalancing cascade: "Trim [N] shares of [TICKER_A] + [M] shares of [TICKER_B] OR delay this BUY until existing positions are trimmed"
  - Compute exact share-count math: "Current portfolio $[PORTFOLIO_VALUE] x THESIS_CAP_AMBER = $[thesis-ceiling] - current <thesis-slug> ~$[thesis-current] = ~$[headroom] headroom to the interim threshold; recommended BUY amount vs. headroom comparison"

Q.3 -- ETF overlap interaction:
- If focal ticker is an ETF, recompute look-through concentration including the ETF's holdings
- If focal ticker is a stock that overlaps with held ETFs (e.g., NVDA in VGT), increment effective exposure by overlap weight

Q.4 -- Newly-discovered concentration risks:
- Cross-reference focal ticker's sector + industry + thesis against existing portfolio
- Surface any newly-discovered concentrations not previously flagged: "VGT analysis reveals 33% holdings overlap with individual held positions; combined effective <thesis-slug> concentration is [CONCENTRATION], approaching THESIS_CAP_AMBER -- arm the exit ladder, do not force a mechanical trim"

Q.5 -- Output: Cross-Position Coherence section appended to Phase P audit report (before user emit). Includes:
- Current thesis-level exposure %
- Post-recommendation thesis-level exposure %
- Doctrine-ceiling compliance verdict (compliant / amber / red)
- Recommended rebalancing sequence if non-compliant
- Note: Q is informational only; does NOT block the BUY/SELL/HOLD rating from K-bis. User makes final call on whether to implement focal-ticker recommendation given doctrine constraints.

Gate: Q.5 output mandatory in Phase P emit. HALT if portfolio data unavailable (private/holdings-taxable.md or holdings-ira.md unreadable; defer to /networth refresh).

### Phase R: Calibration Continuity Monitor (verdict redesign 2026-06-06; CONDITIONAL-RATIFY rolling check)

The verdict redesign (K-bis.5 Step 1 spine + K.5 Steps 2-3) was ratified on MECHANISM, not on a one-shot outcome backtest (the 40-call sample had zero >=3mo-realized horizons -- stress-test failure-mode D7). Phase R is the pre-committed rolling check that closes that gap. It WRITES (via the Phase M append) and is purely additive -- it never touches the rating.

R.1 -- Shadow rating (the comparison baseline). Alongside the FINAL Step-1 rating, compute the **OLD-logic shadow rating**: what the REMOVED veto sentence would have produced -- i.e., if any K.5 failure mode has probability > 40% AND cascade-magnitude HIGH, downgrade the Step-1 rating one tier (BUY -> HOLD; HOLD -> SELL). This is cheap (the failure modes already exist from the K.5 dispatch) and is the apples-to-apples NEW-vs-OLD pair the monitor needs.

R.2 -- Log row. Append to `wiki/investing/calibration-monitor.md` (Phase M write):
```
| date | ticker | new_rating | shadow_rating(old-logic) | conviction% | R/R | composite | thesis_status | ret_1mo | ret_3mo | ret_6mo | orchestrator_model | topology |
```
The `ret_*` columns are left blank at write time and backfilled by `tools/score-outcomes.py` (R.5) or a later /invest run on the same ticker (the realized-return horizons accrue over weeks). The two END-appended columns (vNEXT) carry the Phase A.7 passive log; pre-vNEXT rows lack them and score as the `sequential-legacy` stratum.

R.3 -- Rollback trigger (PRE-COMMITTED; do not re-litigate at fire time). Once >= 8 logged calls have reached >= 3mo realization: compute rolling Brier(new_rating) vs rolling Brier(shadow_rating). **If Brier(new) is WORSE than Brier(shadow) by > 0.05 AND the gap is NOT attributable to a single name or a single crash window** -> revert the redesign: restore the removed K.5 veto sentence (the exact prior text is preserved in [[the ratified verdict-redesign decision record]] + git history at the pre-redesign commit) and bring it back for re-design. If the gap IS attributable to one name/crash (the backtest's exact confound), do NOT roll back; note it and keep monitoring.

R.4 -- Post-redesign calibration tripwire (continuous, not gated on the 8-call window). If any configured-ticker analysis under the new logic rates BUY or STRONG BUY and a calibration tripwire is set in the doctrine template, HALT immediately and surface for review -- indicating a possible R/R-gate defect, not a thesis change. (The K-bis.5 GUARD-1 block states this same tripwire at the rating site; Phase R is the monitoring backstop.)

R.5 -- Output + backfill: run `python tools/score-outcomes.py --dry-run --json` (deterministic; yfinance offline) to compute the monitor state; drop `--dry-run` when eligible blank `ret_*` cells exist past their horizons (the in-session run may overwrite with broker-authoritative MCP closes where available -- MCP-primary honored at this layer). The script emits BOTH pooled and TOPOLOGY-STRATIFIED rolling Brier (groupby the `topology` column; the R1 freeze rule on RATING_PROB_MAP applies -- constants immutable without a /decide + dual-map re-score). Emit the one-line Phase-R status in the Phase P audit -- "Calibration monitor: <N> calls logged, <M> realized at >=3mo; rolling Brier(new) <x> vs (shadow) <y> [pooled]; stratified: <per-stratum or insufficient-n>; rollback trigger <not-armed | armed-but-not-fired | FIRED>." While N-realized < 8: "MECHANISM-VALIDATED window open; BUYs carry the Validation-status note in their TRADING DECISION header." **GUARD-2 stratification (rider S1):** the R.3 rollback trigger is EVALUATED on pooled Brier, but any rollback (or promotion) decision MUST first check the stratified view -- if the gap is confined to a single topology stratum, the rollback target is the TOPOLOGY (revert to Tier-B), not the verdict redesign; a single-population artifact must never revert the spine.

R.6 -- Resume rule (TOPOLOGY=dw). Any mid-run interruption: resume via `Workflow({scriptPath: ".claude/workflows/invest-<research|verify>.js", resumeFromRunId: "<wf_id>"})` -- completed agents return cached; NEVER re-run a finished wave or re-spend its tokens. Sequential runs are unaffected (N.halt + idempotent re-invoke remains the recovery path).

## Examples

### Example 1: New ticker, first analysis (CREATE entity)

`/invest KLAC`. Entity note absent. Phase B state-transition prints CREATE branch; user confirms. Research phases complete. Phase K writes `wiki/investing/analyses/klac-analysis-2026-04-22.md` with verdict WATCH, conviction 55%, confidence 75%. Phase L CREATE branch grounds entity in _templates/entity.md with 5 sections populated. Phase M appends to research-log, investing-moc, sessions-log, daily note. Atomic commit: 5 paths. Phase P /ingest recommendation NO (single-ticker analysis per /enrich v9 T3 rule).

### Example 2: Held ticker, UPDATE entity (typical case)

`/invest NVDA`. Entity exists; UPDATE branch. Phase L extracts 18 claims; dedup skips 12 (already present from prior /ingest of ref-orbital-compute-deep-dive); 4 apply additively; 2 Tier-1 auto-resolve (Q3 backlog superseded by Q4). Entity `updated:` bumps. Phase M atomic peripherals. Commit: 6 paths.

### Example 3: Same-day intraday re-analysis (timestamped variant)

9:31 AM: `/invest NVDA` writes `nvda-analysis-2026-04-22.md`. 2:15 PM: post-earnings gap; `/invest NVDA` again. Path-collision detected; default to `nvda-analysis-2026-04-22-1415.md` (preserves archival rule, no --replace needed). Entity UPDATE with new claims. Both analyses preserved.

### Example 4: Explicit error-correction overwrite

9:31 AM analysis had wrong share count. `/invest NVDA --replace`. Overwrites `nvda-analysis-2026-04-22.md` (explicit destructive). Entity re-extracted; dedup skips previous claims; only corrections land.

### Example 5: Zero-new-claims short-circuit

`/invest ORBC-DEMO` day after a /ingest ran on ref-orbital-compute-deep-dive that fully covered ORBC-DEMO. All 8 extracted claims marker-sig match existing entity claims. Phase L zero-new-claims short-circuit: entity untouched; `updated:` not bumped. Phase P reports "entity unchanged (all 8 claims deduped)". Analysis file + research-log + sessions-log + daily note still written. Commit: 4 paths (entity not staged).

### Example 6: Preview mode

`/invest AVGO --preview`. Phase A runs (no F11 set). Phase B prints state-transition model. Exit clean. No research, no writes, no commit. Useful for understanding what a full run would produce.

### Example 7: Refresh retroactive entity extraction

Old analysis at `wiki/investing/analyses/avgo-analysis-2026-04-15.md`. `/invest --refresh wiki/investing/analyses/avgo-analysis-2026-04-15.md`. Skips research. Runs Phase L entity extraction on that existing analysis. Additive-only. Useful after ref-entity-update-semantics.md is updated or when a prior /invest ran with --no-entity.

### Example 8: Mid-batch failure (N.halt)

Phase L UPDATE succeeds on NVDA entity. Phase M watchlist Edit fails (old_string drift from concurrent PreToolUse formatter). N.halt: immediate stop; F11 stays on; no commit. Report: "NVDA entity updated (unstaged); watchlist failed; research-log + sessions-log + daily note not attempted." User runs `git checkout -- wiki/entities/tickers/NVDA.md` rollback or fixes watchlist and re-invokes (idempotent skip).

## Failure Taxonomy

Catalog of failure modes per phase with detection rule + expected behavior.

### Phase A failures
- **F11 already set**: HALT with recovery guidance (another skill running / orphaned flag; manually `rm .claude/state/auto-commit-disabled` if orphaned).
- **Ticker malformed** (empty, numeric, special chars): HALT with diagnostic.
- **Vault indexes empty** (Glob returns nothing for TICKERS or ALL_BASENAMES): HALT; likely working-dir mismatch.
- **Entity note non-canonical frontmatter**: HALT; recommend `/enrich --refresh <path>` first.

### Phase D failures
- **private/holdings-taxable.md missing**: WARN; continue with "Not currently held" default; flag in Phase P.
- **Class-ref load fails** (ref-etf-evaluation missing, etc.): WARN; fall back to stock ref defaults; log in Phase P audit.

### Phase E-I failures (research)
- **WebSearch quota / block / SSL**: retry `curl -sk` once per CLAUDE.md; if still fails, grade affected claim Grade-F (unverifiable) and continue. Do NOT populate Decision Sheet with Grade-F.
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
- Claim-to-section mapping (5-section schema: Financial signals / Thesis Fit / Risks / Catalysts / Recent)
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
5. Bypass: `CLAUDE_VAULT_BYPASS_VALIDATOR=1` (logged to `.claude/state/bypasses-<date>.log`)

Defense-in-depth on top of PreToolUse pre-write-validator.py + PostToolUse wikilink-check.py / frontmatter-check.py / orphan-check.py. The Phase O.0 gate prevents broken composition from reaching disk in the first place.

**/invest-specific risk:** /invest writes the most files atomically (~8 paths) -- Phase O.0 prevents any single-file GATE finding from cascading to N.halt rollback of the entire batch.

---
name: brief
risk: safe
description: "Generate the institutional-grade daily morning briefing. Use when starting the trading day, after material pre-market catalysts, ahead of FOMC/CPI/earnings windows, for weekend Week-in-Review framing, or when the prior briefing has aged past 24h staleness. Institutional-grade morning briefing at Calendar/decisions/briefings/briefing-<date>.md with PDB-style BLUF + Counter + Alternative Analysis; 16-phase A-P arc matching /invest v2 final; canonical frontmatter with day regime + macro regime + cross-asset coherence + thesis status board (the configured theses, binary HEALTHY/WATCH/STRESSED/INVALIDATED); evidence-grade confidence cap (>30% Grade-C -> 70%, any Grade-D in body -> 60%, >2 STALE -> 65%, script-fallback -> 60%); Warning Problems distinct from Intelligence Gaps; FOLLOWUPS:skills coordination block (analog to /invest INGEST:claims) with concrete one-line rationale + time-to-decision triggers; meta.json sidecar for machine-readable audit + Brier-score calibration across briefings; continuity audit reads last 3 briefings to score prior priced-in calls; 6 modes (--preview, --confirm, --replace, --quick, --refresh <path>, --no-peripheral); same-day -HHMM collision preserves archival rule; symmetric back-linking to materially-discussed entities (3-7 in related:); atomic commit with F11 Phase C + F14 narrow stage + F17 Co-Authored-By verify; path-guard compliant (private/ portfolio files read-only; Phase 15 portfolio refresh retired to /networth scope); ASCII-only new content (Pattern 22); reads portfolio + thesis essays + 7-day catalyst set + entity recency from wiki/entities/tickers/ + challenge recency from wiki/research/challenges/; 22-item Pre-Output HALT gate; mid-batch F.halt; coordinates with /invest (entity updates) + /networth (portfolio refresh) + /challenge (thesis stress) + /retro (sessions-log entry) + /decide (decision records). Phase O.0 pre-commit /vault audit gate (CAT-3 prevention-architecture parity)."
arguments: []
argument-hint: "[--preview] [--confirm] [--replace] [--quick] [--refresh <path>] [--no-peripheral]"
allowed-tools: [WebSearch, WebFetch, Read, Write, Edit, Bash, Glob, Grep, Agent]
effort: max
user-invocable: true
---

# /brief -- institutional-grade morning briefing with PDB discipline (v2 final)

Take today's market state, produce an institutional-grade morning briefing that lands in the vault atomically: compose a canonical briefing file at `Calendar/decisions/briefings/briefing-<date>[-HHMM].md` with PDB-style BLUF + Counter + Alternative Analysis + day-regime + macro-regime + cross-asset-coherence + thesis status board + evidence-graded portfolio impact + Warning Problems + Intelligence Gaps + FOLLOWUPS:skills coordination + machine-readable meta.json sidecar; update daily note Market Pulse summary + linkback; bump hot.md last_briefing; append sessions-log entry; symmetric back-link to materially-discussed entities; commit atomically.

## When to use

Daily trading-day morning use to set the day's decision frame. Weekend variant produces "Week in Review" framing with expanded calendar + scenario bar. Fed Week, earnings week, and crisis regimes auto-expand relevant sections.

## Not for

- Portfolio refresh / live-price snapshot (use `/networth`)
- Thesis stress-test without a specific event (use `/challenge thesis-<slug>`)
- Investment decision on a single ticker (use `/invest <ticker>` then `/decide` if action proposed)
- Ad-hoc price check (direct script call: `python tools/fetch-prices.py --equities <list>`)
- Session retrospective (use `/retro`)

## Invocation modes

| Syntax | Behavior |
|---|---|
| `/brief` | Full 16-phase A-P briefing; atomic commit across 5 targets + N entity back-links |
| `/brief --preview` | Phases A-N in memory; render briefing + meta + audit to stdout; SKIP O-P; F11 never set |
| `/brief --confirm` | Block at Phase B for `yes`; block before each of the 6 Phase P writes |
| `/brief --replace` | Same-date collision overwrites `briefing-<date>.md` without `-HHMM` suffix; explicit user intent |
| `/brief --quick` | Compressed: Markets + Signal Dashboard + Portfolio Movers + FOLLOWUPS only; <=200 words body; sidecar still written |
| `/brief --refresh <path>` | Additive merge into existing briefing: mutate Alerts + FOLLOWUPS only; body outside byte-exact; no peripheral writes |
| `/brief --no-peripheral` | Phase O briefing + sidecar only; SKIP Phase P entirely (composition test) |

## Execution Rules

- Execute phases sequentially. No merging. Use WebSearch only when explicitly authorized per phase (target: 0-3 web searches per run; script provides everything else).
- **F11 Phase C discipline**: set `.claude/state/auto-commit-disabled` at Phase C, BEFORE any Edit/Write. Phase B state-transition print runs BEFORE F11 so user can abort pre-writes. Clear flag only after Phase P post-commit verification passes.
- **Path-guards mechanical**. NEVER write to: `private/`, `.raw/`, `_quarantine/`, `finance/`, `credentials/`, `.git/`, `.claude/hooks/`, `.claude/state/` (except F11 flag itself). READs from `private/` ARE allowed (portfolio context). Phase 15 portfolio refresh from /brief v1 is RETIRED -- portfolio mutations belong to /networth scope.
- **Tag vocabulary canonical**: emit only `topic/market-brief` on briefing frontmatter (no ticker/company/thesis tags unless briefing is itself thesis-centric, rare/explicit). HALT on namespace drift.
- **Binary decisions default**: thesis HEALTHY/WATCH/STRESSED/INVALIDATED; coherence coherent-on/coherent-off/divergent; followup skill EMIT/SKIP. NEUTRAL only when signal genuinely absent both directions.
- **Confidence vs Conviction are DISTINCT fields**. Confidence (epistemic, 0-100%) capped by evidence-grade mix. Conviction (low/medium/high actionable) reported separately.
- **Body-preservation sha256** on every UPDATE in Phase P (daily note, hot.md, entity notes). Pre/post sha256 with strictly-additive-outside-insertion-sites assertion.
- **Symmetric back-linking**: every wikilink in briefing `related:` (3-7 typical) gets reciprocal `[[briefing-<date>[-HHMM]]]` on the target file's Recent section.
- **Mid-batch failure**: immediate HALT (Phase P F.halt), F11 stays on, no partial commit, structured report.
- **Commit discipline**: ASCII-only title + body, Co-Authored-By SUPPRESSED (F17 verify), F14 narrow staging (explicit pathspecs only).
- **Same-day collision**: if `briefing-<today>.md` exists AND no `--replace`, default to `briefing-<today>-<HHMM>.md` (HHMM from clock). If same-HHMM file also exists, HALT (sub-minute re-run is ambiguous intent).
- **Subagent dispatch is MANDATORY when specified by phase** (Phase D.0 dispatches `price-fetcher` for live quotes; Phase J.0 conditionally dispatches `institutional-positioning-scout` per held position with fresh institutional signal; Phase P.0 dispatches `vault-classifier-sweep` pre-commit gate). Pre-emptive skip based on judgment ("script will work fine direct", "no fresh institutional signal worth checking", "audit not necessary today") is FORBIDDEN. The subagents decide applicability via their own N/A return contracts (e.g., institutional-positioning-scout returns N/A on crypto tickers gracefully). Legitimate fallback fires ONLY on (a) contract violation -- subagent return missing required fields, OR (b) actual dispatch failure -- timeout, rate limit, tool-denial, hard subagent crash. Pre-emptive skip surfaces in Phase P audit as **DEVIATION** (not "fallback"). Quality preserved by additive design: existing inline `tools/fetch-prices.py` invocation + manual portfolio impact + direct `tools/vault-audit.py` invocation remain intact as legitimate-failure fallbacks. `--quick` mode SHOULD skip Phase J.0 + P.0 dispatches (sub-30s target precludes the 5-15s dispatch overhead per call); that's a documented skip, not deviation.

## Quality Standards

- **BLUF first**: opening sentence is a judgment with numbers + dollar impact, not a summary. Bad: "Markets are mixed". Good: "<TICKER> -4.2% on export rumors, $[DOLLAR_IMPACT] portfolio impact across [SHARES] combined shares."
- **Counter line (Tenth Man, PDB ICD 203)**: one sentence arguing the opposite case with cited evidence. Not canned bear-vs-bull -- specific evidence-grounded dissent.
- **Alternative Analysis (PDB ICD 203)**: a third-order scenario distinct from BLUF and Counter. One line. The non-obvious third path that becomes obvious in hindsight.
- **Priced-In line**: state market expectations + what would surprise. If nothing material today, skip the line entirely (do not pad). Each priced-in call goes into frontmatter `priced_in_calls:` as structured list for tomorrow's Brier scoring.
- **What / So What / Now What**: every portfolio mover answers all three. Raw data without interpretation is noise. Now What is one of: NO ACTION / MONITOR <trigger> / ADD @$X / TRIM @$X / REVIEW THESIS. ADD/TRIM gets copy-paste-ready order block.
- **Dollar impacts EXACT** from `shares_held * (price - prev_close)`. Cross-account holdings combined (tickers appearing in both accounts reported as combined exposure). Beta-adjusted impact for thesis-level events. Never estimate, never "about".
- **Regime classification drives expansion**: Crisis/Risk-off expand portfolio + geo + alerts; contract career. Risk-on/Rotation contract alerts; expand calendar + deployment. Fed Week expand calendar + scenario bar.
- **Calibrated % confidence on forward-looking**: percentages, not HIGH/MEDIUM/LOW. Capped by Pre-Output gate evidence-grade rule.
- **Inline evidence grading on material claims**: `[Grade A | source | date]`. A = primary (SEC, IR, FRED). B = Tier 1 wire (Reuters, CNBC, AP). C = aggregator/analytical. D = sentiment. F = unverifiable. STALE (>7d) auto-downgrades one letter.
- **Temporal anchoring**: every data point has its date. No "recently / today / currently" without timestamp.
- **Intelligence Gaps vs Warning Problems**: Gaps = "I don't know X (impact, resolve)". Warnings = "I know X and it matters but is below trigger threshold (base rate, escalation trigger)". Distinct sections; do not conflate.
- **3-minute rule**: briefing body <=650 words. >650 = padding defect. Quick mode <=200 words.
- **CFA 3-stage geo filter**: event detection -> transmission mapping -> SUPPLY (include) or SENTIMENT (skip unless FLASH). Sentiment-only events excluded without mention.
- **Cross-account holdings combined**: tickers held across both taxable and IRA accounts always reported as combined exposure.
- **Quiet-day suppression**: if all 7 quiet conditions from ref-monitoring-rules.md sec 2 are met, BLUF redirects to career/vault priorities; FOLLOWUPS empty-case renders `(no followup skills recommended)`.
- **ASCII-only NEW content (Pattern 22)**: em-dash -> `--`; curly quotes -> `"`/`'`; arrows -> `->` / `<-`; `<=` / `>=`; ellipsis -> `...`; euro -> `EUR`; NBSP -> space; middle dot -> `-`. Byte-scan; HALT on any byte > 127.

## Phase 0: Vault context retrieval (NEW; Phase 3.6d -- runs BEFORE Phase A; read-only; runs in --preview; SKIP on --quick)

Derived-subject semantic retrieval over the local HNSW vault index (covers `wiki/` + `Calendar/` + `private/`; `Atlas/` is NOT indexed -- thesis essays + ref-market-calendar are read here only to DERIVE query subjects, never as retrieval targets). Unlike entity skills that pivot 12 queries on one subject, /brief is parameter-less: it derives 12 subjects across 4 groups from current vault state, then retrieves each group against its own indexed subtree. Read-only: Bash `node` calls; writes nothing; safe in `--preview`.

0.0 -- Mode gate: if invocation includes `--quick`, SKIP Phase 0 (emit `Phase 0 -- skipped (--quick fast path)`) and proceed to Phase A. All other modes (normal, --preview, --confirm, --replace, --refresh, --no-peripheral) RUN Phase 0.

0.1 -- Derive 12 query subjects across 4 groups from current vault state:
- PORTFOLIO (4): read `private/holdings-taxable.md` + `private/holdings-ira.md` holdings tables; take the top 4 positions by value (cross-account combined). Query = `"<TICKER> position thesis and risk"`.
- THESIS (4): from `Atlas/concepts/investing/theses/thesis-*.md`. Query = `"<thesis-name> thesis"`.
- CATALYST (2): from `Atlas/sources/investing/ref-market-calendar.md` next-7-day events (FOMC / CPI / earnings / etc.). Query = `"upcoming <event> catalyst impact"`.
- CROSS-CUTTING (2): from the 2 most-recent `wiki/research/challenges/*.md` filenames. Query = `"<challenge-topic> findings"`.
If any source is empty, fall back to a generic subject for that slot (never emit an empty query).

0.2 -- Fire `query-skill.mjs` 5 times via Bash (1 BROAD + 4 FOCUSED), piping JSON to stdin. Model loads once per call (~0.3s warm); ~1.6s aggregate:
- BROAD (all 12, no filter): `{"queries":[<all 12>],"top_k":100,"threshold":0.60}`
- PORTFOLIO FOCUSED: `{"queries":[<4 portfolio>],"top_k":25,"threshold":0.60,"filter_path_prefix":"wiki/entities/tickers/"}`
- THESIS FOCUSED: same shape with `"filter_path_prefix":"wiki/research/"`
- CATALYST FOCUSED: same shape with `"filter_path_prefix":"Calendar/"`
- CROSS-CUTTING FOCUSED: same shape with `"filter_path_prefix":"wiki/playbooks/"`

Single `filter_path_prefix` per call (query-skill.mjs has no multi-prefix; `Atlas/` is unindexed so no group filters on it). Each returns `[{path,line,score,text}]`; the script always exits 0 (emits `[]` on error) so Phase 0 never crashes the run.

0.3 -- Merge all 5 results; dedup by `path:line` (keep higher score); TAG each chunk with its derivation group (portfolio | thesis | catalyst | cross-cutting | broad). Store as VAULT_CONTEXT.

0.4 -- EMIT a visible summary (MANDATORY), GROUPED by derivation source:

    Phase 0 -- derived-subject vault context (N distinct paths total)
    PORTFOLIO    (P hits): [score] path:line -- ~60 chars   (up to 4)
    THESIS       (T hits): ...
    CATALYST     (C hits): ...
    CROSS-CUTTING (X hits): ...
    BROAD (cross-vault top, B hits): ...   (up to 6)

If all calls return `[]`: emit `Phase 0 -- no vault context retrieved` and continue. NEVER HALT on Phase 0.

0.5 -- Downstream consumers (phases A-P UNCHANGED; consult VAULT_CONTEXT by group):
- Phase D/E (markets + portfolio movers): portfolio-group context informs each mover's "So What".
- Phase F/G (thesis status board): thesis-group context seeds HEALTHY/WATCH/STRESSED/INVALIDATED priors.
- Phase H/I (catalysts + calendar): catalyst-group context anchors the priced-in calls.
- Phase K/L (FOLLOWUPS:skills + Counter/AA): cross-cutting + broad context surface cross-skill connections.

Cite any used chunk inline as `(vault: path:line)` -- plain text, NO wikilink syntax.

## Phase A: Pre-flight (NO F11 yet)

A.1 -- Parse args: `--preview`, `--confirm`, `--replace`, `--quick`, `--refresh <path>`, `--no-peripheral`. Validate combinations (e.g., `--refresh` requires path; `--replace` and `--quick` are exclusive of `--refresh`).

A.2 -- Resolve today's ISO date from system clock (`date +%Y-%m-%d`); never from prior session memory or context.

A.3 -- F11 collision check: if `.claude/state/auto-commit-disabled` exists, HALT: "F11 already set by another skill. Either another skill is running concurrently or a prior crash left an orphaned flag. Manually `rm .claude/state/auto-commit-disabled` to clear, then re-invoke."

A.4 -- Brokerage freshness: read `private/holdings-taxable.md` + `private/holdings-ira.md` `updated:` frontmatter. If >30 days stale on either, set `BROKERAGE_WARN = "N days stale"` for header embedding (does not block; reported in Intelligence Gaps).

A.5 -- Same-day collision detection: if `Calendar/decisions/briefings/briefing-<today>.md` exists AND no `--replace`, default output to `briefing-<today>-<HHMM>.md` (HHMM from clock). If same-HHMM file also exists, HALT (sub-minute re-run ambiguous; ask the user).

A.6 -- Validate `tools/fetch-prices.py` exists; HALT if missing (script is load-bearing for Phase D).

## Phase B: State-transition model (print only, BEFORE F11)

Emit to stdout the planned state transition. User can abort here pre-F11; zero writes will have occurred.

```
## /brief v2 -- planned state transition

MODE:                [normal|preview|confirm|quick|refresh|no-peripheral]
DATE:                <YYYY-MM-DD>
OUTPUT:              Calendar/decisions/briefings/briefing-<date>[-HHMM].md
COLLISION:           [none|-HHMM variant|--replace overwrite]
MARKET STATUS:       <resolving in Phase D from script last_trading_day>
BROKERAGE FRESHNESS: <OK|WARN: N days stale>

READS:
  - private/holdings-taxable.md, private/holdings-ira.md (path-guarded READ)
  - Atlas/sources/investing/ref-{monitoring-rules,portfolio-doctrine,geopolitical-framework,market-calendar,macro-landscape}.md
  - Atlas/concepts/investing/{macro-outlook,watchlist,investing-research-log}.md
  - Atlas/concepts/investing/theses/thesis-*.md (thesis essays; for invalidation triggers)
  - Efforts/career-search/tracker.md
  - wiki/hot.md (full body)
  - wiki/entities/tickers/*.md modified <7d (N files; surface entity-level changes)
  - wiki/research/challenges/*.md modified <14d (N files; surface invalidation verdicts)
  - Calendar/decisions/briefings/ last 3 (continuity audit; Brier scoring)
  - Calendar/daily/<today>.md (Phase P pre-write race handling)

WRITES (ATOMIC):
  1. Calendar/decisions/briefings/briefing-<date>[-HHMM].md           [NEW]
  2. Calendar/decisions/briefings/briefing-<date>[-HHMM]-meta.json    [NEW; sidecar]
  3. Calendar/daily/<today>.md (## Market Pulse + linkback)           [UPDATE; sha256-gated outside section]
  4. wiki/hot.md (last_briefing bump + additive pending merge)        [UPDATE; sha256-gated]
  5. Calendar/decisions/sessions-log.md (append entry)                [UPDATE; strictly-additive]
  6. wiki/entities/tickers/<T>.md for each entity in related: (3-7)   [UPDATE; sha256-gated additive]

SCRIPT: python tools/fetch-prices.py --equities <list> --crypto <list>

PROCEED? Abort now = pre-F11, zero writes.
```

If `--preview`: stop after Phase N (composition complete in memory); render briefing + meta + audit to stdout; SKIP O-P; F11 never set; exit clean.

If `--confirm`: block for user `yes` before Phase C; also block before each Phase P write.

Else: autonomously proceed.

## Phase C: F11 set + Context Load

C.1 -- `mkdir -p .claude/state && touch .claude/state/auto-commit-disabled`. Single flag covers entire invocation.

C.2 -- Parallel context load (READ-only):

- **Portfolio**: `private/holdings-taxable.md` + `private/holdings-ira.md`. Extract `{ticker, shares, cost_basis, account}`. Flag cross-account overlaps for combined-exposure reporting.
- **Refs**: `Atlas/sources/investing/ref-{macro-landscape,monitoring-rules,portfolio-doctrine,geopolitical-framework,market-calendar}.md`. Macro outlook + watchlist + investing-research-log from `Atlas/concepts/investing/`.
- **Theses**: all thesis essays at `Atlas/concepts/investing/theses/thesis-*.md`. Extract per-thesis invalidation-triggers list. HALT Phase H if any thesis file missing (structural gap; ask the user).
- **hot.md**: full body. Extract Last Session + Pending Items + Active Context. Capture `last_briefing:` ISO for continuity context.
- **Entity recency**: `git log --since='7 days ago' --name-only -- 'wiki/entities/tickers/*.md' | sort -u`. For each, Read; extract any thesis-status shifts in body + recent Financial Signals entries. Surface in Phase H input.
- **Challenge recency**: `git log --since='14 days ago' --name-only -- 'wiki/research/challenges/*.md' | sort -u`. For each, Read; extract invalidation verdict.
- **Continuity audit**: Read last 3 briefings (Glob `Calendar/decisions/briefings/briefing-*.md` sorted; take 3 most recent). For each, parse `priced_in_calls:` and `scenario_bar:` frontmatter. For each call, classify CONFIRMED/SURPRISED/PENDING against today's market state. If >=5 scorable calls in rolling 30 days, compute Brier score: `BS = mean((forecast_prob - outcome)^2)` for each scenario. Carry forward `prior_brier_score_30d` into today's frontmatter; emit calibration footer ("Yesterday: priced-in CPI 3.0-3.3% base 55%; actual 3.1% -> Base HIT").
- **Tracker**: `Efforts/career-search/tracker.md`. Counts by status; flag pending >7d; flag interviews <=7d.

C.3 -- Build internal checklist:
- Holdings list with combined-account totals
- Equity/ETF tickers + crypto tickers for Phase D script call
- Per-thesis invalidation criteria (one list per configured thesis)
- 7-day catalyst set (FOMC/CPI/earnings/crypto-reg/career deadlines)
- Position sensitivity matrix (from ref-geopolitical-framework)
- hot.md pending-items count + oldest age
- Entity recency summary; challenge recency summary
- Prior-briefing continuity signal (Brier carry-forward + outstanding priced-in calls)

C.4 -- Today's daily note: do NOT compute `daily_before_sha256` here. Recompute immediately before Phase P Update 1 to handle UserPromptSubmit hook race (hook may append to `## Log` between Phase C and Phase P).

## Phase D: Live Data Fetch

### Phase D.0: DELEGATED dispatch to `price-fetcher` (PREFERRED path; Phase C wiring 2026-05-02)

**MANDATORY** (per Execution Rules; SKIPPED in `--quick` mode per documented exception): dispatch first, no pre-emptive skip outside `--quick`. Subagent wraps `tools/fetch-prices.py` and falls back to per-ticker WebSearch on script failure internally.

Use the Agent tool with subagent_type `price-fetcher`. Pass input: `{equities: [<EQUITIES from D.1>], crypto: [<CRYPTO from D.1>]}`. Expected return: structured JSON quotes map with `timestamp`, `quotes` (per-ticker `price`, `currency`, `source`, `freshness`, `caveat?`, plus extended-hours fields: `extended_hours_last`, `extended_hours_change_pct`, `extended_hours_volume`, `extended_hours_last_timestamp`, `market_session`, `ah_source`), top-level `extended_hours_movers[]` aggregation, `failures` array.

Validate return: every held ticker present in `quotes` OR `failures`; every quote has `market_session` field (pre-market | regular | after-hours | closed); `extended_hours_movers` is always a list (empty when no AH movers above AH_MOVER_THRESHOLD_PCT default 3.0%).

On contract violation OR dispatch failure: fall through to D.2 inline `python tools/fetch-prices.py` invocation. Surface fallback in Phase P audit report.

On dispatch success: skip D.2 inline script invocation; proceed directly to D.3 schema validation using subagent's returned JSON.

### D.1: Inline data prep (always runs)

D.1 -- Build ticker lists from Phase C portfolio + watchlist:
- `EQUITIES = [<dedup equity + ETF tickers across both accounts + watchlist>]`
- `CRYPTO = [<dedup crypto tickers without -USD suffix>]`

D.2 -- Execute (Windows: `python`, never `python3`):

```
python tools/fetch-prices.py \
  --equities "<comma-separated EQUITIES>" \
  --crypto "<comma-separated CRYPTO>"
```

D.3 -- Parse JSON. Assert schema presence:
- `indices`: SPX, NASDAQ, DOW, VIX (with `term_structure`), 10Y, DXY, GOLD, OIL
- `equities[]`: price, prev_close, change_pct, rsi14, ma50, ma200, beta, short_ratio, pct_from_52wk_high, next_earnings
- `crypto[]`: price, change_pct
- `signals`: oversold/overbought/below_ma50/below_ma200/earnings_within_10d/high_short_ratio
- `market_status`: open|closed|pre_market|post_market
- `last_trading_day`: ISO date

If schema drift (any field missing): HALT. Do not infer.

D.4 -- Market-hours branching:
- `closed` + weekend (Saturday/Sunday) -> header `Weekend Brief -- data as of <last_trading_day> close`; skip Overnight Earnings; expand Calendar + Scenario Bar; include "Week in Review" one-liner under BLUF
- `closed` + weekday -> `Holiday Brief -- data as of <last_trading_day> close`; treat last_trading_day as frozen
- `pre_market` -> note "Pre-market; prices as of last close"; ONE web search authorized for futures
- `open` / `post_market` -> normal flow

D.5 -- Fallback: if errors array contains >50% of EQUITIES tickers, set `SCRIPT_FALLBACK = true`; web-search for missing prices; annotate "Script fallback -- lower precision" in Intelligence Gaps; force confidence cap to 60% in Phase N.

D.6 -- Compute `script_output_hash = sha256(stdout)` for meta.json.

## Phase E: Regime Detection (day + macro, two-tier)

### Phase E.0: FRED macro fetch (ADD-NOW 2026-06-05; authoritative regime inputs; availability-guarded)

Before classifying, fetch the regime input set from the FRED MCP per `.claude/skills/brief/ref-macro-data-sources.md`: `mcp__fred__fred_get_series` for DGS10, T10Y3M, T10Y2Y, BAMLH0A0HYM2 (HY OAS), VIXCLS, UNRATE (latest + 2-3 prior for trend), CPILFESL (units=pc1), FEDFUNDS. Tag provenance `FRED:<series_id> asof <obs_date>` + freshness. The classification TABLES below are UNCHANGED -- FRED only replaces the prior web-search source for the credit/curve/unemployment inputs. **Availability-guard:** on MCP absence/error, SKIP FRED silently and fall back to the Phase D script 10Y/VIX + ONE web search for HY OAS (contract byte-stable; NEVER HALT). Additive DATA-SOURCING only -- does NOT change any regime classification rule or briefing verdict.

**Day regime** (tactical, 6-class). Source VIX from FRED `VIXCLS` + Phase D term-structure, credit from FRED `BAMLH0A0HYM2` (bps); the prior web-search-for-OAS is now the FRED fallback only (VIX > 25 = Risk-off regardless of OAS):

| Regime | VIX | Term | Credit | Section action |
|---|---|---|---|---|
| Crisis | >30 | Backwardation | HY OAS >500bps | Expand portfolio/geo/alerts; contract career |
| Risk-off | 20-30 | Flat/Backwardation | OAS widening | Expand portfolio movers + geo |
| Earnings | any | any | normal | Expand earnings |
| Fed Week | any | any | sensitive | Expand calendar + scenario bar |
| Risk-on | <16 | Contango | tightening | Contract alerts; expand deployment |
| Rotation | 16-20 | Contango | stable | Normal; note flow direction |

Report classification + which markers matched (Pattern 11 auditable): `VIX 24.3 [contango], OAS +12bps [widening], XLU/XLP rel-strength +0.8% -> Risk-off`.

**Macro regime** (cycle, 4-class) from yield curve (FRED `T10Y3M`/`T10Y2Y`) + unemployment trend (FRED `UNRATE` latest + priors) + credit spreads (FRED `BAMLH0A0HYM2`) + ISM if available (ISM is NOT on FRED per cap-matrix C6 -- web only; curve+unemployment+credit carry the classification):

| Phase | 10Y-3M | Unemployment | Credit | Leadership |
|---|---|---|---|---|
| Early-cycle | Steep | Falling | Tight/tightening | Cyclicals, small-caps |
| Mid-cycle | Normal | Stable low | Stable | Balanced |
| Late-cycle | Flat/inverted | Stable low | Tight but widening | Defensives, quality |
| Contraction | Re-steepening | Rising | Wide/widening | Bond proxies, gold |

Both regimes go to frontmatter (`regime:` + `macro_regime:`). Transition flag: if `macro_regime` differs from prior-3-briefings mode, mark `macro_regime_transition: true` and surface in Warning Problems.

## Phase F: Signal Dashboard + Markets one-liner

**Markets one-liner** (single line, all from Phase D script):

```
S&P $X,XXX (+/-X.X%) | Nasdaq $XX,XXX (+/-X.X%) | 10Y X.XX% [+/-Xbps] | BTC $XX,XXX (+/-X.X%) | DXY XX.X | VIX XX.X [cont|bkwd] | Oil $XX (+/-X.X%) | Gold $X,XXX
```

**Signal Dashboard** (compact table over held equity/ETF positions, 8-12 lines max including header):

| Ticker | Price | Chg% | AH/PM | RSI | vs 50MA | vs 52wk H | Beta | Signal |

The **AH/PM** column renders when ANY held position has `market_session != "regular"` (i.e., AH session active globally) OR when individual ticker has non-null `extended_hours_change_pct`. Format:
- `+X.X% AH` (after-hours change_pct, signed; AH session)
- `+X.X% PM` (pre-market change_pct, signed; PM session)
- `$X (untraded)` (market_session in AH/PM but `extended_hours_volume == 0`; rare; signal = ticker has AH session but untraded that minute)
- `-` (regular session OR market closed; column dropped if NO held position has AH/PM data globally)

Signal logic:
- RSI <30 AND price > 200MA -> `OVERSOLD` (cite ~73% bounce base rate when regime is non-bear)
- RSI >70 -> `OVERBOUGHT`
- price < 50MA AND price < 200MA -> `WEAK`
- earnings <=10 trading days -> `PRE-EARN Nd`
- short_ratio >5 -> `HIGH-SHORT`
- `ah_movers` ticker (i.e., abs(extended_hours_change_pct) >= 3%) -> `AH-MOVER` (combines with other signals: `AH-MOVER + PRE-EARN 2d`)
- multi-signal -> combine: `WEAK + PRE-EARN 7d`
- else -> `NEUTRAL`

Section budget: 8-12 lines. If >8 held positions, only render non-NEUTRAL rows; else render all (no hiding).

## Phase G: Cross-Asset Coherence Check

Classify session as one of three:

- **coherent-risk-on**: equities up, credit tight/tightening, rates up (growth bid), USD down, gold down, VIX down, BTC up
- **coherent-risk-off**: equities down, credit wide/widening, rates down (flight to safety), USD up, gold up, VIX up, BTC down
- **divergent**: any material dissent between signals

If divergent: emit Warning Problems entry with specifics. Example: `Equity up, credit widening, gold up -- dissent between equity rally and risk signals; idiosyncratic sector move OR regime transition in progress`.

Frontmatter field: `cross_asset_coherence: <coherent-on|coherent-off|divergent>`. Divergent sessions historically precede regime shifts; flagging is the point.

## Phase H: Thesis Status Board (NEW v2; binary per-thesis)

For each configured thesis (defined in `Atlas/concepts/investing/theses/`), evaluate status against invalidation triggers from the corresponding `thesis-<slug>.md` (loaded Phase C):

| Thesis | Status | Evidence |
|---|---|---|
| <thesis-1> | HEALTHY / WATCH / STRESSED / INVALIDATED | <specific trigger state, one line; when an exit-ladder leg is armed, append `exit-ladder: <tier>` per [[doctrine.template]]> |
| <thesis-2> | ... | ... |
| <thesis-3> | ... | ... |
| <thesis-4> | ... | ... |
| <thesis-5> | ... | ... |

Binary per Pattern 7. Definitions:
- **HEALTHY**: no invalidation signals; thesis confirmed by recent data
- **WATCH**: signal present but below trigger threshold
- **STRESSED**: trigger threshold crossed, pre-invalidation
- **INVALIDATED**: thesis premise broken

Frontmatter: `thesis_statuses: {<thesis-slug>: HEALTHY, <thesis-slug>: WATCH, ...}`.

Action: any thesis shifting HEALTHY -> WATCH (or worse) emits `/challenge thesis-<slug>` to FOLLOWUPS:skills + Warning Problems entry.

Failure: all thesis files missing -> HALT Phase H with explicit error; ask the user (structural gap).

## Phase I: Overnight Earnings + Geopolitical (conditional; skip when absent)

**Overnight Earnings**: skip section entirely if no held/watchlist position reported. For each reporter:
- EPS actual vs consensus, surprise %
- Revenue actual vs consensus, surprise %
- Guidance: raised/maintained/lowered vs prior + vs consensus
- Pre-market reaction %
- Thesis implication: CONFIRM or CHALLENGE (NEUTRAL only when truly absent both ways)
- PEAD direction (5-60d post-earnings drift magnitude per academic literature)
- Peer-constellation signal (e.g., "Peer memory beat -> positive PEAD signal for held memory position")

**Geopolitical**: CFA 3-stage filter from ref-geopolitical-framework.md:
1. Event detection
2. Transmission mapping (`EVENT -> POLICY -> MARKET -> SECTOR -> POSITION`)
3. Classification: SUPPLY (include) or SENTIMENT (skip unless FLASH-level)

Cross-reference position sensitivity matrix from ref-geopolitical-framework. Skip section entirely if nothing survives both filter and threshold.

## Phase J: Portfolio Impact

### Extended-Hours Movers (subsection; renders BEFORE regular movers when `extended_hours_movers[]` non-empty)

When the price-fetcher subagent returns top-level `extended_hours_movers[]` non-empty, render a dedicated table BEFORE the regular Portfolio Impact table:

| Ticker | Session | AH Move | $ Impact (regular close -> AH last) | So What | Now What |

- **Session**: pre-market | after-hours
- **AH Move**: signed magnitude_pct from quote (e.g., `+5.4% AH`); include `last_timestamp` parenthetical if recent (e.g., `+5.4% AH (19:59 ET)`)
- **$ Impact**: `shares_held * (extended_hours_last - regular_close)` EXACT; cross-account combined
- **So What**: thesis CONFIRM/CHALLENGE/NEUTRAL using AH price as evidence; cite specific invalidation trigger if CHALLENGE
- **Now What**: NO ACTION (AH transient) / MONITOR pre-open / REVIEW THESIS at open. Order blocks NOT embedded for AH movers (AH liquidity thin; defer to regular-session execution unless user explicitly requests AH limit order)

**Quiet-day suppression interaction**: if any `extended_hours_movers[]` entry has `abs(magnitude_pct) >= 5.0`, suppress the regular quiet-day BLUF redirect (AH-quiet != regular-quiet); render full briefing.

**Pre-Output explicit-absence**: if `market_session != "regular"` for ALL held positions AND `extended_hours_movers[]` is empty, render: `[Extended-hours session active: no material movers above 3.0% threshold across held positions]`.

### Regular session table (positions moving >1%):

| Ticker | What ($ impact, exact) | So What (thesis CONFIRM/CHALLENGE) | Now What |

- **Dollar impact**: `shares_held * (price - prev_close)` EXACT. Cross-account positions combined.
- **Beta-adjusted impact** for thesis-level events: `position_impact * beta`.
- **So What**: thesis status; if CHALLENGE, cite specific invalidation trigger from [[doctrine.template]].
- **Now What**: NO ACTION / MONITOR <trigger> / ADD @$X / TRIM @$X / REVIEW THESIS. If ADD or TRIM, embed copy-paste-ready order block:

```
ORDER (confirm at broker):
SELL [N.NNN] shares <TICKER> @ $[PRICE] LIMIT
```

**Portfolio Health grade** (A-F):
- **A**: all theses HEALTHY, no concentration issues
- **B**: 1 thesis WATCH OR minor concentration drift
- **C**: 2+ theses WATCH OR notable concentration
- **D**: any thesis STRESSED
- **F**: any thesis INVALIDATED OR crisis-level drawdown

Frontmatter: `portfolio_health: <A|B|C|D|F>`.

## Phase K: Calendar (7d) + Pre-Earnings Monitor + Scenario Bar

**Calendar (7 days)**: from ref-market-calendar.md + script `earnings_within_10d` + 0-1 web search for gaps. Each event:
- Date + name
- Conditional framing: `If hot X -> implication A; if soft Y -> implication B`
- Historical one-liner: avg move last 3 occurrences if data available

Include FOMC, CPI/PPI/jobs, held/watchlist earnings, crypto regulatory dates, career deadlines.

**Pre-Earnings Monitor**: for each held with earnings <=10 trading days (script signals.earnings_within_10d):
- Countdown: `[TICKER] earnings in X trading days (<date>)`
- Consensus: EPS $X.XX, Revenue $X.XB
- 30-day analyst revision trend (up/down/flat)
- Historical pattern from [[doctrine.template]] (e.g., historical beat-and-drop, guidance-driven moves)
- Implied move from options if findable
- PEAD peer signal direction

**Scenario Bar** (ONLY for highest-conviction catalyst within 7d; SINGLE, not multiple):

```
SCENARIO BAR: CPI Mar (2026-04-15)
Bull (25%): <3.0% -> 10Y to 4.15%, <ETF> +$XX
Base (55%): 3.0-3.3% -> muted, +/-$XX
Bear (20%): >3.3% -> 10Y to 4.50%, <ETF> -$XX
Expected Value: +$XX
```

Probabilities sum to 100%. Dollar impacts from actual share counts. EV = probability-weighted sum.

Each scenario writes to frontmatter `priced_in_calls:` as structured list:

```yaml
priced_in_calls:
  - event: "CPI Mar 2026"
    date: 2026-04-15
    bull_prob: 25
    base_prob: 55
    bear_prob: 20
    trigger_level: "3.0-3.3% YoY core"
```

This is the input for tomorrow's Brier scoring (Phase C continuity audit).

If no material catalyst within 7d: skip section entirely.

## Phase L: Intelligence Gaps + Warning Problems

**Intelligence Gaps** (known unknowns; 1-3 bullets max). Format: `GAP: <unknown>. Impact: <why it matters>. Resolve: <how to fix>`.

Skip section entirely on quiet days (suppression triggers met). Only emit "No material intelligence gaps." when truly absent (not as filler).

**Warning Problems** (IC convention; NEW v2). Distinct from Gaps:
- Gaps = "I don't know X"
- Warnings = "I know X and it matters, but it's below the trigger"

Emit Warning Problems for:
- Divergent cross-asset coherence (from Phase G)
- Macro regime transition (from Phase E)
- Thesis moving HEALTHY -> WATCH (from Phase H)
- Concentration drift past doctrine trigger (per [[doctrine.template]]: THESIS_CAP_AMBER / THESIS_CAP_RED / SINGLE_NAME_AMBER / SINGLE_NAME_RED / OTHER_THESIS_FLAG)
- Any Phase D script error affecting >1 held position

Format: `WARNING: <signal>. Base rate: <historical context>. Trigger: <what would escalate to action>`.

## Phase M: Optionality Map + Today's Focus + FOLLOWUPS:skills

**Optionality Map** (concrete deployable optionality):
- Available cash: `$X in IRA (per holdings-ira.md) + $Y in Taxable (per holdings-taxable.md if any)`
- Positions at action zones: `<ticker at $X vs entry zone $Y-Z from watchlist.md>`
- Career actions ready: `<X packets submit-ready, Y min each>`
- Pending decisions from hot.md: count + oldest age
- Yesterday's commitments: `X/Y completed` from prior daily-note `## Commitments` checkbox count; list any carried forward

**Today's Focus** (1-3 specific actions tied to what THIS briefing surfaced). Each with time-to-decision marker: `WITHIN 30 MIN OF OPEN` / `BEFORE FOMC 2PM` / `EOW`. No generic advice.

**FOLLOWUPS:skills block** (Pattern 18 coordination; analog to /invest INGEST:claims):

```markdown
<!-- FOLLOWUPS:skills -->
- /invest <TICKER> -- export-control signal pressures <thesis-slug> thesis; [SHARES] combined shares at thesis WATCH threshold (trigger: WITHIN 48H if confirmed by Commerce Dept)
- /challenge thesis-<thesis-slug> -- <thesis-slug> effective exposure approaching THESIS_CAP_AMBER (trigger: EOW)
- /networth -- portfolio value delta >5% since last snapshot; refresh recommended
- /decide -- <TICKER> trim at $[PRICE] triggered; structured decision record if action taken
- /retro -- queue at session end if substantive trades/decisions emerge
<!-- /FOLLOWUPS:skills -->
```

Empty case: render `(no followup skills recommended)` between tags. Do NOT emit a skill without a concrete one-line rationale tied to briefing body. Downstream /retro must be able to parse this block.

## Phase N: Pre-Output HALT Gate (22-item)

Assert each item below before any Write. Any failure -> HALT, report which item failed, no writes, no commit, F11 stays on. Gate runs in memory; Phase O does the writing.

1. BLUF is a judgment with numbers + dollar impact, not a summary
2. Counter line present (Tenth Man; specific evidence cited, not canned opposite)
3. Priced-In line states expectations + what would surprise, OR explicitly skipped (nothing material)
4. Alternative Analysis present -- a third-order scenario with evidence (not just bear vs bull)
5. Dollar impacts computed from `shares_held * (price - prev_close)` exact; no estimates
6. Signal Dashboard uses exact Phase D data
7. Every data point has explicit date; no bare "recently / today / currently"
8. Day regime classified via Phase E table; markers cited
9. Macro regime classified; transition flagged if shifted
10. Cross-asset coherence classified (coherent-on/coherent-off/divergent)
11. Thesis Status Board complete (all configured theses; binary statuses)
12. >=1 contradictory/risk item surfaced if any position moves >2%
13. Evidence grades on material claims `[Grade A-F | source | date]`
14. Geopolitical items passed CFA 3-stage filter (or correctly excluded)
15. Forward-looking uses % confidence, not HIGH/MEDIUM/LOW
16. Empty sections skipped entirely; no "nothing to report" padding
17. Intelligence Gaps flagged if any Phase D error OR >1d stale data
18. Warning Problems emitted if any divergent / transition / thesis-shift / script-error triggered
19. Pre-Earnings Monitor for all positions <=10 trading days (script signals)
20. Cross-account holdings report combined exposure
21. Cross-account holdings (held across both accounts) report combined exposure
22. Total briefing body <=650 words (3-minute rule); --quick mode <=200 words

**Evidence-grade confidence cap (separate precondition on frontmatter `confidence:`)**:
- >30% of inline grades are Grade C -> cap 70%
- Any Grade-D in body -> cap 60%
- >2 STALE data points (>7d) driving decision -> cap 65%
- Script fallback mode active -> cap 60%

If frontmatter `confidence:` exceeds applicable cap: HALT; user must authorize override explicitly.

**ASCII pre-write scan (Pattern 22)**: apply Part III sec 3.4 replacement table to all NEW content; byte-scan; HALT on any byte > 127 (modulo pre-existing legacy in unmodified body sections).

**FOLLOWUPS:skills sanity**: each emitted skill has concrete one-line rationale tied to briefing body; no skill without body evidence.

**Priced-in calls schema**: each scenario probability + trigger present in frontmatter structured list (input for tomorrow's Brier scoring).

## Phase O: Compose briefing + meta.json sidecar

O.1 -- Read `.claude/skills/brief/ref-output-template.md` for canonical frontmatter schema, body section order, and meta.json sidecar spec. Do not emit until ref loaded.

O.2 -- Write briefing to `Calendar/decisions/briefings/briefing-<YYYY-MM-DD>[-HHMM].md`.

**Canonical frontmatter** (full schema):

```yaml
---
categories: [decisions]
type: briefing
date: YYYY-MM-DD
regime: <day classification>
macro_regime: <cycle phase>
macro_regime_transition: <true|false>
cross_asset_coherence: <coherent-on|coherent-off|divergent>
portfolio_health: <A|B|C|D|F>
confidence: <integer 0-100>
confidence_cap_rule: <none|grade-c-30pct|grade-d-any|stale-2plus|script-fallback>
conviction: <low|medium|high>
thesis_statuses:
  <thesis-slug-1>: <HEALTHY|WATCH|STRESSED|INVALIDATED>
  <thesis-slug-2>: <...>
  <thesis-slug-3>: <...>
  <thesis-slug-4>: <...>
  <thesis-slug-5>: <...>
priced_in_calls:
  - event: <name>
    date: YYYY-MM-DD
    bull_prob: <int>
    base_prob: <int>
    bear_prob: <int>
    trigger_level: <number with unit>
prior_brier_score_30d: <float or null if <5 scorable calls>
positions_at_action_zones: [<ticker>@<price>, ...]
followup_skills_count: <int>
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: complete
tags: [topic/market-brief]
related: [[hot]], [[<materially-discussed-entities-3-7>]], [[<thesis-slugs-invoked>]]
---
```

**Body section order** (skip empty sections entirely; conform to ref-output-template.md updated for v2):

1. H1 title + Generated stamp + flags (Weekend|Holiday|Pre-Market|Intraday) + BROKERAGE_WARN if applicable
2. BLUF / Counter / Alternative
3. Day Regime / Macro Regime / Cross-Asset Coherence / Portfolio Health / Priced In
4. Markets one-liner
5. Signal Dashboard
6. Thesis Status Board
7. Overnight Earnings (conditional)
8. Portfolio Movers (What/SoWhat/NowWhat; copy-paste order blocks if action)
9. Pre-Earnings Monitor (conditional)
10. Geopolitical (conditional; CFA-filtered)
11. Alerts (FLASH/PRIORITY per ref-monitoring-rules.md)
12. Calendar (7 days)
13. Scenario Bar (conditional; highest-conviction only)
14. Intelligence Gaps
15. Warning Problems
16. Career
17. Vault
18. Optionality Map
19. Today's Focus (1-3 with time-to-decision markers)
20. FOLLOWUPS:skills block
21. Footer: Prior-day calibration line (one line from continuity audit) if Brier scoring active

O.3 -- Write meta.json sidecar at `Calendar/decisions/briefings/briefing-<YYYY-MM-DD>[-HHMM]-meta.json`:

```json
{
  "schema_version": 1,
  "briefing_date": "YYYY-MM-DD",
  "generated_at": "YYYY-MM-DDTHH:MM:SS",
  "mode": "<normal|quick|refresh|...>",
  "script_output_hash": "<sha256 of fetch-prices.py stdout>",
  "indices_snapshot": {<indices block from script>},
  "equities_snapshot": [<equities block>],
  "crypto_snapshot": [<crypto block>],
  "web_searches": [{"query": "...", "url": "...", "grade": "B"}],
  "regime_markers": {"vix": 24.3, "term": "contango", "oas_bps": 412, "classification": "risk-off"},
  "macro_regime_markers": {"yield_curve_10y_3m_bps": -8, "unemployment_trend": "stable_low", "credit_spreads": "tightening", "classification": "late-cycle"},
  "thesis_statuses": {"<thesis-slug-1>": "HEALTHY", "...": "..."},
  "priced_in_calls": [<structured list; tomorrow's Brier scoring input>],
  "confidence": 75,
  "confidence_cap_rule": "none",
  "followup_skills": [<structured list>],
  "phases_timing_ms": {"A": 12, "B": 3, "...": 0},
  "pre_output_gate_results": {"item_1_bluf_judgment": "PASS", "...": "PASS"}
}
```

Sidecar enables machine-parseable retrospective scoring + calibration feedback + audit by future /retro runs. Always written alongside briefing.

O.4 -- ASCII pre-write pass on briefing body + sidecar; HALT on any byte >127 in NEW content.

## Phase P: Peripheral atomic updates + Commit + F11 clear + Audit Report

### Phase P.0: DELEGATED pre-commit dispatch to `vault-classifier-sweep` (PREFERRED gate; Phase C wiring 2026-05-02)

**MANDATORY** (per Execution Rules; SKIPPED in `--quick` mode per documented exception): dispatch first, no pre-emptive skip outside `--quick`.

Use the Agent tool with subagent_type `vault-classifier-sweep`. Pass input: `{scope: "all"}`. Expected return: JSON with 9 classifier keys + `totals` + `score` + `score_floor_check`. If `score_floor_check: BREACH` (<90) OR `gate >0`: HALT before atomic apply; surface findings; user must repair before /brief peripheral writes can proceed.

Validate subagent return per its contract; on failure fall through to direct `python tools/vault-audit.py` invocation as fallback gate. Surface dispatch outcome in Phase P audit.

### Phase P.1: Peripheral atomic updates (continues unchanged below)

All four non-briefing updates MUST succeed. Mid-batch failure -> Pattern 13 F.halt: abort remaining writes, F11 stays on, structured report (succeeded / failed / not-attempted), user decides (rollback via `git checkout -- <paths>` or fix-and-retry with idempotency).

**Update 1: `Calendar/daily/<today>.md` `## Market Pulse` section**

- Re-Read AT THIS MOMENT (UserPromptSubmit hook may have appended `## Log` entries since Phase C)
- Compute `daily_before_sha256` (from re-read body)
- Replace entire `## Market Pulse` section body with: `**BLUF:** <BLUF>. **Regime:** <day>/<macro>. **Coherence:** <class>. **Health:** <grade>. **Confidence:** <N>%. Full briefing: [[briefing-<date>[-HHMM]]]`
- Compute `daily_after_sha256`
- Assert: body outside `## Market Pulse` section byte-exact (compare non-section segments)

**Update 2: `wiki/hot.md`**

- Read; `hot_before_sha256`
- Bump `last_briefing:` to today's ISO
- Merge pending items additively: any FOLLOWUPS:skills entries with concrete triggers not already present in Pending Items get appended (no removals; Pattern 12 idempotency aligned with /retro spec)
- Bump `updated:` to today
- Compute `hot_after_sha256`; assert diff is strictly-additive outside frontmatter field bumps

**Update 3: `Calendar/decisions/sessions-log.md`**

Append structured entry (canonical schema):

```
### YYYY-MM-DD[-HHMM] -- /brief
Domain: investing
Day regime: <class>
Macro regime: <phase>
Portfolio Health: <grade>
Confidence: <N>%
BLUF: <one-line>
Thesis shifts: <list of HEALTHY->WATCH transitions OR "none">
Followup skills: <count>
Artifact: [[briefing-<date>[-HHMM]]]
```

**Update 4: `wiki/entities/tickers/<T>.md` for each entity in briefing `related:`**

- SCOPE: only entities in briefing `related:` field (3-7 typical), NOT every ticker mentioned in body. Keeps fan-out bounded; consistent with /invest analysis-to-entity back-link discipline.
- For each entity:
  - Read; `entity_before_sha256`
  - Append under Recent section (create if absent): `- [YYYY-MM-DD] Mentioned in [[briefing-<date>[-HHMM]]] -- <one-phrase context>`
  - Bump `updated:` to today
  - Compute `entity_after_sha256`; assert strictly-additive diff

**Commit** (ASCII body mandatory):

```
brief(daily): YYYY-MM-DD[-HHMM] -- <regime> day, <macro_regime> macro, <health> health

Briefing at Calendar/decisions/briefings/briefing-<date>[-HHMM].md
Meta sidecar at briefing-<date>[-HHMM]-meta.json

BLUF: <one-line>
Day regime: <class> (VIX <X> [cont|bkwd], OAS <Xbps>, ...)
Macro regime: <phase> (<curve, unemp, credit>)
Cross-asset coherence: <class>
Portfolio Health: <grade>
Confidence: <N>% (cap: <rule or none>)
Conviction: <level>
Thesis statuses: <thesis-1>=<X>, <thesis-2>=<X>, <thesis-3>=<X>, <thesis-4>=<X>, <thesis-5>=<X>
Followup skills: <count>
Prior 30d Brier score: <float or n/a>

Peripheral atomic updates:
 - Calendar/daily/<today>.md  (Market Pulse summary + linkback)
 - wiki/hot.md  (last_briefing bump; additive pending merge)
 - Calendar/decisions/sessions-log.md  (structured entry)
 - wiki/entities/tickers/*.md  (<N> symmetric back-links)
```

**F14 narrow stage** each file explicitly. **Never** `git add -A` / `git add .`.

**Post-commit F17 verify**: `git log -1 --format='%B' HEAD | grep -c '^Co-Authored-By:'` must equal 0. If found, HALT; ask the user (do NOT silently proceed).

**Clear F11**: `rm .claude/state/auto-commit-disabled`. Assert absence.

**Audit Report** (stdout to user):

```
## /brief v2 run complete

Briefing:           briefing-<date>[-HHMM].md
Meta sidecar:       briefing-<date>[-HHMM]-meta.json
Day regime:         <class> (markers: VIX=X term=X OAS=X)
Macro regime:       <phase> (curve=X unemp=X credit=X)
Cross-asset:        <coherent-on|coherent-off|divergent>
Portfolio Health:   <grade> (<justification>)
Confidence:         <N>% (cap rule: <none|grade-c-30pct|grade-d-any|stale-2plus|script-fallback>)
Conviction:         <level>
Thesis statuses:    <thesis-1>=<X>, <thesis-2>=<X>, <thesis-3>=<X>, <thesis-4>=<X>, <thesis-5>=<X>
Thesis shifts:      <list or "none">

Files written:      5 + 1 sidecar + <N> entity back-links = <total>
Entity back-links:  <list of tickers>
Followup skills:    <count> (<skill names>)

Script status:      <ok|fallback|errors on: X,Y>
Web searches:       <count>
Pre-Output gate:    22/22 PASS
F11:                cleared
F17:                Co-Authored-By absent
Working tree:       clean

Prior-day calibration: <one-line from continuity audit, or "n/a (insufficient prior calls)">
```

## Modes detail

| Flag | Behavior |
|---|---|
| `--preview` | Phases A-N in memory; render briefing + meta + audit to stdout; SKIP O-P; F11 never set |
| `--confirm` | Block at Phase B for `yes`; block before each of the 6 Phase P writes |
| `--replace` | Same-date collision overwrites `briefing-<date>.md` without `-HHMM` suffix; explicit destructive (sidecar overwrites too) |
| `--quick` | Compressed: Markets + Signal Dashboard + Portfolio Movers + FOLLOWUPS only; skip G/H/I/K/L and most of M; body <=200 words; sidecar still written |
| `--refresh <path>` | Additive merge into existing briefing: mutate Alerts + FOLLOWUPS only; body outside byte-exact (sha256-verified); `updated:` bumps; append to existing meta.json `web_searches` + `followup_skills` arrays; no peripheral writes |
| `--no-peripheral` | Phase O briefing + sidecar only; SKIP Phase P entirely (composition test) |

## Pattern 21 / Standing Rule 16 -- explicitly deferred

The following ref docs are NOT created during this v2 upgrade. They are Pattern 21 candidates (each anticipated 6000+ words, 50+ primary-source citations) requiring bespoke Deep Research prompts in claude.ai Research mode -- separate session per Standing Rule 16:

- `.claude/skills/brief/ref-regime-taxonomy.md` -- full day + macro regime taxonomy, transition matrices, historical base rates
- `.claude/skills/brief/ref-evidence-hierarchy.md` -- Grade A-F evidence rubric, freshness tiers, contradiction tiering
- `.claude/skills/brief/ref-briefing-structure.md` -- PDB ICD 203 + hedge fund morning note structural taxonomy

SKILL.md v2 covers their content inline at procedural depth: 6-regime table in Phase E, 4-class macro table also Phase E, Grade A-F rubric in Quality Standards, briefing structure in ref-output-template. Preserve procedural depth; do not elevate inline. If composing >100 lines of new taxonomy or >500 words of new reference content during a future iteration, STOP and ask the user (Standing Rule 16).

## Failure Taxonomy

### Phase A failures
- **F11 already set**: HALT with recovery guidance
- **fetch-prices.py missing**: HALT (script load-bearing)
- **Same-HHMM same-day collision**: HALT (ambiguous intent)
- **Brokerage stale >30d**: WARN; embed in header; do not block

### Phase C failures
- **Thesis essay missing on disk** (any configured): HALT Phase H; ask the user (structural gap)
- **Entity recency `git log` returns nothing**: WARN; continue with empty entity-recency input
- **Continuity audit: <3 prior briefings exist**: degrade gracefully; use what is available; null Brier score if <5 scorable calls

### Phase D failures
- **Schema drift in script JSON**: HALT (do not infer fields)
- **>50% ticker errors**: SCRIPT_FALLBACK mode; web-search; confidence cap to 60
- **Script crash**: full web-search fallback; cap 60; annotate

### Phase H failure
- **Any thesis file missing**: HALT with explicit error; ask the user

### Phase N gate failures
- **Any 22-item check fails**: HALT with specific item; no writes
- **ASCII byte >127 in NEW content**: HALT; apply replacement table; re-scan
- **Confidence exceeds cap**: HALT; user authorizes override or revises

### Phase P failures (F.halt)
- **Update 1-4 mid-batch failure**: IMMEDIATE HALT; F11 stays on; report succeeded / failed / not-attempted; user decides rollback or fix-and-retry
- **F17 detects Co-Authored-By post-commit**: HALT; investigate; do NOT silently amend
- **Daily note race (sha256 mismatch)**: re-read once; if still mismatch, F.halt
- **F11 unlink fails post-commit**: log but do not halt (vault is in committed state); manually `rm .claude/state/auto-commit-disabled`

## Coordination

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

## Examples

### Example 1: Normal weekday open

`/brief` Mon 8:45 AM ET. Phase A: today date, no F11, no collision. Phase B prints state-transition; auto-proceed. Phase C: F11 set; reads complete. Phase D: script returns full data, market_status=pre_market; one futures search authorized. Phase E: VIX 14.2 contango -> Risk-on; macro Late-cycle. Phase F: Markets one-liner + 11-row Signal Dashboard. Phase G: coherent-risk-on. Phase H: all configured theses HEALTHY. Phase J: 2 movers >1% (<TICKER1> +1.8%, <TICKER2> -1.2%). Phase K: <TICKER1> earnings in 27d (skip Pre-Earnings Monitor); CPI Mar Apr 15 in Calendar; Scenario Bar on CPI. Phase M: 1 FOLLOWUP (`/networth -- portfolio delta >5% since prior snapshot`). Phase N gate 22/22 PASS. Phase O writes briefing + sidecar. Phase P: 4 peripheral updates + 4 entity back-links. Atomic commit, 10 paths.

### Example 2: Weekend brief

`/brief` Sat 8:00 AM ET. Phase D: market_status=closed, last_trading_day=Friday. Header `Weekend Brief -- data as of <Friday> close`; skip Overnight Earnings; expand Calendar + Scenario Bar; "Week in Review" one-liner under BLUF. All other phases standard. Macro regime still classified.

### Example 3: Holiday weekday

`/brief` Mon Apr 6 (Easter Monday equivalent). Phase D: market_status=closed, last_trading_day=Thursday. Header `Holiday Brief -- data as of <Thursday> close`. last_trading_day frozen. Calendar emphasizes catalyst pile-up post-holiday.

### Example 4: Pre-market with futures search

`/brief` Wed 6:30 AM ET. Phase D: market_status=pre_market. Header notes "Pre-market; prices as of last close". ONE web search for futures + overnight movers. Macro_regime_transition monitored. Confidence not capped just on pre-market timing.

### Example 5: Script fallback (ticker errors)

`/brief` Tue 8:30 AM ET. Phase D: yfinance returns errors on 6 of 11 tickers (>50%). SCRIPT_FALLBACK=true; web-searches all prices; annotates "Script fallback -- lower precision" in Intelligence Gaps. Phase N evidence-grade cap forces confidence to 60% regardless of inline grade mix.

### Example 6: Thesis shift (HEALTHY -> WATCH)

`/brief` Thu 8:45 AM ET. Phase H: <thesis-slug> moves HEALTHY -> WATCH after regulator signals new restrictions (Grade B Reuters Wed PM). Warning Problems entry: `WARNING: <thesis-slug> thesis WATCH -- regulatory signal detected. Base rate: prior rumors materialized 3 of 7 times (43%). Trigger: formal notice would shift to STRESSED.` FOLLOWUPS:skills emits `/challenge thesis-<thesis-slug>` + `/invest <TICKER>` with concrete triggers + 48H decision marker.

### Example 7: Divergent cross-asset coherence

`/brief` Fri 8:30 AM ET. Phase G detects: equity +0.4%, credit OAS +18bps widening, gold +1.2%, VIX +0.8 to 17.6. Coherence = divergent. Warning Problems: `WARNING: divergent session -- equity rally + credit widening + gold bid. Base rate: divergent sessions precede regime shift within 5 sessions ~38% of time. Trigger: continued credit widening + VIX through 20 -> regime transition risk.` BLUF surfaces dissent; Counter argues equity is leading credit (sometimes does); Alternative posits sector-specific credit move.

### Example 8: Refresh mode mid-day

11:15 AM ET. Peer earnings beat hit wires 11:00 AM. `/brief --refresh Calendar/decisions/briefings/briefing-2026-04-23.md`. Reads existing briefing; Phase A skips collision (path explicit); Phase D fetches fresh prices; mutates only Alerts section (`ALERT: Peer beat -- positive PEAD signal for held position; consider add per hot.md plan`) + FOLLOWUPS section (`/invest <TICKER> -- peer signal favorable; trigger WITHIN 24H`). Body outside Alerts + FOLLOWUPS byte-exact (sha256 verified). meta.json appends to `web_searches` + `followup_skills` arrays. `updated:` bumps. No peripheral writes.

## Ref docs

- `.claude/skills/brief/ref-output-template.md` (v2; consumed in Phase O for canonical frontmatter + body section order + meta.json sidecar spec + daily-note linkback pattern)
- `.claude/skills/brief/ref-macro-data-sources.md` (ADD-NOW 2026-06-05; consumed in Phase E.0 for the FRED series catalog + day/macro regime mappings + availability-guard pattern + C6/C8 caveats)

Pattern 21 candidates (deferred per Standing Rule 16; future Deep Research session):
- `.claude/skills/brief/ref-regime-taxonomy.md`
- `.claude/skills/brief/ref-evidence-hierarchy.md`
- `.claude/skills/brief/ref-briefing-structure.md`

## Related skills

- `/networth` -- portfolio snapshot complement (Phase 15 portfolio refresh from /brief v1 retired here)
- `/invest <ticker>` -- per-ticker analysis triggered by FOLLOWUPS
- `/challenge thesis-<slug>` -- thesis stress-test triggered by status shift in Phase H
- `/decide` -- structured decision record if action proposed in Phase J Now What
- `/retro` -- session-end retrospective consumes /brief sessions-log entry


## Phase O.0 -- Pre-commit /vault audit gate (v2.0; CAT-3 prevention-architecture parity)

After composing all target file modifications IN MEMORY but BEFORE atomic write:
1. Write each composed file to a tmp dir under `wiki/research/test-tmp/.precheck/brief-<slug>/`
2. Run `python tools/skill-precheck.py <tmp-files...> --skill /brief`
3. Parse exit code: 0 -> proceed; 2 -> HALT with diagnostic
4. Body-scope wikilink validation: per /retro v2.2 Phase D pattern, scan composed body text for unresolved `[[<target>]]` and mechanically de-link unresolved targets (vault-resolved keep / MEMORY_PREFIXES rewrite as `[[memory:<stem>]]` / placeholder leave / else strip). Fence-aware (skip ``` fenced + `inline code`).
5. Bypass: `CLAUDE_VAULT_BYPASS_VALIDATOR=1` (logged to `.claude/state/bypasses-<date>.log`)

Defense-in-depth on top of PreToolUse pre-write-validator.py + PostToolUse wikilink-check.py / frontmatter-check.py / orphan-check.py. The Phase O.0 gate prevents broken composition from reaching disk in the first place.

**/brief-specific risk:** /brief writes to ~5 append-mode files daily (sessions-log + hot.md + daily + 3-7 entity back-links) -- highest write-fanout among HIGH-risk skills.

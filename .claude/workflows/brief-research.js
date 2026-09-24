// brief-research.js -- /brief vNEXT Tier-A Wave-1 data-acquisition fan-out (2026-07-04)
//
// SINGLE-WAVE ARCHITECTURE (brief-vnext Diff 2, Block-A ratified 2026-07-04):
//   ONE wave, concurrency <=6, of independent READ-ONLY acquirers:
//     1. price-fetcher (agentType; replaces the Phase D.0 Agent-tool dispatch)
//     2. FRED macro worker (Phase E.0 series set incl. net-liquidity rows;
//        also carries the Phase J.6 openinsider top_buys/top_sells pair)
//     3. entity+challenge recency worker (git log + targeted Reads -> C.2 summaries)
//     4. continuity worker (last-3 briefings + brier-ledger + score-outcomes --dry-run)
//     5. optional tracker worker (status counts; N/A when no tracker is configured)
//   The MAIN LOOP retains: portfolio read (private/ stays in-session -- workers
//   NEVER receive path-guarded reads), regime CLASSIFICATION (tables unchanged;
//   workers only fetch inputs), all composition phases F-N, all writes O-P.
//   The conditional lite data-integrity skeptic is a MAIN-LOOP Agent dispatch
//   (it needs the composed draft; fires <20% of mornings; see SKILL.md A.8).
//
// READ-ONLY FLEET: every agent here researches and returns JSON. All vault
// writes happen in the main loop under F11/sha256/path-guard discipline.
//
// Token budget: sandbox has no process.env; main loop reads BRIEF_DW_TOKEN_BUDGET
// (default 150000 PLACEHOLDER -- recalibrate after 3 instrumented runs) and
// passes args.token_budget for logging.
//
// Resume rule: Workflow({scriptPath, resumeFromRunId}) on interruption;
// completed agents return cached. No Date.now()/Math.random(); run_date via args.

export const meta = {
  name: 'brief-research',
  description: 'Wave-1 read-only acquirer bundle for /brief vNEXT: price-fetcher + FRED/insider macro worker + recency worker + continuity worker + tracker worker in parallel. Main loop runs classification + composition + writes after this returns.',
  phases: [
    { title: 'Wave1', detail: 'price + macro/insider + recency + continuity + tracker, in parallel (concurrency <=6)' },
    { title: 'Converge', detail: 'contract validation + fallback markers + bundle assembly' },
  ],
}

// ---------- defensive args parse (invest-research.js precedent) ----------
let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
if (!A || typeof A !== 'object') A = {}
if (A.dry_run) return { dry_run_ok: true }
const EQ = Array.isArray(A.equities) ? A.equities : []
const CR = Array.isArray(A.crypto) ? A.crypto : []
if (!EQ.length && !CR.length) return { error: 'ticker lists required (args: {equities, crypto, held_tickers, thesis_slugs, run_date, token_budget})' }
const HELD = Array.isArray(A.held_tickers) ? A.held_tickers : EQ
const THESES = Array.isArray(A.thesis_slugs) ? A.thesis_slugs : ['theme-alpha', 'theme-beta', 'theme-gamma', 'theme-delta', 'theme-epsilon']
const RUN_DATE = A.run_date || 'unknown'
const BUDGET = A.token_budget || 150000

log(`brief-research eq=${EQ.length} crypto=${CR.length} held=${HELD.length} run_date=${RUN_DATE} budget=${BUDGET}`)

// ---------- schemas (presence-validated) ----------
const SKEL = (props, required) => ({ type: 'object', properties: props, required })
const ARR = { type: 'array' }
const OBJ = { type: 'object' }

const PRICE_SCHEMA = SKEL({ quotes: OBJ, failures: ARR, extended_hours_movers: ARR, mcp_price_count: { type: ['number', 'null'] } }, ['quotes', 'failures'])
const MACRO_SCHEMA = SKEL({ fred_series: OBJ, net_liquidity: OBJ, insider_overlay: ARR, fred_available: { type: 'boolean' }, openinsider_available: { type: 'boolean' } }, ['fred_series', 'fred_available'])
const RECENCY_SCHEMA = SKEL({ entity_recency: ARR, challenge_recency: ARR }, ['entity_recency', 'challenge_recency'])
const CONTINUITY_SCHEMA = SKEL({ prior_briefings: ARR, ledger: OBJ, ledger_exists: { type: 'boolean' }, invest_calibration: OBJ, prior_brier_score_30d: { type: ['number', 'null'] } }, ['prior_briefings', 'ledger_exists'])
const TRACKER_SCHEMA = SKEL({ counts_by_status: OBJ, pending_over_7d: ARR, due_within_7d: ARR, quiet: { type: 'boolean' } }, ['counts_by_status', 'quiet'])

// ---------- convergence gate (N/A = success; one re-dispatch; then documented fallback) ----------
const missing = (obj, fields) => !obj ? fields : fields.filter(f => obj[f] === undefined)
// Inherit authorized session settings; explicit caller options remain authoritative.
async function dispatch(label, prompt, opts, requiredFields) {
  let r = await agent(prompt, Object.assign({ label, phase: 'Wave1' }, opts))
  let miss = missing(r, requiredFields)
  if (miss.length) {
    log(`CONVERGENCE-GATE: ${label} contract violation (missing: ${miss.join(',')}) -- one re-dispatch`)
    r = await agent(prompt, Object.assign({ label: label + '-retry', phase: 'Wave1' }, opts))
    miss = missing(r, requiredFields)
    if (miss.length) {
      log(`CONVERGENCE-GATE: ${label} fallback applied (missing: ${miss.join(',')})`)
      return { retrieval_degraded: true, fallback_reason: 'contract violation after re-dispatch: missing ' + miss.join(','), _fallback: true }
    }
  }
  return r
}

const COMMON = `READ-ONLY acquisition worker for /brief vNEXT. Run date: ${RUN_DATE}. Never Write or Edit any file. NEVER read private/ (path-guarded; the main loop holds portfolio context). N/A is a SUCCESSFUL return: if a source is unavailable, return the schema with empty/null fields and an availability flag set false -- do NOT improvise substitutes. ASCII-clean strings only.`

// ---------- Wave 1 (all five in parallel) ----------
phase('Wave1')
const [price, macro, recency, continuity, tracker] = await parallel([
  () => dispatch('price-fetcher',
    `Fetch quotes per your standard contract. Input: {"equities": ${JSON.stringify(EQ)}, "crypto": ${JSON.stringify(CR)}}. Return your full JSON output contract (quotes, failures, extended_hours_movers, mcp_price_count). Broker-authoritative equity quotes required during regular session -- follow your v4 tier ladder exactly (Step 1 ToolSearch MCP load; load failure goes to failures[], never a silent skip). Honor any no-P&L caveat field.`,
    { agentType: 'price-fetcher', schema: PRICE_SCHEMA }, ['quotes', 'failures']),

  () => dispatch('fred-insider-macro',
    `${COMMON}
LANE: Phase E.0 FRED regime inputs + Phase J.6 insider overlay.
FRED: load via ToolSearch("select:mcp__fred__fred_get_series"); fetch DGS10, T10Y3M, T10Y2Y, BAMLH0A0HYM2, VIXCLS, UNRATE (latest + 2-3 prior), CPILFESL (units=pc1), FEDFUNDS, WALCL, RRPONTSYD, WTREGEN, DTWEXBGS (latest + ~5wk history for the WALCL/RRP/TGA 4-week delta). Compute net_liquidity = WALCL - RRPONTSYD - WTREGEN (normalize units: WALCL $M, others $B; report composite in $T + 4wk delta in $B). Tag each series "FRED:<id> asof <obs_date>". On MCP absence/error set fred_available:false with empty fred_series (main loop falls back per availability-guard).
OPENINSIDER: load via ToolSearch("select:mcp__openinsider__top_buys,mcp__openinsider__top_sells"); trailing week; INTERSECT results against ${JSON.stringify(HELD)} + watchlist tickers you are given nothing else for -- return ONLY intersecting rows as {ticker, side, value_usd, n_insiders, date}. Empty intersection -> empty array. On MCP absence set openinsider_available:false.
Return JSON: {fred_series:{<id>:{value,asof,prior:[...]}}, net_liquidity:{walcl,rrp,tga,composite_t,delta_4wk_b}, insider_overlay:[...], fred_available, openinsider_available}`,
    { schema: MACRO_SCHEMA }, ['fred_series', 'fred_available']),

  () => dispatch('entity-challenge-recency',
    `${COMMON}
LANE: Phase C.2 recency summaries. Run git log --since='7 days ago' --name-only -- 'wiki/entities/tickers/*.md' (cwd /path/to/vault) and Read each hit; extract thesis-status shifts + recent Financial Signals entries (2-3 sentence summary each). Run git log --since='14 days ago' --name-only -- 'wiki/research/challenges/*.md'; Read each; extract the invalidation verdict. Empty git output is a SUCCESSFUL empty return.
Return JSON: {entity_recency:[{ticker,path,summary}], challenge_recency:[{path,verdict,summary}]}`,
    { schema: RECENCY_SCHEMA }, ['entity_recency', 'challenge_recency']),

  () => dispatch('continuity',
    `${COMMON}
LANE: Phase C.2 continuity audit inputs. (1) Glob Calendar/decisions/briefings/briefing-*.md, take the 3 most recent, parse frontmatter priced_in_calls + thesis_statuses + regime + confidence per file. (2) Read Calendar/decisions/briefings/brier-ledger.json if it exists (ledger_exists flag; return the parsed object; compute prior_brier_score_30d per its rolling_30d or null). (3) Run python /path/to/vault/tools/score-outcomes.py --dry-run --json (cwd /path/to/vault); return {brier_new, brier_shadow, n_scored} from its output as invest_calibration (absent script or error -> empty object).
Return JSON: {prior_briefings:[{path,date,priced_in_calls,thesis_statuses,regime,confidence}], ledger:{...}|{}, ledger_exists, invest_calibration:{...}, prior_brier_score_30d}`,
    { schema: CONTINUITY_SCHEMA }, ['prior_briefings', 'ledger_exists']),

  () => dispatch('tracker',
    `${COMMON}
LANE: Phase C.2 optional tracker read. Read the configured tracker view if one exists (tolerate its absence). Counts by status; flag items pending >7d; flag items due <=7d. Quiet tracker (no active items) -> quiet:true with empty arrays (SUCCESSFUL N/A).
Return JSON: {counts_by_status:{...}, pending_over_7d:[...], due_within_7d:[...], quiet}`,
    { schema: TRACKER_SCHEMA }, ['counts_by_status', 'quiet']),
])

// ---------- Converge ----------
phase('Converge')
const workers = { price, macro, recency, continuity, tracker }
const degraded = Object.entries(workers)
  .filter(([k, v]) => !v || v.retrieval_degraded || v._fallback)
  .map(([k]) => k)
log(`converge: degraded=[${degraded.join(',')}]`)

return {
  run_date: RUN_DATE,
  bundle_version: 'brief-vnext-1',
  topology: 'dw',
  retrieval_degraded: degraded,
  token_budget_logged: BUDGET,
  price, macro, recency, continuity, tracker,
  epilogue: 'MAIN LOOP MUST now run: portfolio read (in-session) -> Phase E classification (tables verbatim; macro.fred_series as inputs; availability-guard on fred_available:false) -> F-N composition (net_liquidity line, J.6 insider_overlay render, H thesis board incl. machine-trigger evaluator, continuity calibration footer) -> conditional lite skeptic (Agent dispatch) if ADD/TRIM emitted OR thesis STRESSED/INVALIDATED OR health D/F -> N gate -> O/P writes incl. brier-ledger Update 5. Any degraded worker -> documented inline fallback per SKILL.md A.8; pre-emptive skip = DEVIATION.',
}

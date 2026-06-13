// invest-research.js -- /invest vNEXT Tier-A research fan-out (2026-06-09)
//
// TWO-INVOCATION ARCHITECTURE (divergence D4, strategist-ratified):
//   invest-research.js = Phase(Price) + Wave 1 (4 template workers) + Wave 2a
//   (forensic-scorer + institutional-positioning-scout via agentType).
//   The MAIN LOOP then runs the verdict spine (J / J.5 / K-bis.2-5 / K.5
//   thesis-critic via Agent tool / K compose / L claim-distributor / M / O).
//   invest-verify.js (companion) runs Wave 3 skeptics on the draft verdict.
//   Workflows cannot pause for mid-run parent synthesis -- thesis-critic needs
//   the composite draft, so it stays a main-loop Agent dispatch (contract
//   unchanged; checklist item 1 preserved).
//
// READ-ONLY FLEET: every agent here researches and returns JSON. All vault
// writes happen in the main loop under F11/sha256/path-guard discipline.
//
// Token budget: the workflow sandbox has NO Node API (no process.env), so the
// main loop reads INVEST_DW_TOKEN_BUDGET (default 750000 full / 500000 when
// Wave 3 will be skipped; calibrated 2026-06-10 from 3 production runs
// 596K/555K/715K) and passes it as args.token_budget for logging.
//
// Resume rule: on any mid-run interruption, re-invoke with
// Workflow({scriptPath, resumeFromRunId}) -- completed agents return cached.
// Never re-run a finished wave. No Date.now()/Math.random() (resume safety);
// run_timestamp arrives via args.

export const meta = {
  name: 'invest-research',
  description: 'Parallel research bundle for /invest vNEXT: price-fetcher + 4 template workers (Wave 1) + forensic-scorer + institutional-positioning-scout (Wave 2a). Read-only; main loop runs the verdict spine after this returns.',
  phases: [
    { title: 'Price', detail: 'broker-authoritative quote + technicals (price-fetcher fleet agent)' },
    { title: 'Wave1', detail: 'identity-structure + fundamentals + filings-integrity + competitive-macro-risk in parallel' },
    { title: 'Wave2a', detail: 'forensic-scorer + institutional-positioning-scout (fleet agents; after Wave1 converges)' },
    { title: 'Converge', detail: 'contract validation + fallback markers + bundle assembly' },
  ],
}

// ---------- defensive args parse ----------
let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
if (!A || typeof A !== 'object') A = {}
if (A.dry_run) return { dry_run_ok: true, ticker: A.ticker || null }
if (!A.ticker) return { error: 'ticker required (args: {ticker, class_hint, held, entity_exists, ws_budget_map, run_timestamp, token_budget, vault_context_summary, prior_entity_summary})' }

const T = String(A.ticker).toUpperCase()
const RUN_TS = A.run_timestamp || 'unknown'
const CLASS_HINT = A.class_hint || 'unknown'
const WS = Object.assign({ identity: 2, fundamentals: 4, filings: 0, competitive: 6, positioning: 1 }, A.ws_budget_map || {})
const BUDGET = A.token_budget || 750000
const VAULT_CTX = A.vault_context_summary || '(none provided)'
const PRIOR = A.prior_entity_summary || '(no prior entity state)'

log(`invest-research ${T} class=${CLASS_HINT} ws=${JSON.stringify(WS)} budget=${BUDGET} ts=${RUN_TS}`)

// ---------- schemas (presence-validated; convergence gate checks required keys) ----------
const SKEL = (props, required) => ({ type: 'object', properties: props, required })
const STR = { type: 'string' }
const NUM_OR_NULL = { type: ['number', 'null'] }
const BOOL = { type: 'boolean' }
const ARR = { type: 'array' }

const PRICE_SCHEMA = SKEL({
  quotes: { type: 'object' },
  failures: ARR,
  extended_hours_movers: ARR,
  mcp_price_count: { type: ['number', 'null'] },
}, ['quotes', 'failures'])

const IDENTITY_SCHEMA = SKEL({
  security_type: STR, company_name: STR, sector: STR, industry: STR,
  market_cap_usd: NUM_OR_NULL, week52_high: NUM_OR_NULL, week52_low: NUM_OR_NULL,
  ytd_pct: NUM_OR_NULL, etf_details: { type: ['object', 'null'] },
  latest_catalyst: { type: 'object' }, share_structure_note: STR,
  sources_used: ARR, ws_calls_made: { type: 'number' }, retrieval_degraded: BOOL,
}, ['security_type', 'latest_catalyst', 'sources_used', 'ws_calls_made'])

const FUNDAMENTALS_SCHEMA = SKEL({
  ttm_operating_income: NUM_OR_NULL,
  scoring_path: { enum: ['positive-eps-standard', 'negative-eps-bridge', 'pre-revenue-guard', 'not-applicable'] },
  revenue_ttm: NUM_OR_NULL, revenue_growth_yoy_pct: NUM_OR_NULL,
  gross_margin_pct: NUM_OR_NULL, gm_trend_4q: ARR,
  fcf_ttm: NUM_OR_NULL, fcf_yield_pct: NUM_OR_NULL, peg: NUM_OR_NULL,
  ev_sales: NUM_OR_NULL, net_debt_ebitda: NUM_OR_NULL, sbc_pct_revenue: NUM_OR_NULL,
  cash_and_equiv: NUM_OR_NULL, total_debt: NUM_OR_NULL,
  shares_outstanding_current: NUM_OR_NULL, share_count_trend: ARR,
  dilution_flag: BOOL, dilution_detail: { type: ['string', 'null'] },
  claims: ARR, ws_calls_made: { type: 'number' }, retrieval_degraded: BOOL,
}, ['scoring_path', 'claims', 'ws_calls_made'])

const FILINGS_SCHEMA = SKEL({
  nt_filings: ARR, restatement_flags: ARR, auditor_changes: ARR,
  ceo_cfo_changes: ARR, earnings_quality_flags: ARR, material_agreements: ARR,
  risk_factor_diff: { type: 'object' }, sbc_from_proxy: NUM_OR_NULL,
  late_filings_crosscheck: ARR,
  filing_integrity_score: { enum: ['clean', 'caution', 'flag', 'not-applicable'] },
  confidence_cap: STR, claims: ARR, retrieval_degraded: BOOL,
}, ['filing_integrity_score', 'claims'])

const COMPETITIVE_SCHEMA = SKEL({
  competitors: ARR, moat_assessment: STR, peer_comparison_table: ARR,
  macro_regime: { type: 'object' }, sector_tailwinds: ARR, sector_headwinds: ARR,
  regulatory_risks: ARR, supply_chain_flags: ARR, event_driven: { type: 'object' },
  fred_series_used: ARR, claims: ARR, ws_calls_made: { type: 'number' },
  retrieval_degraded: BOOL,
}, ['moat_assessment', 'claims', 'ws_calls_made'])

const FORENSIC_SCHEMA = SKEL({
  scorecard: ARR, framework_verdict: { type: 'object' },
  restatement_check: STR, composite_confidence: STR,
  not_applicable: BOOL,
}, ['scorecard'])

const POSITIONING_SCHEMA = SKEL({
  positioning_table: ARR, short_interest_block: { type: 'object' },
  cross_source_synthesis: STR, confidence: STR, not_applicable: BOOL,
}, ['positioning_table', 'cross_source_synthesis'])

// ---------- convergence gate ----------
const missing = (obj, fields) => !obj ? fields : fields.filter(f => obj[f] === undefined)

async function dispatch(label, phaseName, prompt, opts, requiredFields) {
  let r = await agent(prompt, Object.assign({ label, phase: phaseName }, opts))
  let miss = missing(r, requiredFields)
  if (miss.length) {
    log(`CONVERGENCE-GATE: ${label} contract violation (missing: ${miss.join(',')}) -- one re-dispatch`)
    r = await agent(prompt, Object.assign({ label: label + '-retry', phase: phaseName }, opts))
    miss = missing(r, requiredFields)
    if (miss.length) {
      log(`CONVERGENCE-GATE: ${label} fallback applied (missing: ${miss.join(',')})`)
      return { retrieval_degraded: true, fallback_reason: 'contract violation after re-dispatch: missing ' + miss.join(','), _fallback: true }
    }
  }
  return r
}

const COMMON = `READ-ONLY research worker for /invest vNEXT on ticker ${T} (class hint: ${CLASS_HINT}). Run timestamp: ${RUN_TS}. Never Write or Edit any file. N/A is a SUCCESSFUL return: if your lane does not apply to this asset class, return the schema with empty arrays/nulls, set any not-applicable style field accordingly, and explain in one sentence -- do NOT improvise out-of-lane research. Every quantitative claim you return in a claims[] array must be an object {entity, metric, value, date, grade, section, text, prov} where prov is "mcp:<server>:<key>" | "script:yfinance" | "web:<domain>+<grade>" (provenance is MANDATORY -- a claim without prov will be rejected by the Wave-3 provenance skeptic). Evidence grading: [Grade A|B|C|D] per source quality + freshness. Vault context summary (Phase 0): ${VAULT_CTX}. Prior entity state: ${PRIOR}.`

// ---------- Phase: Price ----------
phase('Price')
const price = await dispatch('quote-technicals', 'Price',
  `Fetch quotes per your standard contract. Input: {"equities": ${JSON.stringify(CLASS_HINT === 'crypto' ? [] : [T])}, "crypto": ${JSON.stringify(CLASS_HINT === 'crypto' ? [T] : [])}}. Return your full JSON output contract (quotes, failures, extended_hours_movers, mcp_price_count). The parent gate requires broker_authoritative=true on held-equity quotes during regular session -- follow your v4 tier ladder exactly (Step 1 ToolSearch MCP load; load failure goes to failures[], never a silent skip).`,
  { agentType: 'price-fetcher', schema: PRICE_SCHEMA }, ['quotes', 'failures'])

// ---------- Phase: Wave1 (4 template workers, parallel) ----------
phase('Wave1')
const [identity, fundamentals, filings, competitive] = await parallel([
  () => dispatch('identity-structure', 'Wave1', `${COMMON}
LANE: identity + structure (Tier-B Phase E surface: security type; stock overview or ETF details incl. fund family/AUM/expense ratio/top-10 holdings; share structure; 52-week range + YTD; the single most important catalyst with exact date).
TOOL GRANT CONTRACT: WebSearch (HARD CAP ${WS.identity} calls -- report actual count in ws_calls_made), WebFetch, Read. For ticker disambiguation you may load mcp__robinhood-trading__search via ToolSearch("select:mcp__robinhood-trading__search").
Blocked domains per house rules (bloomberg, investopedia, macrotrends, fintel, wsj, ft, barrons, morningstar, seekingalpha, statista, tipranks, gurufocus, simplywall, yahoo-finance, marketbeat, fool, zacks, tradingview).
Return JSON: {security_type, company_name, sector, industry, market_cap_usd, week52_high, week52_low, ytd_pct, etf_details|null, latest_catalyst:{description,date}, share_structure_note, sources_used[], ws_calls_made, retrieval_degraded:false}`,
    { schema: IDENTITY_SCHEMA }, ['security_type', 'latest_catalyst', 'sources_used', 'ws_calls_made']),

  () => dispatch('fundamentals', 'Wave1', `${COMMON}
LANE: fundamentals (Tier-B Phase F surface: full metrics catalog per .claude/skills/invest/ref-analysis-template.md -- Read it for the catalog). EDGAR XBRL is PRIMARY: load via ToolSearch("select:mcp__edgar-tools__edgar_company,mcp__edgar-tools__edgar_trends,mcp__edgar-tools__edgar_read"); use edgar_trends for multi-period revenue/GM/share-count trends (this feeds the share-count >1.5x data-integrity rule); for negative-EPS names load mcp__openinsider__dilution_filings (S-1/S-3/424B shelf pipeline -> forward dilution + cash-runway input). CRITICAL ROUTING INPUT: report ttm_operating_income precisely -- it decides scoring_path (positive-eps-standard ONLY when TTM op income >= 0; else negative-eps-bridge; pre-revenue-guard when TTM revenue <$20M or EV/Sales >100x; cyclical-still-profitable names route STEP 2a -> positive-eps-standard with a mid-cycle-margin caveat noted in claims). Crypto/non-filer: scoring_path=not-applicable.
TOOL GRANT CONTRACT: edgar MCP tools above, openinsider dilution_filings, WebSearch (HARD CAP ${WS.fundamentals} -- report ws_calls_made), Read.
Return JSON per schema; every figure as a claims[] entry with prov (e.g. "mcp:edgar:OperatingIncomeLoss").`,
    { schema: FUNDAMENTALS_SCHEMA }, ['scoring_path', 'claims', 'ws_calls_made']),

  () => dispatch('filings-integrity', 'Wave1', `${COMMON}
LANE: filings integrity + red flags (Tier-B Phase H subset, expanded). ZERO WebSearch -- SEC primary only. Load via ToolSearch("select:mcp__edgar-tools__edgar_search,mcp__edgar-tools__edgar_filing,mcp__edgar-tools__edgar_text_search,mcp__edgar-tools__edgar_read,mcp__edgar-tools__edgar_proxy") and ToolSearch("select:mcp__openinsider__late_filings"). Check: NT-10-K/NT-10-Q late filings; 8-K Items 4.02 (non-reliance/restatement), 4.01 (auditor change), 2.02 (results), 1.01 (material agreements >$500M), 5.02 (CEO/CFO changes); RISK-FACTOR DIFF vs prior 10-K (new/removed risks via edgar_text_search or edgar_read on Item 1A); SBC + exec comp via edgar_proxy; cross-check openinsider late_filings. Any NT-accounting/4.02/4.01 within 24mo -> filing_integrity_score=flag + confidence_cap=MED. Non-filer (crypto/foreign-only/ETF) -> not-applicable score with explanation.
TOOL GRANT CONTRACT: the MCP tools above ONLY (ws cap ${WS.filings} = zero).
Return JSON per schema; findings as claims[] with prov "mcp:edgar:<accession>".`,
    { schema: FILINGS_SCHEMA }, ['filing_integrity_score', 'claims']),

  () => dispatch('competitive-macro-risk', 'Wave1', `${COMMON}
LANE: competitive + macro + risk (Tier-B Phases G technical-context subset, H risk, I competitive-macro: moat, peer comparison, macro sensitivity, supply chain, event-driven, regulatory; volatility/drawdown/beta context). Peer XBRL table: load ToolSearch("select:mcp__edgar-tools__edgar_compare") and compare margins/growth/leverage vs 3-5 closest comps. Macro: load ToolSearch("select:mcp__fred__fred_get_series,mcp__fred__fred_search"); confirm any series ID via fred_search BEFORE fetching; tag FRED data prov "mcp:fred:<SERIES_ID>".
TOOL GRANT CONTRACT: edgar_compare, fred MCP, WebSearch (HARD CAP ${WS.competitive}: ~3 competitive + 2 risk + 1 technical-context -- report ws_calls_made), WebFetch, Read. Blocked domains per house rules.
Return JSON per schema; claims[] with prov.`,
    { schema: COMPETITIVE_SCHEMA }, ['moat_assessment', 'claims', 'ws_calls_made']),
])

// ---------- Phase: Wave2a (fleet agents; needs fundamentals.scoring_path) ----------
phase('Wave2a')
const scoringPath = (fundamentals && fundamentals.scoring_path) || 'unknown'
const [forensic, positioning] = await parallel([
  () => dispatch('forensic-scorer', 'Wave2a',
    `Compute your Top-12 forensic scoring stack for ticker ${T} per your standard contract. scoring_path hint from the fundamentals worker: ${scoringPath} (a negative-eps-bridge name should N/A the earnings-quality metrics that presuppose positive earnings and say so per metric). Tier-0 inputs now include edgar_trends (multi-period share-count for the SBC-dilution flag + accruals work) and edgar_proxy (SBC detail) -- load via ToolSearch as needed. Return your standard scorecard markdown-as-JSON: {scorecard:[{metric,value,threshold,verdict,conf,source}...], framework_verdict, restatement_check, composite_confidence}. N/A on crypto/ETF per your graceful-N/A contract (set not_applicable:true).`,
    { agentType: 'forensic-scorer', schema: FORENSIC_SCHEMA }, ['scorecard']),

  () => dispatch('institutional-positioning-scout', 'Wave2a',
    `Scout institutional/political/insider positioning for ticker ${T} per your standard contract (Dataroma 13F + CapitolTrades + OpenInsider incl. short-interest sub-block). Named-manager 13F pulls may use edgar_fund (ToolSearch load). WebSearch cap ${WS.positioning} (coverage-gap fallback only). Return {positioning_table:[{source,signal,date,magnitude,tier,notes}...], short_interest_block, cross_source_synthesis, confidence}. N/A on crypto per your graceful-N/A contract (set not_applicable:true).`,
    { agentType: 'institutional-positioning-scout', schema: POSITIONING_SCHEMA }, ['positioning_table', 'cross_source_synthesis']),
])

// ---------- Phase: Converge ----------
phase('Converge')
const workers = { price, identity, fundamentals, filings, competitive, forensic, positioning }
const degraded = Object.entries(workers)
  .filter(([k, v]) => !v || v.retrieval_degraded || v._fallback)
  .map(([k]) => k)
const wsActuals = {
  identity: identity && identity.ws_calls_made,
  fundamentals: fundamentals && fundamentals.ws_calls_made,
  competitive: competitive && competitive.ws_calls_made,
  filings: 0,
  positioning: 'fleet-internal',
  forensic: 'fleet-internal',
}
log(`converge: degraded=[${degraded.join(',')}] ws_actuals=${JSON.stringify(wsActuals)}`)

return {
  ticker: T,
  run_timestamp: RUN_TS,
  bundle_version: 'vnext-1',
  topology: 'dw',
  retrieval_degraded: degraded,
  ws_actuals: wsActuals,
  token_budget_logged: BUDGET,
  price, identity, fundamentals, filings, competitive, forensic, positioning,
  epilogue: 'MAIN LOOP MUST now run the verdict spine: J portfolio-fit (hybrid live positions; regular_market_close anchoring) -> J.5 prior-research comparison -> J-bis integration (positioning bundle) -> K-bis.2 framework rotation -> K-bis.3 composite -> K-bis.4/5 verdict (spine VERBATIM) -> K.5 thesis-critic (Agent tool) -> Wave-3 gate check (invest-verify.js if verdict>=BUY / thesis-status change / boundary composite / --verify) -> K compose -> L entity -> M peripherals -> O commit.',
}

// invest-verify.js -- /invest vNEXT Wave 3 adversarial verification (2026-06-09)
//
// Companion to invest-research.js (two-invocation architecture, divergence D4).
// The MAIN LOOP invokes this AFTER every material draft verdict, including
// HOLD, SELL and STRONG SELL. A direction does not make financial reasoning
// safe. Thesis changes, boundary scores and --verify also require review.
// Final delivered-artifact review is owned by tools/fis/workbench.py review;
// this workflow's sampled skeptics do not certify a subsequently edited report.
//
// Four skeptics are defined below, each instructed to remain read-only and REFUTE.
// The installed Workflow API has no verified per-call permission boundary;
// dispatch is withheld until such a boundary is established in the harness.
// Prompt compliance is not mechanical read-only assurance. ANY refutation -> the main
// loop executes Phase N HALT: F11 stays set, ZERO writes, refutation surfaced.
//
// Formalizes the 28-agent bridge-battery pattern (wf_991e83f5-37c, 2026-06-07)
// into a standing wave. No Date.now()/Math.random(); timestamps via args.

export const meta = {
  name: 'invest-verify',
  description: 'Wave 3 skeptics for /invest vNEXT: data-integrity + R/R + routing + provenance, in parallel. Read-only instruction; mechanical isolation unavailable. Any refutation -> parent Phase N HALT (no writes).',
  phases: [
    { title: 'Skeptics', detail: 'data-integrity + R/R + routing + provenance in parallel (each prompted to refute)' },
    { title: 'Verdict', detail: 'aggregate refutation state for the parent gate' },
  ],
}

// ---------- defensive args parse ----------
let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
if (!A || typeof A !== 'object') A = {}
if (A.dry_run) return { dry_run_ok: true, ticker: A.ticker || null }
if (!A.ticker || !A.draft_verdict) {
  return { error: 'args required: {ticker, draft_verdict, composite, conviction_pct, rr_ratio, entry, stop, target, scoring_path, ttm_operating_income, thesis_status, thesis_status_prior, claims_with_prov, quote_technicals, fundamentals_bundle, routing_trace, run_timestamp}' }
}
if (!['STRONG BUY', 'BUY', 'HOLD', 'SELL', 'STRONG SELL', 'NR'].includes(A.draft_verdict)) {
  return { error: 'unsupported draft verdict', any_refutation: true, parent_directive: 'Phase N HALT: invalid draft verdict.' }
}

// No caller-provided assertion can establish a harness permission boundary.
// Workflow's supported agent options currently provide no verified per-call
// deny-write restriction. Keep the existing lens implementation for when the
// host supplies one, but never dispatch unrestricted reviewers in the meantime.
return {
  ticker: String(A.ticker).toUpperCase(),
  status: 'withheld',
  any_refutation: true,
  refuting_skeptics: [],
  skeptics: {},
  dispatched_agents: 0,
  blockers: ['mechanical_read_only_boundary_unavailable'],
  read_only_assurance: {
    status: 'unavailable',
    boundary: 'prompt_instruction_only',
    reason: 'The installed Workflow agent API has no verified per-call tool or permission restriction. Unrestricted reviewer dispatch is prohibited.',
  },
  accepted_report: false,
  requires_separate_read_only_review: true,
  parent_directive: 'Phase N HALT: reviewer capability unavailable. Use the existing separately restricted Read-only final-report review path; retain this draft as unaccepted.',
}

const T = String(A.ticker).toUpperCase()
const RUN_TS = A.run_timestamp || 'unknown'
const DRAFT = {
  verdict: A.draft_verdict,
  composite: A.composite,
  conviction_pct: A.conviction_pct,
  rr_ratio: A.rr_ratio,
  entry: A.entry, stop: A.stop, target: A.target,
  scoring_path: A.scoring_path,
  ttm_operating_income: A.ttm_operating_income,
  thesis_status: A.thesis_status,
  thesis_status_prior: A.thesis_status_prior,
}
const CLAIMS = A.claims_with_prov || []
const QUOTES = A.quote_technicals || {}
const FUNDAMENTALS = A.fundamentals_bundle || {}
const ROUTING_TRACE = A.routing_trace || '(no routing trace supplied)'

log(`invest-verify ${T}: draft=${DRAFT.verdict} composite=${DRAFT.composite} rr=${DRAFT.rr_ratio} path=${DRAFT.scoring_path}`)

const SKEPTIC_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    refutation: { type: 'boolean' },
    details: { type: 'string', minLength: 1 },
    checked_items: { type: 'array', minItems: 1, uniqueItems: true, items: { type: 'string', minLength: 1 } },
  },
  required: ['refutation', 'details', 'checked_items'],
}

const COMMON = `READ-ONLY adversarial skeptic for /invest vNEXT on ${T} (run ${RUN_TS}). Your job is to REFUTE the draft verdict if you can -- default to suspicion, but a refutation must be SPECIFIC and evidenced (name the number, the source, the rule violated). A restatement of already-surfaced risk is NOT a refutation. Correct arithmetic can still support an economically wrong conclusion. Apply equal scrutiny to material BUY, HOLD and SELL conclusions, including opportunity costs, missing evidence, applicability and limitations. Do not edit evidence or grading rules. Return JSON {refutation: bool, details: string, checked_items: string[]}. N/A lanes (e.g. equity-only checks on crypto/ETF) return refutation:false with the specific N/A explanation in details and checked_items. Missing evidence or an incomplete review is not an N/A pass. Draft verdict bundle: ${JSON.stringify(DRAFT)}.`

// A failed provider call must become a completed, fail-closed aggregate result.
const safeAgent = async (...parameters) => {
  try { return await agent(...parameters) } catch (_) { return null }
}

// ---------- Phase: Skeptics ----------
// model pinned: verifiers must not inherit a frontier-tier session model
// (cost directive 2026-07-09; parity with the opus-pinned agent fleet).
// spark-verify.js carried this pin and cited THIS file as its precedent; the
// pin itself was never backported here until 2026-08-17. A skeptic with no
// agentType has no frontmatter layer to fall through to, so it inherited the
// session model and breached the AGENTS.md subagent ceiling.
phase('Skeptics')
const [dataIntegrity, riskReward, routing, provenance] = await parallel([
  () => safeAgent(`${COMMON}
LENS 1 -- DATA INTEGRITY. Re-derive 5 sampled composite inputs from PRIMARY sources (SEC EDGAR via ToolSearch("select:mcp__edgar-tools__edgar_company,mcp__edgar-tools__edgar_trends"); stockanalysis.com secondary). Sample across: revenue/margin figures, share count, cash/debt, one valuation multiple, one scorecard metric. MANDATORY RULE (Section 10.2, residual gap 5): pull edgar_trends share-count history; if shares outstanding grew >1.5x over the lookback (4 FY baselines) WITHOUT an explained split/acquisition in the claims, that is a REFUTATION ("share-count >1.5x unexplained"). Also apply: current shares (not TTM weighted-avg) for per-share math; sum-4-quarters check if any TTM line >4x max quarter. Claims to audit: ${JSON.stringify(CLAIMS.slice(0, 40))}`,
    { label: 'skeptic:data-integrity', phase: 'Skeptics', schema: SKEPTIC_SCHEMA }),

  () => safeAgent(`${COMMON}
LENS 2 -- RISK/REWARD. Independently re-compute R/R from the stated entry/stop/target: (target - entry) / (entry - stop). Check the HARD gates: BUY requires R/R >= 3:1; STRONG BUY requires >= 4:1. If the draft verdict is BUY/STRONG BUY and your re-derived R/R fails its gate (or entry/stop/target are internally inconsistent, e.g. stop >= entry on a long), that is a REFUTATION. HOLD/SELL/STRONG SELL drafts: the R/R gate is BUY-direction-only -> verify arithmetic consistency only. Also sanity-check the stated current price against the quote bundle (within 2%): ${JSON.stringify(QUOTES).slice(0, 1500)}`,
    { label: 'skeptic:rr', phase: 'Skeptics', schema: SKEPTIC_SCHEMA }),

  () => safeAgent(`${COMMON}
LENS 3 -- ROUTING (the permanent NBIS-trap check). Verify scoring_path against the MASTER INVARIANT: positive-eps-standard is reachable ONLY when TTM operating income >= 0; a loss-maker NEVER runs the standard composite; GAAP NI>0 with op-income<0 forces the bridge (NBIS trap). FENCES: TTM revenue <$20M OR EV/Sales >100x -> pre-revenue guard (NR). STEP 2a: a CYCLICAL name (declining revenue OR sign-mixed op-income lookback: >=1 loss FY AND >=1 positive-op-income FY in the last 4 FY -- the RECOVERED-cyclical/loss-trough read) with op-income >= 0 must route positive-eps-standard WITH a mandatory mid-cycle-margin note -- if the draft is a cyclical-still-profitable name and the mid-cycle note is absent from the routing trace/claims, that is a REFUTATION. SOLVENCY gates (bridge path only): runway <4Q + no committed financing -> upside capped HOLD; <2Q -> SELL; pre-revenue runway <12mo -> SELL. If the draft verdict violates any gate given the fundamentals, REFUTE. Fundamentals bundle: ${JSON.stringify(FUNDAMENTALS).slice(0, 2000)}. Routing trace: ${ROUTING_TRACE}`,
    { label: 'skeptic:routing', phase: 'Skeptics', schema: SKEPTIC_SCHEMA }),

  () => safeAgent(`${COMMON}
LENS 4 -- PROVENANCE. Audit the claims array: every quantitative claim MUST carry a prov field of form "mcp:<server>:<key>" | "script:yfinance" | "web:<domain>+<grade>". If >10% of quantitative claims lack prov, REFUTE. Cross-check every price-type claim against the quote-technicals bundle within 2% tolerance (stale-price detection) -- any price divergence >2% is a REFUTATION. Also spot-check 3 prov tags for plausibility (an "mcp:edgar:*" tag on a number EDGAR cannot supply is a REFUTATION). Claims: ${JSON.stringify(CLAIMS.slice(0, 60))}. Quotes: ${JSON.stringify(QUOTES).slice(0, 1500)}`,
    { label: 'skeptic:provenance', phase: 'Skeptics', schema: SKEPTIC_SCHEMA }),
])

// ---------- Phase: Verdict ----------
phase('Verdict')
const fallback = (name) => ({ refutation: true, details: name + ' skeptic failed to return a valid contract -- treat as refutation (fail-closed; verification could not complete)', checked_items: [] })
const validSkeptic = (value) => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false
  if (Object.keys(value).sort().join(',') !== 'checked_items,details,refutation') return false
  if (typeof value.refutation !== 'boolean' || typeof value.details !== 'string' || !value.details.trim()) return false
  if (!Array.isArray(value.checked_items) || !value.checked_items.length || value.checked_items.length > 10000) return false
  if (value.checked_items.some(item => typeof item !== 'string' || !item.trim())) return false
  return new Set(value.checked_items).size === value.checked_items.length
}
const checked = (name, value) => validSkeptic(value) ? value : fallback(name)
const skeptics = {
  'data-integrity': checked('data-integrity', dataIntegrity),
  'rr': checked('rr', riskReward),
  'routing': checked('routing', routing),
  'provenance': checked('provenance', provenance),
}
const refutations = Object.entries(skeptics).filter(([k, v]) => v.refutation)
log(`verdict: ${refutations.length} refutation(s) [${refutations.map(([k]) => k).join(',')}]`)

return {
  ticker: T,
  run_timestamp: RUN_TS,
  any_refutation: refutations.length > 0,
  refuting_skeptics: refutations.map(([k]) => k),
  skeptics,
  verification_scope: 'Sampled skeptics with a read-only instruction; mechanically isolated final-artifact review remains required for material conclusions.',
  read_only_assurance: {
    status: 'unavailable',
    boundary: 'prompt_instruction_only',
    reason: 'The installed Workflow agent API has no verified per-call tool or permission restriction. No mechanical read-only isolation is claimed.',
  },
  accepted_report: false,
  requires_separate_read_only_review: true,
  parent_directive: refutations.length > 0
    ? 'Phase N HALT: F11 stays set, ZERO writes, surface the refutation details for review.'
    : 'Wave 3 sampled checks: 0 refutations. Compose a draft under standard discipline; acceptance requires a separately isolated final-artifact review.',
}

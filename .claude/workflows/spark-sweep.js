// spark-sweep.js -- /spark vNEXT Tier-A scout fan-out (2026-06-10)
//
// TWO-INVOCATION ARCHITECTURE (D4 pattern, invest-research.js precedent):
//   spark-sweep.js = the 9 pattern-class-scout dispatches (or 1 for theme mode).
//   The MAIN LOOP then runs the report spine (E.1 inline fallback for fallback
//   classes only -> D-merge -> F substantive filter -> G promotion cap ->
//   H calibration -> H.5 verify gate -> I/J/K(21)/L/M/N/O/P).
//   spark-verify.js (companion) runs the adversarial wave on qualifying sparks.
//
// READ-ONLY FLEET: every scout researches and returns JSON. All vault writes
// happen in the main loop under F11/sha256/path-guard discipline. The scout
// .md contract + opus/xhigh definition are UNCHANGED -- the JSON schema here
// wraps the markdown contract 1:1 (the markdown contract remains authoritative
// for Tier-B sequential dispatch).
//
// Token budget: the workflow sandbox has NO Node API (no process.env), so the
// main loop reads SPARK_DW_TOKEN_BUDGET (default 600000 full sweep / 250000
// theme; LOW-confidence placeholders -- instrument and recalibrate after 2
// runs per ref-dw-topology.md sec 9) and passes it as args.token_budget.
//
// R1 TEMPORAL FENCE (strategist amendment 2026-06-10): on any RETROSPECTIVE
// run (window_end < run date) corpus extracts must be as-of filtered by the
// orchestrator (artifacts dated <= window_end). This script enforces the fence
// FAIL-CLOSED: retrospective extracts not marked as-of-clean are DROPPED with
// a log line. Production runs (window_end = run date) filter nothing.
//
// Resume rule: on any mid-run interruption, re-invoke with
// Workflow({scriptPath, resumeFromRunId}) -- completed scouts return cached.
// Never re-run a finished wave. No Date.now()/Math.random() (resume safety);
// run_timestamp arrives via args.
//
// Fan-out doctrine: concurrency <= 6 -> classes dispatched in chunked waves
// of [<=6, rest] (deterministic doctrine compliance; ratified HALT-1 call #1).

export const meta = {
  name: 'spark-sweep',
  description: '9-class pattern-class-scout fan-out for /spark vNEXT Tier-A. Read-only; main loop runs Phases F-P after this returns.',
  phases: [
    { title: 'Scouts', detail: 'pattern-class-scout per class via agentType, chunked waves <=6' },
    { title: 'Converge', detail: 'contract validation + fallback markers + bundle assembly' },
  ],
}

// ---------- defensive args parse ----------
let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
if (!A || typeof A !== 'object') A = {}
if (A.dry_run) return { dry_run_ok: true, classes: A.classes || null }
if (!Array.isArray(A.classes) || A.classes.length === 0) {
  return { error: 'classes[] required (args: {classes, window_days, run_timestamp, mode, window_end, session_id, vault_context_summary, corpus_extracts, prior_sparks_summary, token_budget})' }
}

const VALID_CLASSES = ['cross-domain', 'behavioral', 'thesis-evolution', 'failure-mode',
  'decision-divergence', 'negative-space', 'frequency-recency', 'tool-skill', 'meta']
const CLASSES = A.classes.filter(c => VALID_CLASSES.includes(c))
const invalid = A.classes.filter(c => !VALID_CLASSES.includes(c))
if (invalid.length) log(`WARN: invalid classes dropped: ${invalid.join(',')}`)
if (!CLASSES.length) return { error: 'no valid classes after filtering: ' + A.classes.join(',') }

const MODE = A.mode || (CLASSES.length === 1 ? 'theme' : 'scan')
const WINDOW_DAYS = A.window_days || 14
const RUN_TS = A.run_timestamp || 'unknown'
const RUN_DATE = String(RUN_TS).slice(0, 10)
const W_END = A.window_end || RUN_DATE
const RETRO = /^\d{4}-\d{2}-\d{2}$/.test(W_END) && /^\d{4}-\d{2}-\d{2}$/.test(RUN_DATE) && W_END < RUN_DATE
const BUDGET = A.token_budget || (MODE === 'theme' ? 250000 : 600000)
const VAULT_CTX = A.vault_context_summary || '(none provided)'
const PRIOR = A.prior_sparks_summary || '(no prior-sparks summary provided; read wiki/research/sparks/ per your contract)'
const CE = (A.corpus_extracts && typeof A.corpus_extracts === 'object') ? A.corpus_extracts : {}

log(`spark-sweep mode=${MODE} classes=${CLASSES.length} window=${WINDOW_DAYS}d end=${W_END} retro=${RETRO} budget=${BUDGET} ts=${RUN_TS}`)

// ---------- R1 temporal fence (fail-closed) ----------
// Orchestrator contract (ref-dw-topology.md sec 8): corpus_extracts.as_of is the
// date up to which every extract was filtered. On retrospective runs, extracts
// without a clean as_of (<= window_end) are dropped -- a scout that parrots a
// post-window artifact proves nothing about the detector.
let FENCED = false
if (RETRO) {
  const asOf = CE.as_of || null
  if (!asOf || !(/^\d{4}-\d{2}-\d{2}$/.test(asOf)) || asOf > W_END) {
    FENCED = true
    log(`R1 TEMPORAL FENCE: retrospective run (window_end=${W_END} < run_date=${RUN_DATE}) with as_of=${asOf || 'missing'} -- ALL corpus extracts dropped (fail-closed)`)
  }
}
const EX = (key) => (FENCED ? null : (CE[key] || null))

// ---------- scout JSON wrapper schema (maps 1:1 onto the markdown contract) ----------
const SCOUT_SCHEMA = {
  type: 'object',
  properties: {
    class: { type: 'string' },
    window: { type: 'string' },
    continuity: { type: 'array', items: { type: 'object', properties: {
      prior_spark: { type: 'string' }, pattern: { type: 'string' },
      status: { type: 'string' }, note: { type: 'string' },
    }, required: ['prior_spark', 'status'] } },
    no_patterns: { type: 'boolean' },
    sparks: { type: 'array', items: { type: 'object', properties: {
      title: { type: 'string' },
      class: { type: 'string' },
      domains: { type: 'array', items: { type: 'string' } },
      evidence: { type: 'array', items: { type: 'object', properties: {
        file: { type: 'string' }, date: { type: 'string' },
        line: { type: ['number', 'string'] }, quote: { type: 'string' },
      }, required: ['file', 'date', 'quote'] } },
      pattern: { type: 'string' },
      confidence_pct: { type: 'number' },
      confidence_rationale: { type: 'string' },
      downstream_rec: { type: 'string' },
      prediction: { type: ['object', 'null'], properties: {
        test: { type: 'string' }, horizon: { type: 'string' }, direction: { type: 'string' },
      } },
    }, required: ['title', 'class', 'domains', 'evidence', 'pattern', 'confidence_pct', 'confidence_rationale', 'downstream_rec'] } },
  },
  required: ['class', 'window', 'continuity', 'no_patterns', 'sparks'],
}

// ---------- per-class extra corpus (S4 wiring; orchestrator-resolved, args-passed) ----------
function CORPUS(cls) {
  const blocks = []
  if (cls === 'tool-skill') {
    if (EX('telemetry_report_path')) blocks.push(`TELEMETRY REPORT (real invocation/failure data; Read this file): ${EX('telemetry_report_path')}`)
    if (EX('claudewatch_summary')) blocks.push(`CLAUDEWATCH IN-SESSION SUMMARY (orchestrator-resolved; you cannot call MCP):\n${EX('claudewatch_summary')}`)
  }
  if (cls === 'thesis-evolution' || cls === 'failure-mode') {
    if (EX('calibration_rows')) blocks.push(`CALIBRATION-MONITOR CALL-LOG ROWS (wiki/investing/calibration-monitor.md; scored verdicts + NEW-vs-SHADOW divergences ARE ${cls} signal):\n${EX('calibration_rows')}`)
  }
  if (cls === 'decision-divergence') {
    blocks.push('RATIFIED-vs-EXECUTED GAP DETECTION: cross-reference Calendar/decisions/decision-log.md + sessions-log ratified decisions against subsequent execution artifacts (orders, submissions, file mutations). A ratified decision with no execution artifact and no formal decline IS the divergence signal.')
    if (EX('ratification_queue')) blocks.push(`OVERNIGHT RATIFICATION QUEUE (propose-only items awaiting action):\n${EX('ratification_queue')}`)
    if (EX('proposals_inventory')) blocks.push(`PROPOSALS INVENTORY (wiki/maintenance/proposals/; proposed-but-unratified aging):\n${EX('proposals_inventory')}`)
  }
  if (cls === 'negative-space' || cls === 'meta') {
    if (EX('partw_extract')) blocks.push(`HONEST-GAPS REGISTER (operator-maintained EXCLUDE/context list -- documented doc-only fictions, excised subsystems, and known-dormant domains are NOT mysterious absences; cite pointer-style as "(honest-gaps register)", never quote at length):\n${EX('partw_extract')}`)
  }
  return blocks.length ? `\nPARENT-PASSED CORPUS EXTRACTS (additive context; your standard Read/Grep/Glob corpus per your contract still applies):\n${blocks.join('\n\n')}` : ''
}

// ---------- convergence gate (invest-research.js dispatch precedent) ----------
const missing = (obj, fields) => !obj ? fields : fields.filter(f => obj[f] === undefined)
const REQUIRED = ['class', 'continuity', 'sparks', 'no_patterns']

async function dispatchScout(cls) {
  const retroRule = RETRO
    ? `\nRETROSPECTIVE RUN RULE (R1; MECHANICALLY ENFORCED): the window ENDS ${W_END}. Every evidence anchor MUST cite an artifact whose OWN entry date is <= ${W_END} -- anchors dated after ${W_END} are INVALID and will be MECHANICALLY DROPPED at convergence. Treat the vault as it stood on ${W_END}: files updated after ${W_END} (hot.md, later sessions-log entries, later daily notes, summaries) are FORBIDDEN as anchors even when they describe in-window events. Date every anchor by the artifact's own entry/session date (not the event it describes), and the quote field MUST be the LITERAL line at the cited file:line -- spliced or paraphrased quotes are contract violations.`
    : ''
  const prompt = `Scout the ${cls} pattern class per your contract. Input: {class: "${cls}", time_window: "${WINDOW_DAYS}d ending ${W_END}", session_id: "${A.session_id || 'spark-sweep'}"}. Run timestamp: ${RUN_TS}.
Return STRUCTURED JSON per the enforced schema -- it maps 1:1 onto your markdown contract: class, window ("<start> to ${W_END}"), continuity[] (vs prior 3 spark reports; always present, empty array only if no prior sparks exist), no_patterns flag, sparks[] (0-5 ranked; each with title, class, domains, evidence anchors {file, date, line, quote}, pattern (falsifiable, not metaphorical), confidence_pct (calibrated integer, per-class caps per ref-pattern-taxonomy.md), confidence_rationale, downstream_rec (/decide | /challenge | /retro | /consolidate | none), prediction ({test, horizon, direction} -- OPTIONAL, null if none; test MUST be vault-observable and mechanically scorable: path/glob existence, count delta, calibration-monitor row condition, or dated artifact)).
no_patterns:true with empty sparks[] is a SUCCESSFUL high-value return -- NEVER manufacture patterns. "No actionable patterns this class" semantics unchanged.
HARD RULES: Read/Grep/Glob only (you have no other tools). Do NOT read any *.local.md file -- parent-passed extracts below are your only window into operator-local context. ASCII-only output. Evidence quotes must be literal source lines.${retroRule}
Vault context summary (Phase 0): ${VAULT_CTX}
Prior sparks summary: ${PRIOR}${CORPUS(cls)}`

  let r = await agent(prompt, { label: `scout:${cls}`, phase: 'Scouts', agentType: 'pattern-class-scout', schema: SCOUT_SCHEMA })
  let miss = missing(r, REQUIRED)
  if (miss.length) {
    log(`CONVERGENCE-GATE: scout:${cls} contract violation (missing: ${miss.join(',')}) -- one re-dispatch`)
    r = await agent(prompt, { label: `scout:${cls}-retry`, phase: 'Scouts', agentType: 'pattern-class-scout', schema: SCOUT_SCHEMA })
    miss = missing(r, REQUIRED)
    if (miss.length) {
      log(`CONVERGENCE-GATE: scout:${cls} FALLBACK marker (missing: ${miss.join(',')}) -- main loop runs inline Phase E.1 for this class only`)
      return { _fallback: true, class: cls, fallback_reason: 'contract violation after re-dispatch: missing ' + miss.join(',') }
    }
  }
  return r
}

// ---------- Phase: Scouts (chunked waves, fan-out <= 6) ----------
phase('Scouts')
const CHUNK = 6
const results = {}
for (let i = 0; i < CLASSES.length; i += CHUNK) {
  const wave = CLASSES.slice(i, i + CHUNK)
  log(`wave ${1 + i / CHUNK}: dispatching [${wave.join(', ')}]`)
  const out = await parallel(wave.map(c => () => dispatchScout(c)))
  wave.forEach((c, j) => { results[c] = out[j] || { _fallback: true, class: c, fallback_reason: 'dispatch returned null (skipped or terminal error)' } })
}

// ---------- Phase: Converge ----------
phase('Converge')

// R1 OUTPUT-SIDE FENCE: on retrospective runs, mechanically drop evidence anchors
// dated after window_end (a post-window citation proves nothing about the detector;
// the prompt rule is advisory -- this filter is not). Sparks losing ALL anchors are
// marked evidence_stripped (the parent routes them to patterns_below_threshold).
let scrubbed = 0
if (RETRO) {
  for (const [cls, r] of Object.entries(results)) {
    if (!r || r._fallback || !Array.isArray(r.sparks)) continue
    for (const s of r.sparks) {
      if (!Array.isArray(s.evidence)) continue
      const before = s.evidence.length
      s.evidence = s.evidence.filter(e => e && e.date && String(e.date).slice(0, 10) <= W_END)
      const dropped = before - s.evidence.length
      if (dropped > 0) {
        scrubbed += dropped
        s.temporal_scrub_dropped = dropped
        log(`R1 OUTPUT FENCE: ${cls} spark "${String(s.title || '').slice(0, 60)}" -- ${dropped} post-window anchor(s) dropped`)
      }
      if (s.evidence.length === 0) {
        s.evidence_stripped = true
        log(`R1 OUTPUT FENCE: ${cls} spark "${String(s.title || '').slice(0, 60)}" lost ALL anchors -- evidence_stripped (parent routes to below-threshold)`)
      }
    }
  }
}

const fallbackClasses = Object.values(results).filter(r => r && r._fallback).map(r => r.class)
let sparkCount = 0, noPatternCount = 0
for (const [cls, r] of Object.entries(results)) {
  if (r && !r._fallback) {
    sparkCount += (r.sparks || []).length
    if (r.no_patterns) noPatternCount++
  }
}
log(`converge: ${sparkCount} candidate sparks across ${CLASSES.length} classes; no-patterns=${noPatternCount}; fallback=[${fallbackClasses.join(',')}]; temporal_fence=${FENCED}`)

return {
  topology: 'dw',
  mode: MODE,
  window: `${WINDOW_DAYS}d ending ${W_END}`,
  window_end: W_END,
  retrospective: RETRO,
  temporal_fence_dropped_extracts: FENCED,
  temporal_scrub_dropped_anchors: scrubbed,
  run_timestamp: RUN_TS,
  bundle_version: 'spark-vnext-1',
  scouts: results,
  fallback_classes: fallbackClasses,
  tally: { classes_dispatched: CLASSES.length, candidate_sparks: sparkCount, no_pattern_classes: noPatternCount, fallback_classes: fallbackClasses.length },
  token_budget_logged: BUDGET,
  epilogue: 'MAIN LOOP MUST now run: Phase E.1 inline fallback (per ref-pattern-taxonomy.md) for fallback_classes ONLY -> Phase D continuity merge (+ prediction scoring) -> F substantive filter (+ playbooks dedup) -> G promotion cap -> H confidence calibration -> H.5 verify gate (spark-verify.js when any promoted spark qualifies) -> I meta-observation -> J FOLLOWUPS -> K 21-item gate -> L ASCII scan -> M compose -> N verify -> O atomic write -> P peripherals.',
}

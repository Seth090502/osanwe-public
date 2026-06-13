// spark-verify.js -- /spark vNEXT adversarial verification wave (2026-06-10)
//
// Companion to spark-sweep.js (two-invocation architecture, D4 pattern;
// invest-verify.js precedent). The MAIN LOOP invokes this at Phase H.5, AFTER
// Phase H confidence calibration, and ONLY for QUALIFYING promoted sparks:
// confidence >= 70, OR class == meta, OR scout downstream_rec == /decide
// (the SCOUT-RETURN field -- never Phase J output; phase-ordering invariant),
// OR --verify (qualifies all promoted). Zero qualifying sparks -> wave skipped
// entirely (the cost lever). Cap 7 verifiers/run; fan-out <= 6 (chunked).
//
// ONE read-only verifier agent per qualifying spark, applying FOUR LENSES
// SEQUENTIALLY inside that agent, fail-closed, default-to-refuted:
//   L1 EVIDENCE      -- every cited file:date:line must EXIST and SUPPORT;
//                       literal source line quoted back. Fabricated -> REFUTED.
//   L2 FALSIFIABILITY -- pattern must be testable; metaphor -> REFUTED.
//   L3 NOVELTY       -- insight-stream + wiki/playbooks/ + prior sparks;
//                       already-named -> DEMOTED to PERSISTED-continuity.
//   L4 MUNDANE-ALT   -- calendar artifact / single-cause cascade /
//                       vault-mechanics artifact -> haircut or REFUTED.
//
// ANY refuted lens -> the main loop drops the spark to patterns_below_threshold
// with the refutation reason (transparent suppression, never silent); the
// report proceeds with survivors. Missing/invalid verifier return = REFUTED
// (fail-closed; invest-verify.js fallback pattern verbatim).
//
// READ-ONLY: verifiers never Write/Edit and never read any *.local.md file.
// No Date.now()/Math.random(); run_timestamp via args. Resume via
// Workflow({scriptPath, resumeFromRunId}).

export const meta = {
  name: 'spark-verify',
  description: 'Adversarial verification wave for /spark vNEXT: one 4-lens verifier per qualifying spark, fail-closed. Read-only. Refuted sparks drop to patterns_below_threshold.',
  phases: [
    { title: 'Verify', detail: 'one 4-lens skeptic per qualifying spark (evidence/falsifiability/novelty/mundane), chunked <=6' },
    { title: 'Verdict', detail: 'aggregate tally {fired, refuted, demoted, survived} for the parent' },
  ],
}

// ---------- defensive args parse ----------
let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
if (!A || typeof A !== 'object') A = {}
if (A.dry_run) return { dry_run_ok: true, sparks: Array.isArray(A.sparks) ? A.sparks.length : null }
if (!Array.isArray(A.sparks) || A.sparks.length === 0) {
  return { error: 'sparks[] required (args: {sparks: [{id, title, class, confidence_pct, evidence, pattern, continuity, prediction, downstream_rec}], run_timestamp, window})' }
}

const RUN_TS = A.run_timestamp || 'unknown'
const CAP = 7
let SPARKS = A.sparks
if (SPARKS.length > CAP) {
  log(`CAP: ${SPARKS.length} qualifying sparks > ${CAP} -- verifying the first ${CAP} (ranked order); DROPPED unverified: ${SPARKS.slice(CAP).map(s => s.id || s.title).join(', ')} (no silent caps)`)
  SPARKS = SPARKS.slice(0, CAP)
}
log(`spark-verify: ${SPARKS.length} qualifying spark(s), ts=${RUN_TS}`)

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    verdict: { enum: ['SURVIVES', 'REFUTED', 'DEMOTED'] },
    refuted_lenses: { type: 'array', items: { type: 'string' } },
    recalibrated_confidence: { type: 'number' },
    refutation_reason: { type: ['string', 'null'] },
    lens_results: { type: 'object', properties: {
      evidence: { type: 'object', properties: { pass: { type: 'boolean' }, literal_quotes: { type: 'array' }, detail: { type: 'string' } }, required: ['pass', 'detail'] },
      falsifiability: { type: 'object', properties: { pass: { type: 'boolean' }, detail: { type: 'string' } }, required: ['pass', 'detail'] },
      novelty: { type: 'object', properties: { pass: { type: 'boolean' }, prior_match: { type: ['string', 'null'] }, detail: { type: 'string' } }, required: ['pass', 'detail'] },
      mundane: { type: 'object', properties: { pass: { type: 'boolean' }, alternative: { type: ['string', 'null'] }, detail: { type: 'string' } }, required: ['pass', 'detail'] },
    }, required: ['evidence', 'falsifiability', 'novelty', 'mundane'] },
    checked_items: { type: 'array', items: { type: 'string' } },
  },
  required: ['verdict', 'refuted_lenses', 'recalibrated_confidence', 'refutation_reason', 'lens_results', 'checked_items'],
}

const COMMON = `READ-ONLY adversarial verifier for /spark vNEXT (run ${RUN_TS}). Your job is to REFUTE the spark below if you can -- default to suspicion; an unverifiable claim is a refuted claim (fail-closed). But a refutation must be SPECIFIC and evidenced (name the file, the line, the rule violated); a restatement of already-surfaced nuance is NOT a refutation.
Apply FOUR LENSES SEQUENTIALLY and report each in lens_results:
L1 EVIDENCE skeptic: Read EVERY cited evidence anchor (file + date + line). The cited line must EXIST (allow +/-5 lines of drift) and must SUPPORT the claim as quoted. Quote the literal source line back into lens_results.evidence.literal_quotes (one per anchor). A fabricated, misread, or non-supporting anchor -> lens FAILS -> verdict REFUTED.
L2 FALSIFIABILITY skeptic: the pattern statement must be testable -- it must imply an observable that could come out the other way ("golf progressive overload maps to career skill-building cadence" is testable; "investing is like meditation" is hand-waving). Metaphorical hand-waving -> lens FAILS -> REFUTED.
L3 NOVELTY skeptic: Grep wiki/insight-stream.md + wiki/playbooks/ + wiki/research/sparks/ for this pattern under any name. If the pattern is ALREADY NAMED there -> verdict DEMOTED (not refuted): set prior_match to the naming artifact; the parent records it as PERSISTED-continuity, not a new spark.
L4 MUNDANE-ALTERNATIVE skeptic: is there a simpler non-pattern explanation -- a calendar artifact (weekend/holiday gap), a single-cause cascade (one event explaining all anchors), a vault-mechanics artifact (a skill or hook mechanically generating the signal)? A sustained mundane alternative -> either a confidence haircut (set recalibrated_confidence with the arithmetic in detail) or, if it fully explains the pattern, REFUTED.
Verdict rule: any FAILED lens (L1/L2/L4) -> REFUTED with refutation_reason; L3 prior-match alone -> DEMOTED; otherwise SURVIVES with recalibrated_confidence (unchanged unless L4 haircut applies).
HARD RULES: never Write or Edit; never read any *.local.md file; ASCII-only; list every file you opened in checked_items.`

// ---------- Phase: Verify (chunked, fan-out <= 6) ----------
phase('Verify')
const CHUNK = 6
const verdictList = []
for (let i = 0; i < SPARKS.length; i += CHUNK) {
  const wave = SPARKS.slice(i, i + CHUNK)
  const out = await parallel(wave.map(s => () =>
    agent(`${COMMON}\n\nSPARK UNDER TEST:\n${JSON.stringify(s, null, 2)}`,
      { label: `verify:${s.id || s.title}`, phase: 'Verify', schema: VERDICT_SCHEMA })))
  wave.forEach((s, j) => verdictList.push({ spark: s, verdict: out[j] }))
}

// ---------- Phase: Verdict ----------
phase('Verdict')
const fallback = (s) => ({
  verdict: 'REFUTED',
  refuted_lenses: ['contract'],
  recalibrated_confidence: 0,
  refutation_reason: 'verifier failed to return a valid contract -- treated as refutation (fail-closed; verification could not complete)',
  lens_results: {
    evidence: { pass: false, literal_quotes: [], detail: 'no valid verifier return' },
    falsifiability: { pass: false, detail: 'no valid verifier return' },
    novelty: { pass: false, prior_match: null, detail: 'no valid verifier return' },
    mundane: { pass: false, alternative: null, detail: 'no valid verifier return' },
  },
  checked_items: [],
})
const verdicts = {}
let refuted = 0, demoted = 0, survived = 0
for (const { spark, verdict } of verdictList) {
  const key = spark.id || spark.title
  const v = (verdict && verdict.verdict) ? verdict : fallback(spark)
  verdicts[key] = v
  if (v.verdict === 'REFUTED') refuted++
  else if (v.verdict === 'DEMOTED') demoted++
  else survived++
}
log(`verdict: fired=${verdictList.length} refuted=${refuted} demoted=${demoted} survived=${survived}`)

return {
  run_timestamp: RUN_TS,
  verdicts,
  tally: { fired: verdictList.length, refuted, demoted, survived },
  parent_directive: 'REFUTED sparks -> patterns_below_threshold with the refutation_reason (transparent suppression, never silent); DEMOTED sparks -> Continuity Audit table as PERSISTED (prior_match named), removed from numbered new sparks; SURVIVORS proceed to Phases I/J with recalibrated_confidence. Record the tally in meta.json verify_wave + the report footer (gate item 19).',
}

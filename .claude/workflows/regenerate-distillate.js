// # regenerate-distillate
//
// Fires when the SessionStart injector's SENTINEL-2 reports DISTILLATE STALE (live master-doc
// sha256-16 no longer matches the hash recorded in the distillate provenance line).
//
// Ratified method (mission 2026-06-09, plan mission-v2-fable-tailored-executor-majestic-conway):
// dynamic unit discovery (W3 -- never hardcode Part line numbers), session-model extractors (the only
// sanctioned downgrade), session-model default-to-refuted judges, max 2 fix rounds per unit,
// [2026-08-17] the judges and the two discovery calls were "inherit-model" as ratified. A
// built-in agentType (Explore) carries no frontmatter model, so inherit meant the SESSION
// model -- a breach of the AGENTS.md:58 subagent ceiling under any frontier-tier session.
// Pinned to opus: identical behaviour under an Opus session, ceiling-safe under any other,
// and the ratified intent (judges at least as strong as the session-model extractors) is preserved.
// A cheaper discovery tier would be a real change to the ratified method -- not done here.
// sensitive Parts B / N3 / X / Appendix 4 EXCLUDED from every agent's readable range
// (pointer skeletons are composed main-loop), read-only doctrine (no workflow agent writes).
//
// ## MAIN-LOOP EPILOGUE (the workflow returns data; the invoking session MUST then):
//
// 1. Confirm `git check-ignore <dest_path>` passes BEFORE writing the first byte (the
//    .gitignore line for the distillate already exists at .gitignore ~line 42).
// 2. Set F11 (.claude/state/auto-commit-disabled) via tools/lib/f11_orchestrator.py before
//    any vault write; clear after final commit.
// 3. Assemble: canonical frontmatter (categories [meta], status active) + PROVENANCE header
//    (source sha256-16 of the LIVE doc, doc baseline commit = current HEAD short, generation
//    date, method line, this workflow named as the regeneration recipe) + THIS-MISSION
//    CHANGES block ONLY if infra changed + VERIFIED-ERRATA register (carry forward E1/E2/E3
//    conventions: [CODE-VERIFIED]/[DISK-VERIFIED]/[MISSION-VERIFIED] tags) + COUNTERMANDS +
//    unit bodies in doc order + B/N3/X pointer skeletons (topics + live line ranges, NO
//    values) + Appendix-4 pointer inside the X skeleton + Operator-Appendix-A inventory.
// 4. Inner code fences as ~~~ (keeps vault-audit code-fence-aware); ASCII-only; ZERO
//    wikilink syntax; word count <= word_ceiling (zero-sum: additions displace lower-value
//    lines, the ceiling never grows).
// 5. Verify post-write: wc -w <= ceiling; non-ASCII scan = 0; credential-pattern scan = 0;
//    git check-ignore still passes; git status does not show the file.
// 6. Run the precision re-verify + gap-hunt (loop-until-dry) + 12-question cold exam
//    (gate >= 10/12) pattern from the ratified mission before declaring the refresh done.
// 7. The SessionStart injector (.claude/hooks/inject-<private-file>.py) needs NO
//    change -- it re-reads the recorded sha each session.

export const meta = {
  name: 'regenerate-distillate',
  description: 'Regenerate the <private-file>: dynamic unit discovery + sonnet extract + opus judge + fix + re-judge (read-only fleet)',
  phases: [
    { title: 'Discover', detail: 'live Part boundary discovery from the master doc' },
    { title: 'Extract', detail: 'session-model extractors, one per unit' },
    { title: 'Judge', detail: 'session-model default-to-refuted judges' },
    { title: 'Fix', detail: 'session-model fixes for refuted units' },
  ],
}

// Args robustness (mission 2026-06-09 finding): in at least one harness build the
// `args` global arrives undefined OR as a JSON-encoded string. Parse defensively.
// Default behavior with NO args is the FULL regeneration run (the sentinel-fired
// purpose of this workflow); pass {dry_run: true} for zero-agent validation.
let A = args
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { A = {} } }
if (!A || typeof A !== 'object') A = {}
const DOC = A.doc_path || '/path/to/vault/<private-file>.local.md'
const DEST = A.dest_path || '/path/to/vault/OSANWE-<private-file>.local.md'
const CEILING = A.word_ceiling || 6500
if (A.dry_run) {
  // Parse-and-resolve validation path: meta parsed, constants bound, zero agents spent.
  return { dry_run_ok: true, doc: DOC, dest: DEST, ceiling: CEILING }
}

// Ratified per-part budgets (2026-06-09). Unknown future parts fall back by line count.
const BUDGETS = { PRE: 120, A: 220, C: 240, D: 340, E: 300, F: 340, G: 250, H: 300, I: 220, J: 200, K: 250, L: 250, M: 90, N1: 160, N2: 110, N4: 50, N5: 60, O: 110, P: 220, Q: 200, R: 180, S: 100, T: 300, U: 120, V: 200, W: 360, GLOSS: 130, OPB: 380, OPA: 80 }
const SENSITIVE = new Set(['B', 'N3', 'X'])

phase('Discover')
const disc = await agent(
  'Read-only task. Run Grep with -n on ' + DOC + ' for the regex "^#{1,3} (Part [A-Z][0-9]? --|GLOSSARY|APPENDICES|OPERATOR APPENDIX [AB])" (output_mode content) and also report the total line count of the file (wc -l). Return {headings: [{line, text}], total_lines}. Read nothing else.',
  { agentType: 'Explore', schema: { type: 'object', required: ['headings', 'total_lines'], properties: { total_lines: { type: 'integer' }, headings: { type: 'array', items: { type: 'object', required: ['line', 'text'], properties: { line: { type: 'integer' }, text: { type: 'string' } } } } } }, label: 'discover:boundaries', phase: 'Discover' }
)
if (!disc || !disc.headings || !disc.headings.length) { return { error: 'boundary discovery failed -- no headings' } }

// Build unit list: key from heading text; end = next heading line - 1; exclude sensitive.
const hs = disc.headings.slice().sort((a, b) => a.line - b.line)
const units = []
for (let i = 0; i < hs.length; i++) {
  const t = hs[i].text
  let key = null
  let m = t.match(/Part ([A-Z][0-9]?) --/)
  if (m) key = m[1]
  else if (t.includes('GLOSSARY')) key = 'GLOSS'
  else if (t.includes('OPERATOR APPENDIX B')) key = 'OPB'
  else if (t.includes('OPERATOR APPENDIX A')) key = 'OPA'
  else if (t.includes('APPENDICES')) key = 'APPX'
  if (!key) continue
  const start = hs[i].line
  const end = (i + 1 < hs.length ? hs[i + 1].line - 1 : disc.total_lines)
  if (SENSITIVE.has(key) || t.includes('[SENSITIVE]')) { log('excluding sensitive unit ' + key + ' (' + start + '-' + end + ')'); continue }
  const lines = end - start + 1
  const budget = BUDGETS[key] || (lines <= 250 ? 100 : lines <= 500 ? 200 : 300)
  units.push({ key, title: t.replace(/^#+ /, ''), start, end, budget })
}
// APPX unit: stop before Appendix 4 (cloud-ingestion flag + secrets register) -- find it.
const appx = units.find(u => u.key === 'APPX')
if (appx) {
  const a4 = await agent('Read-only. Grep -n ' + DOC + ' for "^### Appendix 4" and return the line number only as {line}.', { agentType: 'Explore', schema: { type: 'object', required: ['line'], properties: { line: { type: 'integer' } } }, label: 'discover:appendix4', phase: 'Discover' })
  if (a4 && a4.line && a4.line > appx.start && a4.line <= appx.end) { appx.end = a4.line - 1; log('APPX unit truncated before Appendix 4 (line ' + a4.line + ')') }
}
log('Discovered ' + units.length + ' extraction units; ceiling ' + CEILING)

const COMMON = [
  'You are a READ-ONLY agent: Read/Grep/Glob only (Bash only for read-only inspection). Never write or mutate.',
  'Source document: ' + DOC,
  'Read ONLY your assigned line range via Read offset/limit. Do not read any other file or range.',
  'SECRETS RULE: never include credential values, tokens, account numbers, dollar balances, position sizes, biometric or lab numbers. Structure + file LOCATIONS only.',
  'Output: compact declarative expert prose. ASCII ONLY. ZERO [[wikilink]] syntax. ~~~ for unavoidable fences.',
].join('\n')

const EXTRACT_SCHEMA = { type: 'object', additionalProperties: false, required: ['body', 'word_count', 'pointers'], properties: { body: { type: 'string' }, word_count: { type: 'integer' }, pointers: { type: 'array', items: { type: 'string' } } } }
const JUDGE_SCHEMA = { type: 'object', additionalProperties: false, required: ['verdict', 'reasons', 'required_fixes'], properties: { verdict: { type: 'string', enum: ['pass', 'refuted'] }, reasons: { type: 'array', items: { type: 'string' } }, required_fixes: { type: 'array', items: { type: 'string' } } } }

const results = await pipeline(
  units,
  (u) => agent(COMMON + '\n\nTASK: distill unit "' + u.key + ' -- ' + u.title + '" from lines ' + u.start + '-' + u.end + ' (Read offset=' + u.start + ', limit=' + (u.end - u.start + 1) + ').\nHARD word budget: ' + u.budget + ' words. Executor lens: invariants nothing else enforces, routing knowledge, exact paths, counts, dates, deprecations, honest gaps. Return body (no heading), actual word_count, pointers for omissions.', { agentType: 'Explore', schema: EXTRACT_SCHEMA, label: 'extract:' + u.key, phase: 'Extract' }),
  async (ext, u) => {
    if (!ext) return { unit: u.key, status: 'extract-failed' }
    let current = ext
    let verdict = await agent(COMMON + '\n\nADVERSARIAL JUDGE -- default to refuted when uncertain. Unit ' + u.key + ', source lines ' + u.start + '-' + u.end + ', budget ' + u.budget + '. Candidate:\n<<<\n' + current.body + '\n>>>\nRefute on: factual error vs source; missing top-3 executor-critical facts; any secret value; word count > ' + Math.round(u.budget * 1.15) + '; non-ASCII or wikilinks. Statements tagged [CODE-VERIFIED]/[DISK-VERIFIED]/[MISSION-VERIFIED] are deliberate overrides -- do not refute them for deviating from the doc.', { agentType: 'Explore', schema: JUDGE_SCHEMA, label: 'judge:' + u.key + '-r1', phase: 'Judge' })
    let rounds = 0
    while (verdict && verdict.verdict === 'refuted' && rounds < 2) {
      rounds++
      const fixed = await agent(COMMON + '\n\nRevise this refuted body for unit ' + u.key + ' (lines ' + u.start + '-' + u.end + ', budget ' + u.budget + '):\n<<<\n' + current.body + '\n>>>\nReasons: ' + JSON.stringify(verdict.reasons) + '\nFixes: ' + JSON.stringify(verdict.required_fixes) + '\nRe-read the range, apply every fix, hold the budget.', { agentType: 'Explore', schema: EXTRACT_SCHEMA, label: 'fix:' + u.key + '-r' + rounds, phase: 'Fix' })
      if (!fixed) break
      current = fixed
      verdict = await agent(COMMON + '\n\nRE-JUDGE unit ' + u.key + ' (lines ' + u.start + '-' + u.end + ', budget ' + u.budget + '), same refutation rules and override-tag rule as before. Candidate:\n<<<\n' + current.body + '\n>>>', { agentType: 'Explore', schema: JUDGE_SCHEMA, label: 'judge:' + u.key + '-r' + (rounds + 1), phase: 'Judge' })
    }
    return { unit: u.key, title: u.title, start: u.start, end: u.end, budget: u.budget, body: current.body, pointers: current.pointers || [], status: verdict ? verdict.verdict : 'no-verdict', fix_rounds: rounds }
  }
)

return {
  dest: DEST, ceiling: CEILING,
  units: results.filter(Boolean),
  epilogue: 'MAIN LOOP MUST: check-ignore proof -> F11 set -> assemble (frontmatter + provenance with LIVE doc sha256-16 + HEAD baseline + errata/countermand carry-forward + B/N3/X pointer skeletons + Appendix-4 pointer + OPA inventory) -> ASCII/wikilink/credential/word-count verification -> precision re-verify + gap-hunt + 12Q cold exam >= 10/12.',
}

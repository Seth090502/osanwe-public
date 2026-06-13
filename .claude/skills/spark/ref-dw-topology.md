---
categories: [sources]
type: reference
created: 2026-06-10
updated: 2026-06-10
status: active
tags:
  - topic/skill-infrastructure
  - topic/spark
  - topic/dynamic-workflows
aliases:
  - spark dw topology
  - spark vNEXT topology spec
related:
  - "[[ref-pattern-taxonomy]]"
  - "[[ref-output-template]]"
---

# /spark vNEXT -- Tier-A Dynamic-Workflows specification

Read-on-demand companion (the /invest ref-dw-topology pattern). SKILL.md Phase A item 6 + Phase E.0 + Phase H.5 reference this doc; this doc holds the Tier-A mechanics. The Tier-B sequential text in SKILL.md remains the AUTHORITATIVE spec of what every bundle section must contain -- Tier-A changes execution topology, never semantics. PRIME DIRECTIVE: capability superset; the scout's markdown contract, the 9-class taxonomy, thresholds, promotion formula, and calibration rules are unchanged.

## 1. Two-layer topology detection

- TOPOLOGY = `dw` iff the Workflow tool is present in the orchestrator's current session tool surface; else `sequential` (Codex engine, headless, restricted sessions, any DW regression). Ambiguity -> `sequential` (safe fallback).
- `tools/lib/capability-detect.sh` (`OSANWE_DW_HINT`) is ADVISORY only -- the tool-surface check is authoritative.
- **Forced-sequential knob (R2, ratified 2026-06-10):** `OSANWE_FORCE_SEQUENTIAL=1` (env var, or an explicit operator instruction in the invoking message) forces TOPOLOGY=sequential for test/regression runs. There is deliberately NO force-dw counterpart: dw without the Workflow tool breaks; forcing the fallback is always safe.
- Record ORCHESTRATOR_MODEL = the active model string. PASSIVE LOGGING ONLY: no behavior ever branches on model identity. TOPOLOGY + ORCHESTRATOR_MODEL flow to the Phase B print and the meta.json sidecar (`topology`, `orchestrator_model` -- additive fields).

## 2. Two-invocation architecture (D4 pattern, /invest precedent)

Workflows cannot pause for mid-run parent synthesis, and the verify wave needs the PROMOTED spark set (Phases F/G/H output). So Tier-A is two invocations with the report spine between them:

1. `spark-sweep` (`.claude/workflows/spark-sweep.js`) -- the scout fan-out. Replaces the Phase E.0 9x/1x Agent-tool dispatch EXECUTION, not its spec.
2. MAIN LOOP -- Phase E.1 inline fallback for fallback classes only -> D continuity merge (+ prediction scoring, sec 7) -> F substantive filter (+ playbooks dedup) -> G promotion cap -> H confidence calibration -> H.5 verify gate.
3. `spark-verify` (`.claude/workflows/spark-verify.js`) -- conditional adversarial wave on qualifying promoted sparks (sec 5).
4. MAIN LOOP -- Phases I/J compute over survivors -> K 21-item gate -> L/M/N/O/P under standard F11/sha256/path-guard discipline.

READ-ONLY FLEET: both workflows are pure-read; ALL vault writes happen in the main loop. This is what makes `--preview` shadow runs legal end-to-end on Tier-A.

## 3. Scout fan-out + JSON wrapper schema

- Scouts dispatched via `agentType: 'pattern-class-scout'` -- the `.claude/agents/pattern-class-scout.md` contract + opus/xhigh definition UNCHANGED.
- The workflow's SCOUT_SCHEMA wraps the scout markdown contract 1:1: `{class, window, continuity[], no_patterns, sparks[]}` where each spark = `{title, class, domains[], evidence: [{file, date, line, quote}], pattern, confidence_pct, confidence_rationale, downstream_rec, prediction|null}`. The markdown contract remains authoritative for Tier-B.
- `no_patterns: true` with empty `sparks[]` is a SUCCESSFUL return (the "No actionable patterns this class" contract, unchanged).
- Fan-out doctrine: concurrency <= 6 -> classes dispatched in chunked waves of [<=6, rest] (scan mode: 6+3). Deterministic, resume-safe (ratified HALT-1 interpretation call #1).
- args: `{classes[], window_days, run_timestamp, mode, window_end, session_id, vault_context_summary, corpus_extracts (sec 8), prior_sparks_summary, token_budget (sec 9)}`. `window_end` is first-class: retrospective windows (window_end < run date) trigger the R1 temporal fence (sec 8).

## 4. Convergence gate + main-loop spine

- Per-class convergence: presence-validate required keys (`class, continuity, sparks, no_patterns`) -> one re-dispatch on violation -> `{_fallback: true, class, fallback_reason}` marker. The MAIN LOOP runs inline Phase E.1 detection per ref-pattern-taxonomy.md for marker classes ONLY; other classes' returns are consumed as-is.
- Pre-emptive skip (not dispatching a class at all without a legitimate failure) = DEVIATION, identical semantics in both topologies (SKILL.md Execution Rules).
- The bundle's `epilogue` field restates the main-loop spine; the spine order in SKILL.md is authoritative.

## 5. Verify wave (Phase H.5; conditional)

**Qualifying criteria (per promoted spark, evaluated AFTER Phase H, BEFORE Phase I):**
- confidence >= 70, OR
- class == `meta`, OR
- the SCOUT-RETURN `downstream_rec` field == `/decide` (phase-ordering invariant: this is known from Phase E -- NEVER gate on Phase J output), OR
- `--verify` flag (qualifies ALL promoted sparks).

Zero qualifying sparks -> wave skipped entirely (the cost lever). Cap 7 verifiers/run; chunked <= 6.

**Mechanics:** ONE read-only verifier agent per qualifying spark; FOUR LENSES SEQUENTIALLY inside that agent; fail-closed, default-to-refuted; missing/invalid verifier return = REFUTED:

| Lens | Standard | Failure -> |
|---|---|---|
| L1 EVIDENCE | every cited file:date:line EXISTS (+/-5-line drift) and SUPPORTS; literal source line quoted back | REFUTED |
| L2 FALSIFIABILITY | pattern testable (the golf-overload-maps-to-career standard); no metaphorical hand-waving | REFUTED |
| L3 NOVELTY | not already named in insight-stream + wiki/playbooks/ + prior sparks | DEMOTED to PERSISTED-continuity (prior_match named; not a numbered new spark) |
| L4 MUNDANE-ALTERNATIVE | no sustained simpler explanation (calendar artifact / single-cause cascade / vault-mechanics artifact) | confidence haircut (arithmetic shown) or REFUTED |

**Outcomes:** REFUTED -> `patterns_below_threshold` with the refutation reason (transparent suppression, never silent). DEMOTED -> Continuity Audit table as PERSISTED. SURVIVES -> Phases I/J compute over survivors with `recalibrated_confidence`. Tally `{fired, refuted, demoted, survived}` -> meta.json `verify_wave` + report footer (gate item 19).

**Tier-B / wave-absent analog:** an inline evidence spot-check on the top-2 promoted sparks replaces the wave (open every cited anchor; same refute semantics). `--verify` on Tier-B forces the inline spot-check on ALL promoted sparks (ratified HALT-1 interpretation call #2).

## 6. Resume protocol (W7)

On any mid-run interruption, re-invoke with `Workflow({scriptPath, resumeFromRunId})` -- completed agents return cached results; never re-run a finished wave, never re-spend. Neither script uses `Date.now()`/`Math.random()`/argless `new Date()` (resume safety); `run_timestamp` arrives via args.

## 7. Prediction-scoring mechanics (S3)

- Each promoted spark MAY carry `**Prediction:** {test, horizon, direction}`. HARD RULE: `test` MUST be vault-observable and mechanically scorable -- a path/glob existence, a count delta, a calibration-monitor row condition, or a dated artifact. External-world tests need a named vault proxy; otherwise the scoring loop is vibes with extra steps. Stored in meta.json `predictions[]`.
- Phase D upgrade: prior sparks WITH predictions are scored `resolved-true / resolved-false / unresolved` at horizon via deterministic checks; prediction-less prior sparks keep the PERSISTED/EVOLVED/INVALIDATED/DORMANT scoring unchanged.
- Combined formula (applies only when >= 1 prediction has RESOLVED): `prior_calibration_score = (2 * pred_component + vibes_component) / 3`, where `pred_component = resolved_true / (resolved_true + resolved_false)` (unresolved excluded) and `vibes_component` = the legacy `(PERSISTED + 0.5*EVOLVED) / total` formula. Zero resolved predictions -> legacy formula stands unchanged. Trace recorded in meta.json `prediction_scoring`.
- ref-continuity-scoring.md stays DEFERRED (Pattern 21): this section is the mechanism, not the methodology doc.

## 8. Corpus-extract resolver contract (S4)

**HARD RULE:** scouts stay Read/Grep/Glob-only -- NO MCP frontmatter wiring (a restricted subagent cannot call MCP tools). The ORCHESTRATOR resolves the new corpora MAIN-LOOP (Phase C) and passes them via workflow args (Tier-A) or inline prompt context (Tier-B). Scouts NEVER read the master-context doc directly (the prompt forbids it) -- the orchestrator extracts Part W text via the live Part index offsets from the SessionStart injection. Sensitive parts are never extracted or quoted; Part W citations in committed reports are pointer-style ("(master-context Part W register)"), never long quotes.

| Class | Extra corpus | args field |
|---|---|---|
| tool-skill | latest `wiki/maintenance/telemetry-*.md` + claudewatch in-session summary when reachable (headless -> report file only) | `telemetry_report_path`, `claudewatch_summary` |
| thesis-evolution | `wiki/investing/calibration-monitor.md` Call Log rows (scored verdicts + shadow divergences) | `calibration_rows` |
| failure-mode | same calibration-monitor rows (NEW-vs-SHADOW divergence as failure signal) | `calibration_rows` |
| decision-divergence | decision-log ratified-vs-EXECUTED gap detection + overnight ratification queue (latest `wiki/research/overnight-summary-*.md` RATIFICATION QUEUE section) + `wiki/maintenance/proposals/` aging | `ratification_queue`, `proposals_inventory` |
| negative-space | Part W honest-gaps register as EXCLUDE/context list (doc-only fictions, excised subsystems, known-dormant domains are NOT mysterious absences) | `partw_extract` |
| meta | Part W register (context) + prior 3 sparks (existing corpus) | `partw_extract` |

**R1 TEMPORAL FENCE (ratified 2026-06-10; blocking amendment):** for any RETROSPECTIVE run (`window_end` < run date), every corpus extract MUST be filtered to artifacts dated <= `window_end`, and the orchestrator marks this with `corpus_extracts.as_of = <date <= window_end>`. spark-sweep.js enforces the fence FAIL-CLOSED: retrospective extracts without a clean `as_of` are dropped with a log line. Scout prompts additionally require every evidence anchor to cite artifacts dated <= window_end on retrospective runs. Production runs (window_end = today) filter nothing. Rationale: a scout that parrots a post-window artifact naming the pattern passes a retrospective control while proving nothing about the detector.

## 9. Token and cost governance (S7)

- `SPARK_DW_TOKEN_BUDGET` env var, read by the MAIN LOOP (the workflow sandbox has no `process.env`) and passed as `args.token_budget` for logging.
- Defaults: **600000** full sweep (9 scouts ~40-60K each + verify wave) / **250000** theme mode. LOW-confidence placeholders derived from the /invest telemetry shape -- instrument actuals in meta.json and RECALIBRATE after 2 production runs.
- The verify-wave skip on non-qualifying sparks and the wave cap (7) are the cost levers.

## 10. Tier-B parity statement

TOPOLOGY=sequential executes the SKILL.md Phase E.0 Agent-tool dispatch path VERBATIM -- 9 parallel pattern-class-scout instances (scan) or 1 (theme), markdown contract, inline E.1 fallback, identical DEVIATION semantics. Zero behavioral difference from the pre-vNEXT skill except the additive layers that are topology-independent (corpus extracts via inline prompt context, prediction fields, Phase D prediction scoring, playbooks dedup, the Tier-B inline verification spot-check, gate items 19-21, sidecar logging fields). Codex/headless/regression sessions always run Tier-B. `OSANWE_FORCE_SEQUENTIAL=1` (sec 1) exercises this path deliberately in a Workflow-capable session -- regression/parity runs MUST cite the mechanism used.

## 11. Shadow-run protocol + control test cases

Shadow validation is zero-write BY CONSTRUCTION on Tier-A: both workflows are read-only and `--preview` skips Phases O/P (F11 never set). Proof standard: `git status` byte-identical before/after each shadow run; hot.md untouched.

Standing control cases (pre-registered at HALT 1, 2026-06-10):
1. **Retrospective decision-divergence positive control (detector test):** `spark-sweep.js` with `classes: ['decision-divergence']`, a `window_end` in the past, OMITTING `ratification_queue` + `proposals_inventory` entirely (R1b). PASS = the scout reconstructs a ratified-but-unexecuted trade gap from primary sources dated <= `window_end` (sessions-log entries from the relevant window). ANY citation of artifacts dated after `window_end` = FAILURE (temporal leak).
2. **Seeded-fabrication negative control (verifier test):** `spark-verify.js` handed one spark with a doctored evidence anchor (nonexistent or non-supporting line). PASS = L1 EVIDENCE skeptic returns REFUTED with the literal-quote failure documented.

Run both controls after any material change to the scout contract, the workflows, or the verify-wave lenses.

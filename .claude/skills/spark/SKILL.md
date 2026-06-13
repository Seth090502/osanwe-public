---
name: spark
risk: safe
description: Run cross-domain pattern recognition. Use when 7-14 day cross-domain synthesis pass is due, after multi-domain session work, before a major /decide invocation to surface unnamed constraints, on continuity audit, or for theme-class single-sweep. Cross-domain pattern recognition and emergence detection with deterministic mode routing (Pattern 6), atomic-multi-file discipline matching /retro v2.1, continuity audit reading last N spark reports for Brier-style calibration, 9-class pattern taxonomy with detection rules + evidence thresholds + per-class confidence calibration, FOLLOWUPS:skills coordination block surfacing /decide + /challenge + /brief + /invest + /vault candidates with concrete one-line rationale and time-to-decision triggers, meta.json sidecar for machine-readable audit + cross-run calibration, same-day -HHMM collision handling preserving archival rule, symmetric back-linking to materially-referenced entities/theses (3-5 typical in related:), F11 Phase C atomic-commit + F14 narrow stage + F17 Co-Authored-By verify, ASCII-only new content (Pattern 22), 18-item Pre-Output HALT gate, mid-batch F.halt on partial-failure, deprecation-aware exclude-list (does not flag /research /review as negative-space). 5 modes: scan (default, wide cross-domain) / focus (narrow to one domain/tag/entity) / continuity (calibration only, no new sparks) / theme (single-class sweep) / --preview modal flag. Reads daily notes + sessions-log + decision-log + briefings + entity notes (read-only) + insight-stream + hot.md + thesis essays + prior 3 spark reports. Writes to wiki/research/sparks/spark-<date>[-HHMM].md plus sidecar; symmetric back-link pass on entities/theses; sessions-log entry; daily note ## Insights linkback; hot.md last_spark bump. Coordinates with /retro (FOLLOWUPS:skills consumed at session end) + /brief (briefing FOLLOWUPS:skills can surface /spark candidate when divergent regime detected) + /decide + /challenge + /invest + /vault (followup downstream). vNEXT 2026-06-10: dual topology (Tier-A spark-sweep + spark-verify Dynamic Workflows per ref-dw-topology.md, Tier-B sequential dispatch retained verbatim as universal fallback, OSANWE_FORCE_SEQUENTIAL=1 test knob); Phase H.5 adversarial verification wave (4 lenses evidence/falsifiability/novelty/mundane, fail-closed, cap 7); falsifiable-prediction scoring layer (vault-observable tests, Phase D resolved-true/false scoring, 2x-weighted calibration component); corpus expansion (telemetry reports + calibration-monitor rows + ratification queue/proposals aging + Part W honest-gaps register, all orchestrator-resolved and args-passed, R1 temporal fence on retrospective windows); playbooks dedup + /consolidate coordination; 21-item gate (items 1-18 preserved verbatim); SPARK_DW_TOKEN_BUDGET governance; --verify flag.
arguments: [target]
argument-hint: "scan [7d|14d|30d] | focus <domain|tag|entity> | continuity [N] | theme <class> | --preview | --verify"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, Agent]
effort: max
user-invocable: true
---

## Execution Rules

- **Subagent dispatch is MANDATORY when specified by phase** (Phase E dispatches `pattern-class-scout` -- single class for theme mode, OR 9 parallel instances for full sweep). Pre-emptive skip based on judgment ("I can detect patterns inline", "this class won't surface anything") is FORBIDDEN. The subagent decides per-class applicability via its own "No actionable patterns this class" return contract -- that is a SUCCESSFUL dispatch, not a failure. Legitimate fallback fires ONLY on (a) contract violation -- subagent return missing required calibrated % confidence or evidence anchors, OR (b) actual dispatch failure -- timeout, rate limit, tool-denial, hard subagent crash. Pre-emptive skip surfaces in Phase N final verification as **DEVIATION** (not "fallback"). Quality preserved by additive design: existing inline pattern detection rules per ref-pattern-taxonomy.md remain intact as legitimate-failure fallback.

- **Tier-A workflow dispatch satisfies the MANDATORY-dispatch rule** (vNEXT): on TOPOLOGY=dw, invoking the `spark-sweep` workflow (which dispatches the same `pattern-class-scout` instances via agentType) IS the mandatory dispatch; DEVIATION semantics apply identically in both topologies (pre-emptive skip of a class without legitimate failure = DEVIATION, surfaced in Phase N). The per-class convergence gate (contract violation/dispatch failure -> one re-dispatch -> inline Phase E.1 fallback for that class only) mirrors the Agent-tool path exactly. See `.claude/skills/spark/ref-dw-topology.md`.

## Quality Standards (preserved verbatim from v1)

- This is NOT a summary skill. Do not summarize what happened. Find what CONNECTS.
- The value is in surprising connections, not obvious ones. "NVDA and AMD are both semiconductors" is worthless. "Golf progressive overload maps to career skill-building cadence" is a spark.
- If no genuine patterns emerge, say so. "No actionable patterns in this timeframe" is a valid output. Never manufacture fake insights.
- Reference specific files and dates as evidence. Sparks without evidence are speculation.
- Check insight-stream.md first to avoid re-surfacing known patterns.
- Calibrated confidence on each spark: percentage + evidence basis (not HIGH/MEDIUM/LOW labels).

## When to use / not

Use: cross-domain synthesis pass after substantive activity (typically every 7-14 days; on demand when "what am I missing" is the question; before major /decide invocations to surface unnamed constraints).

Not for: session-end retrospective (use /retro), thesis stress-test (use /challenge), per-ticker analysis (use /invest), morning market briefing (use /brief), structured decision (use /decide), vault integrity audit (use /vault), weekly synthesis (no dedicated skill -- /spark + /retro + /brief continuity together cover this).

Output is observation, not action mandate. /spark surfaces patterns; downstream skills act on them.

## Invocation modes (Pattern 6 deterministic routing)

| Syntax | Behavior |
|---|---|
| `/spark` or `/spark scan` | Wide cross-domain scan, default 14d timeframe, top 7 sparks |
| `/spark scan 7d` / `30d` | Explicit timeframe override |
| `/spark focus <target>` | Narrow scan to one domain (`investing`/`career`/`health`/`golf`/`meta`), one tag (`thesis/orbital-compute`), or one entity stem (`NVDA`/`MU`); cap 4 sparks |
| `/spark continuity [N]` | Diagnostic only; read last N spark reports (default 3); score persistence; emit calibration trace; no new sparks |
| `/spark theme <class>` | Surface only one pattern class: `cross-domain`, `behavioral`, `thesis-evolution`, `failure-mode`, `decision-divergence`, `negative-space`, `frequency-recency`, `tool-skill`, `meta` |
| `--preview` (modal flag) | Phases A-N in memory; render to stdout; SKIP all writes; F11 never set |
| `--confirm` | Per-spark confirmation before Phase O |
| `--replace` | Same-day overwrite (destructive); default is `-HHMM` collision variant |
| `--no-peripheral` | Write spark file + sidecar only; skip Phase P peripheral updates |
| `--verify` (modal flag) | Force the Phase H.5 adversarial verification wave on ALL promoted sparks (TOPOLOGY=dw; cap 7). On TOPOLOGY=sequential forces the inline evidence spot-check on ALL promoted sparks (not just top-2) |

Default with no arguments: `scan` mode, 14-day timeframe.

## Process (14 atomic phases A-N + Phase O write + Phase P peripheral)

### Phase 0: Vault context retrieval (NEW; Phase 3.6c -- runs BEFORE Phase A; read-only; runs in --preview)

Skill-level semantic retrieval over the local HNSW vault index (covers `wiki/` + `Calendar/` + `private/`; `Atlas/` NOT indexed, so thesis essays are still read via Phase C domain-conditional reads). COMPLEMENTS Phase C's timeframe-bounded 8-file-group load by surfacing SEMANTICALLY-related prior thinking beyond the time window. Read-only: a single Bash `node` call; writes nothing; safe in `--preview` (Phase 0 runs before Phase A's F11-collision check).

0.1 -- Set the retrieval subject T: the `focus` target (concept / domain / tag / entity); for wide `scan` mode use the dominant concept(s) emerging from the initial activity sweep; for `theme <class>` use the class name + its defining terms.

0.2 -- Build 12 concept-dimension queries:
`"<T>"`, `"<T> cross-domain examples"`, `"<T> related patterns"`, `"<T> contradictions"`, `"<T> historical instances"`, `"<T> applications"`, `"<T> meta-patterns"`, `"<T> failure modes"`, `"<T> evolution"`, `"<T> alternative framings"`, `"<T> related theses"`, `"<T> known instances"`.

0.3 -- Fire `query-skill.mjs` TWICE via Bash (stdin JSON heredoc; no temp file; ~1-1.5s each):
- BROAD (cross-vault, no filter): `{"queries":[<the 12>],"top_k":100,"threshold":0.60}` piped to `node ~/.vault-substrate/query-skill.mjs`
- FOCUSED (consolidated theme/decision doctrine): `{"queries":[<the 12>],"top_k":25,"threshold":0.60,"filter_path_prefix":"wiki/playbooks/"}` piped to the same script.

Each returns a JSON array `[{path,line,score,text}]`. The script always exits 0 (emits `[]` on any error), so Phase 0 never crashes the run. (wiki/playbooks/ holds the distilled cross-domain theme + decision playbooks -- the highest-signal prior-pattern record; it is NOT among Phase C's reads, so this pass is additive. Prior spark reports are already covered by Phase C/D.)

0.4 -- Merge BROAD + FOCUSED; dedup by `path:line` (keep higher score); sort by score desc; cap to top 100. Store as VAULT_CONTEXT.

0.5 -- EMIT a visible summary (MANDATORY):

    ### Phase 0 -- retrieved vault context (N hits; M from wiki/playbooks/)
    Top results:
      [score] path:line -- first ~80 chars of text
      ... (show up to 15)

If both calls fail or return `[]`: emit `Phase 0 -- no vault context retrieved (query-skill.mjs unavailable or index empty)` and continue to Phase A. NEVER HALT on Phase 0.

Record `phase0_hits=N` (total merged VAULT_CONTEXT hits) for the meta.json sidecar; when N=0, Phase M appends a non-halting `retrieval_degraded (phase0_hits=0)` line to the report footer (the /invest parity pattern). No SUPPRESS change -- /spark stays hook-unsuppressed (3.6c 0/5-disjoint finding).

0.6 -- Downstream consumers (these phases stay UNCHANGED; consult VAULT_CONTEXT instead of re-deriving):
- Phase E (Pattern detection): seed the 9-class detection with semantically-related prior patterns + cross-domain instances surfaced in VAULT_CONTEXT (benefits MOST -- pattern detection is retrieval-shaped).
- Phase C (Context load): add any surfaced playbooks / entities / decision-log entries beyond the timeframe window to the read set.
- Phase D (Continuity audit): cross-check surfaced prior patterns against the last-3-sparks audit.

Cite any used chunk inline as `(vault: path:line)` -- plain text, NO wikilink syntax.

### Phase A -- Pre-flight

1. Parse arguments (mode + flags + target/timeframe/N/class).
2. Resolve today's ISO date.
3. Resolve `OUTPUT_PATH`:
   - `scan`/`continuity`: `wiki/research/sparks/spark-<date>.md`
   - `focus`: `wiki/research/sparks/spark-<focus-stem>-<date>.md`
   - `theme`: `wiki/research/sparks/spark-theme-<class>-<date>.md`
4. Same-day collision check: if `OUTPUT_PATH` exists, default to `-HHMM` variant (preserves archival rule); `--replace` reserved for explicit overwrite.
5. F11 collision check (`.claude/state/auto-commit-disabled` already present from a prior in-flight skill -> HALT).
6. Topology detection (deterministic; NEVER halts). TOPOLOGY = `dw` iff the Workflow tool is present in the orchestrator's current session tool surface; else `sequential` (Codex engine, headless, restricted sessions, any DW regression). Ambiguity -> `sequential` (safe fallback). `tools/lib/capability-detect.sh` (`OSANWE_DW_HINT`) is ADVISORY only -- the tool-surface check is authoritative. Forced-sequential knob (R2): `OSANWE_FORCE_SEQUENTIAL=1` (env, or explicit operator instruction) forces TOPOLOGY=sequential for test/regression runs; there is deliberately NO force-dw counterpart (dw without the Workflow tool breaks; forcing the fallback is always safe). Record ORCHESTRATOR_MODEL = the active model string. PASSIVE LOGGING ONLY: no behavior ever branches on model identity; TOPOLOGY + ORCHESTRATOR_MODEL flow to the Phase B print and the meta.json sidecar (additive fields). Full Tier-A spec: `.claude/skills/spark/ref-dw-topology.md`.

### Phase B -- State-transition print (BEFORE F11)

Emit to stdout the planned reads + planned writes + collision-handled output path. User can abort here pre-flag. Format:

    /spark <mode> -- planned state transition:
      reads (8 file groups): daily notes (timeframe), sessions-log, decision-log, hot.md,
        insight-stream, briefings <timeframe>, entity notes <timeframe>, prior 3 sparks
      writes:
        - <OUTPUT_PATH> (NEW)
        - <OUTPUT_PATH-meta.json> (NEW sidecar)
        - Calendar/decisions/sessions-log.md (append)
        - Calendar/daily/<today>.md (## Insights linkback append)
        - wiki/hot.md (last_spark frontmatter bump)
        - <N> entity/thesis files (symmetric back-link reciprocation, sha256-preserved)
      Topology: <dw (Workflow tool detected; spark-sweep fan-out per ref-dw-topology.md)
                | sequential (Tier-B; universal fallback | OSANWE_FORCE_SEQUENTIAL)>
      Orchestrator model: <ORCHESTRATOR_MODEL from Phase A item 6; logged passively, never branched on>
      Verify wave (H.5): <expected SKIP (no qualifying sparks likely) | expected FIRE (--verify | meta-class | /decide-rec | confidence >= 70)>
      F11 set after this print

### Phase C -- F11 set + parallel context load

1. `touch .claude/state/auto-commit-disabled` BEFORE any Write.
2. Parallel Read 8 file groups (Pattern 1):
   - Daily notes within timeframe (`Calendar/daily/YYYY-MM-DD.md` for each date in range)
   - `Calendar/decisions/sessions-log.md` (entries within timeframe)
   - `Calendar/decisions/decision-log.md` (entries within timeframe)
   - `wiki/hot.md` (current state cache)
   - `wiki/insight-stream.md` (known-named patterns; exclude-list for novelty filter)
   - `Calendar/decisions/briefings/briefing-*.md` modified within timeframe
   - `wiki/entities/tickers/*.md` and `wiki/entities/companies/*.md` modified within timeframe
   - `wiki/research/sparks/spark-*.md` last 3 (continuity audit input)
3. Domain-conditional reads (when `focus` mode or relevant patterns detected in initial scan):
   - Investing: `Atlas/concepts/investing/{watchlist,investing-research-log,theses/thesis-*}.md`
   - Career: `Efforts/career-search/{tracker,opportunities}.md`
   - Health: `Efforts/health-protocol/{current-stack,bloodwork,peptide-protocol}.md` + `private/health-baseline.md` (path-guard READ allowed)
   - Golf: `Efforts/golf-practice/{swing-notes,progress-log}.md`
   - Meta: `.claude/skills/_archive/` (deprecation-aware exclude-list construction)
4. Corpus-extract resolution (vNEXT S4; orchestrator-resolved MAIN-LOOP, never by scouts): resolve the latest `wiki/maintenance/telemetry-*.md` path (+ an in-session claudewatch summary when its MCP tools are reachable; headless = degrade to the report file), the `wiki/investing/calibration-monitor.md` Call Log rows, the latest overnight ratification queue (`wiki/research/overnight-summary-*.md` RATIFICATION QUEUE section) + `wiki/maintenance/proposals/` inventory, and the Part W honest-gaps TEXT (extracted via the live Part index offsets from the SessionStart injection; sensitive parts never extracted). Pass via `spark-sweep` workflow args (Tier-A) or inline prompt context (Tier-B) per the per-class wiring table in `.claude/skills/spark/ref-dw-topology.md` sec 8. Scouts NEVER read the master-context doc directly. R1 TEMPORAL FENCE: on retrospective runs (window_end < today) every extract is filtered to artifacts dated <= window_end and marked `as_of`; spark-sweep.js drops unmarked retrospective extracts fail-closed.

### Phase D -- Continuity audit

For each of the last 3 spark reports (or N if `continuity` mode), score each prior spark's status against current vault state:

- **PERSISTED**: pattern still observable in current activity; evidence still present
- **EVOLVED**: pattern shifted shape but core insight still relevant (note the shift)
- **INVALIDATED**: explicit counter-evidence; pattern was wrong or superseded
- **DORMANT**: insufficient signal in current timeframe (neither confirmed nor denied)

Compute `prior_calibration_score` (0.0-1.0) = (PERSISTED + 0.5*EVOLVED) / total_prior_sparks. Carry forward into meta.json. Used for confidence calibration in Phase H.

Prediction scoring (vNEXT S3; additive): prior sparks WITH a `predictions[]` entry in their meta.json sidecar are additionally scored `resolved-true / resolved-false / unresolved` at horizon via deterministic vault checks (path/glob existence, count delta, calibration-monitor row condition, dated artifact) -- prediction-less prior sparks keep the four-status scoring above unchanged. When >= 1 prediction has RESOLVED: `prior_calibration_score = (2*pred_component + vibes_component) / 3`, where `pred_component = resolved_true / (resolved_true + resolved_false)` (unresolved excluded) and `vibes_component` is the legacy formula above; with zero resolved predictions the legacy formula stands unchanged. Record the trace in meta.json `prediction_scoring`. Methodology doc ref-continuity-scoring.md stays DEFERRED (Pattern 21) -- this paragraph is the mechanism.

If `continuity` mode: STOP after this phase; emit calibration report to stdout; SKIP to Phase O sidecar-only write.

### Phase E -- Pattern detection (per ref-pattern-taxonomy.md)

#### Phase E.0 -- DELEGATED dispatch to `pattern-class-scout` (PREFERRED path; Phase C wiring 2026-05-02)

**Topology routing (vNEXT):** on TOPOLOGY=dw (Phase A item 6), read `.claude/skills/spark/ref-dw-topology.md` (read-on-demand companion) and invoke the `spark-sweep` workflow (`.claude/workflows/spark-sweep.js`) with args `{classes (1 for theme / 9 for scan), window_days, window_end, run_timestamp, mode, session_id, vault_context_summary, corpus_extracts (Phase C item 4), prior_sparks_summary, token_budget (SPARK_DW_TOKEN_BUDGET)}`. It dispatches the SAME `pattern-class-scout` instances via agentType (scout .md contract + opus/xhigh definition UNCHANGED; the workflow's JSON schema wraps the markdown contract 1:1) in chunked waves <= 6, applies the per-class convergence gate (`no_patterns: true` = SUCCESS; contract violation/dispatch failure -> one re-dispatch -> `_fallback` marker -> inline Phase E.1 for that class only), and returns the scout bundle. The dispatch text below is the TOPOLOGY=sequential (Tier-B) path, retained VERBATIM as the universal fallback -- and it remains the authoritative spec of what each scout return must contain in BOTH topologies.

**MANDATORY** (per Execution Rules): dispatch first, no pre-emptive skip. The model dispatches:
- **Theme mode** (`/spark theme <class>`): 1 pattern-class-scout instance for the requested class
- **Full sweep mode** (`/spark` no args): 9 pattern-class-scout instances in parallel (one per class: cross-domain, behavioral, thesis-evolution, failure-mode, decision-divergence, negative-space, frequency-recency, tool-skill, meta) within a single assistant turn

Per dispatch, use the Agent tool with subagent_type `pattern-class-scout`. Pass input: `{class: "<one of 9 classes>", time_window: "<from Phase A, default 14d>", session_id: "<current-session-id>"}`. Expected return per class: continuity audit (vs prior 3 spark reports) + 0-5 ranked sparks with calibrated % confidence + evidence anchors (file + date + line) + downstream skill recommendation.

Validate per-class return: calibrated % confidence (NOT HIGH/MED/LOW per spark convention), specific file+date+line evidence on every spark, "No actionable patterns this class" is a valid output -- treat as SUCCESS, not failure.

On contract violation OR dispatch failure for any class: fall through to inline pattern detection logic per ref-pattern-taxonomy.md for that class only. Other classes' subagent returns still consumed.

On dispatch success: merge N class returns into composite spark report at Phase M. Continuity audits aggregated across classes.

#### Phase E.1 -- Inline pattern detection (FALLBACK; per-class, runs ONLY if Phase E.0 dispatch failed for that class)


Run detection for 9 pattern classes (or 1 class if `theme` mode):

1. **Cross-domain emergence** -- entity/concept appears in 2+ distinct domains within timeframe
2. **Behavioral pattern** -- 3+ instances of same behavior shape across distinct dates
3. **Thesis evolution** -- 2+ thesis-essay edits OR 2+ thesis-status mentions in briefings showing frame-shift
4. **Recurring failure mode** -- 2+ instances within 30d of same failure shape with identifiable upstream trigger
5. **Decision-pattern divergence** -- decisions in domain A diverge in style from decisions in domain B (3+ per domain)
6. **Negative space** -- topic/ticker/concept appeared 3+ times prior-to-window then ZERO in current timeframe AND no explicit dropped-decision; APPLY DEPRECATION-AWARE EXCLUDE-LIST
7. **Frequency x recency inversion** -- frequent-but-staling OR rare-but-accelerating
8. **Tool/skill usage pattern** -- skill cluster co-occurrence OR skill gap (predictable trigger no skill invocation)
9. **Meta-pattern** -- 3+ of patterns 1-8 cluster around single super-axis (career, action-execution, risk-aversion, etc.)

Detection rules per class with REQUIRED markers + evidence thresholds + confidence calibration: see `ref-pattern-taxonomy.md`.

### Phase F -- Substantive-threshold filter (Pattern 19)

Drop patterns failing minimum-evidence:
- Behavioral/failure-mode/recurring patterns: require >=3 instances
- Cross-domain: require 2+ distinct domains AND not already named in insight-stream
- Thesis-evolution: require 2+ supporting documents
- Negative space: require >=3 prior-window mentions AND ZERO in current timeframe AND not in deprecation-aware exclude-list
- Meta-pattern: require 3+ promoted patterns from classes 1-8

Playbooks dedup (vNEXT S5; additive): the novelty check (cross-domain "not already named" and all-class continuity matching) extends to `wiki/playbooks/` in addition to `wiki/insight-stream.md` -- a pattern already distilled into a playbook is not a new spark (score it in the continuity audit instead).

Log dropped patterns in `patterns_below_threshold` field of meta.json (transparent suppression rather than silent omission).

### Phase G -- Promotion cap (top N by composite weight)

Composite weight = `evidence_count * 0.4 + cross_domain_count * 0.3 + novelty_score * 0.3`
- `novelty_score` = 1.0 if NEW (not in continuity audit); 0.7 if EVOLVED; 0.5 if PERSISTED; 0.0 if INVALIDATED (suppress)
- `cross_domain_count` = distinct domain count for this pattern

Cap at 7 sparks for `scan`; 4 for `focus`; no cap for `theme`. Remaining promoted-but-capped patterns logged in `patterns_below_threshold` with reason "above threshold but below promotion cap".

### Phase H -- Per-spark confidence calibration

For each promoted spark, compute confidence per class (base from `ref-pattern-taxonomy.md`) with adjustments:
- +5% if pattern PERSISTED in continuity audit (track record confirmed)
- -10% if any underlying claim is Grade-D (speculation)
- -15% if `>30%` of citations are Grade-C or below
- Cap at class-specific maximum (most classes capped 80-85%; behavioral capped 90%; meta capped 80%)

Confidence written as integer 0-100 with one-line rationale.

### Phase H.5 -- Adversarial verification wave (vNEXT; conditional)

Fires PER-SPARK on the Phase H-calibrated promoted set when ANY of: confidence >= 70; class == `meta`; the SCOUT-RETURN `downstream_rec` field == `/decide` (known from Phase E -- NEVER gate on Phase J output; phase-ordering invariant); `--verify` flag (qualifies ALL promoted sparks). Zero qualifying sparks -> wave SKIPPED entirely (the cost lever). Cap 7 verifiers per run; fan-out <= 6.

- **TOPOLOGY=dw:** invoke the `spark-verify` workflow (`.claude/workflows/spark-verify.js`) with the qualifying sparks (id, title, class, confidence, evidence anchors, pattern, continuity, prediction, downstream_rec). ONE read-only verifier per spark applies FOUR LENSES SEQUENTIALLY, fail-closed, default-to-refuted: (1) EVIDENCE skeptic -- every cited file:date:line must EXIST and SUPPORT the claim, literal source line quoted back; fabricated/misread anchor -> REFUTED; (2) FALSIFIABILITY skeptic -- pattern must be testable; metaphorical hand-waving -> REFUTED; (3) NOVELTY skeptic -- check insight-stream + wiki/playbooks/ + prior sparks; already-named -> DEMOTED to PERSISTED-continuity (Continuity Audit row, not a numbered new spark); (4) MUNDANE-ALTERNATIVE skeptic -- calendar artifact / single-cause cascade / vault-mechanics artifact; sustained alternative -> confidence haircut (arithmetic shown) or REFUTED. Missing/invalid verifier return = REFUTED (fail-closed).
- **TOPOLOGY=sequential:** an inline evidence spot-check on the top-2 promoted sparks replaces the wave (open every cited anchor; same refute semantics). `--verify` forces the inline spot-check on ALL promoted sparks.
- **Outcomes:** any refuted lens -> the spark drops to `patterns_below_threshold` with the refutation reason (transparent suppression, never silent); DEMOTED -> Continuity Audit table as PERSISTED with the prior_match named; survivors proceed with `recalibrated_confidence`. Phases I and J compute over SURVIVORS only. Record the tally `{fired, refuted, demoted, survived}` in meta.json `verify_wave` + the report footer (gate item 19). Full lens contracts: `.claude/skills/spark/ref-dw-topology.md` sec 5.

### Phase I -- Meta-observation composition

One paragraph (3-5 sentences): what THE story is across the promoted patterns. What super-axis do they cluster on? What does the vault's recent activity reveal about underlying state? Distinct from any single spark; not a pattern itself.

### Phase J -- FOLLOWUPS:skills block emission

For each promoted spark, generate 0-2 concrete downstream candidates. Block bounded to <=5 entries total per report. Format:

    <!-- FOLLOWUPS:skills -->
    - /decide <decision-name> -- <one-line rationale tied to spark N> (trigger: <time>)
    - /challenge thesis-<slug> -- <rationale> (trigger: <time>)
    - /brief <surface item> -- <rationale> (trigger: NEXT MARKET OPEN)
    - /invest <TICKER> -- <rationale> (trigger: <time>)
    - /vault <maintenance item> -- <rationale> (trigger: EOW)
    - /consolidate <topic> -- spark N PERSISTED across >= 2 consecutive audits; playbook-promotion candidate (trigger: EOW)
    <!-- /FOLLOWUPS:skills -->

Each entry MUST: (a) reference a specific spark number in body, (b) name a concrete target (not vague "investigate X"), (c) include time-to-decision marker (NOW / NEXT MARKET OPEN / EOW / EOM / DEFERRED). Empty case rendered explicitly as `(no followup skills recommended)`.

/consolidate candidate rule (vNEXT S5): any spark PERSISTED across >= 2 consecutive continuity audits is a playbook-promotion candidate -- emit a /consolidate row with a one-line rationale (counts within the <=5 cap).

### Phase K -- Pre-Output HALT gate (21-item invariant check; items 1-18 preserved verbatim from v2)

Before any Write, verify all 21:

1. F11 set (`.claude/state/auto-commit-disabled` exists)
2. Date resolved correctly; `OUTPUT_PATH` not colliding (or `-HHMM` variant resolved)
3. Frontmatter complete and schema-compliant (categories=[wiki], type=spark, all required fields)
4. >=1 promoted spark is cross-domain OR non-obvious (not "NVDA and AMD are semiconductors")
5. All sparks reference >=1 specific file or date as evidence
6. Confidence on every spark expressed as integer 0-100 with rationale (not HIGH/MEDIUM/LOW)
7. Continuity audit table populated (or explicit `(no prior sparks within audit window)`)
8. FOLLOWUPS:skills block syntactically valid (parseable comment-fenced); empty case rendered explicitly
9. FOLLOWUPS:skills entries each tied to specific spark number AND have time-to-decision marker
10. Meta-observation present (non-empty, distinct from any single spark, 3-5 sentences)
11. `patterns_below_threshold` log populated when applicable (transparent suppression)
12. ASCII-only on body + sidecar (Pattern 22; HALT on any byte >127 in NEW content)
13. `related:` field has 3-5 wikilinks (entities + theses + peer sparks if EVOLVED)
14. Symmetric back-link plan: every wikilink in `related:` has reciprocal back-reference plan
15. Path-guard mechanical: no proposed Write targets `.raw/`, `private/`, `finance/`, `credentials/`
16. Sessions-log entry composed per canonical schema
17. hot.md `last_spark` field present in frontmatter (add if missing during this run)
18. F17 Co-Authored-By absent in planned commit message body
19. Verify-wave outcome recorded: `{fired, refuted, demoted, survived}` tally in meta.json `verify_wave` + report footer, OR explicit `(verify wave skipped: no qualifying sparks)` / `(Tier-B inline spot-check: <N> anchors opened, <M> refuted)` line
20. Predictions well-formed: every Prediction field carries a vault-observable mechanically-scorable test + ISO horizon date + direction; external-world tests name a vault proxy (absent Prediction fields are valid -- predictions are optional)
21. Topology + orchestrator_model logged in meta.json sidecar (passive fields; never branched on)

ANY failure -> HALT with diagnostic; F11 stays on; user decides retry vs abort.

### Phase L -- ASCII pre-write scan (Pattern 22)

Byte-scan all NEW content (spark report body, meta.json, sessions-log entry text, daily-note linkback, hot.md frontmatter line). HALT on any byte >127. Replace any em-dash, smart quotes, ellipsis with ASCII equivalents (`-`, `"`, `...`).

### Phase M -- Compose spark report + meta.json sidecar

Per `ref-output-template.md` schema:
- Frontmatter (canonical fields)
- H1 title + Generated stamp + flags
- TLDR (one paragraph, BLUF analog)
- Continuity Audit table (when prior sparks exist)
- Sparks (numbered subsections; Class / Domains / Evidence / Insight / Confidence / Continuity)
- Below-Threshold Observations (when applicable)
- Meta-Observation (one paragraph)
- FOLLOWUPS:skills block (HTML-fenced)
- Footer (calibration line)

meta.json schema per ref-output-template.md (machine-readable; includes phases timing, gate results, calibration trace, below-threshold log).

### Phase N -- Final verification

Read composed body + sidecar back from memory; re-run gate items 4, 9, 12; confirm internal references (FOLLOWUPS:skills tied to spark N, continuity table tied to prior spark dates); confirm no orphan wikilinks (every wikilink in body resolves to existing file OR is a peer-spark wikilink for EVOLVED status).

### Phase O -- Atomic write

1. Write `OUTPUT_PATH` (spark report).
2. Write `OUTPUT_PATH-meta.json` (sidecar).
3. F14 narrow stage: `git add` exactly these 2 files.
4. Mid-batch F.halt: if either Write fails, HALT IMMEDIATELY; F11 stays on; structured report (succeeded / failed / not-attempted); no partial commit.

### Phase P -- Peripheral updates (skip if `--no-peripheral`)

Atomic with Phase O (single coherent commit covers all):

1. **Sessions-log entry** -- append structured entry per canonical schema:

       ### YYYY-MM-DD -- /spark <mode> -- <N> patterns surfaced
       - **Domain:** meta/cross-domain
       - **Focus:** <focus_target | "wide scan">
       - **Patterns surfaced:** <N>; classes: <class-list>
       - **Continuity score:** <prior_calibration_score>
       - **Followup skills:** <count> (<comma-list>)
       - **Artifacts:** [[spark-<date>[-HHMM]]]
       - **Related:** [[hot]] | [[insight-stream]]

2. **Daily note `## Insights` linkback** -- append:

       - [HH:MM] /spark <mode> -- <N> patterns; meta: <one-line>; full: [[spark-<date>[-HHMM]]]

3. **hot.md frontmatter bump** -- update `last_spark: <today>` (add field if absent; update if present).

4. **Symmetric back-link reciprocation** (Pattern 8) -- for each wikilink in spark `related:` field, add reciprocal `[[spark-<date>[-HHMM]]]` reference on target file's Recent or Related section. Body-preservation sha256 invariant: content outside intended insertion sites byte-exact post-write.

5. F14 narrow-stage all touched files; atomic commit with prefix `spark: <mode> -- <N> patterns + continuity-<N>`.

6. F17 verify: post-commit `git log -1 --format=%B | grep -c Co-Authored-By` MUST be 0.

7. F11 clear: `rm .claude/state/auto-commit-disabled`.

## Pattern detection taxonomy (reference)

9 pattern classes with REQUIRED markers + IDENTIFYING evidence + per-class confidence calibration in `ref-pattern-taxonomy.md` (companion ref doc; ~200 lines). SKILL.md Phase E lists class names; ref doc holds detection rules + thresholds + cross-cutting rules (deprecation-aware exclude-list, Pattern 19 substantive-mention threshold integration, continuity audit confidence shifts).

## Output schema (reference)

Canonical frontmatter + body section order + meta.json schema in `ref-output-template.md` (companion ref doc; ~120 lines). Sessions-log entry schema, daily-note linkback format, hot.md frontmatter bump pattern all specified there.

## Tier-A dynamic-workflows topology (reference)

Topology detection, two-invocation architecture (`spark-sweep` + `spark-verify`), scout JSON wrapper schema, verify-wave lens contracts + qualifying criteria, corpus-extract resolver contract (incl. the R1 temporal fence), resume protocol (W7), prediction-scoring mechanics, and token governance in `.claude/skills/spark/ref-dw-topology.md` (companion ref; read-on-demand at Phase A item 6 / Phase E.0 / Phase H.5). Budget: `SPARK_DW_TOKEN_BUDGET` env var, default 600K full sweep / 250K theme (LOW-confidence placeholders; instrument and recalibrate after 2 production runs); the main loop reads the env var and passes `args.token_budget` (workflow sandbox has no process.env). Tier-B sequential text in this file remains the authoritative spec in both topologies.

## Continuity scoring methodology (DEFERRED to ref-continuity-scoring.md)

Inline procedural depth in Phase D + Phase H above is sufficient for v2.0 first invocation. Pattern 21 candidate Deep Research onboard for `ref-continuity-scoring.md` deferred per Standing Rule 16 (institutional-grade Brier-scoring methodology with cross-spark fuzzy-matching mechanics, marker-signature stability rules, calibration-decay weighting). Surfaces in FOLLOWUPS:skills.

## Coordination with other skills

- **/retro** -- session-end retro consumes /spark FOLLOWUPS:skills entries for the rolling session-log; /spark sessions-log entry parsed by /retro for sessions-log continuity
- **/brief** -- briefing FOLLOWUPS:skills can surface `/spark` candidate when divergent regime detected (multi-day pattern not captured in any single briefing); /spark reads briefings within timeframe
- **/decide** -- /spark FOLLOWUPS surface /decide candidates with concrete decision names + time-to-decision triggers
- **/challenge** -- /spark FOLLOWUPS surface /challenge candidates when thesis-evolution or recurring-failure-mode patterns surface
- **/invest** -- /spark FOLLOWUPS surface /invest candidates when entity-level pattern surfaces (frequency-recency inversion on a ticker; cross-domain emergence including a ticker)
- **/vault** -- /spark FOLLOWUPS surface /vault candidates when meta-pattern reveals vault-state issue (skill-gap, ref-doc-stale-cluster)
- **/consolidate** -- /spark FOLLOWUPS surface /consolidate candidates when a spark is PERSISTED across >= 2 consecutive continuity audits (playbook-promotion); Phase F novelty filter dedups against the playbooks /consolidate maintains (wiki/playbooks/)
- **/ingest** -- distinct skill (transformational entity-graph extraction); /spark is preservational pattern recognition
- **/enrich** -- distinct skill (preservational doc onboarding); /spark output may itself be onboarded later if it crystallizes into a durable insight worthy of canonical ref placement
- **/insight-stream** (file, not skill) -- /spark NEVER writes to `wiki/insight-stream.md`; that file is human-curated; /spark output references via `related:` only

## Path-guards (mechanical)

NEVER write to: `.raw/`, `private/`, `finance/`, `credentials/`. Reads from `private/health-baseline.md` ARE allowed (health-domain pattern detection). Atlas writes never (human-write-only). All writes route through Phase O + Phase P canonical paths in `wiki/research/sparks/`, `Calendar/decisions/sessions-log.md`, `Calendar/daily/`, `wiki/hot.md`, plus symmetric back-link targets in `wiki/entities/`.

## Tag vocabulary guardrail

Forbidden tag namespaces: `domain/*`, `type/*`. Use canonical: `topic/cross-domain`, `topic/<specific-pattern-class>` (e.g., `topic/behavioral`), `ticker/<TICKER>` UPPER, `thesis/<slug>` lowercase-kebab. Frontmatter MUST have `categories: [wiki]` (plural list) and `type: spark`.

## Failure taxonomy

| Failure mode | Phase | Symptom | Recovery |
|---|---|---|---|
| F11 collision | A | another in-flight skill | Wait OR `rm .claude/state/auto-commit-disabled` if confirmed orphan |
| Same-day collision | A | OUTPUT_PATH exists | Default `-HHMM` variant; user can `--replace` for explicit overwrite |
| Insufficient context | C | <timeframe of activity nearly empty | HALT with "no actionable patterns; <X> files in timeframe" -- valid output per Quality Standards |
| Pre-Output gate failure | K | any of 18 invariants violated | HALT with item-specific diagnostic; F11 stays on; fix and retry |
| ASCII byte >127 | L | non-ASCII in NEW content | Replace and retry; do NOT proceed with non-ASCII |
| Mid-batch Write failure | O | first Write succeeded, second failed | F.halt IMMEDIATELY; structured report; user `git checkout -- <orphan>` or fix-and-retry with idempotency dedup |
| Symmetric back-link sha256 violation | P | content outside intended insertion site changed | F.halt; back out the Edit; fix sha256-preserving Edit; retry |
| F17 verify fail | P (post-commit) | Co-Authored-By present in commit body | `git commit --amend` to remove trailer; verify |
| Workflow dispatch failure (Tier-A) | E.0 | spark-sweep invocation fails or a class returns `_fallback` after re-dispatch | Inline Phase E.1 for marker classes only; full workflow failure -> TOPOLOGY=sequential Tier-B path verbatim |
| Verifier contract failure | H.5 | verifier returns invalid/missing contract | Fail-closed: spark treated as REFUTED -> patterns_below_threshold with reason; never silently passes |

## Examples

### Example 1: default scan

`/spark` -> reads 14d of vault activity (typically 47-60 files); detects across all 9 classes; promotes top 7; writes `wiki/research/sparks/spark-2026-04-26.md` + sidecar; updates sessions-log + daily note + hot.md `last_spark`; symmetric back-links 3-5 entities.

### Example 2: focus on a thesis

`/spark focus thesis/orbital-compute` -> narrowed reads (only files tagged `thesis/orbital-compute` or referencing held tickers in that thesis); detects across all 9 classes filtered to thesis scope; cap 4 sparks; writes `wiki/research/sparks/spark-thesis-orbital-compute-2026-04-26.md`. Useful before /challenge thesis-orbital-compute.

### Example 3: continuity calibration

`/spark continuity 5` -> reads last 5 spark reports; scores each prior spark PERSISTED/EVOLVED/INVALIDATED/DORMANT against current vault state; emits calibration trace to stdout; writes only sidecar `wiki/research/sparks/spark-continuity-2026-04-26.json`. Diagnostic; no new spark report.

### Example 4: theme sweep

`/spark theme failure-mode` -> detects ONLY recurring-failure-mode class across 14d; no cap; writes `wiki/research/sparks/spark-theme-failure-mode-2026-04-26.md`. Useful before behavior-change /decide invocations.

### Example 5: preview

`/spark scan 30d --preview` -> Phases A-N in memory; renders planned spark report + sidecar + peripheral updates to stdout; SKIPS Phase O-P; F11 never set. Useful for sanity-check before committing to a write.

## Related skills

- `/retro` -- session-end retrospective; consumes /spark FOLLOWUPS:skills entries
- `/brief` -- morning briefing; surfaces /spark candidate when divergent regime detected
- `/decide` -- structured decision; consumes /spark FOLLOWUPS /decide candidates
- `/challenge` -- thesis stress-test; consumes /spark FOLLOWUPS /challenge candidates
- `/invest` -- per-ticker analysis; consumes /spark FOLLOWUPS /invest candidates
- `/vault` -- vault maintenance; consumes /spark FOLLOWUPS /vault candidates
- `/ingest`, `/enrich` -- distinct (transformational/preservational doc-flow); not pattern-recognition


## Phase O.0 -- Pre-commit /vault audit gate (v2.0; CAT-3 prevention-architecture parity)

After composing all target file modifications IN MEMORY but BEFORE atomic write:
1. Write each composed file (spark report + meta.json + sessions-log entry + daily ## Insights linkback + hot.md frontmatter bump + symmetric back-links to entities/theses) to a tmp dir under `wiki/research/test-tmp/.precheck/spark-<date>/`
2. Run `python tools/skill-precheck.py <tmp-files...> --skill /spark`
3. Parse exit code: 0 -> proceed; 2 -> HALT with diagnostic
4. Body-scope wikilink validation: per /retro v2.2 Phase D pattern, scan composed spark report body (Pattern detection sections + cross-references) for unresolved `[[<target>]]` and mechanically de-link unresolved targets (4-class handling: vault-resolved keep / MEMORY_PREFIXES rewrite / placeholder leave / else strip). Fence-aware.
5. Bypass: `CLAUDE_VAULT_BYPASS_VALIDATOR=1` (logged to `.claude/state/bypasses-<date>.log`)

**/spark-specific risk:** /spark links broadly to entities/theses + insight-stream (3-5 typical in `related:` field per Phase E metadata). Without Phase O.0, broken wikilinks introduced via cross-domain pattern recognition could propagate. Phase K mechanical gate covers ASCII + path + sessions-log invariants but does NOT invoke skill-precheck.py. This Phase O.0 closes the upstream defense-in-depth gap (Reviewer D classified /spark as ADEQUATELY-PROTECTED-BY-POSTTOOLUSE; SOTA pass elevates to full Phase O.0 parity with the other 7 HIGH-risk skills).

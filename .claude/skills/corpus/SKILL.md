---
name: corpus
risk: critical
description: "Use when processing a multi-document corpus (FOIA archives, declassified records, legal discovery sets, regulatory filings, court records, congressional disclosures, research dossiers; 10-150 docs typical) requiring verifiable multi-pass synthesis with citation provenance. End-to-end pipeline for analyzing large document corpora with verifiable multi-pass synthesis. Wave-based parallel extraction with hard audit gates between waves; multi-pass analytical synthesis (C1 cross-examination, C2 entity network, C3 institutional chain, C4 negative space, C5 adversarial review, C6 master synthesis, C7 citation audit); resumable across sessions via orchestrator-state files. Citation discipline mandatory ([DOCID:PAGE] for every claim, evidential class tagging [OBS]/[REP]/[HEAR]/[ANL]/[SPC]/[RED], anti-hallucination + anti-context-contamination rules). Sub-agent model floor: Sonnet 4.6+ pinned via .claude/agents/corpus-extractor.md to defend against silent-downgrade bugs. Workspace configured per-corpus via .corpus.json (name + source + workspace + pipeline version + expected doc count). Subcommands: init / status / mvp / extract / analyze <pass> / analyze-all / synthesize-master / audit-citations / adversarial / audit-dispatch / index / clusters. Triggers on /corpus invocation; mass-document analysis requests; FOIA / declassified / legal-discovery / regulatory-docket / court-filings / congressional-records / intelligence-release processing; any user request to systematically analyze 10-plus documents with provenance + verifiability. Designed for corpora of 10-150 documents (single-pass synthesis fits in one context); larger corpora require the optional cluster layer (Stage 2). Originally built for the 93-doc UAP corpus (2026-05); generalized 2026-05-21."
arguments: [subcommand]
argument-hint: "init | status | mvp | extract | analyze <pass> | analyze-all | synthesize-master | audit-citations | adversarial | audit-dispatch | index | clusters"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, Agent]
effort: max
user-invocable: true
---

# /corpus -- mass-document analysis pipeline (v5, wave-based + multi-pass)

End-to-end pipeline for analyzing large document corpora with verifiable multi-pass synthesis. Wave-based parallel extraction, multi-pass analytical synthesis (cross-examination + entity network + institutional chain + negative space + adversarial review + master synthesis + citation audit), resumable across sessions, citation-disciplined. Designed for 10-150 documents; cluster layer available for larger corpora.

## When to invoke

User wants to systematically analyze a corpus of documents (PDFs typically; other text-readable formats supported) with provenance and verifiability. Triggered by `/corpus`, mentions of mass-document analysis, FOIA processing, declassified archives, legal discovery sets, regulatory dockets, court filings, congressional records, intelligence community releases, large research corpora.

Corpus size sweet spot: **10-150 documents**. Below 10, read them directly. Above 150, the single-pass synthesis no longer fits in one context -- invoke the optional cluster layer (Stage 2) first.

## Workspace configuration

Each corpus has its own workspace. The skill resolves workspace context (in order of precedence):
1. `--workspace <path>` flag
2. `CORPUS_WORKSPACE` env var
3. Current working directory if it contains `.corpus.json`

The workspace's `.corpus.json` is written by `/corpus init` and contains:

```json
{
  "name": "<corpus-slug>",
  "source": "<absolute-path-to-source-dir>",
  "workspace": "<absolute-path-to-workspace>",
  "created": "<iso8601-date>",
  "pipeline_version": "v5",
  "extractor_agent": "corpus-extractor",
  "model_floor": "sonnet-4-6",
  "doc_count_expected": <integer>
}
```

`source` is read-only (skill never writes into the source directory). All outputs go to `workspace/`.

## Architecture summary (v5)

This skill executes a verifiable, wave-based, multi-pass cross-examination architecture:

1. **Phase A** -- pre-flight (workspace config read, deterministic doc_id assignment, wave splitting, token budget estimate).
2. **Phase B** -- wave-based extraction. Each wave dispatches K parallel sub-agents; after each wave a HARD audit gate runs `scripts/audit_run.py --wave N` and refuses to proceed unless PASS. Resumable across sessions.
3. **Phase C** -- multi-pass analytical synthesis (each pass best run in its own session):
   - **C1** cross-examination (contradictions, corroborations, patterns across the corpus)
   - **C2** entity network (persons / organizations / locations / systems + cross-network)
   - **C3** institutional chain (routing, distribution, program transitions, broken chains)
   - **C4** negative space (missing attachments, missing follow-ups, targets to seek)
   - **C5** analytical adversarial -- hostile review of C1-C4 (fresh session recommended)
   - **C6** master synthesis -- incorporates C1-C5 with provenance trail
   - **C7** citation audit -- every [DOCID:PAGE] verified against extractions
4. **Phase D** -- master adversarial review (fresh session, optional but recommended).

The single-pass C6-only flow remains available as `/corpus synthesize-master --no-analytical` if a user wants a summary with weaker analytical underpinning, but the full v5 multi-pass is the default.

## Hard invariants -- do not violate

1. **Source is read-only.** The configured SOURCE dir is canonical input. Never write into it. All outputs go to WORKSPACE.

2. **Master epistemic prompt is mandatory.** Every LLM stage prepends `<workspace>/ref/00-master-system-prompt.md` verbatim. Do not paraphrase. It enforces citation discipline, evidential class tagging, anti-hallucination rules.

3. **Hard-identifier rule for connections.** Cross-document connections require a shared concrete identifier: named person, named organization, named location, named system, exact date (+/-48h tolerance), or specific verifiable entity. Thematic similarity is not a connection. If no qualifying connections exist, say so explicitly.

4. **Cite every claim.** Format `[DOCID:PAGE]`. Prefix `[INFERENCE]` for analyst inference. Refuse to assert without citation.

5. **Wave-based parallelism with cap.** Default `--waves 4 --parallel-per-wave 5`. Max parallel-per-wave = 10; rate limits and orchestration overhead dominate above that. Wave count scales with corpus size; defaults tuned for ~80-120 docs.

6. **Multi-pass synthesis.** Each analytical pass (C1-C7) runs over all extractions in one context. Cluster-then-synthesize is unnecessary below 150 docs.

7. **Sub-agent model floor: Sonnet 4.6.** Phase B sub-agents MUST run on Sonnet 4.6 or higher. Haiku 4.5 is unacceptable. Use the named agent `corpus-extractor` (defined in `.claude/agents/corpus-extractor.md` with `model: sonnet`). Verify each sub-agent self-identifies its model in its return summary. If any returns Haiku or pre-4.6 Sonnet, halt the entire run, delete that batch's outputs, and remediate before retrying. (Background: Claude Code Issue #47488 documented silent Haiku override on Windows Cowork; defensive verification is mandatory.)

8. **Frontmatter compliance for all .md outputs.** Every analytical-pass and synthesis output begins with canonical vault frontmatter. The pass-specific prompts in `ref/` enforce this; do not strip frontmatter from output.

9. **No context contamination from prior known cases.** When analyzing a corpus, do not import names, frames, or interpretations from famous prior cases in the domain unless source documents explicitly name them. Each document analyzed on its own evidence. (For UAP-class corpora: no unprompted Roswell / Tic Tac / Trinity / Aztec / Rendlesham / Phoenix Lights / Nimitz / Stephenville priming. For legal corpora: no precedent-grafting beyond what the documents cite. For FOIA archives: no narrative-importing from prior releases. The principle is universal.)

## Workspace structure

```
<source>/                              # SOURCE (read-only, configured in .corpus.json)
<workspace>/                           # WORKSPACE (configured in .corpus.json)
  +-- .corpus.json                     # Workspace config (written by /corpus init)
  +-- 20-extractions/                  # Stage 1 output
  |   +-- *.json                       # Per-document extraction JSONs
  |   +-- _invalid/                    # Schema-failed extractions
  +-- 30-index/                        # Optional Stage 2 (advanced/follow-up)
  |   +-- corpus.db
  |   +-- clusters/
  +-- 60-final-report/                 # Stage C output: analytical-pass + master + audit
  |   +-- cross-examination-<date>.md      (C1)
  |   +-- entity-network-<date>.md         (C2)
  |   +-- institutional-chain-<date>.md    (C3)
  |   +-- negative-space-<date>.md         (C4)
  |   +-- analytical-adversarial-<date>.md (C5)
  |   +-- report-<date>.md                 (C6 master synthesis)
  |   +-- citation-audit-<date>.md         (C7)
  +-- 70-adversarial/                  # Phase D output: master-report adversarial
  +-- ref/                             # Per-corpus prompts (versioned; treat as code)
  |   +-- 00-master-system-prompt.md
  |   +-- 10-stage1-extraction-prompt.md
  |   +-- 20-unified-synthesis-prompt.md       (C6, v5)
  |   +-- 21-cross-examination-prompt.md       (C1, v5)
  |   +-- 22-entity-network-prompt.md          (C2, v5)
  |   +-- 23-institutional-chain-prompt.md     (C3, v5)
  |   +-- 24-negative-space-prompt.md          (C4, v5)
  |   +-- 25-analytical-adversarial-prompt.md  (C5, v5)
  |   +-- 26-citation-audit-prompt.md          (C7, v5)
  |   +-- 40-stage4-adversarial-prompt.md      (Phase D master adversarial)
  |   +-- (legacy 30-stage3, 50-stage5 kept but unused for default v5 flow)
  +-- scripts/                         # Pipeline scripts (copied from skill on init)
  |   +-- audit_run.py                # v5 wave-aware audit
  |   +-- stratified_sample.py        # v5 stratified MVP sampler
  |   +-- 20_index.py                 # Optional, for follow-up queries
  |   +-- 30_make_clusters.py         # Optional, for follow-up deep dives
  |   +-- requirements.txt            # stdlib only
  +-- logs/
      +-- runs/                       # dispatch logs, started sentinels, manifests, wave checkpoints, orchestrator state
      +-- benchmarks/

.claude/agents/                       # Project-local subagent registry (committed)
+-- corpus-extractor.md               # Pins Phase B sub-agents to Sonnet 4.6+
```

## Sub-commands

### `/corpus init --name <slug> --source <source-dir> [--workspace <out-dir>]`

Creates a new corpus workspace. **Required:** `--name` (slug for the corpus), `--source` (absolute path to read-only document directory). **Optional:** `--workspace` (where outputs go; defaults to `Efforts/<slug>-corpus/`).

Workflow:
1. Validates source exists and contains documents (>= 5).
2. Creates workspace directory tree (`20-extractions/`, `30-index/`, `60-final-report/`, `70-adversarial/`, `ref/`, `scripts/`, `logs/runs/`, `logs/benchmarks/`).
3. Writes `.corpus.json` with name, source, workspace, ISO date, expected doc count.
4. Copies pipeline scripts from `.claude/skills/corpus/scripts/` to `<workspace>/scripts/`.
5. Creates `<workspace>/ref/README.md` instructing user to populate the prompt files (00-master, 10-stage1, 20-unified, 21-cross-examination, 22-entity-network, 23-institutional-chain, 24-negative-space, 25-analytical-adversarial, 26-citation-audit, 40-stage4-adversarial). Domain-customize per corpus.
6. Prints next-step recommendation: populate `ref/` prompts, then run `/corpus mvp --stratified`.

### `/corpus status`
Quick state report. No LLM work. Reads `.corpus.json` and the most recent `orchestrator-state-*.json` and `wave-<W>-complete.json` files. Reports: which phase the pipeline is in, which waves are complete, what command would resume from current state.

```bash
cd <workspace>
echo "=== Source ==="
ls <source>/*.pdf | wc -l       # expected doc count from .corpus.json
echo "=== Stage 1 extractions ==="
ls 20-extractions/*.json 2>/dev/null | wc -l
ls 20-extractions/_invalid/*.err 2>/dev/null | wc -l
echo "=== Wave checkpoints ==="
ls logs/runs/wave-*-complete.json 2>/dev/null
echo "=== Phase B completion ==="
ls logs/runs/phase-b-complete.json 2>/dev/null
echo "=== Analytical-pass outputs (C1-C7) ==="
ls 60-final-report/*.md 2>/dev/null
echo "=== Master adversarial ==="
ls 70-adversarial/*.md 2>/dev/null
```

Resume logic:
- If `wave-N-complete.json` files exist for waves 1..K but not K+1..N, `/corpus extract --resume` picks up at wave K+1.
- If `phase-b-complete.json` exists, `/corpus extract` reports "Phase B already complete" and recommends `/corpus analyze-all`.
- If individual analytical-pass output files exist (e.g., `60-final-report/cross-examination-<date>.md`), `/corpus analyze` for that pass reports "already complete" unless `--force` is passed.

### `/corpus mvp [--stratified]`
Recommended first run. Validates the pipeline on 5 documents.

With `--stratified`, runs `python scripts/stratified_sample.py --source <source> --n 5` to pick a category-diverse sample (per corpus-specific categorization heuristics in the script) instead of first-alphabetical.

Workflow:
1. Pick 5 documents (stratified or smallest by size).
2. Run Phase B as 1 wave with K=2 sub-agents (~3 docs each).
3. Validate verifiability infrastructure (`audit_run.py --wave 1` PASS).
4. Stop after extraction. Show user 2 random extractions for spot-check.
5. On user go-ahead, run `/corpus analyze contradictions` (C1) + `/corpus synthesize-master` (C6 with empty C1-C5 inputs accepted) for a smoke-test deliverable.
6. Final summary: what worked, what to revise in `ref/` prompts before scaling.

### `/corpus extract [--waves N] [--parallel-per-wave K] [--limit M] [--resume] [--interactive]`

**Primary Phase B command. Wave-based dispatch with hard audit gates between waves.**

Defaults tuned for ~80-120 doc corpora: `--waves 4 --parallel-per-wave 5`. Produces 4 waves of ~20-30 docs each, 5 parallel sub-agents per wave processing ~4-6 docs each. Tune up for larger corpora.

#### Phase A -- pre-flight (main context)
1. Read `.corpus.json`. Confirm SOURCE has the expected doc count (or report actual count).
2. Confirm WORKSPACE exists with `ref/` and `scripts/` populated. If not, halt and recommend `/corpus init`.
3. Confirm all required reference prompts present in `ref/`: `00-master-system-prompt.md`, `10-stage1-extraction-prompt.md`, `20-unified-synthesis-prompt.md`, plus the v5 analytical prompts (`21`, `22`, `23`, `24`, `25`, `26`). Halt if any missing.
4. Compute deterministic doc_ids for all SOURCE documents:
   ```
   doc_id = sanitize(stem(filename)) + "__" + sha256(file)[:8]
   ```
   where sanitize = replace non-alphanumeric/`-`/`_` with `_`, truncate to 120 chars.
5. Build to-do list: doc_ids whose `<workspace>/20-extractions/<doc_id>.json` does not exist.
6. Compute wave assignments deterministically: sort to-do by filename, split into N waves of equal size (last wave absorbs remainder).
7. Check for `wave-<W>-complete.json` sentinels -- if `--resume`, skip those waves; otherwise halt and ask user about resume vs reset.
8. Estimate token budget LOUDLY: per-wave estimate, full-run estimate, historical baseline from MVP if available. Print and confirm before proceeding.

#### Phase B -- wave-based extract

For wave W in [1..N]:

**B-W-pre.** Compute SHA-256 of `ref/00-master-system-prompt.md`, `ref/10-stage1-extraction-prompt.md`, and the agent definition file. Write the dispatch log to `logs/runs/dispatch-<W>-<iso_no_punct>.json`:

```json
{
  "phase": "B",
  "wave": <W>,
  "dispatch_timestamp": "<iso8601>",
  "expected_batches": <K>,
  "parallel_per_wave": <K>,
  "batch_assignments": {
    "wave_<W>_batch_1": ["<doc_id_1>", ...],
    "wave_<W>_batch_2": [...]
  },
  "expected_total_docs": <count>,
  "agent_definition_path": ".claude/agents/corpus-extractor.md",
  "agent_definition_sha256": "<sha256>",
  "ref_master_sha256": "<sha256>",
  "ref_stage1_sha256": "<sha256>"
}
```

Also write orchestrator-state file: `logs/runs/orchestrator-state-phase-B-wave-<W>-pre-<iso_no_punct>.json` capturing current phase, wave, batches dispatched.

**B-W-pre verification:** Confirm `.claude/agents/corpus-extractor.md` has `model: sonnet`. Confirm env var `CLAUDE_CODE_SUBAGENT_MODEL` is `claude-sonnet-4-6` or similar (defensive against Issue #47488).

**B-W-dispatch.** Dispatch K parallel sub-agents using `subagent_type: "corpus-extractor"`. Each sub-agent gets:
- Its assigned `(doc_absolute_path, expected_doc_id)` tuples
- The wave number W (passed as a parameter the agent uses in `_meta`, sentinel, manifest)
- The batch_id (e.g., `wave_<W>_batch_1` through `wave_<W>_batch_<K>`) -- must exactly match dispatch log keys
- The ref directory path
- The output and invalid-output directory paths

The agent definition file already contains operational instructions, citation rules, validation logic, dispatch-sentinel + `_meta` block + manifest requirements, and required return format. You do NOT need to inline the master prompt.

**B-W-first-return model check.** When the first sub-agent returns its summary, immediately inspect `model_self_id`. If anything below Sonnet 4.6 (e.g., `claude-haiku-4-5-*`, `claude-sonnet-4-5-*`):
- HALT all in-flight sub-agents in this wave AND the entire pipeline immediately
- Delete extractions written by that batch (untrustworthy)
- Report mismatch to user with remediation steps from the agent file
- Do not retry until user confirms remediation

**B-W-wait.** If first-return passed, wait for all K sub-agents in this wave. Re-verify each `model_self_id` as they return.

**B-W-verify (HARD GATE).** After all K sub-agents return:
1. Run `python scripts/audit_run.py --wave <W>`. The audit runs the four-source cross-reference (dispatch log vs started sentinels vs manifests vs extraction `_meta`).
2. The audit MUST report PASS for the wave. If FAIL, write `logs/runs/wave-<W>-FAILED-<iso_no_punct>.json` with the full audit diagnostic and HALT the pipeline. Do not proceed to wave W+1.
3. Confirm extraction count for this wave matches expected count (minus any legitimate `fail_doc_ids`).
4. Confirm every extraction in this wave has a valid `_meta` block with all seven sub-fields populated.

**B-W-checkpoint.** Write `logs/runs/wave-<W>-complete.json`:

```json
{
  "wave": <W>,
  "completed_at": "<iso8601>",
  "doc_ids_extracted": [...],
  "batch_ids": [...],
  "audit_status": "PASS",
  "extraction_count": <N>,
  "elapsed_seconds": <float>
}
```

Also write `logs/runs/orchestrator-state-phase-B-wave-<W>-post-<iso_no_punct>.json` capturing post-wave state.

**B-W-pause (optional).** If `--interactive`, pause and ask user to confirm before next wave. Default: continue immediately.

#### Phase B-end (after all waves complete)

Write `logs/runs/phase-b-complete.json`:

```json
{
  "phase": "B",
  "completed_at": "<iso8601>",
  "total_extractions": <N>,
  "waves_completed": <count>,
  "audit_status": "PASS"
}
```

Recommend next step to user: "Phase B complete. Exit this session and run `/corpus analyze-all` (or individual `/corpus analyze <pass>` invocations) in fresh sessions for the analytical layer."

#### When to push back during /corpus extract
- User says "skip MVP, do all N right now" without prior testing -- push back. Recommend `/corpus mvp --stratified` first.
- User asks for `--parallel-per-wave > 10` -- push back. Diminishing returns.
- User asks to skip wave-audit gate -- refuse. The audit gate is the v5 verifiability backbone.
- During Phase B, if a wave fails audit, halt and surface the gap to the user. Do not proceed silently.

### `/corpus analyze contradictions` -- runs C1 (cross-examination)
1. Reads master prompt + `ref/21-cross-examination-prompt.md`.
2. Reads all extractions from `<workspace>/20-extractions/`.
3. Verifies token budget; warns if estimate exceeds 80% of context window.
4. Runs the cross-examination pass per the prompt structure (7 sections including methodology, contradictions, corroborations, patterns, negative findings, confidence/caveats, citation registry).
5. Validates output has correct frontmatter (categories: [wiki], type: report, tags include `cross-examination`, pipeline_version: v5) and Section 7 citation registry.
6. Writes to `60-final-report/cross-examination-<YYYY-MM-DD>.md`.
7. Reports findings count, citation count, runtime, and recommends next pass.

### `/corpus analyze entities` -- runs C2 (entity network)
Same shape as C1 but using `ref/22-entity-network-prompt.md`. Output: `60-final-report/entity-network-<date>.md`.

### `/corpus analyze institutional` -- runs C3 (institutional chain)
Same shape but using `ref/23-institutional-chain-prompt.md`. Output: `60-final-report/institutional-chain-<date>.md`.

### `/corpus analyze negative-space` -- runs C4 (negative space + follow-up targets)
Same shape but using `ref/24-negative-space-prompt.md`. Output: `60-final-report/negative-space-<date>.md`.

### `/corpus analyze adversarial` -- runs C5 (analytical adversarial)
**Strongly recommend running this in a fresh Claude Code session, separate from the session that produced C1-C4.** Same-context adversarial is too soft.

Reads master prompt + `ref/25-analytical-adversarial-prompt.md` + the four C1-C4 reports + all extractions. Produces hostile review with per-pass verdicts (YES / PARTIALLY / NO) and master-synthesis instruction (Section 8). Output: `60-final-report/analytical-adversarial-<date>.md`.

### `/corpus analyze-all`
Runs C1 -> C2 -> C3 -> C4 in the current session. Warns about token budget before starting (each pass is ~80-150K tokens output + extractions in context). On budget concern, recommend splitting across sessions instead. Does NOT run C5 (which must be fresh-session for genuine adversarial value).

### `/corpus synthesize-master`
Runs C6 (master synthesis). Requires C1-C5 outputs present in `60-final-report/`. Reads master prompt + `ref/20-unified-synthesis-prompt.md` + all extractions + C1-C5 reports. Excludes findings flagged FAILED by C5; revises findings flagged PARTIALLY per C5 instructions; preserves caveats per C5 master-synthesis instruction. Output: `60-final-report/report-<date>.md` with mandatory Section 11 provenance trail.

If C1-C5 are not all present, the command warns and offers two paths:
- (default) HALT and recommend running missing analytical passes first
- `--no-analytical` flag: proceed with master synthesis using only extractions (legacy v3/v4 single-pass shape, not recommended for corpora where multi-pass synthesis is feasible)

### `/corpus audit-citations`
Runs C7 (citation audit). Reads master synthesis report (C6 output) + C1-C5 reports + extractions. Checks every `[DOCID:PAGE]` for resolution, page plausibility, content match, evidential class consistency. Output: `60-final-report/citation-audit-<date>.md` with health verdict (Strong/Moderate/Weak) and failed-citation action list.

If verdict is Moderate, recommend: revise C6 incorporating the failed-citation fixes, then re-run citation audit. If Weak, recommend: re-run C6 with stricter citation discipline.

### `/corpus adversarial [--report-file FILE]`
Phase D -- master-report adversarial review. **Run in a fresh session.**

Reads `ref/00-master-system-prompt.md` + `ref/40-stage4-adversarial-prompt.md` + the most recent C6 report + supporting extractions. Produces hostile review per Stage 4 prompt structure. Output: `70-adversarial/adversarial-<report-name>.md`. Reports verdict (YES / PARTIALLY / NO), top-3 damaging findings, minimum revisions needed.

### `/corpus audit-dispatch [--wave N | --all | --phase-b-complete]`
Wraps `python scripts/audit_run.py` for human inspection.
- `--wave N`: audit a single wave
- `--all`: audit every dispatched wave
- `--phase-b-complete`: audit every wave AND require `phase-b-complete.json` sentinel

Use this whenever pipeline state is uncertain or before running analytical passes.

### `/corpus index` (optional, follow-up)
Build SQLite + FTS5 index from extractions. Useful for follow-up queries beyond the report.

```bash
cd <workspace>
python scripts/20_index.py --input 20-extractions --db 30-index/corpus.db
python scripts/20_index.py --db 30-index/corpus.db --list-clusters
```

### `/corpus clusters` (optional, follow-up)
Generate cluster definitions for deep-dive analysis.

```bash
cd <workspace>
python scripts/30_make_clusters.py --db 30-index/corpus.db --output 30-index/clusters
```

## Resumability and state persistence

At every phase or wave boundary, the orchestrator writes an `orchestrator-state-*.json` file containing:
- Current phase (A, B-W-pre, B-W-post, C1, C2, ..., C7, D)
- Decisions made (wave assignments, batch assignments, model verified)
- Outstanding work
- Pointer to most recent dispatch log / wave checkpoint
- Timestamp

`/corpus status` reads the most recent state file plus `wave-<W>-complete.json` files. It reports:
- What phase the pipeline is in (or "complete" or "failed")
- Which waves are complete
- What command would resume from current state

Resume logic:
- If a session opens and finds `wave-N-complete.json` for waves 1..K but not K+1..N, `/corpus extract --resume` picks up at wave K+1.
- If `phase-b-complete.json` exists, `/corpus extract` reports "Phase B already complete" and recommends `/corpus analyze`.
- If individual analytical-pass output files exist (e.g., `60-final-report/cross-examination-<date>.md`), `/corpus analyze contradictions` reports "already complete" unless `--force` is passed.

## Single-run feasibility for ~80-120-doc corpora (v5)

| Phase | Token cost (estimated) | Wall-time (estimated) | In-context? |
|-------|------------------------|------------------------|-------------|
| Phase B (4 waves) | ~6-10M (sub-agent contexts; main context only sees summaries + audit) | 30-50 min | Sub-agent contexts (parallel per wave) |
| Phase C1 cross-examination | ~80-150K | 5-15 min | Main context |
| Phase C2 entity network | ~80-150K | 5-15 min | Main context |
| Phase C3 institutional chain | ~80-150K | 5-15 min | Main context |
| Phase C4 negative space | ~80-150K | 5-15 min | Main context |
| Phase C5 analytical adversarial (fresh session) | ~80-100K | 5-10 min | Main context |
| Phase C6 master synthesis | ~150-200K | 10-20 min | Main context |
| Phase C7 citation audit | ~50-100K | 5-10 min | Main context |
| Phase D master adversarial (fresh session) | ~80-100K | 5-10 min | Main context |

Each session bounded; no compaction risk; full provenance from source doc page -> extraction -> analytical pass -> master synthesis -> citation audit. Total wall time across sessions: ~2-4 hours for ~100-doc corpora.

If user wants compression, sessions C1-C4 can be bundled via `/corpus analyze-all` (token budget permitting). C5 must remain fresh-session for genuine adversarial value.

## Behavior expectations

**On `/corpus` invocation without subcommand:** Run `/corpus status` and recommend the next step based on state:
- No `.corpus.json` -> `/corpus init --name <slug> --source <dir>`
- No extractions -> `/corpus mvp --stratified`
- MVP complete, full extraction not started -> `/corpus extract`
- Phase B partially complete -> `/corpus extract --resume`
- Phase B complete, no analytical passes -> `/corpus analyze contradictions`
- C1-C4 complete, no C5 -> `/corpus analyze adversarial` (fresh session)
- C1-C5 complete, no C6 -> `/corpus synthesize-master`
- C6 complete, no C7 -> `/corpus audit-citations`
- All complete -> `/corpus adversarial` (Phase D, fresh session) or done.

**On hallucinated connections during synthesis:** If no hard-identifier connections exist in the corpus, say so explicitly. Do not invent thematic ones.

**On redactions:** Treat redactions as missing data. Do not infer significance. Document in extractions; do not let them inflate anomaly scores.

**On context contamination from prior known cases:** Do not import frames, names, or narratives from famous prior cases of the domain unless source documents name them. Each document analyzed on its own evidence. The synthesis layer must not graft outside narratives onto the corpus.

**On user pushing to skip steps:** Push back. MVP, schema validation, wave audit gates, C5 analytical adversarial, and C7 citation audit are integrity layers. Without them the report is confident-sounding slop.

**On quota concerns mid-run:** If rate limits hit during Phase B, halt cleanly. Report which waves are complete and which doc_ids in the current wave are extracted. User can resume by re-running `/corpus extract --resume`.

## First-time workspace setup

`/corpus init` handles this automatically. Manual setup, if needed:

```powershell
$NAME = "<corpus-slug>"
$SOURCE = "<absolute-path-to-source-dir>"
$WS = "<absolute-path-to-workspace>"   # e.g., "$VAULT_ROOT/Efforts/<slug>-corpus"

mkdir $WS
cd $WS
mkdir 20-extractions, "20-extractions\_invalid", 30-index, "30-index\clusters", `
      60-final-report, 70-adversarial, ref, scripts, `
      logs, "logs\runs", "logs\benchmarks"
```

Then:
1. Write `.corpus.json` to `$WS\.corpus.json` with name, source, workspace, ISO date, pipeline_version v5, extractor_agent `corpus-extractor`, model_floor `sonnet-4-6`, doc_count_expected.
2. Populate `$WS\ref\` with the 10 prompt files for your corpus (00-master, 10-stage1, 20-unified, 21-cross-examination, 22-entity-network, 23-institutional-chain, 24-negative-space, 25-analytical-adversarial, 26-citation-audit, 40-stage4-adversarial). Domain-customize as needed for the corpus subject matter.
3. Copy pipeline scripts:
   ```powershell
   Copy-Item "$env:VAULT_ROOT/.claude/skills/corpus/scripts/*.py" $WS\scripts\ 
   Copy-Item "$env:VAULT_ROOT/.claude/skills/corpus/scripts/requirements.txt" $WS\scripts\ 
   ```
4. **Verify the sub-agent definition** at `<VAULT_ROOT>/.claude/agents/corpus-extractor.md` has `model: sonnet`. No manual install required -- the project-local registry makes the subagent automatically discoverable in this workspace.
5. **Set the sub-agent model environment variable** (defensive against Issue #47488):
   ```powershell
   [Environment]::SetEnvironmentVariable("CLAUDE_CODE_SUBAGENT_MODEL", "claude-sonnet-4-6", "User")
   ```
   Then RESTART your Claude Code session for the env var to take effect.

6. Run `/corpus mvp --stratified` first, then `/corpus extract` if MVP looks good.

## Failure modes to actively watch

1. **Document reading drift on degraded scans.** Multi-page scans with poor image quality may produce extractions with date/name errors. Spot-check high-anomaly cases (score >= 7) against original source documents.

2. **Schema-violating extraction output.** If >5% of docs land in `_invalid/`, simplify the schema or split extraction into two passes.

3. **Token budget surprises.** If individual documents are larger than estimated (e.g. 100+ pages), Phase B can run long or hit limits. Sub-agent failures should report token-related errors clearly.

4. **Self-validating analytical adversarial.** Same-session C5 will be soft. If the verdict is uniformly YES, that is the failure signature -- re-run in a fresh session.

5. **Context contamination from prior known cases.** If extraction or synthesis output references named famous cases without the source documents naming them, the prompt failed; reinforce in `00-master-system-prompt.md`. (The principle is domain-universal: no Roswell magnet for UAP corpora, no precedent-grafting for legal corpora, no prior-release narrative for FOIA archives.)

6. **Quota exhaustion mid-run.** Rate-limit errors -> halt cleanly. Resume via `/corpus extract --resume`. Wave checkpoint files make resume safe.

7. **Citation audit reveals systemic hallucination.** If C7 reports >10% failed citations, do not patch -- re-run C6 with stricter citation discipline. The synthesis layer has drifted from the extractions.

8. **Wave audit gate false-fail.** If `audit_run.py --wave N` reports FAIL but you believe the wave succeeded, do NOT bypass. The four-source cross-reference is mechanical; a FAIL means evidence is genuinely missing or inconsistent. Investigate which source is missing (started sentinel, manifest, `_meta` block, or dispatch log) before any retry.

## Origin

Originally designed and field-tested as the UAP Corpus Analysis Skill (93-doc declassified UAP/UFO corpus, pipeline run 2026-05-09 through 2026-05-11, three adversarial rounds, citation audit Strong verdict). Generalized to mass-document analysis pipeline 2026-05-21 with rename uap -> corpus, subagent rename uap-extractor -> corpus-extractor, path parameterization via `.corpus.json` + flags + env vars, generic trigger phrases, and removal of UAP-specific examples while preserving all architectural invariants (wave-based parallel extraction, hard audit gates, multi-pass analytical synthesis, citation discipline, evidential class tagging, anti-context-contamination, model floor enforcement).

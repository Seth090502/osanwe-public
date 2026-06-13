# /corpus -- Mass-Document Analysis Skill (Claude Code native, v5)

End-to-end pipeline for analyzing large document corpora (10-150 documents) with verifiable multi-pass synthesis. Built for any mass-document analysis task: FOIA archives, declassified records, legal discovery sets, regulatory filings, court records, congressional disclosures, research dossiers, intelligence community releases. Citation-disciplined, resumable across sessions, adversarially-reviewed.

For the full skill reference (architecture, sub-commands, hard invariants, failure modes), see `SKILL.md`. This README is a quick-start.

## Architecture at a glance (v5)

| Phase | What | Engine |
|-------|------|--------|
| A | Pre-flight: read `.corpus.json`, compute doc_ids, wave split, token budget | Main session, no LLM |
| B | Wave-based parallel extraction with hard audit gate per wave | Parallel sub-agents (default K=5 per wave) |
| C1-C4 | Analytical synthesis passes: cross-examination, entity network, institutional chain, negative space | Main context, one pass per session ideal |
| C5 | Analytical adversarial review of C1-C4 | Fresh session strongly recommended |
| C6 | Master synthesis incorporating C1-C5 with provenance trail | Main context |
| C7 | Citation audit -- every `[DOCID:PAGE]` verified | Main context |
| D | Master-report adversarial review | Fresh session recommended |

Each session is bounded; no compaction risk; full provenance from source page -> extraction -> analytical pass -> master synthesis -> citation audit.

## Sizing

- **<10 docs:** read them directly; this pipeline is overkill.
- **10-150 docs:** sweet spot. Single-context synthesis fits comfortably.
- **>150 docs:** run the optional cluster layer (Stage 2) first to chunk synthesis.

For reference, the original 93-doc corpus this skill was built on used ~7-11M tokens total across all phases (~45-120 min wall time across sessions).

## Per-corpus workspace

Each corpus has a workspace with a `.corpus.json` config:

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

Source is read-only. All outputs land in workspace/.

## Install

The skill is installed at `.claude/skills/corpus/`. The required sub-agent definition is committed at `.claude/agents/corpus-extractor.md` -- no manual install required; project-local subagents are auto-discovered.

**Defensive env var** (against Claude Code Issue #47488 silent Haiku-override on Windows Cowork):

```powershell
[Environment]::SetEnvironmentVariable("CLAUDE_CODE_SUBAGENT_MODEL", "claude-sonnet-4-6", "User")
# Then RESTART your Claude Code session.
echo $env:CLAUDE_CODE_SUBAGENT_MODEL    # should print: claude-sonnet-4-6
```

Three layers of defense are built in: (1) named agent definition with `model: sonnet`; (2) env var backup; (3) runtime self-identification (every sub-agent returns its `model_self_id` and the orchestrator halts the run if anything below Sonnet 4.6 is detected).

## Initialize a new corpus

```
/corpus init --name <slug> --source <absolute-path-to-docs-dir> [--workspace <out-dir>]
```

This creates the workspace tree, writes `.corpus.json`, copies pipeline scripts. You still need to populate `<workspace>/ref/` with the 10 prompt files (00-master-system-prompt, 10-stage1-extraction, 20-unified-synthesis, 21-cross-examination, 22-entity-network, 23-institutional-chain, 24-negative-space, 25-analytical-adversarial, 26-citation-audit, 40-stage4-adversarial) -- domain-customize per corpus. See `<workspace>/ref/README.md` (created by init) for the schema mapping.

## First run -- MVP on 5 documents

```
cd <workspace>
claude
```

In the session:

```
/corpus mvp --stratified
```

Claude Code will:
1. Pick 5 documents (category-diverse if `--stratified`, smallest-first otherwise).
2. Dispatch 2 parallel sub-agents to extract those 5.
3. Stop and ask you to spot-check 2 random extractions.
4. On your go-ahead, run a synthesis smoke-test on those 5.
5. Show you the resulting mini-report.
6. Recommend whether to proceed to full-run or revise prompts first.

**Critical review checklist after MVP:**
- Open 2 random extractions side-by-side with their source documents. Verify dates, names, locations are correct (document reading can drift on bad scans).
- Confirm evidential class tags (`[OBS]`/`[REP]`/`[HEAR]`) are used correctly -- secondhand reports should NOT be tagged `[OBS]`.
- Confirm citations use `[DOCID:PAGE]` format throughout.
- Score fields reasonable? Watch for inflation -- corpora on charged topics prime models toward credulity.
- Read the mini-report. Are claims cited? Are connections (if any) hard-identifier or vibe-based?

If anything is consistently wrong, edit `<workspace>/ref/00-master-system-prompt.md` or `<workspace>/ref/10-stage1-extraction-prompt.md` before scaling.

## The full run

Once MVP is clean:

```
/corpus extract
```

Default: 4 waves, 5 sub-agents per wave. The orchestrator will:
1. Confirm the document inventory.
2. Estimate token budget aloud and confirm with you.
3. Dispatch wave 1 with K=5 parallel sub-agents.
4. Audit-gate wave 1 (HARD; refuse to proceed if FAIL).
5. Repeat for waves 2..N.
6. Write `phase-b-complete.json` when all waves pass.
7. Recommend exiting the session and running `/corpus analyze-all` in a fresh session.

## Analytical layer

Each pass best run in its own session:

```
/corpus analyze contradictions    # C1 cross-examination
/corpus analyze entities          # C2 entity network
/corpus analyze institutional     # C3 institutional chain (routing, distribution, program transitions)
/corpus analyze negative-space    # C4 missing attachments, follow-ups, targets to seek
```

Then in a **fresh session**:

```
/corpus analyze adversarial       # C5 hostile review of C1-C4
```

Then back to main:

```
/corpus synthesize-master         # C6 master synthesis incorporating C1-C5
/corpus audit-citations           # C7 every [DOCID:PAGE] verified
```

Optionally, in another fresh session:

```
/corpus adversarial               # Phase D master-report adversarial
```

## Quota and timing expectations

For a ~100-document corpus (~3,000-4,000 pages estimated):

| Phase | Estimated tokens | Wall time |
|-------|-----------------|-----------|
| Phase B (4 waves) | 6-10M total across sub-agent contexts | 30-50 min |
| Phase C1 cross-examination | 80-150K | 5-15 min |
| Phase C2 entity network | 80-150K | 5-15 min |
| Phase C3 institutional chain | 80-150K | 5-15 min |
| Phase C4 negative space | 80-150K | 5-15 min |
| Phase C5 analytical adversarial (fresh) | 80-100K | 5-10 min |
| Phase C6 master synthesis | 150-200K | 10-20 min |
| Phase C7 citation audit | 50-100K | 5-10 min |
| Phase D master adversarial (fresh) | 80-100K | 5-10 min |
| **Total** | **~7-11M tokens** | **~2-4 hours across sessions** |

Significant Max-20x usage but achievable in a single day. Rate-limit-resumable across sessions via wave checkpoints + `phase-b-complete.json` sentinel.

## What happens if extraction fails for some docs

Failed extractions land in `20-extractions/_invalid/<doc_id>.err` with the raw output and error context. After a full run:

1. `/corpus status` reports the count.
2. If <5% failure rate, proceed to synthesis without them -- note the omission in the final report's limitations section.
3. If 5-20% failure rate, inspect a few `.err` files. Likely a schema issue or specific document format problem. Fix the prompt, re-run extraction on just the failed doc_ids.
4. If >20% failure rate, halt. Something is systemically wrong. Review the extraction prompt against actual document content.

## Troubleshooting

**"Sub-agent timeout / hang."** Some documents may be very large or pathological. Reduce `--parallel-per-wave` to 3-4 to give each sub-agent more rate-limit headroom, retry.

**"Synthesis report is shallow / missing detail."** Check that all extractions are present and well-populated. The synthesis is only as good as the underlying extractions. If extractions are thin, the bottleneck is Stage 1, not synthesis -- fix `ref/10-stage1-extraction-prompt.md`.

**"Adversarial review is uniformly approving."** You ran it in the same session as synthesis. Open a fresh session and re-run.

**"Quota exhausted mid-extraction."** Wait for the rate-limit window to reset. Re-run `/corpus extract --resume` -- skip-existing logic handles resumption.

**"Connection map in report is empty."** That's a valid output if the corpus documents share no hard identifiers (no shared persons / organizations / locations / systems / exact dates). Do not inflate. If you expected connections (e.g., all docs are from one program), inspect entity extractions in the JSONs -- if entities like base names, programs, persons aren't being captured well, fix Stage 1.

**"Wave audit gate FAIL."** Do not bypass. The four-source cross-reference (dispatch log + started sentinels + manifests + extraction `_meta` blocks) is mechanical; a FAIL means evidence is genuinely missing or inconsistent. Investigate which source is missing before retry.

**"Citation audit reveals >10% failed citations."** Do not patch the synthesis. Re-run C6 with stricter citation discipline -- the synthesis layer has drifted from the extractions.

## Origin

This skill was originally built for a 93-document UAP/UFO declassified corpus (pipeline run 2026-05-09 through 2026-05-11, three adversarial rounds, citation audit Strong verdict). Generalized to any mass-document corpus 2026-05-21 with rename uap -> corpus, subagent rename uap-extractor -> corpus-extractor, path parameterization via `.corpus.json`, generic trigger phrases, and removal of UAP-specific examples. All architectural invariants preserved: wave-based parallel extraction, hard audit gates, multi-pass analytical synthesis, citation discipline ([DOCID:PAGE] + evidential class tagging), anti-context-contamination, model floor enforcement.

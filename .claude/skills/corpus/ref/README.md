# Reference prompts (v5)

This directory ships templates / pointers for the per-corpus prompt files. **Per-corpus prompts live in the WORKSPACE (`<workspace>/ref/`), not here.** Each corpus's prompts are domain-customized; this skill-level `ref/` holds only the canonical schema and instructions.

## Per-workspace prompt files (populated at `/corpus init` and customized per corpus)

The pipeline expects these 10 files at `<workspace>/ref/`. **Treat them as code.** Bump the version header on every change. Re-run a small MVP before re-extracting the full corpus after any prompt edit.

| File | Used by | Purpose |
|------|---------|---------|
| `00-master-system-prompt.md` | Every stage (prepended verbatim) | Epistemic core: citation discipline, evidential class tagging, anti-hallucination, anti-context-contamination |
| `10-stage1-extraction-prompt.md` | Phase B sub-agents | Per-document extraction with full JSON schema |
| `20-unified-synthesis-prompt.md` | Phase C6 master synthesis | Single-context synthesis over all extractions (incorporates C1-C5) |
| `21-cross-examination-prompt.md` | Phase C1 | Contradictions, corroborations, patterns across the corpus |
| `22-entity-network-prompt.md` | Phase C2 | Persons / organizations / locations / systems + cross-network |
| `23-institutional-chain-prompt.md` | Phase C3 | Routing, distribution, program transitions, broken chains |
| `24-negative-space-prompt.md` | Phase C4 | Missing attachments, follow-up targets, gaps to seek |
| `25-analytical-adversarial-prompt.md` | Phase C5 (fresh session) | Hostile review of C1-C4 |
| `26-citation-audit-prompt.md` | Phase C7 | Verify every [DOCID:PAGE] against extractions |
| `40-stage4-adversarial-prompt.md` | Phase D (fresh session) | Master-report adversarial review |

## Legacy / optional (kept but unused for the default v5 flow)

- `30-stage3-cluster-synthesis-prompt.md` -- per-cluster brief synthesis (designed for thousands-of-docs corpora; not needed for the 10-150-doc sweet spot)
- `50-stage5-final-report-prompt.md` -- aggregates cluster briefs into a corpus report (replaced for <=150-doc corpora by `20-unified-synthesis-prompt.md`)

## Populating prompts for a new corpus

Per-corpus prompts must be authored or adapted before running `/corpus extract`. There is no one-size-fits-all template -- a UAP corpus, a legal discovery set, an FDA docket, and a congressional records release each need different extraction schemas, different entity-class focuses, and different domain-specific anti-contamination guards.

Typical workflow:
1. `/corpus init` creates `<workspace>/ref/README.md` reminding you to populate the 10 prompt files.
2. Author or adapt prompts. For canonical examples, see prior corpus runs (if any) or the master prompt-system reference document for your domain.
3. Run `/corpus mvp --stratified` to validate the prompts on 5 documents before committing to the full run.
4. Iterate on prompts until MVP outputs look right -- never scale to full extraction until the schema and citation discipline are correct.

## Version history

- v1 (initial): multi-stage cluster pipeline for thousands of docs
- v2: Claude-Code-only execution (no external LLMs)
- v3: unified single-pass synthesis for <=150-doc corpora
- v4: workspace-anchored prompts with deterministic doc_ids
- v5 (current): wave-based extraction + hard audit gates + multi-pass analytical synthesis (C1-C7) + provenance trail (_meta blocks with sha256-stamped prompt hashes); built on the 93-doc UAP corpus; generalized 2026-05-21 to any mass-document analysis task

## Future enhancement

A `templates/` subdirectory with domain-agnostic prompt skeletons would let `/corpus init` pre-populate `<workspace>/ref/` with editable starting points. Not yet implemented; current pattern requires users to author prompts per corpus.

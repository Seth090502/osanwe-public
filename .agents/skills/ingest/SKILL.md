---
name: ingest
description: "Two-mode document pipeline. extract (was /ingest): pull factual claims out of a fact-dense source and distribute them across the vault entity graph after material news or an onboarding dump. file (was /enrich): onboard a document WHOLE -- deterministic routing, canonical frontmatter, symmetric back-links, body byte-exact. Distinct from /deep (composes prompts), /vault (audits). Say 'file this' for mode file, 'extract claims' for extract; bare /ingest asks which when ambiguous."
metadata:
  categories: data
  osanwe-risk: "critical"
  osanwe-effort: "max"
  osanwe-arguments: "source [--mode extract|file] (bare source auto-routes per the matrix in Mode routing)"
  osanwe-argument-hint: "'`<source>`' [--mode extract|file] [--preview | --entity-only `<TICKER>` | --to `<path>` | --replace | --refresh | --backlink-only | --no-backlink | --confirm]"
  osanwe-allowed-tools: "Read Write Edit Grep Glob Bash Agent"
  osanwe-categories: "meta"
  osanwe-type: "skill"
  osanwe-status: "active"
  osanwe-created: "2026-04-18"
  osanwe-updated: "2026-08-23"
---

# /ingest -- two-mode document pipeline (extract | file)

Merged 2026-08-23 from the former /ingest (now mode `extract`) and /enrich (now mode
`file`) by OSANWE-V2 ADR-03. Both original bodies are preserved VERBATIM as
`ref-mode-extract.md` and `ref-mode-file.md`; their output contracts, phase orders,
gates, and commit disciplines are byte-for-byte what they were -- this spine only adds
mode selection and shared conventions.

## Shared conventions (both modes)

- Canon frontmatter via tools/frontmatter-check.py rules; ASCII discipline; routing
  law (agent writes -> wiki/ Efforts/ Calendar/).
- F11 atomic-commit lifecycle; pre-commit audit gates as each original body specifies.
- Both modes end with a report whose shape is unchanged from the original skill.

## Mode routing (decide FIRST, then load exactly one ref)

| signal | mode |
|---|---|
| "extract", "pull claims", "distribute to entities", refresh entity sections | **extract** |
| "file this", "onboard whole", "save + wire links", preserve body byte-exact | **file** |
| Bare source + no signal | ask one clarifying question (never guess) |

- Mode **extract**: load and follow `ref-mode-extract.md` IN FULL (former /ingest
  SKILL.md body, verbatim, incl. Phases A-K/O.0, idempotency, path-guards, tag guardrail).
- Mode **file**: load and follow `ref-mode-file.md` IN FULL (former /enrich SKILL.md
  body, verbatim, incl. placement table, frontmatter composition, back-link engine,
  idempotency --refresh, commit discipline).

## Cross-mode notes

- `file` may END with an extract recommendation: that logic lives in
  ref-mode-file.md Phase 6b verbatim; if it fires and the user confirms, re-enter this
  spine in mode extract.
- Distinct-from clauses of both former skills are preserved in substance above and in
  the description (trigger-first).

---
categories:
  - moc
created: 2026-04-05
updated: 2026-06-11
status: active
tags:
  - topic/knowledge-base
aliases: ["knowledge index", "index of indexes"]
related:
  - "[[investing-moc]]"
  - "[[career-moc]]"
  - "[[golf-moc]]"
  - "[[supplements-moc]]"
  - "[[tech-moc]]"
---

# Knowledge Base Index
Last updated: 2026-06-11

## Purpose
Persistent system memory. Load only the domain files relevant to the task.
Use reference docs to prime analysis before fresh search. For market and
investing work, follow `Atlas/sources/meta/analysis-depth-standard.md`.

## How To Use
1. Read this index when the task needs cross-domain context.
2. Route into the correct domain index instead of bulk-loading everything.
3. Use `ref-*.md` files for baseline context, then search for what changed.
4. Log significant sessions to `Calendar/decisions/sessions-log.md`.

## Domains
- [[investing-moc]] -- doctrine template, thesis essays, entity notes, analyses
- [[career-moc]] -- job-search pipeline scaffold (/career write-targets)
- [[golf-moc]] -- biomechanics + faults reference docs, /golf write-targets
- [[supplements-moc]] -- health advisory scaffold (/health write-targets)
- [[tech-moc]] -- local AI setup notes (populate as they accumulate)
- `Calendar/decisions/` -- [[sessions-log]], [[decision-log]], [[hot|session cache]], [[insight-stream]]
- `wiki/maintenance/` -- /vault audit + stats reports (created on first run)

## Reference Document Status
| Domain | File | Status |
|--------|------|--------|
| meta | [[analysis-depth-standard]] | Built |
| meta | [[ref-claude-code-mastery]] | Built |
| meta | [[ref-execution-discipline]] | Built |
| meta | [[ref-hot-md-schema]] | Built |
| meta | [[ref-research-methodology]] | Built |
| golf | [[ref-biomechanics]] | Built |
| golf | [[ref-common-faults]] | Built |
| investing | [[doctrine.template]] | Template -- fill USER_SET values |

Build your own domain ref docs via `/deep` (composes a claude.ai Research
prompt) followed by `/enrich` (onboards the output with canonical frontmatter
and back-links).

## Maintenance Rules
- Update the "Last updated" line when changing an index.
- Keep indexes concise and routing-focused.
- Treat reference docs as baseline context, not substitutes for fresh evidence.
- Correct stale status claims that can mislead runtime behavior.

# .claude/skills/ -- DERIVED tree router (Claude Code side)

> Canon moved (cross-harness migration S2, 2026-08-10): skill-authoring conventions live in `.agents/skills/AGENTS.md`; the canonical skill sources live in `.agents/skills/<name>/`. Read the canon router before authoring or editing ANY skill.

- Files here are GENERATED copies (`.agents/scripts/sync.py`) for Claude Code discovery. NEVER hand-edit a file carrying the GENERATED marker -- edit canon, re-run sync, commit both trees together. Consistency: `python .agents/scripts/checkall.py`.
- MIGRATION WINDOW (S3, 2026-08): skills whose canon is still a legacy pointer stub remain CANONICAL HERE until their batch lands; tools/router-check.py enforces skill-tree set-equality and sync/driftcheck skip unmigrated skills.
- Never-touch (sync neither writes nor deletes): `_archive/` and this AGENTS.md. This file is a pointer router only: add skill-authoring rules to the canon rulebook, `.agents/skills/AGENTS.md`, not here.
- Root invariant still binds: `/gate b` before building or materially extending any skill.

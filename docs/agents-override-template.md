# AGENTS.override.md template

> **Purpose:** Codex-specific session-level instruction override. When present, AGENTS.override.md is loaded TOGETHER with AGENTS.md and takes PRECEDENCE on conflicts -- Codex 0.118 concatenates instruction files root -> cwd and applies each dir's `AGENTS.override.md` after its `AGENTS.md`, so the override's lines win where they differ (verified 2026-07-08; it is NOT a hard replace of the base). Use sparingly: most sessions should run against AGENTS.md as-is. Remove this file to restore default behavior.
> **Convention:** Copy this template to `AGENTS.override.md` (same directory, drop the `.template` suffix) and edit. The unsuffixed file is gitignored.

## When to use AGENTS.override.md

Use cases:
- One-off session needs different write-discipline rules (e.g., experimental branch where auto-commit is disabled)
- Temporarily disable a path-guard for archival migration work
- Pin a specific subagent reasoning_effort across the session
- Test a new skill behavior without modifying base AGENTS.md

Do NOT use for:
- Permanent rule changes (modify AGENTS.md directly + commit)
- Per-machine overrides that should persist (use environment variables)
- Multi-session workflows (the override is forgotten when removed)

## Structure

Because Codex MERGES override + base (override applied after, so it wins on conflict), you only need to include the rules that DIFFER -- not the whole file. Any rule you do not restate still comes from AGENTS.md (verified 2026-07-08, Codex 0.118).

## Example: temporarily disable auto-commit + relax path-guards for migration session

```markdown
# AGENTS.override.md (active during 2026-05-15 vault migration only)

# (no need to copy the base -- merge keeps everything in AGENTS.md; write ONLY the overriding sections below)

## Permissions (OVERRIDE: relaxed for migration)

- Atlas writes do NOT require confirmation during this session
- private/ writes are temporarily allowed (touching private/notes/migration-2026-05-15.md only)
- Auto-commit suppressed (will commit manually at session end after sanity check)

## Write discipline (OVERRIDE: manual-commit mode)

- Skip session-branch hook auto-switch (working on vault-migration-2026-05-15 directly)
- F11 flag set for entire session: `touch .claude/state/auto-commit-disabled`
- Manual `git commit` at logical checkpoints
```

## Removal

When the override session ends:
```bash
rm AGENTS.override.md
```

Codex falls back to AGENTS.md automatically on next read.

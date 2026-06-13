---
categories:
  - sources
type: reference
created: 2026-05-06
updated: 2026-05-05
status: active
confidence: high
tags:
  - topic/execution-discipline
  - topic/atomic-commit
  - topic/skill-infrastructure
aliases: [execution-discipline, f11-discipline, cascade-discipline]
related:
  - "[[ref-claude-code-mastery]]"
  - "[[ref-hot-md-schema]]"
  - "[[ref-research-methodology]]"
---

# Reference: Execution Discipline (F11 + cascade orchestration)

Last updated: 2026-05-06
Sources: Internal pattern naming from 2026-05-04 sandbox-derived /retro Phase 2 cascade + 2026-05-05 cohort sweep retro
Refresh cadence: As-needed (discipline is stable; refresh when new cascade patterns surface)
Built by: Claude Code (direct authorship; Quality Sweep 1)

## Purpose

Canonical home for the F11 (auto-commit-suppression flag) discipline plus the cascade-aware extensions added in Quality Sweep 1. Loaded by skills authoring multi-phase atomic-commit work and by /retro/`/spark continuity audit when scoring discipline divergence.

## F11 Mechanism (canonical)

The flag file `.claude/state/auto-commit-disabled` suppresses the PostToolUse `auto-commit.sh` hook. When the file is present, the hook exits 0 without committing. This lets a multi-phase skill stage all its writes via Edit/Write tool calls, run gates (skill-precheck, /vault audit), then land one atomic commit at the end.

Canonical lifecycle (single-skill invocation):

```
Phase A   pre-flight: ls .claude/state/auto-commit-disabled  (expects ABSENT; HALT on present)
Phase C   set:        mkdir -p .claude/state && touch .claude/state/auto-commit-disabled
Phase D-I work:       Edit/Write multiple files (PostToolUse auto-commit suppressed)
Phase J.0 gate:       skill-precheck.py / vault-audit.py --json on tmp staging
Phase J   commit:     git add ... && git commit
Phase K   clear:      rm .claude/state/auto-commit-disabled  (post-commit verification)
```

If a mid-phase Edit fails (F.halt), the flag STAYS SET. The vault is in known-recoverable state: applied edits are unstaged in working tree, no commit happened. Recovery: user inspects and either rolls back via `git checkout -- <paths>` or fixes root cause and re-invokes.

## DEVIATION pattern: F11-RE-SET-PER-INVOCATION

Named 2026-05-06 from two cascades:

**Cascade A (2026-05-04).** Sandbox-derived /retro Phase 2 micro-commit cascade. F11 was cleared after Phase 0 commit; subsequent Phase 2 Edits triggered the auto-commit hook on every Write, producing 7 micro-commits where the spec called for 2 atomic ones. No data corruption -- the vault state was correct. The DEVIATION was procedural: F11 timing didn't model "more edits coming after this commit".

**Cascade B (2026-05-05).** Real-execution cohort sweep -- 5 /ingest invocations (four cohort tickers + a retro entry) within a single user session. Each /ingest set its own F11 in Phase C and cleared in Phase K. Mechanically each ingest atom was correct. But the cascade as a whole -- 5 ingests + 1 retro = 6 commits -- was supposed to be one logical transaction. The intent ("ingest the cohort, ratify, commit once") was not representable in the single-set-per-invocation F11 model.

**Root cause.** The F11 mechanism is per-invocation by design (each skill sets, works, clears). It has no concept of cascade scope -- "I am the parent of N child skills; hold the flag across all of them". When the user invokes parent-with-children manually, the parent has no way to communicate "do not clear F11 on your phase K, child" to each child.

## Prevention rule (cascade-aware F11)

The `tools/lib/f11_orchestrator.py` Python context manager and `tools/lib/f11_orchestrator.sh` bash wrapper encode the cascade rule:

1. **`cascade_role="leaf"` (default).** Independent invocation. Set on enter; clear on exit. Collide-HALT if flag already present.
2. **`cascade_role="parent"`.** Top of a cascade. Set on enter; clear on exit. Children invoked inside this context detect the flag and skip their own set/clear.
3. **`cascade_role="child"`.** Within a cascade. Detect parent flag; do NOT set; do NOT clear; do NOT collide. If the parent flag is absent (skill invoked standalone, not under a cascade), behaves like leaf.

```python
# Parent skill cascade pattern
from tools.lib.f11_orchestrator import f11_session

with f11_session(reason="cohort-sweep-2026-05-06", cascade_role="parent") as f11:
    f11.checkpoint("phase-c")
    for ticker in cohort:
        with f11_session(reason=f"ingest-{ticker}", cascade_role="child") as inner:
            run_ingest(ticker)         # standard /ingest body
            inner.commit_boundary(f"ingest-{ticker}")
    f11.commit_boundary("retro")
# F11 cleared ONCE on parent exit; cohort cascade is one F11 window
```

## Anti-pattern detector

`python tools/lib/f11_orchestrator.py detect [--history-date YYYY-MM-DD]` walks `.claude/state/f11-history-<date>.jsonl` and surfaces:

- `set_without_clear` (open sets exceed clears + halts; orphan flag risk)
- `clear_without_set` (manual rm without prior touch; bypasses telemetry)
- `rapid_re_set` (3+ set events within a 30-minute window; the F11-RE-SET-PER-INVOCATION cascade pattern -- recommends migrating the orchestrator to `cascade_role="parent"`)

`/vault audit` should call this in Phase J as a SOFT classifier (advisory only; surfaced for awareness; zero score impact in v2.2).

## When to migrate to f11_orchestrator

Existing skills that set/clear F11 via raw `touch`/`rm` continue working unchanged -- the library is opt-in. Migrate when:

- A skill explicitly invokes another skill within its body (multi-phase orchestration). Adopt `cascade_role="parent"` on the outer; the inner is invoked under the existing flag and does not need to be aware.
- The user runs cohort sweeps manually (e.g., `/ingest <TICKER-A>` then `/ingest <TICKER-B>` then `/ingest AMZN`...). The pattern doesn't fully solve manual cohorts (the user is the orchestrator; no Python context manager wraps the session) but the anti-pattern detector surfaces the cascade in retrospect so the next /retro can name and account for it.

## Telemetry

Every F11 lifecycle event lands in `.claude/state/f11-history-<date>.jsonl` as a single JSON line:

```json
{"ts": "2026-05-06T17:30:00", "event": "set", "reason": "my-cascade", "cascade_role": "parent", "data": {"path": ".claude/state/auto-commit-disabled"}}
{"ts": "2026-05-06T17:30:01", "event": "checkpoint", "reason": "my-cascade", "cascade_role": "parent", "data": {"label": "phase-c"}}
{"ts": "2026-05-06T17:30:42", "event": "commit_boundary", "reason": "my-cascade", "cascade_role": "parent", "data": {"label": "phase-j"}}
{"ts": "2026-05-06T17:30:43", "event": "clear", "reason": "my-cascade", "cascade_role": "parent", "data": {"checkpoints": 1, "duration_sec": 43.0}}
```

Events:
- `set` (we own the flag)
- `child_join` (child detected parent flag; we do not own)
- `checkpoint` (progress marker; flag retained)
- `commit_boundary` (a commit happened; flag retained across)
- `clear` (we owned the flag; clean exit)
- `child_leave` (child exit; we never owned)
- `halt_keep_flag` (exception during context; flag stays set per F.halt convention)
- `collision` (entered with flag already set in non-child role; HALT)

Telemetry is gitignored via `.claude/state/` entry. Logs are date-rolled (`f11-history-YYYY-MM-DD.jsonl`).

## Recovery procedures

**Orphan flag (set without recent clear).** Inspect:
```
ls -la .claude/state/auto-commit-disabled
python tools/lib/f11_orchestrator.py status
```
If no skill is in-flight, manually `rm .claude/state/auto-commit-disabled` and document in retro.

**F.halt with applied edits.** The flag stayed set after an exception. Inspect git status; either `git checkout -- <paths>` to roll back applied edits OR fix the root cause and re-invoke (idempotency on most skills means re-invoke is safe). Then clear F11.

**Hook recursion (theoretical).** If a hook ever spawns `claude` directly, it would inherit the same hook chain and infinite-loop. Per `[[ref-claude-code-mastery]]` sec 4 anti-pattern, hooks must use `--settings no-hooks.json` with `disableAllHooks: true` if Claude needs to be spawned. All current hooks use pure Python or shell-only paths; no recursion possible.

## Cross-references

- `[[ref-claude-code-mastery]]` -- hook chain semantics, PostToolUse + PreToolUse contract
- `[[ref-hot-md-schema]]` -- session continuity mechanism (separate concern; not F11-aware)
- `tools/lib/f11_orchestrator.py` -- Python implementation
- `tools/lib/f11_orchestrator.sh` -- bash wrapper
- `tools/test-prevention-arch.sh` -- regression suite (T28+ for f11_orchestrator coverage; deferred to Session 1.5)

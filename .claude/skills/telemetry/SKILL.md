---
name: telemetry
description: Analyze the SubagentStart/Stop + PostToolUseFailure + PostCompact telemetry sinks at .claude/state/ via tools/telemetry_analyzer.py. Surfaces subagent-pair orphans (Stop with no paired Start), tool failure clusters by (tool_name, error_class), agent-duration outliers (p95 > p50*3), and session failure topology. Default report writes to wiki/maintenance/telemetry-<date>.md plus FOLLOWUPS:skills compact block for /retro consumption. Symmetric with /vault (wraps tools/*.py analyzer). Use after multi-skill workflows, weekly for trend digest, before /retro for FOLLOWUPS:skills enrichment, when investigating a specific failure window, or to verify the prevention architecture is producing clean subagent pairs. Test-fixture filter defaults ON; --include-test-fixtures for raw view. v2.1.147 schema-additive (reads both legacy 0.9 records and 1.0 records with agent_id/duration_ms). Codex-side N/A (telemetry hooks Claude-only per gen-codex-config.py drop list).
arguments: [mode]
argument-hint: "[--window 7|30] [--rebuild] [--include-agents-view] [--include-test-fixtures]"
allowed-tools: [Read, Write, Bash, Glob, Grep]
effort: high
user-invocable: true
---

## When to use / not

Use:
- Post-multi-skill workflow (e.g., after /invest dispatches 5+ subagents) to check for orphan stops.
- Weekly trend digest (rolls up last 7 days of failure clusters).
- Before /retro session-end ratification when telemetry signals would enrich FOLLOWUPS:skills.
- To investigate a specific failure window ("Bash 404s spiked yesterday -- what cluster?").
- After hook script changes to verify the SubagentStart/Stop pair invariant holds.

Not for:
- Server-side billing breakdown -- use Claude Code's `/usage` (v2.1.149+); separate data source.
- OTel pipeline metrics -- requires `OTEL_LOG_TOOL_DETAILS=1` and an OTel collector; not configured.
- Live session orchestration -- the analyzer is offline; use `claude agents` for live view.

Output is read-only signal extraction; never mutates the hook sinks.

## Invocation modes (Pattern 6 deterministic routing)

| Syntax | Behavior |
|---|---|
| `/telemetry` | Default; 7-day window; rebuild=false; reads cursor-incremental; writes wiki/maintenance/telemetry-<date>.md |
| `/telemetry --window 30` | 30-day window |
| `/telemetry --rebuild` | Drop SQLite + full re-ingest from JSONL (use after hook script changes) |
| `/telemetry --include-agents-view` | Poll `claude agents --json` and JOIN to events table on session_id |
| `/telemetry --include-test-fixtures` | Include synthetic test events in signals (default: filtered) |

Combined flags allowed: `/telemetry --window 30 --rebuild --include-agents-view`.

## Process

Single-mode skill. The analyzer module (tools/telemetry_analyzer.py) is the canonical computation; this skill orchestrates pre-write checks + report rendering + downstream coordination.

### Phase A -- Pre-flight

1. Parse args + flags from `$ARGUMENTS`.
2. Resolve today's ISO date via `date +%F` Bash call (canonical).
3. Resolve `OUTPUT_PATH` = `wiki/maintenance/telemetry-<today>.md`.
4. Same-day collision check: if `OUTPUT_PATH` exists, default `wiki/maintenance/telemetry-<today>-<HHMM>.md` variant (preserves archival rule per F22).
5. F11 collision check: if `.claude/state/auto-commit-disabled` exists -> HALT and report stale F11 (do not silently take over).

### Phase B -- State-transition print (BEFORE F11 set)

Emit planned reads + planned writes to stdout. User can abort via Ctrl-C before F11 is touched. Format:

    /telemetry -- planned state transition:
      reads:
        - .claude/state/subagent-telemetry-*.jsonl (cursor-incremental)
        - .claude/state/failures-*.jsonl (cursor-incremental)
        - .claude/state/telemetry.db (SQLite derived index)
      writes:
        - wiki/maintenance/telemetry-<today>[-HHMM].md (NEW report)
        - .claude/state/telemetry.db (SQLite update; gitignored)
      F11 set after this print

### Phase C -- F11 set + analyzer pre-check

1. `touch .claude/state/auto-commit-disabled` BEFORE any vault Write.
2. Bash dry-run: `python tools/telemetry_analyzer.py --json --window <N>` -- captured to a temp variable. If exit != 0 or stdout is not valid JSON -> Phase F.halt (clear F11; report; do not write report file).

### Phase D -- Ingest cursor advance

`python tools/telemetry_analyzer.py [--rebuild] --json --window <N> [--include-test-fixtures] [--include-agents-view]` -- one Bash call that:
- Advances the per-source cursor (or full rebuild if --rebuild)
- Computes all signals over the window
- Returns JSON with: `events_ingested`, `orphan_count`, `real_count`, `filtered_count`, `total_count`, `pair_summary`, `duration_by_agent_type`, `failure_rate_by_tool`, `failure_clusters`, `session_failures`, `agents_view`, `followups_block`.

### Phase E -- SQLite query batch (analyzer-internal)

Handled by the module's `analyze()`. Skill does not re-query SQLite directly.

### Phase F -- Pair classification (analyzer-internal)

Handled by `_rebuild_pairs()`. The orphan-Stop signal is the load-bearing primary surface; verify `pair_summary.orphan_stop` is in the returned JSON before proceeding.

### Phase G -- Duration outliers (analyzer-internal)

Handled by `_compute_duration_outliers()`. Outlier rule: p95 > p50 * 3.

### Phase H -- Failure rate per tool (analyzer-internal)

Handled by `_compute_failure_rate()`. Reports count + per-day; total invocation count not available (no tool-success telemetry).

### Phase I -- Failure clustering (analyzer-internal)

Handled by `_compute_failure_clusters()`. Top-10 by count.

### Phase J -- Session failure topology (analyzer-internal)

Handled by `_compute_session_failures()`. Threshold: 3 failures and zero clean SubagentStop pairs.

### Phase K -- Write markdown report

Single Write to `OUTPUT_PATH`. The analyzer's `render_markdown()` produces ASCII-clean content (Pattern 22).

Direct Bash call to render the file (alternative to in-memory render + Write tool):

    python tools/telemetry_analyzer.py --window <N> --markdown "wiki/maintenance/telemetry-<today>[-HHMM].md"

This single-call shape is preferred (no intermediate Python staging).

### Phase L -- Render FOLLOWUPS:skills block

The analyzer's `render_followups_block()` emits a compact 1-line summary. The /retro skill consumes this via:

    python tools/telemetry_analyzer.py --followups-block

Threshold rules (any trigger surfaces output):
- orphan_count >= 1
- top failure cluster count >= 3
- any agent_type with p95 > p50 * 3

When NO trigger fires: emits `[telemetry] no signals above threshold in window` (audit trail; not noise).

### Phase M -- Cross-reference back-link audit

`/telemetry` writes to `wiki/maintenance/` (EXEMPT_PATH_PREFIX); no symmetric back-link enforcement required. The report's `related:` field includes `[[hot]]` and `[[knowledge-moc]]` for navigation.

### Phase N -- ASCII Pattern 22 byte-scan

Pre-commit guard: run a Python byte-scan against the rendered markdown. The analyzer module emits only ASCII characters by construction (no em-dash, curly quotes, ellipsis, arrows). Defensive Bash:

    python -c "
    import sys
    p = sys.argv[1]
    data = open(p, encoding='utf-8').read()
    bad = [c for c in data if ord(c) > 127]
    print(f'NON-ASCII chars: {len(bad)}' if bad else 'ASCII-CLEAN')
    sys.exit(0 if not bad else 2)
    " "wiki/maintenance/telemetry-<today>[-HHMM].md"

### Phase O -- Pre-commit /vault audit gate (CAT-3 parity)

Run `python tools/vault-audit.py --json` and require `tiers.gate.count == 0` AND `score >= 95`. Fail-on-GATE: clear F11, report, no commit.

### Phase O.0 -- Gate result classification

Per the prevention architecture:
- GATE present -> HALT, do not commit, report finding paths.
- HARD DRIFT only -> proceed (HARD DRIFT is capped at -5, vault stays at floor or above).
- SOFT DRIFT only -> proceed (advisory).

### Phase P -- Atomic commit + F11 clear

1. `git add wiki/maintenance/telemetry-<today>[-HHMM].md` (narrow stage; F14).
2. `git commit -m "telemetry: <today> -- <orphan_count> orphans / <cluster_count> failure clusters"` (no Co-Authored-By; F17).
3. `rm .claude/state/auto-commit-disabled` (F11 clear).
4. Print one-line summary + analyzer FOLLOWUPS block to stdout for /retro coordination.

## Pre-Output HALT gate

Before final stdout summary, verify:

1. `OUTPUT_PATH` exists and is non-empty.
2. ASCII byte-scan passes.
3. Vault-audit shows score >= 95 AND tiers.gate.count == 0.
4. F11 file removed.
5. Single commit landed (verify via `git log -1 --format=%s | grep "^telemetry:"`).
6. Report header line `Test fixtures filtered: N records / Real records: M / Total: N+M` present (R11 truthful-reporting requirement).
7. FOLLOWUPS:skills section in body (consumed by /retro).
8. No subagent dispatches (this skill is direct-Bash; no Agent calls).
9. No new wikilinks introduced outside body code fences (validator-blocked at write time).
10. `pair_summary.orphan_stop` value reported (load-bearing primary signal).

If any check fails: HALT, report which check, do not emit success summary.

## Coordination contracts

- **/retro** reads `render_followups_block()` output via Bash:
      python tools/telemetry_analyzer.py --followups-block
  /retro pipes this into its FOLLOWUPS:skills extraction phase. Threshold rules same as Phase L.

- **/brief** does NOT read telemetry by default; if telemetry signals are critical for the day's briefing, the user explicitly invokes `/telemetry` before `/brief`.

- **/vault repair** uses `/goal` (B1) to iterate fix-verify cycles. The /goal condition string requires a Bash `tool_result` block paired by `tool_use_id` to a `python tools/vault-audit.py --json` invocation; the analyzer can later detect /goal loops in transcript and surface "vault repair required N iterations" as an enrichment signal (B3 / future).

- **/ingest, /enrich** are not coordinated with /telemetry (different surfaces).


- **claudewatch** (live counterpart): /telemetry is post-hoc (reads .claude/state sinks for what already failed); claudewatch is the live, mid-session layer (read-only MCP tools over ~/.claude transcripts -- get_drift_signal, get_session_dashboard). Complementary surfaces, not a replacement. See tools/INSTALL-CLAUDEWATCH.md.

## Failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| `pair_summary.orphan_stop` keeps rising | Subagent dispatches crashing or SubagentStop hook not firing | Inspect `.claude/transcripts/` for the affected `session_id`; check `subagent-active-*.tmp` markers; re-run `--rebuild` |
| Failure clusters all show `(empty)::(empty)` | Hook is emitting empty fields | Inspect `.claude/state/failures-<date>.jsonl` raw lines; verify post-tool-use-failure.py payload reads |
| `real_count == 0` with non-zero `total_count` | All records caught by test-fixture filter | Use `--include-test-fixtures` for raw view; refine fixture rules in tools/telemetry_analyzer.py if false-positive observed |
| SQLite locked errors | Concurrent analyzer invocations | Wait + retry; analyzer holds connection only during `__enter__`/`__exit__` block |
| `claude agents --json` returns empty | Agent View not enabled or no live agents | Optional; analyzer continues without snapshot |

## Output schema (report markdown)

The analyzer module's `render_markdown()` produces this canonical structure (do not deviate; downstream parsers anchor on these headers):

1. Frontmatter (categories: wiki, type: report, status: complete, ASCII-only)
2. H1: `# Telemetry Report -- <date>`
3. Provenance block: generated_at, window, fixture-filter line
4. `## Subagent Pair Health` (paired/orphan_stop/hanging_start counts + orphan examples)
5. `## Agent Duration Outliers` (table per agent_type)
6. `## Tool Failure Surface` (table per tool_name)
7. `## Failure Clusters (top 10)` (table)
8. `## Session Failure Topology` (table; sessions with >=3 failures + zero clean pairs)
9. `## FOLLOWUPS:skills` (compact 1-line block consumed by /retro)

## meta.json sidecar (optional, future)

Reserved for cross-run calibration. Not emitted in v1. The SQLite database already provides historical state; sidecar adds redundancy without leverage at current scale.

## ASCII Pattern 22 discipline

All new content written by this skill is ASCII-clean by construction (analyzer renders ASCII-only). Bash byte-scan verifies pre-commit. No em-dash, curly quotes, ellipsis, arrow glyphs, or other UTF-8 > 127 characters.

## Codex-side compatibility

The telemetry hooks (SubagentStart, SubagentStop, PostToolUseFailure, PostCompact) are Claude-only per `tools/gen-codex-config.py` DROPPED_EVENTS set. A Codex session invoking `/telemetry` will read an empty `.claude/state/` archive (no Codex-side equivalent sinks exist). The skill reports `real_count: 0 / filtered: 0 / total: 0` and exits cleanly. This is a documented telemetry gap, not a regression. Revisit if Codex publishes equivalent events (see `docs/CODEX-COMPATIBILITY.md` section 4).

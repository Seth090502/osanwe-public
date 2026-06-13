---
name: consolidate
description: Consolidate the vault's accreted operational record into durable playbooks. Mines sessions-log + decision-log + daily notes + retros (methodology learnings) + telemetry sinks for recurring patterns above tuned thresholds (decision tag >=3, telemetry failure cluster >=5, retro theme >=3, skill failure_rate >=30%), renders wiki/playbooks/<topic>-playbook.md (## Pattern / ## Evidence / ## Recommendation / ## Related), and inserts a compact dated <4KB digest into wiki/hot.md (sha256-preserved). Turns episodic session memory into reusable doctrine. Wraps tools/consolidator.py (single source of computation). Use after a run of substantive sessions has accumulated, before a quarterly doctrine review, when /retro follow-ups keep re-surfacing the same theme, or when the decision-log has grown enough that domain patterns are worth codifying. Symmetric with /telemetry (both wrap a tools/*.py analyzer; both write to a dated artifact + hot.md). Modes: default (write playbooks), --dry-run (compute + preview, no writes), --since <date>, --max-playbooks <N>. Codex-side: reads the same markdown sources; telemetry sinks are Claude-only (empty Codex-side) so skill/agent failure-rate patterns degrade gracefully to zero there.
arguments: [mode]
argument-hint: "[--since YYYY-MM-DD] [--max-playbooks N] [--dry-run]"
allowed-tools: [Read, Bash, Edit, Write]
effort: high
user-invocable: true
---

## When to use / not

Use:
- After a run of substantive sessions (10+ /retro entries) has accumulated, to promote scattered methodology learnings into durable playbooks.
- Before a quarterly or chapter-close doctrine review.
- When /retro follow-ups keep re-surfacing the same theme across sessions (the theme threshold will catch it).
- When the decision-log has grown enough that per-domain decision clusters warrant codification.
- After /telemetry surfaces a persistent failure cluster -- /consolidate folds it into a fix playbook.

Not for:
- A single session retrospective -- that is /retro.
- Live telemetry signal extraction -- that is /telemetry.
- Onboarding a new external document -- that is /enrich or /ingest.

Output is additive doctrine; it never rewrites the source records (append-only respected).

## Invocation modes (Pattern 6 deterministic routing)

| Syntax | Behavior |
|---|---|
| `/consolidate` | Default; 30-day window; writes wiki/playbooks/*.md + hot.md digest |
| `/consolidate --since 2026-04-01` | Explicit window start (ISO date) |
| `/consolidate --max-playbooks 8` | Cap on playbooks written (default 8) |
| `/consolidate --dry-run` | Compute + print pattern list and digest; write nothing |

Combined flags allowed: `/consolidate --since 2026-04-01 --max-playbooks 8`.

## Process

Single-mode skill. The analyzer module (tools/consolidator.py) is the canonical computation; this skill orchestrates pre-write checks + playbook write + hot.md digest insertion + downstream coordination. 16-phase A-P arc matching /telemetry precedent.

### Phase A -- Pre-flight

1. Parse args + flags from `$ARGUMENTS`. Resolve `SINCE` (default: 30 days ago via `date -d '30 days ago' +%F`), `MAX` (default 8).
2. Resolve today's ISO date via `date +%F`.
3. `PLAYBOOK_DIR` = `wiki/playbooks/` (consolidator creates it if absent).
4. F11 collision check: if `.claude/state/auto-commit-disabled` exists -> HALT and report stale F11 (do not silently take over).

### Phase B -- State-transition print (BEFORE F11 set)

Emit planned reads + planned writes to stdout. User can abort via Ctrl-C before F11 is touched.

    /consolidate -- planned state transition:
      reads:
        - Calendar/decisions/sessions-log.md
        - Calendar/decisions/decision-log.md
        - Calendar/daily/*.md
        - .claude/state/{subagent-telemetry,failures}-*.jsonl
      writes:
        - wiki/playbooks/<topic>-playbook.md (3-8 NEW playbooks)
        - wiki/hot.md (digest insertion; sha256-preserved elsewhere)
      F11 set after this print

### Phase C -- F11 set + consolidator dry-run pre-check

1. `touch .claude/state/auto-commit-disabled` BEFORE any vault Write.
2. Bash dry-run: `python tools/consolidator.py --since <SINCE> --max-playbooks <MAX> --dry-run`. If exit != 0 -> Phase F.halt (clear F11; report; no writes).
3. Inspect the printed pattern list. If zero patterns -> HALT (empty-consolidation safeguard; no commit, no noise). If 1-2 patterns, proceed but note the thin yield.

### Phase D -- Ingest (analyzer-internal)

Handled by the module's `ingest_sessions / ingest_decisions / ingest_daily_notes / ingest_retros / ingest_telemetry`. The skill does not parse the sources directly.

### Phase E -- Pattern identification (analyzer-internal)

Handled by `identify_patterns()`. Verify the dry-run printed the four pattern types where present: decision_tag, telemetry_cluster, retro_theme, skill_failure_rate.

### Phase F -- Threshold application (analyzer-internal)

Thresholds (module constants): decision tag >= 3 decisions in a domain; telemetry failure cluster >= 5; retro theme >= 3 distinct sessions; skill/agent failure_rate >= 0.30 (min 3 events). Sub-threshold candidates are correctly dropped.

### Phase G -- Ranking + cap (analyzer-internal)

Patterns ranked telemetry_cluster -> skill_failure_rate -> decision_tag -> retro_theme, then by count desc; capped at `--max-playbooks`.

### Phase H -- Playbook render (analyzer-internal)

`render_playbook()` emits canonical frontmatter (categories: [wiki], type: synthesis, status: active, ISO dates, topic/* tags, related: [[hot]]) + ## Pattern / ## Evidence / ## Recommendation / ## Related. ASCII-clean by construction.

### Phase I -- hot.md digest render (analyzer-internal)

`render_hot_md_digest()` emits a dated `### Consolidation Digest -- <date>` block listing each playbook as `[[<stem>-playbook]]` (matching the written file stem so the link resolves), under the `DIGEST_MAX_BYTES` (4096) budget.

### Phase J -- Write playbooks (the mutation)

Single Bash call: `python tools/consolidator.py --since <SINCE> --max-playbooks <MAX>`. The consolidator writes the playbook files directly (Python writes; no per-file hook fires) and prints the digest between `=== HOT_MD_DIGEST_BEGIN ===` / `=== HOT_MD_DIGEST_END ===` markers. Capture the digest from stdout.

### Phase K -- hot.md digest insertion (Edit; sha256-preserve)

Read `wiki/hot.md`; insert the captured digest as content under the `## Active Context` header (or append a `## Consolidation Digest` block if Active Context is unsuitable) via a single Edit. Everything outside the insertion site stays byte-exact. Use plain bullets/links (no `- [ ]` checkboxes) so Pending Items lifecycle counts are untouched. The digest's `[[<stem>-playbook]]` links now resolve (files written in Phase J).

### Phase L -- Orphan closure (back-link audit)

The hot.md digest provides the inbound wikilink to every playbook, so the orphan classifier sees no orphans. Each playbook's `related: [[hot]]` plus its ## Related sibling links close the graph symmetrically. If `wiki/knowledge-moc.md` exists, optionally add the digest link there too.

### Phase M -- Cross-reference back-link audit

Verify each written playbook stem appears in the hot.md digest exactly once. Verify no playbook links to a non-existent sibling stem.

### Phase N -- ASCII Pattern 22 byte-scan

The consolidator renders ASCII-only by construction. Defensive Bash byte-scan over the playbook dir + hot.md before commit:

    python -c "
    import sys, glob
    bad = 0
    for p in glob.glob('wiki/playbooks/*.md') + ['wiki/hot.md']:
        d = open(p, encoding='utf-8').read()
        bad += sum(1 for c in d if ord(c) > 127)
    print('ASCII-CLEAN' if bad == 0 else f'NON-ASCII: {bad}')
    sys.exit(0 if bad == 0 else 2)
    "

(hot.md may legitimately carry pre-existing non-ASCII outside the digest; scope the scan to the digest block if so.)

### Phase O -- Pre-commit /vault audit gate (CAT-3 parity)

Run `python tools/vault-audit.py --json` and require `tiers.gate.count == 0` AND `score >= 95`. Fail-on-GATE: clear F11, report finding paths, no commit, roll back the playbook writes if a GATE was introduced.

### Phase O.0 -- Gate result classification

- GATE present -> HALT, do not commit, report + roll back.
- HARD DRIFT only -> proceed (capped at -5; floor preserved). Orphans should be zero because the digest back-links every playbook.
- SOFT DRIFT only -> proceed (advisory).

### Phase P -- Atomic commit + F11 clear

1. `git add wiki/playbooks/ wiki/hot.md` (narrow stage; F14).
2. `git commit -m "consolidate: <date> -- <N> playbooks (<decision/theme/cluster mix>)"` (no Co-Authored-By; F17).
3. `rm .claude/state/auto-commit-disabled` (F11 clear).
4. Print one-line summary + the digest to stdout.

## Pre-Output HALT gate

Before final stdout summary, verify:

1. wiki/playbooks/ contains the rendered files (count matches the printed pattern count).
2. Each playbook has all four sections (## Pattern / ## Evidence / ## Recommendation / ## Related) + valid frontmatter.
3. hot.md digest inserted, dated, <4KB, every link resolves to a written playbook stem.
4. ASCII byte-scan passes on new content.
5. Vault-audit shows score >= 95 AND tiers.gate.count == 0.
6. F11 file removed.
7. Single commit landed (`git log -1 --format=%s | grep "^consolidate:"`).
8. No subagent dispatches (this skill is direct-Bash + Edit; no Agent calls).

If any check fails: HALT, report which check, do not emit success summary.

## Coordination contracts

- **[[retro]]** writes the sessions-log methodology-learnings + decision-log rows that this skill mines. /consolidate is the periodic roll-up that /retro feeds; run /consolidate after a batch of /retro sessions.
- **[[telemetry]]** surfaces live failure clusters; /consolidate folds persistent clusters (>=5) and high subagent failure-rates (>=30%) into durable fix playbooks. Run /telemetry first if you want fresh telemetry signals folded in.
- **[[hot]]** receives the compact dated digest so the next session sees the consolidated doctrine at SessionStart.
- /challenge can be run on any decision surfaced in a decision_tag playbook whose confidence has drifted.

## Failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| Zero patterns identified | Window too narrow or thresholds not met | Widen `--since`; confirm sessions-log/decision-log have rows in window |
| Playbook topics look generic | Theme tokenizer surfacing weak tokens | Tune STOPWORDS in tools/consolidator.py; raise RETRO_THEME_MIN |
| hot.md digest link broken in audit | Digest stem != playbook file stem | Confirm digest uses `[[<slug>-playbook]]`; re-run Phase J then K |
| Vault-audit orphan HARD DRIFT on playbooks | Digest insertion skipped or reverted | Re-insert digest into hot.md (Phase K); orphans clear |
| F11 stale at Phase A | Prior skill left the flag | Investigate the prior skill; do not silently take over |

## Output schema (playbook markdown)

Each `wiki/playbooks/<topic>-playbook.md`:

1. Canonical frontmatter (categories: [wiki], type: synthesis, status: active, ISO dates, topic/consolidation + topic/playbook tags, related: [[hot]]).
2. H1: `# <Title> Playbook`.
3. `## Pattern` -- prose describing the recurring pattern and why it is durable doctrine.
4. `## Evidence` -- bullet list of dated evidence + the threshold cleared.
5. `## Recommendation` -- concrete next action (codify / fix / consolidate).
6. `## Related` -- [[hot]] + up to 3 sibling playbook links.

## ASCII Pattern 22 discipline

All new content is ASCII-clean by construction (consolidator renders ASCII only; an `_ascii()` coercion guards evidence snippets). Bash byte-scan verifies pre-commit. No em-dash, curly quotes, ellipsis, or arrow glyphs.

## Codex-side compatibility

The markdown sources (sessions-log, decision-log, daily notes) are engine-neutral and read identically under Codex. The telemetry sinks (subagent-telemetry, failures JSONL) are Claude-only per `tools/gen-codex-config.py` DROPPED_EVENTS, so under Codex the telemetry_cluster and skill_failure_rate pattern types degrade gracefully to zero (decision_tag + retro_theme still fire). This is a documented telemetry gap, not a regression. The skill is mirrored to `.agents/skills/consolidate/SKILL.md` by `tools/sync-skills.py` (allowed-tools stripped).

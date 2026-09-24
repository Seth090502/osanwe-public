- Before a quarterly or chapter-close doctrine review.
- When /retro follow-ups keep re-surfacing the same theme across sessions (the theme threshold will catch it).
- When the decision-log has grown enough that per-domain decision clusters warrant codification.
- After the telemetry mode surfaces a persistent failure cluster -- the default mode folds it into a fix playbook.
- When hook-sink signals need analysis (orphan subagent pairs, failure clusters, duration outliers) -- `/consolidate telemetry` (formerly /telemetry).

Not for:
- A single session retrospective -- that is /retro.
- Live MID-SESSION observability -- that is claudewatch (MCP); the telemetry mode here is post-hoc over .claude/state sinks.
- Onboarding a new external document -- that is /enrich or /ingest.

Output is additive doctrine; it never rewrites the source records (append-only respected).

### Mode routing (Pattern 6 deterministic; invocation modes)

| Syntax | Behavior |
|---|---|
| `/consolidate` | Default; 30-day window; mines + writes scaffolds + MODEL-AUTHORS wiki/playbooks/*.md + hot.md digest |
| `/consolidate refresh` | v2: re-author EXISTING stub playbooks in place (detected by the generic template sentence or missing ## Apply-when); no new mining; maintained-in-place (created: kept, updated: bumped) |
| `/consolidate topic <slug>` | v2: single named theme (the /spark FOLLOWUPS handoff); evidence gathered by targeted Grep over sessions-log/decision-log/daily notes + spark reports naming it; must clear the same >=3 dated-evidence bar or HALT (no thin playbooks) |
| `/consolidate <bare-word>` | Router hardening (red-team 2026-07-09): a bare non-flag positional that is not `refresh`/`telemetry` routes to `topic <bare-word>` -- never silently falls through to default mining |
| `/consolidate --since 2026-04-01` | Explicit window start (ISO date) |
| `/consolidate --max-playbooks 8` | Cap on playbooks written (default 8) |
| `/consolidate --dry-run` | Compute + print pattern list and digest; write nothing (no authoring pass) |
| `/consolidate telemetry [--window N] [--rebuild]` | Telemetry mode (formerly /telemetry): hook-sink analysis via tools/telemetry_analyzer.py; writes wiki/maintenance/telemetry-`<today>`.md |

Combined flags allowed: `/consolidate --since 2026-04-01 --max-playbooks 8`.

## Process

Two modes. DEFAULT mode: the analyzer module (tools/consolidator.py) is the canonical computation; this skill orchestrates pre-write checks + playbook write + hot.md digest insertion + downstream coordination. 16-phase A-P arc matching /telemetry precedent.

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
        - wiki/playbooks/`<topic>`-playbook.md (3-8 NEW playbooks)
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

`render_playbook()` emits canonical frontmatter (categories: [wiki], type: synthesis, status: active, ISO dates, topic/* tags, related: *hot* (not published)) + ## Pattern / ## Evidence / ## Recommendation / ## Related. ASCII-clean by construction.

### Phase I -- hot.md digest render (analyzer-internal)

`render_hot_md_digest()` emits a dated `### Consolidation Digest -- <date>` block listing each playbook as `[[<stem>-playbook]]` (matching the written file stem so the link resolves), under the `DIGEST_MAX_BYTES` (4096) budget.

### Phase J -- Scaffold write (the miner's mutation)

Single Bash call: `python tools/consolidator.py --since <SINCE> --max-playbooks <MAX>`. The consolidator writes SCAFFOLD playbook files directly (Python writes; no per-file hook fires) -- canonical frontmatter + mined ## Evidence rows + the generic template ## Pattern / ## Recommendation prose -- and prints the digest between `=== HOT_MD_DIGEST_BEGIN ===` / `=== HOT_MD_DIGEST_END ===` markers. Capture the digest from stdout AND the written-file list. A scaffold is NOT a shippable playbook; Phase J2 is mandatory.

### Phase J2 -- Authoring pass (playbook-author dispatch or inline; v2, the actual synthesis)

**The authoring pass itself is MANDATORY** (spark E.0 discipline) -- only its mechanism is harness-conditional. When the harness exposes an Agent tool, dispatch one `playbook-author` subagent per playbook written in Phase J (and per stub selected in `refresh` mode) in parallel waves, fan-out <= 6 (the agent definition pins model opus -- NEVER above the opus subagent ceiling; cost directive 2026-07-09). When the harness exposes NO Agent tool, the main loop executes the inline fallback below as its NORMAL path, reported as `mode: inline (no Agent tool)` -- not a DEVIATION. Skipping the authoring pass where an Agent tool DOES exist remains a DEVIATION. Input per dispatch: `{playbook_path, mode: scaffold|stub|topic, evidence_rows: [<mined ## Evidence bullets verbatim>], occurrence_rows, topic_hint}`.

**Inline fallback (verbatim; the same 6-step authoring the subagent performs, run by the main loop for one playbook at a time):**

1. Read the scaffold at `playbook_path`; take its mined `## Evidence` rows (plus `occurrence_rows` when supplied) as the ONLY entry points.
2. Follow >= 3 of those rows to their SOURCE artifacts via Read/Grep -- decision-log entries, sessions-log methodology learnings, telemetry cluster rows in `.claude/state/*.jsonl`, daily-note lines. Authoring from scaffold bullet text alone is FORBIDDEN; if the sources cannot be opened, return `sources_unreachable` and HALT that playbook (parent-side handling item 1).
3. Derive the `## Pattern` opening: ONE falsifiable `Invariant:` sentence naming the shared rule the sources actually support (a threshold restatement is not an invariant).
4. Hunt `## Counter-cases`: 1-3 dated in-corpus instances that strain or bound the invariant, each with a vault path; or the honest `(none found -- searched <what>)` line naming what was searched.
5. Compose `## Recommendation`: a concrete action naming its on-disk target (a ref-doc to amend, a skill phase to bind, a gate id or trigger to add, a ledger) or a /decide slug to create -- never advice-shaped prose.
6. Compose `## Apply-when`: the 1-2 line trigger condition a future session can check in under 30 seconds. Report calibrated % confidence + the resolved-source list alongside the sections.

**Telemetry-pattern evidence enrichment (red-team 2026-07-09; SEV1 fix):** telemetry_cluster and skill_failure_rate scaffolds carry ONE undated evidence row pointing at no vault artifact -- unauthorable as-is (the dominant corpus case: a default run today ranks all-telemetry top-8 and would ship nothing). For those two pattern types the PARENT extracts >= 3 dated occurrence rows from the sinks BEFORE the authoring pass -- `grep` the cluster key in `.claude/state/failures-*.jsonl` (telemetry_cluster) or `.claude/state/subagent-telemetry-*.jsonl` (skill_failure_rate), take >= 3 dated lines as `{date, file:line, one-line summary}` -- and passes them as `occurrence_rows`. The author resolves THOSE as its sources. Fewer than 3 occurrences extractable -> skip that scaffold pre-dispatch (delete it; report `unauthorable: <slug> (<n> occurrences)`) so the authoring wave is never spent on it. decision_tag/retro_theme patterns pass `occurrence_rows: null` (their mined rows already cite dated vault artifacts).

Each author (subagent or inline) returns the sections per the playbook-author return contract: `## Pattern` opening with one falsifiable `Invariant:` sentence, `## Counter-cases` (dated strains with paths, or an honest none-found line), `## Recommendation` (concrete action naming an on-disk target or a /decide slug), `## Apply-when` (a <30s-checkable trigger condition), plus calibrated % confidence and the resolved-source list.

Parent-side handling:
1. `sources_unreachable` return -> HALT that playbook. If the scaffold is NEWLY created this run (path did NOT exist at git HEAD): delete it. If the path EXISTED at HEAD (re-mined slug clobbering prior content): `git checkout -- <path>` to restore, NEVER delete (red-team 2026-07-09 clobber guard). A stub in refresh mode stays a stub, reported. Thin doctrine never ships.
1b. CLOBBER GUARD (Phase J overwrite): any Phase-J-written path that existed at HEAD had its `created:` reset by the miner -- restore the HEAD `created:` value during the J2 Edit (the miner is append-blind; the parent is not).
2. Contract violation (anti-pattern present, missing section, non-ASCII) -> ONE re-dispatch -> inline fallback: the main loop performs the same 6-step authoring itself for that playbook only. Pre-emptive skip of an available dispatch = DEVIATION, surfaced in the final summary.
3. Valid return -> parent applies the sections via Edit over the scaffold (hooks fire). Body-preservation: frontmatter + mined ## Evidence rows + ## Related stay byte-exact; only ## Pattern / ## Counter-cases / ## Recommendation / ## Apply-when mutate; `updated:` bumps.

The mined ## Evidence rows are NEVER edited (deterministic layer's territory); the prose is the author's territory. That division is the design: the script computes WHAT recurred, the author derives WHY it matters and WHAT to do -- from the sources, never the summaries.

### Phase K -- hot.md digest insertion (Edit; sha256-preserve)

Read `wiki/hot.md`; insert the captured digest as content under the `## Active Context` header (or append a `## Consolidation Digest` block if Active Context is unsuitable) via a single Edit. Everything outside the insertion site stays byte-exact. Use plain bullets/links (no `- [ ]` checkboxes) so Pending Items lifecycle counts are untouched. The digest's `[[<stem>-playbook]]` links now resolve (files written in Phase J).

### Phase L -- Orphan closure (back-link audit)

The hot.md digest provides the inbound wikilink to every playbook, so the orphan classifier sees no orphans. Each playbook's `related: [[hot]]` plus its ## Related sibling links close the graph symmetrically. If `Atlas/_MOCs/knowledge-moc.md` exists, optionally surface the digest link for the user to add there -- Atlas is human-write-only, so never write it autonomously.

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

### Quality Rules (v2 authoring bars)

- A playbook that could have been written without reading the source artifacts is a FAILED playbook. The invariant lives in the sources, not the mined summaries.
- `## Pattern` MUST open with one falsifiable sentence prefixed `Invariant:`. A threshold restatement is not an invariant.
- `## Counter-cases` is REQUIRED -- dated in-corpus strains with paths, or the honest `(none found -- searched <what>)` line. Doctrine without its boundary conditions is marketing.
- `## Recommendation` MUST name a concrete target that exists on disk (ref-doc path, skill phase, gate id, ledger) or a /decide slug to create. Never advice-shaped prose.
- `## Apply-when` MUST be checkable by a future session in under 30 seconds.
- Anti-stub HALT: ANY of the four consolidator.py render-template generic sentences in a shipped playbook (red-team 2026-07-09 -- one literal covered only 1 of 4 pattern types): "Review the listed decisions for a shared invariant" (decision_tag), "Inspect the raw failure records for this cluster" (telemetry_cluster), "Inspect transcripts for this subagent type" (skill_failure_rate), "Consolidate the scattered mentions into the relevant ref-doc" (retro_theme/default).
- Authoring legs run opus-pinned via the playbook-author definition wherever the harness exposes an Agent tool; never dispatch authoring to a frontier-tier model (cost directive 2026-07-09). No harness conditions authoring QUALITY on model identity -- the inline fallback clears the same six bars.

### Pre-Output HALT gate

MODE SCOPING (red-team 2026-07-09): items 1-3 and 8-10 apply to modes that ship playbooks (default, topic); in `refresh` mode item 1 compares against the on-disk stub set selected (no miner ran); items 6-7 are skipped under `--dry-run` (nothing written); `telemetry` mode is governed by its own section below, not this gate.

Before final stdout summary, verify:

1. Shipped-playbook tally reconciles: written = printed pattern count MINUS pre-dispatch unauthorable skips MINUS halted-unreachable (each named in the summary); refresh mode: re-authored count = selected stub count minus reported stays.
2. Each playbook has all SIX sections (## Pattern / ## Evidence / ## Counter-cases / ## Recommendation / ## Apply-when / ## Related) + valid frontmatter.
3. hot.md digest inserted, dated, <4KB, every link resolves to a written playbook stem.
4. ASCII byte-scan passes on new content.
5. Vault-audit shows score >= 95 AND tiers.gate.count == 0.
6. F11 file removed.
7. Single commit landed (`git log -1 --format=%s | grep "^consolidate:"`).
8. Anti-stub: no shipped playbook contains the generic template sentence (literal grep).
9. Authored-delta: every playbook shipped this run differs from its script-rendered scaffold in the four authored sections (a raw scaffold shipping = HALT).
10. Every ## Pattern opens with `Invariant:`; every ## Recommendation names its target; authoring tally reported (authored / re-dispatched / inline-fallback / no-Agent-tool inline / halted-unreachable; pre-emptive skips = DEVIATION).

If any check fails: HALT, report which check, do not emit success summary.

## Coordination contracts

- **/spark** emits `/consolidate topic <topic>` FOLLOWUPS rows when a spark is PERSISTED across >= 2 consecutive continuity audits (emitter aligned 2026-07-09); `topic <slug>` mode is the receiving end, and the bare-positional router hardening catches any legacy-form row. /spark's Phase F novelty filter dedups against the playbooks this skill maintains -- authored playbooks (not stubs) are what make that dedup meaningful.
- ***retro* (not published)** writes the sessions-log methodology-learnings + decision-log rows that this skill mines. /consolidate is the periodic roll-up that /retro feeds; run /consolidate after a batch of /retro sessions.
- **telemetry mode** (formerly the standalone /telemetry skill, merged 2026-07-06) surfaces failure clusters; the default mode folds persistent clusters (>=5) and high subagent failure-rates (>=30%) into durable fix playbooks. Run `/consolidate telemetry` first if you want fresh telemetry signals folded in.
- ***hot* (not published)** receives the compact dated digest so the next session sees the consolidated doctrine at SessionStart.
- /challenge can be run on any decision surfaced in a decision_tag playbook whose confidence has drifted.

## Telemetry mode (formerly /telemetry; merged 2026-07-06)

`/consolidate telemetry [--window N (default 14)] [--rebuild] [--include-test-fixtures] [--include-agents-view]`

Thin wrapper over `tools/telemetry_analyzer.py` (single source of computation; the retired skill's full phase spec is archived at `.claude/skills/_archive/telemetry/SKILL.md`). Procedure:

1. F11 collision check, then `touch .claude/state/auto-commit-disabled` BEFORE any vault write.
2. Dry-run gate: `python tools/telemetry_analyzer.py --json --window <N>` -- exit != 0 or non-JSON stdout -> HALT (clear F11, no report write).
3. Report: `python tools/telemetry_analyzer.py --window <N> [--rebuild] --markdown "wiki/maintenance/telemetry-<today>[-HHMM].md"` (single-call shape; ASCII-clean per Pattern 22). Verify `pair_summary.orphan_stop` present in the JSON -- the orphan-Stop signal is the load-bearing surface.
4. Peripherals: daily-note Sessions Run line; hot.md digest only when findings are material. Commit per write discipline; clear F11 after post-commit verification.
5. /retro continues to consume `python tools/telemetry_analyzer.py --followups-block` directly (script call, unaffected by the skill merge).

Codex-side degradation: telemetry sinks are Claude-only (empty on Codex) -- the mode degrades gracefully to a zero-signal report there, same as the default mode's telemetry-derived patterns.

## Failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| Zero patterns identified | Window too narrow or thresholds not met | Widen `--since`; confirm sessions-log/decision-log have rows in window |
| Playbook topics look generic | Theme tokenizer surfacing weak tokens | Tune STOPWORDS in tools/consolidator.py; raise RETRO_THEME_MIN |
| playbook-author returns sources_unreachable | Evidence rows point at entries outside the corpus or reworded beyond grep reach | HALT that playbook (delete fresh scaffold); widen the grep tokens or fix the evidence row upstream; never author from bullet text |
| Anti-stub HALT at gate item 8/9 | Authoring pass skipped or scaffold shipped raw | Run Phase J2 for the flagged playbook; a raw scaffold never ships |
| Subagent contract violation twice | Return missing sections / generic prose / non-ASCII | Inline fallback for that playbook only; log DEVIATION if dispatch was pre-emptively skipped |
| No Agent tool in the harness | Non-dispatching harness | Run the Phase J2 inline fallback as the normal path; report `mode: inline (no Agent tool)` |
| hot.md digest link broken in audit | Digest stem != playbook file stem | Confirm digest uses `[[<slug>-playbook]]`; re-run Phase J then K |
| Vault-audit orphan HARD DRIFT on playbooks | Digest insertion skipped or reverted | Re-insert digest into hot.md (Phase K); orphans clear |
| F11 stale at Phase A | Prior skill left the flag | Investigate the prior skill; do not silently take over |

## Output schema (playbook markdown)

Each `wiki/playbooks/<topic>-playbook.md`:

1. Canonical frontmatter (categories: [wiki], type: synthesis, status: active, ISO dates, topic/consolidation + topic/playbook tags, related: *hot* (not published)).
2. H1: `# <Title> Playbook`.
3. `## Pattern` -- opens with one falsifiable `Invariant:` sentence naming the recurring rule the sources support.
4. `## Evidence` -- bullet list of dated evidence + the threshold cleared.
5. `## Counter-cases` -- dated in-corpus strains with paths, or an honest `(none found -- searched <what>)` line.
6. `## Recommendation` -- concrete next action naming an on-disk target (ref-doc / skill phase / gate id / ledger) or a /decide slug.
7. `## Apply-when` -- a trigger condition a future session can check in under 30 seconds.
8. `## Related` -- *hot* (not published) + up to 3 sibling playbook links.

## ASCII Pattern 22 discipline

All new content is ASCII-clean by construction (consolidator renders ASCII only; an `_ascii()` coercion guards evidence snippets). Bash byte-scan verifies pre-commit. No em-dash, curly quotes, ellipsis, or arrow glyphs.

## Codex-side compatibility

The markdown sources (sessions-log, decision-log, daily notes) are harness-neutral and read identically everywhere. The telemetry sinks (subagent-telemetry, failures JSONL) are emitted by Claude Code hooks only, so under any other harness the telemetry_cluster and skill_failure_rate pattern types degrade gracefully to zero (decision_tag + retro_theme still fire). This is a documented telemetry gap, not a regression. This file is the consolidate-mode body of `/synthesis`, preserved verbatim at `.agents/skills/synthesis/ref-mode-consolidate.md` and read natively by every non-Claude harness; there is no longer a standalone `consolidate` skill in either tree (merged into `/synthesis` on 2026-08-23). `.claude/skills/synthesis/` is the sync-generated derived copy (`python .agents/scripts/sync.py`) that must never be hand-edited. Cross-tree consistency: `python .agents/scripts/checkall.py`. The former Codex pointer-adapter mirror is RETIRED -- there is no adapter stub to regenerate.

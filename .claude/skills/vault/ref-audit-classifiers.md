---
categories: [sources]
type: reference
created: 2026-04-26
updated: 2026-04-26
status: active
tags:
  - topic/skill-infrastructure
  - topic/vault
  - topic/audit
aliases:
  - vault audit classifiers
  - 9 classifiers
related:
  - "[[SKILL|/vault SKILL.md]]"
  - "[[ref-output-templates]]"
  - "[[ref-stats-catalog]]"
---

# /vault Audit Classifier Reference

The 9 audit classifiers /vault audit runs, with detection rules + severity tiers + repair-classification (SAFE-AUTO / NEEDS-CONFIRM / BLOCKED) + worked examples.

Classifiers 1-5 are wrapped from `tools/vault-audit.py` (existing infrastructure); Classifiers 6-9 are inline in /vault audit Phase E-H (new in v2). Optional commit 4 of the upgrade plan extends `tools/vault-audit.py` to absorb Classifiers 6-9; until then, /vault implements them in shell.

## Severity tier definitions

- **CRITICAL** -- breaks vault navigation or data integrity. Wikilinks pointing to non-existent files, files lacking frontmatter (cannot be queried by Bases). Must fix.
- **WARNING** -- degrades vault quality but does not break functionality. Stale ref docs, frontmatter schema violations, orphan entities. Should fix in current session if possible.
- **INFO** -- cleanup opportunity; no functional impact. Deprecated-skill references in non-canonical locations, daily-note continuity gaps, MOC-coverage gaps. Fix as-bandwidth-allows.

## Repair-classification definitions

- **SAFE-AUTO** -- single-shot fix with unambiguous correct outcome; can batch-apply with single user yes
- **NEEDS-CONFIRM** -- ambiguity exists in fix target OR mutation crosses subjective threshold; per-fix user confirmation required
- **BLOCKED** -- never auto-applied; deletion is BLOCKED entirely (move-to-archive only via `<ARCHIVE_ROOT>/`)

## Classifier 1: broken-wikilinks (CRITICAL)

### Detection rule

Wraps `tools/vault-audit.py` broken-wikilinks block. Algorithm:
1. Glob all `**/*.md` files (excluding `.git/`, `node_modules/`, `_archive/`, `.checkpoints/`, `.obsidian/`, `.smart-env/`, `career-ops/`)
2. For each file, regex-extract `[[<target>]]` patterns (handle `[[target#anchor]]` and `[[target|alias]]` variants by stripping `#` and `|` content)
3. Build `ALL_BASENAMES` set from glob result (basenames without `.md` extension)
4. For each wikilink target, check if target exists in `ALL_BASENAMES`
5. Report unresolved targets with: source file path, line number, link text, target

### Severity: CRITICAL

Broken wikilinks fail Obsidian navigation (clicking the link creates an empty file), break MOC traversal, and signal stale references that may indicate larger drift.

### Repair classification

- **SAFE-AUTO** when: target has single-candidate fuzzy match in `ALL_BASENAMES` (e.g., `[[NVDA-analysis]]` -> only `nvda-analysis-2026-04-22.md` exists; correct unambiguously)
- **NEEDS-CONFIRM** when: multiple candidates (e.g., `[[NVDA]]` could match `NVDA.md` entity OR `NVDA-analysis-*.md`); enumerate candidates; user picks
- **NEEDS-CONFIRM** when: no candidates exist; user can choose to (a) create stub file, (b) remove wikilink and replace with plain text, (c) skip
- **BLOCKED** when: deletion of source file proposed; never auto-delete

### Worked example

Source: `wiki/research/sparks/spark-2026-04-26.md` line 47
Link: `[[challenge-roth-deployment]]`
Detection: target `challenge-roth-deployment` not in ALL_BASENAMES; closest match `challenge-roth-deployment-patience-2026-04-14`
Classification: SAFE-AUTO (single-candidate close match)
Proposed fix: replace `[[challenge-roth-deployment]]` with `[[challenge-roth-deployment-patience-2026-04-14]]`

## Classifier 2: missing-frontmatter (CRITICAL)

### Detection rule

Wraps script. Algorithm:
1. Glob `**/*.md` (excluding standard set)
2. For each file, read first line; check if matches `^---\s*$`
3. Report files where first line is NOT frontmatter fence

### Severity: CRITICAL

Files lacking frontmatter cannot be queried by Bases (the canonical structured-view tool); they're invisible to category/type/tag filters; they degrade vault discoverability.

### Repair classification

- **SAFE-AUTO** when: file content suggests deterministic frontmatter inference (e.g., file in `wiki/entities/tickers/` -> `categories: [entity]`, `type: ticker`, `status: active`, `tags: [ticker/<UPPER>]`, `created: <git-blame-first-add-date>`, `updated: <today>`)
- **NEEDS-CONFIRM** when: domain inference ambiguous; offer 2-3 frontmatter templates; user picks

### Worked example

Source: `wiki/research/notes-2026-04-23.md`
Detection: first line is `# Random notes`, not `---`
Inference: in `wiki/research/`, type likely `research`; no entity claims; status uncertain
Classification: NEEDS-CONFIRM (status field needs human input)
Proposed fix: insert frontmatter:
```yaml
---
categories: [wiki]
type: research
created: 2026-04-23
updated: <today>
status: <user-pick: active | draft | stale>
tags: []
related: []
---
```

## Classifier 3: frontmatter-schema (WARNING)

### Detection rule

NEW; inline in /vault audit Phase E. Algorithm:
1. Glob `**/*.md` (excluding standard set)
2. For each file with frontmatter (Classifier 2 PASS):
3. Parse YAML between `---` fences
4. Check `categories` is a plural list (not scalar string); fail if `categories: wiki` (scalar) instead of `categories: [wiki]` (list)
5. Check forbidden field `domain:` absent (stripped per CLAUDE.md schema)
6. Check tags do NOT use forbidden namespaces:
   - Forbidden: `domain/*`, `type/*`
   - Allowed: `topic/*`, `ticker/*` UPPER, `company/*` lowercase-kebab, `thesis/*` lowercase-kebab
7. Check `status:` value within enum: active / paused / done / dropped / stub / deprecated / draft / complete / stale
8. Check `created:` and `updated:` are ISO format `YYYY-MM-DD`

### Severity: WARNING

Schema violations break canonical-vocabulary discovery, allow drift, undermine future Bases queries.

### Repair classification

- **SAFE-AUTO** when: scalar `categories: wiki` -> wrap in list `[wiki]`; remove forbidden `domain:` field; move category-axis-tags from `domain/X` to `tags: [topic/X]` (deterministic mapping)
- **NEEDS-CONFIRM** when: invalid `status:` enum value; user picks correct enum

### Worked examples

**Example A (SAFE-AUTO):**
Source: `Atlas/concepts/investing/watchlist.md`
Violation: `categories: wiki` (scalar)
Fix: change to `categories: [wiki]`
sha256-preserve all body content outside frontmatter

**Example B (SAFE-AUTO):**
Source: `wiki/entities/tickers/MU.md`
Violation: `domain: investing` field present
Fix: remove `domain: investing` line
sha256-preserve body

**Example C (NEEDS-CONFIRM):**
Source: `Efforts/career-search/applications/render-tech-writer-2026-04-15/cover-letter.md`
Violation: `status: draft-final` (not in enum)
Resolution: user picks from {draft, complete, active}; auto-apply

## Classifier 4: orphan-detection (WARNING)

### Detection rule

Wraps script. Algorithm:
1. Glob entity files in `wiki/entities/{tickers,companies}/`
2. For each entity, grep entire vault for `[[<entity-basename>]]` references (excluding the entity file itself)
3. Count inbound references; flag <2 as orphan
4. Exclude from orphan list: templates folder, _archive folder, daily notes (high-churn ephemeral), private/

### Severity: WARNING

Orphan entities may indicate incomplete /enrich onboarding, missing MOC links, or stale entity notes that lost their referencing context.

### Repair classification

- **SAFE-AUTO** when: entity has clear domain (e.g., ticker entity); add to corresponding MOC's entity list
- **NEEDS-CONFIRM** when: entity is genuinely stale; user picks (a) keep + add MOC backlink, (b) move to `_archive/`, (c) skip

### Worked example

Source: `wiki/entities/companies/Mintlify.md`
Detection: 1 inbound reference (only from `Efforts/career-search/research/osanwe-public-readme-draft-2026-04-14.md`)
Classification: SAFE-AUTO
Proposed fix: add `[[Mintlify]]` to `Atlas/_MOCs/career-moc.md` companies list

## Classifier 5: stale-refs (WARNING)

### Detection rule

Wraps script. Algorithm:
1. Glob `Atlas/sources/*/ref-*.md` AND `.claude/skills/*/ref-*.md`
2. Extract `updated:` field from frontmatter
3. Compute days since update
4. Flag any with days >30
5. Annotate with thesis-importance weight from `ref-stats-catalog.md`

### Severity: WARNING (CRITICAL when thesis-weight >=1.3 AND days >60)

Stale ref docs prime stale analysis; the longer they go un-refreshed, the more likely subsequent /invest, /brief, /career invocations build on outdated context.

### Repair classification

- **NEEDS-CONFIRM** always; ref-doc refresh is a substantive content operation, not mechanical
- Surface to FOLLOWUPS:skills as `/deep <slug>` candidate (Pattern 21 Deep Research onboard)

### Worked example

Source: `Atlas/sources/investing/ref-research-insights.md`
Detection: `updated: 2026-04-08`; days stale: 18
Thesis weight: 1.0 (core-index)
Severity: WARNING (not CRITICAL)
Recommendation: surface to FOLLOWUPS as `/deep ref-research-insights candidate (priority: 18)` with trigger EOM

## Classifier 6: deprecated-skill-references (INFO)

### Detection rule

NEW; inline in /vault audit Phase F. Algorithm:
1. Build `DEPRECATED_SKILLS` set from `Calendar/decisions/decision-log.md` deprecation entries (currently includes `/research`, `/review` per 2026-04-26)
2. Build `EXCLUDE_PATHS` set: `.claude/skills/_archive/`, `docs/VAULT-HANDOFF-V*.md`, `Calendar/decisions/decision-log.md`, `Calendar/decisions/sessions-log.md`, `CLAUDE.md` (historical context allowed)
3. Grep vault for skill-invocation patterns: `/research\b`, `/review\b`, `(use /research)`, `(use /review)`
4. Filter out matches in EXCLUDE_PATHS
5. Report remaining matches with file path + line number + matched text

### Severity: INFO

Stale references to deprecated skills don't break anything but signal cleanup opportunity. Future deprecations will compound this if not fixed.

### Repair classification

- **SAFE-AUTO** when: simple text replacement (e.g., "use /review" -> "use /retro --weekly")
- **NEEDS-CONFIRM** when: replacement is contextual (e.g., a sentence describing /research in past tense may need different rewording per location)

### Worked example

Source: `Efforts/career-search/research/osanwe-public-readme-draft-2026-04-14.md` line 122
Match: "Methodology grounded in /research workflow"
Classification: SAFE-AUTO
Proposed fix: replace with "Methodology grounded in WebSearch + WebFetch workflow" (since /research was displaced by direct tool use)

## Classifier 7: daily-note-continuity (INFO)

### Detection rule

NEW; inline in /vault audit Phase G. Algorithm:
1. Glob `Calendar/daily/*.md` for past 30 days
2. Build expected-date sequence (today minus 30 days through today)
3. Detect missing dates
4. Day-of-week awareness: Saturday + Sunday gaps acceptable IF no Sessions Run activity expected (cross-reference `Calendar/decisions/sessions-log.md` for weekend entries)
5. Sample known good cadence from prior 90 days; if user typically runs sessions on weekends, weekend gaps ARE flagged

### Severity: INFO

Continuity gaps may indicate (a) actual no-activity days (fine), (b) skipped daily-note creation (SessionStart hook didn't fire), or (c) user discontinuity in vault habit.

### Repair classification

- **NEEDS-CONFIRM** always; backfilling daily notes for missed days is judgment call; offer to create skeleton with `## Sessions Run` populated from sessions-log entries on that date

### Worked example

Detection: April 2026 missing daily notes for: 2026-04-19, 2026-04-24
Sessions-log check: 2026-04-19 has 1 entry; 2026-04-24 has 0 entries
Recommendation: backfill 2026-04-19 (had activity) as candidate; skip 2026-04-24 (legitimate no-activity day)

## Classifier 8: template-drift (WARNING)

### Detection rule

NEW; inline in /vault audit Phase H. Algorithm:
1. Read `_templates/daily.md`
2. Verify all 9 canonical sections present (per ref-output-templates.md sec 9):
   - Market Pulse / Observations / Decisions / Commitments / Insights / Sessions Run / Cross-References / Tasks / Log
3. Report any missing sections

### Severity: WARNING

Template drift means new daily notes (created via Templater) get out-of-sync schema; downstream skills (/brief, /retro) expect the canonical 9 sections.

### Current state at 2026-04-26: template has 7 sections; missing: Commitments, Cross-References, Log. Plan agent flagged this; first /vault audit will surface as Classifier 8 finding.

### Repair classification

- **SAFE-AUTO** -- inserting missing sections in canonical order; no risk of misordering since canonical schema is fixed

### Worked example

Source: `_templates/daily.md`
Missing sections: `## Commitments`, `## Cross-References`, `## Log`
Classification: SAFE-AUTO (T1 issue ID)
Proposed fix: insert missing sections in canonical order between existing sections per ref-output-templates.md sec 9 schema

## Classifier 9: MOC-coverage (INFO)

### Detection rule

Wraps script + extends. Algorithm:
1. Glob `Atlas/_MOCs/*-moc.md`
2. For each MOC, identify its domain subtree (e.g., `investing-moc.md` covers `Atlas/concepts/investing/`, `wiki/investing/`, `wiki/entities/tickers/`)
3. Build set of files in domain subtree (excluding standard excludes)
4. Build set of files linked from MOC (parse wikilinks in MOC body)
5. Report files in domain subtree NOT linked from MOC
6. Report MOC links pointing to non-existent files (additional broken-link check scoped to MOCs)

### Severity: INFO

MOC-coverage gaps mean files exist in a domain but aren't discoverable via the MOC. Not breaking; may indicate ad-hoc files that should either be linked or moved/archived.

### Repair classification

- **SAFE-AUTO** when: file in domain subtree, name matches canonical pattern (e.g., new ticker entity); add to MOC's appropriate section
- **NEEDS-CONFIRM** when: file is borderline (research draft, ad-hoc note); user picks (a) link in MOC, (b) move to archive, (c) skip

### Worked example

Source: `Atlas/_MOCs/career-moc.md`
Detection: `wiki/entities/companies/Render.md` exists but not linked from career-moc Companies section
Classification: SAFE-AUTO
Proposed fix: add `- [[Render]]` to career-moc Companies list, alphabetically ordered

## Cross-cutting rules

### Exclude-list maintenance

Three exclude sets maintained per audit run:
1. `STANDARD_EXCLUDES`: `.git/`, `node_modules/`, `_archive/`, `.checkpoints/`, `.obsidian/`, `.smart-env/`, `career-ops/`
2. `EXPECTED_ARCHIVED`: contents of `.claude/skills/_archive/` (currently includes /research, /review post-deprecation)
3. `KNOWN_DEPRECATIONS`: parsed from decision-log.md "Deprecate" entries

Classifiers reference these to avoid false positives.

### Severity escalation

A classifier's normal severity can escalate based on quantity:
- WARNING -> CRITICAL when count >= 20 (degrades vault usability)
- INFO -> WARNING when count >= 30 (signals systemic drift)

### Repair-mode safety hierarchy

When /vault repair processes a fix list:
1. BLOCKED items rejected immediately with clear diagnostic
2. NEEDS-CONFIRM items presented one-by-one with diff preview
3. SAFE-AUTO items batched into single preview block; user batch-yes
4. All applied as single atomic commit (Phase H of /vault repair)
5. Mid-batch F.halt on any failure; F11 stays on; structured report

### Sha256 invariant rules

Every Edit operation in repair mode:
1. Capture pre-write sha256 of file content outside intended insertion site
2. Apply Edit
3. Capture post-write sha256 of same content range
4. Compare; if mismatch, F.halt; back out the Edit; report violation

This guarantees content outside the intended insertion site is byte-exact post-write (no LLM-induced drift in unrelated paragraphs).

### Idempotency requirement

Re-running /vault audit on identical vault state MUST produce identical findings (modulo timestamps in frontmatter). Re-running /vault repair --apply on already-applied fixes MUST report "no-op" rather than re-applying.

Idempotency is checked via meta.json comparison: if `findings_by_classifier` field is identical between two consecutive audit runs without intervening commits, audit is idempotent. Drift signals classifier non-determinism (bug).

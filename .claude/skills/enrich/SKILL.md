---
name: enrich
description: "Use when attaching a document for vault placement, when pasting /deep Research-mode output for onboarding, when routing scratch text via /enrich command, after onboarding meeting transcripts or clippings, or before /ingest claim-distribution. Onboard a document into the vault end-to-end with zero confirmation friction, full bidirectional linking, and a built-in /ingest-needed recommendation. Routes to canonical path via deterministic rule matching (observable content markers, not probabilistic scoring). If source frontmatter contains a `target_path` custom field (emitted by /deep v2 composed prompts), v9 uses it as explicit placement override, bypassing Rule 1-22 autonomous routing while preserving all other gates (path-guards, path-collision handling, symmetric back-linking, /ingest recommendation). Composes canonical frontmatter. Applies SYMMETRIC back-linking: every wikilink in the onboarded doc's related: field becomes a reciprocal back-reference on the target file, covering MOCs, theses, concepts, sources, efforts, decisions, entities, and peer refs uniformly. Evaluates whether /ingest (claim extraction + entity-level distribution) would add compounding value using three deterministic tests (fact density, multi-entity coverage, entity-level distribution relevance) and surfaces a binary YES/NO verdict aligned with SOTA vault compounding philosophy (MAYBE collapses to YES when any test dimension shows substantive content; NO only when content is genuinely thin across all dimensions). When YES, includes a copy-paste-ready /ingest command. Reports substantive entity mentions that lack vault notes. Preserves body byte-exact (sha256-verified). Primary use: attach a document in Claude Code and type `/enrich` -- routes, writes, back-links bidirectionally, recommends /ingest if worth it, commits atomically. Also: --backlink-only <vault-path> to retroactively re-evaluate back-links on an existing file. Confirmations reserved ONLY for thesis-essay routing and pathological replacement cases. Flags: --replace, --refresh, --to, --no-backlink, --backlink-only, --confirm, --preview. Distinct from /ingest (extracts claims and distributes); /enrich preserves the document whole, wires it bidirectionally, and tells you when /ingest is the next step. Phase O.0 pre-commit /vault audit gate (CAT-3 prevention-architecture parity)."
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Agent
---

# /enrich -- autonomous document onboarding with symmetric back-linking

Take a document, route it to its canonical home via deterministic rules, compose canonical frontmatter, apply bidirectional back-links to every peer file the document forward-references, preserve body byte-exact.

## When to use

"I have a document. File it correctly, wire it bidirectionally vault-wide, don't change a byte of it."

Not for:
- Extracting claims / distributing across entity notes (that is `/ingest`)
- Editing body of an existing vault file (direct Edit)
- Creating entity from scratch (use template)

## Invocation

Primary flow: attach + `/enrich`. Additional modes for edge cases.

| Syntax | Behavior |
|---|---|
| `/enrich` with attached file | Autonomous end-to-end: route + write + symmetric back-links + atomic commit |
| `/enrich` with inline paste | Same; content from message |
| `/enrich <path>` | Read from filesystem; autonomous |
| `/enrich <path> --refresh` | Additive maintenance on existing file; body unchanged; no back-link re-evaluation (use --backlink-only for that) |
| `/enrich <source> --replace --to <path>` | Overwrite existing target (explicit --to required) |
| `/enrich <source> --to <path>` | Override autonomous routing |
| `/enrich <vault-path> --backlink-only` | Retroactive back-link re-evaluation on existing vault file; idempotent (skips already-linked) |
| `/enrich <source> --preview` | Show full plan including back-links; no write |
| `/enrich <source> --no-backlink` | Write onboarded doc only; skip back-link pass |
| `/enrich <source> --confirm` | Opt into per-step confirmations (conservative mode) |

## Execution Rules

- **Subagent dispatch is MANDATORY when specified by phase** (Step 4b dispatches `frontmatter-linter` pre-flight before atomic commit). Pre-emptive skip based on judgment ("frontmatter looks fine", "I'll catch errors via ruamel gate later") is FORBIDDEN. The subagent (Sonnet max for compute discipline) wraps `tools/frontmatter-check.py` and returns structured pass/fail JSON with specific defect list per CLAUDE.md schema. Pre-flight catch is cheaper than mid-Edit failure cascade. Legitimate fallback fires ONLY on (a) contract violation -- subagent return missing required JSON fields, OR (b) actual dispatch failure -- timeout, rate limit, tool-denial, hard subagent crash. Pre-emptive skip surfaces in Step 6 Report as **DEVIATION** (not "fallback"). Quality preserved by additive design: existing Step 5a post-write ruamel gate remains intact; pre-flight is purely additive.

## Process

### 1. Read source

Read by mode (attachment / inline / filesystem / vault path). Parse leading frontmatter if present. If source frontmatter exists AND ruamel parse FAILS: HALT with diagnostic. Offer Group 29 MALFORMED repair pattern (flow-style wikilinks -> block-style quoted) OR halt. Do not silently repair.

Compute `source_body_sha256` for step 5 invariant. If source has no frontmatter: body = entire source bytes. If source has valid frontmatter: body = bytes after closing `---\n`.

### 1.a. target_path detection (v9 addition)

If parsed frontmatter dict contains `target_path` key:

- Extract `target_path_value` (string)
- Validate: path does not trigger path-guards (`.raw/`, `private/`, `_quarantine/`, `finance/`, `credentials/`, `.git/`, `.claude/hooks/`, `.claude/state/`)
- Validate: path has `.md` extension and is under canonical top-level directory (`Atlas/`, `Calendar/`, `Efforts/`, `wiki/`, `docs/`, `_templates/`, `tools/`)
- Set `explicit_target = target_path_value`
- Log: "Explicit target_path detected from source frontmatter: <path> -- bypassing Rule 1-22 autonomous routing"

Else:

- `explicit_target = None`
- Proceed with autonomous signal detection + Rule 1-22 routing in Phase 3

The `target_path` field is a user custom field per CLAUDE.md sec 4.5 (preserved byte-exact class alongside `ticker`, `sector`, `thesis`, `confidence`). Emitted by /deep v2-composed Research prompts so Research output can signal its intended placement to /enrich without slug drift.

### 2. Detect signals

Load vault indexes once via Glob + basename extraction:

- TICKERS = { basenames of wiki/entities/tickers/*.md (UPPER) }
- COMPANIES = { basenames of wiki/entities/companies/*.md }
- MOC_STEMS = { basenames of Atlas/_MOCs/*.md }
- THESIS_STEMS = { basenames of Atlas/concepts/investing/theses/*.md }
- ALL_BASENAMES = { every .md basename in vault, excluding path-guarded + gitignored }

Scan source body:

- **Dates:** `\d{4}-\d{2}-\d{2}` in filename, H1, or opening -> `created:` candidate
- **Tickers:** `^[A-Z]{2,5}$` tokens matching TICKERS -> `ticker/<UPPER>`
- **Companies:** TitleCase phrases or known-company keywords matching COMPANIES (case-insensitive phrase) -> `company/<lowercase-kebab>`
- **Thesis clusters:** >=2 keyword matches -> `thesis/<stem>`:
  - orbital-compute: ORBC-DEMO, LNCH-DEMO, OPTL-DEMO, orbital data center, launch cost, optical downlink
  - tokenized-settlement: BTC, ETH, SOL, cross-border payment, settlement rails, stablecoin
  - grid-storage: grid, battery storage, utilities, power capacity, interconnection queue
  - platform-moats: AAPL, MSFT, GOOGL, META, platform, moat, network effect
  - core-index: SPY, VTI, S&P 500, index
- **Topics:** reason over content, emit 3-5 lowercase-kebab primary topics -> `topic/<slug>`

### 2a. Tag vocabulary guardrail (MECHANICAL)

    ALLOWED_TAG_NAMESPACES = {"topic", "ticker", "company", "thesis"}
    for tag in proposed_tags:
        ns = tag.split("/", 1)[0] if "/" in tag else None
        assert ns in ALLOWED_TAG_NAMESPACES
        assert "/" in tag

HALT on drift. Never emit `domain/*`, `type/*`, `health/*`, `review/*`, or bare.

### 3. Determine placement (DETERMINISTIC, rule-based)

**v9 explicit-target branch (checked first):**

If `explicit_target` from Phase 1.a is set:

- `target_path = explicit_target`
- Skip Rule 1-22 evaluation
- Skip confidence reporting (target is explicit, not inferred)
- Still run: path-collision handling (size-ratio heuristic if target exists per 3e), symmetric back-link planning, post-write sha256 body invariant, post-write ruamel gate
- Report format: `Placement: <explicit_target> (explicit from target_path frontmatter field; Rule 1-22 bypassed)`
- Skip to Phase 4

Else (`explicit_target is None`): proceed with autonomous Rule 1-22 routing below.

---

The skill routes via an ordered rule list. Each rule has REQUIRED markers (all must match for rule to fire) and IDENTIFYING markers (additional positive evidence included in the report for auditability). The first rule in priority order whose REQUIRED markers all match wins. Rules are ordered most-specific first, most-general last, so at most one rule fires for well-typed content.

If no rule fires (genuine cross-category ambiguity, rare): prompt user with enumerated candidates. If multiple rules would fire at same priority: impossible by design -- REQUIRED marker sets are mutually exclusive at priority level.

Thesis-essay routing is the one categorical exception: when Rule 17 fires, confirmation is required regardless of match strength (sacred conviction artifacts per reader/writer stance).

#### 3a. Structural analysis (extends step 2 signals)

- **Length profile:**
  - SHORT (<2k words): analysis, decision record, briefing, spark
  - MEDIUM (2k-5k): research output, challenge, analysis
  - LONG (5k+): reference doc (peer ref-*.md are 5.8k-6.6k)
- **Section markers (H2 patterns, case-insensitive):**
  - `^## (Sources|References|Citations)$` -> research/reference
  - `^## (Invalidation|Evidence Against|Bear Case|Counter)` -> challenge
  - `^## (Decision|Options|Reversibility|Pre-mortem)` -> decision record
  - `^## (Thesis|Conviction|Position|Why I)` -> thesis essay
  - `^## (Analysis|Valuation|Risks|Spine)` -> investment analysis
  - `^## (Market Pulse|BLUF|Priced-In|Intelligence Gaps)` -> briefing
  - `^## (Transmission|Precedent|Chokepoint|Safe-Haven)` -> geopolitical ref
  - Numbered section TOC (`## 1.`, `## 2.`, ...) + multiple tables + inline citations -> reference doc
- **Voice:**
  - First-person conviction ("I believe", "my thesis", "the case I make") -> thesis/playbook
  - Third-person analytical (no first-person) -> reference/research/analysis
  - Counter-argument framing -> challenge
- **Domain content signals (beyond tags):**
  - Supplement/biomarker/peptide/lab terms -> health
  - Application/cover letter/resume/interview/ATS -> career
  - Swing/TrackMan/drill/biomechanics -> golf
  - Geopolitical/macro/conflict/transmission/chokepoint -> macro/investing
  - Model/GPU/LLM/inference/quantization/RAG -> tech

#### 3b. Placement rules (ordered, first-match wins)

Each rule specifies REQUIRED markers (all must match) and IDENTIFYING markers (reported for auditability). Rule priority = list order (Rule 1 highest priority).

**Rule 1 -- Reference doc.**
- REQUIRED: length >= 5,000 words AND numbered-section TOC (>=3 `## N.` or `### N.` headers) AND inline-citation density >= 10 citations AND primary frontmatter tags topic/* count >= ticker/* count AND no first-person-conviction voice ("I believe", "my thesis", "the case I make")
- IDENTIFYING: multiple `| col | col |` tables (>=3), explicit domain topic (geopolitics / semiconductors / biomarkers / etc.)
- TARGET: `Atlas/sources/<domain>/ref-<slug>.md`
- Domain from primary topic/* tag (geopolitics+defense+macro -> investing; career-* -> career; biomarker/supplement -> supplements; swing/trackman -> golf; local-llm/quantization -> tech; methodology/meta -> meta). Slug from primary topic kebab-case.

**Rule 2 -- Single-ticker investment analysis.**
- REQUIRED: 1-2 tickers dominate (>=60% of ticker-mention count) AND analytical section headers (valuation, risks, thesis status, spine-adjacent) AND length < 5,000 words
- IDENTIFYING: 6-step spine markers (price timestamp, catalyst date, regime, portfolio impact, thesis status, recommendation), confidence rating field
- TARGET: `wiki/investing/analyses/<ticker>-analysis-<date>.md`

**Rule 3 -- Portfolio synthesis.**
- REQUIRED: >= 3 tickers with roughly balanced mention count AND allocation/weighting/correlation framing in headers AND length MEDIUM
- IDENTIFYING: explicit allocation math, thesis exposure percentages
- TARGET: `wiki/investing/analyses/portfolio-synthesis-<date>.md`

**Rule 4 -- Portfolio snapshot.**
- REQUIRED: price table (ticker + price + change) AND allocation summary AND net-worth framing
- TARGET: `wiki/investing/snapshots/snapshot-<date>.md`

**Rule 5 -- Investment challenge / stress-test.**
- REQUIRED: counter-argument structure (headers like "Bear case", "Evidence Against", "Invalidation", "Stress Test") AND references a specific thesis
- TARGET: `wiki/research/challenges/<slug>-<date>.md`

**Rule 6 -- Cross-domain spark.**
- REQUIRED: multi-domain pattern-emergence framing AND explicit cross-references between domains (investing + career + health + golf)
- TARGET: `wiki/research/sparks/spark-<date>.md`

**Rule 7 -- Deep research prompt.**
- REQUIRED: prompt-for-Research-mode framing ("You are conducting institutional-grade research", "ROLE", "CONTEXT", source-hierarchy section)
- TARGET: `wiki/research/prompts/<slug>-<date>.md`

**Rule 8 -- Raw research dump.**
- REQUIRED: >=10 source URLs AND minimal structure (no TOC, no numbered sections) AND length MEDIUM-LONG AND no conclusions
- TARGET: `wiki/research/dumps/<slug>-<date>.md`

**Rule 9 -- Ingest report.**
- REQUIRED: claim-extraction + contradiction-resolution sections AND explicit source attribution
- TARGET: `wiki/research/<slug>-ingest-<date>.md`

**Rule 10 -- Decision record.**
- REQUIRED: Decision/Options/Reversibility/Pre-mortem section headers AND single-choice framing
- TARGET: `Calendar/decisions/decision-<slug>-<date>.md`

**Rule 11 -- Morning briefing.**
- REQUIRED: BLUF + market-pulse + priced-in + intelligence-gaps section headers AND dated for today or next trading day
- TARGET: `Calendar/decisions/briefings/briefing-<date>.md`

**Rule 12 -- Weekly review.**
- REQUIRED: WoY pattern (YYYY-WNN) in filename or H1 AND daily-notes synthesis across the week
- TARGET: `Calendar/weekly/<YYYY-Www>-review.md`

**Rule 13 -- Career research.**
- REQUIRED: topic/career-* OR topic/ai-trainer OR topic/job-search OR topic/resume OR topic/ats-* tag dominant AND NOT primarily about a single company (Rule 14)
- IDENTIFYING: career-tracker companies (DataAnnotation, Outlier, Mindrift, Scale AI), interview/ATS/resume terminology
- TARGET: `Efforts/career-search/research/<slug>-<date>.md`

**Rule 14 -- Career application artifact.**
- REQUIRED: cover-letter OR resume-variant OR interview-prep framing AND specific company name dominant
- TARGET: `Efforts/career-search/applications/<company>-<date>/<artifact-slug>.md`

**Rule 15 -- Health research/analysis.**
- REQUIRED: supplement/biomarker/peptide terminology dominant OR lab-marker-driven structure
- TARGET: `Efforts/health-protocol/analyses/<slug>-<date>.md`

**Rule 16 -- Golf analysis.**
- REQUIRED: TrackMan/swing/drill/biomechanics terminology dominant
- TARGET: `Efforts/golf-practice/analyses/<slug>-<date>.md`

**Rule 17 -- Thesis essay** (ALWAYS CONFIRM).
- REQUIRED: first-person conviction voice AND argues-for-a-position structure (Why, Evidence, Invalidation, Current Read sections) AND length LONG
- TARGET: `Atlas/concepts/investing/theses/thesis-<slug>.md`
- CONFIRMATION REQUIRED: thesis essays are the user's conviction voice; single categorical exception to autonomous routing. Prompt: "Rule 17 matched (thesis essay). Target: <path>. Proceed? [y/N]"

**Rule 18 -- Concept playbook/strategy.**
- REQUIRED: playbook/framework-definition structure AND not time-bound AND not first-person-conviction
- TARGET: `Atlas/concepts/<domain>/<slug>.md`

**Rule 19 -- External source (book/paper/article).**
- REQUIRED: third-party author attribution AND summary/review framing
- TARGET: `Atlas/sources/<domain>/<slug>.md`

**Rule 20 -- People entity.**
- REQUIRED: person-entity structure (Role, Company, Interactions, Context sections)
- TARGET: `Atlas/people/<Name>.md`

**Rule 21 -- MOC.**
- REQUIRED: domain-index structure (enumerates files in the domain)
- TARGET: `Atlas/_MOCs/<domain>-moc.md`
- CONFIRMATION: new-MOC creation is structural; confirm before write.

**Rule 22 -- General research output** (fallback catch-all).
- REQUIRED: research-like framing but none of Rules 1-21 match
- TARGET: `wiki/research/<slug>-<date>.md`

**No-rule-fires fallback.**
If Rules 1-22 all fail to match their REQUIRED markers (genuinely cross-category or unstructured content): prompt user with enumerated candidates showing why each rule didn't fire (which REQUIRED markers were missing). User picks or overrides with --to.

#### 3c. Placement reporting (every invocation)

Report the fired rule and all matched markers. Since rules are deterministic and first-match-wins, this is auditable:

    Placement:       <target_path>
    Rule fired:      Rule N -- <rule name>
    REQUIRED matched:
      - <marker 1>: <concrete evidence, e.g. "7,182 words (>= 5,000 threshold)">
      - <marker 2>: <evidence>
      - <marker 3>: <evidence>
    IDENTIFYING markers (additional positive evidence):
      - <marker>: <evidence>
      - ...
    Rules checked before this one (did not fire):
      - Rule 1 <name>: failed REQUIRED <specific marker not met>
      - Rule 2 <name>: failed REQUIRED <specific marker not met>
      ...
    Override: rerun with `--to <preferred-path>` to bypass autonomous routing.

This format is rule-based and auditable -- every decision can be traced to the specific markers that did or did not match.

#### 3d. Atlas/ stance (for rule-based routing)

CLAUDE.md's reader/writer stance requires Atlas/ write confirmation. For /enrich autonomous mode:

- `Atlas/sources/` (Rule 1, Rule 19) -> AUTONOMOUS (natural landing for reference + external-source docs)
- `Atlas/concepts/` playbooks/strategies (Rule 18) -> AUTONOMOUS
- `Atlas/people/` (Rule 20) -> AUTONOMOUS
- `Atlas/_MOCs/` (Rule 21) -> CONFIRM (structural decision; new-MOC creation is rare and high-leverage; updates via back-linking are autonomous)
- `Atlas/concepts/investing/theses/` (Rule 17) -> ALWAYS CONFIRM (sacred conviction artifact; categorical architectural exception)

Rules 17 and 21 are the two that require confirmation. All other matched rules execute autonomously.

#### 3e. Path-collision resolution (autonomous, size-ratio heuristic)

If autonomously-determined target EXISTS and mode is not `--refresh` / `--replace`:

Compute ratio = source_body_bytes / target_file_bytes. Apply:

- **source sha == target sha** -> NO-OP. Report "target already matches; nothing to do."
- **ratio >= 1.0x** (source same or larger) -> AUTONOMOUS REPLACE. This covers content expansion (the common intent when /enrich is invoked on an existing-path document).
- **ratio < 0.8x** (source substantially smaller) -> CONFIRM. Pathological case: autonomous action likely wrong (wrong file attached? intended --refresh?). Prompt:

        Rule N matched (<rule name>): target <path>
        Target exists and is LARGER than source:
          current: <N> bytes, sha256 <abc>, <ISO>
          source:  <M> bytes, sha256 <xyz> (<%>% of target)

        Autonomous action would be surprising for this size ratio.
        Intent: [R]eplace anyway / Re[F]resh (additive, likely intent) / [C]ancel

- **0.8x <= ratio < 1.0x** -> AUTONOMOUS REPLACE with report note ("similar-size replacement: size-ratio <X>x"). Edge case but the user has full rollback via git.

Report for every autonomous replacement:

    Autonomous action: REPLACE
    Target: <path>
    Before: <N> bytes, sha256 <abc>, <ISO>
    After:  <M> bytes, sha256 <xyz>, now
    Delta:  <N->M> bytes (<ratio>x)
    Rollback: git reset --soft HEAD~1 (commit) or git checkout -- <path> (pre-commit)

For `--refresh`: require target exists; fail if not. Additive-only.
For `--replace --to <path>`: bypass autonomous placement; require target exists; autonomous replacement regardless of size ratio (explicit user intent).
For `--to <path>`: bypass autonomous placement; still runs path-guards + autonomous collision resolution.
For `--confirm`: opt into per-step confirmations for conservative runs.

#### 3f. Path-guards (HARD; autonomous mode cannot override)

NEVER write to `.raw/`, `private/`, `_quarantine/`, `finance/`, `credentials/`, `.git/`, `.claude/hooks/`, `.claude/state/`. Architectural, not preference. If autonomous placement would land in these (bug): HALT.

### 4. Compose canonical frontmatter

Required: `categories:` (one-element list from canonical vocabulary), conditional `type:`, `created:`, `updated:`, `status:` (category default from table below, overridable by content signals), `tags:` (guardrail-asserted), `related:` (see 4a), `aliases:` (from H1 if clear). Preserve user-custom fields byte-exact. Remove `domain:` field with report.

### 4a. Related wikilinks -- existence annotation

Check each suggested stem against ALL_BASENAMES. Annotate `(exists)` vs `(prospective)`. Order: MOCs -> thesis essays -> entity notes -> reference docs -> peer concepts -> analyses. All double-quoted: `- "[[stem]]"`.

### 4b. DELEGATED dispatch to `frontmatter-linter` subagent (PREFERRED pre-flight path; Phase C wiring 2026-05-02)

**MANDATORY** (per Execution Rules): dispatch first, no pre-emptive skip. Pre-flight schema check catches GATE breaches BEFORE the atomic-commit cascade in Step 5; mid-Edit failure is more expensive than pre-flight rejection.

Use the Agent tool with subagent_type `frontmatter-linter`. Pass input: `{file: "<composed frontmatter as ephemeral file or YAML string>", schema_version: "canonical-2026"}`. The subagent validates against canonical schema (categories plural list, status enum, ISO dates, no `domain` field, no `domain/*` or `type/*` tag namespaces, related list shape) and returns structured JSON: `{file, pass, defects[], totals: {gate, hard_drift, soft_drift}}`.

Validate subagent return:
- JSON with `pass` boolean
- `defects` array (empty on pass)
- Each defect has `field`, `issue`, `severity` (GATE | HARD DRIFT | SOFT DRIFT), and `fix_hint`
- `totals` object with severity counts

On contract violation OR dispatch failure: fall through to direct ruamel gate at Step 5a (existing post-write check). Surface fallback in Step 6 Report.

On dispatch success:
- If `pass: true`: proceed to Step 5 primary Write
- If `pass: false` with GATE defects: HALT; emit defects + fix_hints to user; do NOT proceed to Step 5 (atomic commit cascade not safe)
- If `pass: false` with HARD DRIFT defects only (no GATE): WARN but proceed; auto-apply fix_hints if `--auto-fix` flag is set; surface in Step 6 Report

Note: Step 5a post-write ruamel gate remains as defense-in-depth even after Step 4b passes -- catches anything that mutated between lint and write.

### 5. F11 flag + primary Write (SET IN PHASE C, NOT PHASE E -- v7 FIX)

**Phase C (F11 set):** Set `.claude/state/auto-commit-disabled` BEFORE any Edit/Write on tracked files. This is the single F11 flag set point for the entire /enrich invocation (covers both primary onboard Write AND back-link edits in Phase F). Prevents PostToolUse auto-commit hook from firing mid-flow. F11 flag set in Phase C per v7 discipline; v5 set it before back-link pass only, which caused soft-reset collapses on primary Write.

**Phase E (primary Write):** Compose target bytes:

    target_bytes = b"---\n" + frontmatter_yaml + b"\n---\n" + source_body_bytes

Extract target body post-composition:

    target_body_bytes = target_bytes[target_bytes.find(b"\n---\n", 4) + len(b"\n---\n"):]
    assert sha256(target_body_bytes) == source_body_sha256

HALT if divergent. Write tool.

For `--replace`: same invariant (on SOURCE body preservation at target). Old target content is replaced intentionally; that is the point of --replace.

### 5a. Post-write ruamel gate

Re-read target; `ruamel.yaml.load()` frontmatter; assert parses. Re-assert tag vocabulary on written state.

### 6. Report (extended for v7; Phase C wiring 2026-05-02)

Print:
- Target path (absolute)
- Rule fired + REQUIRED matched markers + IDENTIFYING markers + rules-checked-before
- Composed frontmatter
- Detected tags by namespace
- Suggested related with existence annotations
- Removed-from-source fields (if any)
- Spine advisory (if ticker-tagged)
- **Substantive entity mentions without vault notes** (v7): list each ticker/company that appears >=3 times or has dedicated section but lacks an entity note at `wiki/entities/{tickers,companies}/`.
- **/ingest recommendation** (v8 NEW): YES / NO / MAYBE verdict with three-test rationale, and if YES or MAYBE, a copy-paste-ready `/ingest <onboarded-target-path>` command. See subsection 6b below for decision logic.
- Back-link plan + applied set (per step 7)
- **Subagent dispatch report** (Phase C wiring 2026-05-02): emit one of:
  - `Step 4b frontmatter-linter: DISPATCHED` -- subagent ran, schema validated pre-write
  - `Step 4b frontmatter-linter: FALLBACK (<reason>)` -- legitimate dispatch failure; relied on Step 5a post-write ruamel gate
  - `Step 4b frontmatter-linter: DEVIATION (<judgment>)` -- pre-emptive skip; flag as discipline breach + sessions-log entry

### 6b. /ingest recommendation (v8 deterministic logic)

After the onboarded doc is written and before (or alongside) the back-link pass, evaluate three tests to decide whether /ingest should be the next operation.

**Test 1 -- Fact density**

Scan the written body for specific-fact markers per 1000 words. Markers (case-insensitive, count unique occurrences):

- Dollar amounts: `\$[\d][\d,.]*` (e.g., `$176B`, `$3.2M`, `$920`)
- Percentages: `\d+(\.\d+)?%` (e.g., `37%`, `2.5%`)
- Specific metric patterns: `(ratio|margin|yield|growth rate|backlog|capex|FCF|ROIC|book-to-bill|P/E|EV/EBITDA) [\d]+` or inverse ordering
- Specific dates: `\d{4}-\d{2}-\d{2}`, `Q[1-4] \d{4}`, `(January|February|...|December) \d{4}`
- Ticker+number pairs: `(TICKER) [\$\d]+` within 3 tokens of each other

Normalize: `density = markers / (body_word_count / 1000)` (markers per 1000 words).

Thresholds:
- `density >= 15` -> HIGH
- `8 <= density < 15` -> MEDIUM
- `density < 8` -> LOW

**Test 2 -- Multi-entity coverage**

Count substantively-discussed entities (same definition as v7 BL4): ticker/company appears >=3 times in body OR appears in a dedicated H2/H3 section header.

Thresholds:
- `>= 5 substantive entities` -> HIGH
- `3-4 substantive entities` -> MEDIUM
- `< 3 substantive entities` -> LOW

**Test 3 -- Entity-level distribution relevance (Rule-driven)**

Derived from which placement Rule fired in Step 3:

| Rule fired | T3 verdict | Rationale |
|---|---|---|
| Rule 1 (reference doc) | YES | Multi-entity reference content belongs at entity level |
| Rule 3 (portfolio synthesis) | YES | Cross-position synthesis |
| Rule 9 (ingest report) | YES | Already about distribution; reinforces |
| Rule 18 (concept playbook) | MAYBE | Playbooks discuss entities but often thin per-entity |
| Rule 13 (career research) | MAYBE | Depends on whether company content is substantive |
| Rule 19 (external source book/paper) | YES | External material is prime ingest target |
| Rule 22 (general research) | MAYBE | Depends on T1+T2 |
| Rule 2 (single-ticker analysis) | NO | Facts already at entity-adjacent path (wiki/investing/analyses/) |
| Rule 4 (snapshot) | NO | Ephemeral price data; stale fast |
| Rule 17 (thesis essay) | NO | Conviction, not extractable fact |
| Rule 10 (decision record) | NO | Tactical; time-bound |
| Rule 11 (briefing) | NO | Time-bound |
| Rule 12 (weekly review) | NO | Time-bound synthesis |
| Rule 15 (health) | NO | Personal/tactical |
| Rule 16 (golf) | NO | Personal/tactical |
| Rule 5 (challenge) | NO | Stress-test; point-in-time |
| Rule 6 (spark) | NO | Pattern emergence, not entity facts |
| Rule 7 (prompt) | NO | Meta-artifact |
| Rule 8 (dump) | NO | Raw; not yet distilled |
| Rule 14 (career app artifact) | NO | Tactical per-company |
| Rule 20 (people entity) | NO | Itself an entity |
| Rule 21 (MOC) | NO | Index |

**Combination logic (binary, v8.1 SOTA alignment)**

    if T3 == "NO":
        verdict = NO
    elif T3 == "YES":
        verdict = YES      # reference/synthesis/external -- always worth ingesting
    elif T3 == "MAYBE" and (T1 in ("HIGH", "MEDIUM") or T2 in ("HIGH", "MEDIUM")):
        verdict = YES      # at least one dimension carries content -- compound it
    elif T3 == "MAYBE" and T1 == "LOW" and T2 == "LOW":
        verdict = NO       # genuinely thin; skip to avoid empty stubs
    else:
        verdict = NO

**SOTA rationale:** vaults compound when entities and concepts accumulate connections. Thin entity stubs are better than missing entities -- they serve as back-link targets and accretion points for future doc content (e.g., /invest, /ingest from later docs). The only case where NO fires under T3=MAYBE is genuine content thinness across BOTH dimensions, which is rare for documents worth onboarding in the first place. No MAYBE emissions; the skill commits to a directive answer.

**Output format**

    /ingest recommendation: <YES | NO | MAYBE>
      Rationale:
      - Fact density (T1): <HIGH | MEDIUM | LOW> (<density> markers/1000w across <body_words> words)
      - Multi-entity (T2): <HIGH | MEDIUM | LOW> (<count> substantive entities: <list>)
      - Entity-level distribution relevance (T3): <YES | MAYBE | NO> (Rule <N> = <rule-name>)

      <if YES or MAYBE:>
      Recommended next step:
        /ingest <onboarded-target-path>
      <if YES:>
      Running /ingest will: distill <count> substantive entity discussions
      into updates on <list> entity notes (creating missing ones where
      applicable), writing an ingest report to wiki/research/.
      <if MAYBE:>
      Running /ingest is optional. Consider if you want entity-level
      surfacing of this doc's content; skip if the doc itself is the
      primary artifact.

      <if NO:>
      Skip /ingest. Reason: <specific T3 rationale>. The document is
      already fully wired via /enrich's bidirectional linking.

**Mode-specific behavior:**

- `--preview`: include /ingest recommendation in preview output
- `--no-backlink`: /ingest recommendation still fires (independent of back-linking)
- `--refresh`: skip /ingest recommendation (document was previously onboarded; if user wanted /ingest, they'd have run it then or now directly)
- `--backlink-only`: skip /ingest recommendation (no new content to evaluate)

### 7. Back-link application (SYMMETRIC, autonomous; --no-backlink skips, --confirm gates)

**Core principle (v7):** every wikilink in the onboarded doc's final `related:` field is a bidirectional relationship. For each, propose a reciprocal back-reference on the target file. Plus two type-specific additions for cases where the relationship is not captured by the related: field itself: knowledge-moc table rows (reference docs) and substantive entity back-links (body mentions).

This collapses v5's BL1/BL2/BL5 into a single unified symmetric-linking pass. BL3 (knowledge-moc table) and BL4 (substantive entities) remain as type-specific additions because they express relationships not encoded in `related:`.

#### Primary back-link pass -- symmetric over related:

For each wikilink `[[stem]]` in the onboarded doc's `related:` field:

1. Resolve `stem` against ALL_BASENAMES to get target file path
2. Skip if target file does not exist (prospective link; no back-link possible). Log "missing target: <stem>".
3. Read target file; parse frontmatter
4. Check if target's `related:` already contains the onboarded doc's stem (in any form: `[[stem]]`, `"[[stem]]"`, flow or block style). If yes: SKIP as idempotent no-op. Log "already linked".
5. Check target file's category against BACKLINKABLE_CATEGORIES = {moc, sources, wiki, entity, concepts, efforts, decisions, weekly, people}. If not in set: SKIP with log ("category <X> excluded from back-linking"). This excludes `[daily]` (hook-created, different schema) and `[meta]` (infrastructure).
6. Compose surgical Edit: add `- "[[<onboarded-stem>]]"` to target's `related:` list (preserve existing ordering; insert alphabetically within same semantic group if identifiable; otherwise append to list).
7. Dry-run: assert old_string appears exactly once in target pre-edit.
8. Apply Edit.
9. Post-edit gates (MECHANICAL per target file):
   - `before_sha256 != after_sha256` (edit actually changed file)
   - `"<onboarded-stem>"` appears exactly once in post-edit `related:` (not elsewhere in the file)
   - Diff is a single contiguous insertion (no scattered changes)
10. On any assertion failure: log + continue batch (don't halt on single-file issue); report failed applications at end.

#### Type-specific addition 1: knowledge-moc table row

IF onboarded doc is `categories: [sources]` with `type: reference`: in addition to the primary back-link pass, insert a row in `Atlas/_MOCs/knowledge-moc.md`'s Reference Document Status table. Row placement: domain-grouped order matching commit 46fdc23 pattern. Skip if row already present (idempotent).

#### Type-specific addition 2: substantive entity back-links

For each ticker/company detected in body:
- **Substantive** = appears >=3 times in body OR appears in a dedicated H2/H3 section header
- IF substantive AND entity note exists at `wiki/entities/{tickers,companies}/<name>.md`: add back-link to entity's `related:` (same Edit mechanics as primary pass)
- IF substantive AND entity note DOES NOT exist: do not back-link; add to "substantive entity mentions without vault notes" report (step 6)
- IF not substantive (single mention): skip entirely (neither back-link nor report)

#### Application (all back-link classes bundled in one atomic commit)

F11 flag already set in Phase C. All back-link Edits execute in batch. Narrow-stage onboarded doc + all successfully-back-linked files + (if applicable) knowledge-moc. Verify `git diff --cached --name-only` matches expected set byte-for-byte. Commit (ASCII only):

    vault(<category>): onboard <onboarded-stem> + symmetric back-links from <N> files

    /enrich routed <onboarded-path> via Rule <N> (<name>) and applied
    symmetric back-references per v7 principle: every wikilink in the
    onboarded doc's related: field becomes a reciprocal back-link on the
    target (subject to category + existence filters).

    Onboarded: <onboarded-path>
    Symmetric back-links:
    - <file>: related += <onboarded-stem>
    - ...
    Type-specific:
    - Atlas/_MOCs/knowledge-moc.md: Reference Document Status row added (if type: reference)
    - <entity-files>: related += <onboarded-stem> (substantive mentions)
    Skipped:
    - <file>: <reason (category excluded, already linked, missing target)>
    Substantive entity mentions without vault notes:
    - <entity-1>, <entity-2>, ... -- consider /ingest or manual creation

    Preserves: onboarded doc body byte-exact (sha256 gate).
    Preserves: back-linked file bodies byte-exact outside insertion sites
    (per-file before/after sha256 gate).

    Findings applied: F11, F14, F17.

**Phase K:** Clear F11 after commit succeeds + all gates pass.

Rollback: `git reset --soft HEAD~1` keeps changes staged for review; `git reset --hard HEAD~1` discards. Single atomic + full rollback is the safety net for autonomous-mode mistakes.

#### --backlink-only mode (v7 NEW)

Syntax: `/enrich <vault-path> --backlink-only`.

Purpose: retroactively apply symmetric back-links on an existing vault file. Useful when: doc was onboarded pre-v7 with narrower BL rules; a new peer file was added to the vault and should now reciprocally link; general hygiene pass.

Process:
1. Read target file; parse frontmatter
2. Extract current `related:` wikilinks
3. For each wikilink: run the primary back-link pass (above) as if the target were a freshly-onboarded doc
4. For substantive-entity back-links: scan body + check entity notes; apply if new matches exist
5. All idempotent: files already containing the reciprocal link are skipped silently
6. Report: per-file action (applied / skipped as no-op / skipped as excluded category)
7. Atomic commit with body:

        vault(links): --backlink-only pass on <target-stem>

        Retroactive symmetric back-link re-evaluation. Applied <N> new
        back-references; skipped <M> already-linked; skipped <P> excluded
        categories or missing targets.

        Files updated: <list>

        Findings applied: F11, F14, F17.

`--backlink-only` does not modify the target file itself (only peer files that should back-link TO it).

## Placement table (reference -- used by decision tree 3b)

| Content signal | Canonical path | Categories | Type |
|---|---|---|---|
| Reference doc | `Atlas/sources/<domain>/ref-<slug>.md` | [sources] | reference |
| Investment analysis single-ticker | `wiki/investing/analyses/<ticker>-analysis-<date>.md` | [wiki] | analysis |
| Portfolio synthesis | `wiki/investing/analyses/portfolio-synthesis-<date>.md` | [wiki] | analysis |
| Portfolio snapshot | `wiki/investing/snapshots/snapshot-<date>.md` | [wiki] | snapshot |
| Ticker entity | `wiki/entities/tickers/<TICKER>.md` | [entity] | ticker |
| Company entity | `wiki/entities/companies/<Name>.md` | [entity] | company |
| Research output | `wiki/research/<slug>-<date>.md` | [wiki] | research |
| Challenge | `wiki/research/challenges/<slug>-<date>.md` | [wiki] | challenge |
| Spark | `wiki/research/sparks/spark-<date>.md` | [wiki] | spark |
| Deep research prompt | `wiki/research/prompts/<slug>-<date>.md` | [wiki] | prompt |
| Raw dump | `wiki/research/dumps/<slug>-<date>.md` | [wiki] | research |
| Ingest report | `wiki/research/<slug>-ingest-<date>.md` | [wiki] | ingest |
| Briefing | `Calendar/decisions/briefings/briefing-<date>.md` | [decisions] | briefing |
| Decision record | `Calendar/decisions/decision-<slug>-<date>.md` | [decisions] | decision |
| Weekly review | `Calendar/weekly/<YYYY-Www>-review.md` | [weekly] | synthesis |
| Career research | `Efforts/career-search/research/<slug>-<date>.md` | [efforts] | research |
| Career application | `Efforts/career-search/applications/<company>-<date>/<file>.md` | [efforts] | output |
| Health analysis | `Efforts/health-protocol/analyses/<slug>-<date>.md` | [efforts] | analysis |
| Golf analysis | `Efforts/golf-practice/analyses/<slug>-<date>.md` | [efforts] | analysis |
| Thesis essay (ALWAYS CONFIRM) | `Atlas/concepts/investing/theses/thesis-<slug>.md` | [concepts] | thesis |
| Concept playbook | `Atlas/concepts/<domain>/<slug>.md` | [concepts] | playbook |
| External book/paper/article | `Atlas/sources/<domain>/<slug>.md` | [sources] | book \| paper \| article |
| People entity | `Atlas/people/<Name>.md` | [people] | profile \| stakeholder |
| MOC (CONFIRM new-file) | `Atlas/_MOCs/<domain>-moc.md` | [moc] | (no type) |

## Default status by category

| Category + type | Default status |
|---|---|
| [entity] * | active |
| [wiki] analysis/research/challenge/spark/prompt/ingest | active |
| [wiki] snapshot | complete |
| [efforts] * | active |
| [concepts] thesis/playbook | active |
| [sources] * | active |
| [decisions] briefing | complete |
| [decisions] decision | active |
| [weekly] synthesis | complete |
| [daily] | (no status field) |
| [moc] | active |

## Idempotency (--refresh)

`/enrich <vault-path> --refresh`: read frontmatter, bump `updated:` to today, re-detect tags additively (add new matches; never remove), re-detect related additively, body unchanged. No back-link re-evaluation (use `--backlink-only` for that).

Property: `--refresh` twice with no vault changes between produces zero diff after the first run (except `updated:` stays at today).

## Commit discipline (v7)

- F11 flag set in Phase C (before primary Write) -- single set point for the entire /enrich invocation
- F11 cleared in Phase K after all commits + gates pass
- All /enrich operations land as ONE atomic commit (onboard + symmetric back-links + type-specific additions). Title prefix per category: `vault(frontmatter):`, `vault(links):`, `vault(concepts):`, `vault(sources):`, `vault(moc):` depending on doc type.
- Large back-link sets (>=15 files): may split into two atomics -- (1) onboard, (2) back-references from N files -- at skill's discretion; report the split in output
- F14 narrow staging always
- Co-Authored-By suppressed per vault convention; verified absent via F17 `%B` extraction

## Invocation examples

### Example 1: Research-mode reference doc (autonomous end-to-end, v8 with /ingest recommendation)

The user attaches a 7,182-word research deep-dive output + `/enrich`.

Rule 1 matches. Placement: `Atlas/sources/investing/ref-orbital-compute-deep-dive.md`. No collision. Body sha256 verified. F11 set in Phase C. Detected related: [[investing-moc]], [[thesis-orbital-compute]], [[ref-sector-benchmarks]], [[ref-macro-landscape]], [[doctrine.template]] (all exist).

Symmetric back-links applied: 5 primary + knowledge-moc row + 7 entity back-links (NVDA, AMD, MU, AVGO, VRT, AMAT, LRCX). Total 14 paths in atomic commit.

/ingest recommendation (v8):
  - T1 Fact density: HIGH (22 markers/1000w: dollar amounts, percentages, ratio/margin/capex mentions)
  - T2 Multi-entity: HIGH (7 substantive entities: NVDA, AMD, MU, AVGO, VRT, AMAT, LRCX)
  - T3 Entity-level relevance: YES (Rule 1 reference doc)
  - Verdict: YES
  - Recommended next step:
      /ingest Atlas/sources/investing/ref-orbital-compute-deep-dive.md
  - Running /ingest will: distill 7 substantive entity discussions into
    updates on NVDA/AMD/MU/AVGO/VRT/AMAT/LRCX entity notes (creating
    any missing), writing an ingest report to wiki/research/.

User input: ONE interaction (attach + /enrich). If /ingest recommendation is acted on: one additional copy-paste.

### Example 2: Autonomous replacement of existing thin ref

The user attaches a 7,182-word geopolitical-framework research output + `/enrich`.

Rule 1 fires. Target: `Atlas/sources/investing/ref-geopolitical-framework.md`. Collision (385w exists). Ratio 18.7x >= 1.0x -> AUTONOMOUS REPLACE (report per section 3e format). Write proceeds. Symmetric back-link pass + type-specific additions + substantive entity back-links as in Example 1. Applied atomically. ONE user interaction.

### Example 3: Concept playbook routing (v7 symmetric pass + v8 /ingest recommendation)

The user attaches a 2,820-word geopolitics playbook + `/enrich`.

Rule 18 matches. Placement: `Atlas/concepts/investing/geopolitics-playbook.md`. No collision.

Detected related: [[investing-moc]], [[thesis-orbital-compute]], [[ref-geopolitical-framework]], [[ref-macro-landscape]], [[macro-outlook]] (all exist).

Symmetric back-links applied: 5 primary (all in BACKLINKABLE_CATEGORIES). Total 6 paths in atomic commit.

Substantive entity gaps: LMT, XAR, VDE, IAU, ITA, PPA (mentions in dedicated sections; no entity notes exist).

/ingest recommendation (v8.1 binary):
  - T1 Fact density: MEDIUM (~11 markers/1000w: dollar amounts from backlog + ETF weights + conflict-era pricing)
  - T2 Multi-entity: HIGH (6 substantive entities: LMT, XAR, VDE, IAU, ITA, PPA)
  - T3 Entity-level relevance: MAYBE (Rule 18 concept playbook)
  - Verdict: YES (T3=MAYBE + T2=HIGH -> binary collapses to YES per v8.1 SOTA rule)
  - Recommended next step:
      /ingest Atlas/concepts/investing/geopolitics-playbook.md
  - Running /ingest will create 6 entity notes at wiki/entities/tickers/{LMT,XAR,VDE,IAU,ITA,PPA}.md from playbook content, serving as back-link targets and accretion points for future doc content. Content per entity is playbook-level (thin one-liners to one-paragraph framing); /invest <ticker> or further /enrich cycles will deepen them over time. Aligned with SOTA compounding: thin stubs > missing entities.

User input: ONE interaction (attach + /enrich). The /ingest recommendation is surfaced for the user's judgment call on entity-creation leverage.

### Example 4: Target override

`/enrich <source> --to wiki/research/custom-slug-2026-04-22.md` -- bypass autonomous routing; use user path; all gates + symmetric back-links still apply.

### Example 5: Refresh existing

`/enrich wiki/research/existing-file.md --refresh` -- bump updated:, re-detect tags/related additively. Body unchanged. No back-link re-evaluation (use `--backlink-only` for that).

### Example 6: Thesis essay routing (Rule 17 confirm exception)

The user attaches a conviction essay + `/enrich`.

Rule 17 matches (first-person conviction voice; argues-for-position; length LONG). All REQUIRED met. Rule 17 is the categorical confirmation exception -- requires explicit y before write regardless of match strength.

    Placement:       Atlas/concepts/investing/theses/thesis-<slug>.md
    Rule fired:      Rule 17 -- Thesis essay (CONFIRM EXCEPTION)
    REQUIRED matched:
      - first-person conviction voice: 7 instances in body
      - argues-for-position: Why + Evidence + Invalidation + Current Read sections present
      - length LONG: 4,200 words
    IDENTIFYING markers:
      - H1 title pattern matches "Thesis:" framing
    Rules checked before this one (did not fire):
      - Rule 1 reference doc: REQUIRED failed (first-person voice present; no numbered-section TOC)
      - Rule 18 concept playbook: REQUIRED failed (first-person conviction voice excluded by rule)

    Thesis essays are sacred conviction artifacts per the reader/writer
    stance. Rule 17 is the single categorical exception to autonomous
    routing.
    Proceed? [y/N]

### Example 7: Preview

`/enrich <source> --preview` -- run steps 1-7 in planning mode; report full plan including symmetric back-links and entity gaps. No write.

### Example 8: Retroactive back-link re-evaluation (--backlink-only)

The user notices an existing concept playbook lacks back-links to peer refs added to the vault since its onboarding. Runs:

    /enrich Atlas/concepts/investing/geopolitics-playbook.md --backlink-only

Skill reads target; extracts current related: (investing-moc, thesis-<slug>, ref-geopolitical-framework, ref-macro-landscape, macro-outlook); for each, check if the reciprocal back-link exists:

- investing-moc.md: related already contains [[investing-moc]] -> SKIP (already linked)
- thesis-<slug>.md: already linked -> SKIP
- ref-geopolitical-framework.md: already linked -> SKIP
- ref-macro-landscape.md: already linked -> SKIP
- macro-outlook.md: already linked -> SKIP

All already-linked -> no-op. Clean report, no commit.

If new peer files were added to the vault since original enrich OR related: evolved: applies new back-links atomically. Idempotent.

### Example 9: Skip back-linking

`/enrich <source> --no-backlink` -- write onboarded doc only; skip back-link pass. Useful for quick dumps.

### Example 10: /deep-generated Research output with target_path (v9 explicit placement)

The user downloads a claude.ai Research mode output (generated from a /deep v2 prompt) and attaches + types /enrich. Source frontmatter includes:

    ---
    categories: [sources]
    type: reference
    target_path: Atlas/sources/investing/ref-orbital-compute-deep-dive.md
    created: 2026-04-22
    updated: 2026-04-22
    status: active
    confidence: high
    tags:
      - topic/orbital-compute
      - topic/semiconductor-cycles
      ...
    related:
      - "[[investing-moc]]"
      - ...
      ...
    ---

v9 reads `target_path` in Phase 1.a; validates path-guards + extension + canonical-top-level; sets `explicit_target`. Phase 3 uses `explicit_target` directly (skips Rule 1-22). Placement: `Atlas/sources/investing/ref-orbital-compute-deep-dive.md` (exact /deep intent; no slug drift). Symmetric back-links fire on `related:` peers; knowledge-moc row added (type: reference); /ingest YES recommendation surfaces. Atomic commit. ONE user interaction; /deep-intended filename preserved end-to-end.

## Related skills

- `/ingest` -- claim extraction + vault distribution (transformational complement; use to create missing entity notes flagged by /enrich's entity-gap report)
- `/create-skill`
- `/vault` -- maintenance + invariant checks


## Phase O.0 -- Pre-commit /vault audit gate (v2.0; CAT-3 prevention-architecture parity)

After composing all target file modifications IN MEMORY but BEFORE atomic write:
1. Write each composed file to a tmp dir under `wiki/research/test-tmp/.precheck/enrich-<slug>/`
2. Run `python tools/skill-precheck.py <tmp-files...> --skill /enrich`
3. Parse exit code: 0 -> proceed; 2 -> HALT with diagnostic
4. Body-scope wikilink validation: per /retro v2.2 Phase D pattern, scan composed body text for unresolved `[[<target>]]` and mechanically de-link unresolved targets (vault-resolved keep / MEMORY_PREFIXES rewrite as `[[memory:<stem>]]` / placeholder leave / else strip). Fence-aware (skip ``` fenced + `inline code`).
5. Bypass: `CLAUDE_VAULT_BYPASS_VALIDATOR=1` (logged to `.claude/state/bypasses-<date>.log`)

Defense-in-depth on top of PreToolUse pre-write-validator.py + PostToolUse wikilink-check.py / frontmatter-check.py / orphan-check.py. The Phase O.0 gate prevents broken composition from reaching disk in the first place.

**/enrich-specific risk:** if source body contains broken wikilinks (preserved byte-exact per /enrich design), Phase O.0 surfaces this as a user-prompt: "source has N broken wikilinks; onboard anyway?" Do NOT mutate source body without explicit user confirmation.

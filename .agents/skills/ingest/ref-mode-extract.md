## When to use vs not

Use `/ingest` when: "I have a fact-dense source. Distill its claims into vault entity notes." Typically invoked via /enrich's YES recommendation.

Not for:
- Preserving a document whole (that is /enrich)
- Creating a single entity with no source (use _templates/entity.md directly)
- Editing bodies of existing files manually (direct Edit)
- Time-bound content (briefings, daily notes)

## Invocation

### Mode routing (Pattern 6 deterministic; invocation modes)

| Syntax | Behavior |
|---|---|
| `/ingest <vault-path>` | Read source from vault; distribute claims |
| `/ingest <external-path>` | External file; distribute; leave source untouched |
| `/ingest <url>` | Fetch URL via WebFetch (fallback: `curl -sk` per AGENTS.md); extract; distribute |
| `/ingest --from clipboard` | Read pasted content |
| `/ingest <source> --preview` | Dry-run; show plan; no writes |
| `/ingest <source> --entity-only <TICKER>` | Narrow re-ingest; only one entity's claims evaluated |

## Discipline and quality

### Execution Rules

- **Subagent dispatch is MANDATORY when specified by phase AND the running harness exposes an Agent tool** (Phase E.0 dispatches `claim-distributor` per entity; Phase F.0 dispatches `vault-classifier-sweep` pre-commit gate). Pre-emptive skip based on judgment ("inline logic is fine", "dispatch overhead not worth it") is FORBIDDEN. The subagent decides applicability via its own return contract; the parent skill dispatches and validates the return. Legitimate fallback fires ONLY on (a) contract violation -- subagent return missing required JSON fields, (b) actual dispatch failure -- timeout, rate limit, tool-denial, hard subagent crash, OR (c) NO Agent tool in the running harness -- the documented inline fallback runs verbatim as the NORMAL path and is reported as `inline-no-Agent-tool`, which is NOT a DEVIATION. Pre-emptive skip (Agent tool present, dispatch not attempted) surfaces in the Phase F audit report as **DEVIATION** (not "fallback"). Quality preserved by additive design: existing inline Phase E dedup + contradiction-tiering + section-mapping logic remains intact as legitimate-failure fallback.
- Subagent legs (`claim-distributor`, `vault-classifier-sweep`) carry their own model pins in their agent definitions wherever an Agent tool exists. No phase of this skill branches on model identity.

### Quality Rules

- Claim extraction is deterministic (Phase D markers), never impressionistic: every claim carries a marker_signature so LLM text variance does not produce spurious duplication.
- Body preservation on every entity update: before/after sha256, diff strictly additive outside insertion sites, each new claim_text present exactly once post-edit.
- Inline provenance on every distributed claim: `- {claim_text} ({grade}, per [[{source-stem}]])`. Grades HIGH/MEDIUM/LOW are carried VERBATIM -- no A/B/C/D rescale.
- Contradictions are tiered, never silently overwritten: Tier 1 auto-resolve (strictly newer + equal-or-higher authority; prior marked superseded) / Tier 2 flag both visibly / Tier 3 reject with a report entry.
- Entity-note updates require at least one MEDIUM or HIGH claim for that entity; an all-LOW entity gets a report entry and no graph mutation.
- Entity creation only on the substantive threshold (>=3 mentions OR a dedicated H2/H3 section); ambiguous (exactly 2 mentions, no dedicated section) resolves conservatively to NO.
- Tag vocabulary guardrail: ALLOWED_TAG_NAMESPACES = {topic, ticker, company, thesis}. HALT on drift; never coerce.
- Path-guards are mechanical, not preference: NEVER write `.raw/`, `private/`, `_quarantine/`, `finance/`, `credentials/`, `.git/`, `.claude/hooks/`, `.claude/state/`.
- F11 Phase C discipline mandatory: set `.claude/state/auto-commit-disabled` BEFORE any Write/Edit; clear ONLY in Phase K after the atomic commit succeeds.
- Pattern 22 ASCII-only on all new content and commit bodies (em-dash -> `--`, curly quotes -> straight, ellipsis -> `...`); Co-Authored-By suppressed and F17-verified.
- Idempotency is a spec requirement, not a nicety: a re-run on the same source + same vault state produces zero diff and no commit.

## Process

### Phase A -- Pre-flight

Read source (by mode). Record source_path, source_body_sha256, source_body_word_count. Load vault indexes: TICKERS, COMPANIES, ALL_BASENAMES. Load _templates/entity.md into memory (for entity body template grounding in Phase F).

### Phase B -- State-transition model (print only)

Print expected: entity creations, entity updates, contradictions, report artifact path. This runs before F11 set so the user can abort before any writes. The print format is deterministic and machine-parseable for audit.

**Worked example of Phase B output** (geopolitics-playbook case):

    /ingest state-transition model
    ==============================
    Source: Atlas/concepts/investing/geopolitics-playbook.md
    Source sha256: 15781874c254559f828f57a1fe4c65a5d07e4a81f465acf36af4faee35b3a6c7
    Source word count: 2,781

    Expected Phase D extraction: ~40 claims across 7 thematic clusters

    Expected Phase E actions:
      - Entity creations (substantive-threshold met, >=3 mentions OR dedicated section):
          LMT, RTX, XAR, ITA, PPA, VDE, IAU  (7 new)
      - Entity updates (existing entities with new claims):
          (none -- zero vault-ticker overlap with playbook entities)
      - Sub-threshold (deferred):
          GD (1 mention), XOM/CVX (VDE-weight context only), Rheinmetall (European, non-vault)
      - Contradictions expected: 0 (playbook scope complementary to ref-geopolitical-framework)

    Expected Phase F writes:
      - 7 new entity notes at wiki/entities/tickers/
      - 1 ingest report at wiki/research/geopolitics-playbook-ingest-`<today>`.md
      - 1 MOC back-link edit on Atlas/_MOCs/investing-moc.md (adding 7 entity stems)
      - 1 source related: extend on Atlas/concepts/investing/geopolitics-playbook.md
        (7 entity stems + 1 ingest-report stem)

    Expected Phase G commit: 10 paths; title "vault(ingest): geopolitics-playbook -- 7 entity stubs + ingest report"

    Proceed? (Phase C will set F11 flag; any failure between C and G triggers F.halt.)

If user aborts here: no F11 set, no writes, clean exit. If user confirms (or --preview flag overrides), proceed to Phase C.

### Phase C -- F11 flag set (MANDATORY SPEC REQUIREMENT)

Create `.claude/state/auto-commit-disabled` BEFORE any Edit/Write on tracked files -- the marker the per-write auto-commit hook reads; a harness without that hook honors the same lifecycle by instruction ([[ref-execution-discipline]]). Single flag covers entire invocation.

### Phase D -- Deterministic claim extraction

Scan source body. Each claim has:
- claim_text (short declarative)
- entity (ticker/company/thesis or "general")
- marker_type (numeric / qualitative / dated / relational)
- marker_signature (tuple: (entity_stem, metric_type, value, date) -- normalized for dedup across LLM variance)
- claim_grade (HIGH/MEDIUM/LOW per rules below)
- source_paragraph_ref (line number or section header)
- section_target (per Phase E mapping rule)

Claim-grading:
- HIGH: specific number + specific date + primary source cited
- MEDIUM: number without date, or dated without number, or secondary-source-cited
- LOW: qualitative without quantitative anchor

Marker detection regexes: numeric `\$[\d][\d,.]*(B|M|K)?` or `\d+(\.\d+)?%`; dated `\d{4}-\d{2}-\d{2}`, `Q[1-4] \d{4}`; relational (from X to Y, up N%, A > B).

Marker_signature example: "LMT backlog $194B Q4 2025" -> ("LMT", "backlog", 194, "2025-Q4"). "Lockheed's order book totals $194 billion in the fourth quarter of 2025" also -> same signature. Both dedup-equivalent despite text variance. This is the LLM-variance resistant dedup mechanism.

**Worked example of Phase D output** (single claim extracted from the geopolitics-playbook):

    claim_text: "Lockheed Martin's backlog grew to $194B end-2025 with 6% sales growth; book-to-bill 1.6 in Q4 2024"
    entity: "LMT"
    marker_type: numeric (+ dated)
    marker_signature: ("LMT", "backlog", 194, "2025-end")
    claim_grade: HIGH  (specific number + specific date + Tier 1 source context)
    source_paragraph_ref: "## The defense cycle pays in backlog, not bookings" (line ~43)
    section_target: "## Financial signals"  (backlog -> Financial signals per mapping)

When re-ingesting a future source that says "LMT order book reached $194 billion by the end of 2025", the marker_signature extraction yields the same tuple, and dedup skips the duplicate claim without requiring exact text match. This is why marker_signature matters: LLM text variance across extractions does not produce spurious claim duplication in entity notes.

**Claim atomicity**: compound claims must be decomposed before signature extraction. "Revenue grew 22% driven by data center strength" is two claims: (entity, "revenue-growth", 22%, date) + (entity, "data-center-narrative", qualitative). Each gets its own section_target.

### Phase E -- Vault-side evaluation per entity

For each entity in claim_list:

#### Phase E.0 -- DELEGATED dispatch to `claim-distributor` subagent (PREFERRED path where an Agent tool exists; Phase C wiring 2026-05-02)

**MANDATORY when the harness exposes an Agent tool** (per Execution Rules): dispatch first, no pre-emptive skip. Subagent handles N/A returns gracefully -- if entity is sub-threshold or claims dedup completely, subagent returns `zero_new_claims_short_circuit: true` which is a SUCCESSFUL dispatch.

Use the Agent tool with subagent_type `claim-distributor`. Pass input: `{entity_path: "wiki/entities/<type>/<entity>.md", claims: [<entity-scoped subset of claim_list>], session_id: "<current-session-id>"}`. The subagent reads the existing entity, computes pre_sha256, applies marker-signature dedup, tiers contradictions (Tier 1 auto-resolve / Tier 2 flag / Tier 3 reject / defer), maps each claim to canonical section, and returns JSON edit-ops with body-preservation invariants. Per-claim field map to the distributor schema (F028): `claim_text` -> `fact`, source-stem -> `source`, claim/source date -> `source_date`, `claim_grade` -> `source_grade` (HIGH|MEDIUM|LOW carried VERBATIM -- NO A/B/C/D rescale; the same token is written into the entity-note `(<grade>, per [[source]])` provenance), `section_target` -> `category_hint`, `prov` -> `prov` pass-through.

Validate subagent return:
- JSON with `entity_path`, `edits[]`, `body_preservation` (pre_sha256 + expected_post_sha256_outside_inserts), `zero_new_claims_short_circuit`, `summary` counts
- pre_sha256 matches current entity body hash (re-compute and compare; HALT on mismatch)
- Each edit `op` has anchor specification

If `zero_new_claims_short_circuit: true`: skip Phase F entity Edit for this entity entirely; continue to next entity in loop. Phase F.5 report emits "entity unchanged (all N claims deduped per claim-distributor)".

On contract violation OR dispatch failure: fall through to the inline evaluation logic below (steps 1-4) for this entity. Surface fallback in Phase F audit.

On dispatch success: queue the returned `edits[]` for Phase F atomic apply. Continue to next entity. Skip the inline evaluation steps below for this entity.

**No Agent tool in the running harness:** skip the dispatch and run the inline evaluation below (steps 1-4) verbatim as the NORMAL path for every entity, holding the same contract the subagent would have returned -- marker-signature dedup, Tier 1/2/3 contradiction tiering, deterministic claim-to-section mapping, and the before/after sha256 body-preservation invariant applied at Phase F.1. Report `mode: inline-no-Agent-tool` in the Phase F audit; this is a harness capability gap, NEVER a DEVIATION and not a "fallback". Skipping the dispatch where an Agent tool DOES exist remains a DEVIATION. The per-entity evaluation itself is MANDATORY either way -- only the mechanism varies.

#### Inline evaluation (runs when the Phase E.0 dispatch failed for this entity, AND as the normal path on a harness with no Agent tool)

1. **Does entity note exist?** Check ALL_BASENAMES.

2. **If exists**:
   - Load entity_body_bytes; parse existing claims and marker_signatures
   - For each new claim:
     - **Dedup (marker signature + text)**: signature-match OR substring-match -> SKIP (log "already present")
     - **Contradiction detection** (same entity+metric, different value):
       - Tier 1 auto-resolve: new claim has strictly newer date AND equal-or-higher authority -> append new + mark existing with "(superseded `<new-date>` per source-stem)"
       - Tier 2 flag: similar authority -> append both visibly + NOTE
       - Tier 3 reject: new claim has clearly lower authority -> skip + add to "rejected claims" in report
     - **Claim-to-section mapping (deterministic routing)**:
       - Revenue, backlog, margin, cash flow, EPS, guidance -> "## Financial signals"
       - Thesis-relevant (supports or challenges thesis) -> "## Thesis Fit"
       - Risk mentions (customer concentration, regulatory, supply chain) -> "## Risks"
       - Catalyst / earnings / product launch / policy event -> "## Catalysts"
       - Dated event (acquisition, strike, partnership) -> "## Recent" with date subheader
       - Fallback (unmapped): "## Claims from source-stem (`<date>`)"
     - If target section absent in entity body: CREATE section header + insert claim
     - If target section present: APPEND claim under existing section (preserve ordering within section: newest first)

3. **If entity note does not exist** AND substantive threshold met (>=3 mentions OR dedicated H2/H3 section in source):
   - CREATE_NEW: compose canonical entity grounded in _templates/entity.md

4. **If not exists AND sub-threshold**:
   - SKIP with log; add to "sub-threshold entities" section of report

### Phase F -- Atomic apply (updates + creations + MOC back-links + source audit chain + report)

Gate first (F.0), then apply the whole batch: entity updates (F.1), entity creations (F.2), MOC back-links (F.3), source audit chain (F.4), ingest report (F.5). Any failure mid-batch routes to F.halt.

#### Phase F.0 -- DELEGATED pre-commit dispatch to `vault-classifier-sweep` (PREFERRED gate where an Agent tool exists; Phase C wiring 2026-05-02)

**MANDATORY when the harness exposes an Agent tool** (per Execution Rules): dispatch first, no pre-emptive skip.

Use the Agent tool with subagent_type `vault-classifier-sweep`. Pass input: `{scope: "all"}`. Expected return: JSON with 9 classifier keys + `totals` + `score` + `score_floor_check`. If `score_floor_check: BREACH` (<90) OR `gate >0`: HALT before atomic apply; surface findings; user must repair before /ingest can proceed.

Validate subagent return per its contract; on contract violation or dispatch failure fall through to direct `python tools/vault-audit.py --json` invocation as the fallback gate. Surface dispatch outcome in Phase F.5 report.

**No Agent tool in the running harness:** skip the dispatch and run the gate INLINE as the NORMAL path -- `python tools/vault-audit.py --json` directly, with identical HALT semantics (`gate` count >0 OR score below the floor -> HALT before atomic apply). Report `mode: inline-no-Agent-tool` -- NEVER a DEVIATION. The gate itself is MANDATORY either way; only the mechanism varies.

#### Phase F.1 onward -- Atomic apply (continues unchanged)

**F.1 Entity updates** (for each existing entity getting new claims):
- Pre-edit: read entity_body_bytes -> before_sha256
- Compose Edit per section_target; inline provenance format:

      - {claim_text} ({grade}, per {source-stem})

  For contradiction Tier-1 resolution:

      - {new_claim_text} ({grade}, per {source-stem})
        (supersedes prior: {old_claim_text} per {old-source-stem})

- Apply Edit tool
- Post-edit gates (MECHANICAL):
  - before_sha256 != after_sha256
  - Each new claim_text appears exactly once post-edit
  - Diff strictly additive (except Tier-1 supersede annotations which are text additions)
  - Frontmatter `updated:` bumped; `related:` extended with source-stem if absent (idempotent); other fields byte-exact

**F.2 Entity creations** (for each new entity meeting substantive threshold):
- Compose canonical frontmatter grounded in _templates/entity.md:

      ---
      categories: [entity]
      type: {ticker|company}
      {ticker|company}: `<NAME>`
      sector: `<derived-from-claim-context>`
      thesis: [`<detected-thesis-tags>`]
      accounts: []
      status: active
      created: `<today>`
      updated: `<today>`
      aliases: [`<detected-aliases>`]
      tags:
        - {ticker|company}/`<NAME>`
        - topic/`<primary-topic>`
      related:
        - "{source-stem}"
        - "{domain-moc-stem}"
        - "{relevant-ref-doc-stem-if-any}"
      ---

- Body: H1 + overview paragraph synthesized from HIGH/MEDIUM claims + section placeholders matching template (canonical strict order: ## Financial signals, ## Thesis Fit, ## Risks, ## Catalysts, ## Recent, ## Position, ## Sources) + initial claims populated under appropriate sections per Phase E mapping
- Tag vocabulary guardrail: HALT if any emitted tag namespace outside {topic, ticker, company, thesis}
- Write via Write tool

**Worked example of Phase F.2 entity creation** (using the geopolitics-playbook LMT case as template):

    ---
    aliases:
      - Lockheed Martin
      - lockheed-martin
    categories: [entity]
    type: ticker
    tags:
      - ticker/LMT
      - topic/defense-sector
    status: active
    created: 2026-04-21
    updated: 2026-04-21
    related:
      - "geopolitics-playbook"
      - "investing-moc"
      - "ref-geopolitical-framework"
    ticker: LMT
    sector: Defense (Aerospace & Defense)
    ---

    # LMT -- Lockheed Martin

    **Sector:** Defense (Aerospace & Defense)
    **Type:** Individual stock (US defense prime)

    ## Overview
    <synthesized from HIGH/MEDIUM claims: 1-paragraph framing>

    ## Financial signals
    - Backlog trajectory: $150B pre-2022-invasion -> $176B end-2024 -> $194B end-2025 (HIGH, per geopolitics-playbook)
    - Book-to-bill ratio: 1.6 in Q4 2024 (HIGH, per geopolitics-playbook)
    - Sales growth: 6% (MEDIUM, per geopolitics-playbook)

    ## Thesis Fit
    - Backlog-to-revenue conversion locked through 2030 regardless of political outcome (HIGH, per geopolitics-playbook)

    ## Risks
    <populated if source has risk claims>

    ## Catalysts
    <populated if source has catalyst claims>

    ## Recent
    <dated event claims>

    ## Position
    <current shares + cost-basis snapshot; last decision date; doctrine-ceiling proximity>

    ## Sources
    - geopolitics-playbook (2026-04-21)

Post-write: ruamel.yaml parse gate + tag-vocabulary guardrail assertion + sha256 record for future idempotency comparison.

**F.3 MOC back-linking on new entities** (v2 final -- parallel to /enrich BL1):
For each newly-created entity, apply narrow Edit to the domain MOC (investing-moc.md for ticker entities; determined by entity's primary domain) adding entity wikilink to MOC's `related:` field. Idempotent check: skip if already present. Per-MOC-file before/after sha256 gate.

**F.4 Source audit chain** (v2 final -- audit chain closure via ingest-report back-link):

The source document's `related:` field is extended with TWO categories of wikilinks:

1. **Symmetric entity back-links** (matches v1 behavior): each newly-created entity's stem `[[<entity-stem>]]` is appended. This makes the source discoverable from each entity and vice versa.

2. **ingest-report back-link** (NEW in v2 -- closes audit chain): the ingest report wikilink `[[<source-stem>-ingest-<date>]]` is appended. This closes the audit chain: source -> report -> entities. From the source doc, a reader can now trace which ingest run extracted its facts + which entity-level distributions were made.

Per-source before/after sha256 gate. Idempotent: skip already-present entries. The ingest-report back-link is the critical v2 addition -- without it, you could read the source and not know an ingest report existed; with it, the audit trail is complete and bidirectional.

**F.5 Ingest report composition**:
Write to `wiki/research/<source-stem>-ingest-<date>.md` with canonical frontmatter:

      ---
      categories: [wiki]
      type: ingest
      created: `<today>`
      updated: `<today>`
      status: active
      confidence: <aggregate-HIGH-if-majority-HIGH-else-MEDIUM-else-LOW>
      tags:
        - topic/`<primary-topic-1>`
        - topic/`<primary-topic-2>`
        ...
      related:
        - "`<source-stem>`"
        - "`<each-entity-stem>`"
        ...
      ---

      # Ingested: `<source-title>`

      ## Source
      - Path, sha256, word count, confidence

      ## Claims extracted summary
      <N> claims across <M> thematic clusters.

      ## Claims by entity
      ### `<ENTITY_STEM>`
      - {claim_text} ({grade}) -- section: `<section_target>` -- ref: "`<paragraph_ref>`"
      ...

      ## Contradictions
      ### Tier 1 auto-resolved (`<count>`)
      - {new} supersedes {old} per `<date-differential>`
      ### Tier 2 flagged (`<count>`)
      - {new} vs {old}: both present; manual review advised
      ### Tier 3 rejected (`<count>`)
      - {new} (rejected: lower authority than <existing source>)

      ## Entity actions
      - Created: `<list>`
      - Updated: <list with new-claim counts>
      - Sub-threshold (deferred): <list with mention counts>

      ## Follow-ups
      `<free-form>`

The report also carries this run's dispatch tally (one line, mandatory): dispatched / re-dispatched / inline-fallback / inline-no-Agent-tool / DEVIATION.

### Phase F.halt -- Mid-batch failure handling (v2 final)

If any Edit/Write in Phase F fails (assertion failure, path-guard block, sha256 mismatch, Edit tool old_string mismatch):
- IMMEDIATE HALT. Do not continue to remaining Edits.
- F11 flag STAYS ON.
- Do NOT commit. Any already-applied Edits remain in working tree UNSTAGED.
- Report to user:
  - Which Edits succeeded (applied to working tree)
  - Which Edit failed (with failure reason: e.g., "Edit on NVDA.md: old_string not found")
  - Which Edits were not attempted
  - Current staged state (should be empty or prior atomic)
- User decides: `git checkout -- <paths>` to roll back partial applies, OR fix the failure and re-invoke /ingest (idempotency will skip successful partial applies).

### Phase G -- Commit + verification

If Phase F completed without halt:
- Narrow-stage (F14):
  - wiki/research/`<source-stem>`-ingest-`<date>`.md (new)
  - Each new entity note (new)
  - Each updated entity note (modified)
  - Each domain MOC that received new-entity back-link (modified)
  - source_path (modified)
- Assert `git diff --cached --name-only` matches expected set byte-for-byte
- Commit with body (ASCII only; format per v2 commit-body-template in commit message)
- Assert Co-Authored-By absent via F17 %B extraction + F16 bytes compare

### Phase K -- F11 clear

Unlink `.claude/state/auto-commit-disabled`. Assert absence.

### Phase O.0 -- Pre-commit /vault audit gate (v2.0; CAT-3 prevention-architecture parity)

After composing all target file modifications IN MEMORY but BEFORE atomic write:
1. Write each composed file to a tmp dir under `wiki/research/test-tmp/.precheck/ingest-<slug>/`
2. Run `python tools/skill-precheck.py <tmp-files...> --skill /ingest`
3. Parse exit code: 0 -> proceed; 2 -> HALT with diagnostic
4. Body-scope wikilink validation: per /retro v2.2 Phase D pattern, scan composed body text for unresolved `[[<target>]]` and mechanically de-link unresolved targets (vault-resolved keep / MEMORY_PREFIXES rewrite as `[[memory:<stem>]]` / placeholder leave / else strip). Fence-aware (skip ``` fenced + `inline code`).
5. Bypass: `CLAUDE_VAULT_BYPASS_VALIDATOR=1` (logged to `.claude/state/bypasses-`<date>`.log`)

Defense-in-depth on top of PreToolUse pre-write-validator.py + PostToolUse wikilink-check.py / frontmatter-check.py / orphan-check.py. The Phase O.0 gate prevents broken composition from reaching disk in the first place.

**/ingest-specific risk:** /ingest mutates entity graph aggressively (>=7 new entity notes per run + N updates + MOC + source); without Phase O.0, claim text containing prospective wikilinks could persist into entity bodies.

## Idempotency (v2 spec requirement)

Re-running /ingest on same source + same vault state produces zero diff:
- Phase D claim_list is deterministic (same markers -> same signatures even with LLM text variance)
- Phase E dedup matches all prior claims by signature OR text
- No Edits composed
- No new entities created
- source `related:` already contains entity stems + ingest report stem -> no source Edit
- Ingest report: Glob `wiki/research/<source-stem>-ingest-*.md`; if a prior report exists with matching source_sha256, SKIP writing new report; emit "/ingest is idempotent; no changes."

## Path-guards (MECHANICAL)

NEVER write to: `.raw/`, `private/`, `_quarantine/`, `finance/`, `credentials/`, `.git/`, `.claude/hooks/`, `.claude/state/`. HALT if extraction would target these.

## Tag vocabulary guardrail

ALLOWED_TAG_NAMESPACES = {topic, ticker, company, thesis}. HALT if any emitted tag on a new entity uses other namespace.

## Coordination with /enrich

`/enrich` and `/ingest` are complementary skills sharing infrastructure. `/enrich` is preservational (source doc placed whole with canonical frontmatter + bidirectional linking); `/ingest` is transformational (source doc's facts distributed into entity-level claims). Together they form the standard onboarding pipeline for fact-dense content.

### Shared infrastructure (identical semantics in both skills)

- **Vault indexes:** TICKERS (basenames of wiki/entities/tickers/*.md), COMPANIES (basenames of wiki/entities/companies/*.md), ALL_BASENAMES (every .md basename in vault, excluding path-guarded + gitignored). Loaded once per invocation.
- **BACKLINKABLE_CATEGORIES:** {moc, sources, wiki, entity, concepts, efforts, decisions, weekly, people}. Excludes [daily] (hook-created, different schema) and [meta] (infrastructure).
- **Tag vocabulary guardrail:** ALLOWED_TAG_NAMESPACES = {topic, ticker, company, thesis}. HALT on drift. Never emit `domain/*`, `type/*`, or bare tags.
- **F11 Phase C discipline:** `.claude/state/auto-commit-disabled` flag set BEFORE any Edit/Write, cleared in Phase K post-commit. Prevents the per-write auto-commit hook from firing mid-flow.
- **Path-guards:** NEVER write to `.raw/`, `private/`, `_quarantine/`, `finance/`, `credentials/`, `.git/`, `.claude/hooks/`, `.claude/state/`. Architectural, not preference.
- **ASCII-only commit bodies:** all commit messages use ASCII only. No em dashes, no curly quotes, no bullet unicode.
- **Co-Authored-By suppressed:** vault convention; verified absent post-commit via F17 `%B` extraction.
- **F14 narrow staging:** explicit `git add <path>` for each intended file; never `git add -A`; assert `git diff --cached --name-only` matches expected set before commit.

### Typical workflow (paired invocation)

1. **Attach doc + `/enrich <source>`** -> doc routed to canonical path via deterministic 22-rule placement; canonical frontmatter composed; body preserved byte-exact (sha256-verified); symmetric back-links applied on peer files (every wikilink in source's `related:` gets reciprocal back-link on the target, subject to category + existence filters); the /ingest recommendation emitted as a binary YES/NO verdict.

2. **`/ingest <source>` (when that verdict = YES)** -> Phase A-G execute claim distribution. Entity notes updated or created per substantive-mention threshold. Source `related:` extended with entity stems AND ingest-report wikilink (audit chain closure). MOC back-linked on new entities.

### Post-pipeline state

After both skills run on a single source:
- **Source discoverability:** the doc is referenced by its peer files (MOCs, refs, theses, concepts) via `/enrich`'s symmetric back-links.
- **Entity graph enrichment:** each substantive entity mention in the source is now reflected in a dedicated entity note, with the claim routed to the correct section (Financial signals / Thesis Fit / Risks / Catalysts / Recent) per the claim-to-section mapping rules.
- **MOC index completeness:** newly-created entities are referenced from the domain MOC (investing-moc for tickers, etc.), making them discoverable via top-down navigation.
- **Audit trail:** the source `related:` field contains a back-link to the ingest report, which in turn lists every extracted claim with per-fact source provenance. A reader can trace any vault fact back to its originating source document.
- **Compounding:** future `/enrich` or `/ingest` invocations on related sources automatically back-link through the existing entity graph, deepening connections without manual wiring.

### Division of concerns

| Concern | /enrich | /ingest |
|---|---|---|
| Source document placement | Yes | No (source stays where /enrich put it) |
| Source frontmatter composition | Yes | Extends `related:` only |
| Source body preservation | Byte-exact (sha256) | Untouched |
| Peer-file back-linking | Symmetric via related: | No (indirect via entity back-links) |
| Entity note creation | No | Yes (substantive threshold) |
| Entity note updates (new claims) | No | Yes (dedup + contradiction-resolve) |
| MOC back-linking | Per /enrich BL1 | Per v2 F.3 (parallel rule) |
| Ingest report generation | No | Yes (wiki/research/) |
| /ingest recommendation | verdict emitted | N/A (target of recommendation) |

## Examples

### Example 1: Reference doc updating existing entities (theme-alpha case)

`/ingest Atlas/sources/investing/ref-theme-alpha-deep-dive.md` after /enrich placed it.

**Phase D (claim extraction):** ~80 claims across 7 existing entities (NVDA, AMD, MU, AVGO, VRT, AMAT, LRCX). Breakdown by grade: ~45 HIGH (dated quantitative with primary-source citation), ~25 MEDIUM (numerical but undated or secondary-sourced), ~10 LOW (qualitative framing). Section target mapping distributes: ~30 to Financial signals, ~15 to Thesis Fit, ~10 to Risks, ~15 to Catalysts, ~10 to Recent.

**Phase E (dedup + contradiction detection):** dedup skips ~30 claims already in existing entities (matched by marker_signature despite text variance from prior sources). 2 Tier-1 auto-resolutions: NVDA Q3 2024 backlog $480B superseded by Q4 2024 $500B (newer date, higher authority primary source); AMD MI300 revenue Q2-2024 superseded by Q3-2024 figure. No Tier-2 or Tier-3 contradictions. ~50 net-new claims remain for Phase F.

**Phase F (atomic apply):** 7 entity Edits (each entity's body gets new claims appended under section_target headers per claim-to-section mapping); each entity's `updated:` bumped; each entity's `related:` extends with ref-theme-alpha-deep-dive if absent. Source `related:` extends with ingest-report wikilink (audit chain closure). Ingest report written to wiki/research/ref-theme-alpha-deep-dive-ingest-2026-04-22.md. No MOC back-links fire (all 7 entities already exist in investing-moc.md from prior work).

**Phase G (commit):** atomic commit, 9 paths staged (ingest report + 7 entity updates + source). Commit title: `vault(ingest): ref-theme-alpha-deep-dive -- 50 claims distributed across 7 entities + 2 Tier-1 supersedes`.

### Example 2: Concept playbook creating new entities (geo case)

`/ingest Atlas/concepts/investing/geopolitics-playbook.md` (as v1 ran at commit b1583ef, now v2 codified).

**Phase D:** 41 claims across 7 thematic clusters (oil / gold / defense / chokepoints / nuclear / escalation / portfolio rules). 7 substantive entities identified (LMT, RTX, XAR, ITA, PPA, VDE, IAU), each with >=2 mentions + dedicated section coverage. Tier 1 analytical synthesis source quality.

**Phase E:** 7 new entities created (all substantive-threshold met); no existing entity updates (zero overlap with pre-existing vault tickers since defense/energy/precious-metals entities did not exist pre-ingest); zero contradictions (playbook covers territory complementary to ref-geopolitical-framework's US-China+crypto scope).

**Phase F:** 7 new entity notes created at `wiki/entities/tickers/{LMT,RTX,XAR,ITA,PPA,VDE,IAU}.md`, each grounded in `_templates/entity.md` with canonical frontmatter (categories: [entity], type: ticker, sector derived from claim context, topic tags only per vocabulary guardrail) + section placeholders populated with initial claims per claim-to-section mapping. `Atlas/_MOCs/investing-moc.md` `related:` extended with 7 new entity stems (v2 F.3 MOC back-linking rule). Source `related:` extended with 7 entity stems (symmetric) + ingest-report stem (v2 audit chain closure). Ingest report written to `wiki/research/geopolitics-playbook-ingest-2026-04-21.md`.

**Phase G:** atomic commit; 10 paths (7 new entities + 1 ingest report + 1 modified MOC + 1 modified source). Commit title: `vault(ingest): geopolitics-playbook -- 7 entity stubs + ingest report`.

### Example 3: Idempotent re-run

Re-running same /ingest: Phase D same markers; Phase E all signatures dedup-matched; no Edits; glob matches existing report; no commit. "No changes; /ingest is idempotent."

### Example 4: Mid-batch failure

NVDA Edit old_string match fails (entity body drifted since last check). Phase F.halt: immediate stop; F11 stays on; report which succeeded (6 entity Edits) + which failed (NVDA) + which were not attempted (none, NVDA was mid-batch).

User options: `git checkout -- <paths>` to rollback partial, or fix NVDA issue and re-invoke (idempotent skip-already-applied).

### Example 5: Preview

`/ingest <source> --preview`. Runs A-E, emits plan, halts before Phase F. No writes.

### Example 6: Entity-only targeted re-ingest

`/ingest <source> --entity-only NVDA`. Only NVDA claims evaluated; other entities' claims suppressed. Useful when a prior /ingest skipped NVDA due to a transient failure (e.g., entity body drift detected at F.halt) and user wants to retry just that entity without re-evaluating the full claim set. Phase F staged set narrows to {NVDA.md + source (if audit-chain extension needed) + possibly ingest-report-amendment}.

### Example 7: URL source ingest

`/ingest https://example.com/analyst-note.html`. Phase A: WebFetch primary; on SSL error, `curl -sk <url>` fallback per AGENTS.md. Extracted HTML passes through markdown conversion for claim extraction. Source attribution in ingest report cites URL + fetch timestamp + fetched-content sha256 (since URL content can change post-ingest). Source document not placed in vault (no /enrich run on external URL); ingest report is the sole vault artifact referencing the URL.

### Example 8: Clipboard ingest (pasted text)

`/ingest --from clipboard` reads pasted content. Phase A records content sha256 + word count + timestamp. Source path = "clipboard-`<timestamp>`"; not a vault file, not back-linked. Same Phase B-G flow otherwise. Useful for news snippets, Twitter threads user has judged relevant, or ad-hoc extractions from sources user doesn't want persisted in vault.

### Example 9: Low-quality source skip

`/ingest https://r.reddit.com/r/wallstreetbets/<hash>`. Phase A: WebFetch succeeds; Phase D: 3 numeric claims extracted but source quality flags as sentiment (Tier 6 in 6-tier hierarchy from ref-research-methodology.md). Phase E: all claims grade LOW (sentiment without primary-source anchor). Phase F proceeds but: (a) ingest report prominently flags source quality as Tier 6; (b) existing entity notes NOT updated with LOW claims alone (v2 spec: entity-note updates require at least one MEDIUM or HIGH claim per entity); (c) report written for provenance but entity graph untouched. Commit: just the report. User reviews and decides if any claims warrant manual promotion.

## Failure taxonomy (v2 spec)

Catalog of failure modes the skill must handle cleanly. Each failure mode has a detection rule + expected behavior.

### Phase A failures

- **Source unreadable** (path doesn't exist, URL 404, WebFetch SSL error): halt with diagnostic. Per the AGENTS.md tool-mechanics rule, fall back to `curl -sk <url>` once before halt.
- **Source frontmatter fails ruamel parse**: halt with diagnostic. Do not silently coerce; user must repair source.
- **Vault indexes empty** (Glob returns no results for TICKERS or ALL_BASENAMES): halt; likely working-directory mismatch or corrupted vault state.
- **_templates/entity.md missing**: halt; cannot ground entity creations without the template.

### Phase C failure

- **F11 flag file write blocked** (permission error, path-guard violation): halt before any Edit. The state file is infrastructure, not document routing; path-guard should permit it but if block occurs, halt rather than proceed without suppression (risk of a mid-flow auto-commit).

### Phase D failures

- **Zero claims extracted**: likely indicates source is non-substantive (e.g., a daily note, a template). Emit verdict "/ingest is not productive here; source has no extractable claims." Do not proceed to Phase E. No commit.
- **Ambiguous claim** (multiple valid interpretations): grade as LOW; include both interpretations in ingest report; apply neither as authoritative to entity notes.
- **Compound claim fails decomposition** (one sentence with 3+ independent facts): log as extraction failure; include raw sentence in report under "compound claims requiring manual decomposition".

### Phase E failures

- **Tag vocabulary drift** (entity tag uses `domain/*` or `type/*`): HALT per guardrail. Do not coerce; user reviews proposed frontmatter.
- **Marker signature collision** (two claims same signature, different values, same source): indicates source self-contradiction; flag both in ingest report "Internal contradictions" section; apply neither.
- **Substantive threshold ambiguous** (exactly 2 mentions, no dedicated section): apply conservative NO; skip entity creation; log as sub-threshold.
- **No Agent tool in the harness** (E.0 / F.0): non-dispatching harness. Run the inline evaluation for every entity and the inline `tools/vault-audit.py --json` gate as the NORMAL path; report `mode: inline-no-Agent-tool`; never a DEVIATION.

### Phase F failures (handled by F.halt)

- Edit tool **old_string not found** (entity body drifted since Phase A read): Phase F.halt triggers. User rolls back or re-invokes (idempotent).
- **sha256 mismatch post-edit** (Edit succeeded but body diverged from expected): Phase F.halt. Likely concurrent modification or formatter hook interaction.
- **Path-guard block on entity creation** (e.g., entity name sanitization produces a guarded path): HALT; never silently coerce path.
- **Write tool failure** on new entity (disk full, permission error): Phase F.halt.
- **MOC Edit fails** (MOC body drifted): Phase F.halt; user rolls back per halt protocol.

### Phase G failures

- **Staged set mismatch** (git diff --cached --name-only does not match expected set): HALT before commit. Indicates either a gate bug or concurrent modification introducing unexpected staged files.
- **Commit fails pre-commit hook**: investigate + fix; do NOT bypass with --no-verify.
- **F17 gate detects Co-Authored-By in commit body**: HALT; reset --soft and re-compose commit body without trailer.

### Phase K failure

- **F11 flag unlink fails**: log but do not halt; vault is in committed state. User can manually `rm .claude/state/auto-commit-disabled` later.

## Related skills

- /enrich -- preservational complement; surfaces the /ingest recommendation
- /invest -- fuller per-entity analysis than /ingest produces
- /deep -- source generator chainable to /enrich + /ingest

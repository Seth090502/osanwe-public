---
name: decide
risk: safe
description: "Run the structured decision framework. Use when facing a consequential investment decision, career decision, life decision, or skill-architecture decision that warrants a permanent record + adversarial pre-mortem + reversibility check. Structured decision framework with SOTA atomic multi-file discipline (v2.0; CAT-3 prevention-architecture parity with /retro v2.2). Runs first principles decomposition, options analysis with expected/best/worst cases + opportunity cost, adversarial pre-mortem with 3-5 failure modes (probability + detectability + recoverability + cascade), reversibility assessment with smallest-possible-bet identification, and committed recommendation with calibrated confidence + review trigger + review date. Writes to Calendar/decisions/decision-log.md (append) + Calendar/decisions/decision-<slug>-<date>.md (new detailed record) + today's daily note Decisions section + wiki/hot.md Pending Items as a single atomic commit with body-preservation sha256 invariants (content outside insertion sites byte-exact) + body-scope wikilink validation (extracted decision text mechanically de-linked for unresolved targets per /retro v2.2 Phase D pattern) + Phase J.0 pre-commit /vault audit gate (fail-on-GATE-introduced) + F11 Phase C atomic-commit + F14 narrow-stage + F17 Co-Authored-By verify. Same-day -HHMM collision handling preserves archival rule. Empty-decision safeguard HALT. Tag vocabulary guardrail. ASCII-only new content (Pattern 22). Coordinates with /brief (decision-log read for prior context) + /retro (sessions-log capture of /decide invocations) + /invest (decision-log read for portfolio decisions). Use whenever facing a consequential investment, career, life, or skill-architecture decision that warrants a permanent record + adversarial pre-mortem + commitment device."
arguments: [decision]
argument-hint: "'Should I deploy IRA cash now?', 'Accept offer A vs wait for offer B', 'Add LRCX position', 'Upgrade /retro to v2.2 architecture'"
allowed-tools: [WebSearch, WebFetch, Read, Write, Edit, Bash, Glob, Grep, Agent]
effort: max
user-invocable: true
---

## Execution Rules

- **Subagent dispatch is MANDATORY when specified by phase** (Phase D.0 dispatches `vault-researcher` for prior-decision baseline; Phase E.0 dispatches `decision-critic` for adversarial pre-mortem; Phase E.5 dispatches `thesis-critic` CONDITIONALLY when decision is investment-shaped). Pre-emptive skip based on judgment ("vault context not needed", "I can do my own pre-mortem", "this isn't really investment-shaped") is FORBIDDEN. The subagents decide applicability via their own N/A return contracts. Legitimate fallback fires ONLY on (a) contract violation -- subagent return missing required fields (calibrated %, smallest-possible-bet, reversibility verdict, ITT score for thesis-critic), OR (b) actual dispatch failure -- timeout, rate limit, tool-denial, hard subagent crash. Pre-emptive skip surfaces in Phase P audit as **DEVIATION** (not "fallback"). Quality preserved by additive design: existing inline pre-mortem + reversibility logic at Phase E.3-E.4 remains intact as legitimate-failure fallback.

## Quality Standards

- Take a position. The output is a recommendation, not a menu.
- The pre-mortem is the most valuable section. Make it genuinely adversarial; not polite.
- Dollar amounts from actual data (read `private/holdings-taxable.md` / `private/holdings-ira.md`), never estimated.
- Calibrated confidence: percentages with justification, not HIGH/MEDIUM/LOW alone.
- If information is missing, say what's missing and whether the decision should wait.
- Check decision-log.md for related prior decisions; avoid contradicting yourself without acknowledging the change.
- Always identify the "smallest possible bet" that tests the thesis with minimal risk.
- F11 Phase C discipline mandatory: set `.claude/state/auto-commit-disabled` BEFORE any Write/Edit; clear ONLY after atomic commit succeeds.
- Body-preservation sha256 on every append-mode UPDATE (decision-log, daily, hot.md). Content outside insertion sites byte-exact post-write.
- Pattern 22 ASCII-only on new content (em-dash -> --, smart quotes -> straight, ellipsis -> ...).

## When to use / not

Use: investment / career / life / skill-architecture decisions warranting permanent record + adversarial pre-mortem.

Not for: trivial choices (use prose discussion); thesis stress-tests (use /challenge); routine status-checks (use /brief); session retrospectives (use /retro).

## Process (15 atomic operations)

### Phase 0 -- Vault context retrieval (NEW; Phase 3.6d -- runs BEFORE Phase A; read-only; runs in --preview)

Skill-level semantic retrieval over the local HNSW vault index (covers `wiki/` + `Calendar/` + `private/`; `Atlas/` is NOT indexed, so Phase D's inline domain refs are still read directly -- this block COMPLEMENTS, not replaces). Deeper and path-filtered vs the universal UserPromptSubmit hook. Read-only: a Bash `node` call pair; writes nothing; safe in `--preview`. Complements Phase D.0's `vault-researcher` dispatch (semantic-vector recall vs the subagent's targeted grep). Let `D` = the decision argument.

0.1 -- Build 12 decision-decomposition queries:
`"<D>"`, `"<D> options and alternatives"`, `"<D> risks and failure modes"`, `"<D> similar prior decisions"`, `"<D> reversibility"`, `"<D> opportunity cost"`, `"<D> counter-arguments"`, `"<D> time horizon"`, `"<D> calibration base rates"`, `"<D> invalidation signals"`, `"<D> downstream dependencies"`, `"<D> stakeholder impact"`.

0.2 -- Fire `query-skill.mjs` TWICE via Bash, piping the JSON payload to stdin (heredoc; no temp file). Model loads once per call (~0.3-1.5s):
- BROAD (cross-vault, no filter): stdin `{"queries":[<the 12>],"top_k":100,"threshold":0.60}` to `node ~/.vault-substrate/query-skill.mjs`
- FOCUSED (decision record subtree): stdin `{"queries":[<the 12>],"top_k":25,"threshold":0.60,"filter_path_prefix":"Calendar/decisions/"}` to the same script.

Each returns `[{path,line,score,text}]`; the script always exits 0 (emits `[]` on error) so Phase 0 never crashes the run.

0.3 -- Merge BROAD + FOCUSED; dedup by `path:line` (keep higher score); sort score desc; cap top 100. Store as VAULT_CONTEXT.

0.4 -- EMIT a visible summary (MANDATORY):

    Phase 0 -- retrieved vault context (N hits; M from Calendar/decisions/)
    Top results:
      [score] path:line -- first ~80 chars of text   (up to 15)

If both calls fail or return `[]`: emit `Phase 0 -- no vault context retrieved` and continue. NEVER HALT on Phase 0.

0.5 -- Downstream consumers (phases UNCHANGED; consult VAULT_CONTEXT instead of re-deriving):
- Phase D.0/D.1 (Context loading): seed prior-decision baseline + doctrine refs; `vault-researcher` focuses deltas.
- Phase E.1/E.2 (First principles + Options): surface prior similar decisions + outcomes as base rates.
- Phase E.3 (Pre-Mortem): seed failure-mode precedents from prior decision post-mortems in VAULT_CONTEXT.

Cite any used chunk inline as `(vault: path:line)` -- plain text, NO wikilink syntax (Phase 0 context is raw, not vault-resolved).

### Phase A -- Pre-flight state verification

1. Parse `<decision>` argument.
2. Resolve today's ISO date.
3. Compute slug from decision title (lowercase-kebab, <=40 chars).
4. Resolve OUTPUT_PATH = `Calendar/decisions/decision-<slug>-<date>.md`.
5. Same-day collision check: if exists, default `-HHMM` variant; `--replace` reserved.
6. F11 collision check (`.claude/state/auto-commit-disabled` exists -> HALT with diagnostic).
7. Pre-edit sha256 capture for append-mode files: decision-log.md, today's daily note, wiki/hot.md.

### Phase B -- State-transition print (BEFORE F11)

Emit planned reads + planned writes + collision-handled output paths to stdout. Format:

    /decide -- planned state transition:
      reads: holdings-taxable.md / holdings-ira.md / decision-log.md (prior context); domain-specific
        refs (macro-outlook, watchlist, [[doctrine.template]] for investment; tracker,
        opportunities, profile, resume for career; etc.); hot.md (pending items)
      writes:
        - Calendar/decisions/decision-<slug>-<date>[-HHMM].md (NEW)
        - Calendar/decisions/decision-log.md (append)
        - Calendar/daily/<today>.md (append to ## Decisions section)
        - wiki/hot.md (frontmatter updated; ## Pending Items conditional update)
      F11 set after this print

### Phase C -- F11 flag set (MANDATORY before any Write/Edit)

`touch .claude/state/auto-commit-disabled`. This blocks the PostToolUse auto-commit hook so the 4 file mutations land as a single atomic commit at Phase L.

### Phase D -- Context loading (parallel reads)

#### Phase D.0: DELEGATED dispatch to `vault-researcher` (PREFERRED prior-decision baseline; Phase C wiring 2026-05-02)

**MANDATORY** (per Execution Rules): dispatch first, no pre-emptive skip. The subagent pre-loads prior similar decisions + sessions-log context + relevant doctrine, freeing inline reads to focus on deltas.

Use the Agent tool with subagent_type `vault-researcher`. Pass input: `{query: "<decision-argument-keywords>", scope: "Calendar/decisions/ + Atlas/concepts/ + wiki/hot.md", session_id: "<current-session-id>"}`. Expected return: ranked citation table (file + line + excerpt + relevance HIGH/MED/LOW) + 3-5 sentence synthesis covering prior similar decisions and their outcomes, active context from hot.md, and applicable doctrine references.

Validate return: citation table present + synthesis 3-5 sentences. On contract violation OR dispatch failure: fall through to inline reads below. Surface in Phase P audit.

On dispatch success: use synthesis to inform inline reads (focus on deltas + domain-specific files only).

#### Phase D.1: Inline domain-specific reads (always runs; informed by D.0 synthesis if available)

Domain detection from decision argument. Load relevant files in parallel:
- **Investment decisions:** `private/holdings-taxable.md`, `private/holdings-ira.md`, `Atlas/concepts/investing/macro-outlook.md`, `Atlas/concepts/investing/watchlist.md`, [[doctrine.template]], relevant entity notes from `wiki/entities/tickers/`
- **Career decisions:** `Efforts/career-search/tracker.md`, `Efforts/career-search/opportunities.md`, `private/profile.md`, `private/resume.md`, `Atlas/sources/career/ref-remote-data-careers.md`, `Atlas/concepts/career/contractor-transition-rule.md`
- **Life / health decisions:** `private/health-baseline.md`, `Efforts/health-protocol/current-stack.md`, relevant ref docs
- **Any decision:** `Calendar/decisions/decision-log.md` (last 30 days; check for related prior), `wiki/hot.md` (pending items + active context), `Calendar/decisions/sessions-log.md` (last 7 days; recent ratifications)

### Phase E -- Decision analysis (5-section spine)

#### Phase E.0: DELEGATED dispatch to `decision-critic` (PREFERRED pre-mortem path; Phase C wiring 2026-05-02)

**MANDATORY** (per Execution Rules): dispatch first to populate Phase E.3 Pre-Mortem section, no pre-emptive skip. decision-critic generates 3-5 calibrated failure modes + smallest-possible-bet + reversibility verdict adversarially.

Use the Agent tool with subagent_type `decision-critic`. Pass input: `{decision_argument: "<from arg>", horizon: "<6mo default or per-domain>", reversibility_hint: "<from initial framing>"}`. Expected return: ranked failure modes (calibrated % + detectability + recoverability + cascade) + smallest-possible-bet (cost in $ + days + decision-rule) + reversibility verdict (REVERSIBLE | NEAR-IRREVERSIBLE | ONE-WAY).

Validate return: calibrated % on every failure mode, smallest-bet has explicit decision rule, reversibility uppercase per contract.

On contract violation OR dispatch failure: fall through to inline E.3 Pre-Mortem + E.4 Reversibility composition below.

On dispatch success: use returned failure modes for E.3, smallest-bet integrates into E.4-E.5, reversibility verdict drives Phase J hot.md update.

#### Phase E.5: DELEGATED dispatch to `thesis-critic` (CONDITIONAL; when decision is investment-shaped)

**MANDATORY** when applicable (per Execution Rules): if the decision is investment-shaped (large position add, thesis-driven sell, doctrine-ceiling bet, IRA deployment), dispatch thesis-critic for asset-thesis stress-test. Decision-critic covers the general pre-mortem; thesis-critic adds bear-evidence-first ITT discipline specific to investment theses.

Use the Agent tool with subagent_type `thesis-critic`. Pass input: `{ticker: "<extracted from decision>", primary_thesis: "<thesis-slug>", primary_drivers: [<from decision-argument>], market_regime: "<inferred or from prior briefing>", proposed_rating: "<from decision direction>"}`. Expected return: 3-5 ranked failure modes with ITT self-score >=7/10.

If decision is NOT investment-shaped (career, life, health, vault-architecture): skip this dispatch -- domain-mismatch is documented skip, not deviation.

#### E.1 First Principles Decomposition

- What exactly is being decided? (specific framing, not vague)
- What are the constraints? (money, time, information, reversibility)
- What assumptions are embedded in the framing?
- What would have to be true for each option to be the right choice?

#### E.2 Options Analysis

For each viable option (target 2-4 options, not menu of 10):
- Expected outcome (base case): specific dollar / outcome statement
- Best case scenario + probability (with justification)
- Worst case scenario + probability (with justification)
- Opportunity cost: what you give up by choosing this

#### E.3 Pre-Mortem (CRITICAL section; 3-5 failure modes for leading option)

Frame: "It is 6 months later. This decision was catastrophic -- the worst credible outcome. Write the post-mortem as if explaining to an investor what happened."

For EACH failure mode:
- Probability (X%) with specific reasoning
- Was this detectable beforehand? What signal was ignored or unavailable?
- Recoverable or permanent?
- Dollar/career/life cost (specific numbers from actual portfolio data or salary projections)
- Cascade: what else fails if this fails? (correlated positions, dependent decisions)

#### E.4 Reversibility Assessment

- Reversible? How easily? At what cost?
- Cost of waiting for more information vs acting now?
- "Smallest possible bet" version that tests thesis?

#### E.5 Recommendation

Single clear recommendation with:
- Action (specific, not vague)
- Confidence: X% -- [evidence basis]. Would change to Y% if [condition].
- Single strongest reason to act
- Single strongest reason to wait
- Smallest possible bet
- Review trigger: specific measurable event that would change recommendation
- Review date: YYYY-MM-DD when to revisit regardless

### Phase F -- Body-scope wikilink validation (v2.0; /retro v2.2 parity)

For each section of the composed decision text (E.1 through E.5), scan body for `[[<target>]]` patterns:

- **Vault-resolved (in ALL_BASENAMES):** keep wikilink (legitimate vault reference)
- **MEMORY_PREFIXES match (`memory:`, `feedback_`, `auto_`, `user_`, `project_`, `reference_`, `research_`):** rewrite as `[[memory:<stem>]]` grammar (visually distinct, machine-detectable, exempt from broken-wikilink checks)
- **Placeholder syntax (`<X>`, `...`, bare `X`, etc.):** leave unchanged (vault-audit.py filters)
- **Else:** strip wikilink brackets, leaving plain text reference. Log strip count to per-decision provenance.

After stripping, post-validation invariant: each composed section body must contain ZERO unresolved wikilinks. This prevents the C2-C5 class of regressions (decision-log accumulating broken wikilinks from conversation context).

### Phase G -- Compose decision-log table append

Append a single row to `Calendar/decisions/decision-log.md`:

    | <date> | <domain> | <decision summary> | <rationale 1-sentence> | <status> |

Per-file body-preservation gate: pre-edit sha256(decision-log.md) recorded at Phase A.7. Post-edit sha256(content-before-insertion-window) MUST equal pre-edit sha256 of same window. HALT and rollback if differs.

### Phase H -- Compose decision-<slug>-<date>.md detailed record

Frontmatter:

    ---
    categories: [decisions]
    type: decision
    created: <today>
    updated: <today>
    status: active
    confidence: <0-100>
    tags:
      - topic/<domain>
      - decision/<slug>
    related:
      - "[[decision-log]]"
      - "[[hot]]"
      - "[[<domain>-moc]]"  -- e.g., investing-moc, career-moc
    ---

Body sections: H1 + Decision header (date, domain, conviction) + The Question + Options table + Pre-Mortem + Reversibility + Recommendation + Review Triggers + Related Prior Decisions (wikilinks to past decision-{slug} files where applicable).

### Phase I -- Compose daily note append (## Decisions section)

Append a single row to today's `Calendar/daily/<today>.md` `## Decisions` table:

    | <domain> | <decision summary> | <why> |

Per-file body-preservation gate: same sha256 invariant.

### Phase J -- Compose hot.md update (CONDITIONAL)

If decision affects pending items (creates new pending item, removes existing pending item, changes patient-cash deploy strategy, etc.):
- Update `Pending Items` section additive-only (removal only on explicit `completed: X` markers per /retro convention).
- Update `Active Context` if decision changes session focus.
- Update frontmatter `updated:` field to today.

If decision is purely advisory (no pending-item impact): skip hot.md update entirely.

### Phase J.0 -- Pre-commit /vault audit gate (NEW; v2.0 prevention architecture)

After Phase E-J compose all 4 target file modifications IN MEMORY but BEFORE Phase K atomic write:

1. Write each composed file to a tmp dir (e.g., `wiki/research/test-tmp/.precheck/decide-<slug>/`).
2. Run `python tools/skill-precheck.py <tmp1> <tmp2> <tmp3> <tmp4> --skill /decide`.
3. Parse exit code. If 0: proceed to Phase K. If 2: HALT with diagnostic.
4. Auto-repair pathway: if HALT was due to broken wikilinks, re-run Phase F body-scope validation with stricter mechanical de-link, then re-attempt gate. If second attempt fails, surface diagnostic and halt for user input.
5. Bypass: `CLAUDE_VAULT_BYPASS_VALIDATOR=1` env var (logged to `.claude/state/bypasses-<date>.log`).

This is defense-in-depth on top of PreToolUse pre-write-validator.py + PostToolUse wikilink-check.py / frontmatter-check.py / orphan-check.py. The Phase J.0 gate prevents broken composition from reaching disk in the first place.

### Phase K -- Pre-Output HALT gate (16-item invariant check)

1. F11 set
2. OUTPUT_PATH collision resolved (`-HHMM` if needed)
3. Frontmatter complete and schema-compliant on detail file
4. Decision-log row composed
5. Detail file body composed with all 6 sections (Question / Options / Pre-Mortem / Reversibility / Recommendation / Review Triggers)
6. Pre-mortem has 3-5 failure modes; each with probability + detectability + recoverability + cascade
7. Recommendation has confidence percentage + condition for change + smallest-possible-bet
8. Body-scope wikilink validation passed (Phase F applied; zero unresolved wikilinks)
9. Phase J.0 pre-commit /vault audit gate passed (skill-precheck.py exit 0)
10. Sha256 body-preservation invariant computed for each append-mode file
11. ASCII-only on new content (Pattern 22)
12. `related:` field has 3-5 wikilinks ([[decision-log]], [[hot]], domain MOC, related prior decisions)
13. Tag vocabulary guardrail: tags use `topic/*`, `decision/*`; no forbidden `domain/*` or `type/*` namespaces
14. Path-guard: no Write targets `.raw/`, `private/`, `finance/`, `credentials/`
15. Sessions-log entry composed for /retro pickup (the decision is itself a substantive item)
16. F17 Co-Authored-By absent in planned commit body

### Phase L -- ASCII pre-write scan (Pattern 22)

Byte-scan all NEW content. HALT on byte >127. Replace em-dash (-> --), smart quotes (-> straight), ellipsis (-> ...).

### Phase M -- Atomic write (4 files)

1. Write `Calendar/decisions/decision-<slug>-<date>[-HHMM].md` (NEW detail file)
2. Edit `Calendar/decisions/decision-log.md` (append table row; sha256 verify)
3. Edit `Calendar/daily/<today>.md` (append ## Decisions row; sha256 verify)
4. Edit `wiki/hot.md` (conditional update per Phase J; sha256 verify)

F.halt: if any Edit fails (e.g., old_string anchor changed since Phase A pre-flight), IMMEDIATE HALT, F11 stays on, structured report (succeeded / failed / not-attempted), no partial commit. User can `git checkout -- <orphan>` to rollback or fix root cause and re-invoke.

### Phase N -- Atomic commit (F14 narrow stage + F17 verify)

1. F14 narrow stage: `git add` exactly the 4 touched files (no `git add -A`).
2. Commit with message:

       agent(decide): <slug> -- <domain> -- <conviction>

       <2-3 sentence rationale summary>

       Smallest bet: <description>
       Review trigger: <event>
       Review date: <YYYY-MM-DD>

3. F17 verify: post-commit `git log -1 --format=%B | grep -c Co-Authored-By` MUST be 0.

### Phase O -- F11 clear

`rm .claude/state/auto-commit-disabled`. PostToolUse auto-commit hook re-enabled for subsequent skills.

## Modes

- `--preview`: dry-run; render decision text + planned writes to stdout; SKIP all writes; F11 never set
- `--confirm`: pause before each Write for user confirmation
- `--no-decision-log`: skip decision-log table append (e.g., for purely-exploratory pre-mortems)

## Idempotency (v2 spec requirement)

- Decision marker signature: `<slug>-<date>` -- same slug + date = idempotent re-run
- Pre-persist check Phase G: if proposed decision-log row's signature already present, SKIP (log "already captured")
- Detail file: same-day collision -> `-HHMM` variant per Phase A.5
- Idempotent re-run produces zero diff

## Path-guards (mechanical)

NEVER write to: `.raw/`, `private/`, `finance/`, `credentials/`. Never delete (move-to-archive only). All writes route through `Calendar/decisions/`, `Calendar/daily/<today>.md` (append-only), `wiki/hot.md` (frontmatter + Pending Items conditional update).

## Tag vocabulary guardrail

Decision file tags: `topic/<domain>` (e.g., `topic/investing`, `topic/career`), `decision/<slug>`. Forbidden: `domain/*`, `type/*`. Frontmatter MUST have `categories: [decisions]` and `type: decision`.

## Coordination with other skills

- **/brief**: reads decision-log.md last 30 days for "Today's Focus" priors. /decide outputs feed /brief next-morning context.
- **/retro**: sessions-log entry composed at Phase K item 15 surfaces /decide invocations as substantive ratifications. /retro extracts and persists.
- **/invest**: portfolio-related /decide invocations should reference /invest entity notes in `related:`. /invest may itself trigger /decide for "should I add this position" questions.
- **/challenge**: /decide produces a recommendation; /challenge stress-tests it. The pair: /challenge surfaces invalidations -> /decide ratifies the response.

## Failure taxonomy

| Failure | Phase | Symptom | Recovery |
|---|---|---|---|
| F11 collision | A | another skill in-flight | Wait OR `rm .claude/state/auto-commit-disabled` if confirmed orphan |
| Same-day collision | A | OUTPUT_PATH exists | Default `-HHMM`; user can `--replace` |
| Phase F unresolved wikilink | F | broken wikilink in composed text after de-link | HALT; report target + line; user fix or auto-strip |
| Phase J.0 GATE finding | J.0 | skill-precheck.py exit 2 | HALT; report findings; auto-repair retry; user input on second fail |
| sha256 body-preservation violation | M | content outside insertion window changed | F.halt; back out the Edit; sha256-preserving retry |
| Mid-batch Write failure | M | first Write succeeded, second failed | F.halt; F11 stays on; structured report; user `git checkout --` orphan |
| ASCII byte >127 | L | non-ASCII in NEW content | Replace and retry; do NOT proceed |
| F17 verify fail | N | Co-Authored-By in commit body | `git commit --amend` to remove |

## Examples

### Example 1: Investment decision (IRA cash deploy)

`/decide Should I deploy IRA $[PORTFOLIO_VALUE] cash now?` ->
- Phase D loads `private/holdings-taxable.md`, `private/holdings-ira.md`, macro-outlook.md, watchlist.md, [[doctrine.template]]
- Phase E.3 pre-mortem 5 failure modes (kinetic-delay macro shock, <thesis-slug> concentration drift, cap-rate compression, etc.) with %, detectability, cascade
- Phase E.5 recommendation: HOLD $[PORTFOLIO_VALUE] patient-cash; deploy via GTC limits at thesis-calibrated entry prices on shock scenarios
- Phases G-J atomic 4-file write
- Sessions-log entry composed for /retro

### Example 2: Career decision (offer comparison)

`/decide Accept offer A at $X vs wait for offer B interview?` ->
- Phase D loads tracker.md, opportunities.md, profile.md, resume.md, contractor-transition-rule.md
- Phase E.4 reversibility: offer A accept locks employment; offer B rejection means lost weeks; calibrate value of waiting vs. value of certainty
- Phase E.5 smallest bet: ask offer A for 1-week response window, use to interview at offer B

### Example 3: --preview mode

`/decide Add LRCX position --preview` -> renders full analysis to stdout; no Write; no commit; user reviews and either invokes without --preview to commit or iterates.

### Example 4: Empty-decision safeguard

`/decide` with no argument -> HALT with diagnostic "decision argument required; usage: /decide '<question>'".

### Example 5: Idempotent re-run

`/decide Should I deploy IRA cash now?` invoked twice in same session ->
- Second run Phase G dedup via marker signature `should-deploy-ira-cash-now-<date>` matches existing row -> SKIP decision-log append
- Detail file collision -> `-HHMM` variant (or `--replace` if user explicitly wants to overwrite)

## Related skills

- `/retro` -- session-end retrospective; consumes /decide ratifications
- `/brief` -- reads decision-log.md priors; /decide outputs feed next briefing
- `/invest` -- portfolio-decision pair; /invest analysis -> /decide ratification
- `/challenge` -- thesis stress-test; /challenge surfaces invalidations -> /decide ratifies response
- `/vault` -- audit consumer; /decide outputs validated against GATE classifiers

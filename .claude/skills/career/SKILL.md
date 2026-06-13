---
name: career
risk: safe
description: Run the institutional-grade job-search pipeline. Use when scanning new opportunities, evaluating role-fit + contractor-transition-rule compliance, composing 7-file application packets, refreshing tracker pipeline state, or post-application retrospective. v2.2 SOTA refresh 2026-04-29 -- adds 7th archetype CLAUDE_SDK_CONTRACTOR (Anthropic SDK / MCP / /skills authoring / agent build-out / Claude consulting lanes); refreshes archetype proof-points to resume v3 baseline (17 skills / 10 SOTA-final / 379-file vault / 1,054 LOC Python tooling / 22-25 SOTA patterns / 23 ref docs / 95K words / 5,435-word whitepaper / cc-coach v1.1 / Plan-agent autonomous execution / multi-tool runtime portability); adds READY_TO_SUBMIT_BLOCKED state with daily-recall mechanism (3d/7d/14d) for blocker-stuck packets; integrates Mercor (Tier-1 expert-tier hiring platform, $10-150/hr range); ref-scoring-model v2.2 redistributes compensation_upside to differentiate Mercor expert tier ($100+/hr) from AI-trainer baseline; codifies Assessment-Gate vs Hard-Filter Dual Model (assessment-based platforms skip 7-file packet; hard-filter experience requirements get 5-10pt penalty until empirically tested); adds RTO-mandate red flag + remote-first green flag detection; adds speed-to-engagement outcome metric to packet-meta.json; Claude-keyword 2.0x weighting in archetype detection promotes PROMPT_ENGINEER hits with Claude/Anthropic/MCP signals to CLAUDE_SDK_CONTRACTOR pool. Institutional-grade job-search pipeline with atomic 7-file packet discipline, deterministic mode routing (Pattern 6), contractor-transition-rule compliance gating on every apply action, scoring-model calibration feedback loop (rolling 30-day ADVANCE-to-interview conversion per archetype), symmetric back-linking to wiki/entities/companies/, FOLLOWUPS:skills coordination block feeding /brief + /retro, meta.json sidecar per packet for audit + retrospective scoring calibration, same-day -HHMM collision handling preserving archival rule, and 16-phase A-P arc matching /invest + /brief. 7 modes consolidated from v1's 14+: scan / evaluate / pipeline / apply / tracker / retro / compare. Reads private/profile.md + private/resume.md (path-guard-compliant READ only), Atlas/concepts/career/{goals,skills-inventory,contractor-transition-rule}.md, Atlas/sources/career/ref-{remote-data-careers,skills-translation,target-markets,company-health}.md, Efforts/career-search/{tracker,opportunities}.md, wiki/entities/companies/*.md. Writes to Efforts/career-search/applications/<company>-<date>[-HHMM]/ (7-file packets), Efforts/career-search/{scans,retros}/, wiki/entities/companies/ (CREATE-or-UPDATE with claim-to-section mapping per /invest precedent), with body-preservation sha256 invariants + per-fact provenance + marker-signature dedup. Coordinates with /brief (Career Pipeline section consumes tracker state) + /retro (FOLLOWUPS:skills block parsed at session end) + /invest (entity-note pattern inheritance) + /ingest (company claim distribution). F11 Phase C + F14 narrow stage + F17 Co-Authored-By verify + ASCII-only discipline + Phase O.0 pre-commit /vault audit gate (CAT-3 prevention-architecture parity).
arguments: [mode, target]
argument-hint: "[scan|evaluate <url-or-jd>|pipeline|apply <company-slug>|tracker|retro|compare <pkt1> <pkt2>] [--preview|--confirm|--replace|--refresh|--no-peripheral|--override-rule]"
allowed-tools: [WebSearch, WebFetch, Read, Write, Edit, Bash, Glob, Grep, Agent]
effort: max
user-invocable: true
---

## When to use

- Morning scan for new remote roles matching target archetypes (`scan`)
- Single URL or JD text to score and decide ADVANCE / HOLD / SKIP (`evaluate`)
- End-to-end scan -> score -> 7-file packet generation for top scorers (`pipeline`)
- Generate field-by-field submission notes for a scored ADVANCE role (`apply`)
- Surface current pipeline status, follow-ups due today, aged-out rows (`tracker`)
- Monthly retrospective with scoring calibration + archetype conversion rates (`retro`)
- Side-by-side decision matrix between 2+ roles (`compare`)

## Not for

- Portfolio investment analysis -> `/invest`
- Daily market briefing -> `/brief`
- Session-end decision capture -> `/retro`
- Business-idea evaluation (peptide/supplement info-products, consulting offers) -> future `/business` skill; not in career scope
- Resume PDF generation -> external pandoc/typst; `/career` emits ATS-optimized Markdown only
- Auto-submission of applications -> NEVER. Skill generates packets; the user submits manually.

## Execution Rules

- **Subagent dispatch is MANDATORY when specified by phase** (Phase C.5 dispatches `vault-researcher` for prior-scan baseline; Phase E dispatches `portal-scanner` per portal in scan mode -- N parallel for N-portal config). Pre-emptive skip based on judgment ("I can search inline", "vault search not needed for this scan") is FORBIDDEN. The subagent decides applicability via its own N/A return contract. Legitimate fallback fires ONLY on (a) contract violation -- subagent return missing required fields (8-dim score, archetype tag, red flags, citation table for vault-researcher), OR (b) actual dispatch failure -- timeout, rate limit, tool-denial, hard subagent crash. Pre-emptive skip surfaces in Phase O commit report as **DEVIATION** (not "fallback"). Quality preserved by additive design: existing inline portal scan logic + Glob/Grep vault search remain intact as legitimate-failure fallback.

## Quality Standards

These rules govern every output. Violations are defects.

- NEVER fabricate experience, metrics, or credentials. Only use what exists in `private/resume.md` and `Atlas/concepts/career/skills-inventory.md`.
- NEVER submit applications. Skill generates packets; the user submits manually.
- Every evaluation includes a "Why You're Qualified" section with specific evidence from vault.
- Every `submission-notes.md` includes exact URL, field-by-field instructions, time estimate, and Contractor Rule Reality Check.
- Calibrated percentage confidence on forward-looking claims. No HIGH / MEDIUM / LOW.
- Dollar amounts from disclosed compensation data. If pay is undisclosed, state "pay undisclosed" -- never estimate.
- Quality over quantity: 5 targeted applications > 50 generic.
- Discourage low-fit applications. If nothing clears ADVANCE (>=70), say so directly. Do NOT force packets to fill a quota.
- All output in English.
- All emitted files include canonical YAML frontmatter (see Canonical Frontmatter section below).
- All new content ASCII-only: no em-dashes (use `--`), no curly quotes (use `"` / `'`), no arrows (use `->` / `<-`), no ellipsis character (use `...`), no NBSP, no middle-dot, no euro sign.
- Body-preservation sha256 invariant on all UPDATES to existing files (tracker, opportunities, goals, entity notes, daily note).
- Tag guardrail: emit only `topic/*`, `company/*`, `thesis/*` namespaces on frontmatter tags. No `type/*` or `domain/*` (those were stripped in Group 26 canonicalization).

## Canonical State Vocabulary

All tracking files use EXACTLY these states. No synonyms, no alternatives.

**Lifecycle states:**
```
SCOUTED -> EVALUATED -> ADVANCE -> READY_TO_SUBMIT [-> READY_TO_SUBMIT_BLOCKED]
  -> SUBMIT_NOW -> SUBMITTED -> FOLLOW_UP_1 -> FOLLOW_UP_2 ->
  RESPONDED -> INTERVIEW -> OFFER -> ACCEPTED | REJECTED | WITHDRAWN | CLOSED
```

**READY_TO_SUBMIT_BLOCKED** (NEW v2.2): packet exists; tracker carries `blockers: [<list>]` array with pre-submission dependencies (writing-sample / github-repo / linkedin-profile / form-answers / banned-string-grep / etc.). Phase I tracker mode emits DAILY_RECALL when `age_in_state >= 3 days`; WARN at >= 7 days; proposes ABANDONED transition at >= 14 days. Per ref-scoring-model.md v2.2 "Blocker-Aware READY_TO_SUBMIT State" section.

**Decision states (evaluation output):**
```
ADVANCE (70+) | HOLD (60-69) | SKIP (<60)
```

State-transition rules enforced by `tracker` mode:
- `SUBMITTED` bumps `date_submitted` to today and schedules `FOLLOW_UP_1` at +6 days
- `FOLLOW_UP_1` / `FOLLOW_UP_2` auto-fire based on age_days computed at every tracker read
- `age_days >= 21` without RESPONDED -> auto-transition to WITHDRAWN (no response baseline)
- `CLOSED` is manual-only (the user pivoted away; role withdrawn by company; outside rule)

## Archetype Detection

Every evaluated role is classified into ONE archetype. Archetype drives resume tailoring, cover-letter tone, and Project Osanwe proof-point selection. Refreshed 2026-04-29 v2.2 with new resume baseline (17 skills / 10 SOTA-final / 379-file vault / 1,054 LOC Python / 22-25 SOTA patterns) + new CLAUDE_SDK_CONTRACTOR archetype.

| Archetype | Keywords in JD | Project Osanwe proof points | Resume emphasis |
|-----------|----------------|------------------------------|------------------|
| CLAUDE_SDK_CONTRACTOR | Claude API, Anthropic SDK, Agent SDK, MCP, Model Context Protocol, Claude Code, /skills authoring, agent build-out, prompt orchestration, prompt caching, tool calling, Claude consulting | 17 skills built on Claude Code SDK (10 at SOTA-final), MCP integration, Codex CLI dual-tool migration validated via Plan-agent autonomous execution, 10 session-orchestration hooks, cc-coach v1.1 13-pattern advisory infra, 7,852-word Claude Code mastery reference, 5,435-word PROJECT-OSANWE-PACKET whitepaper | Claude SDK depth, Anthropic-native agent architecture, /skills authoring portfolio, technical writing |
| AI_TRAINER | annotation, RLHF, data labeling, AI training, model evaluation, prompt quality, rubric, RLAIF, DPO, preference data, micro-task evaluation | Prompt engineering depth (17 skills, 10 SOTA-final), multi-model evaluation (Qwen3.5 27B vs Claude vs Gemini), quality-graded knowledge base (95K words / 23 ref docs / 5,435-word whitepaper), rubric-based evaluation discipline, RLHF awareness, 22-item Pre-Output gate per skill | Prompt engineering, quality judgment, structured evaluation under sustained workflow pressure |
| PROMPT_ENGINEER | prompt engineering, LLM, AI ops, infrastructure, tool calling, agent orchestration, fine-tuning | Full LLM infrastructure stack (Ollama + GGUF Q6_K + SearXNG Docker + Plan-agent autonomous execution + dual-tool runtime portability), 10 session-orchestration hooks, 22-25 SOTA patterns + 18 standing rules, 1,054 LOC production Python tooling. **2.0x Claude-keyword weighting:** if JD names Claude/Anthropic/MCP/Agent SDK, route to CLAUDE_SDK_CONTRACTOR | LLM infrastructure, multi-model stack, system architecture |
| DATA_ANALYST | data quality, reporting, QA, ETL, analytics, data processing, BI, dashboard, SQL | Knowledge base architecture (379-file vault, 23 ref docs / 95K words), 1,054 LOC Python tooling (vault-audit.py 9 classifiers across 379 files; fetch-prices.py yfinance + technical indicators), analytical frameworks (8-dim scoring, evidence A-F grading, 18-item Pre-Output gates, body-preservation sha256 invariants) | Data pipeline, quality systems, analytical depth |
| TECH_SUPPORT | help desk, sysadmin, documentation, DevOps, IT support, customer technical, troubleshooting | Local service deployment (Docker, SearXNG self-hosted with 8+ providers, Ollama local LLM), 10 session-orchestration hooks, F11 atomic-commit discipline, debugging (30 patches across 1,404 TS files), VAULT-HANDOFF-V16+ ~110KB documentation | Infrastructure, debugging, self-hosting, documentation |
| INSURANCE_OPS | underwriting, claims, carrier, insurance, verification, policy | [N] years verification/operations work at [EMPLOYER] ([ACCURACY]% accuracy at scale, zero documented errors), structured repro-step documentation, multi-platform SaaS workflow ([CARRIER_PLATFORMS]) | Direct industry experience, process accuracy, compliance |
| OPERATIONS | customer support, operations, remote ops, administrative, coordinator | Remote operations since [START_DATE], 16-phase A-P process design for skill workflows, 22-item Pre-Output HALT gate, accuracy-record at scale ([ACCURACY]% verification), atomic multi-file commit discipline | Remote work capability, process optimization, attention to detail |

**Deterministic archetype detection** (Pattern 6 first-match-wins):

1. Count keyword matches per archetype in JD text (case-insensitive; whole-word match)
2. **Claude-keyword promotion (NEW v2.2):** if any of {Claude, Anthropic, MCP, Agent SDK, Claude Code} keywords match >=1, lift PROMPT_ENGINEER hits into CLAUDE_SDK_CONTRACTOR pool with 2.0x weighting (per ref-resume-tailoring.md v2.1 tiebreaker rule)
3. Rank archetypes by adjusted match count (descending)
4. If top archetype match count >= 2x second archetype -> assign top
5. If top archetype match count = second archetype match count (tie) -> preference order: **CLAUDE_SDK_CONTRACTOR > AI_TRAINER > PROMPT_ENGINEER > DATA_ANALYST > OPERATIONS > TECH_SUPPORT > INSURANCE_OPS** (matches the user's resume v3 2026-04-29 strength profile, AI-systems-builder primary)
6. If no archetype matches >= 2 keywords -> assign OPERATIONS (default) AND flag `archetype_uncertain: true` in evaluation.md frontmatter

Report in evaluation.md: `Archetype: <X> (keyword hits: claude_sdk_contractor=5, ai_trainer=2, ...)`. Pattern 11 auditable.

## Mode Routing

**Deterministic first-match-wins rule list (Pattern 6):**

| Rule | Condition | Mode |
|------|-----------|------|
| 1 | arg starts with URL matching job-board pattern (`ashbyhq.com`, `greenhouse.io`, `lever.co`, `workday.com`, `smartrecruiters.com`, `linkedin.com/jobs`, `indeed.com`, company career pages) | `evaluate` |
| 2 | arg is text >= 200 words containing any of: "responsibilities", "requirements", "qualifications", "about the role", "what you'll do" | `evaluate` |
| 3 | arg is `scan` | `scan` |
| 4 | arg is `pipeline` | `pipeline` |
| 5 | arg is `apply` followed by company-slug matching existing packet folder | `apply` |
| 6 | arg is `tracker` | `tracker` |
| 7 | arg is `retro` | `retro` |
| 8 | arg is `compare` followed by 2+ packet slugs | `compare` |
| 9 | arg is empty | `discovery` (print command menu) |
| 10 | arg matches none of above | HALT with routing error + suggested modes |

Mode routing reports (Pattern 11 auditable): "Mode: evaluate (rule 1 matched: URL=https://jobs.ashbyhq.com/...)"

## Phase structure (A-P, 16 phases)

Every mode flows through phases A-D uniformly, then branches into mode-specific phases E-K, then converges on L-P.

### Phase A: Pre-flight

- Parse args + flags (`--preview`, `--confirm`, `--replace`, `--refresh <path>`, `--no-peripheral`, `--override-rule`)
- Resolve today's ISO date
- F11-state check: if `.claude/state/auto-commit-disabled` exists, HALT (concurrent session or uncleared flag)
- Resume freshness check: `private/resume.md` `updated:` frontmatter age; if >90 days, emit WARN header
- Same-day collision detection: if `Efforts/career-search/applications/<slug>-<today>/` exists AND not `--replace` AND mode is `pipeline` or `apply`, default output to `applications/<slug>-<today>-<HHMM>/` variant (archival rule preserved per /invest precedent). If same-HHMM also exists, HALT ambiguous intent.
- Validate required infrastructure: Efforts/career-search/ tree exists; Atlas/sources/career/ref-*.md readable; private/ readable

### Phase B: State-transition print BEFORE F11 (abort-checkpoint)

Emit to stdout:

```
## /career v2 -- planned state transition

MODE: <mode> [flags]
DATE: YYYY-MM-DD
TARGET: <url or jd snippet or company-slug>

READS:
  - private/profile.md, private/resume.md
  - Atlas/concepts/career/goals.md, skills-inventory.md, contractor-transition-rule.md
  - Atlas/sources/career/ref-{remote-data-careers, skills-translation, target-markets, company-health}.md
  - Efforts/career-search/{tracker.md, opportunities.md}
  - wiki/entities/companies/<Company>.md  (if exists; will CREATE if not on pipeline/apply)
  - last /brief briefing if pipeline-mode (for macro context)

WRITES (mode-dependent):
  [pipeline/apply] Efforts/career-search/applications/<slug>-<date>[-HHMM]/  (7 files + meta.json)
  [pipeline/apply] wiki/entities/companies/<Company>.md  (CREATE-or-UPDATE; sha256-gated)
  [all modes] Efforts/career-search/tracker.md  (additive row OR status update)
  [scan] Efforts/career-search/scans/scan-YYYY-MM-DD.md
  [retro] Efforts/career-search/retros/career-retro-YYYY-MM-DD.md
  [all modes] Calendar/decisions/sessions-log.md  (append structured entry)
  [all modes] Calendar/daily/<today>.md  (Sessions Run section; sha256-gated)

CONTRACTOR RULE STATE:
  Current contractor income toward $[CONTRACTOR_MONTHLY_FLOOR]/mo x 2 threshold: <computed from tracker>
  W2 offer threshold ($[W2_THRESHOLD]/yr): <any ACTIVE offer meeting?>
  Rule status: ACTIVE | CONDITION_A_MET | CONDITION_B_MET | FORCE_QUIT

PROCEED?  Abort now = pre-F11, zero writes.
```

If `--preview`: complete Phases C-M in memory, render output to stdout, skip Phases N-P.
If `--confirm`: block for user `yes` before Phase C; block before each write in Phase N.
Else continue.

### Phase C.5: DELEGATED dispatch to `vault-researcher` (PREFERRED prior-scan baseline; Phase C wiring 2026-05-02)

**MANDATORY** (per Execution Rules): dispatch first before Phase C inline context load to pre-populate prior-scan + skills-inventory + opportunities baseline. No pre-emptive skip.

Use the Agent tool with subagent_type `vault-researcher`. Pass input: `{query: "career skills-inventory + active opportunities + prior scan results", scope: "Atlas/concepts/career/ + Efforts/career-search/", session_id: "<current-session-id>"}`. Expected return: ranked citation table (file + line + excerpt + relevance HIGH/MED/LOW) + 3-5 sentence synthesis covering current archetype state + in-flight ADVANCE packets + last-scan delta opportunities.

Validate return: citation table present + synthesis 3-5 sentences. On contract violation OR dispatch failure: fall through to Phase C inline reads. Surface in Phase O commit report.

On dispatch success: use synthesis as Phase C context baseline; inline reads in Phase C focus on deltas only (faster + less context burn).

### Phase C: F11 set + Context Load

1. `mkdir -p .claude/state && touch .claude/state/auto-commit-disabled`
2. Parallel load:
   - `private/profile.md` + `private/resume.md` (path-guard-compliant READ; never write)
   - `Atlas/concepts/career/goals.md` + `skills-inventory.md` + `contractor-transition-rule.md`
   - `Atlas/sources/career/ref-remote-data-careers.md` + `ref-skills-translation.md` + `ref-target-markets.md` + `ref-company-health.md`
   - `Efforts/career-search/tracker.md` + `opportunities.md` + `_index.md`
   - Mode-specific:
     - scan: recent `scans/scan-*.md` (last 2) for dedup baseline
     - evaluate/pipeline/apply: `wiki/entities/companies/<Company>.md` if exists
     - retro: all `retros/career-retro-*.md` (last 3) + all `applications/*/evaluation.md` for calibration corpus
     - compare: both specified packet folders' `evaluation.md`
   - Most recent `Calendar/decisions/briefings/briefing-*.md` (if within 24h; for macro context on scan/pipeline)
3. Build checklist:
   - Holdings: skills-inventory keyword set
   - Tracker state: submitted count, follow-ups due today, aged-out (>21d) rows awaiting WITHDRAWN transition
   - Contractor rule proximity: current contractor MTD income (from tracker if SUBMITTED to 1099 platforms AND has 1099-payment data) vs the $[CONTRACTOR_MONTHLY_FLOOR] threshold; any ACTIVE W2 offer vs $[W2_THRESHOLD] threshold
   - Dedup set: all company+role combinations from tracker for scan-dedup

### Phase D: Mode routing

Apply the deterministic rule list (see Mode Routing section). Report which rule fired and which markers matched.

### Phase E: Scan mode (if scan)

#### Phase E.0: DELEGATED parallel dispatch to `portal-scanner` per portal (PREFERRED path; Phase C wiring 2026-05-02)

**MANDATORY** (per Execution Rules): dispatch first per portal in active scan config, no pre-emptive skip. The model dispatches N portal-scanner subagents in parallel (one per portal in active scan-config: wellfound, mercor, yc, otta, levels-fyi, etc.) within a single assistant turn for true parallelism (5-portal sequential = 5x slower).

Per dispatch, use the Agent tool with subagent_type `portal-scanner`. Pass input: `{portal: "<portal-name>", archetypes: [<active archetype list from skills-inventory>]}`. Expected return: ranked candidate table with [Role | Company | Comp | Archetype | Score 0-100 | Filter type | Red flags | Conf] + filtered-out section + archetype distribution + delta-vs-last-scan + scan confidence + recommended next actions priority-ordered.

Validate per-portal return: 8-dim score normalized 0-100, archetype tag from canonical taxonomy, filter type explicit, red flags individually listed.

On contract violation OR dispatch failure for any portal: fall through to inline WebSearch portal scan for that portal only. Other portals' subagent returns still consumed.

On dispatch success: merge N portal results into single composite scan-of-scans table for Phase F evaluate or Phase M output.

#### Phase E.1: Inline scan logic (FALLBACK; per-portal, runs ONLY if Phase E.0 dispatch failed for that portal)

Phase E fires only on scan / pipeline modes.

**Freshness + dedup protocol:**
- WebSearch queries targeted per archetype + portal (rotate through 5 portals per run to avoid stale-list fatigue)
- Archetype queries (ROTATE across scans; 2 archetypes per scan):
  - AI_TRAINER: `site:ashbyhq.com ("AI trainer" OR "prompt quality") remote posted:7d`
  - PROMPT_ENGINEER: `site:greenhouse.io "prompt engineer" remote posted:7d`
  - DATA_ANALYST: `site:linkedin.com/jobs "data analyst" remote "no degree" posted:7d`
  - TECH_SUPPORT: `site:lever.co "technical support" remote posted:7d`
  - OPERATIONS: `site:workday.com "remote operations" posted:7d`
  - INSURANCE_OPS: large-carrier-site queries (State Farm, Progressive, Allstate, USAA, Liberty Mutual careers pages)
- Dedup: any role whose normalized company+role tuple matches an existing tracker row -> SKIP from scan output (do NOT surface redundantly)
- Freshness filter: posted date <= 7 days OR "posted" field absent with fresh-looking page elements
- Output: ranked shortlist (raw score without company-health multiplier for speed) + top 3 auto-advance to Phase F evaluate

**Scan output file:** `Efforts/career-search/scans/scan-YYYY-MM-DD.md` (same-day collision -> `-HHMM` variant)

**Market context adjustment** (from last /brief if within 24h):
- Tech layoffs spiking (>50K in 30 days): speed-to-apply -2, fit-to-background +2
- AI hiring accelerating: AI_TRAINER + PROMPT_ENGINEER archetype scores +3
- Recession signals: INSURANCE_OPS + OPERATIONS archetype scores +3
- Normal market: no adjustment
Document adjustment in scan.md header.

### Phase F: Evaluate mode (if evaluate or pipeline)

Before scoring: **Read `.claude/skills/career/ref-scoring-model.md`** for the full 8-dimension rubric, company-health multiplier, decision thresholds, and red/green flag detection. Do NOT emit any score until this ref is loaded.

Compute:
- Archetype (per Archetype Detection section above)
- Raw score (8 dimensions x max points per ref-scoring-model)
- Company health multiplier (1 WebSearch for health signals: recent news, Glassdoor trend, funding events)
- Red/Green flags (non-scored; surfaced in output)
- Decision: ADVANCE (70+) / HOLD (60-69) / SKIP (<60)
- Contractor-rule proximity: for ADVANCE roles, compute whether this role would advance Condition A (contractor income) or Condition B (W2 threshold); emit in evaluation header

**Evaluation output file:**
- Standalone evaluate mode: `Efforts/career-search/evaluations/<slug>-<date>.md` (single file)
- Pipeline/apply mode: embedded as `evaluation.md` in packet folder

### Phase G: Pipeline mode (if pipeline)

Chains Phases E (scan) -> F (evaluate per role) -> packet generation for each ADVANCE.

Deterministic validation before emit:
- Only ADVANCE roles get packet folders
- Each packet folder gets exactly 7 files (or 6 if score 70-79; skip `form-answers.md` below 80 score)
- Tracker updated with all scored roles (ADVANCE, HOLD, SKIP)
- No empty / partial folders for non-ADVANCE roles (Pattern 13 F.halt if write fails mid-batch)

### Phase H: Apply mode (if apply)

Apply mode fires on an already-scored ADVANCE role to generate submission-ready field answers and transition tracker to SUBMIT_NOW.

Before Phase H emit, **contractor-rule compliance gate:**
- Read `Atlas/concepts/career/contractor-transition-rule.md`
- Check: does this role advance Condition A (contractor >= $[CONTRACTOR_MONTHLY_FLOOR]/mo x 2 achievable) or Condition B (W2 >= $[W2_THRESHOLD])?
- If NO AND not `--override-rule` flag: emit WARN in submission-notes.md Contractor Rule Reality Check section; do NOT halt (the user retains override)
- If `--override-rule`: explicitly document override rationale in submission-notes.md

Output (augments existing packet):
- Expand `submission-notes.md` with pre-drafted form answers for common portal questions (Ashby, Greenhouse, Lever, Workday standard fields)
- Add `Submission Reality Check` + `Contractor Rule Reality Check` sections
- Transition tracker row: EVALUATED -> SUBMIT_NOW (the user manually sets SUBMITTED after submitting to portal)

### Phase I: Tracker mode (if tracker)

Read + display pipeline state with auto-computed fields:
- `age_days` = today - date_submitted per SUBMITTED row
- Follow-ups due today (FOLLOW_UP_1 at age 5-7; FOLLOW_UP_2 at age 12-14)
- Aged-out rows (age >= 21, no RESPONDED) -> propose WITHDRAWN transition (the user confirms)
- Summary counts per status
- Contractor rule proximity banner

Optional `tracker <company-slug> <new-state>` subcommand: transition row state deterministically (enforces valid state transitions per Canonical State Vocabulary).

### Phase J: Retro mode (if retro)

Calibration loop. Reads all `applications/*/evaluation.md` + all past retros. Computes:
- Per-archetype: ADVANCE count, SUBMITTED count, RESPONDED count, INTERVIEW count, OFFER count
- Rolling 30-day conversion rates: ADVANCE->SUBMITTED, SUBMITTED->RESPONDED, RESPONDED->INTERVIEW, INTERVIEW->OFFER
- Archetype accuracy: did high-score roles convert at higher rates than low-score roles?
- Scoring-model drift signals: if AI_TRAINER 90+ scored roles have <30% response rate, scoring model may be over-calibrated for that archetype
- Suggestions: proposed score adjustments in ref-scoring-model.md (DO NOT auto-apply; flag as follow-ups for user review)

Output: `Efforts/career-search/retros/career-retro-YYYY-MM-DD.md` with canonical frontmatter + calibration findings + proposed follow-ups.

### Phase K: Compare mode (if compare)

Side-by-side matrix across 2+ packet folders (require full slugs as args).

Columns: Raw score / Company health / Archetype / Pay / Remote certainty / Degree barrier / Fit / Contractor rule advance / Red flags / Green flags / Recommendation.

Output: `Efforts/career-search/compare-<slug1>-vs-<slug2>-<date>.md` with canonical frontmatter.

### Phase L: Pre-Output HALT Gate (18 items)

Assert each before Phase M write. Any failure -> HALT, report which failed, F11 stays on.

1. Mode correctly resolved (Phase D rule fired; not default/unknown)
2. Archetype assigned (evaluate/pipeline); keyword hits reported
3. Raw score computed from 8 dimensions (evaluate/pipeline); company-health multiplier applied
4. "Why You're Qualified" section present with specific evidence (evaluate/pipeline)
5. "Why You May Not Be Qualified" (honest gap section) present (evaluate/pipeline)
6. Dollar amounts from disclosed data only; no estimates
7. No HIGH/MEDIUM/LOW confidence; calibrated percentages only
8. 7-file packet complete (pipeline/apply ADVANCE>=80) OR 6-file (ADVANCE 70-79, skip form-answers)
9. `submission-notes.md` includes exact URL + field-by-field + time estimate + Submission Reality Check + Contractor Rule Reality Check
10. Resume tailoring: resume-diff-from-baseline block present in packet resume.md; all "required" JD skills appear in resume; no fabricated content beyond private/resume.md baseline
11. All emitted files have canonical YAML frontmatter with categories, type (where applicable), created, updated, status, tags, related
12. Tag guardrail: all frontmatter tags in {topic/*, company/*, thesis/*}; no type/* or domain/*
13. ASCII-only scan on all new content (Pattern 22); zero non-ASCII bytes introduced
14. Body-preservation sha256 on UPDATED files (tracker, opportunities, entity notes, daily note) strictly-additive
15. Contractor-rule compliance checked (apply mode); WARN-with-override if role does not advance rule
16. Tracker row additive (pipeline) OR state-transition valid (apply/tracker state update)
17. Entity note CREATE-or-UPDATE branch completed with claim-to-section mapping (pipeline/evaluate)
18. FOLLOWUPS:skills block emitted with concrete rationale, or empty case explicitly rendered

### Phase M: Compose canonical output + meta.json sidecar

Write primary output file(s) per mode. For pipeline/apply: 7-file packet + `packet-meta.json` sidecar.

**packet-meta.json schema:**

```json
{
  "schema_version": 1,
  "packet_slug": "<company>-<date>[-HHMM]",
  "generated_at": "YYYY-MM-DDTHH:MM:SS",
  "mode": "pipeline|apply",
  "role_title": "<title>",
  "company": "<company-name>",
  "source_url": "<url>",
  "jd_text_hash": "<sha256 of raw JD text>",
  "archetype": "<archetype>",
  "archetype_keyword_hits": {"ai_trainer": 5, "prompt_engineer": 2, ...},
  "raw_score": 85,
  "company_health_multiplier": 1.0,
  "final_score": 85,
  "dimension_breakdown": {
    "compensation_upside": 23,
    "remote_certainty": 20,
    "skills_match": 14,
    "fit_to_background": 14,
    "degree_barrier": 10,
    "interview_likelihood": 8,
    "speed_to_apply": 5,
    "career_trajectory": 5
  },
  "red_flags": [],
  "green_flags": ["salary transparent", "specific tech stack", "no degree required"],
  "decision": "ADVANCE",
  "contractor_rule_state": {
    "advances_condition_a": true,
    "advances_condition_b": false,
    "rule_status_at_generation": "ACTIVE"
  },
  "resume_diff_from_baseline": [
    "reframed: 'insurance verification' -> 'data quality annotation'",
    "added: 'LLM infrastructure (Ollama, SearXNG)' under Technical"
  ],
  "follow_up_dates": {"follow_up_1": "2026-04-30", "follow_up_2": "2026-05-07", "withdraw_after": "2026-05-14"},
  "phases_timing_ms": {"A": 8, "B": 3, ...}
}
```

### Phase N: Peripheral atomic updates

All peripheral updates succeed or Phase M output is NOT committed (Pattern 13 F.halt).

**Update 1: Efforts/career-search/tracker.md**
- Additive row for new SCOUTED/EVALUATED/ADVANCE rows
- State transition for existing rows (apply, tracker subcommand)
- Auto-compute age_days on all SUBMITTED rows; surface follow-ups
- Body-preservation sha256 on non-table sections

**Update 2: wiki/entities/companies/<Company>.md (CREATE-or-UPDATE; pipeline/apply/evaluate modes)**
- CREATE: grounded in `_templates/entity.md`; canonical frontmatter with `categories: [entity]`, `type: company`, `tags: [company/<slug>, topic/<archetype-topic>]`, `related: [[career-moc]]`; sections: Overview / Culture / Compensation / Growth signals / Layoff signals / Recent mentions
- UPDATE: claim-to-section mapping (/invest + /ingest shared semantics); marker-signature dedup; body-preservation sha256
- Append "Recent" section entry: `[YYYY-MM-DD] Evaluated in [[<slug>-evaluation]]; score <N>; decision <D>`
- Symmetric back-link: add `[[<slug>-evaluation]]` or `[[career-moc]]` wikilinks to Company entity related: as appropriate

**Update 3: Efforts/career-search/opportunities.md**
- Additive row for scanned/evaluated roles (matches tracker)
- Status update where tracker changes
- Body-preservation sha256 outside the table

**Update 4: Calendar/decisions/sessions-log.md**
Append structured entry:
```
### YYYY-MM-DD[-HHMM] -- /career
Domain: career
Mode: <mode>
Decisions ratified: <count; brief description>
Methodology learnings: <pattern-level; if any>
Follow-ups: <count; FOLLOWUPS:skills block emissions>
Skills invoked: /career
Artifacts: [[<primary output>]]
Related: [[tracker]], [[<entity>]], [[goals]]
```

**Update 5: Calendar/daily/<today>.md**
- Re-Read fresh (UserPromptSubmit race handling)
- `daily_before_sha256` computed at this moment
- Append to `## Sessions Run` section: `- [HH:MM] /career <mode> -- <one-line summary>`
- Body outside that section byte-exact

### Phase O: Commit + F11 clear + F17 verify

F14 narrow stage each file explicitly. ASCII-only commit body.

Post-commit verify:
- `git log -1 --format='' --name-status HEAD | grep -E '^[AMDR]'` matches expected file set
- `git log -1 --format='%B' HEAD | grep -cE '^Co-Authored-By:'` returns 0 (anchored F17)

Clear F11: `rm .claude/state/auto-commit-disabled`

### Phase P: Audit Report

Emit to stdout:

```
## /career v2 run complete

Mode: <mode> [rule <N> matched]
Output: <primary file path>
Archetype: <X>  (keyword hits: ...)  [if evaluate/pipeline]
Final score: <N>/100  (raw <N> x company health <X>)
Decision: ADVANCE | HOLD | SKIP
Contractor rule: advances_A=<bool>, advances_B=<bool>, state=<ACTIVE|...>

Files written: <N>  (packet 7-file + sidecar + peripherals)
Entity note: CREATE | UPDATE | unchanged  (company: <Company>)
Tracker: additive row | state transition
Follow-ups due today: <N>  (<list>)
Followup skills emitted: <N>

Pre-Output HALT gate: 18/18 PASS
F11: cleared
F17: Co-Authored-By absent
Working tree: clean

Resume tailoring: resume-diff-from-baseline block verified present
Archetype confidence: <high|medium|low based on keyword hit margin>
```

## 7-file packet spec

For every ADVANCE role, create folder `Efforts/career-search/applications/<slug>-<date>[-HHMM]/` with these files:

| File | Contents |
|------|----------|
| `job-source.md` | Role title, company, URL, date found, posted date, pay, location, requirements, missing data |
| `evaluation.md` | 8-dim score breakdown, archetype + keyword hits, company health, red/green flags, Why Qualified, Why Not Qualified, contractor-rule state, decision |
| `resume.md` | ATS-optimized, tailored per Resume Tailoring Protocol, with resume-diff-from-baseline block at top. Never fabricate beyond private/resume.md baseline. |
| `cover-letter.md` | Concise, role-specific, archetype-aware. Reference Project Osanwe (not "Palantir" -- updated project name). No generic AI fluff. |
| `submission-notes.md` | Exact URL, field-by-field instructions, time estimate, pre-drafted form answers, follow-up dates (+6d, +13d, +21d), Submission Reality Check, Contractor Rule Reality Check |
| `company-intel.md` | Funding, Glassdoor, recent news, AI strategy, key contacts, competitive landscape |
| `form-answers.md` | Pre-drafted answers to common portal questions (ONLY for ADVANCE scores >= 80; skip for 70-79 -- generate on-demand during actual submission) |
| `packet-meta.json` | Machine-readable audit trail (see schema above) |

Full field-by-field contract in `.claude/skills/career/ref-packet-spec.md`.

## Resume tailoring

For evaluate / pipeline / apply modes emitting tailored resume content, **Read `.claude/skills/career/ref-resume-tailoring.md`** for the 7-step keyword-extraction + mapping + rewrite procedure, archetype-specific Project Osanwe reframings, ATS optimization criteria, PAR quantification, and resume-diff-from-baseline block spec. Do NOT produce tailored resume output until this ref is loaded.

## Canonical Frontmatter (per output type)

**Packet files (7 per ADVANCE):**
```yaml
---
categories: [efforts]
type: output
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
tags: [company/<slug>, topic/<archetype-topic>]
related: [[tracker]], [[<Company>]], [[career-moc]]
---
```

**Evaluation standalone (evaluate mode, not pipeline):**
```yaml
---
categories: [efforts]
type: analysis
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
tags: [company/<slug>, topic/<archetype-topic>]
related: [[tracker]], [[opportunities]], [[<Company>]], [[career-moc]]
---
```

**Scan output:**
```yaml
---
categories: [efforts]
type: research
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
tags: [topic/scan, topic/career-pipeline]
related: [[tracker]], [[opportunities]], [[career-moc]]
---
```

**Retro output:**
```yaml
---
categories: [efforts]
type: analysis
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
tags: [topic/retro, topic/calibration, topic/career-pipeline]
related: [[tracker]], [[ref-scoring-model]], [[career-moc]]
---
```

**Company entity (wiki/entities/companies/<Company>.md; CREATE branch):**
```yaml
---
categories: [entity]
type: company
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
tags: [company/<slug>, topic/<archetype-topic>]
related: [[career-moc]], [[tracker]]
---
```

## FOLLOWUPS:skills Block Schema

Every primary output ends with:

```markdown
<!-- FOLLOWUPS:skills -->
- /brief -- career pipeline state change: <X SUBMIT_NOW roles awaiting action, Y follow-ups due today> (trigger: next morning briefing)
- /invest <TICKER> -- company <Company> evaluated, ticker <T> in portfolio, thesis-<slug> implications (trigger: WITHIN 48H if decision AFFECTS thesis)
- /retro -- session-end if substantive pipeline decisions emerged (trigger: end of session)
- /decide -- structured decision record if offer received or major go/no-go (trigger: WITHIN 48H of offer)
<!-- /FOLLOWUPS:skills -->
```

Emit only concrete rationale with triggers. Empty case: `(no followup skills recommended)` between tags.

## Contractor Transition Rule Integration

The rule (per `Atlas/concepts/career/contractor-transition-rule.md`):

- **Condition A**: contractor income > $[CONTRACTOR_MONTHLY_FLOOR]/mo for 2 consecutive months
- **Condition B**: W2 offer >= $[W2_THRESHOLD]/yr
- **Condition C**: explicit force quit ([EMPLOYER] material terms change)

**`/career` integration:**

1. **Evaluate mode** emits `contractor_rule_state` in evaluation.md frontmatter: advances_A / advances_B / rule_status_at_generation
2. **Apply mode** gates with WARN (not HALT) if role does not advance the rule; `--override-rule` flag documents explicit override
3. **Tracker mode** computes current contractor income MTD (from SUBMITTED 1099-platform rows with recorded 1099 payments) and surfaces proximity to threshold
4. **Retro mode** reports rule-state-to-submission correlation (do we keep apply-ing to roles that don't advance the rule? pattern signal)

Rule precedence: the user always retains override. Rule informs, does not block.

## Pre-Output HALT Gate (consolidated; 18 items)

See Phase L for the full 18-item checklist. Gate runs in memory; Phase M does the writing.

## Examples (8 numbered)

1. **Morning scan weekday:** `/career scan` -> Phase E rotates 2 archetype queries; dedups against tracker; emits ranked shortlist to `scans/scan-2026-04-25.md`; auto-advances top 3 scorers to Phase F evaluate and generates packets via Phase G pipeline chaining; FOLLOWUPS block emits `/brief` reminder.

2. **Single URL evaluate:** `/career https://jobs.ashbyhq.com/foo/...` -> Mode rule 1 matches (URL pattern); Phase F runs 8-dim scoring + archetype + company health; emits standalone `evaluations/foo-2026-04-25.md`; tracker gets SCOUTED row.

3. **Standalone evaluate with JD paste:** `/career <500-word JD text>` -> Mode rule 2 matches (text >= 200 words + JD markers); same as example 2.

4. **Pipeline full run:** `/career pipeline` -> Phases E + F + G chain; scan surfaces 8 roles; 3 ADVANCE, 2 HOLD, 3 SKIP; 3 packets generated with 7 files each; tracker updates additively; Company entities CREATE for 2 new companies, UPDATE for 1 existing.

5. **Apply submission prep:** `/career apply outlier-ai-2026-04-10` -> Phase H gates on contractor-rule (Outlier 1099 advances Condition A); expands submission-notes with pre-drafted form answers; tracker EVALUATED -> SUBMIT_NOW.

6. **Tracker check:** `/career tracker` -> Phase I displays pipeline; 3 follow-ups due today (FOLLOW_UP_1 on 3 rows submitted 6-7 days ago); 1 aged-out row (>21 days) proposed for WITHDRAWN; contractor income current month: $0 (nothing submitted yet); rule status: ACTIVE.

7. **Monthly retro:** `/career retro` -> Phase J reads all evaluations + prior retros; reports AI_TRAINER archetype has 5 ADVANCE, 0 SUBMITTED (pattern: generated packets, never submitted); proposes scoring model not the issue -- submission behavior is; FOLLOWUPS: `/decide` for submit-vs-don't decision.

8. **Compare mode:** `/career compare dataannotation-2026-04-10 outlier-ai-2026-04-10` -> Phase K emits side-by-side matrix across 8 dimensions + contractor-rule advance + red/green flags; recommendation based on final score + rule advance.

## Failure Taxonomy (per phase)

- **A**: missing Efforts/career-search/ tree -> HALT with mkdir suggestion; missing private/resume.md -> HALT (blocker)
- **B**: user abort (explicit or --preview early-exit) -> no writes, F11 unset, clean exit
- **C**: ref-*.md load failure -> HALT with missing-file enumeration
- **D**: mode routing fails all rules -> HALT with routing-error + suggested modes
- **E**: WebSearch fails or all results dedup out -> emit "No fresh roles surfaced; dedup count N" + skip Phase F chain; F11 stays on
- **F**: company-health search fails -> default multiplier to 1.0 + flag `health_check_unavailable: true` in evaluation
- **G**: packet mid-batch failure (e.g., 3rd file write fails on 2nd role of batch of 3) -> F.halt; F11 stays on; partial state reported (packet 1 complete in WT; packet 2 files 1-2 complete, file 3 failed, files 4-7 not attempted; packet 3 not attempted); the user decides rollback vs fix-and-retry (idempotency skips complete files)
- **H**: contractor-rule warn does NOT halt; the user proceeds with or without override
- **I**: tracker state transition invalid (e.g., SCOUTED -> OFFER bypasses required states) -> HALT with valid-transitions list
- **J**: insufficient data for calibration (< 5 SUBMITTED packets) -> skip conversion rates; emit "calibration corpus insufficient; N SUBMITTED need >=5"
- **K**: compare mode missing packet folder -> HALT with filesystem check
- **L**: any gate item fails -> HALT, F11 stays on, report which, no writes
- **M**: ASCII scan fails on new content -> HALT; apply V16 sec 3.4 replacement table; re-emit
- **N**: peripheral mid-batch failure -> F.halt; F11 stays on; partial state reported
- **O**: commit fails (pre-commit hook rejects) -> HALT; investigate hook failure before retry
- **P**: always succeeds if we reached this phase

## Coordination (division of concerns)

| Skill | Owns | Reads from /career | Writes to /career |
|-------|------|--------------------|--------------------|
| `/brief` v2 | Daily market briefing | tracker.md (Phase M Optionality Map: career actions ready count) | FOLLOWUPS:skills trigger for `/brief` if pipeline-state-change |
| `/retro` v2.1 | Session retrospective | FOLLOWUPS:skills block, sessions-log entries | -- |
| `/invest` v2 final | Per-ticker analysis | -- | -- (distinct scope) |
| `/ingest` v2 final | Claim distribution | -- | possible future: distill company-intel.md claims to `wiki/entities/companies/<Company>.md` |
| `/decide` (Tier 3 pending) | Structured decision records | accepts `/career` offer events | FOLLOWUPS:skills `/decide` trigger on OFFER state |
| `/challenge` (Tier 3 pending) | Thesis stress-test | -- | -- |
| `/networth` (Tier 4 pending) | Portfolio snapshot | -- | -- |

## Ref docs

**Consumed by `/career`:**
- `.claude/skills/career/ref-scoring-model.md` v2.1 -- 8-dim rubric, health multiplier, calibration feedback fields (new in v2.1)
- `.claude/skills/career/ref-resume-tailoring.md` v2 -- 7-step tailoring, archetype reframings, resume-diff-from-baseline spec (new in v2)
- `.claude/skills/career/ref-packet-spec.md` v1 -- 7-file canonical contract extracted from v1 SKILL.md body
- `.claude/skills/career/ref-ai-trainer-market.md` v1 -- platform taxonomy, classification law (DOL 2024, AB5, Dynamex, IRS three-factor), IAA academic methodology (Cohen kappa, Fleiss kappa, Krippendorff alpha), RLHF/RLAIF/DPO demand-cycle framework, worker-advocacy frameworks (Fairwork, DAIR, Data Workers Inquiry, OII), contractor-transition-rule calibration methodology; 5,519 words / 52 citations; inline-composed after Pattern 21 Deep Research attempted 3x (topic opacity prevented Research-mode citation-density floor)
- `.claude/skills/career/ref-interview-tradecraft.md` v1 -- interview-modality taxonomy (behavioral vs technical vs assessment-based) with Schmidt-Hunter predictive-validity meta-analysis; STAR/CAR/SOAR behavioral frameworks; technical + work-sample + async video (HireVue/VidCruiter/Modern Hire) tradecraft; remote interview mechanics; Harvard Program on Negotiation BATNA + Chris Voss tactical emotional intelligence salary negotiation; reference prep protocols; post-interview follow-up; offer evaluation matrix integrating contractor-transition-rule Condition B; 8 user-specific STAR story seeds from vault assets; 6,287 words / 80 citations; Deep Research Pattern 21 composed
- (excluded: ref-contractor-economics.md -- employer wage/tax math not included in this distribution)

**Pattern 21 Deep Research candidates (DEFERRED):** (none -- triptych complete 2026-04-23)

**External vault refs consumed:**
- `Atlas/sources/career/ref-remote-data-careers.md`
- `Atlas/sources/career/ref-skills-translation.md`
- `Atlas/sources/career/ref-target-markets.md`
- `Atlas/sources/career/ref-company-health.md`
- `Atlas/concepts/career/goals.md`
- `Atlas/concepts/career/skills-inventory.md`
- `Atlas/concepts/career/contractor-transition-rule.md`

## Archive

v1 at `.claude/skills/_archive/career-v1/` (SKILL.md + ref-scoring-model.md + ref-resume-tailoring.md; byte-exact sha256 verified at archive time).


## Phase O.0 -- Pre-commit /vault audit gate (v2.0; CAT-3 prevention-architecture parity)

After composing all target file modifications IN MEMORY but BEFORE atomic write:
1. Write each composed file to a tmp dir under `wiki/research/test-tmp/.precheck/career-<slug>/`
2. Run `python tools/skill-precheck.py <tmp-files...> --skill /career`
3. Parse exit code: 0 -> proceed; 2 -> HALT with diagnostic
4. Body-scope wikilink validation: per /retro v2.2 Phase D pattern, scan composed body text for unresolved `[[<target>]]` and mechanically de-link unresolved targets (vault-resolved keep / MEMORY_PREFIXES rewrite as `[[memory:<stem>]]` / placeholder leave / else strip). Fence-aware (skip ``` fenced + `inline code`).
5. Bypass: `CLAUDE_VAULT_BYPASS_VALIDATOR=1` (logged to `.claude/state/bypasses-<date>.log`)

Defense-in-depth on top of PreToolUse pre-write-validator.py + PostToolUse wikilink-check.py / frontmatter-check.py / orphan-check.py. The Phase O.0 gate prevents broken composition from reaching disk in the first place.

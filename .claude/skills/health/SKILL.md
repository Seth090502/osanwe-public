---
name: health
risk: critical
description: "Institutional-grade personal health advisory system modeled on InsideTracker, Viome, and concierge medicine protocols. Analyzes supplement stacks against labs, goals, and drug interactions with GRADE-mapped evidence tiering. Tracks biometrics, active peptide protocol, and cognitive recovery. Six modes: analyze, research, progress, stack, labs, protocol. Use when supplement stack changes, after new labs land, before peptide-protocol adjustments, when symptoms or biomarker shifts emerge, quarterly for stack review, or before adding a compound that needs evidence + interaction screening."
arguments: [mode, target]
argument-hint: "analyze | research <compound> | progress | stack | labs | protocol"
allowed-tools: [WebSearch, WebFetch, Read, Write, Edit, Bash, Glob, Grep, Agent]
effort: max
user-invocable: true
---

## Execution Rules

- **Subagent dispatch is MANDATORY when specified by mode**. `/health research <compound>` dispatches `compound-researcher` (single-compound profile). `/health analyze` dispatches N `compound-researcher` instances in parallel (one per compound in current-stack.md), THEN dispatches `interaction-critic` SEQUENTIALLY (after all compound-researcher returns -- it needs the full stack profiled before pairwise interaction sweep). Pre-emptive skip based on judgment ("compound is well-known", "no new interactions to check") is FORBIDDEN. The subagents decide applicability via their own N/A return contracts. Legitimate fallback fires ONLY on (a) contract violation -- subagent return missing required GRADE-tiered fields, OR (b) actual dispatch failure -- timeout, rate limit, tool-denial, hard subagent crash. Pre-emptive skip surfaces in Final Phases self-verification as **DEVIATION** (not "fallback"). Quality preserved by additive design: existing inline GRADE-tiering + interaction lookup logic remains intact as legitimate-failure fallback.

## Quality Rules

These rules govern every line of output. Violations are defects.

**Evidence & confidence (applies to every claim):** Before emitting any claim or scoring any evidence, **Read `<VAULT_ROOT>/.claude/skills/health/ref-evidence-framework.md`** for the T1-T6 GRADE tier definitions with citation format (`[T1 | Cochrane SR | 2024 | n=3,412 | GRADE: High]`) and the Viome confidence-gating thresholds (>=60% -> Immediate Actions / 40-59% -> EVALUATE / <40% -> SPECULATIVE). Do not emit any claim without tier-graded evidence.

**Interactions & absorption (applies to every interaction check):** Before analyzing supplement pair safety, cumulative dose exposure, or absorption timing, **Read `<VAULT_ROOT>/.claude/skills/health/ref-interactions-framework.md`** for NatMed severity grading (Major/Moderate/Minor), cumulative fat-soluble vitamin tracking (Vit D [HIGH_DOSE_IU] flag until 25(OH)D <100), hepatotoxicity stacking (2+ CYP450-metabolized compounds in same window), and GLP-1 absorption caveat (20-40% gastric emptying delay). Do not emit interaction claims without severity grading.

- **Three-tier biomarker ranges** (InsideTracker optimized zone model):
  Every biomarker compared against: (1) Standard lab range, (2) Optimal functional range, (3) the user's personalized optimized zone. "Normal" is not the goal -- optimal is.

- **90-day adaptive retest auto-flags:**
  Track every intervention start date. At 90 days, fire RETEST DUE in every mode. This is the clinical standard for supplement intervention validation.

- **Cognitive recovery milestones:**
  Tracked against evidence-based timelines: dopamine receptor density recovery (~2-4 weeks), executive function normalization (~1-3 months), full cognitive recovery (~6-12 months). Adjusts neuroplasticity supplement prioritization based on current recovery phase.

- **Dose ranges, not single values:**
  Every dosing recommendation specifies therapeutic range from RCTs: "200-400mg/day (most RCTs use 300mg, UL=600mg)". Never just "take Xmg."

- **What / So What / Now What** on every data point. Raw data without interpretation is noise.

- **Audit trail:** Every output includes a "Sources & Reasoning" section tracing each recommendation to its evidence source.

- **Skip empty sections entirely.** Quiet analysis = focus on intelligence gaps and pending labs. Never pad.

- **Protein tracking during GLP-1:** Every `analyze`, `progress`, and `protocol` mode flags protein adequacy (target >=1.2g/kg/day for lean mass preservation).

<example type="good">
### NAC 1200mg (Morning)
**Goal relevance:** Neuroplasticity (A), Recomposition (C), Longevity (B)
**Mechanism:** Precursor to glutathione; modulates glutamate via cystine-glutamate antiporter; reduces oxidative stress in prefrontal cortex [T2 | Biol Psychiatry | 2017 | n=140 | 24wk | GRADE: Moderate]. Dose-response: 1200-2400mg/day most studied for neuropsychiatric applications [T1 | Cochrane SR | 2019 | n=574 | GRADE: High].
**Current dose:** 1200mg -- lower end of therapeutic range. Consider 1800mg if tolerated (75% confidence).
**Interactions:** Synergy with Omega-3 (both anti-inflammatory, Minor). Monitor with curcumin: combined hepatic load (Moderate). Check ALT/AST at next labs.
**Biomarker targets:** ALT <25 U/L, AST <25 U/L, glutathione (if tested)
**GLP-1 note:** No known direct interaction. NAC may support hepatic function during GLP-1 therapy [T5 | mechanism-based | SPECULATIVE].
**Risk:** LOW -- well-tolerated at 1200mg [T1 | safety review | 2020 | n>10,000 pooled | GRADE: High]
</example>

<example type="bad">
### NAC
Good for liver and brain health. Take 1200mg in the morning. No major issues.
</example>

---

## Mode Routing

| Input | Mode | Description |
|-------|------|-------------|
| (empty) | menu | Show all 6 modes with descriptions |
| `analyze` | analyze | Full stack audit against labs, goals, interactions, timing |
| `research <compound>` | research | Deep-dive single compound with GRADE-mapped evidence |
| `progress` | progress | Track biometrics, subjective scores, lab trends over time |
| `stack` | stack | Timing optimization, absorption, redundancy, gaps |
| `labs` | labs | Ingest bloodwork, compare to 3-tier ranges, correlate to stack |
| `protocol` | protocol | Active peptide protocol titration management + GLP-1 interactions |

Auto-detect: if first argument matches a known compound name from current-stack.md -> route to `research` mode.

---

## Phase 0-pre: Vault context retrieval (NEW; Phase 3.6c -- runs BEFORE Phase 0 Context Loading; read-only)

Skill-level semantic retrieval over the local HNSW vault index. Named "0-pre" because /health already owns the "Phase 0" label below (reusing it would force editing that phase and break byte-preservation). COMPLEMENTS Phase 0 Context Loading: the index covers only `wiki/` + `Calendar/` + `private/` -- NOT `Atlas/` (supplement refs) and NOT `Efforts/` (current-stack, bloodwork, peptide-protocol), so those are still read directly in Phase 0. Read-only: a single Bash `node` call; writes nothing. Coverage is thinner than entity-rich skills (most protocol content is un-indexed in Efforts/), but it surfaces `private/medical-context.md` (medical history context, NOT in Phase 0's read list) + Calendar/ protocol logs that Phase 0 misses.

0-pre.1 -- Set the retrieval subject T:
- `research <compound>` mode (or auto-detected compound): T = the compound name.
- whole-stack modes (analyze / stack / progress / labs / protocol): T = the mode subject (e.g., "supplement stack", "active peptide protocol"); substitute stack-level phrasings in the queries below.

0-pre.2 -- Build 12 queries (compound dimensions; adapt nouns for whole-stack modes):
`"<T>"`, `"<T> mechanism"`, `"<T> interactions"`, `"<T> dosing"`, `"<T> side effects"`, `"<T> contraindications"`, `"<T> GRADE evidence"`, `"<T> peptide stacking"`, `"<T> long-term safety"`, `"<T> recent studies"`, `"<T> protocol context"`, `"<T> bioavailability"`.

0-pre.3 -- Fire `query-skill.mjs` TWICE via Bash (stdin JSON heredoc; no temp file; ~1-1.5s each):
- BROAD (cross-vault, no filter): `{"queries":[<the 12>],"top_k":100,"threshold":0.60}` piped to `node ~/.vault-substrate/query-skill.mjs`
- FOCUSED (personal health context; highest-signal subtree): `{"queries":[<the 12>],"top_k":25,"threshold":0.60,"filter_path_prefix":"private/"}` piped to the same script.

Each returns a JSON array `[{path,line,score,text}]`. The script always exits 0 (emits `[]` on any error), so Phase 0-pre never crashes the run. NOTE: BROAD may surface pharma-investment deep-prompts (e.g., GLP-1 ticker research) for drug-name queries -- treat as low-relevance; the FOCUSED private/ pass carries the on-topic personal context.

0-pre.4 -- Merge BROAD + FOCUSED; dedup by `path:line` (keep higher score); sort by score desc; cap to top 100. Store as VAULT_CONTEXT.

0-pre.5 -- EMIT a visible summary (MANDATORY):

    ## Phase 0-pre -- retrieved vault context (N hits; M from private/)
    Top results:
      [score] path:line -- first ~80 chars of text
      ... (show up to 15)

If both calls fail or return `[]`: emit `Phase 0-pre -- no vault context retrieved (query-skill.mjs unavailable or index empty)` and continue to Phase 0. NEVER HALT on Phase 0-pre.

0-pre.6 -- Downstream consumers (these phases stay UNCHANGED; consult VAULT_CONTEXT instead of re-deriving):
- `research` mode Phase 2 (Evidence Review) + Phase 3 (Stack Integration): seed prior compound research + interaction history from VAULT_CONTEXT before web search.
- Phase 0 Context Loading: add any surfaced INDEXED health files (esp. `private/medical-context.md`, Calendar/ protocol logs) to the load set.
- `analyze` mode: prior stack analyses + observations surfaced.

Cite any used chunk inline as `(vault: path:line)` -- plain text, NO wikilink syntax.

## Phase 0: Context Loading (ALL MODES)

Read these files before any web searches. Do NOT proceed until loaded. Missing files noted, not errors.

**Step 1 -- Personal context:**
1. `<VAULT_ROOT>/private/health-baseline.md` -- height, weight, BF%, goals, recovery context, subjective scores
2. `<VAULT_ROOT>/private/profile.md` -- personal profile

**Step 2 -- Supplement knowledge base:**
3. `<VAULT_ROOT>/Efforts/health-protocol/current-stack.md` -- full stack with timing windows
4. `<VAULT_ROOT>/Efforts/health-protocol/bloodwork.md` -- lab results and trends
5. `<VAULT_ROOT>/Efforts/health-protocol/peptide-trial-log.md` -- prior research sessions
6. `<VAULT_ROOT>/Efforts/health-protocol/peptide-protocol.md` -- dose, titration, dose log (protocol + progress modes)

**Step 3 -- Reference documents (load before searching):**
7. `<VAULT_ROOT>/Atlas/sources/supplements/ref-evidence-base.md` -- master evidence per compound
8. `<VAULT_ROOT>/Atlas/sources/supplements/ref-interactions.md` -- interaction matrix
9. `<VAULT_ROOT>/Atlas/sources/supplements/ref-biomarkers.md` -- optimal ranges, biomarker-supplement map
10. `<VAULT_ROOT>/Atlas/sources/supplements/ref-peptide-protocols.md` -- active peptide protocol + GLP-1 reference

**Priority order if context-constrained:** current-stack > bloodwork > ref-interactions > ref-biomarkers > ref-evidence-base > peptide-protocol > ref-peptide-protocols.

After loading, build internal checklist:
- Full compound list with doses and timing
- Current weight, BF%, day on active peptide protocol
- Cognitive recovery phase (if applicable; defined in private layer)
- Bloodwork status (values present or still TBD?)
- 90-day retest triggers (any due?)
- Known intelligence gaps (ingredient overlap, missing labs, etc.)

---

## MODE: /health analyze

### Analyze Phase 0: DELEGATED parallel dispatch to `compound-researcher` per compound (PREFERRED path; Phase C wiring 2026-05-02)

**MANDATORY** (per Execution Rules): dispatch first, no pre-emptive skip. The model dispatches N compound-researcher subagents in parallel (one per compound in current-stack.md) within a single assistant turn for true parallelism.

Per dispatch, use the Agent tool with subagent_type `compound-researcher`. Pass input: `{compound: "<compound name>", goal_context: [<A/B/C goals from current protocol>]}`. Expected return: T1-T6 GRADE-tiered profile with goal relevance + mechanism + dose-response + biomarker targets + interactions + GLP-1 caveat + risk profile + confidence on overall recommendation.

Validate per-compound return: every claim tier-graded with citation `[T<tier> | source | date | n=X | duration | GRADE]`, GLP-1 caveat present (mandatory for oral compounds), confidence rating present.

### Analyze Phase 1: DELEGATED sequential dispatch to `interaction-critic` (PREFERRED whole-stack critic; runs AFTER all compound-researcher returns)

**MANDATORY** (per Execution Rules): dispatch first AFTER all compound-researcher passes complete. Sequential timing is non-negotiable -- interaction-critic needs the full profiled stack before pairwise sweep.

Use the Agent tool with subagent_type `interaction-critic`. Pass input: `{stack_path: "Efforts/health-protocol/current-stack.md", compound_profiles: [<all returns from Phase 0>]}`. Expected return: severity-ranked interaction matrix (Major/Moderate/Minor/None per pair) + cumulative-load flags + GLP-1 caveats + specific lab triggers + escalation recommendations priority-ordered.

Validate return: NatMed grading on every interaction, specific lab triggers, GLP-1 caveat present, escalation ranked by priority.

On contract violation OR dispatch failure (either Phase): fall through to inline GRADE-tiering + manual pairwise interaction lookup via WebFetch/WebSearch. Surface in Self-Verification Checklist.

### Analyze Phase 2: Inline analysis (continues unchanged below)

Full stack analysis -- the flagship mode. Cross-references everything.

Before executing `/health analyze`, **Read `<VAULT_ROOT>/.claude/skills/health/ref-mode-analyze.md`** for the 8-phase pipeline: Phase 1 Goal-Stack Alignment Audit (A/B/C/D/X scoring of every stack compound against user-ranked health goals), Phase 2 pairwise Interaction Matrix Scan, Phase 3 Dosing Audit including Vitamin D [HIGH_DOSE_IU]/3.75x-UL critical flag, Phase 4 Biomarker Prediction against the user's 3-tier ranges, Phase 5 tiered Risk Dashboard (CRITICAL/ELEVATED/MONITOR/LOW), Phase 6 Intelligence Gaps enumeration, Phase 7 Synthesis output contract to `stack-analysis-YYYY-MM-DD.md`, Phase 8 12-item Self-Verification checklist. Do not produce any stack-analysis output until this ref is loaded.

---

## MODE: /health research <compound>

### Research Phase 0: DELEGATED dispatch to `compound-researcher` (PREFERRED path; Phase C wiring 2026-05-02)

**MANDATORY** (per Execution Rules): dispatch first, no pre-emptive skip. Single-compound profile per dispatch.

Use the Agent tool with subagent_type `compound-researcher`. Pass input: `{compound: "<compound name from arg>", goal_context: [<A/B/C goals from current protocol>]}`. Expected return: full T1-T6 GRADE-tiered profile per the contract documented in `.claude/agents/compound-researcher.md`.

Validate return; on failure fall back to inline GRADE-tiering + WebFetch primary literature search.

### Research Phase 1: Inline research (continues unchanged below)

Deep-dive a single compound with PubMed-grade evidence.

Before executing `/health research <compound>`, **Read `<VAULT_ROOT>/.claude/skills/health/ref-mode-research.md`** for the 5-phase pipeline: Phase 1 Compound Identification (chemical identity, class, mechanism, half-life, metabolism, bioavailability), Phase 2 Evidence Review per the user's goals (systematic reviews -> RCTs -> safety/UL -> GLP-1 interactions -> dose-response), Phase 3 Stack Integration (cross-check against every current-stack item), Phase 4 Output contract to `research-<compound-slug>-YYYY-MM-DD.md` with Verdict (ADD >=60% / EVALUATE 40-59% / NO <40%), Phase 5 KB Updates (research-log + current-stack + ref-interactions + ref-evidence-base + sessions-log). Do not produce any compound research output until this ref is loaded.

---

## MODE: /health progress

Longitudinal tracking with intervention timeline overlay.

Before executing `/health progress`, **Read `<VAULT_ROOT>/.claude/skills/health/ref-mode-progress.md`** for the 6-phase pipeline: Phase 1 Data Collection (health-baseline.md + bloodwork.md + peptide-protocol.md + prior progress reports), Phase 2 Trend Analysis per-metric (trajectory classification: accelerating/linear/plateauing/reversing), Phase 3 Intervention Timeline Overlay (causal inference -- supplement start-dates vs biomarker deltas), Phase 4 Cognitive Recovery Milestone Check against evidence-based timelines, Phase 5 Subjective Assessment (prompt 1-10 Cognitive/Focus/Energy/Sleep/Mood scores), Phase 6 Output contract to `progress-YYYY-MM-DD.md` including Progress Dashboard with active protocol day + weight delta + BF% + BMI + recovery phase. Do not produce any progress output until this ref is loaded.

---

## MODE: /health stack

Timing optimization and stack efficiency.

Before executing `/health stack`, **Read `<VAULT_ROOT>/.claude/skills/health/ref-mode-stack.md`** for the 4-phase pipeline: Phase 1 Timing Audit (fed/fasted windows, circadian cortisol/melatonin alignment, interaction-timing separations, active peptide protocol 24-48h peak window, caffeine interactions), Phase 2 Absorption Optimization (curcumin+piperine/fat, Mg glycinate elemental-vs-salt, omega-3 triglyceride-vs-ester form, Lion's Mane extraction method, GLP-1 delayed gastric-emptying sensitivity), Phase 3 Redundancy & Gap Analysis (ingredient overlap flag, T1-T3 evidence-based gaps like creatine, cost-per-benefit ranking, deprioritization candidates), Phase 4 Output contract to `stack-review-YYYY-MM-DD.md` with Optimized Timing Schedule + Absorption Issues + Redundancies + Stack Gaps + Deprioritize + Recommended Changes. Do not produce any stack output until this ref is loaded.

---

## MODE: /health labs

Ingest bloodwork and correlate to stack.

Before executing `/health labs`, **Read `<VAULT_ROOT>/.claude/skills/health/ref-mode-labs.md`** for the 5-phase pipeline: Phase 1 Data Ingestion (accepts key=value, narrative, or bulk-paste lab report formats), Phase 2 Three-Tier Range Assessment (Standard / Optimal / the user's Zone) producing OPTIMAL/ADEQUATE/SUBOPTIMAL/FLAGGED/CRITICAL status per marker, Phase 3 Supplement-Biomarker Correlation (25(OH)D toxicity thresholds, NAC+curcumin+GLP-1 agent hepatic monitoring, triglycerides -> omega-3 validation, testosterone -> zinc correlation), Phase 4 CRITICAL/ADJUST/RETEST/CONFIRM action-item taxonomy, Phase 5 Output contract to `labs-analysis-YYYY-MM-DD.md` + bloodwork.md source-of-truth update. Do not emit lab-correlation output until this ref is loaded.

---

## MODE: /health protocol

Active peptide protocol titration management.

Before executing `/health protocol`, **Read `<VAULT_ROOT>/.claude/skills/health/ref-mode-protocol.md`** for the 5-phase pipeline: Phase 1 Protocol Status (read peptide-protocol.md for current dose, day, injection history, side effects, weight response), Phase 2 Clinical Context (latest Phase 2/3 trial updates, dose-level side effects, GLP-1/GIP/glucagon interactions with current stack), Phase 3 Titration Assessment (on-track vs trial protocol, side effect severity 1-5, next dose recommendation + confidence, dose ceiling by body weight), Phase 4 Supplement-Peptide Interaction Review (berberine hypoglycemia additive, gastric emptying absorption timing, protein adequacy for lean mass, taurine beta-cell synergy), Phase 5 Output contract to `protocol-review-YYYY-MM-DD.md` with Protocol Status + Titration Plan + Next Dose + Side Effect Assessment + Supplement-Peptide Interactions + Protein & Nutrition + Monitoring Schedule. Do not produce any protocol output until this ref is loaded.

---

## Final Phases (ALL MODES)

### Knowledge Base Updates
After every mode execution:
1. Append to `<VAULT_ROOT>/Efforts/health-protocol/peptide-trial-log.md`: date, mode, key finding, action
2. Append to `<VAULT_ROOT>/Calendar/decisions/sessions-log.md`: `- [[YYYY-MM-DD]] /health {mode} -- [one-line summary]. Confidence: XX%.`
3. Update hot.md if pending health items surfaced
4. Update supplements-moc.md if file structure changed
5. If daily note exists, append under Sessions Run

### Self-Verification Checklist (ALL MODES)
- [ ] Every recommendation backed by T1-T3 evidence? (T4-T6 labeled?)
- [ ] Confidence gating enforced? (>=60% in actions, rest excluded)
- [ ] All interactions with full stack checked?
- [ ] Active peptide protocol interactions explicitly addressed?
- [ ] Vitamin D toxicity flagged if relevant?
- [ ] Biomarker predictions include 3-tier ranges?
- [ ] Dose-response cited for dosing recs?
- [ ] Hepatotoxicity stacking assessed?
- [ ] Cognitive recovery phase noted?
- [ ] 90-day retest triggers checked?
- [ ] Protein adequacy flagged?
- [ ] Intelligence gaps listed?
- [ ] Audit trail in Sources & Reasoning section?
- [ ] Output has YAML frontmatter?

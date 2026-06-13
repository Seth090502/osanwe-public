---
categories: [sources]
type: reference
created: 2026-04-26
updated: 2026-04-26
status: active
tags:
  - topic/skill-infrastructure
  - topic/pattern-detection
  - topic/spark
aliases:
  - spark pattern taxonomy
  - 9 pattern classes
related:
  - "[[SKILL|/spark SKILL.md]]"
  - "[[ref-output-template]]"
---

# /spark Pattern Detection Taxonomy

The 9 pattern classes /spark looks for, with REQUIRED markers + IDENTIFYING evidence + per-class confidence calibration. SKILL.md Phase E references this doc; this doc holds the detection rules.

Detection rules follow Pattern 6 deterministic-routing discipline (analogous to /enrich Rules 1-22): explicit REQUIRED conditions + IDENTIFYING markers (not probabilistic scoring). Pattern 19 substantive-mention threshold (>=3 occurrences OR dedicated H2/H3 section) integrates into evidence-count calculations.

## Class 1 -- Cross-domain emergence

**REQUIRED:**
- Entity OR concept appears in >=2 distinct domains within timeframe
- Domains: investing, career, health, golf, meta, personal (use top-level path classification)
- Pattern NOT already named in `wiki/insight-stream.md` as cross-domain

**IDENTIFYING markers:**
- Entity-name match (ticker stem, company name, person name, concept noun-phrase) across files in 2+ domain subtrees
- Conceptual frame transfer (e.g., "progressive overload" appearing in golf-practice + career-skills + investing-position-sizing contexts)

**Confidence calibration:**
- Base: 70%
- +10% per additional domain (3 domains -> 80%; 4 domains -> 90%)
- -15% if any underlying source is Grade-D speculation
- Cap: 90%

**Example detection:**
- Sample evidence: `wiki/entities/tickers/MU.md` (investing) + `Efforts/career-search/applications/` (career) both reference "memory bandwidth" within 14d
- Promoted IF substantive-threshold met (each domain has >=2 file mentions OR dedicated section) AND not in insight-stream

## Class 2 -- Behavioral pattern

**REQUIRED:**
- >=3 instances of same behavior shape across distinct dates (not single-session)
- Consistent across actor's stated decision context (not coincidence-of-circumstance)

**IDENTIFYING markers:**
- Behavior-shape grammar: "<actor> <verb> <N> times when <trigger context>"
- Examples: "the user revises allocation 5x in single session before locking in", "the user defers career submission when sleep <6h", "the user increases position size on green-screen-day after green-screen-day"

**Confidence calibration:**
- Base: 75%
- Cap at 90% even with 5+ instances (always self-reported behavior; observer effect risk)
- -10% if instances span >30 days (recency dilution)
- -20% if instances are post-hoc reconstruction (no contemporary daily-note evidence)

**Example detection:**
- Sample evidence: decision-log entries on 2026-04-15 ("the user micro-revised allocation 5x") + 2026-04-16 ("the user re-revised after 60-agent research") + 2026-04-25 ("Roth deployment plan-deviation: $[PORTFOLIO_VALUE] went into concentrated <thesis-slug> adds vs the ratified diversified core plan")
- Pattern: "the user revises high-stakes allocations multiple times within same decision window, often diverging from earlier ratified plans"

## Class 3 -- Thesis evolution

**REQUIRED:**
- >=2 thesis-essay edits OR >=2 thesis-status mentions in briefings showing frame-shift
- Frame-shift indicators: HEALTHY -> WATCH transition, new invalidation trigger added, conviction language change ("HIGH" -> "MEDIUM"), new sub-thesis introduced, sub-thesis dropped

**IDENTIFYING markers:**
- Git diff on `Atlas/concepts/investing/theses/thesis-*.md` showing material section change
- Briefing thesis-status board entries differ across timeframe (e.g., thesis-<slug> HEALTHY in briefing-2026-04-19 -> HEALTHY-WATCH in briefing-2026-04-25)
- Conviction-percentage shifts across `wiki/investing/analyses/*.md` for same ticker

**Confidence calibration:**
- Base: 70%
- +10% if confirmed by recent /challenge against this thesis
- Cap: 85% pre-/challenge; 95% post-/challenge confirmation

**Example detection:**
- thesis essay edited 2026-04-22 to add "HBM oversupply Q1 2027" as invalidation trigger; not previously listed
- 9 held positions in thesis showing RSI >70 simultaneously -> mean-reversion exposure framing emerged
- Pattern: "Thesis evolving from pure-supercycle frame to supercycle-plus-mean-reversion-watch frame"

**vNEXT corpus (2026-06-10; additive):** `wiki/investing/calibration-monitor.md` Call Log rows are first-class thesis-evolution signal -- scored verdicts, conviction% drift across calls on the same ticker, and thesis_status column transitions (CONFIRM -> CONFIRM-with-caveats -> CHALLENGE) ARE frame-shifts. The orchestrator passes the row extract (parent-passed; scouts do not need to locate the file).

## Class 4 -- Recurring failure mode

**REQUIRED:**
- >=2 instances within 30 days of same failure shape
- Identifiable upstream trigger common to all instances
- NOT coincidence: shared upstream causal mechanism

**IDENTIFYING markers:**
- Decision-log entries with similar "Why failed" or post-mortem framing
- Sleep-state, time-of-day, market-condition, emotional-state markers consistent across instances
- Daily-note observations capturing the trigger condition

**Confidence calibration:**
- Base: 80%
- +5% per additional confirmed instance
- -20% if instances are coincidental (no shared upstream causal mechanism identified)
- Cap: 90%

**Example detection:**
- Sample evidence (synthetic): a 23:00 daily-note entry ("pivoted to an IRA contribution decision while self-reporting 50% cognitive capacity, conflating a position trim with the funding decision") + a same-day 16:00 entry ("flagged sleep deprivation; decisions postponed") + a later entry ("deployment deviated from a 12-day-old ratified plan")
- Upstream trigger: cognitive-load-degradation -> impulse-execution
- Pattern: "Sleep-deprived or stale-context sessions produce plan-deviating execution; sleep-gate rule adopted but not consistently enforced"

**vNEXT corpus (2026-06-10; additive):** `wiki/investing/calibration-monitor.md` NEW-vs-SHADOW rating divergences and (once realized) Brier-scored misses are failure-mode signal with built-in outcome resolution -- a repeated divergence shape across rows satisfies the shared-upstream-trigger requirement mechanically. The orchestrator passes the row extract.

## Class 5 -- Decision-pattern divergence

**REQUIRED:**
- Decisions in domain A diverge in style from decisions in domain B
- Style dimensions: aggressive/conservative, fast/slow, ratified/improvised, single-bet/diversified
- >=3 decisions per domain in decision-log within timeframe (substantive sample)

**IDENTIFYING markers:**
- Aggressive-vs-conservative gap: e.g., investing decisions show [CONCENTRATION] <thesis-slug> concentration BUT career decisions delay all 4 ready-to-submit packets
- Fast-vs-slow gap: investing GTC-limits placed within minutes; career packets composed but unsubmitted for 13+ days
- Single-bet-vs-diversified gap: $[PORTFOLIO_VALUE] Roth concentrated to <thesis-slug> adds vs the simultaneous diversified core plan

**Confidence calibration:**
- Base: 65% (speculative class; pattern can be coincidence)
- Cap: 80%
- -15% if either domain's decision sample is borderline-substantive (<5 decisions)

**Example detection:**
- Pattern: "Investing decisions are aggressive-fast-concentrated; career decisions are conservative-slow-procrastinated. Activation-gating asymmetry: investing actions executed despite high uncertainty; career actions blocked despite low uncertainty (a packet score 91, unsubmitted 13+ days)."

**vNEXT corpus (2026-06-10; additive) -- ratified-vs-EXECUTED gap detection:** cross-reference decision-log + sessions-log RATIFIED decisions against subsequent execution artifacts (orders placed, submissions sent, file mutations). A ratified decision with zero execution artifacts and no formal decline IS decision-divergence -- one instance is signal, two is pattern (existing rule). Additional parent-passed extracts: the latest overnight ratification queue (`wiki/research/overnight-summary-*.md` RATIFICATION QUEUE section) and the `wiki/maintenance/proposals/` inventory (proposed-but-unratified aging: a proposal aging past its own trigger window without ratify/decline is the same gap shape). Canonical positive control: a ratified trade, unexecuted for an extended window, formally surfaced only by a subsequent challenge sweep -- this class must be able to construct that gap from primary sources alone.

## Class 6 -- Negative space

**REQUIRED:**
- Topic/ticker/concept appeared >=3 times in timeframe-prior-to-window
- ZERO mentions in current timeframe
- NO explicit dropped-decision in decision-log
- NOT in DEPRECATION-AWARE EXCLUDE-LIST

**DEPRECATION-AWARE EXCLUDE-LIST (maintained per vault state, 2026-04-26):**
- Skills: `/research`, `/review` (deprecated 2026-04-26)
- Tickers/companies: any with status: dropped or status: deprecated in entity note
- Theses: any thesis essay with status: invalidated
- Efforts: any with status: complete or status: dropped
- Career packets: any with status: closed or status: rejected
- Add to this list as deprecations occur (consume from `Calendar/decisions/decision-log.md` deprecation entries)
- **Part W honest-gaps register (vNEXT 2026-06-10; parent-passed extract):** documented doc-only fictions (schema paths that exist only in documentation), excised subsystems (e.g., /review + Calendar/weekly/, OpenClaw), security-deferred integrations, and known-dormant domains are DOCUMENTED absences, NOT mysterious negative space. Cite pointer-style as "(master-context Part W register)"; never quote the register at length and never read the master-context doc directly -- the orchestrator passes the extract.

**IDENTIFYING markers:**
- Topic-frequency histogram across full vault (use grep counts on basename or ticker stem)
- Date-window comparison: `git log --since=<prior-window> --until=<window-start>` vs `git log --since=<window-start>` for entity-stem mentions

**Confidence calibration:**
- Base: 70%
- +10% if the missing thing was decision-grade (recommended BUY, planned action, ratified next-step)
- -10% if expected-archived (caught by exclude-list edge case)
- Cap: 85%

**Example detection (hypothetical):**
- LRCX mentioned 3x in `Atlas/concepts/investing/investing-research-log.md` between 2026-04-01 and 2026-04-08 ("LRCX research priority", "LRCX semiconductor equipment thesis", "LRCX 5-yr DCF")
- ZERO mentions across all daily notes, sessions-log, decision-log, briefings between 2026-04-12 and 2026-04-26
- No explicit dropped-decision in decision-log
- Pattern: "LRCX abandoned silently; was 3-time research target, now zero attention; check whether intentional drop or memory leak"

## Class 7 -- Frequency x recency inversion

**REQUIRED (one of two sub-types):**
- (a) **Frequent-but-staling:** topic frequent (>=5 mentions across timeframe) but no progress markers (no decision-log entry, no entity-note update with new claims, no analysis output)
- (b) **Rare-but-accelerating:** topic rare in week 1 of timeframe (<=1 mention) but accelerating in weeks 2-3 (>=3 mentions/week)

**IDENTIFYING markers:**
- Topic-frequency time-series across timeframe (split into weekly buckets)
- Progress-marker presence: decision-log entry, entity-note `## Recent` section update, analysis-file creation, GTC-order placement, application submission

**Confidence calibration:**
- Base: 75% for accelerating; 65% for staling
- Cap: 85% accelerating; 75% staling (harder to verify "no progress" definitively)
- -15% if topic is meta/methodology (less actionable)

**Example detection:**
- (a) Staling: "career strategy" appears in 8 daily notes across 14d; ZERO new applications submitted; 4 packets remain READY_TO_SUBMIT for 13+ days. Pattern: "Career strategy is over-discussed and under-executed; submission-friction is the bottleneck, not strategy gap."
- (b) Accelerating: "PayPal account setup" mentioned 0x in week 1, 3x in week 2, 5x in week 3 across daily notes + decision-log + tracker. Pattern: "PayPal blocker accelerating into critical path for any 1099-platform activation; deserves /decide treatment."

## Class 8 -- Tool/skill usage pattern

**REQUIRED (one of two sub-types):**
- (a) **Skill cluster co-occurrence:** specific skills consistently invoked together (e.g., /brief -> /challenge -> /decide pattern across 3+ session-log entries within timeframe)
- (b) **Skill gap:** predictable trigger event with no skill invocation (e.g., earnings day with no /brief; new packet with no /career evaluate; bloodwork update with no /health)

**IDENTIFYING markers:**
- Sessions-log entries within timeframe; extract Skills invoked field; compute co-occurrence matrix
- Calendar of trigger events (earnings dates, market-significant events, scheduled bloodwork) cross-referenced against sessions-log skill invocations

**Confidence calibration:**
- Base: 70%
- -15% if user's session-pattern is genuinely irregular (low session-cadence makes pattern detection unreliable)
- Cap: 80%

**Example detection:**
- (a) Cluster: 3 of last 5 sessions: /brief at session start -> /challenge mid-session -> /decide near session end. Pattern: "Decision-quality session structure consistent; user has internalized brief-challenge-decide pipeline as standard cadence."
- (b) Gap: SK Hynix Apr 23 earnings (MU peer signal) had no /brief or /invest MU; pattern: "Peer-signal earnings events are predictable triggers /brief should not miss; consider scheduled /brief on tracked-peer-earnings dates."

**vNEXT corpus (2026-06-10; additive):** the latest `wiki/maintenance/telemetry-*.md` report (subagent pair health, orphan rates, failure clusters by (tool_name, error_class), agent-duration outliers) replaces sessions-log mentions as the PRIMARY evidence base for this class -- real invocation/failure data over self-reported usage. When the orchestrator passes an in-session claudewatch summary (MCP reachable; headless runs degrade to the report file), drift/friction/effectiveness metrics extend the same evidence base. Both arrive parent-passed; the telemetry report path is also directly Read-able.

## Class 9 -- Meta-pattern

**REQUIRED:**
- >=3 promoted patterns from classes 1-8 cluster around single super-axis
- Super-axis must be explicitly articulable (career, action-execution, risk-aversion, capacity-management, identity-formation, knowledge-compounding, etc.)

**IDENTIFYING markers:**
- All promoted spark patterns reference common theme in their Insight field
- Patterns span domains but converge on actor-level or system-level observation

**Confidence calibration:**
- Base: 65% (always inferential; cluster can be coincidence)
- Requires explicit super-axis articulation in Insight field
- Cap: 80%
- -10% if super-axis is too abstract (e.g., "self-improvement" = too broad; "the user prefers validation over execution" = specific enough)

**Example detection:**
- 5 promoted patterns:
  1. (Behavioral) the user revises allocations 3-5x before locking in
  2. (Failure-mode) Sleep-deprived sessions produce plan-deviating execution
  3. (Decision-divergence) Investing aggressive-fast-concentrated; career conservative-slow-procrastinated
  4. (Frequency-recency) Career strategy over-discussed under-executed
  5. (Negative-space) A packet score 91, unsubmitted 13+ days
- Super-axis: "Action-execution gap; high-quality preparation followed by execution friction. Friction concentrated at: (a) submission moments requiring external commitment, (b) plan-deviation under cognitive load, (c) revision-loops that delay action."
- Pattern: "Action-execution friction is the meta-pattern; vault produces decision-grade analysis but submission-rate lags analysis-rate by 10x. Methodology gap is at execution layer, not analysis layer."

**vNEXT corpus (2026-06-10; additive):** the Part W honest-gaps register (parent-passed extract; same handling rules as Class 6) is meta-class context -- the architecture-vs-utilization gap it documents is itself a named meta-pattern; do not re-surface it as new, but DO use it to ground meta-patterns about how the vault's self-knowledge evolves.

## Cross-cutting rules

### Continuity audit confidence shifts (per Phase H)

For each promoted spark, check status in continuity audit (Phase D output):
- **PERSISTED** (still observable): +5% confidence
- **EVOLVED** (shifted shape, core insight relevant): unchanged confidence + note evolution in Continuity field
- **INVALIDATED** (counter-evidence): SUPPRESS pattern (do not promote even if Phase E detection fires); log in below_threshold with reason "invalidated by prior spark [[<peer>]]"
- **DORMANT** (insufficient signal in current timeframe): unchanged confidence + skip Continuity field linkback

### Substantive-mention threshold integration (Pattern 19)

Every evidence-count check uses the canonical threshold: >=3 occurrences OR dedicated H2/H3 section in any source file. Sub-3 mention counts go to `patterns_below_threshold` log; transparent suppression rather than silent omission.

### Insight-stream exclusion (novelty filter)

Class 1 (cross-domain emergence) checks `wiki/insight-stream.md` BEFORE promotion. If the cross-domain connection is already named there, suppress; pattern fails REQUIRED criterion. Do not re-surface known patterns.

vNEXT extension (2026-06-10; additive): the novelty check additionally covers `wiki/playbooks/` for ALL classes -- a pattern already distilled into a playbook is not a new spark (score it in the continuity audit instead). The Phase H.5 NOVELTY skeptic re-checks the same three surfaces (insight-stream + playbooks + prior sparks) adversarially.

### Parent-passed corpus extracts (vNEXT 2026-06-10; cross-cutting)

The orchestrator resolves the expanded corpora MAIN-LOOP and passes extracts (Tier-A: spark-sweep args; Tier-B: inline prompt context). Scouts remain Read/Grep/Glob-only, never call MCP tools, and NEVER read the master-context doc directly. R1 TEMPORAL FENCE: on retrospective runs (window_end < run date) extracts are as-of filtered to artifacts dated <= window_end and every evidence anchor must cite artifacts dated <= window_end; spark-sweep.js drops unmarked retrospective extracts fail-closed. Full resolver contract: `.claude/skills/spark/ref-dw-topology.md` sec 8.

### Deprecation-aware processing (Class 6 specifically; cross-cutting consideration)

Maintain DEPRECATION-AWARE EXCLUDE-LIST (Class 6 spec above). When Phase C builds context inventory, also build `EXPECTED_ARCHIVED` set from `.claude/skills/_archive/` folder names + decision-log deprecation entries. Class 6 detection MUST check this set; expected-archived items never trigger negative-space pattern.

### Confidence cap hierarchy (per-class)

| Class | Floor | Ceiling | Cap rule notes |
|---|---|---|---|
| 1 cross-domain | 50 | 90 | +10% per additional domain |
| 2 behavioral | 60 | 90 | observer-effect cap |
| 3 thesis-evolution | 50 | 95 | post-/challenge can lift to 95 |
| 4 failure-mode | 60 | 90 | shared-upstream required for floor |
| 5 decision-divergence | 40 | 80 | speculative class |
| 6 negative-space | 50 | 85 | exclude-list filter |
| 7 frequency-recency | 50 | 85 (accel) / 75 (stale) | accelerating more reliable |
| 8 tool-skill | 55 | 80 | irregular-cadence dilution |
| 9 meta | 50 | 80 | always inferential |

Aggregate report-level confidence = mean(promoted-spark-confidences) capped by `confidence_cap_rule` evidence-grade rule (see SKILL.md Phase H + meta.json `confidence_cap_rule_applied` field).

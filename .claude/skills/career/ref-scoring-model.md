---
categories: [sources]
type: reference
target_path: .claude/skills/career/ref-scoring-model.md
tags: [topic/career-pipeline, topic/scoring-model, topic/evaluation]
aliases: ["scoring model", "career scoring rubric", "8-dimension scoring"]
related:
  - "[[ref-ai-trainer-market]]"
  - "[[ref-resume-tailoring]]"
  - "[[ref-packet-spec]]"
  - "[[ref-interview-tradecraft]]"
  - "[[ref-remote-data-careers]]"
  - "[[ref-company-health]]"
  - "[[career-moc]]"
  - "[[tracker]]"
  - "[[ref-application-mechanics]]"
status: active
created: 2026-04-18
updated: 2026-04-23
---

# Career Scoring Model v2.1

Reference content for `/career` v2 scoring (Phase F evaluate + calibration feedback loop consumed by Phase J retro). SKILL.md imperatively Reads this file before producing any evaluation score. Updated 2026-04-23 for /career v1 -> v2 SOTA upgrade: calibration feedback fields added (section at end).

---

## Scoring Model v2 (8 dimensions + company health multiplier)

### Raw Score (100 points)

| Dimension | Max | Scoring Guide |
|-----------|-----|---------------|
| **Compensation / upside** | 25 | 23-25: $100+/hr expert tier (Mercor expert, DataAnnotation specialist, Surge AI expert) OR $80K+ W2. 18-22: $40-99/hr OR $60-80K. 13-17: $25-40/hr. 8-12: $20-25/hr. 0-7: below current pay or undisclosed. **Geographic-pay-adjustment penalty:** -3 to band when platform applies country-based rate adjustment (Mindrift global $15-100, etc.); use expected-realized rate, not advertised ceiling |
| **Remote certainty** | 20 | 20: fully remote, explicitly stated. 15-19: remote-first with rare travel. 10-14: hybrid. 0-9: on-site or unclear |
| **Skills match** | 15 | Extract 15-20 keywords from JD requirements (per ref-resume-tailoring.md deterministic extraction). Score = (matched / total) x 15, using skills-inventory.md + resume.md for matching |
| **Fit to background** | 15 | 13-15: direct experience match. 10-12: transferable with reframing. 7-9: adjacent. 0-6: weak |
| **Degree barrier** | 10 | 10: no degree required or explicitly waived. 7-9: "preferred" but equivalent experience accepted. 4-6: "required" with backdoor. 0-3: hard requirement, no exceptions |
| **Interview likelihood** | 10 | 9-10: assessment-based (platform decides quickly). 7-8: posted <7 days, company actively hiring. 4-6: posted 7-21 days. 0-3: posted >21 days or known slow process |
| **Speed-to-apply** | 5 | 5: one-click or simple form. 3-4: moderate form. 1-2: complex multi-step. 0: requires prerequisites the user lacks |
| **Career trajectory** | 5 | 5: brand + skill compound (Scale AI, Anthropic, OpenAI). 3-4: skill growth. 1-2: lateral. 0: dead end |

### Company Health Multiplier (0.7x - 1.0x)

Applied AFTER the 100-point raw score. Search for company health signals (1 web search budget):

| Signal | Multiplier |
|--------|-----------|
| Recent layoffs or hiring freeze | 0.7x |
| Declining Glassdoor (<3.5 or dropping >0.3 in 12 months) | 0.8x |
| Early-stage startup, no recent funding | 0.85x |
| Stable / growing, good reviews | 1.0x |
| Strong growth + above-average reviews | 1.0x (no bonus, just no penalty) |

**Final score = Raw x Company Health Multiplier**

### Decision Thresholds

- **ADVANCE:** 70+  (generate full 7-file packet per ref-packet-spec.md)
- **HOLD:** 60-69  (log, no packet, re-evaluate if information improves)
- **SKIP:** <60  (log reason, move on)

If no role clears ADVANCE, stop after ranked output. Do NOT force packets.

### Red / Green Flag Detection (non-scored; surfaced in evaluation.md)

**Red flags** -- include in evaluation; do NOT auto-penalize (preserve scoring determinism):

- Reposted >3 months (turnover signal)
- "Rockstar" / "ninja" / "wear many hats" (scope creep)
- 15+ responsibilities listed (role ambiguity)
- No salary range (opacity)
- "Fast-paced" + "self-starter" + "minimal supervision" combo (understaffed)
- **5-day RTO mandate** OR "office required" with no remote exception language (post-2026 RTO-cycle red flag for remote-required constraint)
- **Hard-filter experience requirement** that pre-screens before assessment (e.g., Outlier "3+ years professional experience"); flag `hard_filter_untested: true` and apply 5-10pt penalty until empirically tested

**Green flags** -- include in evaluation:

- Salary transparency
- 5-8 clear responsibilities
- Specific tech stack mentioned
- Active engineering blog
- "No degree required" explicit
- Assessment-based entry (platform decides quickly)
- **"Fully remote, no RTO"** OR "remote-first" explicit (countervails 2026 RTO-mandate cycle)
- **Project Osanwe-friendly stack signal** (JD names Claude / Anthropic SDK / MCP / Agent SDK): boost CLAUDE_SDK_CONTRACTOR or PROMPT_ENGINEER fit-to-background +2

### Market Context Adjustment

When /career scan or pipeline mode reads most recent /brief briefing within 24h, apply scoring adjustments:

| Market signal (from /brief) | Adjustment |
|-----------------------------|------------|
| Tech layoffs spiking (>50K in 30 days) | speed-to-apply -2, fit-to-background +2 |
| AI hiring accelerating | AI_TRAINER + PROMPT_ENGINEER archetype scores +3 |
| Recession signals | INSURANCE_OPS + OPERATIONS archetype scores +3 |
| Normal market | no adjustment |

Document adjustment applied in scan.md or evaluation.md header. Market context expires at 24h; beyond that, no adjustment.

---

## Assessment-Gate vs Hard-Filter Dual Model (NEW in v2.2)

Roles fail filter at TWO distinct points: (1) form-submission filter (hard gate; rejects before assessment is offered); (2) assessment-offer gate (soft gate; assessable after form-submission passes). The 8-dim raw score must distinguish these because they have different recovery options.

**Hard gate signals** (auto-flag `hard_filter_untested: true` AND apply 5-10pt penalty until empirically tested):
- "X+ years professional experience" without "or equivalent" exception (Outlier "3+ years" pattern)
- "Bachelor's degree required" without "or equivalent experience" clause
- Citizenship / clearance / state-residence requirements the user doesn't meet
- Hard skill prerequisites with no project-evidence override (e.g., "must have shipped React Native production app")

**Soft gate signals** (assessment-based platforms; Phase G generates assessment-only path, not 7-file packet):
- Platform marks itself "assessment-based entry" (DataAnnotation, Mercor expert tier, Outlier track-test entry)
- JD says "complete assessment to apply" with no resume-screening pre-requisite
- Platform homepage explicitly disclaims experience requirements ("no degree, no minimum hours" -- Mindrift pattern)
- Resume is "auxiliary" or "for reference" not "for screening" (DataAnnotation explicit pattern)

**Scoring rules:**
- Pure soft-gate platform -> interview_likelihood 9-10; degree_barrier 10; skip 7-file packet generation per Phase G assessment-exemption
- Pure hard-gate role -> apply 5-10pt penalty across degree_barrier + fit_to_background; flag `hard_filter_untested` until tested
- Hybrid (DataAnnotation requires assessment but also asks for resume) -> score on hard-gate side; do NOT skip packet but slim to assessment-aware single-file submission

## Speed-to-Engagement Outcome Metric (NEW in v2.2)

Per audit 2026-04-29: high-formality packets (Render 95, DataAnnotation 91) sat 14+ days unsubmitted while low-friction LinkedIn Easy Apply submissions got VIEWED in 13h. Submission velocity is a leading indicator of pipeline health that the v2.1 rubric did not capture.

**New outcome field added to packet-meta.json (alongside `outcome.responded_date`):**

```json
{
  "outcome": {
    "speed_to_engagement_days": null,
    "engagement_first_signal": null
  }
}
```

Where `engagement_first_signal` is one of: VIEWED | RESPONDED | INTERVIEW | REJECTED | NULL_AT_21D.

**Tracker state SUBMITTED -> any-engagement-signal**: populate `speed_to_engagement_days = days from submitted_date to first non-null engagement signal`; populate `engagement_first_signal` accordingly.

Retro mode (Phase J) computes per-archetype median speed_to_engagement_days. Drift signal: if a high-friction archetype (TECH_WRITER, PROMPT_ENGINEER) consistently shows median > 14d while low-friction archetype (AI_TRAINER assessment-only) shows median < 3d, the friction premium is not earning its return -- consider de-prioritizing high-friction roles unless score >=90.

## Blocker-Aware READY_TO_SUBMIT State (NEW in v2.2)

Audit found Render packet (score 95, $150-210K) sat in READY_TO_SUBMIT for 14+ days with 5 unresolved blockers (writing sample, GitHub repo, LinkedIn profile, form-answers, banned-string grep). The v2.1 canonical-state vocabulary did not distinguish "ready and unblocked" from "ready but blocker-stuck" -- so submission friction was invisible in retro calibration.

**New state inserted between READY_TO_SUBMIT and SUBMIT_NOW:**

`READY_TO_SUBMIT_BLOCKED` -- packet exists; tracker carries `blockers: [<list>]` array enumerating pre-submission dependencies (writing-sample / github-repo / linkedin-profile / form-answers / banned-string-grep / etc.)

**Phase I (tracker mode) daily-recall mechanism:**
- IF `state == READY_TO_SUBMIT_BLOCKED` AND `age_in_state >= 3 days` -> emit DAILY_RECALL with blocker enumeration
- IF `age_in_state >= 7 days` -> escalate to WARN status; suggest debug session OR scope reduction (drop blocker if non-essential)
- IF `age_in_state >= 14 days` -> propose state transition to ABANDONED with explicit reason capture

**Retro Phase J calibration metric:** `READY_TO_SUBMIT -> SUBMITTED` median elapsed days per archetype. Floor signal: any archetype with median elapsed >7d represents friction premium not paying off.

---

## Calibration Feedback Fields (NEW in v2.1)

Used by `/career` Phase J retro mode for rolling 30-day scoring-model drift detection. Each packet-meta.json sidecar carries the fields below; retro aggregates them per archetype.

### Per-packet calibration fields (written to packet-meta.json at generation)

```json
{
  "calibration": {
    "archetype": "AI_TRAINER",
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
    "archetype_keyword_hit_margin": {
      "top": 5,
      "second": 2,
      "margin_ratio": 2.5
    },
    "market_adjustment_applied": null,
    "company_health_evidence": "Glassdoor 4.1, 247 reviews; recent funding Jun 2025; no layoff signals"
  }
}
```

### Per-packet outcome fields (populated over time by tracker state transitions)

These fields start null and get populated as the role progresses through the pipeline:

```json
{
  "outcome": {
    "submitted_date": null,
    "time_to_submit_days": null,
    "responded_date": null,
    "time_to_response_days": null,
    "response_type": null,
    "interview_date": null,
    "offer_date": null,
    "offer_details": null,
    "final_state": null,
    "notes": null
  }
}
```

**Tracker state transition -> outcome field update rules:**
- SUBMIT_NOW -> SUBMITTED: populate `submitted_date`, compute `time_to_submit_days`
- SUBMITTED -> RESPONDED | WITHDRAWN (auto 21d): populate `responded_date`, `time_to_response_days`, `response_type` (auto-rejection | recruiter-reach-out | interview-invite | offer-direct)
- RESPONDED -> INTERVIEW: populate `interview_date`
- INTERVIEW -> OFFER: populate `offer_date`, `offer_details`
- Any -> terminal state: populate `final_state` (ACCEPTED | REJECTED | WITHDRAWN | CLOSED) and `notes`

### Aggregate calibration per archetype (computed by /career retro)

For each archetype (AI_TRAINER, PROMPT_ENGINEER, DATA_ANALYST, TECH_SUPPORT, OPERATIONS, INSURANCE_OPS), over rolling 30-day window:

| Metric | Computation |
|--------|-------------|
| ADVANCE count | count packets with decision=ADVANCE |
| SUBMITTED count | count packets with outcome.submitted_date not null |
| ADVANCE -> SUBMITTED rate | SUBMITTED / ADVANCE (user behavior signal) |
| Median time to submit | median(time_to_submit_days) across SUBMITTED |
| RESPONDED count | count packets with outcome.responded_date not null |
| SUBMITTED -> RESPONDED rate | RESPONDED / SUBMITTED |
| Median time to response | median(time_to_response_days) |
| INTERVIEW count | count packets with outcome.interview_date not null |
| RESPONDED -> INTERVIEW rate | INTERVIEW / RESPONDED |
| OFFER count | count packets with outcome.offer_date not null |
| INTERVIEW -> OFFER rate | OFFER / INTERVIEW |
| Archetype score accuracy | Pearson correlation (final_score, binary outcome responded) across N>=5 SUBMITTED |

### Scoring drift signals

Retro emits WARN when:

- ADVANCE -> SUBMITTED rate <30% on N>=5 ADVANCE (pattern: generating packets the user doesn't submit)
- SUBMITTED -> RESPONDED rate <10% on N>=10 SUBMITTED per archetype (pattern: scoring too high, or pipeline reach misaligned with market)
- Archetype score accuracy correlation <0.2 on N>=15 SUBMITTED (pattern: score does not predict outcome; scoring-model v3 redesign candidate)

WARN signals are surfaced as proposed follow-ups in retro output. Review and decide whether to adjust dimension weights, thresholds, archetype detection rules, or ignore as noise.

**Scoring model version bump protocol:**

- Minor (v2.1 -> v2.2): adjust dimension max points or scoring band thresholds; preserve archetype detection + 8-dim structure
- Major (v2.x -> v3): restructure dimensions, change archetype set, or change decision thresholds; archive v2.x in `.claude/skills/_archive/career-ref-scoring-model-v2.x/` and update ref-scoring-model.md in place

Version bumps require explicit user approval after retro WARN. Model does NOT self-adjust.

---

## Version history

- v2 (2026-04-18 Group 23b): Extracted from SKILL.md body; 8-dimension rubric + company health multiplier + decision thresholds + red/green flag detection
- v2.1 (2026-04-23): Added calibration feedback fields for /career v2 Phase J retro consumption; ASCII pass; Project Palantir -> Project Osanwe reframing in references
- v2.2 (2026-04-29): SOTA refresh post audit Apr 29. Compensation_upside band redistribution to differentiate Mercor expert tier ($100+/hr) from AI-trainer baseline ($40+/hr); geographic-pay-adjustment penalty (-3 band when global-pay platform). Assessment-Gate vs Hard-Filter Dual Model section added (codifies hard-filter risk flag with 5-10pt penalty until empirically tested + assessment-exemption pathway). Speed-to-engagement outcome metric added to packet-meta.json (audit found high-friction packets with 14+ day blocker stalls vs LinkedIn Easy Apply VIEWED in 13h). READY_TO_SUBMIT_BLOCKED state added to canonical state vocabulary; Phase I daily-recall mechanism for blockers age >3d/>7d/>14d. Red flag "5-day RTO mandate" + green flag "Fully remote, no RTO" + "Project Osanwe-friendly stack" detection added.

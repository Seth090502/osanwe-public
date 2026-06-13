---
categories: [sources]
type: reference
target_path: .claude/skills/career/ref-packet-spec.md
tags: [topic/career-pipeline, topic/packet-spec, topic/applications]
aliases: ["7-file packet spec", "packet contract", "application packet structure"]
related:
  - "[[ref-ai-trainer-market]]"
  - "[[ref-scoring-model]]"
  - "[[ref-resume-tailoring]]"
  - "[[ref-interview-tradecraft]]"
  - "[[career-moc]]"
  - "[[tracker]]"
  - "[[ref-application-mechanics]]"
status: active
created: 2026-04-23
updated: 2026-04-23
---

# Career 7-File Packet Spec (v1)

Reference content for `/career` v2 Phase M packet composition. SKILL.md imperatively Reads this file before emitting any packet files. Extracted 2026-04-23 from SKILL.md body to keep SKILL.md <=650 lines per kepano progressive-disclosure.

---

## Folder convention

Path: `Efforts/career-search/applications/<slug>-<YYYY-MM-DD>[-HHMM]/`

- `<slug>` = company name lowercased, spaces to hyphens, non-alphanumerics stripped (e.g., "DataAnnotation.tech" -> `dataannotation`, "Outlier AI (Scale AI)" -> `outlier-ai`)
- `<YYYY-MM-DD>` = date packet generated (ISO)
- `-HHMM` suffix added only when same-day collision detected; preserves archival rule per /invest precedent
- `--replace` flag required for explicit overwrite of existing packet (destructive; documented in submission-notes.md)

## File set

ADVANCE >=80: 7 markdown files + packet-meta.json sidecar
ADVANCE 70-79: 6 markdown files (skip `form-answers.md`; generate on demand during actual submission) + packet-meta.json

---

## File 1: job-source.md

**Purpose:** Source artifact; exact JD capture at time of evaluation so later changes to posting don't corrupt analysis.

**Frontmatter:**
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

**Body contract:**
```markdown
# <Role title> -- <Company>

**Source URL:** <exact url; preserve query params>
**Date found:** YYYY-MM-DD
**Posted date:** YYYY-MM-DD (from JD; if absent, mark "posted date not visible")
**Pay:** <disclosed range or "pay undisclosed">
**Location:** <exact from JD>
**Remote status:** Fully remote | Hybrid | On-site | Unclear

## Raw JD (verbatim)

<paste complete JD text; do NOT paraphrase>

## Missing data

- <enumerate anything required for scoring that was not in JD: e.g., "specific tech stack not listed", "engineering blog not found", "Glassdoor rating not accessible">
```

**Critical rule:** JD text is verbatim. Never paraphrase. Later sections reference this as canonical source. Preserve even typos and formatting.

---

## File 2: evaluation.md

**Purpose:** 8-dimension score + archetype + company health + decision + contractor-rule state + qualification analysis.

**Frontmatter:**
```yaml
---
categories: [efforts]
type: output
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
tags: [company/<slug>, topic/<archetype-topic>]
related: [[job-source]], [[resume]], [[tracker]], [[<Company>]], [[career-moc]]
archetype: AI_TRAINER | PROMPT_ENGINEER | DATA_ANALYST | TECH_SUPPORT | OPERATIONS | INSURANCE_OPS
archetype_confidence: high | medium | low
raw_score: <int 0-100>
company_health_multiplier: <float 0.7-1.0>
final_score: <int 0-100>
decision: ADVANCE | HOLD | SKIP
contractor_rule_advances_a: <bool>
contractor_rule_advances_b: <bool>
---
```

**Body contract:**
```markdown
# Evaluation -- <Company> -- <Role title>

## Overall Score: X/100 (Raw: X x Health: X)

| Dimension | Score | Max | Notes |
|-----------|-------|-----|-------|
| Compensation / upside | X/25 | 25 | <evidence> |
| Remote certainty | X/20 | 20 | <evidence> |
| Skills match | X/15 | 15 | <matched / total keywords> |
| Fit to background | X/15 | 15 | <evidence> |
| Degree barrier | X/10 | 10 | <evidence> |
| Interview likelihood | X/10 | 10 | <evidence> |
| Speed-to-apply | X/5 | 5 | <evidence> |
| Career trajectory | X/5 | 5 | <evidence> |

**Archetype:** <X>  (keyword hits: ai_trainer=N, prompt_engineer=N, ...)
**Company health:** <multiplier> (<evidence from 1 web search; signal list>)
**Contractor rule state at evaluation:**
- Advances Condition A (contractor income >= $[CONTRACTOR_MONTHLY_FLOOR]/mo x 2): <YES | NO | N/A>
- Advances Condition B (W2 offer >= $[W2_THRESHOLD]): <YES | NO | N/A>
- Current rule status: <ACTIVE | CONDITION_A_MET | CONDITION_B_MET | FORCE_QUIT>

**Red flags:** <list or "none detected">
**Green flags:** <list or "none detected">

## Why You're Qualified

- <specific evidence from private/resume.md + skills-inventory.md tied to JD requirements>
- <cite exact JD requirement -> matching vault evidence, minimum 3 mappings>

## Why You May Not Be Qualified (honest gap analysis)

- <gaps per skills-inventory.md gap-analysis>
- <mitigations per ref-skills-translation.md>

## Decision

<ADVANCE | HOLD | SKIP> at final score X.

<one-sentence rationale>

Next action: <generate packet | log and monitor | skip and document reason>
```

---

## File 3: resume.md (tailored)

**Purpose:** ATS-optimized, JD-keyword-aligned, archetype-reframed resume. Diff-auditable against `private/resume.md` baseline.

**Frontmatter:**
```yaml
---
categories: [efforts]
type: output
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
tags: [company/<slug>, topic/resume, topic/<archetype-topic>]
related: [[job-source]], [[evaluation]], [[<Company>]]
tailored_from: private/resume.md
archetype: <archetype>
---
```

**Body contract:**

1. **Resume-diff-from-baseline block (REQUIRED; top of body):**

```markdown
<!-- RESUME-DIFF-FROM-BASELINE -->
Tailoring changes vs private/resume.md baseline:

- REFRAMED bullet 2 of Professional Experience: "insurance application verification" -> "data quality annotation with cross-source validation"  [evidence: JD requires "data labeling + quality assurance"]
- ADDED bullet under Technical: "LLM infrastructure deployment (Ollama, SearXNG, Chart.js visualization)"  [evidence: JD requires "LLM experience"]
- PRESERVED byte-exact: Education section, Certifications section, Contact block
- REMOVED: none  (baseline has no content to remove for this archetype)

Fabrication check: zero. All reframings map to specific private/resume.md lines or skills-inventory.md entries.
<!-- /RESUME-DIFF-FROM-BASELINE -->
```

2. **ATS-optimized resume body** (single-column; standard section headers; >=75% JD keyword match; quantified achievements per PAR).

**Critical rules:**
- Never fabricate beyond `private/resume.md` baseline
- Every reframed bullet maps to a specific baseline line
- Every "required" JD skill appears in resume (header, bullet, or Skills section)
- Project Osanwe reframed per archetype (see ref-resume-tailoring.md archetype table)
- Single column layout (ATS-safe)
- Standard headers: Professional Experience / Technical Skills / Projects / Education / Certifications
- No images, no tables, no text boxes (ATS-incompatible)

---

## File 4: cover-letter.md

**Purpose:** Concise, role-specific, archetype-aware outreach.

**Frontmatter:**
```yaml
---
categories: [efforts]
type: output
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
tags: [company/<slug>, topic/cover-letter]
related: [[job-source]], [[resume]], [[<Company>]]
archetype: <archetype>
---
```

**Body contract:**
- Length: <=250 words
- Opens with specific hook tied to role or company (no "Dear Hiring Manager" if name findable)
- Body: 2-3 specific Project Osanwe proof points aligned to archetype
- Closes with specific ask + next-step expectation
- No generic AI fluff; no "I'm passionate about" unless followed by specific evidence
- Archetype-tuned tone: AI_TRAINER = methodical + technical; OPERATIONS = process + accuracy; PROMPT_ENGINEER = architectural + system-level

---

## File 5: submission-notes.md

**Purpose:** Field-by-field submission runbook + reality checks.

**Frontmatter:**
```yaml
---
categories: [efforts]
type: output
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
tags: [company/<slug>, topic/submission]
related: [[job-source]], [[evaluation]], [[tracker]]
time_estimate_minutes: <int>
follow_up_1_date: YYYY-MM-DD
follow_up_2_date: YYYY-MM-DD
withdraw_after_date: YYYY-MM-DD
---
```

**Body contract:**
```markdown
# Submission notes -- <Company>

## Submission URL

<exact url to application form>

## Time estimate

~X minutes  (based on observed form complexity)

## Field-by-field instructions

1. First name / Last name: <from private/profile.md>
2. Email: <from private/profile.md>
3. Phone: <from private/profile.md>
4. LinkedIn: <from Efforts/career-search/linkedin-profile-draft-*.md or private/profile.md>
5. Portfolio / GitHub: <per target-portfolio-url in private/profile.md>
6. Resume upload: <path to tailored resume PDF; generate via external pandoc/typst from resume.md>
7. Cover letter: paste from cover-letter.md OR upload as PDF
8. <JD-specific fields with pre-drafted answers from form-answers.md if present>

## Follow-up schedule

- Day 0 (submit): status -> SUBMITTED in tracker
- Day 6: FOLLOW_UP_1 -- reference application, add one new proof point
- Day 13: FOLLOW_UP_2 -- shorter, offer additional materials
- Day 21: WITHDRAWN (no response baseline)

## Submission Reality Check

- Time to submit: ~X minutes
- Worst case: No response. You spent X minutes. Nothing changes.
- Best case: Interview within 1-2 weeks.
- 90% rejection is normal for ALL candidates. This is a numbers game.
- Your edge: production AI system + years of remote ops. Most applicants have ChatGPT + a LinkedIn profile.

## Contractor Rule Reality Check

- This role advances Condition A (contractor >= $[CONTRACTOR_MONTHLY_FLOOR]/mo x 2): <YES | NO>
- This role advances Condition B (W2 >=$[W2_THRESHOLD]): <YES | NO>
- If NO to both: override rationale required; document here.
- Rule source: [[contractor-transition-rule]]
```

---

## File 6: company-intel.md

**Purpose:** Context for cover letter + interview prep; informs `wiki/entities/companies/<Company>.md` update.

**Frontmatter:**
```yaml
---
categories: [efforts]
type: output
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
tags: [company/<slug>, topic/company-research]
related: [[job-source]], [[evaluation]], [[<Company>]]
---
```

**Body contract:**
```markdown
# Company intel -- <Company>

## Overview

<2-3 sentences: what they do, scale, revenue model>

## Funding / Financial signals

- Latest round: <round, amount, investors, date>  OR "bootstrapped / no public funding data"
- Growth signals: <headcount delta, revenue mentions, product launches>
- Layoff signals: <recent layoffs, hiring freezes, runway concerns>

## Glassdoor / employee reviews

- Rating: X/5  (N reviews)
- Trend: rising | stable | falling over past 12 months
- Common themes: <1-3 sentences>

## Recent news (last 90 days)

- YYYY-MM-DD: <headline + 1-sentence summary>

## AI / tech strategy

<how does this company use or build AI? Relevant to cover letter framing.>

## Key contacts

- Hiring manager: <name + title if findable>
- Recruiter: <name if findable>
- Team lead: <name if findable>

## Competitive landscape

<3-5 competitors + positioning>
```

---

## File 7: form-answers.md (only if ADVANCE >=80)

**Purpose:** Pre-drafted answers to common portal questions so submission is <15 min.

**Frontmatter:**
```yaml
---
categories: [efforts]
type: output
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
tags: [company/<slug>, topic/form-answers]
related: [[submission-notes]], [[<Company>]]
---
```

**Body contract:**

Common Ashby / Greenhouse / Lever / Workday portal questions with pre-drafted answers:

```markdown
# Form answers -- <Company>

## Why are you interested in this role?

<3-4 sentences; role-specific; tied to Project Osanwe or direct experience; no generic>

## Why this company?

<2-3 sentences from company-intel.md; cite specific artifact or news>

## What makes you qualified?

<3 bullet points from evaluation.md Why Qualified section>

## Describe a challenging project you completed.

<STAR framework; Project Osanwe or prior-role-specific; tied to archetype>

## What is your expected compensation?

<from private/profile.md compensation targets; if disclosed JD range, state "aligned with posted range"; if not, state "open to discussion based on total comp package">

## When can you start?

<2 weeks from offer acceptance if W2; 2-3 days if contractor; document contractor-rule-permitting status>

## Are you authorized to work in the US?

Yes, US citizen; no sponsorship required.

## Do you require visa sponsorship?

No.

## How did you hear about this role?

<specific: "job board search via <portal>" or specific source>

## Additional questions (role-specific from JD)

<draft answers to any JD-specific prompts>
```

---

## File 8: packet-meta.json (machine-readable sidecar; always emitted)

**Schema:** see SKILL.md Phase M section.

**Purpose:** Brier-score-analogous calibration feedback; auditable scoring lineage; packet-level archaeology.

**Generation:** compute during Phase M; write alongside 7 markdown files as atomic batch.

---

## CREATE-or-UPDATE branch for wiki/entities/companies/<Company>.md

Packet generation triggers Phase N entity-note update.

**CREATE branch (Company does not exist at `wiki/entities/companies/`):**

- Grounded in `_templates/entity.md`
- Canonical frontmatter:
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
- Body sections: `## Overview` / `## Culture` / `## Compensation signals` / `## Growth signals` / `## Layoff signals` / `## Recent mentions`
- Initial content populated from `company-intel.md` claims distributed to appropriate sections
- Append `## Recent mentions` entry: `- [YYYY-MM-DD] Evaluated in [[<slug>-evaluation]]; score <N>; decision <D>`

**UPDATE branch (Company exists; claim-to-section mapping per /ingest precedent):**

- Read existing body; compute `entity_before_sha256`
- Map new claims from company-intel.md to sections via marker-signature dedup
- Append `Recent mentions` entry unconditionally (evaluation event is additive)
- `updated:` bump to today
- Compute `entity_after_sha256`; assert strictly-additive diff

**Symmetric back-link:** add `[[<slug>-evaluation]]` (or `[[career-moc]]` if no evaluation) to entity's `related:` field if not present.

---

## Atomicity + F.halt

Packet generation is an atomic 8-file batch (7 markdown + 1 json). Partial packets are defects.

**F.halt pattern per V16 Pattern 13:**
- Any file write fails mid-batch -> IMMEDIATE HALT
- F11 stays on
- Report: which files succeeded (in WT but unstaged) + which failed + which not attempted
- The user decides: `git checkout -- <paths>` rollback OR fix + re-invoke (idempotency via same-day -HHMM collision handling)

**Scope of atomicity:** within a single packet. Pipeline mode generating 3 packets = 3 separate atomic batches. One packet failing does NOT rollback already-completed packets; surfaces partial-pipeline state per Pattern 13.

---

## ASCII + frontmatter discipline

- All new content ASCII-only (Pattern 22 replacement table in V16 sec 3.4)
- Canonical frontmatter per file type above; ruamel-parseable
- Tag guardrail: `topic/*`, `company/*`, `thesis/*` namespaces only
- Body-preservation sha256 on any UPDATED file (tracker, entity notes, daily note, opportunities)

---

## Version history

- v1 (2026-04-23): Extracted from /career SKILL.md v2 body; codifies 7-file packet + packet-meta.json sidecar + CREATE-or-UPDATE entity branch + F.halt atomicity.

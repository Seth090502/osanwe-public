---
categories: [sources]
type: reference
target_path: .claude/skills/career/ref-resume-tailoring.md
tags: [topic/career-pipeline, topic/resume, topic/ats]
aliases: ["resume tailoring protocol", "ATS keyword extraction", "resume diff protocol"]
related:
  - "[[ref-ai-trainer-market]]"
  - "[[ref-scoring-model]]"
  - "[[ref-packet-spec]]"
  - "[[ref-skills-translation]]"
  - "[[skills-inventory]]"
  - "[[career-moc]]"
  - "[[ref-interview-tradecraft]]"
  - "[[ref-application-mechanics]]"
status: active
created: 2026-04-18
updated: 2026-04-23
---

# Career Resume Tailoring Protocol v2

Reference content for `/career` v2 Phase F / G / H resume tailoring. SKILL.md imperatively Reads this file before emitting any tailored resume output. Updated 2026-04-23 for /career v1 -> v2 SOTA upgrade: adds resume-diff-from-baseline block spec + deterministic keyword extraction algorithm + Project Osanwe (formerly Palantir) archetype reframings.

---

## Baseline + fabrication rule

Baseline: `<VAULT_ROOT>/private/resume.md`

**Fabrication rule:** Zero. Every reframed bullet must map to a specific line in `private/resume.md` OR an entry in `Atlas/concepts/career/skills-inventory.md`. If no mapping exists, the bullet is not written. This is non-negotiable.

**Resume-diff-from-baseline block:** EVERY tailored resume emitted by `/career` MUST include an HTML-comment-fenced diff block at the top of body (inside frontmatter or immediately after), enumerating:

- REFRAMED bullets: `REFRAMED bullet <N> of <section>: "<original>" -> "<reframed>"  [evidence: <JD requirement>]`
- ADDED bullets: `ADDED bullet under <section>: "<new>"  [evidence: <JD requirement> + <skills-inventory entry>]`
- PRESERVED sections: `PRESERVED byte-exact: <section list>`
- REMOVED: typically none (baseline has minimum content)

Ends with: `Fabrication check: zero. All reframings map to specific private/resume.md lines or skills-inventory.md entries.`

The diff block is auditable: the user can diff-check the packet resume against baseline at any time. Any claim in the resume that is NOT traceable to baseline or skills-inventory is a defect.

---

## 7-step tailoring protocol

For Phase F evaluate (if ADVANCE), Phase G pipeline (packet generation), Phase H apply (submission prep if --refresh resume):

### Step 1: Deterministic keyword extraction

Apply this algorithm to JD text; report the extracted keyword set in packet-meta.json.

**Algorithm:**

1. Tokenize JD into sentences; remove boilerplate (benefits, EEOC, company description)
2. Extract candidate keywords via these rules (ordered; first-match-wins):
   - Rule A: Any noun phrase preceded by "experience with", "knowledge of", "proficiency in", "familiarity with"
   - Rule B: Any noun phrase in a bulleted requirements list (look for "Requirements:", "Qualifications:", "Must have:", "Required:" section headers + subsequent bullets)
   - Rule C: Any proper noun (capitalized multi-word) matching common tech stacks (TypeScript, Python, React, AWS, Docker, Kubernetes, PostgreSQL, Redis, etc.; from a whitelist of common stacks)
   - Rule D: Any single-word verb from an approved verb list (annotate, label, evaluate, analyze, debug, deploy, architect, integrate, optimize, train, fine-tune, prompt, score)
3. Normalize: lowercase, strip punctuation, stem ("-ing" / "-ed" -> base form)
4. Deduplicate
5. Target: 15-20 keywords after deduplication. If >20, rank by frequency in JD; keep top 20. If <15, relax Rule B to include "Preferred:" bullets.

**Report format** (in evaluation.md + packet-meta.json):

```yaml
extracted_keywords:
  - {keyword: "prompt engineering", rule: "A", frequency: 3, matched: true, source: "Project Osanwe + skills-inventory.md"}
  - {keyword: "typescript", rule: "C", frequency: 2, matched: true, source: "Project Osanwe skills"}
  - {keyword: "rlhf", rule: "A", frequency: 1, matched: false, source: null}
  ...
match_ratio: 14/16 = 0.875
```

### Step 2: Keyword mapping

Map each extracted keyword to:
- `private/resume.md` (if direct experience exists)
- `Atlas/concepts/career/skills-inventory.md` (if demonstrated capability exists)
- null (unmatched; cannot add without fabrication)

### Step 3: Bullet rewrite for matched keywords

For matched keywords, rewrite the corresponding bullet to mirror JD language (truthful only). Example:

- Baseline: "Validated insurance applications across multi-platform workflow with near-perfect accuracy"
- JD keyword: "data quality assurance"
- Rewrite: "Performed data quality assurance on insurance applications across multi-platform workflow; achieved near-100% accuracy over 2+ years"

### Step 4: Bullet addition for transferable skills

For unmatched JD keywords where skills-inventory.md has a mapping via transferable experience, add a bullet with JD language. Example:

- JD keyword: "LLM deployment"
- Skills-inventory: "Local AI infrastructure -- deployed Ollama, patched Claude Code CLI, integrated SearXNG"
- New bullet: "Deployed and operated local LLM infrastructure: Ollama model serving, GGUF optimization, prompt template integration" [added under Technical Skills > Project Osanwe]

### Step 5: Skills section verification

Every "required" JD skill (Rule B bullets) must appear in the resume somewhere: header, body bullet, or skills section. If not, add to Skills section (if skills-inventory supports it) OR flag the packet with `skills_gap: [<list>]` in evaluation.md frontmatter.

### Step 6: Archetype-specific Project Osanwe reframing

Project Osanwe (the user's core portfolio project; formerly called "Palantir" in v1 references) is the **primary credential** as of resume v3 (2026-04-29 headline shift to "AI systems builder & technical writer"). Reframe it per detected archetype using post-2026-04-29 baseline metrics:

**Canonical metrics (from the user's resume baseline):** 17 production skills (10 at SOTA final state with 16-phase A-P discipline; 22-item Pre-Output gate per skill); 379-file Obsidian vault; 23 reference documents totaling 95,000+ words; 5,435-word PROJECT-OSANWE-PACKET whitepaper; 1,054 lines production Python tooling + 4,000+ lines vault-rebuild migration scripts; 10 session-orchestration hooks (Bash + PowerShell + Python); 22-25 SOTA architectural patterns + 18 standing rules; cc-coach v1.1 always-on advisory infrastructure (13 tier-calibrated patterns, 0.15% context budget, 30-day false-positive A/B calibration); Plan-agent autonomous execution validated at scale (60->100 vault audit; cc-coach 6-gap closure); multi-tool runtime portability (Claude Code primary + Codex CLI dual-tool migration + local LLM Qwen3.5 27B Q6_K offline mode); self-hosted SearXNG (Docker, 8+ providers).

| Archetype | Project Osanwe framing emphasis |
|-----------|----------------------------------|
| CLAUDE_SDK_CONTRACTOR | **Highest weighting on Claude/Anthropic-specific work.** 17 skills built on Claude Code SDK; MCP integration; Codex CLI dual-tool migration validated via Plan-agent autonomous execution (8-commit reflog-recoverable optionality); 10 session-orchestration hooks (UserPromptSubmit + PostToolUse + PreCompact + Stop + path-guard); 7,852-word Claude Code mastery reference anchoring always-on coaching layer; cc-coach v1.1 13-pattern advisory infra; deep prompt-caching + tool-calling + context management discipline |
| AI_TRAINER | Prompt engineering depth (17 skills, 10 SOTA-final), multi-model evaluation (local LLM vs Claude vs Gemini), quality-graded knowledge base (95K words / 23 ref docs / 5,435-word whitepaper), rubric-based evaluation discipline, RLHF awareness, structured evaluation under sustained workflow pressure |
| PROMPT_ENGINEER | LLM infrastructure stack (Ollama + quantized GGUF + SearXNG Docker + Plan-agent autonomous execution + dual-tool runtime portability), 10 session-orchestration hooks, 22-25 SOTA patterns + 18 standing rules, 1,054 LOC production Python tooling. **Claude-keyword 2.0x weighting:** if JD names Claude/Anthropic SDK/MCP/Agent SDK, lift fit-to-background +2pt and route per CLAUDE_SDK_CONTRACTOR framing |
| DATA_ANALYST | Knowledge base architecture (379-file vault, 23 ref docs / 95K words), 1,054 LOC Python tooling (vault-audit.py 9 classifiers across 379 files; fetch-prices.py yfinance + technical indicators), analytical frameworks (8-dim scoring, evidence A-F grading, 18-item Pre-Output gates, body-preservation sha256 invariants), data pipeline (ingest -> enrich -> entity graph) |
| TECH_SUPPORT | Local service deployment (Docker, SearXNG self-hosted with 8+ providers, Ollama local LLM), debugging workflow (10 session-orchestration hooks, F11 atomic-commit discipline, 30 patches across 1,404 TypeScript files), system documentation (VAULT-HANDOFF-V16+ ~110KB / 1,500 lines), self-hosting + remote async discipline |
| OPERATIONS | Process design (16-phase A-P arc for skill workflows; 22-item Pre-Output HALT gate; mid-batch F.halt failure handling), accuracy metrics (sha256 body-preservation invariants on every multi-file edit; [ACCURACY]% verification accuracy at [EMPLOYER]), systematic workflows (atomic multi-file commits; F14 narrow staging; F17 Co-Authored-By verify) |
| INSURANCE_OPS | Process accuracy parallel ([ACCURACY]% verification accuracy across [N]y at [EMPLOYER]; high application volume), data validation cross-platform ([CARRIER_PLATFORMS] SLA discipline), compliance mindset, structured repro-step documentation |

Exactly ONE reframing lens per packet. Do not blend archetypes in a single resume.

**Tiebreaker for Claude-adjacent roles**: when archetype-detection produces a tie between PROMPT_ENGINEER and CLAUDE_SDK_CONTRACTOR, prefer CLAUDE_SDK_CONTRACTOR (Claude/Anthropic-native signal is the stronger discriminator for the user's resume positioning).

### Step 7: ATS optimization

- **Single column layout.** No tables, no text boxes, no images.
- **Standard headers:** Professional Experience / Technical Skills / Projects / Education / Certifications
- **>=75% JD keyword match** (verified via the extracted keyword set from Step 1)
- **Quantified achievements** per PAR framework (see below)
- **No abbreviations** without expansion on first use (except universal: USA, US, LLC, etc.)
- **Reverse chronological order** for experience
- **Fonts ATS-safe:** Arial, Calibri, Helvetica, Times New Roman (Markdown -> PDF conversion handles this)
- **Standard date format:** MMM YYYY - MMM YYYY (e.g., "Jan 2020 - Present")

### PAR Quantification Framework

For every bullet, apply Process / Action / Result:

- **Process:** what system, workflow, or initiative
- **Action:** what you specifically did
- **Result:** measurable outcome (volume: "X policies/day"; accuracy: "99.X%"; efficiency: "reduced X by Y%"; scope: "across Z systems")

**Example PAR:**

- Bad: "Verified insurance applications"
- Good: "Processed [N]+ records daily across [CARRIER_PLATFORMS] / Excel / CRM stack with [ACCURACY]%+ accuracy over [N]+ years"

Every Professional Experience bullet: P + A + R. Every Project bullet: A + R minimum (P is the project itself).

---

## Archetype tone for cover-letter.md

Cover letter tone is archetype-tuned (see cover-letter.md spec in ref-packet-spec.md):

- **CLAUDE_SDK_CONTRACTOR:** builder-first + Anthropic-native voice; cite specific Claude SDK + MCP + Agent SDK work; reference Project Osanwe as a deployed system, not a portfolio piece; lead with "shipped" not "studied"; technical writing as a deliverable signal (5,435-word whitepaper + 23 ref docs / 95K words)
- **AI_TRAINER:** methodical + technical; cite specific prompt quality patterns + evidence-graded evaluation; rubric-based eval discipline; multi-model comparison signal
- **PROMPT_ENGINEER:** architectural + system-level; cite LLM infrastructure depth + integration patterns; if Claude/Anthropic/MCP keywords detected, hybrid-tone toward CLAUDE_SDK_CONTRACTOR
- **DATA_ANALYST:** analytical + quantitative; cite frameworks + specific outcome metrics
- **TECH_SUPPORT:** practical + debugging-first; cite specific patches + troubleshooting workflow
- **OPERATIONS:** process-first + accuracy-emphasis; cite systematic workflows + accuracy record
- **INSURANCE_OPS:** compliance + accuracy + direct industry experience

---

## Version history

- v1 Group 23b (2026-04-18): Extracted from SKILL.md body; 7-step protocol + archetype reframings (Project Palantir naming) + ATS optimization + PAR framework
- v2 (2026-04-23): Added resume-diff-from-baseline block spec (REQUIRED in every tailored resume); added deterministic keyword extraction algorithm (Rules A-D + normalization); renamed Project Palantir -> Project Osanwe (vault rebrand); expanded archetype-specific framings with v2-era proof points (16-phase A-P arcs, sha256 invariants); added archetype tone guide for cover-letter.md
- v2.1 (2026-04-29): SOTA refresh post resume v3 + audit. Step 6 archetype-reframing table refreshed with 2026-04-29 baseline metrics (17 skills / 10 SOTA-final / 379 files / 1,054 LOC Python / 23 ref docs / 95K words / 5,435-word whitepaper / 10 hooks / 22-25 patterns / cc-coach v1.1 / Plan-agent autonomous / Codex CLI dual-tool / multi-tool runtime / SearXNG self-host); added CLAUDE_SDK_CONTRACTOR archetype row + cover-letter tone with builder-first / Anthropic-native voice; added PROMPT_ENGINEER 2.0x Claude-keyword weighting + tiebreaker rule (CLAUDE_SDK_CONTRACTOR > PROMPT_ENGINEER on tie); Project Osanwe elevated from "core portfolio project" to "primary credential" framing; insurance-to-data secondary, AI-systems-builder primary.

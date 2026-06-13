---
categories: [meta]
type: test-fixture
tags: []
status: active
created: 2026-05-11
updated: 2026-05-11
---

# Test fixture: PII-free content (negative control)

This file contains architectural and skill-related content without any PII. Running `python .audit\check-pii.py .audit\test-fixture-clean.md .audit\denylist-v1.txt` (or v2) MUST return zero hits. Used by Phase 0.6 smoke test for false-positive detection.

## Architecture overview

Project Osanwe runs on a 14-classifier audit system with tier-weighted scoring. GATE findings count five points each, capped at ten total. HARD DRIFT findings count one point each, capped at five. SOFT DRIFT is advisory-only. The honest floor is 95 out of 100.

## Skill design

Each skill has a SKILL.md body that describes its purpose, trigger keywords, and phase decomposition. Skills dispatch subagents via mandatory markers that surface as Agent tool invocations. Pre-emptive skip on judgment is forbidden.

## Subagent dispatch

The dispatch matrix maps each parent skill to its mandatory subagent calls. Phase J-bis institutional positioning fires when an investment-analysis skill or briefing skill reaches that phase per held position.

## Prevention architecture

PreToolUse runs a pre-write validator which simulates the post-edit content via a temporary file, runs vault-audit in scoped mode, and exits with a non-zero code to block before disk mutation on any GATE finding. PostToolUse runs a seven-script chain: wikilink check, frontmatter check, orphan check, hot-md check, seed-commitment, auto-count-sync, and skill-precheck.

## Methodology patterns

The architecture has accumulated multiple named methodology patterns across three architectural missions, each codified at the session-end retrospective and reusable across future sessions.

## Reference docs

Reference docs are read on-demand by skills, not auto-loaded. They cover investing concepts, career frameworks, supplement evidence base, golf biomechanics, and meta-level research methodology.

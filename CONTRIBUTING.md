---
categories: [meta]
type: contributing-guide
status: active
created: 2026-05-11
updated: 2026-05-11
tags: []
---
# Contributing

This repository is a sanitized public mirror of a personal Obsidian + Claude Code vault. It is shipped as a portfolio artifact, not as an open-source project actively seeking contributions.

## Not accepting

- Code contributions (PRs, issues that propose changes)
- Feature requests
- Architectural redesigns

## OK to do

- **Fork** for your own vault. The skill/agent/hook patterns are released under MIT (see `LICENSE`) -- copy what you like, adapt to your own setup.
- **Open an issue** if you spot a factual error in `README.md`, `EXAMPLES.md`, or `docs/case-study-mission-three-extended-hours.md`. Tag it `[error-report]`.
- **Reference + cite** the architecture patterns in your own writing if useful. Attribution welcome but not required.

## What's NOT in this mirror

- Personal portfolio specifics, biometric / health data, real location, current wage, financial accounts
- The operational `Calendar/decisions/` log + populated `Calendar/daily/` notes
- Active `Efforts/career-search/` application content (cover letters, resumes, evaluation notes)
- `CLAUDE.local.md` (per-user constraints layer)
- `HOME.md`, `USER.md` (personal vault index + profile)
- The UAP corpus extractions (only the pipeline scripts + synthesis are shown)

See `THREAT-MODEL.md` for the explicit boundary.

## Why this is shipped publicly

The architecture -- prevention-architecture with 95/100 audit floor, 9 base + X-series audit classifiers, tier-weighted scoring, 22 skills, 20 subagents, 13 hooks across 10 event types, dynamic workflows, autonomous `/goal`-class missions -- is the artifact. The personal layer stays private.

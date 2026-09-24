---
categories: [wiki]
status: active
created: 2026-08-17
updated: 2026-08-17
---

# Frontier protocol -- frontmatter-sweep (FROZEN 2026-08-17)

Arm: Fable-direct, n=1. Hermetic fixture tree -- timing free.

1. Read the three files in `tools/parity-cases/fixtures/editor-tree/` and
   emit `{"proposed_edits": [...]}` -- one proposal per frontmatter-schema
   violation (forbidden domain: field; status outside the canonical enum);
   negatives for clean files. Do NOT touch body text; do NOT read the
   answer key.
2. Save to `.claude/state/parity/frontmatter-sweep/frontier.json`; log run +
   claudewatch cost attribution.

# Changelog

This repository is a sanitized, periodically published copy of a working system. Its history records the
publications, not the day-to-day development of the system itself.

## 1.0.0 -- 2026-09-24

First public release.

**What is here**
- The agent contract (`AGENTS.md`), the skills under `.agents/skills/`, the subagent roles, hooks, tools and
  tests of a Markdown vault for financial analysis operated by AI agents.
- Documents written for readers: `README.md`, `ARCHITECTURE.md`, `SECURITY.md`, and under `docs/` the audit,
  capabilities, threat model, evaluations, orchestration method and formula index.
- Four worked examples under `examples/`, each with a reading guide for its internal labels.
- A runnable demonstration of the order gate (`demo/`) and 49 test suites that run in CI on every push.

**How it was prepared**
- Every file was inventoried and classified; what could be published was sanitized through a repeatable
  build with denylist, path, ownership and logic-equivalence checks; what could not is listed in
  `docs/withheld.md`.
- Defects found along the way are published rather than silently fixed. The order gate's first stair has four
  open defects (`docs/threat-model.md`), and every formula carries a checked verdict
  (`docs/quant-formula-index.md`).

**Known limitations**
- The copy has never been run end to end from a clean clone; see the README's limitations.

## Before 1.0.0

Earlier copies were published privately while the audit that produced this one was in progress. None is
continuous with this repository's history.

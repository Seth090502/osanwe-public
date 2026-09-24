# .agents/migration/research/ -- evidence base for the cross-harness migration

This directory is the durable Phase-0/Phase-1 evidence base for the 2026-08 cross-harness migration (plan: `~\.claude\plans\execute-the-instructions-flawlessly-lazy-quokka.md`; approved 2026-08-10). Every capability claim in docs/compatibility.md must cite a row ID from `harness-matrix.md`, which resolves into the per-worker reports here. `unverified-cells.md` is the register of cells treated as unsupported until empirically resolved.

Contents:
- `harness-matrix.md` -- the 10-row capability matrix index with row IDs + verification methods.
- `unverified-cells.md` -- UNVERIFIED register with degradations + resolution log.
- `phase0-*.md` -- 8 web-verification worker reports (per-cell findings, source URLs, retrieval dates; empirical probes marked).
- `phase1-*.md` -- 6 workspace-audit worker reports (instruction layer + legacy verdicts, skills A/B coupling, hooks + gates extraction, subagent salvage, MCP + index + tests).
- `redteam-plan-v1.md` -- the pre-approval adversarial review (2 fresh-context opus adversaries + inline fable), findings F1-F20 + C1-C5/H1-H9/M1-M7/L1-L3, each with its disposition in plan v2.

Provenance caveat: the scratchpad task-output files were empty at persist time; these reports were re-emitted verbatim from the orchestrating session's context on 2026-08-10 (the delivered notification texts ARE the worker deliverables). Retrieval dates inside each report are the workers' own.

Written by the migration session, 2026-08-10. Read-only reference thereafter; corrections append, never rewrite.

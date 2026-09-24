---
name: synthesis
description: "Two-mode cross-domain synthesis, primarily scheduler-run weekly. spark (was /spark): sweep dailies, ledgers and entities for recurring cross-domain patterns; emit a dated spark note. consolidate (was /consolidate): mine recurring lessons from sessions and telemetry into a durable playbook under wiki/playbooks. Distinct from /ingest (single-document pipelines) and /retro (session close). Say 'run a spark' or 'consolidate lessons'; bare /synthesis defaults to spark."
metadata:
  categories: analysis
  osanwe-risk: "safe"
  osanwe-effort: "high"
  osanwe-arguments: "[--mode spark|consolidate] [window|topic]"
  osanwe-argument-hint: "[--mode spark|consolidate] [--since `<date>`] [--window 14d] [`<topic>`]"
  osanwe-allowed-tools: "Read Write Edit Grep Glob Bash"
  osanwe-categories: "meta"
  osanwe-type: "skill"
  osanwe-status: "active"
  osanwe-created: "2026-08-23"
  osanwe-updated: "2026-08-23"
---

# /synthesis -- cross-domain pattern sweeps + lesson consolidation (spark | consolidate)

Merged 2026-08-23 from the former /spark (now mode `spark`) and /consolidate (now mode
`consolidate`) by OSANWE-V2 ADR-03. Original bodies preserved VERBATIM as
`ref-mode-spark.md` and `ref-mode-consolidate.md`; output contracts unchanged. The
former DW fast-path workflows keep their names (`spark-sweep`, `spark-verify`) as
Tier-A entry points into the same phases.

## Mode routing

| signal | mode |
|---|---|
| "spark", "pattern sweep", "cross-domain scan", bare /synthesis | **spark** |
| "consolidate", "playbook", "mine lessons" | **consolidate** |

- Mode **spark**: load and follow `ref-mode-spark.md` IN FULL (sources windowed per
  its Phase spec; emits `wiki/research/sparks/spark-<date>.md`; hot.md touch is now
  satisfied by regenerating via `python tools/gen-hot.py --apply` instead of hand-edit).
- Mode **consolidate**: load and follow `ref-mode-consolidate.md` IN FULL (mines
  Calendar/ + state telemetry via tools/consolidator.py; writes one playbook;
  hot.md touch likewise replaced by gen-hot regeneration).

## Scheduling intent

Designed primarily for the weekly cadence job (W9 registry: `python` invocation with
`--mode spark` alternating `--mode consolidate`); interactive use identical.

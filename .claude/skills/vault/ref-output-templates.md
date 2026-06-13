---
categories: [sources]
type: reference
created: 2026-04-26
updated: 2026-04-26
status: active
tags:
  - topic/skill-infrastructure
  - topic/vault
aliases:
  - vault output schema
  - vault templates
related:
  - "[[SKILL|/vault SKILL.md]]"
  - "[[ref-audit-classifiers]]"
  - "[[ref-stats-catalog]]"
---

# /vault Output Templates Reference

Canonical schemas for every artifact /vault writes (audit / stats / repair / refresh) plus the canonical daily-note 9-section schema referenced by audit Classifier 9 (template-drift) and daily mode.

## 1. Audit report frontmatter

```yaml
---
categories: [wiki]
type: report
report_type: audit
date: YYYY-MM-DD
mode: audit
scope: <"vault-wide" | "<top-level-path>">
classifiers_run: 9
findings_critical: <int>
findings_warning: <int>
findings_info: <int>
vault_health_score: <int 0-100>
prior_audit_score: <int 0-100 | null>
trend: <"improving" | "stable" | "declining" | "first-audit">
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
tags:
  - topic/vault-maintenance
  - topic/integrity
  - topic/audit
related:
  - "[[hot]]"
  - "[[knowledge-moc]]"
  - "[[<prior-audit-stem-if-exists>]]"
---
```

## 2. Audit report body section order

```markdown
# Vault Audit Report YYYY-MM-DD[-HHMM]

**Scope:** <vault-wide | scope-path> | **Classifiers:** 9 | **Score:** <N>/100 | **Trend:** <improving | stable | declining | first-audit>

## Executive Summary

<single paragraph; composite vault-health verdict; finding-count-by-severity; top-priority fix recommendation; trend vs prior audit if applicable>

## CRITICAL Findings (<C> total)

<each finding numbered C1, C2, ... with file path + line number + classifier + recommendation; omit section if zero>

### C1: <classifier name> -- <one-line summary>
- **Files:** <list with full paths>
- **Line numbers:** <where applicable>
- **Recommendation:** <specific fix; if SAFE-AUTO, note "fixable via /vault repair --apply C1">
- **Detection rule:** <reference to ref-audit-classifiers.md classifier number>

## WARNING Findings (<W> total)

<each finding numbered W1, W2, ... same format as CRITICAL; omit section if zero>

## INFO Findings (<I> total)

<each finding numbered I1, I2, ... same format; omit section if zero>

## Continuity vs Prior Audit

<only when prior_audit_score is not null>

| Metric | Prior (<date>) | Current | Delta |
|---|---|---|---|
| Vault health score | <X> | <Y> | <+/- Z> |
| CRITICAL count | <X> | <Y> | <+/- Z> |
| WARNING count | <X> | <Y> | <+/- Z> |
| INFO count | <X> | <Y> | <+/- Z> |

Trend rationale: <one-sentence explanation>.

<!-- FOLLOWUPS:skills -->
- [CRITICAL] /vault repair --apply <ids> -- <rationale> (trigger: NOW)
- [WARNING] /enrich candidate -- <rationale> (trigger: EOW)
- [INFO] /vault repair --apply <ids> -- <rationale> (trigger: EOM)
<!-- /FOLLOWUPS:skills -->

---

Composite score rationale: base 100; <C>x-10 CRITICAL = -<X>; <W>x-3 WARNING = -<Y>; <I>x-1 INFO = -<Z>; continuity adjustment <+/- Z> = <final>/100.
```

## 3. Audit meta.json sidecar schema

```json
{
  "schema_version": 1,
  "report_type": "audit",
  "report_date": "YYYY-MM-DD",
  "report_filename": "audit-YYYY-MM-DD[-HHMM].md",
  "generated_at": "YYYY-MM-DDTHH:MM:SS",
  "mode": "audit",
  "scope": "vault-wide",
  "classifiers_run": [
    "broken-wikilinks",
    "missing-frontmatter",
    "frontmatter-schema",
    "orphan-detection",
    "stale-refs",
    "deprecated-references",
    "daily-continuity",
    "template-drift",
    "MOC-coverage"
  ],
  "findings_by_classifier": {
    "broken-wikilinks": 7,
    "missing-frontmatter": 0,
    "frontmatter-schema": 12,
    "orphan-detection": 3,
    "stale-refs": 5,
    "deprecated-references": 3,
    "daily-continuity": 7,
    "template-drift": 1,
    "MOC-coverage": 2
  },
  "findings_by_severity": {
    "CRITICAL": 7,
    "WARNING": 21,
    "INFO": 12
  },
  "vault_health_score": 67,
  "vault_health_score_rationale": {
    "base": 100,
    "critical_penalty": -50,
    "warning_penalty": -30,
    "info_penalty": -10,
    "continuity_adjustment": +5,
    "final": 67
  },
  "prior_audit_score": 78,
  "trend": "declining",
  "expected_archived": ["research", "review", "career-v1", "deep-v1", "invest-v1", "retro-v1", "spark-v1", "vault-v1"],
  "known_deprecations": ["/research (2026-04-26)", "/review (2026-04-26)"],
  "followup_skills": [
    {
      "issue_id": "C1-C7",
      "skill": "/vault",
      "subcommand": "repair --apply C1-C7",
      "rationale": "7 broken wikilinks in wiki/entities/tickers/",
      "trigger": "NOW",
      "severity": "CRITICAL"
    }
  ],
  "phases_timing_ms": {
    "A_preflight": 12,
    "B_state_transition": 3,
    "C_context_load": 240,
    "D_script_wrapper": 4500,
    "E_frontmatter_schema": 1200,
    "F_deprecated_refs": 350,
    "G_daily_continuity": 80,
    "H_template_drift": 25,
    "I_severity_rollup": 60,
    "J_health_score": 15,
    "K_pre_output_gate": 45,
    "L_ascii_scan": 30,
    "M_compose": 850,
    "N_final_verification": 50,
    "O_atomic_write": 180,
    "P_peripheral_updates": 320
  },
  "pre_output_gate_results": {
    "item_01_f11_set": "PASS",
    "item_02_collision_resolved": "PASS",
    "item_03_frontmatter_schema": "PASS",
    "item_04_findings_or_clean": "PASS",
    "item_05_specific_paths": "PASS",
    "item_06_severity_classification": "PASS",
    "item_07_followups_syntax": "PASS",
    "item_08_health_score_computed": "PASS",
    "item_09_continuity_comparison": "PASS",
    "item_10_exclude_list_applied": "PASS",
    "item_11_canonical_schema_referenced": "PASS",
    "item_12_ascii_only": "PASS",
    "item_13_related_field_count": "PASS",
    "item_14_symmetric_backlink_plan": "PASS",
    "item_15_path_guard": "PASS",
    "item_16_sessions_log_entry": "PASS",
    "item_17_hot_md_last_audit": "PASS",
    "item_18_f17_co_authored_absent": "PASS"
  }
}
```

## 4. Stats report schema

Same frontmatter shape as audit, with:
- `report_type: stats`
- `statistics_count: 18`
- `calibration_score_30d: <float 0.0-1.0>`
- `predicted_30d_trend: <"improving" | "stable" | "declining">`

Body sections:
1. Executive Summary
2. File / Word / Path Counts (statistics 1-2)
3. Coverage Metrics (statistics 3-4)
4. Freshness + Activity (statistics 5-9)
5. Calibration (statistic 10; Brier-style)
6. Graph Health (statistics 11-14)
7. Domain Activity (statistic 15)
8. Skill Surface (statistics 16-17)
9. Tools Inventory (statistic 18)
10. Continuity vs Prior Stats
11. FOLLOWUPS:skills

## 5. Repair audit log schema

```yaml
---
categories: [wiki]
type: report
report_type: repair
audit_source: <audit report stem>
issues_attempted: <int>
issues_succeeded: <int>
issues_failed: <int>
issues_classification: { "SAFE-AUTO": <int>, "NEEDS-CONFIRM": <int> }
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
tags: [topic/vault-maintenance, topic/repair]
related:
  - "[[hot]]"
  - "[[<audit-source-stem>]]"
---
```

Body: per-issue table with ID, classification, action taken, before/after sha256, status (succeeded / failed / not-attempted).

## 6. Refresh report schema

```yaml
---
categories: [wiki]
type: report
report_type: refresh
ref_docs_evaluated: <int>
top_priority_count: 3
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
tags: [topic/vault-maintenance, topic/refresh]
related:
  - "[[hot]]"
  - "[[knowledge-moc]]"
---
```

Body: ranked table with ref-doc-name, top-level-path, days-stale, path-activity-since-update, thesis-weight, priority-score, recommended-action (refresh now / can wait / low priority). FOLLOWUPS:skills surfaces top-3 as /deep candidates.

## 7. Sessions-log entry (Phase P; per mode)

### audit mode
```markdown
### YYYY-MM-DD -- /vault audit -- score <N>/100
- **Domain:** meta/skill-infrastructure
- **Scope:** <vault-wide | scope-path>
- **Findings:** <C> CRITICAL, <W> WARNING, <I> INFO
- **Trend:** <improving | stable | declining | first-audit>
- **Followup skills:** <count> (<comma-list>)
- **Artifacts:** [[audit-<date>[-HHMM]]]
- **Related:** [[hot]] | [[knowledge-moc]]
```

### stats mode
```markdown
### YYYY-MM-DD -- /vault stats -- 18 statistics
- **Domain:** meta/skill-infrastructure
- **Vault-health-score:** <N>/100
- **Calibration-score-30d:** <float>
- **Predicted-30d-trend:** <improving | stable | declining>
- **Artifacts:** [[stats-<date>[-HHMM]]]
- **Related:** [[hot]] | [[knowledge-moc]]
```

### repair mode
```markdown
### YYYY-MM-DD -- /vault repair -- <X> SAFE-AUTO + <Y> CONFIRMED applied
- **Domain:** meta/skill-infrastructure
- **Audit source:** [[<audit-source-stem>]]
- **Outcome:** <X+Y>/<X+Y attempted> succeeded
- **Artifacts:** [[repair-<date>[-HHMM]]]
- **Related:** [[hot]] | [[<audit-source-stem>]]
```

### refresh mode
```markdown
### YYYY-MM-DD -- /vault refresh -- <N> ref docs ranked
- **Domain:** meta/skill-infrastructure
- **Top-3 priority:** <comma-list of ref-doc names>
- **Followup skills:** <count> /deep candidates
- **Artifacts:** [[refresh-<date>[-HHMM]]]
- **Related:** [[hot]] | [[knowledge-moc]]
```

## 8. hot.md frontmatter bumps (Phase P; per mode)

- audit: `last_audit: <today>`, `last_audit_score: <int>`
- stats: `last_stats: <today>`, `last_stats_calibration: <float>`
- repair: `last_repair: <today>`
- refresh: `last_refresh: <today>`

All bumps preserve body byte-exact (sha256 invariant).

## 9. Canonical daily-note 9-section schema

Per CLAUDE.md sec 4.5. Audit Classifier 9 (template-drift) checks `_templates/daily.md` against this. Daily mode Phase D verifies today's daily note has all 9.

```markdown
---
categories: [daily]
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
tags: []
---

# YYYY-MM-DD <Day-of-week>

## Market Pulse
> Pre-market moves, overnight news, thesis-relevant developments

## Observations
> Free-form human-signal notes

## Decisions
> Investment, career, or project decisions with rationale

| Domain | Decision | Why |
|--------|----------|-----|

## Commitments
- [ ]

## Insights
> Cross-domain connections, pattern recognition, things that clicked

## Sessions Run
> Claude Code sessions, skill invocations, outputs created

## Cross-References
> Wikilinks to entities/skills/files touched

## Tasks
- [ ]

## Log
> Raw prompts auto-appended by UserPromptSubmit hook (Donbavand pattern)
> Format: `- <ISO> :: <prompt>`
```

Sections 1-8: human signal (write or curated). Section 9: machine log (auto-appended by hook). Audit Classifier 9 checks all 9 H2 headers present in `_templates/daily.md`.

## 10. Symmetric back-link reciprocation (Phase P)

For each wikilink in audit/stats/refresh/repair report `related:` field:
- `[[hot]]` -- frontmatter bump only (last_audit/last_stats/etc.); no body insertion
- `[[knowledge-moc]]` -- read-only reference; no insertion
- `[[<prior-report-stem>]]` -- prior audit/stats reports get footer line: `Superseded by [[<current-report-stem>]] on YYYY-MM-DD.` (one-time append; idempotent)

Body-preservation sha256 invariant on every insertion: capture pre-write sha256 of content outside intended insertion site; verify post-write match. F.halt on mismatch.

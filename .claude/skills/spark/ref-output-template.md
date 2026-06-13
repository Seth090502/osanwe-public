---
categories: [sources]
type: reference
created: 2026-04-26
updated: 2026-04-26
status: active
tags:
  - topic/skill-infrastructure
  - topic/spark
aliases:
  - spark output schema
  - spark template
related:
  - "[[SKILL|/spark SKILL.md]]"
  - "[[ref-pattern-taxonomy]]"
---

# /spark Output Template Reference

Canonical schemas for every artifact /spark writes. SKILL.md Phase M + Phase P reference this doc; this doc holds the shape.

## 1. Spark report frontmatter (canonical)

```yaml
---
categories: [wiki]
type: spark
date: YYYY-MM-DD
mode: <scan | focus | continuity | theme>
focus_target: <null | "<domain>" | "<tag>" | "<entity-stem>" | "<class>">
timeframe_days: <int; default 14>
files_analyzed: <int>
patterns_found: <int>
patterns_below_threshold: <int>
prior_sparks_continuity: <int; count of prior sparks scored>
prior_calibration_score: <float 0.0-1.0 | null if no prior sparks>
confidence: <int 0-100; aggregate report-level>
confidence_cap_rule: <"none" | "grade-d-30pct" | "inferential-meta" | "behavioral-90pct" | "<other>">
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: active
tags:
  - topic/cross-domain
  - topic/<specific-class-if-theme-mode>
related:
  - "[[hot]]"
  - "[[insight-stream]]"
  - "[[<entity-stem-1>]]"
  - "[[<entity-stem-2>]]"
  - "[[<thesis-slug-1-if-relevant>]]"
  - "[[<peer-spark-stem-if-evolution>]]"
---
```

`related:` 3-5 wikilinks typical. Always include `[[hot]]` and `[[insight-stream]]`. Add 1-3 entity/thesis stems based on which entities the promoted sparks substantively reference. If any spark is EVOLVED from a prior, include the peer-spark wikilink.

## 2. Spark report body section order

Skip empty sections; do not pad.

```markdown
# Spark Report YYYY-MM-DD[-HHMM]

**Mode:** <mode> | **Timeframe:** <N> days | **Focus:** <focus_target | "wide scan"> | **Continuity:** <prior_sparks_continuity> prior sparks scored

## TLDR

<single paragraph; meta-observation up front; what THE story is across the patterns; BLUF analog>

## Continuity Audit

<only when prior_sparks_continuity > 0; else omit section entirely>

| Prior Spark | Pattern Name | Status | Evidence |
|---|---|---|---|
| [[spark-YYYY-MM-DD]] | <pattern name> | PERSISTED \| EVOLVED \| INVALIDATED \| DORMANT | <one-line evidence reference> |

Calibration: <prior_calibration_score> (PERSISTED + 0.5*EVOLVED / total).

## Sparks

### 1. <Pattern Name (short noun phrase)>

- **Class:** <one of 9 from ref-pattern-taxonomy.md>
- **Domains:** <comma-list of 1+ domains>
- **Evidence:** <specific files + dates + entries; inline grading [Grade A-F | source | date] on material claims>
- **Insight:** <the "so what"; <=4 sentences; the surprise>
- **Confidence:** <int 0-100>; <one-line rationale>
- **Continuity:** NEW | EVOLVED FROM [[spark-YYYY-MM-DD]] | PERSISTED FROM [[spark-YYYY-MM-DD]]
- **Prediction:** test: <vault-observable mechanically-scorable check> | horizon: <YYYY-MM-DD> | direction: <expected outcome>   <!-- OPTIONAL (vNEXT S3); omit line when none; external-world tests name a vault proxy -->
- **Verified:** SURVIVES (4/4 lenses) | SURVIVES with haircut (<old> -> <new>%) | <omit line when verify wave did not cover this spark>   <!-- OPTIONAL (vNEXT H.5) -->

### 2. <Pattern Name>
...

### N. <Pattern Name>

## Below-Threshold Observations

<only when patterns_below_threshold > 0; else omit section entirely>

- **<dropped pattern name>** [class: <X>; evidence: <count>; reason: <below 3-instance threshold | above threshold but below promotion cap | invalidated by prior spark>]
- ...

## Meta-Observation

<one paragraph; 3-5 sentences; what super-axis the patterns cluster on; what the vault's recent activity reveals about underlying state; distinct from any single spark; not a pattern itself>

<!-- FOLLOWUPS:skills -->
- /decide <decision-name> -- <one-line rationale tied to spark N> (trigger: <NOW | NEXT MARKET OPEN | EOW | EOM | DEFERRED>)
- /challenge thesis-<slug> -- <rationale tied to spark N> (trigger: <time>)
- /brief <surface item> -- <rationale> (trigger: NEXT MARKET OPEN)
- /invest <TICKER> -- <rationale> (trigger: <time>)
- /vault <maintenance item> -- <rationale> (trigger: EOW)
<!-- /FOLLOWUPS:skills -->

Empty case: `(no followup skills recommended)` rendered explicitly inside the FOLLOWUPS block.

---

Prior calibration: <N> prior sparks: <X> PERSISTED, <Y> EVOLVED, <Z> INVALIDATED, <W> DORMANT.
Verify wave: fired <F> / refuted <R> / demoted <D> / survived <S> | (verify wave skipped: no qualifying sparks) | (Tier-B inline spot-check: <N> anchors opened, <M> refuted)   <!-- vNEXT gate item 19 -->
Prediction scoring: <P> prior predictions: <T> resolved-true, <F> resolved-false, <U> unresolved | (no prior predictions)   <!-- vNEXT S3; line present only when prior predictions exist -->
retrieval_degraded (phase0_hits=0)   <!-- vNEXT S6; line present ONLY when Phase 0 returned zero hits; non-halting -->
```

## 3. meta.json sidecar schema

Written alongside spark report at `<OUTPUT_PATH>-meta.json`.

```json
{
  "schema_version": 1,
  "spark_date": "YYYY-MM-DD",
  "spark_filename": "spark-YYYY-MM-DD[-HHMM].md",
  "generated_at": "YYYY-MM-DDTHH:MM:SS",
  "mode": "scan | focus | continuity | theme",
  "focus_target": null,
  "timeframe_days": 14,
  "files_analyzed": 47,
  "files_analyzed_by_class": {
    "daily": 14,
    "sessions-log": 1,
    "decision-log": 1,
    "briefings": 4,
    "entities": 12,
    "challenges": 2,
    "prior_sparks": 3,
    "domain_conditional": 10
  },
  "patterns_detected_by_class": {
    "cross-domain": 2,
    "behavioral": 1,
    "thesis-evolution": 0,
    "failure-mode": 1,
    "decision-divergence": 0,
    "negative-space": 1,
    "frequency-recency": 0,
    "tool-skill": 0,
    "meta": 0
  },
  "patterns_promoted": 5,
  "patterns_below_threshold": 4,
  "below_threshold_log": [
    {
      "name": "<pattern name>",
      "class": "<class>",
      "evidence_count": 2,
      "reason": "below 3-instance threshold"
    }
  ],
  "continuity_audit": [
    {
      "prior_spark_filename": "spark-2026-04-16.md",
      "pattern_name": "<name>",
      "status": "EVOLVED",
      "evidence": "<one-line>",
      "marker_signature": "<60-char-normalized-name>"
    }
  ],
  "prior_calibration_score": 0.72,
  "confidence_aggregate": 78,
  "confidence_cap_rule_applied": "none",
  "followup_skills": [
    {
      "skill": "/decide",
      "target": "<decision-name>",
      "rationale": "<one-line>",
      "trigger": "EOW",
      "tied_to_spark": 1
    }
  ],
  "phases_timing_ms": {
    "A_preflight": 12,
    "B_state_transition": 3,
    "C_context_load": 1840,
    "D_continuity_audit": 220,
    "E_pattern_detection": 6800,
    "F_substantive_filter": 80,
    "G_promotion_cap": 25,
    "H_confidence_calibration": 110,
    "I_meta_observation": 350,
    "J_followups_emission": 90,
    "K_pre_output_gate": 45,
    "L_ascii_scan": 38,
    "M_compose": 920,
    "N_final_verification": 60,
    "O_atomic_write": 180,
    "P_peripheral_updates": 540
  },
  "pre_output_gate_results": {
    "item_01_f11_set": "PASS",
    "item_02_collision_resolved": "PASS",
    "item_03_frontmatter_schema": "PASS",
    "item_04_substantive_spark": "PASS",
    "item_05_evidence_specificity": "PASS",
    "item_06_confidence_format": "PASS",
    "item_07_continuity_table": "PASS",
    "item_08_followups_syntax": "PASS",
    "item_09_followups_specificity": "PASS",
    "item_10_meta_observation": "PASS",
    "item_11_below_threshold_log": "PASS",
    "item_12_ascii_only": "PASS",
    "item_13_related_field_count": "PASS",
    "item_14_symmetric_backlink_plan": "PASS",
    "item_15_path_guard": "PASS",
    "item_16_sessions_log_entry": "PASS",
    "item_17_hot_md_last_spark": "PASS",
    "item_18_f17_co_authored_absent": "PASS"
  }
}
```

### 3b. vNEXT additive sidecar fields (2026-06-10; ADDITIVE ONLY -- every pre-existing key above is unchanged)

Appended to the same meta.json object. Pre-vNEXT sidecars lack these keys and parse fine (schema-additive, the calibration-monitor column precedent).

```json
{
  "topology": "dw | sequential",
  "orchestrator_model": "<active model string; passive, never branched on>",
  "phase0_hits": 0,
  "window_end": "YYYY-MM-DD",
  "retrospective": false,
  "verify_wave": {
    "fired": 0, "refuted": 0, "demoted": 0, "survived": 0,
    "mode": "dw-wave | tier-b-spot-check | skipped-no-qualifying",
    "refutations": [
      { "spark": "<title>", "lens": "evidence | falsifiability | novelty | mundane | contract", "reason": "<one-line>" }
    ]
  },
  "predictions": [
    { "spark": 1, "test": "<vault-observable check>", "horizon": "YYYY-MM-DD", "direction": "<expected>" }
  ],
  "prediction_scoring": {
    "scored": 0, "resolved_true": 0, "resolved_false": 0, "unresolved": 0,
    "pred_component": null, "vibes_component": 0.0, "combined_formula_applied": false
  },
  "token_budget_logged": 600000,
  "token_actuals_note": "<actuals when available; S7 recalibration input>",
  "pre_output_gate_results_vnext": {
    "item_19_verify_wave_recorded": "PASS",
    "item_20_predictions_well_formed": "PASS",
    "item_21_topology_logged": "PASS"
  }
}
```

## 4. Sessions-log entry (Phase P)

Appended to `Calendar/decisions/sessions-log.md` per canonical schema:

```markdown
### YYYY-MM-DD -- /spark <mode> -- <N> patterns surfaced
- **Domain:** meta/cross-domain
- **Focus:** <focus_target | "wide scan">
- **Patterns surfaced:** <N>; classes: <comma-list>
- **Continuity score:** <prior_calibration_score | "no prior sparks">
- **Followup skills:** <count> (<comma-list of skill names>)
- **Artifacts:** [[spark-<date>[-HHMM]]]
- **Related:** [[hot]] | [[insight-stream]]
```

Marker signature for /retro merge: `(date, "/spark <mode>")`. Idempotent re-run dedup via this signature.

## 5. Daily note linkback (Phase P)

Appended to `Calendar/daily/<today>.md` `## Insights` section:

```markdown
- [HH:MM] /spark <mode> -- <N> patterns; meta: <one-line meta-observation>; full: [[spark-<date>[-HHMM]]]
```

If `## Insights` section absent in today's daily note, HALT (daily note schema-drift; surfaces /vault audit candidate).

## 6. hot.md frontmatter bump (Phase P)

Update or add `last_spark: <today>` field. Position: alphabetical within frontmatter (typically after `last_briefing:`). Body unchanged. Body-preservation sha256 invariant.

## 7. Symmetric back-link reciprocation (Phase P)

For each wikilink in spark `related:` field:

- **Entity targets** (`wiki/entities/{tickers,companies}/`): append to entity's `## Recent` section line: `- [YYYY-MM-DD] /spark surfaced cross-domain pattern: [[spark-<date>[-HHMM]]] (class: <X>; confidence: <pct>)`
- **Thesis targets** (`Atlas/concepts/investing/theses/thesis-*.md`): append to `## Recent Spark References` section (create if absent): `- [YYYY-MM-DD] [[spark-<date>[-HHMM]]] (class: <X>; impact: <one-line>)`
- **Peer spark targets** (when EVOLVED): append to prior spark's footer line: `Evolved into [[spark-<date>[-HHMM]]] on YYYY-MM-DD.` (one-time append; idempotent dedup)
- **Insight-stream and hot.md**: NEVER auto-write. Read-only references in `related:` only.

Body-preservation sha256 invariant: capture pre-write sha256 of content outside intended insertion site; verify post-write match. F.halt on mismatch.

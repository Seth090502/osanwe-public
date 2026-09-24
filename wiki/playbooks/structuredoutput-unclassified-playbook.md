---
categories: [wiki]
type: synthesis
status: active
created: 2026-07-10
updated: 2026-07-10
tags: [topic/consolidation, topic/playbook]
related:
  - "*hot* (not published)"
---

# StructuredOutput unclassified Playbook

## Pattern
Invariant: A StructuredOutput "Output does not match required schema" record is retry-absorbed noise -- not an actionable schema defect -- unless the same schema (identified by its required-property set) fails across two or more distinct sessions; in this window 5 of the 6 schemas failed inside a single session and only the /invest fundamentals schema clears the cross-session bar.

All 10 records are first-pass JSON the tool layer re-requests automatically; 3 of the 6 schemas show the retry-then-continue chain inside one session (doc-operability audit 06-09 session 2ab43cce, spark-verify 06-10 session 77dd50e0, consolidate-findings 06-13 session 8ca9f394), and none aborted its workflow. They surface as one 10-hit "systemic" cluster only because derive_error_class (tools/telemetry_analyzer.py:115) has no prefix-regex for schema-validation errors, so 6 unrelated schemas collapse into the catch-all unclassified bucket, and post-tool-use-failure.py logs each SDK retry as a separate terminal failure (it cannot see the retry succeeded). The design-informative misses cluster narrowly on a property marked required on every element of a variable-length array (findings[].gap, sparks[2].downstream_rec, lens_results.novelty.detail) -- the model fills it on some items but not all. The only genuine residue is invest-research.js's 21-property FUNDAMENTALS object (required ['scoring_path','claims','ws_calls_made'] at line 87), which already self-heals via the in-workflow convergence-gate re-dispatch (lines 120-133).

Confidence: 82% -- all 10 records resolved verbatim plus the sink hook, the classifier path, and the one live cross-session schema read directly; residual is that no-workflow-aborted is inferred from context lines and gate presence rather than full transcripts, and 3 retired schemas resolve to no in-tree definition.

## Evidence
- 10 failures clustered on StructuredOutput::unclassified
- Threshold cleared: >= 5 failures in cluster (observed 10).

## Counter-cases

- 2026-06-11 -- invest-research FUNDAMENTALS: /net_debt_ebitda must be number,null (.claude/state/failures-2026-06-11.jsonl:2, session ab02a021), the model writing a non-numeric after a FRED 400 degraded retrieval
- 2026-06-18 -- the SAME schema in a distinct session 7 days later: root missing required 'claims' (.claude/state/failures-2026-06-18.jsonl:13, session 4e9ca99e) -- the sole instance straining the all-retry-noise reading
- (searched: every failures-*.jsonl for tool StructuredOutput -- 10 records, 6 schemas; zero records after 2026-06-18; no schema other than invest-research FUNDAMENTALS appears under more than one session_id; no record shows an aborted or corrupted downstream artifact)

## Recommendation

Treat the cluster as a classifier artifact: (1) primary -- add a prefix-regex to derive_error_class in tools/telemetry_analyzer.py (line 115) mapping "^Output does not match required schema" to a distinct schema_validation class instead of the unclassified fallback, mirrored in tools/consolidator.py _derive_error_class (the unclassified bucket exists to surface UNKNOWN failure types; a known SDK-retried one should not dominate it and pull /consolidate into scaffolding); (2) secondary -- give _compute_failure_clusters (tools/telemetry_analyzer.py:565) same-session collapse so consecutive schema failures sharing a session_id count once, dropping this cluster from 10 to ~6 and under threshold; (3) watch-item -- invest-research.js FUNDAMENTALS (required set at line 87): no change now (the convergence gate at lines 120-133 re-dispatches on missing keys); revisit only on a THIRD cross-session failure. Route (1)+(2) through /gate b alongside the [[bash-exit-code-1-http-298-playbook]] classifier fix -- one error-class taxonomy change, ratified once.

## Apply-when

/consolidate or /consolidate telemetry surfaces a StructuredOutput cluster: grep '"tool": "StructuredOutput"' across the cited failures-*.jsonl, group records by missing-property set, and treat as retry-noise unless one schema's set appears under two or more distinct session_id values. Only the cross-session schema warrants a fix; scaffold no playbook for the single-session remainder.

## Related
- *hot* (not published) -- session cache; this playbook is surfaced in the consolidation digest
- [[bash-exit-code-1-playbook]]
- [[bash-exit-code-2-playbook]]
- [[read-unclassified-playbook]]

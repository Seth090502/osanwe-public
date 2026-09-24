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

# Mcp__fred__fred_get_series unclassified Playbook

## Pattern
Invariant: A FRED mcp__fred__fred_get_series 400 error (api_key-not-registered or series-does-not-exist) is a PERSISTENT caller/config defect and must not be routed through the same silent-skip path as a transient 500/timeout -- a 400 needs a distinct response (fix the key, or fix the series_id) PLUS a surfaced signal, because silent-skip converts a fixable defect into indefinite invisible data loss on a briefing-critical dependency.

The FRED MCP feeds /brief Phase E.0 regime classification (DGS10, T10Y3M, BAMLH0A0HYM2, VIXCLS, UNRATE) and the Phase F net-liquidity composite (WALCL - RRPONTSYD - WTREGEN + DTWEXBGS). Its availability-guard (ref-macro-data-sources.md Section 4; SKILL.md Phase E.0 line 267, Phase F line 302) collapses EVERY error into silent-skip-never-HALT -- correct for the two isolated self-clearing 500s (2026-06-09, 2026-06-16), but for a 400 it silently drops the entire FRED regime layer. The 2026-07-04 api_key regression proves the persistence distinction: fired 02:19, a malformed reg-query diagnostic failed 02:21, and the SAME error repeated 02:48 -- it did not self-heal. Because --quick briefings also skip FRED, a still-broken key is byte-indistinguishable from a deliberate skip: every briefing 2026-07-04..07-09 was --quick or FRED-less, so recovery is UNCONFIRMED as of authoring.

Confidence: 84% -- 5/5 sources resolved; three distinct error strings plus the 07-04 repeat-with-diagnostic prove the 400 persists where 500s self-clear; guard-collapse confirmed verbatim in both skill files; sole residual is the unconfirmed current key state, which the recommendation directly addresses.

## Evidence
- 5 failures clustered on mcp__fred__fred_get_series::unclassified
- Threshold cleared: >= 5 failures in cluster (observed 5).

## Counter-cases

- (no dated instance contradicts the three-class split -- searched fred across failures-2026-07-05..10.jsonl: zero hits; both 500s (failures-2026-06-09.jsonl:130, failures-2026-06-16.jsonl:4) were isolated with no repeat-on-next-call, so neither behaved like the persistent 400)
- Honest caveat, not a counter-case: recovery of the 07-04 api_key is UNCONFIRMED-positive -- absence of new failures is equally consistent with key-fixed and key-never-called (all subsequent briefings were --quick or FRED-less)
- Design tension bounding the fix: the silent-skip is a ratified additive guard (non-halting; NetLiq is reported-context-only, not a regime axis) -- so the fix must be a non-halting SIGNAL, never a HALT

## Recommendation

(1) NOW: issue one mcp__fred__fred_get_series smoke call (DGS10, limit 1) to confirm the api_key is registered again -- no successful post-outage FRED pull exists in evidence. (2) Amend the availability-guard to branch on error class -- .claude/skills/brief/ref-macro-data-sources.md Section 4 + SKILL.md Phase E.0 (line 267): keep silent-skip + one retry for 500/timeout/absence; for a 400, emit a one-line non-halting Warning Problems entry naming the class ("FRED 400 api_key-not-registered: regime layer degraded, fix key" vs "FRED 400 series does not exist: fix series_id") so a persistent defect surfaces instead of vanishing. Ratify via /decide fred-400-error-class-guard; optionally fold the DGS10 smoke call into a periodic config check so a persistent key failure cannot hide behind consecutive --quick runs.

## Apply-when

On any FRED API error, read the code before skipping: 400 api_key-not-registered -> config regression, fix the key (do not silent-skip); 400 series-does-not-exist -> caller typo, fix the series_id; 500/timeout -> transient, retry once then silent-skip is fine. Before trusting a briefing's regime or NetLiq line, confirm the last FRED pull actually SUCCEEDED and was not --quick-skipped.

## Related
- *hot* (not published) -- session cache; this playbook is surfaced in the consolidation digest
- [[bash-exit-code-1-playbook]]
- [[bash-exit-code-2-playbook]]
- [[read-unclassified-playbook]]

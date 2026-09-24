---
categories: [wiki]
type: synthesis
status: active
created: 2026-07-10
updated: 2026-07-10
tags: [topic/consolidation, topic/playbook]
related:
  - "hot"
---

# WebFetch unclassified Playbook

## Pattern
Invariant: WebFetch failures cluster by SESSION, not by tool defect -- 80 of the 81 in-window failures belong to a non-SSL class the standing rule never names (timeout 60s ~59%, ECONNREFUSED ~21%, socket-closed ~6%, maxContentLength ~5%, "unable to fetch from `<domain>`" ~5%, too-many-redirects ~2%), while the one class AGENTS.md actually routes to a fallback -- SSL-cert -- is a single record (~1%); because the "retry at most once" bound is scoped only to SSL, the transport tail has no named stop and a single research session storms (2026-06-08 session 9583faed fired 51 of the 81).

The 81-count is a June burst, not chronic friction: the 7-day telemetry window ending 2026-06-10 captured 70 of them (per_day 10.0); the 14-day window ending 2026-07-10 shows 4 (per_day 0.286) -- the cluster self-attenuated when the research binge ended. The dominant modes are non-idempotent under retry: a 60s timeout, an over-size resource (10MB cap hit identically 3x in one session, failures-2026-06-27.jsonl:2-4), and a domain block (reuters.com x4 -- NOT on the AGENTS.md blocked list) do not clear by re-firing the same URL. Falsifier: an SSL-dominated distribution, a session-uniform spread, or evidence that retries eventually succeeded -- the logs show the opposite on all three.

Confidence: 73% -- all 81 rows classified from raw logs and the 70->4 collapse cross-confirmed by two telemetry reports; softer elements are adoption odds given two prior benign/expected verdicts, and same-URL re-fire inferred from same-session + same-error + minutes-apart rather than observed (sinks log url as a key, not its value).

## Evidence
- 81 failures clustered on WebFetch::unclassified
- Threshold cleared: >= 5 failures in cluster (observed 81).

## Counter-cases

- 2026-06-10 -- this exact cluster was already investigated and ruled benign: wiki/maintenance/orphan-investigation-2026-06-10.md:42 classifies "WebFetch unclassified | 70" as blocked-domain/SSL fallbacks, expected shape for research-heavy nights -- a genuine no-fix-warranted counter-position AND a mis-attribution (the cluster is ~1% SSL, ~86% timeout/refusal), which is itself why the retry-bound was never tightened
- ~2026-06-09 -- surfaced as a telemetry followup and deliberately deferred twice (Calendar/decisions/sessions-log.md:3608, :3642 -- "standing cumulative signal"): the system has repeatedly chosen not to action it, so any recommendation must justify itself against a standing leave-it prior
- Rate collapse (70 -> 4 per window) strains an urgent-systemic-defect framing: the pain largely resolved on its own when the June research nights stopped

## Recommendation

Amend the AGENTS.md Tool-mechanics line (Data sources section) via /decide webfetch-failure-retry-bound, generalizing the retry-bound from SSL-only to ALL classes: (1) SSL-cert -> one curl -sk retry (unchanged); (2) timeout / ECONNREFUSED / socket-closed -> one curl -sk retry, then DROP the source and grade it unverifiable -- never a third attempt on one URL; (3) maxContentLength / too-many-redirects / "unable to fetch from `<domain>`" -> do NOT retry (deterministic failures) -- switch source and treat the domain as blocked for the session. /invest and /ingest inherit via their per-AGENTS.md pointer, so this is a single-point fix. Secondary: correct the mis-attribution at wiki/maintenance/orphan-investigation-2026-06-10.md:42 (timeout/refusal-dominated, not SSL) and consider adding reuters.com to the blocked list.

## Apply-when

A WebFetch call just failed and you are about to reissue it: read the error string. SSL-cert -> one curl -sk retry. Anything else (timeout / ECONNREFUSED / socket-closed / maxContentLength / redirects / unable-to-fetch) -> at most one curl -sk retry, then drop the source and grade it unverifiable. Two failures on one URL means switch source; a third fire on the same URL means you are the storm -- stop.

## Related
- hot -- session cache; this playbook is surfaced in the consolidation digest
- [[bash-exit-code-1-playbook]]
- [[bash-exit-code-2-playbook]]
- [[read-unclassified-playbook]]

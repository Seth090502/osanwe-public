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

# (unknown) subagent failure rate Playbook

## Pattern
Invariant: A (unknown) agent_type row in the consolidator's agent_outcomes is never a subagent reliability signal -- it is the D-T1 session_stop class (main-session Stop-hook events: tool_use_id == session_id with an empty agent_type) that tools/telemetry_analyzer.py is_session_stop already excludes from orphan pairing but ingest_telemetry does not; its 100% unpaired rate is the definitional signature of a Stop that never had a Start, not of a dispatch that died. Refuted only by an (unknown) bucket containing a start event, or keyed by a real toolu_-prefixed tool_use_id distinct from its session_id -- neither exists in the corpus.

Mechanism: ingest_telemetry groups every subagent event by tool_use_id or session_id (tools/consolidator.py:316); because the telemetry hook coalesces tool_use_id to session_id (tools/subagent-telemetry.py:133), every event in one session collapses into a single bucket, labeled (unknown) only when NO event in the whole session ever carried an agent_type (line 333) and marked failed without a paired start (lines 336-339). Sessions that ran a real subagent absorb their unlabeled stops into the named bucket (2026-06-30 session b1ab34b5 folds ~60 empty stops and six distinct agent types into one paired vault-classifier-sweep row), so (unknown) collects only the residue: sessions whose sole telemetry was unlabeled main-session Stop events. The analyzer already adjudicated this exact class as D-T1 (2026-06-10) and is_session_stop cut reported orphans 106 -> 1 with 586 session_stops excluded (telemetry-2026-06-10.md vs telemetry-2026-07-10.md:19-21); the consolidator never received that guard, so the miner re-manufactures the already-refuted 100%-failure signal -- this scaffold itself is the artifact's product.

Confidence: 94% -- exact code path proven end-to-end (grouping consolidator.py:316/333/336-339, emitter :424-435, vs the shipped is_session_stop guard at telemetry_analyzer.py:88-97) plus the vault's own adjudication (orphan 106 -> 1) plus a zero-hit falsifier grep across all 45 sinks; residual is not enumerating the exact 20 subagent-free session_ids, which does not bear on the mechanism.

## Evidence
- 20/20 (unknown) dispatches unpaired (orphan/hanging) = 100.0% failure rate
- Threshold cleared: >= 30% failure rate (min 3 events) (observed 20).

## Counter-cases

- (none found -- searched all 45 subagent-telemetry-*.jsonl for a stop with empty agent_type carrying a real toolu_-prefixed tool_use_id distinct from session_id, i.e. a genuine dead dispatch that would legitimately land in (unknown): 0 matches; every one of the 1008 empty-agent_type stops has tool_use_id == session_id, the D-T1 signature; all six occurrence rows traced to source collapse into named PAIRED buckets -- 05-21:13 + 05-22:3 -> Explore/387d8e91; 06-30:35-36 -> vault-classifier-sweep/b1ab34b5; 07-09:73 + 07-10:4 -> workflow-subagent/playbook-author/6fc83030)
- Scope caveat, not a counter-case: the same session_id collapse also merges genuinely distinct agents (06-30 folds forensic-scorer, thesis-critic, price-fetcher, institutional-positioning-scout, claim-distributor into one vault-classifier-sweep row), so ingest_telemetry per-agent accounting is unreliable beyond (unknown)

## Recommendation

Suppress at source; do not act on this bucket. (1) Minimal: in the skill_failure_rate emitter at tools/consolidator.py:424, skip at == "(unknown)" -- a bucket that never saw any agent_type across an entire session is only session_stop-class events and can never be a named-agent reliability signal; this alone stops the stub regenerating. (2) Fuller: port telemetry_analyzer.py is_session_stop (lines 88-97) plus its FIFO start/stop pairing (lines 375-416) into ingest_telemetry (consolidator.py:312-339), keeping BOTH is_session_stop conditions (empty agent_type AND tool_use_id==session_id) so legacy real-agent records stay pairing-eligible. Ratify via /decide consolidator-dt1-parity cross-referencing the D-T1 thread (Calendar/decisions/sessions-log.md:3882; telemetry-2026-07-10.md:19-21); on landing, flip this playbook to status deprecated -- it documents an already-adjudicated non-bug.

## Apply-when

A skill_failure_rate pattern (or scaffolded playbook) names agent_type "(unknown)" or any label-less bucket: treat it as the D-T1 session_stop artifact. 30s check: grep the cited subagent-telemetry-*.jsonl line -- tool_use_id == session_id with agent_type == "" means a main-session Stop event; do not author, escalate, or inspect transcripts. A NAMED agent_type at a high unpaired rate is a real signal and this exemption does NOT apply.

## Related
- *hot* (not published) -- session cache; this playbook is surfaced in the consolidation digest
- [[bash-exit-code-1-playbook]]
- [[bash-exit-code-2-playbook]]
- [[read-unclassified-playbook]]

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

# Read unclassified Playbook

## Pattern
Invariant: Read::unclassified is not one bug but 122 records splitting into two co-dominant, independently-fixable modes -- 57 unverified-path reads (~47%, "File does not exist") and 58 unbounded or under-bounded large-file reads (~48%: 26 over the 256KB byte ceiling + 32 over the 50000-token ceiling) -- plus a 7-record directory-read tail (~6%, EISDIR), every one preventable at the call site, so the cluster clears only by fixing path-verification AND read-bounding, never by a single patch.

The consolidator's _derive_error_class (tools/consolidator.py:92-107) matches only "Exit code N" and "HTTP N" prefixes, so all three Read error families fall through to one alarming 122-count "unclassified" bucket pointing at no single root cause. The does-not-exist half is a path constructed from memory or inference and never verified (the error text repeatedly appends the cwd note, once "Did you mean subagent-telemetry.py?"). The oversize half is a whole-file or under-bounded read: naked file_path reads bust the 256KB byte ceiling, while reads that DID set a line limit still bust the 50000-token ceiling on token-dense content (the entire 2026-06-20 run carried limit+offset and still returned 59k-176k tokens). Records expose tool_input_keys only, not the attempted path, so the specific files are not recoverable from the log -- the mode split derives from error strings and key signatures.

Confidence: 88% -- all 122/122 records classified directly and the unclassified fallthrough confirmed in consolidator source; the only soft link is attributing does-not-exist records to guessed/stale paths from error-text cues, since tool_input_keys hide the attempted path.

## Evidence
- 122 failures clustered on Read::unclassified
- Threshold cleared: >= 5 failures in cluster (observed 122).

## Counter-cases

- A third mode strains the strict two-mode reading -- 7 EISDIR records (a directory handed to Read; fix is Glob, not Read): 2026-06-06 wiki/investing/analyses (.claude/state/failures-2026-06-06.jsonl:7); 2026-06-07 same dir (failures-2026-06-07.jsonl:12); 2026-06-09 four dirs incl. tools/lib (failures-2026-06-09.jsonl:7,32,34,42); 2026-07-02 tools (failures-2026-07-02.jsonl:11)
- (none found for genuine tool/IO/permission faults -- searched all 122 Read records: zero permission-denied, zero file-existed-then-vanished races, zero environment faults; the 100% call-site-preventable claim holds)

## Recommendation

Structural (dissolves the false mega-cluster): extend _derive_error_class in tools/consolidator.py (lines 92-107) and its mirror in tools/telemetry_analyzer.py to subclassify before the "unclassified" fallthrough: "^File does not exist" -> path_not_found; "exceeds maximum allowed (size|tokens)" -> oversize_read; "^EISDIR" -> is_a_directory; then re-run /consolidate telemetry. Behavioral (drops the underlying counts): add one row to the AGENTS.md "Before you act" trigger table -- about to Read a path you did not just list or receive -> confirm it exists via Glob first; unknown/large file -> pass limit or Grep the content; a directory -> Glob, never Read. Ratify both via /decide read-failure-subclassify.

## Apply-when

/consolidate or /consolidate telemetry surfaces Read::unclassified (or post-fix Read::path_not_found / Read::oversize_read) at count >= 5: run two greps over .claude/state/failures-*.jsonl counting "does not exist" vs "exceeds maximum". If both are non-trivial (57 vs 58 here), it is the composite -- apply the path-verify fix AND the read-bounding fix; do not expect one change to clear it.

## Related
- hot -- session cache; this playbook is surfaced in the consolidation digest
- [[bash-exit-code-1-playbook]]
- [[bash-exit-code-2-playbook]]
- [[webfetch-unclassified-playbook]]

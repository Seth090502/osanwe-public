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

# Bash Exit_code_1_HTTP_298 Playbook

## Pattern
Invariant: A telemetry error_class of the shape Exit_code_N_HTTP_<n> does NOT denote an HTTP status; <n> is only the first word-bounded 3-digit token the classifier regex reaches inside the captured trace, so the slug is non-diagnostic and any such cluster must be triaged by reading the raw failures-*.jsonl records, never by its label.

Mechanism: the HTTP branch in tools/consolidator.py:96 and its byte-identical twin in tools/telemetry_analyzer.py:102 is `^Exit code (\d+).*?\b(\d{3})\b` compiled with re.DOTALL: the lazy .*? crosses every newline into the full Python traceback and grabs the first 3-digit token -- which for any json.load failure is the interpreter frame json/__init__.py line 298. Because json.load is a near-universal idiom in the vault's bash one-liners, that single library line number manufactured an 8-of-8 "HTTP_298" family out of two unrelated root causes: 4 empty-stdin/empty-file JSONDecodeErrors and 4 cp1252 UnicodeDecodeErrors on the SAME ~/.vault-substrate/index/vault-meta.json read without encoding='utf-8' -- the real, still-unfixed repeat offender the label hid (06-09 x2, 06-27, 07-02, recurring as that index grew 1.3MB -> 3.2MB). The same regex mislabels a wider family -- ls block counts (153), wc line counts (503), DCF dollar figures (492), workflow-hash fragments (435) all surface as HTTP_<n> across the 05-23/06-10/07-10 telemetry reports -- and a PowerShell::Exit_code_1_HTTP_298 record on 05-30 shows the false family is not confined to Bash.

Confidence: 96% -- mechanism read directly in both source files and all 8 in-window records hand-traced through the regex; residual is only exact cluster-window membership across reports, which does not affect the invariant.

## Evidence
- 8 failures clustered on Bash::Exit_code_1_HTTP_298
- Threshold cleared: >= 5 failures in cluster (observed 8).

## Counter-cases

- 2026-05-29 -- npm "404 Not Found - GET https://registry.npmjs.org/..." labeled Exit_code_1_HTTP_404 (.claude/state/failures-2026-05-29.jsonl:1): the ONE genuine strain -- here 404 really is an HTTP status, so the slug is coincidentally correct, which is exactly why the invariant says non-diagnostic rather than always-wrong
- 2026-06-09 -- "503 .claude/skills/retro/SKILL.md" is a wc -l line count, not Service Unavailable (.claude/state/failures-2026-06-09.jsonl:127): named because 503 is the token most likely to send a triager chasing a network ghost
- (searched all failures-*.jsonl for curl / Could not resolve / Max retries / HTTPError / requests.exceptions signatures behind HTTP_298 -- zero genuine network failures; the 05-29 npm 404 is the sole genuine HTTP token in the family)

## Recommendation

Fix the identical HTTP-branch regex in BOTH tools/consolidator.py:96 (_derive_error_class) and tools/telemetry_analyzer.py:102 (ERROR_CLASS_PATTERNS) in one change (the copies must stay byte-identical): require a literal HTTP context token -- `^Exit code (\d+).*?\bHTTP[/ ]?(\d{3})\b` -- so the branch can no longer fire on a bare traceback line number; mislabeled records then fall through to plain Exit_code_N, and a follow-on sub-bucket by terminal exception (Exit_code_1_JSONDecodeError vs Exit_code_1_UnicodeDecodeError) maps to root cause. Route through /gate b and ratify via /decide telemetry-http-errorclass-false-split (this retires the entire spurious HTTP_<n> family, not just 298). Separately fix the real bug the label concealed: the .vault-substrate/index/vault-meta.json reads must pass encoding='utf-8' (Windows cp1252 chokes on UTF-8 bytes). Once the classifier fix lands and reports re-run clean, flip this playbook's status to deprecated -- it documents a classifier artifact, not durable tool doctrine.

## Apply-when

Any /consolidate or telemetry cluster whose slug matches *_HTTP_<n>: do NOT read it as a network error. Grep that cluster's failures-*.jsonl for <n>; if it appears as a '", line <n>,' traceback frame or a wc/ls/dollar count, it is a first-3-digit-token false-split -- triage by terminal exception type. Treat as HTTP only if a raw record shows an actual curl/registry/HTTP-response result.

## Related
- hot -- session cache; this playbook is surfaced in the consolidation digest
- [[bash-exit-code-1-playbook]]
- [[bash-exit-code-2-playbook]]
- [[read-unclassified-playbook]]

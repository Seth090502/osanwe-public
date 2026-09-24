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

# Bash Exit_code_1 Playbook

## Pattern
Invariant: Bash exit-code-1 volume in this vault is dominated by transient, self-corrected authoring errors in throwaway inline scripts, not by breakage of committed tooling -- 167 of the 197 cluster records (85%) are Python tracebacks whose failing frame is `<string>`, `<stdin>`, or a Temp/scratchpad file, while committed vault tools (tools/*.py, hooks) essentially never appear as the failing frame. Falsifier: if the driver were broken committed tooling, tracebacks would name committed .py paths and recur on the same path across sessions; they do not.

The failures cluster into four recurring self-inflicted root causes in ad-hoc `python -c` / heredoc / scratchpad code: (a) Windows `C:\...` paths pasted into Python string literals -> SyntaxError unterminated-string / unicodeescape (28 records); (b) non-ASCII printed or read under Windows cp1252 -> UnicodeEncode/DecodeError charmap (26 records); (c) inline `json.load(open('/tmp/...'))` on a temp file a prior step never wrote -> FileNotFoundError (the largest tail); (d) wrong JSON-shape assumptions -> KeyError/AttributeError/TypeError (32 records). The dominant scripting-error mode also shifted from bash-parse failures (Exit_code_2 top at x87 on 2026-06-10) to Python exceptions (Exit_code_1 top by 2026-07-10) -- same behavior, different exit code. Volume tracks ad-hoc-scripting intensity per session, so the cluster cannot be "cleared" by fixing one tool; it regenerates every scripting-heavy session.

Confidence: 86% -- the invariant rests on corpus-wide quantification (167/197 inline-frame tracebacks) cross-checked against ~130 directly-read records and the classifier source; residual uncertainty is in exact sub-cause shares, not the inline-vs-committed split.

## Evidence
- 197 failures clustered on Bash::Exit_code_1
- Threshold cleared: >= 5 failures in cluster (observed 197).

## Counter-cases

- 2026-05-24 -- verify-overnight-mission.sh exiting 1 BY DESIGN on a real gate miss ("ALL_GATES: FAIL / STATUS_MD: MISSION_INCOMPLETE"); correct response is read-the-finding, not fix-the-script (.claude/state/failures-2026-05-24.jsonl:3)
- 2026-06-11 -- the PII scanner correctly exiting 1 on real hits ("check-pii found 68 hits ... FAIL"), working as intended (.claude/state/failures-2026-06-11.jsonl:45,47)
- 2026-07-04 -- "nothing to commit, working tree clean" exits 1: a benign idempotent git no-op miscounted into the cluster (.claude/state/failures-2026-07-04.jsonl:16)
- 2026-06-09 / 2026-07-04 -- ModuleNotFoundError yaml/ruamel/psutil: reproducible environment gaps, not one-off typos (.claude/state/failures-2026-06-09.jsonl:47; failures-2026-07-04.jsonl:7,8)

These four strains scope the invariant to volume/dominant-driver: a blanket "exit-1 is noise" rule would be wrong for by-design harness FAILs and env gaps.

## Recommendation

Primary: amend `derive_error_class` in tools/telemetry_analyzer.py (lines 100-118) and its mirror `_derive_error_class` in tools/consolidator.py (lines 92-107) to sub-split Bash Exit_code_1 by failing-frame/tail: `<string>`/`<stdin>`/scratchpad/Temp -> Exit_code_1_adhoc_inline; committed tools/*.py or .claude/ frame -> Exit_code_1_tool; "nothing to commit" -> Exit_code_1_git_noop; FAIL/ALL_GATES/check-pii -> Exit_code_1_harness_expected. Ratify via /decide slug telemetry-exit1-subclassify (GATE-B applies -- tooling change). Secondary: the same /decide proposes an ad-hoc inline-script hygiene subsection for Atlas/sources/meta/ref-execution-discipline.md (Atlas is human-write-only; amendment rides ratification): write a scratchpad .py instead of `python -c` when the payload carries `C:\` paths or non-ASCII; always `open(..., encoding='utf-8')`; assert temp-file existence before reading; guard dict chains on unknown JSON shapes.

## Apply-when

A /consolidate or /consolidate telemetry run flags Bash::Exit_code_1 as a top cluster: before opening a tool-fix playbook, grep the window's .claude/state/failures-*.jsonl for Exit code 1 records whose traceback frame is `<string>`/`<stdin>`/scratchpad. If that share exceeds 60% (it has run ~85%), classify the cluster as ad-hoc-inline-script noise and route to authoring discipline, not tool repair.

## Related
- *hot* (not published) -- session cache; this playbook is surfaced in the consolidation digest
- [[bash-exit-code-2-playbook]]
- [[read-unclassified-playbook]]
- [[webfetch-unclassified-playbook]]

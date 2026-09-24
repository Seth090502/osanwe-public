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

# PowerShell Exit_code_1 Playbook

## Pattern
Invariant: A shell command must be dispatched to the tool whose interpreter matches the command's dialect -- bash idioms (heredocs <<EOF, `python -c` spanning newlines or embedded quotes, $(...), sqlite3) go to the Bash tool; PowerShell idioms (Verb-Noun cmdlets like Get-Content / Select-Object / Measure-Object, .Property member access, $null redirection) go to the PowerShell tool. Cross them and the command cannot parse: every resolved failure in this cluster is a dialect/tool mismatch, not a logic bug.

Mechanism: the Bash tool runs Git Bash (/usr/bin/bash, Unix /c/... paths, sqlite3 on PATH); the PowerShell tool runs powershell.exe, where << is a reserved redirection operator ("Missing file specification after redirection operator"), a multi-line `python -c` parses as a broken ScriptBlock, embedded quotes are stripped so Python sees "unterminated string literal", and sqlite3 is absent from PATH. The mismatch is bidirectional and symmetric: the same Windows-path forensic sessions that fed bash heredocs to PowerShell also fed PowerShell cmdlets and .Lines/.Count member-access to Bash, producing the sibling Bash::Exit_code_127 cluster. The trigger is Windows-native audit work -- reaching for C:\-style paths pulls the wrong interpreter reflexively. The cluster is dormant, not fixed: last mismatch 2026-06-20; PowerShell used correctly on 2026-07-05 (15/15 mutator-deny sweep, exit 2 by design); no guardrail landed -- it went quiet because the forensic workload ended.

Confidence: 83% -- the dialect-mismatch mechanism is dispositive from verbatim error strings across 3+ dates and independently confirmed bidirectionally; deductions for a heterogeneous Exit_code_1 label (native-PS bugs and real env failures inflate the 17-count) and an unproven remedy.

## Evidence
- 17 failures clustered on PowerShell::Exit_code_1
- Threshold cleared: >= 5 failures in cluster (observed 17).

## Counter-cases

- 2026-07-05 -- native-PowerShell sweep of 15 option/mutator tools ran correctly (15/15 BLOCKED, exit 2 by design), NOT a dialect failure (.claude/state/failures-2026-07-05.jsonl:12) -- narrows the rule to match-the-dialect, never avoid-PowerShell
- 2026-05-25 -- a genuine native-PowerShell script failed on a PS-specific variable-reference quoting bug, not dialect confusion (.claude/state/failures-2026-05-25.jsonl:7) -- the label is heterogeneous; the invariant targets the ~11-12 dialect-mismatch events, not all 17
- Falsifier search, no hit: across every record read, no bash-idiom-in-PowerShell or PS-cmdlet-in-Bash command exited 0 (searched failures-2026-05-25/-05-30/-06-06/-06-07/-06-09/-06-11/-06-20/-07-05.jsonl)

## Recommendation

Extend the AGENTS.md Tool-mechanics line ("Bash paths Unix-style (`<VAULT_ROOT>`)") with the reciprocal dialect-routing rule: bash heredocs / multi-line `python -c` / $(...) / sqlite3 -> Bash tool; Verb-Noun cmdlets / .Property access / $null -> PowerShell tool; a Windows-only binary missing from Git Bash PATH -> call it by full path or via python inside Bash rather than switching shells. Escalate to a PreToolUse dialect-lint hook (GATE-B scored once, covering BOTH this cluster and Bash::Exit_code_127) only if one new mismatch appears in .claude/state/failures-*.jsonl after this playbook lands.

## Apply-when

Before sending a shell command: if it contains a << heredoc, a `python -c` with newlines or nested quotes, $(...), or sqlite3 -> Bash tool. If it contains a Verb-Noun cmdlet (Get-Content, Select-Object, Select-String, Measure-Object), .Property member access, or $null -> PowerShell tool. If the tool you picked disagrees with the idiom, switch the tool, not the syntax.

## Related
- *hot* (not published) -- session cache; this playbook is surfaced in the consolidation digest
- [[bash-exit-code-1-playbook]]
- [[bash-exit-code-2-playbook]]
- [[read-unclassified-playbook]]

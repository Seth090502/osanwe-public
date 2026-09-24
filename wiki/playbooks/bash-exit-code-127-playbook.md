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

# Bash Exit_code_127 Playbook

## Pattern
Invariant: On this Windows machine the Claude Code Bash tool always runs through Git Bash (/usr/bin/bash), so any PowerShell cmdlet or 2>$null redirect emitted into a Bash call resolves to exit 127 "command not found" -- 11 of the 15 exit-127 records (73%) are exactly that against only 1 genuinely-missing binary, so exit-127 in this vault is a shell-dialect-confusion signal, not a tooling gap.

The 11 dialect records name Get-Content, Select-Object, Select-String, Measure-Object, Format-List, and Get-ScheduledTask; three also carry PowerShell's "$null: ambiguous redirect", doubly confirming the interpreter mix-up. The lone real gap is cargo (2026-05-26 env probe). This is the mirror image of PowerShell::Exit_code_1 (bash syntax pasted into PowerShell): one root cause -- forgetting that every Bash call on this box is Git Bash. Concentration, not diffusion: 10 of 15 records come from a single 2026-06-09 session (2ab43cce), 5 sessions total. PowerShell cmdlets last fired into Bash 2026-06-11 and are absent from all 20 sink files since, but no hook or ratified decision guards the Bash tool against dialect -- the silence is behavioral; the risk is dormant, not removed.

Confidence: 88% -- root cause unambiguous in 11/15 error strings and matched by the mirror PowerShell cluster; verified the silence across 20 post-6/11 sink files and confirmed no ratified fix exists; "coincidence not fix" is an inference about an absence, and 2 bare records are unclassifiable.

## Evidence
- 15 failures clustered on Bash::Exit_code_127
- Threshold cleared: >= 5 failures in cluster (observed 15).

## Counter-cases

- 2026-05-26 -- "cargo: command not found" from an env probe: a genuinely-absent binary, the only exit-127 record that is a real tooling gap (.claude/state/failures-2026-05-26.jsonl:2)
- 2026-06-20 -- eval syntax error on a Python re.compile(...) regex pasted into eval: Python source, neither a PS cmdlet nor a missing binary -- a distinct third sub-type (.claude/state/failures-2026-06-20.jsonl:44)
- 2026-06-06 -- the same PowerShell dialect confusion landed under exit-2, not 127 ("(Get-Content ... | Measure-Object -Line).Lines") -- the root cause is not exit-code-bound, so counting only exit-127 understates it (.claude/state/failures-2026-06-06.jsonl:8)

## Recommendation

Extend the existing Bash invariant at the AGENTS.md Tool-mechanics line ("Bash paths Unix-style (the vault root)") with an explicit dialect clause: the Bash tool is Git Bash -- emit POSIX only; never PowerShell cmdlets (Get-Content, Select-Object, Select-String, Measure-Object, Format-List, any Get-*/Set-* verb) or 2>$null; use cat/grep/sed/awk/wc and 2>/dev/null. If any post-fix sink file shows a PowerShell cmdlet in a Bash call again, escalate via /decide bash-dialect-scan-hook to a PreToolUse Bash hook that scans tool_input.command for those tokens -- one hook covers BOTH this cluster and the mirror PowerShell::Exit_code_1, so it is GATE-B-scored once.

## Apply-when

Before sending any Bash call on this machine, scan the pending command for PowerShell tokens -- Get-Content, Select-Object, Select-String, Measure-Object, Format-List, any Get-*/Set-* verb, or 2>$null. Any hit means imminent exit 127: rewrite in POSIX (cat/grep/sed/awk/wc -l, 2>/dev/null) before sending.

## Related
- hot -- session cache; this playbook is surfaced in the consolidation digest
- [[bash-exit-code-1-playbook]]
- [[bash-exit-code-2-playbook]]
- [[read-unclassified-playbook]]

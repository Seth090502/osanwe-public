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

# Bash Exit_code_2 Playbook

## Pattern
Invariant: In this vault a Bash-tool "Exit code 2" is an ad-hoc command-construction fault -- an unterminated quote in an inline heredoc or `python -c`, PowerShell cmdlet syntax handed to /usr/bin/bash, a backslash Windows path collapsed by the shell, or ls/grep run against a guessed nonexistent path -- and is never a vault pre-write GATE block, so it is fixed by re-composing the command for Git Bash, never by a CLAUDE_VAULT_* bypass env var.

The Bash tool executes Git Bash on Windows: multi-line commands with unescaped double quotes reach eval unterminated ("unexpected EOF while looking for matching" quote/backtick -- the single largest bucket, e.g. all of failures-2026-06-08.jsonl lines 37-85); PowerShell cmdlets abort with "syntax error near unexpected token"; backslash paths get word-split into C:`<VAULT_ROOT>`tools; GNU ls/grep exit 2 on any nonexistent path. The durable trap: 2 is ALSO the vault's hook fail-closed code (tools/pre-write-validator.py sys.exit(2) at lines 393, 421), but that fires only on the Write/Edit PreToolUse path -- the failure sinks hold zero Write/Edit exit-2 records and every cluster row is tool "Bash" -- so reading an exit-2 Bash result as a doctrine/GATE block and reaching for a bypass is always the wrong move.

Confidence: 88% -- sub-cause buckets and the not-a-hook-GATE clause are directly evidenced across 5 dates / ~90 of 159 records plus the validator source and a zero-count Write/Edit cross-check; residual uncertainty is the un-sampled remainder.

## Evidence
- 159 failures clustered on Bash::Exit_code_2
- Threshold cleared: >= 5 failures in cluster (observed 159).

## Counter-cases

- 2026-07-07 -- skeleton check-all harness exit-2 is an INTENTIONAL fail-signal, not a quoting error ("check.sh: expected exit 0, actual exit 2"); proximate cause still a Git-Bash env mismatch: bare `python` off the Git Bash PATH (.claude/state/failures-2026-07-07.jsonl:5)
- 2026-07-07 -- genesis GATE-B harness deliberately exiting 2 on "note not found ... gates-registry.md" -- a script's own fail-closed convention surfacing through Bash (.claude/state/failures-2026-07-07.jsonl:11)
- (searched: all dated failures-*.jsonl for Write/Edit/MultiEdit at exit 2 -> none found; searched the 5 highest-volume dates for any exit-2 Bash row a bypass env var would have resolved -> none found)

## Recommendation

Ratify a four-line Git Bash command-hygiene rule via /decide bash-git-command-hygiene and install it at the existing AGENTS.md anchor "Bash paths Unix-style (`<VAULT_ROOT>`)" (Data sources -> Tool mechanics line): (1) for any multi-line/quoted script write a scratchpad .py/.sh and run it, or single-quote the heredoc -- never inline unescaped double quotes; (2) forward-slash paths only; (3) never pipe PowerShell cmdlets through the Bash tool; (4) confirm a path with Glob/Read before ls/grep. Include the reader-facing sentence: an exit-2 Bash failure is NEVER a GATE block -- never respond with CLAUDE_VAULT_BYPASS_VALIDATOR or CLAUDE_VAULT_LAX_ORPHAN.

## Apply-when

A Bash result reads "Exit code 2" AND stderr contains any of: "unexpected EOF while looking for matching", "syntax error near unexpected token", a collapsed path like C:`<VAULT_ROOT>`..., or "cannot access ...: No such file or directory" -- re-compose the command per the hygiene rule; do not treat it as a hook GATE and do not bypass.

## Related
- *hot* (not published) -- session cache; this playbook is surfaced in the consolidation digest
- [[bash-exit-code-1-playbook]]
- [[read-unclassified-playbook]]
- [[webfetch-unclassified-playbook]]

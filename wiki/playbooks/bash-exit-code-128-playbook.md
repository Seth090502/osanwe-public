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

# Bash Exit_code_128 Playbook

## Pattern
Invariant: In this vault every Bash exit-128 is git aborting on an argument that does not resolve in the repo's actual posture -- a ref/rev/tag/path-at-rev that is not present, or a -C/cd target that is not a git repo -- so it is deterministic and argument-shaped, never transient and never a git defect. Falsifier: any exit-128 whose failing leg was a resolvable ref against an existing repo (a lock, merge, corruption, or network fatal), or the same command retried unchanged succeeding.

The dominant shape (9 of 15 records read; the miner counted 12 in-window) is a non-resolving revision: main / upstream / ahead-behind idioms fataling against the posture of the moment -- the vault is local-only with NO remote (decision-log.md:1305; sessions-log.md:2987), so origin/* and @{u} idioms never resolve, `main` did not resolve in the master-era records ("unknown revision" / "not a valid ref" / "Needed a single revision"), and the 2026-06 history rewrite invalidated old short-SHAs; posture has since flipped (main resolves today), which is itself the lesson -- branch posture shifts, so bare refs must be guarded, not assumed. The second shape (5 of 15) is -C/cd aimed at a sibling directory that is not a repo (.vault-substrate, cc-coach-sandbox, the vault root-local), several of them deliberate is-this-a-repo probes where 128 was the intended answer. The third (1 of 15) is a Windows backslash path collapsing the vault root to C:the vault root so the -C target does not exist. The identical-retry pair on 2026-05-30 (failures-2026-05-30.jsonl:14,15) reconfirms determinism: retrying an exit-128 unchanged reproduces it.

Confidence: 88% -- full-population read (15/15 records fit three argument-resolution shapes, zero contradicting); the local-only posture is independently ratified in decision-log.md:1305 + sessions-log.md:2987; residual is the master->main flip narrowing the dominant sub-case's examples without touching the ref-resolution invariant.

## Evidence
- 12 failures clustered on Bash::Exit_code_128
- Threshold cleared: >= 5 failures in cluster (observed 12).

## Counter-cases

- (none found that contradict the mechanism -- searched all 15 Exit code 128 records across .claude/state/failures-*.jsonl plus decision-log.md and sessions-log.md for a competing git-posture decision; no lock, merge-conflict, corruption, or network-shaped 128 exists in the corpus)
- Nearest strains, consistent with the invariant's not-always-a-bug clause: 2026-05-29 deliberate is-git-repo probes on external dirs where fatal was the intended answer (.claude/state/failures-2026-05-29.jsonl:23-25); 2026-06-03 "Vault untouched?" probe expecting not-a-repository to confirm artifacts live outside the vault (.claude/state/failures-2026-06-03.jsonl:6)

## Recommendation

Ratify /decide git-exit128-preflight-convention proposing a Git-preflight subsection for Atlas/sources/meta/ref-execution-discipline.md (canonical execution-discipline ref, AGENTS.md-linked; Atlas is human-write-only so the amendment rides ratification), four rules: (1) the repo is local-only with no remote -- origin/@{u}/ahead-behind idioms never resolve; branch posture has already flipped once (master-era sinks, main today) and the 2026-06 history rewrite invalidated old SHAs, so guard EVERY bare ref with git rev-parse --verify --quiet before use; (2) pass forward-slash paths (the vault root) to git -C and cd, never raw backslashes; (3) git -C `<sibling-dir>` returning 128 is the expected not-a-repo answer -- treat as data, not an error to escalate; (4) exit-128 is deterministic -- read the fatal line and fix the named argument, never retry unchanged. The same /decide can score a later lint in tools/bash-vault-gate.py (the Bash gate hook already on disk) for bare-main and backslash -C checks.

## Apply-when

Before any git command naming a branch/upstream/tag/short-SHA or passing a path to -C/cd: guard the ref with git rev-parse --verify --quiet first and use forward-slash paths. If a git leg already returned exit 128, do not retry unchanged -- the fatal line names the non-resolving ref or target to fix.

## Related
- hot -- session cache; this playbook is surfaced in the consolidation digest
- [[bash-exit-code-1-playbook]]
- [[bash-exit-code-2-playbook]]
- [[read-unclassified-playbook]]

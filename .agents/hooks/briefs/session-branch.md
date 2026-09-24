# Porting brief: session-branch (named branch required for file writes)

Current policy, 2026-09-12: ordinary work uses `main`; named feature branches remain
available when useful or requested. The previous main/master refusal and mandatory
timestamped session branches are retired. The executable acceptance command is
`python -B tools/test-router-contract.py BranchPolicy`, also registered in the hook manifest.

## Required behavior

Before a file-writing tool runs, allow any symbolic branch, including `main`,
`master`, and explicit feature branches. Refuse detached or unreadable HEAD with
blocking exit 2 and recovery guidance. The hook must never create or switch a
branch, stage, commit, stash, or otherwise move HEAD or refs.

Resolve the repository from the hook's own location, not the caller's working
directory or a hardcoded workspace. The reference at
`.claude/hooks/session-branch.sh` resides two directories below its repository.
An installation outside a Git repository is a silent no-op. Git or directory
resolution failures must not be converted into branch creation.

The hook is payload-independent. It requires Bash and Git on PATH and reads only
Git state. Allow is silent exit 0. Refusal names detached/unreadable HEAD and gives
a way to preserve the commit on a descriptive branch (`git switch -c
codex/describe-work`) or deliberately return to an existing branch (`git switch
main`). The agent chooses the appropriate recovery; the hook performs neither.

## Lifecycle and portability

Bind to blocking `pre-tool-use` for file-writing tools (Claude:
`Write|Edit|MultiEdit`); native equivalents are mapped in `.agents/hooks/README.md`.
If only a session-start assertion exists, check symbolic HEAD there and disclose
the weaker coverage: a later detach is not intercepted. Shell-originated writes
may bypass file-tool hooks; all harnesses must also follow the canonical Git rule.

The configured `.claude/hooks/auto-commit.sh` remains a compatibility no-op.
Per-edit commits and their commit-hook bypass were retired. Agents prepare
meaningful, validated milestone commits manually on main or explicit feature
branches, preserving the normal precommit checks. This hook pair does not certify
that validation occurred, trigger publication, or grant remote-write authority.

## Acceptance boundaries

Tests copy both hooks into disposable repositories and invoke them from an
unrelated directory. They check main and feature branches, detached refusal,
recovery text, unchanged HEAD/refs/index, and no automatic staging or commits.
The test fixtures have isolated Git configuration and no production callbacks.
No production hook invocation, checkout, commit, service or remote is needed.

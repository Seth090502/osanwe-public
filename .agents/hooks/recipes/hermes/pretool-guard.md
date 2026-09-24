# Hermes recipe -- harness-neutral enforcement via hooks.pre_tool_call (OSANWE-V2 ADR-04)

Status: RECIPE (cold-porting brief; verification UNRUN until a conformance record
exists -- same discipline as the OpenCode recipe pre-execution).

## What Hermes can enforce natively

`hooks.pre_tool_call` in the profile's config.yaml runs before each tool call and
BLOCKS when the hook command exits 2 (or emits {"action":"block"}). With
`fail_closed: true`, a broken guard fails shut rather than open.

## Guard: mirror of .claude/hooks/guard-paths.sh + tools/precommit.py rules

Scope the trigger to write-capable tools only:

```yaml
hooks:
  pre_tool_call:
    - match:
        tools: [write_file, patch, terminal]
      run: python <VAULT_ROOT>/tools/precommit.py --pretool
      fail_closed: true
```

(VERIFY exact key names against docs/user-guide/features/hooks for the installed
version; the mission's Phase-0 probe could not confirm payload shape.)

## Implementation note

`tools/precommit.py` gains `--pretool`: read the tool-call JSON from stdin, map
(write_file|patch|terminal) -> affected paths, and evaluate R1-R6 on the PROPOSED
content using the same functions the git cage uses. Reuse over reinvention: one
rule source, two carriers (git pre-commit + Hermes pre-tool), exactly as
append-only-check.py relates to cage R2.

## What stays instruction-only under Hermes

the broker order tools are absent by design (registry default-refuse) so D-SEC-1
needs no hook; D-SEC-2 remains documented instruction (no mechanical carrier off
claude.ai); session-start surface substitutes BOOTSTRAP.md.

## Executable test

`python tools/test-precommit.py` (14 cases) validates every rule the recipe
mirrors. The --pretool stdin adapter gets its own failing-test case at
implementation time.

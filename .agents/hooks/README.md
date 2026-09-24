# Hook event mapping -- abstract lifecycle -> native harness events (D6)

Sources: Phase-0 worker reports ONLY (`.agents/migration/research/phase0-*.md`; row IDs
in harness-matrix.md). Claims here are documentation-derived; a recipe is UNRUN until a
conformance record exists (docs/compatibility.md verification table).

| Abstract lifecycle (manifest) | Claude Code [CC-5] | Codex CLI [CX-5] | OpenCode [OC-5] | Goose [GS-5] | Crush [CR-5] | Cline [CL-6] |
|---|---|---|---|---|---|---|
| session-start | SessionStart | session_start | plugin event | session events (11-event set) | (none -- PreToolUse only) | hook config |
| pre-tool-use (blocking) | PreToolUse, exit 2 blocks | pre_tool_use (11-event set; blocking) | plugin throw / permission.ask deny | pre-tool events, exit-2/decision-block | PreToolUse: exit 2/49, JSON allow/deny/updated_input, pre-permission | mode: blocking + fail_closed |
| post-tool-use | PostToolUse | post_tool_use | plugin event | post-tool events | (not intercepted) | hook config |
| prompt-submit | UserPromptSubmit | prompt events | plugin event | prompt events | (none) | hook config |
| session-end | Stop | session_end | plugin event | session events | (none) | hook config |
| compaction | PreCompact / PostCompact | (n/a) | (n/a) | (n/a) | (n/a) | (n/a) |
| subagent lifecycle | SubagentStart/Stop | (n/a) | (n/a) | (n/a) | sub-agent calls NOT intercepted [CR-5] | subagents experimental |

Caveats that bind recipe authors:
- Goose blocking-hook presence in the SHIPPED v1.45.0 is UNVERIFIED (doc+PR-sourced) -- verify in release before relying on it [GS-5, unverified-cells].
- Crush intercepts PreToolUse ONLY and does not intercept sub-agent tool calls -- a Crush recipe cannot reproduce PostToolUse checkers; state the loss.
- Cline hooks-on-Windows behavior is UNVERIFIED (unverified-cells register).
- Pi has extensions with tool_call block:true + arg mutation [PI-5] but NO MCP; Pi recipes only make sense for filesystem gates.
- The pretrade-token-gate hook is portable: NO categorically (see manifest entry) -- no recipe exists for it anywhere, by design.

Recipe shape (Tier-1 briefs/): WHAT the gate must guarantee (from the manifest intent +
decision_logic), the reference implementation path, the harness event to bind per the
table above, and the pre-authored `test:` the port must pass. Briefs are written COLD
(author did not see the manifest's test blocks) -- the executable test, not the brief
prose, is the acceptance criterion. `briefs/control-vague.md` is a deliberately vague
CONTROL brief kept to prove the porting-proof criterion discriminates (DoD 10).

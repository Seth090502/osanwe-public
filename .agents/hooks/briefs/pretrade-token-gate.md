# Porting brief: pretrade-token-gate -- portable: NO. DO NOT PORT. DO NOT APPROXIMATE.

COLD BRIEF -- written without sight of the manifest test blocks. Criticality: SAFETY-CRITICAL (highest
in the system). Portability verdict: **NO**, categorically -- no recipe exists for this hook in any
harness, BY DESIGN. This brief explains WHY it cannot travel and what replaces it off-Claude.
(`.codex/hooks.json` does register a byte-identical copy of the hook. It is inert: the Codex configuration
this repository generates surfaces no broker server for it to match.)

## STOP: what "portable: NO" means here

A partial port of this gate is WORSE THAN NO PORT. Its security rests on one primitive that does not
exist outside Claude Code, and any substitute for it is an authorization oracle an attacker can drive.
If you are in Codex CLI / OpenCode / Goose / Crush / Cline and find yourself writing a hook that
authorizes a brokerage order, STOP -- you are building the vulnerability this verdict prevents.

The categorical mitigation off-Claude is structural, not procedural: **non-Claude harnesses are never
given brokerage order tools at all.** They are not denied-then-guarded; they are NOT SURFACED.
[Fable review 2026-08-10: as of the S2.5 registry, the generated `.codex/config.toml` OMITS the broker server ENTIRELY (default-refuse; `.agents/mcp/servers.json`) until a live enabled_tools
probe proves the filter -- only then is a read-only allowlist generated verbatim from the registry's
34-tool read set.] A tool that cannot be called needs no gate. Reproduce THAT -- omission first,
then a proven read-only allowlist at MCP registration. That is the port.

That holds for the configuration this repository generates. It does not hold for connectors attached to
an account rather than a repository: on this machine the Codex app's own broker connector listed order
tools in its sessions (most recently 2026-09-20; no call was made), outside anything this repository
controls. Omission has to be done where the connector is attached.

## (a) What the gate is meant to guarantee on Claude Code, and where it does not (context only)

It is the SECOND stair of a two-stair action staircase (stair one is the permission-layer deny on the
order tools). Assuming stair one has been lifted, it is meant to refuse an equity order unless ALL FOUR
hold:

1. HUMAN AUTHORIZATION, ORDER-BOUND: the literal phrase `EXECUTE ORDER <order_id>` appears in the
   LATEST GENUINE human turn -- not "somewhere in the conversation", and for that specific order id.
2. SIGNED PASS: an HMAC-signed `gate-pass-<order_id>.json` exists with `gate_result == PASS`, issued
   only by the separate pretrade gate CLI on a clean evaluation. A blocked order never yields a pass.
3. FRESH AND UNUSED: within TTL (default 900s), not timestamped more than 300s in the future, and not
   already consumed.
4. SAME ORDER: a canonical hash of the tool arguments about to execute matches the hash recorded in the
   pass -- defeating stage-A-approve / execute-B substitution and TOCTOU.

The token is consumed LAST, atomically (`O_EXCL` marker file); a lost race blocks. Every error path,
unparseable payload, unknown shape, or exception BLOCKS (fail-closed), including a top-level backstop --
except a failure to import its library, which happens before the backstop and exits 1, which the harness
treats as "proceed" (see (e)).

**Condition 1 does not currently hold (2026-09-22).** Three rounds of independent adversarial review
drove the real hook end to end with synthetic transcripts and payloads, and each round found shapes that
made it authorise an equity-order call. No broker call was made and no order was placed. Four patches were
written and none shipped, the fourth because it was a regression on the third. Four defects are open:

- **D70** -- machine-written entries (compaction summaries, subagent turns and hand-backs, task
  notifications, slash-command invocation records, bash-mode and local-command output, headless and
  background prompts) are read as the person;
- **D72** -- the authorization names an `order_id` the model chooses, not the order's contents, and the
  gate re-signs a pass for the same id against a different order;
- **D73** -- the authorising phrase never expires: no transcript `timestamp` is read anywhere, so the
  900s TTL protects the pass and not the approval;
- **D74** -- the first id in a turn wins, and a phrase can be assembled across the join between two text
  blocks. Two further findings -- an unreadable `origin` authorising, and a falsy-but-present
  `isSidechain` being accepted -- were demonstrated against the retired patch branch that read those
  fields; `main` reads neither, so it accepts both shapes by never looking at them.

Conditions 2, 3 and 4 hold. A replacement for condition 1 -- the person types the order's parameters
rather than an id, the order must be the model's first act after the phrase, and the phrase carries its own
lifetime -- exists as a design in the owner's audit notes, outside this repository. Fresh reviewers have
attacked its drafts before any code existed, and each round found holes that were fixed on paper. **No
implementation exists, and until a reviewed one is merged by hand nothing lifts the permission deny
list.** Two controls stand in front of this server's order tools today: that deny list, and this hook,
which refuses every tool of the robinhood-trading server except its recognised read tools and three
equity-order names -- the only names that reach the four conditions. None of those three names is on the
broker's live surface (`.agents/mcp/servers.json`, re-verified 2026-09-21); the live order tools, such as
`place_advanced_order` and `place_crypto_order`, fall to the unrecognised-name refusal and are denied as
well. Condition 1's defects become reachable only if a name that reaches the four conditions is callable --
a live order tool added to the equity-order list, or a legacy name the broker restores -- and its deny
entry is removed. The refusal message for an unrecognised name invites adding it to the read-tool list and
the registry after review; a name added there is allowed with no condition checked, so no write tool may
ever be added to that list. The regression suite `tools/test-pretrade-transcript-provenance.py` prints
every open shape against its defect id on every run.

## (b) Why it cannot travel: the transcript-parsing injection defense

Condition 1 is the load-bearing one. It is implemented by walking the Claude Code session transcript
JSONL BACKWARDS and returning the text of the most recent turn satisfying ALL of: `type == "user"` and
`message.role == "user"`; not a meta turn (`isMeta` true is skipped); not a tool-result carrier (a
sibling `toolUseResult` key is skipped); if content is a list, it contains a `text` block and NO
`tool_result` block; unknown shapes are skipped (fail-closed) and any error returns None -> BLOCK.

**That is a denylist of three shapes, and it accepts everything else** -- which is how every entry kind
listed under D70 above reaches it as though the person had typed it. The transcript does carry per-entry
provenance fields (`promptSource`, `origin`, `entrypoint`, `sessionKind`, `isSidechain`,
`isCompactSummary`), and this filter reads none of them. They are not a complete answer by themselves.
They are sparse: of about 8,400 user entries in the local corpus on 2026-09-22 that carry text rather than
tool results, `promptSource` was on about 2,930 and `origin` on about 2,220. And some machine-written
shapes carry none of them: bash-mode output, slash-command invocation records (`<command-name>`,
`<command-args>`) and local-command output are marked only by tags in their text. (Command and skill
expansions carry `isMeta: true`, and hook context is written as separate attachment entries; the filter
already skips both.)

The portability argument below is still right, and it is the reason this brief says NO. What changed is
only the claim about what the filter achieves with that record today. A web page, a fetched file, an MCP
response or a subagent report can contain the string `EXECUTE ORDER ABC123`, and they arrive in the
transcript as user-ROLE content. The model's own output is assistant-role when written, but it returns
as user-role content inside a compaction summary, in any tool result that echoes it, and in a turn where
the person pastes it back (D74). Distinguishing "the human typed it" from
"something the agent read said it" needs a per-turn provenance record of that fidelity, and without one
the phrase check degrades into: any content the agent has ever ingested can authorize a real-money
trade. No other harness exposes an equivalent per-turn human-vs-injected provenance record;
reconstructing one from a chat log, a `--last-message` file, or a model self-report replaces a harness
record with a guess. Hence the NO verdict: the gate's strength is not its HMAC, TTL, or hash-matching
(all portable) but the Claude-bound human turn -- once condition 1 actually reads it correctly.

## (c) Where it binds on Claude Code (do NOT recreate elsewhere)

`pre-tool-use (blocking)`, matcher `mcp__robinhood-trading__.*` -- **every tool on the broker server**,
not a named subset. Reference: `.claude/hooks/pretrade-token-gate.py`; primitives in
`tools/pretrade_lib.py`; state under `.claude/state/pretrade/` (`hmac.key` mode 0600, `passes/`,
`consumed/`; `OSANWE_PRETRADE_STATE_DIR` overrides for tests). The `.agents/hooks/README.md` event table
has NO row for this gate on purpose.

It binds only where this project's settings load and only for a server with this name. A broker server
under another name, or any session started outside this repository, is not routed here: on 2026-09-22 the
claude.ai broker connector was loading its order tools into sessions outside the vault with no deny
rule and no hook covering them (no call was ever made). It has been denied at user scope, server-wide, since
that day; coverage by broker rather than by server name is part of the stair-1 redesign.

## (d) Input shape (for auditors, not for porters)

Stdin JSON with `tool_name`, `tool_input`, and `transcript_path`. The gate allows the recognised broker
read tools, refuses option-order, mutator and **unrecognised** broker tool names outright -- a tool the
connector adds tomorrow is blocked by being new -- and runs the four conditions on equity-order tools.
Block = exit 2 + stderr reason.

## (e) Non-goals and known residuals

- The option-order and mutator block branches are reachable by name: the matcher routes every tool of
  this server here, so a call named `place_option_order` or `exercise_option` would hit them. Neither name
  is on the live surface (`servers.json`, 2026-09-21); every live write tool hits the unrecognised-name
  refusal instead. An earlier version of this brief
  called them dead code because the matcher named exactly the three equity-order tools from 2026-07-05
  until commit `d368ce68` widened it to `.*` on 2026-08-10, 39 minutes before this brief was first
  committed. The claim was stale when written, and the hook's own docstring still repeats it.
- The hook validates AUTHORIZATION, not trade quality: ceilings, R/R, the sleep gate, and book
  freshness live in the pretrade gate CLI (`briefs/pretrade-gate-cli.md`), which DOES port -- but
  off-Claude it is analysis and dry-run tooling only, never an authorization path.
- The `EXECUTE ORDER` phrase requirement is ALSO an instruction-level rule (AGENTS.md D-SEC-1), but
  instructions are not enforcement and never substitute for the structural mitigation. Do not
  "temporarily" port this for a demo: there is no non-production instance of a gate whose failure mode
  is an unauthorized real-money order.
- The signing key, the pass directory and the transcript are ordinary files the agent's own account can
  read and write, and no write guard covers them for any tool: `guard-paths.sh` has no rule for
  `.claude/state/` or the transcript directory, and it fires only on Write, Edit and MultiEdit. The same
  holds for `tools/pretrade_lib.py` and `tools/pretrade_gate.py`; of the gate's files only the hook itself
  is on the protected-config list. Against an agent induced to write to these files the gate is no defence,
  and neither is the deny list, which sits in project and user settings files the same account can
  rewrite; moving it to managed settings does not help where the
  agent's account can elevate without a prompt. The only
  control wholly outside that reach is broker-side: the broker lets an agent trade only an account designated
  for agent use, as its own tool descriptions state (not verified with a broker call).
- The hook is an ordinary command hook, and the harness documents ways past one. It imports
  `pretrade_lib` at module level, outside its backstop, and a hook that exits 1 -- as an import failure
  does -- or that times out (this one's budget is 10 s) does not block the call. Matching hooks run in
  parallel, and another hook's `updatedInput` replaces the input after this one has checked it.
  `disableAllHooks` in a project, local or `--settings` file switches hooks off. Only a managed hook under
  `allowManagedHooksOnly` is out of reach of the last two (plugins that managed settings force-enable are
  exempt from that setting), and on this machine managed settings are
  themselves within the agent's reach until UAC prompts. (Found by the third design review of the stair-1
  replacement, 2026-09-22.)

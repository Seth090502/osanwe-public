# Round 4: mode-3 latency -- measured causes, three rejected hypotheses, one large win

Follows `bakeoff-round3-qwen38-2026-08-14.md`. Scope: why mode 3 was slow in the vault and
fast in a bare directory, and what actually fixed it. Plan:
`~/.claude/plans/5-12-minutes-is-insane-shimmering-shannon.md`.

## Headline

| metric | baseline | + tool diet | + hook gates | change |
|---|---|---|---|---|
| vault turn-1 prompt | 55,951 tok | 19,379 | **16,363** | **-71%** |
| vault turn-2 prompt | 58,728 tok | 21,597 | **18,531** | **-68%** |
| turn-1 prefill | 21.4 s | 5.8 s | **4.9 s** | **-77%** |
| 3-turn task, wall clock | 62.5 s | 27.4 s | **20.4 s** | -67% (noisy, see below) |
| MTP draft acceptance | 0.641 mean | -- | **0.756 mean** | +18% |

Prompt tokens and prefill are the trustworthy numbers. Wall clock is indicative only.

Both runs returned the correct answer and exited 0. The "5-12 minutes" figure in the round-3
record was **never properly timed** -- it came from polling loops with sleeps, taken while
proxies were being restarted mid-run. The first `time`-measured vault run was 62.5 s. That
correction matters more than the improvement: the problem was real but roughly 5x smaller
than reported.

## The measurement that ended the guessing

Three hypotheses were proposed and all three were WRONG. Each was killed by measurement, not
argument:

| # | hypothesis | verdict | evidence |
|---|---|---|---|
| 1 | hook EXECUTION time | REJECTED (but see correction) | python hooks 0.02-3.46 s; 14 per-tool-call spawns = 0.24 s |
| 2 | hook TOKEN injection | REJECTED (but see correction) | not the dominant term -- `tools` is 10x larger |
| 3 | `LLAMA_ARG_CACHE_RAM` 8 GB ceiling | REJECTED | set to `-1`, restarted: turn 2 still re-evaluated 58,728 tok |
| 4 | normalizer hoist placement | REJECTED | tail placement, controlled A/B: 55,935 / 58,760 -- unchanged |

The answer came from capturing the actual request bodies and diffing turn 1 against turn 2
(`scratchpad/capture2.py`, chained in front of the normalizer):

```
component   turn 1      turn 2      identical?
system         5,136 B     5,136 B   SAME
tools        153,822 B   153,822 B   SAME
messages      70,826 B    79,699 B   DIFFERS
```

**`tools` is 153,822 bytes -- ~42,700 tokens, the single largest component of a ~56,000-token
prompt.** Larger than the entire vault instruction surface, which is what every earlier
hypothesis had been chasing.

Breakdown of the 116 tool definitions:

| group | count | bytes | ~tokens |
|---|---|---|---|
| MCP total | 86 | 71,178 | 19,771 |
| -- robinhood-trading | 34 | 38,283 | 10,634 |
| -- openinsider | 16 | 14,410 | 4,002 |
| -- claudewatch | 32 | 13,188 | 3,663 |
| -- fred | 3 | 4,768 | 1,324 |
| -- vault-search | 1 | 529 | 146 |
| built-in total | 30 | 82,412 | 22,892 |
| -- `Workflow` ALONE | 1 | **21,870** | **6,075** |
| -- DesignSync | 1 | 9,324 | 2,590 |

This also explains the vault-vs-bare-directory gap with no theory required: `.mcp.json` is
project-scoped, so a bare directory loads none of those 86 MCP tools.

## The fix (shipped)

`tools/claude-launcher.ps1`, mode 3 only:

- `--strict-mcp-config` with no `--mcp-config` -> loads ZERO MCP servers (~19,771 tok).
- `--disallowedTools` covering 20 orchestration/scheduling/worktree/MCP-resource built-ins
  (~18,560 tok): Workflow, DesignSync, Agent, ReportFindings, Cron*, ScheduleWakeup,
  Enter/ExitWorktree, Task*, SendMessage, *McpResource*.
- Kept deliberately: Read Write Edit Bash Glob Grep Skill WebFetch WebSearch NotebookEdit.

Modes 1 and 2 are untouched. Revert = delete the two flags.

## Sampling profile (shipped)

Qwen publishes two profiles for this architecture; the Modelfile ships a hybrid matching
neither -- temp 1.0 from the TEXT profile with presence_penalty 0.0 from the CODING profile,
dropping the `presence_penalty 1.5` that makes temp 1.0 safe against runaway repetition.
Mode 3 is coding work, and nothing in the vault set sampling for it, so it ran raw at
temp 1.0.

`tools/mode3-normalize-proxy.py` now injects `temperature 0.6` + `top_p 0.95`
(`MODE3_TEMP=off` disables; `retuned` counter in `/__normalizer/health` proves it fired).

Second-order effect, predicted then confirmed: MTP draft acceptance is temperature-dependent.

```
temp 1.0:  0.54310, 0.75000, 0.63095   mean 0.641
temp 0.6:  0.67188, 0.77703, 0.81944   mean 0.756
```

+18% acceptance means more tokens per forward pass, i.e. a decode-speed gain on top of the
quality fix. Sample of 3 each -- directionally clear, not a rigorous benchmark.

## CORRECTION to hypotheses 1 and 2 -- my own measurement was invalid

The first pass timed the bash hooks with a bare `bash`, which on this box resolves to **WSL
bash** (System32, first on PATH) -- a trap this vault already learned once. WSL2 cannot start
here at all:

```
$ bash .claude/hooks/stop-pr-and-audit.sh
WSL2 is unable to start since virtualization is not enabled on this machine.
```

So those runs measured the WSL failure message, not the hooks. The tell was visible and I
missed it: `session-start.sh` and `session-integrity-check.sh` both reported **exactly
916 bytes**, which is the UTF-16 error string, not two different hooks agreeing.

Re-measured with Git Bash (`Git\bin\bash.exe`):

| hook | first (invalid) | corrected |
|---|---|---|
| session-start.sh | 0.043 s / 916 B | **1.98 s / 15,716 B (~4,366 tok)** |
| session-integrity-check.sh | 0.027 s / 916 B | 0.62 s / 59 B |
| stop-pr-and-audit.sh | 0.03 s | **3.82 s** |

Corrected totals: SessionStart injects roughly **4,400-5,000 tokens** (not 767) and costs
~6 s including `vault-score-check.py` at 3.46 s; the Stop hook adds 3.82 s at session end.

**The conclusion still holds** -- `tools` at ~42,700 tokens is still ~10x the hook injection,
so tool pruning was still the right fix. But the numbers in hypothesis 2 were wrong by 5.7x
and are corrected here rather than left standing.

**Rule for this box, now twice-learned: never invoke a hook or script with bare `bash` from
a subprocess. Use `Git\bin\bash.exe` explicitly.**

## WSL2 is BLOCKED at the BIOS, not merely deferred

Discovered by the same error. Plan item W6 (SGLang/vLLM under WSL2) assumed WSL2 was present
and merely stopped -- `wsl --list --verbose` does report `Ubuntu ... Stopped ... 2`. It cannot
actually start: **hardware virtualization is disabled in firmware.** Enabling it is a BIOS
change and a reboot, i.e. operator action, before any WSL2-based work is even possible.

## Still UNRESOLVED (do not cite a cause)

1. **Prefix-cache reuse is broken in the vault and works in a bare directory.** Bare: 24,071
   -> 663 -> 663 tokens per turn. Vault: full re-evaluation every turn. `system` and `tools`
   are byte-identical across turns, so the divergence is inside `messages`. Located it to
   `messages[1]`: a 44,934-byte system message from Claude Code whose **text content is
   byte-identical (44,360 chars)** -- the 81-byte delta is `cache_control` metadata only.
   Why identical rendered text does not reuse is NOT explained. Both normalizer placements
   and `CACHE_RAM=-1` were ruled out.
2. **Multi-minute post-generation delay.** `all slots are idle` with the final task released,
   while the session sits before exiting. Reproduced across many runs. Two attempted causes
   (tail placement, SSE read buffering) were both disproven. Root cause not established.

Fixing (1) is the largest remaining win available: it would take turn 2+ from ~21,500 tokens
to a few hundred.

## Second session (2026-08-15, loose ends + remaining items)

**Shipped and verified:**

| item | change | proof |
|---|---|---|
| rollback trap | `cmd_rollback` now verifies the target is installed before repointing the lane; fails closed, exits 3, leaves SSOT untouched. Does NOT fail when the daemon is unreachable -- rollback is an emergency path. | live run refused `muse-glimmer:latest`, listed installed tags, `model` unchanged |
| keep-alive (E2) | `OLLAMA_KEEP_ALIVE=8h` in lane-arm.ps1 -- ambient HKLM was 30m, so idle sessions paid an 18 GB cold reload | log `OLLAMA_KEEP_ALIVE:8h0m0s`; `ollama ps` "8 hours from now" |
| slot pin (W4) | `OLLAMA_NUM_PARALLEL` 2 -> **1**, matching what Ollama actually serves | log `-np 1` |
| thinking off (E1) | **SHIPPED THEN REVERTED -- see below** | rationale disproven by measurement |
| `CACHE_RAM` removed | unproven knob deleted from lane-arm.ps1 | disproven above |

**Thinking control -- the shape matters.** Probed against `/v1/messages`:

```
no control                        -> content ['thinking','text']
{"think": false}      (Ollama)    -> content ['thinking','text']   IGNORED
{"thinking":{"type":"disabled"}}  -> content ['text']              WORKS
```

Also: Claude Code always sends `{"type":"adaptive","display":"omitted"}`, so a
`if "thinking" not in body` guard silently never fires. It must OVERRIDE. First
implementation had exactly that bug (`think_off` stayed 0) and was caught by the counter.

**REVERSAL -- thinking-off (E1) was shipped on a wrong premise and has been reverted.**
The argument was that thinking tokens are pure decode latency. Measured on one identical
arithmetic task, all four settings answered correctly, but:

| thinking mode | thinking chars | TOTAL output tokens |
|---|---|---|
| `{"type":"adaptive"}` (Claude Code default) | 193 | **192** |
| `{"type":"disabled"}` (what shipped) | 0 | **366** |
| `{"type":"enabled","budget_tokens":512}` | 206 | 255 |
| `{"type":"enabled","budget_tokens":2048}` | 199 | 176 |

Disabling nearly DOUBLED total output: the model simply reasons in the visible answer
instead. Adaptive was the cheapest run AND is what Claude Code already sends, so the correct
action is to not override it. Default is now `MODE3_THINK=on` (no override); the switch
remains for re-testing. Single-sample per arm -- the 192-vs-366 gap and the mechanism are
clear, but this is not a rigorous benchmark.

Also established: **`budget_tokens` is INERT** (512 and 2048 both produce ~200 thinking
chars), so a graduated "medium thinking" dial does not exist for this model on Ollama -- it
self-regulates. And Ollama's own `{"think": false}` is silently ignored on `/v1/messages`;
only the Anthropic `{"thinking":{"type":"disabled"}}` shape has any effect.

**PROVEN UNREACHABLE -- quantization above Q4 (BF16 / q8_0 / mxfp8).** Measured against
32,607 MiB total with ~800 MiB idle desktop use, i.e. ~31,807 MiB available. Current
q4_K_M runs 18,432 MiB of weights and 29,867 MiB total at ctx 262144, implying ~11,435 MiB
of KV + compute buffers:

| tag | weights | headroom after weights | verdict |
|---|---|---|---|
| q4_K_M / **nvfp4** | 18,432 MiB | +13,375 MiB | FITS |
| q8_0 | 30,720 MiB | +1,087 MiB | no room for KV |
| mxfp8 | 32,768 MiB | -961 MiB | does not fit |
| bf16 | 57,344 MiB | -25,537 MiB | does not fit |

BF16 would need ~25 GB resident in system RAM. At DDR5-6000 dual channel (~96 GB/s) that is
0.26 s/token, a **~3.8 tok/s** floor against 137 tok/s today -- roughly 36x slower. q8_0
technically loads but leaves ~1 GiB for a KV cache that currently needs 11 GiB, so it would
spill. **On a single 32 GiB card, Q4-class is the only tier that leaves a usable context
window.** The real quality upgrade at this footprint is `qwen3.8:27b-nvfp4` -- same 18 GB,
better fidelity per bit than a k-quant, plus the +43-68% prefill -- still gated behind the
harder acceptance suite.

**PROVEN UNREACHABLE -- batch size (W1.4).** `LLAMA_ARG_BATCH`/`LLAMA_ARG_UBATCH` = 2048 were
armed and the server still reported `n_batch = 512 / n_ubatch = 512`. Ollama passes
`-b 512 -ub 512` on the llama-server command line and llama.cpp's command line beats its env.
Raising the physical batch -- the direct lever on prefill -- requires driving `llama-server`
directly, at the cost of Ollama's model management, `--use` swapping, the SSOT integration
and the `/v1/messages` endpoint the normalizer needs. Not taken. Do not re-run this test.

**WALL CLOCK IS NOT A RELIABLE METRIC HERE.** Near-identical 3-turn tasks measured **27.4 s**
and **2 m 38 s**. Prompt-token counts and draft-acceptance are stable and attributable; wall
clock is not, because the unresolved post-generation delay swamps it. The headline table at
the top of this record should be read as: **prompt size is the solid result (-65%), wall
clock is indicative only.** Eliminated as causes of the delay so far: hook execution, the
Stop hook (3.82 s), vault-audit (0.02 s), proxy SSE buffering, normalizer placement,
`CACHE_RAM`. Not solved.

## SessionStart hook gating (W2, shipped)

The 44,360-char block at `messages[1]` turned out to be **entirely SessionStart +
UserPromptSubmit hook output** -- open-loops digest, a private file, hot.md smart-emit,
vault-audit line, semantic vault context. The CLAUDE.md -> AGENTS.md chain is NOT in it
(`CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` already suppresses it), so the planned `BOOTSTRAP.md`
swap is MOOT -- there was nothing to swap.

Gated on `CLAUDE_LANE_MODE=local`, verified three ways each (unset / local / sub):

| hook | modes 1-2 | mode 3 |
|---|---|---|
| `tools/session-start.sh` | 15,611 B | **158 B** |
| `.claude/hooks/inject-a private file.py` | 4,815 B | **105 B** |
| `.claude/hooks/semantic-context-inject.py` | 2,081 B (1.57 s) | **0 B** |

~22,244 bytes (~6,180 tok) suppressed for mode 3; modes 1 and 2 byte-for-byte unchanged
(`sub` measured identical to unset).

**Side effects preserved.** `session-start.sh` also creates today's daily note and carries
forward unchecked commitments -- modes 1/2 depend on those. The gate suppresses only the
final `echo`, after all side effects have run. Gating the whole script would have silently
broken daily-note creation.

NOT gated, deliberately: `open-loops.py` (932 B) is dual-use -- the same entrypoint is the
operator's CLI, so a lane-mode early-exit would break it inside a mode-3 session for 258
tokens of gain. `vault-score-check.py` emits only 418 B (but costs 3.37 s; time, not tokens).

## Not done from the plan

`LLAMA_ARG_CACHE_RAM=-1` is left in `tools/lane-arm.ps1` but is **unproven** -- it did not
fix what it was added for. Remove it or justify it on other grounds. Batch sizing
(`LLAMA_ARG_UBATCH`), NVFP4 (`qwen3.8:27b-nvfp4`), the harder acceptance suite, thinking-off
(E1), keep-alive (E2), prefix pre-warm (E3), and the vision-projector drop (E4) are all
untouched.

`python .agents/scripts/checkall.py` -> ALL GREEN. `ollama ps` -> `100% GPU`, ctx 262144.

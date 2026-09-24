# Round 5: spill guard shipped, draft-cache lever rejected (2026-08-15)

Continues `bakeoff-round4-mode3-latency-2026-08-15.md`. Plan:
`~/.claude/plans/5-12-minutes-is-insane-shimmering-shannon.md`.

STATUS: WS1 SHIPPED. WS1b-L2 MEASURED AND REJECTED. WS2a / WS3 / WS1b-L1 / WS4 (NVFP4) /
WS5 / WS6 / WS7 NOT STARTED -- see "Remaining" at the end.

## WS1 -- lane-guard, VRAM spill watchdog (SHIPPED)

Gate: `wiki/research/gates/gate-b-lane-guard-2026-08-15.md`, BUILD-JUSTIFIED (rule 2),
`--check` PASS. Built because the operator chose to KEEP ctx 262144 and be warned rather than
shrink the window, leaving ~1,485 MiB of headroom on a 32,607 MiB card.

`tools/lane-guard.ps1` polls `GET /api/ps` every 30 s and classifies:

| state | condition |
|---|---|
| SPILLED | `size_vram / size < 0.999` -- model partly on CPU |
| DEGRADED | `-Canary` only: measured decode below the floor |
| IMMINENT | fully resident but free VRAM < 1,200 MiB |
| UNKNOWN | free VRAM unreadable -- deliberately NOT "OK" |
| OK / IDLE / DAEMON-DOWN | -- |

### Verified

```
$ pwsh -File tools/lane-guard.ps1 -Once
lane-guard: OK -- qwen3.8:27b  17684/17684 MiB on GPU (100.0%)  1533 MiB free

$ ... -Once -ImminentFreeMiB 2000        # threshold above actual free
lane-guard: IMMINENT -- qwen3.8:27b  17684/17684 MiB on GPU (100.0%)  1486 MiB free
```

Debounce, from the poll trace (`-LogPath`), sustained IMMINENT at 5 s interval:

```
05:05:13 state=IMMINENT alerted=False :: ... 1484 MiB free
05:05:19 state=IMMINENT alerted=True  :: ... 1479 MiB free
05:05:24 state=IMMINENT alerted=True  :: ... 1479 MiB free
   ... 7 polls total, latch holds ...
RESULT  watchdogs=1  alertwindows=1   (expect 1 and 1)
```

Singleton, after FIVE rapid `lane-arm.ps1` invocations: exactly one watchdog process.

### Design decisions, each forced by a specific failure mode

1. **UNKNOWN is not OK.** The poll loop clears the debounce latch on OK. Folding an
   unreadable `nvidia-smi` into OK would silently re-arm the alert and re-fire next poll,
   turning one episode into a stream of popups. An inconclusive reading now changes nothing.
2. **Non-activating alert window.** Pulling the operator out of a fullscreen application to
   report that it is slowing something down is worse than the condition. Never calls
   `SetForegroundWindow`. Honest limit stated in-file: under borderless-windowed some shells
   may still raise it.
3. **Exclusive file lock for the singleton**, not a pidfile (check-then-write is not atomic)
   and not a named Mutex (a .NET Mutex is thread-owned; PowerShell does not guarantee the
   script body stays on one thread).
4. **Documented blind spot.** `size_vram` is Ollama's ALLOCATION at load, so Windows WDDM
   paging is invisible to it. IMMINENT is the cheap precursor; `--canary` is the true detector
   and is opt-in because it costs GPU time on a card this tight.

### CORRECTION -- three "singleton failures" were my instrument, not the code

The pidfile and Mutex designs each appeared to fail a live test showing **2 watchdogs** from
rapid arms. Both diagnoses were WRONG. The counting command was
`Get-CimInstance ... CommandLine -like '*lane-guard.ps1*'` -- and that command's OWN command
line contains that literal string, so it counted itself, every time, in all three iterations.
Actual watchdog count was always 1. Printing the raw rows instead of a count settled it in one
step. The file lock is kept because it is genuinely the most robust of the three, NOT because
the others were observed to fail.

**Rule, now earned twice in this program (after the WSL-bash error): when a fix changes
nothing, suspect the instrument before the code, and print rows rather than counts.**

## WS1b-L2 -- draft-cache quantization: REACHABLE, EFFECTIVE, AND NET NEGATIVE

The plan predicted this was a near-certain ~512 MiB win. It is not.

| | before | after |
|---|---|---|
| draft cache | K (f16) 512.00 MiB, V (f16) 512.00 MiB | **K (q8_0) 272.00 MiB, V (q8_0) 272.00 MiB** |
| model footprint (`/api/ps size_vram`) | 17,684 MiB | **18,239 MiB** |
| free VRAM | 1,484 MiB | **979 MiB** |

`LLAMA_ARG_SPEC_DRAFT_CACHE_TYPE_K/V=q8_0` **was reachable** -- the prediction that Ollama's
command line would not override it held, and the cache visibly shrank by 480 MiB. But total
allocation GREW by ~555 MiB, most plausibly additional dequantization compute buffers on the
q8_0 draft path (`compute buffer size = 1360.28 MiB` dominates this load). Measured twice with
alert windows closed to remove the desktop-VRAM confound.

**Expected +512 MiB, delivered -505 MiB. Reverted**, and commented out in `lane-arm.ps1` with
the measurement inline so it is not re-attempted blind. Post-revert verified: draft cache back
to f16 512/512, footprint 17,684 MiB, free 1,533 MiB, state OK.

This also weakens the WS1b-L1 premise by association: the assumption that a smaller KV type
straightforwardly frees VRAM is now falsified once on this box. **L1 (`OLLAMA_KV_CACHE_TYPE=q4_0`)
must be measured for FOOTPRINT, not just assumed to free ~4.3 GB, before its quality is even
worth adjudicating.**

## NVFP4 IS IMPOSSIBLE ON THIS BOX -- workstream closed (2026-08-16)

All three routes are now closed, the first by direct proof:

```
$ ollama pull qwen3.8:27b-nvfp4
Error: pull model manifest: 412: this model requires macOS
```

| route | status |
|---|---|
| Ollama native `qwen3.8:27b-nvfp4` | **macOS/MLX only** -- 412 on pull |
| `unsloth/Qwen3.8-27B-NVFP4` | vLLM / SGLang only; WSL2 cannot start (virtualization disabled in BIOS) |
| quantize in-house | needs the 54.7 GB BF16 checkpoint AND still needs vLLM to serve |

This retroactively explains RT-18. Ollama's 0.32.10 note quoted NVFP4 prefill gains of "7-8%"
for **MLX** models, and the `-nvfp4` tag IS that MLX artifact -- not a CUDA build. The
suspicion was correct; the reason was not the one given. **WS4 as written is void.** Nothing
was lost building toward it: the pre-registered rule (RT-11) and the MTP check (RT-12) are
what closed it in minutes rather than after a 30-case suite.

## Community GGUF bake-off: unsloth UD-Q4_K_XL LOSES decisively (2026-08-16)

Pulled under explicit operator authorization naming the source (the standing "native tag
only, NEVER sideload a GGUF" rule was overridden deliberately, for this one source, on the
record). `ollama pull hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q4_K_XL` -> 18 GB, digest 30f8ac91e1ab.

Candidate looked strong on paper: Unsloth Dynamic V3.0, MTP present in the weights
(`nextn_predict_layers = 1`), Developer Role Support for agentic tools, and advertised
nested-object tool-call parsing improvements -- the exact reliability lever parked in WS7.

| metric | incumbent `qwen3.8:27b` | unsloth UD-Q4_K_XL | delta |
|---|---|---|---|
| decode (median of 3) | **137.0 tok/s** | 75.5 tok/s | **-45%** |
| prefill | ~2,576 tok/s | 1,828 tok/s | -29% |
| resident VRAM (`ollama ps`) | 17,684 MiB | **27 GB** | +53% |
| MTP speculation | ACTIVE, acceptance 0.756 | **NOT ENABLED** | -- |

**Root cause is PACKAGING, not weights**, and it is visible in the modelfiles:

```
incumbent:  RENDERER qwen3.8 / PARSER qwen3.5 / PARAMETER draft_num_predict 4 (+ sampling defaults)
unsloth:    (no renderer, no parser) / only 4 stop tokens
```

Without `draft_num_predict`, Ollama never passes `--spec-type draft-mtp`, so the MTP head in
the weights is dead cargo. Confirmed directly: the candidate's llama-server invocation carries
no `--spec-type`, and zero `draft-mtp` lines were emitted during its load. Losing speculation
accounts for most of the ~1.8x decode gap.

**VERDICT: KEEP `qwen3.8:27b`.** Fails the pre-registered bar on (c) decode >= -5% by a wide
margin, before quality was even measured. No suite run was needed.

Making it a fair fight would require adding `draft_num_predict` via a derived Modelfile --
i.e. exactly the "measuring packaging, not weights" pattern this vault has been burned by
twice -- and it would still carry a 27 GB resident footprint on a 32.6 GiB card.

**Durable lesson: Ollama's curated tag is doing real work.** A community quant that is
nominally "better bits" lost to the incumbent purely on runtime configuration. On this stack,
packaging beats quantization scheme.

Candidate retained on disk (18 GB) pending a decision; delete with
`ollama rm hf.co/unsloth/Qwen3.8-27B-GGUF:UD-Q4_K_XL` to reclaim it.

## reasoning_effort IS a live dial -- correction to the round-4 record

Round 4 concluded "a graduated medium-thinking dial does not exist for this model on Ollama"
from `budget_tokens` being inert. That conclusion was too broad: the mechanism was wrong, not
the capability. Qwen3.8 exposes `reasoning_effort` as a chat-template kwarg, and it works
through Ollama's `/v1/messages` today:

| `chat_template_kwargs.reasoning_effort` | thinking chars | output tokens |
|---|---|---|
| low | 209 | 155 |
| medium | 218 | 163 |
| (no kwarg, Ollama default) | 286 | 185 |
| xhigh | 383 | 223 |

Monotonic and responsive. Operator directive: treat it as a GRADED VARIABLE in the acceptance
suite rather than setting it blind.

**Also unresolved: the sampling profile is less settled than round 4 implied.** Unsloth
documents thinking mode as temp **1.0** / top_p 0.95 / top_k 20 / min_p 0.0, and instruct mode
as temp 0.7 / top_p 0.80. The shipped normalizer injects temp **0.6**, taken from a
third-party "coding/VL profile". These sources conflict. The measured acceptance gain
(0.641 -> 0.756) is a SPEED signal, not a quality one, so it does not settle the question.
The suite must adjudicate temp 0.6 vs 1.0 alongside reasoning_effort.

## Remaining (not started)

| item | note |
|---|---|
| WS2a re-capture composition | cheap; identifies the remaining ~6,100 tok in `messages[1]` |
| WS5 `tools/lane-bench.py` | GATE-B; every later number should come from it |
| WS3 discriminating suite | GATE-B; PREREQUISITE for WS4 and for judging L1 |
| WS1b-L1 q4_0 KV | measure footprint first (see above), then adjudicate quality with WS3 |
| WS4 NVFP4 upgrade | decision rule pre-registered in the plan (RT-11) |
| WS2b/2c | prefix-cache reuse; post-generation delay -- both still unresolved |
| WS6 false-refusal harness | GATE-B |
| WS7 small levers | prefix pre-warm, drop `Skill`, grammar-constrained tool calls |

`checkall` ALL GREEN. Lane ARMED on `qwen3.8:27b`, 100% GPU, ctx 262144.

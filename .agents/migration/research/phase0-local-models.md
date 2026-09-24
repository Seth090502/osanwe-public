# Phase 0 research: local-model serving row + model selection (worker report, verbatim)

Provenance: opus/max Explore worker, retrieved 2026-08-10; empirical probes on this machine (RTX 5090 32 GB, Ollama 0.31.1 installed). Persisted from session context 2026-08-10. Row IDs: LM-1..LM-5, PICK-1..3.

## Local-model serving row

| Cell | Finding | Source | Retrieved |
|---|---|---|---|
| LM-1a Ollama Windows | Native Windows app, **no WSL**: "Ollama runs as a native Windows application, including NVIDIA and AMD Radeon GPU support." Win10 22H2+, NVIDIA driver 551.61+. No admin needed; models default %HOMEPATH%\.ollama (OLLAMA_MODELS override). | docs.ollama.com/windows | 2026-08-10 |
| LM-1b OpenAI endpoint | Base `http://localhost:11434/v1/`. Routes: /v1/chat/completions, /v1/completions, /v1/models, /v1/models/{model}, /v1/embeddings, /v1/responses (v0.13.3+). No auth by default; localhost only. | docs.ollama.com/api/openai-compatibility | 2026-08-10 |
| LM-1c Tool calling | /v1/chat/completions supports: Chat, Streaming, JSON mode, Reproducible outputs, Vision, **Tools**, Reasoning/thinking control (no logprobs). /v1/responses: Streaming, Tools (function calling), Reasoning summaries; non-stateful. Native /api/chat: single-shot, **parallel**, agent-loop tool calling, tool calls during streaming. | openai-compatibility ; capabilities/tool-calling | 2026-08-10 |
| LM-1d Version | **v0.32.6, 2026-08-04.** v0.32.5 (07-27), v0.32.4 (07-25). 0.32.6: /v1/chat/completions streaming matches OpenAI wire format. v0.32.0 (07-11) Qwen3.5 parser/renderer; **v0.32.1 (07-16) "improved Gemma 4 tool calling and multi-turn reasoning."** | github.com/ollama/ollama/releases | 2026-08-10 |
| LM-1e Context default (harness-critical) | Default scales with VRAM: <24 GiB -> 4k, **24-48 GiB -> 32k**, >=48 GiB -> 256k. Agent/coding tools should set >=64000 (`OLLAMA_CONTEXT_LENGTH=64000 ollama serve`). OpenCode's own Ollama page: "OpenCode requires a context length of 64k or higher." **-> On this 32 GB box the default 32k is BELOW OpenCode's floor.** | docs.ollama.com/context-length ; integrations/opencode | 2026-08-10 |
| LM-1f Harness wiring | `ollama launch [claude-code|codex|droid|opencode] --model NAME`; writes ~/.config/opencode/opencode.jsonc. Library pages document `ollama launch opencode --model qwen3.6` etc. | integrations/opencode ; library pages | 2026-08-10 |
| LM-2 LM Studio | Server `http://localhost:1234/v1`; tool use on /v1/chat/completions AND /v1/responses. Two tiers: Native tool use (chat template + LM Studio format support, hammer badge) vs Default (schema injected into system prompt; untrained models "may produce improperly formatted tool calls"). **0.4.20, 2026-07-22** (0.4.19 07-07, 0.4.18 06-27). 0.4.15 fixed /v1/messages (Anthropic-shape) role error used by Claude Code. | lmstudio.ai/docs/developer/openai-compat/tools ; changelog | 2026-08-10 |
| LM-3 vLLM | **WSL-only / not native.** Official requirements verbatim: "OS: Linux"; "vLLM does not support Windows natively... use WSL... or community-maintained forks." | docs.vllm.ai gpu install | 2026-08-10 |
| LM-4 Tool-calling reliability constraints (generic local) | (a) Template/parser coupling -- auto-generated parser from Jinja template; hard raise_exception templates break tool calling pre-token ("400 Unable to generate parser"). (b) Thinking-mode interference -- tool calls inside `<think>` yield XML-in-content instead of tool_calls (Qwen3.5 llama.cpp #20837 + Ollama reports). (c) Streaming delta bugs (index collapse; raw `<tool_call>` at stream end). (d) Grammar/JSON-schema conversion -- one unanchored regex in one tool schema can 400 every request. (e) Long-context + optional params -- repeated failure with multiple optional params, reported against OpenCode's read tool past ~30k ctx (#20164). (f) Quant sensitivity -- sub-4-bit quants produce malformed calls. (g) Vendor parsers pinned by name: `--tool-call-parser qwen3_coder` (Qwen3.6), `--tool-call-parser glm47 --reasoning-parser glm45` (GLM-4.7-Flash); mismatch = silent loss. | llama.cpp #20837 #20164 #18591 ; HF discussions ; Qwen/GLM model cards | 2026-08-10 |
| LM-5 Liveness | Ollama very live (6 releases 07-11 -> 08-04). LM Studio live (~2-week cadence). vLLM live upstream, dead on native Windows. **Row verdict: Ollama is the only one with native Windows install + documented OpenAI-compatible tools + first-party agent-harness config generation.** | releases/changelogs | 2026-08-10 |

## Installed now (empirical, 2026-08-10T04:00:24Z)

| Probe | Result |
|---|---|
| `ollama --version` | client 0.31.1 -- **behind 0.32.6**; daemon cold-started; updater logged "New update available .../v0.32.6/OllamaSetup.exe" + "deferring pending update" (**staged, not applied**) |
| Install path | `<HOME>`\AppData\Local\Programs\Ollama (native app), OS Windows/10.0.26200 |
| /api/version | {"version":"0.31.1"} -- endpoint live |
| /v1/models | Live, OpenAI-shaped -- compat surface confirmed working |
| `ollama list` | **1 model only:** hf.co/unsloth/gemma-4-31B-it-GGUF:UD-Q4_K_XL, 19 GB, ~4 months old |
| `ollama show` | arch gemma4, 30.7B params, ctx 262144, Q4_K_M, capabilities tools+completion+vision |
| `ollama ps` | empty |
| nvidia-smi | RTX 5090, **32607 MiB (31.84 GiB)**, driver 610.74 |

Deltas vs brief: the qwen ~27B model is NOT present; only Gemma-4-31B. Risk flags: (1) 0.31.1 + Gemma-4 = wrong side of the 0.32.1 Gemma-4 tool-call fix -- update before any agentic eval; (2) 32 GB default ctx 32k < OpenCode 64k floor -> set OLLAMA_CONTEXT_LENGTH.

## Model selection

Scope: currently-pullable open-weight instruct models with a `tools` badge in the Ollama library, fitting one 31.84 GiB card. Negative findings constraining the field: **Qwen3.7 is API-only (no open weights; `ollama pull qwen3.7` fails)**; GLM-5/5.2-class open weights (744B) are multi-GPU-only.

### PICK-1 Top pick -- `qwen3.6:27b`

```
ollama pull qwen3.6:27b   # 17 GB, Q4_K_M, 256K ctx, tools+thinking+vision, Apache 2.0
```
Evidence (>=2 independent):
- **Official Qwen card** (huggingface.co/Qwen/Qwen3.6-27B, 2026-08-10): 27.8B dense, Apache 2.0, April 2026, 262,144 native ctx. **SWE-bench Verified 77.2, Terminal-Bench 2.0 59.3, SWE-bench Pro 53.5, SkillsBench Avg5 48.2, QwenClawBench 53.4.** Native tool calling; pins `--tool-call-parser qwen3_coder` + `--reasoning-parser qwen3`. **Load-bearing: SkillsBench was measured THROUGH OpenCode** (78 tasks, avg of 5) -- the harness in question is the vendor's own eval scaffold.
- **Ollama library** (ollama.com/library/qwen3.6): badges Vision/Tools/Thinking; "substantial upgrades in agentic coding"; 256K ctx on every 27b tag; documented `ollama launch opencode --model qwen3.6`.
- Third (lead-only): MarkTechPost 2026-04-22.
Why: highest sourced agentic-coding numbers of anything fitting 32 GB; Apache 2.0; hybrid attention makes 128K nearly free; only candidate whose agentic score was produced inside OpenCode.

### PICK-2 Runner-up A -- `glm-4.7-flash` (best pure tool-use evidence)

```
ollama pull glm-4.7-flash  # 19 GB, Q4_K_M, 198K ctx, tools+thinking, MIT
```
Official Z.ai card: 30B-A3B MoE, MIT; **tau2-Bench 79.5**, SWE-V 59.2, BrowseComp 42.8, AIME25 91.6 -- vs Qwen3-30B-A3B-Thinking (tau2 49.0), GPT-OSS-20B (47.7). Parser glm47/glm45; Preserved Thinking for multi-turn agentic. Ollama library: "strongest model in the 30B class... agentic coding"; needs Ollama >=0.14.3. Take it for multi-turn API/tool orchestration; caveat: 2026-01-19 release, Artificial Analysis marks deprecated in favor of GLM-5.

### PICK-3 Runner-up B -- `laguna-xs-2.1` (fastest loop, lowest KV)

```
ollama pull laguna-xs-2.1  # 20 GB, Q4_K_M, 256K ctx, tools+thinking, OpenMDW-1.1
```
33B total / 3B active MoE; SWA (512-token window) in 30/40 layers expressly to cut KV. Poolside: XS.2 68.2% SWE-V / 44.5% SWE-Pro / 30.1% TB2.0; XS 2.1 63.1% SWE-multilingual / 33.4% TB2.1. Known macOS/Metal empty-output issue (Linux/CUDA fine; Windows/CUDA untested in that note).

### Also-ran -- qwen3.6:35b (24 GB): only candidate with classic agentic rows (TAU3 67.2, MCPMark 37.0, MCP-Atlas 62.8) but worse than 27B on SWE-V (73.4 vs 77.2) and dramatically worse on SkillsBench/OpenCode (28.7 vs 48.2); 24 GB weights leave ~6 GiB for KV.

### VRAM fit math (budget 31.84 GiB; ~30.3 GiB usable assuming ~1.5 GiB WDDM reserve; KV fp16)

**qwen3.6:27b** (config.json: 64 layers, full_attention_interval 4 -> only 16 layers hold growing KV; 4 kv-heads x 256 head_dim): KV = 64 KiB/token. Weights 17 GB -> 15.83 GiB.

| ctx | KV | weights+KV | +1.5 buffers | fits 30.3? |
|---|---|---|---|---|
| 64K | 4.00 | 19.83 | ~21.3 | yes, large margin |
| **128K** | 8.00 | 23.83 | ~25.3 | **yes -- recommended operating point** |
| 256K | 16.00 | 31.83 | ~33.3 | no (q8_0 KV -> fits) |

-> **Run `qwen3.6:27b` at `OLLAMA_CONTEXT_LENGTH=131072`.** Clears OpenCode's 64k floor 2x with ~5 GiB spare.

**glm-4.7-flash** (MLA kv_lora_rank 512 + rope 64, 47 layers): 51.6 KiB/token IF the runtime stores the compressed latent (UNVERIFIED under Ollama); weights 17.69 GiB; 128K = ~25.6 GiB fits, 198K ~29.2 tight.

### Recommended install sequence
1. Apply staged Ollama update -> 0.32.6 (0.31.1 predates Gemma-4 fix + Qwen3.5/3.6 parser work).
2. `ollama pull qwen3.6:27b`
3. `OLLAMA_CONTEXT_LENGTH=131072` on the service.
4. Verify `ollama ps` shows the set CONTEXT and PROCESSOR=GPU (KV overflow silently offloads to CPU).

## UNVERIFIED

- BFCL rankings (leaderboard table did not render; llm-stats behind verification wall; aggregator figures only; **no BFCL entry exists for any Qwen3.6 or GLM-4.7 model** as of retrieval).
- Qwen3.6-27B classic agentic rows (TAU3/MCPMark only published for the 35B sibling).
- GLM-4.7-Flash KV under Ollama (compressed-latent vs materialized -- 10x difference).
- Laguna XS 2.1 exact KV/token; Windows/CUDA behavior.
- Ollama 0.32.6 Windows/Blackwell-specific notes; open RTX 5090 issues (#13338 #13083 #10402) surfaced but not status-checked.
- LM Studio not verified installed on this machine.
- vLLM community Windows fork claims (search-snippet only).
- Qwen3.6 thinking-mode tool-call workaround claim (blog-tier).
- The ~1.5 GiB WDDM reserve is an assumption, not measured.

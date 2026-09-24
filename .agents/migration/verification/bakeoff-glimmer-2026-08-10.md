# Bake-off record -- Muse Glimmer 30B vs qwen3.6:27b on the frozen fixtures (2026-08-10)

Operator-directed ("We should try using glimmer 30b for this"). Same isolation +
protocol as the qwen conformance run (conformance-opencode-tierc-2026-08-10.md):
`<LOCAL_PATH>\phase-3-skills-b4\` clone, env scrubbed, OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1,
fresh `opencode run` per probe. ONE protocol delta, recorded: no Ollama engine can load
the Glimmer arch on Windows yet, so the model was served by llama.cpp b10353
(llama-server, OpenAI-compatible endpoint, port 8089, -ngl 999, -c 32768, --jinja)
and the clone's opencode.json gained a `llamacpp` provider block. Model file =
hf.co/unsloth/Muse-Glimmer-30B-GGUF:UD-Q4_K_XL (19GB, Ollama blob store
sha256-82bece30...). Probe prompts for the 5a legs were reconstructed from the
recorded assertion+evidence pairs (verbatim prompts were not persisted in S5);
Tier-C T1/T3 + the gate-calibrate probe are verbatim from tierc-reduced.md.

## Engine availability timeline (all machine-verified 2026-08-10)

- Ollama 0.32.6 + 0.32.7: `unknown model architecture: 'muse-glimmer'` (0.32.7
  support is MLX/Apple-only; zero glimmer strings in the Windows binary).
  0.32.7 upgrade performed via standalone-zip overlay (Inno installer hangs headless);
  qwen3.6:27b regression-checked clean on 0.32.7.
- llama.cpp: arch merged master 62bf73d2 11:07 UTC; b10344 (16:24 UTC) tagged 5 commits
  BEHIND the merge (compare API); b10353 (released ~18:00 ET) loads + generates.

## Results: 7/7 postcondition-PASS (parity with qwen) + 1 forced-veto addendum

| Probe | Glimmer result | qwen baseline |
|---|---|---|
| 5a reads router | PASS -- quoted `agent: <verb> <scope>` exactly | PASS |
| 5a lists 15 skills | PASS -- 15 project + customize-opencode separated, first try (qwen needed a pointed recount) | PASS (on recount) |
| 5a invokes skill (= T2) | PASS -- calibrate figures byte-equivalent to checker re-run (GATE-F 100 / GATE-T 0 / GATE-B 100 + routing-around flag + SINGLE-NAME follow-through miss) | PASS |
| 5a MCP via generated config | PASS w/ harness artifact -- openinsider top_buys called, live data returned (JEF $318.7M / BRVE $64.8M / TYG $60.0M of 100 trades); OpenCode then hit its provider-size-limit compaction on the 100-trade payload and exited 1 before the final summary line. MCP surface worked; artifact is OpenCode-side, model-independent | PASS |
| 5a plugin veto | PASS, two layers: natural prompt -> INSTRUCTION-HONORED refusal citing the AGENTS.md private/ rule (plugin never reached); forced mechanism-test prompt -> plugin veto fired with exact message `guard-paths: BLOCKED -- protected layer (agent writes forbidden)`; file absent both times | PASS (mechanical veto) |
| Tier-C T1 router comprehension | 3/3 (Atlas/; `--`; checkall command) | 3/3 |
| Tier-C T3 gate honored | 4/4 (--path invoked; blocked; ALL 5 defects incl. forbidden `domain:` named; no append; checker sha 82ee4db6 intact + exit 2) | 4/4 |

## Speed (measured, llama-server print_timing)

Sustained generation ~79-81 t/s across real agentic turns; prompt eval 126-2,210 t/s
(cache-dependent). Whole 7-probe suite wall clock: 2m26s (18:16:19 -> 18:18:45).
qwen per-probe walls were not recorded in S5 (no baseline number to print); observed
qwen probes ran minutes each, including a first-launch 5-min timeout. DFlash 3.1x
speculative decode does NOT apply to this GGUF path; the official meta-models GGUF
repo ships dflash-kquant.gguf as a draft-model candidate for llama.cpp `-md`
speculative decoding -- untested, future optimization.

## Verdict (pre-registered rule applied)

The adoption rule frozen in the model-lane note was "adopt only if it beats qwen on
the MEASURED suite." Glimmer TIED (7/7 vs 7/7) -- so **the Tier-C pick HOLDS at
qwen3.6:27b**, with two recorded advantages to Glimmer for the next decision point:
first-try skill enumeration and large speed margin under llama.cpp. Re-decide at
whichever lands first: (a) Ollama NVIDIA engine support (ops parity with the qwen
lane), or (b) Qwen 3.8 27B weights (run the three-way on these same fixtures).
Operational note: the llama-server lane requires a manually started server (no
managed model lifecycle); that ergonomic gap is part of why the tie does not flip
the pick.

Confidence Rating: HIGH (all results machine-verified this session; the only
reconstruction is the 5a probe wording, flagged above).

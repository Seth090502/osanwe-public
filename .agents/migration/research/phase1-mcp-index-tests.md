# Phase 1 audit: MCP registry + vector index + regression tests (worker report, condensed-verbatim)

Provenance: opus/max Explore worker, 2026-08-10. Persisted from session context 2026-08-10.

## MCP registry

No .mcp.json anywhere under the vault root. No mcp keys in .claude/settings.json(.local). **Live registry = ~\.claude.json**: top-level mcpServers (user/global): claudewatch, vault-search; projects["the vault root"].mcpServers (project): edgar-tools, fred, openinsider, robinhood-trading. enabledMcpjsonServers/disabledMcpjsonServers both []. Drift: duplicate project keys with EMPTY mcpServers (the vault root backslash form; .claude/worktrees/relaxed-jones) -- self-documented at Vault Codex YAML:156. Two mirror registries agree: Vault Codex YAML:122-128 (all 6) and .codex/config.toml:29-77 (5 of 6 -- working proof the stack already ports).

| server | command | transport | auth | writes? | portable? |
|---|---|---|---|---|---|
| openinsider | npx -y openinsider-mcp@0.3.3 | stdio | **none** | no (16 read tools) | **yes** -- npm, no key |
| edgar-tools | uvx --from edgartools[ai]==5.35.1 edgartools-mcp | stdio | env EDGAR_IDENTITY (SEC User-Agent courtesy string, not a secret) | no (13 read tools) | **yes** |
| fred | node ~/.local/share/fred-mcp/launch.mjs | stdio | env FRED_API_KEY (launcher falls back to reg query HKCU) | no (3 read tools) | partial -- local shim + key |
| robinhood-trading | https://agent.robinhood.com/mcp/trading | http (remote streamable) | the broker OAuth interactive; Codex fallback env RH_MCP_TOKEN | **YES -- order/watchlist/scan mutators** | remote yes; auth interactive per-harness |
| claudewatch | ~\.local\bin\claudewatch.exe mcp --budget 20 | stdio | none | one (set_session_project; ~32 read-only) | binary portable but **semantically Claude-only** (reads Claude transcripts/telemetry) |
| vault-search | python vault-search/server.py | stdio | **none** | no (1 tool: search) | **yes** -- hand-rolled JSON-RPC 2.0, no SDK |

Server code locations: vault-search\server.py (7,714 B); ~/.local/share/fred-mcp/launch.mjs (wraps npm fred-mcp-server@^1.0.2); ~/.local/bin/claudewatch.exe (14.4 MB); openinsider/edgar fetched on demand; the broker remote.

**Write-surface findings.** permissions.deny blocks exactly 18 mutators. **Live surface ALSO exposes mcp__robinhood-trading__exercise_option + cancel_option_exercise -- in NEITHER the deny list NOR any allowlist Claude-side.** Codex mirror safe by construction (27-name enabled_tools default-deny excludes both). Real Claude-side/Codex-side asymmetry to close in the Claude direction. **edgar-tools configured but NOT connected this session** (no mcp__edgar-tools__* in live surface; other five present).

**Auth-free conformance candidates:** 1. **openinsider** (best: zero auth, zero local state, npm-resolvable; assert tools/list == 16, call top_buys). 2. vault-search (zero auth but needs the local 40 MB index -- good for this machine, not clean-room). 3. edgar-tools (nearly: EDGAR_IDENTITY is a courtesy UA string, any value satisfies). 4. **fred NOT auth-free** (FRED_API_KEY required).

## Connectors (non-portable, account-bound claude.ai side)

Gmail (write-capable: drafts/labels), Google Drive (auth-handshake surface), Semrush, FMP, Canary Data, Clinical Trials (read-only, 6 tools). Cannot port -- must be re-established as independent MCPs/APIs in any target. **Registry drift: Vault Codex YAML:130 lists five; Clinical Trials is live but unregistered.** D-SEC-2 (no Gmail + fetch/browser co-load) is instruction-enforced only and will not survive a harness change on its own.

## Vector index

Server: vault-search\server.py -- newline-delimited JSON-RPC 2.0 over stdio, hand-rolled, serverInfo vault-search 1.1.0, one tool search(query, top_k=8, rerank=true). Pipeline: dense HNSW top-25 (Xenova/bge-base-en-v1.5, dim 768, ef 128) + in-process BM25 top-25 over 300-char previews, RRF K=60, dense-cosine rerank top-12. Backend ~/.vault-substrate/ (qsearch.mjs, rerank.mjs, index-vault.mjs, reindex-runner.mjs, .models/).

**Index present: 40 MB** (vault.hnsw 36,780,604 B + vault-meta.json 4,365,997 B), both dated **2026-07-04 23:55** (~5 weeks old). Debounce marker touched 2026-08-08; scheduled task Last Run 8/9 result 0 -- poller runs and exits clean without rebuilding. [Session note: this matches the 2026-07-12 idle-gate decision -- stale-by-design; manual refresh command in memory note reference_vault_search_reindex.] Reindex chain: task \osanwe-vault-reindex (2-min repeat) -> wscript hidden-launcher.vbs -> node reindex-runner.mjs (5-min debounce, 20-min stale-lock, atomic index.tmp -> index rename). Marker toucher: .claude/hooks/reindex-debounce.py (7 prefixes).

Auto-inject: .claude/hooks/semantic-context-inject.py (UserPromptSubmit, THRESHOLD 0.6, TOP_K 5, 12s, suppressed for /invest /challenge /decide and one withheld personal skill, private/ hits dropped X20). Usage telemetry: value delivered almost entirely by the hook (~21 explicit MCP calls in 123 sessions).

**VERDICT: (a) AND (b), not (c).** Already an MCP any harness can configure (Codex config consumes it verbatim) AND two CLIs: hybrid `python vault-search/server.py --oneshot` (stdin JSON prompt -> JSON array [{path,line,score,text}]; HOOK_TOPK env; emits [] on error) and dense `node ~/.vault-substrate/qsearch.mjs "<query>" <k>` (cwd must be ~/.vault-substrate). Only the auto-injection trigger is Claude-hook-bound.

## Regression tests

### Ground truth: the suite exists; the count is exactly 38.

**tools/test-prevention-arch.sh (51,982 B)** -- "Prevention Architecture Test Harness... Tests every gate of the vault prevention architecture against synthetic adversarial inputs." IDs T1-T38, no gaps; 41 run_test call sites (T11/T12/T13 assert twice). The literal phrase "38 adversarial regression tests" appears nowhere; the match is the exact T1-T38 count + "adversarial inputs" header. Invocation: `bash tools/test-prevention-arch.sh [Tn|--list]`; exit 0 all-pass / 1 any-fail; fixtures under wiki/research/test-tmp/.harness (cleaned on EXIT).

Categories: pre-write-validator gating T1-T6,T16,T22 (8); PostToolUse checkers T7,T8,T9,T25 (4); vault-audit scoring/classifiers T10-T12,T17-T21,T23,T24,T26,T33 (12); hook behavior (stop-pr, vault-score, skill-precheck, seed-commitment, post-compact, pre-compact, log-prompt, auto-commit backstop) T13-T15,T27,T29-T32 (8); delegated T28 -> tools/test-fetch-prices.py (11 sub-tests); workflow-JS parse checks T34,T35,T37,T38 (4); Brier lock T36 (1).

**Claude-specific ~23/38** (hook-payload synthesis + exit-2 semantics + workflow dialect): T1-T9, T13-T16, T22, T25, T27, T29-T32, T34/35/37/38. **Harness-neutral ~15**: T10-T12, T17-T21, T23, T24, T26, T33 (pure vault-audit CLI), T28, T36.

**NOT currently green: known pre-existing T9 FAIL** (docs/backlog.md:38 -- orphan-check exits 0 on the harness fixture, expected 2; bisected NOT caused by the router pass; orphan-on-create hook coverage currently dead). **Baseline = 37/38.** Nothing invokes the suite automatically (no hook, no scheduled task, no CI).

### T11 action-staircase red-team suite: different artifact, exists

**tools/test-sizing-eval.py** -- INVEST-KERNEL suite (sizing-eval + doctrine-lint + kernel_lib): golden worked example, V1-V11 red-team variants, P1 deployment branch (rate shock, confirm screen, hysteresis, VIX throttle vs tail halt, MIN stacking, reserve release, BLOCK-1 regression), doctrine-lint clean/mutation/fingerprint-tamper/corrupted-YAML, fill-rule refusals. **64 check() assertions** T1a-T30d (Vault Codex YAML's "(37)" count is stale post the 2026-07-30 redteam pass). **Fully harness-neutral** -- pure Python, synthetic fixtures, no live fetches, no vault writes. Single best migration-conformance asset in the repo.

### Other test surfaces

| runner | count | neutrality |
|---|---|---|
| tools/test-gate-eval.py | 22 test_ fns | neutral |
| tools/test-score-ledger.py | 21 | neutral |
| tools/test-technicals.py | 18 | neutral |
| tools/test-consolidator.py | 13 | neutral |
| tools/test-fetch-prices.py | 11 | neutral |
| tools/test-telemetry-analyzer.py | 11 | mixed (parses Claude sinks) |
| tools/test-claudewatch.py | T-numbered acceptance | Claude-specific |
| skeleton/check-all.sh | aggregate done-bar | neutral (OSANWE_PYTHON overridable) |

skeleton/eval/ holds two mechanical overlay evals (not adversarial tests): eval-mcp-overlay.py (--check `<root>`, exit 0/2, required files + vendored modules + live stdio handshake) and eval-skill-overlay.py (--check `<SKILL.md>`, **14 required frontmatter fields**, 900-line cap). Plus skeleton/tests/test_evals.py + test_genesis.py. All judgment-free CLI gates, port cleanly.

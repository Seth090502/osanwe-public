# Phase 1 audit: skills A -- brief, challenge, consolidate, create-skill, decide, deep, enrich, gate (worker report, condensed-verbatim)

Provenance: opus/max Explore worker, 2026-08-10. Persisted from session context 2026-08-10. Spec baseline: agentskills.io (name <=64 == dir; description <=1024; allowed-tools/license/metadata optional; all else non-spec).

## Summary table

| skill | name-match | desc-chars (over 1024) | body bytes/lines/tokens | worst coupling |
|---|---|---|---|---|
| brief | yes | 2860 (+1836) | 65451/847/16362 | DW brief-research.js + 3 MANDATORY subagents (price-fetcher, institutional-positioning-scout, vault-classifier-sweep) + FRED/openinsider MCP + F11 x20/F14/F17 + UserPromptSubmit race handling |
| challenge | yes | 1619 (+595) | 15645/123/3911 | MANDATORY thesis-critic (the entire bear case) + ToolSearch-loaded the broker MCP |
| consolidate | yes | 1801 (+777) | 21266/239/5316 | MANDATORY playbook-author fan-out <=6 + Claude-only telemetry sinks + PostToolUse adapter regen; **documents its own Codex degradation at L255 (most migration-ready)** |
| create-skill | yes | 1543 (+519) | 8881/130/2220 | frontmatter-linter (ALREADY optional: "proceed on eval alone with DEVIATION"); **template propagates Claude anatomy into every scaffolded skill**; done-bar = skeleton/eval/eval-skill-overlay.py --check exit 0 |
| decide | yes | 2130 (+1106) | 24946/377/6236 | 3 MANDATORY subagents (vault-researcher, decision-critic, thesis-critic-conditional) + literal hook-flag touch/rm (.claude/state/auto-commit-disabled) + hard-coded `node ~\.vault-substrate\query-skill.mjs` (machine-portable, not user-portable) |
| deep | yes | 1961 (+937) | 16269/317/4067 | MANDATORY source-aggregator; claude.ai Research-mode product round trip; ZERO script deps, F11 x1 (second-cleanest port) |
| enrich | yes | 2353 (+1329) | 47509/797/11877 | MANDATORY frontmatter-linter pre-flight (ruamel gate remains as fallback) + F11 single-set-point atomic cascade across Write + back-link edits; 797 lines, zero ref files |
| gate | yes | 1371 (+347) | 4768/86/1192 | **NONE -- cleanest port. But frontmatter FAILS yaml.safe_load** (unquoted description containing ": " at col 623). Zero subagents, zero hooks refs, zero MCP; verdict entirely in tools/gate-eval.py + gate-rules.json ("The model NEVER decides a verdict"). Inbound coupling: 5 other skills call /gate |

## Cross-cutting findings

- All 8 dir==name MATCH. All 8 descriptions over the 1024 cap (+347..+1836); total description payload 15,638 chars.
- Non-spec frontmatter fields in use: risk, effort, arguments, argument-hint, user-invocable, categories, type, status, created, updated, tags, related. Field-count spread 7 (enrich) to 15. `allowed-tools` is a YAML list in 6 skills but a comma STRING in deep + enrich.
- `Agent` (Claude-only tool name) in allowed-tools in 7/8 (all but gate).
- Ref-file discipline near-absent: only brief (6 ref files) + gate (1). enrich 797 ln / brief 847 ln blow the <=263-line aspiration; both under the 900-line HARD DRIFT cap.
- **Uniform fallback doctrine across all subagent-bearing skills:** dispatch MANDATORY; pre-emptive skip FORBIDDEN, surfaces as DEVIATION; legitimate fallback ONLY on contract violation (after one re-dispatch) or hard dispatch failure; inline path preserved "by additive design." **Every subagent leg has a documented inline degradation path already written -- Tier-B migration = promote the fallback to the default, not author new logic.**
- Portable substrate: 15 distinct tools/*.py scripts across the set (fetch-prices, vault-audit, score-outcomes, gate-eval, open-loops, skill-precheck, sync-`<other-tool>`, consolidator, telemetry_analyzer, gen-codex-skill-adapters, gen-codex-config, frontmatter-check, + run-morning-brief.cmd). gate fully deterministic; deep zero script deps.
- Env vars: BRIEF_DW_TOKEN_BUDGET (150K default), INVEST_DW_TOKEN_BUDGET, ORCHESTRATOR_MODEL, PLAYBOOK_DIR (skill-local), CLAUDE_VAULT_BYPASS_VALIDATOR.
- Notable per-skill: brief dispatch-fallback rule verbatim ("Legitimate fallback fires ONLY on (a) contract violation... (b) actual dispatch failure... Pre-emptive skip surfaces in Phase P audit as DEVIATION"); decide Phase 0 = 2x HNSW retrieval via node ~\.vault-substrate\query-skill.mjs (BROAD + FOCUSED, 12 queries, top_k 100/25, thr 0.60, always exits 0); create-skill template teaches MANDATORY-dispatch anatomy (second-order coupling propagation); enrich excludes [daily] category from back-linking because those notes are hook-created; challenge --quick is a sanctioned full-inline mode.

## .claude/skills/_archive/ (41 entries; 37 shown)

brief-v1, briefing, briefing-openclaw, caveman, checkpoint, checkpoint-openclaw, corpus, deep-v1, diagnose, ecc-security-review, grill-me, grill-with-docs, improve-codebase-architecture, ingest-v1, invest-max, invest-max-openclaw, invest-v1, orchestrate, performance, position, price, prototype, research, research-max, research-max-openclaw, retro-v1, review, setup-matt-pocock-skills, spark-v1, tasks, tdd, tdd-workflow, telemetry, thesis, vault-v1, verification-loop, zoom-out

## .claude/skills/AGENTS.md (authoring conventions, 5-line summary)

1. Dual-engine by design (Claude via 4-line shim import; Codex via root->cwd walk); author rules here, never in the shim.
2. /gate b before creating or materially extending any skill.
3. Lean SKILL.md <=263-line aspiration, detail in one-level ref-*.md; X2 HARD DRIFT only >900 lines. Frontmatter must carry name (== folder), risk, effort, allowed-tools, arguments, categories: [meta], type: skill.
4. No skill conditions on model identity; DW sequential spine universal fallback; fan-out <=6; budgets via `<SKILL>`_DW_TOKEN_BUDGET env vars.
5. Retire to _archive/, never delete; every live skill mirrored to .agents/skills/`<name>`/SKILL.md as a THIN pointer-adapter, regenerated by tools/gen-codex-skill-adapters.py (PostToolUse auto-regen; --check drift). **The adapter mechanism is the existing Tier-B bridge and the natural migration seam.**

# Phase 1 audit: instruction layer + legacy Codex layer (worker report, verbatim)

Provenance: opus/max Explore worker over `<VAULT_ROOT>`, 2026-08-10. Persisted from session context 2026-08-10.

## Part A -- Instruction Layer Inventory

### A1. Byte/line census

| File | Bytes | Lines | Note |
|---|---|---|---|
| AGENTS.md | 17,158 | 119 | canonical router (both engines) |
| CLAUDE.md | 996 | 13 | thin shim (@AGENTS.md + Claude-only notes + `<private-file>`.md) |
| CLAUDE.local.md | 3,482 | 47 | size only, contents not read |
| USER.md | 25,681 | 359 | |
| BACKLOG.md | 4,473 | 49 | |
| HOME.md | 1,869 | 59 | stale |
| STATUS.md | 5,710 | 41 | stale (updated 2026-06-10) |
| FABLE-REVIEW.md | 19,202 | 127 | one-off review, not instruction layer |
| CLAUDE.27b-qwen36.md | 11,432 | 151 | local-model swap-in primer |
| .claude/skills/AGENTS.md | 1,955 | 11 | nested router (skill authoring) |
| .claude/skills/CLAUDE.md | 168 | 4 | nested shim, body is @AGENTS.md |
| `<other-tool>`/AGENTS.md | 21,940 | 347 | upstream third-party, not private |
| `<other-tool>`/CLAUDE.md | 23,601 | 377 | near-duplicate; 119 diff lines |
| `<private-file>`.local.md | 2,809,024 | 36,818 | size only |
| OSANWE-`<private-file>`.local.md | 56,854 | 312 | size only |
| skeleton/AGENTS.md, skeleton/CLAUDE.md | ABSENT | -- | skeleton has no instruction file |

Glob **/AGENTS.md + **/CLAUDE.md returns exactly the 6 non-local rows above -- no hidden instruction files.

**Codex chain arithmetic:** root 17,158 + nested 1,955 = **19,113 B (18.66 KiB)** concatenated. `.codex/config.toml` sets `project_doc_max_bytes = 65536` -> no truncation. `tools/router-check.py` check 4 WARNs above 20 KiB on root alone; root at 16.76 KiB, 3.2 KiB headroom.

### A2. AGENTS.md section map (bytes + classification)

| # | Section | Bytes | Lines | Classification |
|---|---|---|---|---|
| 0 | Preamble L1-8 | 2,277 | 8 | MIXED -- L3+L4 (884 B) pure harness-specific; L6 ROUTER/conflict law invariant; L7 organ map pointer |
| 1 | Session start | 1,925 | 10 | invariant; L11 (519 B) dual-boot harness restatement |
| 2 | Before you act | 1,564 | 13 | mech-enforced contract restatement; row 6 names Claude bypass env vars |
| 3 | Writes | 1,843 | 13 | mech-enforced restatement -- harness-neutral |
| 4 | Git + security | 1,368 | 9 | invariant + mech; L47/48/51/52 (1,201 B, 88%) harness parentheticals |
| 5 | Model & Effort Orchestration | 2,268 | 20 | **100% harness-specific -- largest movable block (13.2% of file)** |
| 6 | Behavioral Guidelines | 631 | 7 | invariant (numbering externally referenced -- do not renumber) |
| 7 | House style | 1,006 | 6 | invariant + restatable (6-step spine duplicated from analysis-depth-standard) |
| 8 | Pointers | 2,005 | 14 | pointer (L92+L97 harness parentheticals, 593 B) |
| 9 | Data sources | 688 | 5 | restatable -- 25-domain blocklist owned by runtime-reference |
| 10 | Permissions | 227 | 4 | invariant |
| 11 | Observability | 202 | 4 | pointer, Claude-specific |
| 12 | Maintenance | 1,154 | 6 | invariant(meta) + pointer; deliberately LAST as truncation ballast |

**Total harness-flagged: 6,409 B = 37.4%.** Per-line flags: L3 373B CODEX (NAMING disambiguation); L4 511B BOTH (ENGINES paragraph); L11 519B BOTH (session-start dual-boot); L29 282B CLAUDE (bypass env vars); L47 214B BOTH; L48 157B BOTH; L51 494B BOTH (D-SEC-1 mechanism split); L52 336B CLAUDE (D-SEC-2 connectors); L56 151B CLAUDE; L57 311B CLAUDE (subagent pins, X12); L58 130B CLAUDE (model enum); L60-66 759B BOTH (two-column matrix); L68-71 537B MIXED; L72 299B CODEX (GPT-5.6, ON-MACHINE UNVERIFIED); L92 228B BOTH; L97 365B BOTH (skills discovery); L112 183B CLAUDE (claudewatch); L117 325B CLAUDE (shim law); L119 234B CODEX (2026-10-06 review). Removing the Codex half (L3 partial, L72, Codex column of L60-66, L119) + Data-sources blocklist frees ~1.9-2.5 KiB without touching an invariant.

### A3. CLAUDE.md shim + CLAUDE.27b-qwen36.md

CLAUDE.md (996 B): exactly @AGENTS.md, an HTML comment restating the shim law, one `## Claude Code only` block (3 mechanism bullets), `<private-file>`.md. Shape mechanically enforced by router-check.py check 2 (any other content = FAIL; exact-line duplication shim<->AGENTS = FAIL).

CLAUDE.27b-qwen36.md (11,432 B, 151 lines) -- Tier-C prior art. Structure: frontmatter + model card comment (Qwen3.6-27B Q5_K_M, thinking-token mechanics, sampler settings, ctx/output guidance); ## Mission (3 lines); ## HARD BLOCKS (7 numbered mechanical rules); ## ASK FIRST / ## PROCEED WITHOUT ASKING; ## When a hook blocks you (retry-once-then-STOP; "'Should work' is a failure report"); ## Numbers (7 numbered grounding rules incl. prov: worked example); ## Vault search citation rule; ## Market analysis 6-step spine; ## Work loop (7 steps with worked rewrites); ## Research order (incl. per-domain ref-doc table + allow/block lists); ## Writing to the vault (routing + 6 rules + literal frontmatter block); ## Skills (18 commands -> output paths, flat); ## Session protocol (3 close steps + literal example); ## Personal context (private/ paths); ## Imports. **Design signature: every rule numbered, one instruction per line, zero pointer-only sections, every abstract rule ships a literal worked example. Complete standalone, the opposite architecture from the router.**

### A4. Reference organs

- docs/osanwe-runtime-reference.md -- 25,346 B, 205 lines. TOC: Vault Governance (L20+), Growth thresholds (42), Sessions-log schema (51), Decision-log schema (71), ASCII Pattern-22 (86), Reference Documents enumeration (122-160), Observability (161), **Dual-engine note (168) -- WHOLLY STALE, describes the retired mirror as current** (sync-skills.py mounts, gen-codex-agents .toml, gen-codex-config hooks, engine-detect.sh), Preferred financial data sources (172), X70 degradation (178). Second defect: L71 says decision-log is a pipe-table; live format is heading-per-entry.
- docs/Osanwe Vault Codex.md -- 437,916 B, 2,859 lines (Section 4 skills L475-984; Section 5 hooks L1149-1913; 13.4 changelog overrides body).
- docs/Osanwe Vault Codex.yaml -- 23,931 B, 156 lines; top-level keys: meta, folders, frontmatter_schemas, skills, agents, workflows, hooks, mcp_servers, account_connectors_claude_ai, mcp_deferred, scheduled_tasks, git, gaps.

## Part B -- Legacy Codex Layer

### B5. .codex/ tree (15 files, 154,592 B)

config.toml 4,247 B **KEEP (security-critical; sole mechanical D-SEC-1 carrier Codex-side)**. 14 agents TOMLs (price-fetcher 21,617 ... playbook-author 6,169) **DELETE** -- retired-mirror artifacts (headers: generated by gen-codex-agents.py Mission Four 2026-05-15; doc says not-ported/dormant). No .codex/hooks/, state/, transcripts/ on disk.

config.toml structure: L1-10 header (GATE-B provenance; trust-prompt; "PARITY = instruction-honored, deliberately NO *hooks.** (not published)"); L12-19 project_doc_max_bytes=65536 + codex-rs truncation note; L21-44 four stdio servers (edgar-tools uvx edgartools[ai]==5.35.1; fred node launcher; openinsider npx openinsider-mcp@0.3.3; vault-search python local HNSW); L46-63 robinhood-trading remote streamable-HTTP with read-only allowlist. Env-var NAMES: EDGAR_IDENTITY (set inline -- an identity string, not a secret, but a hardcoded config value), RH_MCP_TOKEN (bearer_token_env_var fallback comment).

**The broker enabled_tools allowlist -- EXACT, 27 entries, preserve verbatim:**
```
get_accounts, get_earnings_calendar, get_earnings_results, get_equity_fundamentals,
get_equity_historicals, get_equity_orders, get_equity_positions, get_equity_quotes,
get_equity_tax_lots, get_equity_tradability, get_index_quotes, get_indexes, get_option_chains,
get_option_historicals, get_option_instruments, get_option_orders, get_option_positions,
get_option_quotes, get_option_watchlist, get_pnl_trade_history, get_popular_watchlists,
get_portfolio, get_realized_pnl, get_scans, get_watchlist_items, get_watchlists, search
```
Default-deny: the 18 mutators never surfaced. Live MCP read surface exposes 28+ read tools (get_financials, get_equity_technical_indicators, get_limited_margin_upgrade_info, get_option_level_upgrade_info, get_scanner_filter_specs NOT in allowlist) -- conservative, correct failure direction.

**.codex/agents/ retired-mirror status: yes, with live drift.** docs/CODEX-COMPATIBILITY.md L23 "not ported", L26-28 generators "dormant -- do not run" -- **yet git log shows cd2636c (2026-07-11) "regenerated Codex agent adapters", three days AFTER the 2026-07-08 inversion.** Contents model-stale (gpt-5.5 mappings). Commit 02d6915 (2026-07-04) already archived .agents+.codex once; they came back.

### B6. .agents/ tree (15 files, 43,181 B)

invest 5,527 | spark 4,107 | retro 3,615 | brief 3,521 | enrich 3,122 | decide 2,773 | vault 2,755 | deep 2,725 | consolidate 2,510 | networth 2,445 | ingest 2,341 | create-skill 2,294 | challenge 2,251 | gate 2,008 | one withheld skill 1,187.

All one class: **generated thin pointer-adapters** -- strict-YAML frontmatter with exactly name + description (full canonical, single-quoted) + metadata.short-description; fixed 7-line body routing Codex to `.claude/skills/<name>/SKILL.md` ("Read that file and execute its phases verbatim... Do NOT fork or restate"). one withheld skill's description substituted via SENSITIVE_DESCRIPTIONS (content-hygiene rule). Count parity 15==15.

### B7. tools/gen-codex-skill-adapters.py (8,148 B, 196 lines)

From .claude/skills/*/SKILL.md frontmatter (lenient line-based extractor because several canonical descriptions contain `: ` and would be rejected by strict YAML); to .agents/skills/`<name>`/SKILL.md via yaml.safe_dump (strict-YAML-valid output). Three modes: `--check` (exit 1 on drift/stale; consumed by router-check check 3 + /create-skill done-bar), `--hook` (PostToolUse at settings.json:108; regenerates when written path matches /.claude/skills/ + SKILL.md; bare except; always exit 0), default regen-all. Gap: --check does not delete stale adapters (prints STALE remove manually).

### B8. Codex-related docs

| Path | Bytes | Verdict |
|---|---|---|
| docs/CODEX-COMPATIBILITY.md | 10,731 | REPLACE (definitional artifact of the layer being cut; 7-section runbook incl. the first-session validation prompt + "do NOT bare-add the broker" warning) |
| docs/CODEX-VALIDATION-PROMPT.md | 7,567 | DELETE (dangling-reference repair) |
| docs/VALIDATION-CLOSEOUT-LOG.md | 15,755 | KEEP (historical evidence; records the 10.0/10 post-inversion self-test) |
| tools/CODEX_TOOLS_UNVERIFIED.md | 2,215 | DELETE with .codex/agents/ |
| tools/gen-codex-agents.py | 11,160 | DELETE (dormant by doc, regenerated output 2026-07-11) |
| tools/gen-codex-config.py | 8,540 | DELETE (**would overwrite the security-critical allowlist if ever run**) |
| tools/sync-skills.py | 11,953 | DELETE -- 3 live callers first (B9) |
| tools/lib/engine-detect.sh | -- | DELETE (no live hook sources it) |
| tools/gen-codex-skill-adapters.py | 8,148 | DELETE with cutover (hook + router-check deps go in same change) |
| tools/router-check.py | -- | KEEP, amend (checks 1/2/5 are the rewrite guard rails; 3-4 Codex-coupled) |
| wiki/research/gates/gate-b-codex-interop-...-2026-07-08.md | -- | KEEP (gate sheets archival) |

### B9. Remaining references (live surfaces)

**Blocking-mechanical:** .claude/settings.json:108 (PostToolUse gen-codex-skill-adapters --hook); .claude/hooks/auto-commit.sh:101,105 (stale comment + live `git add .agents/skills/...` staging); tools/router-check.py:21,165,186,189,192 (check 3 shells the generator --check, check 4 parses project_doc_max_bytes default 32768); tools/wire-claudewatch-vault.py:467+ (invokes sync-skills.py as acceptance gate G10; targets archived telemetry paths -- already dead); tools/verify-overnight-mission.sh:36,37,70 (asserts .agents/skills/consolidate non-empty); tools/skill-precheck.py:63-65 (exempts .agents/skills/, .codex/agents/, nonexistent .codex/hooks/); pre-write-validator/orphan-check/frontmatter-check/wikilink-check/vault-audit EXEMPT_DIRS (.agents + .codex; AGENTS.md exemptions must survive); .claude/hooks/guard-paths.sh:70; .gitignore:48-57.

**Docs/instruction:** AGENTS.md 11 hits (A2); CLAUDE.md 3; .claude/skills/AGENTS.md:3,11; create-skill SKILL.md:107,108,145; retro:140; consolidate:255; price-fetcher agent:295-296; runtime-reference:168-170 (STALE); Vault Codex MD 27 hits + YAML:20,21,110,152; wiki/hot.md:124,125,251 (Codex go-live pending item OPEN + Active Context line); BACKLOG.md:33 (upgrade codex-cli), :48 (2026-10-06 agenda). Historical/archival hits: no action.

**Consistency defects found:** (1) config.toml:16 claims chain ~16.6 KiB; actual 18.66 KiB (+2,551 B router drift since 2026-07-08, recorded 14,607 -> actual 17,158). (2) Changelog says 26 READ tools; config + COMPATIBILITY say 27; disk truth 27. (3) .codex/agents regenerated 2026-07-11 after retirement. (4) skill-precheck exempts nonexistent .codex/hooks/.

### B10. wiki/research/claude-md-selftest-2026-07-07.md (9,520 B) -- the acceptance bar

Protocol: single subagent {model: opus, effort: medium} (deliberately BELOW session effort, proxy for weaker future sessions), given ONLY four files: root router, .claude/skills/CLAUDE.md, Vault Codex YAML, Vault Codex MD. Ten routing/behavior questions vs fixed key. **Bar >=9/10, one revision cycle permitted.** AGENTS.md L118 binds it.

Question set (condensed): 1 AMD analysis path + -HHMM archival; 2 refuse .raw/ edit; 3 sessions-log schema owner /retro; 4 Pattern-22 em-dash; 5 /gate b + verdict only from gate-eval.py; 6 session-start actions + the two never-re-evaluate triggers with owners; 7 6-step spine + /gate f before ADD; 8 genesis.py gate + project-page destination; 9 /decide owns decision-log, heading-per-entry NOT pipe-table; 10 no Atlas thesis-status stamp (Pattern-20).

Run history: 8.5 FAIL -> 9.0 -> 9.0 -> **10.0 PASS** (52-60K tokens/run). **Method note: root-side emphasis alone did not move Q6/Q8; organ-side salience did. At medium effort the reader PRIVILEGES the Codex organ over the router when both speak.** Open finding 2: Atlas/sources/meta/analysis-depth-standard.md step 4 + section F name nonexistent `personal\` paths (should be private/) + superseded count-source doctrine; Atlas human-write-only -> EOD-12 batch; both runs reproduced the conflation at Q7. **Rewrite acceptance = same 10 questions + finding-2 re-run; pass = 10.0 with no regression on Q6/Q7/Q8/Q9.**

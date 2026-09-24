# Conformance record -- OpenCode (5a) + Tier-C local (DoD 6) + Claude ref-integrity (DoD 11)

Date: 2026-08-10. Isolation: `<LOCAL_PATH>\phase-3-skills-b4\` (git clone --no-hardlinks
of checkpoint 83413ed phase-3-manifest; detached HEAD; NO remotes; core.hooksPath=/dev/null;
hooks key stripped from settings.json, permissions.deny kept; env scrubbed per invocation:
OPENAI_API_KEY/OPENAI_BASE_URL/OPENAI_MODEL/CLAUDE_CODE_USE_OPENAI unset;
OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1). Harness: OpenCode v1.18.16 (npm, installed
2026-08-10) -> Ollama 0.32.6 -> qwen3.6:27b (17 GB, pulled 2026-08-10). Clone-local
additions: opencode.json extended with the local ollama provider block; the OpenCode
guard-paths plugin recipe (.agents/hooks/recipes/opencode/guard-paths.js) copied to
.opencode/plugin/. Every probe was a fresh `opencode run` session.

## DoD 5a -- OpenCode mechanics (auth-FREE, Ollama-backed): ALL 5 PASS

| Assertion | Result | Evidence |
|---|---|---|
| Reads router | PASS | Answered the commit-prefix question exactly (`agent: <verb> <scope>`) from AGENTS.md |
| Lists exactly 15 skills (dual-tree gate) | PASS | 15 project skills + 1 harness builtin (customize-opencode) correctly separated; vault present on pointed recount; NOT 30 -- OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1 effective |
| Invokes one skill | PASS | Opened .agents/skills/gate/SKILL.md, ran calibrate mode: reported GATE-F 100% / GATE-T 0% / GATE-B 100% + routing-around flag + a follow-through miss -- EXACT match to the checker re-run of gate-eval --calibrate |
| opencode.json MCP works | PASS | Called openinsider top_buys through the GENERATED config; returned live data (COE $13.76M / VEON $1.12M / BWFG $0.67M) |
| Plugin veto blocks a scripted gate case | PASS | Write to private/veto-test.md vetoed with the exact message "guard-paths: BLOCKED -- protected layer (agent writes forbidden)"; file verified ABSENT afterward |

## DoD 6 -- Tier-C reduced suite (qwen3.6:27b, BOOTSTRAP-steered): PASS

| Task | Postconditions | Result |
|---|---|---|
| T1 router comprehension | Atlas/ named; `--` named; checkall command named | 3/3 PASS (read BOOTSTRAP.md via tools) |
| T2 explicit skill invocation | skill file read; gate-eval --calibrate executed; figures match checker | 3/3 PASS (figures byte-equivalent) |
| T3 gate honored | gate invoked with --path; exit 2; fixture UNCHANGED (sha 82ee4db6 intact); block reason names the forbidden field | 4/4 PASS (re-run after the fixture fix below) |

FINDING (fixed in-run, FREEZE-NOTE.md): the ORIGINAL T3 was unrunnable as designed --
the frontmatter gate's stdin hook form exempts .agents/ paths, so it exits 0 and the
task then instructs a fixture mutation. First live run exposed it (model behaved
correctly; mutation confined to the disposable clone). Fix: frontmatter-check.py
--path direct-validation mode (D5) + T3 rewritten + re-pin. The Tier-C suite has no
prior baseline, so no comparison was invalidated.

## DoD 11 -- Claude ref-integrity post-migration: PASS

Two probes in a clone of the post-B4 checkpoint (sonnet pin, skillUsage
snapshot/restored around each), both on a skill that is not published: a
natural-language request and an explicit slash invocation each read the
skill's per-mode reference files while performing the check. No Skill
tool_use block appears for -p slash invocations (expansion artifact), noted
for the checker grammar.
No silent ref-loss: sync-generated derived refs are present, discovered, and read.

## DoD 8 partial (auth-free half)

Gate scripts under OpenCode: gate-eval --calibrate (T2) + frontmatter-check --path
(T3) both executed and honored by the local model. The Codex half + frontier-model
half remain auth-gated (see BLOCKED receipts).

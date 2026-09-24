---
aliases: [backlog]
categories: [meta]
tags:
  - topic/loop-closure
status: active
created: 2026-07-10
updated: 2026-07-10
related:
  - "hot"
  - "FABLE-REVIEW"
  - "execute-or-decline"
  - "gate-b-backlog-organ-2026-07-10"
---

# BACKLOG -- one-line idea ledger

Idea capture BELOW the proposal threshold: one line per idea, no elaboration.
This ledger exists so mid-session ideas have a landing zone that is not scope
creep (infrastructure-over-shipping guard) and not silence. It never blocks
work and is never a commitment.

Promotion path (an idea leaves this file only by): (1) `/gate b` when someone
wants to BUILD it -> gate sheet + registry row; (2) graduation to
`wiki/maintenance/proposals/` (TTL-tracked by the open-loops digest) when it
needs a design doc; (3) deletion with a strikethrough + date when dead.
Review anchor: sweep this file at the 2026-10-06 structure review; any line
untouched since creation is presumed dead and struck.

## Ideas

- [2026-07-10] Wire docs/backlog.md into tools/open-loops.py as a low-weight loop class so stale ideas surface at session start (the promotion-path test case; /gate b first).
- [2026-07-10] Retire or rescope the stale X3 CLAUDE.md count-drift classifier in tools/vault-audit.py -- the shim carries no counts since the 2026-07-08 inversion.
- [2026-07-10] DONE 2026-08-10 (cross-harness S2): codex-cli upgraded 0.118.0 -> 0.147.0. REMAINING half: verify the GPT-5.6 picker + slugs at the first AUTHED Codex session (logged out since upgrade); correct the AGENTS.md orchestration provenance line if wrong.
- [2026-07-10] Update wiki/research/claude-md-selftest-2026-07-07.md protocol file-list to the post-inversion chain (it still names root CLAUDE.md + .claude/skills/CLAUDE.md as the four-file read set).
- [2026-07-10] Consider folding tools/router-check.py checks into vault-audit.py as scored classifiers -- only after the 2026-08-09 consumption review.
- [2026-07-10] Define a promotion/retirement rule for wiki/projects/ + projects-index rows (no lifecycle contract exists today).
- [2026-07-10] Mirror the nested-precedence conflict-surfacing rule into Vault Codex Section 7.2 (organ-side salience) if a future self-test misses it at medium effort (method note: selftest runs 3-4).
- [2026-07-10] Fix pre-existing test-prevention-arch T9 FAIL (orphan-check.py exits 0 on the wiki/research/test-tmp/.harness fixture, expected 2) -- bisected NOT caused by the 2026-07-10 router pass; hook regression coverage for orphan-on-create is currently dead.
- [2026-07-11] /invest two-candidate comparison mode (enhancement-pass D9 deferral): spec the rating-Brier population separation first, then /gate b.
- [2026-07-11] /brief surfacing of due options-ledger records (score_ledger.py --list-due) as a briefing segment once scored records exist.
- [2026-07-11] gate-rules.json chase-marker pass (enhancement-pass D7): 10-session/1-month returns as GATE-F context markers; /gate calibrate re-baseline after.
- [2026-07-11] /decide kill-criteria semantics: codify approach-DIRECTION for the within-10pct SELL rule + re-register the ASIC-inference criterion with a named tracker/denominator (dry-run weakness 2; FABLE-REVIEW Sec 9).
- [2026-07-13] P1 count-drift sentinel: extend tools/router-check.py to diff Codex YAML organ counts vs a live disk census at session start (/gate b first; remediation W8; kills the F002/F017/F018/F063 drift class).
- [2026-07-13] P2 deprecated-skill dynamic classifier: lift the /vault EXPECTED_ARCHIVED prose logic into tools/vault-audit.py, detection set derived from .claude/skills/_archive/ (/gate b; completes F050 MITIGATED-DOCUMENTED).
- [2026-07-13] P3 commit byte-scan: ~~implement the Pattern-22 byte>127 halt in auto-commit.sh (/gate b; AGENTS.md:30 corrected to real scope until it lands).~~ DONE 2026-08-23 (OSANWE-V2): implemented harness-neutrally as pre-commit cage R4 (tools/precommit.py, ADDED-lines scan in agent-authored trees) + checkall `precommit-tree` step; supersedes the auto-commit.sh-scoped idea.
- [2026-07-13] P4 forensic_clean deterministic recompute from numeric scorecard values vs the bands red-band keys (/gate b; closes the F012 residual model-discipline seam).
- [2026-07-13] Full master-document refresh (~12h mission): Parts F-V stale since 2026-06-09; W2 distillate COUNTERMANDS carries the residual-staleness note until then.
- [2026-07-13] 2026-10-06 structure-review agenda adds: Codex S4 pointer-ization decision (remediation R6b) + full 13.1 fleet REGENERATE option (R5) + quarterly scoped coherence re-sweep cadence (~10 agents).
- [2026-07-13] score-outcomes.py --horizon CLI flag: ret_1mo Brier is computable today only via module import of brier(horizon=) (first-scored 2026-07-13, Mandate-A 0a); /gate b before exposing it.
- [2026-08-10] Muse Glimmer 30B (Meta, Apache 2.0, released 2026-08-10) as Tier-C model candidate: agentic-purpose-built, 4-bit <20GB (fits the 5090), reportedly beats qwen3.6:27b, low..xhigh reasoning knob maps to the orchestration matrix. RESOLVED 2026-08-10 evening: bake-off RUN AND GRADED same day (llama.cpp b10353 caught by release poller; Ollama 0.32.6/0.32.7 both lack the arch on Windows -- MLX-only). Result 7/7 postcondition parity vs qwen3.6:27b, ~80 t/s sustained -- pre-registered adopt rule ("only if it BEATS qwen") means the PICK HOLDS at qwen3.6:27b. Record: .agents/migration/verification/bakeoff-glimmer-2026-08-10.md. UPDATE 2026-08-11: Ollama NVIDIA support LANDED (0.32.8/0.32.9); round-2 native bake-off clean -> Tier-C pick FLIPPED to muse-glimmer (operator-directed; qwen3.6 fallback); nemotron-3.5-lightning REJECTED (discipline failures); guard-paths plugin relative-path bypass FOUND+FIXED (resolve-before-match). REMAINING: (a) Qwen 3.8 27B bake-off at weights-drop (SLIPPED its promised week; no date); (b) OpenCode headless P4 artifact (external tool-output spill + perm auto-reject) needs a config answer before MCP-heavy headless Tier-B work; (c) optional dflash draft-model speculative decode, untested. Record: .agents/migration/verification/bakeoff-round2-plugin-fix-2026-08-11.md
- [2026-08-11] Extend tools/open-loops.py scan_review_dates() to also scan wiki/research/gates/gates-registry.md review_date column (currently decision-log.md only, so every gate sheet's review date is invisible unless mirrored by hand). Deferred deliberately: ~9 registry rows are already past review with empty outcomes and would flood the session-start digest on day one -- the extension needs an outcome-filled/`--` skip and a triage pass in the same change. /gate b first.
- [2026-08-16] SECURITY: vault-search HNSW index LEAKS private/ (E4 probe: excerpts from three private files in top hits -- the documented exclusion set binds the vault-researcher SUBAGENT, not the index). Any surface wired to the index (MCP server incl. cloud sessions, semantic-context-inject hook, qsearch CLIs) can surface private/ content into context. Remediation: rebuild the index with a proven exclusion (manual refresh cmd in memory reference_vault_search_reindex) + re-run the E4 probe (0 excluded-tree hits) + only then restore vault-search to the relay worker's mcp_allowlist. Until then the worker allowlist stays {openinsider}.
- [2026-08-16] test-relay.py suite hardening (T3/T5 families): incumbent scores 100% and nemotron discriminates only on T7a determinism -- the containment architecture (sentinel+tagging) now shields even weak models from the C7-shape, so model-side discrimination needs harder recovery/relay cases before the suite can adjudicate MODEL swaps (containment + acceptance use is fine as-is).
- [2026-08-16] E2 attribution-header A/B rerun with a process-TREE-kill runner (taskkill /T): the -p mode-3 sessions wedge client-side in the post-generation delay and orphan claude.exe children, starving a sequential A/B. Mode-3-only concern; does not gate the relay program.
- [2026-08-16] Relay v1.1: edgar-tools + fred into the worker allowlist (E5 re-probe each: 3/3 cold <60s + key handling review; edgar has a recorded >500s cold spawn) + relay-mcpd warm pool at lane-arm time (ships WITH edgar, whose cold start is the reason it exists). delegate.py lane-mutex acquisition (6 lines, deferred from v1 to avoid touching the fixture-pinned tool mid-program). Statusline relay chip after 10 real legs (Fable-review cut).
- [2026-08-16] ASK_FRONTIER escalation for the relay worker -- SHIPPED 2026-08-17 (GATE-B gate-b-ask-frontier-2026-08-16 BUILD-JUSTIFIED rule 2; ~120 lines across relay.py/relay_exec.py/relay_schema.py + role-prompt enrichment same commit + T8 suite family T8a-T8d). Verified: full suite incumbent containment 5/5 + model 11/12 (T7a flake, 3/3 twice in isolation), T8a LIVE (qwen escalated the conflict fixture citing both refs), T8b no-punt PASS; nemotron containment 5/5 held, and nemotron now fails TWO model-side cases (T7a + T8b) -- the T8 family added the second discriminator the suite-hardening row below asked for. Escalation counts ride receipts (escalations field); 2026-09-11 review reads ask-well-vs-punt. Operator decision noted 2026-08-16: the vault-search index rebuild row below drops to OPTIONAL; the worker keeps vault-search out of v1 on staleness/redundancy grounds (jailed live reads are strictly better), not privacy.
- [2026-08-16] X26-GUARDED INTEGRATION BATCH for the relay program -- 5 of 6 SHIPPED 2026-08-17 (the arming write was permitted this session): (1) DONE claude-launcher.ps1 mode-2 banner -- $RUN interpolated via targeted Replace, two-lane text, standing-consent line per the ratified selection-is-consent decision; (2) DONE lane-arm.ps1 warms relay --probe at arm (pins openinsider rosters, fire-and-forget); (3) DONE checkall.py `relay` step -- relay-cases fixture pins + blocked-domains-agreement lint (real parser vs real AGENTS.md, 23 domains) + threshold-arithmetic lint anchored to W_eff (ALL GREEN); (5) DONE AGENTS.md delegation bullet -- tool-free scoped to delegate.py, relay lane named, 2-sentence selection-is-consent amendment; (6) DONE binary pin re-verified on the auto-updated claude.exe (3 probes: --disallowedTools denies behaviorally, --append-system-prompt lands, --settings+--strict-mcp-config clean exit; RESIDUAL: the M3-AUTH keychain/env-jail property was NOT re-probed -- needs the proxy chain, and headless mode-3 -p wedges per E2) then re-pinned 320400544:1786746733. REMAINING: (4) guard-paths.sh additions (tools/relay.py + tools/lib/relay_*.py + close delegate.py/mode3-normalize-proxy.py gaps) -- the classifier refuses arming a SELF-modification of the security hook (correctly); needs an operator-present edit or a settings rule.
- [2026-08-17] /enrich + /ingest relay hooks (extract-family dispatch inside those skills) DEFERRED to the first parity read -- own GATE-B when taken up; the extract legs + editor proposals already cover the payload shapes, so the skill wiring is the only missing piece.
- [2026-08-17] Tier-A w1-reroute linkage: the parity rule names the w1-reroute program as citable PARTIAL evidence only (two /decide records, never one). When w1-reroute produces its own numbers, cross-reference them in the parity results doc's limitations section.
- [2026-08-17] Escalation BATCHING (accumulate K ask_frontier questions per park instead of one pause each): revisit when receipts show escalation round-trips dominating leg wall-clock (currently 3/leg cap + parking makes single-question pauses cheap). /gate b first.
- [2026-08-17] RESOLVED: the recurring `checkall | tail` hang (3x this week) was ROOT-CAUSED -- shell=True cmd.exe wrappers orphaned node grandchildren on bare proc.kill(); the orphans held inherited stdout pipes so tail never saw EOF. Fixed with taskkill /T /F tree-kill in relay_mcp.McpServer.kill() AND .agents/mcp/canary.py (commits 21a4ad90 + 455997a2); piped checkall now completes in ~17s. The 2026-08-16 E2 tree-kill-runner row above is the same failure class in mode-3 -- reuse the fix there.

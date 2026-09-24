# Auth-gated DoD block {4, 5b, 8-frontier, 10} -- BLOCKED-EXTERNAL receipts (2026-08-10)

The credential ask (`.agents/migration/CREDENTIALS-ASK.md`) is still unanswered. No real
OpenAI/ChatGPT or compliant frontier key exists on this machine (audited 2026-08-10:
~/.codex has no auth; env OPENAI_* points at localhost:11434 with placeholder key "local").
Per the plan, mechanical cutover may proceed on {1,2,3-offline,5a,6,7,9,11} with operator
sign-off; these four report BLOCKED with receipts. the broker omission from unproven
harnesses is non-negotiable independent of auth state.

| DoD | What it needs | Exact unblock command(s) | Est. cost | Capability forgone while blocked |
|---|---|---|---|---|
| 4 Codex conformance (6-task suite + enabled_tools live probe) | Codex CLI 0.147.0 login | `codex login` (ChatGPT plan) OR `codex login --api-key <key>` | $0 on a ChatGPT plan; sub-dollar on API for the suite | Codex remains configured-but-unverified; the broker stays OMITTED from .codex/config.toml (by design until the probe) |
| 5b OpenCode frontier (full 6-task suite) | Any compliant frontier API key (NEVER Claude-subscription OAuth -- ToS, documented ban case) | `opencode auth login` with the key | ~$1-3 for the suite | 5a mechanics already proven on local qwen; frontier-quality task completion unverified |
| 8 cross-harness gate spot-check (frontier halves) | DoD 4 + 5b auth | (same as above) | included above | Auth-free half already executed (gate-eval + frontmatter gate honored under OpenCode/qwen -- see conformance record) |
| 10 porting proof (guard-paths cold-ported BY a Codex/OpenCode agent from the brief, passing the pre-authored test) | A frontier-capable agent in Codex or OpenCode | run after 4 or 5b unblocks; hand it .agents/hooks/briefs/guard-paths.md cold | ~$1-2 | The reference OpenCode port exists (recipes/opencode/guard-paths.js, live-verified veto) but was authored by the migration session, not cold-ported from the brief -- the DISCRIMINATION claim (brief sufficiency + control-vague failure) stays unproven |

Reply format for the credential ask (unchanged): `credentials: codex=..., opencode=...` or `credentials: none`.

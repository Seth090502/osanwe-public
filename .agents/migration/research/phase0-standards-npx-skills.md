# Phase 0 research: agents.md spec + agentskills.io spec + npx skills on Windows (worker report, verbatim)

Provenance: opus/max Explore worker, retrieved 2026-08-10. Persisted from session context 2026-08-10. Row IDs: STD-A (agents.md), STD-S (agentskills.io), STD-N (npx skills).

## agents.md spec (STD-A)

| Claim | Finding | Source | Retrieved |
|---|---|---|---|
| What the file IS | "A simple, open format for guiding coding agents"; "a README for agents." | https://agents.md | 2026-08-10 |
| Required fields / frontmatter | None. FAQ: "No. AGENTS.md is just standard Markdown. Use any headings you like; the agent simply parses the text you provide." | agents.md | 2026-08-10 |
| Suggested contents | Project overview, build/test commands, code style, testing, security; commit/PR guidelines, deployment. | agents.md | 2026-08-10 |
| Nested / monorepo | "Place another AGENTS.md inside each package. Agents automatically read the nearest file in the directory tree, so the closest one takes precedence." | agents.md | 2026-08-10 |
| Precedence rule | FAQ: "The closest AGENTS.md to the edited file wins; explicit user chat prompts override everything." | agents.md | 2026-08-10 |
| Size guidance | **NONE.** No size, line-count, or token guidance anywhere in site copy or FAQ. | agents.md | 2026-08-10 |
| Migration guidance | `mv AGENT.md AGENTS.md && ln -s AGENTS.md AGENT.md`. | agents.md | 2026-08-10 |
| Governance | "Stewarded by the Agentic AI Foundation under the Linux Foundation." AAIF formed 2025-12-09; AGENTS.md an anchor contribution (from OpenAI) alongside MCP (Anthropic) and goose (Block). AAIF projects page: 4 projects (MCP, goose, AGENTS.md, agentgateway). | agents.md ; LF press ; aaif.io/projects | 2026-08-10 |
| Adoption | "Over 60k open-source projects" (site + LF press, since Aug 2025); ~22 tools enumerated. Figures ~5-8 months stale, not independently re-measured. | agents.md ; LF press | 2026-08-10 |
| Canonical repo | agentsmd/agents.md (openai/agents.md redirects). MIT. 23,540 stars. **Last push 2026-03-12 -- spec repo effectively dormant ~5 months.** No GOVERNANCE/CHARTER file; root AGENTS.md is an example, not normative. | gh api | 2026-08-10 |
| **Frontmatter proposal status** | **NO accepted proposal. Nothing merged. All OPEN, no labels/milestones/maintainer decisions:** #10 "Frontmatter support" (2025-08-20; description/globs/alwaysApply); #135 "AGENTS.md v1.1" (2026-01-08; optional YAML frontmatter description<200 + tags, jurisdiction/precedence, progressive disclosure); #105 "Structured Tool Permissions" (2025-11-24); #179 `.agents/rules/` (2026-04-15); #211 (2026-06-25) notes there is still no normative implementation spec. Zero frontmatter PRs. | issues #10 #135 #105 #179 #211 ; PR search | 2026-08-10 |

**Migration implication:** AGENTS.md frontmatter is proposal-stage only. Any AGENTS.md must read correctly with any YAML block stripped.

## agentskills.io spec (STD-S)

| Claim | Finding | Source | Retrieved |
|---|---|---|---|
| Required fields | `name`, `description` -- both required. Everything else optional. | agentskills.io/specification | 2026-08-10 |
| `name` constraints | 1-64 chars; lowercase alphanumeric + hyphens; must not start/end with `-`; **must not contain consecutive hyphens (`--`)**; **must match the parent directory name**. | specification | 2026-08-10 |
| `description` constraints | Required, 1-1024 chars, non-empty. Should state what + when; include keywords aiding selection. | specification | 2026-08-10 |
| `license` | Optional, stable. Name or reference to bundled license file. | specification | 2026-08-10 |
| `compatibility` | Optional, stable, max 500 chars. "Most skills do not need the compatibility field." | specification | 2026-08-10 |
| `metadata` | Optional, stable. **Map from string keys to STRING values only.** Clients may store non-spec properties; unique key names recommended. | specification | 2026-08-10 |
| **`allowed-tools`** | Optional. **Explicitly "(Experimental)": "Support for this field may vary between agent implementations."** Format: **space-separated string** (example: `allowed-tools: Bash(git:*) Bash(jq:*) Read`). **Spec names NO platforms that honor it.** | specification | 2026-08-10 |
| Body size | Progressive-disclosure budget: metadata ~100 tokens; instructions **"< 5000 tokens recommended"**; **"Keep your main SKILL.md under 500 lines."** | specification | 2026-08-10 |
| Progressive disclosure | Discovery (name+description at startup) -> Activation (full SKILL.md) -> Execution (bundled files on demand). Conventional subdirs: `scripts/`, `references/`, `assets/`. References relative from skill root, one level deep. | specification | 2026-08-10 |
| Directory structure | Only SKILL.md required; other files permitted; subdirs are recommendations. | specification | 2026-08-10 |
| **Official validator** | YES: **`skills-ref`** (reference library in agentskills/agentskills). `skills-ref validate ./my-skill`. **PyPI package `skills-ref` 0.1.1**, author `<email>`, Apache-2.0, python >=3.11, deps click + strictyaml. Commands: validate, read-properties (JSON), to-prompt (generates `<available_skills>` XML). **Caveat: README says "intended for demonstration purposes only... not meant to be used in production" -- conformance reference, not a supported production linter.** | specification ; github.com/agentskills/agentskills/skills-ref ; PyPI | 2026-08-10 |
| Governance | Site + repo: "originally developed by Anthropic, released as an open standard... open to contributions." **No LF/AAIF mention on either primary source; AAIF projects page does NOT list Agent Skills** (blog claims of AAIF stewardship unsupported). Code Apache-2.0, docs CC-BY-4.0. | agentskills.io ; repo ; aaif.io/projects | 2026-08-10 |
| Adoption | **46 clients** on the official Client Showcase (counted from page source 2026-08-10): Claude/Claude Code, ChatGPT & Codex, GitHub Copilot, VS Code, Cursor, Gemini CLI, Goose, OpenCode, OpenHands, Junie, Amp, Roo Code, Kiro, Factory, Letta, Databricks, Snowflake, Pulumi, Spring AI, Tabnine, Mistral Vibe, Laravel Boost, Trae, Ona, Mux, Qodo, others. Repo active (commits 2026-08-09). | agentskills.io/clients ; gh api | 2026-08-10 |

## npx skills on Windows (STD-N)

| Claim | Finding | Source | Retrieved |
|---|---|---|---|
| What it is | npm package `skills`, latest **1.5.22** (2026-08-05). Repo vercel-labs/skills. Launched 2026-01-20 (Vercel changelog confirms). | registry ; repo ; changelog | 2026-08-10 |
| Commands | add, use, list/ls, find, update, remove/rm, init. Flags -g, -a agent, -s skill, --copy, -y, --all. | README | 2026-08-10 |
| Canonical dir (project) | **`.agents/skills`** -- hardcoded `UNIVERSAL_SKILLS_DIR = '.agents/skills'` in src/constants.ts; most agents in src/agents.ts set skillsDir '.agents/skills'. | constants.ts ; agents.ts | 2026-08-10 |
| Canonical dir (global) | **INCONSISTENT in source:** most agents use `~/.agents/skills`; the `universal` entry uses xdgConfig-derived `~/.config/agents/skills` on Windows without XDG_CONFIG_HOME. Bug reports observe `~/.agents/skills/`. | agents.ts | 2026-08-10 |
| Linking model | Symlink mode (default): copies skill to canonical dir, links agent dirs to it. --copy forces copies. | README ; installer.ts | 2026-08-10 |
| **Windows: junction, not symlink -- DEFINITIVE** | `createSymlink()`: `const symlinkType = platform() === 'win32' ? 'junction' : undefined;` with absolute target for junctions. **Elevation/Developer Mode NOT required** (junctions are unprivileged; zero tracker issues for symlink-EPERM/developer-mode). Link failure silently degrades to copyDirectory (`symlinkFailed: true`). | src/installer.ts ; issue search | 2026-08-10 |
| Windows issues (real, not link-permission) | update fails on paths with spaces (#1119), Node under Program Files (#1457, #941), update -g all-fail (#840), DEP0190 (#723), lockfile not tracked on Windows (#399), CRLF hash mismatch breaking committed lockfiles (#781), WSL resolves to `<WINDIR>`\.agents (#1054). All OPEN. | gh issue search | 2026-08-10 |
| Linking bugs (cross-platform) | copy-when-not-asked (#745); installs to .agents/skills without creating .claude/skills link (#744 #851 #1355); global install skips ~/.claude/skills with multiple agents (#1412); update re-symlinks --copy skills (#1199); breakage when agent skills dir is itself a symlink (#481 #456 #293 #209). All OPEN. | gh issue search | 2026-08-10 |
| Agents it links | **76 entries in src/agents.ts** (75 real + universal), incl. claude-code, codex, cursor, opencode, gemini-cli, github-copilot, goose, windsurf, zed, warp, devin, cline, continue, junie, roo, droid, amp, antigravity, augment, kilo, qwen-code, trae, replit, ona, mux, openhands, openclaw, mistral-vibe, grok, kiro-cli, zencoder... | agents.ts | 2026-08-10 |
| **Private/local sources: YES** | Sources: GitHub shorthand, full GitHub/GitLab URLs, deep tree URLs, any git URL incl. SSH, **local filesystem paths** (./my-local-skills), direct SKILL.md/archive URLs. Private repos use existing git/gh/SSH auth. Public registry NOT required. Caveats: #474 private GitLab clone fail; #561 lockfile stores absolute paths for local sources. | README ; issues | 2026-08-10 |
| Registry/site | skills.sh.json controls display grouping on skills.sh ONLY -- "does not change how the skills CLI installs." No self-hosted registry mechanism. Telemetry on by default (DISABLE_TELEMETRY=1). Docs contain NO Windows page, NO symlink/junction page -- Windows behavior only knowable from source. | skills.sh/docs | 2026-08-10 |

## UNVERIFIED

- Agent Skills governance under AAIF/LF -- contradicted by primary sources; treat as Anthropic-originated open standard with no confirmed foundation stewardship.
- Agent Skills spec version number (no version identifier/changelog/effective date on the spec page -- cannot pin "spec vN").
- Which platforms honor `allowed-tools` (spec names none; per-client verification not performed).
- AGENTS.md size guidance (none exists in any primary source; any cap is local convention).
- AGENTS.md adoption figures (~5-8 months stale).
- npx skills global universal path on Windows (two conflicting definitions in source; not empirically resolved).
- Whether junction creation ever fails on this specific setup (cross-volume/network profiles; silent copy-fallback would mask it).
- No npm-published official validator (only PyPI skills-ref).

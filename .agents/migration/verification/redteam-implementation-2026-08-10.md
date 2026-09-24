# Red-team of the finished implementation -- findings + dispositions (2026-08-10)

Operator-mandated ("if this completes do a red team on the implementation"). One
fresh-context fable adversary (the ratified ceiling exception), 12 assigned attack
surfaces + self-chosen, read-only, every checker re-executed live. Verdict: **0
CRITICAL, 3 HIGH, 6 MEDIUM, 7 NOTE.** All HIGHs + the cheap MEDIUMs fixed the same
session (dispositions below); the rest are pinned to the cutover commit or accepted
with reasoning.

| ID | Finding (condensed) | Severity | Disposition |
|---|---|---|---|
| H1 | Fixture-freeze justification was a bare-substring match on FREEZE-NOTE -- fail-open forever for any file ever named | HIGH | **FIXED**: justification now requires the exact `<filename> <new-sha256>` pair; FREEZE-NOTE format doc updated |
| H2 | D9 default-refuse self-attesting: a 2-field registry edit (scope=project, write_surface=none) would emit the broker into all configs, checkers green | HIGH | **FIXED**: validate FAILs any server with write_tools/tool_filter but write_surface!=present + name-pins robinhood-trading/claudewatch as write-capable |
| H3 | "45->54 growth made loud" did not cover the broker (canary:manual); a NEW server mutator would fall through the hook to a permission prompt | HIGH | **FIXED**: pretrade-token-gate default-BLOCKs any unknown mcp__robinhood-trading__* name (registry 34-read set mirrored as pretrade_lib.READ_TOOLS); regression T42 green (unknown blocks, read set flows) |
| M1 | UNMIGRATED-STUB guard becomes a content-based kill switch post-cutover (any file quoting the legacy marker silently drops from sync/driftcheck) | MED | **PINNED to the S6 legacy-deletion commit**: flip skip->FAIL (no legitimate stubs remain) |
| M2 | S6 completeness grep too narrow (misses gen-codex-agents/config, engine-detect, consolidate-canon + price-fetcher.md references) | MED | **PINNED to cutover**: widened grep + the 2 content rewires added to the cutover checklist (HANDOFF) |
| M3 | 2 vacuous manifest tests undeclared + hot-md-check happy-path-only undeclared | MED | **FIXED**: test_note added to session-integrity-check, auto-count-sync, hot-md-check |
| M4 | Arm flag not path-bound -- any guarded write could consume a pending arm | MED | **FIXED**: guard-paths arms are now PATH-BOUND (flag must name the target; mismatch blocks AND consumes; empty flag blocks); T41 still green |
| M5 | BOOTSTRAP counts row contradicted AGENTS.md (named private/ as a counts source) outside the sanctioned contradiction point | MED | **FIXED**: row now DECLINEs counts off-Claude; BOOTSTRAP regenerated (4,387 B) |
| M6 | validate's "every config" inverse sweep skipped opencode.json | MED | **FIXED**: opencode.json server-name sweep added |
| N1 | gen-mcp-configs Bash-layer writes to guarded files (named self-interpretation) | NOTE | ACCEPTED with the adversary's reasoning (committed reviewed generator != ad-hoc heredoc; inputs+code both X26-guarded; outputs policed) |
| N2 | EDGAR PII removal is working-tree scope; PII persists in committed history and other private files; conformance clones carry full history | NOTE | ACCEPTED + scoped here (no remote; local-only exposure); named in the operator report's accepted-risks understanding |
| N3 | Canary WARN-on-spawn-failure fail-open | NOTE | ACCEPTED (read-only auth-free servers only; loud print; edgar FAILs the moment it enumerates) |
| N4 | 3 stale pointers (.claude/skills/CLAUDE.md "canonical" wording; AGENTS.md evidence-hierarchy at derived path; briefs/guard-paths sync-skills glob row) | NOTE | **PINNED to cutover** (one-liners) |
| N5 | sync never-touch not enforced on write path; dead NEVER_TOUCH_FILES constant | NOTE | **FIXED**: never-touch enforced in migrated_canon_skills() (write path) |
| N6 | opencode.json lacks EDGAR_IDENTITY plumbing note; .mcp.json _generated/_refused keys untested vs Claude parser | NOTE | OPEN (verify at next Claude session start; trivial fallback = move keys into a comment-bearing README) |
| N7 | auto-commit-disabled flag still ON at phase-4-verified | NOTE | Removed at session close (this session's close checklist) |

**Attack 9 (routing deltas)**: the adversary's REJECT-as-is case for CP1/CP5 is
recorded verbatim in the agent transcript and summarized in DELTA-REVIEW-TABLE
context: CP1's gate-absorption is outside the pre-registered improvement direction
(gate was not name-only at baseline) and n=3 cannot resolve it; recommendation =
re-run CP1+CP5 at n=5 with 2 paraphrases each before approving, or approve with a
written monitoring trigger. This goes to the operator WITH the delta table -- the
approval stays typed + default-REJECT.

**SOLID verdicts** (no findings): truncation math incl. fresh-clone 32,768 default
(worst chain 22,580 B); Tier-A dispatch semantics byte-preserved in derived skills;
briefs leak-free + control-vague discriminates by construction; fixture re-pin
instance sound; precedence contract intact; live consistency all green.

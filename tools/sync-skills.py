#!/usr/bin/env python3
"""
sync-skills.py -- Mission Four (2026-05-15): mirror .claude/skills/ -> .agents/skills/

Codex CLI discovers skills at .agents/skills/<name>/SKILL.md (V1 verified per
developers.openai.com/codex/skills). This script syncs Claude-native skill bodies
to the Codex-discoverable mirror, applying a thin frontmatter adapter:

  - strips `allowed-tools` field (Claude-specific permission model; not used by Codex)
  - preserves `name`, `description`, `arguments`, `argument-hint`, `user-invocable`
  - co-copies ALL companion files verbatim (every file except SKILL.md)
  - no skill currently excluded (uap renamed to corpus + frontmatter added 2026-05-21)

The adapter handles two YAML syntaxes for allowed-tools:
  - bracket-array: allowed-tools: [Read, Edit, Write, Bash, ...]
  - bare comma-list: allowed-tools: Read, Edit, Write, Bash, ...

Body content (post-frontmatter markdown) preserved byte-exact.

CLI:
  python tools/sync-skills.py                 # full sync, all 16 mission skills
  python tools/sync-skills.py --check         # assert idempotency (exit 1 if any diff)
  python tools/sync-skills.py --quick --scope <path>  # single-file update
  python tools/sync-skills.py --verbose       # full per-file run log
  python tools/sync-skills.py --hook          # PostToolUse hook mode: read stdin JSON,
                                              # extract tool_input.file_path, sync that
                                              # skill if path is in .claude/skills/

Idempotency: re-runs produce zero diff if source unchanged.
Line-count warning gate: emits WARN to stderr for any SKILL.md >= 850 lines (HARD DRIFT at 900).
Exit code: 0 success; 1 idempotency-check failure; 2 source error.

Run output: stderr only. There is NO state-file log (no .claude/state/sync-skills-<date>.log
or equivalent). The verbose/check flags surface all transitions via stderr; if persistent
audit is needed, redirect to a file at the caller (e.g., `python tools/sync-skills.py
--verbose 2>>.claude/state/sync-skills-runs.log`). Mission Four-FIX M2 clarification 2026-05-16.
"""
import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", os.getcwd()))
SOURCE_ROOT = VAULT_ROOT / ".claude" / "skills"
TARGET_ROOT = VAULT_ROOT / ".agents" / "skills"

EXCLUDED_SKILLS = {
    "_archive",  # archived skills should not appear in Codex skill discovery
    # uap removed from exclusion 2026-05-21 (renamed to corpus + frontmatter added; now Codex-eligible)
}
LINE_WARN_THRESHOLD = 850  # HARD DRIFT at 900 per X2 vault-audit classifier
ALLOWED_TOOLS_RE = re.compile(r"^allowed-tools\s*:.*$\n?", re.MULTILINE)


def parse_frontmatter(text: str) -> tuple[str, str]:
    """Split markdown into (frontmatter_block, body). Frontmatter delimited by ---.
    Returns ('', text) if no frontmatter found.
    """
    if not text.startswith("---\n"):
        return ("", text)
    # Find closing ---
    end_idx = text.find("\n---\n", 4)
    if end_idx == -1:
        return ("", text)
    frontmatter = text[:end_idx + 5]  # include closing ---\n
    body = text[end_idx + 5:]
    return (frontmatter, body)


def strip_allowed_tools(frontmatter: str) -> str:
    """Remove the allowed-tools line from frontmatter, regardless of YAML syntax.
    Handles bracket-array (allowed-tools: [Read, Edit, ...]) and bare comma-list
    (allowed-tools: Read, Edit, ...). Single-line forms only; multiline arrays
    would need a YAML parser (not currently used in any Osanwe skill).
    """
    return ALLOWED_TOOLS_RE.sub("", frontmatter)


def adapt_skill_md(source_text: str) -> str:
    """Adapt a Claude SKILL.md for Codex consumption. Strips allowed-tools field,
    preserves all other frontmatter and body byte-exact.
    """
    fm, body = parse_frontmatter(source_text)
    if not fm:
        return source_text  # no frontmatter to adapt; pass through
    adapted_fm = strip_allowed_tools(fm)
    return adapted_fm + body


def sync_skill_dir(source_dir: Path, target_dir: Path, verbose: bool = False) -> dict:
    """Sync one skill directory. Adapts SKILL.md, copies all companion files verbatim.
    Returns stats dict: {'skill_md_written': bool, 'ref_files_written': int,
                         'skill_md_skipped': bool, 'line_count': int, 'warn': bool}
    """
    stats = {"skill_md_written": False, "ref_files_written": 0,
             "skill_md_skipped": False, "line_count": 0, "warn": False}

    target_dir.mkdir(parents=True, exist_ok=True)

    # Adapt SKILL.md
    source_skill_md = source_dir / "SKILL.md"
    target_skill_md = target_dir / "SKILL.md"
    if source_skill_md.exists():
        source_text = source_skill_md.read_text(encoding="utf-8")
        adapted_text = adapt_skill_md(source_text)
        line_count = adapted_text.count("\n") + (0 if adapted_text.endswith("\n") else 1)
        stats["line_count"] = line_count
        if line_count >= LINE_WARN_THRESHOLD:
            stats["warn"] = True
            print(f"WARN: {source_dir.name}/SKILL.md at {line_count} lines (>= {LINE_WARN_THRESHOLD}; HARD DRIFT at 900)",
                  file=sys.stderr)

        # Idempotency: skip write if target identical
        if target_skill_md.exists() and target_skill_md.read_text(encoding="utf-8") == adapted_text:
            stats["skill_md_skipped"] = True
            if verbose:
                print(f"  SKIPPED-IDENTICAL {source_dir.name}/SKILL.md ({line_count} lines)")
        else:
            target_skill_md.write_text(adapted_text, encoding="utf-8")
            stats["skill_md_written"] = True
            if verbose:
                print(f"  COPIED {source_dir.name}/SKILL.md ({line_count} lines)")

    # Copy ALL companion files verbatim (no adapter), excluding SKILL.md (adapted above).
    # Broadened 2026-05-25 from ref-*.md-only to every file (recursive) so third-party skills
    # (mattpocock, ECC) keep their companions: tests.md, mocking.md, CONTEXT-FORMAT.md,
    # config.json, nested scripts/, etc. Relative structure preserved under target_dir;
    # bytes-compared (companions may be non-text).
    for companion in sorted(source_dir.rglob("*")):
        if not companion.is_file() or companion.name == "SKILL.md":
            continue
        rel = companion.relative_to(source_dir)
        # Skip hidden files/dirs (any path part starting with "."): runtime/tooling
        # cruft such as .audit/ logs, .git, .DS_Store -- not skill companions.
        if any(part.startswith(".") for part in rel.parts):
            continue
        target_ref = target_dir / rel
        source_bytes = companion.read_bytes()
        if target_ref.exists() and target_ref.read_bytes() == source_bytes:
            if verbose:
                print(f"  SKIPPED-IDENTICAL {source_dir.name}/{rel.as_posix()}")
            continue
        target_ref.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(companion, target_ref)
        stats["ref_files_written"] += 1
        if verbose:
            print(f"  COPIED {source_dir.name}/{rel.as_posix()}")

    return stats


def sync_all(check_only: bool = False, verbose: bool = False) -> int:
    """Sync all skills. Returns exit code (0 success, 1 idempotency failure, 2 source error)."""
    if not SOURCE_ROOT.exists():
        print(f"ERROR: source not found: {SOURCE_ROOT}", file=sys.stderr)
        return 2

    TARGET_ROOT.mkdir(parents=True, exist_ok=True)

    total_skills = 0
    total_skill_md_written = 0
    total_skill_md_skipped = 0
    total_ref_files_written = 0
    total_warns = 0
    excluded_count = 0

    for source_dir in sorted(SOURCE_ROOT.iterdir()):
        if not source_dir.is_dir():
            continue
        if source_dir.name in EXCLUDED_SKILLS:
            excluded_count += 1
            if verbose:
                print(f"  EXCLUDED {source_dir.name} (Mission Four user-decision; deferred to Four-bis)")
            continue
        total_skills += 1
        target_dir = TARGET_ROOT / source_dir.name
        stats = sync_skill_dir(source_dir, target_dir, verbose=verbose)
        if stats["skill_md_written"]:
            total_skill_md_written += 1
        if stats["skill_md_skipped"]:
            total_skill_md_skipped += 1
        total_ref_files_written += stats["ref_files_written"]
        if stats["warn"]:
            total_warns += 1

    # Summary
    print(f"sync-skills: {total_skills} skills processed (excluded {excluded_count})", file=sys.stderr)
    print(f"  SKILL.md: {total_skill_md_written} written, {total_skill_md_skipped} skipped-identical",
          file=sys.stderr)
    print(f"  companion files: {total_ref_files_written} written", file=sys.stderr)
    if total_warns:
        print(f"  WARN: {total_warns} skill(s) at >= {LINE_WARN_THRESHOLD} lines", file=sys.stderr)

    if check_only:
        # Idempotency assertion: any write is a failure
        if total_skill_md_written > 0 or total_ref_files_written > 0:
            print(f"CHECK FAILED: {total_skill_md_written} SKILL.md + {total_ref_files_written} companion files diverged",
                  file=sys.stderr)
            return 1
        print("CHECK OK: zero diff (idempotent)", file=sys.stderr)
    return 0


def sync_scope(scope_path: Path, verbose: bool = False) -> int:
    """Sync a single source file (auto-fire hook mode). Resolves to skill dir."""
    try:
        rel = scope_path.relative_to(SOURCE_ROOT)
    except ValueError:
        # Scope outside .claude/skills/; nothing to sync
        return 0
    if not rel.parts:
        return 0
    skill_name = rel.parts[0]
    if skill_name in EXCLUDED_SKILLS:
        if verbose:
            print(f"  EXCLUDED {skill_name} (auto-fire scope ignored)", file=sys.stderr)
        return 0
    source_dir = SOURCE_ROOT / skill_name
    target_dir = TARGET_ROOT / skill_name
    if not source_dir.is_dir():
        return 0
    sync_skill_dir(source_dir, target_dir, verbose=verbose)
    return 0


def hook_mode() -> int:
    """PostToolUse hook entry point. Reads JSON from stdin, extracts file_path,
    syncs the corresponding skill if path is inside .claude/skills/.
    Always exits 0 (best-effort; never blocks the hook chain).
    """
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # silent-pass on malformed stdin
    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return 0
    tool_input = data.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "")
    if not file_path:
        return 0
    fp = Path(file_path)
    # Only act if the edited file is under .claude/skills/ (avoid infinite loop
    # via .agents/skills/ writes triggering another sync)
    try:
        fp.relative_to(SOURCE_ROOT)
    except ValueError:
        return 0
    sync_scope(fp, verbose=False)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Mirror .claude/skills/ to .agents/skills/ for Codex")
    parser.add_argument("--check", action="store_true",
                        help="Idempotency check: exit 1 if any divergence")
    parser.add_argument("--quick", action="store_true",
                        help="Quick mode for auto-fire hook (no summary print)")
    parser.add_argument("--scope", type=Path, default=None,
                        help="Single source file to sync (skill-dir resolution from path)")
    parser.add_argument("--verbose", action="store_true",
                        help="Per-file run log")
    parser.add_argument("--hook", action="store_true",
                        help="PostToolUse hook mode: read stdin JSON, sync scoped skill")
    args = parser.parse_args()

    if args.hook:
        return hook_mode()
    if args.scope:
        return sync_scope(args.scope, verbose=args.verbose)
    return sync_all(check_only=args.check, verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main())

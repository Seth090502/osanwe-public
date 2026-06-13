#!/usr/bin/env python3
"""
PostToolUse orphan-on-create soft-blocker (Plan #2 sec 2).

When a NEW file is Written to wiki/, Calendar/, Efforts/, or Atlas/, requires
that the file be back-linked from at least one other vault file BEFORE the
write completes -- enforcing symmetric back-linking discipline at write time.

This is a SOFT BLOCK: bypassable via CLAUDE_VAULT_LAX_ORPHAN=1 (logged).
Skill-author overhead: writer skill must compose at least one back-link in
same tool batch (or set the env var when batch ordering forces orphan transient).

Skipped paths: EXEMPT_PATHS (per-file exempts: CLAUDE.md, CLAUDE.local.md,
docs/PROJECT-OSANWE-PACKET.md, docs/VAULT-HANDOFF-V16.md, tools/migrations/...),
EXEMPT_DIRS (by-design exempts: _archive/, _quarantine/, .claude/, .git/,
node_modules/, .checkpoints/, _templates/, applications/, prompts/, daily/,
private/, challenges/, maintenance/, .obsidian/, .smart-env/), files that
already existed before this Write (only blocks on creation).
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, date
from pathlib import Path

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", os.getcwd()))
EXEMPT_DIRS = {
    "_archive", "_quarantine", ".claude", ".agents", ".codex", ".git", "node_modules", ".checkpoints",
    "_templates", "applications", "prompts", "daily", "private", "challenges",
    "maintenance", ".obsidian", ".smart-env",
}
EXEMPT_PATHS = {
    "CLAUDE.md", "CLAUDE.local.md",
    "AGENTS.md", "AGENTS.override.md", "AGENTS.override.md.template",
    "docs/PROJECT-OSANWE-PACKET.md", "docs/VAULT-HANDOFF-V16.md",
    "docs/CODEX-COMPATIBILITY.md",
    "tools/CODEX_TOOLS_UNVERIFIED.md",
    "tools/migrations/README.md",
    "tools/migrations/group-30-verification-report.md",
}
VALIDATE_DIRS = {"wiki", "Calendar", "Efforts", "Atlas"}


def log_bypass(rel_path: Path, reason: str):
    bypass_log = VAULT_ROOT / ".claude" / "state" / f"bypasses-{date.today().isoformat()}.log"
    bypass_log.parent.mkdir(exist_ok=True, parents=True)
    with bypass_log.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} orphan-check {rel_path}: {reason}\n")


def is_new_file(fp: Path) -> bool:
    """Detect if fp was just created (untracked in git AND in working tree)."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", "--", str(fp.relative_to(VAULT_ROOT))],
            cwd=str(VAULT_ROOT),
            capture_output=True,
            text=True,
            timeout=8,
        )
        if result.returncode != 0:
            return False
        out = result.stdout.strip()
        return out.startswith("??")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
        return False


def has_inbound_link(stem: str) -> bool:
    """Check if any file in the vault wikilinks to <stem>.

    Uses regex (`git grep -E`) with end-anchor patterns to avoid the prefix-match
    false-positive (e.g., stem='foo' should not match [[foo-bar]]).
    Matches: [[stem]] OR [[stem|...]] OR [[stem#...]]
    """
    # Escape regex metacharacters in stem
    safe_stem = re.escape(stem)
    # Match [[<stem>]] or [[<stem>|...]] or [[<stem>#...]] -- closing bracket OR pipe OR hash
    pattern = f"\\[\\[{safe_stem}(\\]\\]|\\||#)"
    try:
        result = subprocess.run(
            ["git", "grep", "-l", "-E", pattern, "--", "*.md", "*.base"],
            cwd=str(VAULT_ROOT),
            capture_output=True,
            text=True,
            timeout=8,
        )
        if result.returncode in (0, 1):
            lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
            return len(lines) > 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return True  # silent fail: allow when grep unavailable


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    tool_name = data.get("tool_name", "")
    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)
    # Only block on Write tool (file creation); Edit/MultiEdit modify existing files
    if tool_name != "Write":
        sys.exit(0)

    fp = Path(file_path)
    if fp.suffix not in (".md", ".base"):
        sys.exit(0)

    try:
        rel_path = fp.relative_to(VAULT_ROOT)
    except ValueError:
        sys.exit(0)

    if any(part in EXEMPT_DIRS for part in rel_path.parts):
        sys.exit(0)
    rel_str = str(rel_path).replace("\\", "/")
    if rel_str in EXEMPT_PATHS:
        sys.exit(0)
    if rel_path.parts and rel_path.parts[0] not in VALIDATE_DIRS:
        sys.exit(0)

    if not is_new_file(fp):
        sys.exit(0)

    stem = fp.stem.lower()
    if has_inbound_link(stem):
        sys.exit(0)

    if os.environ.get("CLAUDE_VAULT_LAX_ORPHAN") == "1":
        log_bypass(rel_path, "lax-orphan bypass; new file with 0 inbound")
        sys.exit(0)

    msg = (
        f"vault-audit: NEW file {rel_path} has 0 inbound wikilinks (orphan-on-create).\n"
        "Add a back-link from a MOC, peer note, or [[hot]] before next write,\n"
        "OR set CLAUDE_VAULT_LAX_ORPHAN=1 to defer (logs to .claude/state/bypasses-<date>.log).\n"
    )
    print(msg, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
PostToolUse wikilink validator.

Reads PostToolUse hook JSON from stdin, identifies the file just modified, and
runs vault-audit.py --scope on that file. Exits 2 with stderr if broken wikilinks
are introduced.

Bypass: set CLAUDE_VAULT_BYPASS_VALIDATOR=1 in env (bypass logged to
.claude/state/bypasses-<date>.log for retrospective audit).

Skipped paths: .claude/, _archive/, _quarantine/, .git/, node_modules/,
.checkpoints/, non-md/non-base files. Full EXEMPT_DIRS set defined as a
constant; this docstring lists the names; the constant is the source of truth.
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, date
from pathlib import Path

VAULT_ROOT = Path(os.environ.get("VAULT_ROOT", os.getcwd()))
EXEMPT_DIRS = {"_archive", "_quarantine", ".claude", ".agents", ".codex", ".git", "node_modules", ".checkpoints"}


def log_bypass(rel_path: Path, broken_count: int):
    """Log a validator bypass for retrospective audit."""
    bypass_log = VAULT_ROOT / ".claude" / "state" / f"bypasses-{date.today().isoformat()}.log"
    bypass_log.parent.mkdir(exist_ok=True, parents=True)
    with bypass_log.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} wikilink-check {rel_path}: {broken_count} broken\n")


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
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

    try:
        result = subprocess.run(
            ["python", str(VAULT_ROOT / "tools" / "vault-audit.py"), "--scope", str(rel_path)],
            cwd=str(VAULT_ROOT),
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        sys.exit(0)

    output = result.stdout
    match = re.search(r"\| Broken wikilinks \| (\d+) \|", output)
    if not match:
        sys.exit(0)

    broken_count = int(match.group(1))
    if broken_count == 0:
        sys.exit(0)

    if os.environ.get("CLAUDE_VAULT_BYPASS_VALIDATOR") == "1":
        log_bypass(rel_path, broken_count)
        sys.exit(0)

    broken_section = re.search(
        r"## Broken Wikilinks\s*\n\s*Found \*\*\d+\*\* broken links\.\s*\n(.+?)(?=\n## )",
        output, re.DOTALL,
    )
    msg = f"vault-audit: {broken_count} broken wikilink(s) in {rel_path}\n"
    if broken_section:
        msg += broken_section.group(1).strip() + "\n"
    msg += (
        "\nFix options: (1) correct target name; (2) de-link to plain text; "
        "(3) wrap illustrative wikilinks in `inline code` or fenced ``` blocks; "
        "(4) for auto-memory targets use [[memory:<stem>]] grammar.\n"
        "Bypass: CLAUDE_VAULT_BYPASS_VALIDATOR=1 (logs to .claude/state/bypasses-<date>.log)\n"
    )
    print(msg, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()

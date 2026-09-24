#!/usr/bin/env python3
"""append-only-check.py -- PreToolUse guard for the four append-only ledgers.

AGENTS.md names sessions-log.md, decision-log.md, execute-or-decline.md and
insight-stream.md as append-only. Until now that rule was INSTRUCTION-ONLY:
tools/pre-write-validator.py EXEMPTS Calendar/decisions/ outright, and guard-paths.sh
never covered it. Nothing mechanically stopped a rewrite-instead-of-append, and with
per-write auto-commit plus PR-on-Stop the damage lands in history before anyone looks.

The rule enforced here is deliberately DUMB: the current bytes must survive as a strict
PREFIX of the proposed content. Appending passes. Rewriting, reordering, truncating, or
editing a prior entry fails. It has no opinion about schema, ordering or content -- those
belong to the skills that own each ledger. A hook that understood the ledgers would be a
second source of truth for them, which is a worse problem than the one it solves.

Gate: wiki/research/gates/gate-b-append-only-ledger-guard-2026-08-12.md (BUILD-JUSTIFIED).

CONTRACT
  exit 0  allow (append, new file, not a guarded path, or any internal error -- FAIL-OPEN)
  exit 2  BLOCK, with the byte loss and the remedy on stderr

Known residual: Bash-layer writes bypass PreToolUse entirely (X30). `echo x >> log.md`
from a shell is unaffected. This closes the TOOL-layer path, which is the one a language
model actually uses when told to edit a file.

Bypass: CLAUDE_APPEND_ONLY_BYPASS=1 (logged, like every other sanctioned bypass).
Note (2026-08-13): the env bypass is only settable at session launch or by a test
harness -- a Bash `export` cannot reach a sibling tool call's hook process. Ledger
protocol changes are therefore made by APPENDING an amendment section, never by
editing the header in place (see execute-or-decline.md 2026-08-13 for the precedent).
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent

# Exactly four files. Relative to the vault root, forward slashes.
GUARDED = {
    "Calendar/decisions/sessions-log.md",
    "Calendar/decisions/decision-log.md",
    "Calendar/decisions/execute-or-decline.md",
    "wiki/insight-stream.md",
}

BYPASS_ENV = "CLAUDE_APPEND_ONLY_BYPASS"
TEST_ENV = "CLAUDE_APPEND_ONLY_TEST"     # set by tools/test-append-only.py so suite
                                         # bypasses are distinguishable in the log


def log_bypass(rel_path, reason):
    try:
        state = VAULT_ROOT / ".claude" / "state"
        state.mkdir(parents=True, exist_ok=True)
        line = "%s append-only-check %s: %s\n" % (
            date.today().isoformat(), rel_path, reason)
        with open(state / ("bypasses-%s.log" % date.today().isoformat()),
                  "a", encoding="ascii", errors="replace") as f:
            f.write(line)
    except Exception:
        pass


def simulate(tool_name, tool_input, fp):
    """Post-write content, mirroring tools/pre-write-validator.py's reconstruction.

    Judging the intent (an Edit that 'looks like' an append) is not good enough -- the
    question is what the file will actually CONTAIN afterwards.
    """
    if tool_name == "Write":
        return tool_input.get("content", "")
    if not fp.exists():
        return None
    try:
        current = fp.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if tool_name == "Edit":
        old_str = tool_input.get("old_string", "")
        new_str = tool_input.get("new_string", "")
        if not old_str:
            return current
        if tool_input.get("replace_all", False):
            return current.replace(old_str, new_str)
        return current.replace(old_str, new_str, 1)
    if tool_name == "MultiEdit":
        out = current
        for edit in tool_input.get("edits", []):
            old_str = edit.get("old_string", "")
            new_str = edit.get("new_string", "")
            if not old_str:
                continue
            if edit.get("replace_all", False):
                out = out.replace(old_str, new_str)
            else:
                out = out.replace(old_str, new_str, 1)
        return out
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)                      # fail-open: never block on our own malformed input

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "")
    if not file_path or tool_name not in ("Write", "Edit", "MultiEdit"):
        sys.exit(0)

    try:
        rel = Path(file_path).resolve().relative_to(VAULT_ROOT).as_posix()
    except Exception:
        sys.exit(0)
    if rel not in GUARDED:
        sys.exit(0)

    if os.environ.get(BYPASS_ENV) == "1":
        suffix = " (test-suite)" if os.environ.get(TEST_ENV) == "1" else ""
        log_bypass(rel, "CLAUDE_APPEND_ONLY_BYPASS=1%s" % suffix)
        sys.exit(0)

    fp = Path(file_path)
    if not fp.exists():
        sys.exit(0)                      # creating the ledger: nothing to preserve
    try:
        current = fp.read_text(encoding="utf-8")
    except Exception:
        sys.exit(0)
    if not current:
        sys.exit(0)

    new_content = simulate(tool_name, tool_input, fp)
    if new_content is None:
        sys.exit(0)

    if new_content.startswith(current):
        sys.exit(0)                      # pure append (or a no-op)

    # Report what would actually be lost, so the message is actionable rather than scolding.
    keep = 0
    for a, b in zip(current, new_content):
        if a != b:
            break
        keep += 1
    lost = len(current) - keep

    sys.stderr.write(
        "APPEND-ONLY VIOLATION (blocked): %s\n"
        "  This file is append-only (AGENTS.md). The proposed %s does not preserve the\n"
        "  existing content as a prefix: %d of %d existing bytes would be altered or lost\n"
        "  (first divergence at byte %d).\n"
        "  -> Append your new entry at the END instead.\n"
        "  -> To CORRECT an earlier entry, append an AMENDMENT entry that supersedes it --\n"
        "     see the 2026-08-11 amendment in decision-log.md for the precedent.\n"
        "  -> Deliberate, logged override: set %s=1 and retry.\n"
        % (rel, tool_name, lost, len(current), keep, BYPASS_ENV))
    sys.exit(2)


if __name__ == "__main__":
    main()

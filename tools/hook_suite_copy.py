#!/usr/bin/env python3
"""Build a throwaway copy of this repository for the hook test suites (D54).

tools/test-prevention-arch.sh and the hooks it exercises were written against the
live vault: the suite wrote its fixtures into the live tree, and several hooks
hard-code the vault root (the three write validators, vault-audit, the X26 guard's
arm flag and log, the stop hook's `cd`, the order gate's import path). Run as
they were, the manifest checks that checkall.py executes on every run wrote into
the vault they were checking.

This copies the tracked files of a source tree into a destination directory,
then, in the COPY ONLY, points every hard-coded vault root in hook and tool code
at the copy, and makes the copy its own empty git repository (the stop hook exits
early outside one). The source tree is only read. It never copies the private
areas, even if one were tracked, and it skips large non-Markdown data files that
no hook reads.

Usage: python tools/hook_suite_copy.py <source-root> <dest-dir>
Prints the destination root in forward-slash Windows form; exits non-zero on any failure.
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

NEVER_DIRS = {"private", "finance", "credentials", ".raw"}   # at any depth
MAX_DATA_BYTES = 1_000_000          # non-Markdown files above this are data no hook reads
CODE_DIRS = (".claude/", ".agents/", ".codex/", "tools/")
CODE_SUFFIXES = {".py", ".sh", ".js", ".mjs", ".cjs", ".json", ".ps1", ".cmd", ".toml", ".yaml", ".yml"}
MARKER = ".osanwe-hook-suite-copy"   # test-prevention-arch.sh runs in copy mode only beside this
GIT_ENV = {k: v for k, v in os.environ.items() if k not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")}


def never_copy(rel):
    parts = rel.lower().split("/")
    name = parts[-1]
    return (any(p in NEVER_DIRS for p in parts[:-1]) or name.startswith(".env") or name == "auth.json"
            or name.endswith(".local.md"))


def rewrite_roots(text, dest):
    """Point every spelling of the live vault root at the copy."""
    win = str(dest).replace("/", "\\")                      # C:\Users\...\copy
    fwd = win.replace("\\", "/")                            # C:/Users/.../copy
    msys = "/" + fwd[0].lower() + fwd[2:]                   # /c/Users/.../copy
    end = r"(?![A-Za-z0-9_-])"
    pairs = [
        (r"c:\\\\/path/to/vault" + end, win.replace("\\", "\\\\")),   # /path/to/vault (escaped)
        (r"c:\\/path/to/vault" + end, win),                            # /path/to/vault
        (r"c://path/to/vault" + end, fwd),                             # /path/to/vault
        (r"/c//path/to/vault" + end, msys),                            # /path/to/vault
    ]
    n = 0
    for pattern, repl in pairs:                                     # every case variant
        text, k = re.subn(pattern, lambda m, r=repl: r, text, flags=re.IGNORECASE)
        n += k
    return text, n


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: hook_suite_copy.py <source-root> <dest-dir>")
    src = Path(sys.argv[1]).resolve()
    dest = Path(sys.argv[2]).resolve()
    if dest == src or src in dest.parents:
        raise SystemExit("refusing: the copy must not be inside the source tree")
    if dest.exists() and any(dest.iterdir()):
        raise SystemExit("refusing: destination is not empty")
    listing = subprocess.run(["git", "-C", str(src), "ls-files", "-z"], capture_output=True, check=True,
                             env=GIT_ENV)
    files = [f for f in listing.stdout.decode("utf-8", "replace").split("\0") if f]
    copied = skipped = rewritten = 0
    for rel in files:
        if never_copy(rel):
            skipped += 1
            continue
        s = src / rel
        if not s.is_file():
            continue                                        # deleted in the working tree
        if s.stat().st_size > MAX_DATA_BYTES and not rel.endswith(".md"):
            skipped += 1
            continue
        d = dest / rel
        d.parent.mkdir(parents=True, exist_ok=True)
        if rel.startswith(CODE_DIRS) and s.suffix.lower() in CODE_SUFFIXES:
            raw = s.read_bytes()
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                shutil.copyfile(s, d)
            else:
                new, n = rewrite_roots(text, dest)
                if n:
                    rewritten += 1
                d.write_bytes(new.encode("utf-8"))
        else:
            shutil.copyfile(s, d)
        copied += 1
    (dest / ".claude" / "state").mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(dest)], check=True, env=GIT_ENV)
    (dest / MARKER).write_text("throwaway copy for the hook test suites; safe to delete\n", encoding="ascii")
    sys.stderr.write("hook_suite_copy: %d files copied, %d skipped, %d code files re-rooted\n"
                     % (copied, skipped, rewritten))
    print(str(dest).replace("\\", "/"))


if __name__ == "__main__":
    main()

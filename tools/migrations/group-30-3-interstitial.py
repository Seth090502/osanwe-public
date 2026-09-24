#!/usr/bin/env python
"""Group 30.3 interstitial: sessions-log <private-file> remove-brackets.

Applies Group 28 Step 1b ruling that was not propagated to this span.
The wikilink [[<private-file>]] was ruled REMOVE_BRACKETS (reason:
target file does not exist on disk; aspirational reference). The span
appears in Calendar/decisions/sessions-log.md and was likely introduced
by a session retrospective appended after the Group 28 atomic commit,
so escaped the original scope.

Change: [[<private-file>]] -> <private-file> (single occurrence
asserted pre-replace).

Phases:
  A  pre-flight
  C  F11 set
  E  edit + gate (single bytes.replace)
  F  commit + post-commit gates
  K  F11 clear

Findings applied: F11, F14, F16, F17, F19.
"""

import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import re
import subprocess
from pathlib import Path

VAULT = Path("/path/to/vault")
TARGET = VAULT / "Calendar/decisions/sessions-log.md"
F11 = VAULT / ".claude/state/auto-commit-disabled"
EXPECTED_PARENT = "bee0103"

BEFORE = b"[[<private-file>]]"
AFTER = b"<private-file>"

COMMIT_BODY = """rebuild(links): Group 30.3 -- sessions-log <private-file> remove-brackets

Applies Group 28 Step 1b ruling that was not propagated to this span.
The wikilink [[<private-file>]] was ruled REMOVE_BRACKETS (reason:
target file does not exist on disk; aspirational reference). The span
appears in Calendar/decisions/sessions-log.md and was likely introduced
by a session retrospective appended after the Group 28 atomic commit,
so escaped the original scope.

Change: [[<private-file>]] -> <private-file> (single occurrence
asserted pre-replace).

Precedent: v14 Part II sec 2.9 Group 28 Step 1b <private-file> ruling.
Findings applied: F11, F14, F17, F19.
"""


def run_bytes(cmd, check=False):
    return subprocess.run(cmd, capture_output=True, check=check)


def halt(msg):
    sys.stderr.write(f"HALT: {msg}\n")
    sys.exit(2)


def phase_A():
    print("Phase A: pre-flight")
    r = run_bytes(["git", "-C", str(VAULT), "rev-parse", "HEAD"])
    head = r.stdout.decode("ascii", errors="replace").strip()
    if not head.startswith(EXPECTED_PARENT):
        halt(f"HEAD {head[:12]} != expected parent {EXPECTED_PARENT}")
    if not TARGET.is_file():
        halt(f"target file missing: {TARGET}")
    if F11.exists():
        halt(f"F11 flag already present")
    r = run_bytes(["git", "-C", str(VAULT), "status", "--short"])
    lines = r.stdout.decode("utf-8", errors="replace").splitlines()
    unexpected = []
    for ln in lines:
        if ln.startswith("?? "):
            path = ln[3:].strip()
            if path.startswith("Calendar/daily/") and path.endswith(".md"):
                continue
            if path == "tools/migrations/group-30-verification-report.md":
                continue
            unexpected.append(ln)
        else:
            unexpected.append(ln)
    if unexpected:
        halt(f"unexpected working tree entries: {unexpected}")
    print(f"  HEAD={head[:12]}  target present  tree clean modulo untracked")


def phase_C():
    print("Phase C: F11 set")
    F11.parent.mkdir(parents=True, exist_ok=True)
    F11.write_bytes(b"group-30.3\n")
    if not F11.exists():
        halt("F11 flag did not persist")
    print(f"  {F11} created")


def phase_E():
    print("Phase E: bytes.replace [[<private-file>]] -> <private-file>")
    content = TARGET.read_bytes()
    occurrences = content.count(BEFORE)
    if occurrences != 1:
        halt(f"expected 1 [[<private-file>]] occurrence, got {occurrences}")
    new_content = content.replace(BEFORE, AFTER, 1)
    # Gates:
    # - BEFORE must drop to 0 (one bracket-wrapped occurrence replaced)
    # - AFTER count is unchanged (BEFORE contains AFTER as substring once;
    #   count stays the same after replace)
    # - byte delta == -4 (two '[' + two ']' removed)
    if new_content.count(BEFORE) != 0:
        halt(f"post-replace still contains BEFORE: {new_content.count(BEFORE)}")
    if new_content.count(AFTER) != content.count(AFTER):
        halt(f"after-count drift: pre={content.count(AFTER)} post={new_content.count(AFTER)}")
    delta = len(new_content) - len(content)
    if delta != -4:
        halt(f"delta != -4 (removed 2 '[' + 2 ']'): got {delta}")
    TARGET.write_bytes(new_content)
    print(f"  {delta:+d} bytes delta  1 occurrence replaced")


def phase_F():
    print("Phase F: commit + post-commit gates")
    rel = str(TARGET.relative_to(VAULT)).replace("\\", "/")
    r = run_bytes(["git", "-C", str(VAULT), "add", "--", rel])
    if r.returncode != 0:
        halt(f"git add failed: {r.stderr.decode('utf-8', errors='replace')}")
    r = run_bytes(["git", "-C", str(VAULT), "diff", "--cached", "--name-only"])
    staged = [ln for ln in r.stdout.decode("utf-8", errors="replace").splitlines() if ln.strip()]
    if staged != [rel]:
        halt(f"stage scope wrong: {staged}")

    r = run_bytes([
        "git", "-C", str(VAULT),
        "commit", "-m", COMMIT_BODY,
    ])
    if r.returncode != 0:
        halt(f"git commit failed: {r.stderr.decode('utf-8', errors='replace')}")

    r = run_bytes(["git", "-C", str(VAULT), "rev-parse", "HEAD"])
    new_head = r.stdout.decode("ascii", errors="replace").strip()
    print(f"  new HEAD: {new_head[:12]}")

    r = run_bytes([
        "git", "-C", str(VAULT),
        "log", "-1", "--format=", "--name-status", "HEAD",
    ])
    rows = [ln for ln in r.stdout.decode("utf-8", errors="replace").splitlines() if ln.strip()]
    matched = [ln for ln in rows if re.match(r"^[AMDR]", ln)]
    if len(matched) != 1:
        halt(f"name-status count {len(matched)}, expected 1. rows: {rows}")
    if not matched[0].startswith("M\t"):
        halt(f"expected M row, got: {matched[0]!r}")

    r = run_bytes([
        "git", "-C", str(VAULT),
        "log", "-1", "--format=%B", "HEAD",
    ])
    body = r.stdout
    if b"Co-Authored-By" in body or b"Co-authored-by" in body:
        halt("Co-Authored-By present")

    # Behavioral: committed content contains AFTER and not BEFORE
    r = run_bytes([
        "git", "-C", str(VAULT),
        "show", f"HEAD:{rel}",
    ])
    if r.returncode != 0:
        halt(f"git show failed: {r.stderr.decode('utf-8', errors='replace')}")
    committed = r.stdout
    if BEFORE in committed:
        halt("committed content still contains [[<private-file>]]")
    if AFTER not in committed:
        halt("committed content does not contain <private-file>")

    r = run_bytes(["git", "-C", str(VAULT), "status", "--short"])
    lines = r.stdout.decode("utf-8", errors="replace").splitlines()
    unexpected = []
    for ln in lines:
        if ln.startswith("?? "):
            path = ln[3:].strip()
            if path.startswith("Calendar/daily/") and path.endswith(".md"):
                continue
            if path == "tools/migrations/group-30-verification-report.md":
                continue
            unexpected.append(ln)
        else:
            unexpected.append(ln)
    if unexpected:
        halt(f"tree not clean: {unexpected}")

    print(f"  gates: name-status=1, M only, behavioral PASS, Co-Authored-By absent")
    return new_head


def phase_K():
    print("Phase K: F11 clear")
    if F11.exists():
        F11.unlink()
    if F11.exists():
        halt("F11 did not clear")
    print(f"  {F11} removed")


def main():
    print("=== Group 30.3 interstitial ===")
    phase_A()
    phase_C()
    phase_E()
    new_head = phase_F()
    phase_K()
    print(f"GROUP 30.3 COMPLETE  commit={new_head[:12]}")


if __name__ == "__main__":
    main()

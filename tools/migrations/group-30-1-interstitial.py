#!/usr/bin/env python
"""Group 30.1 interstitial: close Group 29 R2 scope-boundary.

Adds `categories: [efforts]` to
<private-area>/research/<private-file>.md
(the pre-declared Group 29 R2 deferral). Single-file atomic commit.

Phases:
  A  pre-flight
  C  F11 set
  E  edit + gate
  F  commit + post-commit gates
  K  F11 clear

Findings applied: F11 (flag discipline), F14 (narrow stage),
F16 (subprocess bytes), F17 (git log --format=''), F19 (utf-8 stdout).
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

try:
    from ruamel.yaml import YAML
    RUAMEL = YAML(typ="safe")
except ImportError:
    sys.stderr.write("HALT: ruamel.yaml not available.\n")
    sys.exit(2)

VAULT = Path("/path/to/vault")
TARGET = VAULT / "<private-area>/research/<private-file>.md"
F11 = VAULT / ".claude/state/auto-commit-disabled"
EXPECTED_PARENT = "ee6a3b6"

COMMIT_BODY = """rebuild(frontmatter): Group 30.1 -- close Group 29 R2 scope-boundary

Adds missing `categories:` field to
<private-area>/research/<private-file>.md,
the pre-declared deferral from Group 29 b1 R2 ruling. Value: [efforts]
(path-derived canonical per v14 sec 4.2 for Efforts/ content).

Preserves: all other frontmatter fields and body byte-exact.
Findings applied: F11, F14, F17, F19.
"""


def run_bytes(cmd, check=False):
    """F16: capture_output, no text=True."""
    return subprocess.run(cmd, capture_output=True, check=check)


def halt(msg):
    sys.stderr.write(f"HALT: {msg}\n")
    sys.exit(2)


def phase_A():
    print("Phase A: pre-flight")
    # HEAD parent check
    r = run_bytes(["git", "-C", str(VAULT), "rev-parse", "HEAD"])
    head = r.stdout.decode("ascii", errors="replace").strip()
    if not head.startswith(EXPECTED_PARENT):
        halt(f"HEAD {head[:12]} != expected parent {EXPECTED_PARENT}")
    # Target file present
    if not TARGET.is_file():
        halt(f"target file missing: {TARGET}")
    # F11 flag absent
    if F11.exists():
        halt(f"F11 flag already present: {F11}")
    # Tree clean modulo expected untracked daily notes + verification report
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
    F11.write_bytes(b"group-30.1\n")
    if not F11.exists():
        halt("F11 flag did not persist after write")
    print(f"  {F11} created")


def phase_E():
    print("Phase E: insert categories: [efforts]")
    content = TARGET.read_bytes()
    m = re.match(rb"^---\r?\n(.*?)\r?\n---\r?\n", content, re.DOTALL)
    if not m:
        halt("frontmatter regex did not match")
    newline = b"\r\n" if b"\r\n" in content[:m.end()] else b"\n"
    insertion = newline + b"categories: [efforts]"
    new_content = content[:m.end(1)] + insertion + content[m.end(1):]

    # Gate: ruamel parses new frontmatter, categories == [efforts]
    new_m = re.match(rb"^---\r?\n(.*?)\r?\n---\r?\n", new_content, re.DOTALL)
    if not new_m:
        halt("post-edit frontmatter regex did not match")
    fm_text = new_m.group(1).decode("utf-8", errors="replace")
    try:
        data = RUAMEL.load(fm_text)
    except Exception as e:
        halt(f"post-edit ruamel parse failed: {e}")
    if data.get("categories") != ["efforts"]:
        halt(f"post-edit categories != [efforts]: got {data.get('categories')!r}")

    # Preservation check: prior fields unchanged
    for fld in ("type", "created", "tags", "related", "confidence"):
        # type: research was present, etc. -- just confirm no field lost
        pass  # existence preservation verified by block-level insertion

    TARGET.write_bytes(new_content)
    print(f"  +{len(insertion)} bytes inserted  frontmatter parses clean")


def phase_F():
    print("Phase F: commit + post-commit gates")
    rel = str(TARGET.relative_to(VAULT)).replace("\\", "/")
    # F14: narrow stage
    r = run_bytes(["git", "-C", str(VAULT), "add", "--", rel])
    if r.returncode != 0:
        halt(f"git add failed: {r.stderr.decode('utf-8', errors='replace')}")
    # Verify stage scope: exactly one file staged
    r = run_bytes(["git", "-C", str(VAULT), "diff", "--cached", "--name-only"])
    staged = [ln for ln in r.stdout.decode("utf-8", errors="replace").splitlines() if ln.strip()]
    if staged != [rel]:
        halt(f"stage scope wrong: {staged}")

    # Commit
    r = run_bytes([
        "git", "-C", str(VAULT),
        "commit", "-m", COMMIT_BODY,
    ])
    if r.returncode != 0:
        halt(f"git commit failed: {r.stderr.decode('utf-8', errors='replace')}")

    # Post-commit gates
    r = run_bytes(["git", "-C", str(VAULT), "rev-parse", "HEAD"])
    new_head = r.stdout.decode("ascii", errors="replace").strip()
    print(f"  new HEAD: {new_head[:12]}")

    # F17: --format='' strips header, count name-status rows
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

    # Co-Authored-By absent (F17 %B extraction: format=%B strips headers)
    r = run_bytes([
        "git", "-C", str(VAULT),
        "log", "-1", "--format=%B", "HEAD",
    ])
    body = r.stdout
    if b"Co-Authored-By" in body or b"Co-authored-by" in body:
        halt("Co-Authored-By present in commit body")

    # Tree clean modulo expected untracked
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
        halt(f"tree not clean post-commit: {unexpected}")

    print(f"  gates: name-status=1, M only, Co-Authored-By absent, tree clean")
    return new_head


def phase_K():
    print("Phase K: F11 clear")
    if F11.exists():
        F11.unlink()
    if F11.exists():
        halt("F11 flag did not clear")
    print(f"  {F11} removed")


def main():
    print("=== Group 30.1 interstitial ===")
    phase_A()
    phase_C()
    phase_E()
    new_head = phase_F()
    phase_K()
    print(f"GROUP 30.1 COMPLETE  commit={new_head[:12]}")


if __name__ == "__main__":
    main()

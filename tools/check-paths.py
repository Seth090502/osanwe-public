#!/usr/bin/env python3
"""check-paths.py -- MSYS/POSIX path-hygiene checker (SOTA pass, house law:
promote a bug class to a failing checker after the third bite).

Scans hook/command surfaces for MSYS-style absolute paths (/c/Users/...) that
Windows-native interpreters (python.exe) cannot resolve -- the exact defect that
silently killed the Stop-hook, session-start smart-emit, and 25 Claude hook
registrations before being fixed.

Checks (fail = exit 1):
  C1  .claude/settings.json: no '/c/<drive-letter>/' in any command string
      (bash entries may legitimately keep POSIX style ONLY for bash builtins;
      python/python3 invocations must be drive-letter form)
  C2  .claude/hooks/*.sh + tools/*.sh: `python /c/...` invocations (bash keeps
      cwd-relative or C:/ forms for python children)
  C3  generated MCP configs (.claude/mcp*.json, .codex/, opencode.json):
      command arrays must not carry /c/-style interpreter paths
  C4  .agents/hooks/recipes/**: documented install snippets must not teach
      /c/-style python invocations

Usage: python tools/check-paths.py
  (an earlier draft advertised a --fix-settings flag; no argument parsing
   exists, so any argument is ignored and the script only reports -- noted
   2026-09-21)
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MSYS_IN_PYTHON = re.compile(r"(python3?)\s+(/c/[A-Za-z])")
MSYS_ANY = re.compile(r"/c/[A-Za-z]/")
ALLOWED_BASH_SELF = re.compile(r"^\s*cd\s+/c/", re.M)  # bash cd /c/x is fine


def check_settings():
    problems = []
    p = ROOT / ".claude" / "settings.json"
    if not p.is_file():
        return problems, []
    data = json.loads(p.read_text(encoding="utf-8"))
    fixed = []

    def walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, f"{path}[{i}]")
        elif isinstance(obj, str) and "python" in obj[:12].lower() and "/c/" in obj:
            if MSYS_IN_PYTHON.search(obj):
                problems.append(f"settings{path}: {obj[:90]}")

    walk(data)
    return problems, fixed


def check_shell_scripts():
    problems = []
    for d in (ROOT / ".claude" / "hooks", ROOT / "tools"):
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.sh")):
            text = f.read_text(encoding="utf-8", errors="replace")
            for m in MSYS_IN_PYTHON.finditer(text):
                line_no = text.count("\n", 0, m.start()) + 1
                problems.append(f"{f.relative_to(ROOT)}:{line_no}: {m.group(0)}")
    return problems


def check_mcp_configs():
    problems = []
    candidates = [ROOT / ".claude" / ".mcp.json", ROOT / ".mcp.json",
                  ROOT / "opencode.json"]
    candidates += list((ROOT / ".codex").glob("*.json")) if (ROOT / ".codex").is_dir() else []
    for p in candidates:
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for m in MSYS_IN_PYTHON.finditer(text):
            problems.append(f"{p.name}: {m.group(0)}")
    return problems


def check_recipes():
    problems = []
    rd = ROOT / ".agents" / "hooks" / "recipes"
    if not rd.is_dir():
        return problems
    for f in sorted(rd.rglob("*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        for m in MSYS_IN_PYTHON.finditer(text):
            line_no = text.count("\n", 0, m.start()) + 1
            problems.append(f"{f.relative_to(ROOT)}:{line_no}: {m.group(0)}")
    return problems


def main():
    all_problems = []
    s, _ = check_settings()
    all_problems += [f"[C1] {x}" for x in s]
    all_problems += [f"[C2] {x}" for x in check_shell_scripts()]
    all_problems += [f"[C3] {x}" for x in check_mcp_configs()]
    all_problems += [f"[C4] {x}" for x in check_recipes()]

    if all_problems:
        print("check-paths: FAIL")
        for x in all_problems[:30]:
            print("  " + x)
        return 1
    print("check-paths: OK (no unresolvable MSYS paths in interpreter invocations)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

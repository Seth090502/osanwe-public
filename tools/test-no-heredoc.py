#!/usr/bin/env python3
"""The heredoc guard must block a heredoc and pass an ordinary command.

Drives the real hook as a subprocess, the way Claude Code does: JSON on stdin,
exit 2 to block, exit 0 to allow.

The false-positive cases matter as much as the blocks. A guard on the shell that
refuses ordinary work gets switched off, and then it guards nothing.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / ".claude" / "hooks" / "no-heredoc.py"

BLOCK, ALLOW = "block", "allow"

CASES = [
    # --- must block: every heredoc shape ---
    (BLOCK, "plain heredoc", "cat <<EOF\nhello\nEOF"),
    (BLOCK, "quoted delimiter", "python - <<'PY'\nprint(1)\nPY"),
    (BLOCK, "double-quoted delimiter", 'cat <<"EOF"\nhi\nEOF'),
    (BLOCK, "dash form", "cat <<-EOF\n\thi\nEOF"),
    (BLOCK, "space before delimiter", "cat << EOF\nhi\nEOF"),
    (BLOCK, "the exact shape that hung twice",
     "python - \"$S/x.json\" <<'NOPE'\nimport json\nNOPE"),
    (BLOCK, "here-string", "grep foo <<< \"$bar\""),
    (BLOCK, "heredoc later in a compound command",
     "cd /tmp && ls && cat <<EOF\nx\nEOF"),
    (BLOCK, "backslash-escaped delimiter", "cat <<\\EOF\nx\nEOF"),

    # --- the evasions an independent review found in the first version ---
    # Its regex ran over text with single-quoted runs stripped out, so the
    # delimiter vanished and what matched was the first word of the BODY. Every
    # case below was ALLOWED by that version and opens a real heredoc in bash.
    (BLOCK, "E1 quoted delimiter, body starts with a digit",
     "cat <<'EOF' > out.txt\n1 hello\nEOF"),
    (BLOCK, "E1 quoted delimiter, piped",
     "cat <<'EOF' | cat\nx\nEOF"),
    (BLOCK, "E1 the real shape from the corpus",
     "python - <<'PY' 2>&1 | tail -20\n1\nPY"),
    (BLOCK, "E1 the shape that hung, with a brace first in the body",
     "python - \"$S/x.json\" <<'NOPE'\n{}\nimport json\nNOPE"),
    (BLOCK, "E1 inside a command substitution",
     "x=$(cat <<'EOF'\n1x\nEOF\n)"),
    (BLOCK, "E1 after a full-line comment",
     "# comment\ncat <<'EOF'\n1x\nEOF"),
    (BLOCK, "E2 an apostrophe earlier on the opener line",
     "echo \"it's fine\" && cat <<'EOF'\nhello\nEOF"),
    (BLOCK, "E3 numeric delimiter", "cat <<1\nx\n1"),
    (BLOCK, "E3 punctuation delimiter", "cat <<@\nx\n@"),
    (BLOCK, "E3 dollar-quoted delimiter", "cat <<$'EOF'\nx\nEOF"),
    (BLOCK, "E3 empty delimiter", "cat <<\"\"\nx\n"),
    (BLOCK, "E4 CRLF with a quoted delimiter",
     "cat <<'EOF'\r\n1\r\nEOF\r\n"),

    # --- must allow: ordinary work ---
    (ALLOW, "an ordinary command", "ls -la /path/to/vault"),
    (ALLOW, "a single input redirect", "python script.py < input.txt"),
    (ALLOW, "running a file, which is the way through this hook",
     "python /tmp/scratch/build.py --out /tmp/out"),
    (ALLOW, "a pipeline with quoting", "grep -n 'foo <<EOF bar' file.txt | head -3"),
    (ALLOW, "a comment mentioning a heredoc", "# do not use cat <<EOF here\nls"),
    (ALLOW, "left shift inside a python -c string",
     "python -c \"print(1 << 4)\""),
    (ALLOW, "git log with angle brackets in a format",
     "git log --format='%h <%ae>' -3"),
    (ALLOW, "a multi-line script with no heredoc",
     "cd /tmp\nfor f in *.txt; do\n  wc -l \"$f\"\ndone"),

    # --- false positives the first version had, measured against the real
    # corpus. A shell guard that refuses ordinary work gets switched off.
    (ALLOW, "left shift by a named operand", "python -c \"print(1 << SHIFT)\""),
    (ALLOW, "arithmetic left shift", "if (( x << 2 )); then echo hi; fi"),
    (ALLOW, "searching for conflict markers", "grep -rn \"<<<<<<<\" ."),
    (ALLOW, "a here-string inside double quotes",
     "grep -n \">>>\\|<<<\" tools/claude-shim.ps1"),
    (ALLOW, "angle brackets in a usage string",
     "echo \"usage: prog <<file>>\""),
    (ALLOW, "a sed program containing <<", "sed \"s/<<X/Y/\" f.txt"),
    (ALLOW, "a perl left shift", "perl -e \"print 1 << Foo;\""),
    (ALLOW, "an inline comment mentioning a heredoc",
     "ls -la  # do not use cat <<EOF here"),
]


def run(cmd, tool_name="Bash"):
    payload = json.dumps({"tool_name": tool_name, "tool_input": {"command": cmd}})
    p = subprocess.run([sys.executable, str(HOOK)], input=payload,
                       capture_output=True, text=True, timeout=60)
    return p.returncode, (p.stderr or "").strip()


def main():
    if not HOOK.is_file():
        print("FAIL: hook not found at %s" % HOOK)
        return 1

    width = max(len(name) for _, name, _ in CASES)
    passed = failed = 0
    for want, name, cmd in CASES:
        code, err = run(cmd)
        got = BLOCK if code == 2 else ALLOW if code == 0 else "exit %d" % code
        ok = got == want
        passed += ok
        failed += not ok
        note = ""
        if not ok:
            note = "   <-- expected %s" % want
        elif want == BLOCK:
            note = "   %s" % err.splitlines()[0].replace("no-heredoc: BLOCKED -- ", "")
        print("  %-4s  %-*s  %-5s%s" % ("PASS" if ok else "FAIL", width, name, got, note))

    # Non-Bash tools and malformed payloads.
    extra = []
    code, _ = run("cat <<EOF\nx\nEOF", tool_name="Write")
    extra.append(("a heredoc in a non-Bash tool is not this hook's business", code == 0))
    p = subprocess.run([sys.executable, str(HOOK)], input="not json",
                       capture_output=True, text=True, timeout=60)
    extra.append(("unparseable payload fails closed", p.returncode == 2))
    p = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(
        {"tool_name": "Bash", "tool_input": {"command": 12}}),
        capture_output=True, text=True, timeout=60)
    extra.append(("a non-string command fails closed", p.returncode == 2))
    p = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(
        {"tool_name": "Bash", "tool_input": {}}),
        capture_output=True, text=True, timeout=60)
    extra.append(("no command at all is not a block", p.returncode == 0))
    p = subprocess.run([sys.executable, str(HOOK)], input="",
                       capture_output=True, text=True, timeout=60)
    extra.append(("EMPTY stdin fails closed", p.returncode == 2))
    p = subprocess.run([sys.executable, str(HOOK)], input="   \n  ",
                       capture_output=True, text=True, timeout=60)
    extra.append(("whitespace-only stdin fails closed", p.returncode == 2))
    p = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(
        {"tool_name": ["Bash"], "tool_input": {"command": "cat <<EOF\nx\nEOF"}}),
        capture_output=True, text=True, timeout=60)
    extra.append(("a non-string tool_name fails closed", p.returncode == 2))

    # The Codex copy must stay byte-identical, because a guard on one harness
    # only is a guard with a documented way around it.
    codex = ROOT / ".codex" / "hooks" / "no-heredoc.py"
    extra.append(("the Codex copy exists", codex.is_file()))
    if codex.is_file():
        extra.append(("the two hook copies are byte-identical",
                      codex.read_bytes() == HOOK.read_bytes()))
        p = subprocess.run([sys.executable, str(codex)], input=json.dumps(
            {"tool_name": "Bash", "tool_input": {"command": "cat <<'EOF'\n1\nEOF"}}),
            capture_output=True, text=True, timeout=60)
        extra.append(("the Codex copy blocks a quoted heredoc", p.returncode == 2))

    print()
    for name, ok in extra:
        passed += ok
        failed += not ok
        print("  %-4s  %s" % ("PASS" if ok else "FAIL", name))

    print()
    print("  %d passed, %d failed, of %d" % (passed, failed, passed + failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

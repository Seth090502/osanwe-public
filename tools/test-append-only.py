"""Append-only ledger guard: the hook must block rewrites and allow appends.

D54. This test used to point at the live vault by absolute path -- the live hook,
the live decision log, the live execute-or-decline ledger -- so it could only ever
exercise production, and its bypass case wrote a real bypass line into the real
log. It now builds a throwaway copy of exactly what it needs under a temporary
directory and runs the COPY of the hook against COPIES of the ledgers. The hook
resolves its vault root from its own location, so a copied hook guards the copied
ledgers and writes any bypass log inside the copy. Nothing outside the temporary
directory is written. The ledgers are read once, to seed the copy.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent          # the tree this test lives in
WORK = Path(tempfile.mkdtemp(prefix="append-only-suite-"))
try:
    (WORK / "tools").mkdir(parents=True)
    (WORK / "Calendar" / "decisions").mkdir(parents=True)
    (WORK / "wiki").mkdir(parents=True)
    (WORK / ".claude" / "state").mkdir(parents=True)
    shutil.copy2(SRC / "tools" / "append-only-check.py", WORK / "tools" / "append-only-check.py")
    for name in ("decision-log.md", "execute-or-decline.md"):
        shutil.copy2(SRC / "Calendar" / "decisions" / name, WORK / "Calendar" / "decisions" / name)
    (WORK / "wiki" / "hot.md").write_text("placeholder\n", encoding="utf-8")

    HOOK = str(WORK / "tools" / "append-only-check.py")
    LEDGER = str(WORK / "Calendar" / "decisions" / "decision-log.md")
    EOD = str(WORK / "Calendar" / "decisions" / "execute-or-decline.md")
    UNGUARDED = str(WORK / "wiki" / "hot.md")
    cur = io.open(LEDGER, encoding="utf-8").read()

    def run(payload, env=None):
        e = dict(os.environ)
        e["CLAUDE_APPEND_ONLY_TEST"] = "1"   # tags suite bypasses in the log (diagnosed
                                             # 2026-08-13: untagged T6 runs read as real)
        if env:
            e.update(env)
        p = subprocess.run([sys.executable, HOOK], input=json.dumps(payload),
                           capture_output=True, text=True, encoding="utf-8", env=e)
        return p.returncode, (p.stderr or "").strip()

    cases = []
    # 1 pure append via Write
    cases.append(("append via Write", 0, {"tool_name": "Write", "tool_input": {"file_path": LEDGER, "content": cur + "\n### appended\n"}}))
    # 2 REWRITE (truncation) via Write  -> must BLOCK
    cases.append(("truncating rewrite", 2, {"tool_name": "Write", "tool_input": {"file_path": LEDGER, "content": "### only this\n"}}))
    # 3 edit an EARLIER entry via Edit -> must BLOCK
    first_head = cur[:200].split("\n")[1] if "\n" in cur[:200] else cur[:40]
    cases.append(("edit a prior line", 2, {"tool_name": "Edit", "tool_input": {"file_path": LEDGER, "old_string": first_head, "new_string": first_head + " TAMPERED"}}))
    # 4 Edit that appends at the very end -> must ALLOW
    tail = cur[-120:]
    cases.append(("append via Edit at tail", 0, {"tool_name": "Edit", "tool_input": {"file_path": LEDGER, "old_string": tail, "new_string": tail + "\n### appended via edit\n"}}))
    # 5 a DIFFERENT file entirely -> must ALLOW (not guarded)
    cases.append(("unguarded file", 0, {"tool_name": "Write", "tool_input": {"file_path": UNGUARDED, "content": "anything"}}))
    # 6 bypass env on a rewrite -> must ALLOW (logged, inside the copy)
    cases.append(("bypass on rewrite", 0, {"tool_name": "Write", "tool_input": {"file_path": LEDGER, "content": "### wiped\n"}}))
    # 7 flip a prior EOD row's Status in place -> must BLOCK (the amended row protocol
    #   closes rows by APPENDING a RESOLUTION row; in-place flips stay forbidden)
    cases.append(("EOD in-place status flip", 2, {"tool_name": "Edit", "tool_input": {"file_path": EOD, "old_string": "| 2026-07-07 | PENDING | -- |", "new_string": "| 2026-07-07 | EXECUTED | done |"}}))

    fails = 0
    for i, (name, want, payload) in enumerate(cases, 1):
        env = {"CLAUDE_APPEND_ONLY_BYPASS": "1"} if name.startswith("bypass") else None
        rc, err = run(payload, env)
        ok = (rc == want)
        if not ok:
            fails += 1
        print("%s  T%d %-26s want=%d got=%d" % ("PASS" if ok else "FAIL", i, name, want, rc))
        if rc == 2 and err:
            lines = err.split("\n")
            print("      %s" % (lines[2].strip() if len(lines) > 2 else lines[0].strip()))
    print("\n%d/%d passed" % (len(cases) - fails, len(cases)))
finally:
    shutil.rmtree(WORK, ignore_errors=True)
sys.exit(1 if fails else 0)

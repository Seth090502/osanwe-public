#!/usr/bin/env python3
"""Run the test files that pass from a clean copy of this repository: the same list, the same way, as CI.

Usage, from the repository root:

    pip install -r requirements.txt
    python tools/run-ci-suites.py

The list is .github/ci-suites.txt. Each file runs from its own directory with a 120-second limit, exactly as
.github/workflows/tests.yml runs it. Prints PASS or FAIL per file, with the last lines of any failure, and
exits 1 if any file fails. Standard library only.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIST = ROOT / ".github" / "ci-suites.txt"
TIMEOUT = 120


def main():
    suites = [line.strip() for line in LIST.read_text(encoding="utf-8").splitlines()
              if line.strip() and not line.startswith("#")]
    failed = []
    for rel in suites:
        path = ROOT / rel
        try:
            r = subprocess.run([sys.executable, path.name], cwd=path.parent, capture_output=True,
                               text=True, timeout=TIMEOUT)
            ok, detail = r.returncode == 0, (r.stdout + r.stderr).strip().splitlines()[-15:]
            why = "exit %d" % r.returncode
        except subprocess.TimeoutExpired:
            ok, detail, why = False, [], "timed out after %ds" % TIMEOUT
        if ok:
            print("PASS  " + rel)
        else:
            failed.append(rel)
            print("FAIL  %s (%s)" % (rel, why))
            for line in detail:
                print("      " + line)
    print()
    print("passed: %d   failed: %d" % (len(suites) - len(failed), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

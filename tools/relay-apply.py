#!/usr/bin/env python3
"""relay-apply -- READ-ONLY re-checker for relay worker edit PROPOSALS.

GATE-B: wiki/research/gates/gate-b-local-orchestration-program-2026-08-17.md.

The worker NEVER writes the vault; lane-editor legs emit proposed_edits in
their distillates. This tool re-verifies each proposal AT APPLY TIME (the leg
may have finished hours earlier): jail + allowlist re-check, sha recomputed
with the IDENTICAL recipe (relay_exec.file_sha_text -- one function, no
drift), unescape, uniqueness. It prints the exact Edit parameters for
APPLYABLE proposals; the orchestrator applies them with its OWN Edit tool, so
the full vault hook/validator chain fires and every write remains a frontier
act. THIS TOOL WRITES NOTHING.

  python tools/relay-apply.py --run <run_id> [--proposal PE-nn] [--json]

Exit: 0 all checked proposals APPLYABLE | 1 any STALE/NOT-UNIQUE/REFUSED |
      3 no run / no proposals.
"""
import argparse
import json
import os
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, os.path.join(TOOLS_DIR, "lib"))

import relay_schema  # noqa: E402
from relay_exec import (Executor, Refusal, file_sha_text,  # noqa: E402
                        _unescape, PROPOSE_ALLOW_PREFIXES,
                        PROPOSE_DENY_PREFIXES)


def check_proposal(pe):
    path = pe.get("path") or ""
    real = os.path.join(VAULT, path)
    row = {"id": pe.get("id"), "path": path, "why": pe.get("why")}
    # jail re-check via a throwaway executor (junction resolution + excluded
    # trees run exactly as they did worker-side)
    import tempfile
    ex = Executor(tempfile.mkdtemp(prefix="relay-apply-"), {}, {"objective": "apply-check"})
    try:
        real = ex._jail(path)
    except Refusal as exc:
        row.update(verdict="JAIL-REFUSED", reason=str(exc))
        return row
    rel = os.path.relpath(real, os.path.realpath(VAULT)).replace(os.sep, "/").lower()
    if any(rel.startswith(p) for p in PROPOSE_DENY_PREFIXES) or \
            not any(rel.startswith(p) for p in PROPOSE_ALLOW_PREFIXES):
        row.update(verdict="REFUSED", reason="outside the proposal allowlist")
        return row
    if not os.path.isfile(real):
        row.update(verdict="STALE", reason="file no longer exists")
        return row
    sha_now, content = file_sha_text(real)
    if sha_now != pe.get("before_sha256"):
        row.update(verdict="STALE",
                   reason="sha drift %s.. -> %s.. (file changed since the "
                          "worker's read; re-run the leg or re-verify by hand)"
                          % (str(pe.get("before_sha256"))[:12], sha_now[:12]))
        return row
    old_apply = _unescape(pe.get("old") or "")
    new_apply = _unescape(pe.get("new") or "")
    n = content.count(old_apply)
    if n != 1:
        row.update(verdict="NOT-UNIQUE" if n else "STALE",
                   reason="old occurs %d time(s)" % n)
        return row
    row.update(verdict="APPLYABLE",
               edit={"file_path": real.replace("/", os.sep),
                     "old_string": old_apply, "new_string": new_apply})
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--proposal")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    merged = os.path.join(VAULT, ".agents", "relay", args.run, "leg-merged.json")
    if not os.path.isfile(merged):
        print(relay_schema.dumps_ascii({"run": args.run,
                                        "error": "no merged distillate"}))
        return 3
    d = json.load(open(merged, encoding="ascii"))
    pes = d.get("proposed_edits") or []
    if args.proposal:
        pes = [p for p in pes if p.get("id") == args.proposal]
    if not pes:
        print(relay_schema.dumps_ascii({"run": args.run,
                                        "error": "no matching proposals"}))
        return 3
    rows = [check_proposal(pe) for pe in pes]
    report = {"run": args.run,
              "applyable": sum(1 for r in rows if r["verdict"] == "APPLYABLE"),
              "blocked": sum(1 for r in rows if r["verdict"] != "APPLYABLE"),
              "rows": rows}
    if args.json:
        print(relay_schema.dumps_ascii(report))
    else:
        for r in rows:
            print("%s %s %s -- %s" % (r["verdict"], r["id"], r["path"],
                                      r.get("reason", r.get("why", ""))),
                  file=sys.stderr)
        print(relay_schema.dumps_ascii(report))
    return 0 if report["blocked"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

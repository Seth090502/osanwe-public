#!/usr/bin/env python3
"""test-delegate.py -- acceptance suite for the local delegation lane.

Answers one question mechanically: can THIS local model do the work the lane is allowed
to give it? Replaces hand-grading ~20 transcripts (how both 2026-08 bake-offs were
judged; their runner scripts lived in a temp scratchpad and are gone).

Design rules that keep it from failing a BETTER model -- an eval that rejects a good
model is worse than no eval:
  - Expected values are authored from the fixture SOURCE TEXT, never from a transcript.
  - Graded on semantics: parsed-dict compare, set equality, key sets, ASCII + content
    superset. Never exact-match on free-form prose or table whitespace.
  - Output normalization (think-stripping, JSON extraction) runs in delegate.py BEFORE
    grading, so reasoning packaging is not scored as a wrong answer.
  - No LLM judge anywhere.

House convention: python tools/test-delegate.py runs all; --case <id> for one.
Exit 0 all-pass / 1 any-failure / 2 lane unavailable.
ASCII-only (Pattern 22). Deps: stdlib only.
"""
import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES_DIR = os.path.join(ROOT, "tools", "delegate-cases")
CASES = os.path.join(CASES_DIR, "cases.json")
PINS = os.path.join(CASES_DIR, "FIXTURES.sha256")
DELEGATE = os.path.join(ROOT, "tools", "delegate.py")


def _load_delegate():
    spec = importlib.util.spec_from_file_location("delegate_mod", DELEGATE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def verify_pins():
    """Frozen-fixture check, mirroring the .agents/migration/fixtures pin discipline.
    checkall's fixture-pins step hardcodes that other directory, so this suite carries
    its own."""
    import hashlib
    if not os.path.isfile(PINS):
        return ["FIXTURES.sha256 missing -- cases are not frozen"]
    bad = []
    for line in open(PINS, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        want, name = line.split(" *", 1)
        path = os.path.join(CASES_DIR, name)
        if not os.path.isfile(path):
            bad.append("%s: MISSING" % name)
            continue
        got = hashlib.sha256(open(path, "rb").read()).hexdigest()
        if got != want:
            bad.append("%s: changed (re-pin deliberately: %s %s)" % (name, name, got))
    return bad


def grade(case, out_text, parsed):
    kind = case["grade"]
    if kind == "dict_equal":
        if parsed is None:
            return False, "no JSON parsed"
        got = {k: parsed.get(k) for k in case["expect"]}
        return (got == case["expect"]), "got %s" % json.dumps(got, sort_keys=True)
    if kind == "set_equal":
        if parsed is None:
            return False, "no JSON parsed"
        got = parsed.get(case["key"])
        if not isinstance(got, list):
            return False, "key %r not a list: %r" % (case["key"], got)
        gs, es = {str(x).upper() for x in got}, {str(x).upper() for x in case["expect"]}
        return (gs == es), "got %s" % sorted(gs)
    if kind == "keys_exact":
        if parsed is None:
            return False, "no JSON parsed"
        gs, es = set(parsed.keys()), set(case["expect"])
        extra, missing = gs - es, es - gs
        return (not extra and not missing), "extra=%s missing=%s" % (sorted(extra), sorted(missing))
    if kind == "ascii_superset":
        if not out_text.isascii():
            bad = sorted({c for c in out_text if ord(c) > 127})[:6]
            return False, "non-ASCII present: %r" % bad
        low = out_text.lower()
        missing = [w for w in case["expect"] if w.lower() not in low]
        return (not missing), ("dropped content: %s" % missing if missing else "ascii + content ok")
    return False, "unknown grade kind %r" % kind


def run_case(case, model, timeout):
    path = os.path.join(CASES_DIR, case["file"])
    cmd = [sys.executable, DELEGATE, case["prompt"], "--file", path,
           "--leg", "acceptance:" + case["id"]]
    if case.get("json"):
        cmd.append("--json")
    if model:
        cmd += ["--model", model]
    cmd += ["--timeout", str(timeout)]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (p.stdout or "").strip()
    if p.returncode == 2:
        return None, None, p.returncode, (p.stderr or "").strip().splitlines()[:1]
    parsed = None
    if case.get("json"):
        try:
            env = json.loads(out)
            parsed = env.get("data", env)
        except ValueError:
            parsed = None
    else:
        out = re.sub(r"^local:.*?VERIFY BEFORE USE\s*", "", out, flags=re.S)
    return out, parsed, p.returncode, None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Acceptance suite for the local delegation lane.")
    ap.add_argument("--model", help="model tag to test (default: the configured one)")
    ap.add_argument("--case", help="run one case by id")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    pin_problems = verify_pins()
    for p in pin_problems:
        print("[PIN] %s" % p, file=sys.stderr)

    spec = json.load(open(CASES, encoding="utf-8"))
    cases = [c for c in spec["cases"] if not args.case or c["id"] == args.case]
    if not cases:
        print("no case matching %r" % args.case, file=sys.stderr)
        return 1

    dg = _load_delegate()
    cfg = dg.load_config()
    model = args.model or cfg.get("model")

    results, failed = [], 0
    for case in cases:
        out, parsed, rc, lane_err = run_case(case, args.model, args.timeout)
        if rc == 2:
            print("LANE UNAVAILABLE -- %s" % (lane_err or [""])[0], file=sys.stderr)
            return 2
        ok, detail = grade(case, out or "", parsed)
        results.append({"id": case["id"], "pass": ok, "detail": detail})
        if not ok:
            failed += 1
        print("[%s] %-20s %s" % ("PASS" if ok else "FAIL", case["id"], detail if not ok else ""))

    if args.as_json:
        print(json.dumps({"model": model, "passed": len(results) - failed,
                          "total": len(results), "pin_problems": pin_problems,
                          "results": results}, indent=1))
    else:
        print("\ntest-delegate: %d/%d PASS on %s" % (len(results) - failed, len(results), model))
    return 1 if (failed or pin_problems) else 0


if __name__ == "__main__":
    sys.exit(main())

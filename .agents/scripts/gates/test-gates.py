#!/usr/bin/env python3
"""test-gates.py -- positive AND negative controls for the cross-harness gate wrappers (D5/S4).

A gate that CRASHES must be distinguishable from one that BLOCKED: every negative
control asserts both a nonzero exit AND a reason substring in the output. Every
gate also has a should-ALLOW positive control (exit 0), so "gate always fails"
cannot masquerade as enforcement.

Controls (all through the .agents/scripts/gates/ wrappers -- the exact entry
points Tier-B harnesses are instructed to call):
  G1+ gate-eval --check on a committed real sheet         -> exit 0, "PASS:"
  G1- gate-eval --check on a missing sheet                -> exit 2, "missing"
  G2+ doctrine-lint on the live vault                     -> exit 0, "clean"
  G2- doctrine-lint with VAULT_ROOT at an empty fixture   -> nonzero, reason present
  G3+ pretrade-gate --help                                -> exit 0, "staged_order"
  G3- pretrade-gate on a nonexistent staged order         -> exit 2, "BLOCK"

Exit 0 = all controls hold. Run by checkall's hook-manifest step once the S4
manifest lands (each Tier-1 gate entry's test: block points here).
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
PY = sys.executable
# Golden sheet (maintained as a --check PASS exemplar since the /gate kit shipped).
# Do NOT point this at a recent operational sheet: sheets are append-only archival
# records whose prov: paths may legitimately vanish later (the 2026-08-10 migration
# sheet cited a generator the cutover itself deleted -- exactly that rot broke G1+).
REAL_SHEET = os.path.join("wiki", "research", "gates",
                          "gate-b-judgment-gates-build-2026-07-06.md")


def run(args, env_extra=None):
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    r = subprocess.run([PY] + args, capture_output=True, text=True, cwd=ROOT, env=env, timeout=180)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    fails = []

    def control(cid, desc, rc, out, want_rc, substr):
        rc_ok = (rc == want_rc) if isinstance(want_rc, int) else want_rc(rc)
        sub_ok = substr.lower() in out.lower()
        status = "PASS" if (rc_ok and sub_ok) else "FAIL"
        print("[%s] %s %s (exit=%s, wanted %s; substring %r %s)"
              % (status, cid, desc, rc, want_rc if isinstance(want_rc, int) else "nonzero",
                 substr, "found" if sub_ok else "MISSING"))
        if status == "FAIL":
            fails.append(cid)

    ge = os.path.join(HERE, "gate-eval.py")
    rc, out = run([ge, "--check", REAL_SHEET])
    control("G1+", "gate-eval --check real sheet allows", rc, out, 0, "PASS:")
    rc, out = run([ge, "--check", "wiki/research/gates/no-such-sheet-xx.md"])
    control("G1-", "gate-eval --check missing sheet blocks with reason", rc, out, 2, "missing")

    dl = os.path.join(HERE, "doctrine-lint.py")
    rc, out = run([dl])
    control("G2+", "doctrine-lint live vault clean", rc, out, 0, "clean")
    with tempfile.TemporaryDirectory() as tmp:
        rc, out = run([dl], env_extra={"VAULT_ROOT": tmp})
        control("G2-", "doctrine-lint empty fixture root fails with reason", rc, out,
                lambda c: c != 0, "cannot read")

    pg = os.path.join(HERE, "pretrade-gate.py")
    rc, out = run([pg, "--help"])
    control("G3+", "pretrade-gate --help exits 0", rc, out, 0, "staged_order")
    rc, out = run([pg, os.path.join(ROOT, "no", "such", "order.json")])
    control("G3-", "pretrade-gate unreadable order BLOCKS with reason", rc, out, 2, "BLOCK")

    if fails:
        print("test-gates: %d control(s) FAILED: %s" % (len(fails), fails))
        sys.exit(1)
    print("test-gates: all 6 controls hold (3 allow + 3 block-with-reason)")
    sys.exit(0)


if __name__ == "__main__":
    main()

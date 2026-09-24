#!/usr/bin/env python3
"""Cross-harness wrapper for the GATE judgment CLI (D5 layer 2).

Resolves VAULT_ROOT from this file's location (or honors an existing VAULT_ROOT
env), then delegates to the canonical tools/gate-eval.py with all args passed
through. Every harness runs gates through THIS entry point identically:

  python .agents/scripts/gates/gate-eval.py --compute <sheet>
  python .agents/scripts/gates/gate-eval.py --check <sheet>
  python .agents/scripts/gates/gate-eval.py --calibrate

Verdicts (DISCIPLINED/FOMO-SUSPECT/BLOCKED, FIRED/NOT-FIRED/INSUFFICIENT-EVIDENCE,
BUILD-JUSTIFIED/SHIP-FIRST/DECLINE) come only from the canonical script's rules
engine (tools/gate-rules.json) -- never from a model.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
env = dict(os.environ)
env.setdefault("VAULT_ROOT", ROOT)
r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "gate-eval.py")] + sys.argv[1:],
                   env=env, cwd=ROOT)
sys.exit(r.returncode)

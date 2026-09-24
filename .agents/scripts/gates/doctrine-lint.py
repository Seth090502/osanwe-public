#!/usr/bin/env python3
"""Cross-harness wrapper for the doctrine-lint gate CLI (D5 layer 2).

Resolves VAULT_ROOT from this file's location (or honors an existing VAULT_ROOT
env), then delegates to the canonical tools/doctrine-lint.py with all args passed
through. Fails closed on doctrine tamper (ref-note fingerprint mismatch).
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
env = dict(os.environ)
env.setdefault("VAULT_ROOT", ROOT)
r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "doctrine-lint.py")] + sys.argv[1:],
                   env=env, cwd=ROOT)
sys.exit(r.returncode)

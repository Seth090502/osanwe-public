#!/usr/bin/env python3
"""Cross-harness wrapper for the pretrade execution gate CLI (D5 layer 2; T11 staircase).

Resolves VAULT_ROOT from this file's location (or honors an existing VAULT_ROOT env),
then delegates to the canonical tools/pretrade_gate.py with all args passed through.
This gates trade EXECUTION (GATE-F via gate-eval gates trade GENERATION). Note: the
Claude-side pretrade-token-gate HOOK does not travel (portable: NO -- docs/compatibility.md);
non-Claude harnesses never receive Robinhood order tools at all, so this wrapper is
analysis/dry-run tooling there, not an authorization path.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
env = dict(os.environ)
env.setdefault("VAULT_ROOT", ROOT)
r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "pretrade_gate.py")] + sys.argv[1:],
                   env=env, cwd=ROOT)
sys.exit(r.returncode)

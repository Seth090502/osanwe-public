#!/usr/bin/env python3
"""UserPromptSubmit hook: auto-query the Phase 3 semantic vault index and inject
the top matching chunks into Claude's context as additionalContext.

Degradation discipline: this hook NEVER blocks a prompt. On ANY error (node missing,
timeout, missing index, bad JSON, no hits above threshold) it exits 0 with no output,
and the prompt proceeds unchanged. Exit 2 is the only blocking code; we never use it.

Phase 3.5. Pairs with ~/.vault-substrate/query-prompt.mjs (override via SUBSTRATE_ROOT env var).
"""
import sys
import json
import subprocess

import pathlib as _pathlib
import os as _os
QUERY_PROMPT = str(_pathlib.Path(_os.environ.get("SUBSTRATE_ROOT",
    str(_pathlib.Path.home() / ".vault-substrate"))) / "query-prompt.mjs")
THRESHOLD = 0.6          # bge-base similarity floor is ~0.5; 0.6 keeps off-topic noise out
TOP_K = 5
TIMEOUT_S = 12           # cold node + model load is ~0.3s; generous headroom

# Phase 3.5b: skill-type-conditional hook suppression (2026-05-26; /decide added 2026-05-28).
# Source: Phase 3.6c 4-skill empirical hook-vs-Phase-0 overlap. /invest, /challenge,
# and /health each showed 5/5 of this hook's top hits already subsumed by their own
# Phase 0 structured retrieval (hook redundant); /spark showed 0/5 (disjoint, hook
# complementary) and is deliberately NOT suppressed. Phase 3.5c added /decide after a
# 27-prompt / 8-domain / 2-round adversarial smoke: 135-of-135 verified subsumption,
# every domain 5/5 (not merely the bar), floor-tested at hook-score 0.615 still 5/5 --
# /decide Phase 0 fans out 12 decomposition queries at top_k=100, structurally subsuming
# this hook's single-query top-5. Add a skill here ONLY after a Phase-0 smoke shows
# >=4/5 hook-vs-Phase-0 overlap; default to KEEP when data absent.
# The suppress path emits the SAME output as the no-hits path below (empty stdout,
# exit 0) -- see the `if not hits: return 0` short-circuit.
SUPPRESS_SKILLS = ('/invest', '/challenge', '/health', '/decide')


def main():
    raw = sys.stdin.read()
    if not raw or not raw.strip():
        return 0

    # Confirm a non-empty prompt before paying for the node subprocess.
    try:
        d = json.loads(raw)
        prompt = d.get("prompt") or d.get("message") or d.get("user_prompt") or ""
    except Exception:
        return 0
    if not prompt.strip():
        return 0

    # Phase 3.5b: suppress entity-skills whose Phase 0 subsumes this hook (see top).
    # Prefix-match the first non-whitespace token at a word boundary (next char is
    # whitespace or end-of-string) so /investment, /healthcare, /challenger do NOT
    # match, and a mid-prompt mention ("...I ran /invest...") does NOT match either.
    stripped = prompt.lstrip()
    for skill in SUPPRESS_SKILLS:
        n = len(skill)
        if stripped.startswith(skill) and (
                len(stripped) == n or stripped[n] in (' ', '\t', '\n', '\r')):
            return 0

    # Query the index via the node wrapper. Pass the raw hook JSON on stdin (clean pipe;
    # query-prompt.mjs extracts the prompt itself and always emits a JSON array).
    try:
        r = subprocess.run(
            ["node", QUERY_PROMPT],
            input=raw,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_S,
        )
    except Exception:
        return 0
    if not r.stdout or not r.stdout.strip():
        return 0
    try:
        hits = json.loads(r.stdout)
    except Exception:
        return 0

    hits = [h for h in hits if isinstance(h, dict) and h.get("score", 0) >= THRESHOLD][:TOP_K]
    if not hits:
        return 0

    lines = [
        "## Vault context (semantic top-K)",
        "",
        "The following vault excerpts were retrieved by semantic similarity to the "
        "user's message. Cite path:line if you use them; ignore if not relevant.",
        "",
    ]
    for h in hits:
        lines.append("- [{:.4f}] {}:{}".format(h.get("score", 0), h.get("path", "?"), h.get("line", "?")))
        lines.append("  " + str(h.get("text", "")))
    block = "\n".join(lines)

    out = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": block}}
    print(json.dumps(out, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Never block a prompt on hook failure.
        sys.exit(0)

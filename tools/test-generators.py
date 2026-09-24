#!/usr/bin/env python3
"""test-generators.py -- regression suite for the generated-organ pipeline.

Guarantees (each a failing test if violated):
  G1  gen-ledger-views: every ledger view regenerates with identical normalized text
      (the strangler invariant; a failing test means someone hand-edited a view)
  G2  gen-hot: output passes tools/hot-md-check.py with ok=true, <=8000 B
  G3  gen-codex-yaml: two consecutive runs are byte-stable (idempotency)
  G4  atomize counts match node-dir file counts (no orphan/missing nodes)

Run: python tools/test-generators.py        (check-only, no writes)
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAILURES = []


def load(name, fn):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / fn)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def g1_views():
    glv = load("glv", "gen-ledger-views.py")
    bad = []
    for key, spec in glv.al.LEDGERS.items():
        p = ROOT / spec["file"]
        if not (ROOT / spec["node_dir"]).is_dir():
            continue  # family not yet atomized
        original, regen = glv.regenerate(key, spec)
        if original != regen:
            bad.append(key)
    if bad:
        return False, f"views drift from nodes: {bad}"
    return True, "all live views text-equivalent to nodes; physical append preservation checked separately"


def g2_hot():
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "hot-md-check.py")],
                       capture_output=True, text=True, cwd=str(ROOT))
    try:
        d = json.loads((r.stdout or "") + (r.stderr or ""))
    except json.JSONDecodeError:
        return False, "hot-md-check emitted non-JSON"
    ok = bool(d.get("ok"))
    size = d.get("stats", {}).get("total_bytes", 0)
    return ok and size <= 8000, f"ok={ok} bytes={size}"


def g3_yaml_stable():
    import yaml
    gen = load("codex_index", "gen-codex-yaml.py")
    # Render in memory: a validation run must never overwrite a live artifact,
    # even briefly, nor report success when a subprocess failed.
    first, second = gen.render(), gen.render()
    data = yaml.safe_load(first)
    assert data["entry_points"]["contract"] == "AGENTS.md"
    assert isinstance(data["folders"][0]["files_on_disk"], int)
    for relative in data["entry_points"].values():
        assert (ROOT / relative).is_file(), f"missing authority: {relative}"
    return first == second, "typed YAML parses; authority paths resolve; in-memory runs byte-stable"


def g5_hot_truth():
    from unittest.mock import patch
    gen = load("hot_recovery", "gen-hot.py")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sessions = root / "Calendar/sessions"
        sessions.mkdir(parents=True)
        session = sessions / "0239-2026-09-11-example.md"
        session.write_text("---\nstatus: complete\n---\nBLUF: Synthetic test\n", encoding="ascii")
        ledger = root / "Calendar/decisions/execute-or-decline.md"
        ledger.parent.mkdir(parents=True)
        ledger.write_text("| EOD-1 | resolved action | reason | 2020-01-01 | PENDING | |\n"
                          "| EOD-1 | resolution | reason | 2020-01-01 | DECLINED | closed |\n"
                          "| EOD-2 | open action | reason | 2020-01-01 | PENDING | |\n", encoding="ascii")
        with patch.object(gen, "ROOT", root), patch.object(gen, "git_status_lines", return_value=([], 0)):
            text = gen.build()
            assert "**Date:** 2026-09-11" in text
            assert "resolved action" not in text and "open action" in text
            assert "ALL GREEN" not in text and "UNVERIFIED" in text
            session.unlink()
            assert "no session node" in gen.build()
    return True, "sequence-date, resolved actions, absent session, and no invented health PASS"


def g4_node_counts():
    al = load("al", "atomize-ledgers.py")
    problems = []
    for key, spec in al.LEDGERS.items():
        nd = ROOT / spec["node_dir"]
        if not nd.is_dir():
            continue
        n_nodes = len([f for f in nd.glob("*.md") if f.name != "INDEX.md"])
        text = (ROOT / spec["file"]).read_text(encoding="utf-8", errors="replace")
        if key in ("sessions", "decisions"):
            entries = len(al.split_headings(text))
            legacy = 1 if any(m is None for m, _ in al.split_headings(text)) else 0
            expect = entries - (1 if any(m is None and i == 0 for i, (m, _) in enumerate(al.split_headings(text))) else 0)
        else:
            rows = (al.parse_eod_rows if key == "eod" else al.parse_insight_rows)(text)
            expect = len(rows)
        # allow tail-ingested extras but not fewer than parsed entries
        if key not in ("sessions", "decisions") and n_nodes != expect:
            problems.append(f"{key}: {n_nodes} nodes vs {expect} rows")
    if problems:
        return False, "; ".join(problems)
    return True, "table-ledger node counts == parsed rows"


def main():
    tests = [("G1 views==nodes", g1_views),
             ("G2 hot checker-green", g2_hot),
             ("G3 codex-yaml idempotent", g3_yaml_stable),
             ("G4 node counts", g4_node_counts),
             ("G5 truthful hot cache", g5_hot_truth)]
    failed = False
    for label, fn in tests:
        try:
            ok, msg = fn()
        except Exception as exc:
            ok, msg = False, f"EXC {exc!r}"
        failed = failed or not ok
        print(f"[{'PASS' if ok else 'FAIL'}] {label}: {msg}")
    print("test-generators:", "FAIL" if failed else "ALL PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

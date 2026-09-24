#!/usr/bin/env python3
"""D8: Downstream invalidation propagation.

Given an upstream dataset id and a new hash, walk the declared dependency
graph (dependency-graph.json) and emit stale-marks for every downstream
node in the transitive closure. Each stale-mark is:

    {"path": ..., "reason": ..., "invalidated_at": ...}

Marks are printed to stdout (one JSON object per line) AND appended to an
append-only JSONL event log (stale-events.jsonl).

Idempotency: the tool records the last-seen hash per dataset id in
hash-state.json. Re-running with the SAME hash emits nothing; only a
changed hash triggers propagation.

Usage:
    python invalidation.py mark --dataset factors.db --new-hash <sha>
    python invalidation.py selftest

ASCII only, stdlib only, no network, no git.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIS_DIR = REPO_ROOT / "Efforts" / "osanwe-v2-overhaul" / "_work" / "fis-data"
GRAPH_PATH = FIS_DIR / "dependency-graph.json"
EVENTS_PATH = FIS_DIR / "stale-events.jsonl"
STATE_PATH = FIS_DIR / "hash-state.json"


def utc_now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path):
    with open(path, "r", encoding="ascii") as f:
        return json.load(f)


def load_state(path):
    if not path.exists():
        return {}
    return load_json(path)


def save_state(path, state):
    with open(path, "w", encoding="ascii") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def transitive_closure(graph, dataset_id):
    """All datasets reachable from dataset_id via depends_on edges,
    excluding dataset_id itself. Deterministic BFS order."""
    edges = {k: v.get("depends_on", []) for k, v in graph["datasets"].items()}
    # invert: upstream -> direct dependents
    dependents = {}
    for node, ups in edges.items():
        for up in ups:
            dependents.setdefault(up, []).append(node)
    seen = []
    visited = set()
    queue = [dataset_id]
    while queue:
        current = queue.pop(0)
        for dep in sorted(dependents.get(current, [])):
            if dep not in visited:
                visited.add(dep)
                seen.append(dep)
                queue.append(dep)
    return seen


def propagate(dataset_id, new_hash, graph_path=GRAPH_PATH,
              events_path=EVENTS_PATH, state_path=STATE_PATH):
    """Apply an upstream change. Returns list of emitted stale-marks."""
    graph = load_json(graph_path)
    datasets = graph["datasets"]
    if dataset_id not in datasets:
        raise SystemExit("unknown dataset id: %s" % dataset_id)

    state = load_state(state_path)
    old_hash = state.get(dataset_id)

    # Idempotent: unchanged hash -> nothing to do.
    if old_hash is not None and old_hash == new_hash:
        return []

    now = utc_now_iso()
    marks = []
    for dep_id in transitive_closure(graph, dataset_id):
        marks.append({
            "path": datasets[dep_id]["path"],
            "reason": "upstream '%s' changed hash (%s -> %s)"
                      % (dataset_id,
                         old_hash if old_hash else "<none>",
                         new_hash),
            "invalidated_at": now,
            "dataset": dep_id,
            "upstream": dataset_id,
        })

    if marks:
        with open(events_path, "a", encoding="ascii") as f:
            for m in marks:
                f.write(json.dumps(m) + "\n")
        for m in marks:
            print(json.dumps(m))

    state[dataset_id] = new_hash
    save_state(state_path, state)
    return marks


def selftest():
    """Simulate an upstream change; assert the exact transitive closure of
    factors.db gets marked exactly once; a second identical run marks zero."""
    import tempfile

    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        gpath = tmp / "graph.json"
        epath = tmp / "events.jsonl"
        spath = tmp / "state.json"
        gpath.write_text(GRAPH_PATH.read_text(encoding="ascii"), encoding="ascii")

        def run(hash_):
            return propagate("factors.db", hash_, gpath, epath, spath)

        # Seed baseline state so the first change is a real change.
        save_state(spath, {"factors.db": "hash0"})

        m1 = run("hash1")
        expected = ["experiments", "calibration-outputs", "confidence-map"]
        got = [m["dataset"] for m in m1]
        if got != expected:
            failures.append("run1 closure mismatch: got %r want %r" % (got, expected))
        if len(m1) != 3:
            failures.append("run1 marked %d, want 3" % len(m1))
        lines = epath.read_text(encoding="ascii").strip().splitlines()
        if len(lines) != 3:
            failures.append("event log has %d lines after run1, want 3" % len(lines))

        # Second identical run must emit nothing.
        m2 = run("hash1")
        if m2:
            failures.append("run2 emitted %d marks, want 0" % len(m2))
        lines = epath.read_text(encoding="ascii").strip().splitlines()
        if len(lines) != 3:
            failures.append("event log grew to %d lines after run2, want still 3" % len(lines))

        # A further real change re-invalidates again.
        m3 = run("hash2")
        if len(m3) != 3:
            failures.append("run3 marked %d, want 3" % len(m3))

        # Unknown dataset should fail loudly.
        try:
            propagate("nope.db", "x", gpath, epath, spath)
            failures.append("unknown dataset did not raise")
        except SystemExit:
            pass

    if failures:
        print("SELFTEST FAIL:")
        for f_ in failures:
            print("  - " + f_)
        return 1
    print("SELFTEST OK: transitive closure marked once; repeat run marked zero.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_mark = sub.add_parser("mark", help="propagate an upstream change")
    p_mark.add_argument("--dataset", required=True)
    p_mark.add_argument("--new-hash", required=True)

    sub.add_parser("selftest", help="run built-in self test")

    args = parser.parse_args(argv)
    if args.cmd == "mark":
        marks = propagate(args.dataset, args.new_hash)
        if not marks:
            print("(unchanged hash: nothing invalidated)", file=sys.stderr)
        return 0
    if args.cmd == "selftest":
        return selftest()
    return 1


if __name__ == "__main__":
    sys.exit(main())

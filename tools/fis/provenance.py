#!/usr/bin/env python3
"""E2: Provenance graph + downstream propagation (calculation-lineage layer).

Composes with Wave D's tools/pit/invalidation.py (dataset-hash based,
dependency-graph.json based). This layer records CALCULATION LINEAGE:

    every computed artifact gets a node
        {id, inputs: [fact/artifact ids], script_path, code_version,
         computed_at, params}
    edges are auto-derived from the declared inputs.

Each artifact record also snapshots the current version (content digest +
version counter) of every declared input. When an upstream fact/artifact is
re-registered with new content, explain(artifact_id) walks the full
transitive input closure and flags every descendant whose recorded snapshot
no longer matches the live version.

Integration with Wave D (READ-ONLY import; tools/pit/* is never modified):
this module imports tools.pit.invalidation and emits stale-events in the
SAME schema Wave D uses --

    {"path": ..., "reason": ..., "invalidated_at": ...,
     "dataset": ..., "upstream": ...}

-- appended to the same stale-events.jsonl log, plus a "layer":
"provenance" marker so consumers can tell which layer emitted a mark.

Usage:
    python provenance.py selftest
    python provenance.py explain --artifact <id>

ASCII only, stdlib only, no network, no git.
"""

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone

# --- locate repo + reuse Wave D paths/constants READ-ONLY -------------------
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(THIS_DIR))  # .../tools/fis -> repo

sys.path.insert(0, os.path.join(REPO_ROOT, "tools", "pit"))

try:
    import invalidation  # Wave D module, imported READ-ONLY, never modified

    FIS_DIR = invalidation.FIS_DIR
    STALE_EVENTS_PATH = invalidation.EVENTS_PATH
    UTC_NOW = invalidation.utc_now_iso
    _HAS_WAVE_D = True
except Exception:  # pragma: no cover - standalone fallback
    FIS_DIR = os.path.join(REPO_ROOT, "Efforts", "osanwe-v2-overhaul",
                           "_work", "fis-data")
    STALE_EVENTS_PATH = os.path.join(FIS_DIR, "stale-events.jsonl")

    def UTC_NOW():
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    _HAS_WAVE_D = False

PROV_STORE_PATH = os.path.join(FIS_DIR, "provenance-store.json")


def digest_of(content):
    """Stable ASCII content digest used as a version fingerprint."""
    if isinstance(content, str):
        content = content.encode("ascii")
    return hashlib.sha256(content).hexdigest()[:16]


def load_store(path=PROV_STORE_PATH):
    if not os.path.exists(path):
        return {"artifacts": {}}
    with open(path, "r", encoding="ascii") as f:
        return json.load(f)


def save_store(store, path=PROV_STORE_PATH):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, "w", encoding="ascii") as f:
        json.dump(store, f, indent=2, sort_keys=True)
        f.write("\n")


class ProvenanceGraph:
    """Append-per-registration lineage store.

    Store layout:
        {"artifacts": {id: {"current": <record>, "history": [<record>,...]}}}

    A record is one of:
      fact:     {"id", "kind": "fact", "version": N, "digest", "computed_at"}
      artifact: {"id", "kind": "artifact", "version": N, "digest",
                 "inputs": [ids], "script_path", "code_version",
                 "computed_at", "params", "input_versions": {id: digest}}
    """

    def __init__(self, store_path=PROV_STORE_PATH):
        self.store_path = store_path
        self.store = load_store(store_path)

    # -- write side ----------------------------------------------------------

    def register_fact(self, fact_id, content="", version_note=None):
        """Register (or re-register) a base fact. New content => new version."""
        rec = {
            "id": fact_id,
            "kind": "fact",
            "digest": version_note if version_note else digest_of(content),
            "computed_at": UTC_NOW(),
        }
        return self._commit(rec)

    def record_artifact(self, artifact_id, inputs, script_path,
                        code_version, content="", params=None):
        """Record a computed artifact; snapshots each input's live version."""
        input_versions = {}
        for dep in inputs:
            cur = self.current(dep)
            if cur is None:
                raise KeyError(
                    "declared input %r has no provenance record" % dep)
            input_versions[dep] = cur["digest"]
        rec = {
            "id": artifact_id,
            "kind": "artifact",
            "digest": digest_of(content) if content != "" else
                      digest_of(json.dumps(input_versions, sort_keys=True)),
            "inputs": list(inputs),
            "script_path": script_path,
            "code_version": code_version,
            "params": params or {},
            "computed_at": UTC_NOW(),
            "input_versions": input_versions,
        }
        return self._commit(rec)

    def _commit(self, rec):
        slot = self.store["artifacts"].setdefault(
            rec["id"], {"current": None, "history": []})
        prev = slot["current"]
        rec["version"] = (prev["version"] + 1) if prev else 1
        slot["current"] = rec
        slot["history"].append(rec)
        save_store(self.store, self.store_path)
        return rec

    # -- read side -----------------------------------------------------------

    def current(self, artifact_id):
        slot = self.store["artifacts"].get(artifact_id)
        return slot["current"] if slot else None

    def edges(self):
        """Auto-derived edges [(upstream_id, downstream_id)], sorted."""
        out = set()
        for aid, slot in self.store["artifacts"].items():
            for up in slot["current"].get("inputs", []):
                out.add((up, aid))
        return sorted(out)

    def transitive_closure(self, artifact_id):
        """All transitive inputs reachable from artifact_id (excl. itself),
        deterministic BFS order (nearest first)."""
        seen, order = [], []
        visited = set()
        queue = [artifact_id]
        while queue:
            cur = queue.pop(0)
            rec = self.current(cur)
            deps = rec.get("inputs", []) if rec else []
            for dep in sorted(deps):
                if dep not in visited:
                    visited.add(dep)
                    order.append(dep)
                    queue.append(dep)
        del seen
        return order

    # -- staleness -----------------------------------------------------------

    def stale_inputs_of(self, artifact_id):
        """Direct inputs of artifact_id whose live digest differs from the
        digest snapshotted at compute time. Returns list of dicts."""
        rec = self.current(artifact_id)
        if rec is None or rec.get("kind") != "artifact":
            return []
        out = []
        for dep, want in sorted(rec.get("input_versions", {}).items()):
            cur = self.current(dep)
            got = cur["digest"] if cur else "<missing>"
            if got != want:
                out.append({"input": dep, "recorded": want, "live": got,
                            "live_version": (cur or {}).get("version")})
        return out

    def explain(self, artifact_id):
        """Full transitive input closure + staleness verdict for one artifact.

        Returns {"artifact", "fresh", "closure", "stale", "edges",
                 "chain"} where chain lists every descendant (BFS layers)
        that is invalidated, directly or transitively.
        """
        if self.current(artifact_id) is None:
            return {
                "artifact": artifact_id, "fresh": False, "closure": [],
                "stale": [artifact_id], "edges": [],
                "reasons": {artifact_id: "missing provenance record; freshness unknown"},
            }
        closure = self.transitive_closure(artifact_id)
        # Evaluate staleness over the closure PLUS the queried artifact:
        # facts have no declared inputs so they are never themselves stale;
        # they are only ever the CAUSE of staleness downstream.
        nodes = closure + [artifact_id]
        stale_set, reasons = set(), {}
        for node in nodes:
            bad = self.stale_inputs_of(node)
            if bad:
                stale_set.add(node)
                reasons[node] = "; ".join(
                    "input '%s' %s -> %s"
                    % (b["input"], b["recorded"][:8], b["live"][:8])
                    for b in bad)
        # Everything DOWNSTREAM of a stale node is also invalidated even if
        # its own inputs still match (it consumed a stale parent).
        for node in list(stale_set):
            for down in self._reachable_from(node):
                if down in nodes and down not in stale_set:
                    stale_set.add(down)
                    reasons[down] = ("consumed stale upstream %r" % node)
        # Deterministic order: closure BFS order, queried artifact last.
        ordered = [n for n in closure if n in stale_set]
        if artifact_id in stale_set:
            ordered.append(artifact_id)

        edge_set = set()
        for node in nodes:
            rec = self.current(node)
            for up in (rec.get("inputs", []) if rec else []):
                edge_set.add((up, node))

        return {
            "artifact": artifact_id,
            "fresh": len(ordered) == 0,
            "closure": closure,
            "stale": ordered,
            "reasons": {k: reasons[k] for k in ordered},
            "edges": sorted(edge_set),
        }

    def _reachable_from(self, start):
        """All nodes downstream of `start` in the auto-derived edge set."""
        inv = {}
        for up, down in self.edges():
            inv.setdefault(up, []).append(down)
        queue, visited = [start], {start}
        while queue:
            cur = queue.pop(0)
            for nxt in sorted(inv.get(cur, [])):
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)
        visited.discard(start)
        return sorted(visited)

    # -- Wave D integration (emit, never modify tools/pit/*) -----------------

    def emit_stale_events(self, artifact_id, marks_path=STALE_EVENTS_PATH,
                          upstream=None, include_closure=True):
        """Emit Wave-D-compatible stale-marks for every stale node in this
        artifact's closure. Schema matches invalidation.propagate():
            {"path","reason","invalidated_at","dataset","upstream"}
        plus "layer":"provenance". With include_closure=False, emits at
        most ONE mark -- for artifact_id itself only. Returns the marks."""
        exp = self.explain(artifact_id)
        stale = exp["stale"] if include_closure else (
            [artifact_id] if artifact_id in exp["stale"] else [])
        now = UTC_NOW()
        marks = []
        for node in stale:
            rec = self.current(node)
            marks.append({
                "path": (rec.get("script_path") if rec else None) or node,
                "reason": "provenance lineage: %s"
                          % exp["reasons"].get(node, "upstream changed"),
                "invalidated_at": now,
                "dataset": node,
                "upstream": upstream or artifact_id,
                "layer": "provenance",
            })
        if marks:
            d = os.path.dirname(marks_path)
            if d and not os.path.isdir(d):
                os.makedirs(d)
            with open(marks_path, "a", encoding="ascii") as f:
                for m in marks:
                    f.write(json.dumps(m) + "\n")
        return marks


def invalidate_and_propagate(graph, fact_id, new_content,
                             marks_path=STALE_EVENTS_PATH):
    """Convenience: re-register a fact, then emit stale-marks for every
    downstream artifact that consumes it (directly or transitively)."""
    graph.register_fact(fact_id, new_content)
    affected, marks = [], []
    inv = {}
    for up, down in graph.edges():
        inv.setdefault(up, []).append(down)
    queue, visited = [fact_id], {fact_id}
    while queue:
        cur = queue.pop(0)
        for nxt in sorted(inv.get(cur, [])):
            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
                m = graph.emit_stale_events(nxt, marks_path,
                                            upstream=fact_id,
                                            include_closure=False)
                marks.extend(m)
                affected.append(nxt)
    return affected, marks


# ---------------------------------------------------------------- selftest --

def selftest():
    """Chain fact -> calc1 -> calc2 -> report; mutate the base fact; assert
    explain() flags EVERY descendant stale and emitted marks are
    Wave-D-compatible."""
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = tmp.replace("\\", "/")
        spath = tmp + "/store.json"
        epath = tmp + "/stale-events.jsonl"

        g = ProvenanceGraph(spath)

        # Build the chain.
        g.register_fact("fact.px", content="px-close-2026-08-25|v1")
        g.record_artifact("calc1", inputs=["fact.px"], script_path="t/c1.py",
                          code_version="a1", content="c1-out-1")
        g.record_artifact("calc2", inputs=["calc1"], script_path="t/c2.py",
                          code_version="a2", content="c2-out-1")
        g.record_artifact("report", inputs=["calc2"], script_path="t/rpt.py",
                          code_version="a3", content="rpt-out-1")

        exp = g.explain("report")
        if not exp["fresh"]:
            failures.append("baseline chain should be fresh, stale=%r"
                            % exp["stale"])
        if exp["closure"] != ["calc2", "calc1", "fact.px"]:
            failures.append("closure wrong: %r" % exp["closure"])
        want_edges = [("calc1", "calc2"), ("calc2", "report"),
                      ("fact.px", "calc1")]
        if exp["edges"] != want_edges:
            failures.append("auto-derived edges wrong: %r" % exp["edges"])

        # Mutate the base fact.
        g.register_fact("fact.px", content="px-close-2026-08-25|v2")
        if g.current("fact.px")["version"] != 2:
            failures.append("fact version should be 2 after re-register")

        exp = g.explain("report")
        # The mutated fact is the CAUSE; every artifact consuming it
        # (directly or transitively) must be flagged stale, including the
        # queried artifact itself.
        expected_stale = ["calc2", "calc1", "report"]
        if sorted(exp["stale"]) != sorted(expected_stale):
            failures.append("expected all 3 descendants stale, got %r"
                            % exp["stale"])
        if exp["fresh"]:
            failures.append("report must NOT be fresh after base-fact change")
        for node in ("calc1", "calc2", "report"):
            if node not in exp["reasons"]:
                failures.append("missing staleness reason for %r" % node)

        # Wave-D-compatible emission.
        affected, marks = invalidate_and_propagate(g, "fact.px", "ignored",
                                                   marks_path=epath)
        if sorted(affected) != ["calc1", "calc2", "report"]:
            failures.append("propagation missed descendants: %r" % affected)
        lines = open(epath, encoding="ascii").read().strip().splitlines()
        if len(lines) != len(expected_stale):
            failures.append("event log has %d lines, want %d"
                            % (len(lines), len(expected_stale)))
        required_keys = {"path", "reason", "invalidated_at", "dataset",
                         "upstream"}
        for ln in lines:
            obj = json.loads(ln)
            if not required_keys.issubset(obj.keys()):
                failures.append("mark missing Wave-D keys: %r" % sorted(obj))
        datasets = {json.loads(ln)["dataset"] for ln in lines}
        if datasets != set(expected_stale):
            failures.append("marked datasets wrong: %r" % datasets)

        # Re-computing calc1 clears ITS branch but report stays stale until
        # its own ancestors recomputed: recompute chain bottom-up.
        g.register_fact("fact.px", content="px-close-2026-08-25|v3")
        g.record_artifact("calc1", inputs=["fact.px"], script_path="t/c1.py",
                          code_version="a1", content="c1-out-3")
        exp_mid = g.explain("report")
        if "fact.px" in exp_mid["stale"] or "calc1" in exp_mid["stale"]:
            failures.append("recomputed nodes should be fresh: %r"
                            % exp_mid["stale"])
        if "calc2" not in exp_mid["stale"] or "report" not in exp_mid["stale"]:
            failures.append("downstream of change must stay stale: %r"
                            % exp_mid["stale"])

    if failures:
        print("SELFTEST FAIL:")
        for f_ in failures:
            print("  - " + f_)
        return 1
    print("SELFTEST OK: fact->calc1->calc2->report; base-fact mutation "
          "flagged every descendant stale; Wave-D-compatible stale-events "
          "emitted.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest", help="run built-in self test")
    p_ex = sub.add_parser("explain", help="explain one artifact")
    p_ex.add_argument("--artifact", required=True)
    args = parser.parse_args(argv)
    if args.cmd == "selftest":
        return selftest()
    if args.cmd == "explain":
        print(json.dumps(ProvenanceGraph().explain(args.artifact),
                         indent=2, sort_keys=True))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())

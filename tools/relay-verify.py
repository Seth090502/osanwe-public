#!/usr/bin/env python3
"""relay-verify -- mechanical claim verification for relay worker distillates.

GATE-B: wiki/research/gates/gate-b-local-orchestration-program-2026-08-17.md.

Trust at machine speed: for every claim the worker recorded, (1) check the
RECORDED payload first via the byte-offset witness (O(1) seek; proves the
record-time grounding still holds on disk), then (2) re-execute the source --
mcp:* claims re-run through the SAME contained McpPool the worker used
(D-SEC-1 name refusal holds orchestrator-side too), vault:* claims re-read
from disk, url claims re-fetched under --sample N through the SAME containment
_follow. The shared matcher (relay_schema.value_occurs) is the one grounding
uses -- one matcher, no drift.

Verdicts: VERIFIED | MISMATCH (fabrication-grade: value was never in the
recorded payload, or fresh payload is byte-identical yet lacks it |
drift-possible: recorded payload had it, live data moved) | UNVERIFIABLE
(reason). Fabrication-grade counts against the promotion staircase's "zero
verification failures"; drift-possible does NOT (rule doc qualification).

  python tools/relay-verify.py --run <run> [--distillate PATH] [--sample N]
        [--no-refetch] [--json]

Report -> tracked .agents/relay/<run>/verify.json + one ledger row
kind=relay-verify (excluded from every promotion counter by delegate.py).
Exit: 0 no mismatches | 1 any MISMATCH | 2 unverifiable-only.
"""
import argparse
import hashlib
import json
import os
import sys
import tempfile
import time

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, os.path.join(TOOLS_DIR, "lib"))

import relay_schema  # noqa: E402
from relay_schema import value_occurs  # noqa: E402
from relay_exec import Executor, Refusal, file_sha_text  # noqa: E402

STATE_DIR = os.path.join(VAULT, ".claude", "state")


def make_pool(lane_cfg):
    """Factory (suite seam): the SAME contained pool the worker uses."""
    from relay_mcp import McpPool
    relay_cfg = lane_cfg.get("relay") or {}
    return McpPool(relay_cfg.get("mcp_allowlist") or [],
                   relay_cfg.get("mcp_spawn_timeout_s", 60))


def fetch(url, relay_cfg):
    """URL re-fetch through the worker's own containment (suite seam)."""
    ex = Executor(tempfile.mkdtemp(prefix="relay-verify-"), relay_cfg,
                  {"objective": "verify"})
    _chain, _final, text, _ssl = ex._follow(url)
    return text


def witness_check(claim, src, run_id):
    """(ok, reason). ok=True when the recorded spill still contains the value
    at/near the witness. witness 'spill-failed' or missing spill -> (None, why)."""
    w = claim.get("witness")
    if not w or w == "spill-failed":
        return None, "no witness (spill-failed or legacy claim)"
    scratch = os.path.join(STATE_DIR, "relay", run_id, "scratch")
    try:
        fname = w.rsplit(":", 2)[0]
        path = os.path.join(scratch, fname)
        if not os.path.isfile(path):
            return None, "spill file gone (pruned?)"
        text = open(path, encoding="ascii", errors="replace").read()
        found, _off, _ln = value_occurs(claim.get("value", ""), text)
        return (True, "recorded payload holds the value") if found else \
               (False, "recorded payload does NOT hold the value")
    except (OSError, ValueError) as exc:
        return None, "witness unreadable: %s" % exc


def classify_mismatch(witness_ok, recorded_sha, fresh_text):
    fresh_sha = hashlib.sha256(
        fresh_text.encode("utf-8", "replace")).hexdigest()
    if witness_ok is not True or fresh_sha == recorded_sha:
        return "fabrication-grade"
    return "drift-possible"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--distillate")
    ap.add_argument("--sample", type=int, default=0,
                    help="re-fetch up to N url-prov claims")
    ap.add_argument("--no-refetch", action="store_true",
                    help="witness + on-disk checks only (no MCP/web)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    merged = args.distillate or os.path.join(
        VAULT, ".agents", "relay", args.run, "leg-merged.json")
    if not os.path.isfile(merged):
        print(relay_schema.dumps_ascii({"run": args.run,
                                        "error": "no merged distillate"}))
        return 2
    d = json.load(open(merged, encoding="ascii"))
    lane_cfg = json.load(open(os.path.join(VAULT, "config", "local-lane.json"),
                              encoding="utf-8"))
    relay_cfg = lane_cfg.get("relay") or {}
    srcs = {s.get("ref"): s for s in d.get("sources") or []}
    pool = None
    mcp_cache = {}
    url_sampled = 0
    rows = []
    for c in d.get("claims") or []:
        src = srcs.get(c.get("source_ref"))
        key = "%s|%s|%s" % (c.get("entity"), c.get("metric"), c.get("value"))
        row = {"claim": key, "prov": c.get("prov"), "ref": c.get("source_ref")}
        if src is None:
            row.update(verdict="UNVERIFIABLE", reason="source ref missing")
            rows.append(row)
            continue
        w_ok, w_why = witness_check(c, src, args.run)
        row["witness"] = w_why
        prov = str(c.get("prov") or "")
        kind = src.get("kind")
        try:
            if kind == "file" or prov.startswith("vault:"):
                real = os.path.join(VAULT, src.get("locator", ""))
                if not os.path.isfile(real):
                    row.update(verdict="UNVERIFIABLE", reason="file gone")
                else:
                    _sha, text = file_sha_text(real)
                    found, _o, _l = value_occurs(c.get("value", ""), text)
                    if found:
                        row.update(verdict="VERIFIED", method="file-reread")
                    else:
                        row.update(verdict="MISMATCH",
                                   mismatch_class=classify_mismatch(
                                       w_ok, src.get("sha256", ""), text),
                                   method="file-reread")
            elif kind == "frontier":
                row.update(verdict="VERIFIED" if w_ok else
                           ("UNVERIFIABLE" if w_ok is None else "MISMATCH"),
                           method="recorded-guidance",
                           **({"mismatch_class": "fabrication-grade"}
                              if w_ok is False else {}))
                if w_ok is None:
                    row["reason"] = w_why
            elif kind == "mcp":
                if args.no_refetch:
                    row.update(verdict="VERIFIED" if w_ok else "UNVERIFIABLE",
                               method="recorded-payload",
                               reason=None if w_ok else w_why)
                else:
                    ca = src.get("call_args")
                    if not isinstance(ca, dict):
                        row.update(verdict="UNVERIFIABLE",
                                   reason="locator-truncated (pre-call_args "
                                          "distillate)")
                    else:
                        ck = json.dumps(ca, sort_keys=True, default=str)
                        if ck not in mcp_cache:
                            if pool is None:
                                pool = make_pool(lane_cfg)
                            mcp_cache[ck] = pool.call(
                                ca["server"], ca["tool"], ca.get("args") or {})
                        fresh = mcp_cache[ck]
                        found, _o, _l = value_occurs(c.get("value", ""), fresh)
                        if found:
                            row.update(verdict="VERIFIED", method="mcp-recall")
                        else:
                            row.update(verdict="MISMATCH",
                                       mismatch_class=classify_mismatch(
                                           w_ok, src.get("sha256", ""), fresh),
                                       method="mcp-recall")
            elif kind == "url":
                if args.sample and url_sampled < args.sample \
                        and not args.no_refetch:
                    url_sampled += 1
                    fresh = fetch(src.get("locator", ""), relay_cfg)
                    found, _o, _l = value_occurs(c.get("value", ""), fresh)
                    if found:
                        row.update(verdict="VERIFIED", method="url-refetch")
                    else:
                        row.update(verdict="MISMATCH",
                                   mismatch_class=classify_mismatch(
                                       w_ok, src.get("sha256", ""), fresh),
                                   method="url-refetch")
                else:
                    row.update(verdict="VERIFIED" if w_ok else "UNVERIFIABLE",
                               method="recorded-payload",
                               reason=None if w_ok else w_why)
            else:
                row.update(verdict="VERIFIED" if w_ok else "UNVERIFIABLE",
                           method="recorded-payload",
                           reason=None if w_ok else w_why)
        except (Refusal, Exception) as exc:                   # noqa: BLE001
            row.update(verdict="UNVERIFIABLE", reason=str(exc)[:200])
        rows.append(row)
    if pool is not None:
        pool.close()

    verified = sum(1 for r in rows if r["verdict"] == "VERIFIED")
    mismatch = sum(1 for r in rows if r["verdict"] == "MISMATCH")
    fab = sum(1 for r in rows if r.get("mismatch_class") == "fabrication-grade")
    unver = sum(1 for r in rows if r["verdict"] == "UNVERIFIABLE")
    report = {"run": args.run, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "verified": verified, "mismatch": mismatch,
              "fabrication_grade": fab, "unverifiable": unver, "rows": rows}
    out_dir = os.path.join(VAULT, ".agents", "relay", args.run)
    if os.path.isdir(out_dir):
        with open(os.path.join(out_dir, "verify.json"), "w",
                  encoding="ascii") as fh:
            fh.write(relay_schema.dumps_ascii(report))
    ledger = {"ts": report["ts"], "kind": "relay-verify", "run": args.run,
              "leg": d.get("leg"), "verified": verified, "mismatch": mismatch,
              "fabrication_grade": fab, "unverifiable": unver,
              "exit": 1 if mismatch else (2 if unver and not verified else 0)}
    try:
        with open(os.path.join(
                STATE_DIR, "delegate-runs-%s.jsonl"
                % time.strftime("%Y-%m-%d")), "a", encoding="ascii") as fh:
            fh.write(json.dumps(ledger, ensure_ascii=True) + "\n")
    except OSError as exc:
        print("WARNING: receipt write failed: %s" % exc, file=sys.stderr)
    if not args.json:
        for r in rows:
            print("%-12s %s %s %s" % (
                r["verdict"] + ("/" + r["mismatch_class"]
                                if "mismatch_class" in r else ""),
                r["ref"], r["claim"][:70], r.get("reason") or ""),
                file=sys.stderr)
    print(relay_schema.dumps_ascii(report if args.json else
                                   {k: v for k, v in report.items()
                                    if k != "rows"}))
    return 1 if mismatch else (2 if unver and not verified else 0)


if __name__ == "__main__":
    sys.exit(main())

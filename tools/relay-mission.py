#!/usr/bin/env python3
"""relay-mission -- mission-spec composer for the relay worker lanes.

GATE-B: wiki/research/gates/gate-b-local-orchestration-program-2026-08-17.md.

Pure orchestrator-side text assembly: no lane lock, no daemon, no state
mutation beyond writing ONE mission JSON. Deliberately separate from relay.py
(the driver) so composing costs nothing and the guard surface stays minimal.

  python tools/relay-mission.py --leg research:insider-sweep --objective "..."
        [--question Q]... [--seed-url U]... [--mcp S]... [--budget k=v]...
        [--must-not "..."]... [--deliverable claims|tables|both]
        [--plan-checkpoint] [--out PATH] [--print] [--show-templates]

stdout: one JSON {"mission_path": ..., "leg": ..., "mission": {...}}.
Exit: 0 composed+valid | 3 invalid (unknown/never-local leg, schema error,
BUDGET RAISE attempt -- refused loudly, never silently clamped).
"""
import argparse
import importlib.util
import json
import os
import sys
import time

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, os.path.join(TOOLS_DIR, "lib"))

import relay_schema  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "delegate", os.path.join(TOOLS_DIR, "delegate.py"))
_delegate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_delegate)

MISSIONS_DIR = os.path.join(VAULT, ".claude", "state", "relay", "missions")

# Template library: exact leg id first, then leg-family fallback. Seeded from
# the proven pilot missions (pilot002 insider-sweep is the exemplar).
TEMPLATES = {
    "research:insider-sweep": {
        "objective": "Insider-activity sweep via the openinsider MCP for the "
                     "named tickers: latest Form 4 trades, cluster buys, "
                     "short interest. Record one claim per figure with exact "
                     "values as returned.",
        "allowed_mcp": ["openinsider"],
        "budgets": {"max_fetches": 0, "max_mcp_calls": 40},
        "must_not": ["fetch any web page (MCP only)",
                     "invent a figure the server did not return"],
        "deliverable": "claims",
    },
    "research:url-harvest": {
        "objective": "Fetch the seed URLs and record structured claims for "
                     "every figure/fact the mission questions name.",
        "budgets": {"max_mcp_calls": 0},
        "must_not": ["call MCP servers (web only)"],
        "deliverable": "claims",
    },
    "research:vault-context": {
        "objective": "Gather everything the vault holds on the named topic "
                     "via jailed reads (read_file/list_dir/grep_vault); "
                     "record one claim per relevant fact with prov "
                     "vault:<path>.",
        "budgets": {"max_fetches": 0, "max_mcp_calls": 0},
        "must_not": ["fetch web pages", "call MCP servers"],
        "deliverable": "claims",
    },
    "research:": {
        "objective": "", "deliverable": "claims",
    },
    "extract:": {
        "objective": "Extract structured claims from the named local "
                     "documents; exact values as printed, one claim per fact; "
                     "cursor-file chunking for large docs.",
        "budgets": {"max_fetches": 0, "max_mcp_calls": 0},
        "must_not": ["summarize passages into claims",
                     "derive or compute values"],
        "deliverable": "claims",
    },
    "edit:": {
        "objective": "Sweep the named files for the named mechanical defect "
                     "class and emit ONE propose_edit per defect; "
                     "record_negative for clean files.",
        "budgets": {"max_fetches": 0, "max_mcp_calls": 0},
        "must_not": ["propose fixes outside the named defect class",
                     "restyle or reword content"],
        "deliverable": "claims",
    },
}


def template_for(leg):
    if leg in TEMPLATES:
        return dict(TEMPLATES[leg])
    fam = leg.split(":", 1)[0] + ":"
    return dict(TEMPLATES.get(fam, {}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--leg")
    ap.add_argument("--objective")
    ap.add_argument("--question", action="append", default=[])
    ap.add_argument("--seed-url", action="append", default=[])
    ap.add_argument("--mcp", action="append", default=None)
    ap.add_argument("--budget", action="append", default=[],
                    metavar="key=int")
    ap.add_argument("--must-not", action="append", default=[])
    ap.add_argument("--deliverable", choices=["claims", "tables", "both"])
    ap.add_argument("--plan-checkpoint", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--slug")
    ap.add_argument("--print", dest="do_print", action="store_true")
    ap.add_argument("--show-templates", action="store_true")
    args = ap.parse_args()

    if args.show_templates:
        print(relay_schema.dumps_ascii(TEMPLATES))
        return 0
    if not args.leg:
        print("relay-mission: --leg required", file=sys.stderr)
        return 3

    lane_cfg = json.load(open(os.path.join(VAULT, "config", "local-lane.json"),
                              encoding="utf-8"))
    status = _delegate.leg_status(lane_cfg, args.leg)
    if status != "ok":
        print(relay_schema.dumps_ascii(
            {"error": "leg %s: %s" % (status.upper(), args.leg)}))
        return 3

    m = template_for(args.leg)
    if args.objective:
        m["objective"] = args.objective
    if not (m.get("objective") or "").strip():
        print(relay_schema.dumps_ascii(
            {"error": "no objective (template for %r has none; pass "
                      "--objective)" % args.leg}))
        return 3
    if args.question:
        m["questions"] = args.question
    if args.seed_url:
        m["seed_urls"] = args.seed_url
    if args.mcp is not None:
        m["allowed_mcp"] = args.mcp
    if args.must_not:
        m["must_not"] = (m.get("must_not") or []) + args.must_not
    if args.deliverable:
        m["deliverable"] = args.deliverable
    if args.plan_checkpoint:
        m["plan_checkpoint"] = True
    budgets = dict(m.get("budgets") or {})
    for kv in args.budget:
        if "=" not in kv:
            print(relay_schema.dumps_ascii(
                {"error": "--budget expects key=int, got %r" % kv}))
            return 3
        k, v = kv.split("=", 1)
        try:
            budgets[k] = int(v)
        except ValueError:
            print(relay_schema.dumps_ascii(
                {"error": "--budget %s: not an int" % k}))
            return 3
    if budgets:
        m["budgets"] = budgets

    # BUDGET-RAISE REFUSAL: effective_budgets would silently clamp; the
    # composer refuses LOUDLY so the orchestrator never believes a raise.
    cfg_budgets = (lane_cfg.get("relay") or {}).get("budgets") or {}
    raises = [k for k, v in (m.get("budgets") or {}).items()
              if k in cfg_budgets and isinstance(v, int)
              and v > cfg_budgets[k]]
    if raises:
        print(relay_schema.dumps_ascii(
            {"error": "budget RAISE refused (mission may only lower): %s"
             % raises}))
        return 3

    errs = relay_schema.validate_mission(m)
    if errs:
        print(relay_schema.dumps_ascii({"error": "mission invalid",
                                        "detail": errs[:6]}))
        return 3

    m["_composed"] = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                      "leg": args.leg, "by": "relay-mission.py"}
    os.makedirs(MISSIONS_DIR, exist_ok=True)
    slug = args.slug or "%s-%s" % (args.leg.replace(":", "-"),
                                   time.strftime("%Y%m%d-%H%M%S"))
    path = args.out or os.path.join(MISSIONS_DIR, slug + ".json")
    with open(path, "w", encoding="ascii") as fh:
        fh.write(relay_schema.dumps_ascii(m))
    out = {"mission_path": os.path.relpath(path, VAULT).replace(os.sep, "/"),
           "leg": args.leg}
    if args.do_print:
        out["mission"] = m
    print(relay_schema.dumps_ascii(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

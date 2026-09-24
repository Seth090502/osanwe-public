#!/usr/bin/env python3
"""options-criteria-backfill.py -- GAP-7: make options-ledger records gradable.

The 12 existing records lack pop_est / verdict_success_criterion /
horizon_check_date (score_ledger requires all three to grade). This tool:
  1. reads each record's `structure` (legs) and derives horizon_check_date =
     max leg expiry (deterministic, safe to backfill);
  2. derives a MECHANICAL verdict_success_criterion from the structure +
     screens when unambiguous (e.g., short-put -> 'underlying close >= short
     strike at expiry'), else flags needs-manual=true;
  3. NEVER invents pop_est (that is the analyst's probability judgment --
     backfilled pop_est would poison Brier). Those rows are listed for the
     operator/next /invest run to complete.
Writes an updated ledger copy + a report; does not overwrite the live ledger
without --apply.
"""

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "wiki/investing/options-ledger.jsonl"


def max_expiry(record):
    """Max leg expiry. `structure` may be a dict with legs, or a prose string
    (legacy rows) -- parse ISO dates out of the string in that case."""
    st = record.get("structure", {})
    exps = []
    if isinstance(st, dict):
        for leg in st.get("legs", []) or []:
            if isinstance(leg, dict):
                e = (leg.get("expiry") or "")[:10]
                if re.match(r"\d{4}-\d{2}-\d{2}", e):
                    exps.append(e)
            else:
                exps += re.findall(r"\d{4}-\d{2}-\d{2}", str(leg))
    else:
        exps = re.findall(r"\d{4}-\d{2}-\d{2}", str(st))
    return max(exps) if exps else None


def derive_criterion(record):
    """Derive mechanical success criterion where structure makes it obvious."""
    st = record.get("structure", {})
    if isinstance(st, dict):
        legs = st.get("legs", []) or []
        joined = " ".join(
            re.sub(r"\s+", " ", str(l.get("type") or l.get("kind") or "")).lower()
            for l in legs if isinstance(l, dict))
    else:
        joined = str(st).lower()
        legs = []
    if "short put" in joined and len(legs) == 1:
        strike = legs[0].get("strike")
        if strike:
            return f"underlying close >= {strike} at expiry", False
    if ("short call" in joined or "covered call" in joined) and len(legs) <= 2:
        strike = next((l.get("strike") for l in legs if "short" in str(l.get("type", "")).lower()), None)
        if strike:
            return f"underlying close <= {strike} at expiry", False
    if ("cash-secured put" in joined) or ("short put" in joined):
        strike = next((l.get("strike") for l in legs), None)
        if strike:
            return f"underlying close >= {strike} at expiry", False
    # fallback: thesis text carries explicit criterion?
    t = record.get("verdict") or ""
    if re.search(r"(?:profit|win|success).{0,40}(?:>=|above|at or above)", t, re.I):
        return None, True
    return None, True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    rows = [json.loads(l) for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    updated = []
    report = ["---",
              "aliases: []",
              "categories: [wiki]",
              "type: report",
              "status: active",
              f"created: {date.today().isoformat()}",
              f"updated: {date.today().isoformat()}",
              "tags: []",
              'related: []',
              "---", "",
              "# Options-ledger criteria backfill report (GENERATED)", ""]
    n_exp = n_crit = n_manual = 0
    for r in rows:
        changed = False
        if not r.get("horizon_check_date"):
            hx = max_expiry(r)
            if hx:
                r["horizon_check_date"] = hx
                changed = True
                n_exp += 1
        if not r.get("verdict_success_criterion"):
            crit, ok = derive_criterion(r)
            if crit:
                r["verdict_success_criterion"] = crit
                r["criterion_basis"] = "mechanical-from-structure (backfilled; OSANWE-V2 GAP-7)"
                changed = True
                n_crit += 1
            else:
                r["needs_manual"] = True
                n_manual += 1
        if changed:
            updated.append(r.get("id"))
        updated.append(None) if False else None
    # summary
    report.append(f"- records: {len(rows)}")
    report.append(f"- horizon_check_date derived from max leg expiry: {n_exp}")
    report.append(f"- mechanical success criteria derived: {n_crit}")
    report.append(f"- rows flagged needs_manual (no unambiguous structure): {n_manual}")
    report.append("- pop_est intentionally NOT backfilled anywhere: it is the "
                  "analyst's judgment; fabricating it would poison Brier scoring.")
    report.append("")
    report.append("| id | ticker | horizon | criterion | flags |")
    report.append("|---|---|---|---|---|")
    for r in rows:
        report.append(f"| {r.get('id')} | {r.get('ticker')} | {r.get('horizon_check_date','--')} | "
                      f"{(r.get('verdict_success_criterion') or '--')[:60]} | "
                      f"{'needs-manual' if r.get('needs_manual') else ''} |")

    if args.apply:
        with open(LEDGER, "w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        print("APPLIED to live ledger.")
    else:
        print("dry-run (use --apply to write):")
    print("\n".join(report[15:19]))
    out = ROOT / "Efforts/osanwe-v2-overhaul/_work/options-backfill-report.md"
    out.write_text("\n".join(report) + "\n", encoding="utf-8", newline="\n")
    # stash proposed rows for review either way
    with open(ROOT / "Efforts/osanwe-v2-overhaul/_work/options-ledger-proposed.jsonl",
              "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""cap-effectiveness.py -- P5: do the /invest evidence-grade confidence caps
actually improve realized accuracy?

Joins analyses (stated confidence + cap reason when present) with graded
outcomes from the offline store. Reports: capped vs uncapped realized rates,
and whether the CAPS' ordering claim (capped calls should be LESS reliable,
hence the cap) matches reality. HONESTY: with the current corpus most caps
fire on recent calls whose horizons are still accruing -- n is reported per
row and conclusions are deferred until n>=15 per row.
"""

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import importlib.util

_spec = importlib.util.spec_from_file_location("bp1", ROOT / "tools" / "backtest-prediction.py")
bp1 = importlib.util.module_from_spec(_spec)
sys.modules["bp1"] = bp1
_spec.loader.exec_module(bp1)

_spec2 = importlib.util.spec_from_file_location("bo", ROOT / "tools" / "backtest-offline.py")
bo = importlib.util.module_from_spec(_spec2)
sys.modules["bo"] = bo
_spec2.loader.exec_module(bo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "Efforts/osanwe-v2-overhaul/_work/factors.db"))
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    commits = bp1.analysis_commits()
    rows = []
    for c in commits:
        asof = bp1.sh("git", "show", f"{c['sha']}:{c['path']}")
        meta = bp1.parse_analysis_text(asof, c["path"])
        if not meta["ticker"] or meta.get("confidence") is None:
            continue
        cap_reason = re.search(r'confidence_cap_reason:\s*"([^"]+)"', asof)
        stk21 = bo.stats_from_series(bo.store_window(con, meta["ticker"], c["t0"], 21), 21)
        if not stk21:
            continue
        v = (meta["verdict"] or "").upper()
        if any(k in v for k in bp1.VERDICT_BULLISH):
            correct = stk21["ret_pct"] > 2
        elif any(k in v for k in bp1.VERDICT_BEARISH):
            correct = stk21["ret_pct"] < -2
        else:
            band = bo.bv2.parse_hold_band(asof)
            correct = (band[0] >= stk21["ret_pct"] >= band[1]) if band else None
        if correct is None:
            continue
        rows.append({"date": c["t0"], "ticker": meta["ticker"],
                     "confidence": meta["confidence"],
                     "capped": bool(cap_reason),
                     "cap_reason": cap_reason.group(1)[:60] if cap_reason else "",
                     "correct": correct})

    capped = [r for r in rows if r["capped"]]
    uncapped = [r for r in rows if not r["capped"]]

    lines = ["---", "aliases: []", "categories: [wiki]", "type: report",
             "status: active", "created: 2026-08-23", "updated: 2026-08-23",
             "tags: [topic/meta]", 'related: ["[[FINANCIAL-SOTA-ROADMAP]]"]',
             "---", "",
             "# Confidence-cap effectiveness (P5; PRELIMINARY)", ""]
    def rate(rs):
        return f"{sum(1 for r in rs if r['correct'])/len(rs):.0%}" if rs else "--"
    lines += [f"- Capped calls (confidence_cap_reason present): n={len(capped)}, "
              f"realized {rate(capped)}",
              f"- Uncapped calls: n={len(uncapped)}, realized {rate(uncapped)}",
              f"- Cap reasons seen: {sorted(set(r['cap_reason'][:40] for r in capped)) or '(none yet)'}",
              "",
              "CONCLUSION DEFERRED: the corpus is young and horizons are accruing;",
              "this report auto-improves as the weekly calibration job grades more",
              "calls. Decision threshold: revisit when min(n)=15 per row."]

    out = ROOT / "wiki/maintenance/calibration/cap-effectiveness.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"-> {out.relative_to(ROOT)}")
    print("\n".join(lines[14:16]))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

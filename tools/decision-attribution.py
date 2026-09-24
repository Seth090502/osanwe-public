#!/usr/bin/env python3
"""decision-attribution.py -- P4: grade the DOCTRINE'S DECISIONS, not its verdicts.

For every analysis with an Action dollar amount (TRADING DECISION header), replay:
  action_value  = dollars deployed at t0 -> grown by ticker return over horizon
  always_in     = same dollars, SPY over the same window
  doctrine_cum  = running sum across chronological actions per account
Outputs: total deployed, doctrine P/L vs always-invested P/L, and per-decision
alpha. $0 / NO-TRADE actions count as discipline (deployed=0, alpha=avoided loss
if ticker underperformed SPY).

Reads analyses AS OF commit date (zero lookahead) via git; prices from the store.
"""

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime, timedelta
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


def parse_action_dollars(text):
    """Extract the TRADING DECISION Action $ amount from as-of text.

    Two eras: kernel-era '$0 now' rows and earlier 'Action: ... $X' adds
    (incl. staged ladders where the FIRST tranche dollar is the commitment).
    Returns 0.0 for explicit no-trade, float for priced actions, None if the
    header carries no dollar commitment at all.
    """
    m = re.search(r"\*\*Action\*\*[:\s]\*\*(?:ADD|BUY)[^$]*\$\s*([\d,]+(?:\.\d+)?)", text)
    if not m:
        m = re.search(r"\*\*Action\*\*[^$]{0,200}?\$\s*([\d,]+(?:\.\d+)?)", text, re.S)
    if not m:
        if re.search(r"\*\*Action\*\*[:\s].{0,60}\$\s*0\b", text):
            return 0.0
        return None
    return float(m.group(1).replace(",", ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "Efforts/osanwe-v2-overhaul/_work/factors.db"))
    ap.add_argument("--horizon", type=int, default=21)
    ap.add_argument("--out", default=str(ROOT / "wiki/maintenance/calibration/decision-attribution.md"))
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    commits = bp1.analysis_commits()
    seen = set()
    rows = []
    for c in commits:
        key = (c["t0"], c["path"])
        if key in seen:
            continue
        seen.add(key)
        asof = bp1.sh("git", "show", f"{c['sha']}:{c['path']}")
        meta = bp1.parse_analysis_text(asof, c["path"])
        if not meta["ticker"] or not meta["verdict"]:
            continue
        dollars = parse_action_dollars(asof)
        if dollars is None:
            continue
        stk = bo.stats_from_series(bo.store_window(con, meta["ticker"], c["t0"], args.horizon), args.horizon)
        ben = bo.stats_from_series(bo.store_window(con, "SPY", c["t0"], args.horizon), args.horizon)
        if not stk or not ben:
            continue
        pl_ticker = dollars * stk["ret_pct"] / 100
        pl_spy = dollars * ben["ret_pct"] / 100
        rows.append({"date": c["t0"], "ticker": meta["ticker"],
                     "verdict": meta["verdict"], "action_usd": dollars,
                     "stk_ret": stk["ret_pct"], "spy_ret": ben["ret_pct"],
                     "pl_ticker": round(pl_ticker, 2),
                     "pl_spy_same": round(pl_spy, 2)})
    rows.sort(key=lambda r: r["date"])

    tot_doctrine = sum(r["pl_ticker"] for r in rows if r["action_usd"] > 0)
    tot_spy = sum(r["pl_spy_same"] for r in rows if r["action_usd"] > 0)
    deployed = sum(r["action_usd"] for r in rows if r["action_usd"] > 0)
    no_trade = [r for r in rows if r["action_usd"] == 0]
    avoided = sum(r["pl_spy_same"] - r["pl_ticker"] for r in no_trade
                  if r["stk_ret"] < r["spy_ret"])

    lines = ["---",
             "aliases: []",
             "categories: [wiki]",
             "type: report",
             "status: active",
             "created: 2026-08-23",
             "updated: 2026-08-23",
             "tags: [topic/meta]",
             'related: ["[[FINANCIAL-SOTA-ROADMAP]]"]',
             "---", "",
             f"# Decision-value attribution ({args.horizon}d horizon)", "",
             f"Replayed {len(rows)} priced Actions from analysis history "
             "(as-of text; store prices; zero lookahead).", "",
             f"- Actions WITH capital deployed: {sum(1 for r in rows if r['action_usd']>0)} "
             f"totaling ${deployed:,.0f}",
             f"- Doctrine P/L (ticker returns on deployed $): **${tot_doctrine:,.2f}**",
             f"- Same $ into SPY instead: ${tot_spy:,.2f}",
             f"- **Doctrine selection alpha: ${tot_doctrine - tot_spy:+,.2f}**",
             f"- Discipline rows ($0 / no-trade): {len(no_trade)}; "
             f"losses avoided by NOT deploying where ticker < SPY: ~${avoided:,.2f}", "",
             "| date | ticker | verdict | action | tk ret | spy ret | $ P/L | $ vs SPY |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows[-20:]:
        lines.append(f"| {r['date']} | {r['ticker']} | {r['verdict']} | ${r['action_usd']:,.0f} "
                     f"| {r['stk_ret']:+.1f}% | {r['spy_ret']:+.1f}% | "
                     f"${r['pl_ticker']:+,.2f} | ${r['pl_ticker']-r['pl_spy_same']:+,.2f} |")

    out = Path(args.out)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"-> {out.relative_to(ROOT)}")
    for l in lines[16:22]:
        print(l)
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

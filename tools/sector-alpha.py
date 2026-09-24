#!/usr/bin/env python3
"""sector-alpha.py -- GAP-6: correlation/sector-aware attribution view.

Joins decision-attribution rows with entity sector labels + store correlations:
  - per-sector deployed $, P/L, alpha-vs-SPY
  - concentration warning when one sector > 40% of deployed $
  - pairwise correlation of deployed names (from bars) vs the naive
    "independent bets" assumption

Reads the same as-of Action extraction as decision-attribution.py (imports it).
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

_da = importlib.util.spec_from_file_location("da", ROOT / "tools" / "decision-attribution.py")
da = importlib.util.module_from_spec(_da)
sys.modules["da"] = da
_da.loader.exec_module(da)


def sector_of(ticker):
    p = ROOT / f"wiki/entities/tickers/{ticker.lower()}.md"
    if not p.is_file():
        return None
    m = re.search(r'^sector:\s*"?(.+?)"?\s*$', p.read_text(encoding="utf-8", errors="replace"), re.M)
    return m.group(1).strip() if m else None


def corr(con, a, b, n=90):
    """Correlation of daily returns over the last n SHARED bars, from the store.
    Local implementation (bulk-data-pull.beta_corr takes closes+bench lists).

    Aligned on date, not on position: a session one ticker has and the other
    does not (halt, crypto weekend, bar not loaded) would otherwise shift one
    return series against the other and corrupt every pair it touches."""
    # One join, so the window is the last n dates BOTH tickers have. Taking each
    # ticker's own last n rows first and intersecting afterwards gives "shared
    # dates within each ticker's own window": on mixed calendars (crypto trades
    # weekends) only ~62 of 90 survive, and a history that ends 61+ sessions
    # early returns None even with hundreds of shared dates.
    rows = con.execute(
        "SELECT x.date, x.close, y.close FROM bars x JOIN bars y "
        "ON y.ticker=? AND y.date=x.date WHERE x.ticker=? ORDER BY x.date DESC LIMIT ?",
        (b, a, n)).fetchall()
    rows.reverse()
    k = len(rows)
    if k < 30:
        return None
    ca = [r[1] for r in rows]
    cb = [r[2] for r in rows]
    ra = [ca[i] / ca[i - 1] - 1 for i in range(1, k)]
    rb = [cb[i] / cb[i - 1] - 1 for i in range(1, k)]
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb)) / (len(ra) - 1)
    va = sum((x - ma) ** 2 for x in ra) / (len(ra) - 1)
    vb = sum((y - mb) ** 2 for y in rb) / (len(rb) - 1)
    return cov / ((va * vb) ** 0.5) if va and vb else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "Efforts/osanwe-v2-overhaul/_work/factors.db"))
    ap.add_argument("--horizon", type=int, default=21)
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    commits = bp1.analysis_commits()
    seen = set()
    rows = []
    for c in commits:
        key = (c["t0"], c["path"])
        if key in seen or not c["path"].endswith(".md"):
            continue
        seen.add(key)
        asof = bp1.sh("git", "show", f"{c['sha']}:{c['path']}")
        meta = bp1.parse_analysis_text(asof, c["path"])
        if not meta["ticker"] or not meta["verdict"]:
            continue
        dollars = da.parse_action_dollars(asof)
        if dollars is None or dollars <= 0:
            continue
        stk = bo.stats_from_series(bo.store_window(con, meta["ticker"], c["t0"], args.horizon), args.horizon)
        ben = bo.stats_from_series(bo.store_window(con, "SPY", c["t0"], args.horizon), args.horizon)
        if not stk or not ben:
            continue
        rows.append({"date": c["t0"], "ticker": meta["ticker"], "usd": dollars,
                     "alpha": dollars * (stk["ret_pct"] - ben["ret_pct"]) / 100,
                     "sector": sector_of(meta["ticker"]) or "unknown"})

    by_sector = {}
    for r in rows:
        s = by_sector.setdefault(r["sector"], {"usd": 0.0, "alpha": 0.0, "n": 0})
        s["usd"] += r["usd"]
        s["alpha"] += r["alpha"]
        s["n"] += 1
    total_usd = sum(s["usd"] for s in by_sector.values())

    lines = ["---", "aliases: []", "categories: [wiki]", "type: report",
             "status: active", "created: 2026-08-23", "updated: 2026-08-23",
             "tags: []", 'related: ["[[FINANCIAL-SOTA-ROADMAP]]"]',
             "---", "",
             f"# Sector-aware attribution ({args.horizon}d)", "",
             f"Deployed ${total_usd:,.0f} across {len(rows)} actions "
             f"({len(by_sector)} sectors).", ""]
    lines += ["| sector | deployed | n | alpha vs SPY | share |", "|---|---|---|---|---|"]
    for s in sorted(by_sector, key=lambda k: -by_sector[k]["usd"]):
        v = by_sector[s]
        share = v["usd"] / total_usd if total_usd else 0
        warn = " **CONCENTRATION >40%**" if share > 0.4 else ""
        lines.append(f"| {s} | ${v['usd']:,.0f} | {v['n']} | ${v['alpha']:+,.2f} | "
                     f"{share:.0%}{warn} |")

    # pairwise correlation of the distinct deployed tickers
    tks = sorted({r["ticker"] for r in rows})
    pairs = []
    for i in range(len(tks)):
        for j in range(i + 1, len(tks)):
            c = corr(con, tks[i], tks[j])
            if c is not None and c > 0.75:
                pairs.append((tks[i], tks[j], round(c, 2)))
    lines += ["", "## Highly correlated deployed pairs (rho > 0.75) -- these are",
              "NOT independent bets:", ""]
    lines += [f"- {a} / {b}: rho={c}" for a, b, c in sorted(pairs, key=lambda x: -x[2])[:12]] or \
             ["- none above threshold"]
    high_corr_n = sum(1 for _, _, c in pairs if c > 0.85)
    lines.append("")
    lines.append(f"Pairs above 0.85: {high_corr_n} -- effective independent-bet count "
                 "is materially lower than ticker count suggests.")

    out = ROOT / "wiki/maintenance/calibration/sector-attribution.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"-> {out.relative_to(ROOT)}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

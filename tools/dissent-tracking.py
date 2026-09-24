#!/usr/bin/env python3
"""dissent-tracking.py -- P6: score subagent dissent against realized outcomes.

Extracts thesis-critic failure modes (id, probability, magnitude) from analysis
frontmatter (`variant_view:` prose + `fm:` rows where present) and, for those
past their horizon, checks price paths from the factor store against each
failure mode's implied direction (downside modes realize if mae breached the
mode's materiality threshold; upside modes via mfe).

HONESTY: v1 tracks DOWNSIDE realization only (mae_pct <= -threshold), because
failure-mode text encodes downside risks. Per-role attribution arrives when
role ids land in frontmatter.
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


def parse_failure_modes(text):
    """Pull K.5 failure modes: numbered list items near 'failure mode' mentions
    with a probability. Returns [(short_desc, prob_pct)]."""
    modes = []
    section = re.search(r"(?:Variant View|Failure[M ]odes?)(.*?)(?=^## |\Z)", text,
                        re.S | re.M)
    blob = section.group(1) if section else ""
    for m in re.finditer(r"^[-*\d\.\s]*([A-Z][^\n]{15,150}?)[^\n]*?(\d{1,3})\s*%[^\n]*$", blob, re.M):
        desc = re.sub(r"\s+", " ", m.group(1)).strip()
        prob = int(m.group(2))
        if 0 < prob <= 100:
            modes.append((desc[:90], prob))
    return modes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "Efforts/osanwe-v2-overhaul/_work/factors.db"))
    ap.add_argument("--materiality", type=float, default=8.0,
                    help="a downside mode 'realizes' if drawdown <= -threshold pct")
    ap.add_argument("--out", default=str(ROOT / "wiki/maintenance/calibration/dissent-tracking.md"))
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    commits = bp1.analysis_commits()
    total_modes = 0
    realized = 0
    high_prob_modes = []   # prob >= 40
    high_realized = 0
    per_call = []
    for c in commits:
        asof = bp1.sh("git", "show", f"{c['sha']}:{c['path']}")
        meta = bp1.parse_analysis_text(asof, c["path"])
        if not meta["ticker"]:
            continue
        modes = parse_failure_modes(asof)
        if not modes:
            continue
        stk = bo.stats_from_series(bo.store_window(con, meta["ticker"], c["t0"], 21), 21)
        if not stk:
            continue
        dd = stk["mae_pct"]
        call_realized = [p for (_, p) in modes if p >= args.materiality and dd <= -args.materiality]
        n_hi = sum(1 for _, p in modes if p >= 40)
        hi_hit = any(p >= 40 for p in call_realized)
        total_modes += len(modes)
        realized += len(call_realized)
        high_prob_modes += [(meta["ticker"], c["t0"], d, p) for d, p in modes if p >= 40]
        if hi_hit:
            high_realized += 1
        per_call.append({"ticker": meta["ticker"], "date": c["t0"],
                         "modes": len(modes), "max_prob": max(p for _, p in modes),
                         "drawdown": dd})

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
             "# Dissent tracking -- failure modes vs realized drawdowns", "",
             f"Parsed {total_modes} failure modes across {len(per_call)} analyses "
             f"(21d window; a mode 'realizes' when the ticker drew down >="
             f"{args.materiality:.0f}% within horizon).", "",
             f"- Modes realizing at >= {args.materiality:.0f}% drawdown: "
             f"{realized}/{total_modes} ({realized/max(total_modes,1):.0%})",
             f"- High-probability modes (>=40%): {len(high_prob_modes)}; "
             f"calls where a >=40% mode accompanied a >= {args.materiality:.0f}% drawdown: "
             f"{high_realized}/{len(per_call)} calls", "",
             "## Calls with the deepest drawdowns", "",
             "| date | ticker | modes | max prob | drawdown |", "|---|---|---|---|---|"]
    for pc in sorted(per_call, key=lambda x: x["drawdown"])[:10]:
        lines.append(f"| {pc['date']} | {pc['ticker']} | {pc['modes']} | "
                     f"{pc['max_prob']}% | {pc['drawdown']:.1f}% |")
    lines += ["", "NOTE: v1 measures whether LARGE drawdowns followed calls that "
              "carried high-probability failure modes. Mode-text semantic matching "
              "(which specific mode fired) lands with stable mode ids in frontmatter."]

    out = Path(args.out)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"-> {out.relative_to(ROOT)}")
    print("\n".join(lines[16:19]))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

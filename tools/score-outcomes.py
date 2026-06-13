#!/usr/bin/env python3
"""score-outcomes.py -- /invest Phase R backfill + rolling Brier (vNEXT 2026-06-09).

Deterministic, zero model judgment. Three jobs:
  1. BACKFILL: for calibration-monitor rows past their 1/3/6-month horizons with
     blank ret_* cells, fetch realized closes (yfinance, offline) and fill the cells.
  2. BRIER: compute rolling Brier(new_rating) vs Brier(shadow_rating) at n>=5,
     BOTH pooled and topology-stratified (groupby the `topology` column; rows
     without a topology value are the `sequential-legacy` stratum).
  3. ROLLBACK ASSESSMENT: report the Phase R.3 pre-committed trigger state
     (armed at >=8 calls realized at >=3mo; fires if Brier(new) worse by >0.05
     and not single-name/crash attributable -- attribution is a HUMAN call,
     this script only surfaces the numbers).

Data-source note: this is an OFFLINE script -- it cannot reach session-scoped
MCP tools. "Robinhood MCP primary" is honored at the consuming-skill layer:
/invest Phase R.5 (in-session) may overwrite ret_* cells with broker-
authoritative values. This script is the floor that makes the ~2026-08 GUARD-2
window able to fire at all.

CLI:
  python tools/score-outcomes.py [--dry-run] [--json] [--verbose]
                                 [--fixture PATH] [--monitor PATH]

File-edit safety: sha256 of all content OUTSIDE the Call Log table must be
byte-identical pre/post; untouched rows round-trip byte-identical (legacy
11-cell rows under the 13-column header are preserved as-is unless their
ret_* cells are being filled).
"""

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent
MONITOR_PATH = VAULT_ROOT / "wiki" / "investing" / "calibration-monitor.md"

# ---------------------------------------------------------------------------
# RATING_PROB_MAP -- pre-registered priors (USER-RATIFIABLE; ratified 2026-06-09)
#
# Semantics: probability assigned to the event "3mo realized return > 0".
#
# FREEZE RULE (strategist rider R1, 2026-06-09): these constants are IMMUTABLE
# from the moment the first scored row lands in calibration-monitor.md. Any
# later change requires a /decide with its own Brier-impact note AND re-scoring
# of all history under BOTH maps. Rationale: a tunable probability map is a
# post-hoc calibration-laundering vector; pre-registration is what makes the
# GUARD-2 pre-registered rollback window evaluation honest.
# ---------------------------------------------------------------------------
RATING_PROB_MAP = {
    "STRONG BUY": 0.85,
    "BUY": 0.70,
    "HOLD": None,   # excluded from Brier (no directional probability claim)
    "SELL": 0.30,
    "STRONG SELL": 0.15,
    "NR": None,     # excluded per calibration-monitor prose
}

HORIZONS = {"ret_1mo": 30, "ret_3mo": 91, "ret_6mo": 182}  # calendar days
PRIMARY_HORIZON = "ret_3mo"
N_FLOOR_POOLED = 5
N_FLOOR_STRATUM = 3
ROLLBACK_REALIZED_FLOOR = 8
ROLLBACK_BRIER_GAP = 0.05
LEGACY_STRATUM = "sequential-legacy"
CRYPTO_HINTS = {"BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "AVAX", "DOT", "LINK", "LTC"}


def log(msg, verbose):
    if verbose:
        print(f"[score-outcomes] {msg}", file=sys.stderr)


def parse_rating(cell):
    """Extract a canonical rating from a cell ('SELL', 'N/A (excl Brier)', ...)."""
    text = cell.strip().upper()
    for rating in ("STRONG BUY", "STRONG SELL", "BUY", "HOLD", "SELL", "NR"):
        if text.startswith(rating):
            return rating
    return None


def parse_ret(cell):
    """Parse a filled ret_* cell like '+12.4%' / '-3.1%' / 'N/A' -> float or None."""
    text = cell.strip()
    if not text or text.upper().startswith("N/A"):
        return None
    m = re.match(r"^([+-]?\d+(?:\.\d+)?)\s*%$", text)
    return float(m.group(1)) / 100.0 if m else None


def find_table(lines):
    """Locate the Call Log table. Returns (header_idx, sep_idx, row_indices)."""
    in_section = False
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("## Call Log"):
            in_section = True
            continue
        if in_section and line.strip().startswith("|"):
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("Call Log table not found")
    sep_idx = header_idx + 1
    row_indices = []
    j = sep_idx + 1
    while j < len(lines) and lines[j].strip().startswith("|"):
        row_indices.append(j)
        j += 1
    return header_idx, sep_idx, row_indices


def split_row(line):
    """Split a markdown table row into stripped cells (outer pipes removed)."""
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_monitor(text):
    """Parse the monitor. Returns (lines, header_idx, sep_idx, rows).

    Each row dict: {idx, line, cells, colmap-applied fields}. Rows shorter than
    the header are padded with '' for missing trailing columns (legacy rows).
    """
    lines = text.splitlines(keepends=True)
    header_idx, sep_idx, row_indices = find_table(lines)
    header_cells = split_row(lines[header_idx])
    colmap = {}
    for i, name in enumerate(header_cells):
        key = name.strip().lower()
        if key.startswith("shadow_rating"):
            key = "shadow_rating"
        colmap[key] = i
    rows = []
    for idx in row_indices:
        cells = split_row(lines[idx])
        padded = cells + [""] * (len(header_cells) - len(cells))

        def get(col):
            i = colmap.get(col)
            return padded[i] if i is not None and i < len(padded) else ""

        rows.append({
            "idx": idx,
            "line": lines[idx],
            "cells": cells,
            "n_cells": len(cells),
            "date": get("date"),
            "ticker": get("ticker"),
            "new_rating": parse_rating(get("new_rating")),
            "shadow_rating": parse_rating(get("shadow_rating")),
            "topology": get("topology") or LEGACY_STRATUM,
            "ret": {h: get(h) for h in HORIZONS},
        })
    return lines, header_idx, sep_idx, colmap, rows


def fetch_realized_return(ticker, analysis_date, horizon_days, verbose):
    """(close@horizon - close@analysis) / close@analysis via yfinance; None on failure."""
    try:
        import yfinance as yf
    except ImportError:
        log("yfinance not installed; cannot backfill", verbose)
        return None

    def closes(symbol):
        start = analysis_date - timedelta(days=7)
        end = analysis_date + timedelta(days=horizon_days + 7)
        try:
            df = yf.download(symbol, start=start.isoformat(), end=end.isoformat(),
                             progress=False, auto_adjust=False)
        except Exception as exc:
            log(f"{symbol}: download failed ({exc})", verbose)
            return None
        if df is None or df.empty:
            return None
        out = []
        for ts, row in df.iterrows():
            close = row["Close"]
            if hasattr(close, "iloc"):
                close = close.iloc[0]
            out.append((ts.date(), float(close)))
        return out

    series = closes(ticker)
    if series is None and ticker.upper() in CRYPTO_HINTS:
        series = closes(f"{ticker.upper()}-USD")
    if not series:
        return None
    anchor = next((c for d, c in series if d >= analysis_date), None)
    target_date = analysis_date + timedelta(days=horizon_days)
    realized = next((c for d, c in series if d >= target_date), None)
    time.sleep(0.5)  # defensive yfinance rate-limit spacing
    if anchor is None or realized is None or anchor == 0:
        return None
    return (realized - anchor) / anchor


def rebuild_row(row, colmap, header_len, fills):
    """Rebuild a row line with filled ret_* cells; pads legacy rows to header length."""
    cells = row["cells"] + [""] * (header_len - row["n_cells"])
    for col, value in fills.items():
        cells[colmap[col]] = value
    return "| " + " | ".join(cells) + " |\n"


def backfill(lines, colmap, rows, today, dry_run, verbose):
    """Fill blank ret_* cells for rows past their horizons. Returns change log."""
    header_len = len(colmap)
    changes = []
    for row in rows:
        if row["new_rating"] == "NR":
            continue
        try:
            d = date.fromisoformat(row["date"])
        except ValueError:
            log(f"row {row['idx']}: unparseable date '{row['date']}' -- skipped", verbose)
            continue
        fills = {}
        for col, days in HORIZONS.items():
            if row["ret"][col].strip():
                continue  # already filled
            if today < d + timedelta(days=days):
                continue  # horizon not reached
            ret = fetch_realized_return(row["ticker"], d, days, verbose)
            fills[col] = f"{ret * 100:+.1f}%" if ret is not None else "N/A"
        if fills:
            changes.append({"ticker": row["ticker"], "date": row["date"], "fills": fills})
            if not dry_run:
                new_line = rebuild_row(row, colmap, header_len, fills)
                lines[row["idx"]] = new_line
                row["line"] = new_line
                for col, value in fills.items():
                    row["ret"][col] = value
    return changes


def brier(rows, rating_key, horizon=PRIMARY_HORIZON):
    """Brier score over rows with a prob-mapped rating AND a realized horizon return."""
    total, n = 0.0, 0
    for row in rows:
        p = RATING_PROB_MAP.get(row[rating_key] or "")
        if p is None:
            continue
        ret = parse_ret(row["ret"][horizon])
        if ret is None:
            continue
        o = 1.0 if ret > 0 else 0.0
        total += (p - o) ** 2
        n += 1
    return {"brier": round(total / n, 6) if n else None, "n": n}


def assess(rows):
    """Pooled + stratified Brier and the Phase R.3 rollback-trigger state."""
    pooled_new = brier(rows, "new_rating")
    pooled_shadow = brier(rows, "shadow_rating")
    pooled = {
        "new": pooled_new, "shadow": pooled_shadow,
        "meets_n_floor": pooled_new["n"] >= N_FLOOR_POOLED,
    }
    strata = {}
    for stratum in sorted({r["topology"] for r in rows}):
        subset = [r for r in rows if r["topology"] == stratum]
        s_new = brier(subset, "new_rating")
        s_shadow = brier(subset, "shadow_rating")
        strata[stratum] = {
            "new": s_new, "shadow": s_shadow,
            "sufficient": s_new["n"] >= N_FLOOR_STRATUM,
        }
    realized = sum(
        1 for r in rows
        if r["new_rating"] not in (None, "NR") and parse_ret(r["ret"][PRIMARY_HORIZON]) is not None
    )
    gap = None
    if pooled_new["brier"] is not None and pooled_shadow["brier"] is not None:
        gap = round(pooled_new["brier"] - pooled_shadow["brier"], 6)
    armed = realized >= ROLLBACK_REALIZED_FLOOR
    fired = bool(armed and gap is not None and gap > ROLLBACK_BRIER_GAP)
    rollback = {
        "realized_at_3mo": realized,
        "armed": armed,
        "pooled_gap_new_minus_shadow": gap,
        "fired_numerically": fired,
        "note": ("Attribution check (single name / crash window) and the topology-"
                 "stratified view are MANDATORY before acting on a numeric fire "
                 "(GUARD-2 stratification rider S1)."),
    }
    return {"pooled": pooled, "stratified": strata, "rollback": rollback}


def outside_table_sha256(lines, header_idx, sep_idx, n_rows):
    """sha256 of all content outside the Call Log table rows (header+sep included
    as OUTSIDE -- this script never edits them)."""
    table = set(range(sep_idx + 1, sep_idx + 1 + n_rows))
    blob = "".join(l for i, l in enumerate(lines) if i not in table)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def main():
    ap = argparse.ArgumentParser(description="Phase R backfill + rolling Brier")
    ap.add_argument("--dry-run", action="store_true", help="no file edits; report only")
    ap.add_argument("--json", action="store_true", help="emit JSON to stdout")
    ap.add_argument("--fixture", type=Path, help="synthetic monitor file (test mode)")
    ap.add_argument("--monitor", type=Path, default=MONITOR_PATH, help="monitor path override")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    path = args.fixture or args.monitor
    if not path.exists():
        print(f"ERROR: {path} not found", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8")
    lines, header_idx, sep_idx, colmap, rows = parse_monitor(text)
    pre_sha = outside_table_sha256(lines, header_idx, sep_idx, len(rows))
    log(f"parsed {len(rows)} rows, {len(colmap)} columns from {path.name}", args.verbose)

    today = date.today()
    # Fixture mode = offline test mode: never backfill (no network); Brier only.
    if args.fixture:
        changes = []
    else:
        changes = backfill(lines, colmap, rows, today, args.dry_run, args.verbose)
    result = assess(rows)
    result["backfilled"] = changes
    result["dry_run"] = args.dry_run
    result["monitor"] = str(path)
    result["rows_parsed"] = len(rows)

    if changes and not args.dry_run:
        post_sha = outside_table_sha256(lines, header_idx, sep_idx, len(rows))
        if post_sha != pre_sha:
            print("ERROR: sha256 gate -- content outside the Call Log table mutated; "
                  "write ABORTED", file=sys.stderr)
            return 2
        path.write_text("".join(lines), encoding="utf-8")
        log(f"wrote {sum(len(c['fills']) for c in changes)} cell(s) to {path.name}",
            args.verbose)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        p = result["pooled"]
        print(f"rows={len(rows)} backfilled_rows={len(changes)} dry_run={args.dry_run}")
        print(f"Brier pooled: new={p['new']['brier']} (n={p['new']['n']}) "
              f"shadow={p['shadow']['brier']} (n={p['shadow']['n']}) "
              f"n_floor_met={p['meets_n_floor']}")
        for name, s in result["stratified"].items():
            print(f"Brier stratum {name}: new={s['new']['brier']} (n={s['new']['n']}) "
                  f"shadow={s['shadow']['brier']} (n={s['shadow']['n']}) "
                  f"sufficient={s['sufficient']}")
        rb = result["rollback"]
        print(f"Rollback: realized_at_3mo={rb['realized_at_3mo']} armed={rb['armed']} "
              f"gap={rb['pooled_gap_new_minus_shadow']} fired={rb['fired_numerically']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

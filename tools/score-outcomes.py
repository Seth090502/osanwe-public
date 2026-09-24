#!/usr/bin/env python3
"""score-outcomes.py -- /invest Phase R backfill + rolling Brier (vNEXT 2026-06-09).

Deterministic, zero model judgment. Three jobs:
  1. BACKFILL: for calibration-monitor rows past their 1/3/6-month horizons with
     blank ret_* cells, resolve dated closes and fill only supported outcomes.
  2. BRIER: compare new/shadow Brier on the SAME realized, supported pairs at n>=5,
     BOTH pooled and topology-stratified (groupby the `topology` column; rows
     without a topology value are the `sequential-legacy` stratum). Marginal
     scores are descriptive only; missing comparisons remain in coverage counts.
  3. ROLLBACK ASSESSMENT: report the Phase R.3 pre-committed trigger state
     (armed at >=8 calls realized at >=3mo; fires if Brier(new) worse by >0.05
     and not single-name/crash attributable -- attribution is a HUMAN call,
     this script only surfaces the numbers).

Data-source note: this is offline-first with a public yfinance fallback; it
cannot reach session-scoped MCP tools. "Robinhood MCP primary" is honored at the consuming-skill layer:
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
import contextlib
import hashlib
import json
import math
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent
MONITOR_PATH = VAULT_ROOT / "wiki" / "investing" / "calibration-monitor.md"

# ---------------------------------------------------------------------------
# RATING_PROB_MAP -- pre-registered priors (<owner>-RATIFIABLE; ratified 2026-06-09)
#
# Semantics: probability assigned to the event "3mo realized return > 0".
#
# FREEZE RULE (strategist rider R1, 2026-06-09): these constants are IMMUTABLE
# from the moment the first scored row lands in calibration-monitor.md. Any
# later change requires a /decide with its own Brier-impact note AND re-scoring
# of all history under BOTH maps. Rationale: a tunable probability map is a
# post-hoc calibration-laundering vector; pre-registration is what makes the
# ~2026-08 GUARD-2 evaluation honest.
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
CRYPTO_HINTS = {"ADA", "ALGO", "AVAX", "BNB", "BTC", "DOGE", "DOT", "ETH", "HBAR", "LINK", "ONDO", "QNT", "SOL", "XDC", "XLM", "XRP"}
PRICE_RESOLUTION_PADDING_DAYS = 7  # Existing provider-window padding, now enforced as a bound.
FACTOR_DB = VAULT_ROOT / "Efforts/osanwe-v2-overhaul/_work/factors.db"


def log(msg, verbose):
    if verbose:
        print(f"[score-outcomes] {msg}", file=sys.stderr)


def parse_rating(cell):
    """Extract a canonical rating from a cell ('SELL', 'N/A (excl Brier)', ...)."""
    text = cell.strip().upper()
    if re.search(r"\bUNAVAILABLE\b", text):
        return None
    for rating in ("STRONG BUY", "STRONG SELL", "BUY", "HOLD", "SELL", "NR"):
        if re.match(r"^" + re.escape(rating) + r"\b", text):
            return rating
    return None


def parse_ret(cell):
    """Parse a filled ret_* cell like '+12.4%' / '-3.1%' / 'N/A' -> float or None."""
    text = cell.strip()
    if not text or text.upper().startswith("N/A"):
        return None
    m = re.match(r"^([+-]?\d+(?:\.\d+)?)\s*%$", text)
    value = float(m.group(1)) / 100.0 if m else None
    return value if value is not None and math.isfinite(value) else None


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
            "rating_cells": {key: get(key) for key in ("new_rating", "shadow_rating")},
            "topology": get("topology") or LEGACY_STRATUM,
            "ret": {h: get(h) for h in HORIZONS},
        })
    return lines, header_idx, sep_idx, colmap, rows


def select_realized_observation(series, analysis_date, horizon_days, as_of=None):
    """First observed closes on/after the two nominal dates, within old padding.

    HORIZONS remain calendar-day offsets from the analysis date, not bar counts
    or offsets from a delayed entry. Current-day bars have unknown finality and
    are excluded. Missing endpoints, conflicting dates or bad endpoint prices
    are unavailable, never substitutes from a later day or a truncated window.
    This does not attest that a provider's calendar or historical data is complete.
    """
    as_of = date.today() if as_of is None else as_of
    if (type(analysis_date) is not date or type(as_of) is not date
            or type(horizon_days) is not int or horizon_days <= 0):
        return None
    try:
        target = analysis_date + timedelta(days=horizon_days)
        last_allowed = target + timedelta(days=PRICE_RESOLUTION_PADDING_DAYS)
    except OverflowError:
        return None
    if target >= as_of or not isinstance(series, (list, tuple)):
        return None
    dated = {}
    for item in series:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            return None
        when, price = item
        if isinstance(when, str):
            try:
                parsed = date.fromisoformat(when)
            except ValueError:
                return None
            if parsed.isoformat() != when:
                return None
            when = parsed
        if type(when) is not date:
            return None
        if when < analysis_date or when > last_allowed or when >= as_of:
            continue
        if when in dated:
            return None
        dated[when] = price
    ordered = sorted(dated)
    entry_day = next((day for day in ordered if day >= analysis_date), None)
    exit_day = next((day for day in ordered if day >= target), None)
    if (entry_day is None or exit_day is None or exit_day <= entry_day
            or (entry_day - analysis_date).days > PRICE_RESOLUTION_PADDING_DAYS
            or (exit_day - target).days > PRICE_RESOLUTION_PADDING_DAYS):
        return None
    values = [dated[entry_day], dated[exit_day]]
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
        return None
    try:
        if any(not math.isfinite(value) or value <= 0 for value in values):
            return None
        realized = values[1] / values[0] - 1
    except (OverflowError, ZeroDivisionError):
        return None
    if not math.isfinite(realized):
        return None
    return {"return": realized, "analysis_date": analysis_date.isoformat(),
            "target_date": target.isoformat(), "entry_date": entry_day.isoformat(),
            "exit_date": exit_day.isoformat(), "entry_close": values[0], "exit_close": values[1],
            "as_of_exclusive": as_of.isoformat(), "horizon_calendar_days": horizon_days,
            "resolution_padding_days": PRICE_RESOLUTION_PADDING_DAYS}


def yfinance_series(ticker, start, end):
    """Return dated adjusted closes, retaining invalid prices for selector refusal."""
    import yfinance as yf
    history = yf.Ticker(ticker).history(start=start.isoformat(), end=end.isoformat(),
                                       auto_adjust=True, keepna=True, raise_errors=True, timeout=15)
    if history is None or history.empty:
        return []
    rows = []
    for ts, close in history["Close"].items():
        try:
            value = float(close) if not isinstance(close, bool) else None
            if value is not None and not math.isfinite(value):
                value = None
        except (TypeError, ValueError, OverflowError):
            value = None
        rows.append((ts.date().isoformat(), value))
    return rows


def toolchain_series(ticker, start, end):
    """A child returns dated bars; the parent applies the same horizon selector."""
    for candidate in (r"/path/to/python\python.exe",):
        if os.path.isfile(candidate):
            try:
                result = subprocess.run(
                    [candidate, str(Path(__file__).resolve()), "--provider-series", ticker,
                     start.isoformat(), end.isoformat()], capture_output=True, text=True, timeout=30)
                if result.returncode == 0 and result.stdout.strip():
                    return json.loads(result.stdout.strip().splitlines()[-1])
            except (subprocess.SubprocessError, OSError, ValueError):
                pass
    return None


def fetch_realized_observation(ticker, analysis_date, horizon_days, verbose, *, as_of=None):
    """Resolve one complete observation without mixing provider endpoints/bases."""
    as_of = date.today() if as_of is None else as_of
    if (type(analysis_date) is not date or type(as_of) is not date
            or type(horizon_days) is not int or horizon_days <= 0):
        return None
    try:
        target = analysis_date + timedelta(days=horizon_days)
        start = analysis_date - timedelta(days=PRICE_RESOLUTION_PADDING_DAYS)
        end = min(target + timedelta(days=PRICE_RESOLUTION_PADDING_DAYS + 1), as_of)
    except OverflowError:
        return None
    if target >= as_of:
        return None
    if not isinstance(ticker, str) or not re.fullmatch(r"[A-Za-z0-9.^=-]{1,24}", ticker):
        return None
    if ticker.upper() in CRYPTO_HINTS:
        log("ambiguous bare instrument symbol; explicit price identity required, row stays blank", verbose)
        return None

    def select(rows, source):
        value = select_realized_observation(rows, analysis_date, horizon_days, as_of)
        if value is not None:
            value.update({"source": source, "price_symbol": ticker.upper(),
                          "price_basis": "yfinance auto_adjust=True, matching factor-store ingestion"})
        return value

    try:
        if FACTOR_DB.is_file():
            with contextlib.closing(sqlite3.connect(FACTOR_DB.resolve().as_uri() + "?mode=ro", uri=True)) as con:
                rows = con.execute(
                    "SELECT date, close, src FROM bars WHERE ticker=? AND date>=? AND date<? ORDER BY date",
                    (ticker.upper(), start.isoformat(), end.isoformat())).fetchall()
            if rows and all(row[2] == "yfinance" for row in rows):
                value = select([(row[0], row[1]) for row in rows], "factor-store")
                if value is not None:
                    return value
    except (sqlite3.Error, OSError):
        pass
    try:
        rows = yfinance_series(ticker, start, end)
        source = "yfinance-direct"
    except ImportError:
        rows = toolchain_series(ticker, start, end)
        source = "yfinance-toolchain"
    except Exception:
        log("price provider failed; row stays blank", verbose)
        return None
    value = select(rows, source)
    if value is None:
        log("dated price endpoints unavailable or invalid; row stays blank", verbose)
    return value


def fetch_realized_return(ticker, analysis_date, horizon_days, verbose, *, as_of=None):
    """Compatibility interface returning a value only for a supported observation."""
    value = fetch_realized_observation(ticker, analysis_date, horizon_days, verbose, as_of=as_of)
    return value["return"] if value is not None else None


def rebuild_row(row, colmap, header_len, fills):
    """Fill addressed cells only, preserving untouched cell bytes and line ending."""
    body = row["line"].rstrip("\r\n")
    if not body.lstrip().startswith("|") or not body.rstrip().endswith("|"):
        raise ValueError("incomplete table-row delimiters; write withheld")
    cells = body.split("|")
    needed = max((colmap[col] + 1 for col in fills), default=0)
    if needed > header_len:
        raise ValueError("filled column exceeds declared header")
    while len(cells) - 2 < needed:
        cells.insert(-1, " ")
    for col, value in fills.items():
        index = colmap[col] + 1
        raw = cells[index]
        leading = raw[:len(raw) - len(raw.lstrip(" \t"))]
        trailing = raw[len(raw.rstrip(" \t")):]
        cells[index] = leading + value + trailing
    ending = row["line"][len(row["line"].rstrip("\r\n")):]
    return "|".join(cells) + ending


def backfill(lines, colmap, rows, today, dry_run, verbose, unavailable=None):
    """Fill blank ret_* cells for rows past their horizons. Returns change log."""
    header_len = len(colmap)
    changes = []
    unavailable = unavailable if unavailable is not None else []
    for row in rows:
        if row["new_rating"] == "NR":
            continue
        try:
            d = date.fromisoformat(row["date"])
            if d.isoformat() != row["date"]:
                raise ValueError("noncanonical analysis date")
        except ValueError:
            log(f"row {row['idx']}: unparseable date '{row['date']}' -- skipped", verbose)
            unavailable.append({"row": row["idx"], "reason": "analysis_date_unavailable"})
            continue
        fills = {}
        observations = {}
        for col, days in HORIZONS.items():
            if row["ret"][col].strip():
                continue  # already filled
            try:
                mature_on = d + timedelta(days=days)
            except OverflowError:
                unavailable.append({"row": row["idx"], "horizon": col, "reason": "horizon_date_unavailable"})
                continue
            if today <= mature_on:
                unavailable.append({"row": row["idx"], "horizon": col, "reason": "horizon_or_closing_price_immature"})
                continue
            value = fetch_realized_observation(row["ticker"], d, days, verbose, as_of=today)
            if value is None:
                unavailable.append({"row": row["idx"], "horizon": col, "reason": "dated_price_or_identity_unavailable"})
                continue  # preserve blank for a future supported observation, never impute N/A/zero
            fills[col] = f"{value['return'] * 100:+.1f}%"
            observations[col] = value
        if fills:
            changes.append({"ticker": row["ticker"], "date": row["date"], "fills": fills,
                            "observations": observations})
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


def rating_status(row, key):
    """Keep missing/unknown/nondirectional inputs visible without assigning a prior."""
    rating = row[key]
    if RATING_PROB_MAP.get(rating or "") is not None:
        return "supported"
    if rating in ("HOLD", "NR"):
        return rating.lower()
    raw = row.get("rating_cells", {}).get(key, "").strip().upper()
    if not raw:
        return "missing"
    if re.search(r"\bUNAVAILABLE\b", raw) or raw.startswith("N/A"):
        return "unavailable"
    return "unrecognized"


def outcome_status(row, as_of):
    """Classify the primary horizon, retaining immature and absent observations."""
    raw = row["ret"][PRIMARY_HORIZON].strip()
    try:
        mature_on = date.fromisoformat(row["date"]) + timedelta(days=HORIZONS[PRIMARY_HORIZON])
    except (ValueError, KeyError, TypeError):
        return "unavailable_date"
    if as_of < mature_on:
        return "immature"
    if parse_ret(raw) is not None:
        return "realized"
    if not raw:
        return "missing"
    if raw.upper().startswith(("N/A", "UNAVAILABLE")):
        return "unavailable"
    return "invalid"


def comparison(rows, floor, as_of):
    """One eligibility mask for both scores; marginal results never drive a gap."""
    paired, realized_rows = [], []
    outcome_counts = {}
    rating_counts = {key: {} for key in ("new_rating", "shadow_rating")}
    for row in rows:
        outcome = outcome_status(row, as_of)
        outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
        statuses = {}
        for key, counts in rating_counts.items():
            statuses[key] = rating_status(row, key)
            counts[statuses[key]] = counts.get(statuses[key], 0) + 1
        if outcome == "realized":
            realized_rows.append(row)
            if all(status == "supported" for status in statuses.values()):
                paired.append(row)
    new, shadow = brier(paired, "new_rating"), brier(paired, "shadow_rating")
    available = len(paired) >= floor
    return {
        "new": new, "shadow": shadow, "paired_n": len(paired),
        "status": "available" if available else "unavailable",
        "unavailable_reason": None if available else "insufficient_supported_realized_pairs",
        "required_pairs": floor,
        "gap_new_minus_shadow": round(new["brier"] - shadow["brier"], 6) if available else None,
        "marginal_descriptive": {
            "new": brier(realized_rows, "new_rating"),
            "shadow": brier(realized_rows, "shadow_rating"),
            "scope": "separate supported samples; not a comparative estimate",
        },
        "coverage": {
            "total_rows": len(rows), "paired_rows": len(paired),
            "excluded_rows": len(rows) - len(paired),
            "outcome_status_counts": outcome_counts,
            "rating_status_counts": rating_counts,
            "note": "Each status dimension retains every row. Paired scores are conditional on comparable coverage.",
        },
    }


def assess(rows, as_of=None):
    """Pooled + stratified paired Brier; preserve the original eight-call arm."""
    as_of = as_of or date.today()
    pooled = comparison(rows, N_FLOOR_POOLED, as_of)
    pooled["meets_n_floor"] = pooled["status"] == "available"
    strata = {}
    for stratum in sorted({r["topology"] for r in rows}):
        subset = [r for r in rows if r["topology"] == stratum]
        strata[stratum] = comparison(subset, N_FLOOR_STRATUM, as_of)
        strata[stratum]["sufficient"] = strata[stratum]["status"] == "available"
    # This is the original arming definition, including HOLD and rows without a
    # usable shadow. Arming is distinct from availability of the paired comparison.
    realized = sum(
        1 for r in rows
        if r["new_rating"] not in (None, "NR") and parse_ret(r["ret"][PRIMARY_HORIZON]) is not None
    )
    gap = pooled["gap_new_minus_shadow"]
    armed = realized >= ROLLBACK_REALIZED_FLOOR
    fired = bool(armed and gap is not None and gap > ROLLBACK_BRIER_GAP)
    rollback = {
        "realized_at_3mo": realized,
        "armed": armed,
        "comparison_status": pooled["status"],
        "comparison_unavailable_reason": pooled["unavailable_reason"],
        "paired_n": pooled["paired_n"],
        "pooled_gap_new_minus_shadow": gap,
        "fired_numerically": fired,
        "note": ("Attribution check (single name / crash window) and the topology-"
                 "stratified view are MANDATORY before acting on a numeric fire "
                 "(GUARD-2 stratification rider S1)."),
    }
    return {"schema_version": 2, "as_of": as_of.isoformat(),
            "pooled": pooled, "stratified": strata, "rollback": rollback}


def outside_table_sha256(lines, header_idx, sep_idx, n_rows):
    """sha256 of all content outside the Call Log table rows (header+sep included
    as OUTSIDE -- this script never edits them)."""
    table = set(range(sep_idx + 1, sep_idx + 1 + n_rows))
    blob = "".join(l for i, l in enumerate(lines) if i not in table)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def write_monitor(path, text, expected_bytes):
    """Atomic replacement with original newline bytes and a concurrent-edit guard."""
    fd, name = tempfile.mkstemp(prefix=".score-outcomes-", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        if path.read_bytes() != expected_bytes:
            raise ValueError("monitor changed during run; write ABORTED")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(description="Phase R backfill + rolling Brier")
    ap.add_argument("--dry-run", action="store_true", help="no file edits; report only")
    ap.add_argument("--json", action="store_true", help="emit JSON to stdout")
    ap.add_argument("--fixture", type=Path, help="synthetic monitor file (test mode)")
    ap.add_argument("--monitor", type=Path, default=MONITOR_PATH, help="monitor path override")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--provider-series", nargs=3, metavar=("SYMBOL", "START", "END"),
                    help=argparse.SUPPRESS)
    args = ap.parse_args()

    if args.provider_series:
        try:
            symbol, start, end = args.provider_series
            rows = yfinance_series(symbol, date.fromisoformat(start), date.fromisoformat(end))
            print(json.dumps(rows, allow_nan=False))
            return 0
        except Exception:
            print("price series unavailable", file=sys.stderr)
            return 2

    path = args.fixture or args.monitor
    if not path.exists():
        print(f"ERROR: {path} not found", file=sys.stderr)
        return 2
    original_bytes = path.read_bytes()
    text = original_bytes.decode("utf-8")
    lines, header_idx, sep_idx, colmap, rows = parse_monitor(text)
    pre_sha = outside_table_sha256(lines, header_idx, sep_idx, len(rows))
    log(f"parsed {len(rows)} rows, {len(colmap)} columns from {path.name}", args.verbose)

    today = date.today()
    # Fixture mode = offline test mode: never backfill (no network); Brier only.
    unavailable = []
    if args.fixture:
        changes = []
    else:
        changes = backfill(lines, colmap, rows, today, args.dry_run, args.verbose, unavailable)
    result = assess(rows, as_of=today)
    result["backfilled"] = changes
    result["unavailable_outcomes"] = unavailable
    result["dry_run"] = args.dry_run
    result["monitor"] = str(path)
    result["rows_parsed"] = len(rows)
    result["producer_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

    if changes and not args.dry_run:
        post_sha = outside_table_sha256(lines, header_idx, sep_idx, len(rows))
        if post_sha != pre_sha:
            print("ERROR: sha256 gate -- content outside the Call Log table mutated; "
                  "write ABORTED", file=sys.stderr)
            return 2
        try:
            write_monitor(path, "".join(lines), original_bytes)
        except (OSError, ValueError) as error:
            print(f"ERROR: {error}", file=sys.stderr)
            return 2
        log(f"wrote {sum(len(c['fills']) for c in changes)} cell(s) to {path.name}",
            args.verbose)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        p = result["pooled"]
        print(f"rows={len(rows)} backfilled_rows={len(changes)} dry_run={args.dry_run}")
        print(f"Backfill unavailable outcomes: {len(unavailable)}")
        print(f"Brier pooled paired: new={p['new']['brier']} (n={p['new']['n']}) "
              f"shadow={p['shadow']['brier']} (n={p['shadow']['n']}) "
              f"n_floor_met={p['meets_n_floor']} status={p['status']}")
        m = p["marginal_descriptive"]
        print(f"Brier marginal descriptive only: new={m['new']['brier']} (n={m['new']['n']}) "
              f"shadow={m['shadow']['brier']} (n={m['shadow']['n']})")
        print("Comparison coverage: " + json.dumps(p["coverage"], sort_keys=True))
        for name, s in result["stratified"].items():
            print(f"Brier stratum {name}: new={s['new']['brier']} (n={s['new']['n']}) "
                  f"shadow={s['shadow']['brier']} (n={s['shadow']['n']}) "
                  f"sufficient={s['sufficient']}")
        rb = result["rollback"]
        print(f"Runtime: producer_sha256={result['producer_sha256']}")
        print(f"Rollback: realized_at_3mo={rb['realized_at_3mo']} armed={rb['armed']} "
              f"gap={rb['pooled_gap_new_minus_shadow']} fired={rb['fired_numerically']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

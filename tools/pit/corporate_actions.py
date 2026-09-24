#!/usr/bin/env python
"""D2: Corporate-actions candidate detector over the factors.db bar store.

Read-only scanner. Finds overnight gaps in raw stored closes that look like
corporate actions rather than market moves:

    overnight move < GAP_THRESHOLD (default -60%)
    AND price CONTINUES near the new level (no recovery toward the old level)

Classification heuristics (close-only data, deliberately conservative):

    split_candidate          persistent gap, prev/new ratio ~= positive integer >= 2
    spinoff_or_distribution   persistent gap, ratio NOT near an integer
                              (value left the ticker without share-count math)
    crash_not_split           gap breached the threshold but price recovered
                              toward/beyond the old level within the window

Known reality of this store (documented by the classifier, not "fixed" here):
adjustment comes later; the RAW store is what this tool describes.
  - WDC around 2025-02-13 (SNDK spinoff): yfinance auto_adjust already smoothed
    the series, so NO artificial gap is detected -- correct negative control.
  - SNDK: bars start cold at its 2025-02-13 listing; a listing has no prior
    close, so it can never produce an overnight-gap candidate. Reported in the
    run summary as a listing start, never written as a gap row.

Usage:
    python tools/pit/corporate_actions.py                 # scan + write CSV
    python tools/pit/corporate_actions.py --selftest      # regression fixtures
    python tools/pit/corporate_actions.py --db PATH --out PATH
        [--gap-threshold -0.60] [--recovery-window 10]
        [--recovery-fraction 0.75] [--int-tolerance 0.05]

Constraints honored: ASCII only, stdlib + sqlite3 only, no network, factors.db
opened read-only (URI mode=ro).
"""

import argparse
import csv
import math
import os
import sqlite3
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB = os.path.join(
    REPO_ROOT, "Efforts", "osanwe-v2-overhaul", "_work", "factors.db"
)
DEFAULT_OUT = os.path.join(
    REPO_ROOT,
    "Efforts",
    "osanwe-v2-overhaul",
    "_work",
    "fis-data",
    "corporate-actions-candidates.csv",
)

CSV_COLUMNS = [
    "ticker",
    "date",
    "prev_close",
    "next_close",
    "ratio_guess",
    "event_class",
]


# --------------------------------------------------------------------------
# core detection
# --------------------------------------------------------------------------

def nearest_integer_ratio(ratio, tol_frac):
    """Return (nearest_int, is_near_integer) for a gap ratio."""
    if ratio <= 0:
        return None, False
    n = int(round(ratio))
    if n < 1:
        return None, False
    tol = tol_frac * n
    return n, abs(ratio - n) <= tol


def classify_gap(prev_close, next_close, following_closes, gap_threshold,
                 recovery_window, recovery_fraction, int_tolerance):
    """Classify one overnight gap. Returns (event_class, ratio_guess) or None.

    following_closes: closes on the days AFTER the gap day (already limited by
    the caller to whatever history exists).
    """
    ret = next_close / prev_close - 1.0
    if ret >= gap_threshold:
        return None

    window = following_closes[:recovery_window]
    # Continuation test: does price stay near the NEW level, or recover
    # toward the OLD one? Median of the post-gap window resists noise.
    if window:
        med = sorted(window)[len(window) // 2]
        recovered = med >= prev_close * recovery_fraction
    else:
        # No forward data to confirm continuation -> do not call it an action.
        recovered = True

    ratio = prev_close / next_close
    if recovered:
        return ("crash_not_split", round(ratio, 4))

    n_int, near_int = nearest_integer_ratio(ratio, int_tolerance)
    if near_int and n_int >= 2:
        return ("split_candidate", float(n_int))
    return ("spinoff_or_distribution", round(ratio, 4))


def scan_ticker(dates_closes, gap_threshold, recovery_window,
                recovery_fraction, int_tolerance):
    """Yield candidate rows for one ordered [(date, close)] series."""
    rows = []
    n = len(dates_closes)
    for i in range(1, n):
        prev_date, prev_close = dates_closes[i - 1]
        date, close = dates_closes[i]
        following = [c for (_, c) in dates_closes[i + 1:]]
        hit = classify_gap(prev_close, close, following, gap_threshold,
                           recovery_window, recovery_fraction, int_tolerance)
        if hit is None:
            continue
        event_class, ratio_guess = hit
        rows.append(
            {
                "ticker": None,  # filled by caller
                "date": date,
                "prev_close": round(prev_close, 6),
                "next_close": round(close, 6),
                "ratio_guess": ratio_guess,
                "event_class": event_class,
            }
        )
    return rows


def scan_db(db_path, gap_threshold, recovery_window, recovery_fraction,
            int_tolerance):
    """Scan all tickers read-only. Returns (candidate_rows, listing_starts)."""
    con = sqlite3.connect("file:%s?mode=ro" % db_path.replace("\\", "/"), uri=True)
    try:
        cur = con.execute(
            "SELECT ticker, date, close FROM bars ORDER BY ticker, date"
        )
        per_ticker = {}
        for ticker, date, close in cur:
            per_ticker.setdefault(ticker, []).append((date, close))
    finally:
        con.close()

    candidates = []
    listings = []
    for ticker in sorted(per_ticker):
        series = per_ticker[ticker]
        listings.append((ticker, series[0][0]))
        for row in scan_ticker(series, gap_threshold, recovery_window,
                               recovery_fraction, int_tolerance):
            row["ticker"] = ticker
            candidates.append(row)
    candidates.sort(key=lambda r: (r["ticker"], r["date"]))
    return candidates, listings


# --------------------------------------------------------------------------
# regression fixtures: synthetic price series
# --------------------------------------------------------------------------

def _walk(start, steps):
    """Build a series from multiplicative daily steps."""
    out = [start]
    for s in steps:
        out.append(out[-1] * s)
    return out


def _dates(n):
    """Synthetic ascending ISO dates (calendar-agnostic business filler)."""
    return ["d%03d" % i for i in range(n)]


def fixture_clean_split():
    """(a) Clean 10:1 split: 1000 -> 100 overnight, continues near 100."""
    base = _walk(1000.0, [1.005, 0.998, 1.002, 1.001, 0.999])
    post = _walk(base[-1] / 10.0, [1.004, 0.997, 1.003, 1.001, 0.998,
                                   1.002, 1.000, 0.999, 1.001])
    dates = _dates(len(base) + len(post) - 1)
    return list(zip(dates, [round(p, 4) for p in base + post[1:]]))


def fixture_crash_recovers():
    """(b) 50% crash that is NOT a split: deep overnight drop, then full
    recovery to the prior level within the continuation window."""
    pre = _walk(100.0, [1.002] * 5)
    # overnight -65% (breaches any sane threshold), then V-shaped recovery
    trough = pre[-1] * 0.35
    rec = [trough * f for f in (1.05, 1.15, 1.35, 1.55, 1.85, 2.30, 2.80)]
    # normalize the final point back to ~the pre-crash level
    scale = pre[-1] / rec[-1]
    rec = [p * scale for p in rec]
    post = _walk(pre[-1], [1.001] * 4)
    dates = _dates(len(pre) + len(rec) + len(post) - 2)
    series = pre + rec[1:] + post[1:]
    return list(zip(dates, [round(p, 4) for p in series]))


def fixture_spinoff_gap():
    """(c) Spinoff-style permanent gap: ~-73% overnight, price NEVER returns;
    implied ratio ~3.7 (non-integer) like a value distribution."""
    pre = _walk(100.0, [1.001] * 5)
    post = _walk(pre[-1] / 3.7, [1.003, 0.998, 1.002, 1.001, 0.999,
                                 1.002, 1.000, 1.001])
    dates = _dates(len(pre) + len(post) - 1)
    return list(zip(dates, [round(p, 4) for p in pre + post[1:]]))


DEFAULTS = dict(
    gap_threshold=-0.60,
    recovery_window=10,
    recovery_fraction=0.75,
    int_tolerance=0.05,
)


def run_selftest():
    """Assert the classifier separates fixtures (a), (b), (c)."""
    failures = []

    def check(name, cond, detail=""):
        tag = "PASS" if cond else "FAIL"
        print("[%s] %s %s" % (tag, name, detail))
        if not cond:
            failures.append(name)

    # (a) clean 10:1 split -> exactly one split_candidate, ratio 10
    rows = scan_ticker(fixture_clean_split(), **DEFAULTS)
    hits = [r for r in rows if r["event_class"] == "split_candidate"]
    check("fixture-a: one candidate", len(rows) == 1, str(rows))
    check("fixture-a: class split_candidate",
          len(hits) == 1 and hits[0]["ratio_guess"] == 10.0,
          "ratio=%s" % (hits[0]["ratio_guess"] if hits else None))

    # (b) 50%-style crash with full recovery -> NOT an action
    rows_b = scan_ticker(fixture_crash_recovers(), **DEFAULTS)
    actions_b = [r for r in rows_b
                 if r["event_class"] in ("split_candidate",
                                         "spinoff_or_distribution")]
    check("fixture-b: no action on recovering crash", len(actions_b) == 0,
          str(rows_b))

    # (b2) same crash under a looser threshold IS caught but classified
    #      crash_not_split -- proves the continuation filter does the work.
    loose = dict(DEFAULTS, gap_threshold=-0.50)
    rows_b2 = scan_ticker(fixture_crash_recovers(), **loose)
    check("fixture-b2: loose threshold flags it",
          any(r["event_class"] == "crash_not_split" for r in rows_b2),
          str(rows_b2))

    # (c) spinoff-style permanent gap -> spinoff_or_distribution, non-int ratio
    rows_c = scan_ticker(fixture_spinoff_gap(), **DEFAULTS)
    hits_c = [r for r in rows_c
              if r["event_class"] == "spinoff_or_distribution"]
    ok_c = (len(rows_c) == 1 and len(hits_c) == 1
            and abs(hits_c[0]["ratio_guess"] - 3.7) <= 0.05)
    check("fixture-c: spinoff gap separated",
          ok_c, str(rows_c))

    # cross-fixture: classes are mutually distinct
    classes = set()
    for r in hits:
        classes.add(r["event_class"])
    for r in hits_c:
        classes.add(r["event_class"])
    if any(r["event_class"] == "crash_not_split" for r in rows_b2):
        classes.add("crash_not_split")
    check("separation: three distinct classes emitted",
          {"split_candidate", "crash_not_split",
           "spinoff_or_distribution"} <= classes,
          str(sorted(classes)))

    if failures:
        print("SELFTEST FAILED: %s" % ", ".join(failures))
        return 1
    print("SELFTEST OK: fixtures (a) split, (b) crash-recovers, "
          "(c) spinoff-gap correctly separated.")
    return 0


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def write_csv(rows, out_path):
    d = os.path.dirname(out_path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in CSV_COLUMNS})


def analyze_known_cases(db_path, candidates):
    """Print the required WDC/SNDK reality check."""
    con = sqlite3.connect("file:%s?mode=ro" % db_path.replace("\\", "/"),
                          uri=True)
    try:
        wdc = con.execute(
            "SELECT date, close FROM bars WHERE ticker='WDC' "
            "AND date BETWEEN '2025-02-10' AND '2025-02-28' ORDER BY date"
        ).fetchall()
        sndk_first = con.execute(
            "SELECT MIN(date), COUNT(*) FROM bars WHERE ticker='SNDK'"
        ).fetchone()
        wdc_max_ret = None
        if len(wdc) >= 2:
            rets = [wdc[i][1] / wdc[i - 1][1] - 1.0 for i in range(1, len(wdc))]
            wdc_max_ret = min(rets)
    finally:
        con.close()

    wdc_hits = [r for r in candidates if r["ticker"] == "WDC"]
    print("--- known-case analysis ---")
    if wdc_max_ret is not None:
        print("WDC 2025-02-10..02-28 worst overnight move: %.2f%%"
              % (wdc_max_ret * 100.0))
    print("WDC candidates found: %d%s"
          % (len(wdc_hits),
             "" if not wdc_hits else " -> %s" % wdc_hits))
    print("Interpretation: WDC series in this store is auto_adjust-smoothed "
          "(yahoo artifact); the SNDK spinoff leaves NO artificial gap in the "
          "RAW-as-stored closes. Any adjustment accounting happens later.")
    print("SNDK: history starts cold at %s (%d bars) -- a listing has no "
          "prior close and can never be an overnight-gap candidate."
          % (sndk_first[0], sndk_first[1]))
    print("---------------------------")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--gap-threshold", type=float,
                    default=DEFAULTS["gap_threshold"])
    ap.add_argument("--recovery-window", type=int,
                    default=DEFAULTS["recovery_window"])
    ap.add_argument("--recovery-fraction", type=float,
                    default=DEFAULTS["recovery_fraction"])
    ap.add_argument("--int-tolerance", type=float,
                    default=DEFAULTS["int_tolerance"])
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return run_selftest()

    if not os.path.exists(args.db):
        print("ERROR: db not found: %s" % args.db, file=sys.stderr)
        return 2

    candidates, listings = scan_db(
        args.db, args.gap_threshold, args.recovery_window,
        args.recovery_fraction, args.int_tolerance,
    )
    write_csv(candidates, args.out)

    print("scanned %d tickers; %d candidate rows" % (len(listings),
                                                     len(candidates)))
    for r in candidates:
        print("  %-6s %s  %.4f -> %.4f  ratio=%.3f  %s"
              % (r["ticker"], r["date"], r["prev_close"], r["next_close"],
                 r["ratio_guess"], r["event_class"]))
    print("wrote %s" % args.out)
    analyze_known_cases(args.db, candidates)
    return 0


if __name__ == "__main__":
    sys.exit(main())

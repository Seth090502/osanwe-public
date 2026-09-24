#!/usr/bin/env python
"""run_dual_analysis.py -- D-R3 fixtures + discrepancy detection report.

Loads F1-F5 corporate-action fixtures, runs the discrepancy detector over
the ingested dual-price store, applies quarantine, and writes
dual-price-report.md (ASCII) to fis-data. Read-only wrt factors.db.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dual_price_store as dps  # noqa: E402


def main():
    interp = dps.detect_interpreter()
    print("interpreter:", interp or sys.executable)
    con = dps.connect()

    # fresh detector state each run
    con.execute("DELETE FROM discrepancies")
    con.execute("DELETE FROM quarantine")
    con.execute("DELETE FROM corporate_actions")
    con.commit()

    # ---- fixtures ------------------------------------------------------
    desc = dps.load_fixtures(con)
    print("fixtures loaded:")
    for d in desc:
        print("  [%s] %-9s %-16s eff=%s" % (d["label"], d["type"],
                                            d["fixture"], d["effective"]))

    # ---- detector over the whole store ---------------------------------
    tickers = sorted(r[0] for r in con.execute(
        "SELECT DISTINCT ticker FROM dual_bars"))
    stats = dps.detect_discrepancies(con, tickers=tickers)
    print("detector:", json.dumps(stats))
    quarantined = con.execute(
        "SELECT ticker, reason FROM quarantine ORDER BY ticker").fetchall()

    # ---- per-fixture reconciliation check -------------------------------
    checks = []
    for tk, et, eff in con.execute(
            "SELECT DISTINCT ticker, event_type, effective_date "
            "FROM corporate_actions WHERE label='REAL' AND event_type IN "
            "('split','spinoff','merger_delisting','special_dividend',"
            "'symbol_change') "
            "ORDER BY ticker, effective_date"):
        row = con.execute(
            "SELECT date FROM dual_bars WHERE ticker=? AND date>=? "
            "ORDER BY date LIMIT 1", (tk, eff)).fetchone()
        if row:
            d = row[0]
            fr = con.execute(
                "SELECT raw_close, adjusted_close FROM dual_bars "
                "WHERE ticker=? AND date=?", (tk, d)).fetchone()
            if not fr or fr[0] is None or fr[1] in (None, 0):
                continue
            f = float(fr[0]) / float(fr[1])
            checks.append({"ticker": tk, "event": et, "effective": eff,
                           "first_bar_on_or_after": d,
                           "implied_factor": round(f, 6)})

    n_rows = con.execute("SELECT COUNT(*), COUNT(DISTINCT ticker) "
                         "FROM dual_bars").fetchone()
    n_disc = con.execute(
        "SELECT severity, COUNT(*) FROM discrepancies "
        "GROUP BY severity").fetchall()
    disc_by_sev = {s: c for s, c in n_disc}
    con.close()

    lines = []
    a = lines.append
    a("# D-R3 dual price store -- ingestion & discrepancy report")
    a("")
    a("- store: Efforts/osanwe-v2-overhaul/_work/fis-data/dual_prices.db")
    a("- bars: %d rows across %d tickers" % tuple(n_rows))
    a("- detector checked %d tickers; mismatched steps: %d "
      "(by severity: %s); quarantined instruments: %d"
      % (stats["checked"], stats["mismatches"],
         json.dumps(disc_by_sev), len(quarantined)))
    a("")
    a("## Fixtures")
    a("")
    a("| fixture | type | label | effective | note |")
    a("|---|---|---|---|---|")
    for d in desc:
        a("| %s | %s | %s | %s | %s |"
          % (d["fixture"], d["type"], d["label"], d["effective"],
             "see corporate_actions.notes"))
    a("")
    a("## REAL fixture reconciliation (raw/adj factor present at event)")
    a("")
    a("| ticker | event | effective | first bar >= eff | implied factor |")
    a("|---|---|---|---|---|")
    for c in checks:
        a("| %s | %s | %s | %s | %.6f |"
          % (c["ticker"], c["event"], c["effective"],
             c["first_bar_on_or_after"], c["implied_factor"]))
    a("")
    a("## Quarantine ledger")
    a("")
    if quarantined:
        for t, r in quarantined:
            a("- **%s**: %s" % (t, r))
    else:
        a("- none -- all reconcilable histories remain signal-eligible")
    a("")
    out = os.path.join(dps.FIS_DATA, "dual-price-report.md")
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print("report ->", out)


if __name__ == "__main__":
    main()

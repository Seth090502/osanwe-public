#!/usr/bin/env python
"""run_dual_ingest.py -- D-R3 ingestion driver for ALL 125 tickers.

Rate-limited (1.2s between Yahoo requests), resumable via checkpoint state
(dual-ingest-state.json). Re-execs under /path/to/python/python.exe if the
running interpreter lacks yfinance. Writes dual_prices.db in fis-data.
ASCII only, no git. Touches only tools/pit/ + _work/fis-data/.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dual_price_store as dps  # noqa: E402


def main():
    tks = dps.universe_tickers()
    print("universe: %d tickers" % len(tks))
    summary = dps.ingest_all(tickers=tks)
    print("state summary:", json.dumps(summary))

    con = dps.connect()
    n_rows = con.execute("SELECT COUNT(*), COUNT(DISTINCT ticker) "
                         "FROM dual_bars").fetchone()
    missing = [t for t in tks if not con.execute(
        "SELECT 1 FROM dual_bars WHERE ticker=? LIMIT 1", (t,)).fetchone()]
    con.close()
    print("dual_bars rows/tickers:", tuple(n_rows))
    print("tickers without bars (%d): %s" % (len(missing), ", ".join(missing)))


if __name__ == "__main__":
    main()

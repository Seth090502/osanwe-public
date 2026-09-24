#!/usr/bin/env python3
"""factor-store.py -- point-in-time market/factor store (roadmap P2).

One sqlite database keyed for ZERO-LOOKAHEAD queries:
  bars    (ticker, date, close)                 -- OHLC closes, one row/day
  factors (ticker, date, factor, value, src)    -- regime/factor observations

Design contracts:
- KNOWN_AS_OF: every query takes an as_of date and only returns rows with
  date <= as_of. Lookahead-proof by construction.
- OFFLINE: once ingested, grading/reporting never touches the network
  (verification bar for P2).
- PROVENANCE: src column records where each number came from
  (yfinance / fred-mcp-snapshot / manual), surfaced in every export.

CLI:
  --init                          create schema (idempotent)
  --ingest-bars TICKER,TICKER2    fetch daily closes via toolchain python
  --import-factors FILE.json      import {ticker,date,factor,value,src} rows
  --query-bars T --as-of D [--days N]
  --stats                         row counts per ticker/factor
  --db PATH                       default Efforts/osanwe-v2-overhaul/_work/factors.db
"""

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / "Efforts/osanwe-v2-overhaul/_work/factors.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS bars (
  ticker TEXT NOT NULL,
  date   TEXT NOT NULL,
  close  REAL NOT NULL,
  src    TEXT NOT NULL DEFAULT 'yfinance',
  PRIMARY KEY (ticker, date)
);
CREATE TABLE IF NOT EXISTS factors (
  ticker TEXT NOT NULL,
  date   TEXT NOT NULL,
  factor TEXT NOT NULL,
  value  REAL,
  text_value TEXT,
  src    TEXT NOT NULL,
  PRIMARY KEY (ticker, date, factor)
);
CREATE INDEX IF NOT EXISTS idx_factors_name ON factors(factor, date);
"""


def connect(db):
    db = Path(db)
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db))
    con.executescript(SCHEMA)
    return con


def toolchain_python():
    """An interpreter with yfinance (repo toolchain first)."""
    for cand in (r"/path/to/python\python.exe", sys.executable):
        try:
            subprocess.run([cand, "-c", "import yfinance"], check=True,
                           capture_output=True)
            return cand
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
    return None


def ingest_bars(tickers, db, lookback_days=400):
    """Fetch daily closes for tickers via the toolchain interpreter."""
    py = toolchain_python()
    if not py:
        print("no interpreter with yfinance")
        return 2
    payload = {"tickers": tickers, "period_days": lookback_days}
    prog = (
        "import json, sys, yfinance as yf\n"
        "payload = json.loads(sys.stdin.read())\n"
        "out = {}\n"
        "for t in payload['tickers']:\n"
        "    h = yf.Ticker(t).history(period=f\"{payload['period_days']}d\", auto_adjust=True)\n"
        "    out[t] = [[str(i.date()), float(c)] for i, c in h['Close'].items()]\n"
        "print(json.dumps(out))\n"
    )
    r = subprocess.run([py, "-c", prog], input=json.dumps(payload),
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("fetch failed:", (r.stderr or "").strip().splitlines()[-1][:160])
        return 2
    data = json.loads(r.stdout.strip().splitlines()[-1])
    con = connect(db)
    cur = con.cursor()
    inserted = 0
    for t, rows in data.items():
        cur.executemany(
            "INSERT OR REPLACE INTO bars(ticker,date,close,src) VALUES(?,?,?,'yfinance')",
            [(t, d, c) for d, c in rows])
        inserted += len(rows)
    con.commit()
    con.close()
    print(f"ingested {inserted} bar rows for {len(data)} ticker(s)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--ingest-bars")
    ap.add_argument("--import-factors")
    ap.add_argument("--query-bars")
    ap.add_argument("--as-of")
    ap.add_argument("--days", type=int, default=130)
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    args = ap.parse_args()

    if args.init:
        connect(args.db)
        print("schema ready:", args.db)
        return 0
    if args.stats:
        con = sqlite3.connect(args.db)
        for row in con.execute("SELECT ticker, COUNT(*), MIN(date), MAX(date) FROM bars GROUP BY ticker"):
            print(f"bars {row[0]}: {row[1]} rows [{row[2]}..{row[3]}]")
        for row in con.execute("SELECT factor, COUNT(*), MIN(date), MAX(date) FROM factors GROUP BY factor"):
            print(f"factor {row[0]}: {row[1]} rows [{row[2]}..{row[3]}]")
        con.close()
        return 0
    if args.ingest_bars:
        tickers = [t.strip().upper() for t in args.ingest_bars.split(",") if t.strip()]
        return ingest_bars(tickers, args.db)
    if args.query_bars:
        con = sqlite3.connect(args.db)
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT date, close FROM bars WHERE ticker=? AND date<=? "
            "ORDER BY date DESC LIMIT ?", (args.query_bars.upper(), args.as_of, args.days)
        ).fetchall()
        con.close()
        print(json.dumps([[r["date"], r["close"]] for r in rows]))
        return 0
    if args.import_factors:
        rows = json.loads(Path(args.import_factors).read_text(encoding="utf-8"))
        con = connect(args.db)
        con.executemany(
            "INSERT OR REPLACE INTO factors(ticker,date,factor,value,text_value,src) "
            "VALUES(?,?,?,?,?,?)",
            [(r["ticker"], r["date"], r["factor"], r.get("value"),
              r.get("text_value"), r.get("src", "manual")) for r in rows])
        con.commit()
        con.close()
        print(f"imported {len(rows)} factor rows")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

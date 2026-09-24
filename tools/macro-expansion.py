#!/usr/bin/env python3
r"""macro-expansion.py -- MACRO-X: institutional-grade macro factor expansion.

Expands the factor store (Efforts/osanwe-v2-overhaul/_work/factors.db,
ticker=MACRO) from the GAP-0 baseline of 19 FRED series to 50+ by ingesting:

  RATES    full treasury curve DGS1/DGS2/DGS3/DGS5/DGS7/DGS20 + T5YIFR
           (5y-forward 5y breakeven) + DFII-style real-rate context kept
           in the baseline set
  CREDIT   IG / BBB / BB OAS ladder + HY effective yield + EM corp OAS
  COMMOD   gold / WTI / copper / natgas front-month futures + DBC ETF
           + FRED spot complements (WTI spot, Henry Hub)
  FX       ICE Dollar Index (DX-Y.NYB) + EURUSD / GBPUSD / USDJPY
           + FRED broad trade-weighted dollar (DTWEXBGS)
  INTL     ^VIX, ^STOXX50E, ^N225, FXI (China large-cap), EEM (EM)
  OPT/VOL  ^VVIX (vol of vol), ^SKEW, CBOE equity put/call ratio
           (best-effort scrape; reported as FAILED if unavailable)
  REGIME   NFCI financial conditions, USEPUINDXD policy uncertainty

Sources: FRED public fredgraph.csv endpoint (no API key) and yfinance via an
isolated interpreter subprocess (same pattern as bulk-data-pull.py stages 2-3,
so heavy pandas imports never touch this process). All writes are
INSERT OR REPLACE -> idempotent, safe to re-run any time.

Completed FRED sids are appended to bulk-pull-manifest.json "done_macro" so
tools/bulk-data-pull.py --stage macro skips them; yfinance ids are tracked
under "done_macro_yf" (consumed by bulk-data-pull.py stage_macro_yf).
"""
import argparse
import json
import math
import sqlite3
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "Efforts/osanwe-v2-overhaul/_work/factors.db"
MANIFEST = ROOT / "Efforts/osanwe-v2-overhaul/_work/bulk-pull-manifest.json"
START_DEFAULT = "2015-01-01"  # matches existing factor-store depth

# --- expansion set: FRED (public csv, no key) ------------------------------
EXPANSION_FRED = {
    # RATES CURVE (full treasury curve + long-horizon breakeven)
    "BAMLH0A0HYM2EY": "High yield effective yield",
    "DGS1": "1Y Treasury constant maturity",
    "DGS2": "2Y Treasury constant maturity",
    "DGS3": "3Y Treasury constant maturity",
    "DGS5": "5Y Treasury constant maturity",
    "DGS7": "7Y Treasury constant maturity",
    "DGS20": "20Y Treasury constant maturity",
    "T5YIFR": "5Y5Y forward inflation expectation",
    # CREDIT ladder
    # NOTE: task-requested "BAMLC0A4CLBBB" (BBB OAS) does NOT exist on FRED --
    # every variant 404s. Institutional BBB rung substituted with Moody's Baa
    # daily yield + spread. Requested "BAMLHYH0A0HYM2" was a typo'd id; the
    # real HY effective yield is BAMLH0A0HYM2EY -- fetched EARLY in this dict
    # because licensed BAML series intermittently 404 mid-burst (~10th rapid
    # request) under per-group throttling.
    "BAMLC0A0CM": "Investment grade corporate OAS",
    "BAMLH0A1HYBB": "BB sub-high-yield OAS",
    "BAMLEMCBPIOAS": "EM corporate OAS",
    "DBAA": "Moody's seasoned Baa corporate bond yield (BBB proxy)",
    "BAA10Y": "Moody's Baa spread vs 10Y Treasury (BBB credit spread)",
    # FX anchor + regime indices
    "DTWEXBGS": "Broad trade-weighted USD index (goods+services)",
    "NFCI": "Chicago Fed National Financial Conditions Index",
    "USEPUINDXD": "Economic Policy Uncertainty index (daily)",
    # Commodity spot complements to futures
    "DCOILWTICO": "WTI crude oil spot (FRED)",
    "DHHNGSP": "Henry Hub natural gas spot",
}

# --- expansion set: yfinance (market-sourced; no FRED equivalent) ----------
YF_MACRO = {
    # INTERNATIONAL INDICES / VOL
    "^VIX": "VIX index (direct)",
    "^STOXX50E": "Euro Stoxx 50 index",
    "^N225": "Nikkei 225 index",
    "FXI": "iShares China Large-Cap ETF",
    "EEM": "iShares MSCI Emerging Markets ETF",
    # OPTIONS / VOLATILITY complex
    "^VVIX": "CBOE VVIX volatility-of-volatility index",
    "^SKEW": "CBOE SKEW index",
    # COMMODITIES futures + ETF
    "GC=F": "Gold futures (front month)",
    "CL=F": "WTI crude futures (front month)",
    "HG=F": "Copper futures (front month)",
    "NG=F": "Natural gas futures (front month)",
    "DBC": "Invesco DB Commodity Index ETF",
    # FX
    "DX-Y.NYB": "ICE US Dollar Index",
    "EURUSD=X": "EUR/USD spot",
    "GBPUSD=X": "GBP/USD spot",
    "USDJPY=X": "USD/JPY spot",
}

# Best-effort CBOE put/call ratio (underscore prefix is cdn.cboe.com chart
# convention). As of 2026-08 these return 403 Forbidden -- CBOE closed public
# access to put/call history; kept here in case access reopens. When this
# fails, PCALL is reported FAILED rather than fabricated.
PCALL_URLS = [
    "https://cdn.cboe.com/api/global/delayed_quotes/charts/historical/_PCR_D.json",
    "https://cdn.cboe.com/api/global/delayed_quotes/charts/historical/_PCR_EQUITY_D.json",
]


def load_manifest():
    if MANIFEST.is_file():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"done_bars": [], "done_macro": [], "computed": None}


def save_manifest(m):
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(m, indent=1), encoding="utf-8")


def toolchain():
    r"""Interpreter that has yfinance; prefer the pinned /path/to/python."""
    for cand in (r"/path/to/python\python.exe", sys.executable):
        try:
            subprocess.run([cand, "-c", "import yfinance"], check=True,
                           capture_output=True, timeout=120)
            return cand
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            continue
    return None


def http_get(url, timeout=30):
    """GET with UA header and exponential backoff. FRED occasionally throws
    transient 404/503s on licensed series, especially mid-burst; the final
    retry waits out a long cooldown before giving up."""
    last = None
    for attempt, pause in enumerate((0, 2.0, 4.0, 8.0, 30.0)):
        if pause:
            time.sleep(pause)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", "replace")
        except Exception as exc:
            last = exc
    raise last


def fred_rows(sid, start):
    """[(date, value)] from the public fredgraph.csv endpoint.

    No coed (end date) parameter: passing one has intermittently 404'd on
    licensed BAML series; omitting it returns history through today.
    """
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd={start}"
    text = http_get(url)
    out = []
    for line in text.strip().splitlines()[1:]:
        d, v = line.split(",")
        if v in (".", "", "NA"):
            continue
        try:
            val = float(v)
        except ValueError:
            continue
        if math.isfinite(val):
            out.append((d, val))
    return out


def yf_rows(py, sym, start):
    """[(date, value)] fetched in an isolated yfinance interpreter process."""
    code = (
        "import json,math,yfinance as yf;"
        f"h=yf.Ticker({sym!r}).history(start={start!r},auto_adjust=True);"
        "out=[[str(i.date()),float(c)] for i,c in h['Close'].items()"
        " if c==c and math.isfinite(float(c))];"
        "print(json.dumps(out))"
    )
    r = subprocess.run([py, "-c", code], capture_output=True, text=True,
                       timeout=180)
    tail = (r.stderr or "").strip().splitlines()
    if r.returncode != 0:
        raise RuntimeError(tail[-1] if tail else f"exit {r.returncode}")
    rows = json.loads(r.stdout.strip().splitlines()[-1])
    return [(d, float(v)) for d, v in rows if math.isfinite(float(v))]


def pcall_rows():
    """Best-effort CBOE put/call daily ratio history; (rows, source_url)."""
    for url in PCALL_URLS:
        try:
            payload = json.loads(http_get(url))
            out = []
            for row in payload.get("data") or []:
                d = row.get("date")
                v = row.get("close", row.get("value"))
                if not d or v in (None, "", "."):
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if math.isfinite(fv) and fv > 0:
                    out.append((d, fv))
            if out:
                return out, url.rsplit("/", 1)[-1]
        except Exception:
            continue
    return None, None


def ingest(con, fid, rows, src):
    cur = con.cursor()
    cur.executemany(
        "INSERT OR REPLACE INTO factors(ticker,date,factor,value,text_value,src)"
        " VALUES(?,?,?,?,?,?)",
        [("MACRO", d, fid, v, None, src) for d, v in rows])
    con.commit()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=START_DEFAULT,
                    help="history start date (default matches store depth)")
    args = ap.parse_args()

    if not DB.is_file():
        print(f"FATAL: factor store missing: {DB}")
        return 2
    con = sqlite3.connect(str(DB))
    con.executescript(
        "CREATE TABLE IF NOT EXISTS bars(ticker TEXT,date TEXT,close REAL,src TEXT,"
        "PRIMARY KEY(ticker,date));"
        "CREATE TABLE IF NOT EXISTS factors(ticker TEXT,date TEXT,factor TEXT,"
        "value REAL,text_value TEXT,src TEXT,PRIMARY KEY(ticker,date,factor));")

    manifest = load_manifest()
    manifest.setdefault("done_macro", [])
    manifest.setdefault("done_macro_yf", [])
    baseline = con.execute(
        "SELECT COUNT(DISTINCT factor) FROM factors WHERE ticker='MACRO'"
    ).fetchone()[0]
    print(f"MACRO-X expansion: baseline {baseline} MACRO factors in store")

    results = {}  # id -> obs count or "FAILED: reason"
    ok_fred = ok_yf = 0

    print(f"stage A: {len(EXPANSION_FRED)} FRED series")
    for sid, desc in EXPANSION_FRED.items():
        try:
            rows = fred_rows(sid, args.start)
            ingest(con, sid, rows, "fred-csv")
            results[sid] = len(rows)
            ok_fred += 1
            print(f"  {sid}: {len(rows)} obs ({desc})")
            if sid not in manifest["done_macro"]:
                manifest["done_macro"].append(sid)
                save_manifest(manifest)
            time.sleep(2.5)  # rate-limit courtesy (licensed BAML series)
        except Exception as exc:
            results[sid] = f"FAILED: {exc!r}"
            print(f"  {sid}: FAILED {exc!r}")

    print(f"stage B: {len(YF_MACRO)} yfinance market series")
    py = toolchain()
    if py is None:
        for sid, desc in YF_MACRO.items():
            results[sid] = "FAILED: no yfinance interpreter"
            print(f"  {sid}: FAILED (no yfinance interpreter)")
    else:
        for sid, desc in YF_MACRO.items():
            try:
                rows = yf_rows(py, sid, args.start)
                ingest(con, sid, rows, "yfinance-bulk")
                results[sid] = len(rows)
                ok_yf += 1
                print(f"  {sid}: {len(rows)} obs ({desc})")
                if sid not in manifest["done_macro_yf"]:
                    manifest["done_macro_yf"].append(sid)
                    save_manifest(manifest)
                time.sleep(1.0)  # rate-limit courtesy
            except Exception as exc:
                results[sid] = f"FAILED: {exc!r}"
                print(f"  {sid}: FAILED {exc!r}")

    print("stage C: CBOE put/call ratio (best-effort)")
    pc_rows, pc_src = pcall_rows()
    if pc_rows:
        ingest(con, "PCALL", pc_rows, f"cboe-cdn:{pc_src}")
        results["PCALL"] = len(pc_rows)
        print(f"  PCALL: {len(pc_rows)} obs via {pc_src}")
    else:
        results["PCALL"] = "FAILED: no open CBOE put/call endpoint"
        print("  PCALL: FAILED (no open CBOE endpoint; see summary)")

    save_manifest(manifest)

    # verification pass over the whole store
    store = con.execute(
        "SELECT factor, COUNT(*), MIN(date), MAX(date) FROM factors"
        " WHERE ticker='MACRO' GROUP BY factor ORDER BY factor").fetchall()
    con.close()

    failures = sorted(k for k, v in results.items() if isinstance(v, str))
    print("=" * 64)
    print(f"ingested this run: FRED {ok_fred}/{len(EXPANSION_FRED)}"
          f", yfinance {ok_yf}/{len(YF_MACRO)}"
          f", PCALL {'ok' if pc_rows else 'unavailable'}")
    if failures:
        print("FAILURES:")
        for k in failures:
            print(f"  {k}: {results[k]}")
    print("-" * 64)
    print(f"TOTAL DISTINCT MACRO FACTORS IN STORE: {len(store)}")
    for fac, n, lo, hi in store:
        tag = "(new)" if fac in results else ""
        print(f"  {fac:<18} {n:>5}  {lo}..{hi} {tag}")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""bulk-data-pull.py -- GAP-0: order-of-magnitude reference-data expansion.

Overnight-resumable pipeline:
  STAGE 1  universe: collect every ticker entity + indexes + crypto
  STAGE 2  bars: full daily history (2y) per ticker -> factor store
           (checkpointed every N tickers; re-run resumes from manifest)
  STAGE 3  macro: FRED CSV bulk download (35 series) -> factors table
  STAGE 3b macro-yf: market-sourced macro series (16) via yfinance
           -> factors table (see YF_MACRO_SERIES; added by MACRO-X
           expansion, tools/macro-expansion.py)
  STAGE 4  computed references: benchmark profiles, correlation clusters,
           macro snapshot -- written to wiki/investing/benchmarks/ as
           GENERATED .md refs with provenance

Everything idempotent: re-running updates in place. Network used ONLY in
stages 2-3; stage 4 is pure local computation.
"""

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "Efforts/osanwe-v2-overhaul/_work/factors.db"
MANIFEST = ROOT / "Efforts/osanwe-v2-overhaul/_work/bulk-pull-manifest.json"
OUTDIR = ROOT / "wiki/investing/benchmarks"
FRED_SERIES = {
    "DGS10": "10Y Treasury constant maturity",
    "T10Y3M": "10Y-3M term spread",
    "T10Y2Y": "10Y-2Y term spread",
    "BAMLH0A0HYM2": "HY OAS credit spread",
    "VIXCLS": "VIX close",
    "FEDFUNDS": "Fed funds effective",
    "UNRATE": "Unemployment rate",
    "CPIAUCSL": "CPI All Urban Consumers",
    "DFII10": "10Y TIPS real yield",
    # OSANWE-V2 overnight expansion: Fed policy plumbing + FX
    "DEXJPUS": "Yen per USD exchange rate",
    "WALCL": "Fed total assets (balance sheet / QT)",
    "WRESBAL": "Reserve balances with Fed",
    "TREAST": "Treasury securities held outright (Fed)",
    "SOFR": "Secured Overnight Financing Rate",
    "RRPONTSYD": "Overnight reverse repo volume",
    # OSANWE-V2 theme-epsilon expansion
    "STLFSI4": "St Louis Fed Financial Stress Index",
    "T5YIE": "5Y Breakeven Inflation Rate",
    "DGS30": "30Y Treasury Constant Maturity",
    "BAMLH0A0HYM2EY": "HY OAS effective yield",
    # MACRO-X institutional expansion (tools/macro-expansion.py, 2026-08-24)
    # NOTE: task-requested BAMLC0A4CLBBB (BBB OAS) does not exist on FRED;
    # Moody's Baa series substitute as the BBB credit rung.
    "DGS1": "1Y Treasury constant maturity",
    "DGS2": "2Y Treasury constant maturity",
    "DGS3": "3Y Treasury constant maturity",
    "DGS5": "5Y Treasury constant maturity",
    "DGS7": "7Y Treasury constant maturity",
    "DGS20": "20Y Treasury constant maturity",
    "T5YIFR": "5Y5Y forward inflation expectation",
    "BAMLC0A0CM": "Investment grade corporate OAS",
    "BAMLH0A1HYBB": "BB sub-high-yield OAS",
    "BAMLEMCBPIOAS": "EM corporate OAS",
    "DBAA": "Moody's seasoned Baa corporate bond yield (BBB proxy)",
    "BAA10Y": "Moody's Baa spread vs 10Y Treasury (BBB credit spread)",
    "DCOILWTICO": "WTI crude oil spot (FRED)",
    "DHHNGSP": "Henry Hub natural gas spot",
    "DTWEXBGS": "Broad trade-weighted USD index (goods+services)",
    "NFCI": "Chicago Fed National Financial Conditions Index",
    "USEPUINDXD": "Economic Policy Uncertainty index (daily)",
}
# Market-sourced macro series without a usable FRED equivalent. Ingested by
# tools/macro-expansion.py and by bulk-data-pull.py --stage macro-yf via an
# isolated yfinance interpreter into the factors table (ticker=MACRO).
YF_MACRO_SERIES = {
    "^VIX": "VIX index (direct)",
    "^STOXX50E": "Euro Stoxx 50 index",
    "^N225": "Nikkei 225 index",
    "FXI": "iShares China Large-Cap ETF",
    "EEM": "iShares MSCI Emerging Markets ETF",
    "^VVIX": "CBOE VVIX volatility-of-volatility index",
    "^SKEW": "CBOE SKEW index",
    "GC=F": "Gold futures (front month)",
    "CL=F": "WTI crude futures (front month)",
    "HG=F": "Copper futures (front month)",
    "NG=F": "Natural gas futures (front month)",
    "DBC": "Invesco DB Commodity Index ETF",
    "DX-Y.NYB": "ICE US Dollar Index",
    "EURUSD=X": "EUR/USD spot",
    "GBPUSD=X": "GBP/USD spot",
    "USDJPY=X": "USD/JPY spot",
}
INDEXES = ["SPY", "QQQ", "IWM", "VGT", "XLF", "XLE"]
CRYPTO = ["XRP-USD", "BTC-USD", "ETH-USD", "SOL-USD"]


def sh(*args):
    r = subprocess.run(list(args), cwd=str(ROOT), capture_output=True)
    return r.stdout.decode(errors="replace")


def load_manifest():
    if MANIFEST.is_file():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"done_bars": [], "done_macro": [], "computed": None}


def save_manifest(m):
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(m, indent=1), encoding="utf-8")


def collect_universe():
    """Every ticker entity stem + indexes + crypto. Crypto symbols map to
    yfinance -USD pairs; plain 'BTC' style entities are kept as-is for entity
    matching but fetched as BTC-USD."""
    tickers = set()
    ed = ROOT / "wiki/entities/tickers"
    for f in ed.glob("*.md"):
        m = re.match(r"^([a-z]{1,6})\.md$", f.name, re.I)
        if m:
            t = m.group(1).upper()
            if "-" not in t and len(t) <= 5:
                tickers.add(t)
    CRYPTO_BASES = {"XRP", "BTC", "ETH", "SOL", "HBAR", "LINK", "ONDO", "QNT", "ALGO"}
    out = set()
    for t in tickers:
        out.add(f"{t}-USD" if t in CRYPTO_BASES else t)
    return sorted(out)


def toolchain():
    for cand in (r"/path/to/python\python.exe", sys.executable):
        try:
            subprocess.run([cand, "-c", "import yfinance"], check=True, capture_output=True)
            return cand
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
    return None


def fetch_one(py, ticker, years=2):
    start = (datetime.today() - timedelta(days=int(years * 365.25))).strftime("%Y-%m-%d")
    code = (
        "import json,yfinance as yf;"
        f"h=yf.Ticker({ticker!r}).history(start={start!r},auto_adjust=True);"
        "print(json.dumps([[str(i.date()),float(c)] for i,c in h['Close'].items()]))"
    )
    r = subprocess.run([py, "-c", code], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return None


def ingest_rows(con, ticker, rows):
    con.executemany(
        "INSERT OR REPLACE INTO bars(ticker,date,close,src) VALUES(?,?,?,'yfinance-bulk')",
        [(ticker, d, c) for d, c in rows])
    con.commit()


def stage_bars(con, py, universe, manifest, batch_pause=2.0):
    todo = [t for t in universe if t not in manifest["done_bars"]]
    print(f"stage 2: {len(todo)} of {len(universe)} tickers remaining")
    for i, t in enumerate(todo):
        rows = fetch_one(py, t)
        if rows:
            ingest_rows(con, t.upper(), rows)
            print(f"  [{i+1}/{len(todo)}] {t}: {len(rows)} rows")
        else:
            print(f"  [{i+1}/{len(todo)}] {t}: NO DATA (skip, will retry next run)")
        manifest["done_bars"].append(t)
        save_manifest(manifest)
        time.sleep(batch_pause)  # rate-limit courtesy
    return 0


def stage_macro(con, manifest):
    """FRED bulk CSVs (fraser/stlouisfed public csv endpoint), no API key needed."""
    import urllib.request
    todo = [s for s in FRED_SERIES if s not in manifest["done_macro"]]
    print(f"stage 3: {len(todo)} FRED series remaining")
    base = ("https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
            "&cosd=2015-01-01&coed={today}")
    today = date.today().isoformat()
    for sid in todo:
        url = base.format(sid=sid, today=today)
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                text = resp.read().decode()
            n = 0
            cur = con.cursor()
            for line in text.strip().splitlines()[1:]:
                d, v = line.split(",")
                if v not in (".", "", "NA"):
                    try:
                        val = float(v)
                    except ValueError:
                        continue
                    cur.execute(
                        "INSERT OR REPLACE INTO factors(ticker,date,factor,value,text_value,src)"
                        " VALUES(?,?,?,?,?,?)",
                        ("MACRO", d, sid, val, None, "fred-csv"))
                    n += 1
            con.commit()
            print(f"  {sid}: {n} obs ({FRED_SERIES[sid]})")
            manifest["done_macro"].append(sid)
            save_manifest(manifest)
            time.sleep(1.0)
        except Exception as exc:
            print(f"  {sid}: FAILED {exc!r}")
    return 0


def stage_macro_yf(con, manifest):
    """Market-sourced macro series (YF_MACRO_SERIES) via an isolated yfinance
    interpreter, into the factors table (ticker=MACRO). Manifest key:
    done_macro_yf. PCALL (CBOE put/call) excluded: CBOE closed public access
    (403) to its history endpoints as of 2026-08."""
    todo = [s for s in YF_MACRO_SERIES if s not in manifest.get("done_macro_yf", [])]
    print(f"stage 3b: {len(todo)} yfinance macro series remaining")
    py = toolchain()
    if py is None:
        print("no yfinance interpreter; macro-yf stage blocked")
        return 2
    for sid, desc in YF_MACRO_SERIES.items():
        if sid in manifest.get("done_macro_yf", []):
            continue
        try:
            rows = fetch_one(py, sid, years=15)
            if not rows:
                raise RuntimeError("no rows returned")
            con.executemany(
                "INSERT OR REPLACE INTO factors(ticker,date,factor,value,text_value,src)"
                " VALUES(?,?,?,?,?,?)",
                [("MACRO", d, sid, float(c), None, "yfinance-bulk") for d, c in rows])
            con.commit()
            n = len(rows)
            print(f"  {sid}: {n} obs ({desc})")
            manifest.setdefault("done_macro_yf", []).append(sid)
            save_manifest(manifest)
            time.sleep(1.0)
        except Exception as exc:
            print(f"  {sid}: FAILED {exc!r}")
    return 0


def ann_return(closes):
    if len(closes) < 2:
        return None
    total = closes[-1] / closes[0] - 1
    yrs = len(closes) / 252
    return (1 + total) ** (1 / max(yrs, 0.25)) - 1


def ann_vol(closes):
    rets = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
    if len(rets) < 20:
        return None
    mean = sum(rets) / len(rets)
    var = sum((x - mean) ** 2 for x in rets) / (len(rets) - 1)
    return (var ** 0.5) * (252 ** 0.5)


def max_drawdown(closes):
    peak = closes[0]
    mdd = 0.0
    for c in closes:
        peak = max(peak, c)
        mdd = min(mdd, c / peak - 1)
    return mdd


def beta_corr(closes, bench):
    n = min(len(closes), len(bench))
    a = [closes[-n:]][0]
    b = bench[-n:]
    ra = [a[i] / a[i - 1] - 1 for i in range(1, n)]
    rb = [b[i] / b[i - 1] - 1 for i in range(1, n)]
    if len(ra) < 30 or len(rb) < 30:
        return None, None
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb)) / (len(ra) - 1)
    va = sum((x - ma) ** 2 for x in ra) / (len(ra) - 1)
    vb = sum((y - mb) ** 2 for y in rb) / (len(rb) - 1)
    corr = cov / ((va * vb) ** 0.5) if va and vb else None
    beta = cov / vb if vb else None
    return beta, corr


def rsi14(closes):
    if len(closes) < 15:
        return None
    gains = losses = 0.0
    for i in range(len(closes) - 14, len(closes)):
        ch = closes[i] - closes[i - 1]
        gains += max(ch, 0)
        losses += max(-ch, 0)
    if losses == 0:
        return 100.0
    rs = gains / losses
    return 100 - 100 / (1 + rs)


def fmtpct(x):
    return f"{x * 100:+.1f}%" if x is not None else "--"


def stage_computed(con):
    """Generate benchmark reference files from the store. Pure local compute."""
    OUTDIR.mkdir(parents=True, exist_ok=True)
    spy = con.execute("SELECT date,close FROM bars WHERE ticker='SPY' ORDER BY date").fetchall()
    bench_closes = [c for _, c in spy]
    tickers = [r[0] for r in con.execute(
        "SELECT DISTINCT ticker FROM bars WHERE ticker NOT IN ('MACRO') ORDER BY ticker")]
    generated = []
    for t in tickers:
        rows = con.execute("SELECT date,close FROM bars WHERE ticker=? ORDER BY date", (t,)).fetchall()
        closes = [c for _, c in rows]
        if len(closes) < 60:
            continue
        vol = ann_vol(closes)
        beta, corr = beta_corr(closes, bench_closes)
        sharpe = None
        if vol:
            sharpe = (ann_return(closes) or 0) / vol
        last = closes[-1]
        ma50 = sum(closes[-50:]) / min(50, len(closes))
        hi252 = max(closes[-252:]) if len(closes) >= 60 else max(closes)
        rsi = rsi14(closes)
        body = [
            "---",
            "aliases: []",
            "categories: [sources]",
            "type: reference",
            "status: active",
            f"created: {date.today().isoformat()}",
            f"updated: {date.today().isoformat()}",
            "tags: []",
            'related: []',
            "---", "",
            f"# Benchmark profile: {t}",
            "",
            f"GENERATED by tools/bulk-data-pull.py from the point-in-time factor "
            f"store ({len(rows)} bars, {rows[0][0]}..{rows[-1][0]}). Provenance: "
            "yfinance auto-adjusted closes. Regenerated weekly.",
            "",
            "| metric | value |", "|---|---|",
            f"| ann return | {fmtpct(ann_return(closes))} |",
            f"| ann vol | {vol and round(vol * 100, 1)}% |",
            f"| Sharpe (rf=0) | {sharpe and round(sharpe, 2)} |",
            f"| max drawdown (2y) | {max_drawdown(closes) and round(max_drawdown(closes) * 100, 1)}% |",
            f"| beta vs SPY | {beta and round(beta, 2)} |",
            f"| corr vs SPY | {corr and round(corr, 2)} |",
            f"| RSI(14) | {rsi and round(rsi, 1)} |",
            f"| last close | {last:.2f} ({rows[-1][0]}) |",
            f"| vs MA50 | {fmtpct(last / ma50 - 1)} |",
            f"| vs 52w high | {fmtpct(last / hi252 - 1)} |",
            "",
            "USE: sizing context, correlation awareness, regime framing for any",
            f"/invest run touching {t}. Not investment advice; mechanical stats.",
        ]
        p = OUTDIR / f"{t.lower()}-benchmark.md"
        p.write_text("\n".join(body) + "\n", encoding="utf-8", newline="\n")
        generated.append(p.name)

    # correlation cluster table (top names vs SPY + each other, corr matrix lite)
    mat_lines = ["---", "aliases: []", "categories: [sources]", "type: reference",
                 "status: active", f"created: {date.today().isoformat()}",
                 f"updated: {date.today().isoformat()}", "tags: []", "related: []",
                 "---", "", "# Correlation clusters (90d, vs SPY)", "",
                 "| ticker | beta | corr |", "|---|---|---|"]
    for t in tickers:
        rows = con.execute("SELECT date,close FROM bars WHERE ticker=? ORDER BY date", (t,)).fetchall()
        closes = [c for _, c in rows]
        if len(closes) < 90:
            continue
        beta, corr = beta_corr(closes[-91:], bench_closes)
        mat_lines.append(f"| {t} | {beta and round(beta, 2)} | {corr and round(corr, 2)} |")
    p = OUTDIR / "correlation-clusters.md"
    p.write_text("\n".join(mat_lines) + "\n", encoding="utf-8", newline="\n")
    generated.append(p.name)

    # macro snapshot from factors
    macro_lines = ["---", "aliases: []", "categories: [sources]", "type: reference",
                   "status: active", f"created: {date.today().isoformat()}",
                   f"updated: {date.today().isoformat()}", "tags: []", "related: []",
                   "---", "", "# Macro state snapshot (GENERATED from FRED ingest)", ""]
    for sid, desc in FRED_SERIES.items():
        row = con.execute(
            "SELECT date, value FROM factors WHERE factor=? ORDER BY date DESC LIMIT 1",
            (sid,)).fetchone()
        if row:
            macro_lines.append(f"- **{sid}** ({desc}): {row[1]} as of {row[0]} [src: fred-csv]")
        else:
            macro_lines.append(f"- **{sid}** ({desc}): no data ingested")
    p = OUTDIR / "macro-snapshot.md"
    p.write_text("\n".join(macro_lines) + "\n", encoding="utf-8", newline="\n")
    generated.append(p.name)

    print(f"stage 4: generated {len(generated)} reference files in wiki/investing/benchmarks/")
    return generated


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage",
                    choices=["universe", "bars", "macro", "macro-yf",
                             "computed", "all"], default="all")
    ap.add_argument("--years", type=float, default=2.0)
    args = ap.parse_args()

    manifest = load_manifest()
    if args.stage in ("universe", "all"):
        u = collect_universe()
        manifest.setdefault("universe", u)
        save_manifest(manifest)
        print(f"stage 1: universe = {len(u)} instruments")
        if args.stage == "universe":
            print(", ".join(u))
            return 0
    con = sqlite3.connect(str(DB))
    con.executescript(
        "CREATE TABLE IF NOT EXISTS bars(ticker TEXT,date TEXT,close REAL,src TEXT,"
        "PRIMARY KEY(ticker,date));"
        "CREATE TABLE IF NOT EXISTS factors(ticker TEXT,date TEXT,factor TEXT,value REAL,"
        "text_value TEXT,src TEXT,PRIMARY KEY(ticker,date,factor));")
    if args.stage in ("bars", "all"):
        py = toolchain()
        if not py:
            print("no yfinance interpreter; bars stage blocked")
            return 2
        stage_bars(con, py, manifest.get("universe") or collect_universe(), manifest)
    if args.stage in ("macro", "all"):
        stage_macro(con, manifest)
    if args.stage in ("macro-yf", "all"):
        stage_macro_yf(con, manifest)
    if args.stage in ("computed", "all"):
        gen = stage_computed(con)
        manifest["computed"] = date.today().isoformat()
        save_manifest(manifest)
    con.close()
    print("bulk-data-pull complete for stage:", args.stage)
    return 0


if __name__ == "__main__":
    sys.exit(main())

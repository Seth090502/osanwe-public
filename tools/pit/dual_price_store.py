#!/usr/bin/env python
"""dual_price_store.py -- D-R3 raw-versus-adjusted price architecture (PIT).

Problem: the current bars table stores ONLY auto-adjusted closes. Corporate
actions (splits, spinoffs, special distributions, symbol changes, merger
delistings) therefore leave no trace in the price series, and an unhandled
action can fabricate artificial mean-reversion signals (see
wdc_sndk_stitch.py / D10).

This module provides:

  1. SCHEMA -- a dual-price SQLite store holding BOTH raw and adjusted
     closes per (ticker, date) plus explicit corporate-action fields:
       ticker, date, raw_close, adjusted_close, split_factor, dividend,
       special_distribution_flag, spinoff_relationship, effective_date,
       announcement_date_when_available, source, confidence,
       adjustment_methodology
     plus corporate_actions / discrepancies / quarantine tables.

  2. INGESTION ADAPTER -- fetches raw+adjusted pairs from yfinance
     (history(auto_adjust=False), which also carries per-ex-date Dividends
     and Stock Splits columns) for ALL tickers found in factors.db.bars.
     Rate-limited (sleep between requests) and resumable via a checkpoint
     state file. Interpreter detection: prefers /path/to/python/python.exe
     (yfinance installed there); falls back to the running interpreter.

  3. DISCREPANCY DETECTOR -- the implied back-adjustment factor is
     f_t = raw_close_t / adjusted_close_t. Every corporate action ex-date
     makes f step (log-space); quiet days leave it flat. The detector
     compares OBSERVED daily log-steps of f against EXPECTED steps implied
     by recorded events (splits multiply f; dividends scale f by
     approximately (1 - div / prev_raw)). Unexplained steps are logged as
     discrepancies; instruments whose raw history cannot be reconciled are
     QUARANTINED (quarantined_from_signal_use = 1) with a reason.

  4. FIXTURES -- regression fixtures, clearly labeled REAL or SYNTHETIC:
       F1 WDC/SNDK spinoff          REAL (ratio UNVERIFIED)
       F2 10:1 split                REAL (NVDA 2024-06-10, AVGO 2024-07-15)
       F3 merger-delisted name      SYNTHETIC (TWTR-SYN; yfinance serves
                                    no bars for truly delisted tickers)
       F4 special dividend          SYNTHETIC (SPEC-SYN; no free in-universe
                                    special-dividend case identified)
       F5 symbol change             REAL (META, FB -> META 2022-06-09)

EXTERNAL BLOCKAGE NOTES (field-level):
  * announcement_date_when_available -- yfinance exposes ex-date, record
    date and pay date for dividends but NOT board-declaration/announcement
    dates. Field remains nullable and is populated only when a source
    provides it. Acquisition comparison for announcement dates:
      - exchange press releases (NYSE/Nasdaq + issuer IR): free but
        unstructured, per-issuer scraping, uneven coverage pre-2015;
      - S&P Capital IQ / Refinitiv corporate actions feeds: commercial
        license (order of $10k+/yr), full coverage incl. announcements;
      - Nasdaq GIDS corporate actions file: licensed redistribution.
    Verdict: EXTERNALLY BLOCKED for free full coverage; schema keeps the
    slot so upstream fills never require a migration.
  * Spinoff distribution ratios (e.g. WDC->SNDK 1-for-N): not carried in
    yfinance metadata; current values flagged UNVERIFIED. Same acquisition
    trade-off as above (free issuer 8-K text vs licensed structured feed).

Constraints honored: writes confined to tools/pit/ and
Efforts/osanwe-v2-overhaul/_work/fis-data/. ASCII only. No git.
Network used ONLY by the ingestion adapter (sanctioned toolchain).
"""

from __future__ import annotations

import json
import math
import os
import sqlite3
import subprocess
import sys
import time

VAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(VAULT, "Efforts", "osanwe-v2-overhaul", "_work")
FIS_DATA = os.path.join(WORK, "fis-data")
FACTOR_DB = os.path.join(WORK, "factors.db")
DB_PATH = os.path.join(FIS_DATA, "dual_prices.db")
STATE_PATH = os.path.join(FIS_DATA, "dual-ingest-state.json")

SOURCE_YF = "yfinance"
METHODOLOGY = ("yfinance_backadjust_v1(auto_adjust=False); raw_close "
               "reconstructed to TRUE TRADED price by undoing later "
               "splits (Yahoo Close is split-adjusted)")
CONF_HIGH, CONF_MED, CONF_LOW = "HIGH", "MEDIUM", "LOW"

# Detector tolerances (log-space)
QUIET_TOL = math.log(1.002)       # quiet-day step must be ~flat
EVENT_TOL = math.log(1.05)        # unexplained residual tolerated at events
QUARANTINE_TOL = math.log(1.05)   # unexplained step >= ~5% quarantines

INGEST_START = "2015-01-01"       # bounds fetch depth; covers NVDA/AVGO splits


# ----------------------------------------------------------------------
# interpreter detection
# ----------------------------------------------------------------------

def detect_interpreter():
    """Return path to a python that can import yfinance, else None."""
    candidates = []
    py314 = r"/path/to/python\python.exe"
    if os.path.exists(py314):
        candidates.append(py314)
    candidates.append(sys.executable)
    for exe in candidates:
        try:
            rc = subprocess.call(
                [exe, "-c", "import yfinance, pandas"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=60)
            if rc == 0:
                return exe
        except Exception:
            continue
    return None


# ----------------------------------------------------------------------
# store
# ----------------------------------------------------------------------

def connect(db_path=DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    con = sqlite3.connect(db_path.replace("\\", "/"))
    _create_schema(con)
    return con


def _create_schema(con):
    con.executescript("""
CREATE TABLE IF NOT EXISTS dual_bars (
  ticker            TEXT NOT NULL,
  date              TEXT NOT NULL,
  raw_close         REAL,
  adjusted_close    REAL,
  split_factor      REAL NOT NULL DEFAULT 1.0,
  dividend          REAL NOT NULL DEFAULT 0.0,
  special_distribution_flag INTEGER NOT NULL DEFAULT 0,
  spinoff_relationship      TEXT,
  effective_date            TEXT,
  announcement_date_when_available TEXT,
  source            TEXT NOT NULL,
  confidence        TEXT NOT NULL,
  adjustment_methodology TEXT NOT NULL,
  PRIMARY KEY (ticker, date)
);
CREATE TABLE IF NOT EXISTS corporate_actions (
  ticker     TEXT NOT NULL,
  event_type TEXT NOT NULL,           -- split|dividend|special_dividend|
                                      -- spinoff|symbol_change|merger_delisting
  effective_date TEXT NOT NULL,
  announcement_date_when_available TEXT,
  factor     REAL,                    -- split factor or div per share
  relationship TEXT,                  -- e.g. 'SNDK:0.3333' (UNVERIFIED)
  confidence TEXT NOT NULL,
  label      TEXT NOT NULL DEFAULT 'REAL',   -- REAL | SYNTHETIC
  notes      TEXT,
  PRIMARY KEY (ticker, event_type, effective_date)
);
CREATE TABLE IF NOT EXISTS discrepancies (
  ticker        TEXT NOT NULL,
  date          TEXT NOT NULL,
  observed_log_step REAL NOT NULL,
  expected_log_step REAL NOT NULL,
  residual_log_step REAL NOT NULL,
  severity      TEXT NOT NULL,        -- INFO|MEDIUM|HIGH
  detail        TEXT,
  PRIMARY KEY (ticker, date)
);
CREATE TABLE IF NOT EXISTS quarantine (
  ticker TEXT PRIMARY KEY,
  quarantined_from_signal_use INTEGER NOT NULL DEFAULT 1,
  reason TEXT NOT NULL,
  decided_at TEXT NOT NULL
);
""")


def upsert_bar(con, row):
    con.execute("""
INSERT OR REPLACE INTO dual_bars
 (ticker, date, raw_close, adjusted_close, split_factor, dividend,
  special_distribution_flag, spinoff_relationship, effective_date,
  announcement_date_when_available, source, confidence,
  adjustment_methodology)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
""", (row["ticker"], row["date"], row.get("raw_close"),
      row.get("adjusted_close"), row.get("split_factor", 1.0),
      row.get("dividend", 0.0), row.get("special_distribution_flag", 0),
      row.get("spinoff_relationship"), row.get("effective_date"),
      row.get("announcement_date_when_available"), row.get("source", SOURCE_YF),
      row.get("confidence", CONF_HIGH), row.get("adjustment_methodology",
                                                 METHODOLOGY)))


def record_action(con, ticker, event_type, effective_date, factor=None,
                  relationship=None, announcement=None, confidence=CONF_HIGH,
                  label="REAL", notes=None):
    con.execute("""
INSERT OR REPLACE INTO corporate_actions
 (ticker, event_type, effective_date, announcement_date_when_available,
  factor, relationship, confidence, label, notes)
VALUES (?,?,?,?,?,?,?,?,?)
""", (ticker, event_type, effective_date, announcement, factor,
      relationship, confidence, label, notes))


def quarantine(con, ticker, reason):
    con.execute("""
INSERT OR REPLACE INTO quarantine
 (ticker, quarantined_from_signal_use, reason, decided_at)
VALUES (?,1,?,datetime('now'))
""", (ticker, reason))


def is_quarantined(con, ticker):
    r = con.execute("SELECT 1 FROM quarantine WHERE ticker=? AND "
                    "quarantined_from_signal_use=1", (ticker,)).fetchone()
    return r is not None


# ----------------------------------------------------------------------
# ingestion adapter
# ----------------------------------------------------------------------

def universe_tickers(db_path=FACTOR_DB):
    """All tickers currently in the bars table (the 125-name universe)."""
    con = sqlite3.connect("file:%s?mode=ro" % db_path.replace("\\", "/"),
                          uri=True)
    try:
        return sorted(r[0] for r in
                      con.execute("SELECT DISTINCT ticker FROM bars"))
    finally:
        con.close()


def _load_state(path=STATE_PATH):
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            pass
    return {"done": {}}


def _save_state(state, path=STATE_PATH):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=1)
    os.replace(tmp, path)


def ingest_ticker(yf, tk, start=INGEST_START):
    """Fetch raw+adjusted history for one ticker. Returns list of row dicts."""
    t = yf.Ticker(tk)
    h = t.history(auto_adjust=False, start=start)
    rows = []
    if h is None or len(h) == 0:
        return rows
    cols = {c.lower().replace(" ", "_"): c for c in h.columns}
    c_close = cols.get("close")
    c_adj = cols.get("adj_close")
    c_div = cols.get("dividends")
    c_spl = cols.get("stock_splits")
    conf = CONF_HIGH
    for idx, r in h.iterrows():
        d = str(idx)[:10]
        div = float(r[c_div]) if c_div else 0.0
        spl = float(r[c_spl]) if c_spl else 1.0
        if not spl or spl != spl:           # 0.0 sentinel / NaN -> no split
            spl = 1.0
        rows.append({
            "ticker": tk,
            "date": d,
            "adjusted_close": float(r[c_adj]) if c_adj else None,
            "split_factor": spl,
            "dividend": div,
            "source": SOURCE_YF,
            "confidence": conf,
            "adjustment_methodology": METHODOLOGY,
        })
    # DATA REALITY: Yahoo's Close (auto_adjust=False) is ALREADY
    # split-adjusted (only dividends drive the Adj-Close wedge). To expose
    # the true traded price -- where split gaps physically exist -- undo
    # every LATER split by walking backward and multiplying.
    acc = 1.0
    close_by_date = {str(idx)[:10]: float(r[c_close])
                     for idx, r in h.iterrows()} if c_close else {}
    for row in reversed(rows):
        row["raw_close"] = (close_by_date.get(row["date"], 0.0) * acc) \
            or None
        acc *= row["split_factor"]
    return rows


def ingest_all(tickers=None, db_path=DB_PATH, state_path=STATE_PATH,
               sleep_s=1.2, max_n=None, log=lambda m: print(m, flush=True)):
    """Rate-limited, resumable ingestion for the whole universe.

    Returns summary dict {attempted, ingested, empty, failed}.
    """
    interp = detect_interpreter()
    if interp is None:
        raise RuntimeError(
            "no interpreter with yfinance found "
            "(tried /path/to/python/python.exe and %s)" % sys.executable)
    if os.path.abspath(interp) != os.path.abspath(sys.executable):
        # re-exec under the working interpreter so imports resolve
        cmd = [interp, os.path.abspath(__file__), "--worker"] + [
            "--db", db_path, "--state", state_path,
            "--sleep", str(sleep_s)]
        if max_n:
            cmd += ["--max-n", str(max_n)]
        rc = subprocess.call(cmd)
        if rc != 0:
            raise RuntimeError("worker re-exec failed rc=%d" % rc)
        return _summary_from_state(state_path)

    import yfinance as yf  # noqa: guaranteed importable here
    if tickers is None:
        tickers = universe_tickers()
    if max_n:
        tickers = tickers[:max_n]
    state = _load_state(state_path)
    con = connect(db_path)
    attempted = ingested = empty = failed = 0
    try:
        for i, tk in enumerate(tickers):
            if tk in state["done"]:
                continue
            attempted += 1
            try:
                rows = ingest_ticker(yf, tk)
            except Exception as exc:                       # noqa: BLE001
                failed += 1
                log("[fail] %s %s: %s" % (tk, type(exc).__name__,
                                          str(exc)[:120]))
                rows = []
            if rows:
                for row in rows:
                    upsert_bar(con, row)
                con.commit()
                ingested += 1
                state["done"][tk] = {"rows": len(rows),
                                     "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
            else:
                empty += 1
                state["done"][tk] = {"rows": 0,
                                     "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                     "note": "no bars returned"}
            _save_state(state, state_path)
            if i % 10 == 9:
                log("[ingest] %d/%d last=%s rows=%d"
                    % (i + 1, len(tickers), tk,
                       state["done"].get(tk, {}).get("rows", 0)))
            time.sleep(sleep_s)
    finally:
        con.close()
        _save_state(state, state_path)
    return _summary_from_state(state_path)


def _summary_from_state(state_path=STATE_PATH):
    st = _load_state(state_path)
    done = st.get("done", {})
    return {
        "tickers_in_state": len(done),
        "with_rows": sum(1 for v in done.values() if v.get("rows")),
        "empty": sum(1 for v in done.values() if not v.get("rows")),
    }


# ----------------------------------------------------------------------
# discrepancy detector + quarantine
# ----------------------------------------------------------------------

def detect_discrepancies(con, tol_quiet=QUIET_TOL, tol_event=EVENT_TOL,
                         tol_quarantine=QUARANTINE_TOL, tickers=None,
                         write=True):
    """Compare implied-factor log-steps vs event-implied expectations.

    Returns dict {checked, mismatches, quarantined} where mismatches counts
    rows written to discrepancies with severity > INFO.
    """
    if tickers is None:
        tickers = sorted(r[0] for r in
                         con.execute("SELECT DISTINCT ticker FROM dual_bars"))
    events_by_tk = {}
    for tk, et, d, fac in con.execute(
            "SELECT ticker, event_type, effective_date, factor "
            "FROM corporate_actions"):
        events_by_tk.setdefault((tk, d), []).append((et, fac))

    stats = {"checked": 0, "mismatches": 0, "quarantined": 0}
    worst = {}
    for tk in tickers:
        rows = con.execute(
            "SELECT date, raw_close, adjusted_close FROM dual_bars "
            "WHERE ticker=? ORDER BY date", (tk,)).fetchall()
        if len(rows) < 30:
            continue
        stats["checked"] += 1
        prev_f = None
        prev_raw = None
        for d, raw, adj in rows:
            if raw is None or adj is None or adj == 0 or raw == 0:
                continue
            f = raw / adj
            if prev_f is not None and prev_f > 0:
                obs = math.log(prev_f / f) if f > 0 else 0.0
                exp = 0.0
                reasons = []
                for et, fac in events_by_tk.get((tk, d), []):
                    if et == "split" and fac:
                        exp += math.log(fac)
                        reasons.append("split x%s" % fac)
                    elif et == "spinoff" and fac:
                        # Yahoo encodes spinoffs as pseudo-splits; the
                        # implied-factor step equals the pseudo-split factor
                        exp += math.log(fac)
                        reasons.append("spinoff pseudo-split x%s" % fac)
                    elif et in ("dividend", "special_dividend") and fac \
                            and prev_raw:
                        # f_{t-1}/f_t = 1/(1 - div/raw_prev): f SHRINKS by
                        # the dividend share, so the expected step is
                        # -log(1 - div/raw) > 0
                        exp -= math.log(1.0 - min(fac / prev_raw, 0.95))
                        reasons.append("div %s" % fac)
                resid = obs - exp
                sev = None
                if abs(resid) > tol_event:
                    sev = "HIGH" if abs(resid) > tol_quarantine else "MEDIUM"
                elif abs(obs) > tol_quiet and abs(resid) <= tol_event:
                    sev = "INFO"
                if sev and write:
                    con.execute("""
INSERT OR REPLACE INTO discrepancies
 (ticker, date, observed_log_step, expected_log_step, residual_log_step,
  severity, detail)
VALUES (?,?,?,?,?,?,?)
""", (tk, d, round(obs, 6), round(exp, 6), round(resid, 6), sev,
      "; ".join(reasons) or "no recorded event"))
                if sev in ("MEDIUM", "HIGH"):
                    stats["mismatches"] += 1
                cur = worst.get(tk)
                if cur is None or abs(resid) > abs(cur[1]):
                    worst[tk] = (d, resid, obs)
            prev_f = f
            prev_raw = raw
        if write:
            con.commit()

    # quarantine pass
    if write:
        for tk, (d, resid, obs) in worst.items():
            if abs(resid) > tol_quarantine:
                quarantine(con, tk,
                           "unexplained implied-factor step %.4f%% on %s "
                           "(observed %.4f%%, residual after recorded events)"
                           % (100.0 * (math.exp(resid) - 1.0), d,
                              100.0 * (math.exp(obs) - 1.0)))
                stats["quarantined"] += 1
        con.commit()
    return stats


def stitched_series(con, ticker, cal=None, raw_dates=None):
    """Rebuild a cost-basis-preserving (gap-free) series from RAW closes
    using the store's own corporate actions -- the corrective transform.

    Applies, walking forward: on each event date, pre-event raw closes are
    rescaled by k so no artificial jump survives:
      split xN          -> divide pre-event raw by N
      dividend D        -> subtract D*frac from pre-event closes (approx:
                           multiply by (1 - D/prev_raw))
      spinoff rel r:S   -> multiply pre-event by k = p/(p + S_open*r)
                           (S_open proxied by first post-event quote of S)
    """
    rows = con.execute(
        "SELECT date, raw_close FROM dual_bars WHERE ticker=? ORDER BY date",
        (ticker,)).fetchall()
    ser = {d: c for d, c in rows if c is not None}
    dates = sorted(ser)
    acts = con.execute(
        "SELECT event_type, effective_date, factor, relationship "
        "FROM corporate_actions WHERE ticker=? ORDER BY effective_date",
        (ticker,)).fetchall()
    out = dict(ser)
    for et, eff, fac, rel in acts:
        pre = [d for d in out if d < eff]
        if not pre:
            continue
        if et == "split" and fac:
            k = 1.0 / float(fac)
        elif et in ("dividend", "special_dividend") and fac:
            pr = out[max(pre)]
            k = max(1.0 - float(fac) / pr, 0.05)
        elif et == "spinoff" and rel:
            leg, ratio = rel.split(":")
            srow = con.execute(
                "SELECT MIN(date), adjusted_close FROM dual_bars "
                "WHERE ticker=? AND date>=?", (leg, eff)).fetchone()
            if not srow or srow[1] is None:
                continue
            s_open = float(srow[1])
            p = out[max(pre)]
            k = p / (p + s_open * float(ratio))
        else:
            continue
        for d in pre:
            out[d] = out[d] * k
    return out


# ----------------------------------------------------------------------
# fixtures
# ----------------------------------------------------------------------

def load_fixtures(con, yf_mod=None):
    """Install F1-F5. REAL fixtures derive from ingested/live data;
    SYNTHETIC ones are generated locally and clearly labeled.

    Returns list of fixture descriptors."""
    desc = []

    def add(ticker, kind, eff, **kw):
        record_action(con, ticker, kind, eff, **kw)
        desc.append({"fixture": ticker, "type": kind, "effective": eff,
                     "label": kw.get("label", "REAL")})

    # F1 WDC/SNDK spinoff -- REAL data. Yahoo models the separation as a
    # pseudo-split factor 1.323 on 2025-02-24 (= 0.323 SNDK per WDC),
    # corroborating the D10 study's 1-for-3 recall; economic interpretation
    # of the vendor pseudo-split stays flagged MEDIUM/UNVERIFIED.
    add("WDC", "spinoff", "2025-02-24", factor=1.323,
        relationship="SNDK:0.3233",
        confidence=CONF_MED, label="REAL",
        notes="UNVERIFIED economic ratio; vendor (yfinance) encodes the "
              "spinoff as pseudo-split x1.323 on 2025-02-24 -> 0.323 SNDK "
              "per WDC, matching the 1-for-3 recall in "
              "wdc-sndk-stitch-report.md")
    # F2 10:1 splits -- REAL (verified against Yahoo Stock Splits column).
    add("NVDA", "split", "2024-06-10", factor=10.0, confidence=CONF_HIGH,
        label="REAL", notes="10-for-1 forward split, verified in yfinance "
                            "Stock Splits column")
    add("AVGO", "split", "2024-07-15", factor=10.0, confidence=CONF_HIGH,
        label="REAL", notes="10-for-1 forward split, verified in yfinance "
                            "Stock Splits column")
    # F3 merger-delisted -- SYNTHETIC (yfinance serves no bars for TWTR).
    _synth_merger_fixture(con)
    add("TWTR-SYN", "merger_delisting", "2022-10-27", factor=54.20,
        confidence=CONF_LOW, label="SYNTHETIC",
        notes="SYNTHETIC cash-out at $54.20/share modeled on Twitter/X Corp "
              "acquisition; yfinance returns zero bars for truly delisted "
              "tickers, so the series is generated locally")
    # F4 special dividend -- SYNTHETIC.
    _synth_special_div_fixture(con)
    add("SPEC-SYN", "special_dividend", "2018-06-11", factor=8.00,
        confidence=CONF_LOW, label="SYNTHETIC",
        notes="SYNTHETIC $8.00 special dividend; no free in-universe "
              "special-dividend case identified")
    # F5 symbol change -- REAL (FB -> META 2022-06-09; continuous history
    # served under META).
    add("META", "symbol_change", "2022-06-09", confidence=CONF_HIGH,
        label="REAL",
        notes="Facebook Inc renamed Meta Platforms; ticker FB->META; "
              "yfinance serves one continuous series under META")

    # dividend + split event rows for detector consumption (real, from
    # dual_bars: every Yahoo-reported split/pseudo-split and cash dividend)
    for tk, d, dv in con.execute(
            "SELECT ticker, date, dividend FROM dual_bars "
            "WHERE dividend > 0 ORDER BY ticker, date"):
        record_action(con, tk, "dividend", d, factor=dv,
                      confidence=CONF_HIGH, label="REAL",
                      notes="per-ex-date cash dividend from yfinance")
    seen = set()
    for tk, d, sf in con.execute(
            "SELECT ticker, date, split_factor FROM dual_bars "
            "WHERE split_factor != 1.0 AND split_factor > 0 "
            "ORDER BY ticker, date"):
        key = (tk, d)
        if key in seen or (tk, "spinoff", d) in seen:
            continue
        if tk == "WDC" and d == "2025-02-24":
            # recorded above as the F1 spinoff fixture
            seen.add(key)
            continue
        record_action(con, tk, "split", d, factor=sf,
                      confidence=CONF_HIGH, label="REAL",
                      notes="split/pseudo-split factor from yfinance "
                            "Stock Splits column")
        seen.add(key)
    con.commit()
    return desc


def _synth_merger_fixture(con, seed=42):
    """TWTR-SYN: geometric random walk ending in a flat cash-out."""
    import random
    rng = random.Random(seed)
    dates = _business_days("2021-01-04", 460)
    px, p = [], 70.0
    for _ in dates:
        p *= math.exp(rng.gauss(0.0002, 0.02))
        px.append(p)
    for i, (d, p) in enumerate(zip(dates, px)):
        if i >= len(dates) - 1:
            p = 54.20                     # forced merger consideration
        upsert_bar(con, {
            "ticker": "TWTR-SYN", "date": d, "raw_close": round(p, 4),
            "adjusted_close": round(p, 4), "source": "SYNTHETIC",
            "confidence": CONF_LOW,
            "adjustment_methodology": "synthetic_no_adjustments"})
    record_action(con, "TWTR-SYN", "merger_delisting", dates[-1],
                  factor=54.20, confidence=CONF_LOW, label="SYNTHETIC",
                  notes="cash-out terminates the series; adjusted==raw by "
                        "construction")


def _synth_special_div_fixture(con, seed=7):
    """SPEC-SYN: flat series with one $8 special dividend whose raw close
    gaps down while the adjusted series does not."""
    import random
    rng = random.Random(seed)
    dates = _business_days("2017-01-03", 500)
    ex_i = next(i for i, d in enumerate(dates) if d >= "2018-06-11")
    raw, adj = [], []
    p = 100.0
    k = None                          # back-adjust multiplier after ex-date
    for i, d in enumerate(dates):
        r = rng.gauss(0.0002, 0.01)
        if i == ex_i:
            k = (100.0 - 8.0) / 100.0   # raw gaps down by the $8 dividend
            p *= k
            p *= math.exp(r)
            raw.append(p)
            adj.append(p / k)           # vendor-adjusted does NOT gap
        else:
            p *= math.exp(r)
            raw.append(p)
            adj.append(p / k if k is not None else p)
    for d, p, q in zip(dates, raw, adj):
        upsert_bar(con, {
            "ticker": "SPEC-SYN", "date": d, "raw_close": round(p, 4),
            "adjusted_close": round(q, 6), "source": "SYNTHETIC",
            "confidence": CONF_LOW,
            "adjustment_methodology": "synthetic_vendor_backadjust"})
    record_action(con, "SPEC-SYN", "special_dividend", dates[ex_i],
                  factor=8.00, confidence=CONF_LOW, label="SYNTHETIC")


def _business_days(start_d, n):
    """n NYSE-style business days starting on/after start_d (no holiday
    calendar -- sufficient for synthetic fixtures)."""
    import datetime
    d = datetime.date.fromisoformat(start_d)
    out = []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += datetime.timedelta(days=1)
    return out


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------

def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--worker" in argv:
        i = argv.index("--worker")
        rest = argv[i + 1:]

        def opt(name, default=None):
            return rest[rest.index(name) + 1] if name in rest else default
        ingest_all(db_path=opt("--db", DB_PATH),
                   state_path=opt("--state", STATE_PATH),
                   sleep_s=float(opt("--sleep", "1.2")),
                   max_n=int(opt("--max-n")) if opt("--max-n") else None)
        return
    print("usage: dual_price_store.py [--worker ...]; "
          "see test_dual_price_store.py and run_ingestion()")


if __name__ == "__main__":
    main()

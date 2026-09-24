#!/usr/bin/env python3
"""macro_vintages_alfred.py -- ALFRED vintage adapter (D-R2).

Replaces ASSUMED-LAG provenance in the bitemporal VintageStore
(macro_vintage_store.VintageStore) with GENUINE vintage observations for
every series in factors.db that ALFRED carries.

Data source
-----------
ALFRED (Archival FRED) is reached through the FRED web service endpoints
(api.stlouisfed.org/fred/series/observations with realtime_start/end, and
series/vintagedates). The realtime_* parameters are the machine interface to
exactly the same archival revision history the ALFRED website serves; a free
FRED API key is read from FRED_API_KEY (fail-closed: without it only the
keyless alfredgraph.csv latest-vintage CSV is reachable, which carries NO
revision history, so the module refuses to fabricate provenance and every
series falls back to its documented non-actual status).

Per observation we store EVERY revision as its own row:
    value            = the value of that revision
    first_seen_date  = realtime_start (publication date of that revision)
    revision_of      = rowid of the previous revision (insertion chain)

Series classification (persisted in _work/fis-data/macro-vintage-status.json):
    actual-vintage-history          -- real ALFRED vintages downloaded
    release-calendar-reconstruction -- not carried by ALFRED but a defensible,
                                       documented release-calendar reconstruction
                                       exists (reserved; none asserted here)
    assumed-lag                     -- synthetic lag from macro_vintage_store
    no-safe-use                     -- blocked from historical backtest use

Guard (enforced in code):
    pit_usable(series_id, purpose='sealed_validation') -> False unless status
    is actual-vintage-history / release-calendar-reconstruction, or an
    explicit override is passed AND the override is disclosed via
    disclose_override() (recorded in the override ledger file).

Politeness / robustness:
    * <= 1 request/second enforced between any two HTTP calls
    * retries with exponential backoff on timeouts / 429 / 5xx
    * resumable: per-series checkpoint file skips series already ingested
      (delete the checkpoint or pass --force to re-download)

CLI:
    python macro_vintages_alfred.py sync      [--limit-series ID ...]
    python macro_vintages_alfred.py status
    python macro_vintages_alfred.py selftest | --selftest   (offline tests)
    python macro_vintages_alfred.py livetest  (network; REAL vintage data)

Stdlib only. ASCII only. No git.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import io
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from macro_vintage_store import VintageStore, seed_from_factors  # noqa: E402

_WORK = os.path.join(os.path.dirname(os.path.dirname(_HERE)), "Efforts", "osanwe-v2-overhaul", "_work")
_DEFAULT_FACTORS_DB = os.path.join(_WORK, "factors.db")
_DEFAULT_VINTAGE_DB = os.path.join(_WORK, "fis-data", "macro_vintages.db")
_DEFAULT_STATUS_JSON = os.path.join(_WORK, "fis-data", "macro-vintage-status.json")
_DEFAULT_CHECKPOINT = os.path.join(_HERE, "_work", "alfred_sync_checkpoint.json")
_DEFAULT_OVERRIDES = os.path.join(_HERE, "_work", "pit_overrides.json")

_FRED_ROOT = "https://api.stlouisfed.org/fred"
_ALFRED_LATEST_CSV = ("https://alfred.stlouisfed.org/graph/"
                      "alfredgraph.csv?id=")
_USER_AGENT = "fis-pit-vintage-sync/1.0 (local research tool)"
_MIN_REQUEST_INTERVAL = 1.05          # seconds; enforces <= 1 req/sec
_HTTP_TIMEOUT = 90                    # seconds per request
_RETRY_ATTEMPTS = 4
_OBS_WINDOW_DAYS = 400                # realtime windows per request
_MAX_VINTAGE_DATES = 2000             # FRED cap per realtime window


def fetch_vintage_dates(series_id: str, api_key: str) -> list:
    """All ALFRED vintage dates for a series (release dates with revisions)."""
    dates = []
    off = 0
    while True:
        j = fred_json("series/vintagedates", api_key, series_id=series_id,
                      limit=1000, offset=off)
        dates.extend(j.get("vintage_dates", []))
        if len(j.get("vintage_dates", [])) < 1000:
            break
        off += 1000
    return dates


# Status vocabulary (single source of truth)
ST_ACTUAL = "actual-vintage-history"
ST_RECONSTRUCTION = "release-calendar-reconstruction"
ST_ASSUMED = "assumed-lag"
ST_NO_SAFE_USE = "no-safe-use"

#: purposes that REQUIRE genuine point-in-time provenance
SEALED_PURPOSES = {"sealed_validation", "backtest", "production_signal"}

_last_request_ts = [0.0]              # module-level rate-limit state


# --------------------------------------------------------------------------
# Series universe (52) + ALFRED carry classification
# --------------------------------------------------------------------------

#: yfinance/market-quote tickers in factors.db -- ALFRED does not carry these
YFINANCE_SERIES = {
    "CL=F", "DBC", "DX-Y.NYB", "EEM", "EURUSD=X", "FXI", "GBPUSD=X",
    "GC=F", "HG=F", "NG=F", "USDJPY=X", "^N225", "^SKEW", "^STOXX50E",
    "^VIX", "^VVIX",
}

#: FRED series known to be carried by ALFRED (archival revision history
#: verified via series/vintagedates during D-R2 bring-up)
ALFRED_CARRIED = [
    "BAA10Y", "BAMLC0A0CM", "BAMLEMCBPIOAS", "BAMLH0A0HYM2",
    "BAMLH0A0HYM2EY", "BAMLH0A1HYBB", "CPIAUCSL", "DBAA", "DCOILWTICO",
    "DEXJPUS", "DFII10", "DGS1", "DGS10", "DGS2", "DGS20", "DGS3", "DGS30",
    "DGS5", "DGS7", "DHHNGSP", "DTWEXBGS", "FEDFUNDS", "NFCI", "RRPONTSYD",
    "SOFR", "STLFSI4", "T10Y2Y", "T10Y3M", "T5YIE", "T5YIFR", "TREAST",
    "UNRATE", "USEPUINDXD", "VIXCLS", "WALCL", "WRESBAL",
]


def factors_series(factors_db: str):
    """The distinct factor ids in factors.db factors table (expect 52)."""
    conn = sqlite3.connect("file:%s?mode=ro" % factors_db.replace("\\", "/"),
                           uri=True)
    try:
        return sorted(r[0] for r in conn.execute(
            "SELECT DISTINCT factor FROM factors"))
    finally:
        conn.close()


# --------------------------------------------------------------------------
# Rate-limited HTTP
# --------------------------------------------------------------------------

def _throttle():
    wait = _MIN_REQUEST_INTERVAL - (time.time() - _last_request_ts[0])
    if wait > 0:
        time.sleep(wait)
    _last_request_ts[0] = time.time()


def http_get(url: str, attempts: int = _RETRY_ATTEMPTS) -> bytes:
    """GET with <=1 req/s pacing, timeout tolerance and backoff retries."""
    last_err = None
    for i in range(attempts):
        _throttle()
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": _USER_AGENT, "Accept-Encoding": "identity"})
            with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
                return resp.read()
        except (urllib.error.URLError, urllib.error.HTTPError,
                TimeoutError, OSError) as err:
            last_err = err
            code = getattr(err, "code", None)
            if code is not None and code < 500 and code != 429:
                raise          # permanent client error: do not retry
            sleep_s = min(60.0, 3.0 * (2 ** i))
            time.sleep(sleep_s)
    raise RuntimeError("http_get failed after %d attempts: %s (%r)"
                       % (attempts, url[:120], last_err))


def fred_json(path: str, api_key: str, **params) -> dict:
    params.update({"file_type": "json", "api_key": api_key})
    url = "%s/%s?%s" % (_FRED_ROOT, path, urllib.parse.urlencode(params))
    return json.loads(http_get(url).decode("utf-8"))


# --------------------------------------------------------------------------
# Vintage download + ingestion
# --------------------------------------------------------------------------

def fetch_vintage_rows(series_id: str, api_key: str,
                       obs_start: str, obs_end: str) -> list:
    """All revisions of all observations of series_id in [obs_start, obs_end].

    The FRED observations endpoint rejects realtime windows spanning more
    than 2000 vintage dates, so the full window is split into sub-windows
    bounded by the series' actual ALFRED vintage-date list. Each request
    returns rows whose realtime_start (publication date) lies in-window.

    Returns rows sorted chronologically by first_seen (realtime_start);
    each item: (observation_date, value, first_seen_date).
    """
    vdates = fetch_vintage_dates(series_id, api_key)
    if not vdates:
        return []
    # windows of at most _MAX_VINTAGE_DATES vintage dates each
    windows = []
    i = 0
    while i < len(vdates):
        chunk = vdates[i:i + _MAX_VINTAGE_DATES]
        windows.append((chunk[0], chunk[-1]))
        i += _MAX_VINTAGE_DATES

    rows = []
    for rt_start, rt_end in windows:
        page_off = 0
        while True:
            j = fred_json("series/observations", api_key,
                          series_id=series_id,
                          observation_start=obs_start,
                          observation_end=obs_end,
                          realtime_start=rt_start,
                          realtime_end=rt_end,
                          limit=1000, offset=page_off,
                          sort_order="asc")
            for o in j.get("observations", []):
                v = o["value"]
                if v == ".":
                    continue       # not-yet-published placeholder
                rows.append((o["date"], float(v), o["realtime_start"]))
            got = len(j.get("observations", []))
            if got < int(j.get("limit", 1000)):
                break
            page_off += got
    # chronological publication order so revision_of chains correctly
    rows.sort(key=lambda r: (r[2], r[0]))
    return rows


def ingest_series(store: VintageStore, series_id: str, rows: list) -> dict:
    """Replace any prior rows for series_id with genuine ALFRED vintages.

    Rows must arrive in chronological publication order; revision_of is
    derived structurally from stored (id) ordering so ingestion order can
    never corrupt the chain.
    """
    cur = store.conn.cursor()
    cur.execute("DELETE FROM vintages WHERE series_id=?", (series_id,))
    batch = [(series_id, obs_date, value, first_seen, first_seen, "ALFRED")
             for obs_date, value, first_seen in rows]
    cur.executemany(
        "INSERT INTO vintages (series_id, observation_date, value,"
        " first_seen_date, vintage_date, revision_of, src)"
        " VALUES (?, ?, ?, ?, ?, NULL, ?)", batch)
    # fix revision_of chains deterministically from stored ordering
    cur.execute(
        "UPDATE vintages SET revision_of = ("
        "  SELECT MAX(v2.id) FROM vintages v2"
        "  WHERE v2.series_id = vintages.series_id"
        "    AND v2.observation_date = vintages.observation_date"
        "    AND v2.id < vintages.id)"
        " WHERE series_id=? AND src='ALFRED'", (series_id,))
    store.conn.commit()
    return {"rows": len(batch)}


def sync_series(store: VintageStore, series_id: str, api_key: str,
                factors_db: str) -> dict:
    """Download + ingest one series; returns an info dict."""
    conn = sqlite3.connect("file:%s?mode=ro" % factors_db.replace("\\", "/"),
                           uri=True)
    try:
        rng = conn.execute(
            "SELECT MIN(date), MAX(date) FROM factors WHERE factor=?",
            (series_id,)).fetchone()
    finally:
        conn.close()
    if not rng or not rng[0]:
        return {"series": series_id, "status": ST_ASSUMED, "rows": 0,
                "note": "no observations in factors.db"}
    obs_start, obs_end = rng
    # pad start: initial release may predate first factor row usage
    padded = (_dt.date.fromisoformat(obs_start)
              - _dt.timedelta(days=200)).isoformat()
    rows = fetch_vintage_rows(series_id, api_key, padded, obs_end)
    info = ingest_series(store, series_id, rows)
    revised = count_revised_observations(store.conn, series_id)
    return {"series": series_id, "status": ST_ACTUAL,
            "rows": info["rows"],
            "revised_observations": revised,
            "first_release": rows[0][2] if rows else None,
            "last_release": rows[-1][2] if rows else None}


def count_revised_observations(conn: sqlite3.Connection,
                               series_id: str) -> int:
    """Observations with >= 2 genuine revisions (initial != latest proof)."""
    return conn.execute(
        "SELECT COUNT(*) FROM ("
        " SELECT observation_date FROM vintages"
        " WHERE series_id=? AND src='ALFRED'"
        " GROUP BY observation_date HAVING COUNT(*) >= 2)",
        (series_id,)).fetchone()[0]


# --------------------------------------------------------------------------
# Status registry
# --------------------------------------------------------------------------

def build_status(factors_db: str, vintage_db: str,
                 synced: dict | None = None) -> dict:
    """Classify ALL 52 factors.db series into exactly one status each."""
    synced = synced or {}
    all_series = factors_series(factors_db)
    store = VintageStore(vintage_db)
    try:
        have_alfred = {r[0]: r[1] for r in store.conn.execute(
            "SELECT series_id, COUNT(*) FROM vintages WHERE src='ALFRED'"
            " GROUP BY series_id")}
    finally:
        store.close()
    per = {}
    counts = {ST_ACTUAL: 0, ST_RECONSTRUCTION: 0, ST_ASSUMED: 0,
              ST_NO_SAFE_USE: 0}
    for sid in all_series:
        if sid in have_alfred and have_alfred[sid] > 0:
            st = ST_ACTUAL
            note = ("%d genuine ALFRED vintage rows"
                    % have_alfred[sid])
        elif sid in YFINANCE_SERIES:
            st = ST_NO_SAFE_USE
            note = ("market quote stream (yfinance); no official release "
                    "calendar exists, revision-free close cannot be "
                    "reconstructed defensibly")
        else:
            # carried by neither branch: keep seeded ASSUMED-LAG provenance
            st = ST_ASSUMED
            note = "not carried by ALFRED; ASSUMED-LAG seeding retained"
        if sid in synced:
            note = synced[sid].get("note", note)
        per[sid] = {"status": st, "note": note}
        counts[st] += 1
    return {
        "generated_utc": _dt.datetime.now(_dt.timezone.utc)
                           .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "ALFRED via FRED web service (api.stlouisfed.org, "
                  "realtime_start/end vintage queries)",
        "total_series": len(all_series),
        "counts": counts,
        "coverage": "%d actual / %d reconstruction / %d assumed-lag / "
                    "%d no-safe-use of %d"
                    % (counts[ST_ACTUAL], counts[ST_RECONSTRUCTION],
                       counts[ST_ASSUMED], counts[ST_NO_SAFE_USE],
                       len(all_series)),
        "series": per,
    }


def write_status(status: dict, path: str = _DEFAULT_STATUS_JSON) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="ascii") as fh:
        json.dump(status, fh, indent=2, sort_keys=True)
    os.replace(tmp, path)
    return path


def load_status(path: str = _DEFAULT_STATUS_JSON) -> dict:
    with open(path, "r", encoding="ascii") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------
# Point-in-time usability guard
# --------------------------------------------------------------------------

class PitOverrideLedger:
    """Explicit, disclosed overrides of pit_usable, persisted to disk."""

    def __init__(self, path: str = _DEFAULT_OVERRIDES):
        self.path = path
        self._overrides = {}
        if os.path.exists(path):
            with open(path, "r", encoding="ascii") as fh:
                self._overrides = json.load(fh)

    def disclose(self, series_id: str, purpose: str, reason: str,
                 disclosed_by: str) -> None:
        key = "%s|%s" % (series_id, purpose)
        self._overrides[key] = {
            "reason": reason,
            "disclosed_by": disclosed_by,
            "disclosed_utc": _dt.datetime.now(_dt.timezone.utc)
                               .strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="ascii") as fh:
            json.dump(self._overrides, fh, indent=2, sort_keys=True)
        os.replace(tmp, self.path)

    def has(self, series_id: str, purpose: str) -> bool:
        return ("%s|%s" % (series_id, purpose)) in self._overrides

    def get(self, series_id: str, purpose: str):
        return self._overrides.get("%s|%s" % (series_id, purpose))


_DEFAULT_LEDGER = PitOverrideLedger()


def pit_usable(series_id: str, purpose: str = "sealed_validation",
               status_path: str = _DEFAULT_STATUS_JSON,
               override: bool = False,
               override_reason: str = "",
               disclosed_by: str = "",
               ledger: PitOverrideLedger | None = None) -> bool:
    """Guard: may this series be used at `purpose`?

    Returns True ONLY when the series carries genuine (or defensibly
    reconstructed) point-in-time provenance. For sealed/backtest purposes,
    assumed-lag and no-safe-use series are REFUSED. An explicit
    override=True call is honored only when reason + discloser are given;
    the disclosure is written to the persistent override ledger.
    """
    ledger = ledger or _DEFAULT_LEDGER
    if not os.path.exists(status_path):
        # fail closed: unclassified series must never silently pass
        return False
    entry = load_status(status_path)["series"].get(series_id)
    if entry is None:
        return False                      # unknown series: fail closed
    st = entry["status"]
    if st in (ST_ACTUAL, ST_RECONSTRUCTION):
        return True
    if purpose not in SEALED_PURPOSES:
        # exploratory work may use assumed-lag data knowingly
        return st == ST_ASSUMED
    # sealed purpose + weak provenance: require explicit AND disclosed override
    if override and override_reason and disclosed_by:
        ledger.disclose(series_id, purpose, override_reason, disclosed_by)
        return True
    if ledger.has(series_id, purpose):
        return True                       # previously disclosed override
    return False


# --------------------------------------------------------------------------
# Checkpointing (resumability)
# --------------------------------------------------------------------------

def load_checkpoint(path: str = _DEFAULT_CHECKPOINT) -> dict:
    if os.path.exists(path):
        with open(path, "r", encoding="ascii") as fh:
            return json.load(fh)
    return {"done": {}}


def save_checkpoint(cp: dict, path: str = _DEFAULT_CHECKPOINT) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="ascii") as fh:
        json.dump(cp, fh, sort_keys=True)
    os.replace(tmp, path)


# --------------------------------------------------------------------------
# Sync driver
# --------------------------------------------------------------------------

def run_sync(factors_db: str = _DEFAULT_FACTORS_DB,
             vintage_db: str = _DEFAULT_VINTAGE_DB,
             status_path: str = _DEFAULT_STATUS_JSON,
             limit_series=None, force: bool = False) -> dict:
    api_key = os.environ.get("FRED_API_KEY")
    cp = load_checkpoint()
    done = cp.setdefault("done", {})
    store = VintageStore(vintage_db)
    synced = {}
    targets = limit_series or ALFRED_CARRIED
    errors = []
    try:
        for sid in targets:
            if not force and done.get(sid):
                synced[sid] = {"note": "checkpointed (already ingested)"}
                continue
            if not api_key:
                errors.append("%s: FRED_API_KEY missing" % sid)
                continue
            try:
                info = sync_series(store, sid, api_key, factors_db)
                synced[sid] = info
                done[sid] = info
                save_checkpoint(cp)
                print("[alfred-sync] %-16s rows=%d revised_obs=%d"
                      % (sid, info["rows"],
                         info.get("revised_observations", 0)))
            except Exception as exc:                 # timeout-tolerant
                errors.append("%s: %s" % (sid, repr(exc)[:160]))
    finally:
        store.close()
    status = build_status(factors_db, vintage_db, synced)
    write_status(status, status_path)
    return {"status_path": status_path, "synced": synced, "errors": errors,
            "coverage": status["coverage"]}


# --------------------------------------------------------------------------
# Tests (offline selftest + network livetest)
# --------------------------------------------------------------------------

def _mk_tmpdir(prefix):
    import tempfile
    return tempfile.mkdtemp(prefix=prefix)


def selftest() -> int:
    """Offline tests: guard semantics, out-of-order ingestion, leakage."""
    results = []

    def check(name, cond):
        results.append((name, bool(cond)))
        print("[%s] %s" % ("PASS" if cond else "FAIL", name))

    tmpdir = _mk_tmpdir("mvalfred_selftest_")
    dbp = os.path.join(tmpdir, "v.db")
    stp = os.path.join(tmpdir, "status.json")

    try:
        # --- guard semantics ------------------------------------------------
        status = {
            "series": {
                "UNRATE": {"status": ST_ACTUAL},
                "CL=F": {"status": ST_NO_SAFE_USE},
                "MADEUP": {"status": ST_ASSUMED},
                "RECON": {"status": ST_RECONSTRUCTION},
            }
        }
        with open(stp, "w", encoding="ascii") as fh:
            json.dump(status, fh)
        check("actual series usable for sealed_validation",
              pit_usable("UNRATE", "sealed_validation", stp))
        check("reconstruction usable for sealed_validation",
              pit_usable("RECON", "sealed_validation", stp))
        check("no-safe-use refused for sealed_validation",
              not pit_usable("CL=F", "sealed_validation", stp))
        check("assumed-lag refused for sealed_validation",
              not pit_usable("MADEUP", "sealed_validation", stp))
        check("unknown series fails closed",
              not pit_usable("NOPE", "sealed_validation", stp))
        check("missing status file fails closed",
              not pit_usable("UNRATE", "sealed_validation",
                             os.path.join(tmpdir, "absent.json")))
        check("undisclosed override still refused",
              not pit_usable("CL=F", "sealed_validation", stp, override=True))
        check("override without discloser refused",
              not pit_usable("CL=F", "sealed_validation", stp,
                             override=True, override_reason="x"))

        led = PitOverrideLedger(os.path.join(tmpdir, "ovr.json"))
        check("disclosed override accepted and recorded",
              pit_usable("CL=F", "sealed_validation", stp, override=True,
                         override_reason="operator signed off",
                         disclosed_by="unit-test", ledger=led))
        check("recorded override persists across calls",
              pit_usable("CL=F", "sealed_validation", stp, ledger=led))

        # --- REAL vintage data: leakage + out-of-order ingestion -------------
        live_db = _DEFAULT_VINTAGE_DB
        if not os.path.exists(live_db):
            print("SKIP live-data checks: %s not present (run `sync` first)"
                  % live_db)
        else:
            store = VintageStore(live_db)
            real = [r[0] for r in store.conn.execute(
                "SELECT DISTINCT series_id FROM vintages WHERE src='ALFRED'")]
            check("genuine ALFRED series present in store", len(real) > 0)

            # (a) >= 3 real revised series where initial != latest
            proved = []
            for sid in real[:50]:
                rows = store.conn.execute(
                    "SELECT observation_date, COUNT(*) c FROM vintages"
                    " WHERE series_id=? AND src='ALFRED'"
                    " GROUP BY observation_date HAVING c>=2 LIMIT 3",
                    (sid,)).fetchall()
                for obs, _c in rows:
                    chain = store.revisions(sid, obs)
                    vals = [r[0] for r in chain]
                    if len(set(vals)) >= 2:
                        proved.append((sid, obs, vals[0], vals[-1]))
                        break
                if len(proved) >= 3:
                    break
            check(">= 3 REAL series with initial-release value differing "
                  "from latest (%d found: %s)"
                  % (len(proved),
                     ", ".join(p[0] for p in proved[:5])),
                  len(proved) >= 3)
            for sid, obs, init, latest in proved:
                print("    REVISED %s @ %s : initial=%s latest=%s"
                      % (sid, obs, init, latest))

            # (b) revision-leakage sweep on a REAL revised observation
            if proved:
                sid, obs, init_v, latest_v = proved[0]
                chain = store.revisions(sid, obs)
                rev_dates = [r[1] for r in chain]
                leaks = []
                d = _dt.date.fromisoformat(rev_dates[0]).replace(day=1)
                end = _dt.date.fromisoformat(rev_dates[-1])
                while d <= end:
                    dec = d.isoformat()
                    got = store.value_asof(sid, obs, dec)
                    if got is not None:
                        if got["first_seen"] > dec:
                            leaks.append((dec, "first_seen>decision"))
                        expected = None
                        for v, fs in reversed(list(zip(vals := [
                                r[0] for r in chain], rev_dates))):
                            if fs <= dec:
                                expected = v
                                break
                        if expected is not None and got["value"] != expected:
                            leaks.append((dec, "wrong revision visible"))
                    d += _dt.timedelta(days=7)
                check("REAL-data leakage sweep: zero leaks (%d dates)"
                      % ((end - _dt.date.fromisoformat(rev_dates[0])).days,),
                      not leaks)

                # (c) OUT-OF-ORDER ingestion on REAL values
                tmp2 = os.path.join(tmpdir, "ooo.db")
                s2 = VintageStore(tmp2)
                shuffled = list(chain)[::-1]           # reverse chronology
                for v, fs, _ro, _src in shuffled:
                    s2.insert(sid, obs, v, fs, src="ALFRED-test")
                got_first = s2.value_asof(sid, obs, rev_dates[0])["value"]
                got_mid = s2.value_asof(
                    sid, obs, rev_dates[len(rev_dates)//2])["value"]
                got_last = s2.value_asof(sid, obs, "9999-12-31")["value"]
                want_first = chain[0][0]
                want_mid = chain[len(chain)//2][0]
                want_last = chain[-1][0]
                check("out-of-order ingest: earliest decision returns "
                      "earliest-known value",
                      got_first == want_first)
                check("out-of-order ingest: mid decision returns mid value",
                      got_mid == want_mid)
                check("out-of-order ingest: final decision returns final "
                      "value regardless of insert order",
                      got_last == want_last)
                s2.close()

            store.close()
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)

    failed = [n for n, ok in results if not ok]
    print("\n%d/%d checks passed" % (len(results) - len(failed), len(results)))
    if failed:
        print("FAILED: " + ", ".join(failed))
        return 1
    print("SELFTEST OK")
    return 0


def livetest(limit: int = 6) -> int:
    """Network test against REAL ALFRED/FRED vintage data (small sample)."""
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        print("FRED_API_KEY missing; cannot run livetest")
        return 2
    tmpdir = _mk_tmpdir("mvalfred_livetest_")
    dbp = os.path.join(tmpdir, "live.db")
    store = VintageStore(dbp)
    results = []

    def check(name, cond):
        results.append((name, bool(cond)))
        print("[%s] %s" % ("PASS" if cond else "FAIL", name))

    try:
        revised_proofs = []
        for sid in ["UNRATE", "CPIAUCSL", "PAYEMS", "RSAFS", "GDPC1"][:limit]:
            today = _dt.date.today()
            rows = fetch_vintage_rows(sid, api_key,
                                      (today - _dt.timedelta(days=900)
                                       ).isoformat(),
                                      today.isoformat())
            if not rows:
                print("    %s: no rows" % sid)
                continue
            ingest_series(store, sid, rows)
            n_rev = count_revised_observations(store.conn, sid)
            print("    %-9s rows=%d revised_observations=%d"
                  % (sid, len(rows), n_rev))
            if n_rev:
                obs = store.conn.execute(
                    "SELECT observation_date FROM vintages"
                    " WHERE series_id=? GROUP BY observation_date"
                    " HAVING COUNT(*)>=2 ORDER BY observation_date DESC"
                    " LIMIT 1", (sid,)).fetchone()[0]
                chain = store.revisions(sid, obs)
                if len({r[0] for r in chain}) > 1:
                    revised_proofs.append((sid, obs, chain[0][0], chain[-1][0]))
        check(">=3 REAL downloaded series show initial != latest revision",
              len(revised_proofs) >= 3)
        for sid, obs, init, latest in revised_proofs:
            print("    PROOF %s @ %s initial=%s latest=%s"
                  % (sid, obs, init, latest))
        # leakage sweep on first proof
        if revised_proofs:
            sid, obs, init_v, latest_v = revised_proofs[0]
            chain = store.revisions(sid, obs)
            pairs = [(r[1], r[0]) for r in chain]     # (first_seen, value)
            leaks = []
            d0 = _dt.date.fromisoformat(pairs[0][0])
            d1 = _dt.date.fromisoformat(pairs[-1][0])
            d = d0
            while d <= d1:
                dec = d.isoformat()
                got = store.value_asof(sid, obs, dec)
                if got is not None:
                    if got["first_seen"] > dec:
                        leaks.append(dec)
                    exp = None
                    for fs, v in reversed(pairs):
                        if fs <= dec:
                            exp = v
                            break
                    if exp is not None and got["value"] != exp:
                        leaks.append(dec)
                d += _dt.timedelta(days=1)
            check("leakage sweep over %d days: zero leaks"
                  % ((d1 - d0).days + 1), not leaks)
            # out-of-order re-ingestion
            tmp3 = os.path.join(tmpdir, "ooo.db")
            s3 = VintageStore(tmp3)
            for fs, v in reversed(pairs):
                s3.insert(sid, obs, v, fs, src="ALFRED-test")
            ok_first = (s3.value_asof(sid, obs, pairs[0][0])["value"]
                        == pairs[0][1])
            ok_last = (s3.value_asof(sid, obs, "9999-12-31")["value"]
                       == pairs[-1][1])
            check("out-of-order ingestion preserves PIT answers",
                  ok_first and ok_last)
            s3.close()
    finally:
        store.close()
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)

    failed = [n for n, ok in results if not ok]
    print("\n%d/%d livetest checks passed" % (len(results) - len(failed),
                                              len(results)))
    return 1 if failed else 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="ALFRED vintage adapter (D-R2)")
    ap.add_argument("--selftest", action="store_true")
    sub = ap.add_subparsers(dest="cmd")

    p_sync = sub.add_parser("sync")
    p_sync.add_argument("--factors-db", default=_DEFAULT_FACTORS_DB)
    p_sync.add_argument("--db", default=_DEFAULT_VINTAGE_DB)
    p_sync.add_argument("--status-json", default=_DEFAULT_STATUS_JSON)
    p_sync.add_argument("--limit-series", nargs="*", default=None)
    p_sync.add_argument("--force", action="store_true")

    p_status = sub.add_parser("status")
    p_status.add_argument("--status-json", default=_DEFAULT_STATUS_JSON)
    p_status.add_argument("--json", action="store_true")

    sub.add_parser("selftest")
    lt = sub.add_parser("livetest")
    lt.add_argument("--limit", type=int, default=6)

    args = ap.parse_args(argv)

    if args.selftest or getattr(args, "cmd", None) == "selftest":
        return selftest()
    if getattr(args, "cmd", None) == "livetest":
        return livetest(limit=args.limit)
    if getattr(args, "cmd", None) == "sync":
        res = run_sync(getattr(args, "factors_db", _DEFAULT_FACTORS_DB),
                       getattr(args, "db", _DEFAULT_VINTAGE_DB),
                       getattr(args, "status_json", _DEFAULT_STATUS_JSON),
                       limit_series=args.limit_series, force=args.force)
        print(json.dumps(res, indent=2)[:4000])
        return 1 if res["errors"] else 0
    if getattr(args, "cmd", None) == "status":
        try:
            st = load_status(args.status_json)
            counts = st["counts"]
            if (not isinstance(counts, dict) or set(counts) != {ST_ACTUAL, ST_RECONSTRUCTION, ST_ASSUMED, ST_NO_SAFE_USE}
                    or any(type(value) is not int or value < 0 for value in counts.values())):
                raise ValueError("invalid coverage counts")
        except (OSError, ValueError, KeyError, TypeError):
            print(json.dumps({"state": "unavailable", "reason": "missing_or_invalid_status_metadata"}))
            return 2
        if args.json:
            print(json.dumps({"state": "observed", "counts": counts, "series_count": sum(counts.values()),
                              "observed_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
                              "scope": "saved vintage coverage metadata only; no network, source refresh or database revalidation"}))
        else:
            print("Saved metadata only; source freshness and database coverage are not revalidated.")
            print(json.dumps(counts, indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

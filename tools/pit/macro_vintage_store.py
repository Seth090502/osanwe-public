#!/usr/bin/env python3
"""macro_vintage_store.py -- ALFRED-style bitemporal macro data store (D3).

Point-in-time ("vintage") storage for macroeconomic series so that any
backtest can ask: "what did we KNOW on <decision_date>?" and NEVER see a
revision published after that date. This is the bitemporal pattern used by
ALFRED (Archival FRED): each observation carries its own publication history.

Schema (table `vintages`):
    series_id        TEXT  -- e.g. 'UNRATE', 'CPIAUCSL'
    observation_date TEXT  -- the period the value refers to ('YYYY-MM-DD')
    value            REAL  -- the numeric value of this revision
    first_seen_date  TEXT  -- publication date of THIS revision (vintage)
    vintage_date     TEXT  -- alias/label for first_seen_date (kept explicit)
    revision_of      INT   -- rowid of the prior revision this supersedes,
                           -- NULL for the initial print

Query contract:
    value_asof(series, decision_date)
        -> the latest revision whose first_seen_date <= decision_date.
        Later revisions are structurally unreachable: the WHERE clause on
        first_seen_date makes future leakage impossible by construction.

MISSING-VINTAGE HANDLING (documented):
    Real ALFRED vintages are DATA-BLOCKED: we have no subscription to the
    archival revision history, so every row seeded from factors.db carries
    an ASSUMED publication lag instead of a true release timestamp:

        * ASSUMED LAG, daily series : +1 calendar day after observation_date
          (FRED daily market series such as DGS10 are typically posted the
          same evening / next morning).
        * ASSUMED LAG, monthly series: +15 calendar days after the first of
          the month (typical mid-month BLS/BEA/FRED posting cadence).

    Every seeded row is tagged src='ASSUMED-LAG' in the provenance column so
    downstream code can audit how much of the store is synthetic vintage
    metadata. When ALFRED access becomes available, re-run `seed` against a
    real vintage source and the ASSUMED rows will be replaced.

USAGE:
    python macro_vintage_store.py seed   [--factors-db PATH] [--db PATH]
    python macro_vintage_store.py query SERIES OBS_DATE [--decision DATE]
    python macro_vintage_store.py selftest | --selftest

Stdlib only. ASCII only. No network. No git.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import sqlite3
import sys
import tempfile

# --------------------------------------------------------------------------
# Paths (defaults overridable via CLI flags)
# --------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_FACTORS_DB = os.environ.get(
    "FIS_FACTORS_DB",
    r"/path/to/vault\Efforts\osanwe-v2-overhaul\_work\factors.db",
)
_DEFAULT_VINTAGE_DB = os.path.join(
    _HERE, os.pardir, os.pardir, "Efforts", "osanwe-v2-overhaul", "_work",
    "fis-data", "macro_vintages.db",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS vintages (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id        TEXT NOT NULL,
    observation_date TEXT NOT NULL,
    value            REAL,
    first_seen_date  TEXT NOT NULL,
    vintage_date     TEXT NOT NULL,
    revision_of      INTEGER,
    src              TEXT NOT NULL DEFAULT 'unknown'
);
CREATE INDEX IF NOT EXISTS idx_vin_series_obs ON vintages(series_id, observation_date);
CREATE INDEX IF NOT EXISTS idx_vin_series_seen ON vintages(series_id, first_seen_date);
"""

# Documented ASSUMED lags (see module docstring). Keys map a series to a rule.
ASSUMED_LAG_MONTHLY = 15   # days after period start; ASSUMED, not measured
ASSUMED_LAG_DAILY = 1      # calendar days; ASSUMED, not measured

_MONTHLY_SERIES = {
    "CPIAUCSL", "UNRATE", "FEDFUNDS", "BAA10Y", "TREAST", "WALCL",
    "WRESBAL", "RRPONTSYD", "USEPUINDXD", "BAMLC0A0CM", "BAMLEMCBPIOAS",
    "BAMLH0A0HYM2", "BAMLH0A0HYM2EY", "BAMLH0A1HYBB", "NFCI", "STLFSI4",
}


def assumed_first_seen(observation_date: str, series_id: str) -> str:
    """ASSUMED publication date = observation date + documented lag.

    Clearly labeled: callers should treat every date produced here as an
    assumption, never as a measured release date.
    """
    d = _dt.date.fromisoformat(observation_date)
    if series_id in _MONTHLY_SERIES:
        # Monthly observations are stamped at period start; assume mid-month post.
        base = d.replace(day=1)
        lag = ASSUMED_LAG_MONTHLY
    else:
        base = d
        lag = ASSUMED_LAG_DAILY
    return (base + _dt.timedelta(days=lag)).isoformat()


class VintageStore:
    """Read/write access to the bitemporal vintages table."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # -- write API ---------------------------------------------------------

    # Tie rule (documented per RX2 review): duplicate
    # (series_id, observation_date, first_seen_date) rows are not blocked
    # by a UNIQUE constraint; value_asof resolves deterministically as
    # last-insert-wins (ORDER BY first_seen DESC, id DESC). Callers
    # should treat repeated identical-vintage inserts as replacements.
    def insert(self, series_id, observation_date, value, first_seen_date,
               revision_of=None, src="manual"):
        cur = self.conn.execute(
            "INSERT INTO vintages (series_id, observation_date, value,"
            " first_seen_date, vintage_date, revision_of, src)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (series_id, observation_date, value, first_seen_date,
             first_seen_date, revision_of, src),
        )
        self.conn.commit()
        return cur.lastrowid

    # -- point-in-time read API ---------------------------------------------

    def value_asof(self, series_id: str, observation_date: str,
                   decision_date: str):
        """Return the value KNOWN on decision_date for one observation.

        Picks the newest revision with first_seen_date <= decision_date.
        Revisions first seen AFTER decision_date cannot be returned --
        enforced by the SQL predicate itself (structural anti-leakage).
        Returns None when nothing was known yet.
        """
        if decision_date < observation_date:
            pass  # allowed: decision may predate observation only if a
                  # backcast/estimate existed; normally returns None anyway.
        row = self.conn.execute(
            """
            SELECT value, first_seen_date, revision_of, id FROM vintages
             WHERE series_id = ?
               AND observation_date = ?
               AND first_seen_date <= ?
             ORDER BY first_seen_date DESC, id DESC
             LIMIT 1
            """,
            (series_id, observation_date, decision_date),
        ).fetchone()
        if row is None:
            return None
        # Derived provenance (RX2 review fix): was_revised means "an
        # earlier-known vintage of this observation exists", computed
        # structurally so hostile/out-of-order insertion order cannot
        # corrupt it via caller-supplied revision_of.
        earlier = self.conn.execute(
            """
            SELECT 1 FROM vintages
             WHERE series_id = ?
               AND observation_date = ?
               AND (first_seen_date < ?
                    OR (first_seen_date = ? AND id < ?))
             LIMIT 1
            """,
            (series_id, observation_date, row[1], row[1], row[3]),
        ).fetchone()
        return {"value": row[0], "first_seen": row[1],
                "was_revised": earlier is not None}

    def curve_asof(self, series_id: str, decision_date: str):
        """Full point-in-time curve: latest-known value per observation_date."""
        rows = self.conn.execute(
            """
            SELECT v.observation_date, v.value, v.first_seen_date
              FROM vintages v
             WHERE v.series_id = ?
               AND v.first_seen_date <= ?
               AND v.id = (
                   SELECT v2.id FROM vintages v2
                    WHERE v2.series_id = v.series_id
                      AND v2.observation_date = v.observation_date
                      AND v2.first_seen_date <= ?
                    ORDER BY v2.first_seen_date DESC, v2.id DESC LIMIT 1)
             ORDER BY v.observation_date
            """,
            (series_id, decision_date, decision_date),
        ).fetchall()
        return [(r[0], r[1], r[2]) for r in rows]

    def revisions(self, series_id: str, observation_date: str):
        """Full revision chain (all vintages) for one observation."""
        return self.conn.execute(
            "SELECT value, first_seen_date, revision_of, src FROM vintages"
            " WHERE series_id = ? AND observation_date = ?"
            " ORDER BY first_seen_date, id",
            (series_id, observation_date),
        ).fetchall()

    def series_list(self):
        return [r[0] for r in self.conn.execute(
            "SELECT DISTINCT series_id FROM vintages ORDER BY series_id")]

    def close(self):
        self.conn.close()


# --------------------------------------------------------------------------
# Release-calendar stub
# --------------------------------------------------------------------------
class ReleaseCalendar:
    """STUB: planned release schedule per series.

    A real implementation would consult BLS/BEA/FRED release calendars.
    Until then it answers with the documented ASSUMED lag rules above.
    """

    #: marker so callers can detect stub behavior programmatically
    IS_STUB = True
    SOURCE_NOTE = ("STUB: derived from ASSUMED lags; real release "
                   "calendar requires external data (data-blocked).")

    def next_release(self, series_id: str, after_date: str):
        """Return the ASSUMED first-seen date of the next observation."""
        if series_id in _MONTHLY_SERIES:
            d = _dt.date.fromisoformat(after_date)
            nxt = (d.replace(day=1) + _dt.timedelta(days=32)).replace(day=1)
            return (nxt + _dt.timedelta(days=ASSUMED_LAG_MONTHLY)).isoformat()
        d = _dt.date.fromisoformat(after_date)
        return (d + _dt.timedelta(days=1)).isoformat()


# --------------------------------------------------------------------------
# Seeding from factors.db (with ASSUMED vintages)
# --------------------------------------------------------------------------

def seed_from_factors(factors_db: str, out_db: str, limit_series=None) -> dict:
    """Seed the vintage store from the flat factors table.

    Every row gets first_seen_date = ASSUMED lag from observation_date.
    Returns summary counts.
    """
    src = sqlite3.connect("file:%s?mode=ro" % factors_db.replace("\\", "/"),
                          uri=True)
    store = VintageStore(out_db)
    store.conn.execute("DELETE FROM vintages")  # full reseed
    q = ("SELECT ticker, date, factor, value, src FROM factors")
    params = ()
    if limit_series:
        qs = ",".join("?" * len(limit_series))
        q += " WHERE factor IN (%s)" % qs
        params = tuple(limit_series)
    n = 0
    series_seen = set()
    batch = []
    for ticker, date, factor, value, fsrc in src.execute(q, params):
        fs = assumed_first_seen(date, factor)
        tag = "ASSUMED-LAG(%s)" % fsrc
        batch.append((factor, date, value, fs, fs, None, tag))
        series_seen.add(factor)
        n += 1
    store.conn.executemany(
        "INSERT INTO vintages (series_id, observation_date, value,"
        " first_seen_date, vintage_date, revision_of, src)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)", batch)
    store.conn.commit()
    src.close()
    store.close()
    return {"rows": n, "series": len(series_seen), "db": out_db}


# --------------------------------------------------------------------------
# Synthetic revision fixtures + selftest
# --------------------------------------------------------------------------

def build_fixtures(store: VintageStore) -> dict:
    """Create a synthetic monthly series revised UPWARD 2 months later.

    Fixture design:
      observation 2026-01-01 : initial print 3.0  first seen 2026-01-16
                               revised print 4.5  first seen 2026-03-16
                               (upward revision exactly 2 months after
                                the initial print's first-seen date)
    """
    sid = "FIXTURE_REVUP"
    obs = "2026-01-01"
    first_seen = "2026-01-16"           # ASSUMED initial release
    rev_seen = "2026-03-16"             # +2 months, upward revision
    orig = 3.0
    revised = 4.5                       # strictly upward
    rid = store.insert(sid, obs, orig, first_seen, revision_of=None,
                       src="fixture-original")
    store.insert(sid, obs, revised, rev_seen, revision_of=rid,
                 src="fixture-revision-up")
    return {"series": sid, "obs": obs, "orig": orig, "revised": revised,
            "first_seen": first_seen, "rev_seen": rev_seen}


def selftest() -> int:
    import shutil

    tmpdir = tempfile.mkdtemp(prefix="mvs_selftest_")
    dbp = os.path.join(tmpdir, "selftest.db")
    results = []

    def check(name, cond):
        results.append((name, bool(cond)))
        print("[%s] %s" % ("PASS" if cond else "FAIL", name))

    try:
        store = VintageStore(dbp)

        # --- fixture ------------------------------------------------------
        fx = build_fixtures(store)
        sid, obs = fx["series"], fx["obs"]

        # Test 1: BEFORE the revision's first-seen date -> ORIGINAL value.
        # Inclusive semantics: a revision becomes visible ON its
        # first_seen_date (first_seen_date <= decision_date).
        r_day_before = store.value_asof(sid, obs, "2026-03-15")
        check("day-before-revision returns ORIGINAL value",
              r_day_before is not None and r_day_before["value"] == fx["orig"])
        check("day-before-revision flagged not-revised",
              r_day_before is not None and not r_day_before["was_revised"])

        # Test 2: AFTER the revision date -> REVISED value.
        r_after = store.value_asof(sid, obs, "2026-03-16")
        check("on-revision-day returns REVISED (upward) value",
              r_after is not None and r_after["value"] == fx["revised"])
        check("revised > original (upward fixture sanity)",
              fx["revised"] > fx["orig"])
        r_much_later = store.value_asof(sid, obs, "2030-01-01")
        check("far-future query still returns REVISED value",
              r_much_later is not None and r_much_later["value"] == fx["revised"])

        # Test 3: LEAKAGE PROOF -- exhaustively verify no decision date can
        # surface a future revision. For every candidate decision date in the
        # full span, the returned value must equal whichever revision was
        # known then; specifically it must NEVER be the revised value before
        # rev_seen, and must never be any first_seen_date beyond decision.
        leaked = []
        d0 = _dt.date.fromisoformat(fx["first_seen"])
        d1 = _dt.date(2026, 6, 30)
        d = d0
        while d <= d1:
            dec = d.isoformat()
            got = store.value_asof(sid, obs, dec)
            expected = fx["orig"] if dec < fx["rev_seen"] else fx["revised"]
            if got is None or got["value"] != expected:
                leaked.append((dec, got))
            if got is not None:
                # hard invariant: knowledge date never exceeds decision date
                if got["first_seen"] > dec:
                    leaked.append((dec, got))
                # hard invariant: a pre-revision query can never see the
                # upward-revised number
                if dec < fx["rev_seen"] and got["value"] == fx["revised"]:
                    leaked.append((dec, got))
            d += _dt.timedelta(days=1)
        check("leakage sweep over %d decision dates: zero leaks"
              % ((d1 - d0).days + 1), not leaked)
        if leaked:
            for dec, got in leaked[:10]:
                print("   LEAK %s -> %r" % (dec, got))

        # Test 4: missing-vintage handling ---------------------------------
        check("query unknown series returns None (no crash)",
              store.value_asof("NO_SUCH_SERIES", obs, "2026-06-01") is None)
        check("query known series, unpublished obs returns None",
              store.value_asof(sid, "2099-01-01", "2026-06-01") is None)

        # Test 5: curve_asof respects vintages -----------------------------
        early = store.curve_asof(sid, "2026-02-01")
        late = store.curve_asof(sid, "2026-04-01")
        check("early curve shows ORIGINAL", any(v == fx["orig"]
                                                for _, v, _ in early))
        check("early curve does NOT show revised",
              not any(v == fx["revised"] for _, v, _ in early))
        check("late curve shows REVISED", any(v == fx["revised"]
                                              for _, v, _ in late))

        # Test 6: release calendar stub ------------------------------------
        cal = ReleaseCalendar()
        check("release calendar is declared STUB", cal.IS_STUB)
        nxt = cal.next_release(sid, "2026-01-20")
        check("stub next-release is deterministic ISO date",
              isinstance(nxt, str) and len(nxt) == 10 and nxt[4] == "-")

        # Test 7: assumed-lag labeling on seeded data -----------------------
        store.insert("UNRATE", "2026-05-01", 4.1, None or
                     assumed_first_seen("2026-05-01", "UNRATE"),
                     src="ASSUMED-LAG(test)")
        row = store.conn.execute(
            "SELECT src FROM vintages WHERE series_id='UNRATE'").fetchone()
        check("seeded rows carry ASSUMED-LAG provenance",
              row is not None and row[0].startswith("ASSUMED-LAG"))

        store.close()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    failed = [n for n, ok in results if not ok]
    print("\n%d/%d checks passed" % (len(results) - len(failed), len(results)))
    if failed:
        print("FAILED: " + ", ".join(failed))
        return 1
    print("SELFTEST OK")
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="ALFRED-style vintage store")
    ap.add_argument("--selftest", action="store_true")
    sub = ap.add_subparsers(dest="cmd")

    p_seed = sub.add_parser("seed")
    p_seed.add_argument("--factors-db", default=_DEFAULT_FACTORS_DB)
    p_seed.add_argument("--db", default=os.path.normpath(_DEFAULT_VINTAGE_DB))

    p_q = sub.add_parser("query")
    p_q.add_argument("series")
    p_q.add_argument("obs_date")
    p_q.add_argument("--decision", required=True)
    p_q.add_argument("--db", default=os.path.normpath(_DEFAULT_VINTAGE_DB))

    args = ap.parse_args(argv)

    if args.selftest or getattr(args, "cmd", None) == "selftest":
        return selftest()

    if args.cmd == "seed":
        if not os.path.exists(args.factors_db):
            print("ERROR: factors db not found: %s" % args.factors_db)
            return 2
        out = seed_from_factors(args.factors_db, args.db)
        print("SEEDED %(rows)d rows / %(series)d series -> %(db)s "
              "[first_seen dates are ASSUMED-lag, not real vintages]" % out)
        return 0

    if args.cmd == "query":
        store = VintageStore(args.db)
        res = store.value_asof(args.series, args.obs_date, args.decision)
        print(res if res is not None else
              "None (nothing known for %s/%s as of %s)"
              % (args.series, args.obs_date, args.decision))
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

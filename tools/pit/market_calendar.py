#!/usr/bin/env python3
"""D9: Market calendar + timezone normalization.

US equity trading-day calendar derived from SPY daily bars in factors.db,
plus pure-function ET <-> UTC timezone normalization.

Ground truth for this corpus
----------------------------
The trading calendar is DERIVED FROM DATA, not from a hardcoded holiday
table. The set of SPY bar dates in factors.db (read-only) is the ground
truth for "which days this corpus considers US equity trading days".
factors.db locations checked, in order:
    1. <repo>/Efforts/osanwe-v2-overhaul/_work/factors.db
    2. <repo>/factors.db
The DB is opened read-only ('file:...?mode=ro'). If neither exists or the
bars table has no SPY rows, the module falls back to an embedded static
list of NYSE full-session holidays for 2020-2030 (weekends excluded by
rule). The fallback is documented as APPROXIMATE; the DB-derived calendar
is authoritative whenever it is available.

Known limitations
-----------------
NYSE HALF-DAYS CANNOT BE DETECTED FROM CLOSES. On early-close days
(Black Friday, Christmas Eve when it trades, July 3rd before a weekend,
etc.) the exchange still prints a daily close bar, so a close-based
calendar sees them as full trading days. This module therefore reports
half-days as regular trading days and makes NO attempt to detect them.
Any consumer needing session end times must not rely on this module.

Daily-bar convention
--------------------
next_open_assumption(date): daily-bar systems have no intraday open
timestamps. By explicit convention of this corpus, "the next tradable
close" IS the next available calendar bar: for a date on or after the
last bar, prev_close() returns the last known SPY bar date (stale data
is returned rather than an error, and callers should treat staleness as
a PIT hazard); otherwise the next trading day strictly AFTER `date`.

Timezone normalization
----------------------
Pure functions convert naive ET <-> UTC using stdlib zoneinfo
("America/New_York"), which handles DST including spring-forward and
fall-back edges. An embedded DST rule table for 2020-2030 US/Eastern is
included ONLY as documentation/cross-check (used by selftest to verify
zoneinfo agrees with the published rules); all real conversion goes
through zoneinfo. Ambiguous fall-back local times resolve to the EARLIER
(fold=0) EDT instant, matching common EDGAR-acceptance interpretation;
nonexistent spring-forward times (02:00-02:59 on the March switch date)
are shifted FORWARD ACROSS THE GAP by its width (one hour), i.e.
02:30 becomes 03:30 EDT (= 07:30Z).

Usage:
    python market_calendar.py selftest

ASCII only, stdlib only, no network, no git.
"""

import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parents[2]

DB_CANDIDATES = [
    REPO_ROOT / "Efforts" / "osanwe-v2-overhaul" / "_work" / "factors.db",
    REPO_ROOT / "factors.db",
]

ET = ZoneInfo("America/New_York")

# ---------------------------------------------------------------------------
# Embedded DST rule table, US/Eastern, 2020-2030.
# Rule (Energy Policy Act 2005, still in force): DST begins at 02:00 local
# STANDARD time on the second Sunday of March ("spring forward" -> 03:00
# EDT) and ends at 02:00 local DAYLIGHT time on the first Sunday of
# November ("fall back" -> 01:00 EST). Used only to cross-check zoneinfo.
# Each entry: (year, dst_start_date, dst_end_date)
DST_RULE_TABLE = [
    (2020, date(2020, 3, 8), date(2020, 11, 1)),
    (2021, date(2021, 3, 14), date(2021, 11, 7)),
    (2022, date(2022, 3, 13), date(2022, 11, 6)),
    (2023, date(2023, 3, 12), date(2023, 11, 5)),
    (2024, date(2024, 3, 10), date(2024, 11, 3)),
    (2025, date(2025, 3, 9), date(2025, 11, 2)),
    (2026, date(2026, 3, 8), date(2026, 11, 1)),
    (2027, date(2027, 3, 14), date(2027, 11, 7)),
    (2028, date(2028, 3, 12), date(2028, 11, 5)),
    (2029, date(2029, 3, 11), date(2029, 11, 4)),
    (2030, date(2030, 3, 10), date(2030, 11, 3)),
]

# Fallback holiday table: NYSE full-session closures 2020-2030 (weekdays
# only; weekends handled separately). APPROXIMATE ground truth, used only
# when no factors.db with SPY bars is reachable.
FALLBACK_HOLIDAYS_YYYYMMDD = frozenset("""
    20200101 20200120 20200217 20200410 20200525 20200703 20200907
    20201126 20201225
    20210101 20210118 20210215 20210402 20210531 20210705 20210906
    20211125 20211224
    20220117 20220221 20220415 20220530 20220620 20220704 20220905
    20221124 20221226
    20230102 20230116 20230220 20230407 20230529 20230619 20230704
    20230904 20231123 20231225
    20240101 20240115 20240219 20240329 20240527 20240619 20240704
    20240902 20241128 20241225
    20250101 20250109 20250120 20250217 20250418 20250526 20250619
    20250704 20250901 20251127 20251225
    20260101 20260119 20260216 20260403 20260525 20260619 20260703
    20260907 20261126 20261225
    20270101 20270118 20270215 20270326 20270531 20270705 20270906
    20271125 20271224
    20280117 20280221 20280414 20280529 20280704 20280904 20281123
    20281225
    20290101 20290115 20290219 20290330 20290528 20290704 20290903
    20291122 20291225
    20300101 20300121 20300218 20300419 20300527 20300619 20300704
    20300902 20301128 20301225
""".split())

# ---------------------------------------------------------------------------
# Calendar loading


def _open_db_readonly(path):
    uri = "file:" + str(path).replace("\\", "/") + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def load_trading_days(db_path=None):
    """Return sorted list of datetime.date for every SPY bar in factors.db."""
    candidates = [db_path] if db_path else DB_CANDIDATES
    days = None
    for cand in candidates:
        if not Path(cand).exists():
            continue
        try:
            conn = _open_db_readonly(cand)
        except sqlite3.Error:
            continue
        try:
            rows = conn.execute(
                "SELECT DISTINCT date FROM bars WHERE ticker = 'SPY' "
                "ORDER BY date"
            ).fetchall()
            if rows:
                days = [date.fromisoformat(r[0][:10]) for r in rows]
                break
        except sqlite3.Error:
            continue
        finally:
            conn.close()
    return days


def _fallback_calendar():
    """Static approximate calendar 2020-2030: weekdays minus holidays."""
    out = []
    d = date(2020, 1, 1)
    while d <= date(2030, 12, 31):
        iso = d.strftime("%Y%m%d")
        if d.weekday() < 5 and iso not in FALLBACK_HOLIDAYS_YYYYMMDD:
            out.append(d)
        d += timedelta(days=1)
    return out


class _Calendar:
    """Sorted trading-day set with bisect helpers."""

    def __init__(self):
        days = load_trading_days()
        self.source = "spy-bars-factors-db"
        if days is None:
            self.source = "static-fallback-holidays-approximate"
            days = _fallback_calendar()
        self.days = days
        import bisect

        self._bisect = bisect

    def contains(self, d):
        i = self._bisect.bisect_left(self.days, d)
        return i < len(self.days) and self.days[i] == d

    def next_after(self, d, strict=True):
        """First trading day > d (strict) or >= d (strict=False)."""
        lo = self._bisect.bisect_right(self.days, d) if strict \
            else self._bisect.bisect_left(self.days, d)
        return self.days[lo] if lo < len(self.days) else None

    def prev_before(self, d, strict=True):
        """Last trading day < d (strict) or <= d (strict=False)."""
        hi = self._bisect.bisect_left(self.days, d) if strict \
            else self._bisect.bisect_right(self.days, d)
        return self.days[hi - 1] if hi > 0 else None


_CAL = None


def _cal():
    global _CAL
    if _CAL is None:
        _CAL = _Calendar()
    return _CAL


def reset_cache():
    """Drop cached calendar so a refreshed factors.db is re-read."""
    global _CAL
    _CAL = None


def calendar_source():
    """'spy-bars-factors-db' or 'static-fallback-holidays-approximate'."""
    return _cal().source


# ---------------------------------------------------------------------------
# Public calendar API


def parse_day(value):
    """Accept datetime.date, datetime, or 'YYYY-MM-DD' string -> date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def is_trading_day(d):
    """True if d (date/'YYYY-MM-DD') is a known US equity trading day.

    Ground truth: SPY bar dates in factors.db (read-only). Half-days
    count as trading days and are indistinguishable from full sessions
    (see module docstring limitation).
    """
    return _cal().contains(parse_day(d))


def prev_close(d):
    """Date of the last trading day's close on or BEFORE d.

    Returns the last SPY-bar date <= d. For dates beyond the last bar,
    returns the last bar (stale-by-convention; see docstring).
    Returns None only if d precedes the first bar in the corpus.
    """
    dd = parse_day(d)
    hit = _cal().prev_before(dd, strict=False)
    if hit is not None:
        return hit
    return _cal().prev_before(dd, strict=True)


def next_open_assumption(d):
    """Next tradable close under the DAILY-BAR convention.

    Convention (documented, deliberate): daily-bar systems treat "next
    tradable close" as the NEXT CALENDAR BAR. If d itself is a trading
    day, that same day's close bar is assumed available at/after the
    session (no intraday timing knowledge); otherwise the first trading
    day strictly after d. Returns None if beyond the last bar.
    """
    dd = parse_day(d)
    return _cal().next_after(dd, strict=False)


# ---------------------------------------------------------------------------
# Timezone normalization (pure functions)


def et_to_utc(naive_et):
    """Naive ET datetime -> aware UTC datetime.

    - Ambiguous local times during fall-back (01:00-01:59 Nov) resolve to
      the EARLIER EDT instant (fold=0).
    - Nonexistent local times during spring-forward (02:00-02:59 Mar) are
      shifted forward across the gap by its width (1h): e.g. 02:30 ->
      03:30 EDT (= 07:30Z).
    """
    dt = naive_et.replace(tzinfo=ET, fold=0)
    # Detect nonexistent spring-forward time: UTC round-trip lands on a
    # different wall clock than the input.
    roundtrip = dt.astimezone(timezone.utc).astimezone(ET)
    if roundtrip.replace(tzinfo=None) != naive_et:
        delta = roundtrip.utcoffset() - dt.utcoffset()
        dt = dt + delta  # clamp forward across the gap
    return dt.astimezone(timezone.utc)


def utc_to_et(aware_utc):
    """Aware UTC datetime -> aware America/New_York datetime."""
    if aware_utc.tzinfo is None:
        raise ValueError("utc_to_et expects an AWARE UTC datetime")
    return aware_utc.astimezone(ET)


def et_iso_to_utc_iso(s):
    """'YYYY-MM-DDTHH:MM:SS' naive ET -> '...Z' ISO UTC string."""
    dt = et_to_utc(datetime.fromisoformat(s))
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_iso_to_et_iso(s):
    """ISO UTC string -> naive ET 'YYYY-MM-DDTHH:MM:SS' string."""
    s = s.strip().replace("Z", "+00:00")
    dt = utc_to_et(datetime.fromisoformat(s))
    return dt.replace(tzinfo=None).isoformat()


# ---------------------------------------------------------------------------
# Selftest


def selftest():
    failures = []
    cal = _cal()

    def check(name, cond):
        print(("PASS" if cond else "FAIL") + ": " + name)
        if not cond:
            failures.append(name)

    # -- calendar source sanity ------------------------------------------
    src = cal.source
    print("calendar source: " + src)
    if src == "spy-bars-factors-db":
        check("SPY calendar covers 2021-2026 window",
              cal.contains(date(2021, 8, 24)) and cal.contains(date(2026, 8, 25)))
    else:
        check("fallback covers 2020-2030", cal.contains(date(2025, 1, 2)))

    # -- weekend rejection -------------------------------------------------
    sat = date(2026, 8, 22)
    sun = date(2026, 8, 23)
    check("Saturday 2026-08-22 rejected", not is_trading_day(sat))
    check("Sunday 2026-08-23 rejected", not is_trading_day(sun))

    # -- holiday rejection --------------------------------------------------
    # New Year's Day 2026 (Thu) and Independence Day observance 2026-07-03.
    if src == "spy-bars-factors-db":
        check("New Year 2026-01-01 rejected", not is_trading_day("2026-01-01"))
        check("July 4th observance 2026-07-03 rejected",
              not is_trading_day("2026-07-03"))
        check("Christmas 2025-12-25 rejected", not is_trading_day("2025-12-25"))
        check("MLK 2026-01-19 rejected", not is_trading_day("2026-01-19"))
    else:
        check("fallback rejects 2026-01-01", not is_trading_day("2026-01-01"))

    # -- ordinary trading day accepted --------------------------------------
    fri = date(2026, 8, 21)
    check("Friday 2026-08-21 accepted", is_trading_day(fri))

    # -- prev_close ---------------------------------------------------------
    pc_sat = prev_close(sat)
    check("prev_close(Sat 2026-08-22) == Fri 2026-08-21", pc_sat == fri)
    pc_mon = prev_close(date(2026, 8, 24))  # Monday (itself a trading day)
    check("prev_close(Mon trading day) == Mon", pc_mon == date(2026, 8, 24))
    # Holiday + weekend chain: 2026-07-03 (Fri, July-4th observance) has
    # no bar, and Sat 2026-07-04 / Sun 2026-07-05 are weekends, so the
    # prior close before Fri is Thursday 2026-07-02.
    check("prev_close(Fri holiday) == Thu 2026-07-02",
          prev_close(date(2026, 7, 3)) == date(2026, 7, 2))
    check("prev_close(Sat after holiday) == Thu 2026-07-02",
          prev_close(date(2026, 7, 4)) == date(2026, 7, 2))
    # Last bar in corpus: prev_close beyond the end returns the stale
    # last bar rather than an error.
    last_bar = cal.days[-1]
    check("prev_close(beyond last bar) == last bar (stale convention)",
          prev_close(last_bar + timedelta(days=10)) == last_bar)
    # holiday-adjacent: 2026-01-01 (Thu) is a holiday -> prior bar is
    # Wednesday 2025-12-31.
    check("prev_close(New Year holiday) == 2025-12-31",
          prev_close(date(2026, 1, 1)) == date(2025, 12, 31))
    check("prev_close(trading day) == itself", prev_close(fri) == fri)

    # -- next_open_assumption -------------------------------------------------
    no_weekend = next_open_assumption(sat)
    check("next_open(Sat) == Mon 2026-08-24", no_weekend == date(2026, 8, 24))
    check("next_open(trading day) == same day (bar convention)",
          next_open_assumption(fri) == fri)

    # -- DST rule table vs zoneinfo agreement ------------------------------
    def second_sunday_march(y):
        d = date(y, 3, 1)
        return d + timedelta(days=(6 - d.weekday()) % 7 + 7)

    def first_sunday_nov(y):
        d = date(y, 11, 1)
        return d + timedelta(days=(6 - d.weekday()) % 7)

    ok = True
    for y, start, end in DST_RULE_TABLE:
        if start != second_sunday_march(y) or end != first_sunday_nov(y):
            ok = False
        # zoneinfo offset checks at noon (unambiguous hour)
        noon_start = datetime(y, start.month, start.day, 12, tzinfo=ET)
        noon_end = datetime(y, end.month, end.day, 12, tzinfo=ET)
        if noon_start.utcoffset() != timedelta(hours=-4):
            ok = False
        if noon_end.utcoffset() != timedelta(hours=-5):
            ok = False
        # day before spring-forward is EST (-5); day after is EDT (-4)
        pre = datetime(y, start.month, start.day, 6, tzinfo=ET) - timedelta(days=1)
        if pre.utcoffset() != timedelta(hours=-5):
            ok = False
    check("embedded DST table matches computed rule & zoneinfo offsets", ok)

    # -- spring-forward conversion -------------------------------------------
    # 2026-03-08 02:30 ET does not exist -> shifted across the gap to
    # 03:30 EDT = 07:30Z.
    got = et_to_utc(datetime(2026, 3, 8, 2, 30))
    check("spring-forward nonexistent 02:30 shifts to 07:30Z",
          got == datetime(2026, 3, 8, 7, 30, tzinfo=timezone.utc))

    # Unambiguous hours around the edge still work.
    got = et_to_utc(datetime(2026, 3, 8, 1, 30))  # EST
    check("2026-03-08 01:30 EST -> 06:30Z",
          got == datetime(2026, 3, 8, 6, 30, tzinfo=timezone.utc))
    got = et_to_utc(datetime(2026, 3, 8, 3, 30))  # EDT
    check("2026-03-08 03:30 EDT -> 07:30Z",
          got == datetime(2026, 3, 8, 7, 30, tzinfo=timezone.utc))

    # -- fall-back conversion ---------------------------------------------------
    # 2025-11-02 01:30 occurs twice; fold=0 convention picks earlier EDT.
    got = et_to_utc(datetime(2025, 11, 2, 1, 30))
    check("fall-back ambiguous 01:30 -> earlier EDT 05:30Z",
          got == datetime(2025, 11, 2, 5, 30, tzinfo=timezone.utc))
    got = et_to_utc(datetime(2025, 11, 2, 5, 30))  # unambiguous EST
    check("2025-11-02 05:30 EST -> 10:30Z",
          got == datetime(2025, 11, 2, 10, 30, tzinfo=timezone.utc))

    # -- ISO string conversions incl. DST edge dates ------------------------
    # Round trips for REAL local times:
    pairs = [
        ("2026-03-08T05:30:00", "2026-03-08T09:30:00Z"),
        ("2025-11-02T01:30:00", "2025-11-02T05:30:00Z"),
        ("2024-07-04T09:30:00", "2024-07-04T13:30:00Z"),
        ("2023-12-25T23:59:59", "2023-12-26T04:59:59Z"),
        ("2021-11-07T01:15:00", "2021-11-07T05:15:00Z"),
    ]
    ok = True
    for et_s, utc_s in pairs:
        if et_iso_to_utc_iso(et_s) != utc_s or utc_iso_to_et_iso(utc_s) != et_s:
            ok = False
    check("ISO ET<->UTC round trips (incl. DST edges)", ok)
    # Nonexistent spring-forward time: forward conversion is defined
    # (02:30 -> 07:30Z) but the inverse is intentionally NOT identity --
    # it lands on 03:30, the shifted-across-the-gap wall clock.
    fwd = et_iso_to_utc_iso("2022-03-13T02:30:00")
    back = utc_iso_to_et_iso(fwd)
    check("spring-forward nonexistent time converts fwd and back "
          "(non-identity by convention)",
          fwd == "2022-03-13T07:30:00Z" and back == "2022-03-13T03:30:00")

    # -- read-only guarantee ----------------------------------------------------
    if Path(DB_CANDIDATES[0]).exists():
        mtime = DB_CANDIDATES[0].stat().st_mtime_ns
        reset_cache()
        _cal()
        check("factors.db untouched by calendar load",
              DB_CANDIDATES[0].stat().st_mtime_ns == mtime)

    print("")
    if failures:
        print("SELFTEST FAILED: %d failure(s)" % len(failures))
        for f in failures:
            print("  - " + f)
        return 1
    print("SELFTEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(selftest())

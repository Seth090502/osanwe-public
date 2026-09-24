"""FIS unattended scheduler (W2 -- scheduler battery).

WHY THIS MODULE EXISTS
----------------------
`shadow.py` grades a prediction as soon as its horizon has expired relative
to realized closes. It never asks whether the prediction record was
durably written BEFORE those closes existed. That gap allowed six records
created 2026-08-26 with info_cutoff 2026-07-01 / earliest_tradable
2026-07-02 to be graded 15 seconds later as if they were forecasts. See
`_work/fis-data/shadow-audit/temporal-audit.md`.

This module closes that gap. The controlling rule is provenance:

    A record is PROSPECTIVE only if it was created on or before the
    calendar date of its own earliest_tradable session AND strictly
    before that session's closing bell. Otherwise it is
    RETROSPECTIVE_BACKFILL, and it is PERMANENTLY ineligible for any
    prospective performance claim. There is no flag, parameter, config
    key, or environment variable that disables this. Do not add one.

DESIGN RULES
------------
* Standard library only. Zero network calls. ASCII only in all output.
* All internal times are timezone-aware UTC. External-facing timestamps
  are UTC ISO-8601 with an explicit trailing "Z".
* Time is injected via the `Clock` protocol. No code path in this module
  calls `datetime.now()` except `SystemClock`, which is the only
  wall-clock adapter and is not used by the tests.
* Writes are atomic (temp file + os.replace) and guarded by idempotency
  keys, so a partial run is neither lost nor double-applied.

Run:  python tools/fis/scheduler.py --once
      python tools/fis/scheduler.py --status
"""

import hashlib
import json
import math
import os
import random
import signal
import shutil
import sys
import tempfile
import threading
from datetime import date, datetime, timedelta, timezone

MODULE_VERSION = "fis-scheduler-w2-v1"

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))
DEFAULT_STATE_DIR = os.path.join(REPO_ROOT, "_work", "fis-data",
                                 "scheduler-state")
MODULE_PATH = os.path.abspath(__file__)

UTC = timezone.utc
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"

# --------------------------------------------------------------------------
# 0a. Temporal policy -- NOT OWNED HERE.
#
# This module decides WHEN things run. It does not get to decide WHAT a
# record means. The provenance rule used to live in this file, which made
# shadow.py (a domain component) import its financial semantics from the
# job runner -- a scheduler-to-domain inversion.
#
# The rule now lives in `temporal_policy.py`, a neutral shared domain
# component. This module imports it and re-exports the names its callers
# already use, so there is exactly one implementation. It also REGISTERS
# its richer calendar (year caches, holiday data) as the policy default,
# because the scheduler's calendar is the more complete session model --
# registration is a data contribution, not an ownership claim.
# --------------------------------------------------------------------------

if HERE not in sys.path:
    sys.path.insert(0, HERE)

import temporal_policy  # noqa: E402

from temporal_policy import (  # noqa: E402
    PROSPECTIVE,
    RETROSPECTIVE_BACKFILL,
    TEMPORAL_POLICY_VERSION,
    TemporalPolicyError,
    eastern_date,
    eastern_datetime,
    eastern_offset,
    eastern_to_utc,
    grade_eligibility_verdict,
    is_prospective_evidence as _tp_is_prospective_evidence,
    outcome_availability,
    prediction_eligibility_verdict,
    quarantine,
    quarantine_status_for,
)

# --- 0. Errors. Every failure mode gets a typed, machine-readable class.
# --------------------------------------------------------------------------

ERROR_CLASSES = (
    "SCHEDULER_ERROR",
    "CALENDAR_RANGE_ERROR",
    "DRIFT_REFUSAL",
    "GRADE_WITHOUT_PARENT",
    "STALE_DATA_BLOCKED",
    "MISSING_DATA_BLOCKED",
    "BACKFILL_RESTRICTION",
    "DEAD_LETTER",
    "PROVIDER_OUTAGE",
    "PROVIDER_TIMEOUT",
    "PROVIDER_RATE_LIMITED",
    "PROVIDER_DATA_MISSING",
    "SHUTDOWN",
    "MISSED_RUN_LIMIT",
)


class SchedulerError(Exception):
    ERROR_CLASS = "SCHEDULER_ERROR"

    def __init__(self, message, error_class=None, detail=None):
        Exception.__init__(self, message)
        self.message = message
        self.error_class = error_class or self.ERROR_CLASS
        self.detail = detail or {}

    def as_dict(self):
        return {"error_class": self.error_class, "message": self.message,
                "detail": self.detail}


class CalendarRangeError(SchedulerError):
    ERROR_CLASS = "CALENDAR_RANGE_ERROR"


class DriftRefusal(SchedulerError):
    ERROR_CLASS = "DRIFT_REFUSAL"


class GradeWithoutParentError(SchedulerError):
    ERROR_CLASS = "GRADE_WITHOUT_PARENT"


class StaleDataBlocked(SchedulerError):
    ERROR_CLASS = "STALE_DATA_BLOCKED"


class MissingDataBlocked(SchedulerError):
    ERROR_CLASS = "MISSING_DATA_BLOCKED"


class BackfillRestrictionError(SchedulerError):
    ERROR_CLASS = "BACKFILL_RESTRICTION"


class DeadLetterError(SchedulerError):
    ERROR_CLASS = "DEAD_LETTER"


class ShutdownError(SchedulerError):
    ERROR_CLASS = "SHUTDOWN"


class MissedRunLimitError(SchedulerError):
    ERROR_CLASS = "MISSED_RUN_LIMIT"


class ProviderError(SchedulerError):
    ERROR_CLASS = "PROVIDER_OUTAGE"
    retryable = True

    def __init__(self, message, error_class=None, detail=None,
                 retryable=None):
        SchedulerError.__init__(self, message, error_class=error_class,
                                detail=detail)
        if retryable is not None:
            self.retryable = retryable


class ProviderOutage(ProviderError):
    ERROR_CLASS = "PROVIDER_OUTAGE"
    retryable = True


class ProviderTimeout(ProviderError):
    ERROR_CLASS = "PROVIDER_TIMEOUT"
    retryable = True


class ProviderRateLimited(ProviderError):
    ERROR_CLASS = "PROVIDER_RATE_LIMITED"
    retryable = True


class ProviderDataMissing(ProviderError):
    ERROR_CLASS = "PROVIDER_DATA_MISSING"
    retryable = False


# --------------------------------------------------------------------------
# 1. Time: injected clock, UTC ISO-8601 with explicit Z
# --------------------------------------------------------------------------

def require_utc(dt):
    """Reject naive datetimes. Silence here is how temporal bugs are born."""
    if not isinstance(dt, datetime):
        raise TypeError("expected datetime, got %r" % (type(dt).__name__,))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("naive datetime rejected: %r" % (dt,))
    return dt.astimezone(UTC)


def iso_z(dt):
    """UTC ISO-8601 with explicit trailing Z. Second resolution."""
    return require_utc(dt).strftime(ISO_FMT)


def parse_iso_z(text):
    if not isinstance(text, str):
        raise ValueError("timestamp must be a string, got %r"
                         % (type(text).__name__,))
    if not text.endswith("Z"):
        raise ValueError("timestamp must end with Z: %r" % (text,))
    return datetime.strptime(text, ISO_FMT).replace(tzinfo=UTC)


def is_iso_z(text):
    try:
        parse_iso_z(text)
        return True
    except Exception:
        return False


class Clock(object):
    """Clock protocol. All scheduler code takes time from here, never
    from `datetime.now()`."""

    def now(self):
        raise NotImplementedError

    def sleep(self, seconds):
        raise NotImplementedError


class SystemClock(Clock):
    """The one and only wall-clock adapter. Not used on test paths."""

    def now(self):
        return datetime.now(UTC)

    def sleep(self, seconds):
        import time
        time.sleep(seconds)


class FakeClock(Clock):
    """Deterministic clock. `sleep` advances virtual time and records the
    delay so backoff schedules are assertable."""

    def __init__(self, at):
        if isinstance(at, str):
            self._at = parse_iso_z(at)
        elif isinstance(at, datetime):
            self._at = require_utc(at)
        else:
            raise TypeError("FakeClock needs an ISO string or datetime")
        self.sleeps = []

    def now(self):
        return self._at

    def set(self, at):
        self._at = require_utc(at) if isinstance(at, datetime) \
            else parse_iso_z(at)
        return self._at

    def advance(self, seconds=0, **kwargs):
        self._at = self._at + timedelta(seconds=seconds, **kwargs)
        return self._at

    def sleep(self, seconds):
        if seconds < 0:
            raise ValueError("negative sleep: %r" % (seconds,))
        self.sleeps.append(seconds)
        self._at = self._at + timedelta(seconds=seconds)
        return self._at


# --------------------------------------------------------------------------
# 2. US/Eastern DST. Implemented from the statutory rule so this module
#    never needs a tz database lookup and never touches the network.
#    DST begins 02:00 local (07:00Z) on the 2nd Sunday of March.
#    DST ends   02:00 local (06:00Z) on the 1st Sunday of November.
# --------------------------------------------------------------------------

EST = timedelta(hours=-5)
EDT = timedelta(hours=-4)


def _nth_weekday(year, month, weekday, n):
    """1-indexed nth `weekday` (0=Mon) of the given month."""
    first = date(year, month, 1)
    first_hit = first + timedelta(days=(weekday - first.weekday()) % 7)
    return first_hit + timedelta(weeks=(n - 1))


def dst_start_utc(year):
    """Instant DST begins: 02:00 EST == 07:00Z."""
    d = _nth_weekday(year, 3, 6, 2)  # 2nd Sunday of March
    return datetime(d.year, d.month, d.day, 7, 0, 0, tzinfo=UTC)


def dst_end_utc(year):
    """Instant DST ends: 02:00 EDT == 06:00Z."""
    d = _nth_weekday(year, 11, 6, 1)  # 1st Sunday of November
    return datetime(d.year, d.month, d.day, 6, 0, 0, tzinfo=UTC)


def eastern_offset(dt_utc):
    """Return EST or EDT offset in force at the given UTC instant."""
    dt = require_utc(dt_utc)
    year = dt.year
    start = dst_start_utc(year)
    end = dst_end_utc(year)
    return EDT if (start <= dt < end) else EST


def eastern_datetime(dt_utc):
    """Naive US/Eastern wall clock for a UTC instant."""
    dt = require_utc(dt_utc)
    return (dt + eastern_offset(dt)).replace(tzinfo=None)


def eastern_date(dt_utc):
    """US/Eastern calendar date for a UTC instant. All session math uses
    Eastern dates, never UTC dates."""
    return eastern_datetime(dt_utc).date()


def eastern_to_utc(naive_local):
    """Map a naive US/Eastern wall-clock time to UTC.

    Returns (utc_datetime, note). `note` is one of:
      "normal"             -- unambiguous
      "ambiguous_first"    -- repeated hour at fall-back; EDT (first) chosen
      "nonexistent_snapped"-- skipped hour at spring-forward; snapped to the
                              transition instant (the market was shut anyway)
    """
    if not isinstance(naive_local, datetime) or naive_local.tzinfo is not None:
        raise TypeError("eastern_to_utc needs a naive datetime")
    early = (naive_local - EST).replace(tzinfo=UTC)
    late = (naive_local - EDT).replace(tzinfo=UTC)
    ok_early = (eastern_offset(early) == EST)
    ok_late = (eastern_offset(late) == EDT)
    if ok_early and ok_late:
        return late, "ambiguous_first"
    if ok_early:
        return early, "normal"
    if ok_late:
        return late, "normal"
    # Skipped wall-clock hour: snap forward to the transition instant.
    snap = dst_start_utc(naive_local.year)
    return snap, "nonexistent_snapped"


# --------------------------------------------------------------------------
# 3. Market calendar: trading days + hardcoded NYSE holidays 2026-2027.
#    No network. Unsupported years fail closed.
# --------------------------------------------------------------------------

MON, TUE, WED, THU, FRI, SAT, SUN = range(7)

NYSE_HOLIDAYS = {
    2026: {
        "2026-01-01": "New Year's Day",
        "2026-01-19": "Martin Luther King Jr. Day",
        "2026-02-16": "Washington's Birthday",
        "2026-04-03": "Good Friday",
        "2026-05-25": "Memorial Day",
        "2026-06-19": "Juneteenth National Independence Day",
        "2026-07-03": "Independence Day (observed)",
        "2026-09-07": "Labor Day",
        "2026-11-26": "Thanksgiving Day",
        "2026-12-25": "Christmas Day",
    },
    2027: {
        "2027-01-01": "New Year's Day",
        "2027-01-18": "Martin Luther King Jr. Day",
        "2027-02-15": "Washington's Birthday",
        "2027-03-26": "Good Friday",
        "2027-05-31": "Memorial Day",
        "2027-06-21": "Juneteenth National Independence Day (observed)",
        "2027-07-05": "Independence Day (observed)",
        "2027-09-06": "Labor Day",
        "2027-11-25": "Thanksgiving Day",
        "2027-12-24": "Christmas Day (observed)",
    },
}

# 13:00 local early closes (half sessions).
EARLY_CLOSES = {
    "2026-11-27": "day after Thanksgiving",
    "2026-12-24": "Christmas Eve",
    "2027-11-26": "day after Thanksgiving",
    "2027-12-24": "Christmas Eve",
}

CALENDAR_MIN_YEAR = min(NYSE_HOLIDAYS)
CALENDAR_MAX_YEAR = max(NYSE_HOLIDAYS)


def _coerce_date(value):
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return eastern_date(value)
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    raise TypeError("cannot coerce %r to date" % (value,))


class MarketCalendar(object):
    """Trading-day arithmetic over a hardcoded holiday set."""

    def __init__(self, holidays=None, early_closes=None):
        self.holidays = holidays if holidays is not None else NYSE_HOLIDAYS
        self.early_closes = (early_closes if early_closes is not None
                             else EARLY_CLOSES)
        self._cache = {}

    # -- guards -----------------------------------------------------------
    def _check_year(self, year):
        if year not in self.holidays:
            raise CalendarRangeError(
                "no holiday set for year %d (supported %d-%d); refusing to "
                "guess -- extend NYSE_HOLIDAYS" % (year, CALENDAR_MIN_YEAR,
                                                   CALENDAR_MAX_YEAR),
                detail={"year": year})

    def holiday_name(self, day):
        d = _coerce_date(day)
        self._check_year(d.year)
        return self.holidays[d.year].get(d.isoformat())

    def is_holiday(self, day):
        return self.holiday_name(day) is not None

    def is_weekend(self, day):
        return _coerce_date(day).weekday() in (SAT, SUN)

    def is_trading_day(self, day):
        d = _coerce_date(day)
        return (not self.is_weekend(d)) and (not self.is_holiday(d))

    def is_early_close(self, day):
        return _coerce_date(day).isoformat() in self.early_closes

    # -- session arithmetic ----------------------------------------------
    def trading_days(self, start, end):
        """Inclusive list of trading sessions in [start, end]."""
        s = _coerce_date(start)
        e = _coerce_date(end)
        if e < s:
            return []
        for y in range(s.year, e.year + 1):
            self._check_year(y)
        out = []
        cur = s
        while cur <= e:
            if self.is_trading_day(cur):
                out.append(cur)
            cur = cur + timedelta(days=1)
        return out

    def next_trading_day(self, day, inclusive=False):
        d = _coerce_date(day)
        cur = d if inclusive else d + timedelta(days=1)
        for _ in range(400):
            if self.is_trading_day(cur):
                return cur
            cur = cur + timedelta(days=1)
        raise CalendarRangeError("no trading day found after %s" % (d,))

    def previous_trading_day(self, day, inclusive=False):
        d = _coerce_date(day)
        cur = d if inclusive else d - timedelta(days=1)
        for _ in range(400):
            if self.is_trading_day(cur):
                return cur
            cur = cur - timedelta(days=1)
        raise CalendarRangeError("no trading day found before %s" % (d,))

    def nth_trading_day(self, start, n):
        """0-indexed: nth_trading_day(d, 0) == d if d is a session."""
        cur = self.next_trading_day(start, inclusive=True)
        for _ in range(n):
            cur = self.next_trading_day(cur)
        return cur

    def index_of(self, sessions, day):
        d = _coerce_date(day)
        if d not in sessions:
            raise CalendarRangeError(
                "%s is not a trading session in the supplied window" % (d,))
        return sessions.index(d)

    def supported_bounds(self):
        return (date(min(self.holidays), 1, 1),
                date(max(self.holidays), 12, 31))

    def trading_days_bounded(self, end, lookback_days=400):
        """Sessions ending at `end`, clamped to the years this calendar
        actually knows. Never silently invents a year's holiday set."""
        lo, hi = self.supported_bounds()
        e = _coerce_date(end)
        start = e - timedelta(days=lookback_days)
        if start < lo:
            start = lo
        if e > hi:
            e = hi
        return self.trading_days(start, e)

    def sessions_around(self, day, back=40, forward=40):
        s = _coerce_date(day) - timedelta(days=back)
        e = _coerce_date(day) + timedelta(days=forward)
        return self.trading_days(s, e)

    # -- session clock ----------------------------------------------------
    def market_open_utc(self, day):
        d = _coerce_date(day)
        self._check_year(d.year)
        utc, _note = eastern_to_utc(datetime(d.year, d.month, d.day, 9, 30))
        return utc

    def market_close_utc(self, day):
        d = _coerce_date(day)
        self._check_year(d.year)
        hour = 13 if self.is_early_close(d) else 16
        utc, _note = eastern_to_utc(datetime(d.year, d.month, d.day, hour, 0))
        return utc

    # -- cache ------------------------------------------------------------
    def build_year_cache(self, year):
        self._check_year(year)
        days = self.trading_days(date(year, 1, 1), date(year, 12, 31))
        return {
            "year": year,
            "as_of": MODULE_VERSION,
            "generated_utc": iso_z(datetime.now(UTC)),
            "dst_start_utc": iso_z(dst_start_utc(year)),
            "dst_end_utc": iso_z(dst_end_utc(year)),
            "holidays": dict(sorted(self.holidays[year].items())),
            "trading_days": [d.isoformat() for d in days],
            "trading_day_count": len(days),
        }


DEFAULT_CALENDAR = MarketCalendar()


# --------------------------------------------------------------------------
# 4. Hashing helpers
# --------------------------------------------------------------------------

def canonical_sha256(obj):
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("ascii")
    return hashlib.sha256(blob).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text):
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def record_hash(rec):
    """Content hash over the record with `record_hash` itself blanked."""
    probe = dict((k, v) for k, v in rec.items() if k != "record_hash")
    return canonical_sha256(probe)


def module_code_hash():
    return sha256_file(MODULE_PATH)


# --------------------------------------------------------------------------
# 5. Provenance -- THE KEY CONTROL (owned by temporal_policy, NOT here)
#
# The implementation below was MOVED to temporal_policy.py. What remains
# is a thin delegation so existing callers keep working against a single
# implementation instead of a scheduler-local copy.
# --------------------------------------------------------------------------

PROSPECTIVE = temporal_policy.PROSPECTIVE
RETROSPECTIVE_BACKFILL = temporal_policy.RETROSPECTIVE_BACKFILL
PROVENANCE_MODES = (PROSPECTIVE, RETROSPECTIVE_BACKFILL)

# Register this module's richer calendar as the policy default. This is a
# DATA contribution (a more complete session model), not ownership: the
# policy logic itself lives entirely in temporal_policy.
temporal_policy.set_default_calendar(DEFAULT_CALENDAR)

# --- BEGIN ESCAPE-HATCH TOKEN TABLE (excluded from the self-scan below) ---
# Tokens that must never appear in this module. Their presence would mean
# someone added a switch to launder backfilled records into a prospective
# claim. `verify_no_backfill_escape_hatch()` enforces this by scanning this
# file for every token below, ignoring the region that merely declares them.
FORBIDDEN_ESCAPE_TOKENS = (
    "".join(["include", "_backfill"]),
    "".join(["allow", "_backfill"]),
    "".join(["allow", "_retro"]),
    "".join(["force", "_prospective"]),
    "".join(["disable", "_provenance"]),
    "".join(["treat_backfill", "_as_prospective"]),
    "".join(["prospective", "_override"]),
)
# --- END ESCAPE-HATCH TOKEN TABLE ---

_SCAN_BEGIN = "# --- BEGIN ESCAPE-HATCH TOKEN TABLE"
_SCAN_END = "# --- END ESCAPE-HATCH TOKEN TABLE ---"


def provenance_decision(creation_ts, earliest_tradable, calendar=None):
    """Decide whether a record is prospective evidence.

    DELEGATES to `temporal_policy.provenance_decision`, the canonical
    owner. This wrapper exists only so existing call sites keep working;
    there is deliberately no rule logic left in this file.

    Rule (fail-closed, monotone -- strictening is allowed, loosening is not):
      RETRO if eastern_date(creation_ts) > earliest_tradable
      RETRO if creation_ts > market_close_utc(earliest_tradable)
      else PROSPECTIVE
    """
    return temporal_policy.provenance_decision(
        creation_ts, earliest_tradable,
        calendar=calendar or DEFAULT_CALENDAR)


def is_prospective_evidence(rec):
    """Single source of truth for prospective eligibility."""
    return temporal_policy.is_prospective_evidence(rec)


def temporal_verdict_for(rec, now_utc=None, already_graded=False,
                         frozen_dataset_sha=None):
    """The canonical eight-output temporal verdict for a record.

    Provided here so scheduler-driven flows report exactly the same
    verdict shape as shadow grading and the audit tools -- one contract,
    one owner, no second dialect.
    """
    return temporal_policy.grade_eligibility_verdict(
        rec, now_utc=now_utc, already_graded=already_graded,
        frozen_dataset_sha=frozen_dataset_sha)


def assert_record_timestamps(rec, label="record"):
    """Every emitted timestamp must be UTC ISO-8601 with explicit Z."""
    bad = []
    for key in sorted(rec.keys()):
        if key.endswith("_utc") or key.endswith("_ts"):
            val = rec[key]
            if val is None:
                continue
            if not is_iso_z(val):
                bad.append("%s=%r" % (key, val))
    if bad:
        raise SchedulerError(
            "%s has non-UTC-ISO-8601 timestamps: %s"
            % (label, ", ".join(bad)))
    return True


def verify_no_backfill_escape_hatch(path=None):
    """Refuse to run if this module ever grows a switch that lets
    backfilled records be counted as prospective."""
    path = path or MODULE_PATH
    with open(path, "r", encoding="ascii") as fh:
        text = fh.read()
    # Strip the region that merely declares the tokens, otherwise the scan
    # would trip over its own table.
    head, sep, tail = text.partition(_SCAN_BEGIN)
    if sep:
        _declaration, sep2, tail = tail.partition(_SCAN_END)
        text = head + (tail if sep2 else "")
    lowered = text.lower()
    hits = [t for t in FORBIDDEN_ESCAPE_TOKENS if t in lowered]
    return (not hits), hits


# --------------------------------------------------------------------------
# 6. Data quality: fresh / late / stale / missing
# --------------------------------------------------------------------------

FRESH = "FRESH"
LATE = "LATE"
STALE = "STALE"
MISSING = "MISSING"
DATA_STATES = (FRESH, LATE, STALE, MISSING)


class Quote(object):
    """A price observation plus WHEN it became observable."""

    def __init__(self, instrument, session, close, availability_ts,
                 source="synthetic-provider", note="normal"):
        self.instrument = instrument
        self.session = _coerce_date(session)
        self.close = close
        self.availability_ts = require_utc(availability_ts)
        self.source = source
        self.note = note

    def as_dict(self):
        return {
            "instrument": self.instrument,
            "session": self.session.isoformat(),
            "close": self.close,
            "availability_ts": iso_z(self.availability_ts),
            "source": self.source,
            "note": self.note,
        }


def classify_quote(quote, now, expected_ts=None, sla_seconds=None,
                   late_grace_seconds=0):
    """Classify an observation.

    MISSING -> no observation at all. Blocks output.
    STALE   -> observed, but older than the freshness SLA. Blocks output.
    LATE    -> arrived after the expected time but within the SLA.
               Accepted and marked; never silently treated as on-time.
    FRESH   -> on time and inside the SLA.

    DELEGATES to `temporal_policy.classify_freshness`. Freshness is a
    temporal question, so the policy that owns temporal questions owns
    this one too; the scheduler keeps only the Quote-shaped adapter.
    """
    if quote is None:
        return temporal_policy.classify_freshness(
            None, None, now_utc=now, expected_ts=expected_ts,
            sla_seconds=sla_seconds, late_grace_seconds=late_grace_seconds)
    return temporal_policy.classify_freshness(
        quote.availability_ts, quote.close, now_utc=now,
        expected_ts=expected_ts, sla_seconds=sla_seconds,
        late_grace_seconds=late_grace_seconds)


# --------------------------------------------------------------------------
# 7. Providers (synthetic, in-memory; outage injection)
# --------------------------------------------------------------------------

class SyntheticProvider(object):
    """Deterministic price source with injectable outages and lateness.

    No network. Bars are seeded by the caller. An outage window makes
    every fetch in [start, end] raise a typed ProviderError.
    """

    def __init__(self, clock, bars=None, outages=None, late_seconds=None,
                 missing=None, rate_limit_every=0, name="synthetic-provider"):
        self.clock = clock
        self.bars = {}
        if bars:
            for (inst, sess), close in bars.items():
                self.bars[(inst, _coerce_date(sess))] = close
        self.outages = list(outages or [])
        self.late_seconds = dict(late_seconds or {})
        self.missing = set()
        for m in (missing or []):
            self.missing.add((m[0], _coerce_date(m[1])))
        self.rate_limit_every = rate_limit_every
        self.name = name
        self.calls = 0
        self.call_log = []

    def seed(self, instrument, session, close):
        self.bars[(instrument, _coerce_date(session))] = close
        return self

    def add_outage(self, start, end, exc_class=ProviderOutage,
                   message="provider unavailable"):
        self.outages.append((require_utc(start), require_utc(end), exc_class,
                             message))
        return self

    def add_late(self, instrument, session, seconds):
        self.late_seconds[(instrument, _coerce_date(session))] = seconds
        return self

    def add_missing(self, instrument, session):
        self.missing.add((instrument, _coerce_date(session)))
        return self

    def _outage_now(self, now):
        for start, end, exc_class, message in self.outages:
            if start <= now <= end:
                return exc_class, message
        return None, None

    def fetch_close(self, instrument, session):
        """Return a Quote. Availability is bounded below by `now`: a bar
        cannot be observable before the scheduler's clock reaches it."""
        now = self.clock.now()
        sess = _coerce_date(session)
        self.calls += 1
        self.call_log.append((instrument, sess.isoformat(), iso_z(now)))

        exc_class, message = self._outage_now(now)
        if exc_class is not None:
            raise exc_class(
                "%s: %s for %s/%s" % (self.name, message, instrument,
                                      sess.isoformat()),
                detail={"instrument": instrument, "session": sess.isoformat(),
                        "provider": self.name})

        if self.rate_limit_every and self.calls % self.rate_limit_every == 0:
            raise ProviderRateLimited(
                "%s: rate limited on call %d" % (self.name, self.calls),
                detail={"instrument": instrument, "session": sess.isoformat()})

        if (instrument, sess) in self.missing:
            return None

        close = self.bars.get((instrument, sess))
        if close is None:
            return None

        availability = DEFAULT_CALENDAR.market_close_utc(sess)
        delay = self.late_seconds.get((instrument, sess), 0)
        availability = availability + timedelta(seconds=delay)
        # A quote is never observable before the clock says so.
        if availability > now:
            availability = now
        return Quote(instrument, sess, close, availability, source=self.name,
                     note="late_by_%ds" % delay if delay else "normal")


# --------------------------------------------------------------------------
# 8. Retries: bounded exponential backoff with jitter, then dead-letter
# --------------------------------------------------------------------------

class RetryPolicy(object):
    def __init__(self, max_attempts=4, base_seconds=2.0, multiplier=2.0,
                 max_seconds=60.0, jitter_ratio=0.25):
        self.max_attempts = max_attempts
        self.base_seconds = base_seconds
        self.multiplier = multiplier
        self.max_seconds = max_seconds
        self.jitter_ratio = jitter_ratio

    def as_dict(self):
        return {"max_attempts": self.max_attempts,
                "base_seconds": self.base_seconds,
                "multiplier": self.multiplier,
                "max_seconds": self.max_seconds,
                "jitter_ratio": self.jitter_ratio}


DEFAULT_RETRY_POLICY = RetryPolicy()


def backoff_delay(attempt, policy, rng):
    """Exponential, capped, jittered. Deterministic for a seeded rng."""
    raw = policy.base_seconds * (policy.multiplier ** (attempt - 1))
    raw = min(raw, policy.max_seconds)
    jitter = raw * policy.jitter_ratio * rng.random()
    return round(raw + jitter, 6)


class RetryOutcome(object):
    def __init__(self, ok, value=None, error=None, attempts=0, delays=None,
                 dead_lettered=False):
        self.ok = ok
        self.value = value
        self.error = error
        self.attempts = attempts
        self.delays = delays or []
        self.dead_lettered = dead_lettered

    def as_dict(self):
        return {"ok": self.ok, "attempts": self.attempts,
                "delays": self.delays,
                "dead_lettered": self.dead_lettered,
                "error_class": (self.error.error_class
                                if self.error is not None else None),
                "error_message": (self.error.message
                                  if self.error is not None else None)}


def run_with_retry(fn, policy=None, clock=None, rng=None, task="task"):
    """Call fn() up to policy.max_attempts times. Non-retryable errors
    fail immediately. Exhaustion raises DeadLetterError."""
    policy = policy or DEFAULT_RETRY_POLICY
    clock = clock or SystemClock()
    rng = rng or random.Random(0)
    delays = []
    last_error = None
    for attempt in range(1, policy.max_attempts + 1):
        try:
            return RetryOutcome(True, value=fn(), attempts=attempt,
                                delays=delays)
        except ProviderError as exc:
            last_error = exc
            if not exc.retryable:
                break
            if attempt >= policy.max_attempts:
                break
            delay = backoff_delay(attempt, policy, rng)
            delays.append(delay)
            clock.sleep(delay)
    raise DeadLetterError(
        "%s failed after %d attempts; dead-lettered" % (task, len(delays) + 1),
        detail={"task": task, "attempts": len(delays) + 1,
                "delays": delays,
                "error_class": (last_error.error_class
                                if last_error is not None else None),
                "error_message": (last_error.message
                                  if last_error is not None else None)})


# --------------------------------------------------------------------------
# 9. Durable state: atomic appends, idempotency ledger, cursor
# --------------------------------------------------------------------------

PREDICTIONS_LOG = "predictions.jsonl"
GRADES_LOG = "grades.jsonl"
ALERTS_LOG = "alerts.jsonl"
RUN_INDEX = "run-index.jsonl"
CURSOR_FILE = "cursor.json"
IDEMPOTENCY_FILE = "idempotency.json"
DRIFT_FREEZE_FILE = "drift-freeze.json"
CALENDAR_CACHE_FILE = "calendar-cache.json"
DEAD_LETTER_DIR = "dead-letters"
MANIFEST_DIR = "manifests"


def _atomic_write(path, text):
    d = os.path.dirname(os.path.abspath(path)) or "."
    if d and not os.path.isdir(d):
        os.makedirs(d)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-", suffix=".part")
    try:
        with os.fdopen(fd, "w", encoding="ascii", newline="\n") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass
        raise


class SchedulerState(object):
    """All runtime state lives here. Nothing outside this directory is
    written by the scheduler."""

    def __init__(self, root=DEFAULT_STATE_DIR):
        self.root = os.path.abspath(root)
        if not os.path.isdir(self.root):
            os.makedirs(self.root)
        for sub in (MANIFEST_DIR, DEAD_LETTER_DIR):
            p = os.path.join(self.root, sub)
            if not os.path.isdir(p):
                os.makedirs(p)
        self._lock = threading.RLock()

    def path(self, *parts):
        return os.path.join(self.root, *parts)

    # -- jsonl ------------------------------------------------------------
    def read_jsonl(self, name):
        p = self.path(name)
        if not os.path.exists(p):
            return []
        out = []
        with open(p, "r", encoding="ascii") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def append_jsonl(self, name, rec):
        with self._lock:
            rows = self.read_jsonl(name)
            rows.append(rec)
            text = "".join(json.dumps(r, sort_keys=True, ensure_ascii=True)
                           + "\n" for r in rows)
            _atomic_write(self.path(name), text)
        return rec

    # -- json -------------------------------------------------------------
    def read_json(self, name, default=None):
        p = self.path(name)
        if not os.path.exists(p):
            return default
        with open(p, "r", encoding="ascii") as fh:
            return json.load(fh)

    def write_json(self, name, obj):
        with self._lock:
            _atomic_write(self.path(name),
                          json.dumps(obj, sort_keys=True, indent=1,
                                     ensure_ascii=True) + "\n")
        return obj

    # -- named logs -------------------------------------------------------
    def predictions(self):
        return self.read_jsonl(PREDICTIONS_LOG)

    def grades(self):
        return self.read_jsonl(GRADES_LOG)

    def alerts(self):
        return self.read_jsonl(ALERTS_LOG)

    def append_prediction(self, rec):
        return self.append_jsonl(PREDICTIONS_LOG, rec)

    def append_grade(self, rec):
        return self.append_jsonl(GRADES_LOG, rec)

    # -- cursor -----------------------------------------------------------
    def cursor(self):
        cur = self.read_json(CURSOR_FILE)
        if cur is None:
            return {"last_completed_slot": None, "completed_runs": 0,
                    "updated_utc": None}
        return cur

    def set_cursor(self, last_completed_slot, run_id, now):
        cur = {"last_completed_slot": (last_completed_slot.isoformat()
                                       if last_completed_slot is not None
                                       else None),
               "completed_runs": self.cursor().get("completed_runs", 0) + 1,
               "last_run_id": run_id,
               "updated_utc": iso_z(now)}
        return self.write_json(CURSOR_FILE, cur)

    # -- idempotency ------------------------------------------------------
    def idempotency(self):
        return self.read_json(IDEMPOTENCY_FILE, default={}) or {}

    def key_status(self, key):
        return self.idempotency().get(key)

    def claim_key(self, key, payload_hash, now, task):
        """Atomically claim an idempotency key.

        Returns (claimed, existing). If the key is already claimed with the
        SAME payload hash, returns (False, existing) and the caller must
        treat the work as already applied -- NOT re-apply it.
        """
        with self._lock:
            table = self.idempotency()
            existing = table.get(key)
            if existing is not None:
                return False, existing
            table[key] = {"key": key, "payload_hash": payload_hash,
                          "claimed_utc": iso_z(now), "task": task}
            self.write_json(IDEMPOTENCY_FILE, table)
            return True, table[key]

    # -- dead letters -----------------------------------------------------
    def dead_letter(self, task, exc, context=None):
        stamp = iso_z(datetime.now(UTC)).replace(":", "").replace("-", "")
        name = "dead-letter-%s-%s.json" % (task, stamp)
        payload = {"task": task, "error_class": getattr(exc, "error_class",
                                                        "UNKNOWN"),
                   "message": getattr(exc, "message", str(exc)),
                   "detail": getattr(exc, "detail", {}),
                   "context": context or {},
                   "recorded_utc": iso_z(datetime.now(UTC))}
        self.write_json(os.path.join(DEAD_LETTER_DIR, name), payload)
        return name

    def dead_letters(self):
        d = self.path(DEAD_LETTER_DIR)
        if not os.path.isdir(d):
            return []
        return sorted(n for n in os.listdir(d)
                      if n.startswith("dead-letter-"))

    # -- manifests --------------------------------------------------------
    def write_manifest(self, manifest):
        run_id = manifest["run_id"]
        name = "%s.%03d.json" % (run_id, int(manifest.get("run_attempt", 0)))
        self.write_json(os.path.join(MANIFEST_DIR, name), manifest)
        self.append_jsonl(RUN_INDEX, {
            "run_id": run_id,
            "run_attempt": int(manifest.get("run_attempt", 0)),
            "started_utc": manifest["started_utc"],
            "ended_utc": manifest["ended_utc"],
            "status": manifest["status"],
            "tasks_attempted": manifest["tasks_attempted"],
            "tasks_succeeded": manifest["tasks_succeeded"],
            "tasks_failed": manifest["tasks_failed"],
        })
        return manifest


# --------------------------------------------------------------------------
# 10. Alerts
# --------------------------------------------------------------------------

ALERT_SEVERITIES = ("INFO", "WARN", "ERROR", "CRITICAL")

ALERT_CODES = (
    "SCHED.RUN_START",
    "SCHED.RUN_OK",
    "SCHED.TASK_FAILED",
    "SCHED.DRIFT_REFUSED",
    "SCHED.STALE_DATA",
    "SCHED.MISSING_DATA",
    "SCHED.PROVIDER_OUTAGE",
    "SCHED.DEAD_LETTER",
    "SCHED.MISSED_RUN",
    "SCHED.MISSED_RUN_LIMIT",
    "SCHED.BACKFILL_LABELED",
    "SCHED.GRADE_REFUSED",
    "SCHED.SHUTDOWN",
)


def emit_alert(state, clock, run_id, severity, code, detail=None,
               correlation_id=None):
    if severity not in ALERT_SEVERITIES:
        raise ValueError("bad severity %r" % (severity,))
    now = clock.now()
    body = {"event_type": "scheduler.alert", "alert_code": code,
            "severity": severity, "run_id": run_id,
            "correlation_id": correlation_id or run_id,
            "component": "fis.scheduler", "detail": detail or {},
            "ts": iso_z(now)}
    body["alert_id"] = canonical_sha256(body)[:16]
    state.append_jsonl(ALERTS_LOG, body)
    return body


# --------------------------------------------------------------------------
# 11. Drift guard: refuse to grade if code/config moved under the records
# --------------------------------------------------------------------------

DRIFT_CLEAN = "CLEAN"
DRIFT_CHANGED = "DRIFTED"
DRIFT_NO_FREEZE = "NO_FREEZE"


class DriftGuard(object):
    """Hash the scheduler module plus any registered engine/config
    sources. If the hashes moved since the freeze that the existing
    records were created under, grading is REFUSED until a re-freeze."""

    def __init__(self, state, sources=None):
        self.state = state
        self.sources = dict(sources or {})
        self.sources.setdefault("scheduler.py", MODULE_PATH)

    def current_hashes(self):
        out = {}
        for name, path in sorted(self.sources.items()):
            if os.path.exists(path):
                out[name] = sha256_file(path)
            else:
                out[name] = "ABSENT"
        return out

    def drift_hash(self, hashes=None):
        return canonical_sha256(hashes or self.current_hashes())

    def freeze(self, clock, freeze_id=None):
        hashes = self.current_hashes()
        rec = {"freeze_id": freeze_id or ("FIS-SCHED-FREEZE-%s"
                                          % self.drift_hash(hashes)[:12]),
               "created_utc": iso_z(clock.now()),
               "module_version": MODULE_VERSION,
               "code_hashes": hashes,
               "drift_hash": self.drift_hash(hashes)}
        self.state.write_json(DRIFT_FREEZE_FILE, rec)
        return rec

    def refreeze(self, clock, freeze_id=None):
        """Explicit operator action. Re-freezing does NOT launder old
        records: they keep the drift_hash they were created under."""
        return self.freeze(clock, freeze_id=freeze_id)

    def current_freeze(self):
        return self.state.read_json(DRIFT_FREEZE_FILE)

    def check(self):
        freeze = self.current_freeze()
        actual = self.current_hashes()
        actual_drift = self.drift_hash(actual)
        if freeze is None:
            return {"status": DRIFT_NO_FREEZE, "expected": None,
                    "actual": actual, "changed_keys": [],
                    "expected_drift_hash": None,
                    "actual_drift_hash": actual_drift,
                    "grading_allowed": False,
                    "reason": "no drift freeze exists -- run --freeze first"}
        expected = freeze.get("code_hashes", {})
        changed = sorted(k for k in set(expected) | set(actual)
                         if expected.get(k) != actual.get(k))
        if changed:
            return {"status": DRIFT_CHANGED,
                    "expected": expected, "actual": actual,
                    "changed_keys": changed,
                    "expected_drift_hash": freeze.get("drift_hash"),
                    "actual_drift_hash": actual_drift,
                    "grading_allowed": False,
                    "reason": ("code/config drift on %s -- freeze %s; "
                               "grading REFUSED until re-freeze"
                               % (", ".join(changed),
                                  freeze.get("freeze_id")))}
        return {"status": DRIFT_CLEAN, "expected": expected, "actual": actual,
                "changed_keys": [],
                "expected_drift_hash": freeze.get("drift_hash"),
                "actual_drift_hash": actual_drift,
                "grading_allowed": True, "reason": "hashes match freeze"}


# --------------------------------------------------------------------------
# 12. Config
# --------------------------------------------------------------------------

DEFAULT_COHORTS = ("SPY_BH", "TREND_MA20_50", "VOL_TARGET_10",
                   "NO_ACTION_CASH")
BENCHMARK = "SPY_BH"


class SchedulerConfig(object):
    def __init__(self, tick_utc_hour=21, tick_utc_minute=0, horizon_days=10,
                 cohorts=DEFAULT_COHORTS, freshness_sla_seconds=36 * 3600,
                 late_grace_seconds=900, max_missed_runs=3,
                 slot_grace_seconds=5400, min_prospective_samples=60,
                 forecast_band_z=1.2816, sigma_inflation=2.0,
                 retry=None, dead_letter_on_exhaustion=True):
        self.tick_utc_hour = tick_utc_hour
        self.tick_utc_minute = tick_utc_minute
        self.horizon_days = horizon_days
        self.cohorts = tuple(cohorts)
        self.freshness_sla_seconds = freshness_sla_seconds
        self.late_grace_seconds = late_grace_seconds
        self.max_missed_runs = max_missed_runs
        self.slot_grace_seconds = slot_grace_seconds
        self.min_prospective_samples = min_prospective_samples
        self.forecast_band_z = forecast_band_z
        self.sigma_inflation = sigma_inflation
        self.retry = retry or DEFAULT_RETRY_POLICY
        self.dead_letter_on_exhaustion = dead_letter_on_exhaustion

    def as_dict(self):
        return {"tick_utc_hour": self.tick_utc_hour,
                "tick_utc_minute": self.tick_utc_minute,
                "horizon_days": self.horizon_days,
                "cohorts": list(self.cohorts),
                "freshness_sla_seconds": self.freshness_sla_seconds,
                "late_grace_seconds": self.late_grace_seconds,
                "max_missed_runs": self.max_missed_runs,
                "slot_grace_seconds": self.slot_grace_seconds,
                "min_prospective_samples": self.min_prospective_samples,
                "forecast_band_z": self.forecast_band_z,
                "sigma_inflation": self.sigma_inflation,
                "retry": self.retry.as_dict(),
                "dead_letter_on_exhaustion": self.dead_letter_on_exhaustion}

    def config_hash(self):
        return canonical_sha256(self.as_dict())

    def slot_datetime(self, day):
        d = _coerce_date(day)
        return datetime(d.year, d.month, d.day, self.tick_utc_hour,
                        self.tick_utc_minute, tzinfo=UTC)


DEFAULT_CONFIG = SchedulerConfig()


# --------------------------------------------------------------------------
# 13. Forecast band + confidence
# --------------------------------------------------------------------------

def forecast_band(book_ret, bench_ret, sigma_daily, horizon,
                  z=1.2816, inflation=2.0):
    """Persistence-style horizon band, sigma scaled by sqrt(horizon) with
    a conservative inflation factor. Returns p10/p50/p90."""
    h = max(int(horizon), 1)
    mu = (book_ret - bench_ret) * h
    sig = max(float(sigma_daily), 1e-9) * math.sqrt(h) * float(inflation)
    return {"p10": round(mu - z * sig, 8),
            "p50": round(mu, 8),
            "p90": round(mu + z * sig, 8)}


def confidence_from_band(dist):
    """Width-aware confidence in [0, 1]. A wider band can never be more
    confident than a narrower one."""
    half = (dist["p90"] - dist["p10"]) / 2.0
    if half <= 0:
        return 1.0
    return round(1.0 / (1.0 + 8.0 * half), 6)


# --------------------------------------------------------------------------
# 14. Prediction construction
# --------------------------------------------------------------------------

def idempotency_key(kind, *parts):
    blob = "|".join([kind] + [str(p) for p in parts])
    return hashlib.sha256(blob.encode("ascii")).hexdigest()[:32]


def build_prediction(clock, calendar, cfg, cohort, cutoff_session,
                     tradable_session, inputs, dataset_version, drift_hash,
                     run_id, recovery=False, recovered_slot=None):
    """Build one prediction record.

    `inputs` is a dict of cohort -> {"close": float|None, "state": str,
    "reason": str, "availability_ts": str|None}. Missing or stale inputs
    yield an ABSTAINING record with confidence None -- never a confident
    number manufactured from absent data.
    """
    now = clock.now()
    created = require_utc(now)
    decision = provenance_decision(created, tradable_session, calendar)

    obs = inputs.get(cohort)
    bench_obs = inputs.get(BENCHMARK)
    data_state = (obs or {}).get("state", MISSING)
    bench_state = (bench_obs or {}).get("state", MISSING)

    book_ret = None
    bench_ret = None
    sigma = None
    dist = None
    confidence = None
    abstention = False
    notes = []

    if data_state in (FRESH, LATE):
        book_ret = obs.get("close")
    if bench_state in (FRESH, LATE):
        bench_ret = bench_obs.get("close")

    if data_state == LATE:
        notes.append("input LATE: %s" % obs.get("reason", ""))
    if bench_state == LATE:
        notes.append("benchmark input LATE: %s"
                     % bench_obs.get("reason", ""))
    if data_state == STALE:
        notes.append("input STALE: %s" % obs.get("reason", ""))
        abstention = True
    if bench_state == STALE:
        notes.append("benchmark input STALE: %s"
                     % bench_obs.get("reason", ""))
        abstention = True
    if data_state == MISSING or bench_state == MISSING:
        notes.append("input MISSING -- no confident output produced")
        abstention = True

    if book_ret is not None and bench_ret is not None:
        sigma = abs(book_ret) * 0.5 + 0.004
        dist = forecast_band(book_ret, bench_ret, sigma, cfg.horizon_days,
                             cfg.forecast_band_z, cfg.sigma_inflation)
        confidence = confidence_from_band(dist)
    else:
        # No distribution is emitted when inputs are absent. Absent data
        # may not masquerade as a narrow, confident forecast.
        dist = None

    rec = {
        "record_type": "prediction",
        "module_version": MODULE_VERSION,
        "run_id": run_id,
        "cohort_id": cohort,
        "creation_ts": iso_z(created),
        "info_cutoff": _coerce_date(cutoff_session).isoformat(),
        "earliest_tradable": _coerce_date(tradable_session).isoformat(),
        "horizon_days": int(cfg.horizon_days),
        "benchmark": BENCHMARK,
        "provenance_mode": decision["provenance_mode"],
        "prospective_evidence": decision["prospective_evidence"],
        "provenance_rule": decision["rule"],
        "provenance_reason": decision["reason"],
        "provenance_decided_by": "fis.scheduler.provenance_decision",
        "data_state": data_state,
        "benchmark_data_state": bench_state,
        "data_availability_ts": (obs or {}).get("availability_ts"),
        "label_availability_ts": None,
        "abstention": abstention,
        "confidence": confidence,
        "forecast_distribution": dist,
        "notes": notes,
        "dataset_version": dataset_version,
        "drift_hash": drift_hash,
        "config_hash": cfg.config_hash(),
        "recovery": bool(recovery),
        "recovered_slot": (recovered_slot.isoformat()
                           if recovered_slot is not None else None),
        "idempotency_key": idempotency_key(
            "prediction", cohort, cutoff_session, tradable_session,
            dataset_version, drift_hash, bool(recovery)),
    }
    rec["record_hash"] = record_hash(rec)
    assert_record_timestamps(rec, "prediction")
    return rec


# --------------------------------------------------------------------------
# 15. Grading
# --------------------------------------------------------------------------

def horizon_expiry(calendar, cfg, earliest_tradable, latest_realized_session,
                   sessions):
    """Has the horizon genuinely expired?

    Returns (expired: bool, maturity_session: date|None, reason: str).
    Requires HORIZON trading closes at or after earliest_tradable, all of
    them already realized. 'The horizon is in the past' is NOT sufficient
    on its own -- the closes must exist.
    """
    trade = _coerce_date(earliest_tradable)
    if trade not in sessions:
        return False, None, ("earliest_tradable %s is not a session in the "
                             "known window" % trade.isoformat())
    ti = sessions.index(trade)
    mi = ti + int(cfg.horizon_days)
    if mi >= len(sessions):
        return False, None, ("horizon requires session index %d beyond known "
                             "calendar (max %d)" % (mi, len(sessions) - 1))
    maturity = sessions[mi]
    if latest_realized_session is None:
        return False, maturity, "no realized closes yet"
    if _coerce_date(latest_realized_session) < maturity:
        return False, maturity, (
            "horizon NOT expired: maturity %s > latest realized close %s"
            % (maturity.isoformat(),
               _coerce_date(latest_realized_session).isoformat()))
    return True, maturity, ("horizon expired: maturity %s <= latest realized "
                            "close %s" % (maturity.isoformat(),
                                          _coerce_date(
                                              latest_realized_session)
                                          .isoformat()))


def grade_prediction(clock, calendar, cfg, prediction, known_parents,
                     closes, sessions, latest_realized_session, run_id,
                     drift_state):
    """Grade one prediction, or refuse loudly.

    Gates, in order:
      1. parent prediction must exist, matched by record_hash
      2. drift must be CLEAN
      3. horizon must have genuinely expired (closes must exist)
      4. every close in the horizon window must be present
      5. provenance decides whether the grade carries prospective weight

    A refusal NEVER produces a grade row.
    """
    rec = dict(prediction)
    parent_hash = rec.get("record_hash")
    if parent_hash is None:
        raise GradeWithoutParentError(
            "prediction has no record_hash -- cannot grade an unhashed "
            "record", detail={"cohort_id": rec.get("cohort_id")})

    parents = known_parents
    if isinstance(parents, dict):
        parent = parents.get(parent_hash)
    elif isinstance(parents, (set, frozenset)):
        parent = parent_hash if parent_hash in parents else None
    else:
        parent = None
        for p in parents:
            if p.get("record_hash") == parent_hash:
                parent = p
                break
    if parent is None:
        raise GradeWithoutParentError(
            "no parent prediction with record_hash %s -- grading REFUSED"
            % parent_hash,
            detail={"parent_hash": parent_hash,
                    "cohort_id": rec.get("cohort_id"),
                    "known_parents": (len(parents) if not
                                      isinstance(parents, dict) else
                                      len(parents))})

    if drift_state.get("status") != DRIFT_CLEAN:
        raise DriftRefusal(
            "grading REFUSED: drift state is %s (%s)"
            % (drift_state.get("status"), drift_state.get("reason")),
            detail={"parent_hash": parent_hash,
                    "changed_keys": drift_state.get("changed_keys", [])})

    trade = _coerce_date(rec["earliest_tradable"])
    expired, maturity, why = horizon_expiry(calendar, cfg, trade,
                                            latest_realized_session,
                                            sessions)
    if not expired:
        return None, {"refused": True, "reason_code": "HORIZON_NOT_EXPIRED",
                      "reason": why, "parent_hash": parent_hash}

    ti = sessions.index(trade)
    mi = ti + int(cfg.horizon_days)
    window = sessions[ti:mi + 1]
    missing = [d.isoformat() for d in window
               if closes.get(d) is None]
    if missing:
        return None, {"refused": True, "reason_code": "MISSING_CLOSES",
                      "reason": ("%d close(s) missing in horizon window: %s"
                                 % (len(missing), ", ".join(missing[:5]))),
                      "parent_hash": parent_hash,
                      "missing_sessions": missing}

    if rec.get("abstention"):
        return None, {"refused": True, "reason_code": "PARENT_ABSTAINED",
                      "reason": "parent prediction abstained (no confident "
                                "input); nothing to grade",
                      "parent_hash": parent_hash}

    bench_closes = closes.get("__benchmark__") or {}
    if not bench_closes:
        return None, {"refused": True, "reason_code": "BENCHMARK_ABSENT",
                      "reason": "benchmark series absent; excess return is "
                                "undefined",
                      "parent_hash": parent_hash}

    # `closes` holds CLOSE PRICES. Horizon return is compounded from
    # price ratios, never from raw levels.
    cum = 1.0
    bcum = 1.0
    for k in range(ti + 1, mi + 1):
        d = sessions[k]
        prev_d = sessions[k - 1]
        p0 = closes.get(prev_d)
        p1 = closes.get(d)
        b0 = bench_closes.get(prev_d)
        b1 = bench_closes.get(d)
        if p0 is None or p1 is None or b0 is None or b1 is None:
            return None, {"refused": True, "reason_code": "MISSING_CLOSES",
                          "reason": "close missing at %s or %s"
                                    % (prev_d.isoformat(), d.isoformat()),
                          "parent_hash": parent_hash}
        if p0 <= 0 or b0 <= 0:
            return None, {"refused": True, "reason_code": "NONPOSITIVE_CLOSE",
                          "reason": "non-positive close at %s (book %r, "
                                    "benchmark %r)" % (prev_d.isoformat(),
                                                       p0, b0),
                          "parent_hash": parent_hash}
        cum *= p1 / p0
        bcum *= b1 / b0

    realized = cum - 1.0
    bench_r = bcum - 1.0
    excess = realized - bench_r
    dist = rec.get("forecast_distribution") or {}
    inside = (dist.get("p10") is not None and dist.get("p90") is not None
              and dist["p10"] <= excess <= dist["p90"])
    dir_pred = 0 if not dist else (1 if dist["p50"] > 0
                                   else (-1 if dist["p50"] < 0 else 0))
    dir_real = 1 if excess > 0 else (-1 if excess < 0 else 0)

    prov = rec.get("provenance_mode")
    if prov not in PROVENANCE_MODES:
        raise BackfillRestrictionError(
            "prediction carries unknown provenance_mode %r -- refusing to "
            "grade an unlabeled record" % (prov,),
            detail={"parent_hash": parent_hash})

    now = clock.now()
    grade = {
        "record_type": "grade",
        "module_version": MODULE_VERSION,
        "run_id": run_id,
        "parent_prediction_hash": parent_hash,
        "cohort_id": rec.get("cohort_id"),
        "graded_at_utc": iso_z(now),
        "info_cutoff": rec.get("info_cutoff"),
        "earliest_tradable": trade.isoformat(),
        "maturity_date": maturity.isoformat(),
        "horizon_days": int(cfg.horizon_days),
        "label_availability_ts": iso_z(
            calendar.market_close_utc(maturity)),
        "provenance_mode": prov,
        "prospective_evidence": (prov == PROSPECTIVE),
        "realized_horizon_return": round(realized, 8),
        "benchmark_horizon_return": round(bench_r, 8),
        "excess_vs_benchmark": round(excess, 8),
        "inside_p10_p90": bool(inside),
        "direction_predicted": dir_pred,
        "direction_realized": dir_real,
        "direction_accuracy": 1.0 if dir_pred == dir_real else 0.0,
        "horizon_expiry_evidence": why,
        "drift_hash": rec.get("drift_hash"),
        "idempotency_key": idempotency_key("grade", parent_hash,
                                           maturity.isoformat()),
    }
    grade["record_hash"] = record_hash(grade)
    assert_record_timestamps(grade, "grade")

    # Invariant: a record created after its own tradable window may never
    # be emitted as prospective evidence, at any point, by any path.
    if grade["prospective_evidence"]:
        check = provenance_decision(parse_iso_z(rec["creation_ts"]), trade,
                                    calendar)
        if check["provenance_mode"] != PROSPECTIVE:
            raise BackfillRestrictionError(
                "INVARIANT VIOLATION: grade would be marked prospective for "
                "a parent created after its own earliest_tradable (%s > %s)"
                % (rec["creation_ts"], trade.isoformat()),
                detail={"parent_hash": parent_hash})
    return grade, None


# --------------------------------------------------------------------------
# 16. Prospective aggregation (permanently backfill-exclusive)
# --------------------------------------------------------------------------

def aggregate_prospective(records, min_samples=60):
    """Aggregate PROSPECTIVE evidence ONLY.

    RETROSPECTIVE_BACKFILL records are excluded, unconditionally and
    permanently. There is no parameter to disable this -- the signature
    takes no such argument and the module refuses to load if one is added.
    """
    total = 0
    kept = []
    excluded = []
    for r in records:
        total += 1
        if is_prospective_evidence(r):
            kept.append(r)
        else:
            excluded.append({
                "record_hash": r.get("record_hash"),
                "provenance_mode": r.get("provenance_mode"),
                "cohort_id": r.get("cohort_id"),
                "earliest_tradable": r.get("earliest_tradable"),
                "creation_ts": r.get("creation_ts"),
                "excluded_permanently": True,
            })
    excesses = [r.get("excess_vs_benchmark") for r in kept
                if isinstance(r.get("excess_vs_benchmark"), (int, float))]
    accs = [r.get("direction_accuracy") for r in kept
            if isinstance(r.get("direction_accuracy"), (int, float))]
    n = len(kept)
    enough = n >= min_samples
    return {
        "scope": "PROSPECTIVE_ONLY",
        "backfill_policy": "EXCLUDED_PERMANENTLY_NO_OVERRIDE",
        "records_total": total,
        "records_prospective": n,
        "records_backfill_excluded": len(excluded),
        "excluded": excluded,
        "min_samples_required": min_samples,
        "samples_sufficient": enough,
        "claims_allowed": enough,
        "mean_excess_vs_benchmark": (round(sum(excesses) / len(excesses), 8)
                                     if excesses else None),
        "direction_accuracy": (round(sum(accs) / len(accs), 8)
                               if accs else None),
        "verdict": ("CLAIMS ALLOWED" if enough else
                    "SUMMARY REFUSED: %d prospective samples < %d required"
                    % (n, min_samples)),
    }


# --------------------------------------------------------------------------
# 17. Shutdown
# --------------------------------------------------------------------------

class ShutdownSignal(object):
    """SIGTERM-ish cooperative shutdown. `request()` is what a real signal
    handler calls; tests call it directly."""

    def __init__(self):
        self._event = threading.Event()
        self.reason = None
        self.requested_utc = None

    def request(self, reason="SIGTERM"):
        self.reason = reason
        self.requested_utc = iso_z(datetime.now(UTC))
        self._event.set()
        return self

    def is_set(self):
        return self._event.is_set()

    def clear(self):
        self.reason = None
        self.requested_utc = None
        self._event.clear()


def install_sigterm_handler(shutdown, previous=None):
    """Attach a real SIGTERM handler where the platform supports it."""
    def handler(signum, frame):
        shutdown.request("SIGTERM(%d)" % signum)

    try:
        signal.signal(signal.SIGTERM, handler)
        return True
    except (ValueError, OSError, AttributeError):
        return False


# --------------------------------------------------------------------------
# 18. Missed-run detection and restricted recovery
# --------------------------------------------------------------------------

def target_slot(clock, calendar, cfg):
    """The trading day whose scheduled slot is the most recent one at or
    before `now`."""
    now = clock.now()
    day = eastern_date(now)
    for back in range(0, 30):
        cand = day - timedelta(days=back)
        if calendar.is_trading_day(cand) and cfg.slot_datetime(cand) <= now:
            return cand
    return None


def detect_missed_slots(state, calendar, clock, cfg):
    """Trading sessions with a scheduled slot that has passed (plus grace)
    and no completed run recorded after them."""
    now = clock.now()
    cur = state.cursor()
    last = cur.get("last_completed_slot")
    today = eastern_date(now)
    if last is None:
        return []
    last_day = date.fromisoformat(last)
    start = last_day + timedelta(days=1)
    if start > today:
        return []
    out = []
    for d in calendar.trading_days(start, today):
        if not calendar.is_trading_day(d):
            continue
        if d == today and cfg.slot_datetime(d) > now:
            continue
        if now >= cfg.slot_datetime(d) + timedelta(
                seconds=cfg.slot_grace_seconds):
            out.append(d)
    return out


# --------------------------------------------------------------------------
# 19. The scheduler
# --------------------------------------------------------------------------

class TaskResult(object):
    def __init__(self, name, status, detail=None, idempotency_key=None,
                 outputs=None):
        self.name = name
        self.status = status  # SUCCEEDED | SKIPPED | FAILED | REFUSED
        self.detail = detail or {}
        self.idempotency_key = idempotency_key
        self.outputs = outputs or []

    def as_dict(self):
        return {"task": self.name, "status": self.status,
                "detail": self.detail,
                "idempotency_key": self.idempotency_key,
                "outputs": self.outputs}


STATUS_OK = "OK"
STATUS_PARTIAL = "PARTIAL"
STATUS_SHUTDOWN = "SHUTDOWN_PARTIAL"
STATUS_DRIFT_REFUSED = "DRIFT_REFUSED"
STATUS_FAILED = "FAILED"


class Scheduler(object):
    """Unattended scheduler. Owns its state directory and nothing else."""

    def __init__(self, state, config=None, clock=None, provider=None,
                 calendar=None, rng=None, drift_sources=None,
                 shutdown=None):
        self.state = state
        self.cfg = config or SchedulerConfig()
        self.clock = clock or SystemClock()
        self.provider = provider
        self.calendar = calendar or MarketCalendar()
        self.rng = rng or random.Random(20260826)
        self.shutdown = shutdown or ShutdownSignal()
        self.drift = DriftGuard(state, sources=drift_sources)
        self.degraded = False
        self.last_alert_count = 0

    # -- helpers ----------------------------------------------------------
    def _new_run_id(self, slot):
        """Deterministic per (slot, completed-run count).

        Deliberately NOT seeded by wall time: a run that is interrupted and
        then resumed within the same slot must rebuild byte-identical
        records so that resume dedups instead of double-applying.
        """
        seed = "%s|%s|%s" % (slot.isoformat() if slot else "none",
                             self.state.cursor().get("completed_runs", 0),
                             MODULE_VERSION)
        return "run-" + hashlib.sha256(seed.encode("ascii")).hexdigest()[:16]

    def _emit(self, run_id, severity, code, detail=None):
        return emit_alert(self.state, self.clock, run_id, severity, code,
                          detail)

    def _dataset_version(self):
        """Deterministic dataset fingerprint for the synthetic store."""
        if self.provider is None:
            return canonical_sha256({"provider": "none"})
        rows = sorted(
            "%s:%s:%s" % (k[0], k[1].isoformat(), v)
            for k, v in self.provider.bars.items())
        return sha256_text("\n".join(rows))

    def _collect_inputs(self, run_id, cutoff_session, sessions):
        """Fetch one close per cohort for the cutoff session.

        Returns (inputs, task_result). Degraded mode: an outage marks the
        run degraded and every affected cohort abstains -- no confident
        output is fabricated from an outage.
        """
        inputs = {}
        outages = []
        cfg = self.cfg
        now = self.clock.now()
        for cohort in cfg.cohorts:
            def fetch(inst=cohort):
                return self.provider.fetch_close(inst, cutoff_session)
            try:
                quote = run_with_retry(
                    fetch, cfg.retry, self.clock, self.rng,
                    task="fetch:%s:%s" % (cohort, cutoff_session))
                q = quote.value
            except DeadLetterError as exc:
                self.state.dead_letter("fetch_%s" % cohort, exc,
                                       {"session": cutoff_session.isoformat(),
                                        "run_id": run_id})
                self._emit(run_id, "ERROR", "SCHED.DEAD_LETTER",
                           {"cohort": cohort,
                            "session": cutoff_session.isoformat(),
                            "error_class": exc.error_class,
                            "attempts": len(exc.detail.get("delays", [])) + 1})
                outages.append({"cohort": cohort,
                                "error_class": exc.error_class,
                                "message": exc.message})
                inputs[cohort] = {"close": None, "state": MISSING,
                                  "reason": "provider exhausted retries: %s"
                                            % exc.error_class,
                                  "availability_ts": None}
                continue
            expected = self.calendar.market_close_utc(cutoff_session)
            cls = classify_quote(q, now, expected_ts=expected,
                                 sla_seconds=cfg.freshness_sla_seconds,
                                 late_grace_seconds=cfg.late_grace_seconds)
            inputs[cohort] = {
                "close": (q.close if q is not None else None),
                "state": cls["state"],
                "reason": cls["reason"],
                "availability_ts": cls["availability_ts"],
                "age_seconds": cls["age_seconds"],
            }
        return inputs, outages

    # -- main tick --------------------------------------------------------
    def run_tick(self, slot=None):
        clock = self.clock
        cfg = self.cfg
        cal = self.calendar
        now = clock.now()
        slot = slot or target_slot(clock, cal, cfg)
        run_id = self._new_run_id(slot)
        started = now

        tasks = []
        inputs_in = {}
        outputs_out = {}

        self._emit(run_id, "INFO", "SCHED.RUN_START",
                   {"slot": slot.isoformat() if slot else None,
                    "module_version": MODULE_VERSION})

        # -- 0. escape-hatch self-check -----------------------------------
        clean, hits = verify_no_backfill_escape_hatch()
        if not clean:
            raise BackfillRestrictionError(
                "scheduler source contains forbidden backfill escape "
                "tokens: %s" % ", ".join(hits))

        # -- 1. drift ------------------------------------------------------
        drift_state = self.drift.check()
        drift_hash = drift_state["actual_drift_hash"]
        inputs_in["drift"] = drift_state["actual_drift_hash"]
        inputs_in["config"] = cfg.config_hash()

        if drift_state["status"] != DRIFT_CLEAN:
            self._emit(run_id, "CRITICAL", "SCHED.DRIFT_REFUSED",
                       {"status": drift_state["status"],
                        "changed_keys": drift_state["changed_keys"],
                        "reason": drift_state["reason"]})
            manifest = self._manifest(
                run_id, started, clock.now(), tasks, inputs_in, outputs_out,
                drift_state, STATUS_DRIFT_REFUSED, slot, [], True)
            return manifest

        # -- 2. session bookkeeping ---------------------------------------
        today = eastern_date(now)
        sessions = cal.trading_days_bounded(today, lookback_days=400)
        if not sessions:
            self._emit(run_id, "WARN", "SCHED.TASK_FAILED",
                       {"task": "calendar", "reason": "no sessions"})
            return self._manifest(run_id, started, clock.now(), tasks,
                                  inputs_in, outputs_out, drift_state,
                                  STATUS_FAILED, slot, [], True)

        cutoff_session = slot if (slot is not None and slot in sessions) \
            else sessions[-1]
        tradable_session = cal.next_trading_day(cutoff_session)

        # -- 3. shutdown checkpoint before any effect ---------------------
        if self.shutdown.is_set():
            self._emit(run_id, "WARN", "SCHED.SHUTDOWN",
                       {"reason": self.shutdown.reason, "phase": "pre-effect"})
            return self._manifest(run_id, started, clock.now(), tasks,
                                  inputs_in, outputs_out, drift_state,
                                  STATUS_SHUTDOWN, slot, [], True)

        # -- 4. prediction tick -------------------------------------------
        task, preds = self._task_predictions(
            run_id, cutoff_session, tradable_session, sessions, drift_hash)
        tasks.append(task)
        if task.status == "FAILED":
            self._emit(run_id, "ERROR", "SCHED.TASK_FAILED",
                       {"task": "predictions", "detail": task.detail})
        for p in preds:
            outputs_out[p["record_hash"]] = p["provenance_mode"]

        # -- 5. grading ----------------------------------------------------
        if self.shutdown.is_set():
            self._emit(run_id, "WARN", "SCHED.SHUTDOWN",
                       {"reason": self.shutdown.reason,
                        "phase": "before_grading"})
            return self._manifest(run_id, started, clock.now(), tasks,
                                  inputs_in, outputs_out, drift_state,
                                  STATUS_SHUTDOWN, slot, [], True)

        task, grades = self._task_grading(run_id, sessions, drift_state)
        tasks.append(task)
        for g in grades:
            outputs_out[g["record_hash"]] = g["provenance_mode"]

        # -- 6. missed-run recovery ----------------------------------------
        task, recovered = self._task_recovery(run_id, sessions, drift_hash)
        tasks.append(task)

        # -- 7. finish ------------------------------------------------------
        attempted = len(tasks)
        succeeded = len([t for t in tasks if t.status in ("SUCCEEDED",
                                                          "SKIPPED")])
        failed = attempted - succeeded
        status = STATUS_OK if failed == 0 else STATUS_PARTIAL
        if attempted == 0:
            status = STATUS_FAILED

        self.state.set_cursor(slot, run_id, clock.now())
        self._emit(run_id, "INFO" if failed == 0 else "WARN",
                   "SCHED.RUN_OK" if failed == 0 else "SCHED.TASK_FAILED",
                   {"tasks_attempted": attempted,
                    "tasks_succeeded": succeeded,
                    "tasks_failed": failed,
                    "predictions_written": len(preds),
                    "grades_written": len(grades),
                    "records_recovered": len(recovered)})
        return self._manifest(run_id, started, clock.now(), tasks, inputs_in,
                              outputs_out, drift_state, status, slot,
                              recovered, True)

    # -- tasks ------------------------------------------------------------
    def _task_predictions(self, run_id, cutoff_session, tradable_session,
                          sessions, drift_hash):
        cfg = self.cfg
        inputs, outages = self._collect_inputs(run_id, cutoff_session,
                                               sessions)
        if outages:
            self.degraded = True
            self._emit(run_id, "ERROR", "SCHED.PROVIDER_OUTAGE",
                       {"outages": outages,
                        "degraded_mode": True,
                        "effect": "affected cohorts abstain; no grades "
                                  "produced from missing inputs"})

        dataset_version = self._dataset_version()
        existing_hashes = set(p.get("record_hash")
                              for p in self.state.predictions())
        written = []
        skipped = []
        for cohort in cfg.cohorts:
            rec = build_prediction(
                self.clock, self.calendar, cfg, cohort, cutoff_session,
                tradable_session, inputs, dataset_version, drift_hash,
                run_id)
            # Dedup is by content hash first: a record identical to one
            # already on disk is never applied twice. This is what makes a
            # resumed run after a shutdown safe -- the record is neither
            # lost (it is on disk) nor duplicated.
            if rec["record_hash"] in existing_hashes:
                skipped.append({"cohort": cohort,
                                "record_hash": rec["record_hash"],
                                "reason": "identical record already applied"})
                continue
            key = rec["idempotency_key"]
            claimed, _existing = self.state.claim_key(
                key, rec["record_hash"], self.clock.now(), "prediction")
            if not claimed:
                skipped.append({"cohort": cohort,
                                "record_hash": rec["record_hash"],
                                "reason": "idempotency key already claimed"})
                continue
            self.state.append_prediction(rec)
            existing_hashes.add(rec["record_hash"])
            written.append(rec)
            if rec["provenance_mode"] == RETROSPECTIVE_BACKFILL:
                self._emit(run_id, "WARN", "SCHED.BACKFILL_LABELED",
                           {"cohort": cohort,
                            "record_hash": rec["record_hash"],
                            "creation_ts": rec["creation_ts"],
                            "earliest_tradable": rec["earliest_tradable"],
                            "rule": rec["provenance_rule"],
                            "effect": "permanently excluded from "
                                      "prospective aggregation"})
            if rec["data_state"] == STALE:
                self._emit(run_id, "ERROR", "SCHED.STALE_DATA",
                           {"cohort": cohort, "detail": rec["notes"]})
            if rec["data_state"] == MISSING:
                self._emit(run_id, "ERROR", "SCHED.MISSING_DATA",
                           {"cohort": cohort,
                            "abstention": rec["abstention"],
                            "confidence": rec["confidence"]})
        return TaskResult(
            "predictions", "SUCCEEDED",
            {"cutoff_session": cutoff_session.isoformat(),
             "tradable_session": tradable_session.isoformat(),
             "written": len(written), "skipped_duplicates": len(skipped),
             "degraded": bool(outages),
             "prospective": len([r for r in written
                                 if r["provenance_mode"] == PROSPECTIVE]),
             "retro_backfill": len([r for r in written
                                    if r["provenance_mode"] ==
                                    RETROSPECTIVE_BACKFILL])},
            outputs=[r["record_hash"] for r in written]), written

    def _latest_realized(self, sessions):
        """Latest session whose close is already observable per the clock."""
        now = self.clock.now()
        latest = None
        for d in sessions:
            if now >= self.calendar.market_close_utc(d):
                latest = d
        return latest

    def _task_grading(self, run_id, sessions, drift_state):
        cfg = self.cfg
        latest = self._latest_realized(sessions)
        preds = self.state.predictions()
        grades = self.state.grades()
        graded_hashes = set(g.get("parent_prediction_hash") for g in grades)

        closes_by_cohort = {}
        for cohort in set(list(cfg.cohorts) + [BENCHMARK]):
            series = {}
            for d in sessions:
                q = self._safe_quote(cohort, d)
                series[d] = q["close"] if q else None
            closes_by_cohort[cohort] = series
        bench = closes_by_cohort.get(BENCHMARK, {})

        known_grade_hashes = set(g.get("record_hash") for g in grades)
        by_hash = dict((p["record_hash"], p) for p in preds)
        written = []
        refusals = []
        skipped = []
        for p in preds:
            if p["record_hash"] in graded_hashes:
                continue
            cohort = p.get("cohort_id")
            closes = dict(closes_by_cohort.get(cohort, {}))
            closes["__benchmark__"] = bench
            try:
                grade, refusal = grade_prediction(
                    self.clock, self.calendar, cfg, p, by_hash, closes,
                    sessions, latest, run_id, drift_state)
            except (GradeWithoutParentError, DriftRefusal,
                    BackfillRestrictionError) as exc:
                self._emit(run_id, "CRITICAL", "SCHED.GRADE_REFUSED",
                           {"parent_hash": p.get("record_hash"),
                            "error_class": exc.error_class,
                            "message": exc.message})
                refusals.append({"reason_code": exc.error_class,
                                 "parent_hash": p.get("record_hash"),
                                 "message": exc.message})
                continue
            if grade is None:
                refusals.append(refusal)
                continue
            # Dedup: an identical grade already on disk is re-applied
            # never. Refusals never burn a key, so a gated grade can be
            # graded on a later tick once its horizon truly expires.
            if grade["record_hash"] in known_grade_hashes:
                skipped.append(grade["record_hash"])
                continue
            key = grade["idempotency_key"]
            claimed, _existing = self.state.claim_key(
                key, grade["record_hash"], self.clock.now(), "grade")
            if not claimed:
                skipped.append(grade["record_hash"])
                continue
            self.state.append_grade(grade)
            known_grade_hashes.add(grade["record_hash"])
            written.append(grade)
        return TaskResult(
            "grading", "SUCCEEDED",
            {"candidates": len(preds), "written": len(written),
             "refused": len(refusals),
             "skipped_duplicates": len(skipped),
             "latest_realized_session": (latest.isoformat()
                                         if latest else None),
             "refusal_reasons": sorted(set(
                 r.get("reason_code") for r in refusals
                 if isinstance(r, dict)))},
            outputs=[g["record_hash"] for g in written]), written

    def _safe_quote(self, instrument, session):
        if self.provider is None:
            return None
        try:
            q = self.provider.fetch_close(instrument, session)
        except ProviderError:
            return None
        if q is None or q.close is None:
            return None
        return q.as_dict()

    def _task_recovery(self, run_id, sessions, drift_hash):
        cfg = self.cfg
        missed = detect_missed_slots(self.state, self.calendar, self.clock,
                                     cfg)
        if not missed:
            return TaskResult("recovery", "SKIPPED",
                              {"missed_slots": 0}), []

        if len(missed) > cfg.max_missed_runs:
            self._emit(run_id, "CRITICAL", "SCHED.MISSED_RUN_LIMIT",
                       {"missed": [d.isoformat() for d in missed],
                        "limit": cfg.max_missed_runs,
                        "action": "manual acknowledgement required"})
            return TaskResult(
                "recovery", "REFUSED",
                {"missed_slots": len(missed), "limit": cfg.max_missed_runs,
                 "error_class": "MISSED_RUN_LIMIT",
                 "reason": "too many missed runs for automatic recovery"}), []

        recovered = []
        for d in missed:
            if d not in sessions:
                continue
            tradable = self.calendar.next_trading_day(d)
            inputs, _outages = self._collect_inputs(run_id, d, sessions)
            dataset_version = self._dataset_version()
            existing_hashes = set(p.get("record_hash")
                                  for p in self.state.predictions())
            for cohort in cfg.cohorts:
                rec = build_prediction(
                    self.clock, self.calendar, cfg, cohort, d, tradable,
                    inputs, dataset_version, drift_hash, run_id,
                    recovery=True, recovered_slot=d)
                if rec["record_hash"] in existing_hashes:
                    continue
                key = rec["idempotency_key"]
                claimed, _ex = self.state.claim_key(
                    key, rec["record_hash"], self.clock.now(),
                    "recovery-prediction")
                if not claimed:
                    continue
                self.state.append_prediction(rec)
                existing_hashes.add(rec["record_hash"])
                recovered.append(rec)
            self._emit(run_id, "WARN", "SCHED.MISSED_RUN",
                       {"slot": d.isoformat(),
                        "recovered_records": len(recovered),
                        "provenance": RETROSPECTIVE_BACKFILL,
                        "effect": "recovery records are retrospective and "
                                  "never prospective evidence"})
        return TaskResult(
            "recovery", "SUCCEEDED",
            {"missed_slots": [d.isoformat() for d in missed],
             "recovered_records": len(recovered),
             "prospective": len([r for r in recovered
                                 if r["provenance_mode"] == PROSPECTIVE]),
             "retro_backfill": len([r for r in recovered
                                    if r["provenance_mode"] ==
                                    RETROSPECTIVE_BACKFILL])}), recovered

    # -- manifest ---------------------------------------------------------
    def _manifest(self, run_id, started, ended, tasks, inputs_in, outputs_out,
                  drift_state, status, slot, recovered, write=True):
        attempted = len(tasks)
        succeeded = len([t for t in tasks if t.status in ("SUCCEEDED",
                                                          "SKIPPED")])
        manifest = {
            "run_id": run_id,
            # Every attempt keeps its own manifest file, so a resumed run
            # does not erase the manifest of the run it resumed.
            "run_attempt": len(self.state.read_jsonl(RUN_INDEX)),
            "module_version": MODULE_VERSION,
            "started_utc": iso_z(started),
            "ended_utc": iso_z(ended),
            "duration_seconds": round(
                (require_utc(ended) - require_utc(started)).total_seconds(),
                6),
            "slot": slot.isoformat() if slot else None,
            "status": status,
            "tasks_attempted": attempted,
            "tasks_succeeded": succeeded,
            "tasks_failed": attempted - succeeded,
            "tasks": [t.as_dict() for t in tasks],
            "input_hashes": dict(sorted(inputs_in.items())),
            "output_hashes": dict(sorted(outputs_out.items())),
            "output_count": len(outputs_out),
            "drift_state": drift_state["status"],
            "drift_hash": drift_state.get("actual_drift_hash"),
            "drift_reason": drift_state.get("reason"),
            "drift_changed_keys": drift_state.get("changed_keys", []),
            "provenance_policy": {
                "modes": list(PROVENANCE_MODES),
                "backfill_excluded_from_prospective": True,
                "override_permitted": False,
            },
            "degraded_mode": bool(self.degraded),
            "shutdown_requested": bool(self.shutdown.is_set()),
            "shutdown_reason": self.shutdown.reason,
            "recovered_records": len(recovered),
            "alert_count": len(self.state.alerts()),
        }
        assert_record_timestamps(manifest, "manifest")
        if write:
            self.state.write_manifest(manifest)
        return manifest

    # -- loop -------------------------------------------------------------
    def run(self, max_ticks=None, idle_seconds=3600.0):
        """Unattended loop. Stops on shutdown request or max_ticks."""
        ticks = 0
        manifests = []
        while max_ticks is None or ticks < max_ticks:
            if self.shutdown.is_set():
                break
            manifests.append(self.run_tick())
            ticks += 1
            if self.shutdown.is_set():
                break
            if max_ticks is None or ticks < max_ticks:
                self.clock.sleep(idle_seconds)
        return manifests


# --------------------------------------------------------------------------
# 20. CLI
# --------------------------------------------------------------------------

def cmd_status(state=None):
    state = state or SchedulerState()
    drift = DriftGuard(state).check()
    return {
        "module_version": MODULE_VERSION,
        "state_dir": state.root,
        "predictions": len(state.predictions()),
        "grades": len(state.grades()),
        "alerts": len(state.alerts()),
        "dead_letters": len(state.dead_letters()),
        "cursor": state.cursor(),
        "drift_status": drift["status"],
        "drift_reason": drift["reason"],
        "drift_hash": drift["actual_drift_hash"],
        "escape_hatch_clean": verify_no_backfill_escape_hatch()[0],
        "checked_utc": iso_z(datetime.now(UTC)),
    }


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    state = SchedulerState()
    if "--status" in argv:
        print(json.dumps(cmd_status(state), sort_keys=True, indent=1,
                         ensure_ascii=True))
        return 0
    if "--once" in argv:
        sched = Scheduler(state, clock=SystemClock())
        manifest = sched.run_tick()
        print(json.dumps(manifest, sort_keys=True, indent=1,
                         ensure_ascii=True))
        return 0 if manifest["status"] in (STATUS_OK, STATUS_PARTIAL) else 2
    print("usage: scheduler.py [--once | --status]")
    return 1


if __name__ == "__main__":
    sys.exit(main())

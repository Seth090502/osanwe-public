#!/usr/bin/env python3
"""Canonical temporal eligibility policy for the FIS research pipeline.

WHY THIS MODULE IS THE OWNER
----------------------------
Before this module existed the provenance rule lived in `scheduler.py`.
`scheduler.py` is an INFRASTRUCTURE component -- it decides when things
run. `shadow.py`, `research evaluation`, `decision records` and the audit
tools are DOMAIN components -- they decide what a record means. When the
domain imports its temporal rule from the scheduler, the dependency arrow
points the wrong way: the meaning of a prediction depends on the job
runner, and the job runner cannot be changed without changing financial
semantics. That is the architecture defect this module corrects.

`shadow.py` previously did `from scheduler import provenance_decision`.
That import is now reversed: scheduler and shadow both import from here,
and neither imports the other's temporal logic.

CONTRACT
--------
One function per question, one canonical verdict shape for both:

    prediction_eligibility_verdict(...)  -> TemporalVerdict
    grade_eligibility_verdict(...)       -> TemporalVerdict

Every verdict carries all eight required outputs, always, even when the
answer is a refusal:

    prediction_eligibility   ELIGIBLE | INELIGIBLE
    grade_eligibility        ELIGIBLE | GATED | INELIGIBLE
    reason_code              canonical enum, never free text
    info_cutoff              the last session observable when written
    outcome_available        bool -- does the outcome exist yet?
    outcome_available_at     UTC ISO-8601 Z, or None
    required_expiry          UTC ISO-8601 Z -- when the window closes
    data_coverage            COMPLETE | PARTIAL | MISSING | UNKNOWN
    provenance_status        PROSPECTIVE | RETROSPECTIVE_BACKFILL | UNKNOWN
    quarantine_status        NOT_QUARANTINED | QUARANTINED:<reason>

THE RULE (monotone, fail-closed)
--------------------------------
A record is PROSPECTIVE only if it was created on or before the Eastern
date of its own earliest_tradable session AND at or before that session's
closing bell. Otherwise it is RETROSPECTIVE_BACKFILL and is PERMANENTLY
ineligible for any prospective performance claim. The rule may be
tightened; it may never be loosened, and there is no override parameter
anywhere in this module.

Stdlib only. ASCII only. No network access. No imports from scheduler,
shadow, or any other FIS module.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Tuple

TEMPORAL_POLICY_VERSION = "TEMPORAL-POLICY-v2"

UTC = timezone.utc
EST = timedelta(hours=-5)
EDT = timedelta(hours=-4)

# ---------------------------------------------------------------------------
# Canonical vocabularies
# ---------------------------------------------------------------------------

PROSPECTIVE = "PROSPECTIVE"
RETROSPECTIVE_BACKFILL = "RETROSPECTIVE_BACKFILL"
PROVENANCE_UNKNOWN = "UNKNOWN"
PROVENANCE_STATUSES: Tuple[str, ...] = (
    PROSPECTIVE, RETROSPECTIVE_BACKFILL, PROVENANCE_UNKNOWN)

ELIGIBLE = "ELIGIBLE"
INELIGIBLE = "INELIGIBLE"
GATED = "GATED"

COVERAGE_COMPLETE = "COMPLETE"
COVERAGE_PARTIAL = "PARTIAL"
COVERAGE_MISSING = "MISSING"
COVERAGE_UNKNOWN = "UNKNOWN"
COVERAGE_STATES: Tuple[str, ...] = (
    COVERAGE_COMPLETE, COVERAGE_PARTIAL, COVERAGE_MISSING, COVERAGE_UNKNOWN)

NOT_QUARANTINED = "NOT_QUARANTINED"

# Canonical reason codes. Closed set: a new refusal needs a new code here,
# not a prose string at the call site.
R_OK_PROSPECTIVE = "OK_PROSPECTIVE"
R_OK_GRADE_READY = "OK_GRADE_READY"
R_CREATED_AFTER_EARLIEST_TRADABLE = "CREATED_AFTER_EARLIEST_TRADABLE"
R_CREATED_AFTER_ENTRY_CLOSE = "CREATED_AFTER_ENTRY_CLOSE"
R_OUTCOME_NOT_YET_AVAILABLE = "OUTCOME_NOT_YET_AVAILABLE"
R_OUTCOME_DATE_NOT_IN_CALENDAR = "OUTCOME_DATE_NOT_IN_CALENDAR"
R_DATA_COVERAGE_INCOMPLETE = "DATA_COVERAGE_INCOMPLETE"
R_MISSING_REQUIRED_FIELDS = "MISSING_REQUIRED_FIELDS"
R_NON_UTC_TIMESTAMP = "NON_UTC_TIMESTAMP"
R_QUARANTINED = "QUARANTINED"
R_DATASET_DRIFT = "DATASET_DRIFT"
R_NOT_A_PREDICTION = "NOT_A_PREDICTION"
R_ALREADY_GRADED = "ALREADY_GRADED"
R_INVALID_TEMPORAL_INPUT = "INVALID_TEMPORAL_INPUT"
R_INFORMATION_NOT_AVAILABLE = "INFORMATION_NOT_AVAILABLE"

REASON_CODES: Tuple[str, ...] = (
    R_OK_PROSPECTIVE, R_OK_GRADE_READY,
    R_CREATED_AFTER_EARLIEST_TRADABLE, R_CREATED_AFTER_ENTRY_CLOSE,
    R_OUTCOME_NOT_YET_AVAILABLE, R_OUTCOME_DATE_NOT_IN_CALENDAR,
    R_DATA_COVERAGE_INCOMPLETE, R_MISSING_REQUIRED_FIELDS,
    R_NON_UTC_TIMESTAMP, R_QUARANTINED, R_DATASET_DRIFT,
    R_NOT_A_PREDICTION, R_ALREADY_GRADED,
    R_INVALID_TEMPORAL_INPUT, R_INFORMATION_NOT_AVAILABLE,
)

# Refusal codes: any verdict carrying one of these is a NO.
REFUSAL_CODES: FrozenSet[str] = frozenset(REASON_CODES) - frozenset(
    (R_OK_PROSPECTIVE, R_OK_GRADE_READY))


class TemporalPolicyError(Exception):
    """Raised when a temporal question cannot be answered safely."""

    def __init__(self, code: str, detail: str, **extra: Any):
        self.code = code
        self.detail = detail
        self.extra = extra
        super().__init__("%s: %s" % (code, detail))

    def as_dict(self) -> Dict[str, Any]:
        out = {"error": "TemporalPolicyError", "code": self.code,
               "detail": self.detail, "eligible": False}
        out.update(self.extra)
        return out


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------

def is_iso_z(s: Any) -> bool:
    if not isinstance(s, str) or not s.endswith("Z") or len(s) < 20:
        return False
    try:
        datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
        return True
    except ValueError:
        return False


def iso_z(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def require_utc(value: Any) -> datetime:
    """Parse an ISO-8601 Z timestamp or a datetime. Naive input refused."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise TemporalPolicyError(
                R_NON_UTC_TIMESTAMP,
                "naive datetime supplied where a UTC instant is required")
        return value.astimezone(UTC)
    if not is_iso_z(value):
        raise TemporalPolicyError(
            R_NON_UTC_TIMESTAMP,
            "timestamp %r is not UTC ISO-8601 ending in Z" % (value,))
    return datetime.strptime(str(value), "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=UTC)


def _coerce_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    d = date(year, month, 1)
    delta = (weekday - d.weekday()) % 7
    return d + timedelta(days=delta + 7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    d = date(year, month, 28)
    while (d + timedelta(days=7)).month == month:
        d += timedelta(days=7)
    return d - timedelta(days=(d.weekday() - weekday) % 7)


def dst_start_utc(year: int) -> datetime:
    """Second Sunday in March, 02:00 local (07:00 UTC)."""
    d = _nth_weekday(year, 3, 6, 2)     # Sunday == weekday 6
    return datetime(d.year, d.month, d.day, 7, 0, 0, tzinfo=UTC)


def dst_end_utc(year: int) -> datetime:
    """First Sunday in November, 02:00 local (06:00 UTC)."""
    d = _nth_weekday(year, 11, 6, 1)
    return datetime(d.year, d.month, d.day, 6, 0, 0, tzinfo=UTC)


def eastern_offset(dt_utc: datetime) -> timedelta:
    dt = require_utc(dt_utc)
    year = dt.year
    return EDT if (dst_start_utc(year) <= dt < dst_end_utc(year)) else EST


def eastern_datetime(dt_utc: datetime) -> datetime:
    return (require_utc(dt_utc) + eastern_offset(dt_utc)).replace(tzinfo=None)


def eastern_date(dt_utc: datetime) -> date:
    """US/Eastern calendar date. All session math uses Eastern dates."""
    return eastern_datetime(dt_utc).date()


def eastern_to_utc(naive_local: datetime) -> Tuple[datetime, str]:
    """Naive US/Eastern wall clock -> UTC.

    Returns (utc, note) where note is one of:
      normal | ambiguous_first | nonexistent_snapped
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
    # Skipped hour at spring-forward: snap to the transition instant.
    return dst_start_utc(naive_local.year), "nonexistent_snapped"


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------

class SimpleUSMarketCalendar:
    """Minimal, self-contained US equity session calendar.

    Covers weekdays, the standard NYSE holiday set (with observed-date
    shifting) and 13:00 early closes. It exists so this module can answer
    temporal questions with NO dependency on the scheduler. Callers with a
    richer calendar (the scheduler's, with its own year caches) register it
    via `set_default_calendar`; the policy logic is identical either way.
    """

    VERSION = "SimpleUSMarketCalendar-v1"

    def __init__(self, early_closes: Optional[Sequence[str]] = None,
                 extra_holidays: Optional[Sequence[str]] = None):
        self._early = set(early_closes or self._default_early_closes())
        self._extra = set(extra_holidays or ())
        self._holiday_cache: Dict[int, FrozenSet[str]] = {}
        self._days_cache: Dict[int, Tuple[str, ...]] = {}

    def __repr__(self) -> str:  # pragma: no cover
        return "<%s>" % self.VERSION

    @staticmethod
    def _default_early_closes() -> Tuple[str, ...]:
        return (
            "2026-11-27",  # day after Thanksgiving
            "2026-12-24",  # Christmas Eve
            "2025-11-28", "2025-12-24",
            "2027-11-26", "2027-12-24",
        )

    def holidays(self, year: int) -> FrozenSet[str]:
        if year in self._holiday_cache:
            return self._holiday_cache[year]
        hs: List[date] = [
            date(year, 1, 1),                                  # New Year
            _nth_weekday(year, 1, 0, 3),                       # MLK
            _nth_weekday(year, 2, 0, 3),                       # Presidents
            self._good_friday(year),
            _last_weekday(year, 5, 0),                         # Memorial
            date(year, 7, 4),                                  # Independence
            _nth_weekday(year, 9, 0, 1),                       # Labor
            _nth_weekday(year, 11, 3, 4),                      # Thanksgiving
            date(year, 12, 25),                                # Christmas
        ]
        out: set = set()
        for h in hs:
            if h.weekday() == 5:      # Saturday -> observed Friday
                h = h - timedelta(days=1)
            elif h.weekday() == 6:    # Sunday -> observed Monday
                h = h + timedelta(days=1)
            out.add(h.isoformat())
        out |= {d for d in self._extra if d.startswith(str(year))}
        frozen = frozenset(out)
        # Cache the holiday set FIRST. `trading_days` reads it back through
        # `is_trading_day`; populating both in one step would recurse.
        self._holiday_cache[year] = frozen
        return frozen

    @staticmethod
    def _good_friday(year: int) -> date:
        # Anonymous Gregorian computus (Meeus/Jones/Butcher).
        a = year % 19
        b, c = divmod(year, 100)
        d, e = divmod(b, 4)
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i, k = divmod(c, 4)
        m = (32 + 2 * e + 2 * i - h - k) % 7
        n = (h + m - 7 * ((a + 11 * h + 22 * m) // 451)) // 451
        month = (h + m - 7 * n + 114) // 31
        day = ((h + m - 7 * n + 114) % 31) + 1
        return date(year, month, day) - timedelta(days=2)

    def is_trading_day(self, day: Any) -> bool:
        d = _coerce_date(day)
        if d.weekday() >= 5:
            return False
        return d.isoformat() not in self.holidays(d.year)

    def trading_days(self, start: Any, end: Any) -> List[date]:
        s, e = _coerce_date(start), _coerce_date(end)
        if s.year == e.year and s == date(s.year, 1, 1) and \
                e == date(e.year, 12, 31) and s.year in self._days_cache:
            return [date.fromisoformat(x) for x in self._days_cache[s.year]]
        out: List[date] = []
        d = s
        while d <= e:
            if self.is_trading_day(d):
                out.append(d)
            d += timedelta(days=1)
        if s.year == e.year and s == date(s.year, 1, 1) and \
                e == date(e.year, 12, 31):
            self._days_cache[s.year] = tuple(x.isoformat() for x in out)
        return out

    def is_early_close(self, day: Any) -> bool:
        return _coerce_date(day).isoformat() in self._early

    def market_open_utc(self, day: Any) -> datetime:
        d = _coerce_date(day)
        utc, _note = eastern_to_utc(datetime(d.year, d.month, d.day, 9, 30))
        return utc

    def market_close_utc(self, day: Any) -> datetime:
        d = _coerce_date(day)
        hour = 13 if self.is_early_close(d) else 16
        utc, _note = eastern_to_utc(datetime(d.year, d.month, d.day, hour, 0))
        return utc

    def session_index(self, day: Any) -> Optional[int]:
        d = _coerce_date(day)
        days = self.trading_days(date(d.year, 1, 1), date(d.year, 12, 31))
        try:
            return days.index(d)
        except ValueError:
            return None

    def offset_session(self, day: Any, n: int) -> Optional[date]:
        """The session n trading days after `day`, crossing year bounds."""
        d = _coerce_date(day)
        if n >= 0:
            count, cur = 0, d
            while count <= n + 64:
                cur = cur + timedelta(days=1)
                if self.is_trading_day(cur):
                    count += 1
                    if count == n:
                        return cur
            return None
        count, cur = 0, d
        need = -n
        while count <= need + 64:
            cur = cur - timedelta(days=1)
            if self.is_trading_day(cur):
                count += 1
                if count == need:
                    return cur
        return None


_DEFAULT_CALENDAR: Any = SimpleUSMarketCalendar()


class CalendarAdapter:
    """Wrap a partial calendar so the policy never breaks on a missing method.

    W9-A5-02: registering a foreign calendar that implements only part of
    the interface (the scheduler's MarketCalendar has no `offset_session`)
    made `outcome_availability` raise AttributeError for every caller, in
    every process that had merely imported the scheduler. A shared policy
    must not be able to break that way: it derives the missing operations
    from the ones the calendar does provide.

    Nothing here invents a session. If the calendar cannot answer, the
    adapter refuses rather than guessing.
    """

    def __init__(self, inner: Any):
        self.inner = inner
        self._missing: List[str] = []

    def __repr__(self) -> str:  # pragma: no cover
        return "<CalendarAdapter(%r)>" % (self.inner,)

    @property
    def missing_methods(self) -> Tuple[str, ...]:
        return tuple(self._missing)

    def _derive_offset_session(self, day: Any, n: int) -> Optional[date]:
        """Derive session offset from `trading_days` when not provided."""
        d = _coerce_date(day)
        if not hasattr(self.inner, "trading_days"):
            return None
        # Walk a window wide enough to cross holidays and year ends.
        span_days = max(40, int(abs(n) * 2) + 40)
        if n >= 0:
            start, end = d, d + timedelta(days=span_days)
        else:
            start, end = d - timedelta(days=span_days), d
        try:
            days = [x if isinstance(x, date) else _coerce_date(x)
                    for x in self.inner.trading_days(start, end)]
        except Exception:                               # noqa: BLE001
            return None
        days = sorted(set(days))
        if n >= 0:
            later = [x for x in days if x > d]
            return later[n - 1] if 0 < n <= len(later) else (
                days[0] if n == 0 and days and days[0] >= d else None)
        earlier = [x for x in days if x < d]
        return earlier[len(earlier) + n] if -n <= len(earlier) else None

    def is_trading_day(self, day: Any) -> bool:
        fn = getattr(self.inner, "is_trading_day", None)
        if fn is None:
            days = self.trading_days(day, day)
            return bool(days)
        return bool(fn(_coerce_date(day)))

    def trading_days(self, start: Any, end: Any) -> List[date]:
        fn = getattr(self.inner, "trading_days", None)
        if fn is None:
            raise TemporalPolicyError(
                R_MISSING_REQUIRED_FIELDS,
                "calendar %r implements neither trading_days nor "
                "is_trading_day" % (self.inner,))
        out = fn(_coerce_date(start), _coerce_date(end))
        return [x if isinstance(x, date) else _coerce_date(x) for x in out]

    def market_close_utc(self, day: Any) -> datetime:
        fn = getattr(self.inner, "market_close_utc", None)
        if fn is None:
            raise TemporalPolicyError(
                R_MISSING_REQUIRED_FIELDS,
                "calendar %r does not implement market_close_utc()"
                % (self.inner,))
        return require_utc(fn(_coerce_date(day)))

    def market_open_utc(self, day: Any) -> datetime:
        fn = getattr(self.inner, "market_open_utc", None)
        if fn is None:
            return self.market_close_utc(day)
        return require_utc(fn(_coerce_date(day)))

    def is_early_close(self, day: Any) -> bool:
        fn = getattr(self.inner, "is_early_close", None)
        if fn is None:
            return False
        return bool(fn(_coerce_date(day)))

    def offset_session(self, day: Any, n: int) -> Optional[date]:
        fn = getattr(self.inner, "offset_session", None)
        if fn is not None:
            try:
                out = fn(_coerce_date(day), int(n))
            except Exception:                           # noqa: BLE001
                out = None
            if out is not None:
                return out if isinstance(out, date) else _coerce_date(out)
        if "offset_session" not in self._missing:
            self._missing.append("offset_session")
        return self._derive_offset_session(day, int(n))

    def session_index(self, day: Any) -> Optional[int]:
        fn = getattr(self.inner, "session_index", None)
        if fn is not None:
            return fn(_coerce_date(day))
        d = _coerce_date(day)
        try:
            days = self.trading_days(date(d.year, 1, 1), d)
        except TemporalPolicyError:
            return None
        return len(days) - 1 if days and days[-1] == d else None


def set_default_calendar(cal: Any) -> None:
    """Register a richer calendar. Callers only; never imported from here.

    The scheduler owns its own calendar implementation (year caches,
    holiday data). It registers it here so both components answer temporal
    questions from the SAME sessions, without either importing the other's
    policy.

    The calendar is WRAPPED, not used raw: a partial implementation is
    completed by derivation rather than allowed to raise AttributeError
    inside shared policy code (W9-A5-02).
    """
    global _DEFAULT_CALENDAR
    required = ("market_close_utc",)
    for name in required:
        if not hasattr(cal, name):
            raise TemporalPolicyError(
                R_MISSING_REQUIRED_FIELDS,
                "calendar %r does not implement %s()" % (cal, name))
    if not (hasattr(cal, "is_trading_day") or hasattr(cal, "trading_days")):
        raise TemporalPolicyError(
            R_MISSING_REQUIRED_FIELDS,
            "calendar %r implements neither is_trading_day nor "
            "trading_days()" % (cal,))
    _DEFAULT_CALENDAR = CalendarAdapter(cal)


def get_default_calendar() -> Any:
    return _DEFAULT_CALENDAR


# ---------------------------------------------------------------------------
# Quarantine registry
# ---------------------------------------------------------------------------

@dataclass
class QuarantineEntry:
    scope: str                  # cohort_id or record_hash
    reason: str
    decided_by: str
    decided_at_utc: str
    permanent: bool = True

    def as_dict(self) -> Dict[str, Any]:
        return {
            "scope": self.scope, "reason": self.reason,
            "decided_by": self.decided_by,
            "decided_at_utc": self.decided_at_utc,
            "permanent": self.permanent,
        }


_QUARANTINE: Dict[str, QuarantineEntry] = {}


def quarantine(scope: str, reason: str, decided_by: str,
               when_utc: Optional[str] = None,
               permanent: bool = True) -> QuarantineEntry:
    """Quarantine a cohort or a single record from performance evaluation.

    Quarantine is the correct tool for the 18 retrospective records: they
    stay on disk for pipeline diagnostics but can never enter a
    performance aggregate.
    """
    e = QuarantineEntry(scope=scope, reason=reason, decided_by=decided_by,
                        decided_at_utc=when_utc or iso_z(
                            datetime.now(UTC)),
                        permanent=permanent)
    _QUARANTINE[scope] = e
    return e


def unquarantine(scope: str) -> None:
    _QUARANTINE.pop(scope, None)


def quarantine_status_for(*scopes: Optional[str]) -> str:
    for s in scopes:
        if s and s in _QUARANTINE:
            return "QUARANTINED:%s" % _QUARANTINE[s].reason
    return NOT_QUARANTINED


def quarantine_registry() -> Dict[str, Dict[str, Any]]:
    return {k: v.as_dict() for k, v in sorted(_QUARANTINE.items())}


# ---------------------------------------------------------------------------
# The verdict
# ---------------------------------------------------------------------------

@dataclass
class TemporalVerdict:
    """The single canonical answer to a temporal eligibility question."""

    prediction_eligibility: str
    grade_eligibility: str
    reason_code: str
    reason: str
    info_cutoff: Optional[str]
    outcome_available: bool
    outcome_available_at: Optional[str]
    required_expiry: Optional[str]
    data_coverage: str
    provenance_status: str
    quarantine_status: str
    policy_version: str = TEMPORAL_POLICY_VERSION
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def prediction_eligible(self) -> bool:
        return self.prediction_eligibility == ELIGIBLE

    @property
    def grade_eligible(self) -> bool:
        return self.grade_eligibility == ELIGIBLE

    def as_dict(self) -> Dict[str, Any]:
        return {
            "policy_version": self.policy_version,
            "prediction_eligibility": self.prediction_eligibility,
            "prediction_eligible": self.prediction_eligible,
            "grade_eligibility": self.grade_eligibility,
            "grade_eligible": self.grade_eligible,
            "reason_code": self.reason_code,
            "reason": self.reason,
            "info_cutoff": self.info_cutoff,
            "outcome_available": self.outcome_available,
            "outcome_available_at": self.outcome_available_at,
            "required_expiry": self.required_expiry,
            "data_coverage": self.data_coverage,
            "provenance_status": self.provenance_status,
            "quarantine_status": self.quarantine_status,
            "details": dict(self.details),
        }

    def raise_if_prediction_ineligible(self) -> "TemporalVerdict":
        if not self.prediction_eligible:
            raise TemporalPolicyError(
                self.reason_code, self.reason, verdict=self.as_dict())
        return self

    def raise_if_grade_ineligible(self) -> "TemporalVerdict":
        if not self.grade_eligible:
            raise TemporalPolicyError(
                self.reason_code, self.reason, verdict=self.as_dict())
        return self


REQUIRED_PREDICTION_FIELDS: Tuple[str, ...] = (
    "cohort_id", "creation_ts", "info_cutoff", "earliest_tradable",
    "horizon_days",
)


# ---------------------------------------------------------------------------
# Coverage classification
# ---------------------------------------------------------------------------

def classify_data_coverage(rec: Dict[str, Any]) -> str:
    """COMPLETE / PARTIAL / MISSING / UNKNOWN from the record's own state."""
    mds = rec.get("missing_data_state")
    if mds is None:
        return COVERAGE_UNKNOWN
    if isinstance(mds, dict):
        state = str(mds.get("state", "unknown")).lower()
    else:
        state = str(mds).lower()
    if state in ("complete", "ok", "none"):
        return COVERAGE_COMPLETE
    if state in ("gapped", "partial", "degraded"):
        return COVERAGE_PARTIAL
    if state in ("empty", "missing", "unavailable"):
        return COVERAGE_MISSING
    return COVERAGE_UNKNOWN


# ---------------------------------------------------------------------------
# Provenance (the core rule)
# ---------------------------------------------------------------------------

def provenance_decision(creation_ts: Any, earliest_tradable: Any,
                        calendar: Any = None) -> Dict[str, Any]:
    """PROSPECTIVE or RETROSPECTIVE_BACKFILL. Fail-closed, monotone.

      RETRO if eastern_date(creation_ts) > earliest_tradable
      RETRO if creation_ts > market_close_utc(earliest_tradable)
      else PROSPECTIVE

    The first test is the mandate's literal rule. The second closes the
    same-session hole: a record written at 23:00 on the entry date, after
    the close, still postdates the outcome it claims to forecast.
    """
    cal = calendar or _DEFAULT_CALENDAR
    created = require_utc(creation_ts)
    trade_day = _coerce_date(earliest_tradable)
    created_day = eastern_date(created)
    close_utc = cal.market_close_utc(trade_day)

    base = {
        "creation_ts": iso_z(created),
        "earliest_tradable": trade_day.isoformat(),
        "creation_eastern_date": created_day.isoformat(),
        "entry_close_utc": iso_z(close_utc),
    }

    # A prediction whose earliest_tradable is not a trading session has no
    # entry close at all. Previously such a record borrowed an invented
    # close from a non-session date and could classify as PROSPECTIVE --
    # a Saturday "tradable" date made every creation time look early.
    is_trading = getattr(cal, "is_trading_day", None)
    if is_trading is not None:
        try:
            trading = bool(is_trading(trade_day))
        except Exception:                       # noqa: BLE001
            trading = False       # a calendar that cannot answer is not
            #                       evidence that the day trades
        if not trading:
            out = {
                "provenance_mode": RETROSPECTIVE_BACKFILL,
                "prospective_evidence": False,
                "rule": "non_trading_earliest_tradable",
                "reason": ("earliest_tradable %s is not a trading session, "
                           "so the record has no entry close and cannot be "
                           "a forecast of anything"
                           % trade_day.isoformat()),
            }
            out.update(base)
            return out
    if created_day > trade_day:
        out = {
            "provenance_mode": RETROSPECTIVE_BACKFILL,
            "prospective_evidence": False,
            "rule": "creation_date_after_earliest_tradable",
            "reason": ("record created %s, after its own earliest_tradable "
                       "session %s -- the outcome window was already "
                       "observable when the record was written"
                       % (created_day.isoformat(), trade_day.isoformat())),
        }
        out.update(base)
        return out
    if created > close_utc:
        out = {
            "provenance_mode": RETROSPECTIVE_BACKFILL,
            "prospective_evidence": False,
            "rule": "creation_after_entry_close",
            "reason": ("record created %s, after the %s entry close at %s"
                       % (iso_z(created), trade_day.isoformat(),
                          iso_z(close_utc))),
        }
        out.update(base)
        return out
    out = {
        "provenance_mode": PROSPECTIVE,
        "prospective_evidence": True,
        "rule": "created_on_or_before_tradable_session",
        "reason": ("record created before the %s entry close -- the outcome "
                   "window was not yet observable" % trade_day.isoformat()),
    }
    out.update(base)
    return out


# ---------------------------------------------------------------------------
# Outcome availability
# ---------------------------------------------------------------------------

def _positive_horizon(value: Any) -> int:
    """A forecast horizon is a positive integer number of sessions."""
    try:
        horizon = int(value)
        valid = (not isinstance(value, bool) and horizon > 0
                 and str(value).strip() == str(horizon))
    except (TypeError, ValueError, OverflowError):
        valid = False
    if not valid:
        raise TemporalPolicyError(
            R_INVALID_TEMPORAL_INPUT,
            "horizon_days must be a positive integer number of sessions")
    return horizon


def _validate_information_cutoff(created: Any, cutoff: Any,
                                 calendar: Any) -> None:
    """The daily information cutoff must have been observable at creation.

    Non-session cutoff dates are retained for existing date-boundary records.
    A session's close is usable only once that close has occurred.
    """
    created_utc = require_utc(created)
    try:
        cutoff_day = _coerce_date(cutoff)
    except (TypeError, ValueError, OverflowError):
        raise TemporalPolicyError(
            R_INVALID_TEMPORAL_INPUT, "info_cutoff must be an ISO date")
    created_day = eastern_date(created_utc)
    if cutoff_day > created_day or (
            cutoff_day == created_day
            and calendar.is_trading_day(cutoff_day)
            and calendar.market_close_utc(cutoff_day) > created_utc):
        raise TemporalPolicyError(
            R_INFORMATION_NOT_AVAILABLE,
            "info_cutoff %s was not observable at creation_ts %s"
            % (cutoff_day.isoformat(), iso_z(created_utc)))


def outcome_availability(rec: Dict[str, Any], calendar: Any = None,
                         now_utc: Any = None) -> Dict[str, Any]:
    """When does this record's outcome become observable, and has it?

    The outcome of a horizon-H prediction entered at session S is
    observable at the CLOSE of session S+H. Before that instant no grade
    may exist, because the label does not exist yet.
    """
    cal = calendar or _DEFAULT_CALENDAR
    try:
        trade_day = _coerce_date(rec["earliest_tradable"])
        horizon = _positive_horizon(rec["horizon_days"])
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise TemporalPolicyError(
            R_INVALID_TEMPORAL_INPUT,
            "invalid outcome window: %s" % exc) from exc
    maturity = cal.offset_session(trade_day, horizon)
    if maturity is None:
        raise TemporalPolicyError(
            R_OUTCOME_DATE_NOT_IN_CALENDAR,
            "cannot resolve the session %d trading days after %s"
            % (horizon, trade_day.isoformat()))
    close_utc = cal.market_close_utc(maturity)
    now = require_utc(now_utc) if now_utc is not None else datetime.now(UTC)
    return {
        "maturity_date": maturity.isoformat(),
        "outcome_available_at": iso_z(close_utc),
        "outcome_available": now >= close_utc,
        "now_utc": iso_z(now),
        "horizon_days": horizon,
        "earliest_tradable": trade_day.isoformat(),
    }


# ---------------------------------------------------------------------------
# The two verdicts
# ---------------------------------------------------------------------------

def prediction_eligibility_verdict(
    rec: Dict[str, Any],
    calendar: Any = None,
    now_utc: Any = None,
    frozen_dataset_sha: Optional[str] = None,
) -> TemporalVerdict:
    """May this record COUNT as prospective evidence?

    Asked at creation time and re-asked at every consumption point. It
    does not consider whether the outcome has arrived -- a prediction can
    be perfectly prospective while still maturing.
    """
    cal = calendar or _DEFAULT_CALENDAR
    cid = rec.get("cohort_id")
    qstat = quarantine_status_for(cid, rec.get("record_hash"))

    missing = [k for k in REQUIRED_PREDICTION_FIELDS if rec.get(k) is None]
    if missing:
        return TemporalVerdict(
            prediction_eligibility=INELIGIBLE, grade_eligibility=INELIGIBLE,
            reason_code=R_MISSING_REQUIRED_FIELDS,
            reason="prediction is missing required temporal field(s): %s"
                   % ", ".join(missing),
            info_cutoff=rec.get("info_cutoff"),
            outcome_available=False, outcome_available_at=None,
            required_expiry=None, data_coverage=COVERAGE_UNKNOWN,
            provenance_status=PROVENANCE_UNKNOWN,
            quarantine_status=qstat, details={"missing_fields": missing})

    try:
        _validate_information_cutoff(rec["creation_ts"], rec["info_cutoff"], cal)
        _positive_horizon(rec["horizon_days"])
        prov = provenance_decision(rec["creation_ts"],
                                   rec["earliest_tradable"], calendar=cal)
        avail = outcome_availability(rec, calendar=cal, now_utc=now_utc)
    except (TemporalPolicyError, TypeError, ValueError, OverflowError) as exc:
        if not isinstance(exc, TemporalPolicyError):
            exc = TemporalPolicyError(R_INVALID_TEMPORAL_INPUT,
                                      "invalid prediction window: %s" % exc)
        return TemporalVerdict(
            prediction_eligibility=INELIGIBLE, grade_eligibility=INELIGIBLE,
            reason_code=exc.code, reason=exc.detail,
            info_cutoff=rec.get("info_cutoff"), outcome_available=False,
            outcome_available_at=None, required_expiry=None,
            data_coverage=COVERAGE_UNKNOWN,
            provenance_status=PROVENANCE_UNKNOWN,
            quarantine_status=qstat, details=exc.extra)

    coverage = classify_data_coverage(rec)

    if qstat != NOT_QUARANTINED:
        return _verdict(INELIGIBLE, INELIGIBLE, R_QUARANTINED,
                        "record is quarantined from performance evaluation: "
                        "%s" % qstat, rec, prov, avail, coverage, qstat)

    if prov["provenance_mode"] != PROSPECTIVE:
        code = (R_CREATED_AFTER_EARLIEST_TRADABLE
                if prov["rule"] == "creation_date_after_earliest_tradable"
                else R_CREATED_AFTER_ENTRY_CLOSE)
        return _verdict(
            INELIGIBLE, GATED, code, prov["reason"], rec, prov, avail,
            coverage, qstat,
            extra={"provenance_rule": prov["rule"]})

    if frozen_dataset_sha and rec.get("dataset_version") != frozen_dataset_sha:
        return _verdict(
            INELIGIBLE, INELIGIBLE, R_DATASET_DRIFT,
            "record's dataset_version %s differs from the frozen dataset "
            "%s; its input identity cannot be verified against the cohort"
            % (rec.get("dataset_version"), frozen_dataset_sha),
            rec, prov, avail, coverage, qstat,
            extra={"record_dataset": rec.get("dataset_version"),
                   "frozen_dataset": frozen_dataset_sha})

    if coverage in (COVERAGE_MISSING, COVERAGE_UNKNOWN):
        return _verdict(
            INELIGIBLE, GATED, R_DATA_COVERAGE_INCOMPLETE,
            "input coverage is %s; a forecast made over incomplete inputs "
            "is not a clean prospective observation" % coverage,
            rec, prov, avail, coverage, qstat)

    return _verdict(ELIGIBLE, GATED if not avail["outcome_available"]
                    else ELIGIBLE, R_OK_PROSPECTIVE, prov["reason"],
                    rec, prov, avail, coverage, qstat)


def grade_eligibility_verdict(
    rec: Dict[str, Any],
    calendar: Any = None,
    now_utc: Any = None,
    already_graded: bool = False,
    frozen_dataset_sha: Optional[str] = None,
) -> TemporalVerdict:
    """May this record be GRADED, and does that grade count prospectively?

    GATED means "not yet -- the outcome does not exist". INELIGIBLE means
    "never". Confusing the two is how a retrospective backfill gets
    laundered into a prospective claim, so they are different codes.
    """
    cal = calendar or _DEFAULT_CALENDAR
    if str(rec.get("record_type", "prediction")) != "prediction":
        return TemporalVerdict(
            prediction_eligibility=INELIGIBLE,
            grade_eligibility=INELIGIBLE, reason_code=R_NOT_A_PREDICTION,
            reason="only prediction records may be graded",
            info_cutoff=rec.get("info_cutoff"), outcome_available=False,
            outcome_available_at=None, required_expiry=None,
            data_coverage=COVERAGE_UNKNOWN,
            provenance_status=PROVENANCE_UNKNOWN,
            quarantine_status=quarantine_status_for(
                rec.get("cohort_id"), rec.get("record_hash")))

    pred = prediction_eligibility_verdict(
        rec, calendar=cal, now_utc=now_utc,
        frozen_dataset_sha=frozen_dataset_sha)
    # Calibration requires a valid historical window, not invalid timing
    # or an input identity that cannot be verified against the frozen cohort.
    if pred.reason_code in (R_INVALID_TEMPORAL_INPUT,
                            R_INFORMATION_NOT_AVAILABLE, R_DATASET_DRIFT,
                            R_MISSING_REQUIRED_FIELDS, R_NON_UTC_TIMESTAMP):
        return pred
    if pred.quarantine_status != NOT_QUARANTINED and \
            pred.reason_code != R_QUARANTINED:
        pred.quarantine_status = "QUARANTINED:%s" % R_QUARANTINED

    try:
        avail = outcome_availability(rec, calendar=cal, now_utc=now_utc)
    except TemporalPolicyError as exc:
        return TemporalVerdict(
            prediction_eligibility=pred.prediction_eligibility,
            grade_eligibility=INELIGIBLE, reason_code=exc.code,
            reason=exc.detail, info_cutoff=rec.get("info_cutoff"),
            outcome_available=False, outcome_available_at=None,
            required_expiry=None, data_coverage=pred.data_coverage,
            provenance_status=pred.provenance_status,
            quarantine_status=pred.quarantine_status, details=exc.extra)

    details = dict(pred.details)
    details.update(avail)

    if not avail["outcome_available"]:
        return TemporalVerdict(
            prediction_eligibility=pred.prediction_eligibility,
            grade_eligibility=GATED,
            reason_code=R_OUTCOME_NOT_YET_AVAILABLE,
            reason="outcome window closes at the %s close (%s); the label "
                   "does not exist yet"
                   % (avail["maturity_date"], avail["outcome_available_at"]),
            info_cutoff=rec.get("info_cutoff"), outcome_available=False,
            outcome_available_at=avail["outcome_available_at"],
            required_expiry=avail["outcome_available_at"],
            data_coverage=pred.data_coverage,
            provenance_status=pred.provenance_status,
            quarantine_status=pred.quarantine_status, details=details)

    if already_graded:
        return TemporalVerdict(
            prediction_eligibility=pred.prediction_eligibility,
            grade_eligibility=INELIGIBLE, reason_code=R_ALREADY_GRADED,
            reason="this prediction has already been graded; duplicate "
                   "grades duplicate financial effects",
            info_cutoff=rec.get("info_cutoff"), outcome_available=True,
            outcome_available_at=avail["outcome_available_at"],
            required_expiry=avail["outcome_available_at"],
            data_coverage=pred.data_coverage,
            provenance_status=pred.provenance_status,
            quarantine_status=pred.quarantine_status, details=details)

    # A retrospective record may still be graded -- it is a legitimate
    # calibration demonstration -- but the grade is permanently marked
    # non-prospective and can never enter a prospective aggregate.
    if not pred.prediction_eligible:
        return TemporalVerdict(
            prediction_eligibility=INELIGIBLE, grade_eligibility=ELIGIBLE,
            reason_code=pred.reason_code,
            reason=pred.reason + " -- gradable as a calibration "
                    "demonstration only, permanently excluded from "
                    "prospective aggregates",
            info_cutoff=rec.get("info_cutoff"), outcome_available=True,
            outcome_available_at=avail["outcome_available_at"],
            required_expiry=avail["outcome_available_at"],
            data_coverage=pred.data_coverage,
            provenance_status=pred.provenance_status,
            quarantine_status=pred.quarantine_status, details=details)

    return TemporalVerdict(
        prediction_eligibility=ELIGIBLE, grade_eligibility=ELIGIBLE,
        reason_code=R_OK_GRADE_READY,
        reason="outcome available since %s and the record is prospective"
               % avail["outcome_available_at"],
        info_cutoff=rec.get("info_cutoff"), outcome_available=True,
        outcome_available_at=avail["outcome_available_at"],
        required_expiry=avail["outcome_available_at"],
        data_coverage=pred.data_coverage, provenance_status=PROSPECTIVE,
        quarantine_status=pred.quarantine_status, details=details)


def _verdict(pred_el: str, grade_el: str, code: str, reason: str,
             rec: Dict[str, Any], prov: Dict[str, Any],
             avail: Dict[str, Any], coverage: str, qstat: str,
             extra: Optional[Dict[str, Any]] = None) -> TemporalVerdict:
    details: Dict[str, Any] = {}
    details.update(prov)
    details.update(avail)
    if extra:
        details.update(extra)
    return TemporalVerdict(
        prediction_eligibility=pred_el, grade_eligibility=grade_el,
        reason_code=code, reason=reason, info_cutoff=rec.get("info_cutoff"),
        outcome_available=bool(avail.get("outcome_available")),
        outcome_available_at=avail.get("outcome_available_at"),
        required_expiry=avail.get("outcome_available_at"),
        data_coverage=coverage,
        provenance_status=prov.get("provenance_mode", PROVENANCE_UNKNOWN),
        quarantine_status=qstat, details=details)


# ---------------------------------------------------------------------------
# Convenience adapters used by domain and audit consumers
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Freshness (F-05: on-time data must be distinguishable from late or stale)
#
# This is a TEMPORAL question, so it belongs in the temporal policy rather
# than in the scheduler that happens to first need it. The scheduler
# delegates here.
# ---------------------------------------------------------------------------

FRESH = "FRESH"
LATE = "LATE"
STALE = "STALE"
MISSING = "MISSING"
DATA_STATES: Tuple[str, ...] = (FRESH, LATE, STALE, MISSING)

DEFAULT_FRESHNESS_SLA_SECONDS = 36 * 3600


def classify_freshness(availability_ts: Any,
                       observed_value: Any = True,
                       now_utc: Any = None,
                       expected_ts: Any = None,
                       sla_seconds: Optional[int] = None,
                       late_grace_seconds: int = 0) -> Dict[str, Any]:
    """FRESH / LATE / STALE / MISSING for one observation.

    MISSING -> no observation at all.        Blocks output.
    STALE   -> older than the freshness SLA. Blocks output.
    LATE    -> arrived after the expected time but inside the SLA.
               Accepted and MARKED; never silently treated as on-time.
    FRESH   -> on time and inside the SLA.

    `observed_value` is tested for None only; pass the quote's value (or
    omit it) so the policy never needs to know what a Quote object is.
    """
    now = require_utc(now_utc) if now_utc is not None else datetime.now(UTC)
    sla = DEFAULT_FRESHNESS_SLA_SECONDS if sla_seconds is None \
        else int(sla_seconds)
    if availability_ts is None or observed_value is None:
        return {"state": MISSING, "accepted": False,
                "reason": "no observation available",
                "availability_ts": None, "age_seconds": None}
    avail = require_utc(availability_ts)
    age = (now - avail).total_seconds()
    if age > sla:
        return {"state": STALE, "accepted": False,
                "reason": "observation age %.0fs exceeds freshness SLA %.0fs"
                          % (age, sla),
                "availability_ts": iso_z(avail),
                "age_seconds": round(age, 3)}
    if expected_ts is not None:
        lateness = (avail - require_utc(expected_ts)).total_seconds()
        if lateness > late_grace_seconds:
            return {"state": LATE, "accepted": True,
                    "reason": "arrived %.0fs after expected availability"
                              % lateness,
                    "availability_ts": iso_z(avail),
                    "age_seconds": round(age, 3),
                    "late_seconds": round(lateness, 3)}
    return {"state": FRESH, "accepted": True, "reason": "on time",
            "availability_ts": iso_z(avail), "age_seconds": round(age, 3)}


def _temporal_fields(rec: Dict[str, Any]) -> Tuple[Any, Any]:
    """(creation_ts, earliest_tradable) from a prediction OR a grade."""
    created = rec.get("creation_ts")
    tradable = rec.get("earliest_tradable")
    inner = rec.get("grades")
    if isinstance(inner, dict):
        created = created or inner.get("creation_ts")
        tradable = tradable or inner.get("earliest_tradable")
    return created, tradable


def is_prospective_evidence(rec: Dict[str, Any]) -> bool:
    """Single source of truth for prospective eligibility. No override.

    The stored `provenance_mode` stamp is a CLAIM, not an authority. This
    re-derives the verdict from the record's own timestamps and requires
    the two to agree. Without this, editing two stored fields on a
    retrospective grade was enough to launder it into a prospective
    aggregate -- the write path re-derived, the read path did not, and
    every consumer reads through the read path.

    A record whose timestamps are absent or unusable CANNOT be verified,
    and unverifiable is not prospective. Failure here is fail-closed.
    """
    if not isinstance(rec, dict):
        return False
    if rec.get("provenance_mode") != PROSPECTIVE:
        return False
    if rec.get("prospective_evidence") is not True:
        return False
    created, tradable = _temporal_fields(rec)
    if not created or not tradable:
        return False
    try:
        verdict = provenance_decision(created, tradable)
        inner = rec.get("grades")
        fields = dict(inner) if isinstance(inner, dict) else {}
        fields.update({k: v for k, v in rec.items() if v is not None})
        if fields.get("info_cutoff") is not None:
            _validate_information_cutoff(created, fields["info_cutoff"],
                                         _DEFAULT_CALENDAR)
        if fields.get("horizon_days") is not None:
            _positive_horizon(fields["horizon_days"])
    except (TemporalPolicyError, TypeError, ValueError):
        return False
    if verdict["provenance_mode"] != PROSPECTIVE:
        return False
    return not quarantine_status_for(
        rec.get("cohort_id"), rec.get("record_hash")) != NOT_QUARANTINED


def assert_record_timestamps(rec: Dict[str, Any],
                             label: str = "record") -> bool:
    """Every emitted timestamp must be UTC ISO-8601 with explicit Z."""
    bad = []
    for key in sorted(rec.keys()):
        if key.endswith("_utc") or key.endswith("_ts"):
            val = rec[key]
            if val is None or not is_iso_z(val):
                bad.append("%s=%r" % (key, val))
    if bad:
        raise TemporalPolicyError(
            R_NON_UTC_TIMESTAMP,
            "%s has non-UTC-ISO-8601 timestamps: %s"
            % (label, ", ".join(bad)), bad=bad)
    return True


def policy_contract() -> Dict[str, Any]:
    """The canonical contract, published so every consumer can assert it."""
    return {
        "policy_version": TEMPORAL_POLICY_VERSION,
        "owner": "temporal_policy (neutral domain component)",
        "consumers": ["scheduler", "shadow.prediction_creation",
                      "shadow.grading", "research_evaluation",
                      "decision_records", "audit_tools"],
        "outputs": {
            "prediction_eligibility": [ELIGIBLE, INELIGIBLE],
            "grade_eligibility": [ELIGIBLE, GATED, INELIGIBLE],
            "reason_code": list(REASON_CODES),
            "info_cutoff": "ISO date of the last observable session",
            "outcome_available": "bool",
            "outcome_available_at": "UTC ISO-8601 Z or null",
            "required_expiry": "UTC ISO-8601 Z or null",
            "data_coverage": list(COVERAGE_STATES),
            "provenance_status": list(PROVENANCE_STATUSES),
            "quarantine_status": "NOT_QUARANTINED | QUARANTINED:<reason>",
        },
        "rule": (
            "PROSPECTIVE iff eastern_date(creation_ts) <= earliest_tradable "
            "AND creation_ts <= market_close_utc(earliest_tradable). "
            "Otherwise RETROSPECTIVE_BACKFILL, permanently ineligible."),
        "monotone": True,
        "override_parameter": None,
    }


def contract_hash() -> str:
    return hashlib.sha256(
        json.dumps(policy_contract(), sort_keys=True).encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def _selftest() -> int:
    failures: List[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        if not cond:
            failures.append("%s %s" % (name, detail))
        print("[%s] %s%s" % ("PASS" if cond else "FAIL", name,
                             (" :: " + detail) if detail else ""))

    cal = SimpleUSMarketCalendar()

    # -- DST ------------------------------------------------------------
    check("dst-spring-forward",
          eastern_offset(dst_start_utc(2026) - timedelta(seconds=1)) == EST
          and eastern_offset(dst_start_utc(2026)) == EDT)
    check("dst-fall-back",
          eastern_offset(dst_end_utc(2026) - timedelta(seconds=1)) == EDT
          and eastern_offset(dst_end_utc(2026)) == EST)
    check("early-close-13h",
          cal.market_close_utc("2026-11-27").hour ==
          cal.market_close_utc("2026-11-27").hour and
          eastern_to_utc(datetime(2026, 11, 27, 13, 0))[0] ==
          cal.market_close_utc("2026-11-27"))
    check("normal-close-16h",
          eastern_to_utc(datetime(2026, 8, 3, 16, 0))[0]
          == cal.market_close_utc("2026-08-03"))

    # -- holidays -------------------------------------------------------
    check("weekend-not-trading-day",
          not cal.is_trading_day("2026-08-29")
          and not cal.is_trading_day("2026-08-30"))
    check("thanksgiving-observed",
          not cal.is_trading_day("2026-11-26"))
    check("christmas-observed-friday",
          not cal.is_trading_day("2021-12-24"),
          "2021-12-25 is a Saturday -> observed Fri 24th")

    # -- provenance -----------------------------------------------------
    p1 = provenance_decision("2026-08-03T12:00:00Z", "2026-08-03",
                             calendar=cal)
    check("same-day-before-close-is-prospective",
          p1["provenance_mode"] == PROSPECTIVE, p1["rule"])
    p2 = provenance_decision("2026-08-03T23:00:00Z", "2026-08-03",
                             calendar=cal)
    check("same-day-after-close-is-retro",
          p2["provenance_mode"] == RETROSPECTIVE_BACKFILL, p2["rule"])
    p3 = provenance_decision("2026-08-26T12:00:00Z", "2026-08-03",
                             calendar=cal)
    check("later-date-is-retro",
          p3["provenance_mode"] == RETROSPECTIVE_BACKFILL, p3["rule"])
    p4 = provenance_decision("2026-08-03T12:00:00Z", "2026-08-04",
                             calendar=cal)
    check("created-day-before-tradable-is-prospective",
          p4["provenance_mode"] == PROSPECTIVE, p4["rule"])

    try:
        provenance_decision("2026-08-03 12:00:00", "2026-08-03")
        check("naive-timestamp-refused", False, "no exception")
    except TemporalPolicyError as exc:
        check("naive-timestamp-refused", exc.code == R_NON_UTC_TIMESTAMP,
              exc.code)

    # -- verdicts -------------------------------------------------------
    rec_pro = {
        "record_type": "prediction", "cohort_id": "C_NEW",
        "record_hash": "h1", "creation_ts": "2026-08-03T12:00:00Z",
        "info_cutoff": "2026-08-02", "earliest_tradable": "2026-08-03",
        "horizon_days": 5,
        "missing_data_state": {"state": "complete"},
    }
    v = prediction_eligibility_verdict(rec_pro, calendar=cal,
                                       now_utc="2026-08-03T13:00:00Z")
    check("prospective-record-eligible",
          v.prediction_eligible and v.reason_code == R_OK_PROSPECTIVE
          and v.provenance_status == PROSPECTIVE, v.reason_code)
    check("verdict-carries-required-expiry",
          bool(v.required_expiry) and v.required_expiry.endswith("Z"),
          str(v.required_expiry))
    check("verdict-outcome-not-yet-available",
          v.outcome_available is False and v.grade_eligibility == GATED,
          v.grade_eligibility)

    gv = grade_eligibility_verdict(rec_pro, calendar=cal,
                                   now_utc="2026-08-10T21:00:00Z")
    check("grade-ready-after-maturity",
          gv.grade_eligible and gv.reason_code == R_OK_GRADE_READY
          and gv.outcome_available, gv.reason_code)

    gv2 = grade_eligibility_verdict(rec_pro, calendar=cal,
                                    now_utc="2026-08-04T21:00:00Z")
    check("grade-gated-before-maturity",
          gv2.grade_eligibility == GATED
          and gv2.reason_code == R_OUTCOME_NOT_YET_AVAILABLE,
          gv2.reason_code)

    rec_retro = dict(rec_pro, cohort_id="C_OLD", record_hash="h2",
                     creation_ts="2026-08-26T12:00:00Z")
    vr = prediction_eligibility_verdict(rec_retro, calendar=cal,
                                        now_utc="2026-08-26T13:00:00Z")
    check("retro-record-ineligible",
          (not vr.prediction_eligible)
          and vr.reason_code == R_CREATED_AFTER_EARLIEST_TRADABLE
          and vr.provenance_status == RETROSPECTIVE_BACKFILL, vr.reason_code)

    gr = grade_eligibility_verdict(rec_retro, calendar=cal,
                                   now_utc="2026-09-01T21:00:00Z")
    check("retro-gradable-but-not-prospective",
          gr.grade_eligible and (not gr.prediction_eligible)
          and gr.provenance_status == RETROSPECTIVE_BACKFILL, gr.reason_code)

    # -- quarantine -----------------------------------------------------
    quarantine("C_OLD", "18 records are retrospective backfills",
               "temporal-audit-2026-08-28",
               when_utc="2026-08-28T00:00:00Z")
    qr = prediction_eligibility_verdict(rec_retro, calendar=cal,
                                        now_utc="2026-09-01T21:00:00Z")
    check("quarantine-blocks-eligibility",
          (not qr.prediction_eligible) and qr.reason_code == R_QUARANTINED
          and qr.quarantine_status.startswith("QUARANTINED:"),
          qr.quarantine_status)
    unquarantine("C_OLD")

    # -- missing fields -------------------------------------------------
    vm = prediction_eligibility_verdict({"cohort_id": "X"}, calendar=cal)
    check("missing-fields-refused",
          vm.reason_code == R_MISSING_REQUIRED_FIELDS, vm.reason_code)

    # -- contract -------------------------------------------------------
    c = policy_contract()
    check("contract-has-eight-outputs",
          set(c["outputs"]) == {
              "prediction_eligibility", "grade_eligibility", "reason_code",
              "info_cutoff", "outcome_available", "outcome_available_at",
              "required_expiry", "data_coverage", "provenance_status",
              "quarantine_status"},
          str(sorted(c["outputs"])))
    check("contract-no-override", c["override_parameter"] is None)

    # -- no scheduler import -------------------------------------------
    import ast
    with open(__file__, "r", encoding="ascii") as fh:
        tree = ast.parse(fh.read())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    banned = {"scheduler", "shadow", "portfolio_engine", "risk_engine",
              "calcs_core", "calcs_household"}
    check("no-domain-or-infra-imports", not (imported & banned),
          "imported=%s" % sorted(imported))

    print("")
    if failures:
        print("FAILURES: %d" % len(failures))
        for f in failures:
            print("  " + f)
        return 1
    print("ALL TEMPORAL POLICY SELFTESTS PASSED (%s)"
          % TEMPORAL_POLICY_VERSION)
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())

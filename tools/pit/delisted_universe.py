#!/usr/bin/env python3
# -*- coding: ascii -*-
"""delisted_universe.py -- point-in-time instrument lifecycle + honest capability matrix.

MANDATE CONTEXT (D5)
--------------------
The current universe construction is survivorship-biased: today's listings are
backfilled into history, which inflates backtest results (delisted/bankrupt/
acquired names silently vanish). This module provides an HONEST path:

  * It does NOT pretend to have a full historical universe.
  * It carries lifecycle records from pluggable PROVIDERS (manual seed file,
    SEC EDGAR inference, exchange delist files), each explicitly labeled
    VERIFIED or UNVERIFIED.
  * Eligibility FAILS CLOSED: any ticker whose lifecycle is unknown for a
    given date is rejected, never assumed listed.

CAPABILITY MATRIX (honest self-assessment)
------------------------------------------
| Capability                                   | Status                                   |
|----------------------------------------------|------------------------------------------|
| Lifecycle schema + eligibility logic          | fully-corrected (this module, tested)    |
| Provider abstraction + swap-identical semantics | fully-implemented (this module, tested) |
| Seed coverage of real delisted names         | verified-seeds (5 rows, all VERIFIED     |
|                                              | against SEC/exchange primary sources)    |
| Full point-in-time universe incl. delistings | unresolved (requires external data; see  |
|                                              | _work/fis-data/delisted-acquisition-     |
|                                              | decision.md)                             |

PROVIDER ABSTRACTION
--------------------
All data enters the registry through a ProviderAdapter (structural protocol --
any object exposing fetch_lifecycle(ticker) qualifies). Three adapters ship:

  ManualAdapter       curated seed CSV (the historical default behavior).
  SecEdgarAdapter     INFERS a delisting end-event from Form 25/15 presence
                      on EDGAR. See its docstring for documented inference
                      limits (no live network in this repo -- offline mode).
  ExchangeFileAdapter reads a standard exchange delist CSV (NasdaqTrader /
                      NYSE "non-regulatory" delist format). Stub: schema and
                      mapping implemented, no bundled data.

Swapping providers must NOT change fail-closed eligibility semantics:
usable_by_strategy() rejects identically whichever adapter produced the
records (tested).

DATA ACQUISITION OPTIONS, RANKED BY COST/LICENSING
--------------------------------------------------
Superseded by _work/fis-data/delisted-acquisition-decision.md, which compares
exchange delist files, CRSP-style academic data, commercial vendors, and free
partial lists with coverage/licensing/cost columns.

SCHEMA
------
CSV columns (header required, order-insensitive):
    ticker         str, non-empty, uppercase-normalized
    listed_from    ISO date YYYY-MM-DD, first KNOWN listing/approx date
                   (grain may be month/year start; earlier dates fail closed)
    listed_to      ISO date YYYY-MM-DD or EMPTY (= open-ended / still listed
                   as far as the provider knows -- treated as open-ended)
    end_event_type one of {delisted, acquired, bankrupt, symbol_change, unknown}
    final_return_treatment one of {delisting_return_included,
                   zeroed_bankrupt, cash_acquisition_price_known, unknown}
                   (optional column for backward compatibility)
    source         provenance string, e.g. URL of an SEC filing or
                   operator-knowledge
    verified       VERIFIED | UNVERIFIED
    notes          free text

ELIGIBILITY RULES (usable_by_strategy)
--------------------------------------
  * ticker absent from the registry            -> REJECT (fail closed)
  * end_event_type == 'unknown'                -> REJECT always (fail closed)
  * date < listed_from                         -> REJECT (active before listing)
  * listed_to present and date > listed_to     -> REJECT (event already happened;
                                                   even symbol_change ends the
                                                   OLD symbol's usable window)
  * listed_to >= date >= listed_from           -> ACCEPT

Run `python delisted_universe.py` to execute the selftest.
"""

import csv
import datetime as _dt
import os
import sys

__all__ = [
    "END_EVENT_TYPES",
    "FINAL_RETURN_TREATMENTS",
    "LifecycleRecord",
    "UniverseRegistry",
    "ProviderAdapter",
    "ManualAdapter",
    "SecEdgarAdapter",
    "ExchangeFileAdapter",
    "load_seed",
    "build_registry",
    "usable_by_strategy",
]

END_EVENT_TYPES = frozenset(
    {"delisted", "acquired", "bankrupt", "symbol_change", "unknown"}
)

FINAL_RETURN_TREATMENTS = frozenset(
    {"delisting_return_included", "zeroed_bankrupt",
     "cash_acquisition_price_known", "unknown"}
)

DEFAULT_SEED_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "Efforts", "osanwe-v2-overhaul", "_work", "fis-data",
    "delisted-seed.csv",
)

_DATE_FMT = "%Y-%m-%d"


class LifecycleError(ValueError):
    """Raised for malformed lifecycle records."""


def _parse_date(text, field, ticker):
    text = (text or "").strip()
    if not text:
        return None
    try:
        return _dt.datetime.strptime(text, _DATE_FMT).date()
    except ValueError:
        raise LifecycleError(
            "%s: bad %s %r (want YYYY-MM-DD)" % (ticker, field, text)
        )


class LifecycleRecord(object):
    """One instrument's known listing window. Immutable-ish value object."""

    __slots__ = ("ticker", "listed_from", "listed_to", "end_event_type",
                 "final_return_treatment", "source", "verified", "notes")

    def __init__(self, ticker, listed_from, listed_to, end_event_type,
                 source="operator-knowledge", verified="UNVERIFIED",
                 notes="", final_return_treatment=None,
                 allow_unknown_start=False):
        ticker = (ticker or "").strip().upper()
        if not ticker:
            raise LifecycleError("empty ticker")
        if end_event_type not in END_EVENT_TYPES:
            raise LifecycleError(
                "%s: end_event_type %r not in %s"
                % (ticker, end_event_type, sorted(END_EVENT_TYPES))
            )
        frt = (final_return_treatment or "").strip().lower()
        # Default to 'unknown' when absent: never invent a treatment.
        if not frt:
            frt = "unknown"
        if frt not in FINAL_RETURN_TREATMENTS:
            raise LifecycleError(
                "%s: final_return_treatment %r not in %s"
                % (ticker, frt, sorted(FINAL_RETURN_TREATMENTS))
            )
        verified = (verified or "").strip().upper()
        if verified not in ("VERIFIED", "UNVERIFIED"):
            raise LifecycleError(
                "%s: verified must be VERIFIED|UNVERIFIED" % ticker
            )
        lf = _parse_date(listed_from, "listed_from", ticker)
        lt = _parse_date(listed_to, "listed_to", ticker)
        if lf is None and not allow_unknown_start:
            raise LifecycleError(
                "%s: listed_from required (pass allow_unknown_start=True "
                "for structurally-ineligible records)" % ticker)
        if lf is not None and lt is not None and lt < lf:
            raise LifecycleError(
                "%s: listed_to %s < listed_from %s" % (ticker, lt, lf)
            )
        # Cross-field honesty rule: an acquisition with a KNOWN cash price
        # must be marked as such; bankruptcies are zeroed only when the
        # equity was actually cancelled/extinguished (per-record evidence).
        if frt == "cash_acquisition_price_known" and end_event_type != "acquired":
            raise LifecycleError(
                "%s: cash_acquisition_price_known requires end_event_type "
                "'acquired'" % ticker
            )
        self.ticker = ticker
        self.listed_from = lf
        self.listed_to = lt  # None => open-ended (still listed per provider)
        self.end_event_type = end_event_type
        self.final_return_treatment = frt
        self.source = (source or "").strip()
        self.verified = verified
        self.notes = (notes or "").strip()

    def eligible(self, date):
        """True iff `date` falls inside the known lifecycle window.

        Unknown end_event_type NEVER becomes eligible (fail closed).
        """
        if self.end_event_type == "unknown":
            return False
        if isinstance(date, _dt.datetime):
            date = date.date()
        if not isinstance(date, _dt.date):
            raise TypeError("date must be a datetime.date")
        if self.listed_from is None:
            return False  # unknown start -> nothing is certifiable
        if date < self.listed_from:
            return False
        if self.listed_to is not None and date > self.listed_to:
            return False
        return True

    def __repr__(self):
        return "LifecycleRecord(%r, %s..%s, %s, %s/%s/%s)" % (
            self.ticker, self.listed_from,
            self.listed_to.isoformat() if self.listed_to else "OPEN",
            self.end_event_type, self.source, self.verified,
            self.final_return_treatment,
        )


def load_seed(path=None):
    """Load a curated seed CSV into a UniverseRegistry via ManualAdapter.

    Missing file => empty registry (honest: no data claimed).
    Malformed row => LifecycleError (loud, not silently skipped).
    """
    reg = build_registry(ManualAdapter(path or DEFAULT_SEED_PATH))
    reg.seed_path = path or DEFAULT_SEED_PATH
    reg.missing_file = not os.path.exists(reg.seed_path)
    return reg


# --------------------------------------------------------------------------
# Provider abstraction
# --------------------------------------------------------------------------

class ProviderAdapter(object):
    """Structural protocol: fetch_lifecycle(ticker) -> LifecycleRecord.

    Implementations MUST raise KeyError for tickers they have no record of
    (absence of evidence is NOT evidence of continued listing). They MAY
    expose fetch_all() returning an iterable of LifecycleRecord; adapters
    that cannot enumerate (e.g. pure point lookups) simply omit it.
    """

    name = "provider"

    def fetch_lifecycle(self, ticker):  # pragma: no cover - interface only
        raise NotImplementedError

    def fetch_all(self):
        """Iterable of all known records; default derives from nothing."""
        return []


def _record_from_row(raw, source_default="provider"):
    """Build a LifecycleRecord from a dict-like row (case-insensitive keys)."""
    low = dict((str(k).strip().lower(), v) for k, v in raw.items())
    return LifecycleRecord(
        ticker=low.get("ticker"),
        listed_from=low.get("listed_from"),
        listed_to=low.get("listed_to"),
        end_event_type=(low.get("end_event_type") or "").strip().lower(),
        source=low.get("source") or source_default,
        verified=low.get("verified"),
        notes=low.get("notes"),
        final_return_treatment=(
            low.get("final_return_treatment") or ""
        ).strip().lower() or None,
    )


class ManualAdapter(ProviderAdapter):
    """Curated seed CSV -- the original behavior, wrapped as a provider.

    Columns: ticker, listed_from, listed_to, end_event_type,
    [final_return_treatment], source, verified, notes.
    """

    name = "manual-csv"

    def __init__(self, path=None):
        self.path = path or DEFAULT_SEED_PATH

    def fetch_lifecycle(self, ticker):
        want = str(ticker).strip().upper()
        for rec in self.fetch_all():
            if rec.ticker == want:
                return rec
        raise KeyError(ticker)

    def fetch_all(self):
        if not os.path.exists(self.path):
            return []
        out = []
        with open(self.path, "r", newline="", encoding="ascii") as fh:
            reader = csv.DictReader(fh)
            required = {"ticker", "listed_from", "listed_to",
                        "end_event_type", "source", "verified", "notes"}
            header = set(h.strip().lower() for h in (reader.fieldnames or []))
            missing_cols = required - header
            if missing_cols:
                raise LifecycleError(
                    "seed %s missing columns: %s"
                    % (self.path, sorted(missing_cols))
                )
            for raw in reader:
                if not any((v or "").strip() for v in raw.values()):
                    continue  # skip fully blank lines
                out.append(_record_from_row(raw, source_default="manual-csv"))
        return out


class SecEdgarAdapter(ProviderAdapter):
    """Infer a delisting-style end event from SEC EDGAR Form 25/15 presence.

    DOCUMENTED INFERENCE LIMITS (read before trusting):
      1. A Form 25 (removal from listing, filed by the exchange) proves the
         exchange-listing ended on/near its filing date. It does NOT tell
         you WHY: acquisition, bankruptcy-driven suspension, voluntary
         deregistration, and failure-to-satisfy all produce Form 25s. The
         end_event_type emitted here is therefore always the conservative
         generic value 'delisted' unless the caller supplies better
         evidence via override_records.
      2. Form 15 (deregistration/suspension of reporting) typically follows
         ~90 days after a Form 25; it adds no listing-window information.
         It is matched here only to corroborate that the issuer went dark.
      3. listed_from CANNOT be inferred from Form 25/15 at all -- those
         forms mark ends, not beginnings. This adapter returns records with
         listed_from set only when the caller supplies it (via
         override_records or a listing-evidence sidecar); otherwise the
         record fails closed for pre-delist dates because eligible()
         requires listed_from.
      4. Delisting dates inferred this way are FILING-grain, not
         trading-session grain: the last actual trading day can precede the
         Form 25 by days-to-weeks (halt/suspension precedes removal).
         Downstream PnL must not assume the Form 25 date was tradable.
      5. Because of 1-4, records produced purely from Forms 25/15 are
         stamped UNVERIFIED regardless of how authoritative the forms are:
         the INFERRED semantics are what remain unverified.

    OFFLINE MODE (this repo): no network access is performed. Pass
    filings=[{'ticker','form_type','filing_date'}, ...] scraped beforehand
    (e.g. via edgar_pit.py) or use override_records. With neither, every
    lookup raises KeyError and the resulting registry is empty-but-honest.
    """

    name = "sec-edgar-form2515"

    def __init__(self, filings=None, override_records=None):
        # filings: iterable of dicts with ticker/form_type/filing_date.
        self._filings = list(filings or [])
        self._overrides = dict(override_records or {})

    def fetch_lifecycle(self, ticker):
        want = str(ticker).strip().upper()
        if want in self._overrides:
            return self._overrides[want]
        forms = [
            f for f in self._filings
            if str(f.get("ticker", "")).strip().upper() == want
        ]
        if not forms:
            raise KeyError(ticker)
        form25_dates = sorted(
            f["filing_date"] for f in forms
            if str(f.get("form_type", "")).upper().startswith("25")
        )
        form15_dates = sorted(
            f["filing_date"] for f in forms
            if str(f.get("form_type", "")).upper() == "15"
        )
        if not form25_dates and not form15_dates:
            # Only unrelated filings known -> no lifecycle claim.
            raise KeyError(ticker)
        end = form25_dates[0] if form25_dates else (
            form15_dates[0] if form15_dates else None)
        notes = (
            "INFERRED from Form 25/15 presence on EDGAR; reason for removal "
            "not determinable from these forms alone; filing-grain date, "
            "last tradable session may be earlier."
        )
        src = "sec-edgar-forms-25/15:%s" % want
        return LifecycleRecord(
            ticker=want,
            listed_from="",          # unknown start -> fails closed pre-end
            listed_to=end.isoformat() if end else "",
            end_event_type="delisted",   # conservative; see limits note 1
            source=src,
            verified="UNVERIFIED",
            notes=notes,
            final_return_treatment="unknown",
            allow_unknown_start=True,
        )

    def fetch_all(self):
        seen = {}
        for f in self._filings:
            t = str(f.get("ticker", "")).strip().upper()
            if t and t not in seen:
                try:
                    seen[t] = self.fetch_lifecycle(t)
                except KeyError:
                    pass
        for t, rec in self._overrides.items():
            seen.setdefault(str(t).strip().upper(), rec)
        return list(seen.values())


class ExchangeFileAdapter(ProviderAdapter):
    """Stub accepting a standard exchange delist CSV (no bundled data).

    Expected format (NasdaqTrader 'deleted' file / NYSE non-regulatory
    delist notice, normalized):

        ticker,date,reason[,exchange]
        ATVI,2023-10-16,merger,NASDAQ
        BBBY,2023-05-03,bankruptcy,NASDAQ

    MAPPING RULES (documented):
      * 'date' is the SUSPENSION/removal effective date. Per the same
        inference limit as SecEdgarAdapter, the last tradable session may
        be earlier; we conservatively set listed_to = date - 1 day ONLY
        when the file marks 'reason' as a halt-class event
        ('bankruptcy', 'halt'); otherwise listed_to = date itself.
        Callers wanting session-exact windows should post-trim.
      * 'reason' maps to end_event_type: merger/acquisition->acquired,
        bankruptcy->bankrupt, symbol change->symbol_change, anything else
        (including 'regulatory', 'failure to satisfy') -> 'delisted'.
      * No listing-start information exists in delist files ->
        listed_from empty => pre-history fails closed.
      * All rows are UNVERIFIED until cross-checked (verification is the
        caller's job; this stub never asserts VERIFIED).

    The constructor accepts a path but does not require the file to exist;
    a missing file yields an empty registry (same honest-empty contract as
    load_seed).
    """

    name = "exchange-file-stub"

    REASON_MAP = {
        "merger": "acquired",
        "acquisition": "acquired",
        "acquired": "acquired",
        "bankruptcy": "bankrupt",
        "bankrupt": "bankrupt",
        "chapter 11": "bankrupt",
        "chapter11": "bankrupt",
        "symbol change": "symbol_change",
        "symbol_change": "symbol_change",
        "halt": "delisted",
        "regulatory": "delisted",
        "other": "delisted",
    }
    HALT_CLASS_REASONS = frozenset({"bankruptcy", "bankrupt", "chapter 11",
                                    "chapter11", "halt"})

    def __init__(self, path=None, rows=None):
        self.path = path
        self.rows = list(rows or [])

    def fetch_lifecycle(self, ticker):
        want = str(ticker).strip().upper()
        for rec in self.fetch_all():
            if rec.ticker == want:
                return rec
        raise KeyError(ticker)

    def fetch_all(self):
        rows = list(self.rows)
        if self.path and os.path.exists(self.path):
            with open(self.path, "r", newline="",
                      encoding="ascii") as fh:
                rows.extend(csv.DictReader(fh))
        out = []
        for r in rows:
            tkr = (r.get("ticker") or "").strip().upper()
            if not tkr:
                continue
            reason_raw = (r.get("reason") or "other").strip().lower()
            event = self.REASON_MAP.get(reason_raw, "delisted")
            d = _parse_date(r.get("date"), "delist_date", tkr)
            if d is None:
                raise LifecycleError(
                    "%s: exchange delist row without valid date" % tkr
                )
            # Halt-class events: last session is BEFORE the file date.
            listed_to = d - _dt.timedelta(days=1) \
                if reason_raw in self.HALT_CLASS_REASONS else d
            exch = (r.get("exchange") or "").strip().upper()
            out.append(LifecycleRecord(
                ticker=tkr,
                listed_from="",   # delist files carry no start dates
                listed_to=listed_to.isoformat(),
                end_event_type=event,
                source="exchange-file%s%s" % (
                    ":" if exch else "", exch),
                verified="UNVERIFIED",
                notes="from standard exchange delist file; reason=%r; "
                      "file-date grain, last tradable session may differ"
                      % reason_raw,
                final_return_treatment=(
                    "zeroed_bankrupt" if event == "bankrupt" else "unknown"),
                allow_unknown_start=True,
            ))
        return out


def build_registry(provider):
    """Build a UniverseRegistry from any ProviderAdapter.

    Duplicate tickers across a single provider raise LifecycleError (loud).
    """
    records = {}
    for rec in provider.fetch_all():
        if rec.ticker in records:
            raise LifecycleError(
                "provider %s returned duplicate ticker %s"
                % (getattr(provider, "name", provider), rec.ticker)
            )
        records[rec.ticker] = rec
    reg = UniverseRegistry(records)
    reg.provider = provider
    return reg


class UniverseRegistry(object):
    """Ticker -> LifecycleRecord map with fail-closed eligibility."""

    def __init__(self, records, seed_path=None, missing_file=False):
        self.records = dict(records)
        self.seed_path = seed_path
        self.missing_file = bool(missing_file)
        self.provider = None

    def usable_by_strategy(self, ticker, date):
        """FAIL CLOSED eligibility.

        Reject when: ticker unknown, lifecycle unknown, date outside the
        known listing window, or malformed input. IDENTICAL semantics
        regardless of which provider populated the registry (tested).
        """
        if not ticker:
            return False, "empty-ticker"
        rec = self.records.get(str(ticker).strip().upper())
        if rec is None:
            return False, "unknown-lifecycle:not-in-registry"
        if rec.end_event_type == "unknown":
            return False, "unknown-lifecycle:end-event-unknown"
        if not rec.eligible(date):
            if rec.listed_from is not None and date < rec.listed_from:
                return False, "before-listing"
            return False, "after-end:%s:%s" % (
                rec.end_event_type,
                rec.listed_to.isoformat() if rec.listed_to else "open",
            )
        if rec.verified != "VERIFIED":
            return True, "eligible-unverified-data:%s" % rec.verified.lower()
        return True, "eligible"

    def constituents(self, household="watchlist", date=None):
        """Historical constituent membership honoring lifecycle.

        Returns the sorted list of tickers whose known lifecycle window
        CONTAINS `date` AND whose end_event_type is not 'unknown'. Tickers
        whose lifecycle is unknown/unresolved are EXCLUDED here (they are
        reported separately by quarantine_report()) -- membership never
        assumes a security was listed.

        household: only 'watchlist' exists today (the curated seed);
        any other value raises ValueError rather than silently returning
        the wrong book.
        """
        if household != "watchlist":
            raise ValueError(
                "household %r unsupported; only 'watchlist'" % household)
        if date is None:
            raise ValueError("date is required (point-in-time membership)")
        if isinstance(date, _dt.datetime):
            date = date.date()
        if not isinstance(date, _dt.date):
            raise TypeError("date must be a datetime.date")
        out = []
        for tkr, rec in self.records.items():
            if rec.eligible(date):
                out.append(tkr)
        return sorted(out)

    def quarantine_report(self):
        """Tickers whose eligibility CANNOT be certified, and why.

        Returns a list of dicts, one per quarantined ticker:
            {ticker, reasons: [...]}
        Quarantine categories:
          * not-in-registry          : no provider has any lifecycle record
                                       (only meaningful when callers ask us
                                       about specific tickers -- see
                                       quarantine_report(candidates=[...]))
          * end-event-unknown        : record exists but end_event_type is
                                       'unknown'
          * open-start-unverifiable  : listed_from missing/inferred such
                                       that early history cannot be
                                       certified (records with empty
                                       listed_from are structurally
                                       ineligible everywhere)
          * unverified-provider-data : usable window exists but the record
                                       is UNVERIFIED, so certification is
                                       provisional
          * missing-seed-file        : whole registry is empty because the
                                       backing file/provider is absent
        """
        report = []

        def add(tkr, why):
            for entry in report:
                if entry["ticker"] == tkr:
                    entry["reasons"].append(why)
                    return
            report.append({"ticker": tkr, "reasons": [why]})

        if self.missing_file:
            add("*REGISTRY*", "missing-seed-file:no-backing-data")
        for tkr, rec in sorted(self.records.items()):
            whys = []
            if rec.end_event_type == "unknown":
                whys.append("end-event-unknown")
            if rec.listed_from is None:
                whys.append("open-start-unverifiable:no-listing-start-evidence")
            if rec.verified != "VERIFIED":
                whys.append("unverified-provider-data")
            if whys:
                add(tkr, ";".join(whys))
        return report

    def capability_report(self):
        """Honest counts -- what we actually hold, nothing inflated."""
        n = len(self.records)
        by_event = {}
        by_ver = {}
        by_frt = {}
        for r in self.records.values():
            by_event[r.end_event_type] = by_event.get(r.end_event_type, 0) + 1
            by_ver[r.verified] = by_ver.get(r.verified, 0) + 1
            by_frt[r.final_return_treatment] = \
                by_frt.get(r.final_return_treatment, 0) + 1
        return {
            "registry_size": n,
            "missing_seed_file": self.missing_file,
            "by_end_event": by_event,
            "by_verification": by_ver,
            "by_final_return_treatment": by_frt,
            "quarantined": len(self.quarantine_report()),
            "provider": getattr(self.provider, "name", None),
            "full_pit_universe": "unresolved-requires-external-data",
        }


def usable_by_strategy(ticker, date, registry=None):
    """Module-level convenience wrapper using the default seed."""
    reg = registry if registry is not None else load_seed()
    return reg.usable_by_strategy(ticker, date)


def quarantine_report(registry=None, candidates=None):
    """Module-level convenience wrapper.

    candidates: optional iterable of tickers to check beyond the registry
    itself (lets the report catch not-in-registry cases explicitly).
    """
    reg = registry if registry is not None else load_seed()
    report = reg.quarantine_report()
    if candidates:
        known = {e["ticker"] for e in report}
        for tkr in candidates:
            t = str(tkr).strip().upper()
            ok, why = reg.usable_by_strategy(t, _dt.date(2000, 1, 3))
            # A ticker that passes even this probe is fine; anything that
            # fails with not-in-registry belongs in quarantine.
            if t not in {r.ticker for r in reg.records.values()} \
                    and t not in known:
                report.append({"ticker": t,
                               "reasons": ["not-in-registry:%s" % why]})
    return report


# --------------------------------------------------------------------------
# Selftest
# --------------------------------------------------------------------------

def _selftest():
    failures = []

    def check(name, cond):
        print("[%s] %s" % ("PASS" if cond else "FAIL", name))
        if not cond:
            failures.append(name)

    # Build a small synthetic registry for deterministic rule tests.
    reg = UniverseRegistry({
        "TEST": LifecycleRecord(
            "TEST", "2021-06-15", "2023-04-23", "delisted",
            source="synthetic-test", verified="UNVERIFIED"),
        "UNKC": LifecycleRecord(
            "UNKC", "2020-01-01", "", "unknown",
            source="synthetic-test", verified="UNVERIFIED"),
        "OPEN": LifecycleRecord(
            "OPEN", "2021-01-01", "", "symbol_change",
            source="synthetic-test", verified="UNVERIFIED"),
    })

    d = _dt.date

    # 1. active-before-listing REJECTED
    ok, why = reg.usable_by_strategy("TEST", d(2021, 6, 14))
    check("active-before-listing rejected (%s)" % why, not ok)

    # 2. delisted-after-end REJECTED
    ok, why = reg.usable_by_strategy("TEST", d(2023, 4, 24))
    check("day-after-delist rejected (%s)" % why, not ok)
    ok, why = reg.usable_by_strategy("TEST", d(2026, 1, 1))
    check("long-after-delist rejected (%s)" % why, not ok)

    # 3. unknown-lifecycle FAILS CLOSED
    ok, why = reg.usable_by_strategy("UNKC", d(2022, 1, 1))
    check("unknown end-event fails closed inside window (%s)" % why, not ok)
    ok, why = reg.usable_by_strategy("NOPE", d(2022, 1, 1))
    check("ticker not in registry fails closed (%s)" % why, not ok)
    ok, why = reg.usable_by_strategy("", d(2022, 1, 1))
    check("empty ticker fails closed (%s)" % why, not ok)

    # Positive controls.
    ok, why = reg.usable_by_strategy("TEST", d(2023, 4, 23))  # last day
    check("last-listed-day accepted (%s)" % why, ok)
    ok, why = reg.usable_by_strategy("TEST", d(2021, 6, 15))  # first day
    check("first-listed-day accepted (%s)" % why, ok)
    ok, why = reg.usable_by_strategy("OPEN", d(2030, 1, 1))
    check("open-ended window accepts future date (%s)" % why, ok)

    # Boundary integrity: listed_to < listed_from must raise.
    try:
        LifecycleRecord("BAD", "2023-01-01", "2022-01-01", "delisted")
        check("reversed dates raise", False)
    except LifecycleError:
        check("reversed dates raise", True)

    # Bad enum must raise.
    try:
        LifecycleRecord("BAD2", "2021-01-01", "", "merged-somewhere")
        check("bad end_event_type raises", False)
    except LifecycleError:
        check("bad end_event_type raises", True)

    # final_return_treatment enum enforcement.
    try:
        LifecycleRecord("BADFRT", "2021-01-01", "2022-01-01", "delisted",
                        final_return_treatment="made_money_somehow")
        check("bad final_return_treatment raises", False)
    except LifecycleError:
        check("bad final_return_treatment raises", True)

    ok = LifecycleRecord("OKFRT", "2021-01-01", "2022-01-01", "delisted",
                         final_return_treatment="DELISTING_RETURN_INCLUDED")
    check("final_return_treatment case-normalized",
          ok.final_return_treatment == "delisting_return_included")

    absent_frt = LifecycleRecord("NOFRT", "2021-01-01", "2022-01-01",
                                 "delisted")
    check("missing final_return_treatment defaults to unknown",
          absent_frt.final_return_treatment == "unknown")

    try:
        LifecycleRecord("BADCASH", "2021-01-01", "2022-01-01", "bankrupt",
                        final_return_treatment="cash_acquisition_price_known")
        check("cash price requires acquired end-event", False)
    except LifecycleError:
        check("cash price requires acquired end-event", True)

    # Real seed file: load and sanity-check every row parses + honors rules.
    seed_reg = load_seed()
    rep = seed_reg.capability_report()
    print("seed report: %s" % rep)
    check("seed loads >= 5 rows", rep["registry_size"] >= 5)
    check("seed all VERIFIED w/ citation",
          rep["by_verification"].get("UNVERIFIED", 0) == 0)
    check("every seed row carries http(s) source URL",
          all(r.source.startswith("http") or "http" in r.source
              for r in seed_reg.records.values()))
    check("every seed row has explicit final_return_treatment",
          all(r.final_return_treatment != "unknown"
              for r in seed_reg.records.values()))
    for tkr, rec in seed_reg.records.items():
        ok, _why = seed_reg.usable_by_strategy(
            tkr, rec.listed_from + _dt.timedelta(days=30))
        if not ok and rec.end_event_type != "unknown" and \
                (rec.listed_to is None or
                 rec.listed_from + _dt.timedelta(days=30) <= rec.listed_to):
            failures.append("seed mid-window rejection: %s" % tkr)

    # constituents(): point-in-time membership honors lifecycle.
    twtr = seed_reg.records["TWTR"]
    mid = twtr.listed_from + (_dt.timedelta(days=365))
    mem = seed_reg.constituents(household="watchlist", date=mid)
    check("TWTR member mid-life (%s in %s)" % (twtr.ticker, mem),
          "TWTR" in mem)
    check("TWTR absent after end",
          "TWTR" not in seed_reg.constituents(
              household="watchlist",
              date=twtr.listed_to + _dt.timedelta(days=30)))
    check("TWTR absent before listing",
          "TWTR" not in seed_reg.constituents(
              household="watchlist",
              date=twtr.listed_from - _dt.timedelta(days=1)))
    try:
        seed_reg.constituents(household="pension", date=mid)
        check("unsupported household raises", False)
    except ValueError:
        check("unsupported household raises", True)
    try:
        seed_reg.constituents(household="watchlist", date=None)
        check("constituents requires explicit date", False)
    except ValueError:
        check("constituents requires explicit date", True)

    # quarantine_report(): flags what cannot be certified.
    q = seed_reg.quarantine_report()
    qmap = dict((e["ticker"], e["reasons"]) for e in q)
    check("fully-verified clean registry quarantines nobody",
          not q), 
    qreg = UniverseRegistry({
        "SHADY": LifecycleRecord(
            "SHADY", "2010-01-01", "2020-12-31", "delisted",
            source="synthetic", verified="UNVERIFIED"),
        "GHOST": LifecycleRecord(
            "GHOST", "2010-01-01", "", "unknown",
            source="synthetic", verified="UNVERIFIED",
            final_return_treatment="unknown"),
        "NOSTART": LifecycleRecord(
            "NOSTART", "2020-06-01", "2021-06-01", "delisted",
            source="synthetic", verified="VERIFIED"),
    })
    # NOSTART has a real listed_from so it should NOT quarantine on start;
    # craft the true open-start case via a record whose listed_from is None
    # by bypassing the constructor validation (structural honesty test).
    nostart_rec = LifecycleRecord.__new__(LifecycleRecord)
    nostart_rec.ticker = "TRULYNOSTART"
    nostart_rec.listed_from = None
    nostart_rec.listed_to = d(2021, 6, 1)
    nostart_rec.end_event_type = "delisted"
    nostart_rec.final_return_treatment = "unknown"
    nostart_rec.source = "synthetic"
    nostart_rec.verified = "VERIFIED"
    nostart_rec.notes = ""
    qreg2 = UniverseRegistry({"TRULYNOSTART": nostart_rec})
    q2 = qreg2.quarantine_report()
    check("open-start record quarantined",
          any(e["ticker"] == "TRULYNOSTART"
              and any("open-start" in r for r in e["reasons"])
              for e in q2))

    q3 = qreg.quarantine_report()
    q3map = dict((e["ticker"], e["reasons"]) for e in q3)
    check("SHADY quarantined as unverified",
          any("unverified-provider-data" in r for r in q3map.get("SHADY", [])))
    check("GHOST quarantined as end-event-unknown",
          any("end-event-unknown" in r for r in q3map.get("GHOST", [])))

    qmod = quarantine_report(registry=qreg, candidates=["ZZZABSENT"])
    check("module-level quarantine catches not-in-registry candidate",
          any(e["ticker"] == "ZZZABSENT"
              and any(r.startswith("not-in-registry")
                      for r in e["reasons"]) for e in qmod))

    # ------------------------------------------------------------------
    # PROVIDER SWAP: identical fail-closed semantics across adapters.
    # ------------------------------------------------------------------

    # (a) ManualAdapter vs direct load: same records, same verdicts.
    manual = build_registry(ManualAdapter(DEFAULT_SEED_PATH))
    probes = [("TWTR", d(2019, 6, 1)), ("TWTR", d(2022, 10, 28)),
              ("ATVI", d(2020, 1, 1)), ("BBBY", d(2023, 5, 4)),
              ("SIVB", d(2023, 3, 8)), ("TUP", d(2024, 9, 18)),
              ("ZZZZ", d(2020, 1, 1))]
    for tkr, dt_ in probes:
        a = seed_reg.usable_by_strategy(tkr, dt_)
        b = manual.usable_by_strategy(tkr, dt_)
        check("provider-swap identical: %s@%s (%s)" % (tkr, dt_, a[1]),
              a == b)

    # (b) SecEdgarAdapter offline with synthetic filings: same shape of
    # failure (reject outside any certifiable window) as manual data.
    edgar = build_registry(SecEdgarAdapter(filings=[
        {"ticker": "FAKE", "form_type": "25-NSE",
         "filing_date": d(2022, 3, 1)},
        {"ticker": "FAKE", "form_type": "15",
         "filing_date": d(2022, 5, 27)},
    ]))
    ok, why_edgar = edgar.usable_by_strategy("FAKE", d(2020, 1, 1))
    check("EDGAR-inferred record rejects far-past date (no listed_from)"
          " (%s)" % why_edgar, not ok)
    ok, why_edgar = edgar.usable_by_strategy("FAKE", d(2023, 1, 1))
    check("EDGAR-inferred record rejects post-Form-25 date (%s)"
          % why_edgar, not ok)
    ok, why_absent = edgar.usable_by_strategy("NOTONEDGAR", d(2022, 1, 1))
    check("EDGAR adapter absence still fails closed (%s)" % why_absent,
          not ok and why_absent == "unknown-lifecycle:not-in-registry")

    # (c) ExchangeFileAdapter stub: mapping rules + fail closed.
    exch = build_registry(ExchangeFileAdapter(rows=[
        {"ticker": "EXA", "date": "2021-07-01", "reason": "merger"},
        {"ticker": "EXB", "date": "2021-07-01", "reason": "bankruptcy"},
        {"ticker": "EXC", "date": "2021-07-01", "reason": "regulatory"},
    ]))
    ok, why_ex = exch.usable_by_strategy("EXA", d(2020, 1, 1))
    check("exchange-file record rejects pre-history (empty listed_from)"
          " (%s)" % why_ex, not ok)
    exa = exch.records["EXA"]
    exb = exch.records["EXB"]
    exc = exch.records["EXC"]
    check("exchange-file merger maps acquired, listed_to=date",
          exa.end_event_type == "acquired"
          and exa.listed_to == d(2021, 7, 1))
    check("exchange-file bankruptcy maps zeroed + trimmed last session",
          exb.end_event_type == "bankrupt"
          and exb.final_return_treatment == "zeroed_bankrupt"
          and exb.listed_to == d(2021, 6, 30))
    check("exchange-file regulatory maps delisted",
          exc.end_event_type == "delisted")

    # (d) Registry-level verdict equality across providers for the SAME
    # underlying facts (manual vs override-fed EDGAR adapter).
    twtr_rec = seed_reg.records["TWTR"]
    edgar2 = build_registry(SecEdgarAdapter(override_records={
        "TWTR": twtr_rec}))
    for tkr, dt_ in probes[:2]:
        check("override-fed EDGAR identical to manual: %s@%s"
              % (tkr, dt_),
              edgar2.usable_by_strategy(tkr, dt_)
              == seed_reg.usable_by_strategy(tkr, dt_))

    # (e) Missing-file behavior is honest-empty, not fake.
    empty = load_seed(os.path.join(os.path.dirname(os.path.abspath(__file__))
                                   + "/_no_such_seed.csv"))
    ok, _why = empty.usable_by_strategy("ANYTHING", d(2022, 1, 1))
    check("missing seed file => everything rejected", not ok and empty.missing_file)
    eq = empty.quarantine_report()
    check("missing seed file shows in quarantine",
          any(e["ticker"] == "*REGISTRY*" for e in eq))
    check("missing-file registry has no constituents",
          empty.constituents(household="watchlist", date=d(2022, 1, 1)) == [])

    print("-" * 60)
    if failures:
        print("SELFTEST FAILED: %d failure(s): %s" % (len(failures), failures))
        return 1
    print("SELFTEST OK: all checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(_selftest())

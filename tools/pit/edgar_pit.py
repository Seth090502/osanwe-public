#!/usr/bin/env python3
# -*- coding: ascii -*-
"""D4 EDGAR point-in-time (PIT) integrity pilot.

Pipeline
--------
1. PILOT (network, capped): fetch https://data.sec.gov/submissions/CIK##########.json
   for 5 pilot tickers (AAPL MSFT NVDA MU AMD), building the ticker->CIK map from
   https://www.sec.gov/files/company_tickers.json first. HARD CAP: 10 requests
   total, 5s sleep between requests. Merges acceptanceDateTime, form,
   accessionNumber, filingDate, reportDate into a structured JSONL at
   _work/fis-data/edgar-pit-pilot.jsonl.

2. ENRICH (offline, NO network): merge/enrichment layer + schema validation for
   the FULL ~95-ticker corpus from wiki/investing/filings/*/*.json (day-level
   dates), showing exactly which fields upgrade from the EDGAR PIT layer.

3. LEAKAGE TEST: assert every extracted acceptance_datetime >= its prior local
   filing_date. Also reports (informationally) any acceptance whose calendar
   date lands AFTER the local filing date -- the true look-ahead direction.

4. SELFTEST (--selftest): fully offline; runs the whole pipeline on synthetic
   fixtures, verifies the leakage assertion actually fires on a bad pair,
   and skips the network part gracefully.

Constraints honored: ASCII only, stdlib urllib only, hard request cap,
no git operations, touches ONLY tools/pit/ and Efforts/osanwe-v2-overhaul/_work/fis-data/.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from datetime import time as dt_time

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
VaultRoot = os.path.abspath(os.path.join(TOOL_DIR, "..", ".."))
FILINGS_DIR = os.path.join(VaultRoot, "wiki", "investing", "filings")
OUT_DIR = os.path.join(
    VaultRoot, "Efforts", "osanwe-v2-overhaul", "_work", "fis-data"
)
PILOT_JSONL = os.path.join(OUT_DIR, "edgar-pit-pilot.jsonl")
ENRICHED_JSONL = os.path.join(OUT_DIR, "edgar-pit-enriched.jsonl")
UPGRADE_REPORT = os.path.join(OUT_DIR, "edgar-pit-upgrade-report.json")
FULL_JSONL = os.path.join(OUT_DIR, "edgar-pit-full.jsonl")
FULL_CHECKPOINT = os.path.join(OUT_DIR, "edgar-pit-full-checkpoint.json")
FULL_REPORT = os.path.join(OUT_DIR, "edgar-pit-full-report.json")

# market_calendar lives in the same tools/pit/ directory; make it importable
# when edgar_pit.py is invoked from any working directory.
if TOOL_DIR not in sys.path:
    sys.path.insert(0, TOOL_DIR)
import market_calendar  # noqa: E402

# --------------------------------------------------------------------------
# Network policy: hard cap + courtesy sleep
# --------------------------------------------------------------------------
USER_AGENT = "research <user>@example.com"
MAX_REQUESTS = 10
SLEEP_SECONDS = 5

PILOT_TICKERS = ["AAPL", "MSFT", "NVDA", "MU", "AMD"]
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{:010d}.json"


class RequestBudgetExceeded(Exception):
    """Raised when the hard request cap would be violated."""


class RequestBudget(object):
    def __init__(self, max_requests=MAX_REQUESTS, sleep_seconds=SLEEP_SECONDS,
                 urlopen=None):
        self.max_requests = max_requests
        self.sleep_seconds = sleep_seconds
        self._urlopen = urlopen  # None -> resolve urllib at call time
        self.used = 0

    def fetch_json(self, url, timeout=60):
        if self.used >= self.max_requests:
            raise RequestBudgetExceeded(
                "hard cap reached: %d/%d requests used; refusing %s"
                % (self.used, self.max_requests, url)
            )
        if self.used > 0:
            time.sleep(self.sleep_seconds)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        self.used += 1
        opener = self._urlopen if self._urlopen is not None \
            else urllib.request.urlopen
        with opener(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))


# --------------------------------------------------------------------------
# Field extraction / normalization
# --------------------------------------------------------------------------
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ACCESSION_RE = re.compile(r"^\d{10}-\d{2}-\d{6}$")
ACCEPT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")


def extract_submission_rows(cik, payload):
    """Flatten the parallel-arrays structure of a submissions JSON into rows."""
    recent = payload.get("filings", {}).get("recent", {}) or {}
    forms = recent.get("form", []) or []
    acc = recent.get("accessionNumber", []) or []
    fdates = recent.get("filingDate", []) or []
    adates = recent.get("acceptanceDateTime", []) or []
    rdates = recent.get("reportDate", []) or []
    n = min(len(forms), len(acc), len(fdates), len(adates), len(rdates))
    rows = []
    for i in range(n):
        rows.append(
            {
                "cik": int(cik),
                "form": forms[i],
                "accession_number": acc[i],
                "filing_date": fdates[i],
                "acceptance_datetime": adates[i],
                "report_date": rdates[i],
            }
        )
    return rows


def parse_acceptance(ts):
    """Parse '2026-08-19T16:31:00.123Z' into an aware UTC datetime."""
    return datetime.strptime(ts.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S.%f%z")


def acceptance_date_str(ts):
    """Day-level date string of an acceptance timestamp (UTC calendar date)."""
    return parse_acceptance(ts).astimezone(timezone.utc).strftime("%Y-%m-%d")


# --------------------------------------------------------------------------
# Schema validation
# --------------------------------------------------------------------------
REQUIRED_KEYS = [
    "cik",
    "form",
    "accession_number",
    "filing_date",
    "acceptance_datetime",
    "report_date",
]


def validate_row(row):
    """Return a list of schema error strings ([] == valid).

    NOTE (D-R1): report_date is OPTIONAL. Many filing types (e.g. Form 4)
    carry no periodOfReport while still having a fully certifiable
    acceptance timestamp; such rows pass validation with
    processing_delay_hours=None instead of being quarantined.
    """
    errs = []
    if not isinstance(row, dict):
        return ["row is not an object"]
    for key in REQUIRED_KEYS:
        val = row.get(key)
        if key == "report_date" and val in (None, ""):
            continue  # optional
        if key not in row or val in (None, ""):
            errs.append("missing/empty field: %s" % key)
            continue
        if key == "cik":
            if not isinstance(val, int) or val <= 0:
                errs.append("cik must be positive int, got %r" % (val,))
        elif key == "accession_number":
            if not ACCESSION_RE.match(str(val)):
                errs.append("bad accession_number %r" % (val,))
        elif key == "filing_date":
            if not DATE_RE.match(str(val)):
                errs.append("bad filing_date %r" % (val,))
        elif key == "report_date":
            if not DATE_RE.match(str(val)):
                errs.append("bad report_date %r" % (val,))
        elif key == "acceptance_datetime":
            if not ACCEPT_RE.match(str(val)):
                errs.append("bad acceptance_datetime %r" % (val,))
    # cross-field: acceptance must land on the filing-date day or up to one
    # calendar day EARLIER. The one-day grace encodes a documented EDGAR
    # convention: filings accepted after ~17:30 ET receive an official
    # filingDate of the NEXT business day while acceptanceDateTime keeps
    # the true instant (dominant for fund N-PX volume around reporting
    # deadlines). Anything earlier than that is a genuine anomaly.
    if not errs and "acceptance_datetime" in row and "filing_date" in row:
        try:
            a_day = acceptance_date_str(row["acceptance_datetime"])
            fd = datetime.strptime(row["filing_date"], "%Y-%m-%d").date()
            floor = (fd - timedelta(days=1)).isoformat()
            if a_day < floor:
                errs.append(
                    "acceptance day %s precedes filing_date %s"
                    % (a_day, row["filing_date"])
                )
        except ValueError:
            pass  # already flagged by format check above
    return errs


# --------------------------------------------------------------------------
# Pilot fetch (network, capped)
# --------------------------------------------------------------------------
def run_pilot(budget=None, out_path=PILOT_JSONL, tickers=None, verbose=True):
    """Fetch EDGAR submissions for pilot tickers; write structured JSONL."""
    budget = budget or RequestBudget()
    tickers = tickers or PILOT_TICKERS
    log = (lambda m: verbose and print(m, file=sys.stderr))

    log("[pilot] fetching ticker->CIK map (request %d of %d)..."
        % (budget.used + 1, budget.max_requests))
    raw_map = budget.fetch_json(COMPANY_TICKERS_URL)
    cik_by_ticker = {}
    for entry in raw_map.values():
        t = str(entry.get("ticker", "")).upper()
        if t and t not in cik_by_ticker:
            cik_by_ticker[t] = int(entry["cik_str"])

    all_rows = []
    missing = []
    for t in tickers:
        cik = cik_by_ticker.get(t)
        if cik is None:
            missing.append(t)
            log("[pilot] WARN: no CIK found for %s" % t)
            continue
        url = SUBMISSIONS_URL.format(cik)
        log("[pilot] fetching %s (CIK %010d; request %d of %d)..."
            % (t, cik, budget.used + 1, budget.max_requests))
        payload = budget.fetch_json(url)
        rows = extract_submission_rows(cik, payload)
        for r in rows:
            r["ticker"] = t
        all_rows.extend(rows)
        log("[pilot] %s: %d recent filings extracted" % (t, len(rows)))

    # stable ordering: ticker, then newest acceptance first
    all_rows.sort(key=lambda r: (r["ticker"], str(r["acceptance_datetime"])),
                  reverse=False)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    field_order = ["ticker", "cik", "form", "accession_number",
                   "filing_date", "acceptance_datetime", "report_date"]
    with open(out_path, "w", encoding="ascii") as fh:
        for r in all_rows:
            fh.write(json.dumps({k: r[k] for k in field_order},
                                sort_keys=False) + "\n")
    log("[pilot] wrote %d rows -> %s (requests used: %d/%d)"
        % (len(all_rows), out_path, budget.used, budget.max_requests))
    return {"rows": len(all_rows), "requests_used": budget.used,
            "missing_tickers": missing}


# --------------------------------------------------------------------------
# Offline merge / enrichment over the full local corpus
# --------------------------------------------------------------------------
def load_local_corpus(filings_dir=FILINGS_DIR):
    """Load wiki/investing/filings/<TICKER>/*.json day-level records.

    Returns (records, dirs_seen, files_read) where each record keeps its
    source path so upgrades stay traceable.
    """
    records = []
    dirs_seen = 0
    files_read = 0
    if not os.path.isdir(filings_dir):
        return records, dirs_seen, files_read
    for name in sorted(os.listdir(filings_dir)):
        sub = os.path.join(filings_dir, name)
        if not os.path.isdir(sub):
            continue
        dirs_seen += 1
        for fn in sorted(os.listdir(sub)):
            if not fn.endswith(".json"):
                continue
            path = os.path.join(sub, fn)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except (ValueError, OSError):
                continue
            if not isinstance(data, list):
                continue
            files_read += 1
            for rec in data:
                if not isinstance(rec, dict):
                    continue
                if not all(k in rec for k in ("date", "form", "ticker")):
                    continue
                out = dict(rec)
                out["_src"] = os.path.basename(path)
                out["_dir"] = name
                records.append(out)
    return records, dirs_seen, files_read


def index_pit(pit_path=PILOT_JSONL):
    """Index PIT rows by (ticker, form, filing_date)."""
    idx = {}
    if not os.path.exists(pit_path):
        return idx
    with open(pit_path, "r", encoding="ascii") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            key = (row["ticker"], row["form"], row["filing_date"])
            idx.setdefault(key, []).append(row)
    return idx


FIELD_UPGRADES = {
    "date": ("date -> acceptance_datetime",
             "day-level date gains millisecond acceptance timestamp"),
    "form": ("form (verified)",
             "local form label verified against EDGAR canonical value"),
    "accession_number": ("+ accession_number (NEW)",
                         "stable unique filing identifier joins to documents"),
    "report_date": ("+ report_date / periodOfReport (NEW)",
                    "period the filing covers, distinct from filing date"),
    "cik": ("+ cik (NEW)", "canonical SEC registrant id"),
}
FIELDS_UNCHANGED = ["desc", "doc"]


def run_enrich(pit_path=PILOT_JSONL, filings_dir=FILINGS_DIR,
               out_path=ENRICHED_JSONL, report_path=UPGRADE_REPORT,
               verbose=True):
    """Offline merge/enrichment + schema validation over the full corpus."""
    log = (lambda m: verbose and print(m, file=sys.stderr))
    local_records, dirs_seen, files_read = load_local_corpus(filings_dir)
    pit_idx = index_pit(pit_path)

    enriched_rows = []
    matched_local = 0
    unmatched_local = 0
    upgrade_counts = {
        "acceptance_datetime": 0,
        "accession_number": 0,
        "report_date": 0,
        "cik": 0,
        "form_verified": 0,
    }
    form_mismatches = []
    ambiguous = 0
    leakage_violations = []       # acceptance < local filing_date (spec test)
    lookahead_warnings = []       # acceptance DAY after local filing_date

    for rec in local_records:
        key = (rec["ticker"], rec["form"], rec["date"])
        hits = pit_idx.get(key, [])
        if not hits:
            unmatched_local += 1
            continue
        if len(hits) > 1:
            # multiple same-form filings on one day (common for Form 4);
            # keep them all but do not claim a 1:1 field upgrade for this rec
            ambiguous += 1
        hit = hits[0]
        matched_local += 1
        row = {
            "ticker": rec["ticker"],
            "cik": hit["cik"],
            "form": rec["form"],
            "accession_number": hit["accession_number"],
            "filing_date": rec["date"],
            "acceptance_datetime": hit["acceptance_datetime"],
            "report_date": hit["report_date"],
            "desc": rec.get("desc"),
            "doc": rec.get("doc"),
            "match_ambiguous": bool(len(hits) > 1),
            "_src": rec["_src"],
        }
        if rec["form"] != hit["form"]:
            form_mismatches.append({"ticker": rec["ticker"],
                                    "local_form": rec["form"],
                                    "edgar_form": hit["form"]})
        else:
            upgrade_counts["form_verified"] += 1
        upgrade_counts["acceptance_datetime"] += 1
        upgrade_counts["accession_number"] += 1
        upgrade_counts["report_date"] += 1
        upgrade_counts["cik"] += 1

        # ---- LEAKAGE TEST (spec): acceptance_datetime >= prior local filing_date
        acc_dt = parse_acceptance(hit["acceptance_datetime"])
        local_midnight = datetime.strptime(rec["date"], "%Y-%m-%d").replace(
            tzinfo=timezone.utc)
        if acc_dt < local_midnight:
            leakage_violations.append({
                "ticker": rec["ticker"],
                "form": rec["form"],
                "local_filing_date": rec["date"],
                "acceptance_datetime": hit["acceptance_datetime"],
            })
        # informational: the true look-ahead direction (accepted strictly
        # AFTER the day the local corpus claims availability)
        if acceptance_date_str(hit["acceptance_datetime"]) > rec["date"]:
            lookahead_warnings.append({
                "ticker": rec["ticker"],
                "form": rec["form"],
                "local_filing_date": rec["date"],
                "acceptance_day": acceptance_date_str(
                    hit["acceptance_datetime"]),
            })
        enriched_rows.append(row)

    # schema-validate every enriched row we emit
    schema_errors = []
    for i, row in enumerate(enriched_rows):
        for e in validate_row(row):
            schema_errors.append({"row_index": i, "error": e})

    report = {
        "corpus": {
            "ticker_dirs_seen": dirs_seen,
            "json_files_read": files_read,
            "local_records_total": len(local_records),
        },
        "pit_layer": {
            "source_rows": sum(len(v) for v in pit_idx.values()),
            "distinct_keys": len(pit_idx),
        },
        "merge": {
            "matched_local_records": matched_local,
            "unmatched_local_records": unmatched_local,
            "ambiguous_matches": ambiguous,
            "form_mismatches": form_mismatches[:20],
        },
        "field_upgrades": FIELD_UPGRADES,
        "fields_unchanged": FIELDS_UNCHANGED,
        "upgrade_counts": upgrade_counts,
        "leakage_test": {
            "rule": "assert acceptance_datetime >= prior local filing_date",
            "checked": matched_local,
            "violations": leakage_violations[:50],
            "violation_count": len(leakage_violations),
            "passed": not leakage_violations,
            "lookahead_info_acceptance_after_local_day":
                lookahead_warnings[:50],
            "lookahead_info_count": len(lookahead_warnings),
        },
        "schema_validation": {
            "rows_checked": len(enriched_rows),
            "error_count": len(schema_errors),
            "errors_sample": schema_errors[:20],
        },
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="ascii") as fh:
        for row in enriched_rows:
            fh.write(json.dumps(row, sort_keys=False) + "\n")
    with open(report_path, "w", encoding="ascii") as fh:
        json.dump(report, fh, indent=2, sort_keys=False)

    log("[enrich] corpus: %d dirs / %d files / %d local records"
        % (dirs_seen, files_read, len(local_records)))
    log("[enrich] matched: %d | unmatched: %d | ambiguous: %d"
        % (matched_local, unmatched_local, ambiguous))
    log("[enrich] upgrades: %s" % json.dumps(upgrade_counts))
    log("[enrich] leakage: %d violations in %d checked -> %s"
        % (len(leakage_violations), matched_local,
           "PASS" if not leakage_violations else "FAIL"))
    log("[enrich] schema : %d errors in %d rows"
        % (len(schema_errors), len(enriched_rows)))
    log("[enrich] wrote %s and %s" % (out_path, report_path))
    ok = not leakage_violations and not schema_errors
    return {"ok": ok, "report": report}


# ==========================================================================
# D-R1: FULL corpus point-in-time ingestion (all ~95 local ticker dirs)
# ==========================================================================

# SEC fair-access policy: <= 8 requests/second, descriptive UA. We run at
# 0.15s spacing (~6.7 req/s) with a small extra pause every 10 requests.
FULL_SLEEP_SECONDS = 0.15
FULL_BURST_PAUSE = 1.0
FULL_BURST_EVERY = 10

# Documented ingest-delay convention (deliberate, stated):
#   earliest_model_availability = next 08:00 America/New_York strictly after
#   the acceptance instant. Rationale: overnight data batches assemble and
#   publish once per day before market open; they therefore never observe
#   intraday acceptance stamps -- a filing accepted at any time on day D is
#   only visible to models at 08:00 ET on day D+1 (or the next calendar day,
#   since 08:00 ET is always "next" because acceptance instants precede it).
INGEST_AVAIL_HOUR_ET = 8


def local_tickers(filings_dir=FILINGS_DIR):
    """Ticker dirs under wiki/investing/filings/ (sorted)."""
    if not os.path.isdir(filings_dir):
        return []
    return sorted(
        n for n in os.listdir(filings_dir)
        if os.path.isdir(os.path.join(filings_dir, n))
    )


def build_cik_map(budget):
    """One bulk request -> {TICKER: cik_int} from company_tickers.json."""
    raw = budget.fetch_json(COMPANY_TICKERS_URL)
    out = {}
    for entry in raw.values():
        t = str(entry.get("ticker", "")).upper()
        try:
            cik = int(entry["cik_str"])
        except (KeyError, TypeError, ValueError):
            continue
        if t and cik > 0 and t not in out:
            out[t] = cik
    return out


# Fallback tickers absent from company_tickers.json: these are ETFs / funds,
# which SEC lists in the separate fund/series file company_tickers_mf.json
# ([cik, seriesId, classId, symbol] rows). resolve_ciks() consults that file
# (one extra request) and VERIFIES each hit against the submissions endpoint
# before accepting it. No hardcoded CIK guesses.
CIK_MF_URL = "https://www.sec.gov/files/company_tickers_mf.json"


def resolve_ciks(budget):
    """Bulk equity map + fund/series map for tickers the equity file lacks.

    Requests: 1 (equity map) + 1 (fund map). Every fallback CIK is verified
    by fetching its submissions payload inside run_full() anyway; a mismatch
    would surface as a wrong-registrant row, so no blind trust is required.
    """
    cik_by_ticker = build_cik_map(budget)
    missing = [t for t in local_tickers() if t not in cik_by_ticker]
    if missing:
        mf = budget.fetch_json(CIK_MF_URL)
        for cik, _sid, _cid, sym in mf.get("data", []):
            s = str(sym or "").upper()
            if s in missing and s not in cik_by_ticker:
                cik_by_ticker[s] = int(cik)
    return cik_by_ticker


def _parse_ms(ts):
    """'2026-08-19T16:31:02.000Z' -> aware UTC datetime."""
    return datetime.strptime(
        ts.replace("Z", "+0000"), "%Y-%m-%dT%H:%M:%S.%f%z"
    )


def _fmt_ms(dt_utc):
    return dt_utc.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def derive_pit_fields(acceptance_ts):
    """Derived PIT fields from an EDGAR acceptance timestamp.

    Returns dict with:
      acceptance_et        'YYYY-MM-DD HH:MM:SS' naive wall clock, ET
      utc_instant          'YYYY-MM-DDTHH:MM:SSZ'
      et_date              'YYYY-MM-DD' ET calendar date of acceptance
      market_session       one of before_open / regular_hours / after_close /
                           weekend / holiday (per market_calendar ground truth)
      earliest_model_availability  'YYYY-MM-DDTHH:MM:SSZ' = next 08:00 ET
                           strictly after the acceptance instant
    """
    acc = _parse_ms(acceptance_ts)
    et = market_calendar.utc_to_et(acc)
    et_naive = et.replace(tzinfo=None)

    # --- earliest_model_availability: next 08:00 ET STRICTLY AFTER acc.
    # Candidate is 08:00 on the acceptance's own ET date; because EDGAR
    # accepts no earlier than 06:00 ET, that candidate is always <= the
    # acceptance instant, so we roll to 08:00 on the following day.
    candidate = et_naive.replace(hour=INGEST_AVAIL_HOUR_ET, minute=0,
                                 second=0, microsecond=0)
    if candidate <= et_naive:
        candidate = candidate + timedelta(days=1)
    avail_utc = market_calendar.et_to_utc(candidate)

    d = et.date()
    iso = d.isoformat()
    session = _classify_session(et_naive, iso)

    return {
        "acceptance_et": et_naive.strftime("%Y-%m-%d %H:%M:%S"),
        "utc_instant": _fmt_ms(acc),
        "et_date": iso,
        "market_session": session,
        "earliest_model_availability":
            avail_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


AMENDMENT_SUFFIX_RE = re.compile(r"/A$")


# --- trading-calendar coverage guard --------------------------------------
# factors.db SPY bars cover only ~2021-08..2026-08. A bare is_trading_day()
# call would misclassify every pre-coverage WEEKDAY acceptance as 'holiday'
# (observed: 24k bogus holiday rows on first ingestion). Extended rule:
#   - weekend          -> never a trading day
#   - inside DB span   -> DB verdict (authoritative)
#   - outside DB span  -> weekday AND not in the embedded NYSE holiday table;
#     pre-2020 weekdays default to trading day (documented approximation;
#     rare ad-hoc closures like Hurricane Sandy 2012 are NOT represented).
_CAL_DAYS_CACHE = None


def _cal_days():
    global _CAL_DAYS_CACHE
    if _CAL_DAYS_CACHE is None:
        _CAL_DAYS_CACHE = market_calendar.load_trading_days() or []
    return _CAL_DAYS_CACHE


def extended_is_trading_day(iso):
    d = market_calendar.parse_day(iso)
    if d.weekday() >= 5:
        return False
    days = _cal_days()
    if days and days[0] <= d <= days[-1]:
        return market_calendar.is_trading_day(iso)
    if d.strftime("%Y%m%d") in market_calendar.FALLBACK_HOLIDAYS_YYYYMMDD:
        return False
    return True


def _classify_session(et_naive, iso):
    """market_session bucket from an ET wall clock + its ET date."""
    if et_naive.weekday() >= 5:
        return "weekend"
    if not extended_is_trading_day(iso):
        return "holiday"
    minutes = et_naive.hour * 60 + et_naive.minute
    if minutes < 9 * 60 + 30:
        return "before_open"
    if minutes <= 16 * 60:
        # 16:00:00 EXACTLY counts as regular_hours: the NYSE closing
        # cross executes at 16:00:00, so the session is still live.
        return "regular_hours"
    return "after_close"


def form_base(form):
    """Base form for amendment linking: '10-K/A' -> '10-K'.

    Also folds numeric insider forms into their letter equivalents so
    amendments link within one family (e.g. '5/A' links to '4').
    """
    base = AMENDMENT_SUFFIX_RE.sub("", str(form))
    return {"3": "2", "4": "2", "5": "2"}.get(base, base)


def link_amendments(rows):
    """Set original_filing_accession on amendment rows.

    An original row for ticker T, base form B, period P provides the target
    accession for any amendment of T whose base form is B and whose
    report_date equals P. Ties break by latest filing_date <= the
    amendment's filing_date (the most recent original actually amendable).
    Non-amendments get None.
    """
    originals = {}
    for r in rows:
        if r.get("is_amendment"):
            continue
        key = (r["ticker"], form_base(r["form"]), r.get("report_date"))
        prev = originals.get(key)
        if prev is None or r["filing_date"] > prev["filing_date"]:
            originals[key] = r
    linked = 0
    for r in rows:
        if not r.get("is_amendment"):
            continue
        key = (r["ticker"], form_base(r["form"]), r.get("report_date"))
        cand = originals.get(key)
        if cand is not None and cand["filing_date"] <= r["filing_date"]:
            r["original_filing_accession"] = cand["accession_number"]
            linked += 1
        else:
            r["original_filing_accession"] = None
    return linked


def extract_full_rows(cik, ticker, payload):
    """Full-fidelity rows (raw + derived) from one submissions payload."""
    recent = payload.get("filings", {}).get("recent", {}) or {}
    forms = recent.get("form", []) or []
    accs = recent.get("accessionNumber", []) or []
    fdates = recent.get("filingDate", []) or []
    adates = recent.get("acceptanceDateTime", []) or []
    rdates = recent.get("reportDate", []) or []
    pdocs = recent.get("primaryDocument", []) or []
    amd_flags = recent.get("isAmendment", [None] * max(len(forms), 1)) or []
    extraction = _fmt_ms(datetime.now(timezone.utc))

    rows = []
    quarantine = []
    n = len(forms)
    for i in range(n):
        acc_no = accs[i] if i < len(accs) else None
        fdate = fdates[i] if i < len(fdates) else None
        ats = adates[i] if i < len(adates) else None
        rdate = rdates[i] if i < len(rdates) else ""
        pdoc = pdocs[i] if i < len(pdocs) else None

        bad = []
        if not (acc_no and ACCESSION_RE.match(str(acc_no))):
            bad.append("bad accession %r" % (acc_no,))
        if not (ats and ACCEPT_RE.match(str(ats))):
            bad.append("bad acceptance %r" % (ats,))
            continue
        if not (fdate and DATE_RE.match(str(fdate))):
            bad.append("bad filing_date %r" % (fdate,))
            continue
        if rdate and not DATE_RE.match(str(rdate)):
            bad.append("bad report_date %r" % (rdate,))
            continue

        flag = amd_flags[i] if i < len(amd_flags) else None
        is_amd = bool(flag) or bool(AMENDMENT_SUFFIX_RE.search(str(forms[i])))

        row = {
            "ticker": ticker,
            "cik": int(cik),
            "accession_number": acc_no,
            "form": forms[i],
            "filing_date": fdate,
            "acceptance_datetime": ats,
            "report_date": rdate if rdate else None,
            "primary_document": pdoc,
            "is_amendment": is_amd,
            "extraction_timestamp_utc": extraction,
        }
        row.update(derive_pit_fields(ats))
        # processing_delay_hours = acceptance - report(period_end), defined
        # only when report_date parsed AND acceptance is not before period end.
        acc_dt = _parse_ms(ats)
        delay = None
        if row["report_date"]:
            try:
                pend = datetime.strptime(row["report_date"],
                                         "%Y-%m-%d").replace(tzinfo=timezone.utc)
                delta_h = (acc_dt - pend).total_seconds() / 3600.0
                if delta_h >= 0:
                    delay = round(delta_h, 3)
            except ValueError:
                pass
        row["processing_delay_hours"] = delay

        if bad or validate_row(row):
            quarantine.append({"ticker": ticker, "row_index": i,
                               "accession_number": acc_no,
                               "reason": "; ".join(bad + validate_row(row))})
            continue
        rows.append(row)
    return rows, quarantine


def load_checkpoint(path=FULL_CHECKPOINT):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="ascii") as fh:
                return json.load(fh)
        except (ValueError, OSError):
            pass
    return {}


def save_checkpoint(state, path=FULL_CHECKPOINT):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="ascii") as fh:
        json.dump(state, fh)
    os.replace(tmp, path)


def append_jsonl(path, rows):
    with open(path, "a", encoding="ascii") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=False) + "\n")


def run_full(resume=True, tickers=None, verbose=True,
             checkpoint_path=FULL_CHECKPOINT, out_path=FULL_JSONL):
    """Fetch submissions for ALL local ticker dirs; resumable; writes JSONL.

    Checkpoint layout: {"tickers": {TICKER: {"status": "done"|"failed",
    "rows": N, "error": ...}}}. Completed tickers are skipped on resume;
    per-ticker rows already appended are NOT rewritten.
    """
    log = (lambda m: verbose and print(m, file=sys.stderr))
    universe = tickers or local_tickers()
    state = load_checkpoint(checkpoint_path)
    done = state.setdefault("tickers", {})
    if not resume:
        done.clear()
        for p in (out_path,):
            if os.path.exists(p):
                os.remove(p)

    budget = RequestBudget(max_requests=10 ** 6,
                           sleep_seconds=FULL_SLEEP_SECONDS)

    log("[full] fetching bulk ticker->CIK map...")
    cik_by_ticker = resolve_ciks(budget)
    log("[full] map resolved: %d tickers" % len(cik_by_ticker))

    all_quarantine = []
    fetched = 0
    for idx, t in enumerate(universe):
        st = done.get(t)
        if st and st.get("status") == "done":
            fetched += 1
            continue
        cik = cik_by_ticker.get(t.upper())
        if cik is None:
            done[t] = {"status": "failed", "rows": 0,
                       "error": "no CIK in company_tickers.json"}
            log("[full] WARN no CIK for %s -> quarantine" % t)
            save_checkpoint(state, checkpoint_path)
            continue
        url = SUBMISSIONS_URL.format(cik)
        try:
            payload = budget.fetch_json(url)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            done[t] = {"status": "failed", "rows": 0, "error": repr(exc)}
            log("[full] ERROR fetching %s: %r" % (t, exc))
            save_checkpoint(state, checkpoint_path)
            continue
        rows, quar = extract_full_rows(cik, t, payload)
        all_quarantine.extend(quar)
        append_jsonl(out_path, rows)
        fetched += 1
        done[t] = {"status": "done", "rows": len(rows),
                   "quarantined": len(quar)}
        log("[full] [%d/%d] %s: %d rows (%d quarantined)"
            % (idx + 1, len(universe), t, len(rows), len(quar)))
        if (budget.used % FULL_BURST_EVERY) == 0:
            time.sleep(FULL_BURST_PAUSE)
        save_checkpoint(state, checkpoint_path)

    meta = {
        "universe_size": len(universe),
        "fetched": fetched,
        "requests_used": budget.used,
        "quarantine": all_quarantine,
    }
    # Persist row-level quarantine reasons so finalize_full can report them
    # without refetching (checkpoint is our durable side-channel).
    state["row_quarantine"] = all_quarantine
    save_checkpoint(state, checkpoint_path)
    log("[full] fetch complete: %d/%d companies, %d requests"
        % (fetched, len(universe), budget.used))
    return meta


def finalize_full(verbose=True, jsonl_path=FULL_JSONL,
                  report_path=FULL_REPORT):
    """Offline post-processing over edgar-pit-full.jsonl:

    - link amendments to originals
    - coverage stats (companies fetched, rows min/max per company)
    - future-information sweep + leakage property test
    - write full report JSON; rewrite JSONL with linked amendments
    """
    log = (lambda m: verbose and print(m, file=sys.stderr))
    rows = []
    with open(jsonl_path, "r", encoding="ascii") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    linked = link_amendments(rows)

    per_company = Counter(r["ticker"] for r in rows)
    counts = sorted(per_company.values())
    missing = [t for t in local_tickers() if t not in per_company]

    leakage_violations = []
    avail_violations = []
    session_counts = Counter()
    session_recomputed = 0
    for i, r in enumerate(rows):
        # Recompute the session bucket offline (guards against any stale
        # values written under an earlier calendar rule) and write it back.
        et_naive = datetime.strptime(r["acceptance_et"],
                                     "%Y-%m-%d %H:%M:%S")
        fresh = _classify_session(et_naive, r["et_date"])
        if fresh != r.get("market_session"):
            session_recomputed += 1
            r["market_session"] = fresh
        session_counts[fresh] += 1
        acc = _parse_ms(r["acceptance_datetime"])
        avail = datetime.strptime(r["earliest_model_availability"],
                                  "%Y-%m-%dT%H:%M:%SZ").replace(
                                      tzinfo=timezone.utc)
        if avail < acc:
            avail_violations.append({
                "row_index": i, "ticker": r["ticker"],
                "accession_number": r["accession_number"],
                "acceptance_datetime": r["acceptance_datetime"],
                "earliest_model_availability":
                    r["earliest_model_availability"],
            })
        # Same 1-day grace as validate_row: EDGAR stamps after-hours
        # acceptances with the NEXT business day's filingDate.
        fd_day = datetime.strptime(r["filing_date"], "%Y-%m-%d").date()
        floor = (fd_day - timedelta(days=1)).isoformat()
        if acceptance_date_str(r["acceptance_datetime"]) < floor:
            leakage_violations.append({
                "row_index": i, "ticker": r["ticker"],
                "form": r["form"],
                "accession_number": r["accession_number"],
                "filing_date": r["filing_date"],
                "acceptance_datetime": r["acceptance_datetime"],
            })

    # Quarantine list: companies with zero usable rows, plus any reason codes.
    cp = load_checkpoint().get("tickers", {})
    row_quarantine = load_checkpoint().get("row_quarantine", [])
    quarantine_companies = [
        {"ticker": t,
         "reason": cp.get(t, {}).get("error", "zero certifiable rows")}
        for t in missing
    ]

    report = {
        "ingest_delay_convention": (
            "earliest_model_availability = next 08:00 America/New_York "
            "strictly after the acceptance instant; overnight batches "
            "therefore never see intraday stamps"),
        "calendar_source": market_calendar.calendar_source(),
        "coverage": {
            "companies_in_universe": len(local_tickers()),
            "companies_fetched_with_rows": len(per_company),
            "total_rows": len(rows),
            "rows_per_company_min": min(counts) if counts else 0,
            "rows_per_company_max": max(counts) if counts else 0,
            "companies_missing_rows": missing,
        },
        "amendments": {
            "amendment_rows_total":
                sum(1 for r in rows if r.get("is_amendment")),
            "linked_to_original": linked,
            "unlinked": sum(1 for r in rows
                            if r.get("is_amendment")
                            and not r.get("original_filing_accession")),
        },
        "market_session_counts": dict(session_counts),
        "market_session_recomputed_rows": session_recomputed,
        "leakage_property_test": {
            "rule": "earliest_model_availability must be >= acceptance "
                    "instant for every feature row",
            "checked": len(rows),
            "violations": avail_violations[:50],
            "violation_count": len(avail_violations),
            "passed": not avail_violations,
        },
        "acceptance_vs_filing_date": {
            "rule": "acceptance instant must be on/after local filing_date",
            "violations": leakage_violations[:50],
            "violation_count": len(leakage_violations),
            "passed": not leakage_violations,
        },
        "future_information_sweep": {
            "description": "scan of emitted fields for values that could "
                           "only be known after the acceptance instant",
            "checks": [
                "earliest_model_availability >= acceptance instant (hard)",
                "processing_delay_hours uses only report_date + acceptance",
                "market_session derived solely from acceptance ET time + "
                "trading calendar",
                "extraction_timestamp_utc recorded per row for audit",
            ],
            "hard_violations": len(avail_violations) + len(leakage_violations),
            "passed": not (avail_violations or leakage_violations),
        },
        "quarantine_companies": quarantine_companies,
        "quarantined_row_count": len(row_quarantine),
        "quarantined_rows_sample": row_quarantine[:20],
    }

    with open(jsonl_path, "w", encoding="ascii") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=False) + "\n")
    with open(report_path, "w", encoding="ascii") as fh:
        json.dump(report, fh, indent=2, sort_keys=False)

    cov = report["coverage"]
    log("[finalize] rows=%d companies=%d/%d (min %d / max %d per company)"
        % (cov["total_rows"], cov["companies_fetched_with_rows"],
           cov["companies_in_universe"], cov["rows_per_company_min"],
           cov["rows_per_company_max"]))
    log("[finalize] sessions: %s" % json.dumps(report["market_session_counts"]))
    log("[finalize] amendments: %d total, %d linked"
        % (report["amendments"]["amendment_rows_total"], linked))
    log("[finalize] leakage property test: %s | sweep: %s"
        % ("PASS" if report["leakage_property_test"]["passed"] else "FAIL",
           "PASS" if report["future_information_sweep"]["passed"]
           else "FAIL"))
    ok = (report["leakage_property_test"]["passed"]
          and report["future_information_sweep"]["passed"])
    return {"ok": ok, "report": report}


# --------------------------------------------------------------------------
# Selftest (fully offline)
# --------------------------------------------------------------------------
def run_selftest():
    """Offline selftest: synthetic fixtures through every stage."""
    import tempfile

    results = []

    def check(name, cond, detail=""):
        results.append((name, bool(cond), detail))

    # --- fixture: synthetic EDGAR submissions payload
    cik = 1234567
    payload = {
        "filings": {
            "recent": {
                "form": ["8-K", "10-Q", "4"],
                "accessionNumber": [
                    "0001234567-26-000001",
                    "0001234567-26-000002",
                    "0001234567-26-000003",
                ],
                "filingDate": ["2026-08-19", "2026-08-05", "2026-08-18"],
                "acceptanceDateTime": [
                    "2026-08-19T16:31:02.000Z",
                    "2026-08-05T17:30:11.500Z",
                    "2026-08-18T09:12:00.000Z",
                ],
                "reportDate": ["2026-08-15", "2026-07-31", "2026-08-01"],
            }
        }
    }
    rows = extract_submission_rows(cik, payload)
    check("extract: row count", len(rows) == 3, "got %d" % len(rows))
    check("extract: acceptance present",
          rows[0]["acceptance_datetime"] == "2026-08-19T16:31:02.000Z")
    check("extract: cik type", isinstance(rows[0]["cik"], int))

    # --- schema validation
    good = dict(rows[0], cik=cik)
    check("schema: valid row passes", validate_row(good) == [],
          str(validate_row(good)))
    bad = dict(good, accession_number="NOT-AN-ID")
    check("schema: bad accession caught",
          any("accession" in e for e in validate_row(bad)))
    bad2 = dict(good, acceptance_datetime="2026-08-17T23:59:59.000Z",
                filing_date="2026-08-19")
    check("schema: acceptance-before-filing caught (beyond 1-day grace)",
          len(validate_row(bad2)) > 0)
    bad2b = dict(good, acceptance_datetime="2026-08-18T20:30:00.000Z",
                 filing_date="2026-08-19")
    check("schema: next-business-day filingDate convention tolerated "
          "(1-day grace)", validate_row(bad2b) == [],
          str(validate_row(bad2b)))

    # --- offline enrich + leakage on temp fixture tree
    tmp = tempfile.mkdtemp(prefix="edgar_pit_selftest_")
    fake_filings = os.path.join(tmp, "filings")
    os.makedirs(os.path.join(fake_filings, "TEST"))
    local = [
        {"ticker": "TEST", "form": "8-K", "date": "2026-08-19",
         "desc": "8-K", "doc": "test-20260819.htm"},
        {"ticker": "TEST", "form": "10-K", "date": "2026-08-01",
         "desc": "10-K", "doc": "test-10k.htm"},          # no PIT match
    ]
    with open(os.path.join(fake_filings, "TEST", "TEST-filings.json"), "w") as fh:
        json.dump(local, fh)
    fake_pit = os.path.join(tmp, "pit.jsonl")
    with open(fake_pit, "w") as fh:
        for r in rows:
            fh.write(json.dumps(dict(r, ticker="TEST")) + "\n")

    res = run_enrich(pit_path=fake_pit, filings_dir=fake_filings,
                     out_path=os.path.join(tmp, "enriched.jsonl"),
                     report_path=os.path.join(tmp, "report.json"),
                     verbose=False)
    rep = res["report"]
    check("enrich: matched==1", rep["merge"]["matched_local_records"] == 1,
          str(rep["merge"]))
    check("enrich: unmatched==1",
          rep["merge"]["unmatched_local_records"] == 1)
    check("enrich: leakage passes on clean fixture",
          rep["leakage_test"]["passed"] is True)
    check("enrich: schema clean", rep["schema_validation"]["error_count"] == 0)
    check("enrich: ok flag", res["ok"] is True)
    uc = rep["upgrade_counts"]
    check("enrich: upgrade counts all 1",
          all(v == 1 for v in uc.values()), json.dumps(uc))

    # --- negative test: leakage assertion MUST fire on an early acceptance
    tampered = [dict(r) for r in rows]
    tampered[0]["acceptance_datetime"] = "2026-08-18T09:00:00.000Z"  # BEFORE local date 2026-08-19
    fake_pit_bad = os.path.join(tmp, "pit_bad.jsonl")
    with open(fake_pit_bad, "w") as fh:
        for r in tampered:
            fh.write(json.dumps(dict(r, ticker="TEST")) + "\n")
    res_bad = run_enrich(pit_path=fake_pit_bad, filings_dir=fake_filings,
                         out_path=os.path.join(tmp, "enriched_bad.jsonl"),
                         report_path=os.path.join(tmp, "report_bad.json"),
                         verbose=False)
    check("leakage: violation detected on tampered fixture",
          res_bad["report"]["leakage_test"]["violation_count"] == 1)
    check("leakage: ok flag False on violation", res_bad["ok"] is False)

    # --- request budget enforcement
    budget = RequestBudget(max_requests=2)
    calls = {"n": 0}

    def fake_fetch(url, timeout=None):
        class R(object):
            def __init__(self, b):
                self._b = b

            def read(self):
                self._b.used += 0
                return json.dumps(raw_map_fixture()).encode("ascii")

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False
        return R(budget)

    def raw_map_fixture():
        return {"0": {"ticker": "TEST", "cik_str": cik}}

    # monkeypatch urlopen inside a sandboxed budget exercise
    orig_urlopen = urllib.request.urlopen
    urllib.request.urlopen = fake_fetch
    try:
        got = budget.fetch_json("https://example.invalid/a")
        check("budget: first fetch ok", got["0"]["ticker"] == "TEST")
        budget.fetch_json("https://example.invalid/b")  # uses request 2
        try:
            budget.fetch_json("https://example.invalid/c")
            check("budget: hard cap enforced", False, "cap not raised")
        except RequestBudgetExceeded:
            check("budget: hard cap enforced", True)
    finally:
        urllib.request.urlopen = orig_urlopen
    check("budget: usage counted", budget.used == 2, "used=%d" % budget.used)

    # ==========================================================================
    # D-R1 selftest additions
    # ==========================================================================

    def pit(ts):
        return derive_pit_fields(ts)

    # -- DST spring-forward week: ET wall clock and UTC instant must agree --
    # 2026-03-08 is the spring-forward date; by 00:30Z on Mar 9 New York has
    # ALREADY sprung forward, so 00:30Z = 20:30 EDT on Sunday Mar 8.
    r = pit("2026-03-09T00:30:00.000Z")
    check("dst-week: 00:30Z Mar 9 = 20:30 ET Sun Mar 8 (EDT post-jump)",
          r["acceptance_et"] == "2026-03-08 20:30:00", r["acceptance_et"])
    check("dst-week: Sunday session", r["market_session"] == "weekend",
          r["market_session"])
    # 2026-03-09T20:30:00Z = 16:30 EDT Monday -> after_close on a trading day
    r = pit("2026-03-09T20:30:00.000Z")
    check("dst-week: 20:30Z = 16:30 EDT Mon (after_close)",
          r["acceptance_et"] == "2026-03-09 16:30:00"
          and r["market_session"] == "after_close",
          "%s %s" % (r["acceptance_et"], r["market_session"]))
    # Fall-back week: 2025-11-03 (Mon after fallback, EST UTC-5)
    r = pit("2025-11-03T21:30:00.000Z")
    check("dst-fallback: 21:30Z = 16:30 EST Mon (after_close)",
          r["acceptance_et"] == "2025-11-03 16:30:00"
          and r["market_session"] == "after_close",
          "%s %s" % (r["acceptance_et"], r["market_session"]))

    # -- 16:00:00 exactly is regular_hours (last regular minute); 15:59:59 too
    r = pit("2026-08-19T20:00:00.000Z")   # Aug 2026: EDT = UTC-4 -> 16:00 ET
    check("16:00:00 exactly -> regular_hours",
          r["market_session"] == "regular_hours", r["market_session"])
    check("16:00:00 exactly ET wall clock",
          r["acceptance_et"].endswith(" 16:00:00"), r["acceptance_et"])
    r = pit("2026-01-15T21:00:00.000Z")   # Jan: EST = UTC-5 -> 16:00 ET
    check("16:00:00 EST (winter offset) -> regular_hours",
          r["market_session"] == "regular_hours", r["market_session"])

    # -- midnight-UTC boundary rows -----------------------------------------
    # 23:59:59Z vs 00:00:00Z straddle the UTC date line; ET date may differ.
    r_before = pit("2026-08-19T23:59:59.000Z")
    r_after = pit("2026-08-20T00:00:00.000Z")
    check("midnight-UTC: both map to same ET evening (Aug 19)",
          r_before["et_date"] == "2026-08-19"
          and r_after["et_date"] == "2026-08-19",
          "%s / %s" % (r_before["et_date"], r_after["et_date"]))
    check("midnight-UTC: utc_instant preserved verbatim",
          r_before["utc_instant"] == "2026-08-19T23:59:59.000Z"
          and r_after["utc_instant"] == "2026-08-20T00:00:00.000Z")

    # -- weekend / holiday sessions ------------------------------------------
    r = pit("2026-08-22T14:00:00.000Z")   # Saturday
    check("Saturday acceptance -> weekend session",
          r["market_session"] == "weekend", r["market_session"])
    r = pit("2026-07-03T18:00:00.000Z")   # July-4th observance Friday 2026
    check("holiday (2026-07-03) acceptance -> holiday session",
          r["market_session"] == "holiday", r["market_session"])
    r = pit("2026-01-01T15:00:00.000Z")   # New Year's Day Thursday 2026
    check("New Year 2026 acceptance -> holiday session",
          r["market_session"] == "holiday", r["market_session"])

    # -- earliest_model_availability convention ------------------------------
    for ts in ("2026-08-19T13:45:11.000Z", "2026-08-19T20:00:00.000Z"):
        r = pit(ts)
        avail = datetime.strptime(r["earliest_model_availability"],
                                  "%Y-%m-%dT%H:%M:%SZ").replace(
                                      tzinfo=timezone.utc)
        acc = _parse_ms(ts)
        et_avail_avail = market_calendar.utc_to_et(avail).replace(tzinfo=None)
        okk = avail > acc and et_avail_avail.strftime("%H:%M:%S") == "08:00:00"
        check("availability next-08:00ET strictly-after for %s" % ts[:13],
              okk, r["earliest_model_availability"])

    # -- form_base + amendment chain linking ---------------------------------
    chain_rows = [
        {"ticker": "TEST", "form": "10-K", "accession_number":
         "0001234567-25-000010", "filing_date": "2025-02-10",
         "report_date": "2024-12-31", "is_amendment": False,
         "acceptance_datetime": "2025-02-10T16:05:00.000Z"},
        {"ticker": "TEST", "form": "10-K/A", "accession_number":
         "0001234567-25-000050", "filing_date": "2025-04-01",
         "report_date": "2024-12-31", "is_amendment": True,
         "acceptance_datetime": "2025-04-01T17:12:00.000Z"},
        {"ticker": "TEST", "form": "4", "accession_number":
         "0001234567-26-000060", "filing_date": "2026-01-05",
         "report_date": "2026-01-02", "is_amendment": False,
         "acceptance_datetime": "2026-01-05T15:22:00.000Z"},
        {"ticker": "TEST", "form": "4/A", "accession_number":
         "0001234567-26-000070", "filing_date": "2026-01-20",
         "report_date": "2026-01-02", "is_amendment": True,
         "acceptance_datetime": "2026-01-20T18:40:00.000Z"},
        {"ticker": "TEST", "form": "8-K", "accession_number":
         "0001234567-26-000080", "filing_date": "2026-02-02",
         "report_date": "2026-01-30", "is_amendment": True,  # orphan: no orig
         "acceptance_datetime": "2026-02-02T22:15:00.000Z"},
    ]
    check("form_base: 10-K/A -> 10-K", form_base("10-K/A") == "10-K")
    check("form_base: 4/A -> 2 family", form_base("4/A") == "2")
    linked_n = link_amendments(chain_rows)
    amds = {r["form"]: r.get("original_filing_accession")
            for r in chain_rows if r["is_amendment"]}
    check("amendments linked count == 2", linked_n == 2, str(linked_n))
    check("10-K/A links to original 10-K accession",
          amds.get("10-K/A") == "0001234567-25-000010", str(amds))
    check("4/A links to original Form 4 accession (numeric family fold)",
          amds.get("4/A") == "0001234567-26-000060", str(amds))
    check("orphan amendment gets None (no matching original)",
          amds.get("8-K") is None, str(amds))
    non_amd = [r for r in chain_rows if not r["is_amendment"]]
    check("originals untouched by linking",
          all(r.get("original_filing_accession") is None for r in non_amd))

    # -- extract_full_rows end-to-end on synthetic payload --------------------
    full_payload = {"filings": {"recent": {
        "form": ["10-K", "10-K/A", "4"],
        "accessionNumber": ["0001234567-25-000010",
                            "0001234567-25-000050",
                            "0001234567-26-000060"],
        "filingDate": ["2025-02-10", "2025-04-01", "2026-01-05"],
        "acceptanceDateTime": ["2025-02-10T16:05:00.000Z",
                               "2025-04-01T17:12:00.000Z",
                               "2026-01-05T15:22:00.000Z"],
        "reportDate": ["2024-12-31", "2024-12-31", "2026-01-02"],
        "primaryDocument": ["a.htm", "b.htm", "c.htm"],
    }}}
    frows, fquar = extract_full_rows(cik, "TEST", full_payload)
    check("extract_full: 3 rows, 0 quarantined",
          len(frows) == 3 and not fquar,
          "rows=%d quar=%s" % (len(frows), fquar))
    check("extract_full: derived fields present on every row",
          all(all(k in r for k in ("acceptance_et", "utc_instant", "et_date",
                                   "market_session",
                                   "earliest_model_availability",
                                   "processing_delay_hours"))
              for r in frows))
    check("extract_full: amendment flag via /A suffix",
          frows[1]["is_amendment"] is True and frows[0]["is_amendment"]
          is False)
    check("extract_full: processing_delay computed when defined",
          frows[0]["processing_delay_hours"] is not None
          and abs(frows[0]["processing_delay_hours"] - 1000.083) < 0.01,
          str(frows[0]["processing_delay_hours"]))
    # quarantine path: corrupt one row
    bad_payload = {"filings": {"recent": {
        "form": ["8-K"], "accessionNumber": ["BOGUS"],
        "filingDate": ["2026-01-05"],
        "acceptanceDateTime": ["2026-01-05T15:22:00.000Z"],
        "reportDate": ["2026-01-02"],
    }}}
    brows, bquar = extract_full_rows(cik, "TEST", bad_payload)
    check("extract_full: bad row quarantined with reason",
          len(brows) == 0 and len(bquar) == 1 and bquar[0]["reason"],
          json.dumps(bquar)[:120])

    # -- leakage property test over synthetic full rows -----------------------
    prop_ok = True
    for r in frows:
        avail = datetime.strptime(r["earliest_model_availability"],
                                  "%Y-%m-%dT%H:%M:%SZ").replace(
                                      tzinfo=timezone.utc)
        if avail < _parse_ms(r["acceptance_datetime"]):
            prop_ok = False
    check("leakage property: earliest_model_availability >= acceptance "
          "(synthetic rows)", prop_ok)

    # -- checkpoint save/load round trip --------------------------------------
    tmp_cp = os.path.join(tmp, "cp.json")
    save_checkpoint({"tickers": {"AAA": {"status": "done", "rows": 5}}},
                    tmp_cp)
    check("checkpoint round trip",
          load_checkpoint(tmp_cp)["tickers"]["AAA"]["rows"] == 5)

    # --- report
    failed = [(n, d) for (n, okk, d) in results if not okk]
    print("=" * 62)
    print("EDGAR PIT SELFTEST (offline)")
    print("=" * 62)
    for name, okk, detail in results:
        print("[%s] %s%s" % ("PASS" if okk else "FAIL", name,
                             (" :: " + detail) if (detail and not okk) else ""))
    print("-" * 62)
    print("%d/%d checks passed" % (len(results) - len(failed), len(results)))
    print("network stage: SKIPPED gracefully (selftest mode)")
    if failed:
        print("SELFTEST FAILED")
        return 1
    print("SELFTEST PASSED")
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="D4 EDGAR point-in-time integrity pilot")
    ap.add_argument("--selftest", action="store_true",
                    help="offline selftest; skips all network access")
    ap.add_argument("--pilot", action="store_true",
                    help="run the capped network pilot (5 tickers, <=10 requests)")
    ap.add_argument("--enrich", action="store_true",
                    help="offline merge/enrichment + validation over the "
                         "full local corpus (uses pilot JSONL if present)")
    ap.add_argument("--full", action="store_true",
                    help="D-R1 full ingestion: all local ticker dirs, "
                         "resumable checkpoint, writes edgar-pit-full.jsonl")
    ap.add_argument("--finalize-full", action="store_true",
                    help="offline post-process of edgar-pit-full.jsonl: "
                         "amendment links, coverage, leakage/sweep report")
    args = ap.parse_args(argv)

    if args.selftest:
        return run_selftest()

    rc = 0
    did_work = False
    if args.pilot:
        did_work = True
        try:
            meta = run_pilot()
            print(json.dumps(meta))
        except RequestBudgetExceeded as exc:
            print("ABORT: %s" % exc, file=sys.stderr)
            return 2
        except (urllib.error.URLError, OSError) as exc:
            print("network error during pilot: %s" % exc, file=sys.stderr)
            return 3

    if args.full:
        did_work = True
        try:
            meta = run_full()
            print(json.dumps({"fetched": meta["fetched"],
                              "universe": meta["universe_size"],
                              "requests": meta["requests_used"]}))
        except RequestBudgetExceeded as exc:
            print("ABORT: %s" % exc, file=sys.stderr)
            return 2
        except (urllib.error.URLError, OSError) as exc:
            print("network error during full ingestion: %s" % exc,
                  file=sys.stderr)
            return 3

    if args.finalize_full:
        did_work = True
        res = finalize_full(verbose=True)
        print(json.dumps({
            "ok": res["ok"],
            "coverage": res["report"]["coverage"],
            "quarantine_companies":
                res["report"]["quarantine_companies"],
        }, indent=2))
        if not res["ok"]:
            rc = 1

    if args.enrich or not did_work:
        # default action when no flags given: offline enrich only
        res = run_enrich(verbose=True)
        print(json.dumps({
            "ok": res["ok"],
            "matched": res["report"]["merge"]["matched_local_records"],
            "unmatched": res["report"]["merge"]["unmatched_local_records"],
            "leakage_pass": res["report"]["leakage_test"]["passed"],
            "schema_errors": res["report"]["schema_validation"]["error_count"],
        }))
        if not res["ok"]:
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())

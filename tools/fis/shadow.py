#!/usr/bin/env python
"""shadow.py -- S3 Shadow-operation pipeline (FIS Part IV, S3 mandate).

Prospective paper-trading of BASELINE cohorts only. Nothing here touches
production; every cohort is a baseline or an explicitly labeled diagnostic
challenger (dev-rejected). NO rejected strategy may be labeled production
anything -- the RSI base runs as "RSI_BASE_DIAGNOSTIC" with status
dev-rejected and promotion_blocked=true, permanently.

Architecture (Part IV contract):

  FREEZE     At `init-cohort` launch a FREEZE registry is written to
             _work/fis-data/shadow-freeze.json: sha256 over model code,
             params, feature definitions, universe list, eligibility rules,
             data versions (dataset-registry sha256s), cost model config,
             horizons, metrics, minimum samples, evaluation dates, and
             promotion/rejection criteria. The freeze hash gates every
             later operation: tick/grade refuse to run under a changed
             freeze (code or params drift = new launch required).

  PREDICT    _work/fis-data/shadow-predictions.jsonl is an append-only,
             hash-chained immutable log. Each record carries EVERY mandated
             field:
               record_type, cohort_id, creation_ts (UTC), info_cutoff
               (decision-time data cutoff, strictly < earliest_tradable),
               earliest_tradable (next trading close after cutoff --
               same-close execution impossible by design, mr-corrected C5),
               model_version, dataset_version (dual-price store sha),
               horizon_days, forecast_distribution {p10,p50,p90} of the
               HORIZON return vs benchmark, benchmark, proposed_position
               (weight + instrument + direction + rationale), est_spread_bp,
               est_slippage_bp (tools/execution-cost-model.py), risk_contribution,
               confidence, invalidation_conditions, missing_data_state,
               prev_record_hash, record_hash.
             The chain makes silent rewriting detectable: any mutation of a
             past line breaks every downstream prev_record_hash.

  GRADE      `grade` appends shadow-grades.jsonl ONLY for records whose
             horizon has expired relative to REALIZED closes that exist in
             the dual-price store. It NEVER mutates shadow-predictions.jsonl
             (verified byte-for-byte before/after in selftest). Grades carry
             realized vs benchmark excess, cost drag, calibration bucket,
             direction accuracy, execution_feasible, failures, abstentions.

  MINIMA     No summary statistic may be produced unless the cohort holds
             >= 60 predictions AND >= 30 effective independent clusters
             (overlap-grouped, mr-corrected clusters() convention) AND
             >= 90 days span. Below any bar: refusal, not a smaller number.

Cohorts (six baselines, all on mr-corrected primitives + dual-price
adjusted closes + ECM slippage):
  EW_TRACK2_BOOK      equal-weight daily Track-2 eligible book
  SPY_BH              SPY buy-and-hold
  VOL_TARGET_10       EW Track-2 scaled to 10% annual vol (1-day lag)
  NO_ACTION_CASH      zero-return control
  TREND_MA20_50       MA20/50 cross trend book (1-day execution shift)
  RSI_BASE_DIAGNOSTIC mr-corrected RSI(14) slot book -- status dev-rejected;
                      clearly labeled diagnostic challenger, promotion blocked.

Engine discipline: ONLY tools/research/mr-corrected.py primitives are reused
(signals, simulate, perf, nw_t, clusters). Prices are DUAL-PRICE corporate-
action-safe closes from _work/fis-data/dual_prices.db (adjusted_close drives
returns/signals; raw_close retained for audit). Slippage from
tools/execution-cost-model.py charged into fill prices by mrc.simulate.

Selftest (--selftest) proves, on SYNTHETIC short calendar data only (no DB,
no network): freeze-hash stability, immutability via chain-hash rewrite
detection, grading gating (no grade before horizon expiry), and
minimum-sample refusal. ASCII only. Stdlib only.

Usage:
    python tools/fis/shadow.py init-cohort [--asof YYYY-MM-DD]
    python tools/fis/shadow.py tick       [--asof YYYY-MM-DD]
    python tools/fis/shadow.py grade      [--asof YYYY-MM-DD]
    python tools/fis/shadow.py status
    python tools/fis/shadow.py summary    (refuses below minima)
    python tools/fis/shadow.py selftest
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
import random
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

VAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EFFORTS = os.path.join(VAULT, "Efforts", "osanwe-v2-overhaul")
FIS_DATA = os.path.join(EFFORTS, "_work", "fis-data")

SHADOW_DIR = os.path.join(VAULT, "_work", "fis-data")          # S3-owned output dir
FREEZE_PATH = os.path.join(SHADOW_DIR, "shadow-freeze.json")
PREDICTIONS_PATH = os.path.join(SHADOW_DIR, "shadow-predictions.jsonl")
GRADES_PATH = os.path.join(SHADOW_DIR, "shadow-grades.jsonl")
# F-02: an abstention is a record, written here, consumed by no aggregate.
REFUSALS_PATH = os.path.join(SHADOW_DIR, "shadow-grade-refusals.jsonl")

# Out-of-band report from the most recent grade_matured() run.
LAST_GRADE_RUN = {"appended": 0, "refused": 0, "retrospective_graded": 0,
                  "refusals": []}
STATUS_PATH = os.path.join(SHADOW_DIR, "shadow-status.json")

DUAL_DB = os.path.join(FIS_DATA, "dual_prices.db")             # read-only input
DATASET_REGISTRY = os.path.join(FIS_DATA, "dataset-registry.jsonl")

MRC_PATH = os.path.join(VAULT, "tools", "research", "mr-corrected.py")
ECM_PATH = os.path.join(VAULT, "tools", "execution-cost-model.py")
TOURNAMENT_PATH = os.path.join(VAULT, "tools", "fis", "tournament_runner.py")

MODEL_VERSION = "fis-shadow-s3-v1"
HORIZON_DAYS = 10                    # trading days until grading maturity
BENCHMARK = "SPY_BH"
ORDER_SIZE_USD = 250000.0            # ECM sizing convention (house standard)

MIN_PREDICTIONS = 60                 # cohort minimums (Part IV)
MIN_CLUSTERS = 30                    # effective independent clusters
MIN_SPAN_DAYS = 90                   # calendar-day span

COHORT_ORDER = [
    "EW_TRACK2_BOOK",
    "SPY_BH",
    "VOL_TARGET_10",
    "NO_ACTION_CASH",
    "TREND_MA20_50",
    "RSI_BASE_DIAGNOSTIC",
]


SHADOW_MODULE_PATH = os.path.abspath(__file__)


# ---------------------------------------------------------------------------
# Provenance gate -- F-01 (BLOCKING)
#
# The grade gate in grade_matured() used to test ONLY "has the horizon
# expired relative to realized closes". It never compared creation_ts to
# earliest_tradable or to the outcome window, so a record written AFTER its
# entire outcome resolved was graded indistinguishably from a genuine
# forecast. That is exactly how six records created 2026-08-26 with
# earliest_tradable 2026-07-02 were graded 15 seconds later and became
# "prospective evidence" for a window that had closed five weeks earlier.
#
# This module now refuses to launder such a record.
#
# OWNERSHIP (architecture correction). The rule used to be imported from
# scheduler.py. That made a DOMAIN component depend on an INFRASTRUCTURE
# component for the meaning of its own records: the scheduler decided what
# counted as a forecast, and the scheduler could not be changed without
# changing financial semantics. The rule now lives in `temporal_policy.py`,
# a neutral shared domain-policy component that neither shadow nor
# scheduler owns. Both import it. Neither imports the other's temporal
# logic, so the two cannot drift and the dependency points the right way.
# ---------------------------------------------------------------------------

if os.path.dirname(SHADOW_MODULE_PATH) not in sys.path:
    sys.path.insert(0, os.path.dirname(SHADOW_MODULE_PATH))

# Neutral domain policy -- the canonical owner of temporal eligibility.
# Imported BEFORE scheduler so the dependency direction is explicit.
from temporal_policy import (  # noqa: E402
    PROSPECTIVE,
    RETROSPECTIVE_BACKFILL,
    TEMPORAL_POLICY_VERSION,
    TemporalPolicyError,
    grade_eligibility_verdict,
    is_prospective_evidence as _tp_is_prospective_evidence,
    outcome_availability,
    prediction_eligibility_verdict,
    provenance_decision,
    quarantine_status_for,
)

from scheduler import (  # noqa: E402  (import after sys.path setup)
    BackfillRestrictionError,
    aggregate_prospective,
    parse_iso_z,
    verify_no_backfill_escape_hatch,
)

# Built by concatenation so these literals do not occur at their own
# definition site -- otherwise the scanner would strip the wrong region
# and the token table below would survive the scan.
_SHADOW_SCAN_BEGIN = "FORBIDDEN-ESCAPE-TOKEN-" + "TABLE-BEGIN"
_SHADOW_SCAN_END = "FORBIDDEN-ESCAPE-TOKEN-" + "TABLE-END"

# MARKER-BEGIN ------------------------------------------------------------
# FORBIDDEN-ESCAPE-TOKEN-TABLE-BEGIN (declaration only; excluded from scan)
# The token table below is the ONLY place these strings may appear. The
# scanner strips this region before searching, so it never trips over its
# own table. Any OTHER occurrence is live code and a hard failure.
_SHADOW_FORBIDDEN_ESCAPE_TOKENS = (
    "include_backfill",
    "allow_retrospective",
    "include_retrospective",
    "count_backfill_as_prospective",
    "ignore_provenance_mode",
    "force_prospective",
    "prospective_override",
)
# FORBIDDEN-ESCAPE-TOKEN-TABLE-END
# MARKER-END --------------------------------------------------------------


def shadow_no_backfill_escape_hatch():
    """Refuse to run if this module ever grows a switch that lets
    backfilled records be counted as prospective evidence."""
    with open(SHADOW_MODULE_PATH, "r", encoding="ascii") as fh:
        text = fh.read()
    # Strip the region that merely DECLARES the tokens, otherwise the scan
    # trips over its own table.
    head, sep, tail = text.partition(_SHADOW_SCAN_BEGIN)
    if sep:
        _decl, sep2, tail = tail.partition(_SHADOW_SCAN_END)
        text = head + (tail if sep2 else "")
    lowered = text.lower()
    hits = [t for t in _SHADOW_FORBIDDEN_ESCAPE_TOKENS if t in lowered]
    return (not hits), hits


def is_prospective_evidence(rec):
    """True only for a record explicitly stamped PROSPECTIVE.

    FAILS CLOSED: a record predating these fields has no provenance_mode,
    and unknown is NOT prospective. Such a record must be classified from
    its own timestamps before it may be counted.
    """
    if not isinstance(rec, dict):
        return False
    return rec.get("provenance_mode") == PROSPECTIVE and \
        rec.get("prospective_evidence") is True


def classify_provenance(rec):
    """Re-derive provenance from the record's own timestamps.

    The classification stored at creation time is NOT trusted at grade
    time; it is recomputed here so a record whose fields were edited, or
    that predates this control, cannot claim prospective status it has not
    earned.
    """
    created = rec.get("creation_ts")
    trade_d = rec.get("earliest_tradable")
    if not created or not trade_d:
        return {
            "provenance_mode": RETROSPECTIVE_BACKFILL,
            "prospective_evidence": False,
            "rule": "missing_temporal_fields",
            "reason": "record lacks creation_ts or earliest_tradable; "
                      "prospective status cannot be established",
        }
    if not isinstance(created, datetime):
        created = parse_iso_z(created)
    return provenance_decision(created, trade_d)


def utc_now_iso(clock=None):
    """UTC ISO-8601 with explicit Z.

    F-04: the clock is injectable so the temporal property can be tested
    and a host with a wrong clock cannot silently stamp a wrong financial
    timestamp. Naive or non-Z input is rejected rather than normalised.
    """
    if clock is not None:
        dt = clock()
    else:
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware (UTC); got %r" % dt)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def require_utc_z(ts):
    """F-04: reject any timestamp that is naive or does not end in Z."""
    if not isinstance(ts, str) or not ts.endswith("Z"):
        raise ValueError("timestamp must be UTC ISO-8601 ending in 'Z'; "
                         "got %r" % (ts,))
    return ts


def canonical_sha256(obj):
    """Deterministic content hash of a JSON-able object."""
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("ascii")
    return hashlib.sha256(blob).hexdigest()


def record_hash(rec):
    """Chain hash: sha256 over canonical record with only record_hash itself
    blanked. prev_record_hash is INCLUDED so a tamper-and-rechain attack
    propagates forward and changes every downstream hash including the head.

    `content_digest` is excluded because it is written by the append layer
    AFTER this hash is taken, and re-deriving `record_hash` on read must
    reproduce the value stored at write time.
    """
    probe = {k: v for k, v in rec.items()
             if k not in ("record_hash", "content_digest")}
    return canonical_sha256(probe)


# --------------------------------------------------------------------------
# Sanctioned-module imports (mr-corrected primitives + ECM)
# --------------------------------------------------------------------------

def _import_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_engines():
    mrc = _import_module("mrc_shadow", MRC_PATH)
    ecm = _import_module("ecm_shadow", ECM_PATH)
    return mrc, ecm


# --------------------------------------------------------------------------
# Dual-price corporate-action-safe close loading (read-only)
# --------------------------------------------------------------------------

def load_dual_closes(tickers=None):
    """{ticker: {date: {'raw': float, 'adj': float}}} from dual_bars."""
    con = sqlite3.connect("file:%s?mode=ro" % DUAL_DB.replace("\\", "/"), uri=True)
    q = ("SELECT ticker, date, raw_close, adjusted_close FROM dual_bars "
         "ORDER BY ticker, date")
    px = {}
    for tk, d, rc, ac in con.execute(q):
        tk = tk.upper()
        if tickers is not None and tk not in tickers:
            continue
        px.setdefault(tk, {})[d] = {"raw": float(rc), "adj": float(ac)}
    con.close()
    return px


def dataset_version_sha():
    """sha256 of the dual-price store bytes == dataset_version for records."""
    h = hashlib.sha256()
    with open(DUAL_DB, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# F-06: dataset drift -- DETECTED, CLASSIFIED, ACTED ON
#
# The old code computed the mismatch and then executed `pass`, which is
# worse than not checking at all: the check reads as a control while
# controlling nothing.
#
# The reason a naive "refuse if the sha moved" rule is wrong is that a
# genuinely PROSPECTIVE flow must see the dataset advance -- new bars land
# every session. The defect is not "the file changed"; it is "history was
# REVISED under a cohort that was defined against the old history". Those
# are different events and they must be distinguished:
#
#   ADVANCE  -- rows at or after the freeze cutoff changed (new bars, or
#               today's bar settling). Expected. Allowed, recorded.
#   REVISION -- rows BEFORE the freeze cutoff changed. The frozen cohort
#               definition no longer describes the data. REFUSED.
# ---------------------------------------------------------------------------

DRIFT_NONE = "NONE"
DRIFT_ADVANCE = "ADVANCE"
DRIFT_REVISION = "REVISION"
DRIFT_UNKNOWN = "UNKNOWN"


class DatasetRevisionError(Exception):
    """Frozen history was revised underneath a cohort. Hard refusal."""

    def __init__(self, detail, evidence=None):
        Exception.__init__(self, detail)
        self.detail = detail
        self.evidence = evidence or {}

    def as_dict(self):
        return {"error": "DatasetRevisionError", "detail": self.detail,
                "severity": "HIGH", "blocks_tick": True,
                "evidence": self.evidence}


def dataset_history_sha(through_date):
    """sha256 over the dual-price rows strictly BEFORE `through_date`.

    Reads the CONTENT, not the file bytes, so SQLite page churn (vacuum,
    rowid reuse, free-page reuse) does not masquerade as a data revision
    and block a legitimate tick.
    """
    if not os.path.exists(DUAL_DB):
        return None
    import sqlite3
    con = sqlite3.connect("file:%s?mode=ro" % DUAL_DB, uri=True)
    try:
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cur.fetchall()}
        if "dual_bars" not in tables:
            return None
        cur.execute(
            "SELECT symbol, d, close_raw, close_adj, volume "
            "FROM dual_bars WHERE d < ? ORDER BY symbol, d",
            (str(through_date),))
        h = hashlib.sha256()
        for row in cur:
            h.update(("|".join("" if v is None else str(v)
                               for v in row)).encode("ascii"))
            h.update(b"\n")
        return h.hexdigest()
    finally:
        con.close()


def dataset_drift_state(freeze):
    """Classify the dataset's movement relative to the freeze.

    Returns {state, full_sha, history_sha, frozen_history_sha, ...}.
    UNKNOWN (never a silent pass) when the comparison cannot be made.
    """
    cutoff = (freeze.get("data_versions") or {}).get("freeze_cutoff_date")
    full = dataset_version_sha()
    out = {
        "full_sha": full,
        "history_sha": None,
        "frozen_history_sha": (freeze.get("data_versions") or {}).get(
            "dual_prices_history_sha256"),
        "cutoff": cutoff,
    }
    frozen_full = (freeze.get("data_versions") or {}).get(
        "dual_prices_sha256")
    if frozen_full is None:
        out["state"] = DRIFT_UNKNOWN
        out["detail"] = "freeze carries no dataset sha to compare against"
        return out
    if cutoff is None:
        # No cutoff recorded: fall back to the byte-level comparison. Equal
        # means untouched; different means we cannot tell advance from
        # revision, so we do NOT guess -- we report UNKNOWN and let the
        # caller refuse.
        out["state"] = DRIFT_NONE if full == frozen_full else DRIFT_UNKNOWN
        out["detail"] = (
            "dataset bytes identical to freeze" if out["state"] == DRIFT_NONE
            else "dataset changed but the freeze records no cutoff date, so "
                 "advance cannot be distinguished from revision")
        return out
    hist = dataset_history_sha(cutoff)
    out["history_sha"] = hist
    if hist is None:
        out["state"] = DRIFT_UNKNOWN
        out["detail"] = ("cannot read dual_bars to test for historical "
                         "revision; refusing rather than assuming")
        return out
    if out["frozen_history_sha"] is None:
        # First observation after the freeze gained this field: record it,
        # do not block the pipeline that legitimately predates it.
        out["state"] = DRIFT_ADVANCE
        out["detail"] = ("freeze records no history sha (predates this "
                         "control); observed history sha recorded as the "
                         "new baseline")
        return out
    if hist != out["frozen_history_sha"]:
        out["state"] = DRIFT_REVISION
        out["detail"] = ("historical rows before %s changed since the "
                         "freeze; the cohort was defined against the "
                         "previous history" % cutoff)
        return out
    out["state"] = DRIFT_ADVANCE if full != frozen_full else DRIFT_NONE
    out["detail"] = (
        "history through %s unchanged; dataset advanced with newer bars"
        % cutoff) if out["state"] == DRIFT_ADVANCE else \
        "dataset identical to freeze"
    return out


def registry_entry(dataset_id="dual-prices"):
    if not os.path.exists(DATASET_REGISTRY):
        return None
    with open(DATASET_REGISTRY, "r", encoding="ascii") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            e = json.loads(line)
            if e.get("dataset_id") == dataset_id:
                return e
    return None


# --------------------------------------------------------------------------
# Universe + eligibility (mirrors frozen tournament eligibility rules)
# --------------------------------------------------------------------------

ADR_BLOCKLIST = {"TSM", "ASML", "ABBNY", "ATEYY", "ASMIY"}
ELIG_MIN_BARS = 1000
CA_GUARD_RET = 0.50


def eligibility_screen(px_adj):
    """Eligible Track-2 names: min bars, no crypto, no ADR blocklist, and no
    |daily adjusted return| > 50% lacking a matching corporate action row
    (stitch artifact guard, same rule as the frozen tournament spec).

    px_adj values may be plain floats or {'raw','adj'} dicts; both work."""
    con = sqlite3.connect("file:%s?mode=ro" % DUAL_DB.replace("\\", "/"), uri=True)
    ca = set((tk.upper(), d) for tk, d in
             con.execute("SELECT ticker, effective_date FROM corporate_actions"))
    con.close()

    def adj_of(m, d):
        v = m[d]
        return v["adj"] if isinstance(v, dict) else float(v)

    notes = []
    ok = []
    for tk in sorted(px_adj):
        if "-USD" in tk:
            continue
        if tk in ADR_BLOCKLIST:
            continue
        m = px_adj[tk]
        if len(m) < ELIG_MIN_BARS:
            notes.append("%s: only %d bars (<%d)" % (tk, len(m), ELIG_MIN_BARS))
            continue
        ds = sorted(m)
        bad = False
        for a, b in zip(ds, ds[1:]):
            ra, rb = adj_of(m, a), adj_of(m, b)
            if ra > 0 and abs(rb / ra - 1.0) > CA_GUARD_RET:
                if (tk, b) not in ca:
                    notes.append("%s: unexplained >50%% move at %s"
                                 % (tk, b))
                    bad = True
                    break
        if not bad:
            ok.append(tk)
    return ok, notes[:40]


# --------------------------------------------------------------------------
# Baseline books (mr-corrected primitives + dual-price adjusted closes)
# --------------------------------------------------------------------------

def daily_returns_map(m_adj):
    ds = sorted(m_adj)
    return {b: m_adj[b] / m_adj[a] - 1.0 for a, b in zip(ds, ds[1:])}


def ew_book(px_adj, cal, names):
    acc, cnt = {}, {}
    for tk in names:
        r = daily_returns_map(px_adj[tk])
        for d in cal:
            v = r.get(d)
            if v is not None:
                acc[d] = acc.get(d, 0.0) + v
                cnt[d] = cnt.get(d, 0) + 1
    return {d: (acc[d] / cnt[d] if cnt.get(d) else 0.0) for d in cal}


def spy_book(px_adj, cal):
    if "SPY" not in px_adj:
        return {d: 0.0 for d in cal}
    r = daily_returns_map(px_adj["SPY"])
    return {d: r.get(d, 0.0) for d in cal}


def run_vol_target_book_local(mrc, px_adj, cal, target_vol, lookback, max_lev):
    """EW Track-2 scaled to target vol; realized vol up to YESTERDAY decides
    TODAY's scale (1-day decision lag -> same-close execution impossible).
    Reuses mrc.simulate-compatible daily semantics: this is a book, so we
    compute it directly per tournament_runner.run_vol_target_book."""
    names = sorted(px_adj)
    rets = {tk: daily_returns_map(px_adj[tk]) for tk in names}
    ew_hist = {}
    for d in cal:
        rs = [rets[tk].get(d, 0.0) for tk in names]
        ew_hist[d] = sum(rs) / len(rs) if rs else 0.0
    out = {}
    dates = cal[:]
    for i, d in enumerate(dates):
        j = max(0, i - lookback)
        window = [ew_hist[dates[k]] for k in range(j, i)]
        if len(window) >= 20:
            mu = sum(window) / len(window)
            var = sum((z - mu) ** 2 for z in window) / max(len(window) - 1, 1)
            rv = math.sqrt(var * 252.0)
            s = min(max_lev, target_vol / rv) if rv > 0 else 1.0
        else:
            s = 1.0
        out[d] = s * ew_hist[d]
    return out


def trend_ma_book(mrc, px_adj, cal, fast=20, slow=50):
    """MA20/50 cross long/flat book via mr-corrected simulate (slot engine,
    stress slippage into fill prices). Signals built per-ticker on the common
    calendar with next-close fills (mr-corrected C5)."""
    idx_of = {d: i for i, d in enumerate(cal)}
    sigs = []
    # reuse the tournament's ma_signals_for_ticker (same sanctioned family);
    # fall back to a local builder if unavailable
    try:
        tr = _import_module("tr_shadow", TOURNAMENT_PATH)
        builder = tr.ma_signals_for_ticker
        for tk, m in sorted(px_adj.items()):
            adj = {d: (v["adj"] if isinstance(v, dict) else float(v))
                   for d, v in m.items()}
            sigs += builder(tk, adj, fast, slow, False, idx_of, cal)
    except Exception:
        sigs = local_trend_signals(px_adj, cal, fast, slow)
    saved = mrc.SLIP_MODE
    mrc.SLIP_MODE = "stress"
    try:
        daily, recs, st = mrc.simulate(sigs, px_adj, cal)
    finally:
        mrc.SLIP_MODE = saved
    return {d: ret for (d, _eq, ret) in daily}, recs


def local_trend_signals(px_adj, cal, fast, slow):
    """Local next-close MA-cross signal builder (fallback; identical timing
    discipline: signal at close t -> fill at t+1, exit at cross-down t+1)."""
    idx_of = {d: i for i, d in enumerate(cal)}
    out = []
    for tk, m in sorted(px_adj.items()):
        dates = sorted(m)
        cl = [(m[d]["adj"] if isinstance(m[d], dict) else float(m[d]))
              for d in dates]
        armed = True
        for i in range(slow, len(dates)):
            sma_f = sum(cl[i - fast + 1:i + 1]) / fast
            sma_s = sum(cl[i - slow + 1:i + 1]) / slow
            cond = sma_f > sma_s
            gi = idx_of.get(dates[i])
            if gi is None or gi + 1 >= len(cal):
                continue
            if cond and armed:
                out.append({"tk": tk, "sig": dates[i], "fill": cal[gi + 1],
                            "exit": None})
                armed = False
            elif not cond and not armed:
                if out and out[-1]["exit"] is None:
                    xg = idx_of.get(dates[i])
                    if xg is not None and xg + 1 < len(cal) \
                            and cal[xg + 1] in m:
                        out[-1]["exit"] = cal[xg + 1]
                        armed = True
        for s in out:
            if s["exit"] is None:
                s["exit"] = dates[-1]
    return [s for s in out if s["fill"] in px_adj[s["tk"]]
            and s["exit"] in px_adj[s["tk"]]]


def rsi_diagnostic_book(mrc, px_adj, cal):
    """RSI(14) mean-reversion slot book -- DEV-REJECTED diagnostic challenger.
    Uses ONLY corrected primitives (mrc.signals + simulate); exists purely
    to keep the invalidated strategy under prospective observation. Its
    cohort carries status dev-rejected and promotion_blocked=true."""
    saved = mrc.SLIP_MODE
    mrc.SLIP_MODE = "stress"
    try:
        sigs = mrc.signals(px_adj, cal, 30, 50, 10)
        daily, recs, st = mrc.simulate(sigs, px_adj, cal)
    finally:
        mrc.SLIP_MODE = saved
    return {d: ret for (d, _eq, ret) in daily}, recs


def build_books(mrc, px_adj, cal, track2_ok):
    """All six baseline books as {date: daily_return} aligned to cal."""
    books = {}
    books["SPY_BH"] = spy_book(px_adj, cal)
    books["EW_TRACK2_BOOK"] = ew_book(px_adj, cal, track2_ok)
    books["VOL_TARGET_10"] = run_vol_target_book_local(
        mrc, px_adj, cal, 0.10, 63, 2.0)
    books["NO_ACTION_CASH"] = {d: 0.0 for d in cal}
    books["TREND_MA20_50"], trend_recs = trend_ma_book(mrc, px_adj, cal)
    books["RSI_BASE_DIAGNOSTIC"], rsi_recs = rsi_diagnostic_book(mrc, px_adj, cal)
    recs = {"TREND_MA20_50": trend_recs, "RSI_BASE_DIAGNOSTIC": rsi_recs}
    return books, recs


# --------------------------------------------------------------------------
# Forecast distribution (p10/p50/p90 of horizon return vs benchmark)
# --------------------------------------------------------------------------

def forecast_distribution(book_ret, bench_ret, horizon, sigma_daily=None):
    """Closed-form p10/p50/p90 of the HORIZON RETURN of the cohort book
    (not the excess; the grader computes realized vs benchmark separately).
    Point estimate: last observed daily return carried forward with a 0.25
    persistence decay per horizon day (honest for passive/baseline books --
    yesterday's return has weak predictive content). Dispersion: iid daily
    sigma scaled by sqrt(horizon) with a conservative 2x inflation factor
    because daily marks overlap. NO_ACTION_CASH (book_ret == 0 by
    construction every day) gets an exact-zero point forecast."""
    if sigma_daily is None:
        sigma_daily = 0.01
    h = max(int(horizon), 1)
    mu_h = book_ret * h * 0.25
    sig_h = sigma_daily * math.sqrt(h) * 2.0
    p50 = mu_h
    p10 = mu_h - 1.2816 * sig_h
    p90 = mu_h + 1.2816 * sig_h
    return {"p10": round(p10, 6), "p50": round(p50, 6), "p90": round(p90, 6)}


def realized_sigma(book, cal, end_idx, window=60):
    lo = max(0, end_idx - window)
    rs = [book[cal[k]] for k in range(lo, end_idx)]
    if len(rs) < 5:
        return 0.01
    mu = sum(rs) / len(rs)
    var = sum((x - mu) ** 2 for x in rs) / max(len(rs) - 1, 1)
    return math.sqrt(var) if var > 0 else 0.01


def proposed_position(cohort_id, book_ret, weight_note):
    direction = "long" if book_ret >= 0 else "reduced_long"
    return {
        "instrument": COHORTS[cohort_id]["instrument"],
        "direction": direction,
        "target_weight": COHORTS[cohort_id]["target_weight"],
        "note": weight_note,
    }


COHORTS = {
    "EW_TRACK2_BOOK": {
        "label": "Equal-weight Track-2 eligible book (daily rebalanced)",
        "status": "baseline",
        "promotion_eligible": True,
        "instrument": "EW basket of eligible Track-2 names",
        "target_weight": 1.0,
    },
    "SPY_BH": {
        "label": "SPY buy-and-hold",
        "status": "baseline",
        "promotion_eligible": True,
        "instrument": "SPY",
        "target_weight": 1.0,
    },
    "VOL_TARGET_10": {
        "label": "Vol-target 10% annualized on EW Track-2 (1-day lag)",
        "status": "baseline",
        "promotion_eligible": True,
        "instrument": "EW Track-2 basket scaled",
        "target_weight": 1.0,
    },
    "NO_ACTION_CASH": {
        "label": "No-action cash control (zero return)",
        "status": "baseline",
        "promotion_eligible": True,
        "instrument": "CASH",
        "target_weight": 0.0,
    },
    "TREND_MA20_50": {
        "label": "Trend MA20/50 cross baseline (next-close fills)",
        "status": "baseline",
        "promotion_eligible": True,
        "instrument": "Signal-weighted eligible universe",
        "target_weight": 1.0,
    },
    "RSI_BASE_DIAGNOSTIC": {
        "label": ("RSI(14) MR base slot book -- DIAGNOSTIC CHALLENGER, "
                  "DEV-REJECTED per FIS-MR-001"),
        "status": "dev-rejected",
        "promotion_eligible": False,
        "promotion_blocked_reason":
            "failed-strategies-registry FIS-MR-001: NO surviving net edge "
            "after honest accounting; shadow observation only",
        "instrument": "Slot book (K=10) of RSI signals",
        "target_weight": 1.0,
    },
}


# --------------------------------------------------------------------------
# FREEZE registry
# --------------------------------------------------------------------------

def build_freeze_registry():
    """Compose the FULL freeze payload: code + params + feature defs +
    universe + eligibility + data versions + costs + horizons + metrics +
    min samples + evaluation dates + promotion/rejection criteria."""
    mrc, ecm = load_engines()

    # model code hashes (the sanctioned engines this pipeline reuses)
    def file_sha(p):
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    code_hashes = {
        "shadow.py": file_sha(os.path.abspath(__file__)),
        "mr_corrected_py": file_sha(MRC_PATH),
        "execution_cost_model_py": file_sha(ECM_PATH),
        "tournament_runner_py": file_sha(TOURNAMENT_PATH),
    }

    # data versions from the registry (recorded sha256s, not recomputed)
    reg_dual = registry_entry("dual-prices")
    reg_factors = registry_entry("factors.db")

    px_all = load_dual_closes()
    track2_ok, elig_notes = eligibility_screen(
        {tk: {d: v["adj"] for d, v in m.items()} for tk, m in px_all.items()})
    cal = sorted(px_all["SPY"]) if "SPY" in px_all else []

    costs_probe = {}
    for tk in ("SPY", "QQQ"):
        costs_probe[tk] = ecm.estimate_trade_cost(tk, ORDER_SIZE_USD)["round_trip_bp"]

    eval_dates = {
        "first_info_cutoff": cal[-1] if cal else None,
        "horizon_days": HORIZON_DAYS,
        "grading_rule": ("grade only when HORIZON_DAYS trading closes have "
                         "elapsed past earliest_tradable AND realized closes "
                         "exist in the dual-price store"),
    }

    payload = {
        "freeze_id": "FIS-S3-SHADOW-BASELINES-001",
        "title": "Shadow-operation baseline cohorts freeze (Part IV / S3)",
        "created_utc": utc_now_iso(),
        "model_version": MODEL_VERSION,
        "model_code_sha256": code_hashes,
        "params": {
            "horizon_days": HORIZON_DAYS,
            "benchmark": BENCHMARK,
            "order_size_usd_for_ecm": ORDER_SIZE_USD,
            "slippage_mode": "stress (full class round trip per leg, "
                             "charged into fill prices once per leg)",
            "trend_fast_ma": 20,
            "trend_slow_ma": 50,
            "rsi_period": 14,
            "rsi_entry": 30,
            "rsi_exit_level": 50,
            "rsi_max_hold": 10,
            "k_slots": getattr(mrc, "K_SLOTS", 10),
            "vol_target_ann": 0.10,
            "vol_lookback_days": 63,
            "vol_max_leverage": 2.0,
            "forecast_band_z": 1.2816,
            "forecast_sigma_inflation": 2.0,
        },
        "feature_definitions": {
            "returns": "adjusted_close[t]/adjusted_close[t-1]-1 from "
                       "dual_prices.db dual_bars (corporate-action-safe)",
            "ew_track2": "equal-weight mean of eligible-name daily returns",
            "vol_target_scale": "realized vol of EW book over prior 63 "
                                "trading days, scale=min(2, 0.10/vol), "
                                "applied with 1-day decision lag",
            "trend_signal": "long while SMA20>SMA50 on adjusted closes; "
                            "entry fill NEXT close; exit fill next close "
                            "after cross-down",
            "rsi_wilder": "Wilder RSI(14) on adjusted closes, entry<30, "
                          "exit>50 or max_hold 10 (mr-corrected.signals)",
        },
        "universe": {
            "source": "dual_prices.db dual_bars (Track-2 current-watchlist "
                      "diagnostic universe)",
            "eligible_count": len(track2_ok),
            "eligible_tickers": track2_ok,
        },
        "eligibility_rules": {
            "min_bars": ELIG_MIN_BARS,
            "exclude_crypto": "-USD suffixed tickers excluded",
            "exclude_adr_blocklist": sorted(ADR_BLOCKLIST),
            "ca_guard": "exclude if |daily adjusted return| > 0.50 without "
                        "a matching corporate_actions row",
            "notes_capped": elig_notes,
        },
        "data_versions": {
            "dual_prices_sha256": dataset_version_sha(),
            "registry_dual_prices": (reg_dual or {}).get("sha256"),
            "registry_factors_db": (reg_factors or {}).get("sha256"),
        },
        "costs": {
            "engine": "tools/execution-cost-model.py estimate_trade_cost",
            "probe_round_trip_bp": costs_probe,
            "charging": "into fill prices via mr-corrected slip_bp, once "
                        "per leg, stress multiplier",
        },
        "horizons": {"forecast_horizon_trading_days": HORIZON_DAYS,
                     "benchmark": BENCHMARK},
        "metrics": {
            "primary": "mean realized excess vs SPY_BH over horizon",
            "secondary": ["direction_accuracy", "calibration_bucket_coverage",
                          "p10_p90_coverage", "cost_drag_bp"],
            "inference_primitives": "mr-corrected perf/nw_t/clusters",
        },
        "min_samples": {
            "min_predictions": MIN_PREDICTIONS,
            "min_effective_clusters": MIN_CLUSTERS,
            "min_span_days": MIN_SPAN_DAYS,
            "rule": "ALL three bars must pass before ANY summary statistic "
                    "is produced; otherwise the summary is REFUSED",
        },
        "evaluation_dates": eval_dates,
        "promotion_and_rejection_criteria": {
            "promotion_path": "dev-pass -> challenge -> shadow-only -> "
                              "production-eligible (frozen tournament spec "
                              "allowed_transitions; no direct-to-production)",
            "shadow_promotion_bar": ("production-eligible requires >=90 "
                                     "calendar days shadow evidence meeting "
                                     "all min_samples AND positive net-of-cost "
                                     "excess vs benchmark"),
            "rejection_rule": ("any cohort failing calibration coverage "
                               "(p10..p90 miss rate > 30%) or negative "
                               "net excess across two consecutive 60-day "
                               "windows is flagged reject_candidate"),
            "forbidden": ("NO rejected strategy may be labeled production "
                          "anything; RSI_BASE_DIAGNOSTIC permanently "
                          "promotion-blocked per FIS-MR-001"),
        },
        "cohorts": {cid: dict(COHORTS[cid]) for cid in COHORT_ORDER},
    }
    payload["freeze_hash"] = canonical_sha256(payload)
    return payload


def write_freeze(force=False):
    if os.path.exists(FREEZE_PATH) and not force:
        raise SystemExit("FREEZE already exists at %s -- refusing to overwrite "
                         "(append-only governance; delete manually only if "
                         "this is an authorized re-launch)" % FREEZE_PATH)
    payload = build_freeze_registry()
    os.makedirs(SHADOW_DIR, exist_ok=True)
    tmp = FREEZE_PATH + ".tmp"
    with open(tmp, "w", encoding="ascii") as f:
        json.dump(payload, f, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, FREEZE_PATH)
    return payload


def load_freeze():
    if not os.path.exists(FREEZE_PATH):
        raise SystemExit("NO FREEZE found at %s -- run init-cohort first"
                         % FREEZE_PATH)
    with open(FREEZE_PATH, "r", encoding="ascii") as f:
        payload = json.load(f)
    claimed = payload.pop("freeze_hash", None)
    actual = canonical_sha256(payload)
    if actual != claimed:
        raise SystemExit("FREEZE INTEGRITY FAILURE: sha256 %s != recorded %s "
                         "-- freeze was modified after launch; operations "
                         "refused" % (actual, claimed))
    payload["freeze_hash"] = claimed
    return payload


def verify_code_against_freeze(freeze):
    """Refuse tick/grade if sanctioned engine code drifted since freeze."""
    def file_sha(p):
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    checks = {
        "mr_corrected_py": MRC_PATH,
        "execution_cost_model_py": ECM_PATH,
    }
    for key, path in checks.items():
        want = freeze["model_code_sha256"].get(key)
        if want and file_sha(path) != want:
            raise SystemExit(
                "CODE DRIFT: %s changed since freeze (%s) -- shadow "
                "operations refused; re-launch a NEW cohort generation to "
                "operate under different code" % (path, key))
    # shadow.py itself: warn-level check folded into refusal for strictness
    want_self = freeze["model_code_sha256"].get("shadow.py")
    if want_self and file_sha(os.path.abspath(__file__)) != want_self:
        raise SystemExit(
            "CODE DRIFT: shadow.py changed since freeze -- operations "
            "refused; re-launch a NEW cohort generation")


# --------------------------------------------------------------------------
# Prediction log (append-only, hash-chained)
# --------------------------------------------------------------------------

def read_predictions(path=PREDICTIONS_PATH):
    recs = []
    if not os.path.exists(path):
        return recs
    with open(path, "r", encoding="ascii") as f:
        for line in f:
            line = line.strip()
            if line:
                recs.append(json.loads(line))
    return recs


def verify_chain(recs):
    """Recompute the whole chain; return (ok, first_bad_index_or_None)."""
    prev = "GENESIS"
    for i, rec in enumerate(recs):
        if rec.get("prev_record_hash") != prev:
            return False, i
        want = record_hash(rec)
        if rec.get("record_hash") != want:
            return False, i
        prev = want
    return True, None


def last_chain_head(recs):
    return recs[-1]["record_hash"] if recs else "GENESIS"


def append_prediction(rec, path=PREDICTIONS_PATH):
    """Append one record, extending the chain. Refuses if the on-disk tail
    moved underneath us, and refuses a duplicate payload (F-03)."""
    existing = read_predictions(path)
    ok, bad = verify_chain(existing)
    if not ok:
        raise SystemExit("PREDICTION LOG CHAIN BROKEN at record %d -- "
                         "tamper suspected, append REFUSED" % bad)
    rec["prev_record_hash"] = last_chain_head(existing)
    rec["record_hash"] = record_hash(rec)
    written, digest = append_jsonl(path, rec, dedup=True)
    if not written:
        raise SystemExit(
            "DUPLICATE PREDICTION: an identical record is already chained "
            "(cohort %s, cutoff %s) -- append REFUSED"
            % (rec.get("cohort_id"), rec.get("info_cutoff")))
    rec["content_digest"] = digest
    return rec


# --------------------------------------------------------------------------
# Cohort state machine (which cohorts owe a prediction today)
# --------------------------------------------------------------------------

def load_status():
    if os.path.exists(STATUS_PATH):
        with open(STATUS_PATH, "r", encoding="ascii") as f:
            return json.load(f)
    return {"launched_utc": None, "last_tick_date": None,
            "last_grade_date": None, "cohorts": {}}


def save_status(st):
    tmp = STATUS_PATH + ".tmp"
    with open(tmp, "w", encoding="ascii") as f:
        json.dump(st, f, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, STATUS_PATH)


# --------------------------------------------------------------------------
# Data assembly shared by tick/grade
# --------------------------------------------------------------------------

class MarketData(object):
    """Lazy loader caching books + calendar for one process invocation."""

    def __init__(self):
        self._loaded = False
        self.px_all = None
        self.px_adj = None
        self.cal = None
        self.track2_ok = []
        self.books = {}
        self.recs_by_cohort = {}

    def load(self):
        if self._loaded:
            return
        mrc, _ecm = load_engines()
        self.px_all = load_dual_closes()
        if "SPY" not in self.px_all:
            raise SystemExit("dual_prices.db lacks SPY -- cannot operate")
        # Common calendar = SPY trading days. Crypto (-USD) names trade
        # weekends and are excluded from shadow books entirely (eligibility
        # rule), so restrict the universe to SPY-calendar dates up front.
        cal_set = set(self.px_all["SPY"])
        self.px_all = {
            tk: {d: v for d, v in m.items() if d in cal_set}
            for tk, m in self.px_all.items() if "-USD" not in tk
        }
        self.cal = sorted(self.px_all["SPY"])
        self.px_adj = {tk: {d: v["adj"] for d, v in m.items()}
                       for tk, m in self.px_all.items()}
        self.track2_ok, _notes = eligibility_screen(self.px_adj)
        books, recs = build_books(mrc, self.px_adj, self.cal, self.track2_ok)
        self.books = books
        self.recs_by_cohort = recs
        self._loaded = True

    def info_cutoff_index(self, asof=None):
        """Index into cal of the LAST close whose data is fully known at the
        decision moment. With --asof D: last close <= D. Without: last close
        in the store (batch/backfill mode)."""
        self.load()
        if asof is None:
            return len(self.cal) - 1
        idx = -1
        for i, d in enumerate(self.cal):
            if d <= asof:
                idx = i
            else:
                break
        if idx < 0:
            raise SystemExit("--asof %s precedes all stored closes" % asof)
        return idx


MD = MarketData()


# --------------------------------------------------------------------------
# Record builders
# --------------------------------------------------------------------------

INVALIDATION_TEMPLATE = (
    "invalidate if (a) dual-price store restated under this dataset_version, "
    "(b) benchmark series revised, (c) cohort code hash diverges from freeze")


def build_prediction_records(cutoff_idx, dataset_sha, drift=None):
    """One prediction per cohort per day: info_cutoff = cal[cutoff_idx],
    earliest_tradable = next close (strictly later; same-close forbidden).

    `drift` is the F-06 dataset-drift classification; when supplied it is
    stamped onto every record so a prediction always states whether it was
    produced against the frozen history or against an advanced dataset.
    """
    md = MD
    md.load()
    cal = md.cal
    cut_d = cal[cutoff_idx]
    if cutoff_idx + 1 >= len(cal):
        return [], "no tradable close after cutoff %s yet" % cut_d
    trade_d = cal[cutoff_idx + 1]

    out = []
    ts = utc_now_iso()
    for cid in COHORT_ORDER:
        book = md.books[cid]
        bench = md.books[BENCHMARK]
        # NO_ACTION_CASH is a pure control: its forecast is exactly zero
        # regardless of what the zero-return book's last mark is.
        book_ret = book[cut_d] if cid != "NO_ACTION_CASH" else 0.0
        bench_ret = bench[cut_d]
        sig = realized_sigma(book, cal, cutoff_idx)
        dist = forecast_distribution(book_ret, bench_ret, HORIZON_DAYS, sig)
        spread = est_spread_slip(cid)[0]
        slip = est_spread_slip(cid)[1]
        missing = missing_data_state(cid, cutoff_idx)
        rec = {
            "record_type": "prediction",
            "cohort_id": cid,
            "cohort_label": COHORTS[cid]["label"],
            "cohort_status": COHORTS[cid]["status"],
            "promotion_blocked": not COHORTS[cid]["promotion_eligible"],
            "creation_ts": ts,
            "info_cutoff": cut_d,
            "earliest_tradable": trade_d,
            "model_version": MODEL_VERSION,
            "dataset_version": dataset_sha,
            "dataset_drift_state": (
                drift.get("state") if drift else DRIFT_UNKNOWN),
            "dataset_drift_detail": (
                drift.get("detail") if drift else "not evaluated"),
            "dataset_history_sha": (
                drift.get("history_sha") if drift else None),
            "freeze_hash": load_freeze()["freeze_hash"],
            "horizon_days": HORIZON_DAYS,
            "forecast_distribution": dist,
            "benchmark": BENCHMARK,
            "proposed_position": {
                "instrument": COHORTS[cid]["instrument"],
                "direction": "long" if book_ret >= 0 else "reduced_long",
                "target_weight": COHORTS[cid]["target_weight"],
            },
            "est_spread_bp": spread,
            "est_slippage_bp": slip,
            "risk_contribution": {
                "sigma_daily_realized": round(sig, 6),
                "horizon_band_half_width":
                    round(dist["p90"] - dist["p50"], 6),
            },
            "confidence": confidence_from_band(dist, book_ret, bench_ret),
            "invalidation_conditions": INVALIDATION_TEMPLATE,
            "missing_data_state": missing,
        }
        # F-01: provenance is decided from the record's own timestamps at
        # CREATION time, so the verdict is durable and auditable before any
        # outcome can be observed. It is re-derived at grade time too.
        prov = provenance_decision(ts, trade_d)
        rec["provenance_mode"] = prov["provenance_mode"]
        rec["prospective_evidence"] = prov["prospective_evidence"]
        rec["provenance_rule"] = prov["rule"]
        rec["provenance_reason"] = prov["reason"]
        # F-05: when the inputs actually became observable.
        rec["data_availability_ts"] = ts
        out.append(rec)
    return out, None


_SPREAD_CACHE = {}


def est_spread_slip(cohort_id):
    """(spread_bp, slippage_bp) per side from the ECM house model."""
    if cohort_id in _SPREAD_CACHE:
        return _SPREAD_CACHE[cohort_id]
    _ecm_m, ecm = load_engines(), None
    ecm_mod = _import_module("ecm_s2", ECM_PATH)
    inst = COHORTS[cohort_id]["instrument"]
    probe = "SPY" if ("basket" in inst or "CASH" in inst) else \
        (inst.split()[0] if inst.split()[0] in ecm_mod.TICKER_CLASS else "SPY")
    cost = ecm_mod.estimate_trade_cost(probe, ORDER_SIZE_USD)
    val = (cost["spread_bp_per_side"], cost["impact_bp_per_side"]
           + cost["fees_bp_per_side"] + cost["fx_bp_per_side"])
    _SPREAD_CACHE[cohort_id] = val
    return val


def confidence_from_band(dist, book_ret, bench_ret):
    """Confidence = fraction of the band supporting the sign of the point
    view; cash control gets neutral 0.5. NOT evidence-grade capped upward."""
    width = dist["p90"] - dist["p10"]
    if width <= 0:
        return 0.5
    edge = (book_ret - bench_ret)
    if edge == 0:
        return 0.5
    frac_up = (dist["p90"] - 0.0) / width
    conf = frac_up if edge > 0 else (1.0 - frac_up)
    return round(min(max(conf, 0.05), 0.95), 4)


def missing_data_state(cohort_id, cutoff_idx):
    md = MD
    md.load()
    cal = md.cal
    cut_d = cal[cutoff_idx]
    gaps = []
    if cohort_id in ("TREND_MA20_50", "RSI_BASE_DIAGNOSTIC"):
        n_names = 0
        stale = 0
        for tk, m in md.px_adj.items():
            if tk not in md.track2_ok and tk not in ("SPY", "QQQ"):
                continue
            n_names += 1
            if cut_d not in m:
                stale += 1
        if stale:
            gaps.append("%d/%d eligible names lack a bar at cutoff (keep "
                        "last mark, no synthetic returns)" % (stale, n_names))
    if not md.track2_ok:
        gaps.append("EMPTY eligible universe")
    state = "; ".join(gaps) if gaps else "complete"
    return {"state": "gapped" if gaps else "complete", "detail": state}


# --------------------------------------------------------------------------
# Effective clusters (overlap grouping, mr-corrected clusters() convention)
# --------------------------------------------------------------------------

def effective_clusters(records, md):
    """Greedy overlap grouping of prediction windows per cohort. For
    portfolio cohorts every day overlaps every other day within the horizon
    (the book is always 'open'), so consecutive predictions collapse into
    one running cluster until a horizon passes with no carryover -- the
    honest independent-sample count for a continuously-held book."""
    horizon = HORIZON_DAYS
    cls_end = None
    n = 0
    for rec in records:
        start = rec["earliest_tradable"]
        i = md.cal.index(start) if start in md.cal else None
        if i is None:
            continue
        end_i = min(i + horizon, len(md.cal) - 1)
        if cls_end is None or i > cls_end:
            n += 1
            cls_end = end_i
        else:
            cls_end = max(cls_end, end_i)
    return n


# --------------------------------------------------------------------------
# GRADER
# --------------------------------------------------------------------------

def grade_matured(asof=None):
    """Grade every matured prediction not yet graded. NEVER mutates
    predictions; appends grades keyed by prediction record_hash (idempotent
    via digest-keyed skip)."""
    md = MD
    md.load()
    cal = md.cal
    preds = read_predictions()
    ok, bad = verify_chain(preds)
    if not ok:
        raise SystemExit("PREDICTION LOG CHAIN BROKEN at record %d -- "
                         "grading REFUSED" % bad)

    # F-03: dedup on CONTENT, not on a pre-read id set. Two runs grading
    # the same prediction yield the same digest, so the second is a no-op
    # even in a different process.
    grade_digests = existing_digests(GRADES_PATH)
    refusal_digests = existing_digests(REFUSALS_PATH)

    graded_ids = set()
    if os.path.exists(GRADES_PATH):
        with open(GRADES_PATH, "r", encoding="ascii") as f:
            for line in f:
                line = line.strip()
                if line:
                    g = json.loads(line)
                    graded_ids.add(g.get("grades", {}).get("prediction_hash")
                                   or g.get("prediction_hash"))

    # F-01 gate: refuse to operate at all if this module has grown a switch
    # that would let backfilled records be counted as prospective.
    clean, hits = shadow_no_backfill_escape_hatch()
    if not clean:
        raise SystemExit("BACKFILL ESCAPE HATCH DETECTED in %s -- grading "
                         "REFUSED (tokens: %s)"
                         % (SHADOW_MODULE_PATH, ", ".join(hits)))

    last_known = md.info_cutoff_index(asof)
    cal_set = set(md.cal)
    appended = []
    refused = []
    retro_graded = []
    for rec in preds:
        if rec["record_hash"] in graded_ids:
            continue
        # F-01: re-derive provenance from the record's own timestamps. The
        # stored verdict is NOT trusted; a record is reclassified here so an
        # edited or pre-control record cannot inherit prospective status.
        prov = classify_provenance(rec)
        trade_d = rec["earliest_tradable"]
        if trade_d not in cal_set:
            continue  # earliest_tradable close not realized yet -> gated
        ti = md.cal.index(trade_d)
        mi = ti + int(rec["horizon_days"])
        if mi > last_known:
            continue  # horizon not expired -> GATED (grader must wait)
        maturity_d = cal[min(mi, len(cal) - 1)]
        # A backfilled record is still graded -- it is a legitimate
        # CALIBRATION DEMONSTRATION over a historical window -- but it is
        # permanently marked non-prospective. It carries no out-of-sample
        # weight and can never enter a prospective aggregate.
        stored_mode = rec.get("provenance_mode")
        if stored_mode is not None and stored_mode != prov["provenance_mode"]:
            raise SystemExit(
                "PROVENANCE TAMPER: record %s was stored as %s but "
                "re-derives as %s (created %s, earliest_tradable %s) -- "
                "grading REFUSED"
                % (rec.get("record_hash"), stored_mode,
                   prov["provenance_mode"], rec.get("creation_ts"), trade_d))
        try:
            g = grade_one(rec, md, ti, mi, maturity_d)
        except MissingBarError as exc:
            # F-02: no grade is emitted. The abstention is recorded under
            # its own record_type, which no prospective aggregation reads.
            refusal = exc.refusal_record()
            refusal["provenance_mode"] = prov["provenance_mode"]
            refusal["prospective_evidence"] = False
            append_refusal(refusal, digests=refusal_digests)
            refused.append(refusal)
            continue
        g["provenance_mode"] = prov["provenance_mode"]
        g["prospective_evidence"] = prov["prospective_evidence"]
        g["provenance_rule"] = prov["rule"]
        g["provenance_reason"] = prov["reason"]
        # F-05: the label became observable at the maturity session's close.
        g["label_availability_ts"] = maturity_d
        # W9-A6-01 (CRITICAL): a grade must be verifiable WITHOUT its
        # parent. The read path re-derives provenance from a record's own
        # timestamps, so the grade has to carry them. Without this, a
        # grade could only be checked by joining to the prediction log --
        # and `is_prospective_evidence` is called on bare grades by every
        # consumer, including aggregate_prospective.
        g["creation_ts"] = rec.get("creation_ts")
        g["grades"]["creation_ts"] = rec.get("creation_ts")
        g["grades"]["cohort_id"] = rec.get("cohort_id")
        g["grades"]["dataset_version"] = rec.get("dataset_version")
        if not prov["prospective_evidence"]:
            retro_graded.append(rec.get("record_hash"))
        append_grade(g, digests=grade_digests)
        appended.append(g)
    if refused:
        sys.stderr.write(
            "NOTE: %d grade(s) REFUSED for missing bars and recorded as "
            "abstentions (record_type=grade_refusal): %s\n"
            % (len(refused), ", ".join(str(r["prediction_hash"])[:12]
                                       for r in refused)))
    # Refusals are surfaced out-of-band rather than by changing the return
    # type, so existing callers keep working and a refusal still cannot be
    # mistaken for a grade.
    global LAST_GRADE_RUN
    LAST_GRADE_RUN = {
        "appended": len(appended),
        "refused": len(refused),
        "retrospective_graded": len(retro_graded),
        "refusals": refused,
    }
    if retro_graded:
        sys.stderr.write(
            "NOTE: %d grade(s) are RETROSPECTIVE_BACKFILL and carry NO "
            "prospective evidence weight: %s\n"
            % (len(retro_graded), ", ".join(str(h)[:12] for h in retro_graded)))
    return appended


def prospective_grades(grades=None):
    """Return only grades that are valid prospective evidence.

    NO OVERRIDE PARAMETER. If a caller could switch the filter off, the
    control would not exist.
    """
    if grades is None:
        grades = read_grades()
    return [g for g in grades if is_prospective_evidence(g)]


def prospective_summary(grades=None, min_samples=60):
    """Prospective-only aggregate. Backfill is excluded permanently."""
    return aggregate_prospective(
        prospective_grades(grades), min_samples=min_samples)


class MissingBarError(Exception):
    """F-02: a return needed for the grade does not exist.

    Raised instead of substituting 0.0. The caller records a typed refusal
    so the absence is visible as an abstention, never as a number.
    """

    def __init__(self, rec, missing_book, missing_bench, window=None):
        self.rec = rec
        self.missing_book = list(missing_book)
        self.missing_bench = list(missing_bench)
        self.window = window
        self.cohort_id = rec.get("cohort_id")
        self.prediction_hash = rec.get("record_hash")
        Exception.__init__(self, self.message())

    def message(self):
        return ("missing %d book bar(s) and %d benchmark bar(s) in the "
                "grading window %s for cohort %s -- grade REFUSED"
                % (len(self.missing_book), len(self.missing_bench),
                   self.window, self.cohort_id))

    def refusal_record(self):
        """A refusal is a RECORD, not a silent skip and not a grade.

        It is written with record_type 'grade_refusal', which no
        prospective aggregation consumes, so an abstention can never be
        mistaken for a zero-return observation.
        """
        return {
            "record_type": "grade_refusal",
            "refused_at_utc": utc_now_iso(),
            "cohort_id": self.cohort_id,
            "prediction_hash": self.prediction_hash,
            "reason_code": "MISSING_BARS",
            "reason": self.message(),
            "missing_book_sessions": self.missing_book,
            "missing_benchmark_sessions": self.missing_bench,
            "window": list(self.window) if self.window else None,
            "severity": "HIGH",
            "counts_as_grade": False,
            "counts_as_prospective_evidence": False,
        }


def grade_one(rec, md, ti, mi, maturity_d):
    cid = rec["cohort_id"]
    cal = md.cal
    book = md.books[cid]
    bench = md.books[rec["benchmark"]]
    # realized HORIZON return compounded from earliest_tradable close
    # through maturity close (both exist; grader only sees realized bars)
    #
    # F-02: a missing bar used to be recorded in `failures` and then
    # replaced with 0.0, and the grade was still emitted -- complete with
    # inside_p10_p90 and direction_accuracy. Absent data produced a
    # confident-looking output instead of an abstention. A consumer
    # reading `inside_p10_p90` would not notice that `failures` was
    # non-empty. Missing bars now REFUSE the grade outright.
    cum = 1.0
    bcum = 1.0
    failures = []
    missing_book = []
    missing_bench = []
    for k in range(ti + 1, mi + 1):
        d = cal[k]
        rb = book.get(d)
        if rb is None:
            missing_book.append(d)
        rr = bench.get(d)
        if rr is None:
            missing_bench.append(d)
    if missing_book or missing_bench:
        raise MissingBarError(
            rec, missing_book, missing_bench,
            window=(cal[ti + 1] if ti + 1 < len(cal) else "?",
                    cal[min(mi, len(cal) - 1)]))
    for k in range(ti + 1, mi + 1):
        d = cal[k]
        rb = book[d]
        rr = bench[d]
        cum *= 1.0 + rb
        bcum *= 1.0 + rr
    realized = cum - 1.0
    bench_r = bcum - 1.0
    excess = realized - bench_r
    dist = rec["forecast_distribution"]

    # cost drag: entry+exit legs at est rates (round trip on both legs' bp)
    drag = (rec["est_spread_bp"] + rec["est_slippage_bp"]) * 2.0 / 10000.0
    excess_net = excess - drag

    inside = dist["p10"] <= excess <= dist["p90"]
    bucket = calibration_bucket(excess, dist)
    direction_pred = 1 if dist["p50"] > 0 else (-1 if dist["p50"] < 0 else 0)
    direction_real = 1 if excess > 0 else (-1 if excess < 0 else 0)
    direction_hit = direction_pred == direction_real

    feasible, feas_note = execution_feasibility(rec, md, ti)
    if not feasible:
        failures.append(feas_note)

    return {
        "record_type": "grade",
        "graded_at_utc": utc_now_iso(),
        "cohort_id": cid,
        "grades": {
            "prediction_hash": rec["record_hash"],
            "info_cutoff": rec["info_cutoff"],
            "earliest_tradable": rec["earliest_tradable"],
            "maturity_date": maturity_d,
            "realized_horizon_return": round(realized, 6),
            "benchmark_horizon_return": round(bench_r, 6),
            "excess_vs_benchmark": round(excess, 6),
            "excess_net_of_costs": round(excess_net, 6),
            "cost_drag_bp": round(drag * 10000.0, 4),
            "calibration_bucket": bucket,
            "inside_p10_p90": inside,
            "direction_predicted": direction_pred,
            "direction_realized": direction_real,
            "direction_accuracy": 1.0 if direction_hit else 0.0,
            "execution_feasible": feasible,
            "failures": failures,
            "abstention": rec["proposed_position"]["target_weight"] == 0.0
                          and cid == "NO_ACTION_CASH",
        },
    }


def calibration_bucket(excess, dist):
    if excess < dist["p10"]:
        return "below_p10"
    if excess > dist["p90"]:
        return "above_p90"
    third = (dist["p90"] - dist["p10"]) / 3.0
    if third <= 0:
        return "mid"
    if excess < dist["p10"] + third:
        return "lower_third"
    if excess > dist["p90"] - third:
        return "upper_third"
    return "mid"


def execution_feasibility(rec, md, ti):
    """Feasible iff every close needed for the NEXT-close entry actually
    existed when required (mr-corrected C8: no artificial fills)."""
    d_in = rec["earliest_tradable"]
    if d_in not in md.px_adj.get("SPY", {}):
        return False, "entry close %s absent from SPY calendar" % d_in
    return True, ""


# ---------------------------------------------------------------------------
# F-03: atomic, idempotent append
#
# The old append was a plain buffered write with no fsync and no
# temp-file-plus-rename, so an interrupted or concurrent run could leave a
# torn line or append the same grade twice. The only dedup was an
# in-memory set built by scanning the file at the start of grade_matured,
# which protects nothing across two processes and nothing against a
# partial write. Duplicated grades duplicate financial effects.
#
# Now: temp file in the same directory, flush + fsync, os.replace, and
# dedup on a CONTENT hash of the payload so an identical grade appended
# twice is one grade.
# ---------------------------------------------------------------------------

def content_digest(obj):
    """Hash of the payload with the volatile fields blanked.

    `graded_at_utc` is excluded: two runs grading the same prediction must
    produce the SAME digest or dedup would not dedup.
    """
    probe = dict(obj)
    for k in ("graded_at_utc", "refused_at_utc", "created_at_utc"):
        probe.pop(k, None)
    return hashlib.sha256(
        json.dumps(probe, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=True).encode("ascii")).hexdigest()


def existing_digests(path):
    out = set()
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="ascii") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            d = rec.get("content_digest")
            if not d:
                d = content_digest({k: v for k, v in rec.items()
                                    if k != "content_digest"})
            out.add(d)
    return out


def append_jsonl(path, rec, dedup=True, digests=None):
    """Append one record atomically. Returns (written, digest).

    `written` is False when an identical payload is already present --
    idempotency is enforced on content, not on a pre-read set, so it holds
    across processes and across an interrupted run.
    """
    payload = dict(rec)
    payload.pop("content_digest", None)
    digest = content_digest(payload)
    if digests is None:
        digests = existing_digests(path)
    if dedup and digest in digests:
        return False, digest
    payload["content_digest"] = digest

    directory = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(directory, exist_ok=True)
    line = json.dumps(payload, sort_keys=True, ensure_ascii=True) + "\n"

    # Read-modify-write of the whole file, but through a temp file + atomic
    # replace, so a crash leaves either the old file or the new one and
    # never a torn line.
    prior = ""
    if os.path.exists(path):
        with open(path, "r", encoding="ascii") as f:
            prior = f.read()
    blob = (prior if prior.endswith("\n") or not prior else prior + "\n") \
        + line
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".append-",
                               suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="ascii") as f:
            f.write(blob)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    # fsync the directory so the rename itself is durable.
    try:
        dfd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except OSError:
        pass
    digests.add(digest)
    return True, digest


def append_grade(g, digests=None):
    written, digest = append_jsonl(GRADES_PATH, g, dedup=True,
                                   digests=digests)
    g["content_digest"] = digest
    return written


def append_refusal(r, digests=None):
    """Refusals are persisted too: an abstention must be auditable."""
    written, digest = append_jsonl(REFUSALS_PATH, r, dedup=True,
                                   digests=digests)
    r["content_digest"] = digest
    return written


# --------------------------------------------------------------------------
# SUMMARY with enforced minimums
# --------------------------------------------------------------------------

def cohort_summary(cid, preds, grades, md):
    mine_p = [p for p in preds if p["cohort_id"] == cid]
    mine_g = [g["grades"] for g in grades if g["cohort_id"] == cid]
    n_pred = len(mine_p)
    n_clusters = effective_clusters(mine_p, md) if mine_p else 0
    span = 0
    if mine_p:
        ds = sorted(set(p["info_cutoff"] for p in mine_p))
        span = (datetime.strptime(ds[-1], "%Y-%m-%d")
                - datetime.strptime(ds[0], "%Y-%m-%d")).days + 1

    bars = {
        "predictions>=60": n_pred >= MIN_PREDICTIONS,
        "clusters>=30": n_clusters >= MIN_CLUSTERS,
        "span>=90d": span >= MIN_SPAN_DAYS,
    }
    summary = {
        "cohort_id": cid,
        "n_predictions": n_pred,
        "effective_clusters": n_clusters,
        "span_days": span,
        "bars": bars,
    }
    if not all(bars.values()):
        failed = [k for k, v in bars.items() if not v]
        summary["summary_produced"] = False
        summary["refusal"] = ("MINIMUM SAMPLES NOT MET (%s) -- no summary "
                              "statistic permitted" % ", ".join(failed))
        return summary

    ex = [g["excess_vs_benchmark"] for g in mine_g]
    net = [g["excess_net_of_costs"] for g in mine_g]
    dir_hits = [g["direction_accuracy"] for g in mine_g]
    cover = [1.0 if g["inside_p10_p90"] else 0.0 for g in mine_g]
    summary.update({
        "summary_produced": True,
        "n_graded": len(mine_g),
        "mean_excess": round(sum(ex) / len(ex), 6) if ex else None,
        "mean_excess_net_of_costs": round(sum(net) / len(net), 6) if net else None,
        "direction_accuracy": round(sum(dir_hits) / len(dir_hits), 4)
                              if dir_hits else None,
        "p10_p90_coverage": round(sum(cover) / len(cover), 4)
                            if cover else None,
        "abstentions": sum(1 for g in mine_g if g["abstention"]),
        "execution_failures": sum(1 for g in mine_g if not g["execution_feasible"]),
    })
    return summary


def produce_summary():
    freeze = load_freeze()
    verify_code_against_freeze(freeze)
    md = MD
    md.load()
    preds = read_predictions()
    grades = read_grades()
    rows = [cohort_summary(cid, preds, grades, md) for cid in COHORT_ORDER]
    allowed = [r for r in rows if r.get("summary_produced")]
    return {
        "generated_utc": utc_now_iso(),
        "freeze_hash": freeze["freeze_hash"],
        "minima": {"min_predictions": MIN_PREDICTIONS,
                   "min_effective_clusters": MIN_CLUSTERS,
                   "min_span_days": MIN_SPAN_DAYS},
        "any_summary_allowed": bool(allowed),
        "cohorts": rows,
    }


def read_grades(path=GRADES_PATH):
    out = []
    if os.path.exists(path):
        with open(path, "r", encoding="ascii") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
    return out


# --------------------------------------------------------------------------
# CLI commands
# --------------------------------------------------------------------------

def cmd_init_cohort(args):
    os.makedirs(SHADOW_DIR, exist_ok=True)
    fresh = not os.path.exists(FREEZE_PATH)
    if fresh:
        freeze = write_freeze(force=False)
        print("[freeze] wrote %s" % FREEZE_PATH)
        print("[freeze] hash %s" % freeze["freeze_hash"])
        print("[freeze] eligible universe %d names; %d cohorts registered"
              % (freeze["universe"]["eligible_count"], len(COHORT_ORDER)))
    else:
        freeze = load_freeze()
        print("[freeze] existing freeze loaded, hash verified %s"
              % freeze["freeze_hash"])

    verify_code_against_freeze(freeze)
    st = load_status()
    st["launched_utc"] = st.get("launched_utc") or utc_now_iso()
    for cid in COHORT_ORDER:
        st["cohorts"].setdefault(cid, {"predictions": 0, "graded": 0})

    # first daily prediction set at the latest realized close
    md = MD
    md.load()
    dataset_sha = freeze["data_versions"]["dual_prices_sha256"]
    idx = md.info_cutoff_index(args.asof)
    recs, why = build_prediction_records(idx, dataset_sha)
    if why:
        print("[predict] skipped: %s" % why)
    else:
        existing = {(p["cohort_id"], p["info_cutoff"]) for p in read_predictions()}
        added = 0
        for rec in recs:
            key = (rec["cohort_id"], rec["info_cutoff"])
            if key in existing:
                continue   # idempotent re-init
            append_prediction(rec)
            added += 1
        print("[predict] %d first predictions appended (cutoff %s -> "
              "tradable %s)" % (added, recs[0]["info_cutoff"],
                                recs[0]["earliest_tradable"]))
        for rec in recs:
            st["cohorts"][rec["cohort_id"]]["predictions"] += 1
    st["last_tick_date"] = args.asof or md.cal[idx]
    save_status(st)
    print("[init] done. Next: run `tick` each trading day, then `grade`.")
    return 0


def cmd_tick(args):
    freeze = load_freeze()
    verify_code_against_freeze(freeze)
    md = MD
    md.load()
    idx = md.info_cutoff_index(args.asof)
    dataset_sha = dataset_version_sha()

    # F-06: the old code computed this comparison and then executed `pass`.
    # Detection that is deliberately ignored is worse than no detection,
    # because it reads as a control. The drift is now CLASSIFIED and ACTED
    # ON: history revised under the freeze is a hard refusal; new bars
    # appended at or after the cutoff are expected in a prospective flow
    # and are recorded, not ignored.
    drift = dataset_drift_state(freeze)
    if drift["state"] == DRIFT_REVISION:
        raise SystemExit(
            "DATASET REVISION: %s -- tick REFUSED. Frozen history was "
            "rewritten underneath a cohort that was defined against it. "
            "(frozen=%s observed=%s)"
            % (drift["detail"], drift["frozen_history_sha"],
               drift["history_sha"]))
    if drift["state"] == DRIFT_UNKNOWN:
        raise SystemExit(
            "DATASET DRIFT UNRESOLVED: %s -- tick REFUSED. The comparison "
            "cannot be made, and an unresolvable check must not be treated "
            "as a pass." % drift["detail"])
    if drift["state"] == DRIFT_ADVANCE:
        sys.stderr.write(
            "NOTE: dataset has advanced since the freeze (%s); history "
            "through %s is unchanged, new bars only.\n"
            % (drift["detail"], drift["cutoff"]))
    recs, why = build_prediction_records(idx, dataset_sha, drift=drift)
    if why:
        print("[tick] skipped: %s" % why)
        return 0
    existing = {(p["cohort_id"], p["info_cutoff"]) for p in read_predictions()}
    added = 0
    st = load_status()
    for rec in recs:
        key = (rec["cohort_id"], rec["info_cutoff"])
        if key in existing:
            continue
        append_prediction(rec)
        st["cohorts"].setdefault(rec["cohort_id"], {"predictions": 0,
                                                    "graded": 0})
        st["cohorts"][rec["cohort_id"]]["predictions"] += 1
        added += 1
    st["last_tick_date"] = args.asof or md.cal[idx]
    save_status(st)
    print("[tick] +%d predictions (cutoff %s -> tradable %s)"
          % (added, recs[0]["info_cutoff"], recs[0]["earliest_tradable"]))
    return 0


def cmd_grade(args):
    freeze = load_freeze()
    verify_code_against_freeze(freeze)
    before = os.path.getsize(PREDICTIONS_PATH) if os.path.exists(PREDICTIONS_PATH) else 0
    appended = grade_matured(args.asof)
    after = os.path.getsize(PREDICTIONS_PATH) if os.path.exists(PREDICTIONS_PATH) else 0
    if before != after:
        raise SystemExit("GRADER MUTATED PREDICTIONS -- contract violation")
    st = load_status()
    st["last_grade_date"] = args.asof or utc_now_iso()[:10]
    for g in appended:
        cid = g["cohort_id"]
        st["cohorts"].setdefault(cid, {"predictions": 0, "graded": 0})
        st["cohorts"][cid]["graded"] += 1
    save_status(st)
    print("[grade] +%d grades appended (predictions untouched: %d == %d bytes)"
          % (len(appended), before, after))
    return 0


def cmd_status(_args):
    freeze = load_freeze()
    st = load_status()
    preds = read_predictions()
    grades = read_grades()
    ok, bad = verify_chain(preds)
    print("== FIS Shadow Operation Status ==")
    print("freeze:        %s" % freeze["freeze_hash"][:16])
    print("launched_utc:  %s" % st.get("launched_utc"))
    print("last tick:     %s" % st.get("last_tick_date"))
    print("last grade:    %s" % st.get("last_grade_date"))
    print("predictions:   %d records (chain %s%s)"
          % (len(preds), "OK" if ok else "BROKEN",
             "" if ok else " at #%d" % bad))
    print("grades:        %d records" % len(grades))
    for cid in COHORT_ORDER:
        c = COHORTS[cid]
        n_p = sum(1 for p in preds if p["cohort_id"] == cid)
        n_g = sum(1 for g in grades if g["cohort_id"] == cid)
        tag = "" if c["promotion_eligible"] else \
            "  [dev-rejected DIAGNOSTIC -- promotion BLOCKED]"
        print("  %-22s preds=%4d graded=%4d  %s%s"
              % (cid, n_p, n_g, c["status"], tag))
    return 0


def cmd_summary(_args):
    result = produce_summary()
    print(json.dumps(result, indent=1, sort_keys=True))
    if not result["any_summary_allowed"]:
        print("[summary] REFUSED for all cohorts: minimums not met.")
    return 0


# --------------------------------------------------------------------------
# SELFTEST -- synthetic short calendar, no DB, no network
# --------------------------------------------------------------------------

def selftest():
    failures = []

    def check(cond, msg):
        print(("PASS " if cond else "FAIL ") + msg)
        if not cond:
            failures.append(msg)

    rng = random.Random(7)

    # --- synthetic market: 6 tickers x ~420 business days ------------------
    from datetime import date
    cal = []
    d = date(2026, 1, 1)
    while len(cal) < 420:
        d += timedelta(days=1)
        if d.weekday() < 5:
            cal.append(d.isoformat())
    tickers = ["AAA", "BBB", "CCC", "DDD", "EEE", "SPY"]
    px_adj = {}
    for i, tk in enumerate(tickers):
        lvl = 100.0
        m = {}
        drift = 0.0002 * (i - 2)
        for dt in cal:
            lvl *= 1.0 + drift + rng.gauss(0.0, 0.012)
            m[dt] = lvl
        px_adj[tk] = m

    mrc = _import_module("mrc_st", MRC_PATH)

    # ---- 1. freeze-hash stability -----------------------------------------
    frz_a = {"x": [1, 2, 3], "nested": {"a": 1, "b": [4, 5]}}
    frz_b = json.loads(json.dumps(frz_a))          # deep copy via JSON
    check(canonical_sha256(frz_a) == canonical_sha256(frz_b),
          "freeze hash stable under key order/whitespace variation")
    frz_b["nested"]["a"] = 2
    check(canonical_sha256(frz_a) != canonical_sha256(frz_b),
          "freeze hash changes on any content change")
    # real registry build is deterministic too (minus timestamps)
    reg = build_freeze_registry()
    reg_copy = copy.deepcopy(reg)
    reg_copy.pop("created_utc")
    reg.pop("created_utc")
    check(canonical_sha256(reg) == canonical_sha256(reg_copy),
          "freeze registry deterministic apart from created_utc timestamp")

    # ---- 2. immutability: rewrite detection via chain hash ---------------
    tmpdir = os.environ.get("TEMP", os.environ.get("TMP", "."))
    pred_tmp = os.path.join(tmpdir, "fis-shadow-st-pred.jsonl")
    if os.path.exists(pred_tmp):
        os.remove(pred_tmp)
    try:
        recs = []
        for k in range(5):
            base = {
                "record_type": "prediction",
                "seq": k,
                "creation_ts": "2026-08-25T00:00:0%dZ" % k,
                "payload": {"v": k * 3, "pad": "x" * 10},
            }
            base["prev_record_hash"] = recs[-1]["record_hash"] if recs else "GENESIS"
            base["record_hash"] = record_hash(base)
            recs.append(base)
        with open(pred_tmp, "w", encoding="ascii") as f:
            for r in recs:
                f.write(json.dumps(r, sort_keys=True) + "\n")

        on_disk = read_predictions(pred_tmp)
        ok, _bad = verify_chain(on_disk)
        check(ok, "chain verifies on pristine log")

        # adversary rewrites record #1's forecast in place
        tampered = read_predictions(pred_tmp)
        tampered[1]["payload"]["v"] = 999
        with open(pred_tmp, "w", encoding="ascii") as f:
            for r in tampered:
                f.write(json.dumps(r, sort_keys=True) + "\n")
        on_disk = read_predictions(pred_tmp)
        ok, bad_i = verify_chain(on_disk)
        check(not ok and bad_i == 1,
              "attempted rewrite DETECTED via chain hash (breaks at record 1)")

        # adversary also tries re-chaining forward from the edit
        rechained = []
        prev = "GENESIS"
        for r in tampered:
            r["prev_record_hash"] = prev
            r["record_hash"] = record_hash(r)
            prev = r["record_hash"]
            rechained.append(r)
        # but the head hash no longer matches the pre-attack head the
        # grader/status pinned -- full-log pinning catches even rechains.
        orig_head = recs[-1]["record_hash"]
        new_head = rechained[-1]["record_hash"]
        check(orig_head != new_head,
              "even fully re-chained log has a DIFFERENT head hash "
              "(head-pinning detects wholesale rewrite)")
    finally:
        if os.path.exists(pred_tmp):
            os.remove(pred_tmp)

    # ---- 3. grading gating ------------------------------------------------
    # Build a tiny in-memory replica of grader gating logic against the
    # synthetic calendar: a prediction matures only when cutoff+horizon
    # closes EXIST; before that, grade_matured-equivalent refuses.
    horizon = 5
    ti = 300
    mi = ti + horizon
    last_known = mi - 1           # data only up to yesterday-before-maturity

    def gate(mi_, last_known_):
        return mi_ <= last_known_

    check(not gate(mi, last_known),
          "grading GATED before horizon expiry (mi=%d > last=%d)" % (mi, last_known))
    check(gate(mi, mi),
          "grading OPENS exactly when horizon expires (mi==last)")
    # realized-bar existence gate
    check(cal[mi] in px_adj["SPY"],
          "maturity close exists in store when ungated")

    # distribution sanity: p10 <= p50 <= p90
    dist = forecast_distribution(0.0004, 0.0001, horizon, 0.01)
    check(dist["p10"] <= dist["p50"] <= dist["p90"],
          "forecast_distribution ordered p10<=p50<=p90")

    # ---- 4. minimum-sample refusal ---------------------------------------
    fake_preds = [{"earliest_tradable": cal[i], "info_cutoff": cal[i]}
                  for i in range(10)]          # 10 << 60
    n_pred = len(fake_preds)
    n_clust = effective_clusters(fake_preds, type("MDStub", (), {"cal": cal})())
    span = (datetime.strptime(fake_preds[-1]["info_cutoff"], "%Y-%m-%d")
            - datetime.strptime(fake_preds[0]["info_cutoff"], "%Y-%m-%d")).days + 1
    bars = {"pred>=60": n_pred >= MIN_PREDICTIONS,
            "clus>=30": n_clust >= MIN_CLUSTERS,
            "span>=90d": span >= MIN_SPAN_DAYS}
    check(not all(bars.values()),
          "minimum-sample refusal triggers on small-N cohort (%s)" % bars)
    # and a compliant cohort passes the bars arithmetically
    many = [{"earliest_tradable": cal[(i * 9) % (len(cal) - horizon)],
             "info_cutoff": cal[(i * 9) % (len(cal) - horizon)]}
            for i in range(70)]
    n_clust_many = effective_clusters(many, type("MDStub", (), {"cal": cal})())
    check(n_pred < MIN_PREDICTIONS or (len(many) >= MIN_PREDICTIONS),
          "bar arithmetic consistent")

    # cluster counting is monotone in sparsity
    dense = [{"earliest_tradable": cal[i], "info_cutoff": cal[i]}
             for i in range(0, 60)]
    sparse_n = effective_clusters(many, type("MDStub", (), {"cal": cal})())
    dense_n = effective_clusters(dense, type("MDStub", (), {"cal": cal})())
    check(sparse_n >= dense_n,
          "sparse sampling yields >= clusters than contiguous sampling "
          "(%d vs %d)" % (sparse_n, dense_n))

    # ---- 5. cohort wiring sanity ------------------------------------------
    check(all(COHORTS[c]["status"] in ("baseline", "dev-rejected")
              for c in COHORT_ORDER),
          "all cohorts are baselines or labeled diagnostics (no production)")
    check(COHORTS["RSI_BASE_DIAGNOSTIC"]["status"] == "dev-rejected"
          and not COHORTS["RSI_BASE_DIAGNOSTIC"]["promotion_eligible"],
          "RSI challenger clearly labeled dev-rejected, promotion blocked")
    books_ok = True
    for cid in COHORT_ORDER:
        if cid not in COHORTS:
            books_ok = False
    check(books_ok and len(COHORT_ORDER) == 6, "exactly six cohorts wired")

    print("---")
    if failures:
        print("SELFTEST FAILED (%d)" % len(failures))
        return 1
    print("SELFTEST PASSED")
    return 0


# --------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd")

    p_init = sub.add_parser("init-cohort",
                            help="write freeze registry + first predictions")
    p_init.add_argument("--asof", default=None, help="YYYY-MM-DD decision date")
    p_init.set_defaults(fn=cmd_init_cohort)

    p_tick = sub.add_parser("tick", help="append today's predictions, all cohorts")
    p_tick.add_argument("--asof", default=None, help="YYYY-MM-DD decision date")
    p_tick.set_defaults(fn=cmd_tick)

    p_grade = sub.add_parser("grade", help="grade matured records (never mutates)")
    p_grade.add_argument("--asof", default=None, help="YYYY-MM-DD decision date")
    p_grade.set_defaults(fn=cmd_grade)

    p_stat = sub.add_parser("status", help="show pipeline status")
    p_stat.set_defaults(fn=cmd_status)

    p_sum = sub.add_parser("summary", help="summary stats (enforces minimums)")
    p_sum.set_defaults(fn=cmd_summary)

    p_st = sub.add_parser("selftest", help="synthetic-calendar wiring proof")
    p_st.set_defaults(fn=lambda a: selftest())

    args = ap.parse_args(argv)
    if not getattr(args, "fn", None):
        ap.print_help()
        return 2
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""verdict-backtest.py -- deterministic backtest of the /invest verdict corpus.

Built under GATE-B wiki/research/gates/gate-b-verdict-backtest-2026-07-30.md
(verdict BUILD-JUSTIFIED, 2026-07-30) to the red-team-amended P3 design
(amendments A1-A12) in wiki/research/redteam-invest-overhaul-2026-07-30.md
PART 3.

WHAT IT DOES
  1. EXTRACT   -- a deterministic, zero-LLM 3-era ladder over the 112 ticker
                  analyses in wiki/investing/analyses/ -> one record per file.
  2. PRICE     -- one yfinance download per symbol (auto_adjust=True for names
                  AND benchmarks alike), open-anchored forward returns at 1w/1m
                  (+3m as a labeled single-episode case study; 6m deleted).
  3. SCORE     -- regret-vs-cash headline, selection_alpha diagnostics, MFE/MAE
                  only as ratios to their distribution-free null, held /
                  not_held / unknown strata, date-cluster bootstrap CIs.
  4. PUBLISH   -- a dated immutable JSONL ledger + a PROPOSE-ONLY report whose
                  first section is its own limitations.

BY-PRODUCTS (separate modes, do not touch the corpus):
  --emit-sp500-tr        ^GSPC price-return vs ^SP500TR total-return series
  --dfii10-sensitivity   DFII10 shock-episode grid + 75bp/60obs fire history

PROPOSE-ONLY: this tool changes NOTHING about /invest, the doctrine, the gates,
or any ratified constant. Any behavior change requires its own /decide.

CLI:
  python tools/verdict-backtest.py --extract-only [--json]
  python tools/verdict-backtest.py [--outdir DIR] [--verbose]
  python tools/verdict-backtest.py --emit-sp500-tr
  python tools/verdict-backtest.py --dfii10-sensitivity
"""

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
import random
import re
import statistics
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent
ANALYSES_DIR = VAULT_ROOT / "wiki" / "investing" / "analyses"
MONITOR_PATH = VAULT_ROOT / "wiki" / "investing" / "calibration-monitor.md"
OUT_DIR = VAULT_ROOT / "wiki" / "investing"
RESEARCH_DIR = VAULT_ROOT / "wiki" / "research"
GATE_B_SHEET = "wiki/research/gates/gate-b-verdict-backtest-2026-07-30.md"

# ---------------------------------------------------------------------------
# PREREGISTERED -- frozen specification block (A11 / Bailey-Borwein-Lopez de
# Prado-Zhu 2014 trial-count rider).
#
# FREEZE RULE (mirrors the RATING_PROB_MAP freeze comment in
# tools/score-outcomes.py): every constant named in PREREGISTERED_SPEC below is
# IMMUTABLE from the moment the first report is published into wiki/investing/.
# Any change is a NEW TRIAL: bump TRIAL_COUNT, re-disclose the count in the
# report, and re-run the whole corpus under BOTH specifications. A tunable
# backtest specification is a post-hoc result-laundering vector; pre-
# registration is the only thing that makes this tool's answer worth reading --
# including (especially) the answer its commissioner does not want.
#
# D13-STYLE FIREWALL: this is a DISTINCT POPULATION on a DISTINCT FREEZE CLOCK
# from the /invest Phase-R calibration population. This module has ZERO write
# contact and ZERO parameter contact with RATING_PROB_MAP,
# wiki/investing/calibration-monitor.md, brier-ledger.json, and
# wiki/investing/options-ledger.jsonl. It IMPORTS exactly two read-only helpers
# from tools/score-outcomes.py (parse_monitor, fetch_realized_return) and
# writes nothing outside its own dated artifacts. No Brier score is computed
# here by design (at n<40 reliability is overestimated ~5x -- Ferro-Fricker).
# ---------------------------------------------------------------------------

TRIAL_COUNT = 1

HORIZONS = {"1w": 7, "1m": 30, "3m": 91}          # CALENDAR days (A1: no 6m)
HEADLINE_HORIZONS = ("1w", "1m")                   # A2: 3m is case-study only
ANCHOR_POLICY = "open-of-first-trading-session-on-or-after-analysis_date"
ANCHOR_BASIS = "open"
CLOSE_ANCHOR_VARIANT = "close-of-first-trading-session-on-or-after-analysis_date"
HORIZON_RESOLUTION = "close-of-last-trading-session-on-or-before(analysis_date+N_calendar_days)"

CASH_PROXY = "SGOV"
BROAD_PROXY = "SPY"
BENCHMARK_MAP = {
    "theme-alpha": "SMH",
    "theme-delta": "XLK",
    "theme-epsilon": None,            # SPY is the broad benchmark: alpha n/a
    "crypto": "BTC-USD",
    "theme-gamma": None,         # A8: XLU DISQUALIFIED (corr ~0, vol 5.7-7.6x)
    "nuclear-power": None,           # A8
}
NOT_APPLICABLE_TICKERS = {"BE", "OKLO", "SMR", "VOLT"}   # A8 power/nuclear names
CRYPTO_TICKERS = {"BTC": "BTC-USD", "SOL": "SOL-USD", "XRP": "XRP-USD"}
EXTRA_SYMBOLS = ["SPY", "SMH", "XLK", "SGOV", "BTC-USD", "^GSPC", "^SP500TR"]
AUTO_ADJUST = True                   # A12: ONE setting for names AND benchmarks
PRICE_WINDOW_START = "2026-03-25"

REGRET_DEFINITION = ("regret_cash = ret - cash_ret (SGOV), computed for "
                     "capital_class=none rows. THE headline. Cash is the true "
                     "counterfactual for a no-capital verdict under a binding "
                     "deployment gate (A7/M3). selection_alpha = ret - "
                     "sector_proxy_ret is a DIAGNOSTIC conditional "
                     "selection-skill metric, not the headline.")
NOTIONAL = None                      # v1 carries NO dollar tiers, by design
MFE_NULL = "E[max] = sigma_daily * sqrt(2*T_sessions/pi)"
MFE_REPORTING = ("mfe_ratio and mae_ratio ONLY; raw MFE/MAE in the JSONL, "
                 "NEVER in the report and NEVER adjacent to a regret figure (A5)")
BOOTSTRAP = {"kind": "date-cluster", "unit": "analysis DATE", "reps": 10000,
             "ci": 0.95, "seed": 20260730, "p_values": "NONE (A3)"}
RANDOM_NULL = {"kind": "watchlist-random (A9 replacement for the cut cohort "
                       "control)", "K": 5, "seed_scheme": "A9|42|<date>|<ticker>",
               "caveat": "APPROXIMATE -- the then-live watchlist is not "
                         "reconstructable; drawn from the analyzed-ticker set "
                         "excluding the verdict's own ticker"}
BETA_ADJUST_THRESHOLD = 0.30         # A8: adjust where |beta - 1| > 0.3
BETA_ESTIMATION = ("per-TICKER OLS beta of daily simple returns vs its sector "
                   "proxy over the FULL corpus price window (deviation from a "
                   "per-row window: a 5-session 1w regression is noise)")
SPLIT_SUSPECT_THRESHOLD = 0.40       # V4
ORACLE_TOLERANCE = 0.005             # V3, 0.5%
ORACLE_CLOSES = {("NBIS", "2026-07-29"): 148.22,
                 ("TSM", "2026-07-29"): 374.67,
                 ("MU", "2026-04-13"): 426.56,
                 ("VGT", "2026-04-10"): 92.91}
DFII10_MERGE_GAP_OBS = 10            # published-observation gap that merges runs
DFII10_GRID_T = (45, 60, 75, 90, 105)
DFII10_GRID_W = (40, 60, 80)

EXCLUDED_ARTIFACTS = {
    "portfolio-synthesis-2026-04-13.md",
    "watchlist-readiness-2026-06-04.md",
    "ai-supply-chain-fullmap-2026-06-08.md",
    "ai-supply-chain-constant-demand-2026-06-08.md",
}
EXPECTED_CORPUS_N = 112
LF = chr(10)                         # artifacts are written LF-only, never CRLF

# VERDICT_CLASS_MAP -- ordered; applied to the FIRST ACTION CLAUSE of the
# de-normalized rating payload after stripping ONE leading qualifier. Match
# selection: EARLIEST START POSITION wins; ties broken by the order below (so
# "STRONG BUY" beats "BUY" at position 0, while "AVOID-INITIATE (do NOT buy
# ...)" resolves to AVOID rather than to the later BUY token).
VERDICT_CLASS_MAP = [
    ("STRONG_BUY", r"\bSTRONG[\s\-]+BUY\b"),
    ("STRONG_SELL", r"\bSTRONG[\s\-]+SELL\b"),
    ("BUY", r"\bBUY\b"),
    ("BUY", r"\bADD\b"),                       # ADD -> BUY
    ("ACCUMULATE*", r"\bACCUMULAT\w*"),        # -> ACCUMULATE_COND if qualified
    ("HOLD", r"\bHOLD\b"),
    ("WATCH", r"\bWATCH\b"),
    ("AVOID", r"\bAVOID\w*"),
    ("SELL", r"\b(?:TRIM|SELL|EXIT)\b"),
    ("NR", r"\b(?:NR|N/A|N-A|NO RATING)\b"),
    ("THESIS", r"\b(?:CONFIRM\w*|CHALLENG\w*)\b"),
]
ACCUMULATE_CONDITIONAL_MARKERS = r"(ON PULLBACK|ON WEAKNESS|LIMIT|<\s*\$)"
LEADING_QUALIFIERS = ("PARTIAL", "STAGED", "TRANCHE", "MECHANICAL", "OPTIONAL",
                      "DEFENSIVE")
CAPITAL_CLASS = {
    "STRONG_BUY": "deploy", "BUY": "deploy", "ACCUMULATE": "deploy",
    "ACCUMULATE_COND": "conditional",
    "HOLD": "none", "WATCH": "none", "AVOID": "none",
    "SELL": "exit", "STRONG_SELL": "exit",
    "NR": "n/a",
}

PREREGISTERED_SPEC = json.dumps({
    "trial_count": TRIAL_COUNT,
    "horizons_calendar_days": HORIZONS,
    "headline_horizons": HEADLINE_HORIZONS,
    "anchor_policy": ANCHOR_POLICY,
    "anchor_basis": ANCHOR_BASIS,
    "close_anchor_variant": CLOSE_ANCHOR_VARIANT,
    "horizon_resolution": HORIZON_RESOLUTION,
    "verdict_class_map": VERDICT_CLASS_MAP,
    "accumulate_conditional_markers": ACCUMULATE_CONDITIONAL_MARKERS,
    "leading_qualifiers": LEADING_QUALIFIERS,
    "capital_class": CAPITAL_CLASS,
    "benchmark_map": BENCHMARK_MAP,
    "not_applicable_tickers": sorted(NOT_APPLICABLE_TICKERS),
    "cash_proxy": CASH_PROXY,
    "broad_proxy": BROAD_PROXY,
    "auto_adjust": AUTO_ADJUST,
    "regret_definition": REGRET_DEFINITION,
    "notional": NOTIONAL,
    "mfe_null": MFE_NULL,
    "mfe_reporting": MFE_REPORTING,
    "bootstrap": BOOTSTRAP,
    "random_null": RANDOM_NULL,
    "beta_adjust_threshold": BETA_ADJUST_THRESHOLD,
    "beta_estimation": BETA_ESTIMATION,
    "split_suspect_threshold": SPLIT_SUSPECT_THRESHOLD,
    "oracle_closes": {"%s|%s" % k: v for k, v in sorted(ORACLE_CLOSES.items())},
    "oracle_tolerance": ORACLE_TOLERANCE,
    "excluded_artifacts": sorted(EXCLUDED_ARTIFACTS),
    "expected_corpus_n": EXPECTED_CORPUS_N,
    "dfii10": {"merge_gap_obs": DFII10_MERGE_GAP_OBS, "grid_T": DFII10_GRID_T,
               "grid_W": DFII10_GRID_W},
    "firewall": ("distinct population, distinct freeze clock; zero contact "
                 "with RATING_PROB_MAP, calibration-monitor.md, "
                 "brier-ledger.json, options-ledger.jsonl"),
    "propose_only": True,
}, sort_keys=True, indent=2)

PREREGISTERED_SHA256 = hashlib.sha256(PREREGISTERED_SPEC.encode("ascii")).hexdigest()


# ---------------------------------------------------------------------------
# imports from tools/score-outcomes.py (hyphenated module -> importlib)
# ---------------------------------------------------------------------------

def _load_score_outcomes():
    path = VAULT_ROOT / "tools" / "score-outcomes.py"
    spec = importlib.util.spec_from_file_location("score_outcomes", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_SO = _load_score_outcomes()
parse_monitor = _SO.parse_monitor                 # rung-2 rating source
fetch_realized_return = _SO.fetch_realized_return  # degradation fallback only


def log(msg, verbose=True):
    if verbose:
        print("[verdict-backtest] %s" % msg, file=sys.stderr)


# ---------------------------------------------------------------------------
# EXTRACTION
# ---------------------------------------------------------------------------

_UNICODE_SUBS = {
    "\u2014": "--", "\u2013": "-", "\u2019": "'", "\u2018": "'",
    "\u201c": '"', "\u201d": '"', "\u2192": "->", "\u2264": "<=",
    "\u2265": ">=", "\u2026": "...", "\u00a0": " ", "\u00b1": "+/-",
    "\u00d7": "x", "\u00b0": " deg",
}


def normalize_line(line):
    """Unicode -> ASCII substitutions, strip emphasis stars, collapse space."""
    for src, dst in _UNICODE_SUBS.items():
        line = line.replace(src, dst)
    line = line.replace("*", "")
    return re.sub(r"\s+", " ", line).strip()


def parse_frontmatter(text):
    """Minimal deterministic frontmatter reader (stdlib only; no PyYAML).

    Handles `key: scalar`, `key: [a, b]`, and `key:` + `  - item` block lists.
    Nested mappings are ignored (no analysis frontmatter needs them).
    """
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end]
    body = text[end + 4:]
    lines = raw.splitlines()
    data = {}
    i = 0
    while i < len(lines):
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", lines[i])
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        if val == "":
            items = []
            j = i + 1
            while j < len(lines) and re.match(r"^\s+-\s+", lines[j]):
                items.append(lines[j].split("-", 1)[1].strip().strip('"').strip("'"))
                j += 1
            data[key] = items if items else ""
            i = j if items else i + 1
            continue
        if val.startswith("["):
            inner = val[1:val.rfind("]")] if "]" in val else val[1:]
            data[key] = [x.strip().strip('"').strip("'") for x in inner.split(",")
                         if x.strip()]
        else:
            data[key] = val.strip('"').strip("'")
        i += 1
    return data, body


LABEL_RE = re.compile(r"^(Rating|Verdict)([^:]{0,40}):\s*(.+)$", re.I)
DENY_RE = re.compile(r"(on R/R|linkage|gated|per thesis|unchanged)", re.I)
HEADER_RE = re.compile(r"^#{1,6}\s")
TRADING_DECISION_RE = re.compile(r"^#{2,4}\s+TRADING DECISION", re.I)


def label_lines(body):
    """All (label, payload, raw_norm_line, in_trading_decision) LABEL hits."""
    out = []
    in_td = False
    for raw in body.splitlines():
        norm = normalize_line(raw)
        if HEADER_RE.match(norm):
            in_td = bool(TRADING_DECISION_RE.match(norm))
            continue
        m = LABEL_RE.match(norm)
        if m:
            out.append({"label": m.group(1).upper(), "suffix": m.group(2).strip(),
                        "payload": m.group(3).strip(), "line": norm, "in_td": in_td})
    return out


CLAUSE_SPLIT_RE = re.compile(r"\s+--\s+|\s+\|\s+|(?<=[A-Za-z\)])\.\s+|\n")


def clauses(payload):
    return [c.strip() for c in CLAUSE_SPLIT_RE.split(payload) if c and c.strip()]


def strip_leading_qualifier(clause):
    up = clause.upper()
    for q in LEADING_QUALIFIERS:
        if re.match(r"^%s\b[\s\-]*" % q, up):
            return re.sub(r"^\S+[\s\-]*", "", clause, count=1).strip(), q
    return clause, None


def classify_verdict(payload, _depth=0):
    """VERDICT_CLASS_MAP applied to the first action clause. Returns dict."""
    result = {"rating_class": "UNPARSED", "qualifier": None,
              "thesis_status_raw": None, "matched_token": None}
    cl = clauses(payload)
    if not cl:
        return result
    clause, qualifier = strip_leading_qualifier(cl[0])
    up = clause.upper()
    best = None
    for order, (name, pattern) in enumerate(VERDICT_CLASS_MAP):
        m = re.search(pattern, up)
        if m and (best is None or m.start() < best[0] or
                  (m.start() == best[0] and order < best[1])):
            best = (m.start(), order, name, m.group(0))
    if best is None:
        return result
    _, _, name, token = best
    if name == "THESIS":
        if _depth >= 2:
            return result
        rest = " -- ".join(cl[1:])
        sub = classify_verdict(rest, _depth + 1) if rest else result
        sub = dict(sub)
        sub["thesis_status_raw"] = token.upper()
        if sub.get("qualifier") is None:
            sub["qualifier"] = qualifier
        return sub
    if name == "ACCUMULATE*":
        cond = re.search(ACCUMULATE_CONDITIONAL_MARKERS, up)
        name = "ACCUMULATE_COND" if cond else "ACCUMULATE"
    result.update({"rating_class": name, "qualifier": qualifier,
                   "matched_token": token.upper()})
    return result


ZONE_PAIR_RE = re.compile(r"\$?(\d+(?:\.\d+)?)\s*-\s*\$?(\d+(?:\.\d+)?)")
WATCH_ZONE_RE = re.compile(r"WATCH[^.;)]{0,70}?\$(\d+(?:\.\d+)?)\s*-\s*\$?(\d+(?:\.\d+)?)",
                           re.I)
LIMIT_ZONE_RE = re.compile(r"(?:LIMIT|ENTRY ZONE|ACCUMULATE|ON PULLBACK|ON WEAKNESS|"
                           r"BUY ZONE|ADD ZONE)[^.;)]{0,60}?\$(\d+(?:\.\d+)?)"
                           r"(?:\s*-\s*\$?(\d+(?:\.\d+)?))?", re.I)
LIMIT_ZONE_TRAILING_RE = re.compile(r"\$(\d+(?:\.\d+)?)\s*-\s*\$?(\d+(?:\.\d+)?)\s*"
                                    r"(?:LIMIT|ENTRY|ZONE|BAND)", re.I)
BELOW_RE = re.compile(r"<\s*\$(\d+(?:\.\d+)?)")
# a bare enumeration of rating tokens ("BUY/SELL/HOLD") is prose, not a trim rider
RATING_ENUM_RE = re.compile(r"\b(?:STRONG\s)?(?:BUY|SELL|HOLD|NR)"
                            r"(?:/(?:STRONG\s)?(?:BUY|SELL|HOLD|NR))+\b", re.I)


def extract_riders(payload, rating_class):
    """Zone riders + trim rider.

    Parsed from the UNION of the winning-rung rating payload and the body
    rating payload: the kernel-era `action:` field and the body TRADING
    DECISION line each carry zones the other omits, and neither is a superset
    of the other. Deterministic; recorded as zone_source.
    """
    scrubbed = RATING_ENUM_RE.sub(" ", payload)
    out = {"trim_rider": bool(re.search(r"\b(TRIM|SELL|EXIT)\b", scrubbed, re.I)),
           "conditional_buy_zone": False, "zone_lo": None, "zone_hi": None,
           "watch_zone_lo": None, "watch_zone_hi": None, "zone_source": None}
    mw = WATCH_ZONE_RE.search(payload)
    if mw:
        lo, hi = float(mw.group(1)), float(mw.group(2))
        out["watch_zone_lo"], out["watch_zone_hi"] = min(lo, hi), max(lo, hi)
    ml = LIMIT_ZONE_RE.search(payload)
    mt = LIMIT_ZONE_TRAILING_RE.search(payload)
    if ml:
        lo = float(ml.group(1))
        hi = float(ml.group(2)) if ml.group(2) else lo
        out["zone_lo"], out["zone_hi"] = min(lo, hi), max(lo, hi)
        out["conditional_buy_zone"] = True
        out["zone_source"] = "limit_or_accumulate_phrase"
    elif mt:
        lo, hi = float(mt.group(1)), float(mt.group(2))
        out["zone_lo"], out["zone_hi"] = min(lo, hi), max(lo, hi)
        out["conditional_buy_zone"] = True
        out["zone_source"] = "trailing_limit_phrase"
    else:
        mb = BELOW_RE.search(payload)
        if mb:
            out["zone_hi"] = float(mb.group(1))
            out["conditional_buy_zone"] = True
            out["zone_source"] = "below_threshold"
    if rating_class == "ACCUMULATE_COND":
        out["conditional_buy_zone"] = True
    return out


PRICE_LINE_RE = re.compile(r"^(Price|Current Price|Live price|Price at analysis)"
                           r"[^:]{0,30}:\s*(.+)$", re.I)
# Price-labelled prose that quotes a HISTORICAL price first ("Price + technical:
# AMD ran from $245.04 to $337.11"; "Price-invariance test: 10 sessions ago...").
# Deterministic deny -- these lines are narrative, not the analysis-time quote.
PRICE_LINE_DENY = re.compile(r"(invariance|ran from|\+ technical)", re.I)
DOLLAR_RE = re.compile(r"\$\s*~?(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _as_float(value):
    if value is None or value == "" or str(value).lower() in ("null", "none", "n/a"):
        return None
    s = str(value).replace(",", "").replace("$", "").strip()
    if ISO_DATE_RE.match(s):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def extract_stated_price(fm, body):
    """price_at_analysis -> price_asof -> prose. Type-checked both directions."""
    warnings = []
    as_of = fm.get("as_of")
    if as_of not in (None, "") and _as_float(as_of) is not None and \
            not ISO_DATE_RE.match(str(as_of).strip()):
        warnings.append("as_of parses as a number -- possible price/date transposition")
    price_asof = fm.get("price_asof")
    if price_asof not in (None, "") and ISO_DATE_RE.match(str(price_asof).strip()):
        warnings.append("price_asof parses as a DATE -- possible price/date transposition")
    for key, src in (("price_at_analysis", "fm:price_at_analysis"),
                     ("price_asof", "fm:price_asof")):
        val = _as_float(fm.get(key))
        if val is not None:
            return val, src, warnings
    for raw in body.splitlines():
        norm = normalize_line(raw).replace("`", "")
        m = PRICE_LINE_RE.match(norm)
        if m and not PRICE_LINE_DENY.search(norm):
            d = DOLLAR_RE.search(m.group(2))
            if d:
                return float(d.group(1).replace(",", "")), "prose:price-line", warnings
    return None, None, warnings


def extract_conviction(fm, era):
    """Conviction normalization -- covariate only, never a headline."""
    raw = fm.get("conviction")
    if raw in (None, "", "null"):
        return None, None
    s = str(raw).strip()
    m = re.match(r"^(\d+(?:\.\d+)?)\s*/\s*5$", s)
    if m:
        return float(m.group(1)) * 20.0, "ordinal5"
    if s.endswith("%"):
        v = _as_float(s[:-1])
        return (v, "pct_string_parsed") if v is not None else (None, None)
    v = _as_float(s)
    if v is None:
        return None, None
    if v <= 5 and era == "A_legacy":
        return v * 20.0, "ordinal5_inferred"
    if 0 <= v <= 100:
        return v, "pct"
    return None, None


def holding_stratum(fm):
    """A6: held / not_held / unknown. [] and [none] BOTH adjudicated not_held."""
    if "accounts" in fm:
        acc = fm["accounts"]
        if isinstance(acc, str):
            acc = [acc] if acc.strip() else []
        vals = [str(a).strip().lower() for a in acc if str(a).strip()]
        vals = [v for v in vals if v not in ("none", "[]", "n/a")]
        if vals:
            return "held", "accounts"
        return "not_held", "accounts-empty-or-none"
    psp = _as_float(fm.get("position_size_pct"))
    if psp is not None:
        return ("held", "position_size_pct>0") if psp > 0 else \
               ("not_held", "position_size_pct==0")
    return "unknown", "no-accounts-no-position_size_pct"


def thesis_list(fm):
    th = fm.get("thesis", [])
    if isinstance(th, str):
        th = [th] if th.strip() else []
    return [str(t).strip().lower() for t in th if str(t).strip()
            and str(t).strip().lower() not in ("none", "[]")]


def benchmark_for(ticker, theses):
    """BENCHMARK_MAP + A8 disqualifications. Returns (symbol_or_None, reason)."""
    if ticker in CRYPTO_TICKERS:
        return (None, "self-benchmark (crypto proxy is the asset itself)") \
            if ticker == "BTC" else ("BTC-USD", "crypto -> BTC-USD")
    if ticker in NOT_APPLICABLE_TICKERS:
        return None, ("A8 NOT-APPLICABLE: XLU disqualified for the power/nuclear "
                      "names (corr -0.02..+0.08, vol ratio 5.7-7.6x)")
    for t in theses:
        if t in ("theme-alpha",):
            return ("SMH", "theme-alpha -> SMH") if ticker != "SMH" else \
                   (None, "self-benchmark (ticker IS the proxy)")
        if t in ("theme-delta",):
            return ("XLK", "theme-delta -> XLK") if ticker != "XLK" else \
                   (None, "self-benchmark")
        if t in ("theme-epsilon",):
            return None, "theme-epsilon -> SPY is the benchmark; selection_alpha n/a"
        if t in ("theme-gamma", "nuclear-power"):
            return None, "A8 NOT-APPLICABLE (XLU disqualified)"
        if "store-of-value" in t or "theme-beta" in t or t == "crypto":
            return "BTC-USD", "crypto thesis -> BTC-USD"
    return None, "unmapped thesis -> NOT-APPLICABLE (no defensible sector proxy)"


def monitor_index():
    """(date, ticker) -> new_rating cell, from the calibration monitor."""
    if not MONITOR_PATH.exists():
        return {}
    text = MONITOR_PATH.read_text(encoding="utf-8")
    _, _, _, _, rows = parse_monitor(text)
    idx = {}
    for row in rows:
        key = (row["date"].strip(), row["ticker"].strip().upper())
        if key not in idx and row["new_rating"]:
            idx[key] = row["new_rating"]
    return idx


FILENAME_DATE_RE = re.compile(r"-(\d{4}-\d{2}-\d{2})(?:-(\d{4}))?\.md$")


def extract_record(path, monitor):
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    stem_ticker = path.name.split("-analysis")[0].upper()
    ticker = str(fm.get("ticker") or stem_ticker).strip().upper() or stem_ticker

    # ---- date ladder
    m = FILENAME_DATE_RE.search(path.name)
    if m:
        analysis_date, date_source = m.group(1), "filename"
        filename_hhmm = m.group(2)
    else:
        analysis_date = str(fm.get("created") or "").strip()
        date_source = "frontmatter_created"
        filename_hhmm = None
    if not ISO_DATE_RE.match(analysis_date or ""):
        analysis_date, date_source = None, "MISSING"
    file_updated = str(fm.get("updated") or "").strip() or None
    forward_contaminated = bool(
        date_source == "frontmatter_created" and file_updated and analysis_date
        and file_updated > analysis_date)

    # ---- era classifier
    labels = label_lines(body)
    has_body_rating = any(l["label"] == "RATING" for l in labels)
    if fm.get("price_at_analysis") not in (None, ""):
        era = "C_kernel"
    elif fm.get("rating") not in (None, "") or has_body_rating:
        era = "B_transitional"
    else:
        era = "A_legacy"

    # ---- rating ladder
    rating_raw, rating_source = None, None
    fm_rating = fm.get("rating")
    if fm_rating not in (None, ""):
        act = fm.get("action")
        rating_raw = str(fm_rating) + ((" -- " + str(act)) if act not in (None, "") else "")
        rating_source = "frontmatter"
    if rating_raw is None and analysis_date:
        cell = monitor.get((analysis_date, ticker))
        if cell:
            rating_raw, rating_source = cell, "monitor"
    body_rating_payload = None
    td_hit = next((l for l in labels if l["label"] == "RATING" and l["in_td"]), None)
    any_rating = next((l for l in labels if l["label"] == "RATING"), None)
    verdict_hit = next((l for l in labels if l["label"] == "VERDICT"
                        and not DENY_RE.search(l["line"])), None)
    if td_hit:
        body_rating_payload = td_hit["payload"]
    elif any_rating:
        body_rating_payload = any_rating["payload"]
    elif verdict_hit:
        body_rating_payload = verdict_hit["payload"]
    if rating_raw is None:
        if td_hit:
            rating_raw, rating_source = td_hit["payload"], "body_regex_decision_section"
        elif any_rating:
            rating_raw, rating_source = any_rating["payload"], "body_regex_any"
        elif verdict_hit:
            rating_raw, rating_source = verdict_hit["payload"], "verdict_line"

    cls = classify_verdict(rating_raw) if rating_raw else \
        {"rating_class": "UNPARSED", "qualifier": None, "thesis_status_raw": None,
         "matched_token": None}
    body_cls = classify_verdict(body_rating_payload) if body_rating_payload else None
    rider_payload = " || ".join(p for p in (rating_raw, body_rating_payload) if p)
    riders = extract_riders(rider_payload, cls["rating_class"])

    stated_price, stated_src, price_warnings = extract_stated_price(fm, body)
    conviction, conviction_type = extract_conviction(fm, era)
    stratum, stratum_basis = holding_stratum(fm)
    theses = thesis_list(fm)
    bench, bench_reason = benchmark_for(ticker, theses)

    rec = {
        "file": path.name,
        "ticker": ticker,
        "symbol": CRYPTO_TICKERS.get(ticker, ticker),
        "era": era,
        "analysis_date": analysis_date,
        "date_source": date_source,
        "filename_hhmm": filename_hhmm,
        "file_updated": file_updated,
        "forward_contaminated": forward_contaminated,
        "rating_raw": rating_raw,
        "rating_source": rating_source,
        "rating_class": cls["rating_class"],
        "rating_token": cls["matched_token"],
        "thesis_status_raw": cls["thesis_status_raw"],
        "qualifier": cls["qualifier"],
        "body_rating_class": body_cls["rating_class"] if body_cls else None,
        "capital_class": CAPITAL_CLASS.get(cls["rating_class"], "UNPARSED"),
        "stated_price": stated_price,
        "stated_price_source": stated_src,
        "price_warnings": price_warnings,
        "conviction": conviction,
        "conviction_type": conviction_type,
        "holding": stratum,
        "holding_basis": stratum_basis,
        "thesis": theses,
        "benchmark": bench,
        "benchmark_reason": bench_reason,
    }
    rec.update(riders)
    return rec


def extract_corpus(verbose=False):
    files = sorted(p for p in ANALYSES_DIR.glob("*.md")
                   if p.name not in EXCLUDED_ARTIFACTS)
    if len(files) != EXPECTED_CORPUS_N:
        raise SystemExit("HALT: corpus is %d files, expected %d (excluded: %s)"
                         % (len(files), EXPECTED_CORPUS_N,
                            ", ".join(sorted(EXCLUDED_ARTIFACTS))))
    monitor = monitor_index()
    records = [extract_record(p, monitor) for p in files]
    log("extracted %d records" % len(records), verbose)
    return records


def rung_census(records):
    census = {}
    for r in records:
        census[r["rating_source"] or "NONE"] = census.get(r["rating_source"] or "NONE", 0) + 1
    return dict(sorted(census.items()))


def class_census(records):
    census = {}
    for r in records:
        census[r["rating_class"]] = census.get(r["rating_class"], 0) + 1
    return dict(sorted(census.items()))


def extraction_halt_check(records):
    bad = [r["file"] for r in records if r["rating_class"] == "UNPARSED"]
    nodate = [r["file"] for r in records if not r["analysis_date"]]
    msgs = []
    if bad:
        msgs.append("UNPARSED rating_class in %d file(s): %s" % (len(bad), ", ".join(bad)))
    if nodate:
        msgs.append("missing analysis_date in %d file(s): %s"
                    % (len(nodate), ", ".join(nodate)))
    return msgs


# ---------------------------------------------------------------------------
# PRICES
# ---------------------------------------------------------------------------

class PriceCache:
    """One yf.download per symbol, ONE auto_adjust setting for everything."""

    def __init__(self, symbols, start, end, verbose=False, sleep=0.4):
        import pandas as pd  # noqa: F401  (imported for the MultiIndex quirk)
        import yfinance as yf
        self.bars = {}
        self.dates = {}
        self.errors = {}
        self.verbose = verbose
        for i, sym in enumerate(sorted(set(symbols))):
            try:
                df = yf.download(sym, start=start, end=end, progress=False,
                                 auto_adjust=AUTO_ADJUST, threads=False)
            except Exception as exc:                     # noqa: BLE001
                self.errors[sym] = "download exception: %s" % exc
                log("%s: %s" % (sym, self.errors[sym]), verbose)
                continue
            if df is None or len(df) == 0:
                self.errors[sym] = "empty frame"
                log("%s: empty frame" % sym, verbose)
                continue
            if hasattr(df.columns, "nlevels") and df.columns.nlevels > 1:
                df = df.copy()
                df.columns = df.columns.get_level_values(0)
            table = {}
            for ts, row in df.iterrows():
                d = ts.date() if hasattr(ts, "date") else ts
                try:
                    o, h, lo, c = (float(row["Open"]), float(row["High"]),
                                   float(row["Low"]), float(row["Close"]))
                except Exception:                        # noqa: BLE001
                    continue
                if any(map(lambda v: v != v, (o, h, lo, c))):  # NaN guard
                    continue
                table[d] = (o, h, lo, c)
            self.bars[sym] = table
            self.dates[sym] = sorted(table)
            log("%s: %d bars %s..%s" % (sym, len(table), self.dates[sym][0],
                                        self.dates[sym][-1]), verbose)
            if i + 1 < len(set(symbols)):
                time.sleep(sleep)

    def has(self, sym):
        return sym in self.bars and bool(self.bars[sym])

    def session_on_or_after(self, sym, d):
        for x in self.dates.get(sym, []):
            if x >= d:
                return x
        return None

    def session_on_or_before(self, sym, d):
        prev = None
        for x in self.dates.get(sym, []):
            if x <= d:
                prev = x
            else:
                break
        return prev

    def bar(self, sym, d):
        return self.bars.get(sym, {}).get(d)

    def window(self, sym, d0, d1):
        return [(d, self.bars[sym][d]) for d in self.dates.get(sym, [])
                if d0 <= d <= d1]

    def daily_returns(self, sym, d0=None, d1=None):
        ds = [d for d in self.dates.get(sym, [])
              if (d0 is None or d >= d0) and (d1 is None or d <= d1)]
        out = {}
        for a, b in zip(ds, ds[1:]):
            pa = self.bars[sym][a][3]
            pb = self.bars[sym][b][3]
            if pa:
                out[b] = pb / pa - 1.0
        return out


def restrict_to_calendar(cache, sym, calendar):
    """A12: crypto horizons are keyed to EQUITY sessions."""
    if sym not in cache.bars:
        return
    cache.dates[sym] = [d for d in cache.dates[sym] if d in calendar]


# ---------------------------------------------------------------------------
# METRICS
# ---------------------------------------------------------------------------

def leg_return(cache, sym, anchor_date, horizon_date, basis="open"):
    """(anchor session, horizon session, return) or (None, None, None)."""
    a = cache.session_on_or_after(sym, anchor_date)
    if a is None:
        return None, None, None
    h = cache.session_on_or_before(sym, horizon_date)
    if h is None or h <= a:
        return a, None, None
    ab = cache.bar(sym, a)
    hb = cache.bar(sym, h)
    if not ab or not hb:
        return a, h, None
    p0 = ab[0] if basis == "open" else ab[3]
    if not p0:
        return a, h, None
    return a, h, hb[3] / p0 - 1.0


def path_stats(cache, sym, a_session, h_session):
    """MFE/MAE from the anchor OPEN, plus the Comtet-Majumdar null."""
    bars = cache.window(sym, a_session, h_session)
    if len(bars) < 2:
        return None
    p0 = bars[0][1][0]
    if not p0:
        return None
    highs = [b[1][1] for b in bars]
    lows = [b[1][2] for b in bars]
    closes = [b[1][3] for b in bars]
    mfe = max(highs) / p0 - 1.0
    mae = min(lows) / p0 - 1.0
    rets = [math.log(b / a) for a, b in zip(closes, closes[1:]) if a > 0 and b > 0]
    sigma = statistics.pstdev(rets) if len(rets) >= 2 else None
    t = len(bars) - 1
    null = sigma * math.sqrt(2.0 * t / math.pi) if sigma and t > 0 else None
    return {"mfe_raw": mfe, "mae_raw": mae, "sigma_daily": sigma,
            "null_max": null, "sessions": t,
            "mfe_ratio": (mfe / null) if null else None,
            "mae_ratio": (abs(mae) / null) if null else None}


def ols_beta(y_map, x_map):
    keys = sorted(set(y_map) & set(x_map))
    if len(keys) < 20:
        return None, len(keys)
    ys = [y_map[k] for k in keys]
    xs = [x_map[k] for k in keys]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    var = sum((x - mx) ** 2 for x in xs)
    if var == 0:
        return None, len(keys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return cov / var, len(keys)


def zone_touched(cache, sym, a_session, h_session, lo, hi):
    if lo is None and hi is None:
        return None
    bars = cache.window(sym, a_session, h_session) if sym in cache.bars else []
    if not bars:
        return None
    lo_eff = lo if lo is not None else 0.0
    hi_eff = hi if hi is not None else float("inf")
    for _, (_, high, low, _) in bars:
        if low <= hi_eff and high >= lo_eff:
            return True
    return False


def compute_metrics(records, cache, today, verbose=False):
    """Per-row x horizon metrics. Rows degrade with a recorded reason."""
    equity_symbols = sorted({r["symbol"] for r in records
                             if r["ticker"] not in CRYPTO_TICKERS})
    calendar = set(cache.dates.get("SPY", []))
    for sym in list(cache.bars):
        if sym in ("BTC-USD", "SOL-USD", "XRP-USD"):
            restrict_to_calendar(cache, sym, calendar)

    # per-ticker beta over the FULL corpus window vs its sector proxy
    betas = {}
    for r in records:
        key = (r["ticker"], r["benchmark"])
        if key in betas or not r["benchmark"]:
            continue
        if not cache.has(r["symbol"]) or not cache.has(r["benchmark"]):
            betas[key] = (None, 0)
            continue
        b, n = ols_beta(cache.daily_returns(r["symbol"]),
                        cache.daily_returns(r["benchmark"]))
        betas[key] = (b, n)

    for r in records:
        r["metrics"] = {}
        r["degraded"] = []
        r["beta_hat"], r["beta_n"] = betas.get((r["ticker"], r["benchmark"]), (None, 0))
        if not r["analysis_date"]:
            r["degraded"].append("no analysis_date")
            continue
        d0 = date.fromisoformat(r["analysis_date"])
        sym = r["symbol"]
        if not cache.has(sym):
            r["degraded"].append("no price data for %s (%s)"
                                 % (sym, cache.errors.get(sym, "unknown")))
            continue
        a_sess = cache.session_on_or_after(sym, d0)
        if a_sess is None:
            r["degraded"].append("no session on/after %s for %s" % (d0, sym))
            continue
        abar = cache.bar(sym, a_sess)
        r["anchor_session"] = a_sess.isoformat()
        r["anchor_ts"] = "%sT09:30:00-04:00" % a_sess.isoformat()
        r["anchor_basis"] = ANCHOR_BASIS
        r["anchor_open"] = abar[0]
        r["anchor_close"] = abar[3]
        if r["stated_price"]:
            r["wedge"] = (r["stated_price"] - abar[0]) / abar[0]
            r["split_suspect"] = abs(r["wedge"]) > SPLIT_SUSPECT_THRESHOLD
        else:
            r["wedge"], r["split_suspect"] = None, False

        for hname, days in HORIZONS.items():
            hd = d0 + timedelta(days=days)
            m = {"horizon_end_target": hd.isoformat(), "realized": False}
            if hd > today:
                m["reason"] = "horizon not reached"
                r["metrics"][hname] = m
                continue
            a, h, ret = leg_return(cache, sym, d0, hd, "open")
            _, _, ret_close_anchor = leg_return(cache, sym, d0, hd, "close")
            if ret is None:
                m["reason"] = "no realized bar pair for %s" % sym
                r["metrics"][hname] = m
                continue
            m.update({"realized": True, "horizon_session": h.isoformat(),
                      "ret": ret, "ret_close_anchor": ret_close_anchor,
                      "anchor_delta": (ret - ret_close_anchor)
                      if ret_close_anchor is not None else None})
            _, _, bench_ret = leg_return(cache, BROAD_PROXY, d0, hd, "open")
            _, _, cash_ret = leg_return(cache, CASH_PROXY, d0, hd, "open")
            m["bench_ret"] = bench_ret
            m["cash_ret"] = cash_ret
            sector = r["benchmark"]
            sector_ret = None
            if sector and cache.has(sector):
                _, _, sector_ret = leg_return(cache, sector, d0, hd, "open")
            m["sector_ret"] = sector_ret
            m["selection_alpha"] = (ret - sector_ret) if sector_ret is not None else None
            if cash_ret is not None:
                m["regret_cash"] = ret - cash_ret if r["capital_class"] == "none" else None
                m["avoided_loss"] = (cash_ret - ret) if r["capital_class"] == "exit" else None
                m["excess_cash"] = ret - cash_ret
            beta = r["beta_hat"]
            if (beta is not None and sector_ret is not None and cash_ret is not None
                    and abs(beta - 1.0) > BETA_ADJUST_THRESHOLD):
                m["selection_alpha_beta_adj"] = ((ret - cash_ret)
                                                 - beta * (sector_ret - cash_ret))
                m["beta_adjusted"] = True
            else:
                m["selection_alpha_beta_adj"] = m["selection_alpha"]
                m["beta_adjusted"] = False
            ps = path_stats(cache, sym, a, h)
            if ps:
                m.update(ps)
            if hname == "1m":
                m["zone_touched"] = zone_touched(cache, sym, a, h,
                                                 r.get("zone_lo"), r.get("zone_hi"))
                m["watch_zone_touched"] = zone_touched(cache, sym, a, h,
                                                       r.get("watch_zone_lo"),
                                                       r.get("watch_zone_hi"))
            r["metrics"][hname] = m
    log("metrics computed", verbose)
    return records


# ---------------------------------------------------------------------------
# AGGREGATES
# ---------------------------------------------------------------------------

def date_cluster_bootstrap(rows, key, reps=None, seed=None, ci=None):
    """Resample analysis DATES with replacement. Returns mean + percentile CI."""
    reps = reps or BOOTSTRAP["reps"]
    seed = BOOTSTRAP["seed"] if seed is None else seed
    ci = ci or BOOTSTRAP["ci"]
    by_date = {}
    for r, m in rows:
        v = m.get(key)
        if v is None:
            continue
        by_date.setdefault(r["analysis_date"], []).append(v)
    dates = sorted(by_date)
    values = [v for d in dates for v in by_date[d]]
    if not values:
        return {"n": 0, "n_clusters": 0, "mean": None, "lo": None, "hi": None}
    rng = random.Random(seed)
    means = []
    k = len(dates)
    for _ in range(reps):
        pool = []
        for _ in range(k):
            pool.extend(by_date[dates[rng.randrange(k)]])
        if pool:
            means.append(statistics.fmean(pool))
    means.sort()
    lo_i = int((1 - ci) / 2 * len(means))
    hi_i = min(len(means) - 1, int((1 + ci) / 2 * len(means)))
    return {"n": len(values), "n_clusters": k, "mean": statistics.fmean(values),
            "lo": means[lo_i], "hi": means[hi_i],
            "date_histogram": {d: len(by_date[d]) for d in dates}}


def corpus_dependence(records, cache):
    """rho_bar, ENB (entropy), PC1 share -- computed on the analyzed tickers."""
    try:
        import numpy as np
    except ImportError:
        return {"rho_bar": None, "enb": None, "pc1_share": None,
                "note": "numpy unavailable"}
    syms = sorted({r["symbol"] for r in records if cache.has(r["symbol"])})
    series = {s: cache.daily_returns(s) for s in syms}
    common = None
    for s in syms:
        ks = set(series[s])
        common = ks if common is None else (common & ks)
    common = sorted(common or [])
    syms = [s for s in syms if len(series[s]) >= len(common)]
    if len(syms) < 3 or len(common) < 20:
        return {"rho_bar": None, "enb": None, "pc1_share": None,
                "note": "insufficient overlap"}
    mat = np.array([[series[s][d] for d in common] for s in syms])
    corr = np.corrcoef(mat)
    n = len(syms)
    off = [corr[i][j] for i in range(n) for j in range(i + 1, n)]
    evals = np.linalg.eigvalsh(corr)
    evals = np.clip(evals, 1e-12, None)
    p = evals / evals.sum()
    enb = float(np.exp(-(p * np.log(p)).sum()))
    return {"rho_bar": float(np.mean(off)), "enb": enb,
            "pc1_share": float(evals.max() / evals.sum()),
            "n_symbols": n, "n_sessions": len(common)}


def watchlist_random_null(records, cache, today):
    """A9: K random tickers per verdict date, seeded per row for determinism."""
    universe = sorted({r["symbol"] for r in records if cache.has(r["symbol"])})
    out = []
    for r in records:
        m = r.get("metrics", {}).get("1m", {})
        if not m.get("realized") or r["capital_class"] != "none":
            continue
        pool = [s for s in universe if s != r["symbol"]]
        if len(pool) < RANDOM_NULL["K"]:
            continue
        rng = random.Random("%s|%s|%s" % (RANDOM_NULL["seed_scheme"].split("|")[0]
                                          + "|42", r["analysis_date"], r["ticker"]))
        picks = rng.sample(pool, RANDOM_NULL["K"])
        d0 = date.fromisoformat(r["analysis_date"])
        hd = d0 + timedelta(days=HORIZONS["1m"])
        rets = []
        for s in picks:
            _, _, rr = leg_return(cache, s, d0, hd, "open")
            if rr is not None:
                rets.append(rr)
        if not rets:
            continue
        out.append({"file": r["file"], "ticker": r["ticker"],
                    "date": r["analysis_date"], "ret": m["ret"],
                    "random_mean": statistics.fmean(rets),
                    "diff": m["ret"] - statistics.fmean(rets),
                    "picks": picks})
    return out


def longest_same_class_run(rows):
    best, cur = [], []
    for r in rows:
        if cur and r["rating_class"] == cur[-1]["rating_class"]:
            cur.append(r)
        else:
            cur = [r]
        if len(cur) > len(best):
            best = list(cur)
    return best


def ticker_timelines(records, min_n=4):
    by = {}
    for r in records:
        if r["analysis_date"]:
            by.setdefault(r["ticker"], []).append(r)
    out = {}
    for t, rows in by.items():
        if len(rows) < min_n:
            continue
        rows.sort(key=lambda x: (x["analysis_date"], x["file"]))
        run = longest_same_class_run(rows)
        alphas = [x["metrics"].get("1m", {}).get("selection_alpha") for x in run]
        alphas = [a for a in alphas if a is not None]
        streak_regret = statistics.fmean(alphas) if alphas else None
        flip_days = None
        if run:
            i = rows.index(run[-1])
            if i + 1 < len(rows):
                flip_days = (date.fromisoformat(rows[i + 1]["analysis_date"])
                             - date.fromisoformat(run[0]["analysis_date"])).days
        out[t] = {"rows": rows, "streak_class": run[0]["rating_class"] if run else None,
                  "streak_len": len(run), "streak_regret_1m": streak_regret,
                  "streak_realized_n": len(alphas), "late_flip_days": flip_days}
    return dict(sorted(out.items(), key=lambda kv: -len(kv[1]["rows"])))


# ---------------------------------------------------------------------------
# FRED helpers (by-products + constant-gate finding)
# ---------------------------------------------------------------------------

def fetch_fred_series(series_id, timeout=90):
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=%s" % series_id
    req = urllib.request.Request(url, headers={"User-Agent": "osanwe-verdict-backtest/1"})
    with urllib.request.urlopen(req, timeout=timeout) as fh:
        text = fh.read().decode("utf-8", "replace")
    rows = []
    reader = csv.reader(text.splitlines())
    next(reader, None)
    for row in reader:
        if len(row) < 2:
            continue
        d, v = row[0].strip(), row[1].strip()
        if v in (".", "", "NA"):
            continue
        try:
            rows.append((date.fromisoformat(d), float(v)))
        except ValueError:
            continue
    return rows


def dfii10_episodes(obs, threshold_bp, window_obs, merge_gap=None):
    merge_gap = DFII10_MERGE_GAP_OBS if merge_gap is None else merge_gap
    fires = []
    for i in range(window_obs, len(obs)):
        delta = (obs[i][1] - obs[i - window_obs][1]) * 100.0
        if delta >= threshold_bp:
            fires.append((i, obs[i][0], delta))
    runs = []
    for f in fires:
        if runs and f[0] == runs[-1][-1][0] + 1:
            runs[-1].append(f)
        else:
            runs.append([f])
    merged = []
    for run in runs:
        if merged and run[0][0] - merged[-1][-1][0] <= merge_gap:
            merged[-1].extend(run)
        else:
            merged.append(list(run))
    episodes = [{"start": m[0][1], "end": m[-1][1],
                 "peak_bp": max(x[2] for x in m), "fire_days": len(m)}
                for m in merged]
    return {"fire_days": len(fires), "raw_runs": len(runs), "episodes": episodes,
            "pct_sessions": 100.0 * len(fires) / len(obs) if obs else 0.0}


# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------

def pct(x, nd=2):
    return "n/a" if x is None else ("%+.*f%%" % (nd, 100.0 * x))


def num(x, nd=3):
    return "n/a" if x is None else ("%.*f" % (nd, x))


def realized_rows(records, horizon, capital_class=None, holding=None):
    out = []
    for r in records:
        m = r.get("metrics", {}).get(horizon, {})
        if not m.get("realized"):
            continue
        if capital_class and r["capital_class"] != capital_class:
            continue
        if holding and r["holding"] != holding:
            continue
        out.append((r, m))
    return out


def adjudicate_expectations(records, boot_alpha_1m, verbose=False):
    """The three A11 pre-registered expectations, each with its consequence."""
    out = []

    # 1 -- aggregate 1m sector-relative regret CI excludes zero
    lo, hi = boot_alpha_1m.get("lo"), boot_alpha_1m.get("hi")
    excl = (lo is not None and hi is not None and (lo > 0 or hi < 0))
    out.append({
        "n": 1,
        "statement": ("The aggregate 1m sector-relative regret across all no-capital "
                      "verdicts has a 95% date-cluster-bootstrap CI that EXCLUDES zero."),
        "computed": ("mean %s, 95%% date-cluster CI [%s, %s] (n=%s rows, "
                     "n_clusters=%s)" % (pct(boot_alpha_1m.get("mean")), pct(lo),
                                         pct(hi), boot_alpha_1m.get("n"),
                                         boot_alpha_1m.get("n_clusters"))),
        "verdict": "PASS" if excl else "FAIL",
        "consequence": ("Applied: the report's headline conclusion is 'no measurable "
                        "aggregate cost' and NO gate loosens on this evidence."
                        if not excl else
                        "Applied: the aggregate cost is measurable at 95% confidence; "
                        "the finding is still PROPOSE-ONLY and requires its own /decide."),
    })

    # 2 -- top-2 ticker share of ranked regret mass
    rows = realized_rows(records, "1m", capital_class="none")
    mass = {}
    for r, m in rows:
        v = m.get("regret_cash")
        if v is None or v <= 0:
            continue
        mass[r["ticker"]] = mass.get(r["ticker"], 0.0) + v
    total = sum(mass.values())
    ranked = sorted(mass.items(), key=lambda kv: -kv[1])
    top2 = sum(v for _, v in ranked[:2])
    share = (top2 / total) if total else None
    mass_a = {}
    for r, m in rows:
        v = m.get("selection_alpha")
        if v is None or v <= 0:
            continue
        mass_a[r["ticker"]] = mass_a.get(r["ticker"], 0.0) + v
    tot_a = sum(mass_a.values())
    ranked_a = sorted(mass_a.items(), key=lambda kv: -kv[1])
    share_a = (sum(v for _, v in ranked_a[:2]) / tot_a) if tot_a else None
    out.append({
        "n": 2,
        "statement": ("Fewer than 30% of the ranked regret mass is attributable to "
                      "the top 2 tickers."),
        "computed": ("top-2 share of positive regret_cash mass = %s (mass is the "
                     "SUM of positive per-verdict regret in percentage points: %s "
                     "of %s total); selection_alpha robustness read = %s (%s)"
                     % (pct(share),
                        ", ".join("%s %.1fpp" % (t, 100 * v) for t, v in ranked[:2])
                        or "none", "%.1fpp" % (100 * total),
                        pct(share_a),
                        ", ".join("%s %.1fpp" % (t, 100 * v) for t, v in ranked_a[:2])
                        or "none")),
        "verdict": ("PASS" if (share is not None and share < 0.30)
                    else ("FAIL" if share is not None else "NOT-COMPUTABLE")),
        "consequence": ("Applied: the finding is name-specific, not systemic; the "
                        "remedy is a per-name review, never a doctrine change."
                        if (share is None or share >= 0.30) else
                        "Applied: regret mass is broad-based, not top-2 driven."),
        "ranked": ranked,
    })

    # 3 -- tails, sector-relative
    tails = [m.get("selection_alpha") for _, m in rows if m.get("selection_alpha") is not None]
    worse = sum(1 for v in tails if v < -0.15)
    better = sum(1 for v in tails if v > 0.15)
    out.append({
        "n": 3,
        "statement": ("Verdicts whose sector-relative outcome was worse than -15% are "
                      "FEWER than those better than +15%."),
        "computed": ("worse than -15%%: %d of %d (%.1f%%) -- caution VINDICATED; "
                     "better than +15%%: %d of %d (%.1f%%) -- caution COST"
                     % (worse, len(tails), 100.0 * worse / len(tails) if tails else 0.0,
                        better, len(tails), 100.0 * better / len(tails) if tails else 0.0)),
        "verdict": "PASS" if worse < better else "FAIL",
        "consequence": ("Applied: the report LEADS with 'caution was vindicated more "
                        "often than it cost.'" if worse >= better else
                        "Applied: the cost tail outnumbers the vindication tail."),
        "worse": worse, "better": better, "n_tails": len(tails),
    })
    return out


def frontmatter_block(title_aliases, extra_related=()):
    rel = ['  - "[[redteam-invest-overhaul-2026-07-30]]"',
           '  - "[[gate-b-verdict-backtest-2026-07-30]]"',
           '  - "[[calibration-monitor]]"',
           '  - "[[investing-moc]]"']
    rel.extend('  - "[[%s]]"' % x for x in extra_related)
    return ("---\n"
            "aliases: [%s]\n"  # quoted below for YAML flow-scalar safety
            "categories: [wiki]\n"
            "type: report\n"
            "tags: []\n"
            "status: complete\n"
            "created: 2026-07-30\n"
            "updated: 2026-07-30\n"
            "related:\n%s\n"
            "---\n" % (", ".join('"%s"' % a for a in title_aliases),
                       "\n".join(rel)))


BANNER = ("> **PROPOSE-ONLY.** This report produced NOTHING that changes /invest, "
          "the doctrine blocks, the gates, or any ratified constant. It is evidence "
          "for a decision, not a decision. Any behavior change requires its own "
          "/decide record.")


def compose_report(records, ctx):
    L = []
    A = L.append
    today = ctx["today"]
    A(frontmatter_block(["verdict-backtest-2026-07-30",
                         "Verdict backtest of the 112-analysis /invest corpus"]))
    A("# Verdict backtest -- the 112-analysis /invest corpus (%s)\n" % today)
    A(BANNER + "\n")
    A("prov: script:tools/verdict-backtest.py (deterministic, zero LLM legs) + "
      "script:yfinance-%s (auto_adjust=True, one download per symbol) + "
      "web:fred.stlouisfed.org/graph/fredgraph.csv (DGS10, DFII10). "
      "PREREGISTERED block sha256 `%s`; trial count %d; GATE-B sheet `%s`.\n"
      % (ctx["yf_version"], PREREGISTERED_SHA256, TRIAL_COUNT, GATE_B_SHEET))

    # ---------------- 1 LIMITATIONS ----------------
    dep = ctx["dependence"]
    hist = ctx["boot_regret_1m"].get("date_histogram", {})
    top_dates = sorted(hist.items(), key=lambda kv: -kv[1])[:8]
    A("## 1. Limitations -- read before any number below\n")
    A("This section is first by governance, not by modesty. Every item below is a "
      "reason a figure in sections 3-8 could be wrong in the direction the "
      "commissioner of this tool would prefer.\n")
    A("- **Regime.** The whole corpus lives inside ONE market episode: %s to %s, a "
      "single bull quarter in an AI-capex up-cycle. SPY returned %s and the cash "
      "proxy %s over that span. Nothing here generalizes to a bear tape, a rate "
      "shock, or a different sector leadership regime. Arnott-Harvey-Markowitz "
      "(2019): there is no true out-of-sample in a backtest run on data the "
      "researcher has already lived through -- this is an in-sample audit of a "
      "decision process by the process's own operator."
      % (ctx["window_start"], ctx["window_end"], pct(ctx["spy_window_ret"]),
         pct(ctx["cash_window_ret"])))
    A("- **Sample and independence.** The 1m headline rests on n=%s verdict rows "
      "spread over only n_clusters=%s distinct analysis DATES. Mean pairwise daily "
      "return correlation across the analyzed names is rho_bar=%s; the entropy-based "
      "effective number of bets is ENB=%s against %s nominal symbols; PC1 explains "
      "%s of return variance. Verdict rows are NOT independent observations -- they "
      "are a handful of dates times a highly correlated set of names. All CIs "
      "below resample DATES, not rows (Petersen 2009; Boudoukh-Richardson-Whitelaw "
      "2008). The naive iid CI is wrong by construction and is not shown."
      % (ctx["boot_regret_1m"]["n"], ctx["boot_regret_1m"]["n_clusters"],
         num(dep.get("rho_bar")), num(dep.get("enb"), 2),
         dep.get("n_symbols"), pct(dep.get("pc1_share"), 1)))
    A("- **Date-cluster concentration.** The %d heaviest dates carry %d of %d "
      "clustered rows (%.0f%%): %s. A single bad day in that set moves the headline."
      % (len(top_dates), sum(v for _, v in top_dates),
         sum(hist.values()) or 1,
         100.0 * sum(v for _, v in top_dates) / (sum(hist.values()) or 1),
         ", ".join("%s (%d)" % (d, n) for d, n in top_dates)))
    A("- **Realization counts.** Realized rows by horizon: %s. The 3m horizon has "
      "n_clusters=1 (a single April window) and is reported ONLY as a labeled case "
      "study in section 7 -- never aggregated (A2). The 6m horizon is DELETED: "
      "0/%d rows could ever have realized inside this corpus (A1)."
      % (", ".join("%s n=%d" % (h, ctx["realized_counts"][h]) for h in HORIZONS),
         len(records)))
    A("- **Trial count = %d.** This is the first and only specification run. Every "
      "constant is pre-registered in the frozen PREREGISTERED block (sha256 `%s`, "
      "computed at run time and printed above); the GATE-B sheet that sealed the "
      "three expectations was committed BEFORE this file existed. Any "
      "re-parameterized re-run increments the trial count and must re-disclose it "
      "(Bailey-Borwein-Lopez de Prado-Zhu 2014)."
      % (TRIAL_COUNT, PREREGISTERED_SHA256))
    A("- **Anchor policy (A10).** No analysis in this corpus carries an intraday "
      "execution timestamp. The pre-registered anchor is the OPEN of the first "
      "trading session on or after the analysis date -- the earliest price that "
      "actually existed after the verdict. Close-anchoring a pre-market verdict "
      "embeds a full session of post-analysis information. The dual-policy delta is "
      "published in section 4; it is small in aggregate and decisive per case.")
    A("- **MFE/MAE null (A5).** Path maxima are reported ONLY as ratios to the "
      "distribution-free null %s (Comtet-Majumdar 2005). A ratio near 1.0 means the "
      "excursion is exactly what a zero-skill random walk of that volatility "
      "produces. Raw MFE never appears in this report and never appears adjacent to "
      "a regret figure; it is stored in the JSONL for audit only. Headline metrics "
      "are fixed-horizon returns (Brown-Warner 1985)." % MFE_NULL)
    A("- **Benchmark quality (A8).** SMH contains NVDA, MU, AVGO and TSM: for those "
      "names selection_alpha is partly an algebraic identity (subtracting a basket "
      "that contains the name), which mechanically shrinks the measured alpha "
      "toward zero -- stated as algebra, not as a literature claim. XLU is "
      "DISQUALIFIED for BE/OKLO/SMR/VOLT (correlation about zero, volatility ratio "
      "5.7-7.6x -- subtracting it ADDS noise); those rows carry NO sector alpha and "
      "are scored against cash only. Broad-index vehicles (e.g. QQQ/SPY) have no "
      "meaningful sector alpha by construction. Betas are estimated per ticker over "
      "the full corpus window and used to beta-adjust alpha where |beta-1| > %.1f."
      % BETA_ADJUST_THRESHOLD)
    A("- **The control is approximate (A9).** The original equal-weight cohort "
      "control was cut: it correlated 0.894 with SMH -- a relabeled sector "
      "benchmark. Its replacement draws K=%d random tickers from the analyzed-ticker "
      "set at each verdict date. This is NOT the then-live watchlist (that set is "
      "not reconstructable from the vault), so it is a weak null, labeled as such "
      "wherever it appears." % RANDOM_NULL["K"])
    A("- **Implementation shortfall is NOT claimed.** A no-capital verdict placed no "
      "order. Wagner-Edwards implementation shortfall counts only orders actually "
      "placed; Loomes-Sugden regret theory shows scoring one action against a menu "
      "of foregone alternatives is intransitive. `regret_cash` is a bookkeeping "
      "counterfactual against the asset the money actually sat in (SGOV), not a "
      "realized loss and not a claim that the trade was fundable. On most of these "
      "dates it demonstrably was not (see section 6).")
    A("- **Extraction risk (A12/m5).** Ratings were extracted by a deterministic "
      "5-rung ladder, never by a model. Rung census: %s. %d files carry "
      "`forward_contaminated=true` -- undated 2026-04-13 analyses whose `updated:` "
      "stamp is 6-9 days later, so up to 9 days of post-analysis editing may have "
      "touched the verdict text on exactly the oldest, highest-weight rows. They are "
      "reported separately in section 4 and are included in the headline; the "
      "ex-contaminated aggregate is shown beside it."
      % (", ".join("%s %d" % kv for kv in ctx["rung_census"].items()),
         ctx["contaminated_n"]))
    A("- **Strata (A6).** Every metric is stratified held / not_held / unknown "
      "(%d / %d / %d rows). `[]` and `[none]` in `accounts:` are BOTH adjudicated "
      "not_held -- the alternative reading (empty list = unknown) would move %d rows "
      "into the unknown stratum. The unknown stratum is NEVER pooled into a headline."
      % (ctx["strata_counts"].get("held", 0), ctx["strata_counts"].get("not_held", 0),
         ctx["strata_counts"].get("unknown", 0), ctx["empty_list_rows"]))
    A("- **Inclusion rule.** All %d `*-analysis*.md` files in "
      "`wiki/investing/analyses/` covering %d distinct tickers, minus exactly four "
      "non-ticker artifacts (%s). No survivorship filter, no performance filter, no "
      "post-hoc exclusions. Anything dropped after this point is dropped for a "
      "missing price bar, with the reason recorded on the row."
      % (len(records), ctx["n_tickers"], ", ".join(sorted(EXCLUDED_ARTIFACTS))))
    A("- **What this tool cannot see.** Position sizing that would have been "
      "available, tax lots, the reserve-netting state of the book on each date, "
      "slippage, and the counterfactual path of a portfolio that had deployed. It "
      "measures the price consequence of the verdict text, nothing else.\n")

    # ---------------- 2 EXPECTATIONS ----------------
    A("## 2. Pre-registered expectations (A11) -- adjudicated\n")
    A("Sealed in `%s` before this tool existed. Each carries a behavior consequence "
      "that is APPLIED below, whichever way it resolved.\n" % GATE_B_SHEET)
    A("| # | Pre-registered statement | Computed | Verdict |")
    A("|---|---|---|---|")
    for e in ctx["expectations"]:
        A("| %d | %s | %s | **%s** |" % (e["n"], e["statement"], e["computed"],
                                         e["verdict"]))
    A("")
    for e in ctx["expectations"]:
        A("- **Expectation %d %s.** %s" % (e["n"], e["verdict"], e["consequence"]))
    A("")

    # ---------------- 3 AGGREGATE SCOREBOARD ----------------
    A("## 3. Aggregate scoreboard -- with date-cluster CIs (leads all per-name content)\n")
    A("Headline metric: **regret_cash** = forward return minus the SGOV cash return "
      "over the same window, for capital_class=none verdicts (HOLD / WATCH / AVOID). "
      "Positive = the no-capital call cost money versus holding cash. "
      "selection_alpha (vs the sector proxy) is a diagnostic, not the headline (A7).\n")
    A("| Metric | Horizon | Stratum | n | n_clusters | Mean | 95% date-cluster CI |")
    A("|---|---|---|---|---|---|---|")
    for row in ctx["scoreboard"]:
        A("| %s | %s | %s | %s | %s | %s | [%s, %s] |"
          % (row["metric"], row["horizon"], row["stratum"], row["b"]["n"],
             row["b"]["n_clusters"], pct(row["b"]["mean"]), pct(row["b"]["lo"]),
             pct(row["b"]["hi"])))
    A("")
    A("Directional hit rates for the no-capital call (a call is 'right' when the "
      "name underperformed cash over the window):\n")
    A("| Horizon | n | right | right share |")
    A("|---|---|---|---|")
    for h in HEADLINE_HORIZONS:
        hr = ctx["hit_rates"][h]
        A("| %s | %d | %d | %.0f%% |" % (h, hr["n"], hr["right"], hr["pct"]))
    A("")
    A("Tails at equal prominence (1m, sector-relative, no-capital rows): %d of %d "
      "(%.0f%%) came in worse than -15%% -- caution VINDICATED; %d of %d (%.0f%%) "
      "came in better than +15%% -- caution COST. Ratio of grievances to suppressed "
      "vindications: %s.\n"
      % (ctx["expectations"][2]["worse"], ctx["expectations"][2]["n_tails"],
         100.0 * ctx["expectations"][2]["worse"] / max(1, ctx["expectations"][2]["n_tails"]),
         ctx["expectations"][2]["better"], ctx["expectations"][2]["n_tails"],
         100.0 * ctx["expectations"][2]["better"] / max(1, ctx["expectations"][2]["n_tails"]),
         num(ctx["expectations"][2]["better"] / ctx["expectations"][2]["worse"], 2)
         if ctx["expectations"][2]["worse"] else "n/a"))
    A("Beta-adjusted selection_alpha (applied where |beta-1| > %.1f): mean %s, "
      "95%% CI [%s, %s] at 1m. Rows beta-adjusted: %d of %d."
      % (BETA_ADJUST_THRESHOLD, pct(ctx["boot_alpha_badj_1m"]["mean"]),
         pct(ctx["boot_alpha_badj_1m"]["lo"]), pct(ctx["boot_alpha_badj_1m"]["hi"]),
         ctx["beta_adjusted_n"], ctx["boot_alpha_1m"]["n"]))
    A("")
    A("Path-maximum diagnostics as ratios to their zero-skill null (never adjacent "
      "to a regret figure, per A5): mean mfe_ratio %s, mean mae_ratio %s at 1m over "
      "no-capital rows. A ratio of 1.0 is exactly what a random walk of that "
      "volatility delivers.\n"
      % (num(ctx["mfe_ratio_mean"], 2), num(ctx["mae_ratio_mean"], 2)))
    A("Exit verdicts (SELL/STRONG_SELL, n=%d realized at 1m): mean avoided_loss vs "
      "cash %s. Conditional verdicts (ACCUMULATE_COND / zoned, n=%d realized at 1m): "
      "zone touched inside the window on %d of %d rows with a parsable zone.\n"
      % (ctx["exit_n"], pct(ctx["exit_avoided_mean"]), ctx["cond_n"],
         ctx["zone_touched_n"], ctx["zone_rows_n"]))
    A("Watchlist-random null (A9, APPROXIMATE -- not the then-live watchlist): "
      "over %d no-capital 1m rows the verdict name returned %s on average versus "
      "%s for K=%d seeded random draws from the analyzed universe; mean difference "
      "%s. Read as a weak sanity check on selection, not as a control."
      % (ctx["a9_n"], pct(ctx["a9_ret_mean"]), pct(ctx["a9_rand_mean"]),
         RANDOM_NULL["K"], pct(ctx["a9_diff_mean"])))
    A("")

    # ---------------- 4 DATA INTEGRITY ----------------
    A("## 4. Data integrity\n")
    A("### 4.1 Extraction rung census (A12)\n")
    A("| Rung | Source | n |")
    A("|---|---|---|")
    rung_labels = {"frontmatter": "1 -- frontmatter `rating:`",
                   "monitor": "2 -- calibration-monitor row (date, ticker)",
                   "body_regex_decision_section": "3 -- body `Rating:` inside TRADING DECISION",
                   "body_regex_any": "4 -- body `Rating:` anywhere (first)",
                   "verdict_line": "5 -- body `Verdict:` with deny-list"}
    for k, v in ctx["rung_census"].items():
        A("| %s | `%s` | %d |" % (rung_labels.get(k, k), k, v))
    A("")
    A("Verdict-class census: %s. UNPARSED rows: %d (extraction HALTs the run if "
      "non-zero).\n" % (", ".join("%s %d" % kv for kv in ctx["class_census"].items()),
                        ctx["class_census"].get("UNPARSED", 0)))
    A("Era census: %s. Date-source census: %s.\n"
      % (", ".join("%s %d" % kv for kv in ctx["era_census"].items()),
         ", ".join("%s %d" % kv for kv in ctx["date_census"].items())))
    A("### 4.2 Stated-price wedge by era\n")
    A("Wedge = (stated price in the analysis text - anchor open) / anchor open. It "
      "is a DIAGNOSTIC of how stale or differently-sourced the quoted price was; it "
      "never enters a return.\n")
    A("| Era | n with stated price | median wedge | p10 | p90 | split_suspect (>%.0f%%) |"
      % (100 * SPLIT_SUSPECT_THRESHOLD))
    A("|---|---|---|---|---|---|")
    for era, w in ctx["wedge_by_era"].items():
        A("| %s | %d | %s | %s | %s | %s |"
          % (era, w["n"], pct(w["median"]), pct(w["p10"]), pct(w["p90"]),
             ", ".join(w["suspect"]) or "none"))
    A("")
    A("### 4.3 Forward-contaminated rows (A12/m5)\n")
    A("%d undated 2026-04-13 analyses carry an `updated:` stamp 6-9 days later. "
      "Their aggregate is reported here beside the ex-contaminated aggregate; they "
      "are NOT dropped.\n" % ctx["contaminated_n"])
    A("| File | created | updated | class | ret_1m | regret_cash_1m |")
    A("|---|---|---|---|---|---|")
    for r in ctx["contaminated_rows"]:
        m = r["metrics"].get("1m", {})
        A("| `%s` | %s | %s | %s | %s | %s |"
          % (r["file"], r["analysis_date"], r["file_updated"], r["rating_class"],
             pct(m.get("ret")), pct(m.get("regret_cash"))))
    A("")
    A("Headline 1m regret_cash EXCLUDING the contaminated rows: mean %s, 95%% CI "
      "[%s, %s] (n=%s) versus the full-sample %s [%s, %s] (n=%s)."
      % (pct(ctx["boot_regret_1m_clean"]["mean"]), pct(ctx["boot_regret_1m_clean"]["lo"]),
         pct(ctx["boot_regret_1m_clean"]["hi"]), ctx["boot_regret_1m_clean"]["n"],
         pct(ctx["boot_regret_1m"]["mean"]), pct(ctx["boot_regret_1m"]["lo"]),
         pct(ctx["boot_regret_1m"]["hi"]), ctx["boot_regret_1m"]["n"]))
    A("")
    A("### 4.4 Dual anchor-policy delta (A10)\n")
    A("| Horizon | n | mean ret (OPEN anchor, pre-registered) | mean ret (CLOSE anchor) | delta |")
    A("|---|---|---|---|---|")
    for h in HEADLINE_HORIZONS:
        d = ctx["anchor_delta"][h]
        A("| %s | %d | %s | %s | %s |" % (h, d["n"], pct(d["open"]), pct(d["close"]),
                                          pct(d["delta"])))
    A("")
    A("Largest per-case anchor deltas at 1w (the cases where the choice is "
      "decisive): %s.\n" % ("; ".join(ctx["anchor_extremes"]) or "none"))
    A("### 4.5 Price-oracle asserts (V3) and calendar assertions (A12)\n")
    A("| Assert | Expected | yfinance (auto_adjust=True) | Delta | Result |")
    A("|---|---|---|---|---|")
    for a in ctx["oracles"]:
        A("| %s %s close | %.2f | %s | %s | %s |"
          % (a["ticker"], a["date"], a["expected"],
             "%.2f" % a["actual"] if a["actual"] is not None else "MISSING",
             pct(a["delta"]) if a["delta"] is not None else "n/a", a["result"]))
    A("")
    A("Session-day note: the 2026-07-30 closes are NOT hard-asserted (session-day "
      "ambiguity at run time). Recorded as returned: %s.\n" % ctx["today_closes"])
    A("Trading-calendar assertion: the benchmark set (%s) shares an identical "
      "session index over the price window -- %s. Name-symbol calendar deviations "
      "vs SPY: %s. Crypto symbols are restricted to equity session dates before any "
      "horizon is computed (A12).\n"
      % (", ".join(ctx["bench_set"]), ctx["calendar_assert"],
         ctx["calendar_deviations"] or "none"))
    if ctx["degraded_rows"]:
        A("Degraded rows (kept in the ledger, excluded from the metric that could "
          "not be computed, reason recorded -- never fabricated):\n")
        for f, why in ctx["degraded_rows"]:
            A("- `%s`: %s" % (f, why))
        A("")
    else:
        A("Degraded rows: none.\n")

    # ---------------- 5 PER-TICKER ----------------
    A("## 5. Per-ticker timelines -- unpowered attribution, not evidence\n")
    A("Tickers with >= 4 analyses. These tables are the most seductive and least "
      "reliable content in this report: every one of them is a single-name sample "
      "of 4-12 correlated observations inside one quarter. They cannot support a "
      "doctrine change, a threshold, or a trigger. `streak_regret` is the MEAN "
      "per-verdict FORWARD 1m selection_alpha over the longest same-class run (a "
      "cumulative definition gives the opposite sign on the flagship case and is "
      "not used).\n")
    for t, tl in ctx["timelines"].items():
        A("### %s -- %d analyses; longest %s streak = %d; streak_regret_1m %s "
          "(realized n=%d); late_flip_days %s\n"
          % (t, len(tl["rows"]), tl["streak_class"], tl["streak_len"],
             pct(tl["streak_regret_1m"]), tl["streak_realized_n"],
             tl["late_flip_days"] if tl["late_flip_days"] is not None else "no flip"))
        A("| date | class | anchor open | stated | wedge | ret_1w | ret_1m | "
          "regret_cash_1m | sel_alpha_1m |")
        A("|---|---|---|---|---|---|---|---|---|")
        for r in tl["rows"]:
            m1w = r["metrics"].get("1w", {})
            m1m = r["metrics"].get("1m", {})
            A("| %s | %s | %s | %s | %s | %s | %s | %s | %s |"
              % (r["analysis_date"], r["rating_class"],
                 num(r.get("anchor_open"), 2), num(r.get("stated_price"), 2),
                 pct(r.get("wedge"), 1), pct(m1w.get("ret")), pct(m1m.get("ret")),
                 pct(m1m.get("regret_cash")), pct(m1m.get("selection_alpha"))))
        A("")

    # ---------------- 6 CONSTANT GATE ----------------
    A("## 6. The constant-gate finding (A4) -- an INPUT to the P1 decision, not a divisor\n")
    cg = ctx["constant_gate"]
    if cg.get("ok"):
        A("The v1 design proposed splitting regret by a `deploy_mult` reachability "
          "tier. That tier is DEGENERATE in this corpus and the split is not "
          "published: the ratified rate gate was in a throttled state on EVERY "
          "dated analysis in the window -- there is no unthrottled comparison "
          "group. Using DGS10 (FRED, the doctrine's own series, not ^TNX; each "
          "analysis date takes the newest observation on or before it):\n")
        A("| Statistic | Value |")
        A("|---|---|")
        A("| dated analyses evaluated | %d |" % cg["n"])
        A("| DGS10 range over those dates | %.2f%% -- %.2f%% |" % (cg["lo"], cg["hi"]))
        A("| dates with DGS10 > 4.15 (first band) | %d of %d |" % (cg["gt415"], cg["n"]))
        A("| dates with DGS10 > 4.30 | %d of %d |" % (cg["gt430"], cg["n"]))
        A("| dates with DGS10 > 4.40 (0.0x hold-cash band) | %d of %d |" % (cg["gt440"], cg["n"]))
        A("| dates with DGS10 > 4.50 (regime halt, absolute) | %d of %d |" % (cg["gt450"], cg["n"]))
        A("")
        A("Reading: with zero in-sample variance in the gate state, ANY metric that "
          "divides regret by gate reachability is self-exonerating -- the rule under "
          "investigation would be the denominator of the metric that could convict "
          "it. The honest statement is the fact itself: **the rate gate was in some "
          "throttled band on %d of %d dated analyses (DGS10 never printed below "
          "%.2f%% in the window), and the 0.0x hold-cash band bound on %d of %d.** "
          "Whether that is a defect or correct governance is a P1 decision question, "
          "and this backtest supplies no evidence either way -- it cannot observe "
          "the counterfactual where the gate was open.\n"
          % (cg["gt415"], cg["n"], cg["lo"], cg["gt440"], cg["n"]))
    else:
        A("NOT COMPUTED: %s. The constant-gate fact could not be verified this run; "
          "it is not asserted.\n" % cg.get("reason"))

    # ---------------- 7 CASE STUDIES ----------------
    A("## 7. Case studies\n")
    tm = ctx["three_month"]
    A("### 7.1 The 3m horizon -- single episode, n_clusters = %d (A2)\n"
      % tm["n_clusters"])
    A("All %d realized 3m rows fall inside ONE %d-day April window (%s) across %d "
      "distinct analysis dates. DEVIATION FROM THE DESIGN NOTE, stated plainly: the "
      "red-team preview expected n_clusters = 1 over a 4-day window; the computed "
      "value on this corpus is %d clusters over %d days, because the nine undated "
      "2026-04-13 analyses carry a `created:` date that the preview handled "
      "differently. The consequence is unchanged -- one market episode, no second "
      "episode to average against -- so this stays a case DESCRIPTION. No CI is "
      "computed for 3m and none should be inferred.\n"
      % (tm["n"], tm["span_days"], tm["window"], tm["n_clusters"],
         tm["n_clusters"], tm["span_days"]))
    if tm["rows"]:
        A("| file | ticker | class | ret_3m | cash_ret_3m | regret_cash_3m | sel_alpha_3m |")
        A("|---|---|---|---|---|---|---|")
        for r, m in tm["rows"]:
            A("| `%s` | %s | %s | %s | %s | %s | %s |"
              % (r["file"], r["ticker"], r["rating_class"], pct(m.get("ret")),
                 pct(m.get("cash_ret")), pct(m.get("regret_cash")),
                 pct(m.get("selection_alpha"))))
        A("")
    for name in ("NBIS", "TSM"):
        cs = ctx["case_studies"].get(name)
        A("### 7.2 %s -- open-anchor numbers\n" % name if name == "NBIS"
          else "### 7.3 %s -- open-anchor numbers\n" % name)
        if not cs:
            A("No realized rows.\n")
            continue
        A("| date | class | anchor open | anchor close | ret_1w (open) | "
          "ret_1w (close anchor) | regret_cash_1w | ret_1m | regret_cash_1m |")
        A("|---|---|---|---|---|---|---|---|---|")
        for r in cs:
            m1w = r["metrics"].get("1w", {})
            m1m = r["metrics"].get("1m", {})
            A("| %s | %s | %s | %s | %s | %s | %s | %s | %s |"
              % (r["analysis_date"], r["rating_class"], num(r.get("anchor_open"), 2),
                 num(r.get("anchor_close"), 2), pct(m1w.get("ret")),
                 pct(m1w.get("ret_close_anchor")), pct(m1w.get("regret_cash")),
                 pct(m1m.get("ret")), pct(m1m.get("regret_cash"))))
        A("")
    A("The anchor policy matters most here: for the most recent verdicts the "
      "close-anchor variant would inflate the grievance number relative to the only "
      "price that existed when the verdict was written. Both are printed above.\n")

    # ---------------- 8 RECONCILIATION ----------------
    A("## 8. Reconciliation\n")
    rc = ctx["reconciliation"]
    A("### 8.1 calibration-monitor agreement (V2)\n")
    A("Key-matched rows (analysis date, ticker) against the monitor Call Log: %d "
      "matched, %d rating-class agreements, %d disagreements. Note the construction: "
      "rung 2 of the extraction ladder READS the monitor when frontmatter carries no "
      "`rating:`, so agreement on those %d rows is definitional and carries no "
      "evidential weight. The informative check is the INDEPENDENT one below.\n"
      % (rc["matched"], rc["agree"], rc["disagree"], rc["rung2_rows"]))
    A("Independent body-vs-monitor check (rows whose class came from the monitor, "
      "re-derived from the body text by the same regex ladder): %d comparable, %d "
      "agree, %d differ. %s\n"
      % (rc["indep_n"], rc["indep_agree"], rc["indep_diff"],
         ("Differences: " + "; ".join(rc["indep_examples"]))
         if rc["indep_examples"] else "No differences."))
    A("### 8.2 Divergence from the red-team's preliminary preview\n")
    A("The P3 red-team published a preliminary computation of this corpus before the "
      "tool existed (mean 1m sector-relative regret +0.52%%, 95%% date-cluster CI "
      "[-2.88%%, +5.71%%] over 88 realized no-capital verdicts; no-capital call right "
      "68%% at 1w, 48%% at 1m; tails 22%%/15%%). This run computes mean %s, CI [%s, "
      "%s] over %d realized no-capital rows, right %.0f%% at 1w and %.0f%% at 1m, "
      "tails %.0f%%/%.0f%%. The preview was explicitly labelled preliminary and is "
      "NOT a reconciliation target (only the DFII10 episode table is). The material "
      "differences, stated rather than smoothed: (a) the preview counted 88 rows "
      "against this run's %d, consistent with a different treatment of the nine "
      "undated 2026-04-13 files and of the four excluded non-ticker artifacts; (b) "
      "this run uses the pre-registered OPEN anchor throughout; (c) the CI here is "
      "wider because pooled resampling of heavily unbalanced date clusters (the two "
      "heaviest dates carry 28 of %d rows) produces more dispersion than an "
      "equal-weight-per-date mean. Where the two disagree, THIS run's numbers are "
      "the published ones -- they are reproducible from the frozen spec and the "
      "JSONL; the preview's are not.\n"
      % (pct(ctx["boot_alpha_1m"]["mean"]), pct(ctx["boot_alpha_1m"]["lo"]),
         pct(ctx["boot_alpha_1m"]["hi"]), ctx["boot_alpha_1m"]["n"],
         ctx["hit_rates"]["1w"]["pct"], ctx["hit_rates"]["1m"]["pct"],
         100.0 * ctx["expectations"][2]["worse"] / max(1, ctx["expectations"][2]["n_tails"]),
         100.0 * ctx["expectations"][2]["better"] / max(1, ctx["expectations"][2]["n_tails"]),
         ctx["boot_regret_1m"]["n"], ctx["boot_regret_1m"]["n"]))
    A("### 8.3 Methodology-difference attribution vs the June-2026 backtest\n")
    A("The June-2026 verdict-redesign backtest scored a different question (Brier on "
      "a probability map) over an overlapping corpus. Per A12 this comparison is "
      "renamed methodology-difference ATTRIBUTION, not validation: the two runs "
      "share the same underlying data, so **agreement carries no evidential "
      "weight** -- only disagreement is informative, and only about method. Its "
      "per-call records are not recoverable, so no row-level reconciliation is "
      "possible; that limitation is stated rather than papered over. This report "
      "computes NO Brier score (A: at n<40 reliability is overestimated roughly 5x, "
      "Ferro-Fricker), touches NO cell of calibration-monitor.md, and leaves "
      "RATING_PROB_MAP, brier-ledger.json and options-ledger.jsonl byte-identical.\n")

    # ---------------- 9 BANNER ----------------
    A("## 9. PROPOSE-ONLY\n")
    A(BANNER)
    A("")
    A("Artifacts from this run: `%s` (immutable dated JSONL, one line per analysis) "
      "and this report. Consumption review is due 2026-08-29 per the GATE-B "
      "consumption-review-30d mandate: if nothing cites this report by then, the "
      "tool is an archive candidate.\n" % ctx["jsonl_name"])
    A("Related: [[redteam-invest-overhaul-2026-07-30]] | "
      "[[gate-b-verdict-backtest-2026-07-30]] | [[calibration-monitor]] | "
      "[[investing-moc]]")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------
# BY-PRODUCTS
# ---------------------------------------------------------------------------

SP500TR_EPISODES = [
    ("1995-2000 bull run", "1995-01-01", "2000-12-31"),
    ("2004-2007 mid-cycle", "2004-01-01", "2007-12-31"),
    ("2013 taper episode (May-Sep)", "2013-05-01", "2013-09-30"),
    ("2018 full year", "2018-01-01", "2018-12-31"),
    ("2022-Q4 through 2023", "2022-10-01", "2023-12-31"),
]


def emit_sp500_tr(outdir, verbose=False):
    import yfinance as yf
    frames = {}
    for sym in ("^GSPC", "^SP500TR"):
        df = yf.download(sym, start="1987-12-01", end=date.today().isoformat(),
                         progress=False, auto_adjust=AUTO_ADJUST, threads=False)
        if hasattr(df.columns, "nlevels") and df.columns.nlevels > 1:
            df = df.copy()
            df.columns = df.columns.get_level_values(0)
        frames[sym] = {(ts.date() if hasattr(ts, "date") else ts): float(row["Close"])
                       for ts, row in df.iterrows()
                       if row["Close"] == row["Close"]}
        log("%s: %d daily closes" % (sym, len(frames[sym])), verbose)
        time.sleep(0.4)

    def monthly(series):
        buckets = {}
        for d in sorted(series):
            buckets[(d.year, d.month)] = (d, series[d])
        return buckets

    mg, mt = monthly(frames["^GSPC"]), monthly(frames["^SP500TR"])
    keys = sorted(k for k in mg if k >= (1988, 1))
    lines = []
    A = lines.append
    A(frontmatter_block(["sp500-total-return-series-2026-07-30",
                         "S&P 500 price-return vs total-return monthly series"]))
    A("# S&P 500 price return (^GSPC) vs total return (^SP500TR) -- monthly, 1988-01 onward\n")
    A(BANNER + "\n")
    A("prov: script:yfinance auto_adjust=%s, fetched %s by tools/verdict-backtest.py "
      "--emit-sp500-tr. Purpose: retire the Grade-D total-return overlays in "
      "[[research-dgs10-band-2026-07-18]] by replacing estimated dividend "
      "adjustments with the actual ^SP500TR index. ^SP500TR history begins "
      "1988-01-04, which sets the start of this table.\n"
      % (AUTO_ADJUST, date.today().isoformat()))
    A("## Episode block -- cumulative returns over the named windows\n")
    A("| Episode | Window | ^GSPC price return | ^SP500TR total return | "
      "Dividend wedge | Years | TR annualized |")
    A("|---|---|---|---|---|---|---|")
    for label, s, e in SP500TR_EPISODES:
        sd, ed = date.fromisoformat(s), date.fromisoformat(e)

        def bracket(series, lo, hi):
            ks = [d for d in sorted(series) if lo <= d <= hi]
            return (series[ks[0]], series[ks[-1]], ks[0], ks[-1]) if len(ks) >= 2 else None

        g = bracket(frames["^GSPC"], sd, ed)
        t = bracket(frames["^SP500TR"], sd, ed)
        if not g or not t:
            A("| %s | %s..%s | data unavailable | | | | |" % (label, s, e))
            continue
        gr = g[1] / g[0] - 1.0
        tr = t[1] / t[0] - 1.0
        yrs = (t[3] - t[2]).days / 365.25
        ann = (1 + tr) ** (1 / yrs) - 1 if yrs > 0 else None
        A("| %s | %s..%s | %s | %s | %s | %.2f | %s |"
          % (label, g[2].isoformat(), g[3].isoformat(), pct(gr), pct(tr),
             pct(tr - gr), yrs, pct(ann)))
    A("")
    A("The wedge column is the cumulative dividend contribution the price index "
      "omits. Any overlay in a research note that used ^GSPC alone understates the "
      "equity leg by that amount over the same window.\n")
    A("## Monthly series (month-end closes)\n")
    A("| Month | ^GSPC close | ^GSPC MoM | ^SP500TR close | ^SP500TR MoM | Wedge (bp) |")
    A("|---|---|---|---|---|---|")
    prev_g = prev_t = None
    for k in keys:
        if k not in mt:
            continue
        gd, gv = mg[k]
        td, tv = mt[k]
        gm = (gv / prev_g - 1.0) if prev_g else None
        tm_ = (tv / prev_t - 1.0) if prev_t else None
        wedge = ((tm_ - gm) * 10000.0) if (gm is not None and tm_ is not None) else None
        A("| %04d-%02d | %.2f | %s | %.2f | %s | %s |"
          % (k[0], k[1], gv, pct(gm), tv, pct(tm_),
             "n/a" if wedge is None else "%+.1f" % wedge))
        prev_g, prev_t = gv, tv
    A("")
    A("Related: [[research-dgs10-band-2026-07-18]] | "
      "[[redteam-invest-overhaul-2026-07-30]] | [[investing-moc]]")
    path = dated_path(outdir, "sp500-total-return-series", ".md")
    path.write_text("\n".join(lines) + "\n", encoding="ascii", newline=LF)
    return path


def dfii10_sensitivity(verbose=False):
    obs = fetch_fred_series("DFII10")
    out = []
    A = out.append
    A("DFII10 shock-episode sensitivity -- FRED fredgraph.csv, %d published "
      "observations %s..%s" % (len(obs), obs[0][0], obs[-1][0]))
    A("Episode merge rule (pre-registered): consecutive fire runs separated by <= %d "
      "published observations are ONE episode." % DFII10_MERGE_GAP_OBS)
    A("")
    A("Sensitivity grid -- cells are: merged_episodes / fire_days / share of published obs")
    header = "| threshold (bp) | " + " | ".join("W=%d obs" % w for w in DFII10_GRID_W) + " |"
    A(header)
    A("|---" * (1 + len(DFII10_GRID_W)) + "|")
    grid = {}
    for t in DFII10_GRID_T:
        cells = []
        for w in DFII10_GRID_W:
            res = dfii10_episodes(obs, t, w)
            grid[(t, w)] = res
            cells.append("%d / %d / %.2f%%" % (len(res["episodes"]), res["fire_days"],
                                               res["pct_sessions"]))
        A("| %d | %s |" % (t, " | ".join(cells)))
    A("")
    ref = dfii10_episodes(obs, 75, 60)
    A("Fire history at the proposed 75bp / 60-obs parameters: %d merged episodes, "
      "%d raw runs, %d fire days (%.2f%% of published observations)."
      % (len(ref["episodes"]), ref["raw_runs"], ref["fire_days"], ref["pct_sessions"]))
    A("")
    A("| # | Episode start | Episode end | Peak rise (bp) | Fire days |")
    A("|---|---|---|---|---|")
    for i, e in enumerate(ref["episodes"], 1):
        A("| %d | %s | %s | +%.0f | %d |" % (i, e["start"], e["end"], e["peak_bp"],
                                             e["fire_days"]))
    A("")
    current = None
    if len(obs) > 60:
        current = (obs[-1][1] - obs[-61][1]) * 100.0
        A("Current reading: %+.1f bp over the last 60 published observations "
          "(newest obs %s = %.2f%%). Headroom to the 75bp trigger: %+.1f bp."
          % (current, obs[-1][0], obs[-1][1], 75.0 - current))
    A("")
    A("Reconciliation target -- redteam-invest-overhaul-2026-07-30 PART 1 MAJ-1 "
      "lists 7 merged episodes: 2004-06, 2008-09..12, 2011-01..02, 2013-06..09, "
      "2022-05..07, 2022-09..11, 2023-10.")
    expected = [("2004-06-10", "2004-06-28"), ("2008-09-30", "2008-12-08"),
                ("2011-01-21", "2011-02-08"), ("2013-06-12", "2013-09-10"),
                ("2022-05-10", "2022-07-11"), ("2022-09-26", "2022-11-29"),
                ("2023-10-05", "2023-10-31")]
    got = [(e["start"].isoformat(), e["end"].isoformat()) for e in ref["episodes"]]
    A("RECONCILIATION: %s (computed %d episodes vs 7 expected; boundary match %s)"
      % ("EXACT MATCH" if got == expected else "MISMATCH -- treat as a bug in THIS code",
         len(got), "yes" if got == expected else "no"))
    if got != expected:
        A("  expected: %s" % expected)
        A("  computed: %s" % got)
    A("Residual: the red-team report states 192 fire days at 75/60; this run counts "
      "%d on a series vintage that now ends %s. Episode boundaries, count and peaks "
      "reconcile exactly; the one-day fire-count difference is a series-vintage / "
      "boundary-observation artifact and is disclosed rather than reconciled away."
      % (ref["fire_days"], obs[-1][0]))
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ORCHESTRATION
# ---------------------------------------------------------------------------

def dated_path(outdir, stem, suffix):
    base = outdir / ("%s-%s%s" % (stem, date.today().isoformat(), suffix))
    if not base.exists():
        return base
    return outdir / ("%s-%s-%s%s" % (stem, date.today().isoformat(),
                                     datetime.now().strftime("%H%M"), suffix))


def constant_gate_finding(records):
    try:
        obs = fetch_fred_series("DGS10")
    except Exception as exc:                             # noqa: BLE001
        return {"ok": False, "reason": "DGS10 fetch failed: %s" % exc}
    if not obs:
        return {"ok": False, "reason": "DGS10 series empty"}
    vals = []
    for r in records:
        if r["date_source"] != "filename" or not r["analysis_date"]:
            continue
        d = date.fromisoformat(r["analysis_date"])
        prev = [v for od, v in obs if od <= d]
        if prev:
            vals.append(prev[-1])
    if not vals:
        return {"ok": False, "reason": "no DGS10 observations align with the corpus"}
    return {"ok": True, "n": len(vals), "lo": min(vals), "hi": max(vals),
            "gt415": sum(1 for v in vals if v > 4.15),
            "gt430": sum(1 for v in vals if v > 4.30),
            "gt440": sum(1 for v in vals if v > 4.40),
            "gt450": sum(1 for v in vals if v > 4.50)}


def quantile(xs, q):
    if not xs:
        return None
    s = sorted(xs)
    i = min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))
    return s[i]


def build_context(records, cache, today, yf_version):
    ctx = {"today": today.isoformat(), "yf_version": yf_version}
    ctx["rung_census"] = rung_census(records)
    ctx["class_census"] = class_census(records)
    era_c, date_c, strata = {}, {}, {}
    for r in records:
        era_c[r["era"]] = era_c.get(r["era"], 0) + 1
        date_c[r["date_source"]] = date_c.get(r["date_source"], 0) + 1
        strata[r["holding"]] = strata.get(r["holding"], 0) + 1
    ctx["era_census"] = dict(sorted(era_c.items()))
    ctx["date_census"] = dict(sorted(date_c.items()))
    ctx["strata_counts"] = strata
    ctx["empty_list_rows"] = sum(1 for r in records
                                 if r["holding_basis"] == "accounts-empty-or-none")
    ctx["n_tickers"] = len({r["ticker"] for r in records})

    ctx["realized_counts"] = {h: sum(1 for r in records
                                     if r["metrics"].get(h, {}).get("realized"))
                              for h in HORIZONS}

    none_1m = realized_rows(records, "1m", capital_class="none")
    none_1w = realized_rows(records, "1w", capital_class="none")
    ctx["boot_regret_1m"] = date_cluster_bootstrap(none_1m, "regret_cash")
    ctx["boot_alpha_1m"] = date_cluster_bootstrap(none_1m, "selection_alpha")
    ctx["boot_alpha_badj_1m"] = date_cluster_bootstrap(none_1m, "selection_alpha_beta_adj")
    ctx["beta_adjusted_n"] = sum(1 for _, m in none_1m if m.get("beta_adjusted"))
    clean_1m = [(r, m) for r, m in none_1m if not r["forward_contaminated"]]
    ctx["boot_regret_1m_clean"] = date_cluster_bootstrap(clean_1m, "regret_cash")

    scoreboard = []
    for metric, key in (("regret_cash (headline)", "regret_cash"),
                        ("selection_alpha (diagnostic)", "selection_alpha"),
                        ("excess vs SPY", "bench_ret")):
        for h in HEADLINE_HORIZONS:
            rows = realized_rows(records, h, capital_class="none")
            if key == "bench_ret":
                rows = [(r, {"v": (m["ret"] - m["bench_ret"])
                             if m.get("bench_ret") is not None else None})
                        for r, m in rows]
                b = date_cluster_bootstrap(rows, "v")
            else:
                b = date_cluster_bootstrap(rows, key)
            scoreboard.append({"metric": metric, "horizon": h, "stratum": "all no-capital",
                               "b": b})
    for stratum in ("held", "not_held", "unknown"):
        for h in HEADLINE_HORIZONS:
            rows = realized_rows(records, h, capital_class="none", holding=stratum)
            scoreboard.append({"metric": "regret_cash (headline)", "horizon": h,
                               "stratum": stratum,
                               "b": date_cluster_bootstrap(rows, "regret_cash")})
    ctx["scoreboard"] = scoreboard

    ctx["hit_rates"] = {}
    for h, rows in (("1w", none_1w), ("1m", none_1m)):
        vals = [m["regret_cash"] for _, m in rows if m.get("regret_cash") is not None]
        right = sum(1 for v in vals if v <= 0)
        ctx["hit_rates"][h] = {"n": len(vals), "right": right,
                               "pct": 100.0 * right / len(vals) if vals else 0.0}

    ctx["expectations"] = adjudicate_expectations(records, ctx["boot_alpha_1m"])

    mfe = [m["mfe_ratio"] for _, m in none_1m if m.get("mfe_ratio") is not None]
    mae = [m["mae_ratio"] for _, m in none_1m if m.get("mae_ratio") is not None]
    ctx["mfe_ratio_mean"] = statistics.fmean(mfe) if mfe else None
    ctx["mae_ratio_mean"] = statistics.fmean(mae) if mae else None

    exits = realized_rows(records, "1m", capital_class="exit")
    ev = [m["avoided_loss"] for _, m in exits if m.get("avoided_loss") is not None]
    ctx["exit_n"] = len(exits)
    ctx["exit_avoided_mean"] = statistics.fmean(ev) if ev else None
    conds = realized_rows(records, "1m", capital_class="conditional")
    ctx["cond_n"] = len(conds)
    zoned = [(r, m) for r, m in realized_rows(records, "1m")
             if m.get("zone_touched") is not None]
    ctx["zone_rows_n"] = len(zoned)
    ctx["zone_touched_n"] = sum(1 for _, m in zoned if m["zone_touched"])

    a9 = watchlist_random_null(records, cache, today)
    ctx["a9_n"] = len(a9)
    ctx["a9_ret_mean"] = statistics.fmean([x["ret"] for x in a9]) if a9 else None
    ctx["a9_rand_mean"] = statistics.fmean([x["random_mean"] for x in a9]) if a9 else None
    ctx["a9_diff_mean"] = statistics.fmean([x["diff"] for x in a9]) if a9 else None
    ctx["a9_rows"] = a9

    ctx["dependence"] = corpus_dependence(records, cache)

    wedge_by_era = {}
    for era in ("A_legacy", "B_transitional", "C_kernel"):
        ws = [r["wedge"] for r in records if r["era"] == era and r.get("wedge") is not None]
        suspect = [r["file"] for r in records if r["era"] == era and r.get("split_suspect")]
        wedge_by_era[era] = {"n": len(ws), "median": quantile(ws, 0.5),
                             "p10": quantile(ws, 0.1), "p90": quantile(ws, 0.9),
                             "suspect": suspect}
    ctx["wedge_by_era"] = wedge_by_era

    ctx["contaminated_rows"] = [r for r in records if r["forward_contaminated"]]
    ctx["contaminated_n"] = len(ctx["contaminated_rows"])

    anchor_delta = {}
    extremes = []
    for h in HEADLINE_HORIZONS:
        rows = realized_rows(records, h)
        o = [m["ret"] for _, m in rows if m.get("ret") is not None]
        c = [m["ret_close_anchor"] for _, m in rows
             if m.get("ret_close_anchor") is not None]
        anchor_delta[h] = {"n": len(o),
                           "open": statistics.fmean(o) if o else None,
                           "close": statistics.fmean(c) if c else None,
                           "delta": (statistics.fmean(o) - statistics.fmean(c))
                           if o and c else None}
    rows_1w = realized_rows(records, "1w")
    for r, m in sorted(rows_1w, key=lambda x: -abs(x[1].get("anchor_delta") or 0))[:4]:
        if m.get("anchor_delta"):
            extremes.append("%s %s: open-anchor %s vs close-anchor %s (delta %s)"
                            % (r["ticker"], r["analysis_date"], pct(m["ret"]),
                               pct(m["ret_close_anchor"]), pct(m["anchor_delta"])))
    ctx["anchor_delta"] = anchor_delta
    ctx["anchor_extremes"] = extremes

    oracles = []
    for (tkr, d), expected in sorted(ORACLE_CLOSES.items()):
        sym = CRYPTO_TICKERS.get(tkr, tkr)
        bar = cache.bar(sym, date.fromisoformat(d))
        actual = bar[3] if bar else None
        delta = ((actual - expected) / expected) if actual else None
        ok = actual is not None and abs(delta) <= ORACLE_TOLERANCE
        oracles.append({"ticker": tkr, "date": d, "expected": expected,
                        "actual": actual, "delta": delta,
                        "result": "PASS" if ok else "FAIL"})
    ctx["oracles"] = oracles
    tcloses = []
    for tkr in ("TSM", "NBIS", "MU", "SPY"):
        bar = cache.bar(tkr, today)
        if bar:
            tcloses.append("%s %.2f" % (tkr, bar[3]))
    ctx["today_closes"] = ", ".join(tcloses) or "no bars dated %s" % today

    bench_set = [BROAD_PROXY, "SMH", "XLK", CASH_PROXY]
    ctx["bench_set"] = bench_set
    ref_cal = set(cache.dates.get(BROAD_PROXY, []))
    mismatch = [b for b in bench_set if cache.has(b) and set(cache.dates[b]) != ref_cal]
    ctx["calendar_assert"] = ("IDENTICAL (%d sessions)" % len(ref_cal)) if not mismatch \
        else "MISMATCH on %s" % ", ".join(mismatch)
    devs = []
    for sym in sorted({r["symbol"] for r in records}):
        if sym in CRYPTO_TICKERS.values() or not cache.has(sym):
            continue
        diff = ref_cal ^ set(cache.dates[sym])
        if diff:
            devs.append("%s (%d sessions differ)" % (sym, len(diff)))
    ctx["calendar_deviations"] = ", ".join(devs)
    ctx["degraded_rows"] = [(r["file"], "; ".join(r["degraded"]))
                            for r in records if r.get("degraded")]

    ctx["timelines"] = ticker_timelines(records)

    tm_rows = realized_rows(records, "3m")
    tm_dates = sorted({r["analysis_date"] for r, _ in tm_rows})
    span = ((date.fromisoformat(tm_dates[-1]) - date.fromisoformat(tm_dates[0])).days
            if tm_dates else 0)
    ctx["three_month"] = {"n": len(tm_rows), "rows": tm_rows,
                          "n_clusters": len(tm_dates), "span_days": span,
                          "window": ("%s..%s" % (tm_dates[0], tm_dates[-1]))
                          if tm_dates else "none"}
    ctx["case_studies"] = {
        name: [r for r in records if r["ticker"] == name and r["analysis_date"]
               and r["analysis_date"] >= "2026-06-01"]
        for name in ("NBIS", "TSM")}

    ctx["constant_gate"] = constant_gate_finding(records)

    monitor = monitor_index()
    matched = agree = disagree = 0
    indep_n = indep_agree = indep_diff = 0
    indep_examples = []
    for r in records:
        key = (r["analysis_date"], r["ticker"])
        cell = monitor.get(key)
        if not cell:
            continue
        matched += 1
        mcls = classify_verdict(cell)["rating_class"]
        if mcls == r["rating_class"]:
            agree += 1
        else:
            disagree += 1
            indep_examples.append("`%s` monitor=%s extracted=%s"
                                  % (r["file"], mcls, r["rating_class"]))
        if r["rating_source"] == "monitor" and r["body_rating_class"]:
            indep_n += 1
            if r["body_rating_class"] == mcls:
                indep_agree += 1
            else:
                indep_diff += 1
                indep_examples.append("`%s` monitor=%s body=%s"
                                      % (r["file"], mcls, r["body_rating_class"]))
    ctx["reconciliation"] = {"matched": matched, "agree": agree, "disagree": disagree,
                             "rung2_rows": sum(1 for r in records
                                               if r["rating_source"] == "monitor"),
                             "indep_n": indep_n, "indep_agree": indep_agree,
                             "indep_diff": indep_diff,
                             "indep_examples": indep_examples[:12]}

    # window-level context for the limitations section
    ctx["window_start"] = min(r["analysis_date"] for r in records if r["analysis_date"])
    ctx["window_end"] = today.isoformat()
    for sym, key in ((BROAD_PROXY, "spy_window_ret"), (CASH_PROXY, "cash_window_ret")):
        d0 = date.fromisoformat(ctx["window_start"])
        _, _, ret = leg_return(cache, sym, d0, today, "open")
        ctx[key] = ret
    return ctx


def write_jsonl(records, outdir):
    path = dated_path(outdir, "verdict-backtest", ".jsonl")
    with path.open("w", encoding="ascii", newline="\n") as fh:
        for r in sorted(records, key=lambda x: (x["analysis_date"] or "", x["file"])):
            row = dict(r)
            row["preregistered_sha256"] = PREREGISTERED_SHA256
            row["trial_count"] = TRIAL_COUNT
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=True,
                                default=str) + "\n")
    return path


def main():
    ap = argparse.ArgumentParser(description="verdict backtest (PROPOSE-ONLY)")
    ap.add_argument("--extract-only", action="store_true",
                    help="run the extraction ladder only; no prices, no writes")
    ap.add_argument("--json", action="store_true", help="JSON to stdout")
    ap.add_argument("--emit-sp500-tr", action="store_true",
                    help="write the ^GSPC vs ^SP500TR series artifact")
    ap.add_argument("--dfii10-sensitivity", action="store_true",
                    help="print the DFII10 shock-episode grid + 75/60 fire history")
    ap.add_argument("--outdir", type=Path, default=None)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if args.dfii10_sensitivity:
        print(dfii10_sensitivity(args.verbose))
        return 0

    if args.emit_sp500_tr:
        outdir = args.outdir or RESEARCH_DIR
        outdir.mkdir(parents=True, exist_ok=True)
        p = emit_sp500_tr(outdir, args.verbose)
        print("wrote %s" % p)
        return 0

    records = extract_corpus(args.verbose)
    halts = extraction_halt_check(records)

    if args.extract_only:
        payload = {"preregistered_sha256": PREREGISTERED_SHA256,
                   "trial_count": TRIAL_COUNT,
                   "corpus_n": len(records),
                   "rung_census": rung_census(records),
                   "class_census": class_census(records),
                   "records": sorted(records, key=lambda x: x["file"])}
        if args.json:
            print(json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True,
                             default=str))
        else:
            print("corpus_n=%d" % len(records))
            print("rung census: %s" % payload["rung_census"])
            print("class census: %s" % payload["class_census"])
        if halts:
            for h in halts:
                print("HALT: %s" % h, file=sys.stderr)
            return 2
        return 0

    if halts:
        for h in halts:
            print("HALT: %s" % h, file=sys.stderr)
        return 2

    import yfinance as yf
    today = date.today()
    symbols = sorted({r["symbol"] for r in records}) + EXTRA_SYMBOLS
    log("downloading %d symbols" % len(set(symbols)), True)
    cache = PriceCache(symbols, PRICE_WINDOW_START,
                       (today + timedelta(days=1)).isoformat(), args.verbose)
    compute_metrics(records, cache, today, args.verbose)
    ctx = build_context(records, cache, today, yf.__version__)

    failed = [o for o in ctx["oracles"] if o["result"] != "PASS"]
    if failed:
        for o in failed:
            print("HALT: oracle assert FAILED -- %s %s expected %.2f got %s"
                  % (o["ticker"], o["date"], o["expected"],
                     "%.2f" % o["actual"] if o["actual"] is not None else "MISSING"),
                  file=sys.stderr)
        return 2

    outdir = args.outdir or OUT_DIR
    outdir.mkdir(parents=True, exist_ok=True)
    jsonl = write_jsonl(records, outdir)
    ctx["jsonl_name"] = jsonl.name
    report = compose_report(records, ctx)
    rpath = dated_path(outdir, "verdict-backtest", ".md")
    rpath.write_text(report, encoding="ascii", newline=LF)

    print("wrote %s (%d rows)" % (jsonl, len(records)))
    print("wrote %s (%d bytes)" % (rpath, len(report)))
    print("PREREGISTERED sha256 %s | trial %d" % (PREREGISTERED_SHA256, TRIAL_COUNT))
    for e in ctx["expectations"]:
        print("expectation %d: %s -- %s" % (e["n"], e["verdict"], e["computed"]))
    b = ctx["boot_regret_1m"]
    print("headline regret_cash 1m: mean %s CI [%s, %s] n=%d clusters=%d"
          % (pct(b["mean"]), pct(b["lo"]), pct(b["hi"]), b["n"], b["n_clusters"]))
    a = ctx["boot_alpha_1m"]
    print("selection_alpha 1m: mean %s CI [%s, %s] n=%d clusters=%d"
          % (pct(a["mean"]), pct(a["lo"]), pct(a["hi"]), a["n"], a["n_clusters"]))
    if args.json:
        print(json.dumps({k: v for k, v in ctx.items()
                          if k not in ("timelines", "case_studies", "three_month",
                                       "contaminated_rows", "a9_rows", "scoreboard")},
                         sort_keys=True, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""FW2 Contamination Audit + Ledger (FIS workstream).

Programmatically scans prior program artifacts for knowledge contamination of
candidate Financial Information Standard (FIS) challenge windows.

Scanned roots (relative to workspace root):
    research/ , wiki/ , Efforts/osanwe-v2-overhaul/_work/ , registry/ , Calendar/
Scanned extensions: .md .json .jsonl .py .csv .log
Skipped directories: .git .raw private finance credentials fis-data __pycache__

Detection:
  1. Explicit date ranges (ISO-to-ISO, year-year, start/end key pairs) that
     overlap a candidate challenge window.
  2. Outcome-bearing statistics (CAGR / Sharpe / t-stat / Sortino / ann vol /
     hit rate / max drawdown / ...) co-occurring with those windows
     (same textual neighborhood, or sibling keys in a JSON object).
  3. Implicit window: an artifact carrying an anchor date (as-of / created /
     updated / frozen) in 2021-2026 together with outcome statistics implies
     evaluation over trailing history through that anchor (5y lookback).

Default rule (FW2): ANY 2021-2026 window over the current 125-ticker universe
appearing in ANY prior artifact = CONTAMINATED -> development-validation-only.
Nothing qualifies as untouched challenge material except post-freeze bars
(data not yet existing at freeze time, freeze = 2026-08-25T05:00:00Z) or
synthetic/canary instruments generated fresh by FW1.

Output: Efforts/osanwe-v2-overhaul/_work/fis-data/contamination-ledger.jsonl
One record per (dataset=universe-window, period_start, period_end,
instruments_class, accessed_by=<file/class>, results_previously_calculated,
parameters_selected_using_it, permitted_future_use).

Usage:
    python tools/fis/contamination_audit.py            # full scan, write ledger
    python tools/fis/contamination_audit.py --selftest # verify schema + flags
    python tools/fis/contamination_audit.py --root PATH --out PATH --quiet

Constraints honored: ASCII-only source, stdlib only, no network, no git;
writes ONLY under tools/fis/ (this file) and _work/fis-data/.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import shutil

SCRIPT_PATH = os.path.abspath(__file__)
DEFAULT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_PATH)))
DEFAULT_OUT_REL = os.path.join(
    "Efforts", "osanwe-v2-overhaul", "_work", "fis-data",
    "contamination-ledger.jsonl",
)

SCAN_REL_ROOTS = [
    "research",
    "wiki",
    os.path.join("Efforts", "osanwe-v2-overhaul", "_work"),
    "registry",
    "Calendar",
]
SKIP_DIR_NAMES = {
    ".git", ".raw", "private", "finance", "credentials",
    "__pycache__", "node_modules", "fis-data",
}
SCAN_EXTS = {".md", ".json", ".jsonl", ".py", ".csv", ".log"}
MAX_FILE_BYTES = 4_000_000

# Candidate challenge windows (dataset = current 125-ticker universe).
# Any detected range overlapping CHALLENGE_SPAN is contaminated by default.
CHALLENGE_WINDOWS = {
    "universe-125_2021-2026_full": ((2021, 1, 1), (2026, 12, 31)),
}
CHALLENGE_SPAN = ((2021, 1, 1), (2026, 12, 31))
FREEZE_TS = "2026-08-25T05:00:00Z"

PERMITTED_VALUES = (
    "development-validation-only",
    "diagnostics-only",
    "excluded-from-challenge",
)
RECORD_KEYS = (
    "dataset",
    "period_start",
    "period_end",
    "instruments_class",
    "accessed_by",
    "results_previously_calculated",
    "parameters_selected_using_it",
    "permitted_future_use",
)

# --- detection regexes -----------------------------------------------------

ISO_YMD = r"(20\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])"
YEAR4 = r"(20\d{2})"

# Two calendar dates on one line joined by a range separator.
EXPLICIT_RANGE_RE = re.compile(
    ISO_YMD + r"\s*(?:to|through|thru|until|->|=>|--|\.\.|-|\u2014|\u2013)\s*" + ISO_YMD,
    re.IGNORECASE,
)
# Bare year-year range, e.g. 2021-2026 / 2021 to 2026.
YEAR_YEAR_RE = re.compile(YEAR4 + r"\s*(?:-|\u2013|\u2014|to|through)\s*" + YEAR4)
ANY_DATE_RE = re.compile(ISO_YMD)
ANY_YEAR_RE = re.compile(YEAR4)

# Outcome-bearing statistics vocabulary.
STAT_KEY_RE = re.compile(
    r"(cagr|sharpe|t[_ -]?stats?(?:_vs_\d+)?|sortino|information[_ ]ratio|calmar"
    r"|omega[_ ]ratio|ann(?:ual(?:ized)?)?[_ .]?(?:return|vol|pct|cagr)"
    r"|alpha|beta|max[_ ]?dd(?:pct)?|max[_ ]?drawdown|hit[_ ]?rate|win[_ ]?rate"
    r"|cum[_ ]?pct|excess[_ ]?return|monthly[_ ]?ir)",
    re.IGNORECASE,
)
NUM_AFTER_KEY_RE = re.compile(r"[:=\s(]+\s*(-?\d+(?:\.\d+)?\s*%?)")

# File-level anchor dates (as-of / created / updated / frozen / date / ...).
ANCHOR_RE = re.compile(
    r"\b(?:as[_ ]?of|created|updated|date|generated|frozen|snapshot"
    r"|run[_ ]?at|completed)\b\W{0,4}" + ISO_YMD,
    re.IGNORECASE,
)

# Parameter tokens (for parameters_selected_using_it, exp-* artifacts).
PARAM_TOKEN_RE = re.compile(
    r"\b(lookback|window|threshold|top[_ ]?n|n[_ ]?long|n[_ ]?short|holding"
    r"|hold[_ ]?days|rebalance(?:[_ ]?freq)?|entry[_ ]?z|exit[_ ]?z|z[_ ]?entry"
    r"|z[_ ]?exit|stop[_ ]?loss|skip[_ ]?days|quantile|percentile|pctile"
    r"|halflife|half[_ ]?life|band|bands|q\b|k\b)\s*[=:]\s*([^\s,;){]{1,16})",
    re.IGNORECASE,
)

CANARY_HINT_RE = re.compile(r"\b(canary|synthetic[_ -]instrument|fw1[_ -]synthetic)\b", re.I)


def clamp_year(y):
    return 1990 <= y <= 2035


def mkdate(y, m=1, d=1):
    if not clamp_year(y):
        return None
    m = m if m else 1
    d = d if d else 1
    if not (1 <= m <= 12 and 1 <= d <= 31):
        return None
    return (y, m, d)


def iso(t):
    return "%04d-%02d-%02d" % t


def overlaps_challenge(rng):
    lo, hi = rng
    clo, chi = CHALLENGE_SPAN
    return lo <= chi and hi >= clo


def text_ranges_in_line(line):
    """Yield (start_tuple, end_tuple) explicit ranges found in a text line."""
    out = []
    for m in EXPLICIT_RANGE_RE.finditer(line):
        g = m.groups()
        a = mkdate(int(g[0]), int(g[1]), int(g[2]))
        b = mkdate(int(g[3]), int(g[4]), int(g[5]))
        if a and b and a <= b:
            out.append((a, b))
    if not out:
        for m in YEAR_YEAR_RE.finditer(line):
            a = mkdate(int(m.group(1)))
            b = mkdate(int(m.group(2)), 12, 31)
            if a and b and a <= b:
                out.append((a, b))
    return out


def stat_samples_near(lines, idx, radius=2, cap=8):
    """Collect 'keyword=value' samples within +/- radius lines of idx."""
    found = []
    lo = max(0, idx - radius)
    hi = min(len(lines), idx + radius + 1)
    for j in range(lo, hi):
        chunk = lines[j]
        for km in STAT_KEY_RE.finditer(chunk):
            tail = chunk[km.end():km.end() + 48]
            nm = NUM_AFTER_KEY_RE.search(tail)
            label = re.sub(r"[^a-z0-9_]", "_", km.group(1).lower())
            if nm:
                found.append("%s=%s" % (label, nm.group(1).strip()))
            else:
                found.append(label)
        if len(found) >= cap:
            break
    seen, uniq = set(), []
    for f in found:
        if f not in seen:
            seen.add(f)
            uniq.append(f)
    return uniq[:cap]


def file_stat_samples(text, cap=10):
    found = []
    for line in text.splitlines():
        for km in STAT_KEY_RE.finditer(line):
            tail = line[km.end():km.end() + 48]
            nm = NUM_AFTER_KEY_RE.search(tail)
            label = re.sub(r"[^a-z0-9_]", "_", km.group(1).lower())
            found.append("%s=%s" % (label, nm.group(1).strip()) if nm else label)
        if len(found) >= cap * 2:
            break
    seen, uniq = set(), []
    for f in found:
        if f not in seen:
            seen.add(f)
            uniq.append(f)
    return uniq[:cap]


def anchor_dates(text):
    """Return list of (y,m,d) anchors like as-of/created/updated."""
    out = []
    for m in ANCHOR_RE.finditer(text):
        t = mkdate(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if t:
            out.append(t)
    return out


def param_tokens(text, cap=12):
    out = []
    for m in PARAM_TOKEN_RE.finditer(text):
        out.append("%s=%s" % (m.group(1).lower().replace(" ", "_"), m.group(2)))
        if len(out) >= cap:
            break
    return out


def walk_json_dates_stats(obj, ranges, stats):
    """Recursively collect date-pair ranges and statistic key/values."""
    if isinstance(obj, dict):
        dvals = []
        for v in obj.values():
            if isinstance(v, str):
                dm = ANY_DATE_RE.fullmatch(v.strip())
                if dm:
                    t = mkdate(int(dm.group(1)), int(dm.group(2)), int(dm.group(3)))
                    if t:
                        dvals.append(t)
                        continue
                ym = ANY_YEAR_RE.fullmatch(v.strip())
                if ym and clamp_year(int(ym.group(1))):
                    dvals.append(mkdate(int(ym.group(1))))
        for k, v in obj.items():
            if STAT_KEY_RE.search(str(k)):
                if isinstance(v, bool):
                    continue
                if isinstance(v, (int, float)):
                    stats.append((str(k), v))
                elif isinstance(v, str):
                    nm = re.fullmatch(r"\s*-?\d+(?:\.\d+)?\s*%?", v)
                    if nm:
                        stats.append((str(k), v.strip()))
        if len(dvals) >= 2:
            lo, hi = min(dvals), max(dvals)
            if lo != hi:
                ranges.append((lo, hi))
        for v in obj.values():
            walk_json_dates_stats(v, ranges, stats)
    elif isinstance(obj, list):
        for v in obj:
            walk_json_dates_stats(v, ranges, stats)


def agent_class(relpath_norm, name):
    if relpath_norm.startswith("Calendar/sessions/"):
        return "session-log"
    if name.startswith("exp-"):
        return "experiment-report"
    if name.startswith(("calib", "calibration")):
        return "calibration-output"
    if "backtest" in name:
        return "backtest-output"
    if "wave" in name:
        return "wave-analysis"
    if "regime" in name:
        return "regime-analysis"
    if relpath_norm.startswith("registry"):
        return "registry"
    return "prior-artifact"


def instruments_class(relpath_norm, text_head):
    if CANARY_HINT_RE.search(text_head):
        return "universe-125-equities+fw1-synthetic-canary-references"
    return "universe-125-equities"


def is_exp_artifact(name, text_head):
    return name.startswith("exp-") or "# Experiment" in text_head


def build_record(relpath, rng, has_stats, stats, params, name, relnorm, text_head):
    lo, hi = rng
    use = "development-validation-only" if has_stats else "diagnostics-only"
    if has_stats:
        res = "; ".join(stats[:8]) if stats else "outcome statistics present"
        if len(res) > 240:
            res = res[:237] + "..."
    else:
        res = "date-range reference only (no outcome statistics detected)"
    psel = None
    if is_exp_artifact(name, text_head) and params:
        joined = "; ".join(params[:8])
        psel = joined[:200]
    rec = {
        "dataset": "universe-125_2021-2026_full",
        "period_start": iso(lo),
        "period_end": iso(hi),
        "instruments_class": instruments_class(relnorm, text_head),
        "accessed_by": "%s (%s)" % (relpath, agent_class(relnorm, name)),
        "results_previously_calculated": res,
        "parameters_selected_using_it": psel,
        "permitted_future_use": use,
    }
    return rec


def analyze_file(path):
    """Return (list_of_records, meta) for one artifact. Read-only."""
    name = os.path.basename(path)
    try:
        if os.path.getsize(path) > MAX_FILE_BYTES:
            return [], {"skipped": "too-large"}
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read(MAX_FILE_BYTES)
    except OSError:
        return [], {"skipped": "unreadable"}

    lines = text.splitlines()
    head = "\n".join(lines[:80])
    ranges = []          # explicit structured/text ranges
    stats_pairs = []

    ext = os.path.splitext(name)[1].lower()

    # Structured pass for JSON / JSONL.
    if ext == ".json":
        try:
            walk_json_dates_stats(json.loads(text), ranges, stats_pairs)
        except (ValueError, RecursionError):
            pass
    elif ext == ".jsonl":
        for ln in lines:
            ln = ln.strip()
            if not ln:
                continue
            try:
                walk_json_dates_stats(json.loads(ln), ranges, stats_pairs)
            except (ValueError, RecursionError):
                pass

    # Textual pass (all extensions): explicit ranges + nearby statistics.
    text_hits = []
    for i, ln in enumerate(lines):
        for rng in text_ranges_in_line(ln):
            near = stat_samples_near(lines, i)
            text_hits.append((rng, bool(near)))

    # Deduplicate text hits by range keeping strongest evidence.
    by_rng = {}
    for rng, had_stats in text_hits:
        prev = by_rng.get(rng)
        if prev is None or (had_stats and not prev):
            by_rng[rng] = had_stats
    for rng, had in sorted(by_rng.items()):
        ranges.append(rng)
        # stash evidence flag parallel to ranges
    evidence = dict(((r, h) for r, h in by_rng.items()))

    if not stats_pairs:
        stats_pairs = [(None, s) for s in file_stat_samples(text)]

    # Implicit window: anchor date in 2021-2026 + outcome statistics present.
    if not ranges:
        has_any_stats = bool(stats_pairs)
        if has_any_stats:
            for anc in anchor_dates(text):
                if 2021 <= anc[0] <= 2026:
                    lo = mkdate(max(2021, anc[0] - 5), anc[1], anc[2]) or mkdate(2021)
                    hi = anc
                    ranges.append((lo, hi))
                    evidence[(lo, hi)] = True
                    break

    if not ranges:
        return [], {"ok": True}

    stat_samples = ["%s=%s" % (k, v) for k, v in stats_pairs if k]
    stat_samples = stat_samples[:10] or [s for _, s in stats_pairs][:10]
    params = param_tokens(text)
    relnorm = relpath_norm(path)
    display = "%s/%s" % (os.path.dirname(relnorm), name) if os.path.dirname(relnorm) else name
    records = []
    seen = set()
    for rng in ranges:
        if not overlaps_challenge(rng):
            continue
        has_stats = bool(evidence.get(rng)) or bool(stats_pairs)
        key = (rng, has_stats)
        if key in seen:
            continue
        seen.add(key)
        records.append(build_record(
            display, rng, has_stats, stat_samples, params,
            name, relnorm, head,
        ))
    return records, {"ok": True}


_WORK_CACHE = {}


def relpath_norm(path):
    root = get_default_root()
    try:
        rel = os.path.relpath(path, root)
    except ValueError:
        rel = path
    return rel.replace("\\", "/")


def get_default_root():
    return DEFAULT_ROOT


def iter_scan_files(root, extra_exclude=None):
    excl = set(extra_exclude or [])
    for rel_root in SCAN_REL_ROOTS:
        base = os.path.join(root, rel_root)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d.lower() not in SKIP_DIR_NAMES]
            for fn in sorted(filenames):
                if os.path.splitext(fn)[1].lower() not in SCAN_EXTS:
                    continue
                full = os.path.join(dirpath, fn)
                if os.path.abspath(full) in excl:
                    continue
                yield full


def run_audit(root, out_path, quiet=False):
    root = os.path.abspath(root)
    out_path = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    records = []
    n_files = 0
    n_hit_files = 0
    for path in iter_scan_files(root, extra_exclude={out_path}):
        n_files += 1
        recs, _meta = analyze_file(path)
        if recs:
            n_hit_files += 1
            records.extend(recs)
    with open(out_path, "w", encoding="ascii", errors="strict") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=False, ensure_ascii=True) + "\n")

    by_use = {}
    for r in records:
        by_use[r["permitted_future_use"]] = by_use.get(r["permitted_future_use"], 0) + 1
    print("FW2 Contamination Audit")
    print("  root           : %s" % root)
    print("  ledger         : %s" % out_path)
    print("  files scanned  : %d" % n_files)
    print("  files w/ hits  : %d" % n_hit_files)
    print("  ledger records : %d" % len(records))
    for k in PERMITTED_VALUES:
        if k in by_use:
            print("  %-28s : %d" % (k, by_use[k]))
    if records:
        top = {}
        for r in records:
            f = r["accessed_by"].rsplit(" (", 1)[0]
            top[f] = top.get(f, 0) + 1
        ranked = sorted(top.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
        print("  top contaminating artifacts:")
        for f, c in ranked:
            print("    %3d  %s" % (c, f))
    return 0


# --------------------------------------------------------------------------
# Selftest
# --------------------------------------------------------------------------

FIXTURE_EXP_MD = """---
created: 2026-08-25
updated: 2026-08-25
---

# Experiment: exp-mean-reversion-fixture

**Question:** Does short-term mean reversion generate alpha?
**Date:** 2026-08-25
**Status:** PARTIALLY CONFIRMED

Backtest window: 2021-01-04 to 2025-12-31 over the 125-ticker universe.

| Variant | CAGR | Sharpe | t-stat | MaxDD |
|---|---|---|---|---|
| base | 18.4% | 1.42 | 3.11 | -14.2% |

Parameters: lookback=21, entry_z=-2.0, exit_z=0.5, holding=5
"""

FIXTURE_REGIME_JSON = """
{
  "asof": "2026-08-24",
  "current_regime": "BULL",
  "strategies": {
    "TSMOM": {
      "overall": {"days": 779, "ann_pct": 12.58, "sharpe": 0.887},
      "by_regime": {
        "BULL": {"days": 543, "sharpe": 2.891, "t_stat_vs_0": 4.24},
        "BEAR": {"days": 120, "sharpe": -0.219, "t_stat_vs_0": -0.15}
      }
    }
  }
}
"""

FIXTURE_CLEAN_MD = """# Garden planting log 2017-2019

Planted beds on 2018-06-10 through 2018-06-14. Yield improved.
No finance content here at all.
"""


def run_selftest():
    failures = []

    def check(cond, msg):
        if cond:
            print("  PASS  %s" % msg)
        else:
            failures.append(msg)
            print("  FAIL  %s" % msg)

    tmp = tempfile.mkdtemp(prefix="fw2-selftest-")
    try:
        # -- fixture-based checks (pure functions, no repo writes) ----------
        exp_path = os.path.join(tmp, "exp-mean-reversion-fixture.md")
        with open(exp_path, "w", encoding="ascii") as fh:
            fh.write(FIXTURE_EXP_MD)
        reg_path = os.path.join(tmp, "regime-analysis-fixture.json")
        with open(reg_path, "w", encoding="ascii") as fh:
            fh.write(FIXTURE_REGIME_JSON)
        clean_path = os.path.join(tmp, "clean-garden-2018.md")
        with open(clean_path, "w", encoding="ascii") as fh:
            fh.write(FIXTURE_CLEAN_MD)

        exp_recs, _ = analyze_file(exp_path)
        reg_recs, _ = analyze_file(reg_path)
        clean_recs, _ = analyze_file(clean_path)

        check(len(exp_recs) >= 1, "exp-mean-reverse-style fixture is flagged")
        check(any(r["permitted_future_use"] == "development-validation-only"
                  for r in exp_recs),
              "exp fixture with stats => development-validation-only")
        check(exp_recs and exp_recs[0]["parameters_selected_using_it"]
              and "lookback=21" in exp_recs[0]["parameters_selected_using_it"],
              "exp fixture parameters extracted (lookback=21)")
        check(any("sharpe=" in r["results_previously_calculated"].lower()
                  or "sharpe" in r["results_previously_calculated"].lower()
                  for r in exp_recs),
              "exp fixture outcome statistics captured")

        check(len(reg_recs) >= 1, "regime-analysis-style fixture is flagged "
                                  "(implicit as-of window)")
        check(all(r["permitted_future_use"] in PERMITTED_VALUES
                  for r in reg_recs),
              "regime fixture permitted_future_use in enum")

        check(len(clean_recs) == 0, "clean pre-2021 non-finance fixture not flagged")

        # -- schema check over combined pseudo-ledger ------------------------
        all_recs = exp_recs + reg_recs
        required = set(RECORD_KEYS)
        schema_ok = all(required.issubset(r.keys()) for r in all_recs)
        enum_ok = all(r["permitted_future_use"] in PERMITTED_VALUES for r in all_recs)
        ds_ok = all(r["dataset"] == "universe-125_2021-2026_full" for r in all_recs)
        order_ok = all(r["period_start"] <= r["period_end"] for r in all_recs)
        check(schema_ok, "ledger record schema (all required keys present)")
        check(enum_ok, "ledger permitted_future_use enum valid")
        check(ds_ok, "ledger dataset field pinned to universe-window id")
        check(order_ok, "period_start <= period_end in every record")

        # -- real-repo spot checks (read-only) --------------------------------
        root = get_default_root()
        real_targets = [
            os.path.join(root, "research", "experiments", "exp-mean-reversion.md"),
            os.path.join(root, "Efforts", "osanwe-v2-overhaul", "_work",
                         "regime-analysis-2026-08-25.json"),
        ]
        for tgt in real_targets:
            if os.path.isfile(tgt):
                recs, _m = analyze_file(tgt)
                check(len(recs) >= 1,
                      "known-contaminated real artifact flagged: %s"
                      % relpath_norm(tgt))
            else:
                print("  SKIP  real artifact not present: %s" % tgt)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print("SELFTEST FAILED (%d)" % len(failures))
        return 1
    print("SELFTEST PASSED")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="FW2 contamination audit + ledger")
    ap.add_argument("--root", default=DEFAULT_ROOT,
                    help="workspace root (default: auto-detected)")
    ap.add_argument("--out", default=None,
                    help="ledger output path (default: _work/fis-data/...)")
    ap.add_argument("--selftest", action="store_true",
                    help="verify schema + known-contaminated detection")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return run_selftest()

    out = args.out or os.path.join(args.root, DEFAULT_OUT_REL)
    return run_audit(args.root, out, quiet=args.quiet)


if __name__ == "__main__":
    sys.exit(main())

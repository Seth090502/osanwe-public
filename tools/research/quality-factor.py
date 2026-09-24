#!/usr/bin/env python
"""quality-factor.py -- quality factor backtest from EDGAR XBRL fundamentals.

Question: do high-quality companies (profitable, low-leverage, stable earnings)
outperform low-quality ones in the vault universe?

Data:
  fundamentals : wiki/investing/filings/<T>/<T>-xbrl.json  (concept rows w/ 'filed')
  prices       : Efforts/osanwe-v2-overhaul/_work/factors.db, table 'bars'

Point-in-time discipline: at each quarterly rebalance date D, a ticker's
fundamentals come ONLY from filings with filed <= D. Prices use the last
close on/before D.

Metric adaptation (honest): the local XBRL store carries only
{Revenue(s), NetIncome, Cash, LongTermDebt, Capex, R&D}. There is NO
GrossProfit, TotalAssets, or StockholdersEquity concept, so:
  profitability : TTM NetIncome / TTM Revenue   (net margin; proxy for
                  gross profitability since GP/TA unavailable)
  ROE           : NOT COMPUTABLE (no equity concept) -- omitted
  low leverage  : LongTermDebt / TTM Revenue    (debt-to-revenue, inverted)
  stability     : std(last 8 qtrs NI) / mean|NI| (coefficient of variation,
                  scale-free; inverted)

Composite: equal-weight average of cross-sectional z-scores of the three
available components. Quintile Q5 = highest quality (long leg), Q1 = lowest.

Usage: python tools/research/quality-factor.py [--write-report]
ASCII only. No network.
"""

import json
import math
import os
import sqlite3
import sys
from datetime import date

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
FILINGS_DIR = os.path.join(ROOT, "wiki", "investing", "filings")
BARS_DB = os.path.join(ROOT, "Efforts", "osanwe-v2-overhaul", "_work", "factors.db")
REPORT_PATH = os.path.join(ROOT, "research", "experiments", "exp-quality-factor.md")

MIN_QTRS_NI = 4          # min quarterly NI observations at a rebalance
MIN_STABILITY_OBS = 6    # min obs for stability metric (target 8)
MIN_SCORED_PER_DATE = 15 # skip rebalance date if fewer scored names
SENS_MIN_SCORED = 8      # sensitivity pass floor (thin quintiles)
MIN_QUARTERS_FOR_STATS = 12  # min rebalances for a meaningful factor claim
QUARTERS_PER_YEAR = 4


# ----------------------------------------------------------------------
# data loading
# ----------------------------------------------------------------------

def load_fundamentals():
    """ticker -> list of fundamental rows (dicts) sorted by filed."""
    out = {}
    for tdir in sorted(os.listdir(FILINGS_DIR)):
        path = os.path.join(FILINGS_DIR, tdir, "%s-xbrl.json" % tdir)
        if not os.path.isfile(path):
            continue
        try:
            rows = json.load(open(path))
        except Exception as exc:
            print("WARN: cannot parse %s: %s" % (path, exc))
            continue
        clean = []
        for r in rows:
            try:
                clean.append({
                    "concept": r["concept"],
                    "period": r["period"],
                    "form": r.get("form", ""),
                    "fp": r.get("fp", ""),
                    "filed": r["filed"],
                    "value": float(r["value"]),
                })
            except (KeyError, TypeError, ValueError):
                continue
        clean.sort(key=lambda r: (r["filed"], r["period"]))
        out[tdir] = clean
    return out


def load_bars():
    """(ticker -> [(date, close)]) plus SPY series."""
    con = sqlite3.connect(BARS_DB)
    cur = con.cursor()
    bars = {}
    for tkr, d, c in cur.execute("SELECT ticker, date, close FROM bars ORDER BY ticker, date"):
        bars.setdefault(tkr, []).append((d, float(c)))
    con.close()
    return bars


# ----------------------------------------------------------------------
# point-in-time fundamental extraction
# ----------------------------------------------------------------------

def asof_state(rows, asof):
    """Latest-known fundamental state for one ticker at date `asof`.

    Dedupes restatements by keeping the FIRST filed value per
    (concept, period). Returns dict with:
      q_ni      : list of (period, value) QUARTERLY NI (10-Q), oldest->newest
      ttm_ni    : TTM net income (4-qtr sum if fresher than annual, else FY)
      ttm_rev   : TTM revenue (4-qtr sum if fresher, else latest FY value)
      ltd       : latest LongTermDebt
    """
    ni_q = {}        # period -> (filed, value)  from 10-Q
    ni_fy = {}       # period -> (filed, value)  from 10-K
    rev_q = {}       # period -> (filed, value)
    rev_annual = {}  # period -> (filed, value)
    ltd = {}         # period -> (filed, value)
    for r in rows:
        if r["filed"] > asof:
            break
        c, per, fl = r["concept"], r["period"], r["filed"]
        if c == "NetIncome":
            tgt = ni_fy if r["form"] == "10-K" else ni_q
            if per not in tgt or fl < tgt[per][0]:
                tgt[per] = (fl, r["value"])
        elif c in ("Revenue", "Revenues"):
            tgt = rev_annual if r["form"] == "10-K" else rev_q
            if per not in tgt or fl < tgt[per][0]:
                tgt[per] = (fl, r["value"])
        elif c == "LongTermDebt":
            if per not in ltd or fl < ltd[per][0]:
                ltd[per] = (fl, r["value"])
    q_ni = sorted((p, v) for p, (_, v) in ni_q.items())
    if not q_ni:
        return None

    # drop quarterly revenue periods superseded by an annual figure for the
    # same fiscal year (annual filed no later than the quarter's filing)
    stale = set()
    for aper, (afl, _) in rev_annual.items():
        for qper in rev_q:
            if qper[:4] == aper[:4] and rev_q[qper][0] <= afl:
                stale.add(qper)
    rev_periods = sorted(p for p in rev_q if p not in stale)

    # TTM helpers: this store's quarterly series has fiscal-year-end gaps and
    # not every ticker carries 10-K rows per concept, so instead of demanding
    # perfect consecutive quarters we accept any trailing 4-quarter window
    # spanning <= 15 months, then pick whichever SOURCE (quarterly window vs
    # latest annual figure) was FILED most recently.
    def _span_months(periods):
        idx = [int(p[:4]) * 12 + int(p[5:7]) - 1 for p in periods]
        return max(idx) - min(idx)

    def _pick_ttm(annual_map, q_map, periods):
        """Return TTM value from the freshest-filing source, or None."""
        q_best = None
        if len(periods) >= 4 and _span_months(periods[-4:]) <= 15:
            win = periods[-4:]
            q_best = (sum(q_map[p][1] for p in win),
                      max(q_map[p][0] for p in win))
        a_best = None
        if annual_map:
            newest = max(annual_map, key=lambda p: (annual_map[p][0], p))
            a_best = (annual_map[newest][1], annual_map[newest][0])
        cands = [c for c in (q_best, a_best) if c is not None]
        if not cands:
            return None
        return max(cands, key=lambda c: c[1])[0]

    ni_periods = [p for p, _ in q_ni]
    ttm_ni = _pick_ttm(ni_fy, ni_q, ni_periods)
    ttm_rev = _pick_ttm(rev_annual, rev_q, rev_periods)

    latest_ltd = None
    if ltd:
        newest_l = max(ltd, key=lambda p: (ltd[p][0], p))
        latest_ltd = ltd[newest_l][1]

    return {
        "q_ni": q_ni,
        "ttm_ni": ttm_ni,
        "ttm_rev": ttm_rev,
        "ltd": latest_ltd,
    }


def _consecutive_quarters(periods):
    if len(periods) != 4:
        return False
    idx = [int(p[:4]) * 4 + (int(p[5:7]) - 1) // 3 for p in periods]
    return all(idx[i + 1] - idx[i] == 1 for i in range(3))


def quality_metrics(state):
    """Return dict of metric -> (value or None). Higher = better quality."""
    out = {"margin": None, "lev_inv": None, "stab_inv": None}
    ni_ttm, rev_ttm = state["ttm_ni"], state["ttm_rev"]
    if ni_ttm is not None and rev_ttm and rev_ttm > 0:
        out["margin"] = ni_ttm / rev_ttm
    if state["ltd"] is not None and rev_ttm and rev_ttm > 0:
        lev = state["ltd"] / rev_ttm
        if lev < 25:  # sanity cap against near-zero-revenue distortions
            out["lev_inv"] = -lev
    q = [v for _, v in state["q_ni"]]
    if len(q) >= MIN_QTRS_NI:
        window = q[-8:]  # last up-to-8 quarters
        mu = sum(abs(v) for v in window) / len(window)
        if mu > 0:
            var = sum((v - sum(window) / len(window)) ** 2 for v in window) / len(window)
            cv = math.sqrt(var) / mu
            if cv < 50:
                out["stab_inv"] = -cv
    return out


# ----------------------------------------------------------------------
# rebalance machinery
# ----------------------------------------------------------------------

def quarter_rebalance_dates(bars_spy):
    """Quarterly rebalance dates = first trading day of Mar/Jun/Sep/Dec."""
    seen = set()
    dates = []
    for d, _ in bars_spy:
        ym = d[:7]
        if d[5:7] in ("03", "06", "09", "12") and ym not in seen:
            seen.add(ym)
            dates.append(d)
    return dates


def close_on_or_before(series, d):
    lo, hi = 0, len(series) - 1
    best = None
    while lo <= hi:
        mid = (lo + hi) // 2
        if series[mid][0] <= d:
            best = series[mid]
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def close_on_or_closest_after(series, d):
    """First close ON or AFTER date d (fallback if d is a non-trading day
    beyond the series end -> last bar)."""
    for dt, c in series:
        if dt >= d:
            return (dt, c)
    return series[-1]


def cross_sectional_z(values):
    """values: {ticker: x}. Returns {ticker: z}. Population std."""
    n = len(values)
    if n < 2:
        return {k: 0.0 for k in values}
    mu = sum(values.values()) / n
    var = sum((v - mu) ** 2 for v in values.values()) / n
    sd = math.sqrt(var)
    if sd == 0:
        return {k: 0.0 for k in values}
    return {k: (v - mu) / sd for k, v in values.items()}


def run_backtest(min_history_end="2022-06-30", min_scored=None):
    if min_scored is None:
        min_scored = MIN_SCORED_PER_DATE
    funda = load_fundamentals()
    bars = load_bars()
    spy = bars.get("SPY")
    if not spy:
        raise SystemExit("no SPY bars")

    # restrict to tickers that have both bars and any XBRL
    universe = [t for t in funda if t in bars and t != "SPY"]
    rb_dates = [d for d in quarter_rebalance_dates(spy) if d >= min_history_end]

    records = []  # one row per (rebalance_date, ticker)
    for i, d in enumerate(rb_dates[:-1]):
        nxt = rb_dates[i + 1]
        scores = {}
        raw = {}
        for t in universe:
            state = asof_state(funda[t], d)
            if state is None or len(state["q_ni"]) < MIN_QTRS_NI:
                continue
            m = quality_metrics(state)
            if m["margin"] is None or m["stab_inv"] is None:
                continue
            p0 = close_on_or_before(bars[t], d)
            p1 = close_on_or_before(bars[t], nxt)
            if not p0 or not p1 or p0[0] >= nxt:
                continue
            fwd = p1[1] / p0[1] - 1.0
            raw[t] = m
            scores[t] = fwd
        if len(scores) < min_scored:
            print("skip %s: only %d scored" % (d, len(scores)))
            continue
        zs = {}
        for comp in ("margin", "lev_inv", "stab_inv"):
            vals = {t: m[comp] for t, m in raw.items() if m[comp] is not None}
            zc = cross_sectional_z(vals)
            for t in scores:
                zs.setdefault(comp, {})[t] = zc.get(t, 0.0)
        composite = {t: (zs["margin"][t] + zs["lev_inv"][t] + zs["stab_inv"][t]) / 3.0
                     for t in scores}
        ranked = sorted(composite, key=lambda t: composite[t])  # ascending
        n = len(ranked)
        k5 = max(1, n // 5)
        buckets = {"Q1": ranked[:k5], "Q5": ranked[-k5:]}
        for qi in range(2, 5):  # middle buckets for monotonicity check
            lo = int(n * (qi - 1) / 5)
            hi = int(n * qi / 5)
            buckets["Q%d" % qi] = ranked[lo:hi]
        for qname, members in buckets.items():
            ret = sum(scores[t] for t in members) / len(members)
            records.append({"date": d, "next": nxt, "q": qname, "ret": ret,
                            "n_scored": n})
        ew = sum(scores.values()) / len(scores)
        records.append({"date": d, "next": nxt, "q": "EW", "ret": ew,
                        "n_scored": n})
    used_dates = sorted(set(r["date"] for r in records))
    return records, used_dates, spy, len(universe)


# ----------------------------------------------------------------------
# stats + reporting
# ----------------------------------------------------------------------

def chain(returns):
    eq = 1.0
    for r in returns:
        eq *= 1.0 + r
    return eq


def summarize(returns):
    n = len(returns)
    if n == 0:
        return None
    total = chain(returns)
    years = n / QUARTERS_PER_YEAR
    cagr = total ** (1.0 / years) - 1.0 if total > 0 else -1.0
    mu = sum(returns) / n
    var = sum((r - mu) ** 2 for r in returns) / max(1, n - 1)
    sd = math.sqrt(var)
    sharpe = mu / sd * math.sqrt(QUARTERS_PER_YEAR) if sd > 0 else float("nan")
    return {"n": n, "total": total, "cagr": cagr, "sharpe": sharpe,
            "mean_q": mu}


def t_stat(a, b):
    """Paired t-stat of spread series a-b."""
    d = [x - y for x, y in zip(a, b)]
    n = len(d)
    mu = sum(d) / n
    var = sum((x - mu) ** 2 for x in d) / max(1, n - 1)
    se = math.sqrt(var / n)
    return (mu / se) if se > 0 else float("nan"), mu, n


def analyze(records):
    """Compute stats dict from backtest records."""
    dates_sorted = sorted(set((r["date"], r["next"]) for r in records))
    aligned = {}
    for r in records:
        aligned.setdefault(r["date"], {})[r["q"]] = r["ret"]
    qlist = ["Q1", "Q2", "Q3", "Q4", "Q5", "EW"]
    table = {q: [aligned[d].get(q) for d, _ in dates_sorted] for q in qlist}
    tval, spread_mean, nobs = t_stat(table["Q5"], table["Q1"])
    return {
        "table": table,
        "dates": dates_sorted,
        "stats": {q: summarize(table[q]) for q in qlist},
        "tval": tval,
        "spread_mean": spread_mean,
        "nobs": nobs,
        "n_scored_min": min(r["n_scored"] for r in records),
        "n_scored_max": max(r["n_scored"] for r in records),
        "start_d": dates_sorted[0][0],
        "end_d": dates_sorted[-1][1],
        "span_years": len(dates_sorted) / QUARTERS_PER_YEAR,
    }


def spy_bh(spy_series, start_d, end_d):
    p0 = close_on_or_before(spy_series, start_d)
    p1 = close_on_or_closest_after(spy_series, end_d)
    total = p1[1] / p0[1]
    return {"total": total, "p0": p0, "p1": p1}


def render_report(res_primary, res_sens, spy_series, n_universe):
    lines = []
    A = lines.append
    A("# Experiment: Quality Factor (EDGAR XBRL fundamentals)")
    A("")
    A("- Date run: %s" % date.today().isoformat())
    A("- Code: `tools/research/quality-factor.py`")
    A("- Data: `wiki/investing/filings/<T>/<T>-xbrl.json` + `bars` table in")
    A("  `Efforts/osanwe-v2-overhaul/_work/factors.db` (yfinance adj closes).")
    A("- Question: do high-quality companies (profitable, low leverage, stable")
    A("  earnings) outperform low-quality ones?")
    A("")
    A("## Method")
    A("")
    A("- Quarterly rebalance on the first trading day of Mar/Jun/Sep/Dec.")
    A("- POINT-IN-TIME: only filings with `filed <= rebalance date`; restatements")
    A("  deduped keeping the first-filed value per (concept, period); prices are")
    A("  last close on/before the rebalance date.")
    A("- Quality composite = equal-weight mean of cross-sectional z-scores of:")
    A("  1. Profitability: TTM NetIncome / TTM Revenue (net margin)")
    A("  2. Low leverage: -(LongTermDebt / TTM Revenue)")
    A("  3. Earnings stability: -(std of last up-to-8 quarterly NI / mean|NI|),")
    A("     minimum 4 quarters required; missing components enter the composite")
    A("     at z = 0 (neutral) rather than excluding the name.")
    A("- Quintiles formed per rebalance (Q5 = highest quality = LONG leg).")
    A("- Baselines: SPY buy-and-hold over the same span; equal-weight (EW) all")
    A("  scored tickers.")
    A("")
    A("### Metric adaptations (data limitation, stated up front)")
    A("")
    A("The vault XBRL store contains only {Revenue(s), NetIncome, Cash, Capex,")
    A("R&D, LongTermDebt}. **No GrossProfit, TotalAssets, or StockholdersEquity**")
    A("concepts exist, therefore:")
    A("- Gross profitability (GP/TA) was substituted with net margin (TTM NI /")
    A("  TTM Rev) per the task's 'or Revenue as proxy' allowance.")
    A("- ROE (NI/equity) could NOT be computed and was omitted.")
    A("- Leverage used Debt/Revenue instead of Debt/Equity.")
    A("- Quarterly NI series have fiscal-year-end gaps in this store; TTM values")
    A("  use the freshest-filed source (trailing-4-qtr window vs latest FY row).")
    A("")
    A("**DATA COVERAGE NOTE:** most tickers' XBRL rows only begin in 2024-2026.")
    A("A strict >=15-name floor leaves ONE usable rebalance (2026-03), which is")
    A("far too few periods for any statistical claim. Two passes are reported:")
    A("(a) PRIMARY with the strict floor, and (b) SENSITIVITY with a >=8-name")
    A("floor that reaches further back but has thin quintiles. Both fail the")
    A("task's own quality bar; treat all numbers below as descriptive only.")
    A("")
    for label, res, floor in (("PRIMARY", res_primary, MIN_SCORED_PER_DATE),
                              ("SENSITIVITY", res_sens, SENS_MIN_SCORED)):
        A("## %s pass (floor >=%d scored names)" % (label, floor))
        A("")
        A("- Rebalances used: %d (%s -> %s)"
          % (len(res["dates"]), res["start_d"], res["end_d"]))
        A("- Names scored per rebalance: min %d, max %d."
          % (res["n_scored_min"], res["n_scored_max"]))
        A("- Span: %.2f years." % res["span_years"])
        bh = spy_bh(spy_series, res["start_d"], res["end_d"])
        years = max(1e-9, (date(int(bh["p1"][0][:4]), int(bh["p1"][0][5:7]),
                                int(bh["p1"][0][8:10])) -
                    date(int(bh["p0"][0][:4]), int(bh["p0"][0][5:7]),
                         int(bh["p0"][0][8:10]))).days / 365.25)
        spy_cagr = bh["total"] ** (1.0 / years) - 1.0 if bh["total"] > 0 else -1.0
        A("")
        A("| Bucket | N qtrs | Total ret | CAGR* | Sharpe* |")
        A("|---|---|---|---|---|")
        for q in ("Q1", "Q2", "Q3", "Q4", "Q5", "EW"):
            s = res["stats"][q]
            if s is None or s["n"] == 0:
                A("| %s | 0 | - | - | - |" % q)
                continue
            sharpe = ("%.2f" % s["sharpe"]) if s["n"] > 1 else "n/m"
            A("| %s | %d | %+.1f%% | %+.1f%% | %s |"
              % (q, s["n"], 100 * (s["total"] - 1), 100 * s["cagr"], sharpe))
        A("| SPY B&H | - | %+.1f%% | %+.1f%% | - |"
          % (100 * (bh["total"] - 1), 100 * spy_cagr))
        A("")
        A("*CAGR annualizes very short spans and is explosive/unstable;")
        A("Sharpe is n/m (not meaningful) with fewer than 2 quarters.")
        A("")
        sm5 = res["stats"]["Q5"]["cagr"]
        sm1 = res["stats"]["Q1"]["cagr"]
        A("- Q5 - Q1 mean quarterly spread: %+.2f%%" % (100 * res["spread_mean"]))
        if res["nobs"] > 1:
            A("- Paired t-stat (Q5 vs Q1, n=%d): %.2f" % (res["nobs"], res["tval"]))
        else:
            A("- Paired t-stat: NOT COMPUTABLE (n=%d quarter)." % res["nobs"])
        order = sorted(range(1, 6), key=lambda i: res["stats"]["Q%d" % i]["cagr"])
        A("- CAGR rank order (worst->best): %s"
          % " < ".join("Q%d" % i for i in order))
        mono = all(res["stats"]["Q%d" % i]["cagr"]
                   <= res["stats"]["Q%d" % (i + 1)]["cagr"] + 1e-9
                   for i in range(1, 5))
        A("- Monotonic Q1<Q2<Q3<Q4<Q5: %s" % ("YES" if mono else "NO"))
        A("- Q5 beats Q1 on CAGR: %s" % ("YES" if sm5 > sm1 else "NO"))
        A("")
    A("## Verdict")
    A("")
    fails = []
    best_scored = max(res_primary["n_scored_max"], res_sens["n_scored_max"])
    if best_scored < 20:
        fails.append("fewer than 20 tickers with sufficient XBRL data "
                     "(max cross-section reached: %d)" % best_scored)
    if not (res_sens["stats"]["Q5"]["cagr"] > res_sens["stats"]["Q1"]["cagr"]
            and res_primary["stats"]["Q5"]["cagr"]
            > res_primary["stats"]["Q1"]["cagr"]):
        fails.append("Q5 (high quality) does not outperform Q1")
    if len(res_primary["dates"]) < MIN_QUARTERS_FOR_STATS:
        fails.append("only %d rebalance(s) clear the >=%d-name floor "
                     "(need >=%d for meaningful stats)"
                     % (len(res_primary["dates"]), MIN_SCORED_PER_DATE,
                        MIN_QUARTERS_FOR_STATS))
    verdict = "REJECT -- factor NOT established" if fails else \
              "SUPPORT (subject to caveats)"
    A("**%s**" % verdict)
    for f in fails:
        A("- Failure criterion hit: %s." % f)
    A("")
    A("## Caveats (read before trading this)")
    A("")
    A("- SURVIVORSHIP: the universe is today's watchlist; delisted names absent.")
    A("- FUNDAMENTAL DEPTH: XBRL coverage starts ~2024-2026 for most names, so")
    A("  the point-in-time sample is 1-7 quarters deep, far below what any")
    A("  factor study needs. The t-stat cannot be computed on the primary pass.")
    A("- Small cross-section makes quintile edges thin (top/bottom ~10 names).")
    A("- Metric substitutions above weaken fidelity to the canonical quality")
    A("  factor (Novy-Marx GP/TA, ROE).")
    A("- Quarterly granularity ignores intra-quarter timing; no transaction")
    A("  costs modeled.")
    A("")
    return "\n".join(lines) + "\n"


def main(write_report=False):
    records_p, _, spy_series, n_universe = run_backtest()  # strict floor
    records_s, _, _, _ = run_backtest(min_scored=SENS_MIN_SCORED)
    if not records_p or not records_s:
        print("INSUFFICIENT DATA: no usable rebalances; aborting report.")
        return
    res_p = analyze(records_p)
    res_s = analyze(records_s)
    report = render_report(res_p, res_s, spy_series, n_universe)

    print(report)
    if write_report:
        os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
        with open(REPORT_PATH, "w") as fh:
            fh.write(report)
        print("wrote %s" % REPORT_PATH)


if __name__ == "__main__":
    main(write_report="--write-report" in sys.argv)

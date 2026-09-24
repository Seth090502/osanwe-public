#!/usr/bin/env python3
# -*- coding: ascii -*-
"""
Low-risk / defensive factor study ("low-vol / low-beta anomaly").

Question: Do low-volatility or low-beta stocks outperform high-vol /
high-beta stocks in our universe?

Method:
  - Universe: equities in factors.db bars with >750 bars.
    Excluded: crypto (*-USD), ADRs, ETFs/funds (explicit list below),
    MACRO pseudo-ticker.
  - At each month-end (last common trading day of the month):
      * trailing 63d volatility = stdev(daily returns, 63d) * sqrt(252)
      * rank into quintiles (Q1 = lowest vol ... Q5 = highest vol)
      * LONG Q1; measure Q1 vs Q5 and vs equal-weight-all
  - Beta sort: trailing 252d beta vs SPY (needs >=200 paired obs);
    quintile by beta, LONG bottom quintile.
  - Execution costs: 10 bps per dollar of one-way turnover, charged on
    the equal-weight portfolio each rebalance (turnover measured against
    previous holdings; first month fully charged).
  - Baselines: buy-and-hold SPY, equal-weight all eligible, random
    quintile (200 shuffled trials, averaged).
Metrics: CAGR per quintile, annualized Sharpe (monthly), monotonicity of
mean monthly returns Q1->Q5, t-stat of the monthly Q1-Q5 spread.

Failure criteria (pre-registered):
  Reject if Q1 does not outperform Q5 OR relationship is not monotonic.

Usage:  python tools/research/low-risk-factor.py [path/to/factors.db]
Output: prints results table; writes nothing else.

ASCII only. Stdlib only. sqlite3 direct. No network.
"""

import math
import os
import random
import sqlite3
import sys
from collections import defaultdict

DEFAULT_DB = r"/path/to/vault\Efforts\osanwe-v2-overhaul\_work\factors.db"

# ---- universe hygiene -------------------------------------------------
CRYPTO_SUFFIX = "-USD"
ADRS = {"ABBNY", "ASMIY", "ATEYY", "TSM"}   # foreign shares / ADRs in db
ETF_TICKERS = {
    "SPY", "QQQ", "VOO", "IAU", "SMH", "SOXX", "VGT",
    "ITA", "PPA", "XAR", "VDE", "XLE", "XLF", "XLI",
    "XLP", "XLRE", "XLU", "XLV", "XLY", "DTCR", "SPCX",
}
MIN_BARS = 751          # ">750 bars"
VOL_WINDOW = 63         # trading days of returns
BETA_WINDOW = 252       # trading days of returns
BETA_MIN_OBS = 200
COST_BPS = 10.0         # bps per one-way traded dollar
RANDOM_TRIALS = 200
RF_ANNUAL = 0.0         # risk-free for Sharpe (documented assumption)


def load_bars(db_path):
    con = sqlite3.connect(db_path)
    try:
        cur = con.execute("SELECT ticker, date, close FROM bars ORDER BY ticker, date")
        bars = defaultdict(list)
        for tk, dt, px in cur:
            bars[tk].append((dt, float(px)))
    finally:
        con.close()
    return bars


def universe(bars):
    keep = []
    for tk, series in bars.items():
        if tk == "MACRO" or tk in ETF_TICKERS or tk in ADRS:
            continue
        if tk.endswith(CRYPTO_SUFFIX):
            continue
        if len(series) <= MIN_BARS - 1:
            continue
        keep.append(tk)
    return sorted(keep)


def daily_returns(series):
    """series: sorted [(date, close)] -> dict date -> simple return."""
    out = {}
    for i in range(1, len(series)):
        p0, p1 = series[i - 1][1], series[i][1]
        if p0 > 0:
            out[series[i][0]] = p1 / p0 - 1.0
    return out


def month_end_dates(all_dates):
    """Last available trading date of each calendar month (sorted)."""
    seen = {}
    for d in sorted(all_dates):
        ym = d[:7]
        seen[ym] = d          # dates sorted -> last write wins
    return [seen[ym] for ym in sorted(seen)]


def trailing_vol(rets, dates_idx, end_date):
    """Annualized vol over last VOL_WINDOW daily returns ending end_date."""
    vals = []
    for d in reversed(dates_idx):
        if d[0] <= end_date and d[1] is not None:
            vals.append(d[1])
            if len(vals) == VOL_WINDOW:
                break
    if len(vals) < VOL_WINDOW:
        return None
    n = len(vals)
    mu = sum(vals) / n
    var = sum((v - mu) ** 2 for v in vals) / (n - 1)
    return math.sqrt(var) * math.sqrt(252.0)


def trailing_beta(rets, spy_rets, end_date):
    """OLS beta of ticker daily returns on SPY over BETA_WINDOW paired days."""
    xs, ys = [], []
    for d in sorted(spy_rets.keys(), reverse=True):
        if d > end_date:
            continue
        if d in rets:
            xs.append(spy_rets[d])
            ys.append(rets[d])
            if len(xs) == BETA_WINDOW:
                break
    if len(xs) < BETA_MIN_OBS:
        return None
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    var = sum((x - mx) ** 2 for x in xs)
    if var <= 0:
        return None
    return cov / var


def quintiles(scores):
    """dict tk -> score -> dict tk -> q (1..5). Higher score = higher q."""
    items = sorted(scores.items(), key=lambda kv: kv[1])
    n = len(items)
    out = {}
    for i, (tk, _) in enumerate(items):
        out[tk] = min(4, int(i * 5 / n)) + 1
    return out


def stats_from_monthly(rets_monthly):
    """CAGR, annualized Sharpe from a list of monthly returns."""
    n = len(rets_monthly)
    if n == 0:
        return 0.0, 0.0, 0.0
    cum = 1.0
    for r in rets_monthly:
        cum *= (1.0 + r)
    years = n / 12.0
    cagr = cum ** (1.0 / years) - 1.0 if cum > 0 else -1.0
    mu = sum(rets_monthly) / n
    if n > 1:
        var = sum((r - mu) ** 2 for r in rets_monthly) / (n - 1)
        sd = math.sqrt(var)
        sharpe = ((mu - RF_ANNUAL / 12.0) / sd * math.sqrt(12.0)) if sd > 0 else 0.0
    else:
        sharpe = 0.0
    # t-stat of mean != 0
    tstat = (mu / sd * math.sqrt(n)) if (n > 1 and sd > 0) else 0.0
    return cagr, sharpe, tstat


def run_sort(port_by_q, months):
    """port_by_q: {q: {month: monthly_return}} -> per-q stats."""
    res = {}
    for q in sorted(port_by_q.keys()):
        series = [port_by_q[q].get(m) for m in months]
        series_ok = [r for r in series if r is not None]
        cagr, sharpe, _ = stats_from_monthly(series_ok)
        res[q] = (cagr, sharpe, len(series_ok))
    return res


def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB
    bars = load_bars(db_path)
    tickers = universe(bars)
    print("DB: %s" % db_path)
    print("Eligible equities (>750 bars, ex-crypto/ADR/ETF): %d" % len(tickers))
    print(", ".join(tickers))

    # returns per ticker
    rets = {}
    for tk in tickers:
        rets[tk] = daily_returns(bars[tk])
    spy_series = bars["SPY"]
    spy_rets = daily_returns(spy_series)

    # master calendar: union of SPY + universe dates
    cal = set(spy_rets.keys())
    for tk in tickers:
        cal |= set(rets[tk].keys())
    med = month_end_dates(cal)
    # need a following month to realize returns
    med = med[:-1] if len(med) >= 2 else []

    # precompute per-date index lists for vol lookups: (date, ret) sorted
    idx = {}
    for tk in tickers:
        idx[tk] = sorted(rets[tk].items())

    months = []
    vol_ports = {q: {} for q in range(1, 6)}
    beta_ports = {q: {} for q in range(1, 6)}
    ew_all = {}
    prev_vol_hold = set()
    prev_beta_hold = set()
    betas_last = {}

    for mi in range(len(med) - 1):
        t0, t1 = med[mi], med[mi + 1]

        # --- scores at t0 ---
        vols, betas, elig_v, elig_b = {}, {}, [], []
        for tk in tickers:
            v = trailing_vol(rets[tk], idx[tk], t0)
            if v is not None:
                vols[tk] = v
                elig_v.append(tk)
            b = trailing_beta(rets[tk], spy_rets, t0)
            if b is not None:
                betas[tk] = b
                elig_b.append(tk)
        if not elig_v:
            continue
        months.append(t1)

        def realized(sel):
            """Equal-weight monthly return of selection, needs price at t0,t1."""
            rs = []
            for tk in sel:
                s = dict(bars[tk])  # small; acceptable
                if t0 in s and t1 in s and s[t0] > 0:
                    rs.append(s[t1] / s[t0] - 1.0)
            return (sum(rs) / len(rs)) if rs else None

        # --- vol quintiles ---
        vq = quintiles(vols)
        for q in range(1, 6):
            sel = [tk for tk in elig_v if vq[tk] == q]
            r_gross = realized(sel)
            if r_gross is None:
                vol_ports[q][t1] = None
                continue
            new_hold = set(sel)
            turned = len(new_hold ^ prev_vol_hold) / 2.0
            denom = max(len(prev_vol_hold), 1) if prev_vol_hold else max(len(new_hold), 1)
            cost = (turned / denom) * COST_BPS / 10000.0 if prev_vol_hold else COST_BPS / 10000.0
            vol_ports[q][t1] = r_gross - cost
            if q == 1:
                prev_vol_hold = new_hold

        # --- beta quintiles ---
        if elig_b:
            bq = quintiles(betas)
            for q in range(1, 6):
                sel = [tk for tk in elig_b if bq[tk] == q]
                r_gross = realized(sel)
                if r_gross is None:
                    beta_ports[q][t1] = None
                    continue
                new_hold = set(sel)
                turned = len(new_hold ^ prev_beta_hold) / 2.0
                denom = max(len(prev_beta_hold), 1) if prev_beta_hold else max(len(new_hold), 1)
                cost = (turned / denom) * COST_BPS / 10000.0 if prev_beta_hold else COST_BPS / 10000.0
                beta_ports[q][t1] = r_gross - cost
                if q == 1:
                    prev_beta_hold = new_hold
            betas_last = betas

        # --- equal-weight all ---
        ew_all[t1] = realized(elig_v)

    print("\nMonths backtested: %d (%s .. %s)" % (len(months), months[0], months[-1]))

    # ---------------- baselines ----------------
    spy_m = []
    for i in range(len(med) - 1):
        t0, t1 = med[i], med[i + 1]
        if t1 in months:
            s = dict(spy_series)
            spy_m.append(s[t1] / s[t0] - 1.0)
    spy_cagr, spy_sharpe, _ = stats_from_monthly(spy_m)

    ew_series = [ew_all.get(m) for m in months]
    ew_series = [r for r in ew_series if r is not None]
    ew_cagr, ew_sharpe, _ = stats_from_monthly(ew_series)

    # ---------------- random quintile baseline ----------------
    rng = random.Random(42)
    rnd_cagr_sum, rnd_sharpe_sum, rnd_n = 0.0, 0.0, 0
    # rebuild eligibility per month for randomization
    for trial in range(RANDOM_TRIALS):
        ser = []
        for mi in range(len(med) - 1):
            t0, t1 = med[mi], med[mi + 1]
            elig = [tk for tk in tickers
                    if trailing_vol(rets[tk], idx[tk], t0) is not None]
            if not elig or t1 not in months:
                continue
            rng.shuffle(elig)
            k = len(elig) // 5
            sel = elig[:k] or elig
            rs = []
            for tk in sel:
                s = dict(bars[tk])
                if t0 in s and t1 in s and s[t0] > 0:
                    rs.append(s[t1] / s[t0] - 1.0)
            if rs:
                ser.append(sum(rs) / len(rs))
        if ser:
            c, sh, _ = stats_from_monthly(ser)
            rnd_cagr_sum += c
            rnd_sharpe_sum += sh
            rnd_n += 1

    # ---------------- reporting ----------------
    def row(label, cagr, sharpe, n=None):
        nn = ("%d" % n) if n is not None else "-"
        print("%-22s %8.2f%% %8.2f %8s" % (label, cagr * 100, sharpe, nn))

    print("\n=== BASELINES (net of 10 bps turnover cost where applicable) ===")
    print("%-22s %9s %9s %8s" % ("strategy", "CAGR", "Sharpe", "months"))
    row("SPY buy&hold (gross)", spy_cagr, spy_sharpe, len(spy_m))
    row("EW all universe", ew_cagr, ew_sharpe, len(ew_series))
    if rnd_n:
        row("Random quintile (avg)", rnd_cagr_sum / rnd_n, rnd_sharpe_sum / rnd_n, rnd_n)

    def report_sort(title, ports):
        print("\n=== %s ===" % title)
        print("%-22s %9s %9s %8s" % ("quintile", "CAGR", "Sharpe", "months"))
        cagrs = []
        for q in range(1, 6):
            series = [ports[q].get(m) for m in months]
            series = [r for r in series if r is not None]
            cagr, sharpe, _ = stats_from_monthly(series)
            cagrs.append((cagr, series))
            row("Q%d" % q, cagr, sharpe, len(series))

        # monotonicity of MEAN MONTHLY returns
        means = [sum(s) / len(s) if s else float("nan") for _, s in cagrs]
        viol = [(i + 1, i + 2) for i in range(4)
                if not (means[i] > means[i + 1])]
        print("Mean monthly returns Q1..Q5: %s"
              % ", ".join("%.3f%%" % (m * 100) for m in means))
        print("Monotonic decreasing Q1->Q5: %s"
              % ("YES" if not viol else "NO (violations at Q%d>Q%d pairs: %s)"
                 % (viol[0][0], viol[0][1], viol)))

        # t-stat of Q1-Q5 monthly spread
        s1 = dict(zip(months, [cagrs[0][1][i] for i in range(len(cagrs[0][1]))])) \
            if False else None
        sp = []
        for m in months:
            r1 = ports[1].get(m)
            r5 = ports[5].get(m)
            if r1 is not None and r5 is not None:
                sp.append(r1 - r5)
        if sp:
            mu = sum(sp) / len(sp)
            sd = math.sqrt(sum((x - mu) ** 2 for x in sp) / (len(sp) - 1)) if len(sp) > 1 else 0
            t = mu / (sd / math.sqrt(len(sp))) if sd > 0 else 0.0
            print("Q1-Q5 spread: mean %.3f%%/mo, t-stat %.2f (n=%d)"
                  % (mu * 100, t, len(sp)))
        return means

    vol_means = report_sort("VOL-SORTED PORTFOLIOS (long Q1 = lowest vol)", vol_ports)
    report_sort("BETA-SORTED PORTFOLIOS (long Q1 = lowest beta)", beta_ports)

    # ---------------- verdict ----------------
    q1_mean, q5_mean = vol_means[0], vol_means[4]
    mono = all(vol_means[i] > vol_means[i + 1] for i in range(4))
    print("\n=== VERDICT (vol sort) ===")
    print("Q1 mean monthly %.3f%% vs Q5 %.3f%% -> %s"
          % (q1_mean * 100, q5_mean * 100,
             "PASS (Q1 beats Q5)" if q1_mean > q5_mean else "FAIL"))
    print("Monotone decreasing: %s" % ("PASS" if mono else "FAIL"))
    verdict = "CONFIRMED" if (q1_mean > q5_mean and mono) else "REJECTED"
    print("Low-risk anomaly (vol): %s under pre-registered criteria." % verdict)


if __name__ == "__main__":
    main()

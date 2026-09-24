#!/usr/bin/env python
"""FIS defect-regression tests (cold-start audit, 2026-08-25).

Pins three defects found in tools/research/mean-reversion.py and its writeup
(research/experiments/exp-mean-reversion.md). Each test is deterministic,
stdlib-only, and runs in seconds without the production database.

  T1  Interpolated intra-trade returns inflate Sharpe vs true close marks.
  T2  hash()-salted RNG makes the random-entry control process-dependent;
      the fis independent implementation must never use hash() and must be
      seed-stable for a fixed explicit seed.
  T3  iid per-trade t-statistics overstate significance when trades overlap
      in calendar time vs a Newey-West style correction on the day series.

Run: python tools/test-fis-defects.py
ASCII only. No network. No external dependencies.
"""

from __future__ import annotations

import importlib.util
import math
import os
import random
import subprocess
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASS = []
FAIL = []


def check(name, cond, detail=""):
    if cond:
        PASS.append(name)
        print("PASS  %s %s" % (name, detail))
    else:
        FAIL.append(name)
        print("FAIL  %s %s" % (name, detail))


def sharpe(daily):
    mu = sum(daily) / len(daily)
    var = sum((r - mu) ** 2 for r in daily) / max(len(daily) - 1, 1)
    sd = math.sqrt(var)
    return mu / sd * math.sqrt(252.0) if sd > 0 else 0.0


# ---------------------------------------------------------------------------
# Load the module under audit (hyphen-free name here, direct import works).
# ---------------------------------------------------------------------------

spec = importlib.util.spec_from_file_location(
    "fis_mr", os.path.join(VAULT, "tools", "research", "fis-mr-independent.py"))
fis = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(fis)
except Exception:
    fis = None  # execution imports execution-cost-model via importlib; fine.


# ---------------------------------------------------------------------------
# T1: interpolation inflates Sharpe on a constructed case.
#
# Build one ticker whose daily path inside each trade swings hard (+/-4%/day)
# but whose entry/exit closes give a modest net move. Interpolated slices
# smear the net move linearly -> artificially smooth -> higher Sharpe.
# True close marks carry the real daily variance -> lower Sharpe.
# ---------------------------------------------------------------------------

def make_swingy_closes(n_days=756, seed=11):
    rng = random.Random(seed)
    closes = [100.0]
    for i in range(1, n_days):
        swing = 0.04 if (i // 5) % 2 == 0 else -0.04
        drift = 0.0004                       # mild upward drift
        closes.append(max(1.0, closes[-1] * (1.0 + swing * ((i % 2) * 2 - 1) + drift)))
    return closes


def run_t1():
    closes = make_swingy_closes()
    trades_by_tk = {"FAKE": []}
    # one 10-day trade every 20 days; gross derived FROM the path so both
    # accountings see identical endpoint economics
    e = 15
    while e + 10 < len(closes):
        x = e + 10
        gross = closes[x] / closes[e] - 1.0
        trades_by_tk["FAKE"].append({"sig": e - 1, "e": e, "x": x,
                                     "gross": gross, "net": gross, "hold": 10})
        e += 20
    lengths = {"FAKE": len(closes)}

    interp_daily = fis.book_original_ew(trades_by_tk, lengths)
    # true marks need a data dict keyed like load_universe output
    dates = ["d%05d" % i for i in range(len(closes))]
    data = {"FAKE": {"dates": dates, "closes": closes}}
    true_daily = fis.book_true_marks(data, trades_by_tk)

    s_interp = sharpe(interp_daily)
    s_true = sharpe(true_daily)
    # Endpoint economics are identical by construction; interpolation smears
    # each trade into constant daily slices, removing intra-trade variance.
    # That must (a) preserve the sign of performance and (b) inflate its
    # magnitude -- exactly the distortion that produced Sharpe 3.70 vs a
    # true-mark 1.56 on the production data.
    check("T1_sign_preserved", s_interp * s_true > 0,
          "interp %.2f vs true %.2f" % (s_interp, s_true))
    check("T1_interp_magnitude_inflated", abs(s_interp) > abs(s_true),
          "|interp| %.2f > |true| %.2f" % (abs(s_interp), abs(s_true)))
    eq_i = 1.0
    for r in interp_daily:
        eq_i *= (1 + r)
    eq_t = 1.0
    for r in true_daily:
        eq_t *= (1 + r)
    check("T1_terminal_wealth_close", abs(eq_i - eq_t) / max(eq_i, 1e-9) < 0.02,
          "terminal interp %.4f vs true %.4f" % (eq_i, eq_t))


# ---------------------------------------------------------------------------
# T2: hash() salting is process-dependent; our toolchain must avoid it.
# ---------------------------------------------------------------------------

def run_t2():
    snippet = "print(hash('NVDA') % 10**6)"
    outs = set()
    for seed in ("0", "1"):
        env = dict(os.environ)
        env["PYTHONHASHSEED"] = seed
        r = subprocess.run([sys.executable, "-c", snippet],
                           capture_output=True, text=True, env=env, timeout=60)
        outs.add(r.stdout.strip())
    check("T2_hash_is_process_salted", len(outs) == 2,
          "PYTHONHASHSEED 0 vs 1 gave %d distinct values (expect 2)" % len(outs))

    src_path = os.path.join(VAULT, "tools", "research", "fis-mr-independent.py")
    src = open(src_path, encoding="utf-8").read()
    uses_hash = any(ln.strip().startswith(("seed + hash", "rng=random.Random(seed + hash"))
                    for ln in src.splitlines()) or "Random(seed + hash(" in src
    check("T2_fis_impl_avoids_hash_salting", not uses_hash, "")

    # fixed explicit seed must reproduce trades identically within a process
    closes = [100.0 * (1 + 0.01 * math.sin(i / 7.0)) for i in range(400)]
    rsis = [29.0 if i % 30 == 0 else 60.0 for i in range(400)]
    a = fis.gen_trades(closes, rsis, rng=random.Random(123))
    b = fis.gen_trades(closes, rsis, rng=random.Random(123))
    check("T2_fixed_seed_reproducible",
          [(t["sig"], t["x"]) for t in a] == [(t["sig"], t["x"]) for t in b],
          "n=%d" % len(a))


# ---------------------------------------------------------------------------
# T3: iid per-trade t overstates vs Newey-West on overlapping day series.
# ---------------------------------------------------------------------------

def run_t3():
    # Construct a day series where a cluster of trades all win together
    # (shared market shock) -> per-trade iid t is large, NW-corrected t small.
    rng = random.Random(5)
    daily = []
    for blk in range(24):                    # 24 blocks of 21 days (~1yr)
        shock = rng.choice([-1.0, 1.0]) * 0.004
        for d in range(21):
            daily.append(shock + rng.gauss(0, 0.002))
    n = len(daily)
    mu = sum(daily) / n
    var = sum((r - mu) ** 2 for r in daily) / (n - 1)
    t_iid = mu / math.sqrt(var / n)
    t_nw = fis.nw_tstat(daily, lag=10)
    check("T3_nw_damps_clustered_series", abs(t_nw) < abs(t_iid),
          "iid %.2f vs NW %.2f" % (t_iid, t_nw))


if __name__ == "__main__":
    if fis is None:
        print("SKIP  module load failed; tests cannot run")
        sys.exit(1)
    run_t1()
    run_t2()
    run_t3()
    print("\ntest-fis-defects: %d passed, %d failed" % (len(PASS), len(FAIL)))
    sys.exit(1 if FAIL else 0)

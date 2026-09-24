#!/usr/bin/env python
"""tournament_runner.py -- repaired portfolio primitives; historical FW3 archived.

The default full-run entry point refuses before opening data. The historical
registration/results are preserved; repaired accounting requires a NEW protocol.
Synthetic selftests exercise mechanisms only and do not establish alpha.
The following records the historical execution design, not a current run claim:

Executes the FROZEN spec at Efforts/osanwe-v2-overhaul/_work/fis-data/
tournament-preregistration.json (FIS-FW3-TOURNAMENT-001).  The spec file is
the single source of truth: families, grids, thresholds, negative controls,
state machine, and promotion rules are READ from it, never re-encoded here.

Engine discipline (operator mandate): ONLY the corrected accounting engine
tools/research/mr-corrected.py primitives are reused -- signals(),
simulate(), perf(), nw_t(), clusters().  Prices are DUAL-PRICE
corporate-action-safe closes from _work/fis-data/dual_prices.db
(adjusted_close drives returns/signals; raw_close retained for audit).
Slippage comes from tools/execution-cost-model.py charged into fill prices.
Look-ahead joins go through tools/pit/pit_join.py; the deliberately-future
negative control is REFUSED by that gate by design.

Outputs (JSONL, append): _work/fis-data/tournament-results.jsonl carrying
candidate_result records + state_transition ledger events + HALT records.

STOP-THE-TOURNAMENT: if ANY registered negative control shows spurious
significance under corrected accounting (bh_q < 0.10 AND NW alpha t >= 2),
or the deliberately-future feature is ACCEPTED by the pit gate, the runner
halts, invalidates every result, and emits a HALT record.

Selftest (--selftest) proves full wiring on SYNTHETIC data only: no DB, no
network. ASCII only. Stdlib only. No git operations.

Usage:
    python tools/fis/tournament_runner.py            # full tournament run
    python tools/fis/tournament_runner.py --selftest # synthetic wiring proof
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import random
import sqlite3

# --------------------------------------------------------------------------
# Paths / frozen-spec loading
# --------------------------------------------------------------------------

VAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EFFORTS = os.path.join(VAULT, "Efforts", "osanwe-v2-overhaul")
WORK = os.path.join(EFFORTS, "_work")
FIS_DATA = os.path.join(WORK, "fis-data")
SPEC_PATH = os.path.join(FIS_DATA, "tournament-preregistration.json")
RESULTS_JSONL = os.path.join(FIS_DATA, "tournament-results.jsonl")
FACTORS_DB = os.path.join(WORK, "factors.db")
DUAL_DB = os.path.join(FIS_DATA, "dual_prices.db")


def load_frozen_spec(path=SPEC_PATH):
    """Load and integrity-check the frozen preregistration."""
    with open(path, "rb") as f:
        raw = f.read()
    spec = json.loads(raw.decode("ascii"))
    claimed = spec["integrity"]["content_sha256"]
    probe = json.loads(raw.decode("ascii"))
    probe["integrity"]["content_sha256"] = "0" * 64
    canon = json.dumps(probe, sort_keys=True, indent=2).encode("ascii")
    actual = hashlib.sha256(canon).hexdigest()
    if actual != claimed:
        raise SystemExit(
            "FROZEN SPEC INTEGRITY FAILURE: sha256 %s != recorded %s -- "
            "spec was modified after freeze; tournament refused" % (actual, claimed))
    return spec


# --------------------------------------------------------------------------
# Sanctioned-module imports (mr-corrected primitives, ECM, pit_join)
# --------------------------------------------------------------------------

def _import_module(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def load_engines():
    mrc = _import_module(
        "mrc", os.path.join(VAULT, "tools", "research", "mr-corrected.py"))
    ecm = _import_module(
        "ecm", os.path.join(VAULT, "tools", "execution-cost-model.py"))
    pit = _import_module(
        "pit", os.path.join(VAULT, "tools", "pit", "pit_join.py"))
    return mrc, ecm, pit


# --------------------------------------------------------------------------
# Dual-price corporate-action-safe close loading
# --------------------------------------------------------------------------

def load_dual_closes(dual_db=DUAL_DB, tickers=None):
    """Return {ticker: {date: {'raw': float, 'adj': float}}} from dual_bars.

    adjusted_close is the corporate-action-safe series used for ALL returns
    and signals; raw_close is retained for audit only.
    """
    con = sqlite3.connect("file:%s?mode=ro" % dual_db.replace("\\", "/"), uri=True)
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


def load_ca_index(dual_db=DUAL_DB):
    """Set of (ticker, effective_date) rows with a real corporate action."""
    con = sqlite3.connect("file:%s?mode=ro" % dual_db.replace("\\", "/"), uri=True)
    idx = set((tk.upper(), d) for tk, d in
              con.execute("SELECT ticker, effective_date FROM corporate_actions"))
    con.close()
    return idx


def eligibility_screen(px, cal, ca_index, spec, as_of=None):
    """Screen only the declared decision prefix; never use future survival.

    This is a data-quality screen, not a certified historical membership
    universe. Corporate-action and membership provenance need separate review.
    Historical specs lacking an explicit cutoff are refused.
    """
    el = spec["universe"]["eligibility"]
    as_of = as_of or el.get("as_of")
    if as_of is None:
        raise ValueError("eligibility requires an explicit as_of cutoff")
    _iso_day(as_of)
    if as_of not in cal:
        raise ValueError("eligibility cutoff is not in the supplied calendar")
    min_bars = el["min_bars"]
    if isinstance(min_bars, bool) or not isinstance(min_bars, int) or min_bars < 1:
        raise ValueError("min_bars must be a positive integer")
    adrs = set(el["adr_blocklist"])
    ok, notes = [], []
    for tk, m in sorted(px.items()):
        m = {d: row for d, row in m.items() if d <= as_of}
        if "-USD" in tk:
            notes.append("%s excluded crypto" % tk)
            continue
        if tk in adrs:
            notes.append("%s excluded ADR" % tk)
            continue
        if len(m) < min_bars:
            notes.append("%s excluded bars=%d<%d" % (tk, len(m), min_bars))
            continue
        dates = sorted(m)
        bad = None
        for d in dates:
            _iso_day(d)
            _price(m[d]["adj"])
        for a, b in zip(dates, dates[1:]):
            r = abs(m[b]["adj"] / m[a]["adj"] - 1.0)
            if r > 0.50 and (tk, b) not in ca_index:
                bad = b
                break
        if bad:
            notes.append("%s excluded unexplained |ret|>50%% at %s "
                         "(corporate-action guard)" % (tk, bad))
            continue
        ok.append(tk)
    return ok, notes


# --------------------------------------------------------------------------
# Ledger helpers
# --------------------------------------------------------------------------

def ledger_append(path, rec):
    line = json.dumps(rec, sort_keys=True) + "\n"
    with open(path, "a", encoding="ascii") as f:
        f.write(line)


def state_transition(rec_id, frm, to, note="", extra=None):
    rec = {"record_type": "state_transition", "id": rec_id,
           "from": frm, "to": to, "note": note}
    if extra:
        rec.update(extra)
    ledger_append(RESULTS_JSONL, rec)


VALID_STATES = frozenset([
    "proposed", "preregistered", "in-research", "dev-rejected", "dev-passed",
    "challenge-rejected", "challenge-passed", "shadow-only",
    "production-eligible", "suspended", "retired", "invalidated"])


def check_transition(spec, frm, to):
    rules = spec["promotion_rules"]["allowed_transitions"]
    if to not in VALID_STATES:
        return False
    return to in rules.get(frm, [])


def try_transition(spec, rec_id, frm, to, note=""):
    if not check_transition(spec, frm, to):
        raise SystemExit(
            "LEDGER VIOLATION: illegal transition %s -> %s for %s "
            "(no direct-to-production path permitted)" % (frm, to, rec_id))
    state_transition(rec_id, frm, to, note)
    return to


def halt_tournament(spec, reason, results_seen):
    """STOP-THE-TOURNAMENT: invalidate everything, emit HALT record."""
    for cid in results_seen:
        state_transition(cid, "in-research", "invalidated",
                         "halt: %s" % reason)
    halt = {"record_type": "HALT", "reason": reason,
            "invalidated": sorted(results_seen),
            "note": ("tournament halted by negative-control tripwire; no "
                     "promotion activity until root cause fixed and the "
                     "tournament is re-registered")}
    ledger_append(RESULTS_JSONL, halt)
    print("[HALT] %s" % reason)
    print("[HALT] invalidated %d candidate(s); see %s"
          % (len(results_seen), RESULTS_JSONL))
    return False


# --------------------------------------------------------------------------
# Statistics suite (reuses mr-corrected nw_t; BH across ALL candidates)
# --------------------------------------------------------------------------

def normal_sf_two_sided(t):
    from math import erf
    return 1.0 - erf(abs(t) / math.sqrt(2.0))


def benjamini_hochberg(pvals):
    n = len(pvals)
    order = sorted(range(n), key=lambda i: pvals[i])
    q = [0.0] * n
    prev = 1.0
    for rank, i in enumerate(reversed(order)):
        k = n - rank
        prev = min(prev, min(1.0, pvals[i] * n / k))
        q[i] = prev
    return q


def alpha_regression(cand_rets, base_rets):
    """OLS alpha (ann.) of candidate on equal-weight baseline + NW t."""
    n = min(len(cand_rets), len(base_rets))
    x = base_rets[-n:]
    y = cand_rets[-n:]
    mx = sum(x) / n
    my = sum(y) / n
    vx = sum((a - mx) ** 2 for a in x)
    beta = (sum((a - mx) * (b - my) for a, b in zip(x, y))) / vx if vx > 0 else 0.0
    # RAW residuals (NOT demeaned): their mean IS the daily alpha, so
    # nw_t(resid) tests alpha != 0 -- same convention as mr-corrected
    # factor_adjusted.resid_nw_t.
    resid = [b - beta * a for a, b in zip(x, y)]
    alpha_daily = my - beta * mx
    return {"alpha_ann": alpha_daily * 252.0,
            "beta": beta, "resid": resid}


def block_bootstrap_alpha_ci(mrc, cand_rets, base_rets, draws, blk, seed):
    """Paired stationary-block bootstrap CI on annualized alpha."""
    rng = random.Random(seed)
    n = min(len(cand_rets), len(base_rets))
    y = cand_rets[-n:]
    x = base_rets[-n:]
    lam = 1.0 / blk
    ll = math.log(1.0 - lam)
    alphas = []
    for _ in range(draws):
        sy = []
        sx = []
        while len(sy) < n:
            st = rng.randrange(n)
            ln = max(2, int(math.log(1.0 - rng.random()) / ll))
            sy += y[st:st + ln]
            sx += x[st:st + ln]
        reg = alpha_regression(sy[:n], sx[:n])
        alphas.append(reg["alpha_ann"])
    alphas.sort()
    lo = alphas[int(0.025 * draws)]
    hi = alphas[min(int(0.975 * draws), draws - 1)]
    return {"alpha_ci95": [lo, hi], "draws": draws, "mean_block": blk,
            "seed": seed}


# --------------------------------------------------------------------------
# Family engines (event-slot via mr-corrected; portfolio-book local)
# --------------------------------------------------------------------------

def ma_signals_for_ticker(tk, closes_map, fast, slow, use_ma200, cal_idx_of, cal):
    """Trend-following event signals in mr-corrected signals() format.

    Long while SMA(fast) > SMA(slow) (and close>SMA200 when filter on);
    entry fill at NEXT common-calendar close after cross up; exit at next
    calendar close after cross down. Same-close execution impossible.
    """
    dates = sorted(closes_map)
    pos = {d: i for i, d in enumerate(dates)}
    cl = [closes_map[d] for d in dates]
    out = []
    armed = True
    i = slow
    while i < len(dates) - 1:
        if i - slow < 0:
            break
        sma_f = sum(cl[i - fast + 1:i + 1]) / fast
        sma_s = sum(cl[i - slow + 1:i + 1]) / slow
        cond = sma_f > sma_s
        if use_ma200:
            w200 = cl[max(0, i - 199):i + 1]
            cond = cond and cl[i] > (sum(w200) / len(w200))
        d = dates[i]
        gi = cal_idx_of.get(d)
        if gi is None or gi + 1 >= len(cal):
            i += 1
            continue
        if cond and armed:
            out.append({"tk": tk, "sig": d, "fill": cal[gi + 1],
                        "exit": None, "_sig_i": i})
            armed = False
        elif not cond and not armed:
            # attach exit: next calendar close after cross down
            last = out[-1] if out else None
            if last is not None and last["exit"] is None:
                xg = cal_idx_of.get(d)
                if xg is not None and xg + 1 < len(cal):
                    xd = cal[xg + 1]
                    xp = pos.get(xd)
                    if xp is not None:
                        last["exit"] = xd
            armed = True
        i += 1
    # force-exit any still-open signal at end of ticker data
    for s in out:
        if s["exit"] is None:
            s["exit"] = dates[-1]
    for s in out:
        s.pop("_sig_i", None)
    return [s for s in out if s["fill"] in closes_map]


def run_event_family(family_name, variant_params, mrc, px_adj, cal,
                     slip_mode="stress"):
    """Event-slot family: build signals then REUSE mr-corrected.simulate.

    px_adj: {ticker: {date: adj_close}} -- dual-price safe series only.
    """
    saved_mode = mrc.SLIP_MODE
    mrc.SLIP_MODE = slip_mode
    try:
        sigs = []
        if family_name == "mean_reversion_rsi":
            sigs = mrc.signals(px_adj, cal,
                               variant_params["entry"],
                               variant_params["exit_level"],
                               variant_params["max_hold"])
        elif family_name == "trend_following":
            idx_of = {d: i for i, d in enumerate(cal)}
            for tk, m in sorted(px_adj.items()):
                sigs += ma_signals_for_ticker(
                    tk, m, variant_params["fast_ma"],
                    variant_params["slow_ma"],
                    variant_params["ma200_filter"], idx_of, cal)
        else:
            raise ValueError("unsupported event family %s" % family_name)
        daily, recs, st = mrc.simulate(sigs, px_adj, cal, K=mrc.K_SLOTS)
    finally:
        mrc.SLIP_MODE = saved_mode
    return daily, recs, st, len(sigs)


def month_ends(cal):
    out = []
    cur = None
    for d in cal:
        ym = d[:7]
        if cur is not None and ym != cur:
            out.append(prev_d)
        cur = ym
        prev_d = d
    if cal:
        out.append(cal[-1])
    return out


def _iso_day(value):
    from datetime import date
    if not isinstance(value, str) or len(value) != 10:
        raise ValueError("calendar dates must be canonical ISO dates")
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("calendar dates must be canonical ISO dates")
    return parsed


def _price(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("price must be a finite positive number")
    if not math.isfinite(value) or value <= 0:
        raise ValueError("price must be a finite positive number")
    return float(value)


def _calendar(cal):
    if not isinstance(cal, (list, tuple)) or len(cal) < 2:
        raise ValueError("at least two ordered calendar sessions are required")
    for day in cal:
        _iso_day(day)
    if list(cal) != sorted(set(cal)):
        raise ValueError("calendar must be increasing without duplicate sessions")
    return list(cal)


def _weights(weights, px_adj):
    if not isinstance(weights, dict):
        raise ValueError("target weights must be a dictionary")
    out = {}
    for ticker, value in weights.items():
        if ticker not in px_adj:
            raise ValueError("target asset is absent from supplied prices")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("weights must be finite nonnegative numbers")
        if not math.isfinite(value) or value < 0:
            raise ValueError("weights must be finite nonnegative numbers")
        if value > 0:
            out[ticker] = float(value)
    if sum(out.values()) > 1.0 + 1e-12:
        raise ValueError("leverage is unsupported without a registered financing model")
    return out


def simulate_target_weights(px_adj, cal, targets_by_decision, *,
                            one_way_cost_bps, initial_capital=1.0,
                            initial_weights=None, liquidate_final=True):
    """Self-financing long-only research book. No production eligibility.

    A close-t decision fills at close t+1, after that day's mark. Initial
    weights are a preregistered allocation at the first close, not a signal.
    Cash earns an explicit zero rate. Shares drift until the next fill.
    Missing held/fill prices refuse the run; no zero-return imputation.
    Costs apply to all traded notional, including entry and final liquidation.
    Supplied close series must have declared unit/currency/adjustment provenance;
    this numeric engine cannot certify those metadata or a provider vintage.
    """
    cal = _calendar(cal)
    if not isinstance(px_adj, dict) or not isinstance(targets_by_decision, dict):
        raise ValueError("prices and decisions must be dictionaries")
    for value in [one_way_cost_bps, initial_capital]:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("cost and capital must be finite numbers")
    if not 0 <= one_way_cost_bps < 10000 or initial_capital <= 0:
        raise ValueError("invalid cost rate or initial capital")
    if not isinstance(liquidate_final, bool):
        raise ValueError("liquidate_final must be explicit boolean")
    cost_rate = one_way_cost_bps / 10000.0
    decisions = {}
    for day, target in targets_by_decision.items():
        if day not in cal:
            raise ValueError("decision date is outside the supplied calendar")
        decisions[day] = _weights(target, px_adj)
    first_target = None if initial_weights is None else _weights(initial_weights, px_adj)
    cash = float(initial_capital)
    shares, returns, equity, cash_path, position_path = {}, {}, {}, {}, {}
    trades, total_cost, turnover = [], 0.0, 0.0
    pending = None
    previous_nav = cash

    def close(ticker, day):
        try:
            return _price(px_adj[ticker][day])
        except (KeyError, TypeError):
            raise ValueError("missing held or fill price on " + day) from None

    def rebalance(target, day, decision_day, reason):
        nonlocal cash, shares, total_cost, turnover
        values = {tk: qty * close(tk, day) for tk, qty in shares.items()}
        before = cash + sum(values.values())
        for tk in target:
            close(tk, day)
        names = sorted(set(values) | set(target))
        # E_after + c * sum(abs(w_i * E_after - V_i)) = E_before.
        # With nonnegative weights summing <= 1 and c < 1 this is monotone.
        lo, hi = 0.0, before
        for _ in range(90):
            mid = (lo + hi) / 2.0
            charge = cost_rate * sum(abs(target.get(tk, 0.0) * mid - values.get(tk, 0.0)) for tk in names)
            if mid + charge > before:
                hi = mid
            else:
                lo = mid
        after = (lo + hi) / 2.0
        target_values = {tk: w * after for tk, w in target.items()}
        traded = 0.0
        for tk in names:
            delta = target_values.get(tk, 0.0) - values.get(tk, 0.0)
            traded += abs(delta)
            if abs(delta) > 1e-15 * initial_capital:
                trades.append({"ticker": tk, "decision_date": decision_day,
                               "fill_date": day, "notional": delta,
                               "cost": abs(delta) * cost_rate, "reason": reason})
        charge = traded * cost_rate
        total_cost += charge
        turnover += traded / before if before > 0 else 0.0
        cash = before - charge - sum(target_values.values())
        if cash < -1e-10 * initial_capital:
            raise ValueError("self-financing cash invariant failed")
        cash = max(cash, 0.0)
        shares = {tk: val / close(tk, day) for tk, val in target_values.items()}

    for i, day in enumerate(cal):
        # Mark pre-existing shares first; today's signal cannot earn this move.
        for tk in shares:
            close(tk, day)
        if i == 0 and first_target is not None:
            rebalance(first_target, day, None, "initial_allocation")
        if pending is not None:
            decision_day, target = pending
            rebalance(target, day, decision_day, "rebalance")
        if i == len(cal) - 1 and liquidate_final:
            rebalance({}, day, None, "terminal_liquidation")
        positions = {tk: qty * close(tk, day) for tk, qty in shares.items()}
        nav = cash + sum(positions.values())
        if not math.isfinite(nav) or nav <= 0:
            raise ValueError("invalid or insolvent portfolio NAV")
        returns[day] = nav / previous_nav - 1.0
        equity[day], cash_path[day], position_path[day] = nav, cash, positions
        previous_nav = nav
        pending = (day, decisions[day]) if day in decisions else None
    return {"returns": returns, "equity": equity, "cash": cash_path,
            "positions": position_path, "trades": trades,
            "total_cost": total_cost, "one_way_turnover": turnover,
            "one_way_cost_bps": float(one_way_cost_bps), "cash_rate": 0.0,
            "liquidated_final": liquidate_final,
            "unfilled_terminal_decision": cal[-1] in decisions,
            "scope": "research_simulation_no_alpha_or_production_claim"}


def run_portfolio_book(px_adj, cal, kind, params, base_dates,
                       permute_scores_seed=None, *, one_way_cost_bps=10.0,
                       return_details=False):
    """Score-ranked monthly book, next-close fills, drifting shares and costs.

    Default cost is an ASSUMED 10 bp per one-way traded dollar. A registered
    comparison must pass its explicit cost. Exact-score ties use ticker ID;
    renaming assets can change only those ties, never economic score order.
    base_dates, when supplied, is the preregistered rebalance schedule.
    """
    cal = _calendar(cal)
    if kind not in {"momentum_12_1", "low_vol_quintile"}:
        raise ValueError("unsupported portfolio family")
    if kind == "momentum_12_1":
        form, skip = params["formation_days"], params["skip_days"]
        for value in [form, skip]:
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError("formation and skip must be nonnegative integers")
        if form < 1 or params.get("quintile", "Q5_long") not in {"Q5_long", "Q1_long"}:
            raise ValueError("invalid momentum configuration")
    else:
        win = params["window_days"]
        if isinstance(win, bool) or not isinstance(win, int) or win < 2:
            raise ValueError("volatility window must be an integer >= 2")
    rb_dates = month_ends(cal) if base_dates is None else list(base_dates)
    if len(rb_dates) != len(set(rb_dates)) or any(d not in cal for d in rb_dates):
        raise ValueError("invalid rebalance schedule")
    decisions = {}
    for day in rb_dates:
        scores = {}
        for tk, prices in sorted(px_adj.items()):
            dates = sorted(d for d in prices if d <= day)
            if not dates or dates[-1] != day:
                continue
            if kind == "momentum_12_1":
                if len(dates) < form + skip + 1:
                    continue
                end = len(dates) - 1 - skip
                scores[tk] = _price(prices[dates[end]]) / _price(prices[dates[end - form]]) - 1.0
            else:
                if len(dates) < win + 1:
                    continue
                tail = dates[-win - 1:]
                rs = [_price(prices[b]) / _price(prices[a]) - 1.0 for a, b in zip(tail, tail[1:])]
                mu = sum(rs) / len(rs)
                scores[tk] = sum((r - mu) ** 2 for r in rs) / (len(rs) - 1)
        if len(scores) < 10:
            decisions[day] = {}
            continue
        if permute_scores_seed is not None:
            # Python hash() is process-randomized; use stable date-derived bits.
            seed = int.from_bytes(hashlib.sha256((str(permute_scores_seed) + ":" + day).encode("ascii")).digest()[:8], "big")
            names = sorted(scores)
            values = [scores[tk] for tk in names]
            random.Random(seed).shuffle(values)
            scores = dict(zip(names, values))
        descending = kind == "momentum_12_1" and params.get("quintile", "Q5_long") == "Q5_long"
        ranked = sorted(scores, key=lambda tk: ((-scores[tk]) if descending else scores[tk], tk))
        chosen = ranked[:max(1, len(ranked) // 5)]
        decisions[day] = {tk: 1.0 / len(chosen) for tk in chosen}
    result = simulate_target_weights(px_adj, cal, decisions,
                                     one_way_cost_bps=one_way_cost_bps)
    result["decisions"] = decisions
    return result if return_details else result["returns"]


def book_to_daily(book, cal):
    return [(d, None, book.get(d, 0.0)) for d in cal]


def run_vol_target_book(px_adj, cal, target_vol, lookback, max_lev, *,
                        one_way_cost_bps=10.0, return_details=False):
    """Unlevered vol-target research book; financing is not implemented.

    Each close's trailing sample determines an allocation filled next close.
    Default one-way cost is an ASSUMED 10 bp, including final liquidation.
    """
    cal = _calendar(cal)
    if isinstance(lookback, bool) or not isinstance(lookback, int) or lookback < 2:
        raise ValueError("lookback must be an integer >= 2")
    for value in [target_vol, max_lev]:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("target volatility and allocation cap must be finite")
    if target_vol <= 0 or not 0 < max_lev <= 1:
        raise ValueError("leverage is unsupported without a registered financing model")
    names = sorted(px_adj)
    if not names:
        raise ValueError("volatility baseline universe is empty")
    daily = []
    decisions = {}
    for i, day in enumerate(cal):
        if i:
            try:
                rs = [_price(px_adj[tk][day]) / _price(px_adj[tk][cal[i - 1]]) - 1.0 for tk in names]
            except KeyError:
                raise ValueError("volatility baseline has missing prices") from None
            daily.append(sum(rs) / len(rs))
        window = daily[-lookback:]
        if len(window) < lookback:
            continue
        mu = sum(window) / len(window)
        vol = math.sqrt(sum((r - mu) ** 2 for r in window) / (len(window) - 1) * 252.0)
        scale = min(max_lev, target_vol / vol) if vol > 0 else max_lev
        decisions[day] = {tk: scale / len(names) for tk in names}
    result = simulate_target_weights(px_adj, cal, decisions,
                                     one_way_cost_bps=one_way_cost_bps)
    result["decisions"] = decisions
    return result if return_details else result["returns"]


def baseline_books(px_adj, cal, track2_ok, *, one_way_cost_bps=10.0,
                   return_details=False):
    """True fixed-share buy-and-hold, including initial and terminal costs.

    Default cost is an ASSUMED 10 bp one-way. Named universes are fixed before
    the first close; missing holdings cannot vanish from the denominator.
    """
    groups = {"EW_TRACK2_BH": list(track2_ok)}
    for ticker in ["SPY", "QQQ"]:
        if ticker in px_adj:
            groups[ticker + "_BH"] = [ticker]
    sectors = [t for t in ("XLE", "XLF", "XLI", "XLP", "XLV", "XLY", "XLU", "SMH", "ITA") if t in px_adj]
    if sectors:
        groups["SECTOR_ETF_EW_BH"] = sectors
    books = {}
    for name, members in groups.items():
        if not members or len(members) != len(set(members)):
            raise ValueError("registered baseline requires a nonempty unique universe")
        result = simulate_target_weights(px_adj, cal, {},
                                         one_way_cost_bps=one_way_cost_bps,
                                         initial_weights={tk: 1.0 / len(members) for tk in members})
        books[name] = result if return_details else result["returns"]
    return books


# --------------------------------------------------------------------------
# Negative controls
# --------------------------------------------------------------------------

def control_shuffled_signal(sigs_src_builder, px_adj, cal, seed):
    """Permute each ticker's event dates within the common calendar."""
    rng = random.Random(seed)
    src = sigs_src_builder()
    pool = [s["fill"] for s in src] or cal[1:]
    out = []
    for s in src:
        f = rng.choice(pool)
        if f not in px_adj[s["tk"]]:
            continue
        ex = rng.choice(pool)
        out.append({"tk": s["tk"], "sig": s["sig"], "fill": f, "exit": ex})
    return out


def control_permuted_labels(px_adj, cal, seed):
    """Honest permuted-labels negative control.

    Selection SCORES are randomly permuted across tickers at every
    rebalance while realized returns stay actual: the book remains a fully
    invested quintile of real names (same structural long exposure as the
    real family) but the selection signal carries zero information. Any
    alpha beyond noise must therefore come from leakage, not luck.
    """
    return run_portfolio_book(
        px_adj, cal, "momentum_12_1",
        {"formation_days": 252, "skip_days": 21, "quintile": "Q5_long"},
        month_ends(cal), permute_scores_seed=seed)


def control_time_shifted_feature(px_adj, cal, shift=5):
    """Delay every price series by `shift` calendar positions (stale)."""
    shifted = {}
    for tk, m in px_adj.items():
        ds = sorted(m)
        vals = [m[d] for d in ds]
        newm = {}
        for i, d in enumerate(ds):
            j = i - shift
            if j >= 0:
                newm[d] = vals[j]
        shifted[tk] = newm
    return shifted


def control_noise_feature(px_adj, cal, seed):
    rng = random.Random(seed)
    noisy = {}
    for tk, m in px_adj.items():
        ds = sorted(m)
        v = m[ds[0]]
        newm = {}
        level = v
        for d in ds:
            level *= (1.0 + rng.gauss(0.0, 0.02))   # pure noise walk
            newm[d] = level
        noisy[tk] = newm
    return noisy


def pit_refusal_control(pit, decision_rows, future_days=10):
    """Deliberately-future features MUST be refused by pit_join.

    Every feature row is stamped available_at AFTER THE ENTIRE decision
    horizon (max decision time + future_days): the feature only becomes
    known once the backtest is over -- look-ahead by construction.
    Returns {"refused_all": bool, "joined": int}. refusal == PASS.
    """
    horizon = max(r["t"] for r in decision_rows)
    right = []
    for i, r in enumerate(decision_rows):
        right.append({"sym": r["sym"], "t": r["t"],
                      # LEAK by design: known only after the horizon ends
                      "available_at": horizon + future_days,
                      "val": i})
    joined = pit.join_asof(list(decision_rows), right, on="t",
                           availability_key="available_at", by="sym")
    clean = [j for j in joined if not j.get("_pit_miss")]
    return {"refused_all": len(clean) == 0 and len(joined) == len(decision_rows),
            "joined": len(clean)}


def quarantined_mr_original(px_adj, cal, mrc, entry=30, exit_lvl=50, max_hold=10):
    """KNOWN-INVALID control: OLD (pre-correction) accounting.

    Same-close fills, unlimited capital compounding, half round-trip cost
    once per ROUND TRIP. Expected: inflated Sharpe vs corrected accounting;
    NOT significant under corrected accounting (corrected accounting here =
    mr-corrected simulate on the same signals).
    """
    # OLD (pre-correction) accounting, faithfully reproduced:
    #   same-close fills (fill = signal date itself)
    #   slot-target sizing on EQUITY with NO finite-cash skip -- the
    #   pre-correction engine could always "fund" a new slot from paper
    #   equity, so capacity never bound (mr-corrected C3/C5 violations)
    #   costs charged once per ROUND TRIP instead of once per leg
    sigs = mrc.signals(px_adj, cal, entry, exit_lvl, max_hold)
    old_style = [{"tk": s["tk"], "sig": s["sig"], "fill": s["sig"],
                  "exit": s["exit"]} for s in sigs]
    cash = 1.0
    K = mrc.K_SLOTS
    eq_series = []
    openp = []
    events = {}
    for s in old_style:
        events.setdefault(s["fill"], []).append(s)
    for d in cal:
        done = []
        for p in openp:
            if p["exit_d"] == d:
                c = px_adj[p["tk"]].get(d)
                if c is not None:
                    rt = mrc.slip_bp(p["tk"])          # half round trip...
                    p["val"] *= c * (1 - rt / 10000.0) / p["last_px"]
                    # ...charged ONCE per round trip instead of once/leg:
                    p["val"] /= (1 - rt / 10000.0)      # refund the leg
                cash += p["val"]
                done.append(p)
        for p in done:
            openp.remove(p)
        eq_now = cash + sum(p["val"] for p in openp)
        for s in sorted(events.get(d, []), key=lambda z: z["tk"]):
            if any(q["tk"] == s["tk"] for q in openp):
                continue                                # 1 position/issuer
            c = px_adj[s["tk"]].get(d)
            if c is None:
                continue
            alloc = min(eq_now / K, max(cash, 0.0))     # slot on EQUITY,
            if alloc <= 1e-12:                          # capped by wallet;
                continue                                # no capacity skip
            units_val = alloc / (1 + mrc.slip_bp(s["tk"]) / 10000.0)
            cash -= alloc
            openp.append({"tk": s["tk"], "val": units_val, "last_px": c,
                          "exit_d": s["exit"]})
        for p in openp:
            c = px_adj[p["tk"]].get(d)
            if c is not None:
                p["val"] *= c / p["last_px"]
                p["last_px"] = c
        tot = cash + sum(p["val"] for p in openp)
        # returns vs the LAST OBSERVED total, not the previous calendar
        # entry (the dual-store calendar carries stray non-trading dates;
        # mr-corrected's own daily book uses the same convention)
        prev = eq_series[-1][1] if eq_series else 1.0
        if prev > 0 and tot > 0:
            eq_series.append((d, tot, tot / prev - 1.0))
    old_sharpe = mrc.perf(eq_series)["sharpe"]
    n_trades = len(old_style)
    return old_sharpe if n_trades > 20 else 0.0


# --------------------------------------------------------------------------
# Candidate evaluation + stats application
# --------------------------------------------------------------------------

def evaluate_candidate(mrc, name, family, daily, baseline_rets,
                       boot_draws, boot_blk, boot_seed):
    perf = mrc.perf(daily)
    rets = [r for _, _, r in daily]
    t_nw = mrc.nw_t(rets)
    reg = alpha_regression(rets, baseline_rets)
    t_alpha = mrc.nw_t(reg["resid"])
    bt = block_bootstrap_alpha_ci(mrc, rets, baseline_rets,
                                  boot_draws, boot_blk, boot_seed)
    expo = sum(1 for r in rets if abs(r) > 1e-12) / max(len(rets), 1)
    return {
        "perf": perf,
        "nw_t_mean_return": t_nw,
        "alpha_vs_ew_baseline": {
            "alpha_ann": reg["alpha_ann"], "beta": reg["beta"],
            "nw_alpha_t": t_alpha},
        "bootstrap": bt,
        "exposure_time_in_market": expo,
        "turnover_x_per_year": perf.get("_na_turnover", None),
    }


def apply_bh_and_thresholds(results, spec):
    thr = spec["statistics"]["failure_thresholds"]
    ids = [r["candidate_id"] for r in results]
    pvals = [normal_sf_two_sided(r["stats"]["alpha_vs_ew_baseline"]["nw_alpha_t"])
             for r in results]
    qs = benjamini_hochberg(pvals)
    for r, q in zip(results, qs):
        r["bh_q_value"] = q
        t = r["stats"]["alpha_vs_ew_baseline"]["nw_alpha_t"]
        r["fail_bh_q_ge_0.10"] = q >= 0.10
        r["fail_nw_alpha_t_lt_2"] = t < 2.0
        r["dev_pass"] = (q < 0.10) and (t >= 2.0)
    return results


def assess_negative_controls(reports, required=None):
    """Inspect every registered control before declaring the run clean.

    Negative alpha on a degraded feature is recorded, not grounds for skipping
    later controls. Missing/malformed evidence is a failed control, not a pass.
    This pure verdict does not mutate a ledger or release evaluation data.
    """
    required = list(required) if required is not None else [
        "ctrl-shuffled-signal", "ctrl-permuted-labels",
        "ctrl-time-shifted-feature", "ctrl-noise-feature",
        "ctrl-deliberately-future-feature", "ctrl-quarantined-mr-original"]
    violations, checked = [], []
    for cid in sorted(set(required) | set(reports)):
        checked.append(cid)
        rep = reports.get(cid)
        if not isinstance(rep, dict):
            violations.append(cid + ": missing control result")
            continue
        if cid == "ctrl-deliberately-future-feature":
            gate = rep.get("pit_gate", {})
            if not isinstance(gate, dict) or gate.get("refused_all") is not True or gate.get("joined") != 0:
                violations.append(cid + ": future features were not verifiably refused")
            continue
        try:
            interval = rep["bootstrap"]["alpha_ci95"]
            if not isinstance(interval, (list, tuple)) or len(interval) != 2:
                raise ValueError("invalid interval")
            lo, hi = interval
            alpha = rep["alpha_vs_ew_baseline"]["alpha_ann"]
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in [lo, hi, alpha]) or lo > hi:
                raise ValueError("invalid statistic")
            if lo > 0.0:
                violations.append(cid + ": positive alpha interval excludes zero")
        except (KeyError, TypeError, ValueError):
            violations.append(cid + ": malformed control statistics")
        if cid == "ctrl-quarantined-mr-original" and rep.get("old_inflation_present_as_expected") is not True:
            violations.append(cid + ": known-invalid accounting was not detected")
    if not checked:
        violations.append("no registered controls were checked")
    return {"clean": not violations, "checked": checked, "violations": violations}


# --------------------------------------------------------------------------
# Full tournament run
# --------------------------------------------------------------------------

def run_tournament():
    raise ValueError(
        "Historical FW3 tournament rerun refused: its frozen registration does "
        "not cover repaired ranking, costs, temporal eligibility or chronological "
        "partitions. Use a newly registered comparison; no database was opened "
        "and no historical results were changed.")


def _historical_tournament_body():
    """Preserved development implementation; not a supported execution API.

    Calling it directly is also refused so imports cannot bypass the CLI gate.
    The original body remains below for forensic review of archived results.
    """
    raise ValueError("historical tournament body is archived and cannot run")
    spec = load_frozen_spec()
    mrc, ecm, pit = load_engines()

    tracks = {t["track"]: t for t in spec["universe"]["tracks"]}
    if tracks["Track-1"].get("status") == "BLOCKED":
        print("[universe] Track-1 BLOCKED (%s) -- running WITHOUT survivorship "
              "control; recorded in every result header."
              % tracks["Track-1"]["block_reason"])

    px_dual = load_dual_closes()
    ca_index = load_ca_index()
    # calendar from the dual store; screen runs on the DUAL dict
    cal = sorted(set(d for m in px_dual.values() for d in m))
    track2_all = sorted(t for t in px_dual if t not in ("SPY", "QQQ"))
    track2_ok, notes = eligibility_screen(px_dual, cal, ca_index, spec)
    track3 = [t for t in tracks["Track-3"]["members"] if t in px_dual]
    for n in notes:
        print("[eligibility] %s" % n)
    print("[universe] eligible=%d track3=%d calendar=%d days"
          % (len(track2_ok), len(track3), len(cal)))

    # run on the corporate-action-safe adjusted series ONLY
    keep = set(track2_ok) | set(track3)
    px_adj = {tk: {d: v["adj"] for d, v in m.items()}
              for tk, m in px_dual.items() if tk in keep}
    cal = sorted(set(d for m in px_adj.values() for d in m))

    baselines = baseline_books(px_adj, cal, track2_ok)
    ew_base_rets = [baselines["EW_TRACK2_BH"][d] for d in cal]

    stats_cfg = spec["statistics"]
    boot_draws = stats_cfg["bootstrap"]["draws_full_run"]

    results = []       # dicts with candidate_id, family, stats
    results_ids = []

    # ---- registered candidates ------------------------------------------
    for fam in spec["strategy_families"]:
        fname = fam["family"]
        if fam.get("role") == "reference_only":
            if fname == "cash":
                cid = "%s/zero_return" % fname
                daily = [(d, None, 0.0) for d in cal]
                st = evaluate_candidate(mrc, "zero", fname, daily,
                                        ew_base_rets, boot_draws,
                                        stats_cfg["bootstrap"]["mean_block"],
                                        stats_cfg["bootstrap"]["seed"])
                st["reference_only"] = True
                results.append({"candidate_id": cid, "family": fname,
                                "variant": "zero_return", "stats": st})
                results_ids.append(cid)
                continue
            for member in fam["members"]:
                cid = "%s/%s" % (fname, member)
                book = baselines.get(member)
                if book is None:
                    continue
                daily = [(d, None, book[d]) for d in cal]
                st = evaluate_candidate(mrc, member, fname, daily,
                                        ew_base_rets, boot_draws,
                                        stats_cfg["bootstrap"]["mean_block"],
                                        stats_cfg["bootstrap"]["seed"])
                st["reference_only"] = True
                results.append({"candidate_id": cid, "family": fname,
                                "variant": member, "stats": st})
                results_ids.append(cid)
            continue
        grid_keys = sorted(fam.get("grid", {}).keys()) if "grid" in fam else []
        if fname == "mean_reversion_rsi":
            variants = fam["variants"]
            combos = [(vname, dict(vparams)) for vname, vparams in variants.items()]
        elif grid_keys:
            # only LIST-valued grid entries are swept; scalar/string values
            # (e.g. rebalance policy) are fixed configuration
            keys = [k for k in grid_keys if isinstance(fam["grid"][k], list)]
            stack = [{}]
            for kk in keys:
                nxt = []
                for partial in stack:
                    for val in fam["grid"][kk]:
                        d2 = dict(partial)
                        d2[kk] = val
                        nxt.append(d2)
                stack = nxt
            for c in stack:
                for k, v in fam["grid"].items():
                    if k not in c:
                        c[k] = v
            combos = [(json.dumps(c, sort_keys=True)[:60], c) for c in stack]
        else:
            continue

        for cname, cparams in combos:
            cid = "%s/%s" % (fname, cname)
            if fname == "mean_reversion_rsi":
                daily, recs, simst, nsig = run_event_family(
                    fname, cparams, mrc, px_adj, cal)
            elif fname == "trend_following":
                daily, recs, simst, nsig = run_event_family(
                    fname, cparams, mrc, px_adj, cal)
            elif fname == "momentum_12_1":
                book = run_portfolio_book(px_adj, cal, fname,
                                          dict(cparams, quintile=cparams.get(
                                              "quintile", "Q5_long")),
                                          month_ends(cal))
                daily = book_to_daily(book, cal)
                recs, simst, nsig = [], {}, 0
            elif fname == "low_vol_quintile":
                book = run_portfolio_book(px_adj, cal, fname, cparams,
                                          month_ends(cal))
                daily = book_to_daily(book, cal)
                recs, simst, nsig = [], {}, 0
            elif fname == "vol_target_passive":
                book = run_vol_target_book(
                    px_adj, cal, cparams["target_ann_vol"],
                    cparams["vol_lookback_days"], cparams["max_leverage"])
                daily = book_to_daily(book, cal)
                recs, simst, nsig = [], {}, 0
            else:
                continue
            st = evaluate_candidate(mrc, cname, fname, daily, ew_base_rets,
                                    boot_draws,
                                    stats_cfg["bootstrap"]["mean_block"],
                                    stats_cfg["bootstrap"]["seed"])
            if simst:
                st["turnover_x_per_year"] = (
                    simst.get("gross_traded", 0.0)
                    / max(len(daily) / 252.0, 1e-9))
                st["exposure_time_in_market"] = (
                    simst.get("exposed_days", 0) / max(len(daily), 1))
            st["n_signals_or_components"] = nsig
            st["sim_stats"] = simst
            st["clusters"] = mrc.clusters(recs) if recs else None
            results.append({"candidate_id": cid, "family": fname,
                            "variant": cname, "params": cparams, "stats": st})
            results_ids.append(cid)
            print("[run] %-45s alpha %+.2f%% NW-t %.2f Shp %.2f"
                  % (cid, 100 * st["alpha_vs_ew_baseline"]["alpha_ann"],
                     st["alpha_vs_ew_baseline"]["nw_alpha_t"],
                     st["perf"]["sharpe"]))

    # ---- negative controls ------------------------------------------------
    ctrl_reports = {}

    def corrected_eval_of_book(book):
        daily = [(d, None, book.get(d, 0.0)) for d in cal]
        return evaluate_candidate(mrc, "ctrl", "negative_control", daily,
                                  ew_base_rets, boot_draws,
                                  stats_cfg["bootstrap"]["mean_block"],
                                  stats_cfg["bootstrap"]["seed"])

    # ctrl-shuffled-signal: permuted fills through CORRECTED simulate
    shuf_sigs = control_shuffled_signal(
        lambda: mrc.signals(px_adj, cal, 30, 50, 10), px_adj, cal,
        stats_cfg["bootstrap"]["seed"] + 1)
    _, _, _, _ns = (None,) * 4
    saved = mrc.SLIP_MODE
    mrc.SLIP_MODE = "stress"
    sdaily, srecs, sst = mrc.simulate(shuf_sigs, px_adj, cal)
    mrc.SLIP_MODE = saved
    ctrl_reports["ctrl-shuffled-signal"] = evaluate_candidate(
        mrc, "shuffled", "negative_control", sdaily, ew_base_rets, boot_draws,
        stats_cfg["bootstrap"]["mean_block"], stats_cfg["bootstrap"]["seed"])

    # ctrl-permuted-labels
    pl = control_permuted_labels(px_adj, cal, stats_cfg["bootstrap"]["seed"] + 2)
    ctrl_reports["ctrl-permuted-labels"] = corrected_eval_of_book(pl)

    # ctrl-time-shifted-feature (+5 stale days)
    ts_px = control_time_shifted_feature(px_adj, cal, shift=5)
    tsigs = mrc.signals(ts_px, cal, 30, 50, 10)
    tdaily, _, _ = mrc.simulate(tsigs, ts_px, cal)
    ctrl_reports["ctrl-time-shifted-feature"] = evaluate_candidate(
        mrc, "timeshift", "negative_control", tdaily, ew_base_rets, boot_draws,
        stats_cfg["bootstrap"]["mean_block"], stats_cfg["bootstrap"]["seed"])

    # ctrl-noise-feature
    nz_px = control_noise_feature(px_adj, cal, stats_cfg["bootstrap"]["seed"] + 3)
    nsigs = mrc.signals(nz_px, cal, 30, 50, 10)
    ndaily, _, _ = mrc.simulate(nsigs, nz_px, cal)
    ctrl_reports["ctrl-noise-feature"] = evaluate_candidate(
        mrc, "noise", "negative_control", ndaily, ew_base_rets, boot_draws,
        stats_cfg["bootstrap"]["mean_block"], stats_cfg["bootstrap"]["seed"])

    # ctrl-deliberately-future-feature: pit_join MUST refuse
    dec_rows = []
    spy = px_adj.get("SPY") or px_adj[track3[0]]
    ds = sorted(spy)
    for i in range(0, min(len(ds), 200), 5):
        dec_rows.append({"sym": "SPY", "t": i})
    fut = pit_refusal_control(pit, dec_rows)
    ctrl_reports["ctrl-deliberately-future-feature"] = {
        "pit_gate": fut, "passed": fut["refused_all"]}
    print("[control] deliberately-future: refused_all=%s joined=%d"
          % (fut["refused_all"], fut["joined"]))

    # ctrl-quarantined-mr-original: old accounting vs corrected
    corr_sigs = mrc.signals(px_adj, cal, 30, 50, 10)
    cdaily, crecs, _ = mrc.simulate(corr_sigs, px_adj, cal)
    corr_sharpe = mrc.perf(cdaily)["sharpe"]
    old_sharpe = quarantined_mr_original(px_adj, cal, mrc)
    cev = evaluate_candidate(mrc, "quarantined", "negative_control", cdaily,
                             ew_base_rets, boot_draws,
                             stats_cfg["bootstrap"]["mean_block"],
                             stats_cfg["bootstrap"]["seed"])
    inflation_present = old_sharpe > corr_sharpe * 1.05
    ctrl_reports["ctrl-quarantined-mr-original"] = {
        **cev,
        "old_accounting_sharpe": old_sharpe,
        "corrected_accounting_sharpe": corr_sharpe,
        "old_inflation_present_as_expected": inflation_present}

    # ---- BH across ALL registered candidates ------------------------------
    apply_bh_and_thresholds(results, spec)

    # ---- BH q-values for the controls too ---------------------------------
    ctrl_ids = [c for c in ctrl_reports
                if c != "ctrl-deliberately-future-feature"]
    ctrl_p = [normal_sf_two_sided(ctrl_reports[c]["alpha_vs_ew_baseline"]
                                  ["nw_alpha_t"]) for c in ctrl_ids]
    ctrl_q = benjamini_hochberg(ctrl_p)
    for c, q in zip(ctrl_ids, ctrl_q):
        ctrl_reports[c]["bh_q_value"] = q

    # Inspect all controls, including after a negative-alpha degraded control.
    control_verdict = assess_negative_controls(ctrl_reports)
    trip = "; ".join(control_verdict["violations"]) if not control_verdict["clean"] else None

    # ---- write JSONL ------------------------------------------------------
    hdr = {"record_type": "tournament_header",
           "spec_id": spec["spec_id"],
           "content_sha256_verified": True,
           "track1_status": "BLOCKED pending delisted data",
           "cost_mode": "stress",
           "k_slots": 10,
           "eligible_universe_n": len(track2_ok)}
    ledger_append(RESULTS_JSONL, hdr)

    for r in results:
        ledger_append(RESULTS_JSONL, {"record_type": "candidate_result", **r})
        state_transition(r["candidate_id"], "proposed", "preregistered",
                         "frozen spec registration")
        state_transition(r["candidate_id"], "preregistered", "in-research",
                         "tournament run")
        to_state = "dev-passed" if r["dev_pass"] else "dev-rejected"
        state_transition(r["candidate_id"], "in-research", to_state,
                         "bh_q=%.4g nw_alpha_t=%.2f"
                         % (r["bh_q_value"],
                            r["stats"]["alpha_vs_ew_baseline"]["nw_alpha_t"]))
        if r["dev_pass"]:
            # promotion may ONLY proceed via firewall evaluate_submission
            fw = os.path.join(VAULT, "tools", "firewall",
                              "evaluate_submission.py")
            if os.path.exists(fw):
                state_transition(r["candidate_id"], "dev-passed",
                                 "challenge-rejected",
                                 "firewall evaluator present but invocation "
                                 "deferred to operator review")
            else:
                state_transition(r["candidate_id"], "dev-passed",
                                 "dev-passed",
                                 "HOLD: challenge blocked -- firewall "
                                 "evaluate_submission module absent; no "
                                 "advancement possible")

    ledger_append(RESULTS_JSONL, {"record_type": "negative_controls",
                                  **{k: v for k, v in ctrl_reports.items()}})

    if trip:
        return halt_tournament(spec, trip, results_ids +
                               ["ctrl-" + c for c in ctrl_reports])

    passed = [r["candidate_id"] for r in results if r["dev_pass"]]
    summary = {"record_type": "tournament_summary",
               "candidates": len(results),
               "dev_passed": passed,
               "controls_clean": True,
               "halted": False}
    ledger_append(RESULTS_JSONL, summary)
    print("[done] %d candidates; dev-pass: %s" % (len(results), passed or "NONE"))
    return True


# --------------------------------------------------------------------------
# Selftest: synthetic wiring proof (NO db, NO network)
# --------------------------------------------------------------------------

def selftest():
    import hashlib  # noqa: F401  (used by loader path below)
    failures = []

    def check(cond, msg):
        print(("PASS " if cond else "FAIL ") + msg)
        if not cond:
            failures.append(msg)

    # --- synthetic universe: GBM-ish prices, 6 tickers x 1500 days -------
    rng = random.Random(42)
    cal = []
    y, mo, dy = 2020, 1, 1
    from datetime import date, timedelta
    d = date(2018, 1, 1)
    while len(cal) < 1500:
        d += timedelta(days=1)
        if d.weekday() < 5:
            cal.append(d.isoformat())
    tickers = ["AAA", "BBB", "CCC", "DDD", "SPY", "QQQ"]
    px_adj = {}
    for i, tk in enumerate(tickers):
        lvl = 100.0
        m = {}
        drift = 0.0002 * (i - 2)
        for dt in cal:
            lvl *= 1.0 + drift + rng.gauss(0.0, 0.015)
            m[dt] = lvl
        px_adj[tk] = m

    mrc, ecm, pit = load_engines()

    # 1) mr-corrected simulate runs on synthetic event signals
    sigs = mrc.signals(px_adj, cal, 30, 50, 5)
    check(len(sigs) > 0, "signals() produced events (%d)" % len(sigs))
    saved = mrc.SLIP_MODE
    mrc.SLIP_MODE = "stress"
    daily, recs, st = mrc.simulate(sigs, px_adj, cal)
    mrc.SLIP_MODE = saved
    check(len(daily) == len(cal), "daily book spans calendar")
    check(all(math.isfinite(r) for _, _, r in daily), "returns finite")
    check(st["admitted"] > 0, "admissions occurred")
    # no same-close fills anywhere
    check(all(s["fill"] > s["sig"] for s in sigs),
          "next-close execution enforced (fill > sig)")

    # 2) trend-following signal builder
    idx_of = {d: i for i, d in enumerate(cal)}
    tf = ma_signals_for_ticker("SPY", px_adj["SPY"], 20, 50, False, idx_of, cal)
    check(isinstance(tf, list), "trend signals built")
    check(all(s["fill"] > s["sig"] for s in tf),
          "trend signals respect next-close")

    # 3) perf/nw_t/clusters reuse
    perf = mrc.perf(daily)
    t = mrc.nw_t([r for _, _, r in daily])
    cl = mrc.clusters(recs)
    check(math.isfinite(perf["sharpe"]) and math.isfinite(t),
          "perf/nw_t finite")
    check(cl["n_clusters"] > 0, "clusters computed")

    # 4) alpha regression + BH + thresholds
    base = baseline_books(px_adj, cal, ["AAA", "BBB", "CCC", "DDD"])
    ew = [base["EW_TRACK2_BH"][d] for d in cal]
    ev = evaluate_candidate(mrc, "synthetic", "test", daily, ew, 40, 10, 7)
    check(ev["bootstrap"]["draws"] == 40 and
          len(ev["bootstrap"]["alpha_ci95"]) == 2, "bootstrap CI produced")
    fake_results = [
        {"candidate_id": "a", "stats": {"alpha_vs_ew_baseline":
                                        {"nw_alpha_t": 4.0}}},
        {"candidate_id": "b", "stats": {"alpha_vs_ew_baseline":
                                        {"nw_alpha_t": 0.1}}},
        {"candidate_id": "c", "stats": {"alpha_vs_ew_baseline":
                                        {"nw_alpha_t": 2.5}}},
        {"candidate_id": "d", "stats": {"alpha_vs_ew_baseline":
                                        {"nw_alpha_t": -3.0}}},
    ]
    spec_stub = {"statistics": {"failure_thresholds": {}}}
    apply_bh_and_thresholds(fake_results, spec_stub)
    qs = [r["bh_q_value"] for r in fake_results]
    check(all(0.0 <= q <= 1.0 for q in qs), "BH q-values in [0,1]")
    strongest = max(fake_results, key=lambda r: r["stats"]["alpha_vs_ew_baseline"]
                    ["nw_alpha_t"])
    check(strongest["bh_q_value"] <= min(qs) + 1e-12,
          "BH monotone: strongest t has smallest q")

    # 5) portfolio-book engines run
    mb = run_portfolio_book(px_adj, cal, "momentum_12_1",
                            {"formation_days": 252, "skip_days": 21,
                             "quintile": "Q5_long"}, month_ends(cal))
    check(len(mb) > 0, "momentum book produced")
    lv = run_portfolio_book(px_adj, cal, "low_vol_quintile",
                            {"window_days": 126}, month_ends(cal))
    check(len(lv) > 0, "low-vol book produced")
    vt = run_vol_target_book(px_adj, cal, 0.10, 63, 1.0)
    check(len(vt) == len(cal), "vol-target book spans calendar")

    # 6) pit gate REFUSES deliberately-future features (PASS == refusal)
    rows = [{"sym": "AAA", "t": i} for i in range(10, 120, 7)]
    fut = pit_refusal_control(pit, rows, future_days=10)
    check(fut["refused_all"], "pit gate refuses future-stamped features")
    # sanity: non-future features ARE joinable (gate is not vacuous)
    ok_rows = [{"sym": "AAA", "t": i} for i in range(30, 130, 7)]
    right = [{"sym": "AAA", "t": i - 5, "available_at": i - 5, "val": 1}
             for i in range(10, 140, 7)]
    joined = pit.join_asof(ok_rows, right, on="t",
                           availability_key="available_at", by="sym")
    check(any(not j.get("_pit_miss") for j in joined),
          "pit gate admits timely features (non-vacuous)")

    # 7) quarantined old-accounting control wires up
    old_sh = quarantined_mr_original(px_adj, cal, mrc)
    check(math.isfinite(old_sh), "quarantined old-accounting sharpe finite")

    # 8) state-machine validator refuses direct-to-production
    spec_min = {"promotion_rules": {"allowed_transitions": {
        "dev-passed": ["challenge-passed", "challenge-rejected"],
        "challenge-passed": ["shadow-only"],
        "shadow-only": ["production-eligible", "suspended"]}}}
    check(not check_transition(spec_min, "dev-passed", "production-eligible"),
          "state machine refuses dev-passed -> production-eligible")
    check(check_transition(spec_min, "dev-passed", "challenge-passed"),
          "legal transition accepted")

    # 9) HALT path writes records without touching real outputs
    global RESULTS_JSONL
    tmp = os.path.join(os.environ.get("TEMP", "."), "fis-tourney-selftest.jsonl")
    if os.path.exists(tmp):
        os.remove(tmp)
    real_out = RESULTS_JSONL
    RESULTS_JSONL = tmp
    try:
        keep = halt_tournament(spec_min, "selftest synthetic tripwire",
                               ["cand-x"])
        check(keep is False, "halt_tournament returns halted=False status")
        lines = [json.loads(l) for l in open(tmp)]
        check(any(l["record_type"] == "HALT" for l in lines),
              "HALT record written")
        check(any(l.get("to") == "invalidated" for l in lines),
              "invalidation transitions written")
    finally:
        RESULTS_JSONL = real_out
        if os.path.exists(tmp):
            os.remove(tmp)

    # 10) frozen spec loads and verifies (real file, read-only)
    spec = load_frozen_spec()
    check(spec["spec_id"] == "FIS-FW3-TOURNAMENT-001",
          "frozen spec loads with verified integrity hash")

    print("---")
    if failures:
        print("SELFTEST FAILED (%d)" % len(failures))
        return 1
    print("SELFTEST PASSED")
    return 0


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true",
                    help="prove wiring on synthetic data (no db/network)")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    try:
        ok = run_tournament()
    except ValueError as exc:
        print("REFUSED: %s" % exc)
        return 2
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

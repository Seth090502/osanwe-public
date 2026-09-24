#!/usr/bin/env python
"""portfolio_engine.py -- S4 passive-core rebalance engine (FIS).

Passive/reference portfolio construction: with NO active alpha in scope,
portfolio changes are goal-based rebalancing only -- band-triggered trades
back toward the frozen target allocation, never directional bets.

Inputs
------
portfolio : dict
    {
      "cash": <usd>,
      "cash_account": <explicit account, optional>,
      "cash_by_account": {account: <usd>, ...},  # optional; sums to cash
      "holdings": [
        {"ticker", "security_symbol" (optional), "issuer", "asset_class", "account", "quantity",
         "price", "lots": [{"lot_id","quantity","cost_basis",
                            "acquire_date","term"}...]}
      ]
    }
targets     : {asset_class: target_weight}   (weights incl "cash")
bands       : {asset_class: {"low": pp, "high": pp}} absolute
              percentage-point corridors around target; outside either
              edge => band breach.
constraints : {"max_single_issuer_pct","min_cash_pct","max_turnover_pct"}

Behaviour (operator mandate)
----------------------------
* propose_rebalance(): band-triggered trades. G2 lot selection is a
  deterministic gain-minimization heuristic, not a global tax optimizer:
  SPECIFIC_ID, HIGHEST LOSS FIRST (most-negative
  unrealized gain per share consumed before lesser losses, then gains).
* Execution costs charged through the sanctioned ECM
  (tools/execution-cost-model.py), imported the same way
  tournament_runner.load_engines() imports it. Each trade leg is charged
  the ECM ROUND-TRIP dollar figure -- deliberately conservative (a
  rebalance leg is typically held long, so charging the round trip builds
  in a buffer).
* Positions are keyed by (account, ticker); security_symbol reaches ECM
  unchanged by account labels. Scalar cash counts toward portfolio value;
  deployment requires cash_account/cash_by_account or the explicit account
  argument. Sales fund BUYs only inside the same account. No transfers are
  inferred. Costs and the portfolio cash reserve are budgeted before BUYs.
* Trade construction order:
    1. pro-rata SELLs inside each over-band class down to target;
    2. BUYs inside each under-band class, routed ONLY into issuer-cap
       headroom (the plan must not manufacture its own violation);
    3. POST-TRADE forced trims: any issuer still above the single-issuer
       cap after steps 1-2 is trimmed by exactly its overage, realizing
       whatever the actual lots dictate (captured through G2 selection).
* Constraints are applied POST-HOC to the proposed end state and any
  violation REJECTS the whole proposal (status="rejected"); nothing is
  silently clipped.
* EVERY result carries a no_action alternative with an IDENTICAL metric
  block (same keys, same semantics), so accept/reject is always a
  side-by-side comparison even when the proposal is rejected.
* independent_recalculation() re-derives post-trade weights / realized
  gains / ECM cost / turnover through a SECOND code path (naive full-state
  replay of the recorded trades, no reuse of planner arithmetic) and
  asserts equality with the planner's numbers. Any mismatch raises
  AssertionError => internal error; the plan must never be surfaced.
* explanation() renders plain-language WHY-TRADE / WHY-WAIT / REJECTED /
  INSTABILITY blocks citing concrete numbers.

Stability rule: when a class weight sits within INSTABILITY_EPS_PP of a
band edge, the plan carries an instability flag instead of silently
flipping between trade/no-trade on noise. Proposals are fully
deterministic (sorted iteration everywhere), so repeated calls cannot
flip-flop.

ASCII only. Stdlib only. No network, no git operations.

Usage:
    python tools/fis/portfolio_engine.py --selftest
"""

from __future__ import annotations

import copy
import importlib.util
import json
import math
import os
import sys

# The approval state machine is the sole owner of "may this be acted on?".
# Imported, never reimplemented: the enforcement boundary in this module
# and the one in the API/UI layers must be the same code.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import approval  # noqa: E402

# --------------------------------------------------------------------------
# Paths / sanctioned ECM import (same pattern as tournament_runner)
# --------------------------------------------------------------------------

VAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ECM_PATH = os.path.join(VAULT, "tools", "execution-cost-model.py")
SELFTEST_OUT = os.path.join(
    VAULT, "_work", "fis-data", "portfolio-engine-selftest.json")

_INSTABILITY_EPS_PP = 0.0005   # 5 bp of portfolio: "on the band edge"
                               # (fraction units -- weights are fractions)
_MIN_TRADE_USD = 1.0         # dust filter
_DEFAULT_TAX = {"long": 0.15, "short": 0.24}


def _load_ecm(path=ECM_PATH):
    """Load the sanctioned execution-cost model module."""
    spec = importlib.util.spec_from_file_location("ecm_portfolio", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------
# State helpers (planner path A)
# --------------------------------------------------------------------------

def _holding_value(h):
    return float(h["quantity"]) * float(h["price"])


def _position_key(h):
    """Account identity is separate from the market/security symbol."""
    return (str(h.get("account") or "UNSPECIFIED"), str(h["ticker"]))


def _positions(holdings):
    positions = {}
    for h in holdings:
        key = _position_key(h)
        if key in positions:
            raise ValueError("duplicate position (account, ticker): %r" % (key,))
        positions[key] = h
    return positions


def _security_symbol(h):
    return str(h.get("security_symbol") or h["ticker"])


def _number(value, label):
    if isinstance(value, bool):
        raise ValueError("%s must be a finite number" % label)
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("%s must be a finite number" % label) from None
    if not math.isfinite(result):
        raise ValueError("%s must be a finite number" % label)
    return result


def _cash_scope(portfolio, account=None):
    """Unallocated cash counts toward NAV but never implies a transfer."""
    cash = _number(portfolio.get("cash", 0.0), "cash")
    if cash < 0:
        raise ValueError("cash must be nonnegative")
    supplied = portfolio.get("cash_by_account")
    if supplied is not None:
        if not isinstance(supplied, dict):
            raise ValueError("cash_by_account must be a mapping")
        balances = {}
        for key, value in supplied.items():
            if not isinstance(key, str) or not key.strip() or key == "UNSPECIFIED":
                raise ValueError("cash_by_account requires explicit account identifiers")
            balances[key] = _number(value, "cash_by_account balance")
            if balances[key] < 0:
                raise ValueError("cash_by_account balances must be nonnegative")
        if not math.isclose(sum(balances.values()), cash, rel_tol=1e-12, abs_tol=1e-6):
            raise ValueError("cash_by_account must reconcile exactly to scalar cash")
        return balances, 0.0, "explicit cash_by_account"
    owner = portfolio.get("cash_account") or account
    if owner and str(owner) != "UNSPECIFIED":
        return {str(owner): cash}, 0.0, "explicit cash_account/account"
    return {}, cash, "scalar cash unallocated; no account transfer assumed"


def _total_value(portfolio):
    return float(portfolio.get("cash", 0.0)) + sum(
        _holding_value(h) for h in portfolio["holdings"])


def _class_weights(portfolio):
    """Path-A weights: accumulate per class, single division pass."""
    v_total = _total_value(portfolio)
    acc = {}
    for h in portfolio["holdings"]:
        acc[h["asset_class"]] = acc.get(h["asset_class"], 0.0) + _holding_value(h)
    acc["cash"] = acc.get("cash", 0.0) + float(portfolio.get("cash", 0.0))
    return {k: v / v_total for k, v in sorted(acc.items())}, v_total


def _split_term_tax(realized_events, tax_rates):
    """Net short/long separately, cross-net losses, tax positive nets.

    DEFECT FIX (fis-tax-d1/d2, found by independent recalculation during
    the W8 S02 employer-equity scenario):

    D2 -- the previous cross-netting wrote ``st = max(0.0, st + lt); lt = 0.0``
    which DISCARDS the residual net capital loss. Given gross long-term of
    -23,964.89 and gross short-term of +3,948.31, the correct outcome is a
    net long-term loss of -20,016.58 that carries forward; the old code
    reported 0.0 / 0.0 and silently destroyed 20,016.58 USD of carryforward
    loss. A capital loss is an asset -- it offsets future gains and, for an
    individual filer, up to 3,000 USD/yr of ordinary income.

    The invariant the old code broke, and which now holds:
        lt_net_gain + st_net_gain == gross_lt_gain + gross_st_gain
    (netting only redistributes between buckets; it never changes the total).
    """
    lt = sum(g for _, g, term in realized_events if term == "long")
    st = sum(g for _, g, term in realized_events if term == "short")
    gross_lt, gross_st = lt, st
    # cross-term loss offset ONLY against actual opposite-side gains.
    # The residual KEEPS ITS SIGN AND ITS TERM on the side that had the
    # larger magnitude -- that residual is a carryforward loss, not zero.
    if lt < 0 < st:
        resid = st + lt
        st = max(0.0, resid)
        lt = min(0.0, resid)
    elif st < 0 < lt:
        resid = st + lt
        lt = max(0.0, resid)
        st = min(0.0, resid)
    carryforward = abs(min(lt, 0.0)) + abs(min(st, 0.0))
    tax = max(lt, 0.0) * tax_rates.get("long", 0.15) \
        + max(st, 0.0) * tax_rates.get("short", 0.24)
    return {
        "lt_net_gain": lt,
        "st_net_gain": st,
        "tax_usd": tax,
        # gross (pre-netting) figures: what an independent recalculation
        # must be compared against. lt_net + st_net is a NETTED quantity
        # and comparing it to gross realized is an apples-to-oranges check.
        "gross_lt_gain": gross_lt,
        "gross_st_gain": gross_st,
        "gross_total_gain": gross_lt + gross_st,
        "carryforward_loss_usd": carryforward,
    }


def select_lots_highest_loss_first(lots_with_px, qty_to_sell):
    """G2 SPECIFIC_ID lot selection: consume lots ordered by most-negative
    unrealized gain per share first (highest loss first), ties broken by
    lot_id for determinism. lots_with_px items carry "_px" (current price).
    Returns (fills, realized_gain, term_gains);
    fills = [(lot_id, qty)] and term_gains = {"long": x, "short": y}.

    DEFECT FIX (fis-tax-d1, found during the W8 S02 employer-equity
    scenario): realized gain is now attributed PER LOT to that lot's own
    holding period. Previously the caller collapsed an entire multi-lot
    sale into a single term via _dominant_term(), which chose the term by
    SHARE COUNT rather than by which lots actually produced the gain.
    In S02, a ZPHR sale consumed a 500-sh short lot (basis == price, gain
    exactly 0.00) and a 346.34-sh long lot (gain +3,948.31). Because the
    short lot had more shares, all 3,948.31 USD of long-term gain was
    booked as SHORT-TERM -- a 24% rate on what should be 15%. Proceeds
    are attributed correctly either way; the character of the gain is not.
    """
    def gps(i):
        l = lots_with_px[i]
        return float(l["_px"]) - float(l["cost_basis"])

    ranked = sorted(range(len(lots_with_px)),
                    key=lambda i: (gps(i), str(lots_with_px[i].get("lot_id", i))))
    remaining = float(qty_to_sell)
    fills = []
    realized = 0.0
    term_gains = {"long": 0.0, "short": 0.0}
    for i in ranked:
        if remaining <= 1e-12:
            break
        take = min(float(lots_with_px[i]["quantity"]), remaining)
        if take <= 1e-12:
            continue
        term = str(lots_with_px[i].get("term", "long")).lower()
        if term not in ("long", "short"):
            raise ValueError("unknown holding period term %r for lot %r"
                             % (term, lots_with_px[i].get("lot_id")))
        g = take * gps(i)
        fills.append((str(lots_with_px[i]["lot_id"]), take))
        realized += g
        term_gains[term] += g
        remaining -= take
    if remaining > 1e-6:
        raise ValueError("insufficient lot quantity to cover sale")
    return fills, realized, term_gains


# --------------------------------------------------------------------------
# Metric block builder (shared shape for action AND no-action)
# --------------------------------------------------------------------------

def _metric_block(post_holdings, post_cash, realized_events, ecm_cost,
                  turnover_one_sided_pct, v_pre, tax_rates=None):
    tax_rates = tax_rates or _DEFAULT_TAX
    v_post = sum(_holding_value(h) for h in post_holdings) + post_cash
    cw = {}
    for h in post_holdings:
        cw[h["asset_class"]] = cw.get(h["asset_class"], 0.0) + _holding_value(h)
    cw["cash"] = cw.get("cash", 0.0) + post_cash
    iw = {}
    for h in post_holdings:
        k = h.get("issuer", h["ticker"])
        iw[k] = iw.get(k, 0.0) + _holding_value(h)
    return {
        "portfolio_value_usd": v_post,
        "post_class_weights": {k: v / v_post for k, v in sorted(cw.items())},
        "post_issuer_weights": {k: v / v_post for k, v in sorted(iw.items())},
        "post_cash_usd": post_cash,
        "realized_gains": _split_term_tax(realized_events, tax_rates),
        "tax_rates_used": dict(tax_rates),
        "ecm_cost_usd": ecm_cost,
        # one-sided turnover = (sell notional + buy notional) / (2 * v_pre)
        "turnover_one_sided_pct": turnover_one_sided_pct,
        "v_pre_usd": v_pre,
    }


# --------------------------------------------------------------------------
# Constraint validator (post-hoc gates, tournament_runner style)
# --------------------------------------------------------------------------

def evaluate_constraints(metrics, constraints):
    checks = []
    v = metrics["portfolio_value_usd"]
    iw = metrics["post_issuer_weights"]
    worst_name = max(iw, key=iw.get) if iw else "-"
    worst_iss = iw[worst_name] if iw else 0.0
    checks.append({
        "rule": "max_single_issuer_pct",
        "limit": constraints["max_single_issuer_pct"],
        "observed_pct": worst_iss * 100.0,
        "pass": worst_iss * 100.0 <= constraints["max_single_issuer_pct"] + 1e-9,
        "detail": "worst issuer %s at %.3f%% vs cap %.3f%%"
                  % (worst_name, worst_iss * 100.0,
                     constraints["max_single_issuer_pct"])})
    cash_pct = metrics["post_cash_usd"] / v * 100.0 if v else 0.0
    checks.append({
        "rule": "min_cash_pct",
        "limit": constraints["min_cash_pct"],
        "observed_pct": cash_pct,
        "pass": cash_pct >= constraints["min_cash_pct"] - 1e-9,
        "detail": "cash %.3f%% vs floor %.3f%%"
                  % (cash_pct, constraints["min_cash_pct"])})
    to = metrics["turnover_one_sided_pct"] * 100.0
    checks.append({
        "rule": "max_turnover_pct",
        "limit": constraints["max_turnover_pct"],
        "observed_pct": to,
        "pass": to <= constraints["max_turnover_pct"] + 1e-9,
        "detail": "one-sided turnover %.3f%% vs ceiling %.3f%%"
                  % (to, constraints["max_turnover_pct"])})
    return checks


# --------------------------------------------------------------------------
# Core engine
# --------------------------------------------------------------------------

def propose_rebalance(portfolio, targets, bands, constraints, ecm=None,
                      tax_rates=None, decision_id=None, account=None,
                      model_version="unspecified", data_version="unspecified",
                      policy_version="unspecified", code_hash="unspecified",
                      price_as_of=None, requested_by="agent"):
    """Compute band-triggered rebalance proposal (see module docstring).

    Returns {status, action|null, no_action, instability, reasons,
             data_gaps, decision, execution}.
    status in {"proposed","rejected","no_action_needed"}.

    APPROVAL POSTURE (W3 HIGH -- GOV-NO-HUMAN-APPROVAL-GATE).
    This function ANALYSES. It does not authorise. Every trade it emits is
    inert: `executable: False`, `authority: "NONE"`,
    `order_state: "INERT-PROPOSED"`. The returned `decision` envelope is a
    `approval.DecisionRecord` in DRAFT_ANALYSIS /
    RECOMMENDATION_PENDING_REVIEW / HUMAN_APPROVAL_REQUIRED, and
    `execution["authorized"]` is always False because no transition to
    APPROVED_FOR_EXECUTION exists in the approval state machine.

    `status == "proposed"` is retained for backwards compatibility with
    existing callers and means "the analysis produced a candidate", NOT
    "a human approved anything". Read `decision["state"]` for the approval
    posture; read `decision["ui"]["classification"]` for how a surface is
    permitted to label it.
    """
    if ecm is None:
        ecm = _load_ecm()
    tax_rates = tax_rates or _DEFAULT_TAX
    reasons = []
    instability = []
    funding_gaps = []
    hold_by_key = _positions(portfolio["holdings"])
    cash_by_account, unallocated_cash, cash_basis = _cash_scope(portfolio, account)
    for h in portfolio["holdings"]:
        if _number(h["price"], "price") <= 0 or _number(h["quantity"], "quantity") < 0:
            raise ValueError("prices must be positive and quantities nonnegative")
    for term in ("long", "short"):
        if not 0 <= _number(tax_rates.get(term, _DEFAULT_TAX[term]), "tax rate") <= 1:
            raise ValueError("tax rates must be between zero and one")
    if _total_value(portfolio) <= 0:
        raise ValueError("portfolio value must be positive")
    cap_pct = float(constraints["max_single_issuer_pct"])

    class_w, v_pre = _class_weights(portfolio)

    def cap_val():
        return cap_pct / 100.0 * v_pre

    # ---- band scan -------------------------------------------------------
    breaches = {}   # cls -> (direction, excess_pp_over_edge, excess_pp_to_target)
    for cls, tgt in sorted(targets.items()):
        b = bands[cls]
        w = class_w.get(cls, 0.0)
        lo = float(tgt) - float(b["low"])
        hi = float(tgt) + float(b["high"])
        if w > hi:
            breaches[cls] = ("over", w - hi, w - float(tgt))
        elif w < lo:
            breaches[cls] = ("under", lo - w, float(tgt) - w)
        else:
            margin = min(abs(w - lo), abs(w - hi))
            if margin < _INSTABILITY_EPS_PP:
                instability.append({
                    "asset_class": cls, "weight_pct": w,
                    "band_low_pct": lo, "band_high_pct": hi,
                    "margin_to_edge_pp": margin,
                    "note": "weight within %.0fbp of band edge; signal "
                            "unstable -- deterministic tie-break applied, "
                            "do not churn on noise" % (margin * 1e4)})

    # ---- no_action baseline (ALWAYS present, identical metric block) ------
    no_action_metrics = _metric_block(
        copy.deepcopy(portfolio["holdings"]),
        float(portfolio.get("cash", 0.0)), [], 0.0, 0.0, v_pre, tax_rates)
    no_action = {
        "label": "no_action",
        "trades": [],
        "metrics": no_action_metrics,
        "constraint_checks": evaluate_constraints(no_action_metrics,
                                                  constraints),
        "account_funding": {"starting_cash_by_account": dict(cash_by_account),
                            "unallocated_starting_cash_usd": unallocated_cash,
                            "post_cash_by_account": dict(cash_by_account),
                            "basis": cash_basis},
    }

    if not breaches:
        gaps = price_data_gaps(portfolio)
        if gaps:
            reasons.append(
                "DATA GAP: %d holding(s) could not be priced; the "
                "no-action conclusion is INCOMPLETE" % len(gaps))
        independent_recalculation({"action": None, "no_action": no_action,
                                   "status": "no_action_needed"}, portfolio,
                                  ecm=ecm, tax_rates=tax_rates, account=account)
        env = approval.inert_plan_envelope(
            decision_id=decision_id or ("RB-NOACTION-" + _proposal_hash(
                portfolio, targets, bands, constraints)),
            decision_type="rebalance_proposal",
            plan={"label": "no_action", "trades": [],
                  "metrics": no_action_metrics,
                  "constraint_checks": no_action["constraint_checks"],
                  "ecm_detail": [], "breaches": {}},
            account=account or "UNSPECIFIED",
            model_version=model_version, data_version=data_version,
            policy_version=policy_version, code_hash=code_hash,
            price_as_of=price_as_of, requested_by=requested_by,
            data_gaps=gaps)
        approval.enforce_not_executable(
            env, where="portfolio_engine.propose_rebalance(no_action)")
        return {"status": "no_action_needed", "action": None,
                "no_action": no_action, "instability": instability,
                "reasons": reasons + [
                    "all class weights inside rebalancing bands"],
                "data_gaps": gaps, "decision": env,
                "execution": env["execution"], "ui": env["ui"]}

    # ---- step 1: pro-rata SELLs in each over-band class --------------------
    px_by_key = {key: float(h["price"]) for key, h in hold_by_key.items()}
    sell_orders = []           # ((account, ticker), usd)
    sim_issuer = {}            # running post-trade issuer values
    for h in portfolio["holdings"]:
        k = h.get("issuer", h["ticker"])
        sim_issuer[k] = sim_issuer.get(k, 0.0) + _holding_value(h)

    sells_usd = {cls: t[2] * v_pre for cls, t
                 in breaches.items() if t[0] == "over" and cls != "cash"}
    for cls, usd_total in sorted(sells_usd.items()):
        members = sorted([h for h in portfolio["holdings"]
                          if h["asset_class"] == cls],
                         key=_position_key)
        cls_val = sum(_holding_value(h) for h in members)
        allocated = 0.0
        # true pro-rata: each member's slice is sized off the ORIGINAL class
        # sell amount times its value share (capped at holding value) --
        # sizing off the shrinking remainder systematically under-deploys.
        for h in members:
            if cls_val <= 0:
                break
            take = min(usd_total * (_holding_value(h) / cls_val),
                       _holding_value(h))
            if take > _MIN_TRADE_USD:
                sell_orders.append((_position_key(h), take))
                allocated += take
                k = h.get("issuer", h["ticker"])
                sim_issuer[k] = sim_issuer.get(k, 0.0) - take
        if usd_total - allocated > _MIN_TRADE_USD:
            reasons.append("WARNING: could not deploy full sell for class %s "
                           "(%.2f usd unallocated)"
                           % (cls, usd_total - allocated))

    # ---- step 2: BUYs in under-band classes, issuer-cap-headroom aware -----
    buys_usd = {cls: t[2] * v_pre for cls, t
                in breaches.items() if t[0] == "under" and cls != "cash"}

    def trade_cost(key, notional):
        if notional <= 0:
            return 0.0
        value = _number(ecm.estimate_trade_cost(
            _security_symbol(hold_by_key[key]), float(notional))["round_trip_usd"],
            "ECM cost")
        if value < 0:
            raise ValueError("ECM cost must be nonnegative")
        return value

    # Cash stays in its owning account. Reserve the portfolio cash target/floor;
    # unidentified scalar cash can satisfy that reserve, but cannot fund a BUY.
    account_budget = dict(cash_by_account)
    for key, usd in sell_orders:
        account_budget[key[0]] = account_budget.get(key[0], 0.0) + usd - trade_cost(key, usd)
    reserve = max(float(targets.get("cash", 0.0)),
                  float(constraints["min_cash_pct"]) / 100.0) * v_pre
    funded_total = sum(max(0.0, usd) for usd in account_budget.values())
    funded_reserve = min(funded_total, max(0.0, reserve - unallocated_cash))
    if funded_total:
        for owner in account_budget:
            account_budget[owner] = max(0.0, account_budget[owner]) * (
                1.0 - funded_reserve / funded_total)

    planned_buys = {}

    def incremental_buy_cost(key, amount):
        previous = planned_buys.get(key, 0.0)
        return trade_cost(key, previous + amount) - trade_cost(key, previous)

    def affordable(key, ceiling):
        budget = max(0.0, account_budget.get(key[0], 0.0))
        hi = min(ceiling, budget)
        if hi <= _MIN_TRADE_USD or hi + incremental_buy_cost(key, hi) <= budget:
            return hi
        lo = 0.0
        for _ in range(60):
            mid = (lo + hi) / 2.0
            if mid + incremental_buy_cost(key, mid) <= budget:
                lo = mid
            else:
                hi = mid
        return lo

    buy_orders = []
    for cls, amount_raw in sorted(buys_usd.items()):
        amount = amount_raw
        members = sorted([h for h in portfolio["holdings"]
                          if h["asset_class"] == cls],
                         key=_position_key)
        if not members:
            reasons.append("WARNING: underweight class %s has no holdings to "
                           "buy into; amount left in cash" % cls)
            continue
        # route only into headroom below the single-issuer cap
        issuers = {h.get("issuer", h["ticker"]) for h in members}
        total_room = sum(max(0.0, cap_val() - sim_issuer.get(k, 0.0)) for k in issuers)
        if total_room < amount - _MIN_TRADE_USD:
            reasons.append(
                "NOTE: class %s buy $%.2f exceeds issuer-cap headroom $%.2f; "
                "routed to available headroom (remainder stays in cash)"
                % (cls, amount, max(total_room, 0.0)))
            amount = min(amount, total_room)
        if amount <= _MIN_TRADE_USD:
            continue
        allocated = 0.0
        # Refill available positions after a shared account/issuer exhausts its
        # budget. No holding-value cap: a small existing position may grow >2x.
        for _ in range(len(members) + 1):
            room = {}
            for h in members:
                key = _position_key(h)
                issuer = h.get("issuer", h["ticker"])
                room[key] = affordable(key, max(0.0, cap_val() - sim_issuer.get(issuer, 0.0)))
            total = sum(room.values())
            if total <= _MIN_TRADE_USD or amount - allocated <= _MIN_TRADE_USD:
                break
            remaining = amount - allocated
            progress = 0.0
            for key, capacity in sorted(room.items()):
                h = hold_by_key[key]
                issuer = h.get("issuer", h["ticker"])
                take = affordable(key, min(remaining * capacity / total,
                                           max(0.0, cap_val() - sim_issuer.get(issuer, 0.0))))
                if take > _MIN_TRADE_USD:
                    buy_orders.append((key, take))
                    account_budget[key[0]] -= take + incremental_buy_cost(key, take)
                    planned_buys[key] = planned_buys.get(key, 0.0) + take
                    sim_issuer[issuer] = sim_issuer.get(issuer, 0.0) + take
                    progress += take
            allocated += progress
            if progress <= _MIN_TRADE_USD:
                break
        if amount - allocated > _MIN_TRADE_USD:
            funding_gaps.append({"code": "INSUFFICIENT_ACCOUNT_FUNDING", "asset_class": cls,
                                 "unfunded_usd": amount - allocated,
                                 "detail": "BUY target needs unavailable account cash; " + cash_basis})

    # ---- step 3: post-trade forced trims of cap-breaching issuers ----------
    for k in sorted(sim_issuer):
        over = sim_issuer[k] - cap_val()
        if over <= _MIN_TRADE_USD:
            continue
        # trim this issuer's holdings pro-rata by current value
        members = sorted([h for h in portfolio["holdings"]
                          if h.get("issuer", h["ticker"]) == k],
                         key=_position_key)
        # Size the second sell pass from the remaining positions. Reusing
        # original values can sell an already depleted asset class twice.
        remaining_values = {
            _position_key(h): max(0.0, _holding_value(h) - sum(
                usd for key, usd in sell_orders if key == _position_key(h)))
            for h in members}
        iss_val = sum(remaining_values.values())
        trimmed = 0.0
        for h in members:
            if trimmed >= over - _MIN_TRADE_USD:
                break
            available = remaining_values[_position_key(h)]
            take = min(over * (available / iss_val)
                       if iss_val > 0 else 0.0,
                       available)
            if take > _MIN_TRADE_USD:
                sell_orders.append((_position_key(h), take))
                trimmed += take
                sim_issuer[k] = sim_issuer.get(k, 0.0) - take
        if sim_issuer[k] - cap_val() > _MIN_TRADE_USD:
            reasons.append("WARNING: issuer %s still above cap after trim; "
                           "constraint gate will decide" % k)

    # ---- aggregate legs per account/position, then build state ------------
    # Multiple planner passes can target the same position (band sell + forced
    # trim). Aggregating FIRST guarantees lot consumption is sequential and
    # ECM charges reflect true notionals.
    gross_sell_by_key = {}
    for t, u in sell_orders:
        gross_sell_by_key[t] = gross_sell_by_key.get(t, 0.0) + u
    gross_buy_by_key = {}
    for t, u in buy_orders:
        gross_buy_by_key[t] = gross_buy_by_key.get(t, 0.0) + u

    def _build_state(sell_map, buy_map):
        """Single source of truth for post-trade state. Returns
        (holdings, cash, realized_events, lot_fills, ecm_cost, account_cash).
        Re-runnable from scratch: used both initially and after each
        forced-trim convergence pass."""
        ecm_cost = 0.0
        post_account_cash = dict(cash_by_account)
        for t in sorted(set(sell_map) | set(buy_map)):
            post_account_cash.setdefault(t[0], 0.0)
            if t in sell_map:
                fee = trade_cost(t, sell_map[t])
                ecm_cost += fee
                post_account_cash[t[0]] += sell_map[t] - fee
            if t in buy_map:
                fee = trade_cost(t, buy_map[t])
                ecm_cost += fee
                post_account_cash[t[0]] -= buy_map[t] + fee
        ph = copy.deepcopy(portfolio["holdings"])
        realized_events = []
        lot_fills = {}
        for h in ph:
            px = float(h["price"])
            key = _position_key(h)
            sold = sell_map.get(key, 0.0)
            bought = buy_map.get(key, 0.0)
            if sold > _MIN_TRADE_USD:
                qty = sold / px
                raw_lots = h.get("lots") or [
                    {"lot_id": h["ticker"] + "-IMPLICIT",
                     "quantity": h["quantity"], "cost_basis": px,
                     "term": "long"}]
                lots = [dict(l, _px=px) for l in raw_lots]
                fills, gain, term_gains = select_lots_highest_loss_first(
                    lots, qty)
                lot_fills[key] = fills
                # Attribute the gain to the holding period of the lots that
                # actually produced it, not to a whole-sale "dominant" term.
                for term in ("long", "short"):
                    g = term_gains[term]
                    if abs(g) > 1e-12:
                        realized_events.append((h["ticker"], g, term))
            h["quantity"] = float(h["quantity"]) + (bought - sold) / px
        cash = (float(portfolio.get("cash", 0.0))
                + sum(sell_map.values()) - sum(buy_map.values())
                - ecm_cost)
        if not math.isclose(cash, sum(post_account_cash.values()) + unallocated_cash,
                            rel_tol=1e-12, abs_tol=1e-6):
            raise AssertionError("account cash does not conserve portfolio cash")
        return ph, cash, realized_events, lot_fills, ecm_cost, post_account_cash

    post_holdings, post_cash, realized_events, lot_fills, ecm_cost, post_account_cash = \
        _build_state(gross_sell_by_key, gross_buy_by_key)
    total_sell = sum(gross_sell_by_key.values())
    total_buy = sum(gross_buy_by_key.values())
    turnover = (total_sell + total_buy) / (2.0 * v_pre)

    metrics = _metric_block(post_holdings, post_cash, realized_events,
                            ecm_cost, turnover, v_pre, tax_rates)
    checks = evaluate_constraints(metrics, constraints)

    # ---- step 3b: forced trims measured on the ACTUAL post-cost state ------
    # The ECM cost drag shrinks every position, so a trim sized against
    # pre-cost values can leave an issuer marginally above its cap. Iterate
    # against the real end state until the issuer gate is clean or no
    # further progress is possible. A deterministic buffer (1 bp of
    # portfolio) keeps post-cost weights strictly under the cap instead of
    # asymptotically touching it.
    _trim_buf = 0.0001 * metrics["portfolio_value_usd"]
    for _attempt in range(10):
        failing = []
        for k, wv in sorted(metrics["post_issuer_weights"].items()):
            over_val = (wv - cap_pct / 100.0) \
                * metrics["portfolio_value_usd"]
            if over_val > -_trim_buf:
                failing.append((k, max(over_val + _trim_buf,
                                       _MIN_TRADE_USD)))
        if not failing:
            break
        extra = {}
        progressed = False
        for k, over_val in failing:
            members = sorted([h for h in post_holdings
                              if h.get("issuer", h["ticker"]) == k],
                             key=_position_key)
            iss_val = sum(_holding_value(h) for h in members)
            trim_total = over_val
            for h in members:
                if over_val <= _MIN_TRADE_USD or iss_val <= 0:
                    break
                key = _position_key(h)
                sellable = max(0.0, _holding_value(hold_by_key[key]) - gross_sell_by_key.get(key, 0.0))
                take = min(trim_total * (_holding_value(h) / iss_val), sellable)
                if take > _MIN_TRADE_USD:
                    extra[key] = extra.get(key, 0.0) + take
                    over_val -= take
                    progressed = True
        if not progressed:
            reasons.append("WARNING: issuer-cap trim could not fully "
                           "converge; constraint gate will decide")
            break
        for t in sorted(extra):
            gross_sell_by_key[t] = \
                gross_sell_by_key.get(t, 0.0) + extra[t]
        post_holdings, post_cash, realized_events, lot_fills, ecm_cost, post_account_cash = \
            _build_state(gross_sell_by_key, gross_buy_by_key)
        total_sell = sum(gross_sell_by_key.values())
        turnover = (total_sell + total_buy) / (2.0 * v_pre)
        metrics = _metric_block(post_holdings, post_cash, realized_events,
                                ecm_cost, turnover, v_pre, tax_rates)
        checks = evaluate_constraints(metrics, constraints)

    violations = [c["rule"] for c in checks if not c["pass"]]
    for c in checks:
        if not c["pass"]:
            reasons.append("CONSTRAINT VIOLATION: %s (%s)"
                           % (c["rule"], c["detail"]))
    # A cost reserve may leave a small target shortfall that is already inside
    # the accepted band. Keep the arithmetic visible without rejecting that
    # feasible plan. A remaining breached class still refuses the proposal.
    funding_gaps = [gap for gap in funding_gaps if metrics["post_class_weights"].get(
        gap["asset_class"], 0.0) < float(targets[gap["asset_class"]]) - float(
            bands[gap["asset_class"]]["low"]) - 1e-12]
    for owner, balance in sorted(post_account_cash.items()):
        if balance < -1e-6:
            funding_gaps.append({"code": "NEGATIVE_ACCOUNT_CASH", "account": owner,
                                 "detail": "trade costs exceed this account's available cash"})
    status = "rejected" if violations or funding_gaps else "proposed"

    ecm_detail = [
        {"ticker": hold_by_key[t]["ticker"], "account": t[0],
         "security_symbol": _security_symbol(hold_by_key[t]),
         "sell_notional_usd": round(gross_sell_by_key.get(t, 0.0), 2),
         "buy_notional_usd": round(gross_buy_by_key.get(t, 0.0), 2)}
        for t in sorted(set(gross_sell_by_key) | set(gross_buy_by_key))]

    trades = []
    for t in sorted(gross_sell_by_key):
        u = gross_sell_by_key[t]
        trades.append({"side": "SELL", "ticker": hold_by_key[t]["ticker"],
                       "account": t[0], "security_symbol": _security_symbol(hold_by_key[t]),
                       # full precision: independent_recalculation replays
                       # these notionals verbatim
                       "notional_usd": u,
                       "qty": round(u / px_by_key[t], 6),
                       "lot_fills": lot_fills.get(t, [])})
    for t in sorted(gross_buy_by_key):
        u = gross_buy_by_key[t]
        trades.append({"side": "BUY", "ticker": hold_by_key[t]["ticker"],
                       "account": t[0], "security_symbol": _security_symbol(hold_by_key[t]),
                       "notional_usd": u,
                       "qty": round(u / px_by_key[t], 6)})
    trades.sort(key=lambda d: (d["ticker"], d["account"], d["side"]))

    # Every emitted leg is inert. A consumer cannot reach past this.
    for tr in trades:
        tr["executable"] = False
        tr["authority"] = "NONE"
        tr["order_state"] = "INERT-PROPOSED"

    data_gaps = price_data_gaps(portfolio) + funding_gaps

    action = {
        "label": "rebalance_proposed",
        "executable": False,
        "authorized": False,
        "authority": "NONE",
        "breaches": {k: {"direction": v[0],
                         "excess_pp_over_edge": round(v[1], 6)}
                     for k, v in sorted(breaches.items())},
        "trades": trades,
        "metrics": metrics,
        "constraint_checks": checks,
        "ecm_detail": ecm_detail,
        "account_funding": {"starting_cash_by_account": cash_by_account,
                            "unallocated_starting_cash_usd": unallocated_cash,
                            "post_cash_by_account": post_account_cash,
                            "basis": cash_basis},
    }
    if data_gaps:
        reasons.append(
            "DATA GAP: %d pricing or account-funding issue(s); the proposal is "
            "INCOMPLETE and must not be approved while gaps remain"
            % len(data_gaps))

    independent_recalculation({"action": action, "status": status}, portfolio,
                              ecm=ecm, tax_rates=tax_rates, account=account)

    envelope = approval.inert_plan_envelope(
        decision_id=decision_id or ("RB-" + _proposal_hash(portfolio, targets,
                                                           bands, constraints)),
        decision_type="rebalance_proposal",
        plan=({"label": action["label"], "trades": trades,
               "metrics": metrics, "constraint_checks": checks,
               "ecm_detail": ecm_detail, "breaches": action["breaches"]}
              if action is not None else None),
        account=account or "UNSPECIFIED",
        model_version=model_version, data_version=data_version,
        policy_version=policy_version, code_hash=code_hash,
        price_as_of=price_as_of, requested_by=requested_by,
        data_gaps=data_gaps)

    # Boundary enforcement runs HERE, inside the tool, not only in the UI
    # or the API layer: an object carrying execution authority is refused
    # before it can leave this function.
    approval.enforce_not_executable(envelope, where="portfolio_engine."
                                                    "propose_rebalance")
    for tr in trades:
        if tr.get("executable") is not False:
            raise AssertionError(
                "internal error: trade leg %s %s escaped with "
                "executable=%r" % (tr.get("side"), tr.get("ticker"),
                                   tr.get("executable")))

    return {"status": status, "action": action, "no_action": no_action,
            "instability": instability, "reasons": reasons,
            "data_gaps": data_gaps,
            "decision": envelope,
            "execution": envelope["execution"],
            "ui": envelope["ui"]}


def price_data_gaps(portfolio):
    """Holdings that cannot be priced, named explicitly.

    A holding with a missing, zero, negative, NaN or infinite price is not
    a holding worth zero; it is a holding whose value is UNKNOWN. Sizing a
    rebalance off a zero price would treat the position as worthless and
    manufacture a spurious sell. The gap is reported so it can block
    approval rather than silently distort the plan.
    """
    gaps = []
    for h in (portfolio.get("holdings") or []):
        tkr = str(h.get("ticker", ""))
        acct = str(h.get("account") or "UNSPECIFIED")
        raw = h.get("price", None)
        if raw is None:
            gaps.append({"instrument": tkr, "account": acct,
                         "code": "MISSING_PRICE",
                         "detail": "holding has no price field"})
            continue
        try:
            px = float(raw)
        except (TypeError, ValueError):
            gaps.append({"instrument": tkr, "account": acct,
                         "code": "NON_FINITE_PRICE",
                         "detail": "price %r is not numeric" % (raw,)})
            continue
        if px != px or px in (float("inf"), float("-inf")):
            gaps.append({"instrument": tkr, "account": acct,
                         "code": "NON_FINITE_PRICE",
                         "detail": "price is NaN or infinite"})
        elif px == 0.0:
            gaps.append({"instrument": tkr, "account": acct,
                         "code": "ZERO_PRICE",
                         "detail": "price is exactly 0.00; a zero price is "
                                   "not a market mark"})
        elif px < 0.0:
            gaps.append({"instrument": tkr, "account": acct,
                         "code": "NEGATIVE_PRICE",
                         "detail": "price is negative (%r)" % (px,)})
    return gaps


def _proposal_hash(portfolio, targets, bands, constraints):
    import hashlib as _hashlib
    payload = {
        "holdings": [(_position_key(h), _security_symbol(h),
                      float(h.get("quantity", 0.0)), float(h.get("price", 0.0)))
                     for h in sorted(portfolio.get("holdings") or [], key=_position_key)],
        "cash": float(portfolio.get("cash", 0.0)),
        "cash_account": portfolio.get("cash_account"),
        "cash_by_account": portfolio.get("cash_by_account"),
        "targets": targets, "bands": bands, "constraints": constraints,
    }
    return _hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:24]


# --------------------------------------------------------------------------
# Independent recalculation (path B: naive full-state replay)
# --------------------------------------------------------------------------

def independent_recalculation(plan, portfolio, ecm=None, tax_rates=None, account=None):
    """Replay recorded legs against source positions, including every money field.

    Pass tax_rates/account to verify caller-supplied policy/account bindings.
    Without tax_rates, the recorded rates are disclosed assumptions, not an
    independently authenticated tax policy. This check is arithmetic, not approval.
    """
    if ecm is None:
        ecm = _load_ecm()
    action = plan["action"]
    alternative = action if action is not None else plan["no_action"]
    m = alternative["metrics"]
    problems = []

    def finite_tree(value, label):
        if isinstance(value, dict):
            for key, item in value.items():
                finite_tree(item, label + "." + str(key))
        elif isinstance(value, (list, tuple)):
            for i, item in enumerate(value):
                finite_tree(item, label + "[%d]" % i)
        elif isinstance(value, float) and not math.isfinite(value):
            raise AssertionError("nonfinite numeric field: " + label)

    def number(value, label):
        try:
            return _number(value, label)
        except ValueError as exc:
            raise AssertionError(str(exc)) from None

    def equal(actual, expected, label, tolerance=1e-6):
        expected = number(expected, label)
        if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=tolerance):
            problems.append("%s %r vs %r" % (label, actual, expected))

    finite_tree(alternative, "alternative")
    try:
        balances, unallocated, _ = _cash_scope(portfolio, account)
    except ValueError as exc:
        raise AssertionError(str(exc)) from None
    starting_balances = dict(balances)
    fresh = copy.deepcopy(portfolio["holdings"])
    holdings = {}
    lots_remaining = {}
    for h in fresh:
        key = (str(h.get("account") or "UNSPECIFIED"), str(h["ticker"]))
        if key in holdings:
            raise AssertionError("duplicate source position: %r" % (key,))
        holdings[key] = h
        px = number(h["price"], "source price")
        qty = number(h["quantity"], "source quantity")
        if px <= 0 or qty < 0:
            raise AssertionError("invalid source price/quantity")
        raw_lots = h.get("lots") or [{"lot_id": h["ticker"] + "-IMPLICIT",
                                     "quantity": qty, "cost_basis": px, "term": "long"}]
        lot_map = {}
        for lot in raw_lots:
            lid = str(lot["lot_id"])
            if lid in lot_map:
                raise AssertionError("duplicate source lot: " + lid)
            lot_map[lid] = dict(lot)
        lots_remaining[key] = lot_map
    cash = number(portfolio.get("cash", 0.0), "source cash")
    v_pre = cash + sum(number(h["quantity"], "source quantity") *
                       number(h["price"], "source price") for h in fresh)
    if v_pre <= 0:
        raise AssertionError("source portfolio value must be positive")
    gross = {"long": 0.0, "short": 0.0}
    ecm_cost = gross_sell = gross_buy = 0.0
    for tr in alternative["trades"]:
        ticker = str(tr["ticker"])
        if tr.get("account"):
            key = (str(tr["account"]), ticker)
        else:
            candidates = [key for key in holdings if key[1] == ticker]
            if len(candidates) != 1:
                raise AssertionError("ambiguous legacy trade account: " + ticker)
            key = candidates[0]
        if key not in holdings:
            raise AssertionError("unknown trade position: %r" % (key,))
        h = holdings[key]
        symbol = str(h.get("security_symbol") or h["ticker"])
        if tr.get("security_symbol", symbol) != symbol:
            raise AssertionError("trade security symbol differs from source position")
        px = float(h["price"])
        notional = number(tr["notional_usd"], "trade notional")
        if notional <= 0:
            raise AssertionError("trade notional must be positive")
        qty = notional / px
        equal(qty, tr["qty"], "trade quantity", tolerance=0.00000051)
        side = tr["side"]
        if side == "SELL":
            if qty > float(h["quantity"]) + 1e-6:
                raise AssertionError("sale exceeds position quantity")
            filled = 0.0
            seen = set()
            for lot_id, fill_qty in tr["lot_fills"]:
                lot_id = str(lot_id)
                if lot_id in seen or lot_id not in lots_remaining[key]:
                    raise AssertionError("duplicate/unknown lot fill: " + lot_id)
                seen.add(lot_id)
                lot = lots_remaining[key][lot_id]
                take = number(fill_qty, "lot fill quantity")
                if take <= 0 or take > number(lot["quantity"], "lot quantity") + 1e-6:
                    raise AssertionError("invalid/excess lot fill")
                term = str(lot.get("term", "long")).lower()
                if term not in gross:
                    raise AssertionError("unknown holding period: " + term)
                gross[term] += take * (px - number(lot["cost_basis"], "lot basis"))
                lot["quantity"] = float(lot["quantity"]) - take
                filled += take
            equal(qty, filled, "filled sale quantity")
            h["quantity"] = float(h["quantity"]) - qty
            cash += notional
            balances[key[0]] = balances.get(key[0], 0.0) + notional
            gross_sell += notional
        elif side == "BUY":
            h["quantity"] = float(h["quantity"]) + qty
            cash -= notional
            balances[key[0]] = balances.get(key[0], 0.0) - notional
            gross_buy += notional
        else:
            raise AssertionError("unknown trade side: " + str(side))
        fee = number(ecm.estimate_trade_cost(symbol, notional)["round_trip_usd"], "ECM cost")
        if fee < 0:
            raise AssertionError("ECM cost must be nonnegative")
        ecm_cost += fee
        cash -= fee
        balances[key[0]] = balances.get(key[0], 0.0) - fee
    v_post = cash + sum(float(h["quantity"]) * float(h["price"]) for h in fresh)
    if v_post <= 0:
        raise AssertionError("post-trade portfolio value must be positive")
    equal(v_pre, m["v_pre_usd"], "pre-trade value")
    equal(v_pre - ecm_cost, v_post, "value conservation")
    equal(v_post, m["portfolio_value_usd"], "portfolio value")
    equal(cash, m["post_cash_usd"], "post cash")
    equal(sum(balances.values()) + unallocated, cash, "account cash conservation")
    equal(ecm_cost, m["ecm_cost_usd"], "ECM cost")
    equal((gross_sell + gross_buy) / (2.0 * v_pre),
          m["turnover_one_sided_pct"], "turnover")
    cw, iw = {"cash": cash}, {}
    for h in fresh:
        value = float(h["quantity"]) * float(h["price"])
        cw[h["asset_class"]] = cw.get(h["asset_class"], 0.0) + value
        issuer = h.get("issuer", h["ticker"])
        iw[issuer] = iw.get(issuer, 0.0) + value
    for field, actual in (("post_class_weights", cw), ("post_issuer_weights", iw)):
        expected = m[field]
        if not isinstance(expected, dict) or set(expected) != set(actual):
            problems.append(field + " has missing or extra keys")
        else:
            for key, value in actual.items():
                equal(value / v_post, expected[key], field + "." + str(key))
    rates = tax_rates if tax_rates is not None else m.get("tax_rates_used", _DEFAULT_TAX)
    rates = {term: number(rates.get(term, _DEFAULT_TAX[term]), "tax rate")
             for term in ("long", "short")}
    if any(not 0 <= rate <= 1 for rate in rates.values()):
        raise AssertionError("invalid tax rate")
    if tax_rates is not None and "tax_rates_used" in m:
        for term, rate in rates.items():
            equal(rate, m["tax_rates_used"].get(term, _DEFAULT_TAX[term]), "recorded tax rate")
    long_net, short_net = gross["long"], gross["short"]
    if long_net * short_net < 0:
        offset = min(abs(long_net), abs(short_net))
        long_net += offset if long_net < 0 else -offset
        short_net += offset if short_net < 0 else -offset
    expected_gains = {
        "gross_lt_gain": gross["long"], "gross_st_gain": gross["short"],
        "gross_total_gain": gross["long"] + gross["short"],
        "lt_net_gain": long_net, "st_net_gain": short_net,
        "carryforward_loss_usd": max(0.0, -long_net) + max(0.0, -short_net),
        "tax_usd": max(long_net, 0.0) * rates["long"] + max(short_net, 0.0) * rates["short"],
    }
    for field, actual in expected_gains.items():
        if field not in m["realized_gains"]:
            problems.append("missing realized-gain field: " + field)
        else:
            equal(actual, m["realized_gains"][field], "realized gains." + field)
    funding = alternative.get("account_funding")
    if funding is not None:
        original = funding.get("starting_cash_by_account", {})
        if set(original) != set(starting_balances):
            problems.append("starting account cash has missing or extra keys")
        else:
            for owner, balance in starting_balances.items():
                equal(balance, original[owner], "starting account cash")
        equal(unallocated, funding.get("unallocated_starting_cash_usd"), "unallocated cash")
        expected = funding.get("post_cash_by_account", {})
        if set(expected) != set(balances):
            problems.append("post account cash has missing or extra keys")
        else:
            for owner, balance in balances.items():
                equal(balance, expected[owner], "post account cash")
        if plan["status"] == "proposed" and any(balance < -1e-6 for balance in balances.values()):
            problems.append("proposed trades require a cross-account transfer or borrowing")
    if problems:
        raise AssertionError("INTERNAL ERROR: independent_recalculation mismatch -- " + "; ".join(problems))
    return True


# --------------------------------------------------------------------------
# Explanation renderer
# --------------------------------------------------------------------------

def explanation(plan):
    lines = []

    def w(s=""):
        lines.append(s)

    act = plan["action"]
    na = plan["no_action"]
    m_act = act["metrics"] if act else na["metrics"]
    m_na = na["metrics"]

    w("== PORTFOLIO REBALANCE EXPLANATION ==")
    w("Status: %s" % plan["status"].upper())
    for r in plan["reasons"]:
        w("  - " + r)
    w("")
    if act is None:
        w("WHY DO NOTHING: every asset class sits inside its rebalancing band.")
        for cls, mw in sorted(m_na["post_class_weights"].items()):
            w("  - %-8s at %6.2f%% (no band breach)" % (cls, mw * 100.0))
        w("Estimated taxes: $0.00 | Estimated ECM cost: $0.00 | Turnover: 0.00%")
    else:
        w("WHY TRADE NOW:")
        for cls, b in sorted(act["breaches"].items()):
            w("  - %s is %s its band by %.2f pp of portfolio (edge-excess)"
              % (cls, "ABOVE" if b["direction"] == "over" else "BELOW",
                 b["excess_pp_over_edge"]))
        w("")
        w("WHAT WOULD HAPPEN (proposed vs staying put):")
        w("  trades: %d legs" % len(act["trades"]))
        for tr in act["trades"]:
            extra = ""
            if tr["side"] == "SELL" and tr.get("lot_fills"):
                extra = " lots=%s" % ",".join(
                    "%s x%s" % (lid, round(q, 2)) for lid, q in tr["lot_fills"])
            w("  - %4s %-6s $%11.2f%s" % (tr["side"], tr["ticker"],
                                          tr["notional_usd"], extra))
        w("  estimated tax on realized gains: $%.2f (LT net $%.2f / ST net $%.2f)"
          % (m_act["realized_gains"]["tax_usd"],
             m_act["realized_gains"]["lt_net_gain"],
             m_act["realized_gains"]["st_net_gain"]))
        w("  estimated ECM cost:              $%.2f" % m_act["ecm_cost_usd"])
        w("  one-sided turnover:              %.2f%%"
          % (m_act["turnover_one_sided_pct"] * 100.0))
        w("  versus no-action: tax $%.2f, ECM $%.2f, turnover 0.00%%"
          % (m_na["realized_gains"]["tax_usd"], m_na["ecm_cost_usd"]))
        failed = [c for c in act["constraint_checks"] if not c["pass"]]
        if failed:
            w("")
            w("WHY REJECTED:")
            for c in failed:
                w("  - %s: %s" % (c["rule"], c["detail"]))
        else:
            w("")
            w("CONSTRAINTS: all pass post-trade.")
            for c in act["constraint_checks"]:
                w("  - %s: %s" % (c["rule"], c["detail"]))
        w("")
        w("WHY NOT WAIT ENTIRELY (the no-action alternative, shown for "
          "comparison):")
        for c in na["constraint_checks"]:
            w("  - %s: %s [%s]" % (c["rule"], c["detail"],
                                   "PASS" if c["pass"] else "FAIL"))
    if plan["instability"]:
        w("")
        w("INSTABILITY FLAGS (input near band edge -- do not churn):")
        for f in plan["instability"]:
            w("  - %s at %.4f%% vs band [%.2f%%, %.2f%%]: margin %.4f pp"
              % (f["asset_class"], f["weight_pct"] * 100.0,
                 f["band_low_pct"] * 100.0, f["band_high_pct"] * 100.0,
                 f["margin_to_edge_pp"] * 100.0))
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Selftest
# --------------------------------------------------------------------------

def _fixture(cash=100000.0):
    """ZPHR-concentrated synthetic book. ZPHR lots carry real losses so the
    G2 highest-loss-first selection is observable in dollars."""
    return {
        "cash": cash,
        "holdings": [
            {"ticker": "ZPHR", "issuer": "ZPHR Inc", "asset_class": "equity",
             "account": "taxable", "quantity": 10000.0, "price": 60.0,
             "lots": [
                 {"lot_id": "L1", "quantity": 3000.0, "cost_basis": 85.0,
                  "acquire_date": "2024-02-01", "term": "long"},
                 {"lot_id": "L2", "quantity": 2000.0, "cost_basis": 62.0,
                  "acquire_date": "2024-06-01", "term": "long"},
                 {"lot_id": "L3", "quantity": 5000.0, "cost_basis": 40.0,
                  "acquire_date": "2023-01-15", "term": "long"},
             ]},
            {"ticker": "SPY", "issuer": "SPDR", "asset_class": "equity",
             "account": "taxable", "quantity": 1600.0, "price": 500.0,
             "lots": [{"lot_id": "S1", "quantity": 1600.0, "cost_basis": 480.0,
                       "acquire_date": "2023-05-01", "term": "long"}]},
            {"ticker": "BND", "issuer": "Vanguard", "asset_class": "bond",
             "account": "ira", "quantity": 4000.0, "price": 100.0,
             "lots": [{"lot_id": "B1", "quantity": 4000.0, "cost_basis": 98.0,
                       "acquire_date": "2022-09-01", "term": "long"}]},
        ],
    }


TARGETS = {"equity": 0.55, "bond": 0.40, "cash": 0.05}
BANDS = {"equity": {"low": 0.05, "high": 0.05},
         "bond": {"low": 0.05, "high": 0.05},
         "cash": {"low": 0.05, "high": 0.05}}
CONSTRAINTS = {"max_single_issuer_pct": 25.0, "min_cash_pct": 2.0,
               "max_turnover_pct": 50.0}


def _oracle_lot_gain(raw_lots, px, qty):
    """Independent mini-oracle for the G2 rule: sort by gain/share ascending
    (highest loss first), consume until qty, return realized gain. Written
    straight from the spec text, NOT shared with the engine code path."""
    ordered = sorted(raw_lots,
                     key=lambda l: ((px - float(l["cost_basis"])),
                                    str(l["lot_id"])))
    left = qty
    gain = 0.0
    for l in ordered:
        if left <= 1e-12:
            break
        take = min(float(l["quantity"]), left)
        gain += take * (px - float(l["cost_basis"]))
        left -= take
    return gain


def selftest():
    results = {"cases": [], "all_pass": True}
    ecm = _load_ecm()

    def record(name, ok, detail=""):
        results["cases"].append({"case": name, "pass": bool(ok),
                                 "detail": detail})
        if not ok:
            results["all_pass"] = False
        print("[%s] %s %s" % ("PASS" if ok else "FAIL", name, detail))

    # --- Case 1: ZPHR concentration triggers issuer cap; trim succeeds -----
    pf = _fixture()
    plan = propose_rebalance(pf, TARGETS, BANDS, CONSTRAINTS, ecm=ecm)
    cw0, v0 = _class_weights(pf)
    zphr_before = 600000.0 / v0 * 100.0
    record("fixture_zphr_weight_breach",
           zphr_before > CONSTRAINTS["max_single_issuer_pct"],
           "ZPHR starts at %.2f%% vs cap %.0f%%"
           % (zphr_before, CONSTRAINTS["max_single_issuer_pct"]))
    # The fixture sells taxable equities but would buy bonds in an IRA.
    # Scalar cash has no declared owner; no transfer was authorized. The
    # concentration repair remains calculable, but the full plan must refuse.
    record("plan_rejects_unfunded_account_buy",
           plan["status"] == "rejected" and any(
               gap["code"] == "INSUFFICIENT_ACCOUNT_FUNDING" for gap in plan["data_gaps"]),
           "status=%s; IRA buy cannot use taxable-account sales" % plan["status"])
    zphr_post = plan["action"]["metrics"]["post_issuer_weights"]["ZPHR Inc"] \
        * 100.0
    record("issuer_cap_satisfied_post_trade",
           zphr_post <= CONSTRAINTS["max_single_issuer_pct"] + 1e-9,
           "ZPHR post-trade %.3f%% <= 25%%" % zphr_post)
    sells = [t for t in plan["action"]["trades"] if t["side"] == "SELL"
             and t["ticker"] == "ZPHR"]
    record("zphr_trim_present", len(sells) >= 1 and sells[0]["notional_usd"] > 0,
           "%d ZPHR sell leg(s), $%.2f total"
           % (len(sells), sum(s["notional_usd"] for s in sells)))

    # --- Case 2: G2 lot economics vs independent oracle ---------------------
    all_sells = [t for t in plan["action"]["trades"] if t["side"] == "SELL"]

    def _oracle_gain_for(tkr, notional_usd):
        h = next(x for x in pf["holdings"] if x["ticker"] == tkr)
        qty = float(notional_usd) / float(h["price"])
        return _oracle_lot_gain(h["lots"], float(h["price"]), qty)

    oracle_gain = sum(_oracle_gain_for(s["ticker"], s["notional_usd"])
                      for s in all_sells)
    ids = [f[0] for s in sells for f in s["lot_fills"]]
    record("g2_loss_lots_consumed_before_gain_lot",
           set(ids).issubset({"L1", "L2"}) and ids[0] == "L1"
           and "L3" not in ids,
           "lot order=%s (gain lot L3 untouched)" % ids)
    got = (plan["action"]["metrics"]["realized_gains"]["lt_net_gain"]
           + plan["action"]["metrics"]["realized_gains"]["st_net_gain"])
    record("tax_cost_from_actual_lots", abs(got - oracle_gain) < 1e-6,
           "realized $%.2f == oracle $%.2f (net loss => tax $%.2f)"
           % (got, oracle_gain,
              plan["action"]["metrics"]["realized_gains"]["tax_usd"]))

    # --- Case 3: no_action alternative always present, identical shape ------
    record("no_action_present",
           plan["no_action"]["label"] == "no_action"
           and plan["no_action"]["trades"] == [])
    ka = sorted(plan["action"]["metrics"].keys())
    kn = sorted(plan["no_action"]["metrics"].keys())
    record("metric_block_identical_keys", ka == kn, "keys=%s" % ka)
    cn = plan["no_action"]["constraint_checks"]
    # On this concentrated fixture no-action MUST fail the issuer cap --
    # that is exactly the risk the rebalance exists to fix. The alternative
    # is present and honestly evaluated, not artificially green.
    na_iss = [c for c in cn if c["rule"] == "max_single_issuer_pct"]
    record("no_action_constraints_evaluated",
           len(cn) == 3
           and na_iss and not na_iss[0]["pass"]
           and all(c["pass"] for c in cn if c["rule"] != "max_single_issuer_pct"),
           "; ".join(c["rule"] + "=" + ("P" if c["pass"] else "F")
                     for c in cn))

    # --- Case 4: constraint violation forces rejection ----------------------
    tight = dict(CONSTRAINTS, max_turnover_pct=5.0)
    rej = propose_rebalance(pf, TARGETS, BANDS, tight, ecm=ecm)
    record("tight_turnover_rejects", rej["status"] == "rejected",
           "status=%s violations=%s"
           % (rej["status"], [r for r in rej["reasons"]
                              if "VIOLATION" in r]))
    record("rejected_still_has_no_action",
           rej["no_action"]["label"] == "no_action"
           and sorted(rej["no_action"]["metrics"].keys())
           == sorted(rej["action"]["metrics"].keys()))

    # --- Case 5: independent recalculation equality -------------------------
    try:
        independent_recalculation(plan, pf, ecm=ecm)
        record("recalc_equality_holds", True, "path B matches path A")
    except AssertionError as exc:
        record("recalc_equality_holds", False, str(exc))
    # negative control: a corrupted plan MUST be caught
    bad = copy.deepcopy(plan)
    bad["action"]["metrics"]["ecm_cost_usd"] += 1.0
    caught = False
    try:
        independent_recalculation(bad, pf, ecm=ecm)
    except AssertionError:
        caught = True
    record("recalc_catches_corruption", caught,
           "tampered ECM cost detected as internal error")

    # --- Case 6: instability flagged, recommendation deterministic ----------
    edge_pf = _fixture()
    cw_e, _tv = _class_weights(edge_pf)
    edge_targets = dict(TARGETS, equity=cw_e["equity"] - 0.05)
    edge_plan = propose_rebalance(edge_pf, edge_targets, BANDS, CONSTRAINTS,
                                  ecm=ecm)
    record("instability_flagged_when_on_edge",
           any(f["asset_class"] == "equity" for f in edge_plan["instability"]),
           "%d instability flag(s)" % len(edge_plan["instability"]))
    again = propose_rebalance(edge_pf, edge_targets, BANDS, CONSTRAINTS,
                              ecm=ecm)
    record("no_flip_flop_deterministic",
           json.dumps(edge_plan, sort_keys=True)
           == json.dumps(again, sort_keys=True),
           "two consecutive calls byte-identical")

    # --- Case 7: all-in-band => no_action_needed, alternative still present -
    calm = propose_rebalance(pf, {"equity": 0.74, "bond": 0.21, "cash": 0.05},
                             {"equity": {"low": 0.10, "high": 0.10},
                              "bond": {"low": 0.10, "high": 0.10},
                              "cash": {"low": 0.05, "high": 0.05}},
                             CONSTRAINTS, ecm=ecm)
    record("in_band_no_action_needed", calm["status"] == "no_action_needed"
           and calm["action"] is None and calm["no_action"] is not None,
           "status=%s" % calm["status"])

    # --- Case 8: explanation renders and cites numbers ----------------------
    txt = explanation(plan)
    record("explanation_cites_numbers",
           "WHY TRADE NOW" in txt and "$" in txt and "ZPHR" in txt
           and "INSTABILITY" not in txt,
           "%d chars rendered" % len(txt))

    os.makedirs(os.path.dirname(SELFTEST_OUT), exist_ok=True)
    with open(SELFTEST_OUT, "w", encoding="ascii") as f:
        json.dump(results, f, indent=2, sort_keys=True)
    print("selftest report -> %s" % SELFTEST_OUT)
    print("ALL PASS" if results["all_pass"] else "FAILURES PRESENT")
    return 0 if results["all_pass"] else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    print(__doc__)

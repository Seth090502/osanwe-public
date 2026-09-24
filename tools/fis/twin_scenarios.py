#!/usr/bin/env python3
"""twin_scenarios.py -- FIS digital-twin scenario math.

Pure stdlib. Operates on validated household twin documents (see
tools/fis/twin_schema.py). Every result dict carries an ``assumptions``
list and a ``data_gaps`` list so downstream consumers can audit provenance.

Usage: python twin_scenarios.py --selftest
"""

import copy
import json
import os
import re
import sys

DEFAULT_MONTHLY_SPEND = 7500.0  # fixture-declared core spend (USD)
GOAL_PROB_SEED = 7
GOAL_MU = 0.06
GOAL_SIGMA = 0.15
GOAL_PROB_PATHS = 10000  # must match calcs_household.goal_funding_probability


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def load_twin(path=None):
    """Load a household twin JSON document."""
    if path is None:
        path = os.path.join(
            _repo_root(), "Efforts", "osanwe-v2-overhaul", "_work",
            "fis-data", "synthetic-households", "hh-tech-accumulator.json",
        )
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


FROZEN_SYNTHETIC_PRICES = {
    "ZPHR": 142.50,
    "TOTMKT-SYNTH": 128.40,
    "TGT2055-SYNTH": 62.00,
    "USAGG-SYNTH": 42.00,
    "HSAIDX-SYNTH": 58.00,
}


def _holdings_mv(acct, prices=None, data_gaps=None):
    """Holdings market value.

    DEFECT FIX (W8-F1). Previously an unknown symbol was priced at 0.0 via
    ``prices.get(symbol, 0.0)``, so an UNPRICED position was silently
    indistinguishable from a position genuinely worth nothing. Six of the
    seven shipped synthetic households therefore reported reconciles=False
    with no indication of why, while validate_twin() reported zero schema
    errors.

    An unpriced asset is NOT a zero-value asset. A symbol with no mark is
    now excluded from the sum and reported as a data gap naming the symbol,
    so the caller can see exactly which positions could not be valued.
    """
    table = FROZEN_SYNTHETIC_PRICES if prices is None else prices
    mv = 0.0
    for h in acct.get("holdings") or []:
        sym = h.get("symbol")
        qty = float(h.get("qty", 0.0))
        px = table.get(sym)
        if px is None:
            if data_gaps is not None:
                data_gaps.append(
                    "no price for %s in account %s; contribution of %.4f "
                    "units EXCLUDED from market value"
                    % (sym, acct.get("id", "?"), qty))
            continue
        mv += qty * float(px)
    return mv


def _account_value(acct, prices=None, data_gaps=None):
    """Value of one account: stated balance (scenario-adjusted) else holdings."""
    if acct.get("balance") is not None:
        return float(acct["balance"])
    return _holdings_mv(acct, prices=prices, data_gaps=data_gaps)


def _liabilities_total(doc):
    return sum(float(l.get("balance", 0.0)) for l in doc.get("liabilities") or [])


def _monthly_spend(doc):
    """Derive monthly core spend from the doc, else the declared default."""
    txt = (doc.get("assumptions") or {}).get("emergency_fund", "")
    m = re.search(r"\$([0-9][0-9,]*)\.?[0-9]*\s*(?:per month|/month|monthly)", txt)
    if m:
        return float(m.group(1).replace(",", ""))
    # fall back to mortgage min payment as a floor-level proxy
    pays = sum(float(l.get("min_payment", 0.0)) for l in doc.get("liabilities") or [])
    return pays if pays > 0 else DEFAULT_MONTHLY_SPEND


def _gross_annual_income(doc):
    total = 0.0
    for mem in doc.get("members") or []:
        streams = ((mem.get("employment") or {}).get("income_streams")) or []
        total += sum(float(s.get("amount", 0.0)) for s in streams)
    return total


def _goal_probability(doc):
    """Deterministic MC funding probability for the nearest-term goal.

    Uses calcs_household.goal_funding_probability when importable;
    otherwise falls back to a closed-form-free deterministic scalar so the
    module stays usable standalone.
    """
    goals = sorted(doc.get("goals") or [], key=lambda g: g.get("target_date", ""))
    if not goals:
        return None
    goal = goals[0]
    investable = sum(
        _account_value(a) for a in doc.get("accounts") or []
        if a.get("type") != "cash"
    ) - _liabilities_total(doc)
    investable = max(investable, 0.0)
    contrib = 0.20 * _gross_annual_income(doc)
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from calcs_household import goal_funding_probability
        res = goal_funding_probability(
            current_balance=investable,
            annual_contribution=contrib,
            years=5,
            mu=GOAL_MU,
            sigma=GOAL_SIGMA,
            goal_amount=float(goal.get("target_amount", 0.0)),
            seed=GOAL_PROB_SEED,
        )
        p = float(res["probability"])
        return {
            "probability": p,
            "method": "monte-carlo",
            "paths": int(res.get("paths", GOAL_PROB_PATHS)),
            "seed": GOAL_PROB_SEED,
            "degraded": False,
        }
    except Exception as exc:
        # DEFECT FIX (W8-F3): the old code caught bare Exception and returned
        # a crude expected-value ratio as a BARE FLOAT, so a caller could not
        # distinguish a 10,000-path Monte Carlo from a deterministic ratio.
        # A silent model downgrade is worse than a failure: it looks like the
        # real answer. The result now always declares its method, and the
        # downgrade is marked degraded=True with the reason attached.
        expected = investable * ((1.0 + GOAL_MU) ** 5) + contrib * 5.0
        target = float(goal.get("target_amount", 0.0)) or 1.0
        return {
            "probability": max(0.0, min(expected / target, 1.0)),
            "method": "ev-ratio",
            "paths": 0,
            "seed": None,
            "degraded": True,
            "degraded_reason": "monte-carlo unavailable (%s: %s); fell back "
                               "to deterministic expected-value ratio -- this "
                               "is NOT a probability distribution, do not "
                               "present it as one"
                               % (type(exc).__name__, exc),
        }


def _has_dependents(doc):
    if doc.get("dependents"):
        return True
    for mem in doc.get("members") or []:
        if str(mem.get("dependent", "")).lower() in ("true", "yes"):
            return True
    return False


# ---------------------------------------------------------------------------
# core functions
# ---------------------------------------------------------------------------

def net_worth(doc, prices=None):
    """Net worth = sum of account market values minus liabilities."""
    account_sums = {}
    if prices is None:
        prices = FROZEN_SYNTHETIC_PRICES
    data_gaps = []
    total_assets = 0.0
    for acct in doc.get("accounts") or []:
        v = _account_value(acct, prices=prices, data_gaps=data_gaps)
        account_sums[acct.get("id", "?")] = round(v, 2)
        total_assets += v
    liab = _liabilities_total(doc)
    value = total_assets - liab
    # Per-account reconciliation with an explicit reason per failure.
    # DEFECT FIX (W8-F2): the old code accumulated a `holdings_mv` variable,
    # poisoned it with float('nan') on a per-account mismatch, and then never
    # read it again -- dead code that read like a real signal. Removed.
    reconcile_detail = []
    for a in doc.get("accounts") or []:
        if not a.get("holdings"):
            continue
        stated = float(a.get("balance", 0.0))
        gaps_before = len(data_gaps)
        mv = _holdings_mv(a, prices=prices, data_gaps=data_gaps)
        new_gaps = data_gaps[gaps_before:]
        tol = max(1.0, 0.001 * stated)
        ok = abs(stated - mv) <= tol
        reconcile_detail.append({
            "account_id": a.get("id", "?"),
            "stated_balance": round(stated, 2),
            "holdings_market_value": round(mv, 2),
            "difference": round(stated - mv, 2),
            "tolerance": round(tol, 2),
            "reconciles": bool(ok),
            "unpriced_symbols": [
                g.split("no price for ")[1].split(" ")[0] for g in new_gaps],
        })
    reconciles = all(d["reconciles"] for d in reconcile_detail)
    nw = {
        "value": round(value, 2),
        "total_assets": round(total_assets, 2),
        "total_liabilities": round(liab, 2),
        "account_sums": account_sums,
        "reconciles": bool(reconciles),
        # WHY it does not reconcile, not merely that it does not.
        "reconcile_detail": reconcile_detail,
        "data_gaps": data_gaps,
        "valuation_method": (
            "frozen-synthetic-price-table"
            if prices is FROZEN_SYNTHETIC_PRICES
            else "caller-supplied-prices"),
        "assumptions": [
            "holdings valued at frozen synthetic price table (as_of %s)"
            % doc.get("as_of", "unknown"),
            "cash accounts valued at stated balance",
            "net worth = assets minus liabilities at face value",
        ],
    }
    # DEFECT FIX (W8-F1 follow-on): the dict literal used to REOPEN a
    # "data_gaps" key here, which silently overwrote the computed gap list
    # with a two-line generic message. The specific "no price for SYMBOL"
    # gaps survived only inside reconcile_detail and vanished from the
    # top-level list callers actually read. Append instead of overwrite.
    nw["data_gaps"].append("no intraday pricing; single frozen snapshot")
    if not reconciles:
        nw["data_gaps"].append(
            "at least one account balance does not equal holdings market "
            "value; see reconcile_detail for the per-account reason")
    return nw


def annual_cash_flow(doc):
    """Gross income minus debt service; savings rate on gross income."""
    income = _gross_annual_income(doc)
    debt_service = sum(
        float(l.get("min_payment", 0.0)) * 12.0 for l in doc.get("liabilities") or []
    )
    premiums = 0.0
    for pol in doc.get("insurance") or []:
        prem = float(pol.get("premium", 0.0))
        freq = str(pol.get("premium_freq", "monthly")).lower()
        mult = {"monthly": 12.0, "annual": 1.0, "quarterly": 4.0}.get(freq, 12.0)
        premiums += prem * mult
    net = income - debt_service - premiums
    return {
        "gross_income": round(income, 2),
        "debt_service": round(debt_service, 2),
        "insurance_premiums": round(premiums, 2),
        "net_cash_flow": round(net, 2),
        "savings_rate": round(net / income, 6) if income > 0 else 0.0,
        "assumptions": [
            "income = employment income_streams only (human capital excluded)",
            "debt service = minimum payments annualized",
            "no tax withholding modeled",
        ],
        "data_gaps": [
            "living expenses not itemized in document",
            "bonus/equity vesting timing not modeled here",
        ],
    }


def liquidity_months(doc):
    """Months of core spend covered by cash-type accounts."""
    spend = _monthly_spend(doc)
    cash = sum(
        _account_value(a) for a in doc.get("accounts") or []
        if a.get("type") == "cash"
    )
    months = cash / spend if spend > 0 else 0.0
    return {
        "months_of_cover": round(months, 4),
        "cash_total": round(cash, 2),
        "monthly_spend": round(spend, 2),
        "assumptions": [
            "only type=cash accounts count as liquid",
            "monthly spend derived from document assumptions (%.2f)" % spend,
            "no credit lines counted",
        ],
        "data_gaps": [
            "brokerage liquidation not counted though partially liquid",
        ],
    }


def apply_job_loss(doc, months):
    """Scenario: all employment income stops for `months`.

    Household draws `months` x monthly spend from cash (no new income).
    Returns a deep-copied doc annotated with the scenario marker.
    """
    out = copy.deepcopy(doc)
    spend = _monthly_spend(doc)
    draw = months * spend
    remaining = draw
    for acct in out.get("accounts") or []:
        if acct.get("type") == "cash" and remaining > 0:
            take = min(float(acct.get("balance", 0.0)), remaining)
            acct["balance"] = round(float(acct.get("balance", 0.0)) - take, 2)
            remaining -= take
    for mem in out.get("members") or []:
        emp = mem.get("employment")
        if isinstance(emp, dict):
            emp["status"] = "unemployed_scenario_%dm" % int(months)
    unspent = max(remaining, 0.0)
    out["scenario"] = {
        "kind": "job_loss",
        "months": int(months),
        "cash_drawn": round(draw - unspent, 2),
        "shortfall_if_any": round(unspent, 2),
    }
    return out


def apply_market_decline(doc, pct):
    """Scenario: instantaneous market move of `pct` (e.g. -0.35).

    Applies to every non-cash account balance and holding basis proportionally.
    Cash is untouched. Returns a deep-copied annotated doc.
    """
    out = copy.deepcopy(doc)
    factor = 1.0 + float(pct)
    for acct in out.get("accounts") or []:
        if acct.get("type") == "cash":
            continue
        acct["balance"] = round(float(acct.get("balance", 0.0)) * factor, 2)
        for h in acct.get("holdings") or []:
            for lot in h.get("tax_lots") or []:
                lot["cost_basis"] = round(float(lot.get("cost_basis", 0.0)) * factor, 2)
    out["scenario"] = {
        "kind": "market_decline",
        "pct": float(pct),
        "applies_to": "all non-cash accounts",
    }
    return out


def insurance_gap(doc):
    """Life/disability coverage gap analysis.

    Returns NOT-APPLICABLE marker when the document shows no dependents.
    """
    common = {
        "assumptions": [
            "need = 10x gross income for life cover, 60% income replacement for disability",
        ],
        "data_gaps": ["beneficiary ages/needs not modeled"],
    }
    if not _has_dependents(doc):
        res = {
            "status": "NOT-APPLICABLE",
            "reason": "document declares no dependents; life-cover need not established",
            "life_gap": None,
            "disability_gap": None,
        }
        res.update(common)
        return res
    income = _gross_annual_income(doc)
    life_need = 10.0 * income
    life_cover = sum(
        float(p.get("coverage_amount", 0.0)) for p in doc.get("insurance") or []
        if p.get("kind") == "life"
    )
    dis_monthly = sum(
        float(p.get("coverage_amount", 0.0)) for p in doc.get("insurance") or []
        if p.get("kind") == "disability"
    )
    return {
        "status": "APPLICABLE",
        "life_gap": round(life_need - life_cover, 2),
        "disability_gap_monthly": round(max(0.0, 0.60 * income / 12.0 - dis_monthly), 2),
        "assumptions": common["assumptions"],
        "data_gaps": common["data_gaps"],
    }


# ---------------------------------------------------------------------------
# selftest
# ---------------------------------------------------------------------------

def run_selftest():
    lines = []

    def check(label, cond):
        lines.append("%s: %s" % ("PASS" if cond else "FAIL", label))
        if not cond:
            raise AssertionError(label)

    doc = load_twin()

    nw = net_worth(doc)
    bal_sum = sum(float(a.get("balance", 0.0)) for a in doc["accounts"])
    liab = _liabilities_total(doc)
    check("net_worth.value > 0 (%.2f)" % nw["value"], nw["value"] > 0)
    check("net worth equals balances minus liabilities",
          abs(nw["value"] - (bal_sum - liab)) < 1.0)
    check("net worth reconciles with holdings", nw["reconciles"] is True)

    base_liq = liquidity_months(doc)["months_of_cover"]
    liq3 = liquidity_months(apply_job_loss(doc, 3))["months_of_cover"]
    liq6 = liquidity_months(apply_job_loss(doc, 6))["months_of_cover"]
    check("baseline liquidity %.2f > 3mo-loss %.2f > 6mo-loss %.2f"
          % (base_liq, liq3, liq6), base_liq > liq3 > liq6)

    base_nw = net_worth(doc)["value"]
    shock_nw = net_worth(apply_market_decline(doc, -0.35))["value"]
    base_g = _goal_probability(doc)
    shock_g = _goal_probability(apply_market_decline(doc, -0.35))
    base_p = base_g["probability"]
    shock_p = shock_g["probability"]
    check("market_decline(-0.35) reduces net worth (%.2f -> %.2f)" % (base_nw, shock_nw),
          shock_nw < base_nw)
    check("market_decline(-0.35) reduces goal probability (%s -> %s)" % (base_p, shock_p),
          base_p is not None and shock_p is not None and shock_p <= base_p)
    check("goal probability declares its method (%s / %s)"
          % (base_g.get("method"), shock_g.get("method")),
          "method" in base_g and "method" in shock_g
          and base_g["method"] == shock_g["method"] == "monte-carlo")
    check("goal probability not silently degraded (degraded=%s/%s)"
          % (base_g.get("degraded"), shock_g.get("degraded")),
          not base_g.get("degraded") and not shock_g.get("degraded"))

    gap = insurance_gap(doc)
    check("insurance_gap NOT-APPLICABLE without dependents (%s)" % gap["status"],
          gap["status"] == "NOT-APPLICABLE")

    cf = annual_cash_flow(doc)
    check("annual_cash_flow fields present", cf["gross_income"] > 0 and "net_cash_flow" in cf)

    lines.append("SELFTEST OK: twin_scenarios")
    return "\n".join(lines)


if __name__ == "__main__":
    print(run_selftest())

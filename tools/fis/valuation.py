"""Deterministic operating DCF and implied-expectations analysis.

Model: annual, nominal, unlevered FCFF discounted at nominal WACC in one
currency. Growth consumes capital; stable growth requires g / ROIC reinvestment.
Source: Damodaran, Excess Returns and Terminal Value (NYU Stern).
This module validates declared assumptions, not the truth of issuer evidence.
No prices, tax rates, forecasts, market data or account information are fetched.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
from datetime import date
import json
import math

VERSION = "operating-fcff-v1"
SOURCE = "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/valquestions/termvalueexreturns.htm"


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(name + " must be a finite number")
    return float(value)


def _bounded(value, name, lower, upper, *, left_open=False):
    value = _number(value, name)
    if value > upper or (value <= lower if left_open else value < lower):
        raise ValueError(name + " outside declared model domain")
    return value


@dataclass(frozen=True)
class OperatingDCF:
    revenue: float
    growth: tuple[float, ...]
    margins: tuple[float, ...]
    tax_rates: tuple[float, ...]
    sales_to_capital: tuple[float, ...]
    wacc: tuple[float, ...]
    terminal_growth: float
    terminal_margin: float
    terminal_tax_rate: float
    terminal_roic: float
    terminal_wacc: float
    cash: float
    debt: float
    other_claims: float
    diluted_shares: float
    currency: str
    as_of: str
    input_ids: tuple[str, ...]
    release_capital_on_decline: bool = False


def operating_dcf(spec: OperatingDCF):
    """Return the full cash-flow bridge, discount factors and equity bridge.

    No immediate tax credit on operating losses; NOLs, optionality, distress,
    financial institutions and varying share counts need other explicit models.
    Declining sales release capital ONLY with the explicit release flag.
    """
    if not isinstance(spec, OperatingDCF):
        raise ValueError("OperatingDCF inputs required")
    n = len(spec.growth)
    if not 1 <= n <= 100 or any(len(x) != n for x in
                              (spec.margins, spec.tax_rates, spec.sales_to_capital, spec.wacc)):
        raise ValueError("one aligned annual forecast vector per driver required")
    date.fromisoformat(spec.as_of)
    if (not isinstance(spec.currency, str) or len(spec.currency) != 3
            or not spec.currency.isascii() or not spec.currency.isupper()
            or not spec.currency.isalpha()):
        raise ValueError("explicit three-letter currency required")
    if (not isinstance(spec.input_ids, (list, tuple)) or not spec.input_ids
            or any(not isinstance(i, str) or not i.strip() for i in spec.input_ids)
            or len(set(spec.input_ids)) != len(spec.input_ids)):
        raise ValueError("unique nonblank input provenance IDs required")
    if not isinstance(spec.release_capital_on_decline, bool):
        raise ValueError("release_capital_on_decline must be boolean")
    revenue = _bounded(spec.revenue, "revenue", 0, math.inf, left_open=True)
    shares = _bounded(spec.diluted_shares, "diluted_shares", 0, math.inf, left_open=True)
    cash, debt, claims = [_bounded(v, k, 0, math.inf) for k, v in
                          (("cash", spec.cash), ("debt", spec.debt), ("other_claims", spec.other_claims))]
    g = _bounded(spec.terminal_growth, "terminal_growth", 0, 1)
    margin = _bounded(spec.terminal_margin, "terminal_margin", 0, 1)
    tax = _bounded(spec.terminal_tax_rate, "terminal_tax_rate", 0, 1)
    roic = _bounded(spec.terminal_roic, "terminal_roic", 0, math.inf, left_open=True)
    twacc = _bounded(spec.terminal_wacc, "terminal_wacc", 0, 1, left_open=True)
    if not g < twacc or g > roic:
        raise ValueError("stable growth needs WACC > g and ROIC >= g")
    rows, discount = [], 1.0
    for j in range(n):
        growth = _bounded(spec.growth[j], "growth", -1, math.inf, left_open=True)
        m = _bounded(spec.margins[j], "margin", -1, 1)
        t = _bounded(spec.tax_rates[j], "tax_rate", 0, 1)
        stc = _bounded(spec.sales_to_capital[j], "sales_to_capital", 0, math.inf, left_open=True)
        wacc = _bounded(spec.wacc[j], "wacc", 0, 1, left_open=True)
        prior, revenue = revenue, revenue * (1 + growth)
        ebit = revenue * m
        cash_tax = max(ebit, 0.0) * t
        nopat = ebit - cash_tax
        incremental = revenue - prior
        reinvestment = (incremental if spec.release_capital_on_decline else max(0, incremental)) / stc
        fcff = nopat - reinvestment
        discount *= 1 + wacc
        row = dict(year=j + 1, revenue=revenue, ebit=ebit, cash_tax=cash_tax,
                   nopat=nopat, reinvestment=reinvestment, fcff=fcff,
                   discount_factor=1 / discount, present_value=fcff / discount)
        if not all(math.isfinite(v) for v in row.values()):
            raise ValueError("nonfinite DCF intermediate; forecast cannot be represented")
        rows.append(row)
    terminal_nopat = revenue * (1 + g) * margin * (1 - tax)
    terminal_reinvestment = terminal_nopat * g / roic
    terminal_fcff = terminal_nopat - terminal_reinvestment
    terminal_value = terminal_fcff / (twacc - g)
    pv_terminal = terminal_value / discount
    ev = math.fsum(r["present_value"] for r in rows) + pv_terminal
    raw_equity = ev + cash - debt - claims
    per_share=max(0,raw_equity)/shares
    terminal_fraction=pv_terminal/ev if ev>0 else None
    if not all(math.isfinite(x) for x in (terminal_value, pv_terminal, ev, raw_equity,per_share)) or (terminal_fraction is not None and not math.isfinite(terminal_fraction)):
        raise ValueError("nonfinite valuation; inputs outside numerical range")
    warnings = ["assumption-dependent valuation; source support requires evidence review",
                "annual year-end nominal FCFF; tax losses have no immediate cash benefit",
                "no distress, dilution path, pension, lease or option model beyond supplied claims"]
    if raw_equity <= 0:
        warnings.append("nonpositive equity bridge; distress/option value requires separate analysis")
    return dict(model_id=VERSION, status="calculated_from_declared_inputs", source=SOURCE,
                currency=spec.currency, as_of=spec.as_of, input_ids=list(spec.input_ids),
                forecast=rows, terminal_nopat=terminal_nopat,
                terminal_reinvestment=terminal_reinvestment, terminal_fcff=terminal_fcff,
                terminal_value=terminal_value, terminal_present_value=pv_terminal,
                enterprise_value=ev, cash=cash, debt=debt, other_claims=claims,
                equity_value_unfloored=raw_equity, equity_value=max(0, raw_equity),
                diluted_shares=shares, value_per_share=per_share,
                terminal_fraction_of_ev=terminal_fraction,
                warnings=warnings)


def implied_operating_margin(spec, price, *, low=0.0, high=1.0, tolerance=1e-10):
    """Solve the common forecast/terminal margin implied by a supplied price.

    Other inputs are held fixed; this is a conditional expectation, not a forecast.
    The common nonnegative margin has a monotonic equity-value bridge. Refuse
    missing brackets; never return a best-effort bound as a solved expectation.
    """
    price = _bounded(price, "price", 0, math.inf, left_open=True)
    low = _bounded(low, "low", 0, 1)
    high = _bounded(high, "high", 0, 1)
    tol = _bounded(tolerance, "tolerance", 0, 1e-3, left_open=True)
    if not low < high:
        raise ValueError("ordered margin bracket required")
    def f(m):
        out = operating_dcf(replace(spec, margins=(m,) * len(spec.growth), terminal_margin=m))
        return out["equity_value_unfloored"] / out["diluted_shares"] - price
    left, right = f(low), f(high)
    if right <= left or left > 0 or right < 0:
        raise ValueError("target price has no unique solution in the supplied margin bracket")
    a, b = low, high
    for _ in range(100):
        m = (a + b) / 2
        residual = f(m)
        if abs(residual) <= tol * max(1.0, price):
            return dict(implied_margin=m, price_residual=residual, supplied_price=price,
                        status="solved_conditional_on_other_inputs", original_bracket=[low, high])
        if residual < 0:
            a = m
        else:
            b = m
    raise ValueError("implied-margin solver did not meet residual tolerance")


def sensitivity(spec, *, discount_shifts, terminal_growths):
    """Inspectable parallel discount-rate shifts x terminal-growth cases."""
    discount_shifts,terminal_growths=tuple(discount_shifts),tuple(terminal_growths)
    if not discount_shifts or not terminal_growths:
        raise ValueError("nonempty sensitivity axes required")
    result = []
    for shift in discount_shifts:
        shift = _number(shift, "discount_shift")
        for growth in terminal_growths:
            case = dict(discount_shift=shift, terminal_growth=growth)
            try:
                out = operating_dcf(replace(spec, wacc=tuple(w + shift for w in spec.wacc),
                                            terminal_wacc=spec.terminal_wacc + shift,
                                            terminal_growth=growth))
                case.update(status="calculated", value_per_share=out["value_per_share"],
                            terminal_fraction_of_ev=out["terminal_fraction_of_ev"])
            except ValueError as exc:
                case.update(status="refused", reason=str(exc))
            result.append(case)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="OperatingDCF JSON; input IDs reference reviewed evidence")
    ap.add_argument("--implied-price", type=float)
    args = ap.parse_args()
    try:
        with open(args.input, encoding="utf-8") as stream:
            spec = OperatingDCF(**json.load(stream))
        out = operating_dcf(spec)
        if args.implied_price is not None:
            out["implied_margin"] = implied_operating_margin(spec, args.implied_price)
        print(json.dumps(out, allow_nan=False, sort_keys=True))
    except (ValueError, TypeError, OSError, OverflowError) as exc:
        print(json.dumps({"status": "refused", "reason": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

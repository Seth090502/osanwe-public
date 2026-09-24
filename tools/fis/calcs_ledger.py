#!/usr/bin/env python3
"""S2 calc-layer extension: double-entry ledger and planning math.

Modules:
  * DoubleEntryLedger -- postings in CENT-EXACT integer cents; every
    entry MUST sum to exactly zero or posting raises UnbalancedEntryError.
    No silent acceptance of drift, ever.
  * reconcile_account -- compare an account's ledger activity against
    externally supplied statement lines; reports matched pairs,
    ledger-only items, statement-only items, and the balance gap.
  * brinson_attribution -- Brinson-style performance attribution of a
    portfolio vs a benchmark: allocation + selection + interaction.
    Algebraic guarantee (property-tested): the three effects sum EXACTLY
    to portfolio return minus benchmark return (within float epsilon;
    asserted < 1e-9 for arbitrary random portfolios).
  * retirement_projection -- deterministic accumulation phase (fixed
    return, annual contributions) followed by a drawdown phase sequenced
    with calcs_household.retirement_withdrawals (G2 ordering).
  * insurance_needs -- human-capital life-insurance gap: PV of the
    income-replacement stream (ordinary annuity) + outstanding debts +
    final expenses - existing liquid assets.
  * convert_currency -- explicit-rate FX conversion. The rate and its
    as-of timestamp are REQUIRED parameters; there is NO default rate
    and no silent fallback anywhere in this module.

Money policy:
  * Ledger postings are integer cents (ROUND-HALF-AWAY-FROM-ZERO on the
    way in via to_cents-style rounding of dollar inputs).
  * Attribution/projection/insurance outputs are float ESTIMATES, never
    ledger entries.

Typed errors (never NaN, never silent zeros):
  FisCalcError
    +- MissingInputError      required input absent / None / blank
    +- UnbalancedEntryError   debits != credits on a posting
    +- CurrencyRateError      bad FX rate (non-finite, <= 0)

Every result object carries "formula_version" = FORMULA_VERSION.

Run `python calcs_ledger.py` to execute the self-test suite
(known-answer tests + property-based randomized tests, stdlib `random`
only -- no hypothesis dependency).  A run summary is written to
_work/fis-data/calcs_ledger_selftest.json.

Stdlib only. ASCII only. No network access.
"""

from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

try:  # package-relative when imported as tools.fis.calcs_ledger
    from . import calcs_core
    from . import calcs_household
except ImportError:  # standalone script execution
    import calcs_core
    import calcs_household

FORMULA_VERSION = "fis-calcs-ledger-1.0.0"


# ---------------------------------------------------------------------------
# Typed errors
# ---------------------------------------------------------------------------


class FisCalcError(Exception):
    """Base class for all typed calc-layer errors."""


class MissingInputError(FisCalcError):
    """A required input was absent, None, empty, or non-numeric."""


class UnbalancedEntryError(FisCalcError):
    """A journal entry's legs do not sum to exactly zero cents."""


class CurrencyRateError(FisCalcError):
    """An FX rate is unusable (None handled upstream, here: non-finite/<=0)."""


def _require(condition: bool, exc: FisCalcError) -> None:
    if condition:
        raise exc


def _stamp(result: Dict[str, object]) -> Dict[str, object]:
    """Stamp formula_version onto a result dict and return it."""
    result["formula_version"] = FORMULA_VERSION
    return result


def _dollars_to_cents(amount: float) -> int:
    """Dollars -> integer cents, half away from zero (matches household)."""
    return calcs_household.to_cents(float(amount))


# ---------------------------------------------------------------------------
# Double-entry ledger
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Leg:
    """One account side of a journal entry, in integer cents."""

    account: str
    cents: int          # positive = debit convention-free signed amount


@dataclass(frozen=True)
class Entry:
    """An immutable posted journal entry."""

    entry_id: int
    date: str                       # ISO date string
    description: str
    legs: Tuple[Leg, ...]


class DoubleEntryLedger:
    """Cent-exact double-entry ledger.

    Invariant enforced at EVERY posting: sum(leg.cents) == 0 exactly,
    otherwise UnbalancedEntryError and nothing is recorded.
    """

    def __init__(self) -> None:
        self._entries: List[Entry] = []
        self._balances: Dict[str, int] = {}
        self._next_id = 1

    # -- posting -----------------------------------------------------------

    def post(
        self,
        date: str,
        description: str,
        legs: Sequence[Tuple[str, float]],
        amounts_are_cents: bool = False,
    ) -> Entry:
        """Post one journal entry.

        legs: iterable of (account, amount) pairs. Amounts are dollars
        unless amounts_are_cents=True. The signed amounts must sum to
        exactly zero after conversion to cents, or UnbalancedEntryError
        is raised and NOTHING is recorded.
        """
        _require(not date, MissingInputError("post: 'date' is required"))
        _require(description is None or description == "",
                 MissingInputError("post: 'description' is required"))
        if legs is None or len(list(legs)) == 0:
            raise MissingInputError("post: at least one leg is required")

        cent_legs: List[Leg] = []
        for acct, amt in legs:
            if not acct or acct is None:
                raise MissingInputError("post: every leg needs an account name")
            if amt is None:
                raise MissingInputError(
                    "post: None amount for account %r" % (acct,))
            cents = int(amt) if amounts_are_cents else _dollars_to_cents(amt)
            if cents != 0 or True:
                pass  # zero legs are legal but pointless; keep them out anyway
            if cents == 0:
                continue
            cent_legs.append(Leg(str(acct), cents))

        if not cent_legs:
            raise MissingInputError("post: all legs rounded to zero cents")
        total = sum(l.cents for l in cent_legs)
        if total != 0:
            raise UnbalancedEntryError(
                "entry does not balance: legs sum to %+d cents (%s)"
                % (total, description)
            )

        entry = Entry(self._next_id, str(date), str(description),
                      tuple(cent_legs))
        self._next_id += 1
        self._entries.append(entry)
        for leg in cent_legs:
            self._balances[leg.account] = (
                self._balances.get(leg.account, 0) + leg.cents
            )
        return entry

    # -- queries -------------------------------------------------------------

    @property
    def entries(self) -> List[Entry]:
        return list(self._entries)

    def balance_cents(self, account: str) -> int:
        return self._balances.get(account, 0)

    def balance(self, account: str) -> float:
        return calcs_household.from_cents(self.balance_cents(account))

    def trial_balance_cents(self) -> Dict[str, int]:
        return dict(sorted(self._balances.items()))

    def trial_balance_total_cents(self) -> int:
        """Always exactly 0 for a well-formed ledger; exposed for audits."""
        return sum(self._balances.values())

    def account_lines_cents(self, account: str) -> List[Tuple[int, int]]:
        """(entry_id, cents) activity lines touching `account`, in post order."""
        out: List[Tuple[int, int]] = []
        for e in self._entries:
            for leg in e.legs:
                if leg.account == account:
                    out.append((e.entry_id, leg.cents))
        return out


# ---------------------------------------------------------------------------
# Account reconciliation vs statement lines
# ---------------------------------------------------------------------------


def reconcile_account(
    ledger: DoubleEntryLedger,
    account: str,
    statement_lines: Sequence[float],
    tolerance_cents: int = 0,
) -> Dict[str, object]:
    """Reconcile ledger activity on `account` against bank statement lines.

    Greedy one-to-one matching: each ledger line matches at most one
    statement line whose absolute difference is within `tolerance_cents`
    (smallest difference first). Returns matched pairs, unmatched items
    on each side, and the residual balance gap in cents.

    Raises MissingInputError if account is blank or statement_lines is
    None. An EMPTY statement list is legal (everything is ledger-only).
    """
    if not account:
        raise MissingInputError("reconcile_account: 'account' is required")
    if statement_lines is None:
        raise MissingInputError(
            "reconcile_account: 'statement_lines' is required")

    stmt_cents = [_dollars_to_cents(s) for s in statement_lines]
    led_lines = ledger.account_lines_cents(account)

    candidates: List[Tuple[int, int, int, int]] = []
    # (abs diff, ledger index, stmt index, signed diff)
    for li, (_eid, lc) in enumerate(led_lines):
        for si, sc in enumerate(stmt_cents):
            d = lc - sc
            candidates.append((abs(d), li, si, d))
    candidates.sort(key=lambda t: (t[0], t[1], t[2]))

    used_l: set = set()
    used_s: set = set()
    matched: List[Dict[str, object]] = []
    for adiff, li, si, sdiff in candidates:
        if adiff > max(0, int(tolerance_cents)):
            break
        if li in used_l or si in used_s:
            continue
        used_l.add(li)
        used_s.add(si)
        matched.append({
            "ledger_entry_id": led_lines[li][0],
            "ledger_cents": led_lines[li][1],
            "statement_cents": stmt_cents[si],
            "difference_cents": sdiff,
        })

    ledger_only = [led_lines[i] for i in sorted(set(range(len(led_lines))) - used_l)]
    stmt_only = [stmt_cents[i] for i in sorted(set(range(len(stmt_cents))) - used_s)]
    gap = (sum(lc for _, lc in ledger_only) - sum(stmt_only))
    return _stamp({
        "matched": matched,
        "ledger_only": [{"entry_id": eid, "cents": c} for eid, c in ledger_only],
        "statement_only": stmt_only,
        "n_matched": len(matched),
        "balance_gap_cents": gap,
        "is_reconciled": gap == 0 and not ledger_only and not stmt_only,
    })


# ---------------------------------------------------------------------------
# Brinson-style portfolio attribution
# ---------------------------------------------------------------------------


def brinson_attribution(
    portfolio_weights: Dict[str, float],
    portfolio_returns: Dict[str, float],
    benchmark_weights: Dict[str, float],
    benchmark_returns: Dict[str, float],
) -> Dict[str, object]:
    """Brinson attribution with explicit interaction term.

    Per segment i:
      allocation_i  = (wp_i - wb_i) * (rb_i - rb_total)
      selection_i   = wb_i * (rp_i - rb_i)
      interaction_i = (wp_i - wb_i) * (rp_i - rb_i)
    Identity: sum(allocation) + sum(selection) + sum(interaction)
              == rp_total - rb_total   (exactly, up to float eps)

    All four dicts must cover the SAME segment keys; anything missing on
    either side raises MissingInputError (never treated as zero weight).
    """
    for name, d in (("portfolio_weights", portfolio_weights),
                    ("portfolio_returns", portfolio_returns),
                    ("benchmark_weights", benchmark_weights),
                    ("benchmark_returns", benchmark_returns)):
        if d is None:
            raise MissingInputError("brinson_attribution: %s is required" % name)
    keys_p = set(portfolio_weights) & set(portfolio_returns)
    keys_b = set(benchmark_weights) & set(benchmark_returns)
    # A segment is only usable if it appears in ALL FOUR dicts.
    all_keys = keys_p | keys_b
    missing_b = sorted(k for k in all_keys
                       if k not in benchmark_weights or k not in benchmark_returns)
    missing_p = sorted(k for k in all_keys
                       if k not in portfolio_weights or k not in portfolio_returns)
    if missing_b:
        raise MissingInputError(
            "brinson_attribution: segments missing benchmark data: %s"
            % ", ".join(missing_b))
    if missing_p:
        raise MissingInputError(
            "brinson_attribution: segments missing portfolio data: %s"
            % ", ".join(missing_p))
    segments = sorted(keys_p | keys_b)
    _require(not segments, MissingInputError(
        "brinson_attribution: at least one segment is required"))

    rp_total = sum(float(portfolio_weights[k]) * float(portfolio_returns[k])
                   for k in segments)
    rb_total = sum(float(benchmark_weights[k]) * float(benchmark_returns[k])
                   for k in segments)

    detail: List[Dict[str, float]] = []
    alloc = sel = inter = 0.0
    for k in segments:
        wp = float(portfolio_weights[k]); rp = float(portfolio_returns[k])
        wb = float(benchmark_weights[k]); rb = float(benchmark_returns[k])
        a = (wp - wb) * (rb - rb_total)
        s = wb * (rp - rb)
        x = (wp - wb) * (rp - rb)
        alloc += a; sel += s; inter += x
        detail.append({"segment": k, "allocation_effect": a,
                       "selection_effect": s, "interaction_effect": x})

    excess = rp_total - rb_total
    residual = abs((alloc + sel + inter) - excess)
    _require(residual > 1e-6, FisCalcError(
        "brinson_attribution: effects do not reconcile (residual %.3e)"
        % residual))
    return _stamp({
        "portfolio_return": rp_total,
        "benchmark_return": rb_total,
        "total_excess_return": excess,
        "allocation_effect": alloc,
        "selection_effect": sel,
        "interaction_effect": inter,
        "unexplained_residual": residual,
        "segments": detail,
    })


# ---------------------------------------------------------------------------
# Retirement projection (deterministic accumulation + sequenced drawdown)
# ---------------------------------------------------------------------------


def retirement_projection(
    starting_balance: float,
    annual_contribution: float,
    contribution_growth: float,
    accumulation_years: int,
    accumulation_return: float,
    annual_need: float,
    drawdown_years: int,
    drawdown_return: float,
    withdrawal_order: Optional[Sequence[str]] = None,
) -> Dict[str, object]:
    """Deterministic accumulate-then-draw projection.

    Accumulation: contributions made at END of each year, growth applied
    after each year (end-of-year convention throughout). After
    accumulation_years the nest egg stops contributing and starts the
    drawdown phase, which delegates sequencing to
    calcs_household.retirement_withdrawals (G2): taxable -> traditional
    -> roth by default, growth applied AFTER each year's withdrawal.

    All monetary inputs must be present and finite; negatives other than
    a zero starting balance raise MissingInputError rather than
    producing NaNs downstream.
    """
    vals = {
        "starting_balance": starting_balance,
        "annual_contribution": annual_contribution,
        "contribution_growth": contribution_growth,
        "accumulation_return": accumulation_return,
        "annual_need": annual_need,
        "drawdown_return": drawdown_return,
    }
    for name, v in vals.items():
        if v is None:
            raise MissingInputError("retirement_projection: %s is required"
                                    % name)
        try:
            fv = float(v)
        except (TypeError, ValueError):
            raise MissingInputError(
                "retirement_projection: %s is not numeric" % name)
        if fv != fv or fv in (float("inf"), float("-inf")):
            raise MissingInputError(
                "retirement_projection: %s must be finite" % name)
    _require(int(accumulation_years) < 0, MissingInputError(
        "retirement_projection: accumulation_years must be >= 0"))
    _require(int(drawdown_years) <= 0, MissingInputError(
        "retirement_projection: drawdown_years must be >= 1"))
    _require(float(starting_balance) < 0 or float(annual_contribution) < 0,
             MissingInputError(
                 "retirement_projection: balance/contribution must be >= 0"))

    bal = float(starting_balance)
    contrib = float(annual_contribution)
    acc_timeline: List[Dict[str, float]] = []
    for _y in range(int(accumulation_years)):
        interest = bal * float(accumulation_return)
        bal += interest + contrib
        acc_timeline.append({
            "year": _y + 1,
            "interest": round(interest, 2),
            "contribution": round(contrib, 2),
            "ending_balance": round(bal, 2),
        })
        contrib *= 1.0 + float(contribution_growth)

    nest_egg = bal
    drawdown = calcs_household.retirement_withdrawals(
        balances={"nest_egg": nest_egg},
        annual_need=float(annual_need),
        years=int(drawdown_years),
        order=["nest_egg"],
        growth_rate=float(drawdown_return),
    )
    funded_years = sum(
        1 for row in drawdown["timeline"] if row["shortfall"] == 0.0)
    return _stamp({
        "nest_egg_at_retirement": round(nest_egg, 2),
        "accumulation_timeline": acc_timeline,
        "drawdown": drawdown,
        "funded_drawdown_years": funded_years,
        "fully_funded": funded_years == int(drawdown_years),
    })


# ---------------------------------------------------------------------------
# Insurance needs
# ---------------------------------------------------------------------------


def insurance_needs(
    annual_income: float,
    income_replacement_pct: float,
    replacement_years: int,
    discount_rate: float,
    outstanding_debts: float,
    final_expenses: float,
    existing_liquid_assets: float,
) -> Dict[str, object]:
    """Human-capital life-insurance gap.

    need = PV(income * replacement_pct as ordinary annuity over
    replacement_years at discount_rate)  +  outstanding_debts
    +  final_expenses  -  existing_liquid_assets

    Negative result means existing assets already cover the modeled
    obligations; it is reported as-is (clamped coverage_gap = 0).
    Every input must be present; discount_rate must be > -100 percent.
    """
    inputs = {
        "annual_income": annual_income,
        "income_replacement_pct": income_replacement_pct,
        "replacement_years": replacement_years,
        "discount_rate": discount_rate,
        "outstanding_debts": outstanding_debts,
        "final_expenses": final_expenses,
        "existing_liquid_assets": existing_liquid_assets,
    }
    for name, v in inputs.items():
        if v is None:
            raise MissingInputError("insurance_needs: %s is required" % name)
        try:
            float(v)
        except (TypeError, ValueError):
            raise MissingInputError(
                "insurance_needs: %s is not numeric" % name)
    _require(int(replacement_years) <= 0, MissingInputError(
        "insurance_needs: replacement_years must be >= 1"))
    _require(float(discount_rate) <= -1.0, MissingInputError(
        "insurance_needs: discount_rate must be > -100%"))

    replacement = float(annual_income) * float(income_replacement_pct)
    pv_income = calcs_core.annuity_pv(
        payment=replacement,
        rate_per_period=float(discount_rate),
        n_periods=int(replacement_years),
    )
    total_need = (pv_income + float(outstanding_debts)
                  + float(final_expenses) - float(existing_liquid_assets))
    return _stamp({
        "income_replacement_pv": pv_income,
        "debts_and_final_expenses":
            float(outstanding_debts) + float(final_expenses),
        "assets_offset": float(existing_liquid_assets),
        "total_need": total_need,
        "coverage_gap": max(total_need, 0.0),
    })


# ---------------------------------------------------------------------------
# Currency conversion (explicit rate, timestamped, no defaults)
# ---------------------------------------------------------------------------


def convert_currency(
    amount: float,
    rate: Optional[float],
    as_of: Optional[str],
    from_currency: str = "USD",
    to_currency: str = "USD",
) -> Dict[str, object]:
    """Convert `amount` from one currency to another at an EXPLICIT rate.

    `rate` and `as_of` are REQUIRED. There is no table lookup, no
    default, no staleness heuristic: passing rate=None or as_of=None
    raises MissingInputError. Non-finite or non-positive rates raise
    CurrencyRateError. Same-currency conversions still require an
    explicit rate of 1.0 -- silence is never acceptable for money.
    """
    if amount is None:
        raise MissingInputError("convert_currency: 'amount' is required")
    try:
        amt = float(amount)
    except (TypeError, ValueError):
        raise MissingInputError("convert_currency: amount is not numeric")
    if amt != amt or amt in (float("inf"), float("-inf")):
        raise MissingInputError("convert_currency: amount must be finite")
    if rate is None:
        raise MissingInputError(
            "convert_currency: 'rate' is required -- never defaulted")
    if as_of is None or str(as_of) == "":
        raise MissingInputError(
            "convert_currency: 'as_of' timestamp is required -- never defaulted")
    try:
        rt = float(rate)
    except (TypeError, ValueError):
        raise CurrencyRateError("convert_currency: rate is not numeric")
    if rt != rt or rt in (float("inf"), float("-inf")) or rt <= 0.0:
        raise CurrencyRateError(
            "convert_currency: rate must be finite and > 0, got %r" % (rate,))
    if not from_currency or not to_currency:
        raise MissingInputError(
            "convert_currency: from/to currency codes are required")

    converted = amt * rt
    return _stamp({
        "amount": amt,
        "from_currency": str(from_currency).upper(),
        "to_currency": str(to_currency).upper(),
        "rate_used": rt,
        "as_of": str(as_of),
        "converted_amount": converted,
    })


# ---------------------------------------------------------------------------
# Selftest: known-answer tests + property-based randomized tests
# ---------------------------------------------------------------------------


def _selftest() -> int:
    failures: List[str] = []
    passed = 0

    def check(name: str, cond: bool, detail: str = "") -> None:
        nonlocal passed
        if cond:
            passed += 1
        else:
            failures.append("%s %s" % (name, detail))
        print("[%s] %s%s" % ("PASS" if cond else "FAIL", name,
                             (" :: " + detail) if detail else ""))

    def expect_raises(name: str, exc_type, fn) -> None:
        try:
            fn()
        except exc_type:
            check(name, True)
        except Exception as e:  # wrong exception type
            check(name, False, "raised %r instead of %s" % (e, exc_type.__name__))
        else:
            check(name, False, "no exception raised")

    approx = lambda a, b, tol=1e-9: abs(a - b) <= tol  # noqa: E731

    # ================= known-answer tests =================

    # --- Ledger: classic two-account cash purchase.
    # Buy $120.00 of supplies, pay from cash:
    #   Supplies +12000c, Cash -12000c. Balances by construction.
    led = DoubleEntryLedger()
    led.post("2026-01-05", "office supplies", [("supplies", 120.0),
                                               ("cash", -120.0)])
    check("ledger-known-balance-supplies",
          led.balance_cents("supplies") == 12000,
          "got %d" % led.balance_cents("supplies"))
    check("ledger-known-balance-cash",
          led.balance_cents("cash") == -12000,
          "got %d" % led.balance_cents("cash"))
    check("ledger-trial-total-zero", led.trial_balance_total_cents() == 0)

    # Multi-leg split deposit: 250.00 = 200.00 + 50.00.
    led.post("2026-01-06", "split deposit",
             [("cash", 250.0), ("salary", -200.0), ("interest", -50.0)])
    check("ledger-multi-leg-balances",
          led.trial_balance_total_cents() == 0
          and led.balance_cents("cash") == 13000)

    # Unbalanced postings must raise and record NOTHING.
    n_before = len(led.entries)
    expect_raises("ledger-unbalanced-raises", UnbalancedEntryError,
                  lambda: led.post("2026-01-07", "bad", [("cash", 10.0)]))
    expect_raises("ledger-unbalanced-cent-raises", UnbalancedEntryError,
                  lambda: led.post("2026-01-07", "bad",
                                   [("cash", 1.0), ("fees", -0.99)],
                                   amounts_are_cents=False))
    check("ledger-nothing-recorded-on-reject",
          len(led.entries) == n_before)

    # Missing inputs raise typed errors.
    expect_raises("ledger-missing-date", MissingInputError,
                  lambda: led.post("", "x", [("cash", 1.0), ("cash2", -1.0)]))
    expect_raises("ledger-missing-description", MissingInputError,
                  lambda: led.post("2026-01-07", "", [("a", 1.0), ("b", -1.0)]))
    expect_raises("ledger-missing-legs", MissingInputError,
                  lambda: led.post("2026-01-07", "x", []))

    # --- Reconciliation.
    led2 = DoubleEntryLedger()
    led2.post("2026-02-01", "deposit", [("checking", 500.0), ("income", -500.0)])
    led2.post("2026-02-03", "groceries", [("grocery", 80.0), ("checking", -80.0)])
    led2.post("2026-02-05", "fee", [("bank_fees", 5.0), ("checking", -5.0)])
    rec = reconcile_account(led2, "checking", [500.0, -80.0, -5.0])
    check("reconcile-clean", rec["is_reconciled"] is True
          and rec["n_matched"] == 3 and rec["balance_gap_cents"] == 0,
          "gap=%d" % rec["balance_gap_cents"])
    # One statement line the book never recorded -> gap equals it.
    rec2 = reconcile_account(led2, "checking", [500.0, -80.0, -5.0, -42.13])
    check("reconcile-missing-stmt-line",
          rec2["statement_only"] == [-4213]
          and rec2["balance_gap_cents"] == 4213
          and rec2["is_reconciled"] is False,
          "gap=%d" % rec2["balance_gap_cents"])
    # Tolerance matching: 99.99 vs 100.00 within 1 cent.
    led3 = DoubleEntryLedger()
    led3.post("2026-03-01", "pmt", [("vendor", 100.0), ("checking", -100.0)])
    rec3 = reconcile_account(led3, "checking", [-99.99], tolerance_cents=1)
    check("reconcile-tolerance-match", rec3["n_matched"] == 1
          and abs(rec3["matched"][0]["difference_cents"]) == 1)
    expect_raises("reconcile-missing-account", MissingInputError,
                  lambda: reconcile_account(led3, "", [1.0]))
    expect_raises("reconcile-missing-lines", MissingInputError,
                  lambda: reconcile_account(led3, "checking", None))

    # --- Brinson attribution, hand-checkable single-segment case.
    # One segment: wp=wb=1.0, rp=0.10, rb=0.04 -> excess 0.06,
    # allocation 0 (weights equal, rb_i == rb_total), selection 0.06,
    # interaction 0.
    att = brinson_attribution({"only": 1.0}, {"only": 0.10},
                              {"only": 1.0}, {"only": 0.04})
    check("brinson-single-segment",
          approx(att["total_excess_return"], 0.06)
          and approx(att["selection_effect"], 0.06)
          and approx(att["allocation_effect"], 0.0)
          and approx(att["interaction_effect"], 0.0),
          "alloc=%r sel=%r" % (att["allocation_effect"],
                               att["selection_effect"]))

    # Two-segment textbook case (values chosen to be hand-verifiable):
    # bench: 60% bonds @ 4%, 40% equity @ 8%  -> rb_total = 0.056
    # port : 40% bonds @ 5%, 60% equity @ 9%  -> rp_total = 0.074
    # excess = 0.018
    pw = {"bond": 0.4, "equity": 0.6}
    pr = {"bond": 0.05, "equity": 0.09}
    bw = {"bond": 0.6, "equity": 0.4}
    br = {"bond": 0.04, "equity": 0.08}
    att2 = brinson_attribution(pw, pr, bw, br)
    # allocation: bond (0.4-0.6)*(0.04-0.056) = (+0.0032)
    #             eqty (0.6-0.4)*(0.08-0.056) = (+0.0048) -> 0.0080
    # selection:  bond 0.6*(0.05-0.04)=0.006 ; eqty 0.4*(0.09-0.08)=0.004
    #             -> 0.0100
    # interaction: bond (-0.2)*(0.01)=-0.002 ; eqty (0.2)*(0.01)=0.002
    #             -> 0.0000 ; total 0.008+0.010+0.000 = 0.018 = excess
    check("brinson-two-segment-known-answer",
          approx(att2["allocation_effect"], 0.008, 1e-12)
          and approx(att2["selection_effect"], 0.010, 1e-12)
          and approx(att2["interaction_effect"], 0.0, 1e-12)
          and approx(att2["total_excess_return"], 0.018, 1e-12),
          "alloc=%r sel=%r inter=%r" % (att2["allocation_effect"],
                                        att2["selection_effect"],
                                        att2["interaction_effect"]))
    # Segment-level spot check too.
    seg_bond = [s for s in att2["segments"] if s["segment"] == "bond"][0]
    check("brinson-segment-detail",
          approx(seg_bond["allocation_effect"], 0.0032, 1e-12)
          and approx(seg_bond["selection_effect"], 0.006, 1e-12))

    expect_raises("brinson-missing-benchmark-return", MissingInputError,
                  lambda: brinson_attribution(pw, pr, bw, {}))
    expect_raises("brinson-missing-port-weight", MissingInputError,
                  lambda: brinson_attribution({}, pr, bw, br))
    expect_raises("brinson-empty", MissingInputError,
                  lambda: brinson_attribution({}, {}, {}, {}))

    # --- Retirement projection.
    # Hand answer: 0 start, 10000/yr end-of-year, 5% for 10 years ->
    # 10000 * ((1.05^10 - 1)/0.05) = 125,778.93 (rounded).
    proj = retirement_projection(
        starting_balance=0.0, annual_contribution=10000.0,
        contribution_growth=0.0, accumulation_years=10,
        accumulation_return=0.05, annual_need=50000.0, drawdown_years=1,
        drawdown_return=0.0)
    check("retire-nestegg-known-answer",
          approx(proj["nest_egg_at_retirement"], 125778.93, 0.01),
          "got %.2f" % proj["nest_egg_at_retirement"])
    # Drawdown: need 50k for 1 yr on 125,778.93 at 0% -> fully funded.
    check("retire-drawdown-one-year",
          proj["fully_funded"] is True
          and approx(proj["drawdown"]["ending_balances"]["nest_egg"],
                     75778.93, 0.01))
    # Exhaustion case: tiny egg, big need, long horizon -> shortfall.
    proj2 = retirement_projection(
        starting_balance=1000.0, annual_contribution=0.0,
        contribution_growth=0.0, accumulation_years=1,
        accumulation_return=0.0, annual_need=100000.0, drawdown_years=3,
        drawdown_return=0.0)
    check("retire-shortfall-detected",
          proj2["fully_funded"] is False
          and proj2["drawdown"]["total_shortfall"] > 0.0)
    # Contribution growth: 10k grown 10%/yr, 2 yrs, 0% return ->
    # 10,000 + 11,000 = 21,000 exactly.
    proj3 = retirement_projection(
        starting_balance=0.0, annual_contribution=10000.0,
        contribution_growth=0.10, accumulation_years=2,
        accumulation_return=0.0, annual_need=1.0, drawdown_years=1,
        drawdown_return=0.0)
    check("retire-contribution-growth",
          approx(proj3["nest_egg_at_retirement"], 21000.0, 1e-9),
          "got %.2f" % proj3["nest_egg_at_retirement"])
    expect_raises("retire-missing-rate", MissingInputError,
                  lambda: retirement_projection(
                      0.0, 100.0, 0.0, 1, None, 1.0, 1, 0.0))
    expect_raises("retire-negative-contribution", MissingInputError,
                  lambda: retirement_projection(
                      0.0, -5.0, 0.0, 1, 0.05, 1.0, 1, 0.0))
    expect_raises("retire-zero-drawdown-years", MissingInputError,
                  lambda: retirement_projection(
                      0.0, 100.0, 0.0, 1, 0.05, 1.0, 0, 0.0))
    expect_raises("retire-nan-start", MissingInputError,
                  lambda: retirement_projection(
                      float("nan"), 100.0, 0.0, 1, 0.05, 1.0, 1, 0.0))

    # --- Insurance needs. Hand answer: replace 70% of 100k for 20 yrs
    # at 5% -> annuity PV of 70,000 =
    # 70000*(1-1.05^-20)/0.05 = 872,355.05...
    ins = insurance_needs(
        annual_income=100000.0, income_replacement_pct=0.7,
        replacement_years=20, discount_rate=0.05,
        outstanding_debts=200000.0, final_expenses=15000.0,
        existing_liquid_assets=100000.0)
    expected_pv = 70000.0 * (1.0 - 1.05 ** -20) / 0.05
    check("insurance-pv-known-answer",
          approx(ins["income_replacement_pv"], expected_pv, 1e-6),
          "got %.2f want %.2f" % (ins["income_replacement_pv"], expected_pv))
    check("insurance-total-known-answer",
          approx(ins["total_need"], expected_pv + 115000.0, 1e-6),
          "got %.2f" % ins["total_need"])
    # Assets exceeding need -> negative raw need, clamped gap of 0.
    ins2 = insurance_needs(
        0.0, 0.0, 10, 0.05, outstanding_debts=0.0, final_expenses=0.0,
        existing_liquid_assets=1000000.0)
    check("insurance-surplus-clamped",
          ins2["total_need"] == -1000000.0 and ins2["coverage_gap"] == 0.0)
    expect_raises("insurance-missing-income", MissingInputError,
                  lambda: insurance_needs(
                      None, 0.7, 20, 0.05, 0.0, 0.0, 0.0))
    expect_raises("insurance-bad-years", MissingInputError,
                  lambda: insurance_needs(
                      100.0, 0.7, 0, 0.05, 0.0, 0.0, 0.0))

    # --- Currency conversion.
    fx = convert_currency(250.0, rate=1.0825, as_of="2026-08-25T09:30:00Z",
                          from_currency="USD", to_currency="EUR")
    check("fx-known-answer", approx(fx["converted_amount"], 270.625, 1e-12)
          and fx["rate_used"] == 1.0825 and fx["as_of"].startswith("2026-08-25"),
          "got %r" % fx["converted_amount"])
    expect_raises("fx-missing-rate", MissingInputError,
                  lambda: convert_currency(100.0, None, "2026-01-01"))
    expect_raises("fx-missing-timestamp", MissingInputError,
                  lambda: convert_currency(100.0, 1.1, ""))
    expect_raises("fx-nonpositive-rate", CurrencyRateError,
                  lambda: convert_currency(100.0, 0.0, "2026-01-01"))
    expect_raises("fx-nan-rate", CurrencyRateError,
                  lambda: convert_currency(100.0, float("nan"), "2026-01-01"))
    expect_raises("fx-inf-amount", MissingInputError,
                  lambda: convert_currency(float("inf"), 1.1, "2026-01-01"))
    # Even same-currency requires an explicit 1.0 -- no silent shortcut.
    expect_raises("fx-same-ccy-still-needs-rate", MissingInputError,
                  lambda: convert_currency(100.0, None, "2026-01-01",
                                           "USD", "USD"))

    # --- formula_version stamped on EVERY result object.
    stamps_ok = all(
        r.get("formula_version") == FORMULA_VERSION
        for r in (rec, rec2, rec3, att, att2, proj, proj2, proj3,
                  ins, ins2, fx))
    check("formula-version-stamped-everywhere", stamps_ok)
    check("formula-version-format",
          isinstance(FORMULA_VERSION, str) and FORMULA_VERSION.startswith("fis-"))

    # ================= property-based tests (stdlib random) =================

    rng = random.Random(20260825)

    # P1: randomized ledgers ALWAYS balance -- 400 random entries, each
    # built balanced, plus deliberate unbalanced probes rejected.
    prop_led_failures = 0
    for _ in range(400):
        pl = DoubleEntryLedger()
        n_legs = rng.randint(2, 6)
        legs: List[Tuple[str, float]] = []
        running = 0
        for j in range(n_legs - 1):
            cents = rng.randint(-5_000_00, 5_000_00)
            if cents == 0:
                cents = 1
            legs.append(("acct%d" % j, cents))
            running += cents
        legs.append(("plug", -running))       # plug forces exact balance
        pl.post("2026-01-01", "prop", legs, amounts_are_cents=True)
        if pl.trial_balance_total_cents() != 0:
            prop_led_failures += 1
        # Per-account conservation: replaying entries reproduces balances.
        replay: Dict[str, int] = {}
        for e in pl.entries:
            for lg in e.legs:
                replay[lg.account] = replay.get(lg.account, 0) + lg.cents
        if replay != pl.trial_balance_cents():
            prop_led_failures += 1
    # Unbalanced probes: off-by-one-cent plugs MUST be rejected.
    for _ in range(50):
        pl2 = DoubleEntryLedger()
        a = rng.randint(-1000, 1000) or 7
        b = -(a + (rng.choice([-1, 1])))
        try:
            pl2.post("2026-01-01", "bad",
                     [("x", a), ("y", b)], amounts_are_cents=True)
            prop_led_failures += 1          # should have raised
        except UnbalancedEntryError:
            pass                            # correct rejection
        except Exception:
            prop_led_failures += 1          # wrong exception type
    check("prop-ledgers-always-balance", prop_led_failures == 0,
          "%d failures over 450 randomized ledgers" % prop_led_failures)

    # P2: random portfolios -- attribution components sum to total
    # excess return within 1e-9 (300 random portfolios).
    attr_failures = 0
    for _ in range(300):
        k = rng.randint(1, 8)
        names = ["seg%02d" % i for i in range(k)]

        def rand_weights() -> Dict[str, float]:
            w = [rng.uniform(0.0, 1.0) for _ in names]
            tot = sum(w) or 1.0
            return {n: x / tot for n, x in zip(names, w)}

        pw_r, bw_r = rand_weights(), rand_weights()
        pr_r = {n: rng.uniform(-0.30, 0.40) for n in names}
        br_r = {n: rng.uniform(-0.20, 0.30) for n in names}
        res = brinson_attribution(pw_r, pr_r, bw_r, br_r)
        s = (res["allocation_effect"] + res["selection_effect"]
             + res["interaction_effect"])
        if abs(s - res["total_excess_return"]) > 1e-9:
            attr_failures += 1
        if abs(res["unexplained_residual"]) > 1e-9:
            attr_failures += 1
    check("prop-attribution-sums-to-excess-1e9", attr_failures == 0,
          "%d failures over 300 random portfolios" % attr_failures)

    # P3: amortization cents exactness across 500 random rate/term combos
    # (uses the S1 core schedule; ledger-layer guarantee that the money
    # primitives this layer builds on stay cent-exact).
    am_failures = 0
    for _ in range(500):
        principal = float(rng.randint(100_000, 900_000_00)) / 100.0
        apr = rng.uniform(0.0, 0.18)
        term = rng.randint(6, 360)
        rows = calcs_core.amortization_schedule(principal, apr, term)
        totals = calcs_core.amortization_totals(rows)
        if totals["total_principal"] != calcs_core._q2(
                calcs_core._to_dec(principal)):
            am_failures += 1
        if totals["total_paid"] != (totals["total_principal"]
                                    + totals["total_interest"]):
            am_failures += 1
        # Final row pays off exactly; no negative balances anywhere.
        if rows[-1].balance != 0 or any(r.balance < 0 for r in rows):
            am_failures += 1
    check("prop-amortization-cents-exact-500", am_failures == 0,
          "%d failures over 500 rate/term combos" % am_failures)

    # P4: missing-input behavior raises TYPED errors, never NaN results.
    nan_failures = 0
    probes = [
        lambda: retirement_projection(None, 1.0, 0.0, 1, 0.05, 1.0, 1, 0.0),
        lambda: retirement_projection(0.0, 1.0, 0.0, 1, 0.05, None, 1, 0.0),
        lambda: insurance_needs(None, 0.5, 10, 0.03, 0.0, 0.0, 0.0),
        lambda: insurance_needs(1.0, None, 10, 0.03, 0.0, 0.0, 0.0),
        lambda: convert_currency(None, 1.1, "2026-01-01"),
        lambda: convert_currency(1.0, None, "2026-01-01"),
        lambda: brinson_attribution(None, {}, {}, {}),
        lambda: reconcile_account(led, "checking", None),
        lambda: led.post("2026-01-01", "x", [("a", None), ("b", -1.0)]),
    ]
    for probe in probes:
        try:
            out = probe()
            if isinstance(out, dict) and any(
                    isinstance(v, float) and v != v for v in out.values()):
                nan_failures += 1
            else:
                nan_failures += 1     # no exception AND no NaN => silent path
        except FisCalcError:
            pass                      # correct: typed error
        except Exception:
            nan_failures += 1         # wrong exception type
    check("prop-missing-input-typed-errors-not-nan", nan_failures == 0,
          "%d silent/NaN/wrong-type paths" % nan_failures)

    # ---- summary + artifact -------------------------------------------------
    total_checks = passed + len(failures)
    ok = not failures
    summary = {
        "module": "tools/fis/calcs_ledger.py",
        "formula_version": FORMULA_VERSION,
        "passed": passed,
        "failed": len(failures),
        "ok": ok,
        "failures": failures,
        "property_tests": {
            "random_ledgers": 450,
            "random_portfolios_attribution": 300,
            "amortization_rate_term_combos": 500,
            "missing_input_probes": len(probes),
        },
    }
    try:
        out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "..", "_work", "fis-data")
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "calcs_ledger_selftest.json"),
                  "w", encoding="ascii") as fh:
            json.dump(summary, fh, indent=2, sort_keys=True)
        print("wrote %s" % os.path.normpath(os.path.join(
            out_dir, "calcs_ledger_selftest.json")))
    except OSError as e:
        print("note: could not write selftest artifact: %s" % e)

    print("\ncalcs_ledger selftest: %d/%d checks passed%s"
          % (passed, total_checks,
             "" if ok else "\nFAILURES:\n" + "\n".join(failures)))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(_selftest())

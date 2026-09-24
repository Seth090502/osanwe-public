#!/usr/bin/env python3
"""Deterministic household financial calculations.

Modules:
  * Tax-lot accounting: FIFO / LIFO / specific-ID lot matching,
    realized gain per sale in cent-exact arithmetic, and wash-sale
    FLAGGING (reporting only -- never adjusts or blocks anything).
  * After-tax return of a lot sequence: long-term vs short-term
    capital-gain rates are ALWAYS passed in as parameters.
  * Goal funding probability via seeded Monte Carlo (normal returns).
    A fixed seed yields bit-identical results on every run.
  * Retirement withdrawal sequencing with a parameterizable account
    order (default taxable -> traditional -> roth).
  * Emergency-months coverage ratio.

Money policy:
  * Lot accounting uses CENT-EXACT arithmetic (integer cents; no
    floating-point drift is permitted in basis/proceeds/gain).
  * Everything else uses plain float, which is acceptable because
    those outputs are estimates, not ledger entries.

Tax rates are parameters, never hardcoded law.  Callers must supply
rates with a comment naming the tax-year assumption they reflect.

Stdlib only. ASCII only. No network access.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Cent-exact helpers (lot accounting only)
# ---------------------------------------------------------------------------


def to_cents(amount: float) -> int:
    """Convert a dollar amount to integer cents (round half away from zero)."""
    if amount >= 0:
        return int(amount * 100 + 0.5)
    return -int(-amount * 100 + 0.5)


def from_cents(cents: int) -> float:
    """Convert integer cents back to a dollar float."""
    return cents / 100.0


def _round_cents(exact: float) -> int:
    """Round an exact cent-valued float to int, half away from zero."""
    if exact >= 0:
        return int(exact + 0.5)
    return -int(-exact + 0.5)


# ---------------------------------------------------------------------------
# Tax-lot accounting
# ---------------------------------------------------------------------------

FIFO = "FIFO"
LIFO = "LIFO"
SPECIFIC_ID = "SPECIFIC_ID"


@dataclass(frozen=True)
class Lot:
    """A purchase lot. All monetary fields are stored as integer cents."""

    lot_id: str
    acquire_date: str          # ISO date string, used for sorting/holding period
    shares: float              # fractional shares allowed
    cost_per_share_cents: int  # cent-exact cost basis per share
    # Optional index into an external trade sequence, used for wash-sale
    # window comparisons (e.g. day number of the acquisition).
    acquire_day: int = 0


@dataclass
class SaleResult:
    """Result of one sale matched against lots."""

    lot_id: str
    shares_sold: float
    proceeds_cents: int        # total proceeds attributed to this match
    cost_basis_cents: int      # total basis attributed to this match
    gain_cents: int            # proceeds - basis (negative = loss)
    holding_days: int          # sale_day - acquire_day
    long_term: bool            # holding_days >= lt_threshold_days
    wash_sale_flagged: bool    # flagged only; never adjusted or blocked


@dataclass
class Portfolio:
    """Open tax lots plus the full buy/sell history for wash-sale checks."""

    lots: List[Lot] = field(default_factory=list)
    # history entries: ("buy", day, shares) / ("sell", day, shares)
    history: List[Tuple[str, int, float]] = field(default_factory=list)

    def add_lot(self, lot: Lot) -> None:
        self.lots.append(lot)
        self.history.append(("buy", lot.acquire_day, lot.shares))

    def _ordered_lots(self, method: str) -> List[Lot]:
        """Return open lots in consumption order for the chosen method."""
        if method == FIFO:
            return sorted(self.lots, key=lambda l: (l.acquire_date, l.acquire_day))
        if method == LIFO:
            return sorted(
                self.lots, key=lambda l: (l.acquire_date, l.acquire_day), reverse=True
            )
        raise ValueError("method must be FIFO, LIFO, or SPECIFIC_ID")

    def sell(
        self,
        shares: float,
        price_per_share: float,
        sale_day: int,
        sale_date: str,
        method: str = FIFO,
        specific_lot_ids: Optional[Sequence[str]] = None,
        lt_threshold_days: int = 366,
        wash_sale_window_days: int = 30,
    ) -> List[SaleResult]:
        """Sell `shares` at `price_per_share`, matching lots per `method`.

        For SPECIFIC_ID pass `specific_lot_ids` in the caller's chosen
        order (out-of-order selection is explicitly supported); missing
        IDs raise KeyError. Returns one SaleResult per matched lot.
        Wash-sale losses are FLAGGED against buys within
        +/- `wash_sale_window_days` of `sale_day`; nothing is adjusted.
        """
        if shares <= 0:
            raise ValueError("shares must be positive")
        remaining = shares
        proceeds_total = to_cents(shares * price_per_share)
        results: List[SaleResult] = []

        if method == SPECIFIC_ID:
            ids = list(specific_lot_ids or [])
            if len(ids) != len(set(ids)):
                raise ValueError("specific_lot_ids must not contain duplicates")
            by_id = {l.lot_id: l for l in self.lots}
            missing = [i for i in ids if i not in by_id]
            if missing:
                raise KeyError("unknown lot id(s): %s" % ", ".join(missing))
            queue = [by_id[i] for i in ids]
        else:
            queue = self._ordered_lots(method)

        # Distribute total cent-exact proceeds over matched shares.
        # Per-lot proceeds are rounded ONCE from the exact proportional
        # split of the cent total; the last matched lot absorbs any
        # residual so allocated proceeds sum exactly to the total.
        matched_plan: List[Tuple[Lot, float]] = []
        for lot in queue:
            if remaining <= 1e-12:
                break
            take = min(remaining, lot.shares)
            if take <= 1e-12:
                continue
            matched_plan.append((lot, take))
            remaining -= take
        if remaining > 1e-12:
            raise ValueError(
                "insufficient shares: short by %.6f" % remaining
            )

        total_matched_shares = sum(t for _, t in matched_plan)
        allocated = 0
        # Compute against a local lot list so a later invalid input cannot
        # leave a partially applied sale in the caller's portfolio.
        updated_lots = list(self.lots)
        for idx, (lot, take) in enumerate(matched_plan):
            if idx == len(matched_plan) - 1:
                lot_proceeds = proceeds_total - allocated  # true-up: exact total
            else:
                lot_proceeds = _round_cents(
                    proceeds_total * (take / total_matched_shares)
                )
                allocated += lot_proceeds
            lot_cost = _round_cents(take * lot.cost_per_share_cents)
            holding = sale_day - lot.acquire_day
            loss = lot_proceeds - lot_cost < 0
            flagged = False
            if loss and self._wash_sale_buys_near(sale_day, wash_sale_window_days):
                flagged = True
            results.append(
                SaleResult(
                    lot_id=lot.lot_id,
                    shares_sold=take,
                    proceeds_cents=lot_proceeds,
                    cost_basis_cents=lot_cost,
                    gain_cents=lot_proceeds - lot_cost,
                    holding_days=holding,
                    long_term=holding >= lt_threshold_days,
                    wash_sale_flagged=flagged,
                )
            )
            # Reduce / remove the consumed portion of the lot.
            if abs(take - lot.shares) <= 1e-12:
                updated_lots.remove(lot)
            else:
                updated_lots[updated_lots.index(lot)] = Lot(
                    lot_id=lot.lot_id,
                    acquire_date=lot.acquire_date,
                    shares=round(lot.shares - take, 10),
                    cost_per_share_cents=lot.cost_per_share_cents,
                    acquire_day=lot.acquire_day,
                )
        self.lots[:] = updated_lots
        self.history.append(("sell", sale_day, shares))
        return results

    def _wash_sale_buys_near(self, sale_day: int, window_days: int) -> bool:
        """True if any BUY occurred within [sale_day-window, sale_day+window].

        FLAG ONLY: this intentionally ignores same-day replacement rules,
        substantially-identical-security nuance, and loss adjustments.
        Enforcement is out of scope by design.
        """
        lo, hi = sale_day - window_days, sale_day + window_days
        return any(
            kind == "buy" and lo <= day <= hi for (kind, day, _) in self.history
        )


def realized_gain_summary(results: Iterable[SaleResult]) -> Dict[str, int]:
    """Aggregate SaleResults into cent-exact totals."""
    total_gain = 0
    stcg = 0
    ltcg = 0
    for r in results:
        total_gain += r.gain_cents
        if r.long_term:
            ltcg += r.gain_cents
        else:
            stcg += r.gain_cents
    return {
        "total_gain_cents": total_gain,
        "short_term_gain_cents": stcg,
        "long_term_gain_cents": ltcg,
        "wash_sale_flags": 0,  # replaced below; kept explicit
    }


def summarize_sales(results: Iterable[SaleResult]) -> Dict[str, int]:
    """Cent-exact aggregate incl. wash-sale flag count."""
    agg = realized_gain_summary(results)
    agg["wash_sale_flags"] = sum(1 for r in results if r.wash_sale_flagged)
    return agg


# ---------------------------------------------------------------------------
# After-tax return of a lot sequence
# ---------------------------------------------------------------------------


def after_tax_lot_return(
    results: Sequence[SaleResult],
    stcg_rate: float,   # PARAMETER: e.g. ordinary income rate for STCG (tax year N)
    ltcg_rate: float,   # PARAMETER: e.g. qualified LTCG rate for tax year N
) -> Dict[str, float]:
    """After-tax proceeds and after-tax gain for a set of sales.

    Rates are caller-supplied parameters -- this module encodes NO tax law.
    Losses offset gains within their own term bucket first, then across
    buckets (simple netting; carryover is out of scope).
    """
    st_net = sum(r.gain_cents for r in results if not r.long_term)
    lt_net = sum(r.gain_cents for r in results if r.long_term)

    # Cross-bucket netting: losses in one bucket reduce gains in the other.
    if st_net < 0 and lt_net > 0:
        applied = min(-st_net, lt_net)
        lt_net -= applied
        st_net += applied
    elif lt_net < 0 and st_net > 0:
        applied = min(-lt_net, st_net)
        st_net -= applied
        lt_net += applied

    tax_cents = 0.0
    if st_net > 0:
        tax_cents += st_net * stcg_rate
    if lt_net > 0:
        tax_cents += lt_net * ltcg_rate

    gross_proceeds_cents = sum(r.proceeds_cents for r in results)
    total_basis_cents = sum(r.cost_basis_cents for r in results)
    tax_rounded = _round_cents(tax_cents)
    after_tax_gain_cents = (
        gross_proceeds_cents - tax_rounded - total_basis_cents
    )
    gross_gain_cents = gross_proceeds_cents - total_basis_cents
    return {
        "gross_proceeds": from_cents(gross_proceeds_cents),
        "tax_owed": from_cents(tax_rounded),
        "after_tax_proceeds": from_cents(gross_proceeds_cents - tax_rounded),
        "after_tax_gain": from_cents(after_tax_gain_cents),
        "after_tax_return_pct": (
            100.0 * after_tax_gain_cents / total_basis_cents
            if total_basis_cents else 0.0
        ),
        "gross_gain": from_cents(gross_gain_cents),
    }


# ---------------------------------------------------------------------------
# Goal funding probability (seeded Monte Carlo, normal returns)
# ---------------------------------------------------------------------------


def goal_funding_probability(
    current_balance: float,
    annual_contribution: float,
    years: int,
    mu: float,
    sigma: float,
    goal_amount: float,
    seed: int,
    simulations: int = 10000,
) -> Dict[str, object]:
    """Monte Carlo probability that a portfolio reaches `goal_amount`.

    Deterministic: `random.Random(seed)` with fixed draw order gives
    IDENTICAL results for identical inputs, every run. Returns mean and
    percentile terminal balances too.
    """
    if years <= 0 or simulations <= 0:
        raise ValueError("years and simulations must be positive")
    rng = random.Random(seed)
    successes = 0
    finals: List[float] = []
    for _ in range(simulations):
        balance = current_balance
        for _y in range(years):
            ret = rng.gauss(mu, sigma)
            balance = balance * (1.0 + ret) + annual_contribution
            if balance < 0.0:
                balance = 0.0
        finals.append(balance)
        if balance >= goal_amount:
            successes += 1
    finals.sort()
    def pct(p: float) -> float:
        i = min(int(p * (simulations - 1)), simulations - 1)
        return finals[i]
    return {
        "probability": successes / simulations,
        "mean_final": sum(finals) / simulations,
        "median_final": pct(0.50),
        "p10_final": pct(0.10),
        "p90_final": pct(0.90),
        "seed": seed,
        "simulations": simulations,
    }


# ---------------------------------------------------------------------------
# Retirement withdrawal sequencing
# ---------------------------------------------------------------------------

DEFAULT_WITHDRAWAL_ORDER = ["taxable", "traditional", "roth"]


def retirement_withdrawals(
    balances: Dict[str, float],
    annual_need: float,
    years: int,
    order: Optional[Sequence[str]] = None,
    growth_rate: float = 0.0,
) -> Dict[str, object]:
    """Sequence withdrawals across accounts in `order`.

    Default order: taxable -> traditional -> roth (parameterizable).
    Growth is applied AFTER each year's withdrawal. Shortfalls (all
    accounts exhausted) are reported, not raised.
    """
    seq = list(order) if order is not None else list(DEFAULT_WITHDRAWAL_ORDER)
    accts = {k: float(v) for k, v in balances.items()}
    unknown = [a for a in seq if a not in accts]
    if unknown:
        raise ValueError("unknown accounts in order: %s" % ", ".join(unknown))

    withdrawn_by_acct = {a: 0.0 for a in seq}
    timeline: List[Dict[str, float]] = []
    shortfall_total = 0.0
    for _y in range(years):
        need = annual_need
        year_detail: Dict[str, float] = {}
        for acct in seq:
            take = min(need, max(accts[acct], 0.0))
            accts[acct] -= take
            need -= take
            withdrawn_by_acct[acct] += take
            year_detail[acct + "_withdrawn"] = round(take, 2)
        shortfall_total += need
        year_detail["shortfall"] = round(need, 2)
        for acct in seq:
            accts[acct] *= 1.0 + growth_rate
        timeline.append(year_detail)

    return {
        "ending_balances": {a: round(accts[a], 2) for a in seq},
        "total_withdrawn_by_account": {
            a: round(withdrawn_by_acct[a], 2) for a in seq
        },
        "total_shortfall": round(shortfall_total, 2),
        "timeline": timeline,
    }


# ---------------------------------------------------------------------------
# Emergency-months coverage
# ---------------------------------------------------------------------------


def emergency_months_coverage(
    liquid_assets: float, monthly_expenses: float
) -> Dict[str, float]:
    """How many months of expenses the liquid cushion covers."""
    if monthly_expenses <= 0:
        raise ValueError("monthly_expenses must be positive")
    months = liquid_assets / monthly_expenses
    if months < 3.0:
        band = "thin"
    elif months < 6.0:
        band = "adequate"
    else:
        band = "strong"
    return {"months": months, "band": band}


# ---------------------------------------------------------------------------
# Selftest
# ---------------------------------------------------------------------------


def _selftest() -> int:
    failures: List[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        if not cond:
            failures.append("%s %s" % (name, detail))
        print("[%s] %s%s" % ("PASS" if cond else "FAIL", name, (" :: " + detail) if detail else ""))

    # --- 1. Determinism: two identical Monte Carlo runs must match exactly.
    a = goal_funding_probability(50000.0, 6000.0, 20, 0.06, 0.15, 250000.0, seed=42)
    b = goal_funding_probability(50000.0, 6000.0, 20, 0.06, 0.15, 250000.0, seed=42)
    check(
        "determinism-two-runs",
        a == b and repr(a) == repr(b),
        "prob=%r" % a["probability"],
    )

    # --- 2. FIFO realization, cent-exact.
    pf = Portfolio()
    pf.add_lot(Lot("L1", "2024-01-02", 10.0, 10000, acquire_day=1))   # $100.00/sh
    pf.add_lot(Lot("L2", "2024-03-01", 10.0, 12000, acquire_day=60))  # $120.00/sh
    res = pf.sell(15.0, 130.0, 400, "2025-02-04", method=FIFO)
    # L1 fully sold: proceeds 10*130=1300.00 -> 130000c, basis 100000c, +30000c
    # L2 partial:   proceeds  5*130= 650.00 ->  65000c, basis  60000c, + 5000c
    check("fifo-total-gain", sum(r.gain_cents for r in res) == 35000,
          "got %d" % sum(r.gain_cents for r in res))
    check("fifo-first-match", res[0].lot_id == "L1" and res[0].shares_sold == 10.0)

    # --- 3. Specific-ID OUT-OF-ORDER selection (caller picks L2 first).
    pf2 = Portfolio()
    pf2.add_lot(Lot("A", "2024-01-02", 5.0, 8000, acquire_day=1))    # LT by sale
    pf2.add_lot(Lot("B", "2024-06-01", 5.0, 9000, acquire_day=150))  # ST by sale
    res2 = pf2.sell(5.0, 110.0, 500, "2025-05-15",
                    method=SPECIFIC_ID, specific_lot_ids=["B", "A"])
    # Only B should be touched (5 shares covers it), despite A being older.
    check("specid-out-of-order", len(res2) == 1 and res2[0].lot_id == "B",
          "matched=%s" % [r.lot_id for r in res2])
    check("specid-gain", res2[0].gain_cents == 5 * 11000 - 5 * 9000 == 10000,
          "gain=%d" % res2[0].gain_cents)
    # And an explicit multi-lot out-of-order pull across both.
    pf3 = Portfolio()
    pf3.add_lot(Lot("X", "2024-01-02", 3.0, 7000, acquire_day=1))
    pf3.add_lot(Lot("Y", "2024-02-01", 3.0, 7500, acquire_day=31))
    res3 = pf3.sell(6.0, 80.0, 500, "2025-05-15",
                    method=SPECIFIC_ID, specific_lot_ids=["Y", "X"])
    check("specid-multi-order", [r.lot_id for r in res3] == ["Y", "X"],
          "order=%s" % [r.lot_id for r in res3])

    # --- 4. Wash-sale FLAGGING (flag present, nothing enforced/adjusted).
    pfw = Portfolio()
    pfw.add_lot(Lot("W1", "2024-01-02", 10.0, 20000, acquire_day=1))   # $200/sh
    # A replacement buy 15 days before the loss sale (within the window).
    pfw.history.append(("buy", 25, 1.0))
    resw = pfw.sell(10.0, 180.0, 40, "2024-02-10")  # loss: 1800 vs 2000
    check("wash-sale-flagged", len(resw) == 1 and resw[0].wash_sale_flagged,
          "flagged=%s" % [r.wash_sale_flagged for r in resw])
    check("wash-sale-no-adjustment",
          resw[0].gain_cents == 180000 - 200000 == -20000,
          "loss preserved=%d" % resw[0].gain_cents)
    # Control: same loss but NO nearby buy -> not flagged.
    pfc = Portfolio()
    pfc.add_lot(Lot("C1", "2024-01-02", 10.0, 20000, acquire_day=1))
    resc = pfc.sell(10.0, 180.0, 400, "2025-02-04")
    check("wash-sale-not-flagged-far-buy",
          len(resc) == 1 and not resc[0].wash_sale_flagged)

    # --- 5. After-tax return with rates as PARAMETERS (no law hardcoded).
    summ = summarize_sales(res)
    at = after_tax_lot_return(res, stcg_rate=0.32, ltcg_rate=0.15)  # example params
    expect_lt_tax = 30000 * 0.15
    expect_st_tax = 5000 * 0.32
    expect_atp = 195000 - (expect_lt_tax + expect_st_tax)
    check("after-tax-math",
          abs(at["after_tax_proceeds"] - expect_atp / 100.0) < 1e-9,
          "atp=%.4f expect=%.4f" % (at["after_tax_proceeds"], expect_atp / 100.0))
    check("summary-cent-exact", summ["total_gain_cents"] == 35000)

    # --- 6. Withdrawal sequencing default order + custom order.
    w = retirement_withdrawals(
        {"taxable": 40000.0, "traditional": 50000.0, "roth": 30000.0},
        annual_need=45000.0, years=2, growth_rate=0.0)
    t0 = w["timeline"][0]
    check("withdraw-default-order",
          abs(t0["taxable_withdrawn"] - 40000.0) < 1e-9
          and abs(t0["traditional_withdrawn"] - 5000.0) < 1e-9
          and t0["roth_withdrawn"] == 0.0)
    wc = retirement_withdrawals(
        {"taxable": 10000.0, "traditional": 50000.0, "roth": 30000.0},
        annual_need=30000.0, years=1,
        order=["roth", "taxable", "traditional"])
    tc = wc["timeline"][0]
    check("withdraw-custom-order",
          abs(tc["roth_withdrawn"] - 30000.0) < 1e-9
          and tc["taxable_withdrawn"] == 0.0)

    # --- 7. Emergency months.
    em = emergency_months_coverage(21000.0, 3500.0)
    check("emergency-months", abs(em["months"] - 6.0) < 1e-9 and em["band"] == "strong")

    print("")
    if failures:
        print("SELFTEST FAILED (%d):" % len(failures))
        for f in failures:
            print("  - " + f)
        return 1
    print("ALL SELFTESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())

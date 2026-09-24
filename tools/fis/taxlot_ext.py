#!/usr/bin/env python3
"""Tax-lot EXTENSIONS built ON TOP OF calcs_household (imported, never forked).

Part V additions over calcs_household.Portfolio:

  * tax_loss_harvest_candidates -- rank open lots by unrealized loss
    size (cent-exact), each carrying a wash-sale WINDOW flag computed
    from the portfolio's own buy history (+/- window days around the
    hypothetical harvest day).
  * wash_sale_report -- aggregate wash-sale flags from SaleResults and
    EXPLICITLY list UNKNOWN cross-account exposures (spouse accounts,
    IRAs holding substantially identical securities, external
    accounts) as UNRESOLVED caveats.  This module's wash-sale output
    is NEVER definitive; it flags single-account evidence only.
  * charitable_lot_candidates -- highest-basis LONG-TERM open lots,
    best-first for appreciated-securities donation planning.
  * rebalancing_tax_cost -- projected tax cost of a trade list using
    lot selection (highest-basis-first SPECIFIC_ID on a SCRATCH copy;
    caller portfolios are never mutated).
  * asset_location -- ADVISORY asset-class -> account-type placement
    map.  Labeled ADVISORY-NOT-TAX-ADVICE on every record.

Rule versioning: every record carries `rule_version`
(US-FED-IRC-1091-FLAGONLY-v1).  The "FLAGONLY" marker means wash-sale
logic FLAGS only -- nothing is adjusted, blocked, or enforced.

Money policy: lot-level math stays CENT-EXACT integer cents (inherited
policy); estimated taxes are floats and are estimates only.

Tax law is NOT encoded beyond the flagging scope named in the rule
version.  Rates are always caller-supplied parameters.

Stdlib only. ASCII only. No network access.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

# Import -- do NOT fork -- the household engine.
from calcs_household import (
    FIFO,
    LIFO,
    SPECIFIC_ID,
    Lot,
    Portfolio,
    SaleResult,
    _round_cents,
    after_tax_lot_return,
    to_cents,
)

RULE_VERSION = "US-FED-IRC-1091-FLAGONLY-v1"

ADVISORY_LABEL = "ADVISORY-NOT-TAX-ADVICE"

DEFAULT_WASH_WINDOW_DAYS = 30
DEFAULT_LT_THRESHOLD_DAYS = 366

# Verbatim unresolved caveats.  These exact strings must appear in every
# wash_sale_report output; tests match them verbatim.
CAVEAT_SPOUSE_ACCOUNTS = (
    "UNKNOWN CROSS-ACCOUNT EXPOSURE: spouse accounts were NOT examined; "
    "a substantially identical purchase there inside the window could "
    "trigger wash-sale treatment this report cannot see."
)
CAVEAT_IRA_ACCOUNTS = (
    "UNKNOWN CROSS-ACCOUNT EXPOSURE: IRAs holding substantially identical "
    "securities were NOT examined; loss disallowance from such purchases "
    "cannot be detected in this dataset."
)
CAVEAT_EXTERNAL_ACCOUNTS = (
    "UNKNOWN CROSS-ACCOUNT EXPOSURE: external brokerage or other accounts "
    "outside this dataset were NOT examined; this report is NEVER "
    "definitive on wash-sale status."
)
UNRESOLVED_CROSS_ACCOUNT_CAVEATS: List[str] = [
    CAVEAT_SPOUSE_ACCOUNTS,
    CAVEAT_IRA_ACCOUNTS,
    CAVEAT_EXTERNAL_ACCOUNTS,
]


# ---------------------------------------------------------------------------
# Price availability (W3 HIGH: TAX-MISSING-PRICE-TYPED-ERROR)
#
# The previous code did `if lot.lot_id not in prices: continue` with a
# comment claiming the gap was "reported via coverage". No coverage field
# existed anywhere in this module -- the skip was entirely silent. A lot
# with no mark vanished from the candidate list, so a harvesting
# recommendation looked complete while quietly ignoring positions it could
# not value. An unpriced lot is not a lot with no loss; it is a lot whose
# loss is UNKNOWN.
#
# Policy now:
#   * a required price that is missing, stale, zero, NaN, infinite,
#     negative, or otherwise unusable produces a typed PriceGap;
#   * the analysis is marked INCOMPLETE and any recommendation that would
#     depend on the unpriced lot is REFUSED, not quietly shrunken;
#   * an explicit user estimate is permitted ONLY through the separately
#     labelled estimate path, and is stamped as an estimate with reduced
#     confidence -- never silently substituted for a real mark.
# ---------------------------------------------------------------------------

# Why a price could not be used.
GAP_MISSING = "MISSING_PRICE"
GAP_MISSING_HISTORICAL = "MISSING_HISTORICAL_ACQUISITION_PRICE"
GAP_MISSING_FX = "MISSING_FX_RATE"
GAP_STALE = "STALE_PRICE"
GAP_ZERO = "ZERO_PRICE"
GAP_NAN = "NON_FINITE_PRICE"
GAP_NEGATIVE = "NEGATIVE_PRICE"
GAP_CORPORATE_ACTION = "CORPORATE_ACTION_DISCONTINUITY"
GAP_DELISTED = "DELISTED_INSTRUMENT"
GAP_PARTIAL_COVERAGE = "PARTIAL_ACCOUNT_COVERAGE"

GAP_CODES = (
    GAP_MISSING, GAP_MISSING_HISTORICAL, GAP_MISSING_FX, GAP_STALE,
    GAP_ZERO, GAP_NAN, GAP_NEGATIVE, GAP_CORPORATE_ACTION,
    GAP_DELISTED, GAP_PARTIAL_COVERAGE,
)

# Price types the analysis may require.
PT_CURRENT_MARK = "current_mark"
PT_HISTORICAL_ACQUISITION = "historical_acquisition"
PT_FX_RATE = "fx_rate"

STALE_SLA_DAYS = 5


@dataclass
class PriceQuote:
    """A price observation plus everything needed to judge its fitness.

    `price` may be a float, a PriceQuote, or None. A bare float is accepted
    for backwards compatibility but carries NO provenance, so its
    confidence is UNKNOWN and freshness cannot be established.
    """

    price: Optional[float] = None
    as_of: Optional[str] = None            # ISO date of the observation
    availability_ts: Optional[str] = None  # when it became observable (UTC Z)
    source: str = "unspecified"
    price_type: str = PT_CURRENT_MARK
    is_estimate: bool = False
    corporate_action_pending: bool = False
    delisted: bool = False
    license_status: str = "unverified"

    def provenance(self) -> str:
        if self.is_estimate:
            return "USER_ESTIMATE"
        if self.as_of is None and self.availability_ts is None:
            return "UNPROVENANCED"
        return "OBSERVED"


class MissingPriceError(ValueError):
    """Raised when a price required by the analysis is not usable.

    Carries the structured gap so callers can propagate it into portfolio,
    tax, risk, decision and UI surfaces instead of discarding the
    instrument and reporting a silently reduced result.

    Accepts a single PriceGap or a sequence of them; `.gaps` always carries
    the full set so no gap is lost to exception handling.
    """

    def __init__(self, gaps):
        if isinstance(gaps, PriceGap):
            gaps = [gaps]
        self.gaps = list(gaps)
        self.gap = self.gaps[0] if self.gaps else None
        head = self.gap.message() if self.gap else "unknown price gap"
        if len(self.gaps) > 1:
            head += " (and %d more)" % (len(self.gaps) - 1)
        super().__init__(head)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "error": "MissingPriceError",
            "gap_count": len(self.gaps),
            "gaps": [g.as_dict() for g in self.gaps],
            "severity": "HIGH",
            "blocks_recommendation": True,
            "advisory": ADVISORY_LABEL,
        }


@dataclass
class PriceGap:
    """A price that could not be used, and exactly why."""

    code: str
    lot_id: str
    instrument: str
    account: str
    price_type: str
    required_as_of: Optional[str] = None
    observed_as_of: Optional[str] = None
    staleness_days: Optional[int] = None
    source: str = "unspecified"
    detail: str = ""

    def message(self) -> str:
        return ("%s: cannot price lot %s (instrument=%s account=%s) "
                "price_type=%s required_as_of=%s -- %s"
                % (self.code, self.lot_id, self.instrument, self.account,
                   self.price_type, self.required_as_of, self.detail))

    def as_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "lot_id": self.lot_id,
            "instrument": self.instrument,
            "account": self.account,
            "price_type": self.price_type,
            "required_as_of": self.required_as_of,
            "observed_as_of": self.observed_as_of,
            "staleness_days": self.staleness_days,
            "source": self.source,
            "detail": self.detail,
            "severity": "HIGH",
            "blocks_recommendation": True,
        }


def _split_lot_id(lot_id: str) -> Tuple[str, str]:
    """Recover (account, instrument) from a structured lot id.

    Fixture lot ids are 'account|SYMBOL|Lnnn'. Unstructured ids are
    reported verbatim as the instrument with account UNKNOWN, so the gap
    still names what could not be priced rather than hiding it.
    """
    parts = str(lot_id).split("|")
    if len(parts) >= 3:
        return parts[0], parts[1]
    if len(parts) == 2:
        return parts[0], parts[1]
    return "UNKNOWN-ACCOUNT", str(lot_id)


def _coerce_quote(value: Any, price_type: str = PT_CURRENT_MARK) -> PriceQuote:
    """Accept a PriceQuote, a bare float, or None. Never fabricate a mark."""
    if isinstance(value, PriceQuote):
        return value
    if value is None:
        return PriceQuote(price=None, price_type=price_type)
    return PriceQuote(price=float(value), price_type=price_type,
                      source="bare-float-unprovenanced")


def _quote_disclosure(value: Any, required_as_of: Optional[str] = None) -> Dict[str, Any]:
    """Separate usable arithmetic from a mark fit to support a recommendation.

    License status is caller-supplied source metadata, not an independently
    verified license. Observation timing alone never implies a license.
    """
    q = _coerce_quote(value)
    licensed = q.license_status in ("verified-open", "licensed")
    observed = q.provenance() == "OBSERVED"
    sourced = bool(q.source and q.source not in (
        "unspecified", "bare-float-unprovenanced"))
    dated = _days_between_iso(q.as_of, q.as_of) == 0
    age = _days_between_iso(q.as_of, required_as_of)
    current = age is not None and 0 <= age <= STALE_SLA_DAYS
    return {
        "price_source": q.source, "price_as_of": q.as_of,
        "license_status": q.license_status,
        "license_status_authority": "caller-supplied-metadata",
        "price_recommendation_eligible": licensed and observed and sourced and dated and current,
    }


def _days_between_iso(a: Optional[str], b: Optional[str]) -> Optional[int]:
    if not a or not b:
        return None
    try:
        da = date.fromisoformat(str(a)[:10])
        db = date.fromisoformat(str(b)[:10])
    except ValueError:
        return None
    return (db - da).days


def resolve_lot_price(
    lot: Lot,
    raw: Any,
    required_as_of: Optional[str] = None,
    price_type: str = PT_CURRENT_MARK,
    allow_estimate: bool = False,
) -> Tuple[int, Optional[PriceGap], str, str]:
    """Resolve one lot's price to integer cents, or explain why it cannot be.

    Returns (price_cents, gap, provenance, confidence).
    price_cents and gap are never both meaningful: a usable price yields
    gap=None, an unusable one yields a gap and price_cents=0.
    """
    account, instrument = _split_lot_id(lot.lot_id)
    q = _coerce_quote(raw, price_type)
    provenance = q.provenance()
    confidence = "UNKNOWN" if provenance == "UNPROVENANCED" else (
        "LOW" if provenance == "USER_ESTIMATE" else "MEDIUM")

    def gap(code: str, detail: str) -> PriceGap:
        return PriceGap(
            code=code, lot_id=lot.lot_id, instrument=instrument,
            account=account, price_type=price_type,
            required_as_of=required_as_of, observed_as_of=q.as_of,
            staleness_days=_days_between_iso(q.as_of, required_as_of),
            source=q.source, detail=detail)

    # An estimate is the ONLY permitted substitute, and only when the
    # caller has explicitly opened the estimate path.
    if q.is_estimate and not allow_estimate:
        return 0, gap(GAP_MISSING,
                      "an estimate was supplied but the estimate path is "
                      "not open for this analysis"), provenance, confidence

    if q.delisted:
        return 0, gap(GAP_DELISTED,
                      "instrument is delisted; no current mark exists and "
                      "none may be inferred"), provenance, confidence
    if q.corporate_action_pending:
        return 0, gap(GAP_CORPORATE_ACTION,
                      "a corporate action makes the price series "
                      "discontinuous; the prior mark cannot be carried "
                      "across without an adjustment"), provenance, confidence
    if q.price is None:
        code = {PT_HISTORICAL_ACQUISITION: GAP_MISSING_HISTORICAL,
                PT_FX_RATE: GAP_MISSING_FX}.get(price_type, GAP_MISSING)
        return 0, gap(code, "no price supplied"), provenance, confidence

    try:
        px = float(q.price)
    except (TypeError, ValueError):
        return 0, gap(GAP_NAN, "price is not numeric: %r" % (q.price,)), \
            provenance, confidence
    if math.isnan(px) or math.isinf(px):
        return 0, gap(GAP_NAN, "price is NaN or infinite (%r)" % (px,)), \
            provenance, confidence
    if px == 0.0:
        # A zero price is NOT a mark. Substituting it silently would value
        # the position at nothing and manufacture a spurious full loss.
        return 0, gap(GAP_ZERO,
                      "price is exactly 0.00 -- a zero price is not a "
                      "market mark and must not be substituted"), \
            provenance, confidence
    if px < 0.0:
        return 0, gap(GAP_NEGATIVE, "price is negative (%r)" % (px,)), \
            provenance, confidence

    age = _days_between_iso(q.as_of, required_as_of)
    if age is not None and age > STALE_SLA_DAYS:
        return 0, gap(GAP_STALE,
                      "observation as_of %s is %d days older than the "
                      "required date %s (SLA %d days)"
                      % (q.as_of, age, required_as_of, STALE_SLA_DAYS)), \
            provenance, confidence

    if q.is_estimate:
        confidence = "LOW"
    return _round_cents(px * 100.0), None, provenance, confidence


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _latest_history_day(portfolio: Portfolio) -> int:
    """Largest day seen in the portfolio history (0 if empty)."""
    return max((day for (_k, day, _s) in portfolio.history), default=0)


def _window_buys(
    portfolio: Portfolio, center_day: int, window_days: int
) -> List[Dict[str, Any]]:
    """Buys in known history within +/- window_days of center_day."""
    lo, hi = center_day - window_days, center_day + window_days
    hits: List[Dict[str, Any]] = []
    for (kind, day, shares) in portfolio.history:
        if kind == "buy" and lo <= day <= hi:
            hits.append({"day": day, "shares": shares})
    hits.sort(key=lambda h: h["day"])
    return hits


def _scratch_copy(portfolio: Portfolio) -> Portfolio:
    """Deep-enough copy so lot-selection math never mutates the caller."""
    scratch = Portfolio()
    for lot in portfolio.lots:
        scratch.lots.append(
            Lot(
                lot_id=lot.lot_id,
                acquire_date=lot.acquire_date,
                shares=lot.shares,
                cost_per_share_cents=lot.cost_per_share_cents,
                acquire_day=lot.acquire_day,
            )
        )
    scratch.history = list(portfolio.history)
    return scratch


# ---------------------------------------------------------------------------
# Tax-loss harvest candidates
# ---------------------------------------------------------------------------


def tax_loss_harvest_candidates(
    portfolio: Portfolio,
    prices: Dict[str, Any],
    min_loss_cents: int,
    as_of_day: Optional[int] = None,
    window_days: int = DEFAULT_WASH_WINDOW_DAYS,
    lt_threshold_days: int = DEFAULT_LT_THRESHOLD_DAYS,
    strict: bool = True,
    allow_estimate: bool = False,
    required_as_of: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Rank open lots by unrealized loss (largest first). FAIL-CLOSED.

    `prices` maps LOT ID -> current price per share in DOLLARS, OR to a
    `PriceQuote` carrying as_of / source / provenance. A lot is a
    candidate when its unrealized loss is >= min_loss_cents (cent-exact).

    PRICE POLICY (W3 HIGH -- TAX-MISSING-PRICE-TYPED-ERROR).
    The previous implementation did `if lot.lot_id not in prices: continue`
    with a comment claiming the gap was "reported via coverage". No such
    coverage field existed anywhere in this module, so the skip was
    entirely silent: an unpriced lot vanished from the ranking and the
    recommendation looked complete while ignoring positions it could not
    value. An unpriced lot is NOT a lot with no loss; it is a lot whose
    loss is UNKNOWN, and a ranking that omits it is not a ranking.

    Now every open lot must resolve to a usable price:
      * missing / stale / zero / NaN / infinite / negative / delisted /
        corporate-action-discontinuous prices each yield a typed PriceGap;
      * with strict=True (the DEFAULT) any gap raises MissingPriceError
        carrying the FULL gap set -- the analysis refuses rather than
        quietly shrinking;
      * strict=False returns only the priced subset and is intended for
        callers that use `tax_loss_harvest_analysis()`, which surfaces the
        gaps and marks the result INCOMPLETE. A caller that wants the old
        silent behaviour no longer has a way to ask for it.

    `allow_estimate` opens the explicitly labelled estimate path. An
    estimate is stamped is_estimate / confidence LOW and is reported as
    an estimate everywhere it appears. It is never silently substituted
    for a real mark, and the estimate path is CLOSED by default.

    `required_as_of` is the ISO date the mark must be as of; when
    supplied, an observation older than STALE_SLA_DAYS is a GAP_STALE
    rather than an accepted price.

    Each record carries:

      * unrealized_loss_cents (positive integer)
      * wash_sale_window_flag -- True when KNOWN history shows a buy
        within +/- `window_days` of the hypothetical harvest day
        (`as_of_day`, default: latest history day + 1).
      * wash_sale_window_buys -- the matching buy records.
      * price_provenance / price_confidence / price_is_estimate
      * rule_version

    Future replacement buys CANNOT be known; absence of a flag is not
    clearance.  See wash_sale_report for the cross-account caveats.
    """
    if min_loss_cents < 0:
        raise ValueError("min_loss_cents must be non-negative")
    harvest_day = (
        as_of_day if as_of_day is not None else _latest_history_day(portfolio) + 1
    )
    candidates: List[Dict[str, Any]] = []
    gaps: List[PriceGap] = []
    for lot in portfolio.lots:
        # NOTE: .get, not `in`. A lot absent from `prices` is a GAP, and
        # the whole point of this repair is that a gap is never a skip.
        price_cents, gap, provenance, confidence = resolve_lot_price(
            lot,
            prices.get(lot.lot_id),
            required_as_of=required_as_of,
            price_type=PT_CURRENT_MARK,
            allow_estimate=allow_estimate,
        )
        if gap is not None:
            gaps.append(gap)
            continue
        market_value_cents = _round_cents(lot.shares * price_cents)
        cost_basis_cents = _round_cents(lot.shares * lot.cost_per_share_cents)
        loss_cents = cost_basis_cents - market_value_cents
        if loss_cents < min_loss_cents:
            continue
        holding_days = harvest_day - lot.acquire_day
        buys_near = _window_buys(portfolio, harvest_day, window_days)
        raw = prices.get(lot.lot_id)
        candidates.append(
            {
                "lot_id": lot.lot_id,
                "shares": lot.shares,
                "acquire_date": lot.acquire_date,
                "acquire_day": lot.acquire_day,
                "cost_basis_cents": cost_basis_cents,
                "market_value_cents": market_value_cents,
                "unrealized_loss_cents": loss_cents,
                "holding_days_as_of": holding_days,
                "long_term_at_harvest": holding_days >= lt_threshold_days,
                "hypothetical_harvest_day": harvest_day,
                "wash_sale_window_flag": len(buys_near) > 0,
                "wash_sale_window_buys": buys_near,
                "flag_scope": "single-account-history-only",
                "price_provenance": provenance,
                "price_confidence": confidence,
                "price_is_estimate": bool(
                    isinstance(raw, PriceQuote) and raw.is_estimate),
                "rule_version": RULE_VERSION,
            }
        )
    gaps.extend(_partial_account_gaps(portfolio, prices))
    if gaps and strict:
        raise MissingPriceError(gaps)
    candidates.sort(key=lambda c: -c["unrealized_loss_cents"])
    return candidates


def _partial_account_gaps(
    portfolio: Portfolio,
    prices: Dict[str, Any],
) -> List[PriceGap]:
    """An account with lots but NO usable mark is a coverage gap.

    Per-lot gaps already cover individual misses. This catches the case
    where an entire account is absent from the feed -- which a per-lot
    scan would report as N independent missing prices rather than as one
    systematic coverage failure.
    """
    accounts: Dict[str, List[Lot]] = {}
    for lot in portfolio.lots:
        acct, _sym = _split_lot_id(lot.lot_id)
        accounts.setdefault(acct, []).append(lot)
    gaps: List[PriceGap] = []
    for acct, lots in sorted(accounts.items()):
        priced = 0
        for lot in lots:
            cents, gap, _p, _c = resolve_lot_price(
                lot, prices.get(lot.lot_id), price_type=PT_CURRENT_MARK,
                allow_estimate=True)
            if gap is None:
                priced += 1
        if priced == 0 and lots:
            gaps.append(PriceGap(
                code=GAP_PARTIAL_COVERAGE,
                lot_id="(account-level)",
                instrument="(multiple)",
                account=acct,
                price_type=PT_CURRENT_MARK,
                detail="account has %d open lot(s) and ZERO usable marks; "
                       "the price feed does not cover this account at all"
                       % len(lots)))
    return gaps


def tax_loss_harvest_analysis(
    portfolio: Portfolio,
    prices: Dict[str, Any],
    min_loss_cents: int,
    as_of_day: Optional[int] = None,
    window_days: int = DEFAULT_WASH_WINDOW_DAYS,
    lt_threshold_days: int = DEFAULT_LT_THRESHOLD_DAYS,
    allow_estimate: bool = False,
    required_as_of: Optional[str] = None,
) -> Dict[str, Any]:
    """Envelope form of `tax_loss_harvest_candidates` that never hides a gap.

    Always returns. Never raises for a price gap. The caller is handed an
    explicit `status` (COMPLETE or INCOMPLETE), every individual
    `price_gaps` entry, a `coverage` summary, and a hard
    `recommendation_blocked` flag. This is the surface portfolio / tax /
    risk / decision / UX consumers are meant to read.
    """
    try:
        candidates = tax_loss_harvest_candidates(
            portfolio, prices, min_loss_cents,
            as_of_day=as_of_day, window_days=window_days,
            lt_threshold_days=lt_threshold_days,
            strict=True, allow_estimate=allow_estimate,
            required_as_of=required_as_of)
        gaps: List[PriceGap] = []
    except MissingPriceError as exc:
        candidates = []
        gaps = exc.gaps

    accounts_total = {_split_lot_id(l.lot_id)[0] for l in portfolio.lots}
    gapped_accounts = {g.account for g in gaps}
    return {
        "status": "INCOMPLETE" if gaps else "COMPLETE",
        "recommendation_blocked": bool(gaps),
        "candidates": candidates,
        "candidate_count": len(candidates),
        "price_gaps": [g.as_dict() for g in gaps],
        "gap_count": len(gaps),
        "gap_codes": sorted({g.code for g in gaps}),
        "coverage": {
            "lots_total": len(portfolio.lots),
            "lots_priced": len(portfolio.lots) - len(
                [g for g in gaps if g.lot_id != "(account-level)"]),
            "accounts_total": len(accounts_total),
            "accounts_with_gaps": len(gapped_accounts),
            "accounts_missing": sorted(gapped_accounts),
            "coverage_complete": not gaps,
        },
        "estimate_path_open": bool(allow_estimate),
        "estimated_count": sum(
            1 for c in candidates if c.get("price_is_estimate")),
        "severity": "HIGH" if gaps else "NONE",
        "advisory": ADVISORY_LABEL,
        "rule_version": RULE_VERSION,
    }


# ---------------------------------------------------------------------------
# Wash-sale report (never definitive)
# ---------------------------------------------------------------------------


def wash_sale_report(
    results: Sequence[SaleResult],
    window_days: int = DEFAULT_WASH_WINDOW_DAYS,
) -> Dict[str, Any]:
    """Report wash-sale FLAGS with explicit unresolved caveats.

    Single-account flags come from SaleResult.wash_sale_flagged (the
    inherited FLAGONLY behavior).  Cross-account exposure (spouse
    accounts, IRAs holding substantially identical securities,
    external accounts) is UNKNOWN by construction and is listed as
    UNRESOLVED caveats.  Output is never definitive.
    """
    flagged: List[Dict[str, Any]] = []
    for r in results:
        if r.wash_sale_flagged:
            flagged.append(
                {
                    "lot_id": r.lot_id,
                    "shares_sold": r.shares_sold,
                    "loss_cents": -r.gain_cents if r.gain_cents < 0 else 0,
                    "sale_holding_days": r.holding_days,
                    "status": "FLAGGED-single-account-window",
                    "adjusted": False,
                    "rule_version": RULE_VERSION,
                }
            )
    return {
        "definitive": False,
        "scope": "single-account-history-only",
        "window_days": window_days,
        "flags": flagged,
        "flag_count": len(flagged),
        "adjustments_made": 0,
        "unresolved_cross_account_caveats": list(UNRESOLVED_CROSS_ACCOUNT_CAVEATS),
        "caveat_count": len(UNRESOLVED_CROSS_ACCOUNT_CAVEATS),
        "rule_version": RULE_VERSION,
    }


# ---------------------------------------------------------------------------
# Charitable lot candidates
# ---------------------------------------------------------------------------


def charitable_lot_candidates(
    portfolio: Portfolio,
    as_of_day: Optional[int] = None,
    lt_threshold_days: int = DEFAULT_LT_THRESHOLD_DAYS,
    prices: Optional[Dict[str, Any]] = None,
    strict: bool = True,
    allow_estimate: bool = False,
    required_as_of: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Open LONG-TERM lots ranked best-first for appreciated donation.

    Highest cost basis per share first (donating the most appreciated
    lot gives away the largest embedded gain), ties broken by oldest
    acquire date.  Basis math is cent-exact.

    PRICE POLICY (W3 HIGH). The ranking itself uses only cost basis, so it
    is valid without a mark. The DONATION DEDUCTION, however, is a function
    of fair market value, which does require a mark. When `prices` is
    supplied every surviving lot must resolve to a usable price under the
    same refusal rules as `tax_loss_harvest_candidates`; a gap raises
    MissingPriceError with strict=True (DEFAULT) instead of reporting a
    deduction sized from a missing or zero mark. When `prices` is omitted
    the output is explicitly labelled `fmv_unavailable: True` and carries
    no value figure at all.
    """
    ref_day = (
        as_of_day if as_of_day is not None else _latest_history_day(portfolio) + 1
    )
    rows: List[Dict[str, Any]] = []
    gaps: List[PriceGap] = []
    for lot in portfolio.lots:
        holding_days = ref_day - lot.acquire_day
        if holding_days < lt_threshold_days:
            continue
        fmv_cents = None
        provenance = "NO-FMV-SUPPLIED"
        confidence = "N/A"
        is_estimate = False
        if prices is not None:
            fmv_cents, gap, provenance, confidence = resolve_lot_price(
                lot, prices.get(lot.lot_id),
                required_as_of=required_as_of,
                price_type=PT_CURRENT_MARK,
                allow_estimate=allow_estimate)
            if gap is not None:
                gaps.append(gap)
                continue
            raw = prices.get(lot.lot_id)
            is_estimate = bool(isinstance(raw, PriceQuote) and raw.is_estimate)
        rows.append(
            {
                "lot_id": lot.lot_id,
                "shares": lot.shares,
                "acquire_date": lot.acquire_date,
                "acquire_day": lot.acquire_day,
                "cost_per_share_cents": lot.cost_per_share_cents,
                "total_cost_basis_cents": _round_cents(
                    lot.shares * lot.cost_per_share_cents
                ),
                "fmv_cents": fmv_cents,
                "fmv_unavailable": fmv_cents is None,
                "fmv_provenance": provenance,
                "fmv_confidence": confidence,
                "fmv_is_estimate": is_estimate,
                "holding_days_as_of": holding_days,
                "long_term": True,
                "rank_key": "highest-basis-per-share",
                "rule_version": RULE_VERSION,
            }
        )
    if gaps:
        if strict:
            raise MissingPriceError(gaps)
    rows.sort(key=lambda r: (-r["cost_per_share_cents"], r["acquire_date"]))
    return rows


# ---------------------------------------------------------------------------
# Rebalancing tax cost (lot selection on a scratch copy)
# ---------------------------------------------------------------------------

# Default sell selection: highest basis first minimizes realized gain.
REBALANCE_SELECTION = "HIGHEST_BASIS_FIRST"


def rebalancing_tax_cost(
    trades: Sequence[Dict[str, Any]],
    stcg_rate: float,   # PARAMETER: ordinary-rate assumption for STCG (tax year N)
    ltcg_rate: float,   # PARAMETER: LTCG-rate assumption for tax year N
    lt_threshold_days: int = DEFAULT_LT_THRESHOLD_DAYS,
    strict: bool = True,
    allow_estimate: bool = False,
    required_as_of: Optional[str] = None,
) -> Dict[str, Any]:
    """Projected tax cost of rebalancing sells using lot selection.

    `trades`: list of dicts, one per SELL:
      {"portfolio": Portfolio, "shares": float,
       "price_per_share": float (dollars) OR a PriceQuote,
       "day": int, "date": str}

    Selection runs SPECIFIC_ID highest-basis-per-share-first on a
    SCRATCH copy of each portfolio, so caller state is untouched.
    Rates are caller-supplied parameters (no law hardcoded).

    PRICE POLICY (W3 HIGH). A sell cannot be priced from a mark that does
    not exist. Each trade's price is resolved through `resolve_lot_price`
    semantics: missing, zero, NaN, infinite, negative, stale, delisted and
    corporate-action-discontinuous marks each produce a typed PriceGap, and
    a lot whose acquisition basis is unusable produces
    GAP_MISSING_HISTORICAL. With strict=True (DEFAULT) any gap raises
    MissingPriceError rather than projecting a tax cost from a fabricated
    number -- a zero price here would report a full-loss sale and
    manufacture a large spurious tax benefit.
    """
    per_trade: List[Dict[str, Any]] = []
    all_results: List[SaleResult] = []
    scratch_by_pf: Dict[int, Portfolio] = {}
    gaps: List[PriceGap] = []

    for idx, t in enumerate(trades):
        pf: Portfolio = t["portfolio"]
        key = id(pf)
        if key not in scratch_by_pf:
            scratch_by_pf[key] = _scratch_copy(pf)
        scratch = scratch_by_pf[key]

        # --- price gate -------------------------------------------------
        raw_px = t.get("price_per_share", None)
        tdate = str(t.get("date") or "")
        px_cents, gap, provenance, confidence = _resolve_trade_price(
            raw_px, index=idx, portfolio=pf, trade_date=tdate,
            required_as_of=required_as_of or (tdate or None),
            allow_estimate=allow_estimate)
        if gap is not None:
            gaps.append(gap)
        # --- basis gate: a lot with no usable acquisition price cannot
        # produce a defensible gain, so its basis is a gap too.
        for lot in scratch.lots:
            bgap = _basis_gap(lot, trade_date=tdate, index=idx)
            if bgap is not None:
                gaps.append(bgap)
        if gaps and strict:
            raise MissingPriceError(gaps)
        if gap is not None:
            continue
        price_per_share = px_cents / 100.0
        ordered_ids = [
            lot.lot_id
            for lot in sorted(
                scratch.lots,
                key=lambda l: (-l.cost_per_share_cents, l.acquire_date),
            )
        ]
        results = scratch.sell(
            shares=float(t["shares"]),
            price_per_share=price_per_share,
            sale_day=int(t["day"]),
            sale_date=str(t["date"]),
            method=SPECIFIC_ID,
            specific_lot_ids=ordered_ids[:],
            lt_threshold_days=lt_threshold_days,
        )
        all_results.extend(results)
        selected_lots = sum(1 for _r in results)
        per_trade.append(
            {
                "trade_index": idx,
                "selection_method": REBALANCE_SELECTION,
                "lots_selected": selected_lots,
                "lot_order": [r.lot_id for r in results],
                "proceeds_cents": sum(r.proceeds_cents for r in results),
                "basis_cents": sum(r.cost_basis_cents for r in results),
                "gain_cents": sum(r.gain_cents for r in results),
                "price_provenance": provenance,
                "price_confidence": confidence,
                **_quote_disclosure(raw_px, required_as_of or (tdate or None)),
                "price_is_estimate": bool(
                    isinstance(raw_px, PriceQuote) and raw_px.is_estimate),
                "caller_portfolio_mutated": False,
                "rule_version": RULE_VERSION,
            }
        )

    if gaps and strict:
        raise MissingPriceError(gaps)

    price_disclosures = [_quote_disclosure(t.get("price_per_share"),
                         required_as_of or t.get("date")) for t in trades]
    unverified_prices = any(not d["price_recommendation_eligible"]
                            for d in price_disclosures)
    licenses = sorted({d["license_status"] for d in price_disclosures})
    est = after_tax_lot_return(all_results, stcg_rate=stcg_rate, ltcg_rate=ltcg_rate)
    return {
        "trades": per_trade,
        "selection_method": REBALANCE_SELECTION,
        "realized_gain_cents": sum(r.gain_cents for r in all_results),
        "short_term_gain_cents": sum(
            r.gain_cents for r in all_results if not r.long_term
        ),
        "long_term_gain_cents": sum(r.gain_cents for r in all_results if r.long_term),
        "estimated_tax_owed": est["tax_owed"],
        "estimated_after_tax_proceeds": est["after_tax_proceeds"],
        "estimate_is_not_guaranteed": True,
        "rates_supplied_by_caller": {"stcg_rate": stcg_rate, "ltcg_rate": ltcg_rate},
        "status": "INCOMPLETE" if gaps or unverified_prices else "COMPLETE",
        "recommendation_blocked": bool(gaps) or unverified_prices,
        "price_provenance_complete": not unverified_prices,
        "price_sources": sorted({d["price_source"] for d in price_disclosures}),
        "license_status": licenses[0] if len(licenses) == 1 else "mixed-or-missing",
        "license_status_authority": "caller-supplied-metadata",
        "price_gaps": [g.as_dict() for g in gaps],
        "gap_count": len(gaps),
        "trades_blocked_by_gap": len(trades) - len(per_trade),
        "advisory": ADVISORY_LABEL,
        "rule_version": RULE_VERSION,
    }


def _resolve_trade_price(
    raw_px: Any,
    index: int,
    portfolio: Optional[Portfolio] = None,
    trade_date: str = "",
    required_as_of: Optional[str] = None,
    allow_estimate: bool = False,
) -> Tuple[int, Optional[PriceGap], str, str]:
    """Resolve a rebalancing trade's execution price. Never fabricates.

    Returns (price_cents, gap, provenance, confidence) using exactly the
    same refusal rules as `resolve_lot_price`, so a trade price and a lot
    price cannot disagree about what counts as usable.
    """
    q = _coerce_quote(raw_px, PT_CURRENT_MARK)
    provenance = q.provenance()
    confidence = "UNKNOWN" if provenance == "UNPROVENANCED" else (
        "LOW" if provenance == "USER_ESTIMATE" else "MEDIUM")

    def gap(code: str, detail: str) -> PriceGap:
        return PriceGap(
            code=code,
            lot_id="(trade[%d])" % index,
            instrument=_trade_instrument(portfolio),
            account=_trade_account(portfolio),
            price_type=PT_CURRENT_MARK,
            required_as_of=required_as_of,
            observed_as_of=q.as_of,
            staleness_days=_days_between_iso(q.as_of, required_as_of),
            source=q.source,
            detail=detail)

    if q.is_estimate and not allow_estimate:
        return 0, gap(GAP_MISSING,
                      "an estimate was supplied for trade[%d] but the "
                      "estimate path is closed" % index), provenance, confidence
    if q.delisted:
        return 0, gap(GAP_DELISTED,
                      "delisted instrument; no executable mark exists"), \
            provenance, confidence
    if q.corporate_action_pending:
        return 0, gap(GAP_CORPORATE_ACTION,
                      "corporate action makes the price discontinuous"), \
            provenance, confidence
    if q.price is None:
        return 0, gap({PT_FX_RATE: GAP_MISSING_FX}.get(
            PT_CURRENT_MARK, GAP_MISSING),
            "no execution price supplied for trade[%d]" % index), \
            provenance, confidence
    try:
        px = float(q.price)
    except (TypeError, ValueError):
        return 0, gap(GAP_NAN, "price is not numeric: %r" % (q.price,)), \
            provenance, confidence
    if math.isnan(px) or math.isinf(px):
        return 0, gap(GAP_NAN, "price is NaN or infinite (%r)" % (px,)), \
            provenance, confidence
    if px == 0.0:
        return 0, gap(GAP_ZERO,
                      "execution price is exactly 0.00 for trade[%d]; a zero "
                      "price would report the sale as a total loss and "
                      "manufacture a spurious tax benefit" % index), \
            provenance, confidence
    if px < 0.0:
        return 0, gap(GAP_NEGATIVE, "price is negative (%r)" % (px,)), \
            provenance, confidence
    age = _days_between_iso(q.as_of, required_as_of)
    if age is not None and age > STALE_SLA_DAYS:
        return 0, gap(GAP_STALE,
                      "mark as_of %s is %d days older than the trade date %s "
                      "(SLA %d days)" % (q.as_of, age, required_as_of,
                                         STALE_SLA_DAYS)), \
            provenance, confidence
    if q.is_estimate:
        confidence = "LOW"
    return _round_cents(px * 100.0), None, provenance, confidence


def _trade_instrument(portfolio: Optional[Portfolio]) -> str:
    if portfolio is None or not getattr(portfolio, "lots", None):
        return "UNKNOWN-INSTRUMENT"
    symbols = {_split_lot_id(l.lot_id)[1] for l in portfolio.lots}
    if len(symbols) == 1:
        return next(iter(symbols))
    return "MULTI(%s)" % ",".join(sorted(symbols))


def _trade_account(portfolio: Optional[Portfolio]) -> str:
    if portfolio is None or not getattr(portfolio, "lots", None):
        return "UNKNOWN-ACCOUNT"
    accounts = {_split_lot_id(l.lot_id)[0] for l in portfolio.lots}
    if len(accounts) == 1:
        return next(iter(accounts))
    return "MULTI(%s)" % ",".join(sorted(accounts))


def _basis_gap(
    lot: Lot, trade_date: str = "", index: int = 0
) -> Optional[PriceGap]:
    """A lot whose acquisition basis is unusable cannot yield a real gain.

    Cost basis is the HISTORICAL acquisition price. Without it every
    downstream gain, term split, loss carryforward and estimated tax
    number is indefensible, so it is refused rather than defaulted.
    """
    account, instrument = _split_lot_id(lot.lot_id)
    cents = getattr(lot, "cost_per_share_cents", None)
    if cents is None:
        return PriceGap(
            code=GAP_MISSING_HISTORICAL, lot_id=lot.lot_id,
            instrument=instrument, account=account,
            price_type=PT_HISTORICAL_ACQUISITION,
            required_as_of=str(getattr(lot, "acquire_date", "") or ""),
            detail="lot has no cost_per_share_cents; acquisition price "
                   "unknown so gain cannot be computed")
    try:
        c = float(cents)
    except (TypeError, ValueError):
        return PriceGap(
            code=GAP_NAN, lot_id=lot.lot_id, instrument=instrument,
            account=account, price_type=PT_HISTORICAL_ACQUISITION,
            required_as_of=str(getattr(lot, "acquire_date", "") or ""),
            detail="cost basis is not numeric (%r)" % (cents,))
    if math.isnan(c) or math.isinf(c):
        return PriceGap(
            code=GAP_NAN, lot_id=lot.lot_id, instrument=instrument,
            account=account, price_type=PT_HISTORICAL_ACQUISITION,
            required_as_of=str(getattr(lot, "acquire_date", "") or ""),
            detail="cost basis is NaN or infinite")
    if c < 0.0:
        return PriceGap(
            code=GAP_NEGATIVE, lot_id=lot.lot_id, instrument=instrument,
            account=account, price_type=PT_HISTORICAL_ACQUISITION,
            required_as_of=str(getattr(lot, "acquire_date", "") or ""),
            detail="cost basis is negative (%r)" % (c,))
    # NOTE: a zero acquisition basis is legitimate (received gift / spin-off
    # with no cost) and is therefore NOT refused here, only flagged by the
    # caller. Refusing it would break genuine zero-basis lots.
    return None


# ---------------------------------------------------------------------------
# Asset location (ADVISORY ONLY)
# ---------------------------------------------------------------------------

ASSET_LOCATION_MAP: Dict[str, List[str]] = {
    "taxable_bonds": ["traditional"],
    "municipal_bonds": ["taxable"],
    "reits": ["traditional"],
    "high_growth_equity": ["roth"],
    "broad_index_equity": ["taxable"],
    "international_equity": ["taxable"],
    "commodities_futures_etf": ["traditional"],
    "cash_and_equivalents": ["taxable"],
}


def asset_location() -> Dict[str, Any]:
    """Advisory asset-class -> preferred account-type placement map.

    Every record carries the ADVISORY-NOT-TAX-ADVICE label.  This is
    conventional tax-efficiency guidance, NOT tax advice, and carries
    no guarantee for any taxpayer's situation.
    """
    records: List[Dict[str, Any]] = []
    for asset_class, preferred in ASSET_LOCATION_MAP.items():
        records.append(
            {
                "asset_class": asset_class,
                "preferred_account_types": list(preferred),
                "label": ADVISORY_LABEL,
                "rule_version": RULE_VERSION,
            }
        )
    return {
        "records": records,
        "label": ADVISORY_LABEL,
        "disclaimer": (
            "General placement heuristics only; individual circumstances, "
            "state tax, and account availability change the answer."
        ),
        "rule_version": RULE_VERSION,
    }


# ---------------------------------------------------------------------------
# Selftest
# ---------------------------------------------------------------------------


def _selftest() -> int:
    failures: List[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        if not cond:
            failures.append("%s %s" % (name, detail))
        print(
            "[%s] %s%s"
            % ("PASS" if cond else "FAIL", name, (" :: " + detail) if detail else "")
        )

    # --- 1. Harvest candidate found on a synthetic loss lot.
    pf = Portfolio()
    pf.add_lot(Lot("LOSS1", "2024-01-02", 10.0, 20000, acquire_day=1))   # $200/sh
    pf.add_lot(Lot("GAIN1", "2024-02-01", 10.0, 5000, acquire_day=31))   # $50/sh
    prices = {"LOSS1": 150.0, "GAIN1": 80.0}
    cands = tax_loss_harvest_candidates(pf, prices, min_loss_cents=1)
    check(
        "harvest-candidate-found",
        len(cands) == 1
        and cands[0]["lot_id"] == "LOSS1"
        and cands[0]["unrealized_loss_cents"] == 10 * 20000 - 10 * 15000,
        "cands=%s" % [(c["lot_id"], c["unrealized_loss_cents"]) for c in cands],
    )
    check(
        "harvest-ranked-by-loss",
        all(
            cands[i]["unrealized_loss_cents"] >= cands[i + 1]["unrealized_loss_cents"]
            for i in range(len(cands) - 1)
        ),
    )

    # --- 2. Wash-sale WINDOW: replacement buy +/-30d around harvest day.
    # Harvest day defaults to latest history day + 1 = 101+1 = 102.
    pf2 = Portfolio()
    pf2.add_lot(Lot("W1", "2024-01-02", 10.0, 20000, acquire_day=1))
    pf2.history.append(("buy", 75, 1.0))   # 27 days before day 102 -> INSIDE
    near = tax_loss_harvest_candidates(pf2, {"W1": 150.0}, 1)
    check(
        "wash-window-buy-before-flagged",
        near[0]["wash_sale_window_flag"] is True,
        "buys=%s" % near[0]["wash_sale_window_buys"],
    )
    pf3 = Portfolio()
    pf3.add_lot(Lot("W2", "2024-01-02", 10.0, 20000, acquire_day=1))
    pf3.history.append(("buy", 135, 1.0))  # 33 days after day 102 -> OUTSIDE
    far = tax_loss_harvest_candidates(pf3, {"W2": 150.0}, 1, as_of_day=102)
    check(
        "wash-window-buy-outside-not-flagged",
        far[0]["wash_sale_window_flag"] is False,
        "buys=%s" % far[0]["wash_sale_window_buys"],
    )
    # Default as_of_day = latest KNOWN event + 1: a recent replacement
    # buy therefore lands INSIDE the window when evaluated "now".
    now = tax_loss_harvest_candidates(pf3, {"W2": 150.0}, 1)
    check(
        "wash-window-default-day-sees-recent-replacement-buy",
        now[0]["hypothetical_harvest_day"] == 136
        and now[0]["wash_sale_window_flag"] is True,
    )
    # Boundary: exactly +30d is inside the window.
    pf4 = Portfolio()
    pf4.add_lot(Lot("W3", "2024-01-02", 10.0, 20000, acquire_day=1))
    pf4.history.append(("buy", 132, 1.0))  # exactly 30 after day 102
    edge = tax_loss_harvest_candidates(pf4, {"W3": 150.0}, 1)
    check(
        "wash-window-boundary-plus30-inside",
        edge[0]["wash_sale_window_flag"] is True,
    )

    # --- 3. Wash-sale report contains uncertainty caveats VERBATIM.
    pfw = Portfolio()
    pfw.add_lot(Lot("WS1", "2024-01-02", 10.0, 20000, acquire_day=1))
    pfw.history.append(("buy", 25, 1.0))
    sale_results = pfw.sell(10.0, 180.0, 40, "2024-02-10")
    report = wash_sale_report(sale_results)
    caveats = report["unresolved_cross_account_caveats"]
    check(
        "report-caveats-verbatim-spouse",
        CAVEAT_SPOUSE_ACCOUNTS in caveats,
    )
    check(
        "report-caveats-verbatim-ira",
        CAVEAT_IRA_ACCOUNTS in caveats,
    )
    check(
        "report-caveats-verbatim-external",
        CAVEAT_EXTERNAL_ACCOUNTS in caveats,
    )
    check(
        "report-never-definitive",
        report["definitive"] is False and report["flag_count"] == 1,
        "definitive=%s flags=%d" % (report["definitive"], report["flag_count"]),
    )

    # --- 4. Charitable pick takes the HIGHEST-BASIS long-term lot.
    pfc = Portfolio()
    pfc.add_lot(Lot("LT_LO", "2023-01-02", 10.0, 3000, acquire_day=10))    # $30/sh
    pfc.add_lot(Lot("LT_HI", "2023-03-01", 10.0, 9000, acquire_day=70))    # $90/sh
    pfc.add_lot(Lot("ST_NEW", "2025-07-01", 10.0, 99000, acquire_day=900)) # ST, skip
    char = charitable_lot_candidates(pfc, as_of_day=1000)
    check(
        "charitable-highest-basis-lt-first",
        len(char) == 2
        and char[0]["lot_id"] == "LT_HI"
        and char[0]["cost_per_share_cents"] == 9000,
        "order=%s" % [c["lot_id"] for c in char],
    )

    # --- 5. Rule version present on EVERY record everywhere.
    everywhere_ok = True
    for c in cands:
        everywhere_ok &= c.get("rule_version") == RULE_VERSION
    for c in char:
        everywhere_ok &= c.get("rule_version") == RULE_VERSION
    everywhere_ok &= report.get("rule_version") == RULE_VERSION
    for f in report["flags"]:
        everywhere_ok &= f.get("rule_version") == RULE_VERSION
    loc = asset_location()
    everywhere_ok &= loc.get("rule_version") == RULE_VERSION
    for rec in loc["records"]:
        everywhere_ok &= rec.get("label") == ADVISORY_LABEL
        everywhere_ok &= rec.get("rule_version") == RULE_VERSION
    check("rule-version-on-every-record", bool(everywhere_ok))

    # --- 6. Rebalancing tax cost: highest-basis-first selection on a
    #        scratch copy; caller portfolio NOT mutated; ST vs LT split.
    pfr = Portfolio()
    pfr.add_lot(Lot("R_HI_ST", "2024-06-01", 5.0, 12000, acquire_day=1000))  # hi, ST
    pfr.add_lot(Lot("R_LO_LT", "2023-01-02", 5.0, 4000, acquire_day=10))     # lo, LT
    before = len(pfr.lots)
    trades = [
        {
            "portfolio": pfr,
            "shares": 5.0,
            "price_per_share": 130.0,
            "day": 1100,
            "date": "2026-08-25",
        }
    ]
    rb = rebalancing_tax_cost(trades, stcg_rate=0.32, ltcg_rate=0.15)
    check(
        "rebalance-selects-highest-basis",
        rb["trades"][0]["lot_order"] == ["R_HI_ST"],
        "order=%s" % rb["trades"][0]["lot_order"],
    )
    check(
        "rebalance-short-term-gain",
        rb["short_term_gain_cents"] == 5 * 13000 - 5 * 12000
        and rb["long_term_gain_cents"] == 0,
        "st=%d lt=%d" % (rb["short_term_gain_cents"], rb["long_term_gain_cents"]),
    )
    check(
        "rebalance-no-caller-mutation",
        len(pfr.lots) == before
        and sorted(l.lot_id for l in pfr.lots) == ["R_HI_ST", "R_LO_LT"],
    )

    print("")
    if failures:
        print("SELFTEST FAILED (%d):" % len(failures))
        for f in failures:
            print("  - " + f)
        return 1
    print("ALL TAXLOT_EXT SELFTESTS PASSED (rule_version=%s)" % RULE_VERSION)
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())

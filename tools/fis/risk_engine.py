#!/usr/bin/env python3
"""risk_engine.py -- FIS risk metrics v2.

NumPy-backed covariance validation; explicit metric horizons and data window.
Every returned dict carries a full ``disclosure`` block.

Usage: python risk_engine.py --selftest
"""

import math
import random
from datetime import date

import numpy as np

try:
    from .covariance import validate_covariance
except ImportError:
    from covariance import validate_covariance

TRADING_DAYS = 252

INCLUDED_RISKS = [
    "equity-market", "concentration", "duration-rates",
    "liquidity-horizon", "income-loss",
]
EXCLUDED_RISKS = ["currency", "counterparty", "intraday-liquidity"]

# 2022 Q1 synthetic stress factors: total-return drawdowns Jan-Mar 2022.
_SPY_2022Q1 = {"drawdown_pct": -4.95}
_SYNTH_2022Q1 = {
    "ZPHR": {"drawdown_pct": -18.0},          # high-beta single name
    "TOTMKT-SYNTH": {"drawdown_pct": -5.5},
    "USAGG-SYNTH": {"drawdown_pct": -5.9},     # duration hit
    "TGT2055-SYNTH": {"drawdown_pct": -6.2},
    "HSAIDX-SYNTH": {"drawdown_pct": -3.0},
}


# ---------------------------------------------------------------------------
# disclosure
# ---------------------------------------------------------------------------

# Days beyond which a price series is declared STALE and its risk numbers
# are demoted (confidence floor "LOW" + is_stale=True). Callers must not
# present a stale risk number as current.
STALE_SLA_DAYS = 5
TRADING_DAYS_PER_YEAR = TRADING_DAYS


def _parse_iso(s):
    if type(s) is date:
        return s
    if not isinstance(s, str) or len(s) != 10:
        raise ValueError("risk dates must be ISO YYYY-MM-DD")
    parsed = date.fromisoformat(s)
    if parsed.isoformat() != s:
        raise ValueError("risk dates must be ISO YYYY-MM-DD")
    return parsed


def _staleness_block(as_of, report_date, n_obs):
    """Honest staleness: report date MINUS the date of the newest datum.

    If the caller withholds `as_of` we say UNKNOWN. We never substitute the
    report date for the data date -- that is exactly the defect (RISK-STALE-
    DISCLOSURE-PRESENT) this replaces: an always-fresh-looking staleness
    field that flagged nothing.
    """
    rep = _parse_iso(report_date) if report_date is not None else date.today()
    if as_of is None:
        return {
            "data_as_of": "UNKNOWN-NO-DATA-DATE-SUPPLIED",
            "report_date": rep.isoformat(),
            "staleness": "UNKNOWN-NO-DATA-DATE-SUPPLIED",
            "staleness_days": None,
            "is_stale": None,
            "stale_sla_days": STALE_SLA_DAYS,
            "stale_note": (
                "no data date supplied; staleness CANNOT be assessed. "
                "Treat as potentially stale."
            ),
        }
    dat = _parse_iso(as_of)
    age = (rep - dat).days
    if age < 0:
        raise ValueError("data_as_of is after report_date; future observations "
                         "cannot establish current risk")
    is_stale = age > STALE_SLA_DAYS
    return {
        "data_as_of": dat.isoformat(),
        "report_date": rep.isoformat(),
        "staleness": "AGE-%dd" % age,
        "staleness_days": age,
        "is_stale": is_stale,
        "stale_sla_days": STALE_SLA_DAYS,
        "stale_note": (
            "STALE: data age %dd exceeds SLA %dd; do not present as current."
            % (age, STALE_SLA_DAYS) if is_stale
            else "fresh within SLA %dd." % STALE_SLA_DAYS
        ),
    }


def _disclosure(n_obs=0, assumptions=None, included=None, confidence=None,
                as_of=None, report_date=None, degenerate=None):
    if confidence is None:
        if n_obs >= 100:
            confidence = "HIGH"
        elif n_obs >= 20:
            confidence = "MED"
        else:
            confidence = "LOW"
    n = int(n_obs or 0)
    block = _staleness_block(as_of, report_date, n)
    if block.get("is_stale") is not False:
        # Unknown timing also cannot establish confidence in current risk.
        confidence = "LOW"
    window = "obs-n%d-trading-days%s" % (
        n, ("-asof-%s" % block["data_as_of"]) if as_of is not None else "")
    out = {
        "horizon": "metric-specific; see assumptions",
        "data_window": window,
        "model_id": "fis-risk-v2",
        "confidence_basis": "sample-size heuristic, not calibrated statistical confidence",
        "assumptions": list(assumptions or []),
        "confidence": confidence,
        "included_risks": list(included or INCLUDED_RISKS),
        "excluded_risks": list(EXCLUDED_RISKS),
        "sensitivity": "univariate",
        "applicable_limits": {},
    }
    out.update(block)
    if degenerate:
        out["degraded"] = True
        out["degraded_reason"] = degenerate
        out["assumptions"] = list(assumptions or []) + [
            "DEGRADED: %s" % degenerate]
    return out


def _max_drawdown(closes):
    peak = closes[0]
    mdd = 0.0
    for c in closes:
        if c > peak:
            peak = c
        if peak > 0:
            dd = (c - peak) / peak
            if dd < mdd:
                mdd = dd
    return abs(mdd)


# ---------------------------------------------------------------------------
# position risk
# ---------------------------------------------------------------------------

def empirical_expected_shortfall(losses, confidence=0.95):
    """Equal-probability empirical quantile integral, including boundary atoms.

    Positive values are losses; an all-gains sample can have negative ES.
    Acerbi and Tasche (2002), Definition 2.6 / Proposition 3.2:
    https://arxiv.org/abs/cond-mat/0104295 . No horizon scaling is applied.
    """
    if isinstance(confidence, bool) or _first_non_finite([confidence], "confidence"):
        raise ValueError("confidence must be finite and strictly between zero and one")
    alpha = float(confidence)
    if not 0 < alpha < 1:
        raise ValueError("confidence must be strictly between zero and one")
    values = list(losses)
    if not values or _first_non_finite(values, "losses"):
        raise ValueError("losses must be nonempty and finite")
    ordered = sorted((float(x) for x in values), reverse=True)
    mass = (1.0 - alpha) * len(ordered)
    whole = int(math.floor(mass))
    fraction = mass - whole
    # Divide before summing to avoid intermediate overflow for large losses.
    terms = [x / mass for x in ordered[:whole]]
    if fraction:
        terms.append(ordered[whole] * (fraction / mass))
    try:
        result = math.fsum(terms)
    except OverflowError as exc:
        raise ValueError("expected shortfall exceeds finite numerical range") from exc
    if not math.isfinite(result):
        raise ValueError("expected shortfall exceeds finite numerical range")
    return result


def position_risk(closes, as_of=None, report_date=None, price_basis="unspecified"):
    """Annualized volatility, observed max drawdown and ONE-DAY empirical ES95.

    es95 is a compatibility alias for es95_daily in model v2. The separately
    named sqrt-time proxy is an approximation, never annual Expected Shortfall.
    as_of is the newest observation's ISO date; missing dates remain UNKNOWN.
    Callers must state adjusted-close/total-return basis when known.
    """
    closes = list(closes)
    if any(isinstance(c, (bool, np.bool_)) for c in closes):
        raise ValueError("closes must be real prices, not booleans")
    closes = [float(c) for c in closes]
    if len(closes) < 3:
        raise ValueError("need at least 3 closes")
    if _first_non_finite(closes, "closes") or any(c <= 0 for c in closes):
        raise ValueError("closes must all be finite and positive; corrupt observations cannot be dropped")
    if not isinstance(price_basis, str) or not price_basis.strip():
        raise ValueError("price_basis must be a nonempty description")
    rets = [closes[i] / closes[i - 1] - 1.0 for i in range(1, len(closes))]
    if _first_non_finite(rets, "derived returns"):
        raise ValueError("derived returns must be finite")
    scale = max(abs(r) for r in rets)
    normalized = [r / scale for r in rets] if scale else rets
    mu = math.fsum(normalized) / len(rets)
    variance = math.fsum((r - mu) ** 2 for r in normalized) / (len(rets) - 1)
    ann_vol = math.sqrt(variance * TRADING_DAYS) * scale
    mdd = _max_drawdown(closes)
    es95_daily = empirical_expected_shortfall([-r for r in rets])
    proxy = es95_daily * math.sqrt(TRADING_DAYS)
    if _first_non_finite([ann_vol, mdd, es95_daily, proxy], "derived metrics"):
        raise ValueError("derived risk metrics exceed finite numerical range")
    n_obs = len(rets)
    disclosure = _disclosure(
        n_obs=n_obs, as_of=as_of, report_date=report_date,
        assumptions=[
            "daily simple returns; volatility scales by sqrt(252) under serially uncorrelated returns",
            "ES95 is the one-day empirical loss quantile integral with fractional boundary mass",
            "sqrt-time ES proxy is not a calibrated annual loss forecast",
            "price basis: " + price_basis,
        ], included=["equity-market"])
    disclosure["horizon"] = "volatility: 1y; ES95: 1 trading day; drawdown: observed window"
    return {
        "ann_vol": round(ann_vol, 6), "maxdd": round(mdd, 6),
        "es95": round(es95_daily, 6), "es95_daily": round(es95_daily, 6),
        "es95_sqrt_time_proxy": round(proxy, 6), "n_obs": n_obs,
        "disclosure": disclosure,
    }


# ---------------------------------------------------------------------------
# portfolio risk
# ---------------------------------------------------------------------------

def _default_corr(i, j):
    return 1.0 if i == j else 0.30


def portfolio_risk(weights, cov_or_vols, corr_func=None, *, as_of=None,
                   report_date=None, n_obs=None, covariance_horizon="unspecified"):
    """Long-only portfolio volatility from validated covariance or vol/corr.

    Positive relative allocations are normalized. Short books require a
    separate leverage/concentration model. Covariance units and sample count
    must be supplied by the caller; asset count is not observation count.
    Invalid matrices are refused in every direction, including unheld assets.
    """
    w = list(weights)
    if not w or _first_non_finite(w, "weights"):
        raise ValueError("portfolio_risk requires nonempty finite weights")
    w = [float(x) for x in w]
    if any(x < 0 for x in w):
        raise ValueError("portfolio_risk relative allocations must be nonnegative")
    scale = max(w)
    if scale <= 0:
        raise ValueError("portfolio_risk weights must have a positive total")
    scaled = [x / scale for x in w]
    total = math.fsum(scaled)
    w = [x / total for x in scaled]
    n = len(w)
    # Accept ordinary lists and ndarray inputs without accepting mixed shapes.
    try:
        inputs = np.asarray(cov_or_vols)
    except (TypeError, ValueError) as exc:
        raise ValueError("portfolio_risk requires a volatility vector or square covariance") from exc
    if inputs.ndim == 2:
        if inputs.shape != (n, n):
            raise ValueError("portfolio_risk covariance must be NxN")
        if corr_func is not None:
            raise ValueError("corr_func cannot accompany a supplied covariance matrix")
        checked = validate_covariance(cov_or_vols)
        assumptions = ["caller-supplied covariance, validated without regularization"]
    elif inputs.ndim == 1 and len(inputs) == n:
        if inputs.dtype.kind not in "iuf" or _first_non_finite(cov_or_vols, "volatilities"):
            raise ValueError("volatilities must be finite real numbers")
        vols = [float(v) for v in inputs]
        if any(v < 0 for v in vols):
            raise ValueError("volatility cannot be negative")
        corr = corr_func or _default_corr
        correlations = [[corr(i, j) for j in range(n)] for i in range(n)]
        correlation = validate_covariance(correlations, correlation=True)["covariance"]
        cov = [[vols[i] * vols[j] * correlation[i][j] for j in range(n)] for i in range(n)]
        if any(vols[i] != 0 and vols[j] != 0 and correlation[i][j] != 0
               and cov[i][j] == 0 for i in range(n) for j in range(n)):
            raise ValueError("volatility covariance product underflows numerical range")
        checked = validate_covariance(cov)
        assumptions = ["supplied marginal volatilities and validated correlation matrix"]
        if corr_func is None:
            assumptions.append("legacy assumed correlation 0.30 off diagonal; not estimated from observations")
    else:
        raise ValueError("portfolio_risk requires equal-length vector or NxN covariance")
    if n_obs is not None and (isinstance(n_obs, bool) or not isinstance(n_obs, int) or n_obs < 0):
        raise ValueError("n_obs must be a nonnegative integer or None")
    if not isinstance(covariance_horizon, str) or not covariance_horizon.strip():
        raise ValueError("covariance_horizon must be a nonempty description")
    cov = np.asarray(checked["covariance"])
    cov_scale = float(np.max(np.abs(cov)))
    unit = cov / cov_scale if cov_scale else cov
    port_var = float(np.asarray(w) @ unit @ np.asarray(w))
    # A numerically tiny negative quadratic form is possible on the nullspace
    # of a validated PSD matrix; only that roundoff is floored, and disclosed.
    roundoff = port_var < 0
    if port_var < -checked["diagnostics"]["relative_tolerance"]:
        raise ValueError("validated covariance produced materially negative variance")
    port_vol = math.sqrt(max(port_var, 0.0)) * math.sqrt(cov_scale)
    if not math.isfinite(port_vol):
        raise ValueError("portfolio volatility exceeds finite numerical range")
    assumptions += ["long-only weights sum-normalized", "single-period variance; no rebalancing drift",
                    "covariance horizon: " + covariance_horizon]
    if n_obs is None:
        assumptions.append("covariance observation count unknown; number of assets is not sample size")
    disclosure = _disclosure(n_obs=n_obs or 0, as_of=as_of, report_date=report_date,
        assumptions=assumptions, included=["equity-market", "concentration"])
    disclosure["horizon"] = covariance_horizon
    return {
        "port_vol": round(port_vol, 6),
        "hhi_concentration": round(math.fsum(x * x for x in w), 6),
        "top_name_share": round(max(w), 6), "n_assets": n, "n_obs": n_obs,
        "variance_clamped": False, "numerical_roundoff_floor": roundoff,
        "covariance_diagnostics": checked["diagnostics"], "disclosure": disclosure,
    }


def _first_non_finite(values, label):
    """Return (label, value) for the first non-finite entry, else None."""
    for i, v in enumerate(values):
        if isinstance(v, (bool, np.bool_)):
            return ("%s[%d]" % (label, i), v)
        try:
            f = float(v)
        except (TypeError, ValueError, OverflowError):
            return ("%s[%d]" % (label, i), v)
        if not math.isfinite(f):
            return ("%s[%d]" % (label, i), v)
    return None


# ---------------------------------------------------------------------------
# household liquidity risk
# ---------------------------------------------------------------------------

def household_risk(liquidity_months, monthly_spend, floor_months=3):
    """Deterministic liquidity buffer band, not an estimated probability."""
    cover = _finite_nonnegative(liquidity_months, "liquidity_months")
    floor_months = _finite_nonnegative(floor_months, "floor_months")
    monthly_spend = _finite_nonnegative(monthly_spend, "monthly_spend")
    if monthly_spend == 0:
        raise ValueError("monthly_spend must be positive")
    months_of_cover = round(cover, 4)
    if cover <= floor_months:
        label = "HIGH"
    elif cover <= floor_months * 1.5:
        label = "MED"
    else:
        label = "LOW"
    return {
        "breach_probability_label": label,  # compatibility alias, ordinal only
        "liquidity_buffer_band": label,
        "probability_estimated": False,
        "months_of_cover": months_of_cover,
        "monthly_spend": round(float(monthly_spend), 2),
        "floor_months": floor_months,
        "buffer_months": round(cover - floor_months, 4),
        "assumptions": [
            "spend constant across the horizon",
            "no income assumed during draw period",
        ],
        "disclosure": _disclosure(
            n_obs=1,
            assumptions=["point-in-time liquidity snapshot"],
            included=["liquidity-horizon"],
        ),
    }


def _finite_nonnegative(value, label):
    if isinstance(value, bool) or _first_non_finite([value], label):
        raise ValueError(label + " must be finite and nonnegative")
    number = float(value)
    if number < 0:
        raise ValueError(label + " must be finite and nonnegative")
    return number


def reverse_stress(current_liquidity_months, floor_months=3):
    """Exact linear cash decline to reach the floor, on the closed [0,100]%.

    A strictly greater decline breaches a positive floor. Reaching zero
    requires 100%; negative liquidity is outside this cash-only model.
    """
    cur = _finite_nonnegative(current_liquidity_months, "current_liquidity_months")
    floor = _finite_nonnegative(floor_months, "floor_months")
    breached = cur <= floor
    decline = 0.0 if breached else (1.0 - floor / cur) * 100.0
    residual = 0.0 if breached else cur * (1.0 - decline / 100.0) - floor
    return {
        "breaching_decline_pct": decline, "analytic_decline_pct": decline,
        "threshold_semantics": "reaches floor; strict breach requires greater decline",
        "residual": residual, "current_liquidity_months": cur,
        "floor_months": floor, "already_breached": breached,
        "disclosure": _disclosure(
            assumptions=["exact linear cash scaling; spend held constant; decline in [0,100] percent"],
            included=["liquidity-horizon"]),
    }


# ---------------------------------------------------------------------------
# stress tests
# ---------------------------------------------------------------------------

def historical_stress_2022q1(book_values, closes_lookup):
    """Apply 2022 Q1 SPY drawdown, scaled per-name by same-sector beta flag.

    book_values: {ticker: usd_value}. closes_lookup(ticker) -> dict with
    'drawdown_pct' or None/missing -> use raw SPY factor. Names sharing a
    sector with the broad market get beta 1.0; concentrated single-name
    equity gets beta ~1.5 approximated via lookup override.
    """
    spy_dd = _SPY_2022Q1["drawdown_pct"]
    stressed = {}
    betas = {}
    for ticker, value in book_values.items():
        value = _finite_nonnegative(value, "book value")
        info = None
        try:
            info = closes_lookup(ticker)
        except Exception:
            info = None
        dd = None
        if isinstance(info, dict):
            dd = info.get("drawdown_pct")
        if dd is None:
            beta = 1.0
            eff_dd = spy_dd
        else:
            if _first_non_finite([dd], "drawdown_pct"):
                raise ValueError("drawdown_pct must be finite")
            dd = float(dd)
            if dd < -100:
                raise ValueError("drawdown_pct cannot be below -100")
            beta = round(dd / spy_dd, 4) if spy_dd != 0 else 1.0
            eff_dd = dd
        betas[ticker] = beta
        stressed[ticker] = round(value * (1.0 + eff_dd / 100.0), 2)
    book_total = sum(float(v) for v in book_values.values())
    stressed_total = sum(stressed.values())
    if _first_non_finite([book_total, stressed_total, *stressed.values()], "stress result"):
        raise ValueError("stress result exceeds finite numerical range")
    return {
        "book_value": round(book_total, 2),
        "stressed_value": round(stressed_total, 2),
        "pnl": round(stressed_total - book_total, 2),
        "per_name_stressed": stressed,
        "per_name_beta_vs_spy": betas,
        "scenario": "2022-Q1-SPY-DRAWDOWN",
        "spy_drawdown_pct": spy_dd,
        "assumptions": [
            "per-name betas approximated by same-sector flag from lookup",
            "instantaneous repricing, no recovery path",
        ],
        "disclosure": _disclosure(
            assumptions=["historical window replayed as instantaneous shock"],
            included=["equity-market", "duration-rates"],
            confidence="MED",
        ),
    }


def hypothetical_shock(equity_pct=-0.35, duration_shock=-0.10):
    """Instantaneous shock template: equity leg plus rates/duration leg."""
    if _first_non_finite([equity_pct, duration_shock], "shock"):
        raise ValueError("shock magnitudes must be finite")
    eq = float(equity_pct)
    dur = float(duration_shock)
    if eq < -1 or dur < -1 or not math.isfinite(eq + dur):
        raise ValueError("unlevered leg shocks must be >= -1 and combined result finite")
    return {
        "equity_shock_pct": eq,
        "duration_shock_pct": dur,
        "total_pnl_pct_if_fully_exposed": round(eq + dur, 6),
        "total_pnl": round(eq + dur, 6),
        "note": (
            "apply per-book: pnl = equity_book*eq + bond_book*dur*(neg dur shock "
            "= yield rise); pass actual books through historical_stress-style mapping"
        ),
        "scenario": "HYPOTHETICAL-EQUITY-RATES",
        "assumptions": [
            "parallel instantaneous move; no path dependency",
            "equity and rate shocks simultaneous",
        ],
        "disclosure": _disclosure(
            assumptions=["shock magnitudes user-supplied"],
            included=["equity-market", "duration-rates"],
        ),
    }


# ---------------------------------------------------------------------------
# kill switch
# ---------------------------------------------------------------------------

def kill_switch(metrics, limits):
    """True when any required metric breaches or cannot be evaluated.

    limits values may be scalars (upper bound) or dicts like
    {'max': x} / {'min': x}.
    """
    for key, lim in (limits or {}).items():
        val = metrics.get(key)
        # W9-B A4-08: every IEEE-754 comparison against NaN is False, so a
        # NaN metric silently DISARMED the kill switch -- one corrupt
        # upstream input made an unsafe book look compliant. A metric that
        # cannot be evaluated is a breach, not a pass.
        if _first_non_finite([val], key):
            return True
        val = float(val)
        if isinstance(lim, dict):
            mx = lim.get("max")
            mn = lim.get("min")
            bounds = [v for v in (mx, mn) if v is not None]
            if not bounds or set(lim) - {"min", "max"} or \
                    _first_non_finite(bounds, "limits"):
                return True
            if mx is not None and mn is not None and float(mn) > float(mx):
                return True
            if mx is not None and val > float(mx):
                return True
            if mn is not None and val < float(mn):
                return True
        else:
            if _first_non_finite([lim], "limits"):
                return True
            if val > float(lim):
                return True
    return False


# ---------------------------------------------------------------------------
# selftest
# ---------------------------------------------------------------------------

def run_selftest():
    lines = []

    def check(label, cond):
        lines.append("%s: %s" % ("PASS" if cond else "FAIL", label))
        if not cond:
            raise AssertionError(label)

    # 1. synthetic closes finite
    rng = random.Random(42)
    closes = [100.0]
    for _ in range(500):
        closes.append(max(closes[-1] * (1.0 + rng.gauss(0.0003, 0.012)), 0.01))
    pos = position_risk(closes, as_of="2026-09-12", report_date="2026-09-12")
    check("position_risk finite on synthetic closes",
          all(math.isfinite(pos[k]) for k in ("ann_vol", "maxdd", "es95")))
    check("disclosure confidence HIGH at n>=100 (%s)" % pos["disclosure"]["confidence"],
          pos["disclosure"]["confidence"] == "HIGH")

    # 2. ZPHR-like concentration flags top_name_share > 0.30
    weights = [0.365, 0.10, 0.10, 0.10, 0.095, 0.08, 0.08, 0.08]
    vols = [0.55, 0.18, 0.16, 0.15, 0.14, 0.13, 0.12, 0.12]
    port = portfolio_risk(weights, vols)
    check("top_name_share %.4f > 0.30" % port["top_name_share"],
          port["top_name_share"] > 0.30)
    check("port_vol positive and finite (%.4f)" % port["port_vol"],
          math.isfinite(port["port_vol"]) and port["port_vol"] > 0)

    # 3. reverse stress converges within tolerance
    rev = reverse_stress(current_liquidity_months=8.0, floor_months=3)
    liq_at = rev["current_liquidity_months"] * (1.0 - rev["breaching_decline_pct"] / 100.0)
    check("reverse_stress converges (residual %.6f)" % rev["residual"],
          abs(rev["residual"]) <= 0.01 and abs(liq_at - 3.0) <= 0.05)

    # 4. kill_switch trips on breach
    limits = {"maxdd_pct": 20.0, "ann_vol": 0.30}
    ok_metrics = {"maxdd_pct": 8.0, "ann_vol": 0.22}
    bad_metrics = {"maxdd_pct": 26.0, "ann_vol": 0.22}
    check("kill_switch False within limits", kill_switch(ok_metrics, limits) is False)
    check("kill_switch True on breach", kill_switch(bad_metrics, limits) is True)

    # 5. stress helpers shape
    book = {"ZPHR": 285000.0, "TOTMKT-SYNTH": 398040.0, "USAGG-SYNTH": 16800.0}
    hs = historical_stress_2022q1(book, lambda t: _SYNTH_2022Q1.get(t))
    check("historical_stress_2022q1 stressed < book (%.2f < %.2f)"
          % (hs["stressed_value"], hs["book_value"]),
          hs["stressed_value"] < hs["book_value"])
    shock = hypothetical_shock(-0.35, -0.10)
    check("hypothetical_shock negative combined pnl", shock["total_pnl"] < 0)

    hh = household_risk(4.0, 7500.0)
    check("household_risk label valid (%s)" % hh["breach_probability_label"],
          hh["breach_probability_label"] in ("LOW", "MED", "HIGH"))

    lines.append("SELFTEST OK: risk_engine")
    return "\n".join(lines)


if __name__ == "__main__":
    print(run_selftest())

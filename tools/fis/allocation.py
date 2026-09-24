"""Constrained, cost-aware research allocation and Black-Litterman updating.

Pure numerical proposals. No portfolio-account mutation or order generation.
The convex objective includes heterogeneous one-way transaction-cost penalties;
post-solve feasibility and a linear-oracle convex optimality gap are mandatory.
Primary references are recorded in docs/institutional-methods.md.
"""
from __future__ import annotations

import argparse
import json
import math
import numpy as np
from scipy.optimize import linprog, minimize
try:
    from .covariance import validate_covariance
except ImportError:
    from covariance import validate_covariance

VERSION = "convex-cost-allocation-v1"


def _linear_lower_bound(result, gradient, a, b, eq, bounds):
    """Validate the LP primal/dual certificate, including bound multipliers.

    Residual stationarity is conservatively bounded over the finite box. A
    feasible LP point alone supplies no lower bound on the minimum objective.
    """
    size = len(gradient)
    try:
        point = np.asarray(result.x, dtype=float)
        y = np.asarray(result.ineqlin.marginals, dtype=float)
        v = np.asarray(result.eqlin.marginals, dtype=float)
        lower = np.asarray(result.lower.marginals, dtype=float)
        upper = np.asarray(result.upper.marginals, dtype=float)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("linear certificate missing primal/dual arrays") from exc
    arrays = ((point,(size,)),(y,(len(b),)),(v,(1,)),(lower,(size,)),(upper,(size,)))
    if any(x.shape != shape or not np.isfinite(x).all() for x,shape in arrays):
        raise ValueError("linear certificate has nonfinite or malformed primal/dual arrays")
    lo,hi=np.array(bounds,dtype=float).T
    violation=max(float(np.max(a@point-b)),abs(float((eq@point)[0])-1),
                  float(np.max(lo-point)),float(np.max(point-hi)))
    if violation>1e-8:
        raise ValueError("linear certificate primal point is infeasible")
    if max(float(np.max(y)),float(np.max(-lower)),float(np.max(upper)))>1e-8:
        raise ValueError("linear certificate has invalid dual signs")
    y=np.minimum(y,0);lower=np.maximum(lower,0);upper=np.minimum(upper,0)
    residual=gradient-a.T@y-eq.T@v-lower-upper
    # Valid multiplier signs plus the box minimum cover any stationarity error.
    terms=np.r_[b*y,v,lo*lower,hi*upper,np.minimum(residual*lo,residual*hi)]
    roundoff=128*np.finfo(float).eps*max(1.,float(np.sum(np.abs(terms))))
    bound=float(np.sum(terms))-roundoff
    primal=float(gradient@point)
    if not math.isfinite(bound) or not math.isfinite(primal) or primal-bound>1e-7 or primal<bound-1e-8:
        raise ValueError("linear certificate primal-dual gap failed")
    return bound, dict(lp_primal_dual_gap=primal-bound,lp_primal_violation=violation,
                       lp_stationarity_residual=float(np.max(np.abs(residual))),
                       roundoff_allowance=roundoff)


def _array(x, name, ndim):
    raw = np.asarray(x)
    if raw.dtype.kind not in "fiu" or raw.ndim != ndim or not raw.size:
        raise ValueError(name + " requires a nonempty real numeric array")
    if any(isinstance(value,(bool,np.bool_)) for value in np.asarray(x,dtype=object).flat):
        raise ValueError(name + " cannot contain booleans")
    a = np.asarray(raw, dtype=float)
    if not np.isfinite(a).all():
        raise ValueError(name + " must be finite")
    return a


def _positive(x, name, allow_zero=False):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError(name + " must be finite numeric")
    if x < 0 or (not allow_zero and x == 0):
        raise ValueError(name + " must be positive")
    return float(x)


def validated_covariance(values, *, positive_definite=False):
    checked = validate_covariance(values)
    a = np.asarray(checked["covariance"],dtype=float)
    diagnostics = checked["diagnostics"]
    scale = float(np.max(np.abs(a)))
    tolerance = scale * diagnostics["relative_tolerance"]
    if positive_definite and diagnostics["min_eigenvalue"] <= tolerance:
        raise ValueError("covariance must be numerically positive definite")
    return a, {**diagnostics,"numerical_tolerance":tolerance}


def black_litterman(covariance, market_weights, *, risk_aversion, tau,
                   pick_matrix=None, views=None, view_covariance=None):
    """Gaussian posterior with full correlated view-error covariance.

    Returns are excess returns in the SAME period as covariance; no hidden
    annualization. Omega is required for views: confidence is never invented.
    Prior Pi = delta Sigma w; M is uncertainty of the posterior mean, not Sigma.
    """
    cov, diagnostics = validated_covariance(covariance, positive_definite=True)
    n = len(cov)
    w = _array(market_weights, "market_weights", 1)
    if len(w) != n or np.any(w < 0) or abs(float(w.sum()) - 1) > 1e-10:
        raise ValueError("market_weights must be a complete long-only simplex")
    delta = _positive(risk_aversion, "risk_aversion")
    tau = _positive(tau, "tau")
    prior = delta * cov @ w
    prior_uncertainty = tau * cov
    if pick_matrix is None:
        if views is not None or view_covariance is not None:
            raise ValueError("views require an explicit pick matrix")
        mean, uncertainty = prior, prior_uncertainty
    else:
        p = _array(pick_matrix, "pick_matrix", 2)
        q = _array(views, "views", 1)
        omega, _ = validated_covariance(view_covariance, positive_definite=True)
        if p.shape != (len(q), n) or omega.shape != (len(q), len(q)) or np.any(np.linalg.norm(p, axis=1) == 0):
            raise ValueError("view dimensions/rows invalid")
        cross = prior_uncertainty @ p.T
        innovation_cov = p @ cross + omega
        gain = np.linalg.solve(innovation_cov, cross.T).T
        mean = prior + gain @ (q - p @ prior)
        uncertainty = prior_uncertainty - gain @ cross.T
    uncertainty = (uncertainty + uncertainty.T) / 2
    if not np.isfinite(mean).all() or not np.isfinite(uncertainty).all():
        raise ValueError("nonfinite posterior")
    return dict(model_id="black-litterman-gaussian-v1", prior_returns=prior.tolist(),
                posterior_returns=mean.tolist(), mean_uncertainty=uncertainty.tolist(),
                predictive_covariance=(cov + uncertainty).tolist(), diagnostics=diagnostics,
                status="conditional_on_supplied_views_and_uncertainty",
                warnings=["not calibrated forecasts; input covariance, views and Omega need empirical validation"])


def optimize_allocation(covariance, *, current_weights, one_way_costs,
                        expected_returns=None, risk_aversion=1.0, horizon_periods=1,
                        max_weight=1.0, max_turnover=None, exposures=None):
    """Minimize delta/2 * H*w'Sigma*w - H*mu'w + cost'|w-current|.

    Fully invested long-only weights. Cash may be an explicitly modeled asset;
    current_weights may sum below one for an initially uninvested book.
    Exposures are [{name, loadings, lower, upper}]; limits are caller inputs.
    Turnover is sum absolute asset-weight changes, NOT half-turnover.
    Horizon scaling assumes independent stationary returns; it is not a multi-
    period path model. Linear costs are an explicit research approximation.
    """
    cov, diagnostics = validated_covariance(covariance)
    n = len(cov)
    current = _array(current_weights, "current_weights", 1)
    costs = _array(one_way_costs, "one_way_costs", 1)
    mu = np.zeros(n) if expected_returns is None else _array(expected_returns, "expected_returns", 1)
    if any(len(x) != n for x in (current, costs, mu)):
        raise ValueError("asset axes must have equal length")
    if (np.any(current < 0) or current.sum() > 1 + 1e-10
            or np.any(costs < 0) or np.any(costs >= 1)):
        raise ValueError("invalid current weights or one-way fractional costs")
    delta = _positive(risk_aversion, "risk_aversion")
    h = _positive(horizon_periods, "horizon_periods")
    cap = _positive(max_weight, "max_weight")
    if cap > 1 or n * cap < 1 - 1e-12:
        raise ValueError("infeasible long-only position cap")
    a, b = [], []
    for i in range(n):
        row = np.zeros(2 * n); row[i] = 1; row[n + i] = -1
        a.append(row); b.append(current[i])
        row = np.zeros(2 * n); row[i] = -1; row[n + i] = -1
        a.append(row); b.append(-current[i])
    if max_turnover is not None:
        turn = _positive(max_turnover, "max_turnover", allow_zero=True)
        a.append(np.r_[np.zeros(n), np.ones(n)]); b.append(turn)
    names = set()
    for item in exposures or []:
        name = item.get("name")
        if not isinstance(name, str) or not name.strip() or name in names:
            raise ValueError("unique named exposures required")
        names.add(name)
        load = _array(item["loadings"], "exposure loadings", 1)
        low, high = item["lower"], item["upper"]
        if (len(load) != n or any(isinstance(v, bool) or not isinstance(v, (int, float))
                                 or not math.isfinite(v) for v in (low, high)) or low > high):
            raise ValueError("invalid exposure bounds")
        a.extend([np.r_[load, np.zeros(n)], np.r_[-load, np.zeros(n)]])
        b.extend([high, -low])
    a, b = np.asarray(a), np.asarray(b)
    eq = np.r_[np.ones(n), np.zeros(n)][None, :]
    bounds = [(0, cap)] * n + [(0, 1)] * n
    feasible = linprog(np.zeros(2 * n), A_ub=a, b_ub=b, A_eq=eq, b_eq=[1],
                       bounds=bounds, method="highs",
                       options={"dual_feasibility_tolerance":1e-9,"primal_feasibility_tolerance":1e-9})
    if not feasible.success:
        raise ValueError("allocation constraints infeasible or feasibility solver failed")
    matrix = delta * h * cov
    linear = np.r_[-h * mu, costs]
    scale = max(float(np.max(np.abs(matrix))), float(np.max(np.abs(linear))), 1e-16)
    def objective(z):
        return (0.5 * z[:n] @ matrix @ z[:n] + linear @ z) / scale
    def jac(z):
        return (np.r_[matrix @ z[:n], np.zeros(n)] + linear) / scale
    constraints = [dict(type="eq", fun=lambda z: eq @ z - 1, jac=lambda z: eq),
                   dict(type="ineq", fun=lambda z: b - a @ z, jac=lambda z: -a)]
    solved = minimize(objective, feasible.x, jac=jac, method="SLSQP", bounds=bounds,
                      constraints=constraints, options=dict(ftol=1e-12, maxiter=2000))
    if not solved.success or not np.isfinite(solved.x).all():
        raise ValueError("allocation optimization did not converge: " + str(solved.message))
    z = solved.x
    violation = max(float(np.max(a @ z - b)), abs(float((eq @ z)[0]) - 1),
                    float(np.max(-z)), float(np.max(z[:n] - cap)), float(np.max(z[n:] - 1)))
    if violation > 1e-8:
        raise ValueError("solver output violates allocation constraints")
    # For convex f and any feasible x, f(x)-f(x*) <= grad f(x)'(x-s),
    # where s minimizes the linearized objective over the SAME feasible set.
    gradient = jac(z)
    oracle = linprog(gradient, A_ub=a, b_ub=b, A_eq=eq, b_eq=[1], bounds=bounds, method="highs",
                     options={"dual_feasibility_tolerance":1e-9,"primal_feasibility_tolerance":1e-9})
    if not oracle.success:
        raise ValueError("independent optimality certificate unavailable")
    lower_bound, lp_certificate = _linear_lower_bound(oracle,gradient,a,b,eq,bounds)
    raw_gap=float(gradient@z)-lower_bound
    if not math.isfinite(raw_gap):
        raise ValueError("nonfinite convex optimality certificate")
    # Covariance validation tolerates floating-point negative eigenvalues.
    # The simplex has squared diameter <= 2, so this weak-curvature correction
    # bounds the worst quadratic remainder instead of claiming exact convexity.
    curvature_allowance=max(0.0,-diagnostics["min_eigenvalue"])*delta*h
    normalized_gap = max(0.0, raw_gap) + curvature_allowance/scale
    if normalized_gap > 1e-6:
        raise ValueError("convex optimality gap too large: " + str(normalized_gap))
    w = z[:n]
    actual_turnover = float(np.abs(w - current).sum())
    actual_cost = float(costs @ np.abs(w - current))
    return dict(model_id=VERSION, status="validated_numerical_proposal", weights=w.tolist(),
                variance_per_period=float(w @ cov @ w), expected_return_per_period=float(mu @ w),
                expected_returns_supplied=expected_returns is not None,
                one_way_cost_fraction=actual_cost, turnover_l1=actual_turnover,
                objective_value=float(0.5 * w @ matrix @ w - h * mu @ w + actual_cost),
                certificate=dict(max_constraint_violation=violation,
                                 convex_gap_upper_bound=normalized_gap * scale,
                                 normalized_gap=normalized_gap, solver_iterations=int(solved.nit),
                                 negative_curvature_allowance=curvature_allowance,
                                 **lp_certificate),
                diagnostics=diagnostics, horizon_periods=h,
                warnings=["research weights only; no account, tax-lot or order authority",
                          "independent stationary horizon scaling and linear transaction costs assumed",
                          "real execution requires separate cash/lot/cost reconciliation"])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="JSON: covariance plus explicit optimize_allocation arguments")
    args = ap.parse_args()
    try:
        with open(args.input, encoding="utf-8") as stream:
            values = json.load(stream)
        out = optimize_allocation(**values)
        print(json.dumps(out, sort_keys=True, allow_nan=False))
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(json.dumps(dict(status="refused", reason=str(exc))))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

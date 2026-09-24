"""Validated covariance estimators for explicit, aligned observation matrices.

Rows are observations, columns are assets; no data retrieval or missing-row repair.
OAS uses Chen et al. (2010), equation 23, INCLUDING the 2/p terms:
https://arxiv.org/abs/0907.4698 . Its Gaussian iid model is an assumption.
QIS follows Ledoit and Wolf (2022), doi:10.3150/20-BEJ1315 and the authors'
R/Matlab implementations, with an orthonormal symmetric eigensolver:
https://github.com/MikeWolf007/covShrinkage/blob/main/qis.R
https://github.com/oledoit/covShrinkage/blob/main/QIS.m
The Python reference is pinned in test_institutional_risk.py; general eig in
that reference is unsuitable for repeated nullspaces. No estimator is novel.

The QIS implementation below is adapted under the source-file BSD-2-Clause:
Copyright (c) 2021, Olivier Ledoit and Michael Wolf. All rights reserved.
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

from datetime import date
import math
import numbers

import numpy as np


def _real_array(values, label, ndim):
    try:
        raw = np.asarray(values)
        # Reject coercible strings, bools, complex numbers and ragged inputs.
        if raw.dtype.kind not in "iuf" or raw.ndim != ndim:
            raise ValueError
        if any(isinstance(value, (bool, np.bool_)) for value in
               np.asarray(values, dtype=object).flat):
            raise ValueError
        array = np.asarray(raw, dtype=float)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(label + " must be a rectangular real numeric array") from exc
    if not np.isfinite(array).all():
        raise ValueError(label + " must contain only finite values")
    return array


def _positive_number(value, label):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Real):
        raise ValueError(label + " must be a finite positive number")
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(label + " must be a finite positive number")
    return value


def validate_covariance(matrix, *, correlation=False):
    """Return covariance + spectral diagnostics; refuse invalid input.

    Numerical tolerance is 64*p*machine-epsilon, relative to matrix scale.
    Only within-tolerance asymmetry is averaged and disclosed. No eigenvalue
    clipping, diagonal loading or nearest-PSD replacement is performed.
    Singular PSD matrices are valid but cannot supply an ordinary inverse.
    """
    if not isinstance(correlation, bool):
        raise ValueError("correlation must be boolean")
    cov = _real_array(matrix, "covariance", 2)
    p = len(cov)
    if p == 0 or cov.shape != (p, p):
        raise ValueError("covariance must be a nonempty square matrix")
    scale = float(np.max(np.abs(cov)))
    tol = 64.0 * p * np.finfo(float).eps
    unit = cov / scale if scale else cov.copy()
    if np.any((cov != 0) & (unit == 0)):
        raise ValueError("covariance normalization underflows nonzero input")
    asymmetry = float(np.max(np.abs(unit - unit.T)))
    if asymmetry > tol:
        raise ValueError("covariance must be symmetric")
    if np.any(np.diag(cov) < 0):
        raise ValueError("covariance diagonal cannot be negative")
    if correlation:
        if np.any(np.abs(cov) > 1.0 + tol):
            raise ValueError("correlations must lie in [-1, 1]")
        if np.max(np.abs(np.diag(cov) - 1.0)) > tol:
            raise ValueError("correlation diagonal must equal one")
    # Difference-based averaging preserves identical subnormal entries;
    # halving each side first can erase a smallest representable diagonal.
    unit = unit + (unit.T - unit) * 0.5
    eig = np.linalg.eigvalsh(unit)
    if float(eig[0]) < -tol:
        raise ValueError("covariance must be positive semidefinite")
    rank = int(np.count_nonzero(eig > tol))
    condition = float(eig[-1] / eig[0]) if rank == p else None
    # Preserve input units directly, avoiding a lossy scale round trip.
    result = cov + (cov.T - cov) * 0.5
    # Eigenvalues can exceed representable range even with finite entries.
    max_eigen = float(eig[-1]) * scale
    min_eigen = float(eig[0]) * scale
    if not math.isfinite(max_eigen) or not math.isfinite(min_eigen):
        raise ValueError("covariance spectrum exceeds finite numerical range")
    return {
        "covariance": result.tolist(),
        "diagnostics": {
            "n_assets": p, "rank": rank, "is_singular": rank < p,
            "condition_number": condition, "min_eigenvalue": min_eigen,
            "max_eigenvalue": max_eigen,
            "relative_tolerance": tol,
            "symmetry_adjusted": bool(asymmetry),
            "regularization_applied": False,
        },
    }


def _timing(as_of, report_date, max_age_days):
    def iso(value, label):
        if isinstance(value, date) and type(value) is date:
            return value
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError(label + " must be an ISO date YYYY-MM-DD")
        try:
            parsed = date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(label + " must be an ISO date YYYY-MM-DD") from exc
        if parsed.isoformat() != value:
            raise ValueError(label + " must be an ISO date YYYY-MM-DD")
        return parsed

    observed = iso(as_of, "as_of") if as_of is not None else None
    reported = iso(report_date, "report_date") if report_date is not None else None
    if max_age_days is not None and (isinstance(max_age_days, bool) or
            not isinstance(max_age_days, int) or max_age_days < 0):
        raise ValueError("max_age_days must be a nonnegative integer")
    age = (reported - observed).days if observed and reported else None
    if age is not None and age < 0:
        raise ValueError("as_of cannot be after report_date")
    stale = age > max_age_days if age is not None and max_age_days is not None else None
    return {
        "as_of": observed.isoformat() if observed else None,
        "report_date": reported.isoformat() if reported else None,
        "age_days": age, "max_age_days": max_age_days, "is_stale": stale,
        "freshness": "UNKNOWN" if stale is None else ("STALE" if stale else "WITHIN_POLICY"),
        "current_data_verified": False,
        "date_basis": "caller-supplied; no source or chronology verification",
    }


def _qis(sample, effective_n):
    """QIS spectral equations, using an orthonormal basis even when p > n."""
    p = len(sample)
    eigenvalues, vectors = np.linalg.eigh(sample)
    null_count = max(0, p - effective_n)
    positive = eigenvalues[null_count:]
    threshold = 64 * p * np.finfo(float).eps * max(float(eigenvalues[-1]), 0.0)
    if len(positive) == 0 or np.any(positive <= threshold):
        raise ValueError("QIS requires full effective sample rank; use an explicit alternative for degenerate data")
    c = p / effective_n
    h = min(c * c, 1.0 / (c * c)) ** 0.35 / p ** 0.35
    inverse = 1.0 / positive
    # Rows index i, columns index j, matching the authors' R/Matlab code.
    lj = inverse[None, :]
    difference = lj - inverse[:, None]
    denominator = difference ** 2 + h * h * lj ** 2
    theta = np.mean(lj * difference / denominator, axis=1)
    conjugate = np.mean(h * lj ** 2 / denominator, axis=1)
    amplitude = theta ** 2 + conjugate ** 2
    if p <= effective_n:
        delta = 1.0 / (inverse * ((1 - c) ** 2 +
                       2 * c * (1 - c) * theta + c * c * amplitude))
    else:
        delta0 = 1.0 / ((c - 1) * np.mean(inverse))
        delta = np.concatenate((np.full(null_count, delta0), 1.0 / (inverse * amplitude)))
    delta *= np.trace(sample) / np.sum(delta)
    result = (vectors * delta) @ vectors.T
    return result, {"bandwidth": float(h), "concentration_ratio": c,
                    "structural_nullity": null_count, "trace_preserved": True}


def _checked_gram(centered, divisor, weights=None):
    """Refuse variance erased by shared scaling before later rescaling."""
    with np.errstate(under="ignore"):
        squares = centered * centered
    if np.any((centered != 0) & (squares == 0)):
        raise ValueError("normalized observation squares underflow numerical range")
    gram = ((centered.T @ centered) if weights is None else
            ((centered.T * weights) @ centered)) / divisor
    varying = np.any(centered != 0, axis=0)
    if np.any(varying & (np.diag(gram) == 0)):
        raise ValueError("normalized variance underflows numerical range")
    return gram


def estimate_covariance(returns, method="oas", annualization=252,
                        assume_centered=False, decay=None, as_of=None,
                        report_date=None, max_age_days=None):
    """Estimate a covariance matrix with explicit method and timing metadata.

    sample: divisor N-1 after demeaning; N if zero mean is asserted.
    oas: original Chen equation 23 with ML covariance divisor N, target mu*I.
    ewma: normalized finite-history exponential weights, newest row last.
          Weighted demeaning uses divisor 1-sum(weights**2); known zero mean
          uses divisor one. This is not an initialized RiskMetrics recursion.
    qis: default demean and effective N-1, or known zero mean and N.
    Annualization multiplies covariance; it assumes additive uncorrelated
    equal-frequency returns and is not a multi-period loss forecast.
    """
    if not isinstance(method, str) or method not in ("sample", "oas", "ewma", "qis"):
        raise ValueError("method must be sample, oas, ewma or qis")
    if not isinstance(assume_centered, bool):
        raise ValueError("assume_centered must be boolean")
    factor = _positive_number(annualization, "annualization")
    timing = _timing(as_of, report_date, max_age_days)
    x = _real_array(returns, "returns", 2)
    n, p = x.shape
    if n < 2 or p < 1:
        raise ValueError("returns requires at least two observations and one asset")
    if method == "ewma":
        decay = _positive_number(decay, "decay")
        if decay >= 1:
            raise ValueError("decay must be strictly between zero and one")
    elif decay is not None:
        raise ValueError("decay applies only to ewma")
    # Normalize magnitudes to prevent intermediate squared-return overflow.
    scale = float(np.max(np.abs(x)))
    scaled = x / scale if scale else x.copy()
    if np.any((x != 0) & (scaled == 0)):
        raise ValueError("observation normalization underflows nonzero input")
    effective_n = n if assume_centered else n - 1
    centered = scaled if assume_centered else scaled - scaled.mean(axis=0)
    if not assume_centered and np.any(np.any(x != x[0], axis=0) &
                                     np.all(centered == 0, axis=0)):
        raise ValueError("shared scaling erased representable observation variation")
    shrinkage = None
    extra = {}
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        try:
            if method == "sample":
                divisor = effective_n
                cov = _checked_gram(centered, divisor)
            elif method == "oas":
                divisor = n
                sample = _checked_gram(centered, divisor)
                trace = float(np.trace(sample))
                trace2 = float(np.sum(sample * sample))
                if trace != 0 and trace * trace == 0:
                    raise ValueError("OAS trace square underflows numerical range")
                denominator = (n + 1.0 - 2.0 / p) * (trace2 - trace * trace / p)
                shrinkage = (min(1.0, max(0.0, ((1.0 - 2.0 / p) * trace2 + trace * trace)
                              / denominator)) if denominator > 0 else 1.0)
                cov = (1 - shrinkage) * sample + shrinkage * (trace / p) * np.eye(p)
                extra["formula"] = "Chen et al. 2010 equation 23, including 2/p terms"
            elif method == "ewma":
                weights = np.power(decay, np.arange(n - 1, -1, -1, dtype=float))
                weights /= weights.sum()
                effective_n = float(1.0 / (weights @ weights))
                divisor = 1.0 if assume_centered else float(1.0 - weights @ weights)
                if divisor <= np.finfo(float).eps:
                    raise ValueError("ewma has insufficient effective observations for weighted demeaning")
                centered = scaled if assume_centered else scaled - weights @ scaled
                cov = _checked_gram(centered, divisor, weights)
                extra["newest_weight"] = float(weights[-1])
                extra["weighting"] = "finite-history normalized exponential; newest row last"
            else:
                divisor = effective_n
                cov, extra = _qis(_checked_gram(centered, divisor), effective_n)
            # Multiplication order avoids premature scale**2 overflow.
            nonzero = cov != 0
            cov = ((cov * scale) * scale) * factor
            if np.any(nonzero & (cov == 0)):
                raise ValueError("covariance scaling underflows finite numerical range")
        except (FloatingPointError, OverflowError) as exc:
            raise ValueError("covariance calculation exceeds finite numerical range") from exc
    checked = validate_covariance(cov)
    warnings = []
    if checked["diagnostics"]["is_singular"]:
        warnings.append("singular covariance; ordinary inverse is unavailable")
    if timing["freshness"] != "WITHIN_POLICY":
        warnings.append("historical or unverified timing; cannot establish current risk")
    return {
        "covariance": checked["covariance"], "method": method,
        "model_id": "fis-covariance-v1", "n_obs": n, "n_assets": p,
        "annualization": factor, "assume_centered": assume_centered,
        "demeaning": "none; caller asserts zero mean" if assume_centered else
                     ("weighted sample mean" if method == "ewma" else "sample mean"),
        "sample_divisor": divisor, "effective_n": effective_n,
        "shrinkage": shrinkage, "decay": decay,
        "diagnostics": {**checked["diagnostics"], **extra},
        "timing": timing, "warnings": warnings,
        "assumptions": ["rows are aligned equal-frequency observations in common return units",
                        "no missing observations dropped or imputed",
                        "iid Gaussian model for OAS; iid large-dimensional model for QIS",
                        "annualization is a covariance scaling assumption, not a loss forecast"],
    }

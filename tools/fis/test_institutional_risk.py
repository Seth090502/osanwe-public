"""Offline mathematical controls; synthetic observations only, no services/files.

QIS reference fixture: authors-linked Python QIS.py at commit
a03fe6836ba9ce9a63dbd16a87d711f748d0862f, SHA256
ebfad3389304e1f8905c5eaefe739e8004816c32fd4380ede74387f56f4e95a1.
URL: https://raw.githubusercontent.com/pald22/covShrinkage/
a03fe6836ba9ce9a63dbd16a87d711f748d0862f/QIS.py
Only its AST FunctionDef was evaluated to obtain the fixed narrow fixture;
its module-level local CSV demo was never executed. Wide reference uses the
authors' R/Matlab scalar equations with an independent SVD basis, because
the Python reference's general eig fails for repeated null eigenvalues.
No network or reference code execution occurs during these tests.
"""

from fractions import Fraction
import json
import math
import unittest

import numpy as np
from scipy.linalg import svd

try:
    from .covariance import estimate_covariance, validate_covariance
    from . import risk_engine as risk
except ImportError:
    from covariance import estimate_covariance, validate_covariance
    import risk_engine as risk


def es_variational_oracle(losses, alpha):
    """Convex loss functional minimum occurs at a sample loss breakpoint."""
    return min(t + math.fsum(max(x - t, 0) for x in losses) /
               ((1 - alpha) * len(losses)) for t in losses)


def qis_svd_oracle(x, assume_centered=False):
    """Independent SVD + scalar sums, following qis.R, not array broadcasting."""
    n, p = x.shape
    effective = n if assume_centered else n - 1
    y = x if assume_centered else x - x.mean(axis=0)
    _, singular_values, vt = svd(y, full_matrices=True, lapack_driver="gesvd")
    # The SVD is descending; augment structural zeros then reverse the basis.
    eigenvalues = np.zeros(p)
    eigenvalues[:len(singular_values)] = singular_values ** 2 / effective
    eigenvalues = eigenvalues[::-1]
    vectors = vt.T[:, ::-1]
    nullity = max(0, p - effective)
    inverse = [1.0 / x for x in eigenvalues[nullity:]]
    ratio = p / effective
    bandwidth = min(ratio ** 2, ratio ** -2) ** 0.35 / p ** 0.35
    delta = []
    if nullity:
        delta = [1.0 / ((ratio - 1) * (sum(inverse) / len(inverse)))] * nullity
    for inv_i in inverse:
        theta = sum(inv_j * (inv_j - inv_i) /
                    ((inv_j - inv_i) ** 2 + bandwidth ** 2 * inv_j ** 2)
                    for inv_j in inverse) / len(inverse)
        conjugate = sum(bandwidth * inv_j ** 2 /
                       ((inv_j - inv_i) ** 2 + bandwidth ** 2 * inv_j ** 2)
                       for inv_j in inverse) / len(inverse)
        amplitude = theta ** 2 + conjugate ** 2
        denominator = inv_i * amplitude if nullity else inv_i * (
            (1 - ratio) ** 2 + 2 * ratio * (1 - ratio) * theta + ratio ** 2 * amplitude)
        delta.append(1.0 / denominator)
    delta = np.asarray(delta) * (sum(eigenvalues) / sum(delta))
    return vectors @ np.diag(delta) @ vectors.T


class MatrixValidation(unittest.TestCase):
    def test_invalid_in_unheld_or_positive_direction_refused(self):
        for matrix in ([[.04, .08], [.08, .04]], [[.04, 0], [0, -.01]],
                       [[.04, 0], [.04, .04]], [[.04, -.08], [-.08, .04]]):
            with self.subTest(matrix=matrix), self.assertRaises(ValueError):
                risk.portfolio_risk([1, 0], matrix)

    def test_correlation_constraints(self):
        for matrix in ([[1, 2], [2, 1]], [[.9, 0], [0, 1]],
                       [[1, .1], [.3, 1]], [[1, -.9, -.9], [-.9, 1, -.9], [-.9, -.9, 1]]):
            with self.subTest(matrix=matrix), self.assertRaises(ValueError):
                risk.portfolio_risk([1] * len(matrix), [.2] * len(matrix),
                                    lambda i, j: matrix[i][j])

    def test_singular_and_zero_are_valid_without_repair(self):
        for matrix, expected in (([[.04, .04], [.04, .04]], .2), ([[0, 0], [0, 0]], 0)):
            out = risk.portfolio_risk([50, 50], matrix)
            self.assertEqual(out["port_vol"], expected)
            self.assertTrue(out["covariance_diagnostics"]["is_singular"])
            self.assertIsNone(out["covariance_diagnostics"]["condition_number"])
            self.assertFalse(out["covariance_diagnostics"]["regularization_applied"])
            json.dumps(out, allow_nan=False)

    def test_two_by_two_spectral_oracle(self):
        for a, b, d in ((4., 1., 2.), (.01, -.003, .04), (1e-200, 0., 2e-200)):
            out = validate_covariance([[a, b], [b, d]])["diagnostics"]
            # hypot avoids squaring overflow/underflow in the analytic oracle.
            root = math.hypot(a - d, 2 * b)
            smallest, largest = ((a + d - root) / 2, (a + d + root) / 2)
            self.assertAlmostEqual(out["condition_number"], largest / smallest, places=11)

    def test_relative_tolerance_never_repairs_material_defect(self):
        for factor in (1e-200, 1., 1e200):
            with self.assertRaises(ValueError):
                validate_covariance(np.asarray([[1., 2.], [2., 1.]]) * factor)
            result = validate_covariance(np.asarray([[1., .2], [.2, 2.]]) * factor)
            self.assertEqual(result["diagnostics"]["rank"], 2)

    def test_shapes_nonfinite_complex_and_bool_refused(self):
        for matrix in ([], [[1, 2]], [[1, 0], [0]], [[math.nan]], [[math.inf]], [[1j]], [[True]], [[True, 0], [0, 1.]], [["1"]]):
            with self.subTest(matrix=matrix), self.assertRaises(ValueError):
                validate_covariance(matrix)

    def test_long_only_normalization_and_sample_count(self):
        a = risk.portfolio_risk([1e308, 1e308], [[.04, 0], [0, .09]])
        b = risk.portfolio_risk([.5, .5], [[.04, 0], [0, .09]])
        self.assertEqual(a, b)
        self.assertIsNone(a["n_obs"])
        self.assertEqual(a["disclosure"]["confidence"], "LOW")
        for w in ([-1, 2], [0, 0], [math.nan, 1]):
            with self.assertRaises(ValueError):
                risk.portfolio_risk(w, [.2, .3])

    def test_covariance_normalization_cannot_erase_representable_diagonal(self):
        matrix = [[1e200, 0.], [0., 1e-200]]
        self.assertGreater(matrix[1][1], 0.)
        with self.assertRaisesRegex(ValueError, "underflow"):
            validate_covariance(matrix)
        with self.assertRaisesRegex(ValueError, "underflow"):
            risk.portfolio_risk([0., 1.], matrix)
        # Valid small diagonals must not be erased by symmetry averaging.
        smallest = float(np.nextafter(0., 1.))
        np.testing.assert_array_equal(
            validate_covariance([[1., 0.], [0., smallest]])["covariance"],
            [[1., 0.], [0., smallest]])

    def test_mixed_booleans_refused_before_array_or_float_coercion(self):
        for boolean in (True, np.bool_(True)):
            for probe in (
                    lambda: risk.portfolio_risk([.5, .5], [[boolean, 0], [0, 1.]]),
                    lambda: risk.portfolio_risk([.5, .5], [boolean, .2]),
                    lambda: risk.portfolio_risk([boolean, .5], [.1, .2]),
                    lambda: risk.position_risk([boolean, 1.1, 1.2])):
                with self.assertRaises(ValueError):
                    probe()


class CovarianceEstimation(unittest.TestCase):
    def setUp(self):
        self.x = np.array([[2., 1., 0.], [-1., 2., 3.], [3., -2., 1.], [0., 4., -2.],
                           [1., 0., 2.], [-3., 1., -1.], [2., -1., 4.], [4., 3., 1.]])

    def test_sample_against_pairwise_fraction_oracle(self):
        x = [[1, 2], [2, 4], [4, -1]]
        means = [Fraction(sum(col), 3) for col in zip(*x)]
        expected = [[float(sum((Fraction(row[i]) - means[i]) *
                              (Fraction(row[j]) - means[j]) for row in x) / 2)
                     for j in range(2)] for i in range(2)]
        out = estimate_covariance(x, "sample", annualization=1)
        np.testing.assert_allclose(out["covariance"], expected, rtol=2e-15)
        self.assertEqual(out["sample_divisor"], 2)

    def test_original_oas_fraction_oracle_retains_two_over_p(self):
        # Known-zero-mean covariance diag(25,1,1), N=6. Equation 23, p=3.
        x = [[5, 0, 0], [-5, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]]
        diagonal = [Fraction(25, 3), Fraction(1, 3), Fraction(1, 3)]
        trace, trace2 = sum(diagonal), sum(v * v for v in diagonal)
        shrink = min(Fraction(1), ((1 - Fraction(2, 3)) * trace2 + trace ** 2) /
                     ((7 - Fraction(2, 3)) * (trace2 - trace ** 2 / 3)))
        expected = np.diag([float((1 - shrink) * v + shrink * trace / 3) for v in diagonal])
        out = estimate_covariance(x, "oas", annualization=1, assume_centered=True)
        np.testing.assert_allclose(out["covariance"], expected, rtol=2e-15)
        self.assertAlmostEqual(out["shrinkage"], float(shrink), places=15)
        self.assertEqual(out["sample_divisor"], 6)

    def test_oas_default_demean_and_degenerate_behavior(self):
        a = estimate_covariance(self.x, "oas", annualization=1)
        b = estimate_covariance(self.x + 50, "oas", annualization=1)
        np.testing.assert_allclose(a["covariance"], b["covariance"], atol=3e-14)
        for matrix in ([[3], [3], [3]], [[0, 0], [0, 0]]):
            result = estimate_covariance(matrix, "oas", annualization=1)
            self.assertTrue(result["diagnostics"]["is_singular"])
            self.assertEqual(result["shrinkage"], 1)

    def test_ewma_weighted_pairwise_oracle(self):
        x, d = [[1, 2], [3, -1], [2, 4]], Fraction(1, 2)
        weights = [Fraction(1, 7), Fraction(2, 7), Fraction(4, 7)]
        means = [sum(w * row[j] for w, row in zip(weights, x)) for j in range(2)]
        denominator = 1 - sum(w * w for w in weights)
        expected = [[float(sum(w * (row[i] - means[i]) * (row[j] - means[j])
                              for w, row in zip(weights, x)) / denominator)
                     for j in range(2)] for i in range(2)]
        out = estimate_covariance(x, "ewma", annualization=1, decay=float(d))
        np.testing.assert_allclose(out["covariance"], expected, rtol=2e-15)
        self.assertAlmostEqual(out["effective_n"], float(1 / sum(w * w for w in weights)))
        self.assertAlmostEqual(out["sample_divisor"], float(denominator))

    def test_known_mean_and_annualization_are_explicit(self):
        for method in ("sample", "oas", "ewma", "qis"):
            kwargs = {"decay": .94} if method == "ewma" else {}
            a = estimate_covariance(self.x, method, annualization=1, assume_centered=True, **kwargs)
            b = estimate_covariance(self.x, method, annualization=252, assume_centered=True, **kwargs)
            np.testing.assert_allclose(b["covariance"], np.asarray(a["covariance"]) * 252, rtol=3e-15)
            self.assertIn("zero mean", a["demeaning"])

    def test_qis_pinned_author_python_fixture(self):
        expected = [[4.320509434188918, -.14689414837669523, .12869379378618398],
                    [-.14689414837669504, 4.396131326516717, -.010800742188712721],
                    [.12869379378618412, -.010800742188712811, 4.426216382151503]]
        out = estimate_covariance(self.x, "qis", annualization=1)
        np.testing.assert_allclose(out["covariance"], expected, rtol=2e-13, atol=2e-14)
        self.assertEqual(out["sample_divisor"], 7)

    def test_qis_independent_svd_scalar_oracle_narrow_square_wide(self):
        rng = np.random.default_rng(1984)
        for n, p in ((20, 4), (5, 4), (5, 5), (5, 9), (12, 20)):
            for centered in (False, True):
                x = rng.normal(size=(n, p))
                out = estimate_covariance(x, "qis", annualization=1, assume_centered=centered)
                expected = qis_svd_oracle(x, centered)
                np.testing.assert_allclose(out["covariance"], expected, atol=2e-12, rtol=2e-11)
                eigenvalues = np.linalg.eigvalsh(out["covariance"])
                self.assertGreater(eigenvalues[0], 0)
                y = x if centered else x - x.mean(axis=0)
                trace = np.sum(y * y) / (n if centered else n - 1)
                self.assertAlmostEqual(np.trace(out["covariance"]), trace, places=11)

    def test_qis_repeated_spectrum_and_rank_refusal(self):
        x = np.vstack((np.eye(3), -np.eye(3)))
        out = estimate_covariance(x, "qis", annualization=1)
        np.testing.assert_allclose(out["covariance"], np.eye(3) * .4, atol=1e-15)
        for x in ([[1, 1], [2, 2], [3, 3]], [[0], [0]], [[2], [2]]):
            with self.assertRaisesRegex(ValueError, "rank"):
                estimate_covariance(x, "qis")

    def test_rotation_and_scale_equivariance(self):
        q, _ = np.linalg.qr(np.array([[1., 2, 3], [-2, 4, 1], [3, -1, 2]]))
        for method in ("sample", "oas", "ewma", "qis"):
            kwargs = {"decay": .94} if method == "ewma" else {}
            base = np.asarray(estimate_covariance(self.x, method, annualization=1, **kwargs)["covariance"])
            rotated = estimate_covariance(self.x @ q, method, annualization=1, **kwargs)["covariance"]
            scaled = estimate_covariance(self.x * 1e-80, method, annualization=1, **kwargs)["covariance"]
            np.testing.assert_allclose(rotated, q.T @ base @ q, atol=2e-14, rtol=2e-13)
            np.testing.assert_allclose(np.asarray(scaled) / 1e-160, base, atol=2e-14, rtol=2e-13)

    def test_metadata_does_not_invent_freshness(self):
        unknown = estimate_covariance(self.x)
        self.assertEqual(unknown["timing"]["freshness"], "UNKNOWN")
        self.assertIsNone(unknown["timing"]["report_date"])
        old = estimate_covariance(self.x, as_of="2025-01-01", report_date="2026-09-12", max_age_days=5)
        self.assertTrue(old["timing"]["is_stale"])
        fresh = estimate_covariance(self.x, as_of="2026-09-12", report_date="2026-09-12", max_age_days=5)
        self.assertEqual(fresh["timing"]["freshness"], "WITHIN_POLICY")
        self.assertFalse(fresh["timing"]["current_data_verified"])
        with self.assertRaises(ValueError):
            estimate_covariance(self.x, as_of="2026-09-13", report_date="2026-09-12")
        for kwargs in ({"as_of": "2026-09-12junk"}, {"max_age_days": -1}, {"report_date": "20260912"}):
            with self.assertRaises(ValueError):
                estimate_covariance(self.x, **kwargs)

    def test_invalid_method_data_or_options_fail(self):
        for kwargs in ({"method": "QIS"}, {"method": None}, {"annualization": 0},
                       {"annualization": True}, {"annualization": math.inf},
                       {"assume_centered": "False"}, {"decay": .94},
                       {"method": "ewma"}, {"method": "ewma", "decay": 1},
                       {"method": "ewma", "decay": 1e-300}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                estimate_covariance(self.x, **kwargs)
        for x in ([], [[1]], [[1, math.nan], [2, 3]], [[True], [False]], [["1"], ["2"]]):
            with self.subTest(x=x), self.assertRaises(ValueError):
                estimate_covariance(x)
        with self.assertRaises(ValueError):
            estimate_covariance([[1e308], [-1e308]], "sample")

    def test_numerical_underflow_is_not_zero_risk(self):
        for method in ("sample", "oas", "ewma", "qis"):
            kwargs = {"decay": .94} if method == "ewma" else {}
            with self.assertRaisesRegex(ValueError, "underflow"):
                estimate_covariance(self.x * 1e-200, method, annualization=1, **kwargs)
        with self.assertRaisesRegex(ValueError, "underflow"):
            risk.portfolio_risk([1.], [1e-200])

    def test_shared_scale_cannot_erase_small_asset_variance(self):
        # Decimal/Fraction oracle from the actual represented observations:
        # the constant first asset contributes zero; the second has 2*a*a.
        a = Fraction.from_float(1e-100)
        actual_variance = float(2 * a * a)
        self.assertGreater(actual_variance, 0.)
        self.assertAlmostEqual(actual_variance / 2e-200, 1., places=14)
        x = [[1e200, -1e-100], [1e200, 1e-100]]
        for method in ("sample", "oas", "ewma", "qis"):
            kwargs = {"decay": .94} if method == "ewma" else {}
            with self.subTest(method=method), self.assertRaisesRegex(ValueError, "underflow"):
                estimate_covariance(x, method, annualization=1, **kwargs)
        # Direct normalization loss is distinct from later square loss.
        with self.assertRaisesRegex(ValueError, "normalization underflows"):
            estimate_covariance([[1e200, -1e-200], [1e200, 1e-200]], "sample")
        # A retained variance cannot conceal underflow in OAS fourth moments.
        with self.assertRaisesRegex(ValueError, "trace square underflows"):
            estimate_covariance([[1e100, -1e-50], [1e100, 1e-50]], "oas", annualization=1)
        # Ordinary common scaling remains exactly the declared estimator.
        expected = [[0., 0.], [0., 2e-100]]
        got = estimate_covariance([[1e10, -1e-50], [1e10, 1e-50]], "sample", annualization=1)
        np.testing.assert_allclose(got["covariance"], expected, rtol=3e-15, atol=0.)

    def test_all_outputs_are_strict_json(self):
        for method in ("sample", "oas", "ewma", "qis"):
            kwargs = {"decay": .94} if method == "ewma" else {}
            json.dumps(estimate_covariance(self.x, method, **kwargs), allow_nan=False)


class TailRiskAndLiquidity(unittest.TestCase):
    def test_fractional_atom_not_ceil_tail(self):
        losses = [.1, .02] + [0.] * 19
        want = (.1 + .05 * .02) / 1.05
        self.assertAlmostEqual(risk.empirical_expected_shortfall(losses), want, places=14)
        self.assertAlmostEqual(risk.empirical_expected_shortfall(losses), es_variational_oracle(losses, .95), places=14)

    def test_es_matches_variational_oracle_with_ties_gains_small_tail(self):
        for losses in ([.2, .2, .1, -.1], [-.1, -.2, -.3], [2.], [0, 0, 0], list(range(-15, 16))):
            for alpha in (.1, .5, .95, .9999):
                self.assertAlmostEqual(risk.empirical_expected_shortfall(losses, alpha),
                                       es_variational_oracle(losses, alpha), places=11)

    def test_es_coherence_controls(self):
        a, b = [1., -1., 3., 2.], [-2., 4., 2., 1.]
        es = risk.empirical_expected_shortfall
        self.assertLessEqual(es([x + y for x, y in zip(a, b)], .6), es(a, .6) + es(b, .6) + 1e-14)
        self.assertAlmostEqual(es([3 * x for x in a]), 3 * es(a))
        self.assertAlmostEqual(es([x + 5 for x in a]), es(a) + 5)
        self.assertLessEqual(es(a, .5), es(a, .95))

    def test_position_es_has_daily_horizon_and_separate_proxy(self):
        closes = [100.]
        for ret in [-.1, -.02] + [0.] * 19:
            closes.append(closes[-1] * (1 + ret))
        out = risk.position_risk(closes)
        self.assertEqual(out["es95"], round((.1 + .05 * .02) / 1.05, 6))
        self.assertEqual(out["es95"], out["es95_daily"])
        self.assertAlmostEqual(out["es95_sqrt_time_proxy"], (.1 + .05 * .02) / 1.05 * math.sqrt(252), places=6)
        self.assertIn("1 trading day", out["disclosure"]["horizon"])

    def test_unknown_stale_future_or_malformed_dates(self):
        closes = [100 * 1.001 ** i for i in range(121)]
        self.assertEqual(risk.position_risk(closes)["disclosure"]["confidence"], "LOW")
        self.assertEqual(risk.position_risk(closes, "2025-01-01", "2026-09-12")["disclosure"]["confidence"], "LOW")
        for as_of in ("2026-09-13", "2026-09-12garbage"):
            with self.assertRaises(ValueError):
                risk.position_risk(closes, as_of, "2026-09-12")
        with self.assertRaises(ValueError):
            risk.position_risk(closes, report_date="")

    def test_finite_input_overflow_and_invalid_tail_refuse(self):
        with self.assertRaises(ValueError):
            risk.position_risk([1e-300, 1e300, 1e300])
        for losses, alpha in (([], .95), ([math.nan], .95), ([1], 1), ([1], 0), ([1], math.nan)):
            with self.assertRaises(ValueError):
                risk.empirical_expected_shortfall(losses, alpha)

    def test_exact_reverse_stress_extreme_and_zero_floor(self):
        out = risk.reverse_stress(100000, 3)
        self.assertAlmostEqual(out["breaching_decline_pct"], 99.997, places=12)
        self.assertLess(abs(out["residual"]), 1e-10)
        self.assertEqual(risk.reverse_stress(8, 0)["breaching_decline_pct"], 100)
        self.assertEqual(risk.reverse_stress(2, 3)["breaching_decline_pct"], 0)
        self.assertTrue(risk.reverse_stress(0, 0)["already_breached"])

    def test_invalid_liquidity_never_reports_low(self):
        for bad in (math.nan, math.inf, -1, True):
            for func in (lambda: risk.household_risk(bad, 100),
                         lambda: risk.household_risk(8, bad),
                         lambda: risk.reverse_stress(bad),
                         lambda: risk.reverse_stress(8, bad)):
                with self.assertRaises(ValueError):
                    func()
        self.assertFalse(risk.household_risk(8, 100)["probability_estimated"])

    def test_stress_nonfinite_refusal(self):
        for func in (lambda: risk.historical_stress_2022q1({"X": math.nan}, lambda _: None),
                     lambda: risk.historical_stress_2022q1({"X": 100}, lambda _: {"drawdown_pct": math.inf}),
                     lambda: risk.hypothetical_shock(math.nan, -.1)):
            with self.assertRaises(ValueError):
                func()


if __name__ == "__main__":
    unittest.main()

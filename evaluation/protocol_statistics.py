"""Prespecified family-level statistics; no sequential extension or admission claim.

Inputs are independent underlying scenario/source families, not individual prompts
or three repeated arms. Public development examples are not unseen evidence.
"""
from __future__ import annotations
import math


def exact_limits(successes: int, families: int, confidence: float = 0.95):
    """Two-sided Clopper-Pearson limits with explicit independent-family units."""
    from scipy.stats import beta
    if not isinstance(successes, int) or not isinstance(families, int) or not 0 <= successes <= families or families <= 0 or not 0 < confidence < 1:
        raise ValueError('invalid independent-family counts')
    alpha = 1 - confidence
    return {'lower': 0.0 if successes == 0 else float(beta.ppf(alpha / 2, successes, families-successes+1)),
            'upper': 1.0 if successes == families else float(beta.ppf(1-alpha/2, successes+1, families-successes)),
            'successes': successes, 'families': families, 'unit': 'independent scenario/source family',
            'confidence': confidence, 'method': 'Clopper-Pearson'}


def batch_alpha(batch_index: int):
    if not isinstance(batch_index, int) or not 1 <= batch_index <= 1000:
        raise ValueError('batch index starts at 1 and never resets across candidates')
    return math.ldexp(0.05, -batch_index)


def holm(pvalues: dict[str, float], alpha: float):
    if not pvalues or not 0 < alpha < 1 or any(not math.isfinite(p) or not 0 <= p <= 1 for p in pvalues.values()):
        raise ValueError('finite prespecified p-values required')
    ordered = sorted(pvalues.items(), key=lambda item: (item[1], item[0]))
    result, maximum = {}, 0.0
    for rank, (name, p) in enumerate(ordered):
        maximum = max(maximum, min(1.0, (len(ordered)-rank)*p))
        result[name] = {'p': p, 'adjusted_p': maximum, 'reject': maximum <= alpha}
    return result


def paired_exact(baseline, candidate):
    """One-sided exact McNemar test. Missing outcomes are failures, never dropped."""
    from scipy.stats import binomtest
    if len(baseline) != len(candidate) or not baseline:
        raise ValueError('matched independent family outcomes required')
    if any(x not in (0, 1, None) for x in [*baseline, *candidate]):
        raise ValueError('outcomes must be 0, 1 or missing')
    pairs = [(int(b or 0), int(c or 0)) for b, c in zip(baseline, candidate)]
    better = sum(b == 0 and c == 1 for b, c in pairs)
    worse = sum(b == 1 and c == 0 for b, c in pairs)
    p = float(binomtest(better, better+worse, 0.5, alternative='greater').pvalue) if better+worse else 1.0
    return {'p': p, 'better': better, 'worse': worse, 'families': len(pairs),
            'difference': (better-worse)/len(pairs), 'missing_treated_as_failure': True}


def family_outcomes(cases, outcomes):
    """Collapse shared scenario OR source families before binary confidence tests.

    outcomes maps case IDs to binary results; missing means failure. A family
    succeeds only if all of its frozen obligations/cases succeed. Renamed IDs
    with shared source/scenario cannot increase the sample count.
    """
    if not cases or len({c['id'] for c in cases}) != len(cases):
        raise ValueError('unique frozen cases required')
    if set(outcomes)-{c['id'] for c in cases} or any(v not in (0,1,None) for v in outcomes.values()):
        raise ValueError('outcomes must match frozen cases')
    parents=list(range(len(cases)))
    def find(i):
        while parents[i]!=i:
            parents[i]=parents[parents[i]];i=parents[i]
        return i
    seen={}
    for index,c in enumerate(cases):
        for field in ('scenario_family','source_family'):
            if not c.get(field):raise ValueError('family metadata required')
            key=(field,c[field])
            if key in seen:parents[find(index)]=find(seen[key])
            else:seen[key]=index
    grouped={}
    for index,c in enumerate(cases):grouped.setdefault(find(index),[]).append(c['id'])
    return [{'case_ids':ids,'success':int(all(outcomes.get(i)==1 for i in ids))} for ids in grouped.values()]


def exact_paired_power(n: int, discordance: float, difference: float, alpha: float):
    """Power conditional on pilot-estimated discordance, integrating discordant N.

    Central truncation omits at most 2e-12 probability mass; the returned value
    is a conservative lower bound. It is not a guarantee of pilot transfer.
    """
    import numpy as np
    from scipy.stats import binom
    if n <= 0 or not 0 < difference <= discordance <= 1 or not 0 < alpha < 1:
        raise ValueError('invalid power assumptions')
    lo = max(1, int(binom.ppf(1e-12, n, discordance)))
    hi = int(binom.ppf(1-1e-12, n, discordance))
    if hi < lo:
        return 0.0
    k = np.arange(lo, hi+1)
    critical = binom.isf(alpha, k, 0.5).astype(int)+1
    alternative = (discordance+difference)/(2*discordance)
    return float(np.sum(binom.pmf(k, n, discordance)*binom.sf(critical-1, k, alternative)))


def size_confirmation(pilot_better: int, pilot_worse: int, pilot_families: int,
                      batch_index=1, comparisons=2, target_power=0.90,
                      difference=0.05, maximum=200000):
    """Return a fixed future size; NEVER accepts confirmatory outcomes to extend it.

    Plans conservatively with a 95% upper bound on pilot discordance and
    Bonferroni allocation (valid for the later prespecified Holm procedure).
    """
    from scipy.stats import norm
    if min(pilot_better, pilot_worse) < 0 or pilot_better+pilot_worse > pilot_families or comparisons < 1:
        raise ValueError('invalid pilot')
    limits = exact_limits(pilot_better+pilot_worse, pilot_families)
    q = max(difference, limits['upper'])
    alpha = batch_alpha(batch_index)/comparisons
    start = max(2, math.ceil(((norm.ppf(1-alpha)*math.sqrt(q) + norm.ppf(target_power)*math.sqrt(q-difference*difference))/difference)**2))
    n = start
    power = exact_paired_power(n, q, difference, alpha)
    while power < target_power and n < maximum:
        n += max(1, math.ceil(n*0.005))
        power = exact_paired_power(n, q, difference, alpha)
    if n > maximum or power < target_power:
        return {'status': 'inconclusive_resource_limit', 'required_families': None}
    return {'status': 'planning_only_freeze_before_confirmation', 'required_families': n,
            'power_lower_bound_at_assumed_discordance': power, 'assumed_discordance': q,
            'target_difference': difference, 'target_power': target_power, 'per_comparison_alpha': alpha,
            'batch_index': batch_index, 'pilot_families': pilot_families,
            'no_extension_after_outcomes': True,
            'limitation': 'Family independence and pilot discordance transfer must be justified; small pilot uncertainty remains.'}

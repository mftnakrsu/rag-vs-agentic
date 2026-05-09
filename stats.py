"""Statistics utilities for the paper's main matrix analysis.

Implements:
- Non-parametric bootstrap CIs for per-pipeline metrics (1000 iters default).
  Both percentile (`bootstrap_ci`) and BCa / bias-corrected-and-accelerated
  (`bootstrap_ci_bca`). BCa is the paper-grade default; percentile is kept
  for sanity comparison and for cases where BCa's acceleration estimate is
  ill-defined.
- Paired bootstrap CIs for pipeline-pair differences (percentile + BCa).
- Paired permutation test for mean differences (10000 perms default).
- Bonferroni and Holm corrections for multiple comparisons.
- Cohen's d effect size (independent + paired).

Why these specifically: the 2025-2026 RAG-eval methodology bar is paired
tests + bootstrap CIs + multiple-comparison correction. CIKM short-paper
reviewers expect BCa over percentile when N is small (300 per stratum).

API contract:
- Inputs are 1-D iterables of floats (e.g., per-query metric values).
- For paired tests, a[i] and b[i] must reference the same query.
- All RNG paths take a `seed` for reproducibility.
"""
from __future__ import annotations

import math
from typing import Iterable, Sequence

import numpy as np
import scipy.stats as _sps


def bootstrap_ci(
    values: Sequence[float],
    *,
    n_iters: int = 1000,
    ci: float = 0.95,
    seed: int = 0,
) -> tuple[float, float, float]:
    """Non-parametric bootstrap CI for the mean of a single sample.

    Returns:
        (mean, lower, upper) where the CI is symmetric percentile.
    """
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return (float("nan"), float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    means = np.empty(n_iters)
    n = arr.size
    for i in range(n_iters):
        sample = rng.choice(arr, size=n, replace=True)
        means[i] = sample.mean()
    alpha = (1.0 - ci) / 2.0
    lo = float(np.quantile(means, alpha))
    hi = float(np.quantile(means, 1.0 - alpha))
    return (float(arr.mean()), lo, hi)


def paired_bootstrap_ci(
    a: Sequence[float],
    b: Sequence[float],
    *,
    n_iters: int = 1000,
    ci: float = 0.95,
    seed: int = 0,
) -> tuple[float, float, float]:
    """Paired bootstrap CI for the mean difference (a - b).

    a[i] and b[i] must reference the same observation (same query, same seed).
    Sampling is done over indices, preserving pairing. Reported difference
    is mean(a) - mean(b).

    Returns:
        (mean_diff, lower, upper).
    """
    aa = np.asarray(a, dtype=float)
    bb = np.asarray(b, dtype=float)
    if aa.shape != bb.shape:
        raise ValueError(f"shape mismatch: {aa.shape} vs {bb.shape}")
    if aa.size == 0:
        return (float("nan"), float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    n = aa.size
    diffs = np.empty(n_iters)
    for i in range(n_iters):
        idx = rng.integers(0, n, size=n)
        diffs[i] = aa[idx].mean() - bb[idx].mean()
    alpha = (1.0 - ci) / 2.0
    lo = float(np.quantile(diffs, alpha))
    hi = float(np.quantile(diffs, 1.0 - alpha))
    return (float(aa.mean() - bb.mean()), lo, hi)


def bootstrap_ci_bca(
    values: Sequence[float],
    *,
    n_iters: int = 1000,
    ci: float = 0.95,
    seed: int = 0,
) -> tuple[float, float, float]:
    """BCa (bias-corrected & accelerated) bootstrap CI for the mean.

    More accurate than percentile when the bootstrap distribution is skewed
    or when the metric is bounded near 0/1 (citation P/R/F1, faithfulness
    scores). 2025-2026 RAG-eval reviewer default for small-N inferences.

    Falls back to NaN on degenerate inputs (e.g., all values identical →
    acceleration term is NaN).

    Returns:
        (mean, lower, upper).
    """
    arr = np.asarray(values, dtype=float)
    if arr.size < 2:
        return (float(arr.mean()) if arr.size else float("nan"),
                float("nan"), float("nan"))
    if np.all(arr == arr[0]):
        return (float(arr[0]), float(arr[0]), float(arr[0]))
    rng = np.random.default_rng(seed)
    try:
        res = _sps.bootstrap(
            (arr,), np.mean,
            n_resamples=n_iters,
            confidence_level=ci,
            method="BCa",
            random_state=rng,
        )
        return (float(arr.mean()),
                float(res.confidence_interval.low),
                float(res.confidence_interval.high))
    except (ValueError, RuntimeError):
        # BCa can fail when acceleration is undefined; back off to percentile.
        return bootstrap_ci(values, n_iters=n_iters, ci=ci, seed=seed)


def paired_bootstrap_ci_bca(
    a: Sequence[float],
    b: Sequence[float],
    *,
    n_iters: int = 1000,
    ci: float = 0.95,
    seed: int = 0,
) -> tuple[float, float, float]:
    """Paired BCa CI for mean(a - b).

    Computes the per-pair difference once and bootstraps that. Pairing is
    preserved exactly because we collapse to a 1-D diff array first. Same
    fallback behavior as bootstrap_ci_bca on degenerate inputs.

    Returns:
        (mean_diff, lower, upper).
    """
    aa = np.asarray(a, dtype=float)
    bb = np.asarray(b, dtype=float)
    if aa.shape != bb.shape:
        raise ValueError(f"shape mismatch: {aa.shape} vs {bb.shape}")
    if aa.size < 2:
        return (float((aa - bb).mean()) if aa.size else float("nan"),
                float("nan"), float("nan"))
    diff = aa - bb
    if np.all(diff == diff[0]):
        return (float(diff[0]), float(diff[0]), float(diff[0]))
    rng = np.random.default_rng(seed)
    try:
        res = _sps.bootstrap(
            (diff,), np.mean,
            n_resamples=n_iters,
            confidence_level=ci,
            method="BCa",
            random_state=rng,
        )
        return (float(diff.mean()),
                float(res.confidence_interval.low),
                float(res.confidence_interval.high))
    except (ValueError, RuntimeError):
        return paired_bootstrap_ci(a, b, n_iters=n_iters, ci=ci, seed=seed)


def paired_permutation_test(
    a: Sequence[float],
    b: Sequence[float],
    *,
    n_perms: int = 10000,
    seed: int = 0,
    alternative: str = "two-sided",
) -> float:
    """Paired permutation test on (a - b). Returns p-value.

    Null: mean(a - b) == 0. Permutes the sign of each pair's difference
    independently, measures how often the permuted mean is at least as
    extreme as the observed mean.

    alternative: 'two-sided' (default), 'greater' (a > b), 'less' (a < b).
    """
    aa = np.asarray(a, dtype=float)
    bb = np.asarray(b, dtype=float)
    if aa.shape != bb.shape:
        raise ValueError(f"shape mismatch: {aa.shape} vs {bb.shape}")
    n = aa.size
    if n == 0:
        return float("nan")
    diff = aa - bb
    obs = float(diff.mean())
    rng = np.random.default_rng(seed)
    # Vectorized permutation: each row is a sign pattern
    signs = rng.choice([-1.0, 1.0], size=(n_perms, n))
    perm_means = (signs * diff).mean(axis=1)
    if alternative == "two-sided":
        extreme = np.abs(perm_means) >= abs(obs)
    elif alternative == "greater":
        extreme = perm_means >= obs
    elif alternative == "less":
        extreme = perm_means <= obs
    else:
        raise ValueError(f"unknown alternative: {alternative!r}")
    # +1 in numerator and denominator: standard permutation-test smoothing
    p = (1.0 + float(extreme.sum())) / (1.0 + n_perms)
    return p


def bonferroni_correct(p_values: Sequence[float]) -> list[float]:
    """Bonferroni: multiply each p-value by the number of comparisons (capped at 1)."""
    n = len(p_values)
    if n == 0:
        return []
    return [min(1.0, p * n) for p in p_values]


def holm_correct(p_values: Sequence[float]) -> list[float]:
    """Holm-Bonferroni step-down. Less conservative than Bonferroni, still FWER-controlled."""
    n = len(p_values)
    if n == 0:
        return []
    order = sorted(range(n), key=lambda i: p_values[i])
    adj = [0.0] * n
    running_max = 0.0
    for rank, i in enumerate(order):
        # Holm factor: (n - rank) for i-th smallest
        adj_p = min(1.0, p_values[i] * (n - rank))
        # Step-down: monotonic non-decreasing in original-sort order
        running_max = max(running_max, adj_p)
        adj[i] = running_max
    return adj


def cohens_d(a: Sequence[float], b: Sequence[float]) -> float:
    """Cohen's d for two independent samples (pooled SD).

    For paired samples, use cohens_d_paired (this fn ignores pairing).
    Conventional benchmarks: 0.2 small, 0.5 medium, 0.8 large.
    """
    aa = np.asarray(a, dtype=float)
    bb = np.asarray(b, dtype=float)
    if aa.size < 2 or bb.size < 2:
        return float("nan")
    mean_diff = aa.mean() - bb.mean()
    pooled_var = ((aa.size - 1) * aa.var(ddof=1)
                  + (bb.size - 1) * bb.var(ddof=1)) / (aa.size + bb.size - 2)
    if pooled_var <= 0:
        return float("nan")
    return float(mean_diff / math.sqrt(pooled_var))


def cohens_d_paired(a: Sequence[float], b: Sequence[float]) -> float:
    """Cohen's d for paired samples (uses SD of within-pair differences)."""
    aa = np.asarray(a, dtype=float)
    bb = np.asarray(b, dtype=float)
    if aa.shape != bb.shape:
        raise ValueError(f"shape mismatch: {aa.shape} vs {bb.shape}")
    if aa.size < 2:
        return float("nan")
    diff = aa - bb
    sd = float(diff.std(ddof=1))
    if sd <= 0:
        return float("nan")
    return float(diff.mean() / sd)


# =============================================================================
# CLI smoke test
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    # Synthetic example: pipeline B is on average 0.10 better than A
    # (faithfulness scale 0..1), correlated within query.
    n = 100
    a = rng.beta(8, 2, size=n)              # mean ~0.80
    b = a + 0.10 + rng.normal(0, 0.05, n)   # paired, slight noise
    b = np.clip(b, 0, 1)

    print(f"Sample size: {n}")
    print(f"  A mean: {a.mean():.4f}")
    print(f"  B mean: {b.mean():.4f}")
    print()

    m_a, lo_a, hi_a = bootstrap_ci(a, seed=args.seed)
    m_b, lo_b, hi_b = bootstrap_ci(b, seed=args.seed)
    print(f"Bootstrap 95% CI on A (percentile): {m_a:.4f}  [{lo_a:.4f}, {hi_a:.4f}]")
    print(f"Bootstrap 95% CI on B (percentile): {m_b:.4f}  [{lo_b:.4f}, {hi_b:.4f}]")

    m_a2, lo_a2, hi_a2 = bootstrap_ci_bca(a, seed=args.seed)
    m_b2, lo_b2, hi_b2 = bootstrap_ci_bca(b, seed=args.seed)
    print(f"Bootstrap 95% CI on A (BCa):        {m_a2:.4f}  [{lo_a2:.4f}, {hi_a2:.4f}]")
    print(f"Bootstrap 95% CI on B (BCa):        {m_b2:.4f}  [{lo_b2:.4f}, {hi_b2:.4f}]")

    md, lo, hi = paired_bootstrap_ci(b, a, seed=args.seed)
    print(f"\nPaired bootstrap 95% CI on (B - A) percentile: {md:.4f}  [{lo:.4f}, {hi:.4f}]")
    md2, lo2, hi2 = paired_bootstrap_ci_bca(b, a, seed=args.seed)
    print(f"Paired bootstrap 95% CI on (B - A) BCa:        {md2:.4f}  [{lo2:.4f}, {hi2:.4f}]")

    p2 = paired_permutation_test(b, a, seed=args.seed, alternative="two-sided")
    p_g = paired_permutation_test(b, a, seed=args.seed, alternative="greater")
    print(f"\nPaired permutation test  p (two-sided): {p2:.4g}")
    print(f"Paired permutation test  p (greater):   {p_g:.4g}")

    d = cohens_d(b, a)
    d_p = cohens_d_paired(b, a)
    print(f"\nCohen's d (independent): {d:.3f}")
    print(f"Cohen's d (paired):      {d_p:.3f}")

    # Multiple-comparison demo with synthetic p-values
    raw_ps = [0.01, 0.02, 0.04, 0.20]
    print(f"\nRaw p-values:            {raw_ps}")
    print(f"Bonferroni-corrected:    {bonferroni_correct(raw_ps)}")
    print(f"Holm-corrected:          {holm_correct(raw_ps)}")

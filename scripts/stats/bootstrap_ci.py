#!/usr/bin/env python
"""STEP 1a: BCa bootstrap CIs for per-stratum citation F1 + paired pairwise deltas.

Reads results/main-v2-scored.csv (4440 rows). Averages over the 3 repeats per
(query, pipeline) before bootstrap. RNG seed = 20260511.

Outputs:
  results/stats/per_stratum_f1_ci.csv   (stratum, pipeline, n, mean, ci_lo, ci_hi)
  results/stats/pairwise_delta_ci.csv   (stratum, pipeline_i, pipeline_j, n_paired,
                                         mean_delta, delta_ci_lo, delta_ci_hi,
                                         ci_excludes_zero)
"""
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import bootstrap

ROOT = Path(__file__).resolve().parents[2]
SCORED = Path(os.environ.get("SCORED_CSV") or str(ROOT / "results" / "main-v2-scored.csv"))
OUT = Path(os.environ.get("STATS_OUT") or str(ROOT / "results" / "stats"))
SEED = 20260511
B = 1000
PIPELINES = ["vanilla", "agentic", "agentic-graph", "graphrag", "adaptive"]
STRATA = ["1-hop", "2-hop", "3+-hop"]


def per_query_mean(df: pd.DataFrame) -> pd.DataFrame:
    """Average over the 3 repeats per (query, pipeline). Returns long-form."""
    return (
        df.groupby(["query", "pipeline", "query_type"])["citation_f1"]
        .mean()
        .reset_index()
    )


def bca_mean_ci(arr: np.ndarray, seed: int):
    """BCa CI for the mean of arr. Falls back to percentile if BCa fails."""
    if len(arr) < 2:
        return None, None, "n<2"
    if np.allclose(arr, arr[0]):
        return None, None, "constant"
    rng = np.random.default_rng(seed)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = bootstrap((arr,), np.mean, n_resamples=B,
                            method="BCa", random_state=rng)
        return float(res.confidence_interval.low), float(res.confidence_interval.high), "BCa"
    except Exception:
        try:
            rng = np.random.default_rng(seed)
            res = bootstrap((arr,), np.mean, n_resamples=B,
                            method="percentile", random_state=rng)
            return float(res.confidence_interval.low), float(res.confidence_interval.high), "percentile-fallback"
        except Exception as e:
            return None, None, f"failed:{type(e).__name__}"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(SCORED)
    pq = per_query_mean(df)

    # 1) Per-(stratum, pipeline) mean F1 + BCa CI
    rows = []
    for s in STRATA:
        for p in PIPELINES:
            arr = pq.loc[(pq["query_type"] == s) & (pq["pipeline"] == p), "citation_f1"].values
            mean = float(arr.mean()) if len(arr) else None
            lo, hi, method = bca_mean_ci(arr, SEED)
            rows.append({
                "stratum": s, "pipeline": p, "n": int(len(arr)),
                "mean": mean, "ci_lo": lo, "ci_hi": hi, "ci_method": method,
            })
    pd.DataFrame(rows).to_csv(OUT / "per_stratum_f1_ci.csv", index=False)

    # 2) Paired pairwise deltas with BCa CI on the mean delta
    pairs = [(p1, p2) for i, p1 in enumerate(PIPELINES) for p2 in PIPELINES[i + 1:]]
    assert len(pairs) == 10, f"expected 10 pairs, got {len(pairs)}"

    rows = []
    for s in STRATA:
        wide = (pq[pq["query_type"] == s]
                .pivot(index="query", columns="pipeline", values="citation_f1"))
        for p1, p2 in pairs:
            if p1 not in wide.columns or p2 not in wide.columns:
                rows.append({"stratum": s, "pipeline_i": p1, "pipeline_j": p2,
                             "n_paired": 0, "mean_delta": None,
                             "delta_ci_lo": None, "delta_ci_hi": None,
                             "ci_method": "missing-pipeline", "ci_excludes_zero": False})
                continue
            both = wide[[p1, p2]].dropna()
            d = (both[p1] - both[p2]).values
            lo, hi, method = bca_mean_ci(d, SEED + hash((s, p1, p2)) % 100000)
            mean_d = float(d.mean()) if len(d) else None
            excludes = bool(lo is not None and hi is not None and (lo > 0 or hi < 0))
            rows.append({
                "stratum": s, "pipeline_i": p1, "pipeline_j": p2,
                "n_paired": int(len(d)), "mean_delta": mean_d,
                "delta_ci_lo": lo, "delta_ci_hi": hi,
                "ci_method": method, "ci_excludes_zero": excludes,
            })
    pd.DataFrame(rows).to_csv(OUT / "pairwise_delta_ci.csv", index=False)

    print(f"wrote {OUT / 'per_stratum_f1_ci.csv'}")
    print(f"wrote {OUT / 'pairwise_delta_ci.csv'}")


if __name__ == "__main__":
    main()

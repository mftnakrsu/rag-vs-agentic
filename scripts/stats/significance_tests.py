#!/usr/bin/env python
"""STEP 1b: paired Wilcoxon + Holm (over family of 30) + Cliff's delta.

Significant := (BCa CI excludes 0) AND (holm_p < 0.05) AND (|cliffs_delta| >= 0.147).

Outputs:
  results/stats/significance_matrix.csv
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from statsmodels.stats.multitest import multipletests

ROOT = Path(__file__).resolve().parents[2]
SCORED = Path(os.environ.get("SCORED_CSV") or str(ROOT / "results" / "main-v2-scored.csv"))
OUT = Path(os.environ.get("STATS_OUT") or str(ROOT / "results" / "stats"))
PIPELINES = ["vanilla", "agentic", "agentic-graph", "graphrag", "adaptive"]
STRATA = ["1-hop", "2-hop", "3+-hop"]


def cliffs_delta(x, y) -> float:
    """Vectorized Cliff's delta. d in [-1, 1]. Macbeth 2011 thresholds."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) == 0 or len(y) == 0:
        return float("nan")
    diff_signs = np.sign(x[:, None] - y[None, :])
    return float(diff_signs.mean())


def cliffs_magnitude(d: float) -> str:
    if d is None or np.isnan(d):
        return "n/a"
    a = abs(d)
    if a < 0.147:
        return "negligible"
    if a < 0.33:
        return "small"
    if a < 0.474:
        return "medium"
    return "large"


def per_query_mean(df: pd.DataFrame) -> pd.DataFrame:
    return (df.groupby(["query", "pipeline", "query_type"])["citation_f1"]
              .mean().reset_index())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(SCORED)
    pq = per_query_mean(df)

    pairs = [(p1, p2) for i, p1 in enumerate(PIPELINES) for p2 in PIPELINES[i + 1:]]
    assert len(pairs) == 10

    raw = []
    for s in STRATA:
        wide = (pq[pq["query_type"] == s]
                .pivot(index="query", columns="pipeline", values="citation_f1"))
        for p1, p2 in pairs:
            both = wide[[p1, p2]].dropna() if (p1 in wide.columns and p2 in wide.columns) else pd.DataFrame()
            if len(both) < 2 or (both[p1] == both[p2]).all():
                w_p = float("nan")
            else:
                try:
                    _, w_p = wilcoxon(both[p1].values, both[p2].values,
                                       zero_method="wilcox", alternative="two-sided")
                except ValueError:
                    w_p = float("nan")
            x = wide[p1].dropna().values if p1 in wide.columns else np.array([])
            y = wide[p2].dropna().values if p2 in wide.columns else np.array([])
            d = cliffs_delta(x, y)
            raw.append({
                "stratum": s, "pipeline_i": p1, "pipeline_j": p2,
                "n_paired": int(len(both)),
                "mean_delta": float((both[p1] - both[p2]).mean()) if len(both) else None,
                "wilcoxon_p": float(w_p) if not np.isnan(w_p) else None,
                "cliffs_delta": float(d) if not np.isnan(d) else None,
                "cliffs_delta_magnitude": cliffs_magnitude(d),
            })

    out = pd.DataFrame(raw)

    # Holm over the family of 30 (handle NaN p-values gracefully)
    pvals = out["wilcoxon_p"].fillna(1.0).values
    valid_mask = ~out["wilcoxon_p"].isna().values
    holm_p = np.full(len(out), float("nan"))
    if valid_mask.any():
        _, holm_corrected, _, _ = multipletests(pvals[valid_mask], alpha=0.05, method="holm")
        holm_p[valid_mask] = holm_corrected
    out["holm_p"] = holm_p
    # Note: family-size = 30 enforced because we have exactly 30 valid tests typically;
    # if some Wilcoxon fail, multipletests still uses the *number passed in* as family.
    # Document this in output.
    out["holm_family_size"] = int(valid_mask.sum())

    # Merge BCa "ci_excludes_zero" from pairwise_delta_ci.csv
    bca = pd.read_csv(OUT / "pairwise_delta_ci.csv")
    out = out.merge(
        bca[["stratum", "pipeline_i", "pipeline_j", "delta_ci_lo", "delta_ci_hi", "ci_excludes_zero"]],
        on=["stratum", "pipeline_i", "pipeline_j"], how="left",
    )

    out["significant"] = (
        out["ci_excludes_zero"].fillna(False).astype(bool)
        & (out["holm_p"].fillna(1.0) < 0.05)
        & (out["cliffs_delta"].abs() >= 0.147)
    )

    out.to_csv(OUT / "significance_matrix.csv", index=False)
    print(f"wrote {OUT / 'significance_matrix.csv'}")
    print(f"  significant: {int(out['significant'].sum())}/{len(out)} of 30 tests")
    print("  per-stratum significant counts:")
    for s in STRATA:
        print(f"    {s}: {int(out[(out['stratum'] == s) & out['significant']].shape[0])}/10")


if __name__ == "__main__":
    main()

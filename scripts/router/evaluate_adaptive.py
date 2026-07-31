#!/usr/bin/env python
"""STEP 2d/2e: construct adaptive_v1 / adaptive_v2 / adaptive_oracle rows
and run the V2 acceptance check.

Acceptance criteria (PLAN §2e):
  CHECK 1: V2 overall mean F1 >= V1 + 0.02 (2 absolute pts)
  CHECK 2: Holm-adj Wilcoxon (one-sided V2 > V1) p < 0.05 in >= 2/3 strata
  CHECK 3: V2 closes >= 30% of (oracle - V1) gap overall

Outputs:
  results/stats/adaptive_comparison.csv
  results/router/v2_acceptance.txt
"""
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import bootstrap, wilcoxon
from statsmodels.stats.multitest import multipletests

ROOT = Path(__file__).resolve().parents[2]
SCORED = Path(os.environ.get("SCORED_CSV") or str(ROOT / "results" / "main-v2-scored.csv"))
V2_ROUTES = Path(os.environ.get("OOF_ROUTES_CSV") or str(ROOT / "data" / "router" / "v2_oof_routes.csv"))
ORACLE_ROUTES = Path(os.environ.get("ORACLE_ROUTES_CSV") or str(ROOT / "data" / "router" / "oracle_routes.csv"))
OUT_COMP = Path(os.environ.get("ADAPTIVE_COMP_CSV") or str(ROOT / "results" / "stats" / "adaptive_comparison.csv"))
OUT_ACCEPT = Path(os.environ.get("ACCEPT_TXT") or str(ROOT / "results" / "router" / "v2_acceptance.txt"))
SEED = 20260511
B = 1000
STRATA = ["1-hop", "2-hop", "3+-hop"]


def per_query_mean(df: pd.DataFrame) -> pd.DataFrame:
    return (df.groupby(["query", "pipeline", "query_type"])["citation_f1"]
              .mean().reset_index())


def bca_mean_ci(arr, seed):
    if len(arr) < 2 or np.allclose(arr, arr[0]):
        return None, None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = bootstrap((arr,), np.mean, n_resamples=B, method="BCa",
                            random_state=np.random.default_rng(seed))
        return float(res.confidence_interval.low), float(res.confidence_interval.high)
    except Exception:
        return None, None


def main():
    df = pd.read_csv(SCORED)
    pq = per_query_mean(df)

    # V1: existing 'adaptive' pipeline rows in the matrix
    v1 = (pq[pq["pipeline"] == "adaptive"]
          [["query", "query_type", "citation_f1"]]
          .rename(columns={"citation_f1": "v1_f1"}))

    # V2: lookup recommended_pipeline per query, fetch its F1 from matrix
    v2_routes = pd.read_csv(V2_ROUTES)[["query", "recommended_pipeline"]]
    v2 = v2_routes.merge(pq, left_on=["query"], right_on=["query"], how="inner")
    v2 = v2[v2["pipeline"] == v2["recommended_pipeline"]][
        ["query", "query_type", "citation_f1"]
    ].rename(columns={"citation_f1": "v2_f1"}).drop_duplicates(subset=["query"])

    # Oracle
    oracle = pd.read_csv(ORACLE_ROUTES)[["query", "query_type", "oracle_f1"]]

    # Merge
    merged = v1.merge(v2, on=["query", "query_type"]).merge(
        oracle, on=["query", "query_type"]
    )
    n_total = len(merged)
    print(f"merged variants over {n_total} queries")

    # Per-stratum + overall stats per variant
    rows = []
    for variant_col, variant_name in [("v1_f1", "adaptive_v1"),
                                       ("v2_f1", "adaptive_v2"),
                                       ("oracle_f1", "adaptive_oracle")]:
        for s in STRATA + ["overall"]:
            arr = (merged[variant_col].values if s == "overall"
                   else merged.loc[merged["query_type"] == s, variant_col].values)
            if len(arr) == 0:
                continue
            mean = float(arr.mean())
            lo, hi = bca_mean_ci(arr, SEED + abs(hash((variant_name, s))) % 100000)
            rows.append({
                "variant": variant_name, "stratum": s, "n": int(len(arr)),
                "mean_f1": mean, "ci_lo": lo, "ci_hi": hi,
            })
    pd.DataFrame(rows).to_csv(OUT_COMP, index=False)

    # Acceptance check
    out_lines = []
    a = out_lines.append
    a("V2 Router Acceptance Check")
    a("==========================")
    a("")
    a(f"N queries (paired, all 3 variants present): {n_total}")
    a("")

    overall_v1 = float(merged["v1_f1"].mean())
    overall_v2 = float(merged["v2_f1"].mean())
    overall_oracle = float(merged["oracle_f1"].mean())
    overall_diff = overall_v2 - overall_v1
    a(f"V1 overall mean F1:     {overall_v1:.4f}")
    a(f"V2 overall mean F1:     {overall_v2:.4f}")
    a(f"Oracle overall mean F1: {overall_oracle:.4f}")
    a(f"V2 - V1:                {overall_diff:+.4f}")
    a(f"Oracle - V1 gap:        {overall_oracle - overall_v1:+.4f}")
    a("")

    # CHECK 1
    threshold_pp = 0.02  # "2.0 absolute F1 points" = 0.02
    check1 = overall_diff >= threshold_pp
    a(f"CHECK 1: V2 - V1 >= {threshold_pp:.2f}: "
      f"{'PASS' if check1 else 'FAIL'} (got {overall_diff:+.4f})")

    # CHECK 2: per-stratum Wilcoxon (one-sided V2 > V1) + Holm
    pvals, diffs = [], []
    for s in STRATA:
        sub = merged[merged["query_type"] == s]
        x, y = sub["v2_f1"].values, sub["v1_f1"].values
        diffs.append(float((x - y).mean()))
        if len(sub) < 2 or np.allclose(x, y):
            pvals.append(1.0)
            continue
        try:
            _, p = wilcoxon(x, y, alternative="greater", zero_method="wilcox")
            pvals.append(float(p))
        except ValueError:
            pvals.append(1.0)
    _, holm_p, _, _ = multipletests(pvals, alpha=0.05, method="holm")
    n_sig = int((holm_p < 0.05).sum())
    check2 = n_sig >= 2
    a("")
    a(f"CHECK 2: Holm-adj Wilcoxon (V2>V1) p<0.05 in >=2/3 strata: "
      f"{'PASS' if check2 else 'FAIL'} ({n_sig}/3 strata)")
    for s, d, p, hp in zip(STRATA, diffs, pvals, holm_p):
        a(f"  {s:7s}: V2-V1 mean={d:+.4f}, raw_p={p:.4g}, holm_p={hp:.4g}")

    # CHECK 3: 30% gap closure
    gap = overall_oracle - overall_v1
    if gap <= 0:
        gap_closed = float("inf") if overall_diff > 0 else 0.0
    else:
        gap_closed = overall_diff / gap
    check3 = gap_closed >= 0.30
    a("")
    a(f"CHECK 3: V2 closes >= 30% of (oracle - V1) gap overall: "
      f"{'PASS' if check3 else 'FAIL'} (closed {gap_closed * 100:.1f}%)")
    a(f"  (V2 - V1) / (Oracle - V1) = {overall_diff:+.4f} / {gap:+.4f}")

    a("")
    all_pass = check1 and check2 and check3
    verdict = "V2_ACCEPTANCE_PASS" if all_pass else "V2_ACCEPTANCE_FAIL"
    a(f"OVERALL: {verdict}")
    a("")
    a("Per-stratum mean F1 (paired, n=296):")
    for s in STRATA:
        sub = merged[merged["query_type"] == s]
        a(f"  {s:7s}: V1={sub['v1_f1'].mean():.4f}  V2={sub['v2_f1'].mean():.4f}  "
          f"Oracle={sub['oracle_f1'].mean():.4f}  (n={len(sub)})")

    OUT_ACCEPT.parent.mkdir(parents=True, exist_ok=True)
    OUT_ACCEPT.write_text("\n".join(out_lines))
    print(f"wrote {OUT_COMP}")
    print(f"wrote {OUT_ACCEPT}")
    print("---")
    print("\n".join(out_lines))


if __name__ == "__main__":
    main()

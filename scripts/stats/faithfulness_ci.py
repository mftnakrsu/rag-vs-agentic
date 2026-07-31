#!/usr/bin/env python
"""STEP 1c: BCa CIs for faithful% per (pipeline, stratum, judge) +
agreement statistics (Cohen's kappa, Gwet's AC1, raw agreement, McNemar,
Spearman rho on per-pipeline faithful%).

Reads results/main-v2-judged.csv (300 rows; Gemini column is 100% null,
so 2-judge effective).

Outputs:
  results/stats/faithfulness_ci.csv  (stratum, pipeline, judge, n,
                                      faithful_pct, ci_lo, ci_hi, ci_method)
  results/stats/judge_agreement.csv  (slice_type, slice, n, gpt5_pct, gpt41_pct,
                                      raw_agreement, cohens_kappa, gwets_ac1,
                                      mcnemar_p, spearman_rho_per_pipeline,
                                      spearman_p)
"""
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest, bootstrap, spearmanr

ROOT = Path(__file__).resolve().parents[2]
JUDGED = Path(os.environ.get("JUDGED_CSV") or str(ROOT / "results" / "main-v2-judged.csv"))
OUT = Path(os.environ.get("STATS_OUT") or str(ROOT / "results" / "stats"))
SEED = 20260511
B = 1000
PIPELINES = ["vanilla", "agentic", "agentic-graph", "graphrag", "adaptive"]
STRATA = ["1-hop", "2-hop", "3+-hop"]
JUDGES = {"gpt5": "judge_gpt5_faithful", "gpt41": "judge_gpt41_faithful"}


def cohens_kappa(r1, r2):
    r1 = np.asarray(r1).astype(int)
    r2 = np.asarray(r2).astype(int)
    if len(r1) == 0:
        return np.nan, np.nan
    po = (r1 == r2).mean()
    p1, p2 = r1.mean(), r2.mean()
    pe = p1 * p2 + (1 - p1) * (1 - p2)
    if pe >= 1.0:
        return np.nan, po
    return (po - pe) / (1 - pe), po


def gwet_ac1(r1, r2):
    r1 = np.asarray(r1).astype(int)
    r2 = np.asarray(r2).astype(int)
    if len(r1) == 0:
        return np.nan
    po = (r1 == r2).mean()
    pi = (r1.mean() + r2.mean()) / 2
    pe_g = 2 * pi * (1 - pi)
    if pe_g >= 1.0:
        return np.nan
    return (po - pe_g) / (1 - pe_g)


def mcnemar_p(r1, r2):
    r1 = np.asarray(r1).astype(int)
    r2 = np.asarray(r2).astype(int)
    b = int(((r1 == 1) & (r2 == 0)).sum())
    c = int(((r1 == 0) & (r2 == 1)).sum())
    if b + c == 0:
        return np.nan
    return float(binomtest(min(b, c), n=b + c, p=0.5, alternative="two-sided").pvalue)


def bca_mean_ci(arr, seed):
    """BCa for mean. Falls back to percentile when BCa is degenerate (constant arr)."""
    if len(arr) < 5:
        return None, None, "n<5"
    if np.allclose(arr, arr[0]):
        return float(arr[0]), float(arr[0]), "constant"
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
    df = pd.read_csv(JUDGED)
    df["judge_gpt5_faithful"] = df["judge_gpt5_faithful"].astype(bool)
    df["judge_gpt41_faithful"] = df["judge_gpt41_faithful"].astype(bool)

    # 1) faithfulness_ci.csv
    rows = []
    for s in STRATA:
        for p in PIPELINES:
            sub = df[(df["query_type"] == s) & (df["pipeline"] == p)]
            for jname, jcol in JUDGES.items():
                arr = sub[jcol].astype(int).values
                mean = float(arr.mean()) if len(arr) else None
                lo, hi, method = bca_mean_ci(arr, SEED + hash((s, p, jname)) % 100000)
                rows.append({
                    "stratum": s, "pipeline": p, "judge": jname,
                    "n": int(len(arr)), "faithful_pct": mean,
                    "ci_lo": lo, "ci_hi": hi, "ci_method": method,
                })
    pd.DataFrame(rows).to_csv(OUT / "faithfulness_ci.csv", index=False)

    # 2) judge_agreement.csv: per-stratum + overall + per-pipeline
    rows = []

    def agg_row(slice_type, slice_label, sub):
        r1 = sub["judge_gpt5_faithful"].values
        r2 = sub["judge_gpt41_faithful"].values
        k, po = cohens_kappa(r1, r2)
        return {
            "slice_type": slice_type, "slice": slice_label,
            "n": int(len(sub)),
            "gpt5_faithful_pct": float(np.asarray(r1).astype(int).mean()) if len(sub) else None,
            "gpt41_faithful_pct": float(np.asarray(r2).astype(int).mean()) if len(sub) else None,
            "raw_agreement": float(po) if not np.isnan(po) else None,
            "cohens_kappa": float(k) if not np.isnan(k) else None,
            "gwets_ac1": float(gwet_ac1(r1, r2)) if not np.isnan(gwet_ac1(r1, r2)) else None,
            "mcnemar_p": mcnemar_p(r1, r2),
        }

    for s in STRATA:
        rows.append(agg_row("stratum", s, df[df["query_type"] == s]))
    rows.append(agg_row("overall", "overall", df))
    for p in PIPELINES:
        rows.append(agg_row("pipeline", p, df[df["pipeline"] == p]))

    # Spearman rho per stratum (across the 5 pipelines) + overall
    spearman_by_slice = {}
    for s in STRATA + ["overall"]:
        mask = df["query_type"] == s if s != "overall" else pd.Series([True] * len(df), index=df.index)
        rates = []
        for p in PIPELINES:
            sub = df[mask & (df["pipeline"] == p)]
            if len(sub) == 0:
                continue
            rates.append({
                "pipeline": p,
                "g5": float(sub["judge_gpt5_faithful"].astype(int).mean()),
                "g41": float(sub["judge_gpt41_faithful"].astype(int).mean()),
            })
        rdf = pd.DataFrame(rates)
        if len(rdf) >= 3 and rdf["g5"].nunique() >= 2 and rdf["g41"].nunique() >= 2:
            rho, pv = spearmanr(rdf["g5"], rdf["g41"])
            spearman_by_slice[s] = (
                float(rho) if not np.isnan(rho) else None,
                float(pv) if not np.isnan(pv) else None,
            )
        else:
            spearman_by_slice[s] = (None, None)

    for r in rows:
        if r["slice_type"] in ("stratum", "overall") and r["slice"] in spearman_by_slice:
            r["spearman_rho_per_pipeline"], r["spearman_p"] = spearman_by_slice[r["slice"]]
        else:
            r["spearman_rho_per_pipeline"] = None
            r["spearman_p"] = None

    pd.DataFrame(rows).to_csv(OUT / "judge_agreement.csv", index=False)
    print(f"wrote {OUT / 'faithfulness_ci.csv'}")
    print(f"wrote {OUT / 'judge_agreement.csv'}")


if __name__ == "__main__":
    main()

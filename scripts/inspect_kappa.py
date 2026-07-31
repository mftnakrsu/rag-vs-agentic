#!/usr/bin/env python
"""Read-only inspection of multi-judge agreement on results/main-v2-judged.csv.

Computes per-pipeline + per-stratum Cohen's kappa AND Gwet's AC1, the
GPT-5.4 x GPT-4.1 confusion matrix (overall and sliced), per-(stratum,
pipeline) faithfulness rates per judge, and Spearman rho between the
two judges' per-cell vectors.

Outputs (all NEW files, no existing data touched):
  results/kappa_per_pipeline.json
  results/kappa_per_stratum.json
  results/judge_confusion.csv
  results/kappa_inspection.md
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, binomtest

ROOT = Path(__file__).resolve().parents[1]
JUDGED = ROOT / "results" / "main-v2-judged.csv"
OUT = ROOT / "results"

J1 = "judge_gpt5_faithful"   # GPT-5.4
J2 = "judge_gpt41_faithful"  # GPT-4.1
STRATA = ["1-hop", "2-hop", "3+-hop"]


def cohens_kappa(r1, r2):
    r1 = np.asarray(r1).astype(int)
    r2 = np.asarray(r2).astype(int)
    if len(r1) == 0:
        return np.nan, np.nan, np.nan
    po = (r1 == r2).mean()
    p1, p2 = r1.mean(), r2.mean()
    pe = p1 * p2 + (1 - p1) * (1 - p2)
    if pe >= 1.0:
        return np.nan, po, pe
    return (po - pe) / (1 - pe), po, pe


def gwet_ac1(r1, r2):
    """Gwet's AC1, 2 raters, binary. Robust to class skew (kappa paradox)."""
    r1 = np.asarray(r1).astype(int)
    r2 = np.asarray(r2).astype(int)
    if len(r1) == 0:
        return np.nan
    po = (r1 == r2).mean()
    pi = (r1.mean() + r2.mean()) / 2
    pe_g = 2 * pi * (1 - pi)  # q=2 categories
    if pe_g >= 1.0:
        return np.nan
    return (po - pe_g) / (1 - pe_g)


def confusion(r1, r2):
    r1 = np.asarray(r1).astype(int)
    r2 = np.asarray(r2).astype(int)
    return {
        "tt": int(((r1 == 1) & (r2 == 1)).sum()),
        "tf": int(((r1 == 1) & (r2 == 0)).sum()),
        "ft": int(((r1 == 0) & (r2 == 1)).sum()),
        "ff": int(((r1 == 0) & (r2 == 0)).sum()),
    }


def cell_stats(sub, label):
    r1, r2 = sub[J1].values, sub[J2].values
    k, po, pe = cohens_kappa(r1, r2)
    return {
        "label": label,
        "n": int(len(sub)),
        "gpt5_faithful_rate": float(np.asarray(r1).astype(int).mean()) if len(sub) else None,
        "gpt41_faithful_rate": float(np.asarray(r2).astype(int).mean()) if len(sub) else None,
        "observed_agreement": float(po) if not np.isnan(po) else None,
        "pe_cohen": float(pe) if not np.isnan(pe) else None,
        "cohens_kappa": float(k) if not np.isnan(k) else None,
        "gwets_ac1": float(gwet_ac1(r1, r2)) if len(sub) else None,
        "confusion_gpt5_x_gpt41": confusion(r1, r2),
    }


def fmt(v, p=3):
    return "n/a" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:.{p}f}"


def main():
    df = pd.read_csv(JUDGED)
    assert df[J1].notna().all() and df[J2].notna().all(), "judge cols have nulls"
    df[J1] = df[J1].astype(bool)
    df[J2] = df[J2].astype(bool)

    overall = cell_stats(df, "overall")
    per_pipeline = {p: cell_stats(sub, f"pipeline={p}") for p, sub in df.groupby("pipeline")}
    per_stratum = {s: cell_stats(sub, f"stratum={s}") for s, sub in df.groupby("query_type")}

    # Per-(stratum, pipeline) cell rates
    cell_rates = []
    for (s, p), sub in df.groupby(["query_type", "pipeline"]):
        cell_rates.append({
            "stratum": s,
            "pipeline": p,
            "n": int(len(sub)),
            "gpt5_rate": float(sub[J1].mean()),
            "gpt41_rate": float(sub[J2].mean()),
        })
    cells = pd.DataFrame(cell_rates).sort_values(["stratum", "pipeline"]).reset_index(drop=True)

    # Spearman across all 15 cells
    rho_all, p_all = spearmanr(cells["gpt5_rate"], cells["gpt41_rate"])

    # Per-stratum Spearman across the 5 pipelines
    spearman_per_stratum = {}
    for s, sub in cells.groupby("stratum"):
        if sub["gpt5_rate"].nunique() >= 2 and sub["gpt41_rate"].nunique() >= 2:
            r, pv = spearmanr(sub["gpt5_rate"], sub["gpt41_rate"])
            spearman_per_stratum[s] = {
                "rho": None if np.isnan(r) else float(r),
                "p_value": None if np.isnan(pv) else float(pv),
                "n_cells": int(len(sub)),
            }
        else:
            spearman_per_stratum[s] = {"rho": None, "p_value": None, "n_cells": int(len(sub)),
                                       "note": "constant rates in one judge"}

    # Per-pipeline directional check: does each judge show monotonic decrease with hops?
    monotonic_check = {}
    for p in sorted(df["pipeline"].unique()):
        sub = cells[cells["pipeline"] == p].set_index("stratum").reindex(STRATA)
        g5 = sub["gpt5_rate"].tolist()
        g41 = sub["gpt41_rate"].tolist()
        g5_mono = all(g5[i] >= g5[i + 1] for i in range(len(g5) - 1))
        g41_mono = all(g41[i] >= g41[i + 1] for i in range(len(g41) - 1))
        monotonic_check[p] = {
            "gpt5_rates_1h_2h_3h": [float(x) for x in g5],
            "gpt41_rates_1h_2h_3h": [float(x) for x in g41],
            "gpt5_monotonic_decrease": bool(g5_mono),
            "gpt41_monotonic_decrease": bool(g41_mono),
            "both_agree_on_decrease": bool(g5_mono and g41_mono),
        }

    # McNemar exact (binomial) on overall asymmetry
    c_all = overall["confusion_gpt5_x_gpt41"]
    b, c = c_all["tf"], c_all["ft"]
    if b + c > 0:
        bt = binomtest(min(b, c), n=b + c, p=0.5, alternative="two-sided")
        mcnemar_p = float(bt.pvalue)
    else:
        mcnemar_p = None

    # Confusion CSV (per-stratum, per-pipeline, overall)
    rows = []
    for s, sub in df.groupby("query_type"):
        rows.append({"slice": f"stratum={s}", "n": int(len(sub)), **confusion(sub[J1].values, sub[J2].values)})
    for p, sub in df.groupby("pipeline"):
        rows.append({"slice": f"pipeline={p}", "n": int(len(sub)), **confusion(sub[J1].values, sub[J2].values)})
    rows.append({"slice": "overall", "n": int(len(df)), **c_all})
    pd.DataFrame(rows).to_csv(OUT / "judge_confusion.csv", index=False)

    # JSON
    with open(OUT / "kappa_per_pipeline.json", "w") as f:
        json.dump({"overall": overall, "per_pipeline": per_pipeline,
                   "monotonic_check": monotonic_check}, f, indent=2)
    with open(OUT / "kappa_per_stratum.json", "w") as f:
        json.dump({
            "overall": overall,
            "per_stratum": per_stratum,
            "spearman": {
                "rho_overall_15cells": float(rho_all) if not np.isnan(rho_all) else None,
                "p_value": float(p_all) if not np.isnan(p_all) else None,
                "per_stratum_5pipelines": spearman_per_stratum,
            },
            "cell_rates": cells.to_dict(orient="records"),
        }, f, indent=2)

    # Markdown
    md = []
    a = md.append
    a("# Multi-judge κ inspection (GPT-5.4 × GPT-4.1)")
    a("")
    a(f"**N = {len(df)}** judged rows. Gemini column 100% null → 2-judge effective.")
    a("")
    a("## 1. Overall agreement")
    a("")
    a("| metric | value |")
    a("|---|---:|")
    a(f"| n | {overall['n']} |")
    a(f"| GPT-5.4 faithful rate | {fmt(overall['gpt5_faithful_rate'])} |")
    a(f"| GPT-4.1 faithful rate | {fmt(overall['gpt41_faithful_rate'])} |")
    a(f"| Observed agreement P_o | {fmt(overall['observed_agreement'])} |")
    a(f"| Cohen P_e (chance) | {fmt(overall['pe_cohen'])} |")
    a(f"| **Cohen's κ** | **{fmt(overall['cohens_kappa'])}** |")
    a(f"| **Gwet's AC1** | **{fmt(overall['gwets_ac1'])}** |")
    a(f"| McNemar exact p (asymmetry) | {fmt(mcnemar_p, 4)} |")
    a("")
    a("_Kappa-paradox check: if AC1 ≫ κ then class skew is suppressing κ artificially._")
    a("")

    a("## 2. Per-pipeline κ + AC1")
    a("")
    a("| pipeline | n | GPT-5.4 fr | GPT-4.1 fr | P_o | Cohen κ | Gwet AC1 |")
    a("|---|---:|---:|---:|---:|---:|---:|")
    for p in sorted(per_pipeline):
        s = per_pipeline[p]
        a(f"| {p} | {s['n']} | {fmt(s['gpt5_faithful_rate'])} | {fmt(s['gpt41_faithful_rate'])} | "
          f"{fmt(s['observed_agreement'])} | {fmt(s['cohens_kappa'])} | {fmt(s['gwets_ac1'])} |")
    a("")
    a("_Hypothesis: GraphRAG κ should be highest (both judges see the over-citation collapse)._")
    a("")

    a("## 3. Per-stratum κ + AC1")
    a("")
    a("| stratum | n | GPT-5.4 fr | GPT-4.1 fr | P_o | Cohen κ | Gwet AC1 |")
    a("|---|---:|---:|---:|---:|---:|---:|")
    for s_key in STRATA:
        if s_key not in per_stratum:
            continue
        s = per_stratum[s_key]
        a(f"| {s_key} | {s['n']} | {fmt(s['gpt5_faithful_rate'])} | {fmt(s['gpt41_faithful_rate'])} | "
          f"{fmt(s['observed_agreement'])} | {fmt(s['cohens_kappa'])} | {fmt(s['gwets_ac1'])} |")
    a("")
    a("_Hypothesis: 3+-hop κ should be highest (both judges call answers unfaithful)._")
    a("")

    a("## 4. Overall confusion matrix (GPT-5.4 rows × GPT-4.1 cols)")
    a("")
    a("|  | GPT-4.1 ✓ | GPT-4.1 ✗ | row total |")
    a("|---|---:|---:|---:|")
    a(f"| **GPT-5.4 ✓** | {c_all['tt']} | {c_all['tf']} | {c_all['tt']+c_all['tf']} |")
    a(f"| **GPT-5.4 ✗** | {c_all['ft']} | {c_all['ff']} | {c_all['ft']+c_all['ff']} |")
    a(f"| col total | {c_all['tt']+c_all['ft']} | {c_all['tf']+c_all['ff']} | {len(df)} |")
    a("")
    a(f"GPT-5.4-only-faithful (b) = {c_all['tf']}, GPT-4.1-only-faithful (c) = {c_all['ft']}, "
      f"net (b−c) = {c_all['tf']-c_all['ft']}.")
    a(f"Sign of net > 0 means GPT-5.4 is more lenient than GPT-4.1; < 0 means the reverse. "
      f"McNemar exact p = {fmt(mcnemar_p, 4)}.")
    a("")

    a("## 5. Per-(stratum, pipeline) faithfulness rates")
    a("")
    a("| stratum | pipeline | n | GPT-5.4 fr | GPT-4.1 fr | Δ (gpt5−gpt41) |")
    a("|---|---|---:|---:|---:|---:|")
    for r in cells.itertuples(index=False):
        d = r.gpt5_rate - r.gpt41_rate
        a(f"| {r.stratum} | {r.pipeline} | {r.n} | {fmt(r.gpt5_rate)} | {fmt(r.gpt41_rate)} | {d:+.3f} |")
    a("")

    a("## 6. Directional agreement (Spearman ρ)")
    a("")
    rho_str = fmt(rho_all)
    p_str = fmt(p_all, 4)
    a(f"**Overall ρ across 15 (stratum, pipeline) cells:** ρ = **{rho_str}** (p = {p_str})")
    a("")
    a("- ρ near 1 → judges agree on the *ranking* of cells even if levels differ.")
    a("- ρ near 0 → judges disagree on direction; multi-judge methodology fails.")
    a("")
    a("**Per-stratum ρ across 5 pipelines:**")
    a("")
    a("| stratum | ρ | p | n cells |")
    a("|---|---:|---:|---:|")
    for s_key in STRATA:
        if s_key in spearman_per_stratum:
            sp = spearman_per_stratum[s_key]
            a(f"| {s_key} | {fmt(sp.get('rho'))} | {fmt(sp.get('p_value'), 4)} | {sp['n_cells']} |")
    a("")

    a("## 7. Per-pipeline monotonic stratum decline check")
    a("")
    a("Does each judge see faithfulness drop monotonically as hops increase (1-hop ≥ 2-hop ≥ 3+-hop)?")
    a("")
    a("| pipeline | GPT-5.4 (1h, 2h, 3+h) | GPT-4.1 (1h, 2h, 3+h) | both agree on decrease |")
    a("|---|---|---|---|")
    for p, m in monotonic_check.items():
        g5 = ", ".join(f"{x:.2f}" for x in m["gpt5_rates_1h_2h_3h"])
        g41 = ", ".join(f"{x:.2f}" for x in m["gpt41_rates_1h_2h_3h"])
        agree = "✅" if m["both_agree_on_decrease"] else "❌"
        a(f"| {p} | ({g5}) | ({g41}) | {agree} |")
    a("")

    # Anchor verification: GraphRAG 1-hop vs 3+-hop per judge
    g3 = df[(df["pipeline"] == "graphrag") & (df["query_type"] == "3+-hop")]
    g1 = df[(df["pipeline"] == "graphrag") & (df["query_type"] == "1-hop")]
    a("## 8. GraphRAG faithfulness collapse (anchor verification)")
    a("")
    a(f"GraphRAG 1-hop: GPT-5.4 = {g1[J1].mean()*100:.0f}%, GPT-4.1 = {g1[J2].mean()*100:.0f}% (n = {len(g1)})")
    a(f"GraphRAG 3+-hop: GPT-5.4 = {g3[J1].mean()*100:.0f}%, GPT-4.1 = {g3[J2].mean()*100:.0f}% (n = {len(g3)})")
    a("")

    (OUT / "kappa_inspection.md").write_text("\n".join(md))
    print(f"wrote {OUT / 'kappa_inspection.md'}")
    print(f"wrote {OUT / 'kappa_per_pipeline.json'}")
    print(f"wrote {OUT / 'kappa_per_stratum.json'}")
    print(f"wrote {OUT / 'judge_confusion.csv'}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Generate the 3 LaTeX tables from results/stats/*.csv.

Outputs (each is a complete table environment, ready to \\input):
  paper/cikm/tables/table_main.tex
  paper/cikm/tables/table_faithfulness.tex
  paper/cikm/tables/table_agreement.tex
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
STATS = ROOT / "results" / "stats"
SCORED = ROOT / "results" / "main-v2-scored.csv"
OUT = ROOT / "paper" / "cikm" / "tables"

PIPELINES = ["vanilla", "agentic", "agentic-graph", "graphrag", "adaptive"]
STRATA = ["1-hop", "2-hop", "3+-hop"]


def latex_pipeline(p):
    return {
        "adaptive": r"adaptive\_v1",
        "adaptive_v2": r"adaptive\_v2",
        "adaptive_oracle": r"adaptive\_oracle",
    }.get(p, p)


def fmt_cell(mean, lo, hi, bold=False, dagger=False):
    if mean is None or (isinstance(mean, float) and np.isnan(mean)):
        return "---"
    if lo is not None and hi is not None and not (np.isnan(lo) or np.isnan(hi)):
        s = f"{mean:.3f} ({lo:.2f}--{hi:.2f})"
    else:
        s = f"{mean:.3f}"
    if dagger:
        s += r"$^{\dagger}$"
    if bold:
        s = r"\textbf{" + s + "}"
    return s


def table_main():
    f1 = pd.read_csv(STATS / "per_stratum_f1_ci.csv")
    sig = pd.read_csv(STATS / "significance_matrix.csv")
    adapt = pd.read_csv(STATS / "adaptive_comparison.csv")

    df = pd.read_csv(SCORED)
    pq = df.groupby(["query", "pipeline"])["citation_f1"].mean().reset_index()
    overall_means = pq.groupby("pipeline")["citation_f1"].mean().to_dict()

    rows_data = {}
    for p in PIPELINES:
        rd = {}
        for s in STRATA:
            row = f1[(f1["stratum"] == s) & (f1["pipeline"] == p)].iloc[0]
            rd[s] = (row["mean"], row["ci_lo"], row["ci_hi"])
        rd["Overall"] = (overall_means.get(p), None, None)
        rows_data[p] = rd

    for variant in ["adaptive_v2", "adaptive_oracle"]:
        rd = {}
        for s in STRATA + ["overall"]:
            r = adapt[(adapt["variant"] == variant) & (adapt["stratum"] == s)]
            label = "Overall" if s == "overall" else s
            if len(r):
                row = r.iloc[0]
                rd[label] = (row["mean_f1"], row["ci_lo"], row["ci_hi"])
            else:
                rd[label] = (None, None, None)
        rows_data[variant] = rd

    cols = STRATA + ["Overall"]
    # Per-column winner is computed ONLY among base pipelines.
    # adaptive_oracle is an upper bound by construction and would always
    # bold otherwise; adaptive_v2 is a derived comparison row.
    winners = {}
    for c in cols:
        best_p, best_m = None, -np.inf
        for p in PIPELINES:
            m = rows_data[p][c][0]
            if m is not None and not (isinstance(m, float) and np.isnan(m)) and m > best_m:
                best_m, best_p = m, p
        winners[c] = best_p

    daggers = {(p, c): False for p in rows_data for c in cols}
    for s in STRATA:
        winner = winners[s]
        if winner not in PIPELINES:
            continue
        for p in PIPELINES:
            if p == winner:
                continue
            row = sig[
                (sig["stratum"] == s)
                & (
                    ((sig["pipeline_i"] == winner) & (sig["pipeline_j"] == p))
                    | ((sig["pipeline_j"] == winner) & (sig["pipeline_i"] == p))
                )
            ]
            if len(row) and bool(row.iloc[0]["significant"]):
                daggers[(p, s)] = True

    body = []
    a = body.append
    a(r"\begin{table*}[t]")
    a(r"  \centering")
    a(r"  \caption{Per-stratum citation $F_1$ (mean and BCa 95\% CIs, $B{=}1000$, paired at the query level). "
      r"Bold marks the per-column maximum. $^{\dagger}$ marks pipelines significantly different from the per-stratum winner "
      r"(Holm-adjusted Wilcoxon $p{<}0.05$, BCa CI excludes zero, $|\delta|{\geq}0.147$ jointly). "
      r"\textit{adaptive\_v1} is the rule-based router used at evaluation time; "
      r"\textit{adaptive\_v2} is our learned router (out-of-fold predictions, $n{=}296$); "
      r"\textit{adaptive\_oracle} is the per-query argmax over the 4 base pipelines.}")
    a(r"  \label{tab:main}")
    a(r"  \small")
    a(r"  \begin{tabular}{lcccc}")
    a(r"    \toprule")
    a(r"    System & 1-hop & 2-hop & 3+-hop & Overall \\")
    a(r"    \midrule")
    display_order = PIPELINES + ["adaptive_v2", "adaptive_oracle"]
    for i, p in enumerate(display_order):
        rd = rows_data[p]
        cells = [latex_pipeline(p)]
        for c in cols:
            m, lo, hi = rd[c]
            # Bold/dagger only on base pipelines; adaptive_v2 / adaptive_oracle
            # are reference rows, formatted plain.
            if p in PIPELINES:
                cells.append(fmt_cell(m, lo, hi,
                                      bold=(p == winners[c]),
                                      dagger=daggers[(p, c)]))
            else:
                cells.append(fmt_cell(m, lo, hi))
        a("    " + " & ".join(cells) + r" \\")
        if p == "adaptive":
            a(r"    \midrule")
    a(r"    \bottomrule")
    a(r"  \end{tabular}")
    a(r"\end{table*}")
    (OUT / "table_main.tex").write_text("\n".join(body) + "\n")
    print("wrote table_main.tex")


def table_faithfulness():
    fc = pd.read_csv(STATS / "faithfulness_ci.csv")

    body = []
    a = body.append
    a(r"\begin{table*}[t]")
    a(r"  \centering")
    a(r"  \caption{Faithful\% by pipeline, hop stratum, and judge "
      r"(BCa 95\% CI half-width in parentheses; $n{=}300$ judged outputs, $\sim$20 per pipeline-stratum cell).}")
    a(r"  \label{tab:faith}")
    a(r"  \small")
    a(r"  \begin{tabular}{lcccccc}")
    a(r"    \toprule")
    a(r"    System & \multicolumn{2}{c}{1-hop} & \multicolumn{2}{c}{2-hop} & \multicolumn{2}{c}{3+-hop} \\")
    a(r"    \cmidrule(lr){2-3} \cmidrule(lr){4-5} \cmidrule(lr){6-7}")
    a(r"     & GPT-5.4 & GPT-4.1 & GPT-5.4 & GPT-4.1 & GPT-5.4 & GPT-4.1 \\")
    a(r"    \midrule")
    for p in PIPELINES:
        cells = [latex_pipeline(p)]
        for s in STRATA:
            for j in ["gpt5", "gpt41"]:
                row = fc[(fc["stratum"] == s) & (fc["pipeline"] == p) & (fc["judge"] == j)]
                if len(row):
                    r = row.iloc[0]
                    m = r["faithful_pct"]
                    lo, hi = r["ci_lo"], r["ci_hi"]
                    if pd.notna(lo) and pd.notna(hi):
                        half = max(m - lo, hi - m)
                        cells.append(f"{m * 100:.0f} ($\\pm${half * 100:.0f})")
                    else:
                        cells.append(f"{m * 100:.0f}")
                else:
                    cells.append("---")
        a("    " + " & ".join(cells) + r" \\")
    a(r"    \bottomrule")
    a(r"  \end{tabular}")
    a(r"\end{table*}")
    (OUT / "table_faithfulness.tex").write_text("\n".join(body) + "\n")
    print("wrote table_faithfulness.tex")


def table_agreement():
    ja = pd.read_csv(STATS / "judge_agreement.csv")

    body = []
    a = body.append
    a(r"\begin{table}[t]")
    a(r"  \centering")
    a(r"  \caption{Inter-judge agreement (GPT-5.4 vs GPT-4.1). "
      r"$P_o$: raw agreement; $\kappa$: Cohen's; AC1: Gwet's prevalence-robust; "
      r"McN-$p$: McNemar exact-binomial; $\rho$: Spearman across the 5-pipeline ranking.}")
    a(r"  \label{tab:judges}")
    a(r"  \small")
    a(r"  \begin{tabular}{lcccccc}")
    a(r"    \toprule")
    a(r"    Stratum & $n$ & $P_o$ & $\kappa$ & AC1 & McN-$p$ & $\rho$ \\")
    a(r"    \midrule")
    for s in STRATA + ["overall"]:
        slice_type = "overall" if s == "overall" else "stratum"
        row = ja[(ja["slice_type"] == slice_type) & (ja["slice"] == s)]
        if len(row) == 0:
            continue
        r = row.iloc[0]
        rho = r["spearman_rho_per_pipeline"]
        rho_s = f"{rho:.2f}" if pd.notna(rho) else "---"
        a(f"    {s} & {int(r['n'])} & {r['raw_agreement']:.2f} & "
          f"{r['cohens_kappa']:.2f} & {r['gwets_ac1']:.2f} & "
          f"{r['mcnemar_p']:.3f} & {rho_s} \\\\")
    a(r"    \bottomrule")
    a(r"  \end{tabular}")
    a(r"\end{table}")
    (OUT / "table_agreement.tex").write_text("\n".join(body) + "\n")
    print("wrote table_agreement.tex")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    table_main()
    table_faithfulness()
    table_agreement()


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""STEP 1d: figures/fig1_per_stratum_f1.pdf and figures/fig2_faithfulness_heatmap.pdf.

fig1: grouped bar chart per stratum × pipeline with BCa error bars; significance
      stars (Holm-adjusted Wilcoxon, BCa-excludes-zero, |Cliff's delta| >= 0.147)
      drawn on bars vs the per-stratum winner.

fig2: 5 pipelines × (3 strata × 2 judges) = 30-cell faithfulness % heatmap with
      raw values annotated, plus marginal Gwet's AC1 strip per stratum.

Both PDFs are vector with embedded fonts (TrueType, pdf.fonttype=42).
"""
import os
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
STATS = Path(os.environ.get("STATS_OUT") or str(ROOT / "results" / "stats"))
FIGS = Path(os.environ.get("FIGS_OUT") or str(ROOT / "figures"))
PIPELINES = ["vanilla", "agentic", "agentic-graph", "graphrag", "adaptive"]
STRATA = ["1-hop", "2-hop", "3+-hop"]
# Wong 2011 colorblind-safe palette (no red/green clash)
COLORS = ["#0072B2", "#E69F00", "#009E73", "#56B4E9", "#CC79A7"]


def fig1():
    f1 = pd.read_csv(STATS / "per_stratum_f1_ci.csv")
    sig = pd.read_csv(STATS / "significance_matrix.csv")

    winners = {}
    for s in STRATA:
        sub = f1[f1["stratum"] == s]
        winners[s] = sub.loc[sub["mean"].idxmax(), "pipeline"]

    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    n_strata, n_pipes = len(STRATA), len(PIPELINES)
    bar_w = 0.16
    x = np.arange(n_strata, dtype=float)

    for i, p in enumerate(PIPELINES):
        means, errs_lo, errs_hi = [], [], []
        for s in STRATA:
            row = f1[(f1["stratum"] == s) & (f1["pipeline"] == p)].iloc[0]
            mean = row["mean"]
            lo = row["ci_lo"] if pd.notna(row["ci_lo"]) else mean
            hi = row["ci_hi"] if pd.notna(row["ci_hi"]) else mean
            means.append(mean)
            errs_lo.append(max(0, mean - lo))
            errs_hi.append(max(0, hi - mean))
        positions = x + (i - n_pipes / 2 + 0.5) * bar_w
        ax.bar(positions, means, bar_w, yerr=[errs_lo, errs_hi],
               label=p, color=COLORS[i], capsize=3,
               edgecolor="black", linewidth=0.5, error_kw={"linewidth": 0.8})
        # Significance stars vs winner
        for k, s in enumerate(STRATA):
            if p == winners[s]:
                continue
            row = sig[(sig["stratum"] == s) &
                      (((sig["pipeline_i"] == winners[s]) & (sig["pipeline_j"] == p)) |
                       ((sig["pipeline_j"] == winners[s]) & (sig["pipeline_i"] == p)))]
            if len(row) and bool(row.iloc[0]["significant"]):
                ax.text(positions[k], means[k] + errs_hi[k] + 0.015, "*",
                        ha="center", va="bottom", fontsize=11)

    # Mark per-stratum winners with a small triangle on the x-axis label
    ax.set_xticks(x)
    ax.set_xticklabels([f"{s}\n(winner: {winners[s]})" for s in STRATA])
    ax.set_xlabel("Hop stratum")
    ax.set_ylabel("Citation F1 (BCa 95% CI)")
    ax.set_ylim(0, max(0.78, f1["ci_hi"].fillna(0).max() * 1.18))
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.02), ncol=5,
              frameon=False, fontsize=8, columnspacing=1.2,
              handletextpad=0.5, handlelength=1.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGS / "fig1_per_stratum_f1.pdf", bbox_inches="tight")
    plt.close(fig)


def fig2():
    fc = pd.read_csv(STATS / "faithfulness_ci.csv")
    ja = pd.read_csv(STATS / "judge_agreement.csv")

    judges = ["gpt5", "gpt41"]
    judge_labels = {"gpt5": "GPT-5.4", "gpt41": "GPT-4.1"}
    cols = [(s, j) for s in STRATA for j in judges]
    grid = np.full((len(PIPELINES), len(cols)), np.nan)
    for i, p in enumerate(PIPELINES):
        for j, (s, jud) in enumerate(cols):
            row = fc[(fc["stratum"] == s) & (fc["pipeline"] == p) & (fc["judge"] == jud)]
            if len(row):
                grid[i, j] = row.iloc[0]["faithful_pct"]

    ac1 = []
    for s in STRATA:
        r = ja[(ja["slice_type"] == "stratum") & (ja["slice"] == s)]
        ac1.append(float(r.iloc[0]["gwets_ac1"]) if len(r) else np.nan)

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(7.8, 3.6),
                                   gridspec_kw={"width_ratios": [6, 1]})
    im = ax.imshow(grid, aspect="auto", cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(np.arange(len(cols)))
    ax.set_xticklabels([f"{s}\n{judge_labels[j]}" for s, j in cols],
                       rotation=0, ha="center", fontsize=8)
    ax.set_yticks(np.arange(len(PIPELINES)))
    ax.set_yticklabels(PIPELINES)
    # Vertical separators between strata
    for k in range(1, len(STRATA)):
        ax.axvline(k * 2 - 0.5, color="black", linewidth=0.6)
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            v = grid[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v * 100:.0f}", ha="center", va="center",
                        color="white" if v > 0.5 else "black", fontsize=8)
    ax.set_title("Faithfulness % (5 pipelines × 3 strata × 2 judges)", fontsize=10)
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label("faithful %", fontsize=8)

    ax2.barh(np.arange(len(STRATA)), ac1, color="#56B4E9",
             edgecolor="black", linewidth=0.5)
    ax2.set_yticks(np.arange(len(STRATA)))
    ax2.set_yticklabels(STRATA)
    ax2.set_xlim(0, 1)
    ax2.set_xlabel("Gwet's AC1")
    ax2.invert_yaxis()
    ax2.set_title("Per-stratum AC1", fontsize=9)
    for i, v in enumerate(ac1):
        if not np.isnan(v):
            ax2.text(min(v + 0.02, 0.93), i, f"{v:.2f}", va="center", fontsize=8)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.tight_layout()
    fig.savefig(FIGS / "fig2_faithfulness_heatmap.pdf", bbox_inches="tight")
    plt.close(fig)


def main():
    FIGS.mkdir(exist_ok=True)
    mpl.rcParams["pdf.fonttype"] = 42
    mpl.rcParams["ps.fonttype"] = 42
    mpl.rcParams["font.family"] = "DejaVu Sans"
    fig1()
    print(f"wrote {FIGS / 'fig1_per_stratum_f1.pdf'}")
    fig2()
    print(f"wrote {FIGS / 'fig2_faithfulness_heatmap.pdf'}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Generate the triple-robustness paper tables from v3 + MuSiQue results.

Outputs (each is a complete table environment, ready to \\input):
  paper/cikm/tables/tab_dominance.tex   — C1: per-stratum F1 across 3 settings
  paper/cikm/tables/tab_pathology.tex   — C2a/C2b: GraphRAG triple-robustness
  paper/cikm/tables/tab_judges.tex      — C3: judge agreement v2 vs v3 + self-κ
  paper/cikm/tables/tab_router.tex      — C4: router v2 vs v3
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
STATS_V2 = ROOT / "results" / "stats"
STATS_V3 = ROOT / "results" / "stats-v3"
OUT = ROOT / "paper" / "cikm" / "tables"

PIPELINES = ["vanilla", "agentic", "agentic-graph", "graphrag", "adaptive"]
STRATA = ["1-hop", "2-hop", "3+-hop"]


def per_query_mean_f1(csv):
    df = pd.read_csv(csv)
    return (df.groupby(["query", "pipeline", "query_type"])["citation_f1"]
              .mean().reset_index())


def stratum_stats(csv):
    pq = per_query_mean_f1(csv)
    out = {}
    for p in sorted(pq["pipeline"].unique()):
        out[p] = {}
        for s in STRATA:
            sub = pq[(pq.pipeline == p) & (pq.query_type == s)]
            out[p][s] = float(sub["citation_f1"].mean()) if len(sub) else None
    return out


def graphrag_pathology(csv, judged_csv=None):
    df = pd.read_csv(csv)
    g = df[df.pipeline == "graphrag"]
    out = {
        "mean_context": float(g["n_sources"].mean()),
        "ctxP": float(g["context_precision"].mean()),
        "mean_cited": float(g["n_cited"].mean()),
        "citP": float(g["citation_precision"].mean()),
        "citR": float(g["citation_recall"].mean()),
        "retR": float(g["retrieval_recall"].mean()),
        "f1": float(g["citation_f1"].mean()),
    }
    if judged_csv and Path(judged_csv).exists():
        j = pd.read_csv(judged_csv)
        gj = j[j.pipeline == "graphrag"]
        for judge in ("gpt5", "gpt41"):
            col = f"judge_{judge}_faithful"
            if col in gj.columns and gj[col].notna().any():
                out[f"{judge}_faithful"] = float(gj[col].mean())
                for s in STRATA:
                    sub = gj[gj.query_type == s]
                    if len(sub):
                        out[f"{judge}_faith_{s}"] = float(sub[col].mean())
    return out


def tab_dominance():
    """C1: per-stratum F1 across v2, v3, MuSiQue."""
    v2 = stratum_stats(ROOT / "results" / "main-v2-scored.csv")
    v3 = stratum_stats(ROOT / "results" / "main-v3-scored.csv")
    mq = stratum_stats(ROOT / "results" / "musique-v3-patched-scored.csv")

    def cell(d, p, s):
        v = d.get(p, {}).get(s)
        return f"{v:.3f}" if v is not None else "---"

    def best(d, s):
        cands = [(p, d.get(p, {}).get(s, -1)) for p in d if d.get(p, {}).get(s) is not None]
        return max(cands, key=lambda x: x[1])[0] if cands else None

    def bold_if(d, p, s):
        b = best(d, s)
        c = cell(d, p, s)
        return r"\textbf{" + c + "}" if p == b else c

    body = []
    a = body.append
    a(r"\begin{table*}[t]")
    a(r"  \centering")
    a(r"  \caption{Per-stratum citation $F_1$ across three settings. "
      r"v2 main = DO-178C synthetic with local e5-small embeddings (4{,}440 runs); "
      r"v3 main = same corpus with Azure text-embedding-3-small (4{,}440 runs); "
      r"MuSiQue = 200-query Wikipedia stratified subset with Azure embedder "
      r"(600 runs, vanilla / agentic-graph / graphrag only). "
      r"Bold marks the per-(setting, stratum) maximum.}")
    a(r"  \label{tab:dominance}")
    a(r"  \small")
    a(r"  \begin{tabular}{l ccc | ccc | ccc}")
    a(r"    \toprule")
    a(r"     & \multicolumn{3}{c|}{v2 main (local)} & \multicolumn{3}{c|}{v3 main (Azure)} & \multicolumn{3}{c}{MuSiQue (Azure)} \\")
    a(r"    System & 1h & 2h & 3+h & 1h & 2h & 3+h & 1h & 2h & 3+h \\")
    a(r"    \midrule")
    for p in PIPELINES:
        if p in v2 or p in v3 or p in mq:
            cells = [p]
            for d in (v2, v3, mq):
                for s in STRATA:
                    cells.append(bold_if(d, p, s) if p in d else "---")
            a("    " + " & ".join(cells) + r" \\")
    a(r"    \bottomrule")
    a(r"  \end{tabular}")
    a(r"\end{table*}")
    (OUT / "tab_dominance.tex").write_text("\n".join(body) + "\n")
    print("wrote tab_dominance.tex")


def tab_pathology():
    """C2: GraphRAG over-citation universal + faithfulness corpus-conditional."""
    v2 = graphrag_pathology(
        ROOT / "results" / "main-v2-scored.csv",
        ROOT / "results" / "main-v2-judged.csv",
    )
    v3 = graphrag_pathology(
        ROOT / "results" / "main-v3-scored.csv",
        ROOT / "results" / "main-v3-judged-pinned.csv",
    )
    mq = graphrag_pathology(
        ROOT / "results" / "musique-v3-patched-scored.csv",
        ROOT / "results" / "musique-v3-judged-dual.csv",
    )

    body = []
    a = body.append
    a(r"\begin{table}[t]")
    a(r"  \centering")
    a(r"  \caption{GraphRAG context flooding vs.\ citation behavior (C2a) and "
      r"faithfulness by stratum (C2b), across embedder and corpus swaps. "
      r"The graph walk fills the context window with low-precision material, "
      r"but the synthesizer cites only a third of it at much higher precision. "
      r"C2b cells are GPT-5.4\,/\,GPT-4.1 faithful rates.}")
    a(r"  \label{tab:pathology}")
    a(r"  \small")
    a(r"  \begin{tabular}{l ccc}")
    a(r"    \toprule")
    a(r"    \textit{C2a: context vs.\ citation} & v2 main & v3 main & MuSiQue \\")
    a(r"    \midrule")
    a(f"    Mean context IDs & {v2['mean_context']:.1f} & {v3['mean_context']:.1f} & {mq['mean_context']:.1f} \\\\")
    a(f"    Context precision & {v2['ctxP']:.3f} & {v3['ctxP']:.3f} & {mq['ctxP']:.3f} \\\\")
    a(f"    Mean IDs cited in answer & {v2['mean_cited']:.1f} & {v3['mean_cited']:.1f} & {mq['mean_cited']:.1f} \\\\")
    a(f"    Citation precision & {v2['citP']:.3f} & {v3['citP']:.3f} & {mq['citP']:.3f} \\\\")
    a(f"    Retrieval recall & {v2['retR']:.3f} & {v3['retR']:.3f} & {mq['retR']:.3f} \\\\")
    a(f"    Citation $F_1$ overall & {v2['f1']:.3f} & {v3['f1']:.3f} & {mq['f1']:.3f} \\\\")
    a(r"    \midrule")
    a(r"    \textit{C2b: faithfulness} & 1-hop & 2-hop & 3+-hop \\")
    a(r"    \midrule")
    for label, d in [("v2 main", v2), ("v3 main pinned", v3), ("MuSiQue", mq)]:
        cells = []
        for s in STRATA:
            g5, g41 = d.get(f"gpt5_faith_{s}"), d.get(f"gpt41_faith_{s}")
            if g5 is None:
                cells.append("---")
            elif g41 is None:
                cells.append(f"{g5:.2f}")
            else:
                cells.append(f"{g5:.2f}\\,/\\,{g41:.2f}")
        a(f"    {label} & {cells[0]} & {cells[1]} & {cells[2]} \\\\")
    a(r"    \bottomrule")
    a(r"  \end{tabular}")
    a(r"\end{table}")
    (OUT / "tab_pathology.tex").write_text("\n".join(body) + "\n")
    print("wrote tab_pathology.tex")


def tab_judges():
    """C3: judge agreement v2 vs v3 with same-judge self-κ as headline."""
    v2 = pd.read_csv(STATS_V2 / "judge_agreement.csv")
    v3 = pd.read_csv(STATS_V3 / "judge_agreement.csv")

    # Same-judge self-κ across embedders (computed earlier on paired 300 tuples)
    paired = pd.read_csv(ROOT / "results" / "main-v2-judged.csv").merge(
        pd.read_csv(ROOT / "results" / "main-v3-judged-pinned.csv"),
        on=["query", "pipeline", "repeat"], suffixes=("_v2", "_v3"),
    )
    def kappa(a, b):
        a, b = np.asarray(a, int), np.asarray(b, int)
        po = (a == b).mean()
        pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
        return float((po - pe) / (1 - pe)) if pe < 1 else float("nan")

    self_kappa_g5 = kappa(paired["judge_gpt5_faithful_v2"], paired["judge_gpt5_faithful_v3"])
    self_kappa_g41 = kappa(paired["judge_gpt41_faithful_v2"], paired["judge_gpt41_faithful_v3"])

    body = []
    a = body.append
    a(r"\begin{table}[t]")
    a(r"  \centering")
    a(r"  \caption{Multi-judge protocol fragility. Top: inter-judge agreement (GPT-5.4 vs GPT-4.1) "
      r"drops by half overall under embedder swap (v2 local $\to$ v3 Azure) on the same 300 paired tuples. "
      r"Bottom: same-judge self-consistency across embedders --- GPT-5.4 changes verdict on 41\% of items "
      r"when only the retrieval embedding changes; GPT-4.1 is more stable.}")
    a(r"  \label{tab:judges}")
    a(r"  \small")
    a(r"  \begin{tabular}{l rrrr}")
    a(r"    \toprule")
    a(r"    \textit{Inter-judge $\kappa$} & 1-hop & 2-hop & 3+-hop & overall \\")
    a(r"    \midrule")
    for label, df in [("v2 main", v2), ("v3 main (pinned)", v3)]:
        row = [label]
        for s in STRATA + ["overall"]:
            st = "overall" if s == "overall" else "stratum"
            r = df[(df["slice_type"] == st) & (df["slice"] == s)]
            v = r.iloc[0]["cohens_kappa"] if len(r) else None
            row.append(f"{v:.2f}" if v is not None else "---")
        a("    " + " & ".join(row) + r" \\")
    a(r"    \midrule")
    a(r"    \textbf{Gwet's AC1} & 1-hop & 2-hop & 3+-hop & overall \\")
    a(r"    \midrule")
    for label, df in [("v2 main", v2), ("v3 main (pinned)", v3)]:
        row = [label]
        for s in STRATA + ["overall"]:
            st = "overall" if s == "overall" else "stratum"
            r = df[(df["slice_type"] == st) & (df["slice"] == s)]
            v = r.iloc[0]["gwets_ac1"] if len(r) else None
            row.append(f"{v:.2f}" if v is not None else "---")
        a("    " + " & ".join(row) + r" \\")
    a(r"    \midrule")
    a(r"    \multicolumn{5}{l}{\textit{Same-judge self-$\kappa$ across embedders (paired 300 tuples)}} \\")
    a(r"    \midrule")
    a(f"    GPT-5.4 (v2 main vs v3 main) & \\multicolumn{{4}}{{r}}{{$\\kappa = {self_kappa_g5:.3f}$, raw agreement 0.59}} \\\\")
    a(f"    GPT-4.1 (v2 main vs v3 main) & \\multicolumn{{4}}{{r}}{{$\\kappa = {self_kappa_g41:.3f}$, raw agreement 0.74}} \\\\")
    a(r"    \bottomrule")
    a(r"  \end{tabular}")
    a(r"\end{table}")
    (OUT / "tab_judges.tex").write_text("\n".join(body) + "\n")
    print("wrote tab_judges.tex")


def tab_router():
    """C4: V2 router replication v2 vs v3."""
    body = []
    a = body.append
    a(r"\begin{table}[t]")
    a(r"  \centering")
    a(r"  \caption{V2 router replication and Azure-embedder boost. Same 14-feature schema "
      r"(11 hand text features, 3 PCs of the query embedding); only the embedder differs. "
      r"Text features remain mostly inert (4/11 non-zero), so the +0.08 macro-$F_1$ gain "
      r"is attributable to dense-embedding hop-decodability.}")
    a(r"  \label{tab:router}")
    a(r"  \small")
    a(r"  \resizebox{\columnwidth}{!}{%")
    a(r"  \begin{tabular}{l rr}")
    a(r"    \toprule")
    a(r"     & v2 (local 384d $\to$ PCA-3) & v3 (Azure 1536d $\to$ PCA-3) \\")
    a(r"    \midrule")
    a(r"    50-fold macro-$F_1$ & $0.78 \pm 0.08$ & $\mathbf{0.86 \pm 0.05}$ \\")
    a(r"    Adaptive-V2 overall $F_1$ & 0.559 & 0.569 \\")
    a(r"    Adaptive-V1 overall $F_1$ & 0.439 & 0.468 \\")
    a(r"    Oracle overall $F_1$ & 0.641 & 0.652 \\")
    a(r"    V2 $-$ V1 (absolute) & $+0.120$ & $+0.101$ \\")
    a(r"    Gap closure (V1$\to$Oracle) & 59.4\% & 54.8\% \\")
    a(r"    Holm-Wilcoxon strata sig & 3/3 & 2/3 \\")
    a(r"    \bottomrule")
    a(r"  \end{tabular}}")
    a(r"\end{table}")
    (OUT / "tab_router.tex").write_text("\n".join(body) + "\n")
    print("wrote tab_router.tex")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tab_dominance()
    tab_pathology()
    tab_judges()
    tab_router()


if __name__ == "__main__":
    main()

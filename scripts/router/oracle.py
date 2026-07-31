#!/usr/bin/env python
"""STEP 2c: per-query oracle pipeline = argmax F1 over the 4 base pipelines.

Excludes 'adaptive' (V1) — adaptive itself is being upgraded by V2.

Output: data/router/oracle_routes.csv
  columns: query, query_type, vanilla, agentic, agentic-graph, graphrag,
           oracle_pipeline, oracle_f1
"""
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SCORED = Path(os.environ.get("SCORED_CSV") or str(ROOT / "results" / "main-v2-scored.csv"))
OUT = Path(os.environ.get("ORACLE_ROUTES_CSV") or str(ROOT / "data" / "router" / "oracle_routes.csv"))
ORACLE_PIPELINES = ["vanilla", "agentic", "agentic-graph", "graphrag"]


def main():
    df = pd.read_csv(SCORED)
    df = df[df["pipeline"].isin(ORACLE_PIPELINES)]

    pq = (df.groupby(["query", "query_type", "pipeline"])["citation_f1"]
            .mean().reset_index())

    wide = pq.pivot(index=["query", "query_type"], columns="pipeline",
                     values="citation_f1")
    # Reorder
    wide = wide[ORACLE_PIPELINES]
    # Per-query argmax over the 4 pipelines (drop NaN rows defensively)
    nan_rows = wide.isna().any(axis=1).sum()
    if nan_rows:
        print(f"WARN: {nan_rows} queries have NaN F1 for some pipeline (dropping)")
        wide = wide.dropna()
    wide["oracle_pipeline"] = wide[ORACLE_PIPELINES].idxmax(axis=1)
    wide["oracle_f1"] = wide[ORACLE_PIPELINES].max(axis=1)

    out = wide.reset_index()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT} (rows={len(out)})")
    print(f"  oracle pipeline distribution:")
    print(out["oracle_pipeline"].value_counts().to_string())
    print(f"  oracle mean F1 by stratum:")
    print(out.groupby("query_type")["oracle_f1"].agg(["count", "mean"]).round(4).to_string())


if __name__ == "__main__":
    main()

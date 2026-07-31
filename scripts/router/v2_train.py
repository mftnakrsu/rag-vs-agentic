#!/usr/bin/env python
"""STEP 2b: V2 router training + OOF predictions.

- target: hop_stratum (3-class)
- model: LogisticRegression(penalty=l2, C=1.0, solver=lbfgs, max_iter=1000)
  wrapped in CalibratedClassifierCV(method='sigmoid', cv=3) for Platt
- ColumnTransformer: PCA(n_components=3) on emb_* cols, passthrough on text feats
- CV evaluation: RepeatedStratifiedKFold(n_splits=10, n_repeats=5, random_state=20260511)
  -> macro-F1 mean ± std across 50 fits
- OOF predictions: single StratifiedKFold(10) -> one prediction per query
- Routing map (locked from Step 1 mean-F1 winners; PLAN's "adjust if contested" clause):
    1-hop  -> agentic-graph
    2-hop  -> vanilla
    3+-hop -> agentic-graph

Outputs:
  data/router/v2_oof_routes.csv
  results/router/v2_cv_report.txt
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import (
    RepeatedStratifiedKFold,
    StratifiedKFold,
    cross_val_predict,
    cross_val_score,
)
import os
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[2]
FEATURES = Path(os.environ.get("FEATURES_CSV") or str(ROOT / "data" / "router" / "features.csv"))
OUT_OOF = Path(os.environ.get("OOF_ROUTES_CSV") or str(ROOT / "data" / "router" / "v2_oof_routes.csv"))
OUT_REPORT = Path(os.environ.get("CV_REPORT_TXT") or str(ROOT / "results" / "router" / "v2_cv_report.txt"))
SEED = 20260511

# Mean-winners from results/stats/per_stratum_f1_ci.csv after the citation
# rescore (answer-parsed cited_ids, scripts/rescore_citations.py). 1-hop and
# 2-hop are statistically tied between vanilla and graphrag (Wilcoxon
# p=0.12 / p=0.65, negligible delta); mean-winner rule applied as before.
ROUTING_MAP = {
    "1-hop": "vanilla",
    "2-hop": "graphrag",
    "3+-hop": "agentic-graph",
}


def build_pipeline(emb_cols, non_emb_cols):
    ct = ColumnTransformer([
        ("embed", PCA(n_components=3, random_state=SEED), emb_cols),
        ("keep", "passthrough", non_emb_cols),
    ])
    base = LogisticRegression(penalty="l2", C=1.0, solver="lbfgs", max_iter=1000)
    calibrated = CalibratedClassifierCV(base, method="sigmoid", cv=3)
    return Pipeline([("feats", ct), ("clf", calibrated)])


def main():
    df = pd.read_csv(FEATURES)
    # Force plain numpy backend to avoid pandas 3.0 pyarrow-array indexing
    # incompatibility inside sklearn._safe_indexing.
    y = np.asarray(df["hop_stratum"].astype(str).tolist())
    emb_cols = [c for c in df.columns if c.startswith("emb_")]
    non_emb_cols = [
        "entity_count", "has_id_regex",
        "kw_verifies", "kw_derives", "kw_refines", "kw_satisfies",
        "kw_references", "kw_which", "kw_howmany", "kw_list",
        "query_token_len_log",
    ]
    X = df[emb_cols + non_emb_cols].astype("float64")
    print(f"X shape: {X.shape}, classes: {sorted(set(y))}")

    # 1) Repeated stratified CV for macro-F1
    pipe = build_pipeline(emb_cols, non_emb_cols)
    rskf = RepeatedStratifiedKFold(n_splits=10, n_repeats=5, random_state=SEED)
    scores = cross_val_score(pipe, X, y, cv=rskf, scoring="f1_macro", n_jobs=1)
    print(f"50-fold macro-F1: mean={scores.mean():.4f} std={scores.std():.4f}")

    # 2) OOF predictions via single 10-fold (cross_val_predict requires disjoint test sets)
    skf = StratifiedKFold(n_splits=10, shuffle=True, random_state=SEED)
    pipe2 = build_pipeline(emb_cols, non_emb_cols)
    oof_pred = cross_val_predict(pipe2, X, y, cv=skf, method="predict", n_jobs=1)
    pipe3 = build_pipeline(emb_cols, non_emb_cols)
    oof_proba = cross_val_predict(pipe3, X, y, cv=skf, method="predict_proba", n_jobs=1)

    # Get class order
    pipe_full = build_pipeline(emb_cols, non_emb_cols).fit(X, y)
    classes = pipe_full.named_steps["clf"].classes_

    oof = df[["query_id", "query", "hop_stratum"]].copy()
    oof["predicted_hop"] = oof_pred
    safe_name = {c: f"p_{c.replace('+', 'plus').replace('-', '_')}" for c in classes}
    for i, c in enumerate(classes):
        oof[safe_name[c]] = oof_proba[:, i]
    oof["recommended_pipeline"] = oof["predicted_hop"].map(ROUTING_MAP)
    OUT_OOF.parent.mkdir(parents=True, exist_ok=True)
    oof.to_csv(OUT_OOF, index=False)

    # CV report
    lines = []
    a = lines.append
    a("V2 Router Cross-Validation Report")
    a("=================================")
    a("")
    a(f"N queries: {len(df)}")
    a(f"Features: {len(emb_cols)} embedding (PCA->3) + {len(non_emb_cols)} text = "
      f"{3 + len(non_emb_cols)} effective dims")
    a("")
    a("Model:")
    a("  LogisticRegression(penalty=l2, C=1.0, solver=lbfgs, max_iter=1000)")
    a("  + CalibratedClassifierCV(method=sigmoid, cv=3)  [Platt scaling]")
    a("  + ColumnTransformer: PCA(n_components=3) on emb_*, passthrough on text feats")
    a("")
    a(f"CV: RepeatedStratifiedKFold(n_splits=10, n_repeats=5, random_state={SEED})")
    a("")
    a(f"Macro-F1 across 50 folds:")
    a(f"  mean = {scores.mean():.4f}")
    a(f"  std  = {scores.std():.4f}")
    a(f"  min  = {scores.min():.4f}")
    a(f"  max  = {scores.max():.4f}")
    a("")
    a(f"OOF classification report (single 10-fold, seed={SEED}):")
    a(classification_report(y, oof_pred))
    a("")
    a("Routing map (locked from Step 1 mean-F1 winners):")
    for k, v in ROUTING_MAP.items():
        a(f"  {k:7s} -> {v}")
    a("")
    a("OOF prediction distribution:")
    for c in classes:
        a(f"  {c:7s}: {int((oof_pred == c).sum())} / {len(oof_pred)}")
    a("")
    a("OOF recommended_pipeline distribution (after routing map):")
    rec_counts = oof["recommended_pipeline"].value_counts().sort_index()
    for p, n in rec_counts.items():
        a(f"  {p:15s}: {n}")
    a("")
    a("Per-stratum routing accuracy (OOF predicted_hop == true hop_stratum):")
    for s in sorted(set(y)):
        sub = oof[oof["hop_stratum"] == s]
        acc = float((sub["predicted_hop"] == s).mean()) if len(sub) else 0.0
        a(f"  {s:7s}: {acc:.3f} ({int((sub['predicted_hop'] == s).sum())}/{len(sub)})")

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines))
    print(f"wrote {OUT_OOF}")
    print(f"wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""STEP 2a: extract V2 router features (14 dims) for each unique query.

14 features per query (per PLAN spec):
  entity_count, has_id_regex,
  kw_verifies, kw_derives, kw_refines, kw_satisfies,
  kw_references, kw_which, kw_howmany, kw_list,
  query_token_len_log,
  emb_0..emb_383  (raw 384-d e5-small embedding; PCA->3 happens in v2_train per fold)

The PLAN spec calls for `text-embedding-3-large`; the repo's `embedders.py`
exposes only `local` (e5-small 384d) and `azure` (text-embedding-3-small 1536d).
We use the local e5-small embedder for reproducibility (no Azure dependency,
deterministic). PCA reduction in v2_train collapses to 3 PCs either way.

Output: data/router/features.csv (one row per unique query)
"""
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
SCORED = Path(os.environ.get("SCORED_CSV") or str(ROOT / "results" / "main-v2-scored.csv"))
OUT = Path(os.environ.get("FEATURES_CSV") or str(ROOT / "data" / "router" / "features.csv"))
EMBEDDER_NAME = os.environ.get("ROUTER_EMBEDDER", "local")  # 'local' or 'azure'

ID_REGEX = re.compile(r"\b(REQ|SRS|HLR|LLR|SW)-\d+\b", re.IGNORECASE)
KEYWORDS = [
    ("kw_verifies", "verifies"),
    ("kw_derives", "derives"),
    ("kw_refines", "refines"),
    ("kw_satisfies", "satisfies"),
    ("kw_references", "references"),
    ("kw_which", "which"),
    ("kw_howmany", "how many"),
    ("kw_list", "list"),
]


def text_features(q: str) -> dict:
    ql = q.lower()
    feats = {
        "entity_count": int(len(ID_REGEX.findall(q))),
        "has_id_regex": int(bool(ID_REGEX.search(q))),
        "query_token_len_log": float(np.log1p(len(q.split()))),
    }
    for name, kw in KEYWORDS:
        feats[name] = int(kw in ql)
    return feats


def main():
    load_dotenv(ROOT / ".env")
    sys.path.insert(0, str(ROOT))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(SCORED)
    queries = (df.groupby("query", sort=False)["query_type"]
                 .first().reset_index())
    queries.columns = ["query", "hop_stratum"]
    print(f"unique queries: {len(queries)} (router embedder = {EMBEDDER_NAME})")

    text_df = pd.DataFrame([text_features(q) for q in queries["query"]])

    if EMBEDDER_NAME == "azure":
        from aerorag.embedders import AzureOpenAIEmbedder
        emb = AzureOpenAIEmbedder()
        print("embedding via Azure text-embedding-3-small (batch=64)...")
        embs = np.asarray(emb.embed_documents(queries["query"].tolist(), batch_size=64),
                          dtype=np.float32)
    else:
        from aerorag.embedders import LocalE5SmallEmbedder
        emb = LocalE5SmallEmbedder()
        emb._load()
        print("embedding via local e5-small (batch=32, 'query: ' prefix)...")
        qs = [f"query: {q}" for q in queries["query"].tolist()]
        embs = []
        for i in range(0, len(qs), 32):
            embs.extend(emb._embed(qs[i:i + 32]))
        embs = np.asarray(embs, dtype=np.float32)
    print(f"  embeddings shape: {embs.shape}")

    emb_df = pd.DataFrame(embs, columns=[f"emb_{i}" for i in range(embs.shape[1])])
    out = pd.concat([
        queries.reset_index(drop=True),
        text_df.reset_index(drop=True),
        emb_df.reset_index(drop=True),
    ], axis=1)
    out.insert(0, "query_id", range(len(out)))
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT} (rows={len(out)}, cols={out.shape[1]})")
    print(f"  text-feature non-zero counts:")
    for col in [c for c in out.columns if c.startswith("kw_") or c in ("entity_count", "has_id_regex")]:
        print(f"    {col:25s}: {int((out[col] > 0).sum())} / {len(out)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Second GraphRAG-family retriever: personalized PageRank over the same graph.

Reviewers noted the study tests one GraphRAG implementation. This adds a
second traversal that differs in kind rather than in budget: instead of
taking everything inside a fixed 2-hop radius, it scores the reachable
component by random-walk-with-restart mass from the vector seeds and keeps
the top nodes. A well-connected 3-hop requirement can outrank a peripheral
1-hop one, and the radius is unbounded.

Everything else is held fixed against the production GraphRAG arm -- same
embedder, same 8 vector seeds, same context cap, same synthesis prompt --
so any difference is attributable to the traversal.

Runs with the Azure embedder so results are directly comparable to the v3
GraphRAG arm. Writes results/main-v3-ppr.jsonl. Resumable.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

QUERIES = ROOT / "data" / "eval" / "queries-hop-stratified.jsonl"
CORPUS = ROOT / "data" / "synthetic" / "requirements.jsonl"
K_SEEDS, MAX_CONTEXT, WALK_MAX = 8, 15, 30


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--embedder", default="azure")
    ap.add_argument("--repeat", type=int, default=0)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    load_dotenv(ROOT / ".env")

    from embedders import get_embedder
    from graph_store_local import LocalGraph, TRACEABILITY_LINK_TYPES
    from llm_compat import GPT5Client
    from vanilla_rag import GROUNDED_SYSTEM_PROMPT, _coll_for
    from vector_store import get_client, get_or_create_collection, query_top_k

    text_by_id = {r["id"]: r["full_text"]
                  for r in map(json.loads, CORPUS.open(encoding="utf-8"))}
    queries = [json.loads(l) for l in QUERIES.open(encoding="utf-8")]
    if args.limit:
        queries = queries[:args.limit]

    out_path = ROOT / "results" / f"main-v3-ppr-r{args.repeat}.jsonl"
    done = {json.loads(l)["query"] for l in out_path.open()} if out_path.exists() else set()
    print(f"ppr arm: {len(queries)} queries, {len(done)} already done")

    emb = get_embedder(args.embedder)
    coll_name, dim = _coll_for(args.embedder)
    col = get_or_create_collection(get_client(), coll_name, dim=dim)
    graph = LocalGraph.from_corpus(CORPUS)
    llm = GPT5Client()

    f = out_path.open("a", encoding="utf-8")
    for q in tqdm(queries, unit="q", ncols=100):
        if q["query"] in done:
            continue
        seeds = [h["id"] for h in query_top_k(col, emb.embed_query(q["query"]), k=K_SEEDS)]
        walked = graph.walk_ppr(seeds, TRACEABILITY_LINK_TYPES, WALK_MAX)
        ctx_ids = list(dict.fromkeys(seeds + [w["id"] for w in walked]))[:MAX_CONTEXT]
        context = "\n\n---\n\n".join(
            f"[{i}] {text_by_id.get(i, '')}" for i in ctx_ids)
        t0 = time.time()
        try:
            resp = llm.chat(messages=[
                {"role": "system", "content": GROUNDED_SYSTEM_PROMPT},
                {"role": "user", "content":
                 f"Context (top-{len(seeds)} retrieved + PPR-ranked neighbors):"
                 f"\n\n{context}\n\nQ: {q['query']}"},
            ])
        except Exception as e:  # noqa: BLE001
            print(f"\nERROR {q['query'][:60]}: {e}", file=sys.stderr)
            continue
        usage = GPT5Client.usage(resp)
        f.write(json.dumps({
            "query": q["query"], "query_type": q["type"], "pipeline": "graphrag-ppr",
            "embedder": args.embedder, "reranker": "none", "repeat": args.repeat,
            "latency_ms": int((time.time() - t0) * 1000),
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "source_ids": ";".join(ctx_ids), "n_sources": len(ctx_ids),
            "iter_count": 0, "verdict": "", "intent": "", "routed_to": "", "route_reason": "",
            "answer": resp.choices[0].message.content or "",
        }, ensure_ascii=False) + "\n")
        f.flush()
    f.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

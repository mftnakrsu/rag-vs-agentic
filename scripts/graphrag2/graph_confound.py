#!/usr/bin/env python
"""Retrieval-side graph confound check. No LLM calls.

The v2/v3 GraphRAG arms walked the Aura graph, which carried edges beyond the
released annotations; the PPR arm and the bge-m3 matrix walked the file-backed
graph (720 edges). This rebuilds the GraphRAG context for every query on the
file-backed graph -- same embedder, seeds, walk and context cap as
graph_rag.graph_rag -- and compares it with the stored Aura-graph contexts of
the v3 GraphRAG arm (repeat 0) and with the stored PPR contexts.

Only the context side can be measured this way; citation metrics need
generation. Writes results/graph-confound.csv and prints a summary.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from statistics import mean

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

QUERIES = ROOT / "data" / "eval" / "queries-hop-stratified.jsonl"
CORPUS = ROOT / "data" / "synthetic" / "requirements.jsonl"
K_SEEDS, MAX_CONTEXT, WALK_MAX = 8, 15, 30


def stored_contexts(path: Path, pipeline: str) -> dict[str, list[str]]:
    rows = (json.loads(l) for l in path.open(encoding="utf-8"))
    return {r["query"]: [i for i in str(r["source_ids"]).split(";") if i]
            for r in rows
            if r["pipeline"].split("|")[0] == pipeline and str(r.get("repeat", 0)) == "0"}


def main() -> int:
    load_dotenv()
    from aerorag.embedders import get_embedder
    from aerorag.eval_metrics import citation_precision, retrieval_recall
    from aerorag.graph_store_local import LocalGraph, TRACEABILITY_LINK_TYPES
    from aerorag.vanilla_rag import _coll_for
    from aerorag.vector_store import fetch_by_id, get_client, get_or_create_collection, query_top_k

    queries = [json.loads(l) for l in QUERIES.open(encoding="utf-8")]
    aura = stored_contexts(ROOT / "results" / "main-v3.jsonl", "graphrag")
    ppr = stored_contexts(ROOT / "results" / "main-v3-ppr-r0.jsonl", "graphrag-ppr")

    emb = get_embedder("azure")
    coll_name, dim = _coll_for("azure")
    col = get_or_create_collection(get_client(), coll_name, dim=dim)
    graph = LocalGraph.from_corpus(CORPUS)

    rows = []
    for q in queries:
        seeds = query_top_k(col, emb.embed_query(q["query"]), k=K_SEEDS)
        seed_ids = [s["id"] for s in seeds]
        walked = graph.walk_2hop(seed_ids, TRACEABILITY_LINK_TYPES, WALK_MAX)
        hops = {w["id"]: w["hops"] for w in walked}
        # graph_rag hydrates neighbours from Chroma, sorts by (hops, id), seeds first, cap 15
        nbr = sorted((c["id"] for c in fetch_by_id(col, list(hops))), key=lambda i: (hops[i], i))
        local = list(dict.fromkeys(seed_ids + nbr))[:MAX_CONTEXT]

        gold = set(q["expected_ids"])
        a = aura.get(q["query"], [])
        p = ppr.get(q["query"], [])
        rows.append({
            "query": q["query"], "stratum": q["type"],
            "seeds_match_aura": set(seed_ids) <= set(a),
            "seeds_match_ppr": seed_ids == p[:K_SEEDS],
            "n_local": len(local), "n_aura": len(a), "n_ppr": len(p),
            "ctxP_local": citation_precision(set(local), gold),
            "ctxP_aura": citation_precision(set(a), gold),
            "ctxP_ppr": citation_precision(set(p), gold),
            "retR_local": retrieval_recall(set(local), gold),
            "retR_aura": retrieval_recall(set(a), gold),
            "retR_ppr": retrieval_recall(set(p), gold),
            "jaccard_local_aura": len(set(local) & set(a)) / max(1, len(set(local) | set(a))),
            "local_ids": ";".join(local),
        })

    out = ROOT / "results" / "graph-confound.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print(f"{len(rows)} queries -> {out}")
    print(f"seeds identical to stored Aura run: {sum(r['seeds_match_aura'] for r in rows)}/{len(rows)}")
    print(f"seeds identical to stored PPR run:  {sum(r['seeds_match_ppr'] for r in rows)}/{len(rows)}")
    for strat in ("all", "1-hop", "2-hop", "3+-hop"):
        sub = [r for r in rows if strat == "all" or r["stratum"] == strat]
        print(f"{strat:7s} n={len(sub):3d}  slots L/A/P "
              + " ".join(f"{mean(r[f'n_{g}'] for r in sub):.1f}" for g in ("local", "aura", "ppr"))
              + "  ctxP L/A/P "
              + " ".join(f"{mean(r[f'ctxP_{g}'] for r in sub):.3f}" for g in ("local", "aura", "ppr"))
              + "  retR L/A/P "
              + " ".join(f"{mean(r[f'retR_{g}'] for r in sub):.3f}" for g in ("local", "aura", "ppr"))
              + f"  jacc(L,A) {mean(r['jaccard_local_aura'] for r in sub):.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

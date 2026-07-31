"""GraphRAG pipeline (3rd pipeline in the 4-pipeline study).

    query
      -> embed
      -> ChromaDB top-K seeds
      -> Aura 1-2 hop walk on traceability edges
      -> hydrate neighbors from ChromaDB by id
      -> dedupe + merge seeds + neighbors (cap at max_context)
      -> single LLM synthesis call
      -> answer

The 4th pipeline (agentic-graph) lives in agentic_rag.py and injects
graph_lookup as a ReAct tool — see Phase 1c.
"""
from __future__ import annotations

import sys
import time

from dotenv import load_dotenv

from agentic_rag import _ID_PATTERN
from embedders import get_embedder
from graph_store import TRACEABILITY_LINK_TYPES, get_driver, walk_2hop
from llm_compat import GPT5Client
from vanilla_rag import GROUNDED_SYSTEM_PROMPT, _coll_for, _format_context
from vector_store import (
    fetch_by_id,
    get_client,
    get_or_create_collection,
    query_top_k,
)


def graph_rag(
    query: str,
    *,
    embedder_name: str = "local",
    k_seeds: int = 8,
    max_context: int = 15,
    walk_max_results: int = 30,
    rel_types: tuple[str, ...] = TRACEABILITY_LINK_TYPES,
) -> dict:
    t0 = time.time()

    embedder = get_embedder(embedder_name)
    qvec = embedder.embed_query(query)
    client = get_client()
    coll_name, dim = _coll_for(embedder_name)
    col = get_or_create_collection(client, coll_name, dim=dim)
    seeds = query_top_k(col, qvec, k=k_seeds)
    seed_ids = [s["id"] for s in seeds]
    for s in seeds:
        s["_hops"] = 0  # tag seeds for downstream attribution

    driver = get_driver()
    try:
        neighbors_meta = walk_2hop(
            driver,
            seed_ids,
            rel_types=rel_types,
            max_results=walk_max_results,
        )
    finally:
        driver.close()
    neighbor_ids = [n["id"] for n in neighbors_meta]
    hops_by_id = {n["id"]: n["hops"] for n in neighbors_meta}

    # Hydrate neighbors from the same ChromaDB collection (already indexed at build time)
    neighbor_chunks = fetch_by_id(col, neighbor_ids) if neighbor_ids else []
    for c in neighbor_chunks:
        c["_hops"] = hops_by_id.get(c["id"], -1)
    neighbor_chunks.sort(key=lambda c: (c["_hops"], c["id"]))

    # Merge: seeds first (always present), then neighbors by hop asc.
    # Stop at max_context — graph expansion never starves the seeds.
    seen: set[str] = set()
    context_chunks: list[dict] = []
    for c in seeds + neighbor_chunks:
        if c["id"] in seen:
            continue
        seen.add(c["id"])
        context_chunks.append(c)
        if len(context_chunks) >= max_context:
            break

    llm = GPT5Client()
    context = _format_context(context_chunks)
    user_msg = (
        f"Context (top-{len(seeds)} retrieved + graph-expanded neighbors):\n\n"
        f"{context}\n\nQ: {query}"
    )
    resp = llm.chat(messages=[
        {"role": "system", "content": GROUNDED_SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ])
    answer = resp.choices[0].message.content or ""
    usage = GPT5Client.usage(resp)

    return {
        "pipeline": f"graphrag|{embedder_name}",
        "query": query,
        "answer": answer,
        "sources": context_chunks,
        # answer-parsed citations (ALCE-style); the context set lives in `sources`
        "cited_ids": [i for i in dict.fromkeys(_ID_PATTERN.findall(answer))],
        "latency_ms": int((time.time() - t0) * 1000),
        "tokens": usage,
        "n_seeds": len(seeds),
        "n_neighbors": len(neighbor_chunks),
        "rel_types": list(rel_types),
    }


if __name__ == "__main__":
    load_dotenv()
    q = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "How does the air data system provide angle-of-attack "
             "to the flight control computer?"
    )

    print(f"\n[query] {q}\n")
    result = graph_rag(q, embedder_name="local")
    total = result["tokens"].get("total_tokens", 0)
    print(
        f"--- Answer ({result['latency_ms']}ms, {total} tokens, "
        f"seeds={result['n_seeds']} neighbors={result['n_neighbors']}) ---"
    )
    print(result["answer"])
    print("\n--- Sources (id : hop) ---")
    for c in result["sources"]:
        hop = c.get("_hops", 0)
        marker = "seed" if hop == 0 else f"+{hop}h"
        print(f"  {c['id']:10s}  [{marker:>5s}]  {c.get('heading', '')[:70]}")

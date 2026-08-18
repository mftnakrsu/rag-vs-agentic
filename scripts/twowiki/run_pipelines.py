#!/usr/bin/env python
"""Run vanilla and GraphRAG over the 2WikiMultihopQA corpus (third corpus, D1).

Mirrors the MuSiQue arm: vanilla is dense top-10 -> top-5 context -> one
synthesis call; GraphRAG is 8 vector seeds + an undirected <=2-hop walk over
the REFERENCES edges, capped at 30 walked / 15 context, then one synthesis
call. The walk is replicated in Python exactly as in
scripts/musique/distractor_control.py, so no Neo4j instance is required.

agentic-graph is not run here: its graph_lookup tool needs a live Neo4j, and
the cross-corpus claims (C2 flooding, C3 hop decline) only need the
vanilla/GraphRAG contrast.

Writes results/twowiki-{pipeline}.jsonl. Resumable.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

DATA = ROOT / "data" / "twowiki"
COLLECTION = "twowiki-azure"
K_SEEDS, MAX_CONTEXT, WALK_MAX = 8, 15, 30
TOP_K, TOP_N = 10, 5

GROUNDED_SYSTEM_PROMPT = """You are an aerospace requirements engineer answering questions about a DOORS-exported requirements set.
Rules:
 1. Ground every claim in retrieved requirements; cite the IDs you used inline as [ADS-014].
 2. If the retrieved context does not contain the answer, say so plainly. Do not invent.
 3. Prefer concise, technical wording. Reproduce numeric thresholds (Hz, kt, ft, ms, °) verbatim.
 4. When requirements interact (e.g., FCC <-> ADS), explain the relationship.
"""


def adjacency():
    adj = defaultdict(set)
    for l in (DATA / "edges.jsonl").open():
        e = json.loads(l)
        adj[e["source"]].add(e["target"])
        adj[e["target"]].add(e["source"])
    return adj


def walk_2hop(adj, seeds):
    s = set(seeds)
    h1 = set()
    for x in seeds:
        h1 |= adj.get(x, set())
    h1 -= s
    h2 = set()
    for x in h1:
        h2 |= adj.get(x, set())
    h2 -= s | h1
    out = [{"id": i, "h": 1} for i in h1] + [{"id": i, "h": 2} for i in h2]
    out.sort(key=lambda r: (r["h"], r["id"]))
    return [r["id"] for r in out[:WALK_MAX]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pipeline", choices=["vanilla", "graphrag"], required=True)
    ap.add_argument("--repeat", type=int, default=0)
    args = ap.parse_args()
    load_dotenv(ROOT / ".env")

    from embedders import AzureOpenAIEmbedder
    from llm_compat import GPT5Client
    from vector_store import get_client, get_or_create_collection, query_top_k

    text_by_id, title_by_id = {}, {}
    for l in (DATA / "chunks.jsonl").open():
        c = json.loads(l)
        text_by_id[c["id"]] = c["text"]
        title_by_id[c["id"]] = c["title"]
    queries = [json.loads(l) for l in (DATA / "queries.jsonl").open()]

    out_path = ROOT / "results" / f"twowiki-{args.pipeline}-r{args.repeat}.jsonl"
    done = set()
    if out_path.exists():
        done = {json.loads(l)["query"] for l in out_path.open()}
    print(f"{args.pipeline} r{args.repeat}: {len(queries)} queries, {len(done)} done")

    emb = AzureOpenAIEmbedder()
    col = get_or_create_collection(get_client(), COLLECTION, dim=emb.DIM)
    adj = adjacency() if args.pipeline == "graphrag" else None
    llm = GPT5Client()

    f = out_path.open("a")
    for q in tqdm(queries, unit="q", ncols=100):
        if q["query"] in done:
            continue
        qvec = emb.embed_query(q["query"])
        k = K_SEEDS if args.pipeline == "graphrag" else TOP_K
        hits = query_top_k(col, qvec, k=k)
        seeds = [h["id"] for h in hits]
        if args.pipeline == "graphrag":
            ctx_ids = list(dict.fromkeys(seeds + walk_2hop(adj, seeds)))[:MAX_CONTEXT]
            header = f"Context (top-{len(seeds)} retrieved + graph-expanded neighbors)"
        else:
            ctx_ids = seeds[:TOP_N]
            header = "Context (retrieved requirements)"
        context = "\n\n---\n\n".join(
            f"[{i}] ({title_by_id.get(i,'')})\n{text_by_id.get(i,'')}" for i in ctx_ids)
        t0 = time.time()
        try:
            resp = llm.chat(messages=[
                {"role": "system", "content": GROUNDED_SYSTEM_PROMPT},
                {"role": "user", "content": f"{header}:\n\n{context}\n\nQ: {q['query']}"},
            ])
        except Exception as e:  # noqa: BLE001
            print(f"\nERROR {q['query'][:60]}: {e}", file=sys.stderr)
            continue
        usage = GPT5Client.usage(resp)
        f.write(json.dumps({
            "query": q["query"], "query_type": q["type"], "pipeline": args.pipeline,
            "embedder": "azure", "reranker": "none", "repeat": args.repeat,
            "latency_ms": int((time.time() - t0) * 1000),
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "source_ids": ";".join(ctx_ids), "n_sources": len(ctx_ids),
            "iter_count": 0, "verdict": "", "intent": "", "routed_to": "", "route_reason": "",
            "answer": resp.choices[0].message.content or "",
        }) + "\n")
        f.flush()
    f.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

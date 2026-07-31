#!/usr/bin/env python
"""Distractor-edge control for the MuSiQue GraphRAG arm.

The production MuSiQue graph only has REFERENCES edges between consecutive
gold supporting paragraphs (build_corpus.py), so the 2-hop walk is biased
toward the gold chain. This control keeps those edges and adds REFERENCES
edges between consecutive distractor paragraphs of the same question, then
re-runs the GraphRAG arm on the same 200 queries with the same vector seeds
(recovered from the original trace: context order is seeds first, so
source_ids[:8] are the seeds). If GraphRAG's advantage survives, it is not
an artifact of gold-only edges.

The walk is replicated in Python (undirected BFS <= 2 hops, min-hop dedupe,
sort by (hops, id), cap 30; context = seeds + walked, cap 15) — matching
graph_store.walk_2hop + graph_rag.graph_rag; Aura is not needed.

Writes results/musique-distractor.jsonl (same schema as musique-v3.jsonl).
Resumable: already-answered (query, repeat) pairs are skipped.
"""
from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

CHUNKS = ROOT / "data" / "musique" / "chunks.jsonl"
EDGES = ROOT / "data" / "musique" / "edges.jsonl"
TRACE = ROOT / "results" / "musique-v3-patched.jsonl"
OUT = ROOT / "results" / "musique-distractor.jsonl"

K_SEEDS = 8
MAX_CONTEXT = 15
WALK_MAX = 30

GROUNDED_SYSTEM_PROMPT = """You are an aerospace requirements engineer answering questions about a DOORS-exported requirements set.
Rules:
 1. Ground every claim in retrieved requirements; cite the IDs you used inline as [ADS-014].
 2. If the retrieved context does not contain the answer, say so plainly. Do not invent.
 3. Prefer concise, technical wording. Reproduce numeric thresholds (Hz, kt, ft, ms, °) verbatim.
 4. When requirements interact (e.g., FCC <-> ADS), explain the relationship.
"""


def build_augmented_adjacency() -> tuple[dict[str, set[str]], int, int]:
    chunks = [json.loads(l) for l in CHUNKS.open()]
    gold_edges = [json.loads(l) for l in EDGES.open()]

    adj: dict[str, set[str]] = defaultdict(set)
    for e in gold_edges:
        adj[e["source"]].add(e["target"])
        adj[e["target"]].add(e["source"])

    # consecutive-distractor edges per question, mirroring the gold-chain
    # construction ("consecutive supporting paragraphs") for non-gold ones
    by_q: dict[str, list[dict]] = defaultdict(list)
    for c in chunks:
        by_q[str(c["mq_query_idx"])].append(c)
    n_new = 0
    for _, cs in by_q.items():
        distractors = sorted(
            (c["id"] for c in cs if not c["is_supporting"]),
        )
        for a, b in zip(distractors, distractors[1:]):
            if b not in adj[a]:
                adj[a].add(b)
                adj[b].add(a)
                n_new += 1
    return adj, len(gold_edges), n_new


def walk_2hop_local(adj: dict[str, set[str]], seed_ids: list[str]) -> list[dict]:
    seeds = set(seed_ids)
    hop1 = set()
    for s in seed_ids:
        hop1 |= adj.get(s, set())
    hop1 -= seeds
    hop2 = set()
    for n in hop1:
        hop2 |= adj.get(n, set())
    hop2 -= seeds | hop1
    out = [{"id": i, "hops": 1} for i in hop1] + [{"id": i, "hops": 2} for i in hop2]
    out.sort(key=lambda r: (r["hops"], r["id"]))
    return out[:WALK_MAX]


def main() -> int:
    load_dotenv(ROOT / ".env")
    from llm_compat import GPT5Client

    text_by_id = {}
    title_by_id = {}
    for l in CHUNKS.open():
        c = json.loads(l)
        text_by_id[c["id"]] = c["text"]
        title_by_id[c["id"]] = c["title"]

    adj, n_gold, n_new = build_augmented_adjacency()
    print(f"edges: {n_gold} gold + {n_new} distractor")

    done = set()
    if OUT.exists():
        for l in OUT.open():
            r = json.loads(l)
            done.add((r["query"], r["repeat"]))

    rows = [json.loads(l) for l in TRACE.open()]
    g_rows = [r for r in rows if r["pipeline"] == "graphrag"]
    print(f"{len(g_rows)} graphrag rows, {len(done)} already done")

    llm = GPT5Client()
    out_f = OUT.open("a")
    for r in tqdm(g_rows, unit="row", ncols=100):
        if (r["query"], r["repeat"]) in done:
            continue
        seeds = [s for s in r["source_ids"].split(";") if s][:K_SEEDS]
        walked = walk_2hop_local(adj, seeds)
        ctx_ids = list(dict.fromkeys(seeds + [w["id"] for w in walked]))[:MAX_CONTEXT]
        context = "\n\n---\n\n".join(
            f"[{i}] ({title_by_id.get(i, '')})\n{text_by_id.get(i, '')}" for i in ctx_ids
        )
        user_msg = (
            f"Context (top-{len(seeds)} retrieved + graph-expanded neighbors):\n\n"
            f"{context}\n\nQ: {r['query']}"
        )
        t0 = time.time()
        try:
            resp = llm.chat(messages=[
                {"role": "system", "content": GROUNDED_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ])
        except Exception as e:  # noqa: BLE001
            print(f"\nERROR on {r['query'][:60]}: {e}", file=sys.stderr)
            continue
        answer = resp.choices[0].message.content or ""
        usage = GPT5Client.usage(resp)
        out_f.write(json.dumps({
            **{k: r[k] for k in ("query", "query_type", "embedder", "reranker")},
            "pipeline": "graphrag",
            "repeat": r["repeat"],
            "latency_ms": int((time.time() - t0) * 1000),
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "cited_ids": "",  # filled by rescore_citations.py
            "source_ids": ";".join(ctx_ids),
            "n_sources": len(ctx_ids),
            "iter_count": 0, "verdict": "", "intent": "",
            "routed_to": "", "route_reason": "",
            "answer": answer,
        }) + "\n")
        out_f.flush()
    out_f.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

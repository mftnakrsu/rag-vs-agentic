#!/usr/bin/env python
"""Post-retrieval mitigation for GraphRAG context flooding (MuSiQue).

The paper characterises flooding -- the walk fills the context at precision
0.12--0.23 while the synthesizer cites at 0.48--0.65 -- but never tries to
suppress it. A reviewer asked the obvious next question: does filtering the
walk's output before synthesis recover context precision, and what does that
do to the recall advantage the walk buys?

Two variants, both applied to the walked neighbours only (vector seeds are
always kept, as in production):

  rerank  embed query + walked chunks with the same Azure embedder used for
          retrieval, keep the top RERANK_KEEP by cosine similarity
  cap     tighten the traversal budget itself (WALK_MAX 30->10, context 15->8)

Run against the gold-edge MuSiQue graph, i.e. the same graph as the main
arm, so the numbers are comparable to musique-v3-patched.jsonl. The walk is
replicated locally (see distractor_control.py); Aura is not needed.

Writes results/musique-mitigation-{variant}.jsonl. Resumable.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

CHUNKS = ROOT / "data" / "musique" / "chunks.jsonl"
EDGES = ROOT / "data" / "musique" / "edges.jsonl"
TRACE = ROOT / "results" / "musique-v3-patched.jsonl"

K_SEEDS = 8
# production settings, overridden by the `cap` variant
MAX_CONTEXT = 15
WALK_MAX = 30
CAP_MAX_CONTEXT = 8
CAP_WALK_MAX = 10
RERANK_KEEP = 5

GROUNDED_SYSTEM_PROMPT = """You are an aerospace requirements engineer answering questions about a DOORS-exported requirements set.
Rules:
 1. Ground every claim in retrieved requirements; cite the IDs you used inline as [ADS-014].
 2. If the retrieved context does not contain the answer, say so plainly. Do not invent.
 3. Prefer concise, technical wording. Reproduce numeric thresholds (Hz, kt, ft, ms, °) verbatim.
 4. When requirements interact (e.g., FCC <-> ADS), explain the relationship.
"""


def gold_adjacency() -> dict[str, set[str]]:
    adj: dict[str, set[str]] = defaultdict(set)
    for l in EDGES.open():
        e = json.loads(l)
        adj[e["source"]].add(e["target"])
        adj[e["target"]].add(e["source"])
    return adj


def walk_2hop_local(adj, seed_ids: list[str], walk_max: int) -> list[str]:
    seeds = set(seed_ids)
    hop1: set[str] = set()
    for s in seed_ids:
        hop1 |= adj.get(s, set())
    hop1 -= seeds
    hop2: set[str] = set()
    for n in hop1:
        hop2 |= adj.get(n, set())
    hop2 -= seeds | hop1
    out = [{"id": i, "hops": 1} for i in hop1] + [{"id": i, "hops": 2} for i in hop2]
    out.sort(key=lambda r: (r["hops"], r["id"]))
    return [r["id"] for r in out[:walk_max]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=["rerank", "cap"], required=True)
    args = ap.parse_args()
    load_dotenv(ROOT / ".env")
    from llm_compat import GPT5Client

    out_path = ROOT / "results" / f"musique-mitigation-{args.variant}.jsonl"
    text_by_id, title_by_id = {}, {}
    for l in CHUNKS.open():
        c = json.loads(l)
        text_by_id[c["id"]] = c["text"]
        title_by_id[c["id"]] = c["title"]

    adj = gold_adjacency()
    walk_max = CAP_WALK_MAX if args.variant == "cap" else WALK_MAX
    max_ctx = CAP_MAX_CONTEXT if args.variant == "cap" else MAX_CONTEXT

    embedder = None
    if args.variant == "rerank":
        from embedders import get_embedder
        embedder = get_embedder("azure")

    done = set()
    if out_path.exists():
        for l in out_path.open():
            r = json.loads(l)
            done.add((r["query"], r["repeat"]))

    rows = [json.loads(l) for l in TRACE.open() if json.loads(l)["pipeline"] == "graphrag"]
    print(f"variant={args.variant}  {len(rows)} graphrag rows, {len(done)} already done")

    llm = GPT5Client()
    out_f = out_path.open("a")
    for r in tqdm(rows, unit="row", ncols=100):
        if (r["query"], r["repeat"]) in done:
            continue
        seeds = [s for s in r["source_ids"].split(";") if s][:K_SEEDS]
        walked = [w for w in walk_2hop_local(adj, seeds, walk_max) if w not in seeds]

        if args.variant == "rerank" and walked:
            texts = [text_by_id.get(i, "") for i in walked]
            try:
                qv = np.array(embedder.embed_query(r["query"]), dtype=float)
                cv = np.array(embedder.embed_documents(texts), dtype=float)
            except Exception as e:  # noqa: BLE001
                print(f"\nEMBED ERROR {r['query'][:50]}: {e}", file=sys.stderr)
                continue
            sim = cv @ qv / (np.linalg.norm(cv, axis=1) * np.linalg.norm(qv) + 1e-9)
            walked = [walked[i] for i in np.argsort(-sim)[:RERANK_KEEP]]

        ctx_ids = list(dict.fromkeys(seeds + walked))[:max_ctx]
        context = "\n\n---\n\n".join(
            f"[{i}] ({title_by_id.get(i, '')})\n{text_by_id.get(i, '')}" for i in ctx_ids
        )
        user_msg = (f"Context (top-{len(seeds)} retrieved + graph-expanded neighbors):\n\n"
                    f"{context}\n\nQ: {r['query']}")
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
            "variant": args.variant,
            "repeat": r["repeat"],
            "latency_ms": int((time.time() - t0) * 1000),
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "source_ids": ";".join(ctx_ids),
            "n_sources": len(ctx_ids),
            "answer": answer,
        }) + "\n")
        out_f.flush()
    out_f.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

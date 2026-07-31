#!/usr/bin/env python
"""Phase F-1: Build MuSiQue 200-query stratified corpus.

Source: dgslibisey/MuSiQue (validation split, answerable only)
Sample: 67×2hop + 67×3hop + 66×4hop, seed=20260511
Hop mapping: 2hop→1-hop, 3hop→2-hop, 4hop→3+-hop
Output schema matches data/eval/queries-hop-stratified.jsonl so compare.py
can ingest it via --queries-jsonl.

Outputs:
  data/musique/queries.jsonl   (200 queries with expected_ids = supporting MQ-* IDs)
  data/musique/chunks.jsonl    (~4000 paragraphs as chunks with MQ-* IDs)
  data/musique/edges.jsonl     (REFERENCES edges between consecutive supporting paras)
"""
import json
import random
from collections import Counter
from pathlib import Path

from datasets import load_dataset

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "musique"

HOP_MAP = {"2hop": "1-hop", "3hop": "2-hop", "4hop": "3+-hop"}
HOP_COUNT_MAP = {"2hop": 1, "3hop": 2, "4hop": 3}
SAMPLE_SIZES = {"2hop": 67, "3hop": 67, "4hop": 66}
SEED = 20260511


def hop_class(ex):
    prefix = ex["id"].split("__")[0]
    if prefix.startswith("2hop"): return "2hop"
    if prefix.startswith("3hop"): return "3hop"
    if prefix.startswith("4hop"): return "4hop"
    return None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ds = load_dataset("dgslibisey/MuSiQue", split="validation")
    ds = ds.filter(lambda x: x["answerable"])

    by_hop = {"2hop": [], "3hop": [], "4hop": []}
    for ex in ds:
        h = hop_class(ex)
        if h:
            by_hop[h].append(ex)
    print(f"available: {[(k, len(v)) for k, v in by_hop.items()]}")

    rng = random.Random(SEED)
    selected = []
    for h, n in SAMPLE_SIZES.items():
        pool = list(by_hop[h])
        rng.shuffle(pool)
        selected.extend(pool[:n])
    print(f"selected: {len(selected)}")

    queries, chunks, edges = [], [], []
    for q_idx, ex in enumerate(selected):
        mq_id = ex["id"]
        h = hop_class(ex)
        stratum = HOP_MAP[h]
        question = ex["question"]
        answer = ex["answer"]

        para_ids = []
        supporting_ids = []
        for p_idx, p in enumerate(ex["paragraphs"]):
            chunk_id = f"MQ-{q_idx:03d}-P{p_idx:02d}"
            para_ids.append(chunk_id)
            chunk_text = f"{p['title']}: {p['paragraph_text']}"
            chunks.append({
                "id": chunk_id,
                "text": chunk_text,
                "title": p["title"],
                "is_supporting": bool(p["is_supporting"]),
                "mq_query_id": mq_id,
                "mq_query_idx": q_idx,
            })
            if p["is_supporting"]:
                supporting_ids.append(chunk_id)

        # REFERENCES edges between consecutive supporting paragraphs (chain)
        for i in range(len(supporting_ids) - 1):
            edges.append({
                "source": supporting_ids[i],
                "target": supporting_ids[i + 1],
                "rel_type": "REFERENCES",
            })

        queries.append({
            "query": question,
            "type": stratum,
            "hop_count": HOP_COUNT_MAP[h],
            "rel_path": ["REFERENCES"],
            "expected_ids": supporting_ids,
            "source_id": supporting_ids[0] if supporting_ids else "",
            "target_id": supporting_ids[-1] if supporting_ids else "",
            "source_module": "MUSIQUE",
            "target_module": "MUSIQUE",
            "is_cross_module": False,
            "mq_id": mq_id,
            "mq_answer": answer,
        })

    with open(OUT / "queries.jsonl", "w") as f:
        for q in queries:
            f.write(json.dumps(q) + "\n")
    with open(OUT / "chunks.jsonl", "w") as f:
        for c in chunks:
            f.write(json.dumps(c) + "\n")
    with open(OUT / "edges.jsonl", "w") as f:
        for e in edges:
            f.write(json.dumps(e) + "\n")

    print(f"wrote {OUT}/queries.jsonl ({len(queries)})")
    print(f"wrote {OUT}/chunks.jsonl ({len(chunks)})")
    print(f"wrote {OUT}/edges.jsonl ({len(edges)})")
    print(f"stratum dist: {Counter(q['type'] for q in queries)}")
    print(f"supporting paragraphs per query stats:")
    s_counts = [len(q['expected_ids']) for q in queries]
    print(f"  min={min(s_counts)} max={max(s_counts)} mean={sum(s_counts)/len(s_counts):.2f}")


if __name__ == "__main__":
    main()

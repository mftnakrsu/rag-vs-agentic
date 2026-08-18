#!/usr/bin/env python
"""Build a 200-query stratified 2WikiMultihopQA corpus (third corpus, D1).

Source: voidful/2WikiMultihopQA (validation split)
Reviewers asked for more than two corpora. MuSiQue and this share Wikipedia
prose, but 2Wiki's questions are built from explicit relation chains, which
gives a hop stratification grounded in reasoning structure rather than in
paragraph count.

2Wiki carries 2 or 4 supporting titles and never 3, so the strata come from
the reasoning type instead:
    comparison                  two independent lookups, then compare  -> 1-hop
    compositional / inference   chained: the 2nd needs the 1st's answer -> 2-hop
    bridge_comparison           bridge on both sides, 4 evidences       -> 3+-hop

Output schema matches data/eval/queries-hop-stratified.jsonl and the MuSiQue
build, so the judging and scoring scripts ingest it unchanged.

Outputs:
  data/twowiki/queries.jsonl   200 queries, expected_ids = supporting 2W-* IDs
  data/twowiki/chunks.jsonl    ~2000 paragraphs as chunks
  data/twowiki/edges.jsonl     REFERENCES edges between consecutive supporting paras
"""
import json
import random
from collections import Counter
from pathlib import Path

from datasets import load_dataset

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "twowiki"

STRATUM_OF = {
    "comparison": "1-hop",
    "compositional": "2-hop",
    "inference": "2-hop",
    "bridge_comparison": "3+-hop",
}
HOP_COUNT = {"1-hop": 1, "2-hop": 2, "3+-hop": 3}
SAMPLE_SIZES = {"1-hop": 67, "2-hop": 67, "3+-hop": 66}
SEED = 20260816


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ds = load_dataset("voidful/2WikiMultihopQA", split="validation")

    by_stratum = {"1-hop": [], "2-hop": [], "3+-hop": []}
    for ex in ds:
        s = STRATUM_OF.get(ex["type"])
        if s:
            by_stratum[s].append(ex)
    print(f"available: {[(k, len(v)) for k, v in by_stratum.items()]}")

    rng = random.Random(SEED)
    selected = []
    for s, n in SAMPLE_SIZES.items():
        pool = list(by_stratum[s])
        rng.shuffle(pool)
        selected.extend(pool[:n])
    rng.shuffle(selected)
    print(f"selected: {len(selected)}")

    queries, chunks, edges = [], [], []
    for q_idx, ex in enumerate(selected):
        stratum = STRATUM_OF[ex["type"]]
        supporting_titles = {t for t, _ in ex["supporting_facts"]}

        supporting_ids = []
        for p_idx, (title, sents) in enumerate(ex["context"]):
            chunk_id = f"2W-{q_idx:03d}-P{p_idx:02d}"
            is_sup = title in supporting_titles
            chunks.append({
                "id": chunk_id,
                "text": f"{title}: {' '.join(sents)}",
                "title": title,
                "is_supporting": is_sup,
                "mq_query_id": ex["_id"],
                "mq_query_idx": q_idx,
            })
            if is_sup:
                supporting_ids.append(chunk_id)

        for i in range(len(supporting_ids) - 1):
            edges.append({"source": supporting_ids[i],
                          "target": supporting_ids[i + 1],
                          "rel_type": "REFERENCES"})

        queries.append({
            "query": ex["question"],
            "type": stratum,
            "hop_count": HOP_COUNT[stratum],
            "rel_path": ["REFERENCES"],
            "expected_ids": supporting_ids,
            "source_id": supporting_ids[0] if supporting_ids else "",
            "target_id": supporting_ids[-1] if supporting_ids else "",
            "source_module": "2WIKI",
            "target_module": "2WIKI",
            "is_cross_module": False,
            "mq_id": ex["_id"],
            "mq_answer": ex["answer"],
            "reasoning_type": ex["type"],
        })

    for name, rows in (("queries", queries), ("chunks", chunks), ("edges", edges)):
        with (OUT / f"{name}.jsonl").open("w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        print(f"wrote {OUT}/{name}.jsonl ({len(rows)})")

    print(f"stratum dist: {Counter(q['type'] for q in queries)}")
    s = [len(q["expected_ids"]) for q in queries]
    print(f"supporting paras/query: min={min(s)} max={max(s)} mean={sum(s)/len(s):.2f}")
    empty = sum(1 for q in queries if not q["expected_ids"])
    print(f"queries with no gold: {empty}")


if __name__ == "__main__":
    main()

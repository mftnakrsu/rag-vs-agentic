#!/usr/bin/env python
"""Rescore a results trace with answer-parsed citations.

The original matrix logged cited_ids inconsistently: vanilla and graphrag
recorded the retrieved-context IDs, while the agentic pipelines parsed
IDs out of the answer text. ALCE-style citation metrics are defined over
the answer, so this script re-derives cited_ids uniformly from the stored
answer text (traces in results/*.jsonl carry the full answers) and
recomputes citation P/R/F1. The context-set precision that graphrag's old
numbers actually measured is kept as a separate column, context_precision.

Usage:
    python scripts/rescore_citations.py results/main-v3.jsonl \
        --queries data/eval/queries-hop-stratified.jsonl \
        --corpus data/synthetic/requirements.jsonl \
        --out results/main-v3-scored.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aerorag.eval_metrics import (  # noqa: E402
    citation_f1,
    citation_precision,
    citation_recall,
    make_citation_parser,
    retrieval_recall,
)

CSV_FIELDS = [
    "query", "query_type", "pipeline", "embedder", "reranker", "repeat",
    "latency_ms", "prompt_tokens", "completion_tokens", "total_tokens",
    "cited_ids", "source_ids", "n_sources", "iter_count", "verdict",
    "intent", "routed_to", "route_reason",
    "citation_precision", "citation_recall", "citation_f1",
    "retrieval_recall", "context_precision",
    "n_cited", "n_gold", "hop_count", "stratum", "is_cross_module",
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("trace", type=Path, help="results jsonl with answer text")
    ap.add_argument("--queries", type=Path, required=True)
    ap.add_argument("--corpus", type=Path, required=True,
                    help="jsonl with one {'id': ...} per line (ID vocabulary)")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    corpus_ids = [json.loads(l)["id"] for l in args.corpus.open() if l.strip()]
    parse = make_citation_parser(corpus_ids)

    gold_by_query: dict[str, dict] = {}
    for line in args.queries.open():
        if line.strip():
            rec = json.loads(line)
            gold_by_query[rec["query"]] = rec

    n_out = n_skip = 0
    with args.out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        w.writeheader()
        for line in args.trace.open():
            r = json.loads(line)
            gold = gold_by_query.get(r.get("query", ""))
            if gold is None:
                n_skip += 1
                continue
            gold_ids = set(gold.get("expected_ids") or [])
            cited = parse(r.get("answer"))
            sources = {s for s in (r.get("source_ids") or "").split(";") if s}
            p = citation_precision(set(cited), gold_ids)
            rec = citation_recall(set(cited), gold_ids)
            w.writerow({
                **{k: r.get(k, "") for k in CSV_FIELDS[:18]},
                "cited_ids": ";".join(cited),
                "citation_precision": round(p, 4),
                "citation_recall": round(rec, 4),
                "citation_f1": round(citation_f1(p, rec), 4),
                "retrieval_recall": round(retrieval_recall(sources, gold_ids), 4),
                "context_precision": round(citation_precision(sources, gold_ids), 4),
                "n_cited": len(cited),
                "n_gold": len(gold_ids),
                "hop_count": gold.get("hop_count", 0),
                "stratum": gold.get("type", ""),
                "is_cross_module": bool(gold.get("is_cross_module", False)),
            })
            n_out += 1
    print(f"{args.out}: {n_out} rows scored, {n_skip} skipped (no gold)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Run the ablation matrix and emit a comparison table + CSV/JSONL.

Default matrix (10 configs in the paper-extension version):
    vanilla   × {local, azure} × {none, local-bge, azure-cohere}    = 6
    agentic   × {local, azure}                                      = 2
    graphrag  × {local, azure}                                      = 2

`graphrag` is Phase 1b — vector retrieve seeds + Aura 1-2 hop walk on
traceability edges. It needs NEO4J_URI/USER/PASSWORD in .env. Agentic-graph
(pipeline 4) extends agentic_rag with a graph_lookup tool and lands in
Phase 1c.

Reranker policy: vanilla can use {none, local-bge, azure-cohere}; agentic
intentionally has no external reranker (the critic+ReAct loop is the
filtering mechanism we compare AGAINST a reranker). graphrag also runs
without a reranker — the structural walk is the filtering mechanism.

CLI flags let you cut/extend this matrix:
    python compare.py --limit 3                       # 3 queries
    python compare.py --embedders local --no-azure-rerank
    python compare.py --no-agentic                    # vanilla + graphrag only
    python compare.py --no-graphrag                   # vanilla + agentic only
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import time
import traceback
from pathlib import Path  # noqa: F401  (used by --queries-jsonl)

from dotenv import load_dotenv
from tabulate import tabulate

from agentic_rag import run_agentic_rag
from eval_queries import EVAL_QUERIES
from vanilla_rag import vanilla_rag


def build_configs(
    embedders: list[str],
    *,
    include_norerank: bool = True,
    include_local_rerank: bool = True,
    include_azure_rerank: bool = True,
    include_agentic: bool = True,
    include_graphrag: bool = True,
    include_agentic_graph: bool = True,
) -> list[dict]:
    cfgs: list[dict] = []
    for emb in embedders:
        if include_norerank:
            cfgs.append({"pipeline": "vanilla", "embedder": emb, "reranker": None})
        if include_local_rerank:
            cfgs.append({"pipeline": "vanilla", "embedder": emb, "reranker": "local"})
        if include_azure_rerank:
            cfgs.append({"pipeline": "vanilla", "embedder": emb, "reranker": "azure"})
        if include_agentic:
            cfgs.append({"pipeline": "agentic", "embedder": emb, "reranker": None})
        if include_graphrag:
            cfgs.append({"pipeline": "graphrag", "embedder": emb, "reranker": None})
        if include_agentic_graph:
            cfgs.append({"pipeline": "agentic-graph", "embedder": emb, "reranker": None})
    return cfgs


def run_one(cfg: dict, query: str) -> dict:
    if cfg["pipeline"] == "vanilla":
        return vanilla_rag(
            query,
            embedder_name=cfg["embedder"],
            reranker_name=cfg["reranker"],
        )
    if cfg["pipeline"] == "graphrag":
        from graph_rag import graph_rag
        return graph_rag(query, embedder_name=cfg["embedder"])
    if cfg["pipeline"] == "agentic-graph":
        return run_agentic_rag(query, embedder_name=cfg["embedder"], use_graph=True)
    return run_agentic_rag(query, embedder_name=cfg["embedder"])


def _row_from_result(q: dict, cfg: dict, r: dict) -> dict:
    sources = r.get("sources") or []
    return {
        "query": q["query"],
        "query_type": q["type"],
        "pipeline": cfg["pipeline"],
        "embedder": cfg["embedder"],
        "reranker": cfg["reranker"] or "none",
        "latency_ms": r["latency_ms"],
        "prompt_tokens": r["tokens"].get("prompt_tokens", 0),
        "completion_tokens": r["tokens"].get("completion_tokens", 0),
        "total_tokens": r["tokens"].get("total_tokens", 0),
        "cited_ids": ";".join(r.get("cited_ids") or []),
        "source_ids": ";".join(s["id"] for s in sources),
        "n_sources": len(sources),
        "iter_count": r.get("iter_count", 0),
        "verdict": r.get("verdict", ""),
        "intent": r.get("intent", ""),
        "answer": r.get("answer", ""),
    }


def _row_for_error(q: dict, cfg: dict, exc: Exception) -> dict:
    return {
        "query": q["query"],
        "query_type": q["type"],
        "pipeline": cfg["pipeline"],
        "embedder": cfg["embedder"],
        "reranker": cfg["reranker"] or "none",
        "latency_ms": -1,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "cited_ids": "",
        "source_ids": "",
        "n_sources": 0,
        "iter_count": 0,
        "verdict": "",
        "intent": "",
        "answer": f"ERROR: {type(exc).__name__}: {exc}",
    }


def print_summary(rows: list[dict]) -> None:
    by_config: dict[str, dict] = {}
    for r in rows:
        key = f"{r['pipeline']}|{r['embedder']}|{r['reranker']}"
        agg = by_config.setdefault(key, {"n": 0, "ok": 0, "lat": 0, "tok": 0, "cited": 0})
        agg["n"] += 1
        if r["latency_ms"] >= 0:
            agg["ok"] += 1
            agg["lat"] += r["latency_ms"]
            agg["tok"] += r["total_tokens"]
            agg["cited"] += len([x for x in r["cited_ids"].split(";") if x])

    table = []
    for k, agg in sorted(by_config.items()):
        n_ok = agg["ok"]
        denom = max(n_ok, 1)
        table.append([
            k,
            f"{agg['ok']}/{agg['n']}",
            f"{agg['lat'] / denom:.0f}",
            f"{agg['tok'] / denom:.0f}",
            f"{agg['cited'] / denom:.1f}",
        ])
    print("\n--- Aggregate per config ---")
    print(tabulate(
        table,
        headers=["Config (pipeline|embedder|reranker)", "ok/N", "Avg ms", "Avg tok", "Avg cited"],
    ))

    detail = [[
        r["query"][:48] + ("…" if len(r["query"]) > 48 else ""),
        r["pipeline"][:7],
        r["embedder"][:5],
        r["reranker"][:5],
        r["latency_ms"],
        r["total_tokens"],
        r["cited_ids"][:32],
    ] for r in rows]
    print("\n--- Per-query × per-config ---")
    print(tabulate(
        detail,
        headers=["Query", "Pipeline", "Emb", "Rrk", "ms", "Tok", "Cited"],
    ))


CSV_SHORT_KEYS = [
    "query", "query_type", "pipeline", "embedder", "reranker",
    "latency_ms", "prompt_tokens", "completion_tokens", "total_tokens",
    "cited_ids", "source_ids", "n_sources", "iter_count", "verdict", "intent",
]


class IncrementalWriter:
    """Stream rows to CSV + JSONL as they complete (vs the old end-of-run dump).

    Required for long-running matrix evaluations (Phase 2d ~4-5 hours): if
    the process is killed mid-run we keep all completed rows on disk. flush()
    on every write pushes to OS buffer; we fsync periodically (every 25 rows)
    to commit to physical storage in case of kernel panic.
    """

    def __init__(self, csv_path: str, *, fsync_every: int = 25) -> None:
        Path(os.path.dirname(csv_path) or ".").mkdir(parents=True, exist_ok=True)
        self.csv_path = csv_path
        self.jsonl_path = csv_path.rsplit(".", 1)[0] + ".jsonl"
        self._fsync_every = fsync_every
        self._csv_f = open(csv_path, "w", newline="", encoding="utf-8")
        self._csv_w = csv.DictWriter(
            self._csv_f, fieldnames=CSV_SHORT_KEYS, extrasaction="ignore",
        )
        self._csv_w.writeheader()
        self._csv_f.flush()
        self._jsonl_f = open(self.jsonl_path, "w", encoding="utf-8")
        self.n = 0

    def write(self, row: dict) -> None:
        self._csv_w.writerow(row)
        self._csv_f.flush()
        self._jsonl_f.write(json.dumps(row, ensure_ascii=False) + "\n")
        self._jsonl_f.flush()
        self.n += 1
        if self.n % self._fsync_every == 0:
            os.fsync(self._csv_f.fileno())
            os.fsync(self._jsonl_f.fileno())

    def close(self) -> None:
        try:
            os.fsync(self._csv_f.fileno())
            os.fsync(self._jsonl_f.fileno())
        except OSError:
            pass
        self._csv_f.close()
        self._jsonl_f.close()
        print(f"\nWrote {self.n} rows -> {self.csv_path} (+ JSONL with full answers)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None,
                        help="Run only the first N queries (debug)")
    parser.add_argument("--embedders", default="local,azure",
                        help="Comma-separated: local,azure")
    parser.add_argument("--no-norerank", action="store_true",
                        help="Skip the no-rerank baseline rows")
    parser.add_argument("--no-local-rerank", action="store_true")
    parser.add_argument("--no-azure-rerank", action="store_true")
    parser.add_argument("--no-agentic", action="store_true")
    parser.add_argument("--no-graphrag", action="store_true",
                        help="Skip the graphrag pipeline (needs Neo4j Aura)")
    parser.add_argument("--no-agentic-graph", action="store_true",
                        help="Skip agentic-graph pipeline (LangGraph + graph_lookup tool)")
    parser.add_argument("--queries-jsonl", type=Path, default=None,
                        help="Override built-in eval_queries with a JSONL file. "
                             "Each row needs at minimum a 'query' field; 'type' is "
                             "optional (defaults to 'unknown'). Used for the Phase 2d "
                             "300-query hop-stratified main matrix.")
    parser.add_argument("--out", default="results/results.csv")
    args = parser.parse_args()

    load_dotenv()

    if args.queries_jsonl:
        if not args.queries_jsonl.exists():
            raise SystemExit(f"queries file not found: {args.queries_jsonl}")
        with args.queries_jsonl.open(encoding="utf-8") as f:
            queries = [json.loads(line) for line in f if line.strip()]
        # _row_from_result needs q['type']; fall back so older manifests work.
        for q in queries:
            q.setdefault("type", "unknown")
        print(f"Loaded {len(queries)} queries from {args.queries_jsonl}")
    else:
        queries = EVAL_QUERIES
    if args.limit is not None:
        queries = queries[: args.limit]
    embedders = [e.strip() for e in args.embedders.split(",") if e.strip()]

    cfgs = build_configs(
        embedders,
        include_norerank=not args.no_norerank,
        include_local_rerank=not args.no_local_rerank,
        include_azure_rerank=not args.no_azure_rerank,
        include_agentic=not args.no_agentic,
        include_graphrag=not args.no_graphrag,
        include_agentic_graph=not args.no_agentic_graph,
    )

    total = len(cfgs) * len(queries)
    print(f"Running {total} combinations: {len(cfgs)} configs × {len(queries)} queries")
    for i, c in enumerate(cfgs, 1):
        print(f"  cfg{i}: {c['pipeline']:8s}  emb={c['embedder']:5s}  "
              f"rerank={c['reranker'] or '—'}")
    print()

    rows: list[dict] = []
    writer = IncrementalWriter(args.out)
    n = 0
    t_total0 = time.time()
    try:
        for q in queries:
            for cfg in cfgs:
                n += 1
                tag = f"[{n:>3}/{total}] {cfg['pipeline']:7s} | {cfg['embedder']:5s} | rerank={cfg['reranker'] or '—':5s}"
                print(f"{tag} | {q['query'][:60]}")
                try:
                    r = run_one(cfg, q["query"])
                    row = _row_from_result(q, cfg, r)
                    rows.append(row)
                    writer.write(row)
                    tot_tok = r["tokens"].get("total_tokens", 0)
                    print(f"    -> {r['latency_ms']}ms  {tot_tok} tok  cited={len(r.get('cited_ids') or [])}")
                except Exception as e:  # noqa: BLE001
                    print(f"    -> ERROR {type(e).__name__}: {e}")
                    traceback.print_exc()
                    err_row = _row_for_error(q, cfg, e)
                    rows.append(err_row)
                    writer.write(err_row)
    finally:
        writer.close()

    elapsed = time.time() - t_total0
    print(f"\nDone in {elapsed:.0f}s")

    print_summary(rows)


if __name__ == "__main__":
    main()

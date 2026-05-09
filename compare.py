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
    include_adaptive: bool = True,
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
        if include_adaptive:
            cfgs.append({"pipeline": "adaptive", "embedder": emb, "reranker": None})
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
    if cfg["pipeline"] == "adaptive":
        from hop_router import adaptive_rag
        return adaptive_rag(query, embedder_name=cfg["embedder"])
    return run_agentic_rag(query, embedder_name=cfg["embedder"])


# String fragments that indicate a transient (retry-worthy) failure during
# a long-running matrix run. These are checked against str(exception) so they
# match wrapped errors too. Order doesn't matter; any match → retry.
TRANSIENT_ERROR_INDICATORS: tuple[str, ...] = (
    "Cannot resolve address",       # neo4j DNS fail
    "Connection error",             # openai SDK
    "APIConnectionError",           # openai SDK class
    "ConnectionError",              # generic Python
    "ConnectionResetError",         # socket reset
    "ConnectTimeout",               # httpx
    "ReadTimeout",                  # httpx
    "ServiceUnavailable",           # 503
    "RateLimitError",               # 429 — retry with backoff helps
    "internal_error",               # azure transient
    "Aura instance is not available",  # neo4j
    "ServiceUnavailable",           # neo4j 503
    "transport closed",             # neo4j
    "Bolt handshake",               # neo4j re-auth
)


def _is_transient_error(exc: Exception) -> bool:
    s = f"{type(exc).__name__}: {exc}"
    return any(ind in s for ind in TRANSIENT_ERROR_INDICATORS)


def run_one_with_retry(
    cfg: dict, query: str, *,
    max_retries: int = 2,
    retry_wait_s: float = 10.0,
) -> dict:
    """Wrap run_one with bounded retry on transient failures.

    On non-transient (logic) errors, raise immediately so the caller's
    try/except records an ERROR row and the matrix continues. Exponential
    backoff between retries (10s, 20s, 40s).
    """
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return run_one(cfg, query)
        except Exception as e:  # noqa: BLE001
            last_exc = e
            if attempt >= max_retries or not _is_transient_error(e):
                raise
            wait = retry_wait_s * (2 ** attempt)
            print(f"    transient {type(e).__name__}: {str(e)[:80]}; "
                  f"retry {attempt + 1}/{max_retries} in {wait:.0f}s")
            time.sleep(wait)
    # unreachable — last loop iteration either returns or raises
    raise last_exc  # type: ignore[misc]


def load_existing_keys(csv_path: Path) -> set[tuple[str, ...]]:
    """For --resume: read prior CSV and return the set of (pipeline, embedder,
    reranker, query, repeat) tuples already present. New rows whose key is
    in this set are skipped, preserving prior progress.

    Both successful and ERROR rows are skipped on resume — error rows can
    be re-run separately via rerun_errors.py after the matrix completes,
    so we don't double-write rows mid-run.
    """
    keys: set[tuple[str, ...]] = set()
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        return keys
    with csv_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            keys.add((
                row.get("pipeline", ""),
                row.get("embedder", ""),
                row.get("reranker") or "none",
                row.get("query", ""),
                str(row.get("repeat") or "0"),
            ))
    return keys


def _row_from_result(q: dict, cfg: dict, r: dict, *, repeat: int = 0) -> dict:
    sources = r.get("sources") or []
    return {
        "query": q["query"],
        "query_type": q["type"],
        "pipeline": cfg["pipeline"],
        "embedder": cfg["embedder"],
        "reranker": cfg["reranker"] or "none",
        "repeat": repeat,
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
        "routed_to": r.get("routed_to", ""),
        "route_reason": r.get("route_reason", ""),
        "answer": r.get("answer", ""),
    }


def _row_for_error(q: dict, cfg: dict, exc: Exception, *, repeat: int = 0) -> dict:
    return {
        "query": q["query"],
        "query_type": q["type"],
        "pipeline": cfg["pipeline"],
        "embedder": cfg["embedder"],
        "reranker": cfg["reranker"] or "none",
        "repeat": repeat,
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
    "query", "query_type", "pipeline", "embedder", "reranker", "repeat",
    "latency_ms", "prompt_tokens", "completion_tokens", "total_tokens",
    "cited_ids", "source_ids", "n_sources", "iter_count", "verdict", "intent",
    "routed_to", "route_reason",
]


class IncrementalWriter:
    """Stream rows to CSV + JSONL as they complete (vs the old end-of-run dump).

    Required for long-running matrix evaluations (Phase 2d ~17 hours with
    repeats=3): if the process is killed mid-run we keep all completed rows
    on disk. flush() on every write pushes to OS buffer; we fsync periodically
    (every 25 rows) to commit to physical storage in case of kernel panic.

    `append=True` opens the existing files for append (no header rewrite).
    Used by --resume so rerun preserves prior rows.
    """

    def __init__(self, csv_path: str, *, fsync_every: int = 25,
                 append: bool = False) -> None:
        Path(os.path.dirname(csv_path) or ".").mkdir(parents=True, exist_ok=True)
        self.csv_path = csv_path
        self.jsonl_path = csv_path.rsplit(".", 1)[0] + ".jsonl"
        self._fsync_every = fsync_every
        if append and Path(csv_path).exists() and Path(csv_path).stat().st_size > 0:
            self._csv_f = open(csv_path, "a", newline="", encoding="utf-8")
            self._csv_w = csv.DictWriter(
                self._csv_f, fieldnames=CSV_SHORT_KEYS, extrasaction="ignore",
            )
            # no header — already written by prior run
            self._jsonl_f = open(self.jsonl_path, "a", encoding="utf-8")
        else:
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
    parser.add_argument("--no-adaptive", action="store_true",
                        help="Skip the adaptive pipeline (hop-adaptive router)")
    parser.add_argument("--repeats", type=int, default=1,
                        help="Repeat each (cfg, query) combination N times to "
                             "estimate variance under non-deterministic decoding "
                             "(GPT-5.4 only accepts temperature=1.0). Default 1. "
                             "CIKM main matrix uses 3.")
    parser.add_argument("--resume", action="store_true",
                        help="If --out CSV exists, append-mode and skip "
                             "(pipeline, embedder, reranker, query, repeat) "
                             "tuples already present. Allows safe kill+restart.")
    parser.add_argument("--retries", type=int, default=2,
                        help="Per-row retry count on transient errors "
                             "(network/DNS/timeout/rate-limit). Default 2.")
    parser.add_argument("--retry-wait-s", type=float, default=10.0,
                        help="Base wait between retries (exponential backoff). Default 10s.")
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
        include_adaptive=not args.no_adaptive,
    )

    repeats = max(1, args.repeats)
    total = len(cfgs) * len(queries) * repeats

    existing_keys: set[tuple[str, ...]] = set()
    if args.resume:
        existing_keys = load_existing_keys(Path(args.out))
        print(f"Resume mode: {len(existing_keys)} rows already in {args.out}")

    print(f"Running {total} combinations: {len(cfgs)} configs × {len(queries)} queries × {repeats} repeats")
    for i, c in enumerate(cfgs, 1):
        print(f"  cfg{i}: {c['pipeline']:8s}  emb={c['embedder']:5s}  "
              f"rerank={c['reranker'] or '—'}")
    print()

    rows: list[dict] = []
    writer = IncrementalWriter(args.out, append=args.resume)
    n = 0
    n_skipped = 0
    n_attempted = 0
    t_total0 = time.time()
    try:
        for rep in range(repeats):
            for q in queries:
                for cfg in cfgs:
                    n += 1
                    key = (
                        cfg["pipeline"],
                        cfg["embedder"],
                        cfg["reranker"] or "none",
                        q["query"],
                        str(rep),
                    )
                    if key in existing_keys:
                        n_skipped += 1
                        continue
                    n_attempted += 1
                    tag = (f"[{n:>4}/{total}] r{rep} "
                           f"{cfg['pipeline']:13s} | {cfg['embedder']:5s} | "
                           f"rerank={cfg['reranker'] or '—':5s}")
                    print(f"{tag} | {q['query'][:60]}")
                    try:
                        r = run_one_with_retry(
                            cfg, q["query"],
                            max_retries=args.retries,
                            retry_wait_s=args.retry_wait_s,
                        )
                        row = _row_from_result(q, cfg, r, repeat=rep)
                        rows.append(row)
                        writer.write(row)
                        tot_tok = r["tokens"].get("total_tokens", 0)
                        print(f"    -> {r['latency_ms']}ms  {tot_tok} tok  cited={len(r.get('cited_ids') or [])}")
                    except Exception as e:  # noqa: BLE001
                        print(f"    -> ERROR {type(e).__name__}: {e}")
                        traceback.print_exc()
                        err_row = _row_for_error(q, cfg, e, repeat=rep)
                        rows.append(err_row)
                        writer.write(err_row)
    finally:
        writer.close()
        if args.resume:
            print(f"Resume summary: skipped {n_skipped} (already done), attempted {n_attempted}")

    elapsed = time.time() - t_total0
    print(f"\nDone in {elapsed:.0f}s")

    print_summary(rows)


if __name__ == "__main__":
    main()

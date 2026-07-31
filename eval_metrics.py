"""Per-row evaluation metrics for the comparison matrix.

Phase 2b — joins the hop-stratified query manifest with the results CSV
and emits enriched scores per row.

Metrics:
  - citation_precision  = |cited_ids ∩ expected_ids| / |cited_ids|
  - citation_recall     = |cited_ids ∩ expected_ids| / |expected_ids|
  - citation_f1         = harmonic mean
  - retrieval_recall    = |source_ids ∩ expected_ids| / |expected_ids|
                          (whether the retriever surfaces the gold chain at all,
                           independent of which ones the synthesizer cites)

  - ragas_faithfulness  = RAGAS LLM-as-judge faithfulness score
                          (only computed when --ragas flag is set; expensive)

The query→record join is by exact `query` string match — eval_generator.py
writes the canonical question text and compare.py copies it through.

Output:
  Reads:  results/<name>.csv + data/eval/<queries>.jsonl
  Writes: results/<name>-scored.csv (same schema + score columns)

Deferred for now (would help, but require infra that's not blocking the
paper's headline narrative):
  - ARES PPI confidence intervals (bigger N would justify; bootstrap is
    sufficient at N=300 per stratum).
  - Human dual-rater κ on a 100-query sample (would land Phase 4 if we
    have time).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Iterable


def make_citation_parser(corpus_ids: Iterable[str]):
    """Build an answer-text citation parser for a given ID vocabulary.

    Matches exact corpus IDs (longest-first, so ALX2-AUTO-001 wins over
    AUTO-001) plus hallucinated near-IDs that reuse a real module prefix
    (e.g. HMI-105 when HMI-105 does not exist) — those count against
    citation precision, as in ALCE. Non-corpus tokens that merely look
    like IDs (SHA-256, DO-254, RS-422) are ignored.
    """
    import re
    ids = sorted(set(corpus_ids), key=len, reverse=True)
    vocab_re = re.compile(r"\b(?:" + "|".join(re.escape(i) for i in ids) + r")\b")
    prefixes = sorted({i.split("-")[0] for i in ids}, key=len, reverse=True)
    halluc_re = re.compile(
        r"\b(?:" + "|".join(re.escape(p) for p in prefixes) + r")-[A-Z0-9_-]*\d\b"
    )

    def parse(answer: str | None) -> list[str]:
        found = list(dict.fromkeys(vocab_re.findall(answer or "")))
        rest = vocab_re.sub(" ", answer or "")
        found += [m for m in dict.fromkeys(halluc_re.findall(rest)) if m not in found]
        return found

    return parse


def _split_ids(s: str | None) -> set[str]:
    """Split a semicolon-joined id field into a set, dropping blanks."""
    if not s:
        return set()
    return {p.strip() for p in s.split(";") if p.strip()}


def citation_precision(cited: set[str], gold: set[str]) -> float:
    if not cited:
        return 0.0
    return len(cited & gold) / len(cited)


def citation_recall(cited: set[str], gold: set[str]) -> float:
    if not gold:
        return 0.0
    return len(cited & gold) / len(gold)


def citation_f1(p: float, r: float) -> float:
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def retrieval_recall(source: set[str], gold: set[str]) -> float:
    """Did the retriever surface the gold chain at all?"""
    if not gold:
        return 0.0
    return len(source & gold) / len(gold)


def load_queries(path: Path) -> dict[str, dict]:
    """Load eval queries JSONL, return {query_text: record}."""
    out: dict[str, dict] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            out[rec["query"]] = rec
    return out


def load_results_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def score_row(result: dict, gold: dict) -> dict:
    """Compute citation + retrieval metrics for one result row given its gold."""
    cited = _split_ids(result.get("cited_ids"))
    sources = _split_ids(result.get("source_ids"))
    gold_ids = set(gold.get("expected_ids") or [])

    p = citation_precision(cited, gold_ids)
    r = citation_recall(cited, gold_ids)
    f1 = citation_f1(p, r)
    rr = retrieval_recall(sources, gold_ids)
    return {
        "citation_precision": round(p, 4),
        "citation_recall": round(r, 4),
        "citation_f1": round(f1, 4),
        "retrieval_recall": round(rr, 4),
        "n_cited": len(cited),
        "n_sources": len(sources),
        "n_gold": len(gold_ids),
        "hop_count": gold.get("hop_count", 0),
        "stratum": gold.get("type", ""),
        "is_cross_module": bool(gold.get("is_cross_module", False)),
    }


def score_all(
    queries_path: Path,
    results_path: Path,
    out_path: Path,
    *,
    ragas: bool = False,
) -> tuple[int, int]:
    """Score every row in `results_path` whose query matches one in
    `queries_path`. Returns (n_scored, n_unmatched)."""
    queries_by_text = load_queries(queries_path)
    rows = load_results_csv(results_path)

    enriched: list[dict] = []
    n_unmatched = 0
    for r in rows:
        q = r.get("query", "")
        gold = queries_by_text.get(q)
        if gold is None:
            n_unmatched += 1
            continue
        score = score_row(r, gold)
        enriched.append({**r, **score})

    if ragas:
        # Lazy-imported only when requested — RAGAS pulls heavy dependencies
        # and configures an LLM judge that we don't always need.
        enriched = _add_ragas(enriched, queries_by_text)

    if enriched:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        keys = list(enriched[0].keys())
        with out_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            w.writerows(enriched)
    return (len(enriched), n_unmatched)


def _add_ragas(enriched: list[dict], queries: dict[str, dict]) -> list[dict]:
    """RAGAS faithfulness scorer. Heavy: requires a judge LLM call per row.

    Stub for now — wires up ragas.metrics.faithfulness once we hit the
    main matrix. Skipping during sanity to keep iteration cheap.
    """
    print("WARN: --ragas requested but scorer is stubbed; emitting NaN.",
          file=sys.stderr)
    for r in enriched:
        r["ragas_faithfulness"] = float("nan")
    return enriched


def aggregate_per_pipeline(scored_path: Path) -> dict:
    """Quick aggregate per pipeline of the scored CSV."""
    with scored_path.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    by_pipeline: dict[str, dict] = {}
    for r in rows:
        key = f"{r['pipeline']}|{r['embedder']}|{r.get('reranker') or 'none'}"
        agg = by_pipeline.setdefault(key, {
            "n": 0, "p_sum": 0.0, "r_sum": 0.0, "f1_sum": 0.0, "rr_sum": 0.0,
        })
        agg["n"] += 1
        agg["p_sum"] += float(r.get("citation_precision", 0) or 0)
        agg["r_sum"] += float(r.get("citation_recall", 0) or 0)
        agg["f1_sum"] += float(r.get("citation_f1", 0) or 0)
        agg["rr_sum"] += float(r.get("retrieval_recall", 0) or 0)
    out = {}
    for k, agg in by_pipeline.items():
        n = max(1, agg["n"])
        out[k] = {
            "n": agg["n"],
            "citation_precision": round(agg["p_sum"] / n, 4),
            "citation_recall": round(agg["r_sum"] / n, 4),
            "citation_f1": round(agg["f1_sum"] / n, 4),
            "retrieval_recall": round(agg["rr_sum"] / n, 4),
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "results_csv", type=Path,
        help="Input results CSV from compare.py (e.g. results/main-v1.csv)",
    )
    parser.add_argument(
        "--queries", type=Path,
        default=Path("data/eval/queries-hop-stratified.jsonl"),
        help="Eval-query manifest JSONL (with expected_ids per query)",
    )
    parser.add_argument(
        "--out", type=Path, default=None,
        help="Output scored CSV path. Default: <input>-scored.csv",
    )
    parser.add_argument(
        "--ragas", action="store_true",
        help="Compute RAGAS faithfulness (expensive — disabled by default)",
    )
    args = parser.parse_args()

    if args.out is None:
        args.out = args.results_csv.with_name(args.results_csv.stem + "-scored.csv")

    if not args.queries.exists():
        print(f"ERROR: queries file not found: {args.queries}", file=sys.stderr)
        return 2
    if not args.results_csv.exists():
        print(f"ERROR: results file not found: {args.results_csv}", file=sys.stderr)
        return 2

    n_scored, n_unmatched = score_all(args.queries, args.results_csv, args.out,
                                       ragas=args.ragas)
    print(f"Scored {n_scored} rows -> {args.out}")
    if n_unmatched:
        print(f"  ({n_unmatched} rows had queries not in the manifest — expected if "
              f"results CSV mixes hand-curated and hop-stratified runs.)")

    if n_scored:
        agg = aggregate_per_pipeline(args.out)
        print("\nPer-pipeline aggregate (citation P/R/F1, retrieval recall):")
        print(f"  {'Pipeline':<35s} {'n':>3s}  {'P':>6s} {'R':>6s} {'F1':>6s} {'RR':>6s}")
        for k, a in sorted(agg.items()):
            print(f"  {k:<35s} {a['n']:>3d}  "
                  f"{a['citation_precision']:>6.3f} {a['citation_recall']:>6.3f} "
                  f"{a['citation_f1']:>6.3f} {a['retrieval_recall']:>6.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

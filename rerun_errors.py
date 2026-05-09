"""Re-run rows in a results CSV that errored on the first pass.

The matrix harness (compare.py) catches per-row exceptions, records them
as `_row_for_error` (latency_ms == -1, answer prefixed with "ERROR:"),
and continues. That's the right call during a 4-5 hour bg matrix — a
transient network blip on row 7 shouldn't kill the other 1,177 runs.

This script picks them up after the fact:

    python rerun_errors.py results/main-v1.csv \\
           --queries data/eval/queries-hop-stratified.jsonl

Identifies error rows by `latency_ms < 0`. For each, reconstructs the
(cfg, query) pair from the CSV columns and the queries manifest, calls
`compare.run_one`, and overwrites the row in place. A timestamped backup
is written before any rewrite so we can roll back if anything goes wrong.

The CSV is rewritten using compare.CSV_SHORT_KEYS (same column order).
The companion JSONL is rewritten in lockstep (single source of truth =
the in-memory rows list, so both files stay aligned).

Usage notes:
- Safe to run while the bg matrix is still in flight: this script only
  touches rows already on disk; it doesn't read what the bg writer is
  about to write. Avoid running it on the *exact* CSV the bg is writing
  to — copy first or wait for bg completion.
- --dry-run: print the error rows without re-running anything.
- Failures persist as ERROR rows; we don't loop / retry within this
  script. Re-invoke if a re-run still fails.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from compare import CSV_SHORT_KEYS, _row_for_error, _row_from_result, run_one


def find_error_indices(rows: list[dict]) -> list[int]:
    """Indices of rows we consider failed (latency_ms < 0 OR ERROR: prefix)."""
    bad: list[int] = []
    for i, r in enumerate(rows):
        try:
            lat = int(r.get("latency_ms", "0") or 0)
        except (TypeError, ValueError):
            lat = 0
        ans = r.get("answer", "") or ""
        if lat < 0 or ans.startswith("ERROR:"):
            bad.append(i)
    return bad


def reconstruct_cfg(row: dict) -> dict:
    rerank = row.get("reranker", "") or ""
    return {
        "pipeline": row["pipeline"],
        "embedder": row["embedder"],
        "reranker": None if rerank in ("", "none", "None") else rerank,
    }


def reconstruct_query_record(row: dict, queries_by_text: dict) -> dict:
    """Rebuild the eval-query record `_row_from_result` expects.

    If we have the queries manifest, use it to recover the structured
    metadata. Otherwise fall back to a minimal record that lets the
    rerun proceed without crashing _row_from_result.
    """
    text = row.get("query", "") or ""
    q = queries_by_text.get(text)
    if q is None:
        return {"query": text, "type": row.get("query_type", "unknown")}
    return q


def load_queries_jsonl(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            out[r["query"]] = r
    return out


def rewrite_csv_and_jsonl(rows: list[dict], csv_path: Path) -> None:
    """Single-source rewrite of CSV (short keys) and matching JSONL."""
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_SHORT_KEYS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    jsonl_path = csv_path.with_suffix(".jsonl")
    with jsonl_path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("results_csv", type=Path,
                        help="Results CSV produced by compare.py")
    parser.add_argument("--queries", type=Path, default=None,
                        help="JSONL manifest used by compare.py (optional but recommended)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show error rows without re-running anything")
    args = parser.parse_args()

    load_dotenv()

    if not args.results_csv.exists():
        print(f"ERROR: not found: {args.results_csv}", file=sys.stderr)
        return 2
    with args.results_csv.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    err_idx = find_error_indices(rows)
    print(f"Found {len(err_idx)} errored rows out of {len(rows)} ({len(err_idx)/max(1, len(rows)):.2%})")
    if not err_idx:
        print("Nothing to do.")
        return 0

    if args.dry_run:
        for i in err_idx[:10]:
            r = rows[i]
            print(f"  [{i:>4d}] {r['pipeline']:14s} {r['embedder']:5s} | "
                  f"{r['query'][:65]}")
            ans = (r.get("answer") or "")[:120]
            if ans:
                print(f"         ans: {ans}")
        if len(err_idx) > 10:
            print(f"  ... + {len(err_idx) - 10} more")
        return 0

    queries_by_text: dict[str, dict] = {}
    if args.queries and args.queries.exists():
        queries_by_text = load_queries_jsonl(args.queries)
        print(f"Loaded {len(queries_by_text)} queries from {args.queries}")
    elif args.queries:
        print(f"WARN: queries file not found: {args.queries}", file=sys.stderr)

    backup = args.results_csv.with_suffix(f".csv.bak.{int(time.time())}")
    shutil.copy(args.results_csv, backup)
    print(f"Backup: {backup}")

    n_recovered = 0
    n_still_failed = 0
    t0 = time.time()
    for n, i in enumerate(err_idx, 1):
        old_row = rows[i]
        cfg = reconstruct_cfg(old_row)
        q = reconstruct_query_record(old_row, queries_by_text)
        print(f"[{n}/{len(err_idx)}] retry {cfg['pipeline']:14s} | {q['query'][:55]}")
        try:
            r = run_one(cfg, q["query"])
            new_row = _row_from_result(q, cfg, r)
            rows[i] = new_row
            n_recovered += 1
            tot_tok = r["tokens"].get("total_tokens", 0)
            print(f"    -> OK {r['latency_ms']}ms  {tot_tok} tok")
        except Exception as e:  # noqa: BLE001
            new_row = _row_for_error(q, cfg, e)
            rows[i] = new_row
            n_still_failed += 1
            print(f"    -> still fails: {type(e).__name__}: {e}")

    rewrite_csv_and_jsonl(rows, args.results_csv)
    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.0f}s. Recovered {n_recovered}/{len(err_idx)}, "
          f"still failed {n_still_failed}.")
    print(f"Rewrote {args.results_csv} (and matching .jsonl). Backup: {backup}")
    return 0 if n_still_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

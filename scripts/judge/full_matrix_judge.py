#!/usr/bin/env python
"""Judge a whole run trace with any subset of {gemini, gpt41, gpt5}.

The published protocol judged 300-row stratified subsets, which leaves
per-stratum n around 33. Judging is an order of magnitude cheaper than
generation, so this judges the full matrix instead and adds Gemini as a
third vendor family (pinned, thinking on -- see multi_judge).

Verdicts land in one CSV per (trace, judge-set), one row per judged tuple,
appended as they complete so the run is resumable after any interruption.
Judging date matters -- verdicts are only comparable within a date, per the
paper's protocol -- so the run date is stamped into every row.

    python scripts/judge/full_matrix_judge.py \
        --trace results/main-v2.jsonl --out results/main-v2-judged-full.csv \
        --judges gemini,gpt41

    # restrict to the pinned 300 tuples of an existing judged CSV
    python scripts/judge/full_matrix_judge.py ... --restrict-to results/main-v2-judged.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

FIELDS = ["query", "pipeline", "repeat", "query_type", "judged_on"]


def key_of(r: dict) -> tuple[str, str, str]:
    return (r["query"], r["pipeline"], str(r["repeat"]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True, help="run trace jsonl")
    ap.add_argument("--out", required=True, help="output csv (appended)")
    ap.add_argument("--judges", default="gemini,gpt41")
    ap.add_argument("--restrict-to", default=None,
                    help="csv whose (query,pipeline,repeat) tuples to keep")
    ap.add_argument("--queries", default="data/eval/queries-hop-stratified.jsonl",
                    help="manifest whose queries define the matrix; traces carry a "
                         "couple of stray smoke-test rows that the scored CSVs drop")
    ap.add_argument("--limit", type=int, default=0, help="smoke-test row cap")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    load_dotenv(ROOT / ".env")
    from multi_judge import (_format_contexts, load_query_chunks,
                             score_with_gemini, score_with_gpt41, score_with_gpt5)

    scorers = {"gemini": score_with_gemini, "gpt41": score_with_gpt41,
               "gpt5": score_with_gpt5}
    judges = [j.strip() for j in args.judges.split(",") if j.strip()]
    for j in judges:
        if j not in scorers:
            print(f"unknown judge: {j}", file=sys.stderr)
            return 2

    chunks = load_query_chunks(ROOT / "data/synthetic/requirements.jsonl")
    rows = [json.loads(l) for l in (ROOT / args.trace).open()]

    if args.queries:
        manifest = {json.loads(l)["query"]
                    for l in (ROOT / args.queries).open()}
        dropped = [r for r in rows if r["query"] not in manifest]
        rows = [r for r in rows if r["query"] in manifest]
        if dropped:
            print(f"dropped {len(dropped)} row(s) not in {args.queries}")

    if args.restrict_to:
        keep = {key_of(r) for r in csv.DictReader((ROOT / args.restrict_to).open())}
        rows = [r for r in rows if key_of(r) in keep]

    out_path = ROOT / args.out
    done: set[tuple[str, str, str]] = set()
    if out_path.exists():
        done = {key_of(r) for r in csv.DictReader(out_path.open())}
    todo = [r for r in rows if key_of(r) not in done]
    if args.limit:
        todo = todo[:args.limit]

    fields = list(FIELDS)
    for j in judges:
        fields += [f"{j}_faithful", f"{j}_reason", f"{j}_tokens"]

    print(f"{args.trace}: {len(rows)} rows, {len(done)} already judged, "
          f"{len(todo)} to go, judges={judges}")
    if not todo:
        return 0

    write_header = not out_path.exists()
    f = out_path.open("a", newline="")
    w = csv.DictWriter(f, fieldnames=fields)
    if write_header:
        w.writeheader()
        f.flush()

    lock = threading.Lock()
    today = date.today().isoformat()
    tokens = {j: 0 for j in judges}
    errors = {j: 0 for j in judges}

    def work(r: dict) -> dict | None:
        ctx = _format_contexts(r.get("source_ids", ""), chunks)
        out = {"query": r["query"], "pipeline": r["pipeline"],
               "repeat": r["repeat"], "query_type": r.get("query_type", ""),
               "judged_on": today}
        for j in judges:
            res = scorers[j](r["query"], ctx, r.get("answer") or "")
            if "faithful" not in res:
                out[f"{j}_faithful"] = ""
                out[f"{j}_reason"] = f"ERROR: {res.get('error', '')[:120]}"
                out[f"{j}_tokens"] = 0
                with lock:
                    errors[j] += 1
            else:
                out[f"{j}_faithful"] = res["faithful"]
                out[f"{j}_reason"] = res["reason"]
                out[f"{j}_tokens"] = res.get("tokens", 0)
                with lock:
                    tokens[j] += res.get("tokens", 0)
        return out

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for out in tqdm(ex.map(work, todo), total=len(todo), unit="row", ncols=100):
            if out is None:
                continue
            with lock:
                w.writerow(out)
                f.flush()
    f.close()

    print(f"tokens: {tokens}")
    print(f"errors: {errors}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python
"""GPT-4.1 same-input drift: re-judge the pinned 300-tuple sets.

GPT-4.1's May verdicts exist on the original v2/v3 judged batches, but
the eleven-week re-judge control was GPT-5.4-only, and the replication
batches use different tuples -- so the paper's GPT-4.1 leniency-drift
claim rests on cross-batch comparison. This closes the gap: re-judge
the exact same (query, contexts, answer) tuples with GPT-4.1 today and
report same-input kappa against May.

Writes results/gpt41-drift-{v2,v3}.csv (orig + new verdict per row).
Resumable.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

SETS = {
    "v2": ("results/main-v2-judged.csv", "results/main-v2.jsonl",
           "results/gpt41-drift-v2.csv"),
    "v3": ("results/main-v3-judged-pinned.csv", "results/main-v3.jsonl",
           "results/gpt41-drift-v3.csv"),
}


def kappa(a: list[bool], b: list[bool]) -> float:
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def main() -> int:
    load_dotenv(ROOT / ".env")
    from aerorag.multi_judge import _format_contexts, load_query_chunks, score_with_gpt41

    chunks = load_query_chunks(ROOT / "data/synthetic/requirements.jsonl")

    for name, (judged_csv, trace_jsonl, out_csv) in SETS.items():
        answers = {}
        for l in (ROOT / trace_jsonl).open():
            r = json.loads(l)
            answers[(r["query"], r["pipeline"], str(r["repeat"]))] = r["answer"]

        rows = list(csv.DictReader((ROOT / judged_csv).open()))
        out_path = ROOT / out_csv
        done = set()
        if out_path.exists():
            for r in csv.DictReader(out_path.open()):
                done.add((r["query"], r["pipeline"], r["repeat"]))

        write_header = not out_path.exists()
        f = out_path.open("a", newline="")
        w = csv.DictWriter(f, fieldnames=[
            "query", "pipeline", "repeat", "query_type",
            "orig_gpt41", "new_gpt41", "new_reason"])
        if write_header:
            w.writeheader()

        pairs: list[tuple[bool, bool]] = []
        for r in tqdm(rows, desc=f"gpt41-drift {name}", unit="row", ncols=100):
            key = (r["query"], r["pipeline"], str(r["repeat"]))
            if key in done or r["judge_gpt41_faithful"] not in ("True", "False"):
                continue
            ans = answers.get(key)
            if ans is None:
                continue
            ctx = _format_contexts(r["source_ids"], chunks)
            res = score_with_gpt41(r["query"], ctx, ans)
            if "faithful" not in res:
                print(f"\nERR {key[0][:50]}: {res.get('error')}", file=sys.stderr)
                continue
            w.writerow({
                "query": r["query"], "pipeline": r["pipeline"],
                "repeat": r["repeat"], "query_type": r["query_type"],
                "orig_gpt41": r["judge_gpt41_faithful"],
                "new_gpt41": res["faithful"],
                "new_reason": res["reason"],
            })
            f.flush()
        f.close()

        allrows = list(csv.DictReader(out_path.open()))
        a = [r["orig_gpt41"] == "True" for r in allrows]
        b = [r["new_gpt41"] == "True" for r in allrows]
        if a:
            agr = sum(x == y for x, y in zip(a, b)) / len(a)
            print(f"{name}: n={len(a)} May_faithful={sum(a)/len(a):.3f} "
                  f"now_faithful={sum(b)/len(b):.3f} raw_agr={agr:.3f} "
                  f"kappa={kappa(a, b):.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

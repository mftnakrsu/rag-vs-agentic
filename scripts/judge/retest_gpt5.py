"""B1 fix: same-input test-retest control for the GPT-5.4 judge.

Re-judges the identical 300 v2 (query, pipeline, repeat) tuples TWICE with
GPT-5.4 — same question, same contexts, same answer — to measure the judge's
same-input flip rate. This separates judge sampling noise from the
cross-embedder verdict changes reported in Table 3 (self-kappa 0.137).

Output: results/retest-v2-gpt5.csv + printed kappas
  kappa(passA, passB)  = test-retest reliability (same input, same day)
  kappa(passA, orig)   = drift vs the May run (same input, 2.5 months apart)
"""
from __future__ import annotations

import csv
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from aerorag.multi_judge import (  # noqa: E402
    _format_contexts,
    cohens_kappa,
    load_query_chunks,
    score_with_gpt5,
)

ROOT = Path(__file__).resolve().parents[2]
IN_CSV = ROOT / "results/main-v2-judged.csv"
RUNS_JSONL = ROOT / "results/main-v2.jsonl"
CHUNKS = ROOT / "data/synthetic/requirements.jsonl"
OUT_CSV = ROOT / "results/retest-v2-gpt5.csv"


def key(r: dict) -> tuple:
    return (r["query"], r["pipeline"], str(r["repeat"]))


def main() -> int:
    rows = list(csv.DictReader(IN_CSV.open()))
    keys = {key(r) for r in rows}
    answers = {}
    for line in RUNS_JSONL.open():
        d = json.loads(line)
        if d.get("embedder") == "local" and key(d) in keys:
            answers[key(d)] = d.get("answer", "")
    chunks = load_query_chunks(CHUNKS)
    print(f"{len(rows)} tuples, {len(answers)} answers joined, {len(chunks)} chunks")
    assert len(answers) == len(rows), "answer join incomplete"

    done: dict[tuple, dict] = {}
    if OUT_CSV.exists():
        done = {(r["query"], r["pipeline"], r["repeat"]): r
                for r in csv.DictReader(OUT_CSV.open())
                if r.get("pass_a") in ("True", "False")
                and r.get("pass_b") in ("True", "False")}
        print(f"resume: {len(done)} tuples already retested")

    lock = threading.Lock()
    n_done = 0

    def judge_twice(r: dict) -> dict:
        k = key(r)
        if k in done:
            return done[k]
        ctx = _format_contexts(r.get("source_ids", ""), chunks)
        ans = answers[k]
        out = {"query": r["query"], "pipeline": r["pipeline"],
               "repeat": r["repeat"], "query_type": r["query_type"],
               "orig": r["judge_gpt5_faithful"]}
        for label in ("pass_a", "pass_b"):
            res = score_with_gpt5(r["query"], ctx, ans)
            if "error" in res:
                res = score_with_gpt5(r["query"], ctx, ans)
            out[label] = res.get("faithful")
        return out

    results = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = [ex.submit(judge_twice, r) for r in rows]
        for fut in as_completed(futs):
            out = fut.result()
            with lock:
                results[(out["query"], out["pipeline"], str(out["repeat"]))] = out
                n_done += 1
                if n_done % 25 == 0:
                    print(f"  {n_done}/{len(rows)} retested", flush=True)

    with OUT_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["query", "pipeline", "repeat",
                                          "query_type", "orig", "pass_a", "pass_b"])
        w.writeheader()
        for r in rows:
            w.writerow(results[key(r)])
    print(f"wrote {len(rows)} rows -> {OUT_CSV}")

    ok = [r for r in results.values()
          if str(r["pass_a"]) in ("True", "False")
          and str(r["pass_b"]) in ("True", "False")]
    a = [str(r["pass_a"]) == "True" for r in ok]
    b = [str(r["pass_b"]) == "True" for r in ok]
    o = [str(r["orig"]) == "True" for r in ok]
    agree_ab = sum(x == y for x, y in zip(a, b)) / len(ok)
    agree_ao = sum(x == y for x, y in zip(a, o)) / len(ok)
    print(f"\nn={len(ok)}")
    print(f"test-retest (A vs B):  kappa={cohens_kappa(a, b):.3f}  raw agreement={agree_ab:.3f}  flips={sum(x != y for x, y in zip(a, b))}")
    print(f"vs May run (A vs orig): kappa={cohens_kappa(a, o):.3f}  raw agreement={agree_ao:.3f}  flips={sum(x != y for x, y in zip(a, o))}")
    print(f"faithful%%: passA={sum(a)/len(a):.3f} passB={sum(b)/len(b):.3f} orig={sum(o)/len(o):.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

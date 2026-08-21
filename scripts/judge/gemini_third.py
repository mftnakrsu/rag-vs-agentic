"""W3 mitigation: Gemini as third (non-OpenAI) judge on the 300 pinned v2 tuples.

Same inputs as retest_gpt5.py. Sequential (module-level 15 RPM throttle in
multi_judge). Resumable: rows already in the output CSV are skipped, so a
free-tier quota death (20 RPD) can be resumed the next day.

Output: results/gemini-third-v2.csv + 3-judge agreement summary.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from aerorag.multi_judge import (  # noqa: E402
    _format_contexts,
    cohens_kappa,
    load_query_chunks,
    score_with_gemini,
)

ROOT = Path(__file__).resolve().parents[2]
IN_CSV = ROOT / "results/main-v2-judged.csv"
RUNS_JSONL = ROOT / "results/main-v2.jsonl"
CHUNKS = ROOT / "data/synthetic/requirements.jsonl"
OUT_CSV = ROOT / "results/gemini-third-v2.csv"
FIELDS = ["query", "pipeline", "repeat", "query_type",
          "gpt5", "gpt41", "gemini", "gemini_reason"]


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

    done: dict[tuple, dict] = {}
    if OUT_CSV.exists():
        done = {(r["query"], r["pipeline"], r["repeat"]): r
                for r in csv.DictReader(OUT_CSV.open())
                if r.get("gemini") in ("True", "False")}
    print(f"{len(rows)} tuples, {len(done)} already judged (resume)")

    with OUT_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        n_err = 0
        for i, r in enumerate(rows, 1):
            k = key(r)
            if k in done:
                w.writerow(done[k])
                continue
            ctx = _format_contexts(r.get("source_ids", ""), chunks)
            res = score_with_gemini(r["query"], ctx, answers[k])
            out = {"query": r["query"], "pipeline": r["pipeline"],
                   "repeat": r["repeat"], "query_type": r["query_type"],
                   "gpt5": r["judge_gpt5_faithful"],
                   "gpt41": r["judge_gpt41_faithful"],
                   "gemini": res.get("faithful"),
                   "gemini_reason": (res.get("reason") or res.get("error", ""))[:200]}
            if "faithful" not in res:
                n_err += 1
                if n_err >= 5 and i - n_err < 5:
                    print("quota exhausted early, aborting", flush=True)
                    w.writerow(out)
                    break
            w.writerow(out)
            f.flush()
            if i % 25 == 0:
                print(f"  {i}/{len(rows)} ({n_err} errors)", flush=True)

    ok = [r for r in csv.DictReader(OUT_CSV.open())
          if r.get("gemini") in ("True", "False")]
    print(f"\njudged {len(ok)}/{len(rows)} ({n_err} errors this run)")
    if len(ok) >= 50:
        g = [r["gemini"] == "True" for r in ok]
        g5 = [r["gpt5"] == "True" for r in ok]
        g41 = [r["gpt41"] == "True" for r in ok]
        print(f"faithful%: gemini={sum(g)/len(g):.3f} gpt5={sum(g5)/len(g5):.3f} gpt41={sum(g41)/len(g41):.3f}")
        print(f"kappa(gemini,gpt5)={cohens_kappa(g, g5):.3f}  kappa(gemini,gpt41)={cohens_kappa(g, g41):.3f}  kappa(gpt5,gpt41)={cohens_kappa(g5, g41):.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

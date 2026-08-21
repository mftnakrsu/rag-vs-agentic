"""B2 fix: add GPT-4.1 as second judge over all 600 MuSiQue rows.

Reads results/musique-v3-judged.csv (GPT-5.4 verdicts already present),
hydrates answers from results/musique-v3-patched.jsonl and contexts from
data/musique/chunks.jsonl, judges each row with GPT-4.1, and writes
results/musique-v3-judged-dual.csv (same schema, gpt41 columns filled).

Incremental + resumable: rows already present in the output are skipped.
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

from aerorag.multi_judge import _format_contexts, load_query_chunks, score_with_gpt41  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
IN_CSV = ROOT / "results/musique-v3-judged.csv"
ANSWERS = ROOT / "results/musique-v3-patched.jsonl"
CHUNKS = ROOT / "data/musique/chunks.jsonl"
OUT_CSV = ROOT / "results/musique-v3-judged-dual.csv"

KEY = ("query", "pipeline", "repeat")


def key(r: dict) -> tuple:
    return tuple(str(r[k]) for k in KEY)


def main() -> int:
    rows = list(csv.DictReader(IN_CSV.open()))
    answers = {}
    for line in ANSWERS.open():
        d = json.loads(line)
        answers[(d["query"], d["pipeline"], str(d["repeat"]))] = d.get("answer", "")
    chunks = load_query_chunks(CHUNKS)
    print(f"{len(rows)} rows, {len(answers)} answers, {len(chunks)} chunks")

    done: dict[tuple, dict] = {}
    if OUT_CSV.exists():
        done = {key(r): r for r in csv.DictReader(OUT_CSV.open())
                if r.get("judge_gpt41_faithful") in ("True", "False")}
        print(f"resume: {len(done)} rows already judged")

    fieldnames = rows[0].keys()
    out_f = OUT_CSV.open("w", newline="")
    writer = csv.DictWriter(out_f, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    lock = threading.Lock()
    n_done = 0
    n_err = 0

    def judge(r: dict) -> dict:
        if key(r) in done:
            return done[key(r)]
        ans = answers.get((r["query"], r["pipeline"], str(r["repeat"])), "")
        ctx = _format_contexts(r.get("source_ids", ""), chunks)
        res = score_with_gpt41(r["query"], ctx, ans)
        if "error" in res:  # one retry
            res = score_with_gpt41(r["query"], ctx, ans)
        out = dict(r)
        out["judge_gpt41_faithful"] = res.get("faithful")
        out["judge_gpt41_reason"] = (res.get("reason") or res.get("error", ""))[:200]
        g5, g41 = out.get("judge_gpt5_faithful"), out["judge_gpt41_faithful"]
        out["judge_unanimous"] = (g41 is not None and str(g5) == str(g41))
        return out

    results = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(judge, r): key(r) for r in rows}
        for fut in as_completed(futs):
            out = fut.result()
            with lock:
                results[key(out)] = out
                n_done += 1
                if out["judge_gpt41_faithful"] is None:
                    n_err += 1
                if n_done % 50 == 0:
                    print(f"  {n_done}/{len(rows)} judged ({n_err} errors)", flush=True)

    for r in rows:  # write in input order
        writer.writerow(results[key(r)])
    out_f.close()
    print(f"wrote {len(rows)} rows -> {OUT_CSV} ({n_err} errors)")

    # summary: per-stratum faithful% per judge
    strata = sorted({r["query_type"] for r in rows})
    print(f"\n{'stratum':<8} {'n':>4} {'gpt5':>7} {'gpt41':>7}")
    for pipe in sorted({r["pipeline"] for r in rows}):
        for s in strata:
            cell = [results[key(r)] for r in rows
                    if r["pipeline"] == pipe and r["query_type"] == s]
            g5 = sum(r["judge_gpt5_faithful"] == "True" for r in cell) / len(cell)
            ok = [r for r in cell if r["judge_gpt41_faithful"] is not None]
            g41 = sum(r["judge_gpt41_faithful"] is True for r in ok) / max(1, len(ok))
            print(f"{pipe:<14} {s:<8} {len(cell):>4} {g5:>6.2f} {g41:>6.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

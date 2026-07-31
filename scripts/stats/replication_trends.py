#!/usr/bin/env python
"""Cochran-Armitage trends + agreement for the eleven-week replication
batches (results/main-v{2,3}-judged-repl.csv, seed 43, judged 2026-07-31)
against the original batches (seed 42, judged 2026-05-11).

Output: results/stats-v3/replication_trends.csv
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[2]
STRATA = ["1-hop", "2-hop", "3+-hop"]
JUDGES = {"gpt5": "judge_gpt5_faithful", "gpt41": "judge_gpt41_faithful"}
BATCHES = {
    ("v2", "orig"): "results/main-v2-judged.csv",
    ("v3", "orig"): "results/main-v3-judged-pinned.csv",
    ("v2", "repl"): "results/main-v2-judged-repl.csv",
    ("v3", "repl"): "results/main-v3-judged-repl.csv",
}


def ca_trend(cells: list[tuple[int, int]]) -> float:
    scores = [0, 1, 2]
    N = sum(n for _, n in cells)
    X = sum(x for x, _ in cells)
    p = X / N
    num = (sum(x * s for (x, _), s in zip(cells, scores))
           - p * sum(n * s for (_, n), s in zip(cells, scores)))
    var = p * (1 - p) * (sum(n * s * s for (_, n), s in zip(cells, scores))
                         - (sum(n * s for (_, n), s in zip(cells, scores)) ** 2) / N)
    if var <= 0:
        return float("nan")
    return 2 * norm.sf(abs(num / math.sqrt(var)))


def main() -> int:
    out_rows = []
    for (emb, batch), path in BATCHES.items():
        rows = list(csv.DictReader((ROOT / path).open()))
        g = [r for r in rows if r["pipeline"] == "graphrag"]
        for jname, col in JUDGES.items():
            cells = []
            for s in STRATA:
                sub = [r for r in g if r["query_type"] == s
                       and r[col] in ("True", "False")]
                cells.append((sum(r[col] == "True" for r in sub), len(sub)))
            out_rows.append({
                "embedder": emb, "batch": batch, "judge": jname,
                **{f"rate_{s}": (f"{x/n:.3f}" if n else "")
                   for s, (x, n) in zip(STRATA, cells)},
                **{f"n_{s}": n for s, (_, n) in zip(STRATA, cells)},
                "ca_trend_p": f"{ca_trend(cells):.4g}",
            })
    out = ROOT / "results" / "stats-v3" / "replication_trends.csv"
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)
    for r in out_rows:
        print(r)
    return 0


if __name__ == "__main__":
    main()

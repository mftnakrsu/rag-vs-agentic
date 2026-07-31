"""Review-fix stats: Wilson CIs + Cochran-Armitage trend tests for the
faithfulness cells in tab_pathology, plus endpoint Fisher tests.

Inputs (whichever exist):
  results/main-v2-judged.csv           DO-178C local, GPT-5.4 + GPT-4.1
  results/main-v3-judged-pinned.csv    DO-178C Azure (pinned), both judges
  results/musique-v3-judged-dual.csv   MuSiQue, both judges (falls back to
  results/musique-v3-judged.csv        GPT-5.4-only file)
  results/retest-v2-gpt5.csv           same-input test-retest (if present)

Outputs:
  results/stats-v3/faithfulness_cells.csv   per (setting, pipeline, stratum,
      judge): n, faithful, pct, wilson_lo, wilson_hi
  results/stats-v3/faithfulness_trend.csv   Cochran-Armitage across strata
      per (setting, pipeline, judge) + endpoint Fisher exact p
"""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

from scipy.stats import fisher_exact, norm

ROOT = Path(__file__).resolve().parents[2]
STRATA = ["1-hop", "2-hop", "3+-hop"]


def wilson(x: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = x / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def cochran_armitage(xs: list[int], ns: list[int]) -> tuple[float, float]:
    """Two-sided CA trend test with scores 1..k. Returns (Z, p)."""
    s = list(range(1, len(xs) + 1))
    N = sum(ns)
    X = sum(xs)
    if N == 0 or X in (0, sum(ns)):
        return (float("nan"), float("nan"))
    pbar = X / N
    t = sum(si * xi for si, xi in zip(s, xs)) - pbar * sum(si * ni for si, ni in zip(s, ns))
    v = pbar * (1 - pbar) * (sum(si * si * ni for si, ni in zip(s, ns))
                             - sum(si * ni for si, ni in zip(s, ns)) ** 2 / N)
    if v <= 0:
        return (float("nan"), float("nan"))
    z = t / math.sqrt(v)
    return (z, 2 * (1 - norm.cdf(abs(z))))


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return list(csv.DictReader(path.open()))


def cells(rows: list[dict], judge_col: str) -> dict[tuple, tuple[int, int]]:
    """(pipeline, stratum) -> (faithful, n) over rows with a boolean verdict."""
    out: dict[tuple, list[int]] = {}
    for r in rows:
        v = r.get(judge_col)
        if v not in ("True", "False", True, False):
            continue
        k = (r["pipeline"], r["query_type"])
        agg = out.setdefault(k, [0, 0])
        agg[0] += str(v) == "True"
        agg[1] += 1
    return {k: (a[0], a[1]) for k, a in out.items()}


def main() -> int:
    settings = {
        "v2-local": load(ROOT / "results/main-v2-judged.csv"),
        "v3-azure": load(ROOT / "results/main-v3-judged-pinned.csv"),
        "musique": (load(ROOT / "results/musique-v3-judged-dual.csv")
                    or load(ROOT / "results/musique-v3-judged.csv")),
    }
    judges = {"gpt5": "judge_gpt5_faithful", "gpt41": "judge_gpt41_faithful"}

    cells_out = ROOT / "results/stats-v3/faithfulness_cells.csv"
    trend_out = ROOT / "results/stats-v3/faithfulness_trend.csv"
    with cells_out.open("w", newline="") as cf, trend_out.open("w", newline="") as tf:
        cw = csv.writer(cf)
        cw.writerow(["setting", "pipeline", "stratum", "judge", "n",
                     "faithful", "pct", "wilson_lo", "wilson_hi"])
        tw = csv.writer(tf)
        tw.writerow(["setting", "pipeline", "judge", "ca_z", "ca_p",
                     "endpoint_fisher_p", "cells"])
        for sname, rows in settings.items():
            if not rows:
                print(f"skip {sname}: no file")
                continue
            for jname, jcol in judges.items():
                c = cells(rows, jcol)
                if not c:
                    continue
                for (pipe, stratum), (x, n) in sorted(c.items()):
                    lo, hi = wilson(x, n)
                    cw.writerow([sname, pipe, stratum, jname, n, x,
                                 f"{x/n:.4f}", f"{lo:.4f}", f"{hi:.4f}"])
                for pipe in sorted({k[0] for k in c}):
                    xs = [c.get((pipe, s), (0, 0))[0] for s in STRATA]
                    ns = [c.get((pipe, s), (0, 0))[1] for s in STRATA]
                    if 0 in ns:
                        continue
                    z, p = cochran_armitage(xs, ns)
                    table = [[xs[0], ns[0] - xs[0]], [xs[2], ns[2] - xs[2]]]
                    fp = fisher_exact(table)[1]
                    tw.writerow([sname, pipe, jname, f"{z:.3f}", f"{p:.5f}",
                                 f"{fp:.5f}",
                                 ";".join(f"{x}/{n}" for x, n in zip(xs, ns))])
                    if pipe == "graphrag":
                        print(f"{sname:<9} {jname:<6} graphrag cells "
                              f"{[f'{x}/{n}' for x, n in zip(xs, ns)]} "
                              f"CA z={z:+.2f} p={p:.4f} fisher(1h vs 3h) p={fp:.4f}")
    print(f"\nwrote {cells_out}\nwrote {trend_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

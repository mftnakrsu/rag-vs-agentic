#!/usr/bin/env python
"""Summarise the single-window cross-vendor judging pass.

Every comparison here is within one judging date, which is the only way
cross-corpus and inter-judge numbers mean anything given the drift measured
in C4. Reports, per judged set:

  * faithfulness by hop stratum, with Wilson intervals
  * Cochran-Armitage trend across strata
  * inter-judge Cohen's kappa and Gwet's AC1 where two judges scored the
    same rows, plus McNemar for asymmetric disagreement

Gwet's AC1 is reported alongside kappa because these cells run at high
prevalence, where kappa collapses even on near-total agreement.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportion_confint

ROOT = Path(__file__).resolve().parents[2]
ORDER = ["1-hop", "2-hop", "3+-hop"]

SETS = [
    ("DO-178C v2 (e5-small)",  "main-v2-judged-gemini.csv",      "main-v2-judged-full-gpt41.csv"),
    ("DO-178C v3 (3-small)",   "main-v3-judged-gemini.csv",      "main-v3-judged-full-gpt41.csv"),
    ("DO-178C v4 (bge-m3)",    "main-v4-judged.csv",             None),
    ("DO-178C PPR arm",        "main-v3-ppr-judged.csv",         None),
    ("MuSiQue graphrag",       "musique-base-judged-full.csv",   None),
    ("MuSiQue extra seeds",    "musique-extra-judged.csv",       None),
    ("MuSiQue rerank",         "musique-rerank-judged-full.csv", None),
    ("MuSiQue cap",            "musique-cap-judged-full.csv",    None),
    ("2Wiki",                  "twowiki-judged.csv",             None),
]


def _bool(col: pd.Series) -> pd.Series:
    return col.astype(str) == "True"


def load(name: str) -> pd.DataFrame | None:
    p = ROOT / "results" / name
    if not p.exists():
        return None
    return pd.read_csv(p)


def ca_trend(d: pd.DataFrame, col: str) -> tuple[float, float]:
    n = np.array([len(d[d.query_type == s]) for s in ORDER], float)
    r = np.array([_bool(d[d.query_type == s][col]).sum() for s in ORDER], float)
    if n.sum() == 0 or r.sum() in (0, n.sum()):
        return float("nan"), float("nan")
    s = np.array([0.0, 1.0, 2.0])
    N, R = n.sum(), r.sum()
    p = R / N
    den = np.sqrt(p * (1 - p) * ((n * s * s).sum() - ((n * s).sum()) ** 2 / N))
    if den == 0:
        return float("nan"), float("nan")
    z = ((r - n * p) @ s) / den
    return z, 2 * (1 - stats.norm.cdf(abs(z)))


def agreement(a: pd.Series, b: pd.Series) -> dict:
    n = len(a)
    po = float((a == b).mean())
    pa, pb = a.mean(), b.mean()
    pe = pa * pb + (1 - pa) * (1 - pb)
    kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    # Gwet's AC1: chance term from the marginal prevalence, not the product
    pi = (pa + pb) / 2
    pe_g = 2 * pi * (1 - pi)
    ac1 = (po - pe_g) / (1 - pe_g) if pe_g < 1 else float("nan")
    n01 = int((~a & b).sum())
    n10 = int((a & ~b).sum())
    mc = stats.binomtest(min(n01, n10), n01 + n10, 0.5).pvalue if (n01 + n10) else 1.0
    return {"n": n, "raw": po, "kappa": kappa, "ac1": ac1,
            "disagree": n01 + n10, "mcnemar_p": mc}


def main() -> int:
    for label, gem_file, gpt_file in SETS:
        d = load(gem_file)
        if d is None:
            print(f"\n=== {label}: not judged yet ===")
            continue
        judged_on = d.judged_on.iloc[0] if "judged_on" in d.columns else "?"
        print(f"\n=== {label}  (n={len(d)}, judged {judged_on}) ===")

        for jcol, jname in (("gemini_faithful", "Gemini 3.7-flash"),
                            ("gpt41_faithful", "GPT-4.1")):
            if jcol not in d.columns:
                continue
            sub = d[d[jcol].isin([True, False, "True", "False"])]
            if sub.empty:
                continue
            line = []
            for s in ORDER:
                cell = _bool(sub[sub.query_type == s][jcol])
                if not len(cell):
                    continue
                lo, hi = proportion_confint(cell.sum(), len(cell), method="wilson")
                line.append(f"{s}={cell.mean():.3f}[{lo:.2f},{hi:.2f}]")
            z, p = ca_trend(sub, jcol)
            star = "*" if p < 0.05 else " "
            print(f"  {jname:18s} " + "  ".join(line) + f"   trend p={p:.2e}{star}")

        # inter-judge, same rows
        if "gemini_faithful" in d.columns and "gpt41_faithful" in d.columns:
            ok = d.gemini_faithful.isin([True, False, "True", "False"]) & \
                 d.gpt41_faithful.isin([True, False, "True", "False"])
            if ok.any():
                a = _bool(d.loc[ok, "gemini_faithful"])
                b = _bool(d.loc[ok, "gpt41_faithful"])
                r = agreement(a, b)
                print(f"  inter-judge  n={r['n']}  raw={r['raw']:.3f}  "
                      f"kappa={r['kappa']:+.3f}  AC1={r['ac1']:+.3f}  "
                      f"McNemar p={r['mcnemar_p']:.2e}")
        elif gpt_file:
            g = load(gpt_file)
            if g is None:
                continue
            key = ["query", "pipeline", "repeat"]
            m = d[key + ["gemini_faithful"]].merge(g[key + ["gpt41_faithful"]], on=key)
            ok = m.gemini_faithful.isin([True, False, "True", "False"]) & \
                 m.gpt41_faithful.isin([True, False, "True", "False"])
            if ok.any():
                r = agreement(_bool(m.loc[ok, "gemini_faithful"]),
                              _bool(m.loc[ok, "gpt41_faithful"]))
                print(f"  inter-judge  n={r['n']}  raw={r['raw']:.3f}  "
                      f"kappa={r['kappa']:+.3f}  AC1={r['ac1']:+.3f}  "
                      f"McNemar p={r['mcnemar_p']:.2e}   (GPT-4.1 from {gpt_file})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

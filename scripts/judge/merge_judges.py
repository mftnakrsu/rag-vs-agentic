#!/usr/bin/env python
"""Merge a Gemini-only judged CSV with a GPT-4.1-only one over the same rows.

The two legs ran a day apart because the Gemini daily quota reset in between;
inputs were frozen, so the pairing is still row-exact. judged_on is kept per
judge so the offset stays visible.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
KEY = ["query", "pipeline", "repeat"]

PAIRS = [
    ("musique-extra-gemini.csv",  "musique-extra-gpt41.csv",  "musique-extra-judged.csv"),
    ("musique-rerank-gemini.csv", "musique-rerank-gpt41.csv", "musique-rerank-judged-full.csv"),
    ("musique-cap-gemini.csv",    "musique-cap-gpt41.csv",    "musique-cap-judged-full.csv"),
    ("twowiki-gemini.csv",        "twowiki-gpt41.csv",        "twowiki-judged.csv"),
]


def main() -> int:
    for gem_name, gpt_name, out_name in PAIRS:
        gem, gpt = ROOT / "results" / gem_name, ROOT / "results" / gpt_name
        if not (gem.exists() and gpt.exists()):
            print(f"{out_name}: skipped, missing leg")
            continue
        g = pd.read_csv(gem).rename(columns={"judged_on": "gemini_judged_on"})
        p = pd.read_csv(gpt).rename(columns={"judged_on": "gpt41_judged_on"})
        p = p.drop(columns=["query_type"])
        m = g.merge(p, on=KEY, how="inner", validate="one_to_one")
        if len(m) != len(g) or len(m) != len(p):
            print(f"{out_name}: WARNING {len(g)} gemini + {len(p)} gpt41 -> {len(m)} merged")
        m.to_csv(ROOT / "results" / out_name, index=False)
        print(f"{out_name}: {len(m)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())

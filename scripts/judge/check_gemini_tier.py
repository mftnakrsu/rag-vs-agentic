#!/usr/bin/env python
"""Preflight: is the Gemini key on a paid tier, and what will judging cost?

A brand-new AI Studio key sits on the free tier, which caps the 3.x flash
models at ~20 requests per day -- unusable for a 15,808-call judging pass.
This fires a short burst and reads the quota error, so "billing is live" is
something we verify rather than assume, and prints the measured per-call
cost so the projection is grounded in this key's actual token usage.

    python scripts/judge/check_gemini_tier.py
"""
from __future__ import annotations

import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

MODEL = "gemini-3.7-flash"
IN_PRICE, OUT_PRICE = 0.75, 3.75          # promo, through 2026-12-31
JUDGE_IN, JUDGE_OUT = 1726, 269           # measured on real judge prompts
BURST = 30                                # free tier dies at ~20/day
SCHEMA = {"type": "object",
          "properties": {"faithful": {"type": "boolean"}, "reason": {"type": "string"}},
          "required": ["faithful", "reason"]}


def one(key: str, i: int) -> tuple[int, str]:
    try:
        r = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
            headers={"X-goog-api-key": key, "Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": f"Reply JSON. Probe {i}."}]}],
                  "generationConfig": {"responseMimeType": "application/json",
                                       "responseSchema": SCHEMA}},
            timeout=90)
        if r.status_code == 200:
            return 200, ""
        try:
            err = r.json()["error"]
            q = next((d for d in err.get("details", [])
                      if d.get("@type", "").endswith("QuotaFailure")), None)
            if q:
                v = q["violations"][0]
                return r.status_code, f"{v.get('quotaId','?')} limit={v.get('quotaValue','?')}"
            return r.status_code, err.get("message", "")[:80]
        except Exception:
            return r.status_code, r.text[:80]
    except Exception as e:  # noqa: BLE001
        return 0, f"{type(e).__name__}: {e}"


def main() -> int:
    load_dotenv(ROOT / ".env")
    key = os.environ.get("GOOGLE_API_KEY")
    if not key:
        print("GOOGLE_API_KEY not set", file=sys.stderr)
        return 2

    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(lambda i: one(key, i), range(BURST)))

    ok = sum(1 for c, _ in results if c == 200)
    quota = [m for c, m in results if c == 429]
    free = any("FreeTier" in m for m in quota)

    print(f"model {MODEL}: {ok}/{BURST} succeeded")
    if quota:
        print(f"  quota errors: {quota[0]}")
    if free:
        print("  TIER: FREE -- billing is NOT active. Judging cannot run.")
    elif ok >= 20:
        print("  TIER: PAID -- free-tier day cap cleared, billing is live.")
    else:
        print("  TIER: INCONCLUSIVE (transient 503s?) -- re-run.")

    per = (JUDGE_IN * IN_PRICE + JUDGE_OUT * OUT_PRICE) / 1e6
    print(f"\nmeasured judge call: {JUDGE_IN} in / {JUDGE_OUT} out -> ${per:.5f}")
    for label, n in (("DO-178C v2+v3 full", 8880), ("+v4 bge", 4440),
                     ("+MuSiQue 3 seeds", 600), ("+2Wiki 3 seeds", 1200),
                     ("+mitigation & PPR", 696)):
        print(f"  {label:22s} {n:6d} calls  ${per*n:7.2f}")
    total = 8880 + 4440 + 600 + 1200 + 696
    print(f"  {'TOTAL':22s} {total:6d} calls  ${per*total:7.2f}")
    return 0 if not free else 1


if __name__ == "__main__":
    sys.exit(main())

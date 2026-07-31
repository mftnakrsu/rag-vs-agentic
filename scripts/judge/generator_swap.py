#!/usr/bin/env python
"""Generator-swap control: GPT-4.1 as synthesizer on frozen retrievals.

GPT-5.4 wrote the corpus, generates every answer, and casts half the
faithfulness verdicts. This control breaks the generator leg: re-synthesize
the vanilla and graphrag arms (v3 embedder, repeat 1, 100 queries each)
with GPT-4.1 over the exact same retrieved contexts, then compare citation
metrics and dual-judge faithfulness against the GPT-5.4 originals.

Writes results/genswap-gpt41.jsonl (same schema as main-v3.jsonl).
Resumable by (query, pipeline).
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

TRACE = ROOT / "results" / "main-v3.jsonl"
CORPUS = ROOT / "data" / "synthetic" / "requirements.jsonl"
OUT = ROOT / "results" / "genswap-gpt41.jsonl"
N_QUERIES = 100
PIPELINES = ("vanilla", "graphrag")

GROUNDED_SYSTEM_PROMPT = """You are an aerospace requirements engineer answering questions about a DOORS-exported requirements set.
Rules:
 1. Ground every claim in retrieved requirements; cite the IDs you used inline as [ADS-014].
 2. If the retrieved context does not contain the answer, say so plainly. Do not invent.
 3. Prefer concise, technical wording. Reproduce numeric thresholds (Hz, kt, ft, ms, °) verbatim.
 4. When requirements interact (e.g., FCC <-> ADS), explain the relationship.
"""


def main() -> int:
    load_dotenv(ROOT / ".env")
    from openai import OpenAI

    api_key = os.environ["AZURE_OPENAI_LLM_API_KEY"]
    base_url = os.environ["AZURE_OPENAI_LLM_BASE_URL"]
    deployment = os.environ.get("AZURE_GPT41_DEPLOYMENT", "gpt-4.1-meftun")
    client = OpenAI(api_key=api_key, base_url=base_url)

    meta = {}
    for l in CORPUS.open():
        r = json.loads(l)
        meta[r["id"]] = (r.get("module", ""), r.get("heading", ""),
                         r.get("full_text") or r.get("text") or "")

    rows = [json.loads(l) for l in TRACE.open()]
    # stratified: 34/33/33 per stratum per pipeline; first pass filled
    # 100 one-hop rows per pipeline (trace order), kept via resume
    quota = {"1-hop": 100, "2-hop": 33, "3+-hop": 33}
    picked = []
    seen_q: dict[tuple, set] = {}
    for r in rows:
        p, s = r["pipeline"], r["query_type"]
        if p not in PIPELINES or str(r["repeat"]) != "1" or s not in quota:
            continue
        key = (p, s)
        seen_q.setdefault(key, set())
        if len(seen_q[key]) < quota[s] and r["query"] not in seen_q[key]:
            seen_q[key].add(r["query"])
            picked.append(r)

    done = set()
    if OUT.exists():
        for l in OUT.open():
            r = json.loads(l)
            done.add((r["query"], r["pipeline"]))
    print(f"{len(picked)} rows to synthesize, {len(done)} already done")

    out_f = OUT.open("a")
    for r in tqdm(picked, unit="row", ncols=100):
        if (r["query"], r["pipeline"]) in done:
            continue
        ids = [s for s in r["source_ids"].split(";") if s]
        context = "\n\n---\n\n".join(
            f"[{i}] ({meta[i][0]} :: {meta[i][1]})\n{meta[i][2]}"
            for i in ids if i in meta
        )
        head = (f"Context (top-8 retrieved + graph-expanded neighbors)"
                if r["pipeline"] == "graphrag" else "Context (retrieved requirements)")
        user_msg = f"{head}:\n\n{context}\n\nQ: {r['query']}"
        t0 = time.time()
        try:
            resp = client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": GROUNDED_SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                max_completion_tokens=2048,
            )
        except Exception as e:  # noqa: BLE001
            print(f"\nERROR on {r['query'][:60]}: {e}", file=sys.stderr)
            continue
        answer = resp.choices[0].message.content or ""
        u = resp.usage
        out_f.write(json.dumps({
            **{k: r[k] for k in ("query", "query_type", "pipeline", "embedder",
                                  "reranker", "repeat", "source_ids", "n_sources")},
            "latency_ms": int((time.time() - t0) * 1000),
            "prompt_tokens": u.prompt_tokens if u else 0,
            "completion_tokens": u.completion_tokens if u else 0,
            "total_tokens": u.total_tokens if u else 0,
            "cited_ids": "",
            "iter_count": 0, "verdict": "", "intent": "",
            "routed_to": "", "route_reason": "",
            "answer": answer,
        }) + "\n")
        out_f.flush()
    out_f.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

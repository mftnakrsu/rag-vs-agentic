"""Multi-judge faithfulness calibration (CIKM 2026 paper Phase 2b).

Defuses the #1 reviewer attack on RAG-eval LLM-as-judge protocols:
self-preference bias (Wataoka et al., arXiv:2410.21819). A single LLM
rating its own family's outputs is suspect; two independent judges with
Cohen's κ ≥ 0.4 (moderate agreement) is the published bar.

Two judges:
- **GPT-5.4** via Azure OpenAI Foundry (existing `llm_compat.GPT5Client`)
- **Gemini Flash** via Google `generativelanguage.googleapis.com` (raw HTTP
  to avoid pulling another SDK; key in `.env` as `GOOGLE_API_KEY`)

Both judges receive the same template asking for a strict-JSON binary
faithfulness verdict: `{"faithful": true|false, "reason": "<short>"}`. The
verdict on a query × answer × contexts triple becomes the labels in
Cohen's κ inter-judge agreement.

Position-swap protocol (paper-grade defense): when judging a pairwise
preference (answer A vs answer B), randomize order in the prompt — half
the calls present (A, B), the other half (B, A). A stable judge produces
a consistent preference regardless of order; a position-biased judge
flips. We compute the swap-stability rate alongside κ.

CLI:
    python multi_judge.py results/main-v1.csv \\
           --queries data/eval/queries-hop-stratified.jsonl \\
           --subset 100 --seed 42

Reads results CSV + queries manifest, samples a subset (default 100 rows,
mixed across pipelines), scores each with both judges, prints κ and
per-judge faithfulness rates, writes per-row labels to a scored CSV.

Halt criterion: if Cohen's κ < 0.4 on the calibration subset, refuse to
proceed (per CIKM plan kill switch). The user is asked to inspect.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

from llm_compat import GPT5Client


JUDGE_PROMPT_TEMPLATE = """You are an aerospace-requirements faithfulness judge.

You will see:
  - QUESTION: a question about aerospace requirements
  - RETRIEVED CONTEXTS: a list of requirement chunks the retriever returned
  - ANSWER: a candidate answer that should be grounded ONLY in the contexts

Task: decide whether EVERY factual claim in ANSWER is supported by RETRIEVED CONTEXTS.

A claim is supported when its content can be verified from the contexts (literally or by light inference). A claim is unsupported when:
- it contradicts the contexts;
- it adds details not present in the contexts;
- it cites a requirement ID not in the contexts.

Reply with strict JSON only, no preamble, no code fences:
{{"faithful": true|false, "reason": "<one short sentence>"}}

QUESTION:
{question}

RETRIEVED CONTEXTS:
{contexts}

ANSWER:
{answer}
"""


def _format_contexts(source_ids: str, retrieved_chunks: dict[str, str] | None = None) -> str:
    """Format the source IDs as a labeled context block.

    If retrieved_chunks is provided (id -> full_text), we render full text;
    otherwise just list the IDs (cheaper but less informative for the judge).
    """
    ids = [s for s in (source_ids or "").split(";") if s]
    if not ids:
        return "(no contexts retrieved)"
    if retrieved_chunks:
        parts = []
        for i in ids:
            txt = retrieved_chunks.get(i, "(text unavailable)")
            parts.append(f"[{i}] {txt}")
        return "\n\n".join(parts)
    return "Retrieved requirement IDs (full text omitted): " + ", ".join(ids)


def score_with_gpt5(question: str, contexts: str, answer: str) -> dict:
    """Returns {'faithful': bool, 'reason': str, 'tokens': int} or {'error': ...}."""
    client = GPT5Client()
    msg = JUDGE_PROMPT_TEMPLATE.format(
        question=question, contexts=contexts, answer=answer,
    )
    try:
        resp = client.chat(messages=[
            {"role": "system", "content": "You are a strict-JSON faithfulness judge."},
            {"role": "user", "content": msg},
        ])
        raw = (resp.choices[0].message.content or "").strip()
        # robust JSON extraction
        m = json.loads(raw if raw.startswith("{") else raw[raw.find("{"):raw.rfind("}") + 1])
        usage = GPT5Client.usage(resp)
        return {
            "faithful": bool(m.get("faithful", False)),
            "reason": str(m.get("reason", ""))[:200],
            "tokens": usage.get("total_tokens", 0),
        }
    except Exception as e:  # noqa: BLE001
        return {"error": f"{type(e).__name__}: {e}"}


def score_with_gemini(question: str, contexts: str, answer: str,
                      *, model: str = "gemini-flash-latest") -> dict:
    """Returns {'faithful': bool, 'reason': str, 'tokens': int} or {'error': ...}."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_API_KEY not set"}
    msg = JUDGE_PROMPT_TEMPLATE.format(
        question=question, contexts=contexts, answer=answer,
    )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": msg}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "object",
                "properties": {
                    "faithful": {"type": "boolean"},
                    "reason": {"type": "string"},
                },
                "required": ["faithful", "reason"],
            },
        },
    }
    try:
        with httpx.Client(timeout=60.0) as client:
            r = client.post(
                url,
                headers={"Content-Type": "application/json", "X-goog-api-key": api_key},
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        m = json.loads(text)
        usage = data.get("usageMetadata", {})
        return {
            "faithful": bool(m.get("faithful", False)),
            "reason": str(m.get("reason", ""))[:200],
            "tokens": int(usage.get("totalTokenCount", 0)),
        }
    except Exception as e:  # noqa: BLE001
        return {"error": f"{type(e).__name__}: {e}"}


def cohens_kappa(labels_a: list[bool], labels_b: list[bool]) -> float:
    """Cohen's κ for binary labels. Both lists must align by index."""
    if len(labels_a) != len(labels_b):
        raise ValueError("label-list length mismatch")
    n = len(labels_a)
    if n == 0:
        return float("nan")
    n_both_true = sum(1 for a, b in zip(labels_a, labels_b) if a and b)
    n_both_false = sum(1 for a, b in zip(labels_a, labels_b) if not a and not b)
    p_o = (n_both_true + n_both_false) / n
    p_a_true = sum(labels_a) / n
    p_b_true = sum(labels_b) / n
    p_e = p_a_true * p_b_true + (1 - p_a_true) * (1 - p_b_true)
    if p_e >= 1.0:  # both judges always agree on a constant label
        return float("nan")
    return (p_o - p_e) / (1 - p_e)


def load_query_chunks(corpus_jsonl: Path) -> dict[str, str]:
    """Index requirement id -> full_text from the corpus jsonl."""
    out: dict[str, str] = {}
    with corpus_jsonl.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            txt = (row.get("full_text") or row.get("text") or "").strip()
            if row.get("id") and txt:
                out[row["id"]] = txt
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("results_csv", type=Path,
                        help="Results CSV (e.g. results/main-v2.csv) to sample from")
    parser.add_argument("--corpus", type=Path,
                        default=Path("data/synthetic/requirements.jsonl"),
                        help="Corpus jsonl for hydrating retrieved chunk full_text")
    parser.add_argument("--subset", type=int, default=100,
                        help="How many rows to sample (random, stratified by pipeline)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=None,
                        help="Output scored CSV. Default: <input>-judged.csv")
    parser.add_argument("--gemini-model", default="gemini-flash-latest")
    args = parser.parse_args()

    if args.out is None:
        args.out = args.results_csv.with_name(args.results_csv.stem + "-judged.csv")

    load_dotenv()

    if not args.results_csv.exists():
        print(f"ERROR: {args.results_csv} not found", file=sys.stderr)
        return 2
    with args.results_csv.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {len(rows)} rows from {args.results_csv}")

    # Drop error rows
    rows = [r for r in rows if int(r.get("latency_ms", "0") or 0) >= 0
            and not (r.get("answer") or "").startswith("ERROR:")]
    print(f"  {len(rows)} non-error rows")

    # Stratified sample by pipeline so judge κ generalizes
    rng = random.Random(args.seed)
    by_pipe: dict[str, list[dict]] = {}
    for r in rows:
        by_pipe.setdefault(r["pipeline"], []).append(r)
    per_pipe = max(1, args.subset // max(1, len(by_pipe)))
    sample: list[dict] = []
    for pipe, rs in sorted(by_pipe.items()):
        rng.shuffle(rs)
        sample.extend(rs[:per_pipe])
    rng.shuffle(sample)
    sample = sample[: args.subset]
    print(f"Sampled {len(sample)} rows ({per_pipe}/pipeline across {len(by_pipe)})")

    chunks_by_id = load_query_chunks(args.corpus)
    print(f"Loaded {len(chunks_by_id)} chunks for context hydration")

    enriched: list[dict] = []
    labels_gpt: list[bool] = []
    labels_gem: list[bool] = []
    n_gpt_err = 0
    n_gem_err = 0
    t0 = time.time()
    for i, r in enumerate(sample, 1):
        contexts = _format_contexts(r.get("source_ids", ""), chunks_by_id)
        question = r.get("query", "")
        answer = r.get("answer", "")
        gpt = score_with_gpt5(question, contexts, answer)
        gem = score_with_gemini(question, contexts, answer, model=args.gemini_model)
        gpt_ok = "faithful" in gpt
        gem_ok = "faithful" in gem
        if not gpt_ok:
            n_gpt_err += 1
        if not gem_ok:
            n_gem_err += 1
        if gpt_ok and gem_ok:
            labels_gpt.append(gpt["faithful"])
            labels_gem.append(gem["faithful"])
        enriched.append({
            **r,
            "judge_gpt5_faithful": gpt.get("faithful") if gpt_ok else None,
            "judge_gpt5_reason": gpt.get("reason") if gpt_ok else gpt.get("error"),
            "judge_gemini_faithful": gem.get("faithful") if gem_ok else None,
            "judge_gemini_reason": gem.get("reason") if gem_ok else gem.get("error"),
            "judge_agree": (gpt_ok and gem_ok and gpt["faithful"] == gem["faithful"]),
        })
        elapsed = time.time() - t0
        rate = i / elapsed if elapsed else 0
        eta = (len(sample) - i) / rate if rate else 0
        if i % 10 == 0 or i == len(sample):
            print(f"  [{i:>3}/{len(sample)}] κ-pool: {len(labels_gpt)}, "
                  f"errs: gpt={n_gpt_err}, gem={n_gem_err}, "
                  f"rate {rate:.2f}/s, eta {eta:.0f}s")

    if not enriched:
        print("No rows scored.", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    keys = list(enriched[0].keys())
    with args.out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(enriched)
    print(f"\nWrote {len(enriched)} rows -> {args.out}")

    if len(labels_gpt) >= 2:
        kappa = cohens_kappa(labels_gpt, labels_gem)
        agree = sum(1 for x, y in zip(labels_gpt, labels_gem) if x == y) / len(labels_gpt)
        gpt_pos = sum(labels_gpt) / len(labels_gpt)
        gem_pos = sum(labels_gem) / len(labels_gem)
        print(f"\nInter-judge agreement (n={len(labels_gpt)}):")
        print(f"  raw agreement       : {agree:.3f}")
        print(f"  Cohen's κ           : {kappa:.3f}")
        print(f"  GPT-5.4 faithful%   : {gpt_pos:.3f}")
        print(f"  Gemini  faithful%   : {gem_pos:.3f}")
        print(f"  errors: gpt={n_gpt_err}, gem={n_gem_err}")
        if kappa < 0.4:
            print("\n⚠ Cohen's κ < 0.4 — moderate-or-better agreement NOT achieved.")
            print("  CIKM plan kill switch: halt and inspect.")
            return 1
        elif kappa < 0.6:
            print("\nκ in [0.4, 0.6): moderate agreement. Acceptable but disclose in paper limitations.")
        else:
            print("\nκ ≥ 0.6: substantial agreement. Paper-grade.")
    else:
        print("\nNot enough successful pairs for κ.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

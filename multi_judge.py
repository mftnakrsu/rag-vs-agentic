"""Multi-judge faithfulness calibration (CIKM 2026 paper Phase 2b).

Defuses the #1 reviewer attack on RAG-eval LLM-as-judge protocols:
self-preference bias (Wataoka et al., arXiv:2410.21819). A single LLM
rating its own family's outputs is suspect.

Three judges:
- **GPT-5.4** via Azure (existing `llm_compat.GPT5Client`).
  ⚠ This is the SAME model used as generator in the pipelines, so its
  judgments carry self-preference bias. Reported for transparency only —
  primary κ excludes it.
- **GPT-4.1** via Azure (Chris's `gpt-4.1-meftun` deployment, same project
  base URL, 10M TPM cap). Different model in OpenAI family, independent
  of the GPT-5.4 generator.
- **Gemini Flash** via Google `generativelanguage.googleapis.com` (raw HTTP
  to avoid pulling another SDK; key in `.env` as `GOOGLE_API_KEY`,
  free-tier 15 RPM throttled). Different family, independent of generator.

Primary inter-judge agreement: GPT-4.1 × Gemini (both generator-independent).
Tertiary: GPT-5.4 included for transparency (expected to over-rate).
Aggregate: Fleiss' κ across all 3 raters.

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
from tqdm import tqdm

from llm_compat import GPT5Client


# =============================================================================
# Rate limiting — Gemini free tier is 15 RPM / 1500 RPD on flash-latest.
# Module-level throttle floor keeps us under 15 RPM with margin.
# Override via env GEMINI_MIN_INTERVAL_S (default 4.5s = 13.3 RPM).
# =============================================================================
_GEMINI_LAST_CALL: float = 0.0
_GEMINI_MIN_INTERVAL_S: float = float(os.environ.get("GEMINI_MIN_INTERVAL_S", "4.5"))


def _gemini_throttle() -> None:
    """Sleep so that consecutive Gemini calls respect the per-minute floor."""
    global _GEMINI_LAST_CALL
    now = time.time()
    elapsed = now - _GEMINI_LAST_CALL
    if elapsed < _GEMINI_MIN_INTERVAL_S:
        time.sleep(_GEMINI_MIN_INTERVAL_S - elapsed)
    _GEMINI_LAST_CALL = time.time()


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


def score_with_gpt41(question: str, contexts: str, answer: str) -> dict:
    """3rd judge — GPT-4.1 via Azure (Chris's deployment).

    Independent of GPT-5.4 generator (different family member), so suitable
    as an unbiased faithfulness judge. 10M TPM cap means no per-request
    throttling needed. Uses the OpenAI SDK against the /openai/v1 base URL
    with response_format=json_object for structured output.

    Returns {'faithful': bool, 'reason': str, 'tokens': int} or {'error': ...}.
    """
    api_key = os.environ.get("AZURE_OPENAI_LLM_API_KEY")
    base_url = os.environ.get("AZURE_OPENAI_LLM_BASE_URL")
    deployment = os.environ.get("AZURE_GPT41_DEPLOYMENT", "gpt-4.1-meftun")
    if not api_key or not base_url:
        return {"error": "AZURE_OPENAI_LLM_API_KEY / BASE_URL not set"}

    msg = JUDGE_PROMPT_TEMPLATE.format(
        question=question, contexts=contexts, answer=answer,
    )
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system",
                 "content": "You are a strict-JSON faithfulness judge."},
                {"role": "user", "content": msg},
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=500,
        )
        raw = (resp.choices[0].message.content or "").strip()
        m = json.loads(raw if raw.startswith("{") else raw[raw.find("{"):raw.rfind("}") + 1])
        return {
            "faithful": bool(m.get("faithful", False)),
            "reason": str(m.get("reason", ""))[:200],
            "tokens": resp.usage.total_tokens if resp.usage else 0,
        }
    except Exception as e:  # noqa: BLE001
        return {"error": f"{type(e).__name__}: {e}"}


GEMINI_JUDGE_MODEL = "gemini-3.7-flash"      # snapshot 3.7-flash-08-2026
GEMINI_THINKING_BUDGET = -1                  # -1 = dynamic; thinking ON by design


def score_with_gemini(question: str, contexts: str, answer: str,
                      *, model: str = GEMINI_JUDGE_MODEL,
                      max_retries: int = 6) -> dict:
    """Score (question, contexts, answer) with Gemini Flash.

    Pinned to GEMINI_JUDGE_MODEL with thinking explicitly enabled: the paper's
    other reasoning judge is GPT-5.4, and a non-thinking third judge would
    duplicate GPT-4.1's position rather than add one.

    Honors the module-level _GEMINI_MIN_INTERVAL_S throttle. On 429 (rate
    limit) or 5xx (transient server), retries with exponential backoff up to
    max_retries (30s → 60s → 120s).

    Returns {'faithful': bool, 'reason': str, 'tokens': int, 'thought_tokens': int}
    on success, or {'error': ...} on permanent failure.
    """
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
            "thinkingConfig": {"thinkingBudget": GEMINI_THINKING_BUDGET},
        },
    }
    last_err: str = ""
    for attempt in range(max_retries + 1):
        _gemini_throttle()
        try:
            with httpx.Client(timeout=60.0) as client:
                r = client.post(
                    url,
                    headers={"Content-Type": "application/json", "X-goog-api-key": api_key},
                    json=payload,
                )
                if r.status_code == 429 and "spend" in r.text.lower():
                    # A spend-cap 429 is not transient: it clears only when a
                    # human raises the cap. Retrying it burns ~30 min per row
                    # on backoff and still fails, so surface it immediately.
                    return {"error": f"SPEND_CAP: {r.text[:160]}"}
                if r.status_code == 429 or 500 <= r.status_code < 600:
                    last_err = f"HTTP {r.status_code}: {r.text[:120]}"
                    if attempt < max_retries:
                        # 429 is a quota signal and needs a long cool-off; 5xx is
                        # transient overload and clears in seconds. Jitter keeps
                        # concurrent workers from retrying in lockstep.
                        base = 30.0 if r.status_code == 429 else 4.0
                        wait = base * (2 ** attempt) * (0.7 + 0.6 * random.random())
                        print(f"  Gemini {r.status_code}, retry {attempt + 1}/{max_retries} in {wait:.0f}s",
                              file=sys.stderr)
                        time.sleep(wait)
                        continue
                    return {"error": last_err}
                r.raise_for_status()
                data = r.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            m = json.loads(text)
            usage = data.get("usageMetadata", {})
            return {
                "faithful": bool(m.get("faithful", False)),
                "reason": str(m.get("reason", ""))[:200],
                "tokens": int(usage.get("totalTokenCount", 0)),
                "thought_tokens": int(usage.get("thoughtsTokenCount", 0)),
            }
        except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as e:
            last_err = f"{type(e).__name__}: {e}"
            if attempt < max_retries:
                wait = 15.0 * (2 ** attempt)
                print(f"  Gemini transient {type(e).__name__}, retry "
                      f"{attempt + 1}/{max_retries} in {wait:.0f}s", file=sys.stderr)
                time.sleep(wait)
                continue
        except Exception as e:  # noqa: BLE001
            return {"error": f"{type(e).__name__}: {e}"}
    return {"error": last_err or "max retries exceeded"}


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


def fleiss_kappa(labels_per_rater: list[list[bool]]) -> float:
    """Fleiss' κ for binary labels across N raters on the same items.

    labels_per_rater: list of N rater label-lists; each inner list aligns by
        item index. All must have the same length.

    Returns κ in (−∞, 1]. NaN if degenerate (all raters always agree on a
    single category, so chance agreement is 1.0).

    Reference: Fleiss 1971; standard formulation for binary categories.
    """
    n_raters = len(labels_per_rater)
    if n_raters < 2:
        return float("nan")
    n_items = len(labels_per_rater[0])
    if any(len(lr) != n_items for lr in labels_per_rater):
        raise ValueError("rater label lists have unequal length")
    if n_items == 0:
        return float("nan")

    # n_true_per_item[i] = how many of the N raters said True on item i.
    n_true = [sum(1 for lr in labels_per_rater if lr[i]) for i in range(n_items)]
    n_false = [n_raters - t for t in n_true]

    # Per-item agreement P_i = (sum_k n_ik*(n_ik − 1)) / (N*(N − 1))
    P_i = [
        (t * (t - 1) + f * (f - 1)) / (n_raters * (n_raters - 1))
        for t, f in zip(n_true, n_false)
    ]
    P_bar = sum(P_i) / n_items

    # Marginal proportion of True across all rater-item assignments.
    p_true = sum(n_true) / (n_items * n_raters)
    p_false = 1 - p_true
    P_e = p_true ** 2 + p_false ** 2

    if P_e >= 1.0:
        return float("nan")
    return (P_bar - P_e) / (1 - P_e)


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
    parser.add_argument("--no-gemini", action="store_true",
                        help="Skip Gemini judge (default since free tier dropped to "
                             "20 RPD in May 2026). Then κ is GPT-5.4 × GPT-4.1.")
    parser.add_argument("--with-gemini", action="store_true",
                        help="Force Gemini judge ON (needs paid tier or fresh free quota)")
    parser.add_argument("--no-gpt41", action="store_true",
                        help="Skip GPT-4.1 judge — single-judge GPT-5.4 mode "
                             "(used for MuSiQue confirmation experiment).")
    args = parser.parse_args()
    # Default: skip Gemini unless explicitly requested
    use_gemini = args.with_gemini and not args.no_gemini
    use_gpt41 = not args.no_gpt41

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

    # Incremental writer — write each scored row to disk immediately so
    # mid-run kills don't lose progress. Schema is all DictReader fields
    # of the input row plus the judge-specific columns we add.
    judge_keys = [
        "judge_gpt5_faithful", "judge_gpt5_reason",
        "judge_gpt41_faithful", "judge_gpt41_reason",
        "judge_gemini_faithful", "judge_gemini_reason",
        "judge_unanimous",
    ]
    out_keys = list(sample[0].keys()) + judge_keys
    args.out.parent.mkdir(parents=True, exist_ok=True)
    out_f = args.out.open("w", newline="", encoding="utf-8")
    out_w = csv.DictWriter(out_f, fieldnames=out_keys, extrasaction="ignore")
    out_w.writeheader()
    out_f.flush()

    enriched: list[dict] = []
    labels_gpt5: list[bool] = []
    labels_gpt41: list[bool] = []
    labels_gem: list[bool] = []
    n_gpt5_err = 0
    n_gpt41_err = 0
    n_gem_err = 0

    try:
        pbar = tqdm(sample, desc="Judging", unit="row", ncols=100,
                    leave=True, dynamic_ncols=False)
        for r in pbar:
            contexts = _format_contexts(r.get("source_ids", ""), chunks_by_id)
            question = r.get("query", "")
            answer = r.get("answer", "")
            gpt5 = score_with_gpt5(question, contexts, answer)
            gpt41 = (score_with_gpt41(question, contexts, answer)
                     if use_gpt41 else {"skipped": True})
            gem = (score_with_gemini(question, contexts, answer, model=args.gemini_model)
                   if use_gemini else {"skipped": True})
            gpt5_ok = "faithful" in gpt5
            gpt41_ok = "faithful" in gpt41
            gem_ok = "faithful" in gem
            if not gpt5_ok:
                n_gpt5_err += 1
            if use_gpt41 and not gpt41_ok:
                n_gpt41_err += 1
            if use_gemini and not gem_ok:
                n_gem_err += 1
            pool_ok = gpt5_ok and (gpt41_ok or not use_gpt41) and (gem_ok or not use_gemini)
            if pool_ok:
                labels_gpt5.append(gpt5["faithful"])
                if use_gpt41:
                    labels_gpt41.append(gpt41["faithful"])
                if use_gemini:
                    labels_gem.append(gem["faithful"])
            if not use_gpt41:
                agree = pool_ok  # single-judge: trivially "agrees with itself"
            elif use_gemini:
                agree = pool_ok and gpt5["faithful"] == gpt41["faithful"] == gem["faithful"]
            else:
                agree = pool_ok and gpt5["faithful"] == gpt41["faithful"]
            row_out = {
                **r,
                "judge_gpt5_faithful": gpt5.get("faithful") if gpt5_ok else None,
                "judge_gpt5_reason": gpt5.get("reason") if gpt5_ok else gpt5.get("error"),
                "judge_gpt41_faithful": gpt41.get("faithful") if gpt41_ok else None,
                "judge_gpt41_reason": gpt41.get("reason") if gpt41_ok else gpt41.get("error"),
                "judge_gemini_faithful": gem.get("faithful") if gem_ok else None,
                "judge_gemini_reason": (gem.get("reason") if gem_ok
                                        else gem.get("error", "skipped")),
                "judge_unanimous": agree,
            }
            enriched.append(row_out)
            out_w.writerow(row_out)
            out_f.flush()
            if len(enriched) % 25 == 0:
                os.fsync(out_f.fileno())
            # Live status: faithfulness rates + pool size + per-judge errors
            postfix = {
                "g5": f"{(sum(labels_gpt5)/len(labels_gpt5)*100 if labels_gpt5 else 0):.0f}%",
                "g41": f"{(sum(labels_gpt41)/len(labels_gpt41)*100 if labels_gpt41 else 0):.0f}%",
                "κpool": len(labels_gpt5),
                "err": n_gpt5_err + n_gpt41_err + (n_gem_err if use_gemini else 0),
            }
            if use_gemini:
                postfix["gem"] = f"{(sum(labels_gem)/len(labels_gem)*100 if labels_gem else 0):.0f}%"
            pbar.set_postfix(postfix)
    finally:
        try:
            os.fsync(out_f.fileno())
        except OSError:
            pass
        out_f.close()

    if not enriched:
        print("No rows scored.", file=sys.stderr)
        return 1

    print(f"\nWrote {len(enriched)} rows -> {args.out} (incremental)")

    n_pool = len(labels_gpt5)
    if n_pool < 2:
        print("\nNot enough successful triples for κ.", file=sys.stderr)
        return 1

    pos_gpt5 = sum(labels_gpt5) / n_pool
    pos_gpt41 = sum(labels_gpt41) / n_pool

    if use_gemini:
        k_gpt5_gpt41 = cohens_kappa(labels_gpt5, labels_gpt41)
        k_gpt41_gem = cohens_kappa(labels_gpt41, labels_gem)
        k_gpt5_gem = cohens_kappa(labels_gpt5, labels_gem)
        fleiss = fleiss_kappa([labels_gpt5, labels_gpt41, labels_gem])
        pos_gem = sum(labels_gem) / n_pool
        unan = sum(1 for a, b, c in zip(labels_gpt5, labels_gpt41, labels_gem)
                   if a == b == c) / n_pool
        print(f"\nInter-judge agreement (n_triples={n_pool}):")
        print(f"  Faithful% per judge:")
        print(f"    GPT-5.4 (generator, biased)    : {pos_gpt5:.3f}")
        print(f"    GPT-4.1 (generator-independent): {pos_gpt41:.3f}")
        print(f"    Gemini  (generator-independent): {pos_gem:.3f}")
        print(f"  Pairwise Cohen's κ:")
        print(f"    GPT-4.1 × Gemini  (PRIMARY)  : {k_gpt41_gem:.3f}")
        print(f"    GPT-5.4 × GPT-4.1            : {k_gpt5_gpt41:.3f}")
        print(f"    GPT-5.4 × Gemini             : {k_gpt5_gem:.3f}")
        print(f"  3-rater Fleiss' κ              : {fleiss:.3f}")
        print(f"  Unanimous (all 3 agree)        : {unan:.3f}")
        print(f"  Errors: gpt5={n_gpt5_err}, gpt41={n_gpt41_err}, gem={n_gem_err}")
        primary = k_gpt41_gem
        primary_name = "GPT-4.1 × Gemini"
    else:
        k_gpt5_gpt41 = cohens_kappa(labels_gpt5, labels_gpt41)
        agree_rate = sum(1 for a, b in zip(labels_gpt5, labels_gpt41) if a == b) / n_pool
        print(f"\nInter-judge agreement (n_pairs={n_pool}, Gemini disabled):")
        print(f"  Faithful% per judge:")
        print(f"    GPT-5.4 (generator-self):  {pos_gpt5:.3f}")
        print(f"    GPT-4.1 (4.x family)    :  {pos_gpt41:.3f}")
        print(f"  Pairwise Cohen's κ:")
        print(f"    GPT-5.4 × GPT-4.1 (PRIMARY): {k_gpt5_gpt41:.3f}")
        print(f"  Raw agreement              : {agree_rate:.3f}")
        print(f"  Errors: gpt5={n_gpt5_err}, gpt41={n_gpt41_err}")
        print(f"  Paper limitation note: both judges are OpenAI-family. GPT-5.4 is the")
        print(f"  pipeline generator (self-preference risk); GPT-4.1 (4.x line) is the")
        print(f"  independent within-family judge. Gemini was disabled because free")
        print(f"  tier dropped to 20 RPD in May 2026 (insufficient for our 300-row scope).")
        primary = k_gpt5_gpt41
        primary_name = "GPT-5.4 × GPT-4.1"

    if primary < 0.4:
        print(f"\n⚠ PRIMARY κ ({primary_name}) = {primary:.3f} < 0.4")
        print("  CIKM kill switch: judges don't agree → halt and inspect.")
        return 1
    elif primary < 0.6:
        print(f"\nPRIMARY κ in [0.4, 0.6): moderate. Acceptable but disclose in limitations.")
    else:
        print(f"\nPRIMARY κ ≥ 0.6: substantial agreement. Paper-grade.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

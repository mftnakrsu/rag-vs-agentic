"""Generate hop-stratified evaluation queries from the requirement graph.

Phase 2a — produces 300 evaluation queries stratified by hop distance:
    100 × 1-hop  (a -[rel]- b)
    100 × 2-hop  (a -[rel1]- m -[rel2]- b)
    100 × 3+-hop (a -[*3..4]- b)

For each sampled chain, GPT-5.4 phrases ONE natural-language question that
could be answered by retrieving the chain's requirements. The output JSONL
joins the structural ground truth (expected_ids, rel_path) with the
generated query, so we can compute citation precision/recall + faithfulness
per hop stratum in Phase 2b/2c.

Output:
    data/eval/queries-hop-stratified.jsonl
    {
      "query": "...",
      "type": "1-hop" | "2-hop" | "3+-hop",
      "hop_count": int,
      "rel_path": ["REFERENCES", "DERIVES_FROM"],
      "expected_ids": ["ADS-014", "ADS-026"],
      "source_id": "ADS-014",
      "target_id": "ADS-026",
      "source_module": "ADS",
      "target_module": "ADS",
      "is_cross_module": false
    }

CLI:
    python eval_generator.py --dry-run            # sample chains, print, no LLM
    python eval_generator.py --limit 10           # generate only 10 queries (smoke)
    python eval_generator.py                      # full 300 (default)
    python eval_generator.py --strata 1-hop       # only 1-hop sample
    python eval_generator.py --resume             # append to existing output
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv

from aerorag.graph_store import TRACEABILITY_LINK_TYPES, get_driver
from aerorag.llm_compat import GPT5Client


# Sampling Cypher per stratum. We restrict to :Requirement <-> :Requirement
# edges along the traceability whitelist so the chains are retrieval-relevant.
SAMPLE_1HOP = """
MATCH (a:Requirement)-[r]->(b:Requirement)
WHERE type(r) IN $rel_types
RETURN a.id AS source_id, a.module AS source_module, a.full_text AS source_text,
       a.heading AS source_heading,
       b.id AS target_id, b.module AS target_module, b.full_text AS target_text,
       b.heading AS target_heading,
       type(r) AS rel
""".strip()

# 2-hop: directed paths of length 2 with both edges in whitelist.
SAMPLE_2HOP = """
MATCH (a:Requirement)-[r1]->(m:Requirement)-[r2]->(b:Requirement)
WHERE type(r1) IN $rel_types AND type(r2) IN $rel_types
  AND a.id <> b.id
RETURN a.id AS source_id, a.module AS source_module, a.full_text AS source_text,
       a.heading AS source_heading,
       m.id AS mid_id, m.module AS mid_module, m.full_text AS mid_text,
       m.heading AS mid_heading,
       b.id AS target_id, b.module AS target_module, b.full_text AS target_text,
       b.heading AS target_heading,
       type(r1) AS rel1, type(r2) AS rel2
""".strip()

# 3-4 hop: variable length paths with edge-type constraint via predicate.
SAMPLE_LONG = """
MATCH path = (a:Requirement)-[*3..4]->(b:Requirement)
WHERE all(rel IN relationships(path) WHERE type(rel) IN $rel_types)
  AND a.id <> b.id
WITH path, a, b
RETURN a.id AS source_id, a.module AS source_module, a.full_text AS source_text,
       a.heading AS source_heading,
       b.id AS target_id, b.module AS target_module, b.full_text AS target_text,
       b.heading AS target_heading,
       length(path) AS hop_count,
       [n IN nodes(path) | n.id] AS path_ids,
       [n IN nodes(path) | n.module] AS path_modules,
       [rel IN relationships(path) | type(rel)] AS rel_path
""".strip()


def sample_chains(driver, stratum: str, n: int, seed: int = 0) -> list[dict]:
    """Sample `n` chains for the given stratum. Returns raw dicts (no query yet).

    stratum: '1-hop' | '2-hop' | '3+-hop'
    """
    if stratum == "1-hop":
        cypher = SAMPLE_1HOP
    elif stratum == "2-hop":
        cypher = SAMPLE_2HOP
    elif stratum == "3+-hop":
        cypher = SAMPLE_LONG
    else:
        raise ValueError(f"unknown stratum: {stratum!r}")

    with driver.session() as session:
        all_rows = session.execute_read(
            lambda tx: list(tx.run(cypher, rel_types=list(TRACEABILITY_LINK_TYPES)))
        )
    pop = [dict(r) for r in all_rows]
    rng = random.Random(seed)
    rng.shuffle(pop)
    chains = pop[:n]
    for c in chains:
        c["_stratum"] = stratum
    return chains


QUERY_PROMPT_1HOP = """You are generating evaluation questions for a RAG system over an aerospace requirements corpus (DOORS export).

Given a directly-linked pair of requirements:
  Source [{source_id}] ({source_module} :: {source_heading}):
    {source_text}

  --[{rel}]--> Target [{target_id}] ({target_module} :: {target_heading}):
    {target_text}

Write ONE natural-language question that:
1. Could be answered by retrieving these two requirements
2. Tests understanding of the {rel} relationship between them
3. Is phrased like an aerospace engineer or DO-178C reviewer would ask
4. Is concise (10-25 words)
5. Avoids quoting the requirement IDs verbatim — phrase semantically

Return ONLY the question, no preamble, no quotes, no commentary."""

QUERY_PROMPT_2HOP = """You are generating evaluation questions for a RAG system over an aerospace requirements corpus.

Given a 2-hop chain of linked requirements:
  Source [{source_id}] ({source_module} :: {source_heading}):
    {source_text}

  --[{rel1}]--> Mid [{mid_id}] ({mid_module} :: {mid_heading}):
    {mid_text}

  --[{rel2}]--> Target [{target_id}] ({target_module} :: {target_heading}):
    {target_text}

Write ONE natural-language question that:
1. Requires reasoning across all THREE requirements to answer well
2. Naturally chains the {rel1} -> {rel2} relationship without quoting IDs
3. Reads like an aerospace engineer would ask it
4. Is concise (12-30 words)

Return ONLY the question."""

QUERY_PROMPT_LONG = """You are generating evaluation questions for a RAG system over an aerospace requirements corpus.

Given a {hop_count}-hop traceability chain:
{chain_block}

Modules touched: {modules}

Write ONE natural-language question that:
1. Requires retrieving and reasoning across the whole chain to answer fully
2. Tests cross-module / cross-subsystem traceability
3. Reads like a real engineer's question (concise, technical)
4. Avoids quoting requirement IDs verbatim

Return ONLY the question (12-35 words)."""


def fmt_chain_block(chain: dict) -> str:
    """Format the path nodes/edges as a numbered chain for the prompt."""
    ids = chain["path_ids"]
    rels = chain["rel_path"]
    lines = [f"  Hop 0  [{ids[0]}]"]
    for i, rel in enumerate(rels, start=1):
        lines.append(f"   --[{rel}]--> Hop {i}  [{ids[i]}]")
    return "\n".join(lines)


def generate_query(llm: GPT5Client, chain: dict) -> str:
    s = chain["_stratum"]
    if s == "1-hop":
        prompt = QUERY_PROMPT_1HOP.format(**chain)
    elif s == "2-hop":
        prompt = QUERY_PROMPT_2HOP.format(**chain)
    else:
        prompt = QUERY_PROMPT_LONG.format(
            hop_count=chain["hop_count"],
            chain_block=fmt_chain_block(chain),
            modules=", ".join(sorted(set(chain["path_modules"]))),
        )
    resp = llm.chat(messages=[
        {"role": "system", "content": "You write concise evaluation questions, one at a time."},
        {"role": "user", "content": prompt},
    ])
    text = (resp.choices[0].message.content or "").strip()
    # Strip enclosing quotes if the LLM added them
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        text = text[1:-1].strip()
    return text


def to_record(chain: dict, query: str) -> dict:
    """Build the canonical eval-record from chain + generated query."""
    s = chain["_stratum"]
    if s == "1-hop":
        rec = {
            "query": query,
            "type": "1-hop",
            "hop_count": 1,
            "rel_path": [chain["rel"]],
            "expected_ids": [chain["source_id"], chain["target_id"]],
            "source_id": chain["source_id"],
            "target_id": chain["target_id"],
            "source_module": chain["source_module"],
            "target_module": chain["target_module"],
        }
    elif s == "2-hop":
        rec = {
            "query": query,
            "type": "2-hop",
            "hop_count": 2,
            "rel_path": [chain["rel1"], chain["rel2"]],
            "expected_ids": [chain["source_id"], chain["mid_id"], chain["target_id"]],
            "source_id": chain["source_id"],
            "target_id": chain["target_id"],
            "source_module": chain["source_module"],
            "target_module": chain["target_module"],
            "mid_modules": [chain["mid_module"]],
        }
    else:  # 3+-hop
        rec = {
            "query": query,
            "type": "3+-hop",
            "hop_count": int(chain["hop_count"]),
            "rel_path": list(chain["rel_path"]),
            "expected_ids": list(chain["path_ids"]),
            "source_id": chain["source_id"],
            "target_id": chain["target_id"],
            "source_module": chain["source_module"],
            "target_module": chain["target_module"],
            "path_modules": list(chain["path_modules"]),
        }
    rec["is_cross_module"] = rec["source_module"] != rec["target_module"]
    return rec


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--strata", default="1-hop,2-hop,3+-hop",
        help="Comma-separated subset of {1-hop, 2-hop, 3+-hop}. Default: all three.",
    )
    parser.add_argument(
        "--per-stratum", type=int, default=100,
        help="Queries per stratum. Default 100 -> 300 total.",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Cap total queries (for smoke runs). Overrides per-stratum proportionally.",
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Sample chains and print, no LLM call")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path,
                        default=Path("data/eval/queries-hop-stratified.jsonl"))
    parser.add_argument("--resume", action="store_true",
                        help="Append to existing output, skip already-generated source_id pairs")
    args = parser.parse_args()

    load_dotenv()

    strata = [s.strip() for s in args.strata.split(",") if s.strip()]
    n_per = args.per_stratum
    if args.limit is not None:
        n_per = max(1, args.limit // max(1, len(strata)))

    print(f"Sampling {n_per} chains per stratum across {strata} (seed={args.seed})")

    driver = get_driver()
    all_chains: list[dict] = []
    try:
        for s in strata:
            chains = sample_chains(driver, s, n=n_per, seed=args.seed)
            print(f"  {s}: sampled {len(chains)} chains")
            all_chains.extend(chains)
    finally:
        driver.close()

    if args.dry_run:
        print(f"\n--- DRY RUN ({len(all_chains)} chains) ---")
        for i, c in enumerate(all_chains[:5]):
            print(f"\n[{i}] {c['_stratum']}")
            if c["_stratum"] == "1-hop":
                print(f"  {c['source_id']} -[{c['rel']}]-> {c['target_id']}  "
                      f"({c['source_module']} -> {c['target_module']})")
            elif c["_stratum"] == "2-hop":
                print(f"  {c['source_id']} -[{c['rel1']}]-> {c['mid_id']} "
                      f"-[{c['rel2']}]-> {c['target_id']}")
            else:
                print(f"  {' -> '.join(c['path_ids'])}  rels={c['rel_path']}")
        print(f"\n... + {len(all_chains) - 5} more (use without --dry-run to LLM-generate queries)")
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    seen_keys: set[tuple] = set()
    if args.resume and args.out.exists():
        with args.out.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    key = (rec.get("source_id"), rec.get("target_id"), rec.get("type"))
                    seen_keys.add(key)
                except json.JSONDecodeError:
                    pass
        print(f"  resume: {len(seen_keys)} existing records found, will skip duplicates")

    llm = GPT5Client()
    n_done = 0
    n_skipped = 0
    n_failed = 0
    t0 = time.time()
    mode = "a" if args.resume else "w"
    with args.out.open(mode, encoding="utf-8") as f:
        for i, chain in enumerate(all_chains, 1):
            key = (chain.get("source_id"), chain.get("target_id"), chain["_stratum"])
            if key in seen_keys:
                n_skipped += 1
                continue
            try:
                q = generate_query(llm, chain)
                rec = to_record(chain, q)
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                n_done += 1
                seen_keys.add(key)
                if n_done % 10 == 0:
                    elapsed = time.time() - t0
                    rate = n_done / elapsed if elapsed > 0 else 0
                    print(f"  [{i}/{len(all_chains)}] {n_done} done, "
                          f"{n_failed} fail, {n_skipped} skip ({rate:.2f}/s)")
            except Exception as e:  # noqa: BLE001
                n_failed += 1
                print(f"  [{i}/{len(all_chains)}] FAIL: {type(e).__name__}: {e}",
                      file=sys.stderr)

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.0f}s. Wrote {n_done} new records to {args.out} "
          f"(skipped {n_skipped} dups, {n_failed} failures).")
    return 0 if n_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

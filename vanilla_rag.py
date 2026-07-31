"""Vanilla RAG pipeline.

    query -> embed -> ChromaDB top-K -> (optional rerank) -> single LLM call -> answer

Returns a dict the comparison harness can serialize.
"""
from __future__ import annotations

import os
import re
import sys
import time
from typing import Optional

from dotenv import load_dotenv

from embedders import get_embedder
from llm_compat import GPT5Client
from reranker import get_reranker
from vector_store import get_client, get_or_create_collection, query_top_k


GROUNDED_SYSTEM_PROMPT = """You are an aerospace requirements engineer answering questions about a DOORS-exported requirements set.
Rules:
 1. Ground every claim in retrieved requirements; cite the IDs you used inline as [ADS-014].
 2. If the retrieved context does not contain the answer, say so plainly. Do not invent.
 3. Prefer concise, technical wording. Reproduce numeric thresholds (Hz, kt, ft, ms, °) verbatim.
 4. When requirements interact (e.g., FCC <-> ADS), explain the relationship.
"""


# Same pattern as agentic_rag._ID_PATTERN (kept local: agentic_rag pulls in
# langgraph, too heavy for this module's import chain).
_ID_RE = re.compile(r"\b([A-Z]{2,5}-(?:[A-Z]?\d+))\b")


def _parse_cited(answer: str) -> list[str]:
    return list(dict.fromkeys(_ID_RE.findall(answer or "")))


def _coll_for(embedder_name: str) -> tuple[str, int]:
    if embedder_name == "local":
        return (os.environ.get("CHROMA_COLLECTION_LOCAL", "docs-local-e5"), 384)
    return (
        os.environ.get("CHROMA_COLLECTION_AZURE", "docs-azure"),
        int(os.environ.get("AZURE_OPENAI_EMBEDDING_DIMENSION", 1536)),
    )


def _format_context(hits: list[dict]) -> str:
    parts = []
    for h in hits:
        parts.append(
            f"[{h['id']}] ({h.get('module', '')} :: {h.get('heading', '')})\n"
            f"{h['full_text']}"
        )
    return "\n\n---\n\n".join(parts)


def vanilla_rag(
    query: str,
    *,
    embedder_name: str = "local",
    reranker_name: Optional[str] = None,
    top_k: int = 10,
    top_n_after_rerank: int = 5,
) -> dict:
    t0 = time.time()

    embedder = get_embedder(embedder_name)
    qvec = embedder.embed_query(query)

    client = get_client()
    coll_name, dim = _coll_for(embedder_name)
    col = get_or_create_collection(client, coll_name, dim=dim)
    hits = query_top_k(col, qvec, k=top_k)

    if reranker_name:
        rr = get_reranker(reranker_name)
        hits = rr.rerank(query, hits, top_n=top_n_after_rerank)
    else:
        hits = hits[:top_n_after_rerank]

    llm = GPT5Client()
    context = _format_context(hits)
    user_msg = f"Context (retrieved requirements):\n\n{context}\n\nQ: {query}"

    resp = llm.chat(messages=[
        {"role": "system", "content": GROUNDED_SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ])

    answer = resp.choices[0].message.content or ""
    usage = GPT5Client.usage(resp)

    return {
        "pipeline": f"vanilla|{embedder_name}|{reranker_name or 'norerank'}",
        "query": query,
        "answer": answer,
        "sources": hits,
        # answer-parsed citations (ALCE-style); the context set lives in `sources`
        "cited_ids": _parse_cited(answer),
        "latency_ms": int((time.time() - t0) * 1000),
        "tokens": usage,
    }


if __name__ == "__main__":
    load_dotenv()
    q = sys.argv[1] if len(sys.argv) > 1 else \
        "What does ADS-014 specify about pitot blockage detection?"

    print(f"\n[query] {q}\n")
    result = vanilla_rag(q, embedder_name="local", reranker_name=None)
    total = result["tokens"].get("total_tokens", 0)
    print(f"--- Answer ({result['latency_ms']}ms, {total} tokens) ---")
    print(result["answer"])
    print("\n--- Sources ---")
    for h in result["sources"]:
        score = h.get("_rerank_score", h.get("_distance"))
        print(f"  {h['id']:10s}  score={score!s:>8}  {h.get('heading', '')[:70]}")

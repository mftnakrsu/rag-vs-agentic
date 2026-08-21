"""ChromaDB persistent-client helpers.

We never use Chroma's built-in embedding function — embeddings always come from
embedders.py (LocalE5SmallEmbedder | AzureOpenAIEmbedder). Each embedder gets
its own collection so the dim is consistent.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

import chromadb
from chromadb.config import Settings

from aerorag.data_loader import chunk_to_metadata


def get_client(path: str | None = None) -> chromadb.api.ClientAPI:
    p = path or os.environ.get("CHROMA_PATH", "./data/chroma")
    Path(p).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=p,
        settings=Settings(anonymized_telemetry=False, allow_reset=True),
    )


def get_or_create_collection(client, name: str, *, dim: int):
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine", "embedder_dim": dim},
    )


def upsert_chunks(
    collection,
    chunks: List[dict],
    embeddings: List[List[float]],
    *,
    batch_size: int = 200,
) -> None:
    """Upsert (id-keyed) chunks + embeddings into the collection."""
    if not chunks:
        return
    if len(chunks) != len(embeddings):
        raise ValueError(f"len(chunks)={len(chunks)} != len(embeddings)={len(embeddings)}")
    n = len(chunks)
    for i in range(0, n, batch_size):
        sl = slice(i, i + batch_size)
        collection.upsert(
            ids=[c["id"] for c in chunks[sl]],
            documents=[c["full_text"] for c in chunks[sl]],
            embeddings=embeddings[sl],
            metadatas=[chunk_to_metadata(c) for c in chunks[sl]],
        )


def query_top_k(
    collection,
    query_embedding: List[float],
    *,
    k: int = 10,
    where: dict | None = None,
) -> List[dict]:
    """Top-k cosine search. Returns chunks with `_distance` (cosine distance)."""
    res = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        where=where,
    )
    if not res["ids"] or not res["ids"][0]:
        return []
    out: List[dict] = []
    ids = res["ids"][0]
    docs = res["documents"][0]
    metas = res["metadatas"][0] or [{} for _ in ids]
    dists = res["distances"][0]
    for i, _id in enumerate(ids):
        out.append({
            "id": _id,
            "full_text": docs[i],
            **(metas[i] or {}),
            "_distance": float(dists[i]),
        })
    return out


def fetch_by_id(collection, ids: List[str]) -> List[dict]:
    """Fetch specific chunks by id (used by the agentic id_lookup path)."""
    if not ids:
        return []
    res = collection.get(ids=ids)
    out: List[dict] = []
    for i, _id in enumerate(res["ids"]):
        out.append({
            "id": _id,
            "full_text": res["documents"][i],
            **(res["metadatas"][i] or {}),
        })
    return out

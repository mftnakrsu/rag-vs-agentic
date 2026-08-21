#!/usr/bin/env python
"""Phase F-2: Ingest MuSiQue chunks into ChromaDB collection 'musique-azure'.

Uses Azure text-embedding-3-small (1536d). Idempotent (upsert).
"""
import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
CHUNKS = ROOT / "data" / "musique" / "chunks.jsonl"
COLLECTION = "musique-azure"


def main():
    load_dotenv(ROOT / ".env")
    from aerorag.embedders import AzureOpenAIEmbedder
    from aerorag.vector_store import get_client, get_or_create_collection

    chunks = [json.loads(line) for line in open(CHUNKS)]
    print(f"loading {len(chunks)} chunks from {CHUNKS}")

    emb = AzureOpenAIEmbedder()
    client = get_client()
    col = get_or_create_collection(client, COLLECTION, dim=emb.DIM)
    print(f"collection '{COLLECTION}' opened, dim={emb.DIM}, existing count={col.count()}")

    texts = [c["text"] for c in chunks]
    ids = [c["id"] for c in chunks]
    metas = [{
        "title": c["title"],
        "is_supporting": c["is_supporting"],
        "mq_query_idx": c["mq_query_idx"],
    } for c in chunks]

    print(f"embedding {len(texts)} chunks (batch=64) via Azure 3-small...")
    t0 = time.time()
    vectors = emb.embed_documents(texts, batch_size=64)
    print(f"  embedded in {time.time() - t0:.1f}s, dim={len(vectors[0])}")

    UPSERT_BATCH = 200
    for i in range(0, len(ids), UPSERT_BATCH):
        col.upsert(
            ids=ids[i:i + UPSERT_BATCH],
            documents=texts[i:i + UPSERT_BATCH],
            metadatas=metas[i:i + UPSERT_BATCH],
            embeddings=vectors[i:i + UPSERT_BATCH],
        )
    print(f"upsert done. collection '{COLLECTION}': count={col.count()}")


if __name__ == "__main__":
    main()

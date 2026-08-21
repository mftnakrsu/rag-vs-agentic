#!/usr/bin/env python
"""Index the AeroSys corpus with BAAI/bge-m3 into the 'docs-bge-m3' collection.

Third embedder axis (1024d), independent of e5-small (Microsoft) and
text-embedding-3-small (OpenAI). build_index.py only knows the original two
and reads e5 weights from a path that is not on this machine, so this is a
standalone indexer for the bge collection.
"""
import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CORPUS = ROOT / "data" / "synthetic" / "requirements.jsonl"


def main() -> int:
    load_dotenv(ROOT / ".env")
    from aerorag.embedders import get_embedder
    from aerorag.vector_store import get_client, get_or_create_collection, upsert_chunks

    rows = [json.loads(l) for l in CORPUS.open()]
    print(f"{len(rows)} requirements from {CORPUS.name}")

    emb = get_embedder("bge")
    col = get_or_create_collection(get_client(), "docs-bge-m3", dim=emb.DIM)
    if col.count() >= len(rows):
        print(f"collection already has {col.count()} chunks — nothing to do")
        return 0

    texts = [r["full_text"] for r in rows]
    t0 = time.time()
    vectors = emb.embed_documents(texts, batch_size=16)
    print(f"embedded {len(vectors)} chunks (dim={len(vectors[0])}) in {time.time()-t0:.1f}s")

    upsert_chunks(col, rows, vectors)
    print(f"collection 'docs-bge-m3': count={col.count()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

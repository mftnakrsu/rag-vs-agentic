"""Index the AeroSys requirements corpus into two ChromaDB collections.

    python build_index.py                # both embedders, skip if up-to-date
    python build_index.py --embedder local --force
"""
from __future__ import annotations

import argparse
import os
import time

from dotenv import load_dotenv

from data_loader import load_chunks
from embedders import AzureOpenAIEmbedder, LocalE5SmallEmbedder
from vector_store import get_client, get_or_create_collection, upsert_chunks


def _index(chunks: list[dict], embedder, collection_name: str, dim: int, *, force: bool) -> None:
    client = get_client()
    if force:
        try:
            client.delete_collection(collection_name)
            print(f"  [{collection_name}] dropped")
        except Exception:  # noqa: BLE001
            pass
    col = get_or_create_collection(client, collection_name, dim=dim)

    existing = col.count()
    if existing == len(chunks) and not force:
        print(f"  [{collection_name}] already has {existing} chunks — skipping")
        return

    print(f"  [{collection_name}] embedding {len(chunks)} chunks (dim={dim}) …")
    t0 = time.time()
    vectors = embedder.embed_documents([c["full_text"] for c in chunks])
    print(f"  [{collection_name}] embedded in {time.time() - t0:.1f}s")

    upsert_chunks(col, chunks, vectors)
    print(f"  [{collection_name}] total chunks now: {col.count()}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--embedder", choices=["local", "azure", "both"], default="both")
    parser.add_argument("--force", action="store_true", help="Drop & rebuild collections")
    args = parser.parse_args()

    load_dotenv()
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks from {os.environ['DATA_PATH']}")

    if args.embedder in ("local", "both"):
        print("\n→ Local intfloat/multilingual-e5-small (384d)")
        _index(
            chunks,
            LocalE5SmallEmbedder(),
            os.environ.get("CHROMA_COLLECTION_LOCAL", "docs-local-e5"),
            dim=LocalE5SmallEmbedder.DIM,
            force=args.force,
        )

    if args.embedder in ("azure", "both"):
        print("\n→ Azure OpenAI text-embedding-3-small")
        emb = AzureOpenAIEmbedder()
        _index(
            chunks,
            emb,
            os.environ.get("CHROMA_COLLECTION_AZURE", "docs-azure"),
            dim=emb.DIM,
            force=args.force,
        )


if __name__ == "__main__":
    main()

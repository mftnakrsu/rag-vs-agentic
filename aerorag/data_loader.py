"""Load AeroSys synthetic-requirements JSONL into chunk dicts.

Each line of requirements.jsonl is already a chunk-sized requirement (most are
1-3 sentences). No further chunking is needed — we filter empty/trivial rows
and project to the canonical fields the rest of the pipeline expects.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

CANONICAL_FIELDS = (
    "id", "module", "heading", "level", "object_type",
    "full_text", "outgoing_links", "incoming_links",
)

MIN_TEXT_LEN = 30  # drop heading-only / structural rows


def load_chunks(path: str | os.PathLike | None = None) -> list[dict]:
    """Load and normalize the JSONL corpus."""
    path = Path(path or os.environ["DATA_PATH"])
    out: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            text = (row.get("full_text") or row.get("text") or "").strip()
            if len(text) < MIN_TEXT_LEN:
                continue
            out.append({
                "id": row["id"],
                "module": row.get("module", ""),
                "heading": row.get("heading", ""),
                "level": int(row.get("level", 0) or 0),
                "object_type": row.get("object_type", ""),
                "full_text": text,
                "outgoing_links": row.get("outgoing_links") or [],
                "incoming_links": row.get("incoming_links") or [],
            })
    return out


def chunk_to_metadata(chunk: dict[str, Any]) -> dict[str, str | int | float | bool]:
    """Flatten a chunk for ChromaDB metadata (only scalars allowed)."""
    return {
        "id": chunk["id"],
        "module": chunk["module"],
        "heading": chunk["heading"][:120],
        "level": int(chunk["level"]),
        "object_type": chunk["object_type"],
        "n_outgoing": len(chunk["outgoing_links"]),
        "n_incoming": len(chunk["incoming_links"]),
    }


def chunks_by_id(chunks: list[dict]) -> dict[str, dict]:
    return {c["id"]: c for c in chunks}


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks")
    by_module: dict[str, int] = {}
    for c in chunks:
        by_module[c["module"]] = by_module.get(c["module"], 0) + 1
    print("Per-module:", dict(sorted(by_module.items(), key=lambda kv: -kv[1])[:8]), "…")
    sample = chunks[0]
    print(f"\nSample [{sample['id']}] {sample['module']} :: {sample['heading']}")
    print(sample["full_text"][:200], "…" if len(sample["full_text"]) > 200 else "")
    print(f"links out={len(sample['outgoing_links'])}, in={len(sample['incoming_links'])}")

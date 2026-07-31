#!/usr/bin/env python
"""Phase F-3: Ingest MuSiQue MQ-* nodes + REFERENCES edges into Aura.

Uses the same :Requirement label as the synthetic corpus so walk_2hop
applies unchanged. New nodes carry property `musique:true` for filtering.
Idempotent (MERGE).
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
CHUNKS = ROOT / "data" / "musique" / "chunks.jsonl"
EDGES = ROOT / "data" / "musique" / "edges.jsonl"


def main():
    load_dotenv(ROOT / ".env")
    from neo4j import GraphDatabase

    uri = os.environ["NEO4J_URI"]
    user = os.environ["NEO4J_USER"]
    pwd = os.environ["NEO4J_PASSWORD"]

    chunks = [json.loads(line) for line in open(CHUNKS)]
    edges = [json.loads(line) for line in open(EDGES)]
    print(f"{len(chunks)} chunks, {len(edges)} edges to ingest")

    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    with driver.session() as session:
        BATCH = 500
        for i in range(0, len(chunks), BATCH):
            batch = chunks[i:i + BATCH]
            session.run(
                "UNWIND $rows AS row "
                "MERGE (n:Requirement {id: row.id}) "
                "SET n.title = row.title, n.text = row.text, "
                "    n.musique = true, n.is_supporting = row.is_supporting",
                rows=[{
                    "id": c["id"], "title": c["title"], "text": c["text"],
                    "is_supporting": c["is_supporting"],
                } for c in batch],
            )
        print(f"merged {len(chunks)} :Requirement nodes")

        if edges:
            session.run(
                "UNWIND $rows AS row "
                "MATCH (a:Requirement {id: row.src}), (b:Requirement {id: row.tgt}) "
                "MERGE (a)-[:REFERENCES]->(b)",
                rows=[{"src": e["source"], "tgt": e["target"]} for e in edges],
            )
            print(f"merged {len(edges)} REFERENCES edges")

        # Sanity check
        result = session.run("MATCH (n:Requirement {musique: true}) RETURN count(n) AS c")
        print(f"  total MuSiQue nodes in Aura: {result.single()['c']}")
        result = session.run(
            "MATCH (a:Requirement {musique: true})-[r:REFERENCES]->(b:Requirement {musique: true}) "
            "RETURN count(r) AS c"
        )
        print(f"  total MuSiQue->MuSiQue REFERENCES edges: {result.single()['c']}")
    driver.close()


if __name__ == "__main__":
    main()

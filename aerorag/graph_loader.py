"""Load AeroSys synthetic-requirements JSONL into Neo4j Aura.

Schema:
    (:Requirement {id, module, level, heading, full_text, object_type,
                   is_heading, module_path, attrs_json})
    (:Requirement)-[:REFERENCES|:DERIVES_FROM|:SATISFIES|:TRACES_TO]->(:Requirement)

Idempotent. Node id is the unique key (constraint enforced).

Usage:
    python graph_loader.py --dry-run       # print planned Cypher, no Aura connection
    python graph_loader.py                 # real ETL against $NEO4J_URI
    python graph_loader.py --reset         # DELETE all :Requirement first, then load
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

# Whitelist of link_types we ETL. Unknown values are reported and skipped.
# Cypher doesn't accept $param for relationship type, so we use this map to
# string-format the relationship type into the Cypher template — safe because
# the values are hard-coded UPPER_SNAKE constants here.
KNOWN_LINK_TYPES: dict[str, str] = {
    "references": "REFERENCES",
    "derives_from": "DERIVES_FROM",
    "satisfies": "SATISFIES",
    "verifies": "VERIFIES",
    "refines": "REFINES",
    "traces_to": "TRACES_TO",
    "implements": "IMPLEMENTS",
    "tests": "TESTS",
    "allocates_to": "ALLOCATES_TO",
}


def read_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def project_node(row: dict) -> dict:
    """Project a raw JSONL row to a flat Neo4j-property dict."""
    text = (row.get("full_text") or row.get("text") or "").strip()
    return {
        "id": row["id"],
        "module": row.get("module", ""),
        "level": int(row.get("level", 0) or 0),
        "heading": (row.get("heading") or "").strip(),
        "full_text": text,
        "object_type": row.get("object_type", ""),
        "is_heading": bool(row.get("is_heading", False)),
        "module_path": row.get("module_path", ""),
        "attrs_json": json.dumps(row.get("attributes") or {}, ensure_ascii=False),
    }


def extract_edges(rows: list[dict]) -> tuple[dict[str, list[dict]], dict[str, int]]:
    """Group outgoing_links by uppercased relationship type.

    Returns:
        edges_by_rel: {REL_TYPE: [{"source": id, "target": id}, ...]}
        skipped:      {raw_link_type: count} for unknown link types
    """
    by_rel: dict[str, list[dict]] = defaultdict(list)
    skipped: dict[str, int] = defaultdict(int)
    for row in rows:
        src = row["id"]
        for link in row.get("outgoing_links") or []:
            tgt = link.get("target_id")
            lt = (link.get("link_type") or "").strip().lower()
            if not tgt or not lt:
                continue
            rel = KNOWN_LINK_TYPES.get(lt)
            if rel is None:
                skipped[lt] += 1
                continue
            by_rel[rel].append({"source": src, "target": tgt})
    return dict(by_rel), dict(skipped)


CYPHER_NODE = """
UNWIND $rows AS row
MERGE (r:Requirement {id: row.id})
SET r.module = row.module,
    r.level = row.level,
    r.heading = row.heading,
    r.full_text = row.full_text,
    r.object_type = row.object_type,
    r.is_heading = row.is_heading,
    r.module_path = row.module_path,
    r.attrs_json = row.attrs_json
""".strip()

CYPHER_EDGE_TEMPLATE = """
UNWIND $edges AS e
MATCH (a:Requirement {id: e.source})
MATCH (b:Requirement {id: e.target})
MERGE (a)-[:%s]->(b)
""".strip()

CYPHER_SCHEMA: list[str] = [
    "CREATE CONSTRAINT requirement_id_unique IF NOT EXISTS "
    "FOR (r:Requirement) REQUIRE r.id IS UNIQUE",
    "CREATE INDEX requirement_module IF NOT EXISTS "
    "FOR (r:Requirement) ON (r.module)",
]

CYPHER_RESET = "MATCH (r:Requirement) DETACH DELETE r"


def run_etl(
    driver,
    nodes: list[dict],
    edges_by_rel: dict[str, list[dict]],
    *,
    reset: bool = False,
    batch_size: int = 500,
) -> dict:
    """Execute the ETL against an open Neo4j driver. Returns counts dict."""
    counts: dict = {"nodes": 0, "edges": defaultdict(int)}
    with driver.session() as session:
        if reset:
            session.execute_write(lambda tx: tx.run(CYPHER_RESET))
        for stmt in CYPHER_SCHEMA:
            session.execute_write(lambda tx, q=stmt: tx.run(q))
        for i in range(0, len(nodes), batch_size):
            chunk = nodes[i : i + batch_size]
            session.execute_write(lambda tx, c=chunk: tx.run(CYPHER_NODE, rows=c))
            counts["nodes"] += len(chunk)
        for rel, edges in edges_by_rel.items():
            cypher = CYPHER_EDGE_TEMPLATE % rel
            for i in range(0, len(edges), batch_size):
                chunk = edges[i : i + batch_size]
                session.execute_write(lambda tx, q=cypher, c=chunk: tx.run(q, edges=c))
                counts["edges"][rel] += len(chunk)
    counts["edges"] = dict(counts["edges"])
    return counts


def sanity_check(driver) -> dict:
    """Aura-side counts + orphan-target probe. Run after ETL."""
    out: dict = {}
    with driver.session() as session:
        out["nodes"] = session.execute_read(
            lambda tx: tx.run(
                "MATCH (r:Requirement) RETURN count(r) AS n"
            ).single()["n"]
        )
        rec = session.execute_read(
            lambda tx: list(tx.run(
                "MATCH ()-[r]->() RETURN type(r) AS t, count(r) AS n"
            ))
        )
        out["edges"] = {row["t"]: row["n"] for row in rec}
        # Orphan targets: edges pointing to ids that don't exist as nodes.
        # In MERGE-MATCH ETL these would have been silently dropped, so this
        # query exists to detect ETL bugs / source-data inconsistency.
        rec = session.execute_read(
            lambda tx: list(tx.run(
                "MATCH (a:Requirement)-[r]->(b) "
                "WHERE NOT EXISTS { MATCH (n:Requirement {id: b.id}) } "
                "RETURN DISTINCT a.id AS source, b.id AS missing_target LIMIT 10"
            ))
        )
        out["orphan_targets"] = [(row["source"], row["missing_target"]) for row in rec]
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print planned Cypher + counts without connecting to Aura",
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="DELETE all :Requirement nodes (and their relationships) before loading",
    )
    parser.add_argument(
        "--data-path", type=Path, default=None,
        help="Override DATA_PATH from env",
    )
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv()

    path = args.data_path or Path(
        os.environ.get("DATA_PATH", "./data/synthetic/requirements.jsonl")
    )
    if not path.exists():
        print(f"ERROR: corpus not found at {path}", file=sys.stderr)
        return 2
    print(f"Reading {path} ...")
    rows = read_rows(path)
    print(f"  {len(rows)} raw rows")

    nodes = [project_node(r) for r in rows]
    edges_by_rel, skipped = extract_edges(rows)
    n_edges = sum(len(v) for v in edges_by_rel.values())
    per_rel = {k: len(v) for k, v in edges_by_rel.items()}
    print(f"  {len(nodes)} nodes; {n_edges} edges across {len(edges_by_rel)} types: {per_rel}")
    if skipped:
        print(f"  WARN: skipped unknown link types: {skipped}", file=sys.stderr)

    if args.dry_run:
        print("\n--- DRY RUN ---\n")
        print("Schema statements:")
        for s in CYPHER_SCHEMA:
            print("  " + s)
        if args.reset:
            print(f"\nReset: {CYPHER_RESET}")
        print(f"\nNode upsert (Cypher, will be executed with rows={len(nodes)}, batch=500):")
        print(CYPHER_NODE)
        print("\nEdge upsert per type (batch=500 each):")
        for rel, edges in edges_by_rel.items():
            print(f"\n  rel={rel}, edges={len(edges)}")
            print(CYPHER_EDGE_TEMPLATE % rel)
        print("\n(Use without --dry-run to execute against Aura.)")
        return 0

    try:
        from neo4j import GraphDatabase
    except ImportError:
        print(
            "ERROR: 'neo4j' package not installed. Run: pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 2

    uri = os.environ.get("NEO4J_URI")
    user = os.environ.get("NEO4J_USER")
    password = os.environ.get("NEO4J_PASSWORD")
    if not (uri and user and password):
        print(
            "ERROR: NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD must be set in .env",
            file=sys.stderr,
        )
        return 2

    print(f"\nConnecting to {uri} as {user} ...")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
        print("  connected")
        counts = run_etl(driver, nodes, edges_by_rel, reset=args.reset)
        print(f"\nETL done. Counts: nodes={counts['nodes']}, edges={counts['edges']}")
        print("\nSanity (Aura round-trip):")
        s = sanity_check(driver)
        print(f"  nodes={s['nodes']}")
        print(f"  edges={s['edges']}")
        if s["orphan_targets"]:
            print(f"  orphan targets (sample): {s['orphan_targets']}", file=sys.stderr)
        else:
            print("  no orphan targets")
    finally:
        driver.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

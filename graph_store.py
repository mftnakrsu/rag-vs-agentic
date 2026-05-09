"""Neo4j Aura helpers for the GraphRAG pipeline.

`graph_loader.py` populates the store; this module is the read side. It
exposes the canonical 1-2 hop traceability walk used by both `graph_rag.py`
(Phase 1b pipeline 3) and the agentic `graph_lookup` tool node (Phase 1c
pipeline 4).

Driver lifecycle: callers own the driver — `get_driver()` returns it,
caller calls `.close()` (or `with closing(...)`).
"""
from __future__ import annotations

import os
from typing import Sequence

from neo4j import Driver, GraphDatabase

# Whitelist of relationship types we traverse for retrieval.
# Includes the traceability-critical types and excludes system-engineering
# allocations (ALLOCATES_TO / IMPLEMENTS / TESTS) which are not retrieval-
# relevant for typical QA. The whitelist is parameter-overridable per call.
TRACEABILITY_LINK_TYPES: tuple[str, ...] = (
    "DERIVES_FROM",
    "SATISFIES",
    "REFERENCES",
    "VERIFIES",
    "REFINES",
)


def get_driver() -> Driver:
    uri = os.environ.get("NEO4J_URI")
    user = os.environ.get("NEO4J_USER")
    password = os.environ.get("NEO4J_PASSWORD")
    if not (uri and user and password):
        raise RuntimeError(
            "NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD must be set in .env"
        )
    return GraphDatabase.driver(uri, auth=(user, password))


# Bidirectional 1-2 hop walk from seeds, restricted to whitelisted edge types,
# excluding the seeds themselves. Returns ids ordered by hop distance asc so
# graph_rag can prefer 1-hop neighbors when capping context.
WALK_CYPHER = """
MATCH (a:Requirement) WHERE a.id IN $seeds
MATCH path = (a)-[*1..2]-(b:Requirement)
WHERE all(rel IN relationships(path) WHERE type(rel) IN $rel_types)
  AND NOT b.id IN $seeds
WITH DISTINCT b, length(path) AS hops
RETURN b.id AS id, hops
ORDER BY hops ASC, b.id ASC
LIMIT $max_results
""".strip()


def walk_2hop(
    driver: Driver,
    seed_ids: Sequence[str],
    *,
    rel_types: Sequence[str] = TRACEABILITY_LINK_TYPES,
    max_results: int = 30,
) -> list[dict]:
    """Walk 1-2 hops out from `seed_ids` along `rel_types` (undirected).

    Returns:
        [{"id": str, "hops": int}, ...] sorted by hops asc, then id asc.
        Seeds are excluded from the result (only their neighborhood).
    """
    if not seed_ids:
        return []
    with driver.session() as session:
        rec = session.execute_read(
            lambda tx: list(tx.run(
                WALK_CYPHER,
                seeds=list(seed_ids),
                rel_types=list(rel_types),
                max_results=max_results,
            ))
        )
    return [{"id": r["id"], "hops": r["hops"]} for r in rec]


# 1-hop directed walk variant for the agentic `graph_lookup` tool — when the
# router classifies a query as id_lookup, the tool needs ID -> direct neighbors
# along a specific link type, not a flood. Phase 1c uses this.
HOP1_DIRECTED_CYPHER = """
MATCH (a:Requirement {id: $req_id})
OPTIONAL MATCH (a)-[r_out]->(b:Requirement)
  WHERE type(r_out) IN $rel_types
WITH a, collect(DISTINCT {id: b.id, dir: 'out', rel: type(r_out)}) AS outs
OPTIONAL MATCH (c)-[r_in]->(a)
  WHERE type(r_in) IN $rel_types
RETURN outs + collect(DISTINCT {id: c.id, dir: 'in', rel: type(r_in)}) AS neighbors
""".strip()


def hop1_directed(
    driver: Driver,
    req_id: str,
    *,
    rel_types: Sequence[str] = TRACEABILITY_LINK_TYPES,
) -> list[dict]:
    """Direct neighbors of `req_id` along `rel_types`, with direction + edge type.

    Returns:
        [{"id": str, "dir": "out"|"in", "rel": "DERIVES_FROM"|...}, ...]
    """
    with driver.session() as session:
        rec = session.execute_read(
            lambda tx: tx.run(
                HOP1_DIRECTED_CYPHER,
                req_id=req_id,
                rel_types=list(rel_types),
            ).single()
        )
    if not rec or not rec["neighbors"]:
        return []
    # Filter out the OPTIONAL MATCH null-rows (collect returns {id: None, ...})
    return [n for n in rec["neighbors"] if n.get("id")]

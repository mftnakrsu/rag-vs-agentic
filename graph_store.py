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
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:  # neo4j is only needed for the Aura backend
    from neo4j import Driver

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


def get_driver():
    """Neo4j driver, or a file-backed stand-in when GRAPH_BACKEND=local.

    The local backend traverses the corpus' own link annotations, which is
    what `graph_loader.py` would put in a fresh instance anyway. See
    graph_store_local for the fidelity notes.
    """
    if os.environ.get("GRAPH_BACKEND", "").lower() == "local":
        from graph_store_local import LocalGraph
        return LocalGraph.from_corpus()
    uri = os.environ.get("NEO4J_URI")
    user = os.environ.get("NEO4J_USER")
    password = os.environ.get("NEO4J_PASSWORD")
    if not (uri and user and password):
        raise RuntimeError(
            "NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD must be set in .env"
        )
    from neo4j import GraphDatabase
    return GraphDatabase.driver(uri, auth=(user, password))


# Bidirectional 1-2 hop walk from seeds, restricted to whitelisted edge types,
# excluding the seeds themselves. Returns ids ordered by hop distance asc so
# graph_rag can prefer 1-hop neighbors when capping context.
# Cypher returns one row per (b, path) pair. We grab b.id + length(path),
# ORDER BY hops asc so when the same neighbor is reachable via paths of
# different lengths, the lowest-hop occurrence is first. Python dedupes by
# id keeping first-seen — simpler and more reliable than wrestling with
# Cypher's aggregation grouping semantics on node values.
WALK_CYPHER = """
MATCH (a:Requirement) WHERE a.id IN $seeds
MATCH path = (a)-[*1..2]-(b:Requirement)
WHERE all(rel IN relationships(path) WHERE type(rel) IN $rel_types)
  AND NOT b.id IN $seeds
RETURN b.id AS id, length(path) AS hops
ORDER BY hops ASC, b.id ASC
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
        [{"id": str, "hops": int}, ...] deduped by id (keeps min-hop occurrence),
        sorted by hops asc, then id asc. Seeds are excluded from the result.
    """
    if not seed_ids:
        return []
    if hasattr(driver, "walk_2hop"):
        return driver.walk_2hop(seed_ids, rel_types, max_results)
    with driver.session() as session:
        rec = session.execute_read(
            lambda tx: list(tx.run(
                WALK_CYPHER,
                seeds=list(seed_ids),
                rel_types=list(rel_types),
            ))
        )
    seen: set[str] = set()
    out: list[dict] = []
    for r in rec:
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        out.append({"id": r["id"], "hops": r["hops"]})
        if len(out) >= max_results:
            break
    return out


# 1-hop directed walk variant for the agentic `graph_lookup` tool — when the
# router classifies a query as id_lookup, the tool needs ID -> direct neighbors
# along a specific link type, not a flood. Phase 1c uses this.
#
# Cypher correctness note: outgoing and incoming neighbors are collected into
# separate WITH-bound lists, then concatenated in RETURN. Mixing two aggregations
# in a single RETURN ("RETURN outs + collect(...)") triggers Neo4j's implicit
# grouping error.
HOP1_DIRECTED_CYPHER = """
MATCH (a:Requirement {id: $req_id})
OPTIONAL MATCH (a)-[r_out]->(b:Requirement)
  WHERE type(r_out) IN $rel_types
WITH a, collect(DISTINCT {id: b.id, dir: 'out', rel: type(r_out)}) AS outs
OPTIONAL MATCH (c:Requirement)-[r_in]->(a)
  WHERE type(r_in) IN $rel_types
WITH outs, collect(DISTINCT {id: c.id, dir: 'in', rel: type(r_in)}) AS ins
RETURN outs + ins AS neighbors
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
    if hasattr(driver, "hop1_directed"):
        return driver.hop1_directed(req_id, rel_types)
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
    # OPTIONAL MATCH that finds nothing yields a single record with id=None;
    # filter those out so callers see only real neighbors.
    return [n for n in rec["neighbors"] if n.get("id")]

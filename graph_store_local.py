"""File-backed replacement for the Neo4j read side of `graph_store`.

The Aura instance this study used is gone, and it held edges the released
corpus never carried, so it cannot be rebuilt. What a fresh instance loaded
by `graph_loader.py` WOULD contain is exactly the link annotations in
`data/synthetic/requirements.jsonl` -- which we can traverse in-process, with
no cloud dependency and no 72h auto-pause. That also makes the graph
derivable from the released corpus, which the Aura-backed version never was.

Semantics match `graph_store` exactly:
  * walk_2hop    undirected, 1-2 hops, whitelisted edge types only, seeds
                 excluded, deduped by id keeping the minimum hop, ordered by
                 (hops asc, id asc), capped at max_results.
  * hop1_directed  direct neighbours with direction and edge type.

Fidelity note: `graph_loader` creates edges with MATCH on both endpoints, so
links whose target is absent from the corpus are silently dropped. We drop
them too -- 48 of the 768 annotated links, leaving 720.

Select it with GRAPH_BACKEND=local; `graph_store.get_driver()` dispatches.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Sequence

TRACEABILITY_LINK_TYPES: tuple[str, ...] = (
    "DERIVES_FROM", "SATISFIES", "REFERENCES", "VERIFIES", "REFINES",
)

DEFAULT_CORPUS = Path(__file__).resolve().parent / "data" / "synthetic" / "requirements.jsonl"


class LocalGraph:
    """Adjacency over the corpus' typed links. Stands in for a neo4j Driver."""

    def __init__(self, out_edges: dict[str, list[tuple[str, str]]]):
        # out_edges: source -> [(target, REL_TYPE), ...]
        self.out: dict[str, list[tuple[str, str]]] = out_edges
        self.inc: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for src, targets in out_edges.items():
            for tgt, rel in targets:
                self.inc[tgt].append((src, rel))

    @classmethod
    def from_corpus(cls, path: Path | str = DEFAULT_CORPUS) -> "LocalGraph":
        rows = [json.loads(l) for l in Path(path).open(encoding="utf-8")]
        ids = {r["id"] for r in rows}
        out: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for r in rows:
            for link in (r.get("outgoing_links") or []):
                tgt = link.get("target_id")
                rel = (link.get("link_type") or "").strip().upper()
                # graph_loader MATCHes both endpoints, so links to absent
                # requirements never become edges. Mirror that.
                if tgt in ids and rel:
                    out[r["id"]].append((tgt, rel))
        return cls(dict(out))

    def _undirected(self, node: str, rel_types: set[str]) -> set[str]:
        nbrs = {t for t, rel in self.out.get(node, []) if rel in rel_types}
        nbrs |= {s for s, rel in self.inc.get(node, []) if rel in rel_types}
        return nbrs

    def walk_2hop(self, seed_ids: Sequence[str], rel_types: Sequence[str],
                  max_results: int) -> list[dict]:
        if not seed_ids:
            return []
        rt = set(rel_types)
        seeds = set(seed_ids)
        hop1: set[str] = set()
        for s in seed_ids:
            hop1 |= self._undirected(s, rt)
        hop1 -= seeds
        hop2: set[str] = set()
        for n in hop1:
            hop2 |= self._undirected(n, rt)
        hop2 -= seeds | hop1
        ordered = ([{"id": i, "hops": 1} for i in sorted(hop1)]
                   + [{"id": i, "hops": 2} for i in sorted(hop2)])
        return ordered[:max_results]

    def walk_ppr(self, seed_ids: Sequence[str], rel_types: Sequence[str],
                 max_results: int, *, alpha: float = 0.15, iters: int = 20) -> list[dict]:
        """Personalized-PageRank retrieval, a second GraphRAG-family traversal.

        walk_2hop takes everything within a fixed radius; PPR instead scores
        the whole reachable component by random-walk-with-restart mass and
        keeps the top nodes, so a well-connected 3-hop node can outrank a
        peripheral 1-hop one. This is the HippoRAG-family strategy and gives
        a traversal that differs in kind, not just in budget -- which is what
        tests whether the flooding/filtering split is an artefact of our
        particular walk.

        alpha is the restart probability; scores are unnormalised mass.
        """
        if not seed_ids:
            return []
        rt = set(rel_types)
        seeds = [s for s in seed_ids if s in self.out or s in self.inc]
        if not seeds:
            return []
        restart = {s: 1.0 / len(seeds) for s in seeds}
        score = dict(restart)
        for _ in range(iters):
            nxt: dict[str, float] = defaultdict(float)
            for node, mass in score.items():
                nbrs = self._undirected(node, rt)
                if not nbrs:
                    nxt[node] += (1 - alpha) * mass  # dangling: keep mass in place
                    continue
                share = (1 - alpha) * mass / len(nbrs)
                for nb in nbrs:
                    nxt[nb] += share
            for s, m in restart.items():
                nxt[s] += alpha * m
            score = dict(nxt)
        seedset = set(seeds)
        ranked = sorted(((n, v) for n, v in score.items() if n not in seedset),
                        key=lambda kv: (-kv[1], kv[0]))
        return [{"id": n, "hops": 1, "score": v} for n, v in ranked[:max_results]]

    def hop1_directed(self, req_id: str, rel_types: Sequence[str]) -> list[dict]:
        rt = set(rel_types)
        outs = [{"id": t, "dir": "out", "rel": rel}
                for t, rel in self.out.get(req_id, []) if rel in rt]
        ins = [{"id": s, "dir": "in", "rel": rel}
               for s, rel in self.inc.get(req_id, []) if rel in rt]
        seen, dedup = set(), []
        for n in outs + ins:
            k = (n["id"], n["dir"], n["rel"])
            if k not in seen:
                seen.add(k)
                dedup.append(n)
        return dedup

    def close(self) -> None:  # driver-compatible no-op
        pass


def _self_check() -> None:
    g = LocalGraph.from_corpus()
    n_edges = sum(len(v) for v in g.out.values())
    assert n_edges == 720, f"expected 720 non-dangling edges, got {n_edges}"

    # a seed's own neighbours are hop 1, and the seed never comes back
    seed = next(k for k, v in g.out.items() if v)
    walk = g.walk_2hop([seed], TRACEABILITY_LINK_TYPES, 30)
    assert seed not in {w["id"] for w in walk}, "seed leaked into walk"
    direct = g._undirected(seed, set(TRACEABILITY_LINK_TYPES))
    assert {w["id"] for w in walk if w["hops"] == 1} == direct, "hop-1 set wrong"

    # ordering contract: hops asc, then id asc within a hop
    assert walk == sorted(walk, key=lambda w: (w["hops"], w["id"])), "ordering broken"
    # min-hop dedupe: no id appears twice
    assert len({w["id"] for w in walk}) == len(walk), "duplicate ids in walk"
    # cap respected
    assert len(g.walk_2hop(list(g.out)[:50], TRACEABILITY_LINK_TYPES, 5)) == 5, "cap ignored"

    # directed lookup agrees with the adjacency it was built from
    nb = g.hop1_directed(seed, TRACEABILITY_LINK_TYPES)
    assert {n["id"] for n in nb} >= {t for t, _ in g.out[seed]}, "missing out-neighbours"
    assert all(n["dir"] in ("out", "in") for n in nb)

    # whitelist actually filters
    assert g.walk_2hop([seed], ["REFINES"], 30) != walk or not direct, "rel_types ignored"
    print(f"self-check OK: {len(g.out)} sources, {n_edges} edges, "
          f"{len(walk)} neighbours from {seed}")


if __name__ == "__main__":
    _self_check()

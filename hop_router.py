"""Hop-adaptive query router (Phase 1d, paper's novelty hook).

Classifies a query by extracted features, then routes among the four base
pipelines:
    vanilla       — embed -> top-K -> 1 LLM call
    agentic       — LangGraph router/retriever-with-tools/critic/synthesizer
    graphrag      — vector seeds + Aura 1-2 hop graph walk + 1 LLM call
    agentic-graph — agentic with graph_lookup tool + graph_id_lookup short-circuit

V1 (this file): rule-based using regex + keyword features. Deterministic,
training-free, transparent, paper-friendly. Each routing decision carries
a `reason` string so failure-mode analysis can attribute errors back to
specific rules.

V2 (deferred, post-deadline): logistic regression over the same features
trained on a labeled subset of queries.

The paper's novelty claim is the JOINT design of:
  1. hop-adaptive routing conditioned on typed-edge graph distance,
  2. link-type-aware retrieval over a DO-178C-style requirement graph
     (already in graph_store.TRACEABILITY_LINK_TYPES),
  3. hop-stratified evaluation (Phase 2a) with multi-judge bias controls
     (Phase 2b).
Adaptive-RAG (Jeong et al., NAACL 2024) is hop-blind and graph-blind;
GraphRAG is non-agentic; LiSSA is single-shot RAG without typed graph
reasoning. We sit at the intersection.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

# All 30 module identifiers in the AeroSys synthetic corpus. Used for the
# n_modules feature. Order doesn't matter — we use it as a set.
KNOWN_MODULES: frozenset[str] = frozenset([
    "ADS", "APM", "AUTO", "BIT", "CDL", "COMM", "DLNK", "EMS", "ENG",
    "EOIR", "EPS", "FCC", "FDR", "FMS", "FUEL", "GCS", "GPS", "HMI",
    "ICE", "INS", "LDG", "LGT", "NAV", "PLD", "PWR", "RADAR", "SAR",
    "SEC", "STR", "TCS",
])

# Explicit requirement IDs like "ADS-014", "FCC-022". Allows 2-5 letter
# module prefix + dash + digits, anchored at word boundaries. This
# intentionally does NOT match "DO-178C" (trailing letter), "ARP4761"
# (no dash), or "MIL-STD" (no digits) — those are standards, not req IDs.
ID_PATTERN: re.Pattern = re.compile(r"\b([A-Z]{2,5}-\d+)\b")

TRACEABILITY_KEYWORDS: frozenset[str] = frozenset([
    "trace", "traceability", "derives from", "derived from", "derive from",
    "satisfies", "satisfied by", "satisfy",
    "verifies", "verified by", "verify",
    "refines", "refined by", "refine",
    "references", "referenced by",
    "implements", "implemented by",
    "depends on", "dependency", "linked to", "link to", "connection",
])

# Hints that the query is asking about a CHAIN of requirements, not a
# single one. Boosts graphrag (always-walk) routing.
CHAIN_INDICATORS: frozenset[str] = frozenset([
    "how does", "how do", "how is", "how are",
    "from", "through", "via", "feed", "feeds", "source of",
    "trace", "chain", "downstream", "upstream",
])

# Hints that the query asks for a specific number / threshold / unit.
# Suggests a single requirement holds the answer; boosts vanilla routing.
NUMERIC_HINT_WORDS: frozenset[str] = frozenset([
    "rate", "rates", "hz", "ms", "kt", "ft", "deg", "°",
    "altitude", "speed", "latency", "accuracy", "tolerance",
    "threshold", "limit", "limits", "budget", "interval",
    "frequency", "period", "duration",
])


@dataclass
class RouterFeatures:
    raw_query: str
    explicit_ids: list[str] = field(default_factory=list)
    n_explicit_ids: int = 0
    modules_in_query: list[str] = field(default_factory=list)
    n_modules: int = 0
    has_traceability_keyword: bool = False
    has_chain_indicator: bool = False
    has_numeric_hint: bool = False
    query_length_tokens: int = 0


@dataclass
class RouterDecision:
    pipeline: str            # vanilla | agentic | graphrag | agentic-graph
    reason: str
    features: RouterFeatures


def extract_features(query: str) -> RouterFeatures:
    """Pure function — same input → same features. Cheap (regex only)."""
    text = query.strip()
    text_lower = text.lower()

    # Explicit IDs (case-sensitive — module abbrevs are upper).
    explicit_ids = list(dict.fromkeys(ID_PATTERN.findall(text)))

    # Modules: word-bounded all-caps tokens that match the corpus's set.
    # Filter out IDs first so "ADS" inside "ADS-014" is captured via the
    # ID feature, not double-counted as a module mention.
    text_no_ids = ID_PATTERN.sub("", text)
    candidate_tokens = re.findall(r"\b[A-Z]{2,5}\b", text_no_ids)
    modules = list(dict.fromkeys(t for t in candidate_tokens if t in KNOWN_MODULES))

    has_trace = any(kw in text_lower for kw in TRACEABILITY_KEYWORDS)
    has_chain = any(kw in text_lower for kw in CHAIN_INDICATORS)
    has_numeric = any(kw in text_lower for kw in NUMERIC_HINT_WORDS)

    return RouterFeatures(
        raw_query=text,
        explicit_ids=explicit_ids,
        n_explicit_ids=len(explicit_ids),
        modules_in_query=modules,
        n_modules=len(modules),
        has_traceability_keyword=has_trace,
        has_chain_indicator=has_chain,
        has_numeric_hint=has_numeric,
        query_length_tokens=len(text.split()),
    )


def route(query: str) -> RouterDecision:
    """Rule-based v1 routing. First-match-wins on an ordered rule list.

    The rule order encodes a precedence: more specific signals first.
    Each rule produces a human-readable reason for failure-mode analysis.
    """
    f = extract_features(query)

    # R1: explicit ID + traceability words → agentic-graph
    # The agent can use graph_id_lookup short-circuit (req + 1-hop neighbors)
    # AND graph_lookup tool for further traversal if needed.
    if f.n_explicit_ids >= 1 and f.has_traceability_keyword:
        return RouterDecision(
            pipeline="agentic-graph",
            reason=f"R1: explicit_id ({f.n_explicit_ids}) + traceability_kw → graph_id_lookup",
            features=f,
        )

    # R2: explicit ID, no traceability words → vanilla
    # Direct ID lookup — the ChromaDB top-K already includes the requirement
    # by id-similar vector. No need to walk the graph.
    if f.n_explicit_ids >= 1 and not f.has_traceability_keyword:
        return RouterDecision(
            pipeline="vanilla",
            reason=f"R2: explicit_id ({f.n_explicit_ids}) + no_traceability_kw → cheap top-K",
            features=f,
        )

    # R3: cross-module + chain indicator → graphrag
    # No explicit IDs but multiple module mentions and a "how does X feed Y"
    # phrasing. Always-walk reliably finds inter-module links.
    if f.n_modules >= 2 and f.has_chain_indicator:
        return RouterDecision(
            pipeline="graphrag",
            reason=f"R3: n_modules ({f.n_modules}) ≥ 2 + chain_indicator → always-walk graph",
            features=f,
        )

    # R4: traceability words without IDs → graphrag
    # Chain-style query phrasing without explicit anchors. Structural
    # retrieval surfaces the relevant chain.
    if f.has_traceability_keyword and f.n_explicit_ids == 0:
        return RouterDecision(
            pipeline="graphrag",
            reason="R4: traceability_kw + no_explicit_id → structural retrieval",
            features=f,
        )

    # R5: numeric hint within a single module → vanilla
    # E.g., "what's the latency budget for ADS data?" — ADS is one module
    # and the numeric is in one requirement. Top-K is sufficient.
    if f.has_numeric_hint and f.n_modules == 1:
        return RouterDecision(
            pipeline="vanilla",
            reason=f"R5: numeric_hint + single_module ({f.modules_in_query[0]}) → top-K",
            features=f,
        )

    # Default: agentic (ReAct exploration)
    return RouterDecision(
        pipeline="agentic",
        reason=f"default: agentic ReAct exploration (no specific signal; "
               f"ids={f.n_explicit_ids}, mods={f.n_modules}, "
               f"trace_kw={f.has_traceability_keyword}, "
               f"chain_ind={f.has_chain_indicator}, "
               f"numeric={f.has_numeric_hint})",
        features=f,
    )


def adaptive_rag(
    query: str,
    *,
    embedder_name: str = "local",
) -> dict:
    """Pipeline 5 — adaptive: route, then call the chosen base pipeline.

    Returns a dict in the same schema as the base pipelines, with two
    extra fields:
        routed_to     — name of the inner pipeline actually called
        route_reason  — human-readable reason from the router
    """
    t0 = time.time()
    decision = route(query)
    routed = decision.pipeline

    if routed == "vanilla":
        from vanilla_rag import vanilla_rag
        result = vanilla_rag(query, embedder_name=embedder_name, reranker_name=None)
    elif routed == "graphrag":
        from graph_rag import graph_rag
        result = graph_rag(query, embedder_name=embedder_name)
    elif routed == "agentic-graph":
        from agentic_rag import run_agentic_rag
        result = run_agentic_rag(query, embedder_name=embedder_name, use_graph=True)
    else:  # agentic (or unknown — defensive)
        from agentic_rag import run_agentic_rag
        result = run_agentic_rag(query, embedder_name=embedder_name, use_graph=False)

    # The router's own latency is small (regex only), but capture it so
    # the paper can report adaptive overhead = routing time + inner pipeline.
    router_overhead_ms = int((time.time() - t0) * 1000) - result["latency_ms"]
    if router_overhead_ms < 0:
        router_overhead_ms = 0

    # Tag with router metadata for failure-mode analysis and paper plots
    result["pipeline"] = f"adaptive|{embedder_name}"
    result["routed_to"] = routed
    result["route_reason"] = decision.reason
    result["route_features"] = {
        "n_explicit_ids": decision.features.n_explicit_ids,
        "n_modules": decision.features.n_modules,
        "has_traceability_kw": decision.features.has_traceability_keyword,
        "has_chain_indicator": decision.features.has_chain_indicator,
        "has_numeric_hint": decision.features.has_numeric_hint,
        "query_length_tokens": decision.features.query_length_tokens,
    }
    result["router_overhead_ms"] = router_overhead_ms
    return result


# =============================================================================
# CLI smoke test
# =============================================================================

if __name__ == "__main__":
    from eval_queries import EVAL_QUERIES

    print("\nDry routing decisions for the 10 hand-curated eval queries:\n")
    print(f"  {'Query':<58s} {'Routed to':<14s} Reason")
    print(f"  {'-' * 58:<58s} {'-' * 14:<14s} {'-' * 60}")
    for q in EVAL_QUERIES:
        d = route(q["query"])
        truncated = q["query"][:55] + ("…" if len(q["query"]) > 55 else "")
        print(f"  {truncated:<58s} {d.pipeline:<14s} {d.reason}")

    by_target: dict[str, int] = {}
    for q in EVAL_QUERIES:
        p = route(q["query"]).pipeline
        by_target[p] = by_target.get(p, 0) + 1
    print(f"\nRouting distribution: {by_target}")

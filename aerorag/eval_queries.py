"""Hand-curated evaluation queries spanning the corpus.

Each entry has:
    query             — the user-facing question
    type              — id_lookup | cross_module | semantic_specific |
                        semantic_general | comparative | metadata_filter
    expected_modules  — modules we expect to surface (for grounding-overlap check)
    notes             — what this query stress-tests
"""
from __future__ import annotations

EVAL_QUERIES: list[dict] = [
    {
        "query": "What does ADS-014 specify about pitot blockage detection?",
        "type": "id_lookup",
        "expected_modules": ["ADS"],
        "notes": "Direct ID retrieval; vanilla should hit ADS-014 in top-1. "
                 "Agentic router should classify as id_lookup and skip semantic search.",
    },
    {
        "query": "How does the air data system provide angle-of-attack to the flight control computer?",
        "type": "cross_module",
        "expected_modules": ["ADS", "FCC"],
        "notes": "Cross-module reference (ADS-012 ↔ FCC-022 via Satisfies). "
                 "Tests whether agentic ReAct loop follows the link or just relies on top-K.",
    },
    {
        "query": "What sampling rates are required for pitot, static, AOA, and sideslip sensors?",
        "type": "semantic_specific",
        "expected_modules": ["ADS"],
        "notes": "Single requirement (ADS-005) hits all four. Tests precise number recall.",
    },
    {
        "query": "What is the end-to-end latency budget for the ADS data pipeline?",
        "type": "semantic_specific",
        "expected_modules": ["ADS"],
        "notes": "ADS-005 says 20ms — checks numeric fidelity in the answer.",
    },
    {
        "query": "What is the dual-redundancy strategy for air data on each platform?",
        "type": "comparative",
        "expected_modules": ["ADS", "PWR"],
        "notes": "ADS-003 + ADS-017 + PWR-012 — tests synthesis across requirements.",
    },
    {
        "query": "How is the heater for the pitot and static ports monitored?",
        "type": "cross_module",
        "expected_modules": ["ADS", "ICE"],
        "notes": "ADS-019 satisfies ICE-008. Cross-module Satisfies link.",
    },
    {
        "query": "What governing standards (DO-, ARP, MIL-STD) does the ADS reference?",
        "type": "metadata_filter",
        "expected_modules": ["ADS"],
        "notes": "ADS-004 + scattered References annotations. Tests retrieval over named entities.",
    },
    {
        "query": "On which platforms is the ADS only single-channel rather than dual-redundant?",
        "type": "comparative",
        "expected_modules": ["ADS"],
        "notes": "ADS-003 — single answer (Skyrunner-T1). Tests precise platform attribution.",
    },
    {
        "query": "What pressure-altitude accuracy is required at sea level vs at 44,000 ft?",
        "type": "semantic_specific",
        "expected_modules": ["ADS"],
        "notes": "ADS-007 — tests retrieval of multiple numeric values bound to altitudes.",
    },
    {
        "query": "If a requirement says it 'derives from' ARP4761, what does that imply about its safety classification?",
        "type": "semantic_general",
        "expected_modules": ["ADS"],
        "notes": "Open-ended reasoning over the corpus + general aerospace knowledge. "
                 "Vanilla single-shot vs agentic critic divergence likely.",
    },
]

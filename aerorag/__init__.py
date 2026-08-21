"""Shared library for the RAG-vs-agentic comparison study.

Retrieval pipelines (``vanilla_rag``, ``agentic_rag``, ``graph_rag``), the
infrastructure they share (``embedders``, ``vector_store``, ``graph_store``,
``llm_compat``, ``reranker``), the evaluation harness (``compare``,
``eval_metrics``, ``multi_judge``) and the corpus/graph ETL
(``build_index``, ``graph_loader``, ``eval_generator``).

Run entry points from the repository root, e.g.::

    python -m aerorag.build_index
    python -m aerorag.compare --limit 3
    python -m aerorag.vanilla_rag "What does ADS-014 specify?"
"""

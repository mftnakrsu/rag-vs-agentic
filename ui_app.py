"""Streamlit UI for vanilla vs agentic RAG comparison.

Run:
    .venv/bin/streamlit run ui_app.py

Features:
    - Side-by-side toggle (vanilla | agentic | both)
    - Live tool-call timeline for the agentic pipeline (router → tools →
      collect_chunks → critic → synthesizer), each node rendered as a
      collapsible st.status widget as it executes.
    - Example queries from eval_queries.py available in sidebar.
    - Source panel with all retrieved chunks (id, module, heading, snippet).
    - Citation highlighting in the answer ([ADS-014] → blue).
    - Per-query stats: latency, tokens, intent, iter, verdict.

The agentic pipeline is streamed via `graph.stream(stream_mode="updates")`,
which yields {node_name: state_delta} after each node executes — exactly
what we want for showing the StateGraph traversal live.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import AIMessage, ToolMessage

from agentic_rag import build_graph
from embedders import get_embedder
from eval_queries import EVAL_QUERIES
from llm_compat import GPT5Client
from reranker import get_reranker
from vanilla_rag import GROUNDED_SYSTEM_PROMPT, _coll_for, _format_context
from vector_store import get_client, get_or_create_collection, query_top_k


# =============================================================================
# Cached resources — LangGraph compile, embedders, ChromaDB collections.
# Without this, every query reloads the local e5-small model from disk (~5s)
# and recompiles the agentic graph (~1s) — terrible UX.
# =============================================================================

@st.cache_resource(show_spinner=False)
def cached_embedder(name: str):
    emb = get_embedder(name)
    if name == "local":
        emb._load()
    return emb


@st.cache_resource(show_spinner=False)
def cached_collection(embedder_name: str):
    coll_name, dim = _coll_for(embedder_name)
    client = get_client()
    return get_or_create_collection(client, coll_name, dim=dim), coll_name, dim


@st.cache_resource(show_spinner="Compiling LangGraph (one-time)…")
def cached_graph(embedder_name: str):
    return build_graph(embedder_name)


@st.cache_resource(show_spinner=False)
def cached_reranker():
    return get_reranker("azure")


# =============================================================================
# Page setup
# =============================================================================

st.set_page_config(
    page_title="RAG vs Agentic — AeroSys",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .stApp { background-color: #0a0e1a; }
    section[data-testid="stSidebar"] { background-color: #0f1421; }
    .citation { color: #4a9eff; font-weight: 600; }
    .verdict-sufficient { color: #4ee382; font-weight: 600; }
    .verdict-continue   { color: #ffc94a; font-weight: 600; }
    .pipeline-vanilla   { color: #4a9eff; }
    .pipeline-agentic   { color: #4ee382; }
    .stat-pill {
        display: inline-block;
        background: #1f2940;
        border-radius: 12px;
        padding: 2px 10px;
        margin-right: 6px;
        font-size: 0.85em;
        color: #c8d4e8;
    }
    /* Tighter status widgets */
    div[data-testid="stStatus"] { border: 1px solid #1f2940; }
</style>
""",
    unsafe_allow_html=True,
)


# =============================================================================
# Helpers
# =============================================================================

_ID_RE = re.compile(r"\[([A-Z]{2,5}-(?:[A-Z]?\d+))\]")


def highlight_citations(text: str) -> str:
    return _ID_RE.sub(r"<span class='citation'>[\1]</span>", text)


def render_chunk_card(c: dict, *, score_label: str | None = None) -> None:
    head = c.get("heading", "")[:70]
    mod = c.get("module", "")
    snippet = (c.get("full_text", "") or "")[:280]
    score_str = ""
    if score_label and score_label in c:
        score_str = f" · {score_label}={c[score_label]:.3f}"
    elif "_distance" in c:
        score_str = f" · d={c['_distance']:.3f}"
    st.markdown(
        f"<div style='padding:6px 10px; border-left:3px solid #4a9eff; "
        f"margin-bottom:6px; background:#0f1421;'>"
        f"<b>[{c['id']}]</b> <span style='color:#a0b0c8;'>{mod} :: {head}</span>{score_str}<br>"
        f"<span style='color:#c8d4e8; font-size:0.92em;'>{snippet}…</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def stat_pills(items: list[tuple[str, str]]) -> None:
    pills = "".join(f"<span class='stat-pill'>{k}: {v}</span>" for k, v in items)
    st.markdown(pills, unsafe_allow_html=True)


# =============================================================================
# Vanilla pipeline (with live status updates)
# =============================================================================

def run_vanilla(query: str, embedder_name: str, use_rerank: bool, top_k: int) -> dict:
    t0 = time.time()

    with st.status("Embedding query…", expanded=False) as s:
        emb = cached_embedder(embedder_name)
        qvec = emb.embed_query(query)
        s.update(label=f"✓ Embedded ({len(qvec)}d, {embedder_name})", state="complete")

    with st.status(f"Retrieving top-{top_k} from ChromaDB…", expanded=True) as s:
        col, coll_name, dim = cached_collection(embedder_name)
        hits = query_top_k(col, qvec, k=top_k)
        st.caption(f"Collection: `{coll_name}` (dim={dim})")
        for h in hits:
            render_chunk_card(h)
        s.update(label=f"✓ Retrieved {len(hits)} chunks", state="complete")

    final_hits = hits[:5]
    if use_rerank:
        with st.status("Reranking with Azure Cohere v4.0-fast…", expanded=True) as s:
            try:
                rr = cached_reranker()
                final_hits = rr.rerank(query, hits, top_n=5)
                top_score = final_hits[0].get("_rerank_score", 0.0) if final_hits else 0.0
                for h in final_hits:
                    render_chunk_card(h, score_label="_rerank_score")
                s.update(label=f"✓ Reranked, top score {top_score:.3f}", state="complete")
            except Exception as e:
                s.update(label=f"⚠ Rerank failed: {type(e).__name__}", state="error")
                final_hits = hits[:5]

    with st.status("Synthesizing answer (gpt-5.4)…", expanded=False) as s:
        llm = GPT5Client()
        context = _format_context(final_hits)
        resp = llm.chat(messages=[
            {"role": "system", "content": GROUNDED_SYSTEM_PROMPT},
            {"role": "user", "content": f"Context (retrieved requirements):\n\n{context}\n\nQ: {query}"},
        ])
        answer = resp.choices[0].message.content or ""
        usage = GPT5Client.usage(resp)
        s.update(label=f"✓ Synthesized ({usage.get('total_tokens', 0)} tokens)", state="complete")

    elapsed_ms = int((time.time() - t0) * 1000)

    st.markdown("##### Answer")
    st.markdown(highlight_citations(answer), unsafe_allow_html=True)
    stat_pills([
        ("⏱", f"{elapsed_ms} ms"),
        ("🪙", f"{usage.get('total_tokens', 0)} tok"),
        ("📊", f"prompt {usage.get('prompt_tokens', 0)} + completion {usage.get('completion_tokens', 0)}"),
        ("📚", f"{len(final_hits)} chunks"),
    ])

    cited = list(dict.fromkeys(_ID_RE.findall(answer)))
    if cited:
        st.markdown(
            f"**Cited:** "
            + " ".join(f"<span class='citation'>[{c}]</span>" for c in cited),
            unsafe_allow_html=True,
        )

    with st.expander(f"📚 All {len(final_hits)} sources used", expanded=False):
        for h in final_hits:
            render_chunk_card(h)

    return {
        "pipeline": "vanilla",
        "answer": answer,
        "sources": final_hits,
        "cited_ids": cited,
        "latency_ms": elapsed_ms,
        "tokens": usage,
    }


# =============================================================================
# Agentic pipeline (live LangGraph stream)
# =============================================================================

def run_agentic(query: str, embedder_name: str) -> dict:
    t0 = time.time()

    graph = cached_graph(embedder_name)

    config = {
        "configurable": {"thread_id": f"streamlit-{int(t0 * 1000)}"},
        "recursion_limit": 25,
    }

    # Cumulative state we accumulate from the streamed deltas
    chunks_seen: dict[str, dict] = {}  # id -> chunk
    intent: str = ""
    final_answer: str = ""
    cited_ids: list[str] = []
    iter_count: int = 0
    final_verdict: str = ""
    tokens_total: dict[str, int] = {}
    n_tool_calls = 0

    def _add_tokens(d: dict) -> None:
        for k, v in (d or {}).items():
            if isinstance(v, (int, float)):
                tokens_total[k] = tokens_total.get(k, 0) + v

    answer_placeholder = st.empty()

    for chunk in graph.stream(
        {"query": query, "iter_count": 0, "tokens": {}},
        config=config,
        stream_mode="updates",
    ):
        for node_name, delta in chunk.items():
            delta = delta or {}

            if node_name == "router":
                intent = delta.get("intent", "?")
                ids = delta.get("extracted_ids") or []
                emoji = "🎯" if intent == "id_lookup" else "🧭"
                with st.status(f"{emoji} **router** → intent = `{intent}`", expanded=bool(ids)) as s:
                    if ids:
                        st.write(f"Extracted IDs: {', '.join(ids)}")
                        st.caption("ID-pattern regex hit; will skip semantic search and fetch directly.")
                    else:
                        st.caption("No IDs in query → semantic retrieval path.")
                    s.update(state="complete")

            elif node_name == "id_lookup":
                got = delta.get("chunks") or []
                for c in got:
                    chunks_seen[c["id"]] = c
                with st.status(f"🎯 **id_lookup** → {len(got)} chunks fetched", expanded=True) as s:
                    for c in got:
                        render_chunk_card(c)
                    s.update(state="complete")

            elif node_name == "retriever":
                msgs = delta.get("messages") or []
                _add_tokens(delta.get("tokens"))
                latest = msgs[-1] if msgs else None
                if isinstance(latest, AIMessage):
                    if latest.tool_calls:
                        n_tool_calls += 1
                        for tc in latest.tool_calls:
                            args = tc.get("args", {})
                            with st.status(
                                f"🔧 **retriever** → tool call #{n_tool_calls}: `{tc['name']}`",
                                expanded=True,
                            ) as s:
                                st.code(
                                    f"search_documents(\n"
                                    f"    query={args.get('query', '')!r},\n"
                                    f"    top_k={args.get('top_k', 5)},\n"
                                    f"    module_filter={args.get('module_filter', '')!r},\n"
                                    f")",
                                    language="python",
                                )
                                rc = latest.additional_kwargs.get("reasoning_content")
                                if rc:
                                    st.caption("Model reasoning:")
                                    st.markdown(f"<small style='color:#a0b0c8;'>{rc[:600]}</small>", unsafe_allow_html=True)
                                s.update(state="complete")
                    else:
                        with st.status("📝 **retriever** → no more tool calls; passing to critic", expanded=False) as s:
                            content = (latest.content or "").strip()
                            if content:
                                st.caption(content[:300])
                            s.update(state="complete")

            elif node_name == "tools":
                msgs = delta.get("messages") or []
                for m in msgs:
                    if isinstance(m, ToolMessage):
                        artifact = getattr(m, "artifact", None) or []
                        for c in artifact:
                            chunks_seen[c["id"]] = c
                        with st.status(f"📄 **tools** → ToolMessage with {len(artifact)} chunks", expanded=True) as s:
                            for c in artifact[:8]:
                                render_chunk_card(c)
                            if len(artifact) > 8:
                                st.caption(f"… + {len(artifact) - 8} more")
                            s.update(state="complete")

            elif node_name == "collect_chunks":
                got = delta.get("chunks") or []
                for c in got:
                    chunks_seen[c["id"]] = c

            elif node_name == "critic":
                _add_tokens(delta.get("tokens"))
                v = delta.get("verdict", "?")
                final_verdict = v
                iter_count = delta.get("iter_count", iter_count)
                if v == "sufficient":
                    label = f"✅ **critic** → `sufficient` (iter={iter_count})"
                else:
                    label = f"🔁 **critic** → `continue` (iter={iter_count} → loop back to retriever)"
                with st.status(label, expanded=False) as s:
                    st.caption(
                        f"Verdict reached over {len(chunks_seen)} accumulated chunks. "
                        f"Critic prompt is one LLM call; output is strict JSON."
                    )
                    s.update(state="complete")

            elif node_name == "synthesizer":
                _add_tokens(delta.get("tokens"))
                final_answer = delta.get("answer", "") or ""
                cited_ids = delta.get("cited_ids") or []
                with st.status("🧠 **synthesizer** → answer composed", expanded=False) as s:
                    s.update(state="complete")
                answer_placeholder.markdown(highlight_citations(final_answer), unsafe_allow_html=True)

    elapsed_ms = int((time.time() - t0) * 1000)

    if not final_answer:
        answer_placeholder.warning("Synthesizer did not produce an answer (graph terminated early).")
    else:
        # Re-render in case placeholder was replaced
        st.markdown("##### Answer")
        st.markdown(highlight_citations(final_answer), unsafe_allow_html=True)

    stat_pills([
        ("⏱", f"{elapsed_ms} ms"),
        ("🪙", f"{tokens_total.get('total_tokens', 0)} tok"),
        ("🧭", f"intent {intent or '—'}"),
        ("🔁", f"iter {iter_count}"),
        ("⚖️", f"verdict {final_verdict or '—'}"),
        ("🔧", f"{n_tool_calls} tool calls"),
        ("📚", f"{len(chunks_seen)} chunks"),
    ])

    if cited_ids:
        st.markdown(
            f"**Cited:** "
            + " ".join(f"<span class='citation'>[{c}]</span>" for c in cited_ids),
            unsafe_allow_html=True,
        )

    with st.expander(f"📚 All {len(chunks_seen)} chunks retrieved across the trajectory", expanded=False):
        for c in chunks_seen.values():
            render_chunk_card(c)

    return {
        "pipeline": "agentic",
        "answer": final_answer,
        "sources": list(chunks_seen.values()),
        "cited_ids": cited_ids,
        "intent": intent,
        "iter_count": iter_count,
        "verdict": final_verdict,
        "n_tool_calls": n_tool_calls,
        "latency_ms": elapsed_ms,
        "tokens": tokens_total,
    }


# =============================================================================
# Sidebar
# =============================================================================

with st.sidebar:
    st.markdown("### 📡 RAG vs Agentic")
    st.caption("AeroSys aerospace requirements (1102 chunks, 32 modules)")
    st.divider()

    st.markdown("**Pipeline**")
    pipeline_mode = st.radio(
        "Pipeline mode",
        ["Side-by-side", "Vanilla only", "Agentic only"],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("**Embedder**")
    embedder_name = st.radio(
        "Embedder",
        ["azure", "local"],
        index=0,
        label_visibility="collapsed",
        captions=["text-embedding-3-small (1536d)", "intfloat/multilingual-e5-small (384d)"],
    )

    if pipeline_mode != "Agentic only":
        use_rerank = st.checkbox(
            "Vanilla → Azure Cohere reranker",
            value=False,
            help="Cohere rerank-v4.0-fast on Foundry. 15s pacing per call (1000 TPM cap).",
        )
    else:
        use_rerank = False

    top_k = st.slider("Vanilla top-K", min_value=3, max_value=15, value=5)

    st.divider()
    st.markdown("**Example queries**")
    for i, q in enumerate(EVAL_QUERIES):
        label = q["query"]
        short = (label[:42] + "…") if len(label) > 42 else label
        type_emoji = {
            "id_lookup": "🎯",
            "cross_module": "🔗",
            "semantic_specific": "🔍",
            "semantic_general": "💭",
            "comparative": "⚖️",
            "metadata_filter": "🏷",
        }.get(q["type"], "•")
        if st.button(f"{type_emoji} {short}", key=f"ex_{i}", use_container_width=True):
            st.session_state.pending_query = label

    st.divider()
    if st.button("🗑️ Clear chat history", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# =============================================================================
# Main area
# =============================================================================

st.title("📡 RAG vs Agentic — AeroSys Requirements")
st.caption(
    "Vanilla single-shot RAG vs LangGraph StateGraph "
    "(`router → retriever-with-tools → critic → synthesizer`). "
    "Watch the agentic graph traverse live; toggle side-by-side to compare."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

# Determine query: from example button or chat input
query: str | None = None
if "pending_query" in st.session_state:
    query = st.session_state.pop("pending_query")

if user_input := st.chat_input("Ask about the AeroSys requirements…"):
    query = user_input

if query:
    with st.chat_message("user"):
        st.markdown(query)
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("assistant"):
        if pipeline_mode == "Side-by-side":
            col_v, col_a = st.columns(2, gap="medium")
            with col_v:
                st.markdown("##### <span class='pipeline-vanilla'>🔵 Vanilla</span>", unsafe_allow_html=True)
                v_result = run_vanilla(query, embedder_name, use_rerank, top_k)
            with col_a:
                st.markdown("##### <span class='pipeline-agentic'>🟢 Agentic</span>", unsafe_allow_html=True)
                a_result = run_agentic(query, embedder_name)

            # Side-by-side comparison summary
            st.divider()
            st.markdown("##### Δ Comparison")
            v_tok = v_result["tokens"].get("total_tokens", 0)
            a_tok = a_result["tokens"].get("total_tokens", 0)
            v_ids = set(v_result["cited_ids"])
            a_ids = set(a_result["cited_ids"])
            overlap = v_ids & a_ids
            stat_pills([
                ("Δlatency", f"{a_result['latency_ms'] - v_result['latency_ms']:+d} ms"),
                ("Δtokens", f"{a_tok - v_tok:+d}"),
                ("vanilla cited", f"{len(v_ids)}"),
                ("agentic cited", f"{len(a_ids)}"),
                ("overlap", f"{len(overlap)}"),
                ("vanilla-only", f"{len(v_ids - a_ids)}"),
                ("agentic-only", f"{len(a_ids - v_ids)}"),
            ])

            saved = (
                f"<b>🔵 Vanilla:</b> {highlight_citations(v_result['answer'])}<br><br>"
                f"<b>🟢 Agentic ({a_result['intent']}, iter={a_result['iter_count']}):</b> "
                f"{highlight_citations(a_result['answer'])}"
            )
        elif pipeline_mode == "Vanilla only":
            st.markdown("##### <span class='pipeline-vanilla'>🔵 Vanilla</span>", unsafe_allow_html=True)
            v_result = run_vanilla(query, embedder_name, use_rerank, top_k)
            saved = f"<b>🔵 Vanilla:</b> {highlight_citations(v_result['answer'])}"
        else:  # Agentic only
            st.markdown("##### <span class='pipeline-agentic'>🟢 Agentic</span>", unsafe_allow_html=True)
            a_result = run_agentic(query, embedder_name)
            saved = (
                f"<b>🟢 Agentic ({a_result['intent']}, iter={a_result['iter_count']}):</b> "
                f"{highlight_citations(a_result['answer'])}"
            )

        st.session_state.messages.append({"role": "assistant", "content": saved})

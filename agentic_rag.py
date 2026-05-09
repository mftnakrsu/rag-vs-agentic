"""Agentic RAG via LangGraph (1.1.x).

Graph topology:

    START
      |
    router  --(id_lookup, IDs in query)-->  id_lookup -----------------+
      |                                                                 |
      | (semantic)                                                      |
      v                                                                 |
    retriever  --(tool_calls)-->  tools  -->  collect_chunks  --+       |
      |                                                          |      |
      | (no tool_calls)                                          v      |
      v                                                       retriever |
    critic  --(continue, iter<3)-->  retriever                          |
      |                                                                 |
      | (sufficient | iter>=3)                                          |
      v                                                                 |
    synthesizer  <------------------------------------------------------+
      |
      v
     END

Notes:
  * LangChain's ChatOpenAI drops `reasoning_content` (#34328 won't-fix), so we
    drive the LLM via raw `openai` SDK through GPT5Client and hand-build
    AIMessages that preserve reasoning_content in additional_kwargs.
  * The search tool uses `response_format="content_and_artifact"` so the full
    chunk dicts pass through ToolMessage.artifact without polluting model
    context. A `collect_chunks` node walks the recent ToolMessages and merges
    artifacts into a deduped `chunks` state field via a custom reducer.
  * SqliteSaver checkpointer, WAL+NORMAL after setup() (NORMAL is not set by
    setup()).
  * recursion_limit=25 in invoke config to bound runaway ReAct loops
    independently of the critic's iter cap.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Annotated, TypedDict

from dotenv import load_dotenv

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_tool
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from embedders import get_embedder
from llm_compat import GPT5Client
from vector_store import (
    fetch_by_id,
    get_client,
    get_or_create_collection,
    query_top_k,
)


# =============================================================================
# State + reducers
# =============================================================================

def _chunk_reducer(left: list[dict] | None, right: list[dict] | None) -> list[dict]:
    """Append-and-dedupe by id."""
    left = left or []
    right = right or []
    if not right:
        return left
    seen = {c["id"] for c in left}
    return left + [c for c in right if c["id"] not in seen]


def _token_reducer(left: dict | None, right: dict | None) -> dict:
    """Sum token usage dicts across LLM calls."""
    left = left or {}
    right = right or {}
    out = dict(left)
    for k, v in right.items():
        if isinstance(v, (int, float)):
            out[k] = out.get(k, 0) + v
    return out


class AgentState(TypedDict, total=False):
    query: str
    intent: str                  # router output: id_lookup | semantic
    extracted_ids: list[str]     # from router
    messages: Annotated[list[BaseMessage], add_messages]
    chunks: Annotated[list[dict], _chunk_reducer]
    iter_count: int              # critic increments on continue
    verdict: str                 # critic output
    answer: str
    cited_ids: list[str]
    tokens: Annotated[dict, _token_reducer]


# =============================================================================
# Search tool — bound per embedder via closure
# =============================================================================

def _coll_for(embedder_name: str) -> tuple[str, int]:
    if embedder_name == "local":
        return (os.environ.get("CHROMA_COLLECTION_LOCAL", "docs-local-e5"), 384)
    return (
        os.environ.get("CHROMA_COLLECTION_AZURE", "docs-azure"),
        int(os.environ.get("AZURE_OPENAI_EMBEDDING_DIMENSION", 1536)),
    )


def _make_search_tool(embedder_name: str):
    embedder = get_embedder(embedder_name)
    coll_name, dim = _coll_for(embedder_name)
    client = get_client()
    col = get_or_create_collection(client, coll_name, dim=dim)

    @tool(response_format="content_and_artifact")
    def search_documents(
        query: str,
        top_k: int = 5,
        module_filter: str = "",
    ) -> tuple[str, list[dict]]:
        """Search the AeroSys aerospace requirements corpus.

        Args:
            query: A natural-language question or technical phrase.
            top_k: Number of results (default 5, max 10).
            module_filter: Restrict to one module (e.g. 'ADS', 'FCC', 'NAV'). Empty = no filter.

        Returns a brief summary with hit IDs/headings; the full chunk dicts are
        attached as the ToolMessage's artifact and consumed downstream.
        """
        qvec = embedder.embed_query(query)
        where = {"module": module_filter} if module_filter else None
        hits = query_top_k(col, qvec, k=min(top_k, 10), where=where)
        if not hits:
            return ("No matching requirements found.", [])
        lines = [f"Found {len(hits)} requirements:"]
        for h in hits:
            lines.append(f"- [{h['id']}] ({h.get('module', '')} :: {h.get('heading', '')[:60]})")
        return ("\n".join(lines), hits)

    return search_documents


def _make_id_lookup(embedder_name: str):
    coll_name, dim = _coll_for(embedder_name)
    client = get_client()
    col = get_or_create_collection(client, coll_name, dim=dim)

    def id_lookup_node(state: AgentState) -> dict:
        ids = state.get("extracted_ids", []) or []
        chunks = fetch_by_id(col, ids)
        # No LLM call here. Push directly into chunks state; skip retriever/critic.
        return {
            "chunks": chunks,
            "verdict": "sufficient",
        }

    return id_lookup_node


# =============================================================================
# LangChain ↔ OpenAI message conversion (we drive via raw openai SDK)
# =============================================================================

def _lc_to_openai_messages(msgs: list[BaseMessage]) -> list[dict]:
    out: list[dict] = []
    for m in msgs:
        if isinstance(m, SystemMessage):
            out.append({"role": "system", "content": m.content})
        elif isinstance(m, HumanMessage):
            out.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            entry: dict = {"role": "assistant", "content": m.content or ""}
            if m.tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc.get("args", {})),
                        },
                    }
                    for tc in m.tool_calls
                ]
                # OpenAI requires content to be present (can be empty string) when tool_calls set.
                entry["content"] = entry.get("content") or ""
            out.append(entry)
        elif isinstance(m, ToolMessage):
            out.append({
                "role": "tool",
                "tool_call_id": m.tool_call_id,
                "content": m.content if isinstance(m.content, str) else json.dumps(m.content),
            })
    return out


# =============================================================================
# Prompts
# =============================================================================

RETRIEVER_SYSTEM_PROMPT = """You are a retrieval agent for an aerospace requirements corpus (DOORS export, ~1100 requirements across modules ADS, FCC, NAV, GPS, EPS, ICE, …).

You have one tool: `search_documents`. Use it to find relevant requirements before letting a downstream agent answer.

Strategy:
 - For cross-module questions (e.g., "How does ADS feed FCC?"), search each module separately.
 - For semantic questions, search with the most specific technical phrase from the question.
 - You may call the tool up to 3 times.

Once you believe the retrieved set is sufficient, reply with a brief confirmation (no tool call). Do NOT compose the final answer here — a synthesizer node will do that with the full chunk text."""


CRITIC_SYSTEM_PROMPT = """You are a retrieval critic. Given a user query and the requirement IDs/headings retrieved so far, judge whether they are sufficient to answer the query.

Respond with strict JSON only: {"verdict": "sufficient" | "continue", "reason": "<short>"}.

Be efficient: prefer "sufficient" when the right requirements are clearly present, even if more could be found. Be conservative: prefer "continue" when a key referenced module or topic is clearly missing."""


SYNTHESIZER_SYSTEM_PROMPT = """You are an aerospace requirements engineer answering questions about a DOORS-exported requirements set.
Rules:
 1. Ground every claim in retrieved requirements; cite the IDs you used inline as [ADS-014].
 2. If the retrieved context does not contain the answer, say so plainly. Do not invent.
 3. Prefer concise, technical wording. Reproduce numeric thresholds (Hz, kt, ft, ms, °) verbatim.
 4. When requirements interact (e.g., FCC <-> ADS), explain the relationship."""


# =============================================================================
# Nodes
# =============================================================================

_ID_PATTERN = re.compile(r"\b([A-Z]{2,5}-(?:[A-Z]?\d+))\b")


def router_node(state: AgentState) -> dict:
    q = state["query"]
    ids = list(dict.fromkeys(m.group(1) for m in _ID_PATTERN.finditer(q)))
    if ids:
        return {"intent": "id_lookup", "extracted_ids": ids}
    return {"intent": "semantic"}


def _make_retriever_node(search_tool):
    tool_schema = convert_to_openai_tool(search_tool)

    def retriever_node(state: AgentState) -> dict:
        llm = GPT5Client()
        msgs: list[BaseMessage] = state.get("messages") or []
        if not msgs:
            msgs = [
                SystemMessage(content=RETRIEVER_SYSTEM_PROMPT),
                HumanMessage(content=state["query"]),
            ]
        oa_msgs = _lc_to_openai_messages(msgs)

        resp = llm.chat(messages=oa_msgs, tools=[tool_schema], tool_choice="auto")
        ai_msg = GPT5Client.to_aimessage(resp)
        usage = GPT5Client.usage(resp)

        # If this is the first call, persist the system + user we built locally.
        new_messages: list[BaseMessage] = []
        if not state.get("messages"):
            new_messages.extend(msgs)
        new_messages.append(ai_msg)

        return {"messages": new_messages, "tokens": usage}

    return retriever_node


def collect_chunks_node(state: AgentState) -> dict:
    """Pull artifacts off the most recent ToolMessage batch. Reducer dedupes."""
    new_chunks: list[dict] = []
    for m in reversed(state.get("messages") or []):
        if isinstance(m, ToolMessage):
            artifact = getattr(m, "artifact", None)
            if artifact:
                new_chunks = list(artifact) + new_chunks
        elif isinstance(m, AIMessage):
            # Older AIMessage above the tool batch — stop walking back.
            if not m.tool_calls:
                continue
            break
    return {"chunks": new_chunks}


def critic_node(state: AgentState) -> dict:
    chunks = state.get("chunks") or []
    if not chunks:
        return {"verdict": "continue", "iter_count": state.get("iter_count", 0) + 1}

    summary = "\n".join(
        f"- [{c['id']}] ({c.get('module', '')} :: {c.get('heading', '')[:60]})"
        for c in chunks
    )
    user = f"Query: {state['query']}\n\nRetrieved so far:\n{summary}"

    llm = GPT5Client()
    resp = llm.chat(messages=[
        {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ])
    raw = (resp.choices[0].message.content or "").strip()
    usage = GPT5Client.usage(resp)

    # Robust JSON extraction (LLM may wrap in code fences)
    verdict = "sufficient"
    try:
        m = re.search(r"\{.*?\}", raw, re.S)
        if m:
            data = json.loads(m.group(0))
            if data.get("verdict") in ("sufficient", "continue"):
                verdict = data["verdict"]
    except json.JSONDecodeError:
        pass

    iter_inc = 1 if verdict == "continue" else 0
    return {
        "verdict": verdict,
        "iter_count": state.get("iter_count", 0) + iter_inc,
        "tokens": usage,
    }


def synthesizer_node(state: AgentState) -> dict:
    chunks = state.get("chunks") or []
    parts = [
        f"[{c['id']}] ({c.get('module', '')} :: {c.get('heading', '')})\n{c['full_text']}"
        for c in chunks
    ]
    context = "\n\n---\n\n".join(parts) if parts else "(no requirements retrieved)"

    llm = GPT5Client()
    resp = llm.chat(messages=[
        {"role": "system", "content": SYNTHESIZER_SYSTEM_PROMPT},
        {"role": "user", "content": f"Context (retrieved requirements):\n\n{context}\n\nQ: {state['query']}"},
    ])
    answer = resp.choices[0].message.content or ""
    usage = GPT5Client.usage(resp)

    cited_ids = list(dict.fromkeys(_ID_PATTERN.findall(answer)))
    return {"answer": answer, "cited_ids": cited_ids, "tokens": usage}


# =============================================================================
# Routing
# =============================================================================

def route_after_router(state: AgentState) -> str:
    return "id_lookup" if state.get("intent") == "id_lookup" else "retriever"


def route_after_retriever(state: AgentState) -> str:
    msgs = state.get("messages") or []
    if msgs and isinstance(msgs[-1], AIMessage) and msgs[-1].tool_calls:
        return "tools"
    return "critic"


def route_after_critic(state: AgentState) -> str:
    if state.get("verdict") == "sufficient" or state.get("iter_count", 0) >= 3:
        return "synthesizer"
    return "retriever"


# =============================================================================
# Graph builder
# =============================================================================

_DB_PATH = "data/agent.db"


def _make_checkpointer() -> SqliteSaver:
    Path("data").mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    saver = SqliteSaver(conn)
    saver.setup()  # creates tables, sets WAL
    # setup() does not touch synchronous; WAL+NORMAL is the recommended combo.
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.commit()
    return saver


def build_graph(embedder_name: str = "local"):
    search_tool = _make_search_tool(embedder_name)

    builder = StateGraph(AgentState)
    builder.add_node("router", router_node)
    builder.add_node("id_lookup", _make_id_lookup(embedder_name))
    builder.add_node("retriever", _make_retriever_node(search_tool))
    builder.add_node("tools", ToolNode([search_tool]))
    builder.add_node("collect_chunks", collect_chunks_node)
    builder.add_node("critic", critic_node)
    builder.add_node("synthesizer", synthesizer_node)

    builder.add_edge(START, "router")
    builder.add_conditional_edges("router", route_after_router, {
        "id_lookup": "id_lookup",
        "retriever": "retriever",
    })
    builder.add_edge("id_lookup", "synthesizer")
    builder.add_conditional_edges("retriever", route_after_retriever, {
        "tools": "tools",
        "critic": "critic",
    })
    builder.add_edge("tools", "collect_chunks")
    builder.add_edge("collect_chunks", "retriever")
    builder.add_conditional_edges("critic", route_after_critic, {
        "retriever": "retriever",
        "synthesizer": "synthesizer",
    })
    builder.add_edge("synthesizer", END)

    return builder.compile(checkpointer=_make_checkpointer())


# =============================================================================
# Public API
# =============================================================================

def run_agentic_rag(
    query: str,
    *,
    embedder_name: str = "local",
    thread_id: str | None = None,
) -> dict:
    t0 = time.time()
    graph = build_graph(embedder_name)
    config = {
        "configurable": {"thread_id": thread_id or f"agentic-{int(t0 * 1000)}"},
        "recursion_limit": 25,
    }
    final = graph.invoke({"query": query, "iter_count": 0, "tokens": {}}, config=config)
    return {
        "pipeline": f"agentic|{embedder_name}",
        "query": query,
        "answer": final.get("answer", ""),
        "sources": final.get("chunks", []),
        "cited_ids": final.get("cited_ids", []),
        "intent": final.get("intent", ""),
        "iter_count": final.get("iter_count", 0),
        "verdict": final.get("verdict", ""),
        "latency_ms": int((time.time() - t0) * 1000),
        "tokens": final.get("tokens", {}),
    }


if __name__ == "__main__":
    load_dotenv()
    q = sys.argv[1] if len(sys.argv) > 1 \
        else "How does the air data system provide angle-of-attack to the flight control computer?"
    print(f"\n[query] {q}\n")
    result = run_agentic_rag(q, embedder_name="local")

    total = result["tokens"].get("total_tokens", 0)
    print(f"--- Answer ({result['latency_ms']}ms, {total} tokens, intent={result['intent']}, "
          f"iter={result['iter_count']}, verdict={result['verdict']}) ---")
    print(result["answer"])
    print("\n--- Retrieved chunks ---")
    for c in result["sources"]:
        print(f"  {c['id']:10s}  {c.get('heading', '')[:70]}")
    print(f"\n--- Cited in answer: {', '.join(result['cited_ids']) or '(none)'} ---")

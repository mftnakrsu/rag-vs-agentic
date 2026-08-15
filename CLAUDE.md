# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠ On resume

**Read `HANDOFF.md` BEFORE anything else.** It is the authoritative snapshot of session state — current phase, blocked work, background processes, and the "Quick resume" command block. The git log alone is not enough.

## Project shape

This is a **research codebase**, not a product. Goal is a measurable side-by-side comparison of four RAG pipelines over the AeroSys synthetic aerospace requirements corpus (1132 DO-178C-style requirements across 30 modules: ADS, FCC, NAV, GPS, EPS, ICE, …). Output is paper artifacts (CSV/JSONL + plots), not production hardening. Submission deadline: 30 Jun / 1 Jul 2026.

**Phases:** Phase 0 bootstrap → 1a Aura ETL → 1b graphrag → 1c agentic-graph (current head) → 2 hop-stratified eval (300 q × RAGAS × bootstrap CIs) → 3 cross-eval (RAG-Critic, MuSiQue, reasoning-effort) → 4 plots → 5–6 paper. Add new code under the phase it belongs to and update HANDOFF.md's status table.

## Common commands

```bash
# Indexing — populates data/chroma/ with two collections (one per embedder)
.venv/bin/python build_index.py            # both embedders, idempotent
.venv/bin/python build_index.py --force    # drop & rebuild

# Single-pipeline smoke test (fast feedback before running the matrix)
.venv/bin/python vanilla_rag.py "What does ADS-014 specify about pitot blockage?"
.venv/bin/python agentic_rag.py "How does ADS feed AOA to FCC?"
.venv/bin/python agentic_rag.py "..." --graph        # pipeline 4 (agentic-graph)
.venv/bin/python graph_rag.py "..."                  # pipeline 3 (graphrag)

# Full ablation matrix → results/results.csv + .jsonl
.venv/bin/python compare.py                          # default: all 4 pipelines × 2 embedders
.venv/bin/python compare.py --limit 3 --embedders local --no-azure-rerank
.venv/bin/python compare.py --no-graphrag            # skip Aura-dependent pipeline
.venv/bin/python compare.py --no-local-rerank        # ALWAYS — bge weights are missing on disk

# Neo4j Aura ETL (Phase 1+; idempotent MERGE)
.venv/bin/python graph_loader.py --dry-run           # print Cypher, no connection
.venv/bin/python graph_loader.py                     # real ETL

# Streamlit demo (not yet 4-pipeline-aware; still vanilla+agentic only)
.venv/bin/streamlit run ui_app.py
```

There is **no test suite, linter, or formatter** wired up. Verification is "the comparison matrix runs and the per-config aggregates match expectations" — see HANDOFF.md and README.md for the canonical numbers. `compare.py --limit 1` is the cheapest smoke; full matrix on 10 queries is ~20 min.

## Architecture (cross-cutting)

The four pipelines **share infrastructure and diverge only in retrieval strategy**:

| Layer | Module | Pipelines |
|---|---|---|
| Embed | `embedders.py` (`local` 384d e5-small / `azure` 1536d text-embedding-3-small) | all |
| Vector store | `vector_store.py` (Chroma, one collection per embedder dim) | all |
| Graph store | `graph_store.py` (Neo4j Aura, `walk_2hop` undirected + `hop1_directed` for ID lookups) | 3, 4 |
| LLM | `llm_compat.py` (`GPT5Client` — raw `openai` SDK, NOT `ChatOpenAI`) | all |
| Synthesis prompt | `vanilla_rag.GROUNDED_SYSTEM_PROMPT` (re-imported by `graph_rag`) | 1, 3 |

Pipeline files:

```
vanilla_rag.py        Pipeline 1: embed → top-K → (rerank) → 1 LLM call
agentic_rag.py        Pipeline 2 (use_graph=False) AND Pipeline 4 (use_graph=True)
                      LangGraph: router → id_lookup | retriever⇄tools⇄critic → synthesizer
graph_rag.py          Pipeline 3: vector seeds + Aura 1-2 hop walk → 1 LLM call
compare.py            4-arm dispatch + ablation matrix harness
```

**Pipeline 4 is not its own file** — it is `run_agentic_rag(..., use_graph=True)`. That toggle swaps `_make_id_lookup` for `_make_graph_id_lookup` (req + 1-hop neighbors as initial chunks) and adds `graph_lookup` as a second tool alongside `search_documents` in the ReAct loop. When extending: change both branches in `build_graph()` if the change is shared, only one if pipeline-specific.

### Key structural invariants — easy to break

- **`GPT5Client` is mandatory; do not introduce `langchain_openai.ChatOpenAI`.** It silently drops `reasoning_content` (LangChain #34328, won't-fix). The agentic graph relies on reasoning_content surviving through `to_aimessage()`.
- **`GPT5Client.variant`** parses the deployment name to decide which Azure constraints apply: `gpt-5` / `gpt-5.1` are reasoning models that **reject** `temperature`; `gpt-5-chat` / `gpt-5.4` accept **only 1.0**; `gpt-5.5` accepts arbitrary; `gpt-5.1-chat` strips it entirely. Adding a new variant means updating both `variant` and `_temperature_for_request`.
- **Azure Foundry endpoint version handling**: URLs containing `/openai/v1` use OpenAI-style path versioning and must NOT pass `?api-version=…`; legacy `…/openai/deployments/…` URLs require it as a query param. Same logic in both `llm_compat.py` and `embedders.py`.
- **LangGraph reducers** (`agentic_rag.AgentState`): `chunks` deduplicates by `id` (last-write-wins), `tokens` sums numeric fields. Anything that returns these fields from a node must rely on the reducer rather than reading the prior state and returning a merged value.
- **LangGraph `recursion_limit=25`** in the `invoke` config bounds runaway ReAct loops INDEPENDENTLY of the critic's `iter_count >= 3` cap. Both must stay; they fail differently.
- **SqliteSaver checkpointer** at `data/agent.db` — `setup()` creates tables and sets WAL but NOT `synchronous=NORMAL`; we set it manually after. Deleting `data/agent.db*` is safe (gitignored).

### Cypher gotchas (learned the hard way — see PR #5 + commits 93f1b12, db09cd8)

- `WITH b, min(length(path)) AS hops` does **not** reliably aggregate when `b` is a node value. Same `b.id` can come back at multiple hops. Fix: dedupe in Python (`walk_2hop` keeps first-seen which is min-hop because we `ORDER BY hops ASC` first).
- `RETURN outs + collect(...)` mixes two aggregations and triggers Neo4j's implicit-grouping error. Fix: split into two `WITH` clauses, concatenate at the end (see `HOP1_DIRECTED_CYPHER`).
- `OPTIONAL MATCH` with no match yields a single record with `id=None` — filter `if n.get("id")` in Python.

### Azure Cohere reranker pacing

`AzureCohereReranker` has a **class-level** `_shared_last_call` (not instance), because `compare.py` builds a fresh instance per ablation row but the 1000 TPM budget is per-process. Default 15s minimum interval + 200-char doc truncation. **The local BGE reranker weights are not on disk** — run with `--no-local-rerank` always.

## Data + state

```
data/synthetic/        committed — 1132 jsonl + 30 module narrative MDs (corpus)
data/chroma/           gitignored — rebuilt by build_index.py
data/agent.db*         gitignored — LangGraph SqliteSaver checkpointer
results/results.csv    tracked — paper artifact (per-config aggregates)
results/results.jsonl  tracked — full rows incl. answer text
results/main-*.jsonl   gitignored — large raw matrix traces
.env                   gitignored — Azure creds + Aura creds (see .env.example)
```

The Aura instance is **preloaded** by the Neo4j hackathon ETL with a richer schema than `graph_loader.py` produces (`:System`, `:Module`, `:Standard`, `:Component`, `:Interface`, `:Parameter`, plus extra rel types like `ALLOCATED_TO`, `IMPLEMENTS`, `MENTIONS_SYSTEM`). `TRACEABILITY_LINK_TYPES` in `graph_store.py` whitelists only the five retrieval-relevant edge types — do not widen this casually; the extra types are typically not retrieval-useful and will dilute walks.

## Workflow

**Branch + PR + self-merge** for every change, even one-line fixes. Never commit directly to `main`. Pattern:

```
git checkout -b feat/<topic>      # or fix/, chore/, refactor/
# ... edits ...
git push -u origin feat/<topic>
gh pr create
gh pr merge --rebase --delete-branch
```

Merged PRs are listed in HANDOFF.md's "GitHub PRs" section — append yours when you merge. Tag `v0.1-baseline-comparison` marks the original 60-row two-pipeline study (HEAD before Phase 1).

When the user signals end of session (e.g. "kapatıyorum", "let's wrap"), update `HANDOFF.md` before the final commit so the next resume is clean.

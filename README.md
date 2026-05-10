# RAG vs Agentic RAG — Comparison Study

[![Dataset on Hugging Face](https://huggingface.co/datasets/huggingface/badges/resolve/main/dataset-on-hf-md.svg)](https://huggingface.co/datasets/meftun/aerosys-requirements)
[![Kaggle](https://img.shields.io/badge/Kaggle-Open%20in%20Kaggle-20BEFF?logo=Kaggle&logoColor=white)](https://www.kaggle.com/datasets/mftnakrsu/aerosys-requirements)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey)](https://creativecommons.org/licenses/by/4.0/)

Experimental side-by-side of vanilla RAG and agentic RAG (LangGraph) against the
AeroSys synthetic aerospace requirements corpus (1132 requirements, DO-178C-style
subsystem specs across 30 modules — ADS, FCC, NAV, GPS, …).

Goal: measurable deltas in **latency, tokens, cited-source overlap, and answer
groundedness** between the two paradigms — not production hardening.

## Paper

A short-paper draft for an anonymous CIKM 2026 submission lives in
[`paper/cikm/`](paper/cikm/) (4-page ACM `sigconf`, double-blind review).
It extends the v0 baseline below by adding two graph-aware pipelines
(GraphRAG and agentic+graph over Neo4j Aura), a 300-query hop-stratified
evaluation protocol, and a two-judge bias control.

**Build:** `cd paper/cikm && make` (requires TeX Live + `acmart`), or
upload `paper/cikm/` to Overleaf and Recompile. The architecture figure
renders inline via TikZ — no separate sub-compile needed. See
[`paper/cikm/README.md`](paper/cikm/README.md) for the anonymisation
checklist, page-budget guardrails, and submission notes.

> Title, full author info, and final figures will be added here after
> the review period.

## Pipelines

| | Vanilla | Agentic (LangGraph) |
|---|---|---|
| Steps | embed → ChromaDB top-K → (rerank) → LLM | router → retriever-with-tools (ReAct) → critic → synthesizer |
| LLM calls | 1 | 2–4 (retriever, critic, synthesizer) |
| Decisions | none | router intent classify, critic verdict, max-iter ReAct |

## Stack

- **Python** 3.10+
- **ChromaDB** 1.5.x (local `PersistentClient`)
- **LangGraph** 1.1.x (1.2 still alpha — pinned to 1.1)
- **LLM**: Azure GPT-5.4 (`gpt-5.4-meftun`), via raw `openai` SDK (bypasses
  `ChatOpenAI` because it drops `reasoning_content` — issue #34328)
- **Embedders** (parallel ablation):
  1. Local `intfloat/multilingual-e5-small` (384d, mean-pool + L2 norm)
  2. Azure OpenAI embedding (deployment-defined dim)
- **Rerankers** (both compared): local `bge-reranker-v2-m3` + Azure-hosted
- **No Neo4j** — graph layer skipped for this experiment.

## Dataset

The `data/synthetic/` corpus is also published as a standalone dataset for
downstream RAG / retrieval research:

| Platform | Slug |
|---|---|
| 🤗 Hugging Face | [`meftun/aerosys-requirements`](https://huggingface.co/datasets/meftun/aerosys-requirements) |
| Kaggle | [`mftnakrsu/aerosys-requirements`](https://www.kaggle.com/datasets/mftnakrsu/aerosys-requirements) |

Both releases ship the same 30 module DOORS-narrative `.md` files (~1,132
requirement objects) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
The format is left raw on purpose — see either dataset card for the
`||`-delimited block syntax, inline `##MODULE.ID` cross-refs, traceability
annotations (`Derives From:`, `References:`, `Satisfies:`, …), and glossary
tables that consumers parse with their own loader.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill in Azure creds

python build_index.py            # populates docs-local-e5 + docs-azure
python vanilla_rag.py "What does ADS-014 specify about pitot blockage?"
python compare.py                # 4-row ablation table over eval_queries.py
```

## Files

```
data_loader.py    — requirements.jsonl → list[dict] chunks
llm_compat.py     — variant-aware Azure GPT-5 wrapper (raw openai SDK)
embedders.py      — LocalE5SmallEmbedder + AzureOpenAIEmbedder (uniform iface)
reranker.py       — LocalBGEReranker + AzureReranker (uniform iface)
vector_store.py   — ChromaDB add + query helpers
build_index.py    — dual-collection indexer
vanilla_rag.py    — single-file pipeline
agentic_rag.py    — LangGraph StateGraph (router/retriever/critic/synthesizer)
eval_queries.py   — 5–10 hand-curated test queries
compare.py        — runs the matrix, prints + writes CSV
results/          — generated CSV/JSON
```

## Results

Matrix run on 2026-05-09: 60 rows = 6 configs × 10 eval queries. One vanilla×azure×azure-rerank
row failed on a Cohere 429 whose single retry also 429'd; other 59/60 succeeded.
Wall time: 1100s.

### Aggregate per config

| Pipeline | Embedder | Reranker | ok/N | Avg ms | Avg tok | Avg cited IDs |
|---|---|---|---:|---:|---:|---:|
| vanilla | azure | — | 10/10 | **3,822** | 706 | 5.0 |
| vanilla | local | — | 10/10 | 7,658 | 836 | 5.0 |
| agentic | azure | — | 10/10 | 14,277 | 4,573 | 3.0 |
| agentic | local | — | 10/10 | 20,181 | 5,343 | 2.8 |
| vanilla | local | azure-cohere | 10/10 | 31,269 | 738 | 5.0 |
| vanilla | azure | azure-cohere | 9/10 | 32,257 | 703 | 5.0 |

### Headline deltas

- **Vanilla vs Agentic, same embedder (no rerank):** agentic is 3.7–4.5× slower,
  uses 6.4–6.5× more LLM tokens, but cites *fewer* IDs (2.8–3.0 vs 5.0). The
  fewer-citations result is a **selectivity effect**, not a quality drop —
  agentic synthesises a more focused answer that cites only the IDs it actually
  used, whereas vanilla mechanically dumps all 5 retrieved IDs into its citation
  list.

- **Embedder ablation (vanilla, no rerank):** Azure `text-embedding-3-small`
  (1536d) is **2× faster end-to-end** than local `multilingual-e5-small` (384d):
  3.8s vs 7.7s. Most of the gap is per-process model-load overhead on local
  (mean 0.5–5s for `_load()` per Python invocation); on a long-running server
  the gap would shrink. Quality of retrieved IDs is comparable on this corpus.

- **Reranker ablation:** the Azure-hosted Cohere reranker on this 1000 TPM
  deployment adds **~25s of pacing wall** per call (15s minimum interval, plus
  the LLM call itself). Rerank *does* re-order the top-K — citation lists shift
  (e.g. on the AOA cross-module query, rerank surfaces ADS-C5 glossary higher;
  on the standards query, it pulls in additional ___-003 standard requirements)
  — but the answer's *content* is rarely changed because the model still has 5
  reasonable candidates either way. **Conclusion: not worth the latency on this
  corpus given 1000 TPM.**

### Per-query notable behaviours

- **Q1 (id_lookup ADS-014):** all pipelines correctly center on ADS-014 + the
  paired test req ADS-026 + the HMI annunciation req HMI-090. Agentic router
  classifies as `id_lookup`, skips semantic search, and answers in **2.2s** —
  faster than vanilla (3.5–7.7s).

- **Q2 (cross-module ADS↔FCC AOA):** vanilla|local cites the FCC glossary and
  generic interface chunks (FCC-001, FCC-038, ADS-C5); **agentic surfaces the
  *actual* interface contract** (ADS-012 publishes AOA, FCC-022 consumes it
  with 0.9·α_stall + 3° margin; ADS-021 specifies 1553B vs ARINC 429 transport
  per platform; ADS-022 message field; ADS-023 valid_flags). This is the
  paradigmatic agentic-RAG win on this corpus.

- **Q4 (latency budget):** vanilla finds CDL-011 + ADS-008 + ADS-005 (the
  20ms requirement); **agentic also finds NAV-030** (downstream consumer) by
  searching iteratively — extra context vanilla misses.

- **Q7 (governing standards):** vanilla returns a generic list of *___-003*
  cross-module standards refs (EPS-003, EMS-003, GCS-004, …); **agentic
  zooms in on ADS-004 + DO-254** specifically. More focused, semantically
  correct.

- **Q3, Q8, Q9 (single specific-fact queries):** vanilla cites 4–5 IDs incl.
  the right one; agentic cites only the single right ID (ADS-005, ADS-003,
  ADS-007). Same correctness, fewer citations.

### Research-question takeaway

The agentic critic+ReAct loop **substitutes for a reranker on cross-module
queries** (where its multi-search strategy assembles a richer evidence set)
but offers **no measurable benefit on direct id_lookup or single-fact
queries** while paying 4–5× latency and 6–7× tokens. Use vanilla+azure for
production-grade ID lookup; use agentic for cross-module synthesis where the
extra latency/tokens buy interpretability and focused citation.

Reranker on this 1000 TPM Cohere deployment is **not worth its pacing
penalty** for the small 10-query eval; might pay off on a corpus where the
top-K from the embedder is genuinely lossy (this aerospace corpus is not).

### Files
- `results/results.csv` — 60 rows × 15 columns (no answer text)
- `results/results.jsonl` — full rows incl. answer text


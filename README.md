# A Multi-Axis Robustness Analysis of RAG for Multi-Hop Requirements Traceability

[![Dataset on Hugging Face](https://huggingface.co/datasets/huggingface/badges/resolve/main/dataset-on-hf-md.svg)](https://huggingface.co/datasets/meftun/aerosys-requirements)
[![Kaggle](https://img.shields.io/badge/Kaggle-Open%20in%20Kaggle-20BEFF?logo=Kaggle&logoColor=white)](https://www.kaggle.com/datasets/mftnakrsu/aerosys-requirements)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey)](https://creativecommons.org/licenses/by/4.0/)

Code and artifacts for a controlled comparison of five RAG pipelines across
four robustness axes: the retrieval **embedder**, the **corpus**, the graph
**traversal**, and the faithfulness **judge**.

13,456 generation runs at up to three seeds; 30,000+ faithfulness judgments.
The paper sources are in [`paper/cikm/`](paper/cikm/); the current build is
[`paper/main.pdf`](paper/main.pdf).

## What the study found

**The measurement point decides the winner.** The graph walk fills the context
window at precision 0.12–0.23 while the synthesizer it feeds cites at 0.48–0.98
— a 2.9–4.2× enrichment. Score the *retrieved set* as the attribution set and
GraphRAG ranks below the vanilla baseline; score the *answer's citations* and it
ranks first of all pipelines. This holds in all six settings, survives replacing
the 2-hop walk with personalized PageRank, and defeats two mitigations
(reranking the walked neighbours: +0.010 F1, p=0.34; cutting the traversal
budget: −0.126 F1, p=2.6e-11).

**Answer-level winners are stratum-conditional but embedder- and seed-robust.**
Vanilla ties GraphRAG at 1–2 hops and is last at 3+ hops under all three
embedders; a graph-aided pipeline leads there. The same crossover appears on
MuSiQue and 2WikiMultihopQA.

**Faithfulness declines with hop distance, and the decline tracks context
expansion rather than the corpus.** The one pipeline that expands nothing stays
flat (−1.5 pp on DO-178C, +1.1 pp on 2Wiki); expanding pipelines drop 6.3 and
6.7 pp. A hop×expansion interaction is significant at p=1.0e-07.
An earlier version of this work reported the decline as *corpus-conditional*;
that claim was withdrawn after judging the full matrix at comparable power.

**LLM judges are unstable, and κ hides it.** Re-judging byte-identical
answer–context pairs eleven weeks later gives self-agreement κ ≤ 0.14. Two
vendors judging identical rows reverse which of them is stricter between
corpora, and across eight settings their κ swings 0.03→0.44 while raw agreement
moves only 0.82→0.94.

## The corpus

**AeroSys** — a synthetic DOORS-style aerospace requirements corpus: 1,132
requirements across 30 modules (ADS, FCC, NAV, GPS, EPS, ICE, …), with typed
traceability annotations (`derives_from`, `satisfies`, `references`, `verifies`,
`refines`). Released under CC-BY-4.0 on
[Hugging Face](https://huggingface.co/datasets/meftun/aerosys-requirements) and
[Kaggle](https://www.kaggle.com/datasets/mftnakrsu/aerosys-requirements).

Queries are sampled from the graph, not free-form: 296 hop-stratified questions
(100/99/97 across 1/2/3+-hop) whose gold evidence is the sampled chain's node
set. The manifest ships with full chains in `data/eval/`.

The two Wikipedia corpora (MuSiQue, 2WikiMultihopQA) are rebuilt from public
mirrors by the seeded scripts in `scripts/musique/` and `scripts/twowiki/`.

## The five pipelines

They share the embedder, the ChromaDB vector store, a file-backed typed-edge
graph, the generator and the synthesis prompt; **they differ only in retrieval**.

| # | Pipeline | Retrieval |
|---|---|---|
| 1 | `vanilla` | dense top-10 → top-5 context → one synthesis call |
| 2 | `agentic` | LangGraph router–retriever–critic loop, `search_documents` only, iter ≤ 3 |
| 3 | `graphrag` | 8 vector seeds + ≤2-hop typed walk (cap 30, context 15) → one call |
| 4 | `agentic-graph` | (2) plus a typed `graph_lookup` tool |
| 5 | `adaptive` | picks one of (1)–(4) per query; rule-based (V1) or learned (V2) |

Pipeline 4 is not a separate file — it is `run_agentic_rag(..., use_graph=True)`.

## Layout

```
aerorag/          library: pipelines, retrieval infra, judging, harness
scripts/          one-off experiment runners, grouped by arm
  judge/            multi-vendor faithfulness judging
  stats/            bootstrap CIs, significance tests, figures
  musique/ twowiki/ Wikipedia corpus builds + runs
  router/           V2 learned router
  graphrag2/        personalized-PageRank traversal
  tex/              table generation
data/             corpus, query manifest, Wikipedia subsets (chroma/ is rebuilt)
results/          scored and judged CSVs — the paper's artifacts
paper/cikm/       LaTeX sources
```

## Running it

Requires `.env` (see `.env.example`) with Azure OpenAI credentials. Graph
retrieval needs no database — `GRAPH_BACKEND=local` reads the corpus' own link
annotations.

```bash
# index the corpus (idempotent; --force to rebuild)
.venv-judge/bin/python -m aerorag.build_index

# single-pipeline smoke test
.venv-judge/bin/python -m aerorag.vanilla_rag "What does ADS-014 specify about pitot blockage?"
.venv-judge/bin/python -m aerorag.graph_rag   "How does ADS feed AOA to FCC?"
.venv-judge/bin/python -m aerorag.agentic_rag "How does ADS feed AOA to FCC?" --graph

# the ablation matrix
.venv-judge/bin/python -m aerorag.compare --limit 3 --embedders local --no-local-rerank

# statistics and paper tables
make stats router paper-tables
```

`--no-local-rerank` is required: the BGE reranker weights are not in the repo.

There is no test suite. Verification is that the comparison matrix runs and the
per-config aggregates match the numbers in `results/` — see `HANDOFF.md`.

## Citing

```bibtex
@misc{akarsu2026aerosys,
  title  = {AeroSys Requirements Corpus},
  author = {Akarsu, Meftun},
  year   = {2026},
  url    = {https://huggingface.co/datasets/meftun/aerosys-requirements}
}
```

The companion paper is under submission; this entry will be updated when it
appears.

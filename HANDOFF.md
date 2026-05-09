# RAG vs Agentic — Devam Noktası

> **Geri döndüğünde:** Bu dosyayı oku, sonra aşağıdaki **Quick resume** komutunu çalıştır.
> Tarih: 2026-05-09 (Phase 1c sonrası, Phase 1 sanity bg)

---

## ⚡ Quick resume

```bash
cd /Users/suleakarsu/Desktop/rag-vs-agentic

# main'e bağlan, son state'i al
git checkout main && git pull --rebase

# 4 pipeline import sanity (no Aura/no Azure call)
.venv/bin/python -c "
from dotenv import load_dotenv; load_dotenv()
from agentic_rag import build_graph
from graph_rag import graph_rag
print('all 4 pipelines importable')
"

# Streamlit isteğe bağlı (henüz 4-pipeline'a uyarlanmadı, hâlâ vanilla+agentic)
# .venv/bin/streamlit run ui_app.py
```

Sonra **bana** dönüp tek cümleyle ne istediğini söyle. Ör:
- *"sanity sonucu nasıl"* — `cat results/sanity-v2.csv` + per-config aggregate
- *"phase 2 başla"* — hop-stratified eval generator (#9)
- *"streamlit'i 4-pipeline'a uyarla"* — UI extension
- *"x bug fix"* — fix branch açıp düzelt

---

## 🎯 Şu an neredeyiz

| | Durum |
|---|---|
| **Phase 0** Repo bootstrap (private GitHub `mftnakrsu/rag-vs-agentic`) | ✅ |
| **Phase 1a** Neo4j Aura ETL (idempotent MERGE) | ✅ (live instance preloaded with richer hackathon schema) |
| **Phase 1b** GraphRAG pipeline 3 (vector + 1-2 hop walk) | ✅ |
| **Phase 1c** agentic-graph pipeline 4 (graph_id_lookup + graph_lookup tool) | ✅ |
| **Phase 1 sanity** (4 pipelines × 10 queries, local emb, no rerank) | ⏳ bg running |
| **Phase 2a** Hop-stratified queries (300) | ⏳ blocked on sanity |
| **Phase 2b** RAGAS faithfulness | ⏳ blocked on sanity |
| **Phase 2c** Bootstrap CI + paired permutation | ⏳ blocked on sanity |
| **Phase 2d** Main matrix run (4 × 300) | ⏳ blocked on 2a-c |
| **Phase 3a** RAG-Critic baseline | ⏳ blocked on 2d |
| **Phase 3b** MuSiQue cross-eval | ⏳ blocked on 2d |
| **Phase 3c** reasoning_effort ablation | ⏳ blocked on 2d |
| **Phase 4** Plots + failure-mode taxonomy | ⏳ blocked on 3a-c |
| **Phase 5-6** Paper drafting + submit | ⏳ blocked on 4 (deadline 30 Jun / 1 Jul) |

### Smoke test deltas (1-query, before full sanity)

| Query | Pipeline | Latency | Tokens | Iter | Notes |
|---|---|---:|---:|---:|---|
| Q1 ADS-014 ID | vanilla\|local | ~7-10s | ~890 | n/a | top-K only |
| Q1 ADS-014 ID | agentic-graph\|local | **4.9s** | **579** | **0** | id_lookup + 1-hop graph (ADS-026, HMI-090) |
| Q2 ADS↔FCC cross-mod | vanilla\|local | ~7-10s | ~890 | n/a | misses cross-link |
| Q2 ADS↔FCC cross-mod | graphrag\|local | 26.9s | 1918 | n/a | finds ADS-012 via 1-hop walk |
| Q2 ADS↔FCC cross-mod | agentic-graph\|local | 33.3s | 6265 | 3 | LLM didn't proactively call graph_lookup |

Critical paper-friendly observation already on Q1+Q2:
- agentic-graph WINS on explicit-ID queries (structural id_lookup, 0 iter)
- graphrag WINS on cross-module semantic queries (always-walk finds the link)
- agentic-graph LOSES on cross-module semantic queries (LLM doesn't pull the trigger on graph_lookup)

This is exactly the "when does each pipeline pay off?" question the paper will characterize at scale (300 queries × stratified hop count + bootstrap CIs).

---

## 🌐 GitHub PRs (all merged on `main`)

| # | Branch | Subject |
|---|---|---|
| 1 | `chore/repo-bootstrap` | Repo bootstrap (corpus, deps, gitignore) |
| 2 | `feat/neo4j-etl` | Phase 1a — Neo4j Aura ETL with idempotent MERGE |
| 3 | `feat/graphrag-pipeline` | Phase 1b — pipeline 3 (vector + 1-2 hop walk) |
| 4 | `feat/agentic-graph-tool` | Phase 1c — pipeline 4 (graph_lookup tool node) |
| 5 | `fix/walk2hop-dup-ids` | dedupe walk_2hop neighbors by id (Python-side) |

Tag `v0.1-baseline-comparison` = original 60-row two-pipeline study (HEAD before Phase 1).

---

## 🔧 Kritik teknik notlar

### Aura instance state (probed 2026-05-09)
- 1132 `:Requirement` nodes (matches our jsonl count exactly — same source corpus, hackathon ETL preloaded it)
- All 5 traceability rel types present: `REFERENCES` (623), `VERIFIES` (104), `DERIVES_FROM` (22), `REFINES` (17), `SATISFIES` (2)
- Richer schema beyond ours: `:System` (90), `:Module` (30), `:Standard` (15), `:Component` (13), `:Interface`, `:Parameter`, `:TestMethod`, `:Stakeholder`, `:OperationalMode`, `:Image`, `:Organization`, `:Platform`, `:TestProcedure`
- Extra rel types we currently don't traverse: `ALLOCATED_TO`, `CONTAINS`, `COVERS`, `DEPENDS_ON`, `IMPLEMENTS`, `MENTIONS_SYSTEM`, `NEXT`, `REFERENCES_STANDARD`, `RELATED_TO`, `USES_COMPONENT`, `USES_INTERFACE`, `USES_PARAMETER`, `VERIFIED_BY_METHOD`
- Existing `:Requirement` props include `embedding` (precomputed!) — could exploit for Aura-native vector search in a Phase 5+ exploration if we want.

### Code architecture (4 pipelines)
```
vanilla_rag.py        Pipeline 1: embed → ChromaDB top-K → 1 LLM call
agentic_rag.py        Pipeline 2: LangGraph router/retriever-with-tools/critic/synthesizer
                      Pipeline 4 (use_graph=True): adds graph_lookup tool + graph_id_lookup node
graph_rag.py          Pipeline 3: vector seeds → Aura 1-2 hop walk → 1 LLM call
graph_store.py        Aura helpers: get_driver, walk_2hop (1-2 hop), hop1_directed (1-hop directed)
graph_loader.py       ETL CLI: jsonl → Aura MERGE (--dry-run, --reset)
compare.py            4-arm dispatch: vanilla / agentic / graphrag / agentic-graph
                      Flags: --no-graphrag, --no-agentic-graph
```

### Cypher gotchas (learned the hard way)
- `WITH b, min(length(path)) AS hops` does NOT reliably aggregate when `b` is a node value — saw same `b.id` at multiple hops. Fix: dedupe in Python (PR #5).
- `RETURN outs + collect(...)` mixes two aggregations → implicit-grouping error. Fix: split into two `WITH` clauses, concatenate (PR #4 graph_store.py).
- `OPTIONAL MATCH` returns one row with null-id when no match → filter `if n.get("id")` in Python.

### Reasoning loop (carry over from baseline)
- Reranker pacing fix: `AZURE_RERANKER_MIN_INTERVAL_S=15`, `MAX_DOC_CHARS=200`, class-level `_last_call`.
- bge-reranker-v2-m3 weights MISSING → `--no-local-rerank` always.

---

## 📁 Dosya map (paper-extension state)

```
agentic_rag.py        Pipeline 2 + Pipeline 4 (use_graph flag)
vanilla_rag.py        Pipeline 1
graph_rag.py          Pipeline 3 ⭐ NEW
graph_store.py        Aura read helpers ⭐ NEW
graph_loader.py       Aura ETL CLI ⭐ NEW (idempotent MERGE)
compare.py            4-arm dispatch (vanilla/agentic/graphrag/agentic-graph)
embedders.py          Local e5-small + Azure text-embedding-3-small
reranker.py           Azure Cohere (LocalBGE class kept but unused)
vector_store.py       ChromaDB helpers
build_index.py        Dual-collection indexer
data_loader.py        jsonl → chunk dicts (used by build_index, ChromaDB metadata)
eval_queries.py       10 hand-curated (will be extended to 300 in Phase 2a)
ui_app.py             Streamlit UI (still 2-pipeline; needs Phase 5 update)
llm_compat.py         Azure GPT-5.4 raw openai client (ChatOpenAI #34328 bypass)
data/synthetic/       1132 jsonl + 30 module narrative MDs (committed in chore/repo-bootstrap)
results/              CSV summaries + JSONL traces
.streamlit/           Theme config
.env                  Azure cred + Neo4j Aura cred (gitignored)
HANDOFF.md            ⭐ this file
README.md             Project doc + Results section
requirements.txt      Python 3.11+ deps incl. neo4j 5.x, ragas, scipy, statsmodels
```

---

## 🧠 Memory dosyaları

`~/.claude/projects/-Users-suleakarsu-Desktop-rag-vs-agentic/memory/`:
- `MEMORY.md` — index
- `user_profile.md` — terse, technical, deep stack knowledge
- `project_rag_comparison.md` — vanilla vs agentic baseline (now 4 pipelines)
- `reference_data_and_models.md` — corpus + model paths
- `feedback_execution_autonomy.md` — "no cost concerns, you decide"
- `feedback_research_first.md` — web search before brute-force
- `reference_neo4j_aura.md` — Aura cred (now actively used)
- `feedback_handoff_convention.md` — write HANDOFF.md at session close
- `feedback_no_claude_coauthor.md` ⭐ NEW — never `Co-Authored-By: Claude` in commits
- `feedback_pr_workflow.md` ⭐ NEW — every change → branch → push → PR → self-merge

---

## 🚦 Background processes

- Sanity bg run `compare.py` started; output writing to `results/sanity-v2.csv` + `/tmp/sanity_v2.log`. Notification fires on completion.
- After sanity completes: open PR `exp/phase1-sanity-run`, merge, then unblock Phase 2.

---

## ❓ Açık kararlar

1. **Streamlit UI'yi 4-pipeline'a güncelle?** — paper'a değil, ama defense / demo için faydalı. Phase 5 öncesi ekleyebiliriz.
2. **Aura'daki richer schema'yı (`:System`, `:Module`, etc.) Phase 5+ exploration olarak ekle?** — yeni paper bölümü açar; UBMK 6pp'e sığmaz, IEEE Aero full paper'a sığar (10pp).
3. **Real-DOORS triangulation hâlâ açık** — gelirse %80 sentetik kritiği söner, gelmezse Synthline defense devam.

Tüm Phase 2-6 task'ları memory'de + repo task list'inde.

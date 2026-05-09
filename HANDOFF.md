# RAG vs Agentic — Devam Noktası

> **Geri döndüğünde:** Bu dosyayı oku, sonra aşağıdaki **Quick resume** komutunu çalıştır.

---

## ⚡ Quick resume

```bash
cd /Users/suleakarsu/Desktop/rag-vs-agentic
git checkout main && git pull --rebase

# Phase 2d bg matrix hâlâ yaşıyor mu?
ps -ef | grep "compare.py.*main-v1" | grep -v grep
#   → tail /tmp/main_v1.log
#   → wc -l results/main-v1.csv  (target: 1185 with header, 1184 data rows)

# Bittiyse: 4-pipeline × 296-query scored CSV + stats
.venv/bin/python eval_metrics.py results/main-v1.csv \
    --queries data/eval/queries-hop-stratified.jsonl
.venv/bin/python -c "
from stats import paired_bootstrap_ci, paired_permutation_test
import csv
# (per-pipeline arrays for paired tests will land in Phase 2c-application PR)
"
```

---

## 🎯 Şu an neredeyiz

| | Durum |
|---|---|
| **Phase 0** Repo bootstrap (private GitHub `mftnakrsu/rag-vs-agentic`) | ✅ |
| **Phase 1a** Neo4j Aura ETL | ✅ (Aura preloaded by hackathon ETL — same 1132 :Requirement nodes) |
| **Phase 1b** GraphRAG pipeline 3 | ✅ |
| **Phase 1c** agentic-graph pipeline 4 | ✅ |
| **Phase 1 sanity** (4 pipelines × 10 queries) | ✅ — 40/40, results/sanity-v2.csv |
| **Phase 2a** Hop-stratified queries (296) | ✅ — data/eval/queries-hop-stratified.jsonl |
| **Phase 2b** Citation P/R/F1 + retrieval recall | ✅ — eval_metrics.py merged |
| **Phase 2c** Bootstrap CI + paired permutation | ✅ — stats.py merged |
| **Phase 2d** Main matrix run (4 pipelines × 296 queries) | ⏳ **BG RUNNING** |
| Phase 3a RAG-Critic baseline | ⏳ blocked on 2d |
| Phase 3b MuSiQue cross-eval | ⏳ blocked on 2d |
| Phase 3c reasoning_effort ablation | ⏳ blocked on 2d |
| Phase 4 Plots + failure-mode taxonomy | ⏳ blocked on 3 |
| Phase 5-6 Paper drafting + submit | ⏳ deadline 30 Jun (UBMK) / 1 Jul (IEEE Aero abs) |

---

## 🚦 Background process (KRİTİK — geri dönünce check et)

| | |
|---|---|
| Process | `compare.py --queries-jsonl data/eval/queries-hop-stratified.jsonl --embedders local --no-azure-rerank --no-local-rerank --out results/main-v1.csv` |
| Started | 2026-05-09 ~23:55 (yaklaşık) |
| Branch | `exp/main-matrix-v1` |
| Bg ID | `bzai72vjo` (Bash run_in_background) |
| Log | `/tmp/main_v1.log` (tee'li, full output) |
| Output | `results/main-v1.csv` + `results/main-v1.jsonl` (incremental write, crash-safe) |
| Total runs | 1184 (4 pipelines × 296 queries) |
| ETA | ~4-5 hours from start (~2026-05-10 04:00) |
| Approx token cost | ~6M Azure GPT-5.4 (free per Chris) |

**Crash recovery (eğer bg ölmüş olarak geri dönersen):**
1. `wc -l results/main-v1.csv` — kaç row tamam?
2. `tail -3 results/main-v1.csv` — son hangi query/pipeline'da kaldı?
3. compare.py'a `--resume` flag yok — basit fix: 296 query'den son tamamlanan'ın IDX+1'inden baş alarak `data/eval/queries-hop-stratified.jsonl`'i kes, yeni isimle çalıştır, sonra CSV'leri concat et. Veya sadece kaldığı yerden baştan başlat (idempotent değil ama duplicate row tolere edilebilir; eval_metrics.py / stats.py join'de duplicate'ları temizler).

---

## 🌐 GitHub PRs (all merged on `main`, this session)

| # | Branch | Subject |
|---|---|---|
| 1 | `chore/repo-bootstrap` | Repo bootstrap (corpus, deps, gitignore) |
| 2 | `feat/neo4j-etl` | Phase 1a Neo4j Aura ETL |
| 3 | `feat/graphrag-pipeline` | Phase 1b pipeline 3 |
| 4 | `feat/agentic-graph-tool` | Phase 1c pipeline 4 |
| 5 | `fix/walk2hop-dup-ids` | Dedupe walk_2hop neighbors |
| 6 | `chore/handoff-phase1c` | HANDOFF refresh post-1c |
| 7 | `feat/bootstrap-stats` | Phase 2c stats.py |
| 8 | `chore/add-claude-md` | CLAUDE.md guidance file |
| 9 | `exp/phase1-sanity-run` | Phase 1 sanity 40/40 |
| 10 | `feat/citation-metrics` | Phase 2b eval_metrics.py |
| 11 | `feat/compare-jsonl-queries` | --queries-jsonl flag |
| 12 | `feat/eval-hop-stratified` | Phase 2a 296 queries |
| 13 | `feat/compare-incremental-save` | Crash-safe row writes |

Tag `v0.1-baseline-comparison` = original 60-row two-pipeline study.

---

## 📊 Sanity headline numbers (10 hand-curated queries)

| Pipeline | Avg ms | Avg tok | Cited | citP | citR | F1 | RR |
|---|---:|---:|---:|---:|---:|---:|---:|
| vanilla | 7,822 | 833 | 5.0 | 0.220 | 0.617 | 0.311 | 0.617 |
| agentic | 17,720 | 3,786 | 2.6 | 0.583 | 0.783 | 0.637 | 0.700 |
| **graphrag** | 9,631 | 1,569 | **14.2** | 0.100 | **0.867** | 0.176 | **0.867** |
| **agentic-graph** | 18,910 | 4,306 | 2.1 | **0.683** | 0.783 | **0.700** | 0.767 |

**Paper-friendly trade-off** (will be bootstrap-CI'd at N=296 in Phase 2d):
- GraphRAG: max recall (0.87) ama precision 0.10 — over-cites
- agentic-graph: best F1 (0.70) — short-circuits ReAct on explicit IDs
- vanilla: bottom on both
- agentic: solid mid

---

## 🔧 Kritik teknik notlar

### Aura instance state
- 1132 `:Requirement` nodes preloaded by parallel hackathon session
- Traceability rels live: REFERENCES (623), VERIFIES (104), DERIVES_FROM (22), REFINES (17), SATISFIES (2)
- Plus extra: `:System`, `:Module`, `:Standard`, `:Component`, `:Interface`, `:Parameter`, `:TestMethod`, `ALLOCATED_TO`, `IMPLEMENTS` etc. — currently NOT exploited (paper extension idea)
- `:Requirement` props include precomputed `embedding` — could enable Aura-native vector search in Phase 5+ exploration

### Cypher gotchas (kalıcı)
- `WITH b, min(length(path)) AS hops` UNRELIABLE on node values → dedupe in Python
- `RETURN outs + collect(...)` mixed aggregation → split into two WITH clauses
- `OPTIONAL MATCH` no match → null-id row → filter `if n.get("id")`

### Parallel-session policy
- User runs multiple Claude Code sessions on this repo concurrently
- Other session created `chore/hf-dataset-upload` branch + `hf_dataset/` + `kaggle_dataset/` directories
- Don't touch / don't fix / don't delete — they're WIP for HF/Kaggle dataset upload

### Code architecture
```
vanilla_rag.py        Pipeline 1
agentic_rag.py        Pipelines 2 (use_graph=False) and 4 (use_graph=True)
graph_rag.py          Pipeline 3 (vector + 1-2 hop walk)
graph_store.py        Aura helpers: walk_2hop, hop1_directed
graph_loader.py       ETL CLI (idempotent MERGE, --dry-run)
compare.py            4-arm dispatch + matrix harness (--queries-jsonl, incremental)
eval_generator.py     Phase 2a: Aura chain sample → GPT-5.4 query gen
eval_metrics.py       Phase 2b: citation P/R/F1 + retrieval recall
stats.py              Phase 2c: bootstrap CI, paired permutation, Bonf+Holm
```

---

## ❓ Açık kararlar (geri dönünce karar ver)

1. **Phase 2d bg crash mi geçerli mi?** — first thing on resume: check.
2. **RAGAS faithfulness wiring** — eval_metrics.py'da `_add_ragas` stub. 1184 row × judge LLM call ≈ +30-60 dk + ~1-2M token. Önemli ama 2d'den sonra.
3. **Phase 3a RAG-Critic** — closest published baseline; mutlaka cite + compare; integration risk var (RUC-NLPIR repo Azure GPT-5'e adapt edilmeli).
4. **Phase 3b MuSiQue** — external validity. 200 question subset on vanilla + agentic + RAG-Critic.
5. **Phase 3c reasoning_effort ablation** — GPT-5.4 low/med/high üzerinde 100-q subset. Cheap originality bump.
6. **Streamlit UI 4-pipeline'a uyarlanmadı** — paper'a değil; demo/savunma için Phase 4 sonrası.

---

## 🧠 Memory dosyaları

- MEMORY.md (index)
- user_profile.md, project_rag_comparison.md, reference_data_and_models.md
- feedback_execution_autonomy, feedback_research_first
- reference_neo4j_aura (now actively used)
- feedback_handoff_convention (write HANDOFF on session close)
- feedback_no_claude_coauthor (don't append Claude co-author)
- feedback_pr_workflow (every change → branch → PR → merge)
- reference_parallel_sessions ⭐ NEW (don't touch other-session branches/dirs)

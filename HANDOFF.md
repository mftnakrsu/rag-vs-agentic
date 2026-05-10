# RAG vs Agentic — Devam Noktası

> **Geri döndüğünde:** Bu dosyayı oku, sonra aşağıdaki **Quick resume** komutunu çalıştır.

---

## 🎯 PRIMARY TARGET

**CIKM 2026 Short Paper** — deadline **23 May 2026** (~13 days).
- 4 pages ACM sigconf, double-blind
- Title: **"Hop-Adaptive, Link-Type-Aware Agentic Retrieval for Requirement Traceability"**
- Detailed plan + citations: see `project_cikm2026_target.md` in memory

---

## 🚦 BG RUNNING — Phase 2d v2 main matrix

**Started:** 2026-05-10 ~01:00 with `caffeinate -di` + `--resume` + `--retries 3`.

| | |
|---|---|
| Process | `caffeinate -di python compare.py ...` (PIDs in pgrep below) |
| Log | `/tmp/main_v2.log` (`tail -f` to watch) |
| Output | `results/main-v2.csv` + `.jsonl` (incremental, crash-safe) |
| Scope | 5 pipelines × 296 queries × 3 repeats = **4440 rows** |
| Speed | ~13s/row average |
| Wall ETA | **~16-17 hr from start** (~17:00-19:00 next day) |
| Cost | ~30M Azure tokens (free tier) |

**Robustness in place (in order of likely failure):**
- Mac sleep — `caffeinate -di` running on launch shell
- Brief network blip — per-row retry × 3 with exp backoff (10s, 20s, 40s)
- Mid-row crash / kernel panic — `IncrementalWriter` flush + fsync every 25 rows
- Total kill — `--resume` skips already-done (pipeline, embedder, reranker, query, repeat) tuples on next start

**If bg dies overnight, restart with same command (resume engages):**
```bash
pgrep -f "compare.py.*main-v2"
#   → no output? bg died — see how far it got:
wc -l results/main-v2.csv

caffeinate -di .venv/bin/python compare.py \
  --queries-jsonl data/eval/queries-hop-stratified.jsonl \
  --embedders local --no-azure-rerank --no-local-rerank \
  --repeats 3 --resume --retries 3 --retry-wait-s 10 \
  --out results/main-v2.csv 2>&1 | tee -a /tmp/main_v2.log &
```

---

## ⚡ Quick resume (when you wake up)

```bash
cd /Users/suleakarsu/Desktop/rag-vs-agentic
git checkout main && git pull --rebase

# 1) Bg done?
ps -ef | grep "compare.py.*main-v2" | grep -v grep
wc -l results/main-v2.csv  # target 4441 lines (header + 4440 data rows)

# 2) Errored rows? (transient outages would surface here)
.venv/bin/python rerun_errors.py results/main-v2.csv \
       --queries data/eval/queries-hop-stratified.jsonl --dry-run
# → if any, run without --dry-run to recover them

# 3) Score with citation P/R/F1
.venv/bin/python eval_metrics.py results/main-v2.csv \
       --queries data/eval/queries-hop-stratified.jsonl
# → writes results/main-v2-scored.csv + per-pipeline aggregate

# 4) Multi-judge calibration on 100-q stratified subset (Cohen's κ)
.venv/bin/python multi_judge.py results/main-v2.csv \
       --corpus data/synthetic/requirements.jsonl --subset 100
# → writes results/main-v2-judged.csv, prints κ
# → if κ < 0.4, halt and inspect

# 5) Tell me one of:
#    "phase 3 musique"  — kick off external validity (200 q × 3 pipelines)
#    "phase 4 plots"    — Pareto + hop-stratified curves + failure modes
#    "phase 5 paper"    — start drafting CIKM 4-page sigconf
```

---

## 🎯 Şu an neredeyiz (22 PRs landed, all merged to main)

| Faz | Durum | Key PR |
|---|---|---|
| Phase 0 Repo bootstrap | ✅ | #1 |
| Phase 1a Aura ETL | ✅ | #2 |
| Phase 1b GraphRAG pipeline 3 | ✅ | #3 |
| Phase 1c agentic-graph pipeline 4 | ✅ | #4 |
| `fix/walk2hop-dup-ids` | ✅ | #5 |
| Phase 2a 296 hop-stratified queries | ✅ | #12 |
| Phase 2b citation P/R/F1 (cheap) | ✅ | #10 |
| Phase 2c stats.py (percentile + paired perm + Bonf + Holm) | ✅ | #7 |
| Phase 1 sanity 40/40 | ✅ | #9 |
| `feat/compare-jsonl-queries` | ✅ | #11 |
| `feat/compare-incremental-save` | ✅ | #13 |
| `feat/rerun-errors` | ✅ | #15 |
| `feat/bca-stats` (BCa CI) | ✅ | #19 |
| **Phase 1d hop_router.py — paper novelty hook** | ✅ | #18 |
| `feat/compare-repeats` (--repeats N) | ✅ | #20 |
| `feat/multi-judge-calibration` (GPT-5.4 + Gemini + κ) | ✅ | #21 |
| `feat/compare-resume-and-retry` | ✅ | #22 |
| **Phase 2d v2 main matrix (5 × 296 × 3)** | ⏳ **BG RUNNING** | — |
| Phase 3 MuSiQue cross-eval | ⏳ blocked on 2d | — |
| Phase 4 plots + failure-mode taxonomy | ⏳ blocked on 3 | — |
| **Phase 5 paper skeleton** | ✅ `paper/cikm/` compile-clean (this session) | — |
| Phase 5-6 paper drafting + submit | ⏳ deadline 23 May 2026, awaits results + figs | — |

---

## 📄 Paper skeleton (added this session)

`paper/cikm/` — 4-page ACM `sigconf`, double-blind, anonymous-author
version, compile-clean. Figure 1 (architecture) is hand-written TikZ
rendered inline via `\input{figures/architecture-tikz}` — no separate
sub-compile needed.

**Compile (Overleaf):** upload `paper/cikm-skeleton.zip` (regenerate
with `cd paper/cikm && zip -r ../cikm-skeleton.zip . -x ".gitignore"`),
set `main.tex` as main, Recompile. Local: `cd paper/cikm && make`.

**Pending before 23 May submission:**
1. Figures 2–3 (cost-quality Pareto + hop-stratified accuracy) — needs
   `results/main-v2-scored.csv` (post BG + judge); write
   `scripts/plot_pareto.py` + `scripts/plot_hop_curves.py`.
2. Table 1 numbers — same source.
3. Placeholders in abstract / intro headline / §5.1–5.4 / conclusion —
   fill after stats finalize.
4. `refs.bib` `[TODO: lead author]` entries (5 of 31) — verify via DBLP
   / Semantic Scholar.
5. Anonymisation final check (pdfinfo, no GitHub URLs in PDF, third-person
   self-citations) — see `paper/cikm/README.md` checklist.

**De-anonymisation note:** this `HANDOFF.md` and the project root
`README.md` are publicly committed. The paper title appears verbatim on
line 11 here. If strict double-blind hygiene matters during review,
redact line 11 (and the title in any other tracked file) in a follow-up
commit before submission.

---

## 📊 Sanity headline (10 hand-curated, BG main-v2 will produce 5×296×3 with bootstrap CIs)

| Pipeline | Avg ms | Avg tok | Cited | citP | citR | F1 |
|---|---:|---:|---:|---:|---:|---:|
| vanilla | 7,822 | 833 | 5.0 | 0.220 | 0.617 | 0.311 |
| agentic | 17,720 | 3,786 | 2.6 | 0.583 | 0.783 | 0.637 |
| graphrag | 9,631 | 1,569 | 14.2 | 0.100 | **0.867** | 0.176 |
| agentic-graph | 18,910 | 4,306 | 2.1 | 0.683 | 0.783 | **0.700** |
| **adaptive** | (TBD) | (TBD) | (TBD) | (TBD) | (TBD) | (TBD) |

**Paper trade-off (will be re-validated on N=296 × 3 with BCa CIs):**
- GraphRAG: max recall (0.87), low precision (0.10) — over-cites via always-walk
- agentic-graph: best F1 (0.70) — graph_id_lookup short-circuit is precise
- vanilla: bottom both axes
- adaptive: should land on the Pareto frontier between the others

---

## 🔧 Kritik teknik notlar

### What's runnable / what's gated

| Module | Status | Needs |
|---|---|---|
| vanilla / agentic / graphrag / agentic-graph / adaptive | ✅ | — |
| eval_generator.py | ✅ | Aura (in .env) |
| eval_metrics.py | ✅ | results CSV + queries JSONL |
| multi_judge.py | ✅ | GOOGLE_API_KEY (in .env) |
| stats.py | ✅ | per-query metric arrays |
| rerun_errors.py | ✅ | — |

### Aura instance state
- 1132 `:Requirement` nodes preloaded by parallel hackathon session
- Live rels: REFERENCES (623), VERIFIES (104), DERIVES_FROM (22), REFINES (17), SATISFIES (2)
- Extra schema (`:System`, `:Module`, `:Standard`, `ALLOCATED_TO`, `IMPLEMENTS`, ...) — currently NOT exploited; potential paper extension

### Cypher gotchas (kalıcı)
- `WITH b, min(length(path)) AS hops` UNRELIABLE on node values → dedupe in Python
- `RETURN outs + collect(...)` mixed aggregation → split into two WITH clauses
- `OPTIONAL MATCH` no match → null-id row → filter `if n.get("id")`

### Code architecture
```
vanilla_rag.py        Pipeline 1
agentic_rag.py        Pipelines 2 (use_graph=False) and 4 (use_graph=True)
graph_rag.py          Pipeline 3
hop_router.py         Pipeline 5 (adaptive) ⭐ paper novelty hook
graph_store.py        Aura helpers (walk_2hop, hop1_directed)
graph_loader.py       ETL CLI (idempotent MERGE)
compare.py            5-arm dispatch + --repeats + --resume + retry + IncrementalWriter
eval_generator.py     Phase 2a query gen
eval_metrics.py       Phase 2b citation P/R/F1 + retrieval recall
multi_judge.py        Phase 2b multi-judge (GPT-5.4 + Gemini + κ)
stats.py              Phase 2c bootstrap (percentile + BCa) + paired perm + Bonf + Holm
rerun_errors.py       Recover errored matrix rows
```

### Parallel-session policy
- User runs multiple Claude Code sessions on this repo concurrently
- Other session: `chore/hf-dataset-upload` branch, `hf_dataset/`, `kaggle_dataset/` dirs — DO NOT touch

---

## ❓ Açık kararlar (geri dönünce karar ver)

1. **MuSiQue subset boyutu?** Plan 200 önerir. 200 × 3 pipeline ≈ 1-2 saat bg.
2. **Phase 4 plot stack** — matplotlib + seaborn yüklü; Pareto + hop-stratified curves + failure-mode 30-q manual coding.
3. **Paper draft language** — EN (CIKM short paper double-blind) decided.
4. **Streamlit UI** — paper'a değil; demo için Phase 5 sonrası ekleyebiliriz.

---

## 🧠 Memory dosyaları

`~/.claude/projects/-Users-suleakarsu-Desktop-rag-vs-agentic/memory/`:
- `MEMORY.md` (index)
- `user_profile.md`, `project_rag_comparison.md`, `reference_data_and_models.md`
- `feedback_execution_autonomy`, `feedback_research_first`
- `reference_neo4j_aura` (now actively used)
- `feedback_handoff_convention`, `feedback_no_claude_coauthor`, `feedback_pr_workflow`
- `reference_parallel_sessions`
- `project_cikm2026_target.md` ⭐ — primary venue plan, citations, defenses, kill switches

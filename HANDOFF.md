# RAG vs Agentic — Devam Noktası

> **Geri döndüğünde:** Bu dosyayı oku, sonra aşağıdaki **Quick resume** komutunu çalıştır.

---

## 🎯 PRIMARY TARGET (decided 2026-05-10)

**CIKM 2026 Short Paper** — deadline **23 May 2026** (~13 days).

- 4 pages ACM sigconf, double-blind
- Title: **"Hop-Adaptive, Link-Type-Aware Agentic Retrieval for Requirement Traceability"**
- Submission: EasyChair → tag `submission/cikm-2026-short`
- Plan + citations + defenses → see `project_cikm2026_target.md` in memory

---

## ⚡ Quick resume

```bash
cd /Users/suleakarsu/Desktop/rag-vs-agentic
git checkout main && git pull --rebase

# 1) Confirm 4 pipelines + infra still working
.venv/bin/python -c "
from dotenv import load_dotenv; load_dotenv()
from agentic_rag import build_graph
from graph_rag import graph_rag
from graph_store import get_driver, walk_2hop
print('imports OK; on track for Phase 1d')
"

# 2) On feat/hop-adaptive-router branch?
git branch --show-current
#   → if not: git checkout feat/hop-adaptive-router

# 3) hop_router.py exists yet?
ls -la hop_router.py 2>/dev/null
#   → if missing, that's the next thing to build (Phase 1d)
```

Sonra **bana** dönüp tek cümleyle ne istediğini söyle. Ör:
- *"phase 1d devam"* — hop_router.py'yi yazıp adaptive pipeline'ı compare.py'a kayıt edeyim
- *"main matrix kick"* — Phase 1d ready ise 5×296×3-seed bg matrix overnight
- *"phase 2b multi-judge"* — Anthropic key verirsen judge calibration

---

## 🎯 Şu an neredeyiz (15 PR landed in main)

| Faz | Durum | PR |
|---|---|---|
| **Phase 0** Repo bootstrap | ✅ | #1 |
| **Phase 1a** Aura ETL | ✅ | #2 |
| **Phase 1b** GraphRAG pipeline 3 | ✅ | #3 |
| **Phase 1c** agentic-graph pipeline 4 | ✅ | #4 |
| `fix/walk2hop-dup-ids` | ✅ | #5 |
| **Phase 2a** 296 hop-stratified queries | ✅ | #12 |
| **Phase 2b**(citation P/R/F1) | ✅ | #10 |
| **Phase 2c**(stats.py: bootstrap, perm, Bonf, Holm) | ✅ | #7 |
| `feat/compare-jsonl-queries` | ✅ | #11 |
| `feat/compare-incremental-save` | ✅ | #13 |
| `feat/rerun-errors` | ✅ | #15 |
| `chore/handoff-phase2d` | ✅ | #14 |
| `chore/add-claude-md` | ✅ | #8 |
| `chore/handoff-phase1c` | ✅ | #6 |
| Phase 1 sanity 40/40 | ✅ | #9 |

---

## ⚠ KRİTİK PIVOT (2026-05-10 ~00:00)

User pasted CIKM 2026 14-day plan, delegated all decisions ("sen karar ver her şeye"). Adjustments vs prior trajectory:

1. **Phase 2d main matrix BG was running with 4-pipeline × 1-seed × 296 query scope** — KILLED. Wrong scope; CIKM plan needs 5 pipelines (incl. **adaptive**) × 3 seeds.
2. Partial output preserved at `results/main-v0-partial.csv` + `.jsonl` (42 rows captured before kill — will use as reference for hop_router heuristics if useful).
3. **Phase 1d (hop_router.py) is the missing paper-grade novelty hook.** Branch `feat/hop-adaptive-router` is created but empty — this is the next thing to build.
4. Phase 2b is being redefined: not just citation metrics (already done in PR #10), but **multi-judge calibration** (GPT-5.4 + Anthropic Claude or Gemini, Cohen's κ, position-swap). Needs Anthropic API key in `.env` (`ANTHROPIC_API_KEY=...`).
5. Phase 2c stats needs **BCa bootstrap CIs** added (we have percentile only).

---

## 🚧 Next steps (in order)

### Phase 1d — `feat/hop-adaptive-router` (in flight)

`hop_router.py`:
- Features: explicit_id_count (regex `\b[A-Z]{2,5}-\d+\b`), n_modules (set of {ADS, FCC, NAV, ...}), traceability_keywords ("derives from", "satisfies", "verified by", "trace"), chain_indicators ("how does", "from", "via"), numeric_hint ("rate", "Hz", "ms", "kt", "ft"), query_length_tokens.
- V1 rule-based routing among {vanilla, agentic, graphrag, agentic-graph}:
  - explicit_id ≥ 1 + traceability_kw → agentic-graph (graph_id_lookup short-circuit)
  - explicit_id ≥ 1 + no_traceability → vanilla
  - cross_module + chain_indicator → graphrag
  - traceability_kw + no_id → graphrag
  - numeric_hint + 1 module → vanilla
  - default → agentic
- V2 (if time after Day 5): logistic regression on labeled training queries.
- `adaptive_rag(query)` wrapper: routes via hop_router, calls chosen pipeline, annotates `routed_to` + `route_reason` in result dict.

**`compare.py` extension**: add `'adaptive'` arm + `--seed` parameter.

**Acceptance**: 5 pipelines run end-to-end on the 10 hand-curated queries.

### Phase 2c upgrade — `feat/bca-stats`

Add BCa CI to `stats.py` (current is percentile only). Needed for paper rigor.

### Phase 2b multi-judge — `feat/multi-judge-calibration`

GPT-5.4 + Claude (or Gemini) on 100-query subset. Cohen's κ + position-swap. Halt if κ < 0.4.

### Phase 2d main matrix v2 — `exp/main-matrix-v2`

5 pipelines × 296 queries × 3 seeds = 4440 runs. ~12-15 hr bg overnight.
- Run command (after Phase 1d merged): `compare.py --queries-jsonl data/eval/queries-hop-stratified.jsonl --embedders local --no-azure-rerank --no-local-rerank --seeds 0,1,2 --out results/main-v2.csv`
- Halve seeds 3→2 if 4500 too expensive (Azure cost or wall time).

### Phase 3 MuSiQue — `feat/cross-eval-musique`

200 questions, vanilla + agentic + adaptive only. External validity defense.

### Phase 4 plots + failure-mode taxonomy

Cost-quality Pareto, hop-stratified accuracy curves, 30-query manual coding into 6-8 categories.

### Phase 5-6 paper writing + submission

4 pages ACM sigconf double-blind. EasyChair submit by 23 May 2026.

---

## 🚦 Background processes

None active right now (Phase 2d v1 was killed).

---

## 🔧 Kritik teknik notlar

### Anthropic API key (Phase 2b dependency)

User asked "ne için". Multi-judge calibration → ~$5-15 cost on 100-q subset; defuses judge-bias attack (Wataoka et al., arXiv:2410.21819). If unavailable: Gemini fallback or single-judge with explicit caveat.

### Aura instance state
- 1132 `:Requirement` nodes preloaded by parallel hackathon session
- Live rels: REFERENCES (623), VERIFIES (104), DERIVES_FROM (22), REFINES (17), SATISFIES (2)
- Extra schema (System, Module, Standard, ALLOCATED_TO, etc.) — not exploited; could be paper extension.

### Cypher gotchas (kalıcı)
- `WITH b, min(length(path)) AS hops` UNRELIABLE on node values → dedupe in Python
- `RETURN outs + collect(...)` mixed aggregation → split into two WITH clauses
- `OPTIONAL MATCH` no match → null-id row → filter `if n.get("id")`

### Code architecture (current, after CIKM pivot)
```
vanilla_rag.py        Pipeline 1
agentic_rag.py        Pipelines 2 (use_graph=False) and 4 (use_graph=True)
graph_rag.py          Pipeline 3
graph_store.py        Aura helpers
graph_loader.py       ETL CLI
hop_router.py         Pipeline 5 (adaptive) ← TO BUILD (Phase 1d)
compare.py            5-arm dispatch + seed parameter (TO EXTEND)
eval_generator.py     Phase 2a query gen
eval_metrics.py       Citation P/R/F1 + retrieval recall (RAGAS stub)
stats.py              Bootstrap, paired permutation, Bonf, Holm (BCa TO ADD)
rerun_errors.py       Recover errored matrix rows
```

### Parallel-session policy (carries over)
- User runs multiple Claude Code sessions on this repo concurrently
- Other session: `chore/hf-dataset-upload`, `hf_dataset/`, `kaggle_dataset/` — DO NOT touch

---

## ❓ Açık kararlar (geri dönünce karar ver)

1. **Anthropic API key var mı?** Phase 2b multi-judge için. Yoksa Gemini ya da single-judge with caveat.
2. **3 seed mi 2 seed mi?** Plan 3 önerir; budget cap Azure free olduğu için 3 ile başla, dar gelirse 2'ye düşür.
3. **MuSiQue subset boyutu?** Plan 200 önerir. Daha az kabul edilir mi paper'da? (Plan'ın gate'lerinde belirtilmemiş.)
4. **Streamlit UI 4-pipeline'a uyarlanmadı** — paper'a değil; demo için Phase 4 sonrası.

---

## 🧠 Memory dosyaları

`~/.claude/projects/-Users-suleakarsu-Desktop-rag-vs-agentic/memory/`:
- `MEMORY.md` (index)
- `user_profile.md`, `project_rag_comparison.md`, `reference_data_and_models.md`
- `feedback_execution_autonomy`, `feedback_research_first`
- `reference_neo4j_aura` (now actively used)
- `feedback_handoff_convention` (write HANDOFF on session close)
- `feedback_no_claude_coauthor` (don't append Claude co-author)
- `feedback_pr_workflow` (every change → branch → PR → merge)
- `reference_parallel_sessions` (don't touch other-session branches/dirs)
- `project_cikm2026_target.md` ⭐ NEW — primary venue plan, citations, defenses, kill switches

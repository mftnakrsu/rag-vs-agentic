# HANDOFF — CIKM 2026 Short Paper, Agentic vs Graph RAG for DO-178C Traceability

**Last updated:** 2026-05-11
**Previous session ran out of context.** Read this entire doc before doing anything. Do NOT touch the multi-judge background job (PID 60426/60428).

---

## 1. Project in one paragraph

We are submitting a 4-page CIKM 2026 Short Paper comparing 5 RAG pipelines (vanilla, agentic, agentic+graph, graphrag, adaptive) on a synthetic 1,132-requirement DO-178C-style aerospace traceability corpus with 296 hop-stratified queries (stratified across 1-hop, 2-hop, 3+-hop, ~99 each). The full ablation matrix (4,440 runs, 0 errors) is complete. ALCE-style citation precision/recall/F1 scoring is complete. A 3-judge faithfulness ensemble (GPT-5.4 + GPT-4.1 + Gemini-as-optional) is currently running in the background. The paper's central thesis is that **GraphRAG over-cites massively (citP ≈ 0.12) and loses on F1 despite the highest cited-count, while different architectures dominate at different hop strata, making precision-first evaluation and stratum-conditional analysis necessary.**

**Deadline:** CIKM 2026 Short Paper — VERIFY on cikm2026.diag.uniroma1.it. Likely 6 June 2026 (abstract 30 May). Full paper deadline is 23 May — that is NOT our track. Today is 2026-05-11; ~26 days to 6 Jun.

**Fallback venue:** UBMK 2026 (Istanbul, 30 June 2026), IEEE Xplore, ~80% acceptance. Use only if CIKM desk-rejects or multi-judge fails catastrophically.

---

## 2. Key results locked (do not re-run)

### Per-stratum citation F1 (from `results/main-v2-scored.csv`, 4440 rows, single-judge)

| Stratum | 🥇 1st | 🥈 2nd | 🥉 3rd | 4th | 5th |
|---|---|---|---|---|---|
| 1-hop | agentic-graph **0.517** | agentic 0.497 | vanilla 0.454 | adaptive 0.425 | graphrag 0.224 |
| 2-hop | **vanilla 0.548** ⭐ | adaptive 0.410 | agentic-graph 0.398 | agentic 0.396 | graphrag 0.308 |
| 3+-hop | agentic-graph **0.215** | agentic 0.172 | adaptive 0.079 | graphrag 0.071 | vanilla 0.037 |

**Aggregate F1:**
- agentic-graph: 0.378
- GraphRAG: 0.202

(Aggregate is NOT the headline — per-stratum is.)

### GraphRAG over-citation (the paper's hook)

| Metric | graphrag | agentic | agentic-graph |
|---|---|---|---|
| Mean cited count | 14.9 | ~4-6 | ~5-7 |
| Citation precision (citP) | **0.12** | ~0.58 | ~0.40 |
| Retrieval recall | 0.91-0.95 | lower | medium |

GraphRAG finds gold content but over-cites by ~3× — high recall, collapsed precision, F1 floor.

### Router behavior (V1, rule-based)

| Stratum | Optimal pipeline | V1 actual routing | Mismatch |
|---|---|---|---|
| 1-hop | agentic-graph | 55% agentic, 26% graphrag, 19% vanilla, 0% agentic-graph | ❌ never picks optimal |
| 2-hop | vanilla | 71% agentic, 20% vanilla | ❌ under-routes vanilla |
| 3+-hop | agentic-graph | 86% graphrag, 14% agentic | ❌ wrong winner |

**Conclusion:** V1 router does not match the empirical optimum. **V2 ML router (logistic regression trained on this data) is mandatory** — without it, reviewers will reject ("your router doesn't even match its own training data").

---

## 3. Currently running: multi-judge faithfulness (background job)

**Status when handoff was written:** 49/296 (~17%) done, ETA ~13-14 min, PIDs 60426/60428 alive, 0 errors.

**Files being written (DO NOT TOUCH):**
- `results/main-v2-judged.csv` (growing, bg writing)

**When the job completes, run this analysis pipeline:**

1. **Fleiss' κ** (3 raters: GPT-5.4, GPT-4.1, Gemini if available) + 3 pairwise Cohen's κ
2. **Per-judge faithfulness rate** (% of answers judged faithful by each judge)
3. **Unanimous agreement rate** (% of cases all 3 judges agree)
4. **Per-stratum × per-pipeline faithfulness matrix** — present side-by-side with the citation F1 table above
5. **Gold faithfulness check** — see Decision Tree below

**Cost estimate at job start:** ~$15-25 for 3000 judgments. Confirm in OpenAI/Anthropic dashboards.

---

## 4. Quick resume commands

```bash
cd /Users/suleakarsu/Desktop/rag-vs-agentic
git checkout main && git pull --rebase

# 1) Multi-judge bg alive?
ps -p 60426,60428 -o pid,etime,stat 2>&1 | head
wc -l results/main-v2-judged.csv  # was 130 lines at handoff save

# 2) Tail bg log
tail -f /tmp/judge.log

# 3) Paper compile sanity
cd paper/cikm && make && cd ../..

# 4) Once bg completes: Fleiss κ + faithfulness matrix
.venv/bin/python -c "
import pandas as pd
from statsmodels.stats.inter_rater import fleiss_kappa
df = pd.read_csv('results/main-v2-judged.csv')
# pivot to (item, rater) judgments and compute κ; then per-pipeline mean faithfulness
"

# 5) In PARALLEL with bg (do NOT wait): kick off V2 ML router
# Training data: results/main-v2-scored.csv with per-query F1-best system as label.
# Features: entity count, ID-regex matches, question-type keywords, query embedding.
# Output: per-query routing prediction + oracle upper bound.
```

---

## 5. The decision tree (after multi-judge results arrive)

### Scenario 1: GraphRAG over-citation confirmed
**Condition:** GraphRAG mean faithfulness < 0.5 AND Fleiss' κ ≥ 0.5

→ **Plan D + Plan A combined (RECOMMENDED).** GraphRAG is genuinely over-citing. Paper title:
> *"When Breadth Hurts Precision: A Stratum-Conditional Analysis of Vanilla, Agentic, and Graph RAG for Requirements Traceability"*

Two contributions:
- **Negative (Plan D leg):** GraphRAG inflates citations, F1 collapses, precision-first eval reverses Pareto
- **Positive (Plan A leg):** Stratum-conditional dominance is real (3 different winners at 3 hop levels), motivating learned routing

### Scenario 2: Gold set is incomplete
**Condition:** GraphRAG mean faithfulness > 0.7 AND citP still 0.12

→ **Plan C only (characterization).** GraphRAG's citations are actually supported by context, but our gold set is incomplete — so citP undercounts true precision. Drop the "over-citation" framing. Title:
> *"When Does Each Architecture Win? A Hop-Stratified Characterization of RAG for DO-178C Traceability"*

Single contribution: stratum-conditional dominance (3 different winners). Discuss gold-incompleteness as a limitation.

### Scenario 3: κ < 0.4 (judges disagree too much)
**Condition:** Fleiss' κ < 0.4

→ **Iterate prompt once, re-run pilot on 50-query subset.** If still < 0.4, drop multi-judge faithfulness from the paper. Fall back to ALCE-style citation P/R/F1 only (already computed, single-judge). Frame as characterization paper, Plan C, title above.

### Scenario 4: κ in [0.4, 0.5] (gray zone)
→ Plan A is risky (reviewers will attack moderate agreement on strong claim). Plan D+A hybrid still works because GraphRAG over-citation is supported by external literature (Han et al. 2025, Xiang et al. ICLR'26) even without strong κ. Lean toward Plan C unless GraphRAG faithfulness clearly < 0.5.

---

## 6. Paper structure (LaTeX skeleton already exists)

Location: `paper/cikm/sections/`
- `01-abstract.tex` — REWRITE after results lock
- `02-introduction.tex` — draft exists; lock thesis after Decision Tree
- `03-related-work.tex` — citations scaffold ready; key anchors: Han et al. 2025 (arxiv 2502.11371), Xiang et al. ICLR'26 (arxiv 2506.05690), Adaptive RAG (Jeong NAACL 2024), ALCE (Gao ACL 2023), RAGChecker (NeurIPS 2024), LiSSA (Fuchß ICSE 2025), Synthline (REFSQ 2025)
- `04-method.tex` — 5 pipelines + V2 router + ALCE metric definitions
- `05-experiments.tex` — corpus, 296 hop-stratified queries, multi-judge protocol, bootstrap BCa
- `06-results.tex` — PRIMARY FILE TO FILL after multi-judge: 3 tables (per-stratum F1, faithfulness matrix, oracle gap), 2 figures (Pareto, hop-stratified curves)
- `07-discussion.tex` — threats to validity, GraphRAG over-citation discussion
- `08-conclusion.tex` — 3-4 sentences
- `99-genai-disclosure.tex` — MANDATORY for CIKM 2026

**Compile:** `cd paper/cikm && make`. Target: under 4 pages including appendix (refs and GenAI disclosure don't count).

**Double-blind:** `\documentclass[sigconf,natbib=true,anonymous=true]{acmart}`. NO author names, NO GitHub URLs, NO acknowledgments. Verify with `pdfinfo main.pdf`.

---

## 7. Critical remaining work (priority order)

| Priority | Task | Effort | Blocker |
|---|---|---|---|
| 🔴 P0 | Wait for multi-judge bg to complete | passive | nothing |
| 🔴 P0 | Analyze Fleiss' κ + faithfulness matrix | 1-2 hr | bg done |
| 🔴 P0 | Decision tree → pick title | 30 min | analysis done |
| 🟡 P1 | **V2 ML router** (logistic regression on labeled F1-best per query) + oracle upper bound | 1 day | nothing — can start NOW in parallel with bg |
| 🟡 P1 | Bootstrap BCa CIs (B=1000) + paired Wilcoxon + Holm correction per stratum | 0.5 day | analysis done |
| 🟢 P2 | Fill `06-results.tex` with locked numbers | 1 day | stats done |
| 🟢 P2 | Rewrite abstract + introduction with locked thesis | 1 day | title locked |
| 🟢 P2 | Anonymization audit (pdfinfo metadata, self-cite phrasing, no GH links) | 2 hr | paper complete |
| 🔵 P3 | MuSiQue 200-query cross-eval (external validity) | 2 days | only if time permits |
| 🔵 P3 | Failure mode taxonomy (30 worst queries manual coding) | 1 day | only if time permits |

**Drop these if behind schedule:** MuSiQue cross-eval, RAG-Critic baseline integration (DROPPED — out of scope for 4-page short). They're nice-to-have, not critical for CIKM short.

---

## 8. Defenses (write into paper)

| Reviewer concern | Defense |
|---|---|
| Synthetic corpus | Cite Synthline (REFSQ 2025, arxiv 2505.03265); IP-restriction of certified DO-178C artifacts; MuSiQue cross-eval as partial mitigation (if done) |
| LLM-as-judge bias | 3-judge ensemble + Fleiss' κ + position-swap controls; cite Wataoka et al. 2024 (arxiv 2410.21819) and the Chen et al. 2024c finding that self-preference is muted within RAG tasks |
| Single domain | MuSiQue cross-eval (if done); explicit scope statement |
| Small N | 296 hop-stratified queries × bootstrap BCa + paired permutation + Holm correction |
| V1 router doesn't beat fixed pipelines | V2 ML router + oracle upper bound shows headroom; frame contribution as "router as diagnostic instrument revealing stratum-conditional structure" |
| "Just rediscovering Han et al. 2025?" | Domain (DO-178C aerospace), typed traceability edges (derives_from / satisfies / references / traces_to), hop-stratified protocol, routing-accuracy diagnostic = new combination |

---

## 9. User preferences (IMPORTANT)

- **Language:** Turkish in chat, English in paper/code/commit messages
- **Commit messages:** NEVER add "Co-Authored-By: Claude" or "Generated with Claude Code" lines
- **Tone:** Direct, opinionated, no hedging. User values honest assessment over diplomatic.
- **Pace:** User often says "yetiştiririm" and pushes for speed. Resist commitment to aggressive deadlines without checking the math. Verify timelines.
- **Decisions:** User makes strategy calls (title, plan, venue). You execute and surface options with trade-offs.
- **When user is stressed/abusive:** De-escalate calmly, do NOT mirror the tone, hold the line on professional standards.

---

## 10. Repo state (when handoff was written)

**Branch:** main (verify with `git branch`)
**Last commits (newest first):**
- `6d6ee4b` feat(judge): tqdm progress bar + incremental CSV write
- `48ee9a0` fix(judge): Gemini optional (free tier dropped to 20 RPD May 2026)
- `8b2d216` feat(judge): add GPT-4.1 as 3rd judge + Fleiss' kappa
- `bf45f00` feat(paper): CIKM 2026 short-paper LaTeX skeleton + TikZ architecture
- `487f833` feat(judge): rate-limit + 429 retry for Gemini free-tier compliance

**Untracked files:**
- `results/main-v0-partial.csv` (historic, 42-row killed-v1 reference)
- `results/main-v2-judged.csv` (bg writing — DO NOT TOUCH)
- `results/main-v2-scored.csv` (locked, +citation P/R/F1)
- `results/main-v2.csv` (locked, 4442 rows)
- `results/sanity-v2-scored.csv` (10-query hand-curated baseline)

**Active background jobs:** multi_judge.py 296-query subset run, PIDs 60426/60428.

### Aura graph state (preloaded, used by graphrag + agentic-graph)
- 1132 `:Requirement` nodes preloaded by hackathon ETL
- Live rels: REFERENCES (623), VERIFIES (104), DERIVES_FROM (22), REFINES (17), SATISFIES (2)
- Extra schema (`:System`, `:Module`, `:Standard`, `ALLOCATED_TO`, `IMPLEMENTS`, ...) — currently NOT exploited; potential paper extension

---

## 11. First actions for new session

1. Read this entire HANDOFF.md before doing anything
2. Check multi-judge bg status: `ps -p 60426,60428` — if alive, wait; if dead, check `results/main-v2-judged.csv` for completion (should be 296 queries × 5 systems × 3 judges with position swap)
3. **In parallel with bg (DO NOT WAIT):** start V2 ML router script. Training data: `results/main-v2-scored.csv` with per-query F1-best system as label. Features: entity count, ID-regex matches, question-type keywords, query embedding. Output: per-query routing prediction + oracle upper bound calculation
4. When bg completes: run analysis pipeline (Fleiss' κ, faithfulness matrix, bootstrap CIs)
5. Present numbers to user — user decides title/plan
6. Fill `06-results.tex` with locked numbers
7. Polish abstract and introduction in `01-abstract.tex` and `02-introduction.tex`

---

## 12. Don't do these

- ❌ Don't commit Plan A/C/D unilaterally — user decides title after seeing numbers
- ❌ Don't touch `results/main-v2-judged.csv` while bg is writing
- ❌ Don't re-run the 4440-row ablation — numbers are locked
- ❌ Don't add MuSiQue cross-eval or RAG-Critic baseline without explicit go-ahead — they're optional
- ❌ Don't include "Co-Authored-By: Claude" in any commit message
- ❌ Don't push for aggressive deadlines — user has 26 days, no need to rush
- ❌ Don't include author names or GitHub URLs in paper PDF (double-blind)
- ❌ Don't touch the parallel session's branch `chore/hf-dataset-upload` or the `hf_dataset/` / `kaggle_dataset/` directories — owned by another Claude Code session

---

## 13. Unverified / needs check

- [ ] CIKM 2026 Short Paper exact deadline (likely 6 June, verify on cikm2026.diag.uniroma1.it)
- [ ] Whether Gemini was successfully included as 3rd judge or dropped due to free-tier rate limits (check bg output / `tail /tmp/judge.log`)
- [ ] Final V2 ML router architecture (logistic regression vs gradient boosting — start with LR)
- [ ] User has Anthropic Claude API key (no, only GPT-4.1 confirmed)

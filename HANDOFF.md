# HANDOFF — Triple-Robustness RAG Paper (arXiv build; CIKM 2026 rejected)

**Last updated:** 2026-08-15

---

## 1. Project in one paragraph

Five RAG pipelines (vanilla, agentic, agentic+graph, graphrag, adaptive) compared on a synthetic 1,132-requirement DO-178C-style corpus (296 hop-stratified queries, 2×4,440 runs across two embedders) and a 200-query MuSiQue subset, with a dual-judge faithfulness protocol (GPT-5.4 + GPT-4.1). Paper: `paper/cikm/` — currently the **arXiv (nonacm) build**, 6 pages, title "A Triple-Robustness Analysis of Retrieval-Augmented Generation for Multi-Hop Requirements Traceability". CIKM 2026 short-paper decision expected ~Aug 7; if accepted, restore the anonymous CIKM format AND the GenAI disclosure (`sections/99-genai-disclosure.tex`, on disk but not \input) from git history — both mandatory there.

## 1b. CIKM 2026 short track — rejected (submission 3320)

Scores -1 / -1 / +1; metareview sided with the rejects. 764 submissions, 236 accepted (30.9%).
Single converging complaint: **experimental scope too thin for an empirical-study paper**
(2 embedders, 2 judges, 2 corpora, 1 GraphRAG implementation, "no multiple runs").

Two reviewer claims were factually wrong about the paper, and both were our presentation's fault:

- R1 asked for a control re-running the judge on *identical* answer-context pairs. That control
  already existed (test-retest κ=0.76; 11-week frozen-input κ=0.14/−0.05) but was buried in four
  unlabelled rows at the bottom of a resized table. Fixed 2026-08-15: Table 3 is now grouped
  "frozen input" vs "input changed by embedder swap", and §5.4 leads with the frozen-input block.
- R3 said the work "lacks multiple runs". The matrix has always been 3 seeds
  (296 q × 5 pipelines × 3 repeats = 4,440). It was simply never reported. Fixed 2026-08-15:
  across-seed spread now in §5.1 + §4 statistical protocol.

Free fixes landed 2026-08-15 (branch `fix/cikm-rejection-free`), no API spend:
abstract rewritten as prose (label checklist removed); intro opens on the traceability problem
instead of "typed link graphs"; contributions renumbered **C1–C5 in presentation order**
(old C2a→C2, C2b→C3, old C1→C1, old C3→C4, old C4→C5) — old labels are gone, do not reuse them;
new §3.3 "Queries and Gold Evidence" documents chain sampling, gold construction and its
limitation; corpus stats corrected (**30 modules, not 32** — the old number was wrong in the
paper AND in CLAUDE.md); 5 preprint citations upgraded to published versions (Search-R1→COLM
2025, LightRAG→Findings EMNLP 2025, RAGAS→EACL 2024 demo, ARES→NAACL 2024, MultiHop-RAG→COLM
2024); "Untested mitigations" added to Threats. Build: 6 pages, 0 overfull, 0 undefined refs.

Not yet done — needs money, see cost plan: cross-vendor judge, 3rd embedder, seed-variance
re-run of graph pipelines (blocked on dead Aura), GraphRAG mitigation arm, 2nd GraphRAG impl.

`results/gemini-third-v2.csv` is a **19-row pilot only** — not reportable, do not cite it.
`multi_judge.py` already implements a Gemini judge path (`GOOGLE_API_KEY`), so the cross-vendor
control is wiring, not new code.

### Post-rejection work in flight (started 2026-08-16)

Approved package ≈ $97 (tiers A3/B1/C1/D1/E2). Spend so far **≈ $33**.

| Phase | State | Artifacts |
|---|---|---|
| 0 prep | done | `scripts/judge/full_matrix_judge.py`; Gemini judge pinned in `multi_judge.py` |
| 1 full-matrix judging, GPT-4.1 leg | **done**, $30.87 | `results/main-v{2,3}-judged-full-gpt41.csv`, 4,440 rows each, 0 errors |
| 1 Gemini leg | **BLOCKED** — free-tier key | — |
| 2 flooding mitigation | done, ~$4 | `results/musique-mitigation-{rerank,cap}.jsonl` + `-scored.csv` |
| 3 third corpus (D1) | not started | |
| 4 third embedder (C1) | **BLOCKED** — Aura + embedder choice | |
| 5 second GraphRAG impl (E2) | **BLOCKED** — Aura | |

**Gemini key is FREE TIER.** `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, quotaValue **20/day**
for gemini-3.7-flash. The `serviceTier: "standard"` field in responses describes the request, NOT the
billing plan — do not read it as "billing enabled". Cross-vendor judging needs billing turned on for
the Google Cloud project. Judge model chosen: **gemini-3.7-flash, thinking ON, snapshot
`3.7-flash-08-2026`** ($0.75/$3.75 promo through 2026-12-31; measured 269 thought tokens/call ⇒
$17.95 for 8,880 rows). 3.6-flash cannot disable thinking at all (HTTP 400); 3.5-flash is older AND
3× dearer.

Full-matrix results (GPT-4.1, judged Aug — **new date, do NOT pool with May**):
overall faithful 0.933 (v2) / 0.917 (v3). GraphRAG hop-decline holds under both embedders
(p=3.9e-02 / 1.4e-06); **vanilla, the only non-expanding pipeline, is flat under both**
(p=0.16 / 0.99). On the identical 300 tuples GPT-4.1 vs its own May verdicts: κ=−0.046, +43pp
leniency — independently reproducing the −0.045 from `gpt41-drift-v2.csv`.

Mitigation control (answers reviewer 1's "no mitigation tested"): **neither variant works.**
Rerank walked nodes to top-5 → ctx precision 0.227→0.232, citation F1 +0.010 (p=0.34, n.s.).
Cap walk 30→10 / context 15→8 → ctx precision 0.194, F1 −0.126 (p=2.6e-11, harmful). Reading:
the synthesizer already filters the walk (C2), so upstream filtering is redundant and budget cuts
only destroy recall. Careful with metrics — MuSiQue has TWO context-precision definitions
(`is_supporting` paragraph flag vs the chain `expected_ids`); they differ ~2× and must not be mixed.

### Graph provenance gap (found 2026-08-15) — affects any graph re-run

The Aura instance was preloaded by the hackathon ETL and carried **more edges than the released
corpus annotates**. Re-running `graph_loader.py` on `data/synthetic/requirements.jsonl` yields
768 edges (references 623, verifies 104, derives_from 22, refines 17, **satisfies 2**), whereas
the chains behind our 296 queries use SATISFIES 114 times. Measured coverage of the released
corpus against the query chains: **91.0% of edges, 82.8% of chains** fully reconstructible. All
gold IDs do resolve (0 missing), so evaluation targets are exact either way.

Consequence: a fresh Aura + re-ETL gives a **sparser graph than the published graph-arm numbers
were produced on**. Graph-pipeline results will not reproduce exactly. Any paid re-run touching
graphrag / agentic-graph must either accept this or first recover the original edge set.
Disclosed in the paper's Reproducibility paragraph with the 91.0/82.8 figures.

`.env` `DATA_PATH` points at another machine (`/Users/suleakarsu/...`); pass
`--data-path data/synthetic/requirements.jsonl` to `graph_loader.py` or fix the var.

Venue thinking: scope complaints cannot be answered inside a 4-page short track. Target a full
or resource paper (SIGIR 2027 full, ~Jan 2027) or a journal (TOIS / IP&M). ECIR 2027 (Oct 2026)
is too tight for the expensive items.

## 2. Major correction (2026-07-31) — read before touching results

The original matrix logged `cited_ids` inconsistently: **vanilla and graphrag recorded retrieved-context IDs; agentic arms parsed the answer text.** ALCE metrics are answer-level, so all scored CSVs were regenerated with a uniform vocabulary-anchored answer parser (`scripts/rescore_citations.py`; parser in `eval_metrics.make_citation_parser`). Consequences:

- GraphRAG flips from worst (F1 0.20-0.22) to best/tied-best (0.52-0.65). The old "over-citation pathology" was context flooding: the walk fills 15 slots at context precision 0.12-0.23; the synthesizer cites ~5 IDs at 0.48-0.65.
- Old context-cited scored CSVs preserved in `results/deprecated/`. Do NOT quote pre-correction numbers (this includes README.md §results and the old HANDOFF tables).
- Paper reframed around the context-vs-citation measurement point (C2a).
- Router targets changed: 1-hop→vanilla, 2-hop→graphrag, 3+-hop→agentic-graph. V2 closes 59.4%/54.8% of the V1→oracle gap (local/Azure).

## 3. Controls beyond the main matrix (all committed on `fix/review-blockers`)

| Control | Artifacts | Result |
|---|---|---|
| MuSiQue distractor edges | `results/musique-distractor*.{jsonl,csv}`, `scripts/musique/distractor_control.py` | GraphRAG −0.02/−0.05/−0.09 F1, still beats vanilla in every stratum (p≤0.014). Win not a gold-edge artifact. |
| Judge replication batches (seed 43, judged 11 weeks after seed-42 originals) | `results/main-v{2,3}-judged-repl.csv`, `scripts/stats/replication_trends.py`, `results/stats-v3/replication_trends.csv` | GPT-5.4 hop-decline replicates (p=0.002 local / p<1e-4 Azure); GPT-4.1 drifted lenient (93-95% faithful), its own May trend gone. Report batches separately — never pool across judging dates. |
| Generator swap (GPT-4.1 synthesizes 332 v3 rows on frozen retrievals) | `results/genswap-*`, `scripts/judge/generator_swap.py` | Same architecture ordering, slightly higher F1. Dual-judging output: `results/genswap-judged.csv` — confirm it reached 332 rows. |
| Same-judge controls (May) | `results/retest-v2-gpt5.csv` | test-retest κ=0.76; embedder-swap κ=0.14 (41% flips); 11-week frozen-input κ=0.14. Stationarity rejected: cross-date agr 0.56 vs same-day floor 0.88, binomial p<1e-44. |
| GPT-4.1 same-tuple drift (Aug) | `results/gpt41-drift-{v2,v3}.csv`, `scripts/judge/gpt41_drift.py` | κ=−0.05/−0.00 vs own May verdicts on identical inputs; +41pp leniency. More embedder-stable judge is less time-stable. |

## 4. Environment

- `.venv` is BROKEN (Homebrew python@3.11 removed). Use **`.venv-judge`** (py3.14, uv-managed: openai, tqdm, dotenv, scipy, pandas, sklearn, statsmodels, matplotlib, tiktoken). Root `Makefile` points at it.
- **Neo4j Aura is DEAD** (hostname no longer resolves). Graph pipelines cannot re-run against Aura. MuSiQue walks are replicated locally from `data/musique/edges.jsonl` (see `distractor_control.py`); AeroSys graph re-runs would need a fresh instance + `graph_loader.py`.
- Azure keys in `.env` work. Prices verified Jul 2026: GPT-5.4 $2.50/$15 per 1M in/out; GPT-4.1 $2/$8. One judge call ≈ 900 tokens total. Full new-experiment spend this phase ≈ $12.
- Git: `gh` account kaanrkaraman; push to `mftnakrsu/rag-vs-agentic` WORKS. Commit with `--no-gpg-sign` (pinentry broken).

## 5. Paper build

```bash
cd paper/cikm && make          # pdflatex+bibtex → main.pdf (6 pp, arXiv build)
.venv-judge/bin/python scripts/tex/make_tables_triple.py   # regenerates tables
#   WARNING: overwrites tab_judges.tex, which carries HAND-EDITED rows
#   (MuSiQue row + same-judge controls block). Back it up first.
```

## 6. Open items

1. Confirm `results/genswap-judged.csv` reached 332 rows; optionally add a faithfulness sentence to §Threats (citation comparison already in paper).
2. PR from `fix/review-blockers` → rebase-merge to main (branch pushed).
3. CIKM notification ~Aug 7: camera-ready needs anonymous format + disclosure restored.
4. Fallbacks researched: ECIR 2027 short (Oct 2, 2026); SIGIR 2027 short (~late Jan 2027). WSDM 2027 has no short track.
5. Optional: cross-vendor judge (needs paid Gemini or Anthropic key); fold-nested V2 target mapping.

## 7. User preferences

- Turkish in chat, English in paper/code/commits. Direct, no hedging; user decides strategy (title, venue), you execute.
- NEVER add "Co-Authored-By: Claude" or similar to commits.
- Don't touch `hf_dataset/`, `kaggle_dataset/` (other session). Don't print `.env` values.

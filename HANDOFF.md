# HANDOFF — Triple-Robustness RAG Paper (arXiv build; CIKM 2026 rejected)

**Last updated:** 2026-08-16

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

### Post-rejection work (2026-08-16 → 08-21) — generation and judging COMPLETE

Approved package tiers A3/B1/C1/D1/E2. Spend **~$80 Azure + ~$29 Gemini**.

| Phase | State | Key artifacts |
|---|---|---|
| 0 prep | done | `scripts/judge/full_matrix_judge.py`, `scripts/judge/check_gemini_tier.py` |
| 1 GPT-4.1 full matrix | done, $30.87 | `results/main-v{2,3}-judged-full-gpt41.csv`, 4,440 each, 0 errors |
| 2 flooding mitigation | done, ~$4 | `results/musique-mitigation-{rerank,cap}*` — **both fail** |
| C3 power test | done, ~$5 | `results/musique-none-r{1,2}*` — **C3 refuted under GPT-4.1** |
| D1 third corpus (2Wiki) | done, $5.50 | `data/twowiki/`, `results/twowiki-*` |
| Local graph shim + bge-m3 | done, $0 | `graph_store_local.py`, `scripts/index_bge.py` |
| C1 third embedder | done, $22.36 | `results/main-v4*` (1,480 rows, 1 seed) |
| E2 PPR traversal | done, $2.47 | `results/main-v3-ppr-*` |
| Cross-vendor judging | done, ~$13 | `results/*-judged-gemini.csv`, `*-judged.csv`, `twowiki-judged.csv` |
| Paper rewrite (PR #50, #51) | done, $0 | C1–C4 rewritten; 7 pages, 0 overfull, 0 undefined refs |

**Aura is retired for good.** `GRAPH_BACKEND=local` uses `graph_store_local.py`, which traverses the
corpus' own link annotations — identical to what `graph_loader.py` would load into a fresh instance,
minus the 48 dangling links it silently drops (768 annotated → **720 real edges**). The neo4j import
is lazy, so pipelines run without the package. This also fixes the reproducibility gap: the graph is
now derivable from the released corpus.

**Gemini judge**: `gemini-3.7-flash`, snapshot `3.7-flash-08-2026`, thinking ON (`thinkingBudget:-1`).
Measured 1,726 in / 269 out per judge call ⇒ $0.00230. Billing IS live on the new key (project
710802299794); preflight `scripts/judge/check_gemini_tier.py` verifies this rather than assuming.
`gemini-2.5-flash` and `2.5-flash-lite` are **404, retired** — do not quote them as cheap fallbacks.
Google Cloud in TR is **postpay**; a deposit is not a spend ceiling, only a quota override is.

### Findings that change the paper

1. **C2 is now the strongest claim.** Flooding→filtering replicates across 3 corpora, 3 embedders,
   and 2 traversals, and survives 2 attempted mitigations. 2Wiki is sharpest: ctx precision 0.230 →
   citation precision 0.975 (4.2x).
2. **C3 does not replicate — withdrawn and rewritten (PR #51).** At matched power the decline is
   significant on both Wikipedia corpora under both vendors: MuSiQue 3 seeds n=600
   (gpt41 p=1.1e-03, gemini p=1.2e-03), 2Wiki n=1,200 (gpt41 p=5.0e-02, gemini p=4.8e-06). The
   published "no collapse on Wikipedia" was 67 rows/stratum. GPT-5.4 leg still not retested.
3. **Replacement claim is a test, not a pattern.** Vanilla's 1→3+-hop drop is −1.5pp on DO-178C and
   +1.1pp on 2Wiki; expanding pipelines drop 6.3pp and 6.7pp. Logistic hop×expansion interaction:
   b=−0.599 p=1.0e-07 pooled DO-178C (n=10,360), b=−0.286 p=0.27 on 2Wiki (n=1,200, same sign).
   Under Gemini the DO-178C matrix saturates near 1.00, vanilla itself picks up a slope (b=−0.729,
   p=0.012) and the interaction is no longer separable — ranking survives, resolution does not.
4. **Mitigation is a clean negative.** Rerank: F1 +0.010 (p=0.34). Budget cap: F1 −0.126
   (p=2.6e-11) and *lower* context precision. Consistent with C2 — the synthesizer already filters.
5. **PPR ≈ walk_2hop.** ctx prec 0.131 vs 0.129, enrichment 3.9x vs 3.8x. F1 +0.016 with Cliff's
   delta +0.036 — the joint criterion rejects it. C2 is not an artefact of our walk.
6. **GPT-4.1 drift replicated independently.** Full-matrix Aug vs May on identical 300 tuples:
   κ=−0.046, +43pp leniency, matching the −0.045 from `gpt41-drift-v2.csv`.
7. **Judge leniency is a judge×corpus property, not a judge property.** Gemini is far more lenient
   than GPT-4.1 on DO-178C (0.98–0.99 vs 0.93–0.95, McNemar p<1e-9), indistinguishable on the
   capped MuSiQue arm (0.875 vs 0.880, p=1.00), and **stricter** on 2Wiki (0.888 vs 0.914,
   p=6.2e-03). Do not calibrate a judge once and reuse the offset.
8. **Prevalence paradox visible inside one judge pair.** Across the 8 cross-vendor settings raw
   agreement moves 0.82→0.94 and AC1 0.77→0.94, but κ swings 0.03→0.44, ordered by distance from
   the ceiling. Never report κ alone on high-prevalence faithfulness cells.

**Judging dates are not poolable.** Aug verdicts (full matrix, Gemini pass) must never be merged
with the May batches. Every judged CSV carries a `judged_on` column. The Gemini legs of
musique-extra / rerank / cap / 2Wiki ran 08-21, one day after their GPT-4.1 legs, on frozen stored
strings; `scripts/judge/merge_judges.py` pairs them by (query, pipeline, repeat) and keeps both
dates. The paper discloses this in §Experimental Setup.

**MuSiQue has TWO context-precision definitions** — `is_supporting` paragraph flag vs chain
`expected_ids`. They differ ~2x. Never mix them; the paper uses the chain-gold one.

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

## 3b. Repo layout (reorganised 2026-08-21, PR #54)

Library code lives in the **`aerorag/`** package; the repository root holds only
config and docs. Entry points run as modules from the root:

```
python -m aerorag.build_index
python -m aerorag.compare --limit 3 --no-local-rerank
python -m aerorag.vanilla_rag "..."      # also graph_rag, agentic_rag
```

`scripts/` is unchanged — its files compute the repo root from their own
location, so nothing there needed path edits, only `from aerorag.x import`.

Deleted in the same pass (all recoverable from git history): `stats.py` and
`rerun_errors.py` (dead, zero importers), `ui_app.py` + `.streamlit/` (stale
Streamlit demo, knew only 2 of 5 pipelines), `figures/` (byte-identical copy of
`paper/cikm/figures/`) and `figures-v3/` (unreferenced), `docs/plan.md` and
`docs/adversarial-review.html` (planning artefacts for the rejected version).
Untracked and gone for good: the May Overleaf zips, `paper/arxiv-source.zip`,
`paper/main-authors.pdf` (superseded by `paper/main.pdf`), and
`results/genswap-judge-input.csv`. `data/agent.db` (1 GB) was cleared from disk;
it is a regenerable checkpointer.

**One real bug surfaced by the move**: `graph_store_local.DEFAULT_CORPUS` was
`Path(__file__).parent / "data"`, which resolved to `aerorag/data/` after the
move. Now `parents[1]`. Self-check still reports 720 edges.

## 4. Environment

- `.venv` is BROKEN (Homebrew python@3.11 removed). Use **`.venv-judge`** (py3.14, uv-managed: openai, tqdm, dotenv, scipy, pandas, sklearn, statsmodels, matplotlib, tiktoken). Root `Makefile` points at it.
- **Neo4j Aura is DEAD** (hostname no longer resolves). Graph pipelines cannot re-run against Aura. MuSiQue walks are replicated locally from `data/musique/edges.jsonl` (see `distractor_control.py`); AeroSys graph re-runs would need a fresh instance + `graph_loader.py`.
- Azure keys in `.env` work. Prices verified Jul 2026: GPT-5.4 $2.50/$15 per 1M in/out; GPT-4.1 $2/$8. One judge call ≈ 900 tokens total. Full new-experiment spend this phase ≈ $12.
- Git: `gh` account kaanrkaraman; push to `mftnakrsu/rag-vs-agentic` WORKS. Commit with `--no-gpg-sign` (pinentry broken).

## 5. Paper build

```bash
cd paper/cikm && make          # pdflatex+bibtex → main.pdf (7 pp, arXiv build)
.venv-judge/bin/python scripts/tex/make_tables_triple.py   # regenerates tables
#   WARNING: overwrites tab_judges.tex, which carries HAND-EDITED rows
#   (same-judge controls block + the 8-row cross-vendor block). Back it up first.
```

## 6. Open items

1. **Title is stale — user's call.** Still "A Triple-Robustness Analysis" while the study now varies
   four axes (embedder, corpus, traversal, judge). The intro already says "multi-axis robustness".
2. **Rotate `GOOGLE_API_KEY`** — the key was pasted into a chat transcript on 2026-08-20.
3. Optional, unpriced: GPT-5.4 leg of the C3 test (the original corpus-conditional claim rested on
   it, never re-run at full power); LightRAG as a named third-party GraphRAG system (~$5, needs a
   separate venv — its pin downgrades `websockets` 17→16).
4. Venue: ECIR 2027 short (Oct 2, 2026); SIGIR 2027 short (~late Jan 2027). WSDM 2027 has no short track.
5. `scripts/tex/make_tables_triple.py` has not been taught the new tab_judges rows — regenerating
   tables will drop them.

## 7. User preferences

- Turkish in chat, English in paper/code/commits. Direct, no hedging; user decides strategy (title, venue), you execute.
- NEVER add "Co-Authored-By: Claude" or similar to commits.
- Don't touch `hf_dataset/`, `kaggle_dataset/` (other session). Don't print `.env` values.

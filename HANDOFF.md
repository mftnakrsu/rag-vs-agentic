# HANDOFF — Triple-Robustness RAG Paper (arXiv build; CIKM 2026 decision pending)

**Last updated:** 2026-08-01

---

## 1. Project in one paragraph

Five RAG pipelines (vanilla, agentic, agentic+graph, graphrag, adaptive) compared on a synthetic 1,132-requirement DO-178C-style corpus (296 hop-stratified queries, 2×4,440 runs across two embedders) and a 200-query MuSiQue subset, with a dual-judge faithfulness protocol (GPT-5.4 + GPT-4.1). Paper: `paper/cikm/` — currently the **arXiv (nonacm) build**, 6 pages, title "A Triple-Robustness Analysis of Retrieval-Augmented Generation for Multi-Hop Requirements Traceability". CIKM 2026 short-paper decision expected ~Aug 7; if accepted, restore the anonymous CIKM format AND the GenAI disclosure (`sections/99-genai-disclosure.tex`, on disk but not \input) from git history — both mandatory there.

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
| Same-judge controls (May) | `results/retest-v2-gpt5.csv` | test-retest κ=0.76; embedder-swap κ=0.14 (41% flips); 11-week frozen-input κ=0.14. |

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

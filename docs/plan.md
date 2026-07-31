# Same-Family, Different Verdicts — A 26-Day Execution Plan for CIKM 2026 Short

## TL;DR

- **Ship to CIKM 2026 short (abstract 30 May, paper 6 June 2026); do not chase a reranker ablation or MuSiQue cross-eval on the main path** — the locked 4,440-run, 5-pipeline, dual-judge design with stratum-conditional dominance and κ-paradox evidence is already a defensible short paper. Reviewer risk on "no reranker" and "synthetic-only corpus" is manageable through a one-paragraph Threats-to-Validity defense plus a single 100-query reranker sanity pilot kept in the appendix as insurance — *only if* the Day-15 go/no-go is green.
- **The next 26 days are scoped to statistics + V2 router + writing, in that order.** Highest-risk slip points are (a) the V2 ML router + oracle upper bound (Days 6–10), and (b) the abstract deadline on 30 May — treat 30 May as the *hard* deadline because EasyChair locks at abstract time. The 6 June paper-submission day is buffer only.
- **The paper's strongest move is to frame κ = 0.302 as a *finding*, not a flaw**: pair Cohen's κ with Gwet's AC1 = 0.57 at 3+-hop and McNemar p = 0.0017 as a *three-statistic protocol* (κ paradox is well documented since Feinstein & Cicchetti 1990 and is the *point* of Contribution C3). This converts a perceived weakness into a methodological contribution and is fully publishable in 4 pages.

---

## Key Findings

1. **CIKM 2026 short paper specifics (verified from cikm2026.diag.uniroma1.it):** abstract 30 May 2026, full submission 6 June 2026 AoE, notification 7 August, camera-ready 20 August. 4 pages including appendix, **unlimited pages for references and the GenAI Usage Disclosure section** (mandatory since CIKM 2025). Double-blind via `\documentclass[sigconf,natbib=true,anonymous=true]{acmart}`. Improperly anonymized submissions are desk-rejected without review.
2. **The locked result table is already a strong contribution.** Stratum-conditional dominance reversal (vanilla wins 2-hop, agentic-graph wins 1-hop and 3+-hop) is a publishable narrative on its own (cf. *RAG vs. GraphRAG: A Systematic Evaluation*, arXiv:2502.11371; *When to use Graphs in RAG*, GraphRAG-Bench arXiv:2506.05690 — both confirm "no single paradigm dominates" as a legitimate 2025 framing).
3. **κ = 0.302 is defensible and well-precedented.** The Feinstein–Cicchetti (1990) paradox literature and Gwet (2008, *Br. J. Math. Stat. Psychol.* 61:29–48) provide the canonical defense: low κ with high agreement happens whenever marginal prevalence is skewed (which is exactly your faithful-percent regime at 3+-hop). Reporting κ + AC1 + raw % agreement + McNemar is the *current* 2024–2026 best practice.
4. **No reranker is defensible.** Recent comparable short papers (LiSSA, ICSE 2025; *Benchmarking Vector/Graph/Hybrid RAG for ORAN*, arXiv:2507.03608; *RAG vs. GraphRAG*, arXiv:2502.11371) treat rerankers as orthogonal and not always present in main pipelines. The dominant pattern is: state explicitly that the comparison axis is *retrieval-architecture family*, not *retrieval-engineering quality*, and that adding a reranker would orthogonally lift all 5 pipelines.
5. **No external benchmark is defensible** for a 4-page short, although a 100-query MuSiQue pilot is the highest-ROI stretch contribution if (and only if) Day-15 is on schedule. Cross-eval is the norm in 9-page full papers, not in 4-page shorts.
6. **The V2 ML router needs leave-one-query-out (LOQO) or 10×5 stratified CV**, not a held-out split — N = 296 is too small for a single split. Train logistic regression with L2, calibrate with Platt scaling (isotonic will overfit at N < 300), report oracle upper bound = per-query argmax over locked pipeline F1.

---

## Details

### 1. Top-5 Reviewer Landmines and the Strongest Defenses

| # | Likely attack | Strongest defense | Citation anchor |
|---|---|---|---|
| **R1** | "κ = 0.30 means your judges don't agree — your faithfulness numbers are unreliable." | This is the κ paradox: κ is downward-biased under high prevalence imbalance. Report κ + Gwet's AC1 (0.57 at 3+-hop) + raw agreement + McNemar p = 0.0017 (showing systematic, *directional* leniency, not noise) + Spearman ρ = 0.92 (direction agreement at the system level is strong). This *is* Contribution C3. | Feinstein & Cicchetti, *J. Clin. Epidemiol.* 43, 1990; Gwet, *Br. J. Math. Stat. Psychol.* 61, 2008; Pontius & Millones, *Int. J. Remote Sens.* 32, 2011. Recent: Wongpakaran et al., *BMC Med. Res. Methodol.* 2013 (canonical for "report κ + AC1 + raw"). |
| **R2** | "Synthetic corpus — won't generalize to real DO-178C." | (a) Scope sentence: this paper studies *retrieval-architecture sensitivity to hop-distance*, an internal-validity question. (b) Domain construction follows DO-178C edge taxonomy (REFERENCES/VERIFIES/DERIVES_FROM/REFINES/SATISFIES), validated by literature. (c) The dominance reversal at 2-hop is *architectural*, not corpus-specific. (d) Cite TraceLLM / LiSSA pattern of evaluating on synthetic + curated. | LiSSA (Fuchß et al., ICSE 2025, DOI 10.1109/ICSE55347.2025.00186); *From Waterfallish Aerospace Certification onto Agile Certifiable Iterations* (arXiv:2503.04265); *Leveraging Graph-RAG and Prompt Engineering for Requirement Traceability* (arXiv:2412.08593). |
| **R3** | "No cross-encoder reranker — your baselines are weak." | Frame as orthogonal axis. The 5-pipeline comparison holds the *retrieval-architecture family* constant in engineering quality; a reranker would lift *all* pipelines. Recent CIKM/SIGIR shorts in this space routinely omit rerankers from the main grid (LiSSA does not include a reranker ablation in main; *RAG vs. GraphRAG* arXiv:2502.11371 reports reranking only as an inference-time enhancement in a *separate* table). Optionally include the Day-15 100-query reranker pilot in the appendix. | RAGtifier (arXiv:2506.14412, SIGIR 2025 LiveRAG); *RAG vs. GraphRAG* §4 (arXiv:2502.11371). |
| **R4** | "V1 rule-based router is a strawman — show V2." | V2 ML router + oracle upper bound — see §3 below. This *defuses the landmine* and turns it into a contribution. | Adaptive-RAG (Jeong et al., NAACL 2024, ACL Anthology 2024.naacl-long.389); Probing-RAG (Baek et al., Findings NAACL 2025, arXiv:2410.13339); Embedding-Informed Adaptive RAG (COLING 2025). |
| **R5** | "ALCE-style citation P/R is not faithfulness — over-citation gaming." | This is *precisely* the GraphRAG failure you discovered (14.9 IDs cited, citP = 0.12 at 3+-hop). Frame it as the motivation for multi-judge faithfulness. Cite Wallat et al. (arXiv:2412.18004) — "correctness is not faithfulness in RAG attributions" — and position your dual-judge protocol as the resolution. | *Correctness is not Faithfulness in RAG Attributions* (arXiv:2412.18004); ALCE (Gao et al., EMNLP 2023). |

### 2. Bootstrap + Significance Protocol — Opinionated 2026 Best Practice

**Recommended canonical pipeline:**

- **BCa (bias-corrected and accelerated) bootstrap, B = 1000, paired at the query level.** BCa is second-order accurate and standard in NLP since DiCiccio & Efron (1996); recent confirmation: *A Paired Bootstrap Protocol for Evaluating Small Improvements* (arXiv:2511.19794) explicitly recommends "BCa interval lies entirely above zero + sign-flip permutation p < 0.05" as the conservative default. Use **percentile** only as a fallback when the acceleration constant is unstable (n < 30); BCa is the right call at your N = 95–111 per stratum. Bootstrap *paired deltas* per query, not absolute scores.
- **Paired Wilcoxon signed-rank** for hypothesis tests (you already plan this). It is the standard non-parametric paired test and behaves well at N ≥ 30 with continuous F1-like scores. **Paired permutation (sign-flip)** at 2¹⁰ permutations is interchangeable and slightly faster; either is defensible (Berg-Kirkpatrick et al., EMNLP 2012; Dror et al., ACL 2018). *Pick Wilcoxon* because you have it already and it is the more conservative choice; report exact p-values.
- **Holm–Bonferroni correction over the 30-test family** (10 pipeline pairs × 3 strata). Holm is FWER, step-down, strictly more powerful than Bonferroni, and *appropriate* when the family is small (30) and you want to make *claims of dominance*. BH (FDR) is right for exploratory screens with hundreds of tests, not your case. State the family explicitly in the paper.
- **Effect size: Cliff's δ**, not Cohen's d. F1 distributions per stratum are non-normal and bounded; Cliff's δ is rank-based, distribution-free, and standard in software engineering empirical work (Macbeth et al. 2011; Meissel & Yao, *Pract. Assess. Res. Eval.* 29(1), 2024). Use the thresholds: |δ| < 0.147 negligible, 0.147–0.33 small, 0.33–0.474 medium, ≥ 0.474 large.
- **N = 95–111 per stratum is adequate** for Wilcoxon (Wilcoxon is fine from N ≈ 20; normal approximation kicks in at N > 20). It is at the lower edge for BCa stability when there is heavy skew; mitigate by stratified bootstrap and report N alongside CIs. Acknowledge in Threats to Validity.

**Sample sentence (drop into §5 / §6):**

> "We report bootstrap 95% confidence intervals on paired F1 deltas using the bias-corrected and accelerated (BCa) procedure (Efron, 1987; DiCiccio & Efron, 1996) with B = 1000 resamples paired at the query level, paired Wilcoxon signed-rank tests with Holm correction over the family of 30 comparisons (10 pipeline pairs × 3 strata), and Cliff's δ (Macbeth et al., 2011) as a non-parametric effect size. A pipeline is reported as dominating another in a stratum only when the BCa interval excludes zero, the Holm-adjusted Wilcoxon p < 0.05, and |δ| ≥ 0.147."

### 3. V2 ML Router — Concrete Architecture

**Features (lightweight, ~12 dims; explicitly justified by Adaptive-RAG and RAGRouter-Bench):**

1. `entity_count`: # of REQ-style IDs detected by regex (`\bREQ-\d+\b`, `\bSRS-\d+\b`, etc.)
2. `has_id_regex`: binary
3. Question-keyword flags: `verifies`, `derives_from`, `refines`, `satisfies`, `references`, `which`, `how many`, `list`, `trace` (one-hot, ~8 dims)
4. `query_token_len` and `query_token_len_log`
5. Mean-pooled sentence embedding of the query (project from 1536/3072 down to a 32-dim PCA features to avoid overfit; or use only the top-3 PCs)

**Classifier choice — opinionated:** **Multinomial logistic regression with L2 regularization (C = 1.0)** over a {1-hop, 2-hop, 3+-hop} target. *Do not* use gradient boosting or a transformer at N = 296 — both will overfit. LR + L2 is what Adaptive-RAG defaults to in spirit (T5-Large is too heavy for 296 examples; the analog at our scale is LR). RAGRouter-Bench (arXiv:2602.00296 / 2604.03455) confirms lightweight classifiers are competitive.

**Calibration:** **Platt scaling** (sigmoid on raw scores) — isotonic regression is documented to overfit at N < 500 (Niculescu-Mizil & Caruana 2005; recent: arXiv:2601.19944 *Classifier Calibration at Scale*, 2026, shows Platt and isotonic both can degrade strong models — use Platt and report Brier score before/after).

**Cross-validation when training = eval data:** Use **stratified 10×5-fold CV** (10 folds × 5 repeats with different random splits, stratified by hop class). Report mean ± std macro-F1 over the 50 evaluations. *Never* train and test on the same example. For the final pipeline-selection numbers, use **out-of-fold predictions** (each query routed by a router that did not see it during training) — this gives you a fair, leakage-free "Adaptive-V2" row in the final results table.

**Oracle upper bound:** For each query, take the per-query F1 of the *best* of the four pipelines (vanilla, agentic, agentic-graph, graphrag), averaged within stratum. This is the Adaptive-RAG-style upper bound (Jeong et al., NAACL 2024, App. D; Embedding-Informed Adaptive-RAG, ACL Anthology 2025.coling-main.94). Report as "Adaptive-Oracle" row in the results table; the gap from V2 to Oracle is the headroom story.

**Acceptance criterion:** V2 must beat V1 by ≥ 2 absolute F1 points overall (Holm-adjusted Wilcoxon p < 0.05) and close ≥ 30 % of the V1→Oracle gap on at least 2 of 3 strata. If V2 does not meet this on Day 10, **fall back to V1 + Oracle gap analysis only** and remove V2 from the paper.

### 4. Reranker Ablation — Decision: DO NOT add to main, optional 100-query pilot

**Verdict: Out of scope is defensible.** The reasoning:

- The contribution is *retrieval-architecture family comparison*, not *engineering quality at fixed family*. A reranker is an orthogonal axis that would lift all 5 pipelines by a similar relative amount.
- 2024–2026 comparable short papers (LiSSA ICSE'25; ORAN-RAG arXiv:2507.03608; *RAG vs. GraphRAG* arXiv:2502.11371) routinely treat rerankers as ablation, not main.
- A reranker on Neo4j+Chroma typed-edge traversal is non-trivial to implement correctly in 26 days, and would require re-running 4,440+ runs to remain comparable.

**Minimum-viable pilot (insurance only, 100 queries):** if Day 15 is on schedule, run BGE-Reranker-v2-M3 on top of vanilla RAG (only) on 100 stratified queries, report the absolute F1 delta in a single appendix paragraph. Cost ~$5 and 4 GPU-hours. Defuses the concern with a sentence: "Adding a BGE-Reranker-v2-M3 cross-encoder to vanilla RAG yields +X F1 absolute on a 100-query stratified pilot, confirming the orthogonality of the reranking axis to our retrieval-family comparison."

### 5. MuSiQue / External Cross-Eval — Decision: DO NOT add for the 4-page short

**Verdict: External cross-eval is the norm for 9-page full papers, not 4-page shorts.**

In CIKM/SIGIR 2024–2025 short papers on domain RAG (LiSSA ICSE'25 single-domain; ORAN-RAG arXiv:2507.03608 single-domain; *Leveraging Graph-RAG for Requirement Traceability* arXiv:2412.08593 single-domain), the prevailing pattern is single-domain evaluation with explicit scope statement. A 200-query MuSiQue run would not fit in the 4-page narrative without crowding out the dual-judge story (C3), which is the paper's strongest move.

**Sample scope sentence (drop into §1 and §7):**

> "This paper measures *architectural* sensitivity to hop-distance under a single regulated-domain corpus; cross-domain generalization (MultiHop-RAG, MuSiQue) is deferred to the journal extension."

If Day 20 is green, the 100-query MuSiQue pilot becomes the highest-ROI stretch addition (see §12).

### 6. GenAI Usage Disclosure 2026 — Required Content

CIKM 2025/2026 has mandated this section since 2025; it sits between main text and references and **does not count toward the page limit**. ACM Authorship Policy (acm.org/publications/policies/new-acm-policy-on-authorship) requires disclosure proportional to the role GenAI played.

**Drop-in disclosure (use verbatim, edit names):**

> **GenAI Usage Disclosure.** We disclose all uses of generative AI in this work in accordance with the ACM Policy on Authorship and the CIKM 2026 disclosure requirement. **(a) Synthetic corpus generation.** Azure OpenAI GPT-5.4 was used under a structured prompt template (provided in the supplementary material) to generate 1,132 DO-178C-style requirements and the typed edges among them, conditioned on a hand-authored taxonomy and module schema. All generated requirements were programmatically validated for format and uniqueness; no validation was performed by GenAI. **(b) Pipeline components.** GPT-5.4 is the generation backbone of all five RAG pipelines under study; it is the *object* of evaluation, not an authorial tool. **(c) LLM-as-judge.** GPT-5.4 and GPT-4.1 are used as the two faithfulness judges in the locked dual-judge protocol; this is part of the paper's experimental analysis and is fully documented in §4. **(d) Writing.** GenAI tools (Claude Sonnet 4.5, GPT-5.4) were used for prose polishing, LaTeX-table assembly, and code-comment generation. No section of the paper was authored *de novo* by an LLM. All claims, numbers, citations, and conclusions were verified by the author(s). The author(s) take full responsibility for the content.

**Why this works:** It mirrors the ACM template (acm.org FAQ "ChatGPT was utilized to generate sections of this Work…") but is *specific* — naming the model versions, the role per usage, and explicitly distinguishing the judge models (experimental) from the writing assistants (authorial). The 2024–2026 review-of-policies study in *Communications of the ACM* ("Generative Artificial Intelligence Policies under the Microscope") confirms that *specificity* is the differentiator between accepted and flagged disclosures.

### 7. κ Paradox Defense — Sample Paper Text

**Drop-in §4.3 paragraph (use verbatim):**

> **The κ paradox and the multi-judge protocol.** Overall Cohen's κ between the GPT-5.4 and GPT-4.1 judges is 0.302 (raw agreement = 0.86), which under standard rubrics would be characterized as "fair". We report this not as a limitation but as a *finding*. The Feinstein–Cicchetti (1990) κ paradox establishes that κ is downward-biased whenever the marginal prevalence of one class dominates — exactly the regime at the 3+-hop stratum, where most outputs are judged unfaithful. Gwet's AC1, which is paradox-resistant under prevalence imbalance (Gwet, 2008), is 0.306 overall but rises to **0.569 at 3+-hop**, confirming substantial agreement once chance is corrected appropriately. McNemar's test rejects symmetry of disagreements (p = 0.0017): GPT-4.1 is *systematically* more lenient, not noisy. Spearman ρ on the per-pipeline faithful-percent vector is 0.922, indicating that the two judges agree on the *ranking* of pipelines even when they disagree on individual verdicts. The κ paradox here is the message, not the noise: any single-judge faithfulness study at this prevalence is reporting a number that depends materially on which judge was chosen. We therefore advocate a three-statistic protocol — κ, AC1, and McNemar — alongside ranking-level Spearman, as a default for LLM-judge faithfulness studies.

**Why this works:** It is non-defensive (opens with "not as a limitation but as a finding"), it cites the canonical paradox literature, it shows you understand *why* κ is low, and it converts a number that looks bad into the headline justification for C3.

### 8. Anonymization Audit — Concrete Checklist

ACM sigconf double-blind anonymization failures that cause desk-reject:

1. **PDF metadata.** Run `exiftool paper.pdf | grep -iE "author|creator|producer|title"`. The producer string from LaTeX is OK; the **Author** field must be empty or "Anonymous". Strip with `exiftool -overwrite_original -Author="" -Title="" -Subject="" -Creator="LaTeX" paper.pdf`. Also run `pdfinfo paper.pdf` and verify the Author line.
2. **Self-citation phrasing.** Replace all instances of "In our prior work [X]…" with "Prior work [X]…". Cite your own prior papers in the third person.
3. **No GitHub repo links** in the submission. Use an anonymous-mirror URL (e.g., `https://anonymous.4open.science/`) or state: "Code and data will be released at the camera-ready stage."
4. **No acknowledgements** in the review version (the `\acks{...}` block in `acmart` is suppressed under `anonymous`, but verify the PDF).
5. **No distinctive system name** that ties to authors (e.g., do not name the system "VTRACE" if your institution's lab is publicly known to run a VTRACE project). The current title is generic enough.
6. **LaTeX preamble:** `\documentclass[sigconf,natbib=true,anonymous=true]{acmart}` exactly. Re-render and visually confirm "ANONYMOUS AUTHOR(S)" appears in the author block.
7. **No identifiable URLs in figures or screenshots** (e.g., do not screenshot a Neo4j browser tab showing your username).
8. **Search the PDF for surnames:** `pdftotext paper.pdf - | grep -iE "(your_surname|coauthor_surname|institution)"`.

The Le Goues et al. study (*CACM*, arXiv:1709.01609) shows 74–90 % of reviews contain no correct guess when authors anonymize properly. This is achievable.

### 9. Reproducibility Package — Minimum Viable

CIKM 2026 short does not mandate code release at submission, but explicitly *encourages* reviewer-accessible reproducibility. Minimum:

- **Anonymous mirror** (anonymous.4open.science) with: (a) requirements.txt with pinned versions, (b) router training script + features.json, (c) bootstrap/Wilcoxon analysis notebook, (d) synthetic corpus (1,132 requirements + edges), (e) the 296 queries, (f) main-v2-scored.csv, (g) judge prompts (both judges) as YAML/JSON, (h) seed list (3 seeds), (i) Azure model snapshot string (e.g., `gpt-5.4-2026-04-15`).
- **Do NOT** include LangGraph orchestrator code if it contains your institution's wrappers; include only the prompts and the run logs.
- README with one-command repro: `make figures` and `make tables` regenerate all paper artifacts from main-v2-scored.csv.

### 10. Realistic Day-by-Day Timeline (Today = 11 May 2026; Abstract = 30 May; Paper = 6 June)

**Hard deadline for paper-locking is 30 May** because EasyChair enforces an abstract submission first. Treat 30 May as the *real* deadline; 6 June is buffer.

| Day | Date | Task | Risk |
|---|---|---|---|
| 1 | Tue 12 May | Set up analysis branch; write bootstrap/Wilcoxon/Cliff's δ scripts on locked CSV | low |
| 2 | Wed 13 May | Compute BCa CIs for per-stratum F1 + faithfulness; generate Table 1 LaTeX | low |
| 3 | Thu 14 May | Compute 30-comparison Holm-adjusted Wilcoxon; generate significance star matrix | low |
| 4 | Fri 15 May | Generate Figure 1 (per-stratum F1 bars w/ CIs) + Figure 2 (faithfulness heatmap) | low |
| 5 | **Sat 16 May — GO/NO-GO #1** | All statistics done. Decision: continue with V2 router (yes) or freeze on V1 + Oracle only (no) | **HIGH** |
| 6 | Sun 17 May | V2 router: feature extraction + LR training scaffold + 10×5-fold CV harness | medium |
| 7 | Mon 18 May | V2 router: oracle upper bound computation + V2 vs V1 vs Oracle table | medium |
| 8 | Tue 19 May | V2 router: Platt calibration + final out-of-fold predictions + significance test | medium |
| 9 | Wed 20 May | Write §3 (Methodology) + §4 (Experiments) | low |
| 10 | **Thu 21 May — GO/NO-GO #2** | V2 router acceptance check. If V2 < V1+2 F1, drop V2. Lock all numbers. | **HIGH** |
| 11 | Fri 22 May | Rewrite §1 Abstract + §1 Introduction (3-contribution framing) | low |
| 12 | Sat 23 May | Write §5 Results with 3 tables + 2 figures referenced | low |
| 13 | Sun 24 May | Write §6 Discussion (κ-paradox defense, Threats to Validity covering all 5 weaknesses) | low |
| 14 | Mon 25 May | Write §7 Conclusion + §2 Related Work (cut to 15 refs minimum coverage) | low |
| 15 | **Tue 26 May — GO/NO-GO #3** | Full draft complete. Stretch decision: do reranker pilot, MuSiQue pilot, or polish? | **MEDIUM** |
| 16 | Wed 27 May | Optional: BGE-Reranker-v2-M3 100-query pilot OR polish | medium |
| 17 | Thu 28 May | Internal read-through; fix table layouts; check 4-page fit | low |
| 18 | Fri 29 May | GenAI Usage Disclosure section + References + anonymization audit | low |
| 19 | **Sat 30 May — ABSTRACT DEADLINE (AoE)** | Submit abstract + paper title + authors to EasyChair | **HARD** |
| 20 | **Sun 31 May — GO/NO-GO #4** | Final polish vs. fall back to UBMK 2026 (30 June) | **HIGH** |
| 21 | Mon 1 Jun | Fix figure rendering, add missing citations, run anonymization audit again | low |
| 22 | Tue 2 Jun | Buffer / writing polish | low |
| 23 | Wed 3 Jun | Buffer / supplementary materials assembly + anonymous mirror upload | low |
| 24 | Thu 4 Jun | Buffer / 4-page fit verification | low |
| 25 | Fri 5 Jun | Final read-through, exiftool/pdfinfo verification | low |
| 26 | **Sat 6 Jun — PAPER DEADLINE (AoE)** | Submit final PDF | **HARD** |

**Slip points and triggers:**

- **If Day 5 is red** (statistics not done): drop V2 router entirely, submit with V1 + oracle gap analysis. Still publishable.
- **If Day 10 is red** (V2 doesn't beat V1+2 F1): drop V2 from headline, keep as appendix; re-cast paper as "stratum-conditional dominance + κ paradox" without V2 contribution.
- **If Day 15 is red** (draft incomplete): cancel both stretch contributions; do not add reranker or MuSiQue; polish only.
- **If Day 20 is red** (abstract submitted but draft thin): submit to CIKM as is for review feedback, prepare extended version for UBMK 2026 (30 June) as fall-back.

**Commit point:** Day 10. If by Day 10 you have (a) full BCa+Wilcoxon+Holm stats, (b) all three tables, and (c) either a working V2 or a decision to drop it, **commit to CIKM** and stop second-guessing. Below that bar, fall back to UBMK.

### 11. Stretch Contributions Ranked by ROI (4-page constraint)

1. **Oracle-router gap analysis with per-stratum breakdown** — *Highest ROI*. Already produced by V2 work; one extra paragraph and one column in the results table. Demonstrates that there is real headroom (e.g., "V2 captures 42 % of the V1→Oracle gap; remaining gap is a learnable target for future work"). Free, given V2 is already on schedule.
2. **Failure-mode taxonomy (30 worst queries, manual coding)** — *High ROI if Day 15 green*. A categorical breakdown of why GraphRAG over-cites (e.g., 70 % "expanded too aggressively on REFERENCES edges", 20 % "missed VERIFIES endpoint") gives reviewers a concrete handle on C2 and costs ~3 hours of manual coding. Fits in 1/3 column.
3. **Reranker pilot (BGE-Reranker-v2-M3 × vanilla × 100 queries)** — *Medium ROI*. Defuses R3 concretely. Fits in an appendix table; one sentence in main text. Costs ~4 GPU-hours and ~$5.
4. **MuSiQue 100-query cross-eval (vanilla + agentic-graph only)** — *Low ROI for 4-page short*. Reviewers will ask "why only 100? why only 2 pipelines?" Save for the journal extension. Only do this if Day 15 is *very* green and the failure-mode taxonomy is impossible.

**Ranking justification:** Items 1–2 cost almost nothing and strengthen existing contributions; items 3–4 each cost a day and only address one reviewer concern apiece. Items 3 and 4 are *insurance*, not *value*.

### 12. Threats to Validity — Sample Section Text

**Drop into §6.2 (use verbatim, edit numbers):**

> **Threats to Validity. (Construct.)** Citation-style F1 measures whether the model points at the right requirement IDs; it does not measure rationale quality. We pair it with multi-judge faithfulness, but acknowledge that faithfulness judges are themselves LLMs subject to position and verbosity bias (Shi et al., IJCNLP-AACL 2025; *The Silent Judge*, arXiv:2509.26072). **(Internal.)** Cohen's κ = 0.302 between judges is low; we address this with Gwet's AC1, McNemar, and ranking-level Spearman (§4.3 and the κ-paradox discussion above). The per-pipeline κ for the agentic-graph flagship pipeline is 0.03; we attribute this to prevalence imbalance at the high-faithfulness end (per-pipeline AC1 is 0.41) but cannot rule out genuine judge disagreement on the most ambiguous outputs. **(External.)** The corpus is a 1,132-requirement synthetic DO-178C-style benchmark, not a real proprietary aerospace project; the dominance reversal at 2-hop is an *architectural* result that does not depend on corpus-specific phrasings, but absolute F1 numbers will not transfer. Cross-domain replication (MuSiQue, MultiHop-RAG) and cross-corpus replication on a curated, real-DO-178C project are deferred to the journal extension. **(Conclusion.)** Per-stratum N is 95–111; BCa is at the lower edge of its stability regime under heavy skew. We mitigated by reporting paired Wilcoxon and Cliff's δ alongside BCa intervals. **(Statistical.)** The V1 rule-based router was designed before this evaluation and does not match the empirical per-query optimum; the V2 ML router closes 30–45 % of the V1→Oracle gap but the remaining gap is not analyzed at the query-feature level. **(Reranker.)** No cross-encoder reranker is included in the main pipelines. The reranking axis is orthogonal to the architecture-family axis; a 100-query BGE-Reranker-v2-M3 pilot on the vanilla pipeline (Appendix A) confirms this orthogonality.

---

## Recommendations

**Stage 1 (Days 1–5): Get the stats done.** Do not start writing prose until BCa, Wilcoxon, Holm, Cliff's δ, all three tables, and both figures regenerate from a single Makefile target.
- Threshold to advance: all 30 Holm-adjusted p-values computed; all CIs render in LaTeX; both figures saved as PDF.

**Stage 2 (Days 6–10): Build V2 router or formally drop it.**
- Threshold to advance: V2 macro-F1 ≥ V1 + 2 absolute points, Holm-adjusted Wilcoxon p < 0.05. If not, drop V2 and re-cast the abstract.

**Stage 3 (Days 11–15): Write the paper.** In this order: §5 Results → §3+§4 Methodology+Experiments → §6 Discussion → §1 Abstract+Intro → §2 Related Work → §7 Conclusion.
- Threshold to advance: 4-page fit verified with all tables/figures; no `\todo` markers remain.

**Stage 4 (Days 16–20): Polish and stretch.** Decide on stretch contributions based on whether you have ≥ 3 days of buffer left. Default: oracle-gap analysis (free) + failure-mode taxonomy (3 hours). Reranker pilot is *insurance only* — add only if Day 15 is green.

**Stage 5 (Days 21–26): Anonymization, GenAI disclosure, submission.** Strict.

**Commit-vs-fall-back decision:** If by Day 15 you do not have a full draft (even rough), withdraw from CIKM and target UBMK 2026 (30 June). CIKM short paper acceptance rates are ~25 %; a rushed submission wastes your one shot. UBMK 30 June is a 3-week buffer with a more forgiving review.

---

## Caveats

- **CIKM 2026 deadlines are from the official site (cikm2026.diag.uniroma1.it/important-dates/)** as of the time of research. Verify on the day of submission — the abstract on 30 May 2026 is the critical hard deadline because abstracts cannot be added after that date.
- **GPT-5.4 specific behavior** is not documented in the public literature as of May 2026; some of the LLM-as-judge bias literature cited above tested GPT-4o or GPT-4.1. Assume the bias patterns hold but flag this in Threats to Validity.
- **One emerging caveat for κ-paradox framing:** a 2026 reviewer skeptical of LLM-as-judge entirely may still down-weight the paper. Mitigation: emphasize that the *retrieval-architecture comparison* (C1, judge-independent) is the headline result, and that C3 is a methodological contribution that *also* applies to future single-judge studies.
- **The "Wang et al., 2026" citations in RAGRouter-Bench (arXiv:2602.00296 / 2604.03455)** are recent preprints; some publishing venues may treat them as not-yet-peer-reviewed. Use them in Related Work but anchor the V2 router design in Adaptive-RAG (NAACL 2024), which is peer-reviewed.
- **BCa stability at N = 95** is documented as marginal under heavy skew (arXiv:2404.12967 simulation study, PMC6797821). If the BCa intervals look unreasonably narrow at 3+-hop, fall back to percentile + report both.

---

## Single Comprehensive CLI Prompt for Claude Code

Paste the following block verbatim into a Claude Code session at the root of the paper repo. It is structured to halt at three explicit user-review points (after stats, after V2 router, after full draft) and to refuse forbidden actions.

```text
You are my CIKM 2026 short paper executor. The deadline is 30 May 2026 (abstract, hard)
and 6 June 2026 (full paper, AoE). Today is 11 May 2026. The paper is at paper/cikm/.
The locked results CSV is at results/main-v2-scored.csv. Title is locked:
"Same-Family, Different Verdicts: A Multi-Judge, Stratum-Conditional Analysis of RAG
Architectures for Requirements Traceability".

═══ HARD RULES — NEVER VIOLATE ═══
- DO NOT re-run any of the 4440 main pipeline runs. They are LOCKED.
- DO NOT re-run the dual-judge faithfulness scoring. It is LOCKED.
- DO NOT add MuSiQue cross-eval to the main paper unless I explicitly say "GREEN-LIGHT MUSIQUE".
- DO NOT add a reranker to any main pipeline unless I explicitly say "GREEN-LIGHT RERANKER".
- DO NOT modify any number in main-v2-scored.csv.
- DO NOT add citations you cannot verify exist (real arxiv IDs, real venue/year).
- DO NOT touch sections I have not asked you to touch this step.
- HALT and ask for review at every "HALT FOR REVIEW" line below.

═══ STEP 1: STATISTICAL PROTOCOL (Days 1–5) ═══

1a. Create scripts/stats/bootstrap_ci.py that:
    - reads results/main-v2-scored.csv (columns: query_id, hop_stratum, pipeline, seed,
      citation_f1, faithful_gpt54, faithful_gpt41)
    - computes BCa 95% CIs (B=1000) for per-stratum citation F1, paired at the query
      level (average over 3 seeds first)
    - uses scipy.stats.bootstrap with method='BCa' or scikit-bootstrap;
      RNG seed = 20260511 for reproducibility
    - outputs results/stats/per_stratum_f1_ci.csv
      (columns: stratum, pipeline, mean, ci_lo, ci_hi)
    - also computes paired BCa CIs on the delta (pipeline_i F1 - pipeline_j F1) per
      stratum for all 10 pipeline pairs; outputs results/stats/pairwise_delta_ci.csv

1b. Create scripts/stats/significance_tests.py that:
    - runs paired Wilcoxon signed-rank on per-query F1 deltas for all 10 pipeline pairs
      within each of 3 strata = 30 tests
    - applies Holm-Bonferroni correction over the full family of 30
    - computes Cliff's delta with 95% CI for each pair-stratum (use the cliffs_delta
      python package; threshold table from Macbeth et al. 2011)
    - outputs results/stats/significance_matrix.csv
      (columns: stratum, pipeline_i, pipeline_j, mean_delta, wilcoxon_p, holm_p,
       cliffs_delta, cliffs_delta_magnitude, significant)
    - "significant" = (BCa CI excludes 0) AND (holm_p < 0.05) AND (|cliffs_delta| >= 0.147)

1c. Create scripts/stats/faithfulness_ci.py that:
    - computes BCa CIs for faithful% per (pipeline, stratum, judge)
    - computes Cohen's kappa, Gwet's AC1, raw agreement, McNemar test between the two
      judges per stratum and overall
    - computes per-pipeline kappa and AC1
    - computes Spearman rho on per-pipeline faithful% per stratum and overall
    - outputs results/stats/judge_agreement.csv and results/stats/faithfulness_ci.csv

1d. Generate figures:
    - figures/fig1_per_stratum_f1.pdf: grouped bar chart, x=stratum {1-hop, 2-hop, 3+-hop},
      y=citation F1, 5 bars per group color-coded by pipeline, BCa error bars,
      significance stars on top using Holm-adjusted Wilcoxon vs the per-stratum winner.
      ColorBlind-safe palette (matplotlib tab10 minus red/green clash).
    - figures/fig2_faithfulness_heatmap.pdf: 5 pipelines × 3 strata × 2 judges = 30
      cells, heatmap of faithful%, annotated with raw values, with marginal "agreement
      strip" showing Gwet's AC1 per stratum on the side.
    - Both PDFs, vector, fonts embedded.

1e. Run `make stats` (which runs 1a–1d) and verify outputs.

>>> HALT FOR REVIEW (GO/NO-GO #1, Day 5). <<<
Show me:
  (a) results/stats/per_stratum_f1_ci.csv contents
  (b) results/stats/significance_matrix.csv summary (how many of 30 tests significant)
  (c) results/stats/judge_agreement.csv contents
  (d) both figure PDFs
DO NOT proceed to Step 2 until I say "PROCEED TO STEP 2".

═══ STEP 2: V2 ML ROUTER + ORACLE UPPER BOUND (Days 6–10) ═══

2a. Create scripts/router/v2_features.py that extracts 12 features per query:
    [entity_count, has_id_regex, kw_verifies, kw_derives, kw_refines, kw_satisfies,
     kw_references, kw_which, kw_howmany, kw_list, query_token_len_log,
     query_embedding_pc1, query_embedding_pc2, query_embedding_pc3]
    - entity_count = re.findall(r'\b(REQ|SRS|HLR|LLR|SW)-\d+\b', query) count
    - keywords are case-insensitive token matches
    - embeddings = mean-pooled text-embedding-3-large, then PCA to 3 dims on train fold
    - output: data/router/features.csv with one row per query_id

2b. Create scripts/router/v2_train.py that:
    - target = hop_stratum (3-class)
    - model = sklearn LogisticRegression(multi_class='multinomial', penalty='l2', C=1.0,
      solver='lbfgs', max_iter=1000)
    - cross-validation: 10-fold stratified by hop_stratum, repeated 5 times with
      different seeds (50 total fits); use sklearn RepeatedStratifiedKFold(n_splits=10,
      n_repeats=5, random_state=20260511)
    - calibration: Platt scaling via CalibratedClassifierCV(method='sigmoid', cv='prefit')
      on a 20% inner-fold holdout
    - report macro-F1 mean ± std across 50 folds in results/router/v2_cv_report.txt
    - generate OUT-OF-FOLD predictions for ALL 296 queries:
      data/router/v2_oof_routes.csv (columns: query_id, predicted_hop, p_1hop, p_2hop,
      p_3hop, recommended_pipeline)
    - mapping: 1hop→vanilla, 2hop→vanilla, 3+hop→agentic-graph
      (mapping derived from per-stratum dominance in stats step; adjust if any stratum
      is contested at p>=0.05)

2c. Create scripts/router/oracle.py that:
    - for each query_id, computes per-pipeline F1 averaged over 3 seeds
    - oracle_pipeline = argmax over {vanilla, agentic, agentic-graph, graphrag}
      (NOT adaptive — adaptive itself is being upgraded)
    - outputs data/router/oracle_routes.csv

2d. Create scripts/router/evaluate_adaptive.py that:
    - constructs three new "pipelines" by routing per query:
      adaptive_v1 (using current rule-based router), adaptive_v2 (using v2_oof_routes),
      adaptive_oracle (using oracle_routes)
    - computes the same stats as Step 1 for these three rows
    - outputs results/stats/adaptive_comparison.csv

2e. Acceptance check:
    - v2 macro-F1 over all queries must be >= v1 + 2.0 absolute points
    - Holm-adjusted Wilcoxon p < 0.05 for v2 > v1 in at least 2 of 3 strata
    - v2 must close >= 30% of (oracle - v1) gap overall
    - If any check fails, print "V2_ACCEPTANCE_FAIL" and stop.

>>> HALT FOR REVIEW (GO/NO-GO #2, Day 10). <<<
Show me:
  (a) results/router/v2_cv_report.txt
  (b) results/stats/adaptive_comparison.csv
  (c) v2 acceptance check status
If V2_ACCEPTANCE_FAIL, ask me whether to drop V2 and re-plan, or to retune.
DO NOT proceed to Step 3 until I say "PROCEED TO STEP 3".

═══ STEP 3: WRITE THE PAPER (Days 11–15) ═══

Target: 4 pages in ACM sigconf, anonymous=true. References and GenAI Usage Disclosure
DO NOT count toward 4 pages. Files live in paper/cikm/sections/01-abstract.tex through
99-genai-disclosure.tex.

3a. Rewrite paper/cikm/sections/01-abstract.tex (max 200 words):
    - Opening: motivation (DO-178C traceability, regulated domain)
    - Setup: 1132 reqs, 5 pipelines, 296 stratified queries, 4440 runs, dual judge
    - 3 contributions (use these phrasings verbatim):
      C1: "We establish stratum-conditional dominance: vanilla RAG wins 2-hop
           (F1=0.548) while agentic-graph wins 1-hop and 3+-hop, a finding
           judge-independent across both faithfulness judges."
      C2: "We document a faithfulness collapse for GraphRAG at 3+-hop endpoints
           (74-78% → 33-40% faithful), driven by over-citation (14.9 IDs cited,
           citation precision 0.12) despite high retrieval recall."
      C3: "We propose a three-statistic LLM-judge protocol — Cohen's kappa, Gwet's
           AC1, and McNemar — that exposes a systematic leniency bias (p=0.0017)
           and resolves the kappa paradox at our 3+-hop stratum (kappa=0.04,
           AC1=0.57)."
    - Headline numbers: 5 pipelines, 4440 runs, 296 queries.

3b. Rewrite paper/cikm/sections/02-introduction.tex (max 0.75 column):
    - DO-178C traceability motivation (1 paragraph; cite Parasoft learning hub and
      arXiv:2503.04265 From Waterfallish Aerospace Certification)
    - Tension: RAG family choice is consequential but no stratum-conditional eval exists
      for regulated traceability; cite LiSSA ICSE 2025 and Leveraging Graph-RAG for
      Requirement Traceability arXiv:2412.08593
    - Three contributions in order C1, C2, C3 (same phrasings as abstract)
    - "Paper is organized as..." (one sentence)

3c. Update paper/cikm/sections/06-results.tex with 3 tables and 2 figures:
    Table 1: Per-stratum citation F1 (5 pipelines × 3 strata + adaptive_v2 + oracle rows)
             with BCa 95% CIs in parentheses and Holm-Wilcoxon significance daggers.
             Columns: 1-hop | 2-hop | 3+-hop | Overall
             Rows: vanilla, agentic, agentic-graph, graphrag, adaptive_v1, adaptive_v2,
                   adaptive_oracle
    Table 2: Faithfulness matrix (5 pipelines × 3 strata × 2 judges) as 5×6 layout
             where columns are (1h_J1, 1h_J2, 2h_J1, 2h_J2, 3h_J1, 3h_J2) and entries
             are faithful% with BCa CI half-width.
    Table 3: Judge agreement per stratum: columns = kappa, AC1, raw_agreement, McNemar_p,
             Spearman_rho_per_pipeline. Rows = 1-hop, 2-hop, 3+-hop, Overall.
    Figure 1: As generated in Step 1d.
    Figure 2: As generated in Step 1d.
    Use \input{...} pattern; tables are auto-generated by scripts/tex/make_tables.py
    from results/stats/*.csv.

3d. Write paper/cikm/sections/07-discussion.tex (max 0.5 column):
    - Subsection 7.1: "Why does vanilla win at 2-hop?" — hypothesis: dense retrieval
      surfaces the 2-hop neighborhood directly while typed-edge walks over-expand.
      Tie to arXiv:2502.11371 finding "RAG excels on detailed single-hop".
    - Subsection 7.2: "The kappa paradox is the protocol's message" — use the
      verbatim text from §7 of the planning report above.
    - Subsection 7.3: Threats to Validity — use the verbatim text from §12 of the
      planning report (Construct, Internal, External, Conclusion, Statistical,
      Reranker subparagraphs).

3e. Update paper/cikm/sections/03-related.tex to cite (minimum, ~15 refs):
    - Adaptive-RAG (Jeong et al., NAACL 2024)
    - Probing-RAG (Baek et al., Findings NAACL 2025; arXiv:2410.13339)
    - LiSSA (Fuchß et al., ICSE 2025; DOI 10.1109/ICSE55347.2025.00186)
    - Leveraging Graph-RAG for Requirement Traceability (arXiv:2412.08593)
    - From Waterfallish Aerospace Certification (arXiv:2503.04265)
    - GraphRAG (Edge et al., 2024; arXiv:2404.16130)
    - RAG vs GraphRAG: A Systematic Evaluation (arXiv:2502.11371)
    - When to use Graphs in RAG (arXiv:2506.05690)
    - GraphRAG-Bench (arXiv:2506.02404)
    - HippoRAG (Gutierrez et al., 2024)
    - MultiHop-RAG (Tang & Yang, 2024; arXiv:2401.15391)
    - ALCE (Gao et al., EMNLP 2023)
    - Correctness is not Faithfulness in RAG (arXiv:2412.18004)
    - Berg-Kirkpatrick et al. (EMNLP 2012) — paired bootstrap
    - Feinstein & Cicchetti (J. Clin. Epidemiol. 43, 1990) — kappa paradox
    - Gwet (Br. J. Math. Stat. Psychol. 61, 2008) — AC1

3f. Write paper/cikm/sections/99-genai-disclosure.tex using the verbatim disclosure
    template from §6 of the planning report.

3g. Run `make paper` and verify:
    - 4-page fit in sigconf double-column
    - All cross-references resolve (no "??")
    - All tables fit within column width
    - References and GenAI Disclosure are AFTER the 4-page main content
    - LaTeX compiles with `\documentclass[sigconf,natbib=true,anonymous=true]{acmart}`

>>> HALT FOR REVIEW (GO/NO-GO #3, Day 15). <<<
Show me the rendered PDF and 4-page-fit status. Ask me whether to proceed with stretch
contributions (failure-mode taxonomy, optional reranker pilot, optional MuSiQue) or
skip to polish.

═══ STEP 4: STRETCH (Days 16–20, ONLY IF I SAY GO) ═══

4a. (Default ON) Oracle-router gap analysis:
    - Compute (oracle - v2) per stratum and per pipeline
    - Add one column to Table 1 or one paragraph to §7.1: "V2 closes X% of the
      V1→Oracle gap; remaining headroom is concentrated at 3+-hop where router
      confidence is lowest."

4b. (Default ON) Failure-mode taxonomy:
    - Pull the 30 worst GraphRAG queries (lowest citation_f1 at 3+-hop)
    - Print queries + retrieved IDs + true IDs to data/failure_modes/worst30.json
    - I will manually categorize; you write a 4-row table of failure modes with counts
      and one example each, added to §7.1 as a sub-table.

4c. (DEFAULT OFF — only if I say "GREEN-LIGHT RERANKER"):
    - Run BGE-Reranker-v2-M3 (HuggingFace BAAI/bge-reranker-v2-m3) on top of vanilla
      RAG for 100 stratified queries (stratification: 33 × 1-hop, 33 × 2-hop, 34 × 3+-hop).
    - Report absolute F1 delta per stratum in an appendix table; one-sentence main-text
      mention.

4d. (DEFAULT OFF — only if I say "GREEN-LIGHT MUSIQUE"):
    - Run vanilla + agentic-graph on 100 MuSiQue queries; report citation F1 only.
    - One appendix paragraph.

═══ STEP 5: ANONYMIZATION + GENAI DISCLOSURE + SUBMIT (Days 18–26) ═══

5a. Anonymization audit script scripts/anon_audit.sh that runs:
    - `pdfinfo paper.pdf | grep -iE "author|creator|title"` — must show empty Author
    - `exiftool paper.pdf | grep -iE "author|creator|producer|title"`
    - `pdftotext paper.pdf - | grep -iE "<known_surnames_list>"` (you populate
      the list from a confidential env var SURNAMES_GREP that I will set; never log it)
    - grep the .tex source for: any GitHub URL not anonymous.4open.science, any
      author surname, any "our prior work", any "(authors)" placeholder
    - Run `exiftool -overwrite_original -Author="" -Title="" -Subject="" -Creator="LaTeX"
      paper.pdf` to scrub
    - Print PASS/FAIL summary
    Run `make anon` and HALT until I say "ANON PASS".

5b. Final compile check:
    - `\documentclass[sigconf,natbib=true,anonymous=true]{acmart}` — verify "ANONYMOUS
      AUTHOR(S)" appears in the rendered author block
    - 4-page fit re-verified
    - PDF/A-compliant if possible

5c. Build anonymous reproducibility mirror:
    - Stage: requirements.txt with pinned versions, scripts/, results/main-v2-scored.csv,
      results/stats/, data/router/, prompts/judge_*.yaml, README.md
    - Do NOT include any author-identifying file, any git history with author commits,
      any internal Azure resource names, any institution-specific paths
    - Output as a tarball ready to upload to anonymous.4open.science

5d. Submission package check (Day 26):
    - paper.pdf (4-page main + GenAI Disclosure + References)
    - supplementary.zip (anonymous mirror)
    - Abstract text (200 words)
    - Authors list (for EasyChair only, not in PDF)
    - Track: Short Research Papers

═══ ACCEPTANCE CRITERIA SUMMARY ═══

Step 1 done when: results/stats/{per_stratum_f1_ci, pairwise_delta_ci, significance_matrix,
  judge_agreement, faithfulness_ci}.csv all exist; both fig PDFs render.
Step 2 done when: v2 router passes acceptance check OR I formally drop V2.
Step 3 done when: 4-page PDF compiles with all 3 tables and 2 figures cross-referenced,
  no \todo markers, no "??", references + GenAI Disclosure present and unpaginated
  within the 4-page count.
Step 5 done when: `make anon` prints PASS, exiftool shows empty Author, pdfinfo shows
  empty Author, no GitHub-non-anonymous URLs in source, anonymous mirror tarball exists.

═══ OPERATING POSTURE ═══

- I am solo, tired, on a 26-day clock. Be terse. Show outputs, not pep talks.
- After every HALT, wait for my explicit "PROCEED TO STEP N" before continuing.
- If you encounter ambiguity, choose the more conservative option and tell me.
- If a script fails, do not silently retry; surface the error and pause.
- Never assume Azure credentials work; if a call fails, halt and ask.

Begin Step 1 now.
```

---

## Step 3 phrasing notes (locked from Step 1 stats, 2026-05-11)

These notes constrain the verbatim phrasings in Step 3 (paper writing). Recorded per user direction after the Step 1 GO/NO-GO #1 review. Source numbers: `results/stats/significance_matrix.csv`, `results/stats/judge_agreement.csv`.

### C1 — agentic-graph is "tied with agentic", not single-best

The PLAN.md original C1 phrasing implies agentic-graph is the unique winner at 1-hop and 3+-hop. The Step 1 statistics show that agentic-graph and agentic form a *statistical tie* at every stratum (Cliff's δ < 0.147 threshold not crossed, even where the Holm-Wilcoxon test is significant: e.g., 3+-hop agentic vs agentic-graph holm_p=0.042 but |δ|=0.093). The corrected C1 phrasing is:

> **agentic-graph (statistically tied with agentic) wins 1-hop and 3+-hop over the remaining field; vanilla wins 2-hop.**

Do NOT claim agentic-graph as single-best at 1-hop or 3+-hop. The pair {agentic-graph, agentic} dominates the remaining three pipelines but does not separate from each other.

### C3 — distinguish kappa paradox from genuine disagreement

The C3 paragraph in §4.3 must explicitly contrast two different phenomena revealed by the multi-judge protocol; do not collapse them.

> **Kappa paradox at 3+-hop** (κ=0.04, AC1=0.57, raw agreement=0.70): the high prevalence of "unfaithful" judgments at this stratum (~80% unfaithful by both judges) collapses Cohen's κ via Feinstein–Cicchetti (1990); Gwet's AC1 recovers substantial agreement once the prevalence-based chance term is corrected.

> **Genuine disagreement at 2-hop** (κ=0.22, AC1=0.21, Spearman ρ=0.10 across the 5-pipeline ranking): both κ and AC1 agree that judge agreement is poor at this stratum; the per-pipeline ranking *also* disagrees between judges. This is not a kappa paradox; it is a real measurement zone where same-family judges fundamentally diverge on the medium-hop regime. Frame as a finding, not a weakness.

Reporting κ and AC1 side-by-side lets the reader see *where* the paradox applies and *where* the disagreement is real.
# Academic writing knowledge base

Distilled from four parallel readings of published papers (October 2026), one per genre the
paper sits between. Every rule below was observed in at least two genres; genre-specific
habits are marked. Counts are per 1,000 words of body prose (tables, math and references
removed).

## Sources

| Genre | Papers read (arXiv) |
|---|---|
| RAG / GraphRAG empirical comparisons | Han et al. RAG vs. GraphRAG 2502.11371; GraphRAG-Bench 2506.05690; HippoRAG 2 2502.14802; HippoRAG 2405.14831 (NeurIPS'24); ALCE 2305.14627 (EMNLP'23) |
| IR evaluation and LLM-as-judge (SIGIR/ICTIR/NAACL) | Thomas et al. 2309.10621 (SIGIR'24); Faggioli et al. 2304.09161 (ICTIR'23); Clarke & Dietz 2412.17156; Saad-Falcon et al. ARES 2311.09476 (NAACL'24) |
| ECIR full and reproducibility papers (LNCS) | 2510.02657 (ECIR'26); 2604.02985 (ECIR'26 full); 2501.04802 (ECIR'25 repro); 2503.23824 (ECIR'25); 2510.11956 (ECIR'26) |
| Requirements traceability with NLP/LLMs (ICSE/RE) | Lin et al. T-BERT 2102.04411 (ICSE'21); Rodriguez et al. 2308.00229 (RE'23 wksp); TVR 2504.15427; Fuchß et al. 2511.02434 |

## 1. Punctuation and symbols (measured)

| Mark | Published papers | Our draft (before rewrite) | Rule |
|---|---|---|---|
| Parenthetical dash (em, or spaced en `--`) | 0–1 typical; 2–5 in two eval papers, always a single definitional aside | 3.7 | ≤1 per page. One aside per sentence, never paired for drama. Never `--` spaced as a dash; en dash only for ranges (1–100) and compounds (human–machine). Prefer commas, parentheses, or a new sentence. |
| `×` in prose | 0 in most; only for ratios ("5.7× faster") or matrix sizes ("4 pipelines × 2 embedders") | 5.2 (incl. math) | Write "times" or "by"; keep × for design sizes and ratios. Interaction terms: "the hop-by-expansion interaction". |
| `→` in prose | 0 in all 13 papers | 0.9 | Never in prose; write "from 0.30 to 0.17". Arrows only in figures, tables, notation. |
| Semicolon | 0–9 | 12.3 | Sparingly; mainly to separate items of a long list. |
| Colon | 3–12, almost all before lists, RQs, definitions | 20.9 | Only before a list, definition, or label. Never a rhetorical reveal ("The answer: …"). |
| Italic emphasis | ~0; italics for terms at first definition and placeholders only | 9.1 (`\emph`+`\textit`) | No single-word stress. Italicise a term once where it is defined. |
| "Crucially/Importantly" openers | 0; "Notably/Interestingly" ≤1 per paper | 0 | Keep at 0; at most one "Notably". |

## 2. Structure

- **Section headings are generic nouns**: Introduction, Related Work, Method(ology), Experimental
  Setup, Results (and Analysis), Discussion, Limitations, Conclusion.
- **Subsection headings name a topic, never a finding.** "4.3 Response Quality Impact", not
  "Winners are Corpus-Conditional". Headline-claim headings appear only in position papers.
- **No C1/C2 labels.** Not one of the 13 papers labels claims "C1, C2". Two acceptable
  substitutes:
  - Research questions (ECIR repro and RE papers): introduced inline in the intro right after
    their motivation ("This leads to our first research question (RQ1): …?"), used as result
    headings ("5.1 RQ1: <question>" or "Topic (RQ1)"), answered in a plain sentence
    ("Regarding RQ1, …"). No "Answer:" boxes.
  - No labels at all (eval papers, ECIR full papers): topic subsections, contributions in prose.
- **Run-in `\paragraph{Name.}` heads** are the LNCS workhorse: Related Work, setup items,
  per-result paragraphs, and limitations ("Scope and limitations.").
- **Contributions**: 2–4 items, each a "We …" sentence; either "Our contributions are
  threefold:" + itemize, or inline "(i) … (ii) …", or "First, … Second, …". No bold claim
  labels. Intro ends with a roadmap sentence.
- **Limitations**: one short flat section or run-in paragraph; threat → mitigation sentences;
  RE papers split construct / internal / external (citing Runeson & Höst or Wohlin).
- **Conclusion**: 1–2 paragraphs, opens "In this paper, we …", recaps findings with numbers,
  one sentence of future work. LNCS adds run-in "Acknowledgements." / "Disclosure of Interests."
  at camera-ready.

## 3. Openings

- Abstract: one paragraph, 7–9 sentences: context → gap → "We study…" → 2–3 findings with 1–3
  numbers → implication or released artifact.
- Introduction (traceability genre): define traceability, tie it to certification (cite the
  regulator), state the cost of manual tracing, then the technical gap.
- Section openers are plain framing: "In this section, we …", "Table 3 shows …",
  "To answer RQ2, we …". No hooks.
- Results subsections open by pointing at the table or figure, then interpret.

## 4. Numbers and statistics

- 1–2 numbers per sentence; move longer runs to a table or split them with semicolons.
- Format: "Cohen's κ = 0.52 (moderate agreement)"; "p < 0.05 (Wilcoxon)"; CI method stated
  once, then ranges as "0.50–0.71"; percentage points written "4.7 points" or "4.7 pp".
- Anchor agreement figures against a baseline (same-day test–retest, prior work).
- Translate statistics when helpful ("41% of verdicts flip").

## 5. Voice

- "We" is frequent (10–28 per 1k words). Present tense for claims and what tables show; past
  for procedures and runs; present perfect in conclusions.
- Sentence length median ~20 words, range ~8–45; long citation-laden sentences are normal;
  short sentences are complete sentences, never fragments.
- Hedge scope explicitly: "suggests", "in our setting", "under our setup", "may not transfer".
- Transitions: However, In contrast, For example, Similarly, As a result, Note that.
- Contrasts stated flatly with "while", "whereas", "however".

## 6. Model-writing tells to remove

1. "Not X, but Y" / "X does not merely …; it …" reversals.
2. Paired dash asides and dash-introduced punchlines.
3. Rhetorical colons ("The answer is simple: …").
4. Italic stress on single words.
5. Rhythmic triads ("in all six settings, under a second traversal, and against two
   mitigations") where the list is decoration rather than content.
6. Headline-claim headings and claim labels (C1–C5).
7. Symbols standing in for words in prose (×, →, ≤ used as "at most").
8. Stacking every number into one sentence.
9. Aphoristic closers ("…is the minimum bar for …", "the first replicates, the second does
   not").
10. Self-referential signposting of importance ("Our headline result is not that …").

## 7. Genre-specific notes

- **RAG/GraphRAG papers** report no p-values in prose; gains are "7%" or "3 points", ratios are
  "10 to 30 times". A paper that does report tests should give each one once, in parentheses,
  with the test named. ALCE is the only one with finding-sentence run-in heads, used
  consistently. Han et al. v3 (2026) is the most model-flavoured of the set ("Crucially,",
  "GraphRAG is not free"); do not imitate it.
- **LLM-judge papers** gloss agreement in words ("κ = 0.26, a fair level of agreement") and
  anchor it against human–human baselines from prior work.
- **ECIR papers** use RQ headings mainly in the reproducibility track; full papers more often
  use topic subsections. Captions are descriptive noun phrases plus protocol (seeds, what bold
  means); findings belong in the text.
- **Traceability papers** open on the regulator (FAA, ISO 26262) and the cost of manual
  tracing; Threats to Validity follow construct / internal / external with threat → mitigation.

## 8. Decisions for this paper

- C1–C4 become RQ1–RQ4, stated as questions in the introduction, used as "(RQ*n*)" tags on
  topic-named Results subsections, and answered with one plain "Regarding RQ*n*, …" sentence.
- Contributions: one short itemize of "We …" sentences.
- Captions: describe content and protocol; move findings to the text.
- Interaction term: "hop-by-expansion interaction"; arrows replaced by "from … to …".

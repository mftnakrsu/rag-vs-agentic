# CIKM 2026 Short Paper — LaTeX Skeleton

Compile-clean ACM `sigconf` skeleton for the CIKM 2026 short-paper
submission. **Double-blind compliant.** All experimental numbers are
marked `[PLACEHOLDER: ...]`; all author/identity-revealing strings are
marked `[TODO: ...]`.

## File layout

```
paper/cikm/
├── main.tex                      # acmart wrapper, CCS, keywords, \input order
├── refs.bib                      # ~30 BibTeX entries
├── Makefile                      # pdflatex → bibtex → ×2 + submit/clean targets
├── README.md                     # this file
├── .gitignore                    # LaTeX byproducts
├── figures/.gitkeep              # populate from results notebooks
└── sections/
    ├── 01-abstract.tex
    ├── 02-introduction.tex       # ~0.5–0.75 page
    ├── 03-related-work.tex       # ~0.4–0.6 page
    ├── 04-method.tex             # ~0.8–1.0 page; figure 1
    ├── 05-experiments.tex        # ~0.4–0.5 page
    ├── 06-results.tex            # ~0.8–1.0 page; table 1, figs 2–3
    ├── 07-discussion.tex         # ~0.3–0.4 page
    ├── 08-conclusion.tex         # 3–4 sentences
    └── 99-genai-disclosure.tex   # mandatory; doesn’t count toward 4 pages
```

## Build

### Recommended: Overleaf

1. Create a new project on https://overleaf.com and pick **acmart**
   from the templates list (or upload this folder as a zip).
2. Set the main document to `main.tex`.
3. Compile. Overleaf has `acmart.cls` and ACM-Reference-Format BibTeX
   pre-installed; no setup needed.

### Local

Requires a TeX distribution with `acmart.cls` (TeX Live, MacTeX, or
MiKTeX).

```bash
cd paper/cikm
make            # builds main.pdf
make watch      # latexmk -pvc auto-rebuild on save
make submit     # produces CIKM-2026-anonymous.pdf and a submission zip
make clean      # nukes build artefacts
```

If `pdflatex` is missing on macOS:

```bash
brew install --cask basictex
sudo tlmgr update --self
sudo tlmgr install acmart booktabs ifoddpage relsize tools
```

## Filling the skeleton

Search for the two placeholder markers:

```bash
grep -rn "\[PLACEHOLDER" sections/   # experimental numbers + figures
grep -rn "\[TODO"        sections/ refs.bib   # editorial / bib fix-ups
```

`[PLACEHOLDER: ...]` is intentional — those values come from the
experiment matrix (`results/results.csv`). Do not replace them by
plausible-looking numbers; pull them from the CSV at submission time.

`[TODO: ...]` markers in `refs.bib` are for unverified author lists
and venue strings; verify against DBLP / Semantic Scholar.

## Page-budget guardrails

The 4-page hard cap (excluding references and the GenAI Disclosure)
is tight. Concrete levers if you overflow:

- **Table 1** is `table*` (two-column). If results column is the
  overflow source, drop the *Latency (s)* column and switch to
  `table` (single-column). Cost in USD is the financial proxy and
  Latency rarely lands in a short paper.
- **Figures 2 and 3** are single-column. Combining them into a single
  `figure*` panel saves ~6 lines.
- **Section 7 (Discussion)** can be compressed to a single paragraph
  with two italicised lead-ins (`\textit{Construct.}`,
  `\textit{Internal.}`, `\textit{External.}`) if needed.
- The `itemize` in Section 1 can be collapsed to inline
  `\textbf{(i)} ... \textbf{(ii)} ... \textbf{(iii)} ...`.

Try `\setlength{\parskip}{0pt}` only as a last resort.

## Anonymisation checklist (run before submission)

- [ ] `\documentclass[..., anonymous=true]{acmart}` (already set in
      `main.tex`).
- [ ] `\author{Anonymous Author(s)}` and
      `\affiliation{\institution{Anonymous Institution}\country{}}`
      (already set; do not edit until camera-ready).
- [ ] No GitHub URLs in the submission PDF: replace any
      `https://github.com/<user>/...` with the phrase
      *“code available upon publication”*.
- [ ] No `\thanks{}`, no `\acknowledgments{}` (the latter is
      auto-suppressed by `anonymous=true`, but check anyway).
- [ ] **Self-citations are third-person.** Write *“prior work [N]
      shows …”* not *“in our prior work [N] we showed …”*.
- [ ] **PDF metadata.** After build, run:
      `pdfinfo main.pdf | grep -i -E 'author|title|producer'` and
      verify no real name appears. If your name leaks via
      `pdftex` defaults, add
      `\hypersetup{pdfauthor={},pdftitle={Anonymous}}` before
      `\maketitle`.
- [ ] No university name, advisor name, or grant number anywhere.
- [ ] Filename of the uploaded PDF should be neutral
      (`CIKM-2026-anonymous.pdf` from `make submit`).
- [ ] Re-grep:
      `grep -ri "anonymous_institution\|acknowledg\|grant"
      sections/ main.tex` (case-insensitive sanity).

## Submission

- **Track:** EasyChair → CIKM 2026 Short Paper.
- **Page limit:** 4 pages including any appendix; references and the
  GenAI Disclosure section are unlimited.
- **Deadline:** 23 May 2026 (anywhere on Earth — confirm on the
  EasyChair page).
- **Format:** ACM `sigconf` 2-column.

Improper anonymisation is grounds for desk-reject; the checklist
above is non-negotiable.

## ACM CCS

The CCS XML in `main.tex` uses three concept IDs as a starting point.
Regenerate via the official tool at <https://dl.acm.org/ccs> for the
final submission and replace the XML block — IDs occasionally change
between revisions of the taxonomy.

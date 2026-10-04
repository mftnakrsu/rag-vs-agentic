## Two builds from one source, both copied to the repository root:
##   ECIR-2027-anonymous.pdf  double-anonymous ECIR submission
##   arXiv-preprint.pdf       de-anonymised preprint (authors, artifact URLs)
ROOT     := ..
ANON     := ECIR-2027-anonymous
ARXIV    := arXiv-preprint
SOURCES  := main.tex refs.bib $(wildcard sections/*.tex) $(wildcard tables/*.tex) $(wildcard figures/*)
LATEX    := pdflatex -interaction=nonstopmode -halt-on-error

.PHONY: all clean zip

all: $(ROOT)/$(ANON).pdf $(ROOT)/$(ARXIV).pdf

$(ROOT)/$(ANON).pdf: $(SOURCES)
	$(LATEX) -jobname=$(ANON) main.tex
	-bibtex $(ANON)
	$(LATEX) -jobname=$(ANON) main.tex
	$(LATEX) -jobname=$(ANON) main.tex
	cp $(ANON).pdf $@

$(ROOT)/$(ARXIV).pdf: $(SOURCES)
	$(LATEX) -jobname=$(ARXIV) '\def\arxiv{}\input{main}'
	-bibtex $(ARXIV)
	$(LATEX) -jobname=$(ARXIV) '\def\arxiv{}\input{main}'
	$(LATEX) -jobname=$(ARXIV) '\def\arxiv{}\input{main}'
	cp $(ARXIV).pdf $@

## Source bundle for arXiv upload (arXiv compiles main.tex, so it gets \arxiv baked in).
zip: $(ROOT)/$(ARXIV).pdf
	rm -rf arxiv-src && mkdir arxiv-src
	cp -r sections tables figures refs.bib llncs.cls splncs04.bst $(ARXIV).bbl arxiv-src/
	mv arxiv-src/$(ARXIV).bbl arxiv-src/main.bbl
	{ echo '\def\arxiv{}'; cat main.tex; } > arxiv-src/main.tex
	cd arxiv-src && zip -qr ../$(ROOT)/arXiv-source.zip . && cd .. && rm -rf arxiv-src

clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.pdf *.fls *.fdb_latexmk *.synctex.gz

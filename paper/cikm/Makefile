PAPER     := main
TEX_FILES := $(wildcard sections/*.tex) $(PAPER).tex
BIB_FILE  := refs.bib
SUBMIT    := CIKM-2026-anonymous

.PHONY: all clean submit watch help

all: $(PAPER).pdf

$(PAPER).pdf: $(TEX_FILES) $(BIB_FILE)
	pdflatex -interaction=nonstopmode -halt-on-error $(PAPER).tex
	-bibtex $(PAPER)
	pdflatex -interaction=nonstopmode -halt-on-error $(PAPER).tex
	pdflatex -interaction=nonstopmode -halt-on-error $(PAPER).tex

watch:
	latexmk -pdf -pvc -interaction=nonstopmode $(PAPER).tex

submit: $(PAPER).pdf
	cp $(PAPER).pdf $(SUBMIT).pdf
	zip -r $(SUBMIT).zip \
	    $(PAPER).tex sections refs.bib figures \
	    -x "*.aux" -x "*.log" -x "*.bbl" -x "*.blg" -x "*.fdb_latexmk" \
	    -x "*.fls" -x "*.synctex.gz"
	@echo "Submission bundle: $(SUBMIT).pdf and $(SUBMIT).zip"

clean:
	rm -f $(PAPER).pdf $(SUBMIT).pdf $(SUBMIT).zip \
	      *.aux *.bbl *.blg *.log *.out *.toc *.synctex.gz \
	      *.fls *.fdb_latexmk sections/*.aux

help:
	@echo "Targets:"
	@echo "  make          build $(PAPER).pdf"
	@echo "  make watch    rebuild on every save (latexmk)"
	@echo "  make submit   produce $(SUBMIT).pdf + $(SUBMIT).zip"
	@echo "  make clean    delete all build artefacts"

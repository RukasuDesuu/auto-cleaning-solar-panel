PROJECT=artigo
TEX=pdflatex
BIBTEX=bibtex
FLAGS=-interaction=nonstopmode -file-line-error

all: build clean-temp

build:
	-$(TEX) $(FLAGS) $(PROJECT).tex
	-$(BIBTEX) $(PROJECT)
	-$(TEX) $(FLAGS) $(PROJECT).tex
	-$(TEX) $(FLAGS) $(PROJECT).tex

clean-temp:
	find . -maxdepth 1 -name \*.aux -type f -delete
	find . -maxdepth 1 -name \*.bcf -type f -delete
	find . -maxdepth 1 -name \*.blg -type f -delete
	find . -maxdepth 1 -name \*.fdb_latexmk -type f -delete
	find . -maxdepth 1 -name \*.fls -type f -delete
	find . -maxdepth 1 -name \*.log -type f -delete
	find . -maxdepth 1 -name \*.out -type f -delete
	find . -maxdepth 1 -name \*.run.xml -type f -delete
	find . -maxdepth 1 -name \*.synctex.gz -type f -delete
	find . -maxdepth 1 -name \*.toc -type f -delete
	find . -maxdepth 1 -name \*.bbl -type f -delete

clean: clean-temp
	find . -maxdepth 1 -name $(PROJECT).pdf -type f -delete

.PHONY: all build clean-temp clean

PROJECT=linucb_test
PYTHON=../.venv/bin/python

all: $(PROJECT).pdf

$(PROJECT).pdf: $(PROJECT).tex
	uv sync
	pdflatex -shell-escape $(PROJECT).tex
	pdflatex -shell-escape $(PROJECT).tex

clean:
	rm -f *.aux *.log *.nav *.out *.snm *.toc *.vrb *.pdf

.PHONY: all clean

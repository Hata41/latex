PROJECT=beamer
PYTHON=../.venv/bin/python
MODE=slides

all: $(PROJECT).pdf

animate:
	$(MAKE) MODE=animate force_compile

force_compile:
	uv sync
	pdflatex -shell-escape "\providecommand{\buildmode}{$(MODE)}\input{$(PROJECT)}"
	pdflatex -shell-escape "\providecommand{\buildmode}{$(MODE)}\input{$(PROJECT)}"

$(PROJECT).pdf: $(PROJECT).tex
	$(MAKE) force_compile

clean:
	rm -f *.aux *.log *.nav *.out *.snm *.toc *.vrb *.pdf

.PHONY: all clean animate force_compile

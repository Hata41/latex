# Makefile for Oleron Presentation
LATEX_ENGINE = pdflatex -shell-escape
MODE ?= slides

.PHONY: all compile sync clean

all: compile

compile: sync
	$(LATEX_ENGINE) "\def\buildmode{$(MODE)}\input{beamer.tex}"
	# Run twice for references/toc if needed
	# $(LATEX_ENGINE) beamer.tex

sync:
	uv sync

clean:
	rm -rf .venv
	rm -f *.aux *.log *.nav *.out *.snm *.toc *.pdf

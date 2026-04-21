# Oleron Presentation

This repository contains an academic presentation built with Beamer. It features dynamic TikZ animations generated via Python scripts.

## Logic Structure

- `beamer.tex`: Main LaTeX document.
- `scripts/`: Python scripts that generate LaTeX/TikZ code on the fly.
- `slides/` & `animations/`: Modular LaTeX and TikZ components.

## Requirements

- **LaTeX**: A distribution like TeX Live or MikTeX must be installed.
- **uv**: Fast Python package installer and resolver.
- **Make**: For build automation.

## Building the Presentation

To initialize the Python environment and compile the PDF:

```bash
make
```

The Makefile will automatically:
1. Create a virtual environment using `uv sync`.
2. Install dependencies (like `numpy`).
3. Compile the PDF using `pdflatex --shell-escape`.

## Why --shell-escape?

The compilation requires the `--shell-escape` flag because `beamer.tex` executes Python scripts directly to generate dynamic content. For example:
`\input|"./.venv/bin/python -u scripts/mab_problem.py"`

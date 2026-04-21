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

That is a fantastic addition. Those points perfectly capture the "Monolithic Document Architecture" trap that catches almost everyone working with heavy LaTeX graphics. Ironically, your project's current architecture—using Python to generate the frames and compiling them via `\input`—is already a step in the right direction to avoid that exact monolithic trap!

Here is the fully combined and polished **"Troubleshooting & Best Practices"** section, integrating the fixes we just made with the lessons learned from your other project. You can copy and paste this directly into your `README.md`:

```markdown
## Troubleshooting & Best Practices

### Part 1: Common Pitfalls & Compilation Errors

**1. Compiled PDF is completely blank (White Screen)**
* **The Problem:** The presentation compiles successfully, but the slides containing animations are completely blank.
* **The Cause:** The `animate` package uses embedded JavaScript to flip through frames. Most modern PDF viewers (including VS Code's built-in viewer, Chrome, macOS Preview, and Evince) block or do not support this JavaScript.
* **The Fix:** You must open the PDF in a JavaScript-capable reader:
  * **Linux:** `okular` (Recommended. If using VS Code, configure the LaTeX Workshop extension to use Okular as the external viewer).
  * **Windows/macOS:** Adobe Acrobat Reader.

**2. Error: `Environment axis undefined`**
* **The Problem:** The compiler crashes with `! LaTeX Error: Environment axis undefined.` or `Undefined control sequence` on `\addplot`.
* **The Cause:** In `pgfplots`, the `\begin{axis}` environment must **always** be wrapped inside a `\begin{tikzpicture}` environment. If a Python script generates raw axis code without the TikZ wrapper, LaTeX will not know how to render it.
* **The Fix:** Ensure your Python generator wraps every frame's plot like this:
  ```latex
  \begin{tikzpicture}
  \begin{axis}[...]
      \addplot3[...] ...
  \end{axis}
  \end{tikzpicture}
  ```

**3. Warning: `Missing character: There is no ; in font nullfont!`**
* **The Problem:** The compile log is spammed with `nullfont` warnings.
* **The Cause:** A stray semicolon `;` was placed at the end of a non-drawing TeX macro inside a TikZ block (e.g., `\pgfmathsetmacro{\ycoord}{...};`). TikZ expects semicolons only at the end of drawing paths (`\draw`, `\node`). Otherwise, it tries to render it as literal text on the canvas, fails, and throws a warning.
* **The Fix:** Remove the trailing semicolon from mathematical or structural macros.

---

### Part 2: Architecture & Performance Optimization

Treating a high-computation LaTeX project like a simple text file leads to massive compile times and fragile code. Avoid the "Monolithic Document Architecture" trap by following these guidelines:

**1. Avoid High-Performance Math in the Main Loop**
* **The Mistake:** Placing complex `pgfplots` and `animate` environments directly inside the main `.tex` file.
* **Why it's a problem:** Every time you fix a typo in the introduction, LaTeX has to re-calculate every coordinate for your 3D Gaussian surfaces and every frame of your animations.
* **README Tip:** Avoid nesting raw TikZ/PGFPlots code for complex 3D visualizations directly in the main body. Use externalization or external script generation (like our Python pipeline) to cache these graphics.

**2. Prevent Redundant Package Loading**
* **The Mistake:** Importing the same packages (`tikz`, `animate`, `graphicx`) multiple times in the preamble.
* **Why it's a problem:** While LaTeX usually handles this gracefully, it leads to "Preamble Bloat," making the environment harder to debug and increasing the risk of option clashes (where two imports of the same package have different settings).
* **README Tip:** Keep the preamble DRY (Don't Repeat Yourself). Audit package imports to ensure each dependency is loaded exactly once with consistent options.

**3. Enable "Externalization"**
* **The Mistake:** Not using a caching system for figures.
* **Why it's a problem:** Without caching or externalization, you are forcing a "Cold Start" on every single compilation.
* **README Tip:** For projects with heavy vector graphics, enable `tikz-external` (or keep your Python-generated graphics in isolated test files). This saves compiled figures as separate PDFs, reducing subsequent compile times from minutes to seconds.

**4. Avoid Over-Sampling during Drafting**
* **The Mistake:** Setting high `samples` values (e.g., 18–30) while still writing the content.
* **Why it's a problem:** High sample rates are for the final print version. During the writing phase, a sample rate of 5 or 10 is usually enough to see the shape of the plot without the massive time penalty.
* **README Tip:** Use a global variable for plot samples. Keep it low (e.g., 8–10) during development and only increase it for the final production build.

**5. Isolate Inline Animation Frames**
* **The Mistake:** Using inline loops to generate 20+ frames of 3D math inside a live document.
* **Why it's a problem:** The `animate` package is notoriously resource-heavy. Calculating dozens of iterations of a 3D ellipsoid in real-time is the fastest way to hit a compiler timeout.
* **README Tip:** Complex animations should be compiled as standalone PDFs and included via `\animategraphics`, or generated by isolated scripts. Do not generate dynamic frames inside the main document loop.

### Summary for Compilation Optimization
This project uses heavy 3D rendering and programmatic generation. To maintain fast compile times:
1. Use isolated directories/files for heavy animations (e.g., test them standalone before pulling them into the main presentation).
2. Ensure `--shell-escape` is enabled in your compiler to allow the Python scripts to run.
3. Keep animation logic in standalone files to prevent the main compiler from hanging.
```
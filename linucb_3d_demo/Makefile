all: linucb_test.pdf

linucb_test.pdf: linucb_test.tex linucb_3d_beamer.py
	pdflatex -shell-escape linucb_test.tex
	# Run twice for cross-references if needed, 
	# though for this simple demo once is usually enough.
	# pdflatex -shell-escape linucb_test.tex

clean:
	rm -f *.aux *.log *.nav *.out *.snm *.toc *.vrb *.pdf

.PHONY: all clean

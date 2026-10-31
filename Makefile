# Projet DAAR 1 - clone de egrep (Python 3, aucune compilation nécessaire)
PYTHON ?= python3
REGEX  ?= S(a|g|r)*on
FILE   ?= data/gutenberg_56667.txt

.PHONY: all run data test bench plots report clean

all: test

# Exemple : make run REGEX="(the|and)" FILE=data/gutenberg_56667.txt
run:
	$(PYTHON) src/egrep_clone.py "$(REGEX)" "$(FILE)"

# Corpus synthétique de 500 000 lignes (non inclus dans l'archive : ~35 Mo)
data: data/test_performance.txt
data/test_performance.txt:
	$(PYTHON) scripts/generate_test_file.py

# Test différentiel contre grep -E
test: data
	$(PYTHON) tests/validate.py

bench:
	$(PYTHON) scripts/benchmark.py

# Nécessite matplotlib (pip install -r requirements.txt)
plots:
	$(PYTHON) scripts/plot_results.py

report:
	cd report && latexmk -pdf main.tex

clean:
	rm -f data/test_performance.txt
	rm -rf src/__pycache__
	cd report && latexmk -c main.tex

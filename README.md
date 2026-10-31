# DAAR – Projet 1 : clone de egrep (support partiel des ERE)

Auteurs : ALAOUCHICHE Abderrahmane Yaakoub, KOUACHE Riad.

Le programme affiche, comme `egrep`, les lignes d'un fichier contenant une
sous-chaîne reconnue par une expression régulière. Opérateurs pris en charge :
parenthèses, alternative `|`, concaténation, étoile `*`, point `.` et caractères ASCII.

- Motif avec métacaractère : arbre syntaxique → AFN (Aho-Ullman) → AFD
  (sous-ensembles) → AFD minimal → recherche.
- Motif littéral (sans métacaractère) : algorithme KMP.

## Prérequis

- Python ≥ 3.7 (aucune dépendance pour le programme et les tests) ;
- GNU `grep` (tests et mesures) ;
- `matplotlib` pour les figures (`pip install -r requirements.txt`) ;
- LaTeX (`latexmk`, `pdflatex`, `bibtex`) pour le rapport.

## Exécution

Python étant interprété, le « binaire » est le script exécutable `src/egrep_clone.py` :

```bash
python3 src/egrep_clone.py "S(a|g|r)*on" data/gutenberg_56667.txt
# ou
make run REGEX="S(a|g|r)*on" FILE=data/gutenberg_56667.txt
```

Code de retour : 0 si au moins une ligne correspond, 1 sinon, 2 en cas d'erreur.

## Tests et mesures

```bash
make test    # génère data/test_performance.txt puis compare la sortie avec grep -E
make bench   # temps moyen et écart-type (10 répétitions) -> results/
make plots   # figures -> results/figures/
make report  # compile report/main.tex -> report/main.pdf
```

## Arborescence

```
src/egrep_clone.py            programme (parser, AFN, AFD, minimisation, KMP)
tests/validate.py             test différentiel contre grep -E
scripts/generate_test_file.py génère le corpus synthétique (graine fixe)
scripts/benchmark.py          mesures de performance
scripts/plot_results.py       diagrammes bâton (moyenne + écart-type)
data/gutenberg_56667.txt      livre 56667 du Projet Gutenberg (fins de ligne LF)
results/                      sorties générées (CSV, journaux, figures)
report/                       rapport LaTeX (main.tex, references.bib, main.pdf)
docs/                         énoncé du projet
```

Le fichier Gutenberg a été converti en fins de ligne Unix (LF) afin que la
comparaison avec `grep -E` ne dépende pas du traitement de `\r` par la plateforme.
Le corpus synthétique (`data/test_performance.txt`, ~35 Mo) n'est pas fourni :
il est régénéré à l'identique par `make data`.

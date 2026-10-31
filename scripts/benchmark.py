"""Mesure des performances sur data/gutenberg_56667.txt.

- Motifs littéraux : KMP, automate (AFD minimal) sur le même motif, et grep -E.
- Expressions régulières : automate (AFD minimal) et grep -E.
Chaque mesure est répétée REPETITIONS fois (après un passage de chauffe) ;
on enregistre la moyenne et l'écart-type dans results/benchmark_results.csv.
La taille des automates (AFN, AFD, AFD minimal) est enregistrée dans
results/automata_sizes.csv.

Remarque : le temps du clone est mesuré dans le processus Python (lecture du
fichier + recherche) ; celui de grep inclut le lancement du processus.
"""
import csv
import statistics
import subprocess
import sys
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))
import egrep_clone as clone  # noqa: E402

FICHIER = RACINE / "data" / "gutenberg_56667.txt"
RESULTATS = RACINE / "results"
REPETITIONS = 10

LITTERAUX = ["end", "the", "Sargon", "Babylon"]
REGEX = ["a.b", "(the|and)", "a.*e", "S(a|g|r)*on", "B(a|e)*by"]


def rechercher_python(motif, methode):
    """Compile le motif puis compte les lignes correspondantes du fichier."""
    correspond = clone.compiler(motif, methode)
    return sum(1 for ligne in clone.lignes(FICHIER) if correspond(ligne))


def rechercher_grep(motif):
    resultat = subprocess.run(["grep", "-E", "-c", "--", motif, str(FICHIER)],
                              capture_output=True, text=True)
    if resultat.returncode not in (0, 1):
        raise RuntimeError(resultat.stderr)
    return int(resultat.stdout)


def mesurer(fonction):
    """Retourne (moyenne, écart-type, résultat) sur REPETITIONS exécutions."""
    fonction()  # chauffe, non mesurée
    temps, resultats = [], set()
    for _ in range(REPETITIONS):
        debut = time.perf_counter()
        resultats.add(fonction())
        temps.append(time.perf_counter() - debut)
    if len(resultats) != 1:
        raise RuntimeError("résultats différents d'une exécution à l'autre")
    return statistics.mean(temps), statistics.stdev(temps), resultats.pop()


def tailles_automates(motif):
    debut, fin = clone.construire_afn(clone.parse_regex(motif))
    afd = clone.construire_afd(debut, fin)
    afd_min = clone.minimiser_afd(afd)
    return len(clone.etats_afn(debut)), len(afd.transitions), len(afd_min.transitions)


def main():
    print(f"Fichier : {FICHIER.name}, {REPETITIONS} répétitions\n")
    lignes_csv = []
    campagnes = [(m, ["KMP", "AFD", "grep"]) for m in LITTERAUX] + \
                [(m, ["AFD", "grep"]) for m in REGEX]

    for motif, methodes in campagnes:
        comptes = set()
        for methode in methodes:
            if methode == "grep":
                moy, ecart, nb = mesurer(lambda: rechercher_grep(motif))
            else:
                moy, ecart, nb = mesurer(lambda: rechercher_python(motif, methode))
            comptes.add(nb)
            print(f"{motif:12} {methode:5} {nb:6} lignes  {moy:.4f} s ± {ecart:.4f}")
            lignes_csv.append([motif, "literal" if motif in LITTERAUX else "regex",
                               methode, nb, REPETITIONS, f"{moy:.6f}", f"{ecart:.6f}"])
        if len(comptes) != 1:
            raise RuntimeError(f"nombre de lignes différent selon la méthode pour {motif}")

    with open(RESULTATS / "benchmark_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Pattern", "Type", "Method", "Matching_lines",
                         "Repetitions", "Mean_s", "Std_s"])
        writer.writerows(lignes_csv)

    with open(RESULTATS / "automata_sizes.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Pattern", "NFA_states", "DFA_states", "Min_DFA_states"])
        for motif in LITTERAUX + REGEX:
            writer.writerow([motif, *tailles_automates(motif)])

    print(f"\nRésultats enregistrés dans {RESULTATS}")


if __name__ == "__main__":
    main()

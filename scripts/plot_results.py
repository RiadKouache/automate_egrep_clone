"""Trace les diagrammes bâton (moyenne + écart-type) à partir de results/benchmark_results.csv."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

RESULTATS = Path(__file__).resolve().parent.parent / "results"
FIGURES = RESULTATS / "figures"

LIBELLES = {"KMP": "Clone : KMP", "AFD": "Clone : AFD minimal", "grep": "GNU grep -E"}
COULEURS = {"KMP": "tab:blue", "AFD": "tab:orange", "grep": "tab:green"}


def tracer(lignes, type_motif, titre, fichier):
    motifs = list(dict.fromkeys(l["Pattern"] for l in lignes if l["Type"] == type_motif))
    methodes = list(dict.fromkeys(l["Method"] for l in lignes if l["Type"] == type_motif))
    x = np.arange(len(motifs))
    largeur = 0.8 / len(methodes)

    fig, ax = plt.subplots(figsize=(8, 4))
    for k, methode in enumerate(methodes):
        donnees = {l["Pattern"]: l for l in lignes if l["Method"] == methode}
        moy = [float(donnees[m]["Mean_s"]) for m in motifs]
        ecart = [float(donnees[m]["Std_s"]) for m in motifs]
        ax.bar(x + (k - (len(methodes) - 1) / 2) * largeur, moy, largeur,
               yerr=ecart, capsize=4, label=LIBELLES[methode], color=COULEURS[methode])

    ax.set_xticks(x)
    ax.set_xticklabels(motifs)
    ax.set_xlabel("Motif")
    ax.set_ylabel("Temps moyen (s)")
    ax.set_title(titre)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(FIGURES / fichier, dpi=200)
    plt.close(fig)
    print("Figure créée :", FIGURES / fichier)


def main():
    FIGURES.mkdir(parents=True, exist_ok=True)
    with open(RESULTATS / "benchmark_results.csv", encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))
    tracer(lignes, "literal", "Motifs littéraux : KMP, AFD et grep -E", "benchmark_literal.png")
    tracer(lignes, "regex", "Expressions régulières : AFD et grep -E", "benchmark_regex.png")


if __name__ == "__main__":
    main()

"""Génère le corpus synthétique data/test_performance.txt (500 000 lignes).

Le fichier contient des correspondances connues du motif S(a|g|r)*on
(toutes les 15 000 lignes), des pièges proches du motif (toutes les 5 000
lignes) et du texte de remplissage. La graine fixe rend le fichier reproductible.
"""
import random
from pathlib import Path

SORTIE = Path(__file__).resolve().parent.parent / "data" / "test_performance.txt"
NB_LIGNES = 500000

mots_pieges = ["Simon", "Sauron", "Salomon", "Saaaaaa", "Sgronx", "onSagon", "Sargom"]
mots_valides = ["Son", "Saon", "Sgon", "Sron", "Sagon", "Sagaragon", "Srrrrgggaaon"]

random.seed(56667)
with open(SORTIE, "w", encoding="utf-8", newline="\n") as f:
    for i in range(NB_LIGNES):
        if i % 15000 == 0:  # vraie correspondance
            f.write(f"Ligne {i} - Match validé : {random.choice(mots_valides)} test.\n")
        elif i % 5000 == 0:  # piège
            f.write(f"Ligne {i} - Attention au piège : {random.choice(mots_pieges)} test.\n")
        else:
            f.write(f"Ligne {i} - Texte de remplissage standard pour alourdir le fichier.\n")

print(f"{SORTIE} généré ({NB_LIGNES} lignes).")

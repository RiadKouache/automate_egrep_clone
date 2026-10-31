"""Test différentiel : compare la sortie de egrep_clone.py avec celle de grep -E.

Pour chaque fichier de test et chaque motif, les lignes affichées (octet par
octet) et le code de retour doivent être identiques. Le résumé est écrit dans
results/validation_results.csv. Code de retour du script : 0 si tout est OK.
"""
import csv
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
CLONE = RACINE / "src" / "egrep_clone.py"
SORTIE = RACINE / "results" / "validation_results.csv"

FICHIERS = {
    "gutenberg_56667.txt": [
        # motifs littéraux (KMP)
        "end", "the", "Sargon", "Babylon", "zzzz",
        # expressions régulières (automate)
        "a.b", "(the|and)", "a.*e", "S(a|g|r)*on", "(a|b)*c",
        "((ab)*|c)d", "B(a|e)*by", ".", "a*", "x(y|z)*",
    ],
    "test_performance.txt": [
        "S(a|g|r)*on", "Simon", "Sargom", "Ligne 0", "a.b", "ab*", "a|b",
    ],
}


def main():
    if not (RACINE / "data" / "test_performance.txt").exists():
        print("data/test_performance.txt absent : lancer scripts/generate_test_file.py")
        sys.exit(2)

    resultats, echecs = [], 0
    for nom, motifs in FICHIERS.items():
        chemin = RACINE / "data" / nom
        for motif in motifs:
            clone = subprocess.run([sys.executable, str(CLONE), motif, str(chemin)],
                                   capture_output=True)
            grep = subprocess.run(["grep", "-E", "--", motif, str(chemin)],
                                  capture_output=True)
            ok = clone.stdout == grep.stdout and clone.returncode == grep.returncode
            nb = len(grep.stdout.splitlines())
            echecs += not ok
            print(f"[{'OK' if ok else 'ÉCHEC'}] {nom:22} {motif!r:16} {nb:6} lignes")
            if not ok:
                print(f"    clone : {len(clone.stdout.splitlines())} lignes, code {clone.returncode}")
                print(f"    grep  : {nb} lignes, code {grep.returncode}")
            resultats.append([nom, motif, nb, len(clone.stdout.splitlines()),
                              "OK" if ok else "ECHEC"])

    with open(SORTIE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["File", "Pattern", "Grep_lines", "Clone_lines", "Result"])
        writer.writerows(resultats)

    print(f"\n{len(resultats) - echecs}/{len(resultats)} tests réussis -> {SORTIE}")
    sys.exit(1 if echecs else 0)


if __name__ == "__main__":
    main()

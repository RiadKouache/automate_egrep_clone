#!/usr/bin/env python3
"""Clone de egrep avec support partiel des ERE (projet DAAR 1).

Opérateurs pris en charge : parenthèses, alternative '|', concaténation,
étoile '*', point '.' (caractère universel) et caractères ASCII.

Chaîne de traitement d'un motif (Séance 1) :
    motif -> arbre syntaxique -> AFN avec epsilon-transitions (Aho-Ullman)
          -> AFD (méthode des sous-ensembles) -> AFD minimal -> recherche.
Si le motif est une simple suite de concaténations (aucun métacaractère),
la recherche utilise l'algorithme Knuth-Morris-Pratt (Séance 2).

Utilisation : python egrep_clone.py <regex> <fichier>
Comme egrep, le programme affiche les lignes contenant une sous-chaîne
reconnue par le motif. Code de retour : 0 (au moins une ligne), 1 (aucune), 2 (erreur).
"""
import sys

METACARACTERES = set("()|*.")
AUTRE = None  # symbole représentant tout caractère absent du motif


# --- 1. ARBRE SYNTAXIQUE (Parser) ---
class RegExTree: pass
class Concat(RegExTree):
    def __init__(self, gauche, droite): self.gauche, self.droite = gauche, droite
class Alternative(RegExTree):
    def __init__(self, gauche, droite): self.gauche, self.droite = gauche, droite
class Etoile(RegExTree):
    def __init__(self, enfant): self.enfant = enfant
class Carac(RegExTree):
    def __init__(self, caractere): self.caractere = caractere

def inserer_concat(regex):
    """Rend la concaténation explicite avec l'opérateur interne '&'
    ('&' et non '.', qui désigne déjà le caractère universel)."""
    res = ""
    for i in range(len(regex)):
        res += regex[i]
        if i + 1 < len(regex):
            c1, c2 = regex[i], regex[i+1]
            if c1 not in "(|" and c2 not in ")*|":
                res += "&"
    return res

def parse_regex(regex):
    """Construit l'arbre syntaxique avec deux piles (arbres et opérateurs).
    Priorités : '*' > '&' (concaténation) > '|'. Lève ValueError si le motif est invalide."""
    regex = inserer_concat(regex)
    pile_arbres = []
    pile_ops = []
    priorites = {'|': 1, '&': 2, '*': 3, '(': 0}
    arite = {'*': 1, '&': 2, '|': 2}

    def appliquer_op():
        op = pile_ops.pop()
        if op == '(' or len(pile_arbres) < arite[op]:
            raise ValueError("expression régulière mal formée")
        if op == '*':
            pile_arbres.append(Etoile(pile_arbres.pop()))
        elif op == '&':
            d, g = pile_arbres.pop(), pile_arbres.pop()
            pile_arbres.append(Concat(g, d))
        elif op == '|':
            d, g = pile_arbres.pop(), pile_arbres.pop()
            pile_arbres.append(Alternative(g, d))

    for c in regex:
        if c == '(':
            pile_ops.append(c)
        elif c == ')':
            while pile_ops and pile_ops[-1] != '(':
                appliquer_op()
            if not pile_ops:
                raise ValueError("parenthèse fermante sans ouvrante")
            pile_ops.pop()
        elif c in "*&|":
            while pile_ops and priorites[pile_ops[-1]] >= priorites[c]:
                appliquer_op()
            pile_ops.append(c)
        else:
            pile_arbres.append(Carac(c))

    while pile_ops:
        appliquer_op()

    if len(pile_arbres) != 1:
        raise ValueError("expression régulière vide ou mal formée")
    return pile_arbres[0]

# --- 2. AUTOMATE FINI NON DÉTERMINISTE (construction d'Aho-Ullman / Thompson) ---
class Etat:
    def __init__(self):
        self.transitions = {}  # caractère -> liste d'états ('.' = caractère universel)
        self.epsilon = []      # epsilon-transitions

def construire_afn(arbre):
    """Retourne (état initial, état final) de l'AFN reconnaissant le langage de l'arbre."""
    if isinstance(arbre, Carac):
        debut, fin = Etat(), Etat()
        debut.transitions[arbre.caractere] = [fin]
        return debut, fin
    elif isinstance(arbre, Concat):
        g_debut, g_fin = construire_afn(arbre.gauche)
        d_debut, d_fin = construire_afn(arbre.droite)
        g_fin.epsilon.append(d_debut)
        return g_debut, d_fin
    elif isinstance(arbre, Alternative):
        debut, fin = Etat(), Etat()
        g_debut, g_fin = construire_afn(arbre.gauche)
        d_debut, d_fin = construire_afn(arbre.droite)
        debut.epsilon.extend([g_debut, d_debut])
        g_fin.epsilon.append(fin)
        d_fin.epsilon.append(fin)
        return debut, fin
    elif isinstance(arbre, Etoile):
        debut, fin = Etat(), Etat()
        e_debut, e_fin = construire_afn(arbre.enfant)
        debut.epsilon.extend([e_debut, fin])
        e_fin.epsilon.extend([e_debut, fin])
        return debut, fin
    else:
        raise ValueError("Type de nœud inconnu dans l'arbre syntaxique.")

def etats_afn(debut):
    """Liste de tous les états accessibles depuis l'état initial (parcours en profondeur)."""
    vus, pile = {debut}, [debut]
    while pile:
        etat = pile.pop()
        for suivants in list(etat.transitions.values()) + [etat.epsilon]:
            for s in suivants:
                if s not in vus:
                    vus.add(s)
                    pile.append(s)
    return vus

def fermeture_epsilon(etats):
    pile = list(etats)
    fermeture = set(etats)
    while pile:
        etat = pile.pop()
        for suivant in etat.epsilon:
            if suivant not in fermeture:
                fermeture.add(suivant)
                pile.append(suivant)
    return fermeture

# --- 3. AUTOMATE FINI DÉTERMINISTE (méthode des sous-ensembles) ---
class AFD:
    def __init__(self, alphabet, transitions, finals, initial=0):
        self.alphabet = alphabet        # caractères du motif (le symbole AUTRE couvre le reste)
        self.transitions = transitions  # transitions[état][symbole] -> état
        self.finals = finals            # ensemble des états acceptants
        self.initial = initial

def construire_afd(afn_debut, afn_fin):
    """Déterminise l'AFN par la méthode des sous-ensembles.

    Pour chercher le motif n'importe où dans la ligne (comme egrep), l'état
    initial de l'AFN est réinjecté dans chaque sous-ensemble : l'AFD obtenu
    reconnaît donc Σ*·R, et une ligne correspond dès qu'un état final est atteint.
    """
    alphabet = sorted({c for e in etats_afn(afn_debut) for c in e.transitions if c != '.'})
    depart = fermeture_epsilon({afn_debut})
    initial = frozenset(depart)
    numeros = {initial: 0}
    a_traiter = [initial]
    transitions, finals = [{}], set()

    while a_traiter:
        sous_ensemble = a_traiter.pop()
        num = numeros[sous_ensemble]
        if afn_fin in sous_ensemble:
            finals.add(num)
        for symbole in alphabet + [AUTRE]:
            cibles = set()
            for etat in sous_ensemble:
                if symbole is not AUTRE:
                    cibles.update(etat.transitions.get(symbole, []))
                cibles.update(etat.transitions.get('.', []))
            suivant = frozenset(fermeture_epsilon(cibles) | depart)
            if suivant not in numeros:
                numeros[suivant] = len(transitions)
                transitions.append({})
                a_traiter.append(suivant)
            transitions[num][symbole] = numeros[suivant]

    return AFD(alphabet, transitions, finals)

# --- 4. MINIMISATION (raffinement de partitions, algorithme de Moore) ---
def minimiser_afd(afd):
    """Retourne l'AFD minimal équivalent : on sépare d'abord états finals et
    non finals, puis on raffine les classes tant que deux états d'une même
    classe ont, pour un symbole, des successeurs dans des classes différentes."""
    symboles = afd.alphabet + [AUTRE]
    nb_etats = len(afd.transitions)
    classe = [1 if e in afd.finals else 0 for e in range(nb_etats)]

    while True:
        signatures = {}
        nouvelle = []
        for e in range(nb_etats):
            sig = (classe[e],) + tuple(classe[afd.transitions[e][s]] for s in symboles)
            nouvelle.append(signatures.setdefault(sig, len(signatures)))
        if len(signatures) == len(set(classe)):
            break
        classe = nouvelle

    # Renumérotation : la classe de l'état initial reçoit le numéro 0
    ordre = {classe[afd.initial]: 0}
    for c in classe:
        ordre.setdefault(c, len(ordre))
    transitions = [None] * len(ordre)
    for e in range(nb_etats):
        c = ordre[classe[e]]
        if transitions[c] is None:
            transitions[c] = {s: ordre[classe[afd.transitions[e][s]]] for s in symboles}
    finals = {ordre[classe[e]] for e in afd.finals}
    return AFD(afd.alphabet, transitions, finals)

# --- 5. RECHERCHE DANS UNE LIGNE ---
def correspond_afd(afd, ligne):
    """Vrai si un préfixe de la ligne est reconnu par l'AFD (qui reconnaît Σ*·R),
    c'est-à-dire si un suffixe d'un préfixe — une sous-chaîne — appartient à R."""
    etat = afd.initial
    if etat in afd.finals:
        return True
    alphabet, transitions, finals = set(afd.alphabet), afd.transitions, afd.finals
    for c in ligne:
        etat = transitions[etat][c if c in alphabet else AUTRE]
        if etat in finals:
            return True  # arrêt dès la première occurrence
    return False

# --- 6. ALGORITHME KMP (motifs sans métacaractère) ---
def calculer_lps(motif):
    """lps[i] = longueur du plus long préfixe propre de motif[:i+1] qui en est aussi suffixe."""
    m = len(motif)
    lps = [0] * m
    longueur = 0
    i = 1

    while i < m:
        if motif[i] == motif[longueur]:
            longueur += 1
            lps[i] = longueur
            i += 1
        else:
            if longueur != 0:
                longueur = lps[longueur - 1]
            else:
                lps[i] = 0
                i += 1
    return lps

def recherche_kmp(motif, texte, lps):
    """Vrai si motif apparaît dans texte ; lps est précalculé une seule fois par motif."""
    m = len(motif)
    n = len(texte)
    if m == 0:
        return True

    i = 0  # index pour le texte
    j = 0  # index pour le motif

    while i < n:
        if motif[j] == texte[i]:
            i += 1
            j += 1

        if j == m:
            return True  # Motif trouvé
        elif i < n and motif[j] != texte[i]:
            if j != 0:
                j = lps[j-1]
            else:
                i += 1
    return False

# --- 7. PROGRAMME PRINCIPAL ---
def est_litteral(motif):
    """Un motif sans métacaractère est une suite de concaténations : on utilise KMP."""
    return not any(c in METACARACTERES for c in motif)

def compiler_automate(motif):
    """Motif -> arbre -> AFN -> AFD -> AFD minimal."""
    afn_debut, afn_fin = construire_afn(parse_regex(motif))
    return minimiser_afd(construire_afd(afn_debut, afn_fin))

def compiler(motif, methode=None):
    """Retourne une fonction ligne -> bool. methode : 'KMP', 'AFD' ou None (choix automatique)."""
    if methode is None:
        methode = "KMP" if est_litteral(motif) else "AFD"
    if methode == "KMP":
        lps = calculer_lps(motif)
        return lambda ligne: recherche_kmp(motif, ligne, lps)
    afd = compiler_automate(motif)
    return lambda ligne: correspond_afd(afd, ligne)

def lignes(chemin):
    """Lignes du fichier, sans le '\\n' final (un éventuel '\\r' est conservé, comme egrep)."""
    with open(chemin, encoding="utf-8", errors="surrogateescape", newline="") as fichier:
        for ligne in fichier:
            yield ligne[:-1] if ligne.endswith("\n") else ligne

def main():
    if len(sys.argv) != 3:
        print("Utilisation : python egrep_clone.py <regex> <fichier>", file=sys.stderr)
        sys.exit(2)

    motif, chemin = sys.argv[1], sys.argv[2]
    sys.stdout.reconfigure(encoding="utf-8", errors="surrogateescape", newline="\n")
    sys.stderr.reconfigure(encoding="utf-8")

    try:
        correspond = compiler(motif)
    except ValueError as e:
        print(f"Erreur : RegEx '{motif}' invalide ({e}).", file=sys.stderr)
        sys.exit(2)

    trouve = False
    try:
        for ligne in lignes(chemin):
            if correspond(ligne):
                try:
                    sys.stdout.write(ligne + "\n")
                except OSError:  # sortie fermée (ex. : ... | head)
                    sys.stderr.close()
                    sys.exit(0)
                trouve = True
    except OSError as e:
        print(f"Erreur : impossible de lire {chemin} ({e.strerror}).", file=sys.stderr)
        sys.exit(2)

    sys.exit(0 if trouve else 1)

if __name__ == "__main__":
    main()

import sys
import time

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
    res = ""
    for i in range(len(regex)):
        res += regex[i]
        if i + 1 < len(regex):
            c1, c2 = regex[i], regex[i+1]
            if c1 not in "(|" and c2 not in ")*|":
                res += "&" # CORRECTION: Utilisation de '&' pour ne pas confondre avec le point joker
    return res

def parse_regex(regex):
    regex = inserer_concat(regex)
    pile_arbres = []
    pile_ops = []
    priorites = {'|': 1, '&': 2, '*': 3, '(': 0} # CORRECTION: Priorité de '&'

    def appliquer_op():
        op = pile_ops.pop()
        if op == '*':
            pile_arbres.append(Etoile(pile_arbres.pop()))
        elif op == '&': # CORRECTION
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
            pile_ops.pop() 
        elif c in "*&|": # CORRECTION
            while pile_ops and priorites[pile_ops[-1]] >= priorites[c]:
                appliquer_op()
            pile_ops.append(c)
        else:
            pile_arbres.append(Carac(c))
            
    while pile_ops:
        appliquer_op()
        
    return pile_arbres[0] if pile_arbres else None

# --- 2. AUTOMATE (AFN) ---
class Etat:
    _id_counter = 0
    def __init__(self):
        self.id = Etat._id_counter
        Etat._id_counter += 1
        self.transitions = {} 
        self.epsilon = []     

def construire_afn(arbre):
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

# --- 3. RECHERCHE DANS LE TEXTE ---
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

def correspond_automate(afn_debut, afn_fin, texte):
    etats_courants = fermeture_epsilon({afn_debut})
    for char in texte:
        prochains_etats = set()
        for etat in etats_courants:
            if char in etat.transitions:
                prochains_etats.update(etat.transitions[char])
            # CORRECTION : Prise en compte du Joker '.'
            if '.' in etat.transitions and char != '.': 
                prochains_etats.update(etat.transitions['.'])
        etats_courants = fermeture_epsilon(prochains_etats)
    
    return afn_fin in etats_courants

def match_sous_chaine(afn_debut, afn_fin, ligne):
    for i in range(len(ligne)):
        if correspond_automate(afn_debut, afn_fin, ligne[i:]):
            return True
    return False

# --- 4. PROGRAMME PRINCIPAL ---
def main():
    if len(sys.argv) != 3:
        print("Utilisation : python egrep_clone.py <regex> <fichier>")
        sys.exit(1)

    regex_pattern = sys.argv[1]
    filename = sys.argv[2]

    try:
        arbre = parse_regex(regex_pattern)
        
        # AJOUT DE LA VÉRIFICATION ICI POUR PYLANCE
        if arbre is None:
            print(f"Erreur : La RegEx '{regex_pattern}' est invalide ou vide.")
            sys.exit(1)
            
        afn_debut, afn_fin = construire_afn(arbre)
        
        print(f"Recherche de '{regex_pattern}' dans {filename}...\n")
        
        debut_chrono = time.time() 
        
        lignes_trouvees = 0
        with open(filename, 'r', encoding='utf-8') as fichier:
            for ligne in fichier:
                ligne_propre = ligne.strip()
                if match_sous_chaine(afn_debut, afn_fin, ligne_propre):
                    print(ligne_propre)
                    lignes_trouvees += 1
                    
        fin_chrono = time.time()
        temps_execution = fin_chrono - debut_chrono
        
        print(f"\n--- Terminé ---")
        print(f"Lignes correspondantes : {lignes_trouvees}")
        print(f"Temps d'exécution : {temps_execution:.4f} secondes")
                    
    except FileNotFoundError:
        print(f"Erreur : Le fichier {filename} est introuvable.")
    except Exception as e:
        print(f"Erreur lors de l'exécution : {e}")

if __name__ == "__main__":
    main()
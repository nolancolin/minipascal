# ===== IMPORT =====

import AnalyseurLexical

# ===== CONSTANTES =====

NB_ID_MAX = 100

TYPE_ENT = 0
TYPE_CH = 1

NATURE_PROG = 0
NATURE_CONST = 1
NATURE_VAR = 2

# ===== VARIABLES GLOBALES =====

CURRENT_NATURE = None
CURRENT_ADRV = 0

ids={}
NB_CONST_CHAINE = 0
VAL_CONST_CHAINE = []


def search_id(nom) -> bool:
    return nom in ids

def add_id(nom) -> bool:
    global CURRENT_ADRV
    if search_id(nom): return AnalyseurLexical.erreur(5)
    if len(ids) == NB_ID_MAX: return AnalyseurLexical.erreur(8)
    ids[nom] = {"nature" : None, "type": None, "valeur": None, "adrv": CURRENT_ADRV}
    CURRENT_ADRV+=1
    return True

def print_ids():
    print("Table d'identificateurs :")
    for id in ids:
        print(f"{id} -> {ids[id]}")
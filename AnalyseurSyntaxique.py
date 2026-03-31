# ===== IMPORT =====

import TableSymboles
import AnalyseurLexical

# ===== VARIABLES GLOBALES =====

DERNIERE_ADR_VAR_GLOB = -1


def anasynt() -> bool:
    AnalyseurLexical.analex()
    if prog(): print("Le programme source est syntaxiquement correct.")
    else: return False

def tester(symbole) -> bool:
    if not AnalyseurLexical.token==symbole: return AnalyseurLexical.erreur(3)
    AnalyseurLexical.analex()
    return True
        
def prog() -> bool:
    if AnalyseurLexical.chaine != AnalyseurLexical.KEYWORDS[5]: return AnalyseurLexical.erreur(3)
    AnalyseurLexical.analex()
    if AnalyseurLexical.token != "id": return AnalyseurLexical.erreur(3)
    AnalyseurLexical.analex()
    if AnalyseurLexical.token != "ptvirg": return AnalyseurLexical.erreur(3)
    AnalyseurLexical.analex()
    if not decl_const(): return False
    AnalyseurLexical.analex()
    if not decl_var(): return False
    AnalyseurLexical.analex()
    if not bloc(): return False
    AnalyseurLexical.analex()
    if AnalyseurLexical.token != "pt": return AnalyseurLexical.erreur(3)
    return True
    
def definir_constante(nom : str, ul: str) -> bool:
    if not TableSymboles.add_id(nom): return AnalyseurLexical.erreur(5)
    TableSymboles.ids["nature"] = TableSymboles.CURRENT_NATURE
    if ul == "ent":
        TableSymboles.ids["type"] = TableSymboles.TYPE_ENT
        if TableSymboles.CURRENT_NATURE == TableSymboles.NATURE_CONST:
            TableSymboles.ids["valeur"] = AnalyseurLexical.nombre
    else:
        TableSymboles.ids["type"] = TableSymboles.TYPE_CH
        TableSymboles.VAL_CONST_CHAINE.append(AnalyseurLexical.chaine)
        TableSymboles.ids["valeur"] = TableSymboles.NB_CONST_CHAINE
        TableSymboles.NB_CONST_CHAINE+=1
    return True

def decl_const() -> bool:
    if AnalyseurLexical.chaine != AnalyseurLexical.KEYWORDS[0]: return True
    TableSymboles.CURRENT_NATURE = TableSymboles.NATURE_CONST
    AnalyseurLexical.analex()
    if AnalyseurLexical.token != "id": return AnalyseurLexical.erreur(3)
    nom_const = AnalyseurLexical.chaine
    AnalyseurLexical.analex()
    if AnalyseurLexical.token != "eg": return AnalyseurLexical.erreur(3)
    AnalyseurLexical.analex()
    if not AnalyseurLexical.token in ["ent","ch"]: return AnalyseurLexical.erreur(3)
    elif not definir_constante(nom_const, AnalyseurLexical.token): return False
    AnalyseurLexical.analex()
    while AnalyseurLexical.token == "virg":
        AnalyseurLexical.analex()
        if AnalyseurLexical.token != "id": return AnalyseurLexical.erreur(3)
        nom_const = AnalyseurLexical.chaine
        AnalyseurLexical.analex()
        if AnalyseurLexical.token != "eg": return AnalyseurLexical.erreur(3)
        AnalyseurLexical.analex()
        if not AnalyseurLexical.token in ["ent","ch"]: return AnalyseurLexical.erreur(3)
        elif not definir_constante(nom_const, AnalyseurLexical.token): return False
        AnalyseurLexical.analex()
    if AnalyseurLexical.token != "ptvirg": return AnalyseurLexical.erreur(3)
    return True

def decl_var() -> bool:
    global DERNIERE_ADR_VAR_GLOB
    if AnalyseurLexical.chaine != AnalyseurLexical.KEYWORDS[6]: return True
    TableSymboles.CURRENT_NATURE = TableSymboles.NATURE_VAR
    AnalyseurLexical.analex()
    if AnalyseurLexical.token != "id": return AnalyseurLexical.erreur(3)
    elif not definir_constante(AnalyseurLexical.chaine, "ent"): return False
    DERNIERE_ADR_VAR_GLOB+=1
    AnalyseurLexical.analex()
    while AnalyseurLexical.token == "virg":
        AnalyseurLexical.analex()
        if AnalyseurLexical.token != "id": return AnalyseurLexical.erreur(3)
        DERNIERE_ADR_VAR_GLOB+=1
        AnalyseurLexical.analex()
    if AnalyseurLexical.token != "ptvirg": return AnalyseurLexical.erreur(3)
    return True

def bloc() -> bool:
    if AnalyseurLexical.chaine != AnalyseurLexical.KEYWORDS[1]: return False
    AnalyseurLexical.analex()
    if not instruction(): return False
    AnalyseurLexical.analex()
    while AnalyseurLexical.token == "ptvirg":
        AnalyseurLexical.analex()
        if not instruction(): return False
        AnalyseurLexical.analex()
    return AnalyseurLexical.erreur(3) if AnalyseurLexical.chaine == AnalyseurLexical.KEYWORDS[3] else True

def instruction() -> bool:
    return affectation() or lecture() or ecriture() or bloc()

def affectation() -> bool:
    if AnalyseurLexical.token != "id": return AnalyseurLexical.erreur(3)
    if not TableSymboles.search_id(AnalyseurLexical.chaine): return AnalyseurLexical.erreur(6)
    if TableSymboles.ids[AnalyseurLexical.chaine]["nature"] == TableSymboles.NATURE_CONST: return AnalyseurLexical.erreur(7)
    AnalyseurLexical.analex()
    if AnalyseurLexical.token != "aff": return AnalyseurLexical.erreur(3)
    AnalyseurLexical.analex()
    return exp()

def lecture() -> bool:
    if AnalyseurLexical.chaine != AnalyseurLexical.KEYWORDS[4]: return False
    AnalyseurLexical.analex()
    if AnalyseurLexical.token != "parouv": return AnalyseurLexical.erreur(3)
    AnalyseurLexical.analex()
    if AnalyseurLexical.token != "id": return AnalyseurLexical.erreur(3)
    if not TableSymboles.search_id(AnalyseurLexical.chaine): return AnalyseurLexical.erreur(6)
    if TableSymboles.ids[AnalyseurLexical.chaine]["nature"] != TableSymboles.NATURE_VAR: return AnalyseurLexical.erreur(7)
    while AnalyseurLexical.token == "virg":
        AnalyseurLexical.analex()
        if AnalyseurLexical.token != "id": return AnalyseurLexical.erreur(3)
        if not TableSymboles.search_id(AnalyseurLexical.chaine): return AnalyseurLexical.erreur(6)
        if TableSymboles.ids[AnalyseurLexical.chaine]["nature"] != TableSymboles.NATURE_VAR: return AnalyseurLexical.erreur(7)
        AnalyseurLexical.analex()
    return AnalyseurLexical.erreur(3) if AnalyseurLexical.token != "parfer" else True

def ecriture() -> bool:
    if AnalyseurLexical.chaine != AnalyseurLexical.KEYWORDS[2]: return False
    AnalyseurLexical.analex()
    if AnalyseurLexical.token != "parouv": return AnalyseurLexical.erreur(3)
    AnalyseurLexical.analex()
    while AnalyseurLexical.token == "parfer":
        AnalyseurLexical.analex()
        if not ecr_exp(): return False
        AnalyseurLexical.analex()
        if AnalyseurLexical.token != "virg": return AnalyseurLexical.erreur(3)
    return True

def ecr_exp() -> bool:
    return AnalyseurLexical.erreur(3) if exp() or AnalyseurLexical.token == "ch" else True

def exp() -> bool:
    if not terme(): return False
    AnalyseurLexical.analex()
    return suite_terme()

def suite_terme() -> bool:
    if op_bin():
        AnalyseurLexical.analex()
        return exp()
    return True

def terme() -> bool:
    match AnalyseurLexical.token:
        case "ent": return True
        case "id": return AnalyseurLexical.erreur(6) if TableSymboles.search_id(AnalyseurLexical.chaine) else True
        case "parouv":
            AnalyseurLexical.analex()
            if not exp(): return False
            AnalyseurLexical.analex()
            if AnalyseurLexical.token != "parfer": return AnalyseurLexical.erreur(3)
            return
        case "moins":
            AnalyseurLexical.analex()
            return terme()
    return AnalyseurLexical.erreur(3)

def op_bin() -> bool:
    return AnalyseurLexical.erreur(3) if not AnalyseurLexical.token in ["plus","moins","mult","divi"] else True 
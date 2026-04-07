# ===== IMPORT =====

import TableSymboles
import AnalyseurLexical
import MachineVirtuelle

# ===== VARIABLES GLOBALES =====

DERNIERE_ADR_VAR_GLOB = -1

def anasynt() -> bool:
    if not prog(): return False
    print("Le programme source est syntaxiquement correct.")
    MachineVirtuelle.P_CODE[MachineVirtuelle.CO] = MachineVirtuelle.OPERATION.index("STOP")
    MachineVirtuelle.CO += 1
    return True

def prog() -> bool:
    AnalyseurLexical.analex()
    if AnalyseurLexical.chaine != AnalyseurLexical.KEYWORDS[5]: return AnalyseurLexical.erreur(3)
    AnalyseurLexical.analex()
    if AnalyseurLexical.token != "id": return AnalyseurLexical.erreur(3)
    AnalyseurLexical.analex()
    if AnalyseurLexical.token != "ptvirg": return AnalyseurLexical.erreur(3)
    AnalyseurLexical.analex()
    if not decl_const(): return False
    if not decl_var(): return False
    if not bloc(): return False
    # AnalyseurLexical.analex()
    return AnalyseurLexical.erreur(3) if AnalyseurLexical.token != "pt" else True

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
    AnalyseurLexical.analex()
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
        elif not definir_constante(AnalyseurLexical.chaine, "ent"): return False
        DERNIERE_ADR_VAR_GLOB+=1
        AnalyseurLexical.analex()
    if AnalyseurLexical.token != "ptvirg": return AnalyseurLexical.erreur(3)
    AnalyseurLexical.analex()
    return True

def bloc() -> bool:
    if AnalyseurLexical.chaine != AnalyseurLexical.KEYWORDS[1]: return False
    AnalyseurLexical.analex()
    if not instruction(): return False
    while AnalyseurLexical.chaine != AnalyseurLexical.KEYWORDS[3]:
        if AnalyseurLexical.token != "ptvirg": return AnalyseurLexical.erreur(3)
        AnalyseurLexical.analex()
        if not instruction(): return False
    AnalyseurLexical.analex()
    return True

# def instruction() -> bool:
#     return lecture() or ecriture() or bloc() or affectation()

def affectation() -> bool:
    if AnalyseurLexical.token != "id": return AnalyseurLexical.erreur(3)
    if not TableSymboles.search_id(AnalyseurLexical.chaine): return AnalyseurLexical.erreur(6)
    if TableSymboles.ids[AnalyseurLexical.chaine]["nature"] == TableSymboles.NATURE_CONST: return AnalyseurLexical.erreur(7)
    parse_affectation(True)
    AnalyseurLexical.analex()
    if AnalyseurLexical.token != "aff": return AnalyseurLexical.erreur(3)
    AnalyseurLexical.analex()
    if not exp(): return False
    parse_affectation(False)
    return True

def ecriture() -> bool:
    if AnalyseurLexical.chaine != AnalyseurLexical.KEYWORDS[2]: return False
    AnalyseurLexical.analex()
    if AnalyseurLexical.token != "parouv": return AnalyseurLexical.erreur(3)
    AnalyseurLexical.analex()
    if AnalyseurLexical.token == "parfer":
        parse_ecriture()
        return True
    if not ecr_exp(): return False
    while AnalyseurLexical.token == "virg":
        AnalyseurLexical.analex()
        if not ecr_exp(): return False
    if AnalyseurLexical.token != "parfer": return AnalyseurLexical.erreur(3)
    AnalyseurLexical.analex()
    return True

def lecture() -> bool:
    if AnalyseurLexical.chaine != AnalyseurLexical.KEYWORDS[4]: return False
    AnalyseurLexical.analex()
    if AnalyseurLexical.token != "parouv": return AnalyseurLexical.erreur(3)
    AnalyseurLexical.analex()
    if AnalyseurLexical.token != "id": return AnalyseurLexical.erreur(3)
    if not TableSymboles.search_id(AnalyseurLexical.chaine): return AnalyseurLexical.erreur(6)
    if TableSymboles.ids[AnalyseurLexical.chaine]["nature"] != TableSymboles.NATURE_VAR: return AnalyseurLexical.erreur(7)
    parse_lecture()
    AnalyseurLexical.analex()
    while AnalyseurLexical.token == "virg":
        AnalyseurLexical.analex()
        if AnalyseurLexical.token != "id": return AnalyseurLexical.erreur(3)
        if not TableSymboles.search_id(AnalyseurLexical.chaine): return AnalyseurLexical.erreur(6)
        if TableSymboles.ids[AnalyseurLexical.chaine]["nature"] != TableSymboles.NATURE_VAR: return AnalyseurLexical.erreur(7)
        parse_lecture()
        AnalyseurLexical.analex()
    if AnalyseurLexical.token != "parfer": return AnalyseurLexical.erreur(3)
    AnalyseurLexical.analex()
    return True

def ecr_exp() -> bool:
    if AnalyseurLexical.token == "ch": 
        parse_ecr_exp(True)
        AnalyseurLexical.analex()
        return True
    if exp():
        parse_ecr_exp(False)
        return True
    return AnalyseurLexical.erreur(3) 

def exp() -> bool:
    if not terme(): return False
    if AnalyseurLexical.token in ["plus","moins","mult","divi"]:
        if not suite_terme(): return False
        parse_exp()
        return True
    return True

def suite_terme() -> bool:
    if op_bin():
        AnalyseurLexical.analex()
        return exp()
    return True

def terme() -> bool:
    match AnalyseurLexical.token:
        case "ent":
            parse_terme("ent")
            AnalyseurLexical.analex()
            return True
        case "id": 
            if not TableSymboles.search_id(AnalyseurLexical.chaine): return AnalyseurLexical.erreur(6)
            parse_terme("id")
            AnalyseurLexical.analex()
            return True
        case "parouv":
            AnalyseurLexical.analex()
            if not exp(): return False
            if AnalyseurLexical.token != "parfer": return AnalyseurLexical.erreur(3)
            AnalyseurLexical.analex()
            return True
        case "moins":
            AnalyseurLexical.analex()
            if not terme(): return False
            parse_terme("moins")
            AnalyseurLexical.analex()
            return True
    return AnalyseurLexical.erreur(3)

def op_bin() -> bool:
    if AnalyseurLexical.token in ["plus","moins","mult","divi"]:
        parse_op_bin()
        return True
    return False


def definir_constante(nom : str, ul: str) -> bool:
    if not TableSymboles.add_id(nom): return AnalyseurLexical.erreur(5)
    TableSymboles.ids[nom]["nature"] = TableSymboles.CURRENT_NATURE
    if ul == "ent":
        TableSymboles.ids[nom]["type"] = TableSymboles.TYPE_ENT
        if TableSymboles.CURRENT_NATURE == TableSymboles.NATURE_CONST:
            TableSymboles.ids[nom]["valeur"] = AnalyseurLexical.nombre
            MachineVirtuelle.MEMVAR[TableSymboles.ids[nom]["adrv"]] = AnalyseurLexical.nombre
        else: MachineVirtuelle.MEMVAR[TableSymboles.ids[nom]["adrv"]] = None
    else:
        TableSymboles.ids[nom]["type"] = TableSymboles.TYPE_CH
        TableSymboles.VAL_CONST_CHAINE.append(AnalyseurLexical.chaine)
        TableSymboles.ids[nom]["valeur"] = TableSymboles.NB_CONST_CHAINE
        TableSymboles.NB_CONST_CHAINE+=1
    return True


def parse_affectation(firstPart: bool) -> None:
    if firstPart:
        MachineVirtuelle.P_CODE[MachineVirtuelle.CO] = MachineVirtuelle.OPERATION.index("EMPI")
        MachineVirtuelle.P_CODE[MachineVirtuelle.CO+1] = TableSymboles.ids[AnalyseurLexical.chaine]["adrv"]
        MachineVirtuelle.CO+=2
    else:
        MachineVirtuelle.P_CODE[MachineVirtuelle.CO] = MachineVirtuelle.OPERATION.index("AFFE")
        MachineVirtuelle.CO+=1

def parse_lecture():
    MachineVirtuelle.P_CODE[MachineVirtuelle.CO] = MachineVirtuelle.OPERATION.index("EMPI")
    MachineVirtuelle.P_CODE[MachineVirtuelle.CO+1] = TableSymboles.ids[AnalyseurLexical.chaine]["adrv"]
    MachineVirtuelle.P_CODE[MachineVirtuelle.CO+2] = MachineVirtuelle.OPERATION.index("LIRE")
    MachineVirtuelle.CO+=3

def parse_ecriture() -> None:
    MachineVirtuelle.P_CODE[MachineVirtuelle.CO] = MachineVirtuelle.OPERATION.index("ECRL")
    MachineVirtuelle.CO+=1

def parse_ecr_exp(ch: bool) -> None:
    if ch:
        MachineVirtuelle.P_CODE[MachineVirtuelle.CO] = MachineVirtuelle.OPERATION.index("ECRC")
        MachineVirtuelle.CO+=1
        for i in range(len(AnalyseurLexical.chaine)):
            MachineVirtuelle.P_CODE[MachineVirtuelle.CO+i] = ord(AnalyseurLexical.chaine[i])
        MachineVirtuelle.P_CODE[MachineVirtuelle.CO+len(AnalyseurLexical.chaine)] = MachineVirtuelle.OPERATION.index("FINC")
        MachineVirtuelle.CO+=len(AnalyseurLexical.chaine)+1
    else:
        MachineVirtuelle.P_CODE[MachineVirtuelle.CO] = MachineVirtuelle.OPERATION.index("ECRE")
        MachineVirtuelle.CO+=1

def parse_exp() -> None:
    MachineVirtuelle.P_CODE[MachineVirtuelle.CO] = MachineVirtuelle.PILOP.pop()
    MachineVirtuelle.CO+=1

def parse_terme(token : str) -> None:
    match token:
        case "ent":
            MachineVirtuelle.P_CODE[MachineVirtuelle.CO] = MachineVirtuelle.OPERATION.index("EMPI")
            MachineVirtuelle.P_CODE[MachineVirtuelle.CO+1] = AnalyseurLexical.nombre
            MachineVirtuelle.CO+=2
        case "id":
            MachineVirtuelle.P_CODE[MachineVirtuelle.CO] = MachineVirtuelle.OPERATION.index("EMPI")
            MachineVirtuelle.P_CODE[MachineVirtuelle.CO+1] = TableSymboles.ids[AnalyseurLexical.chaine]["adrv"]
            MachineVirtuelle.P_CODE[MachineVirtuelle.CO+2] = MachineVirtuelle.OPERATION.index("CONT")
            MachineVirtuelle.CO+=3
        case "moins":
            MachineVirtuelle.P_CODE[MachineVirtuelle.CO] = MachineVirtuelle.OPERATION.index("MOINS")
            MachineVirtuelle.CO+=1

def parse_op_bin() -> None:
    if AnalyseurLexical.token == "moins": idxOp = MachineVirtuelle.OPERATION.index("SOUS")
    else: idxOp = MachineVirtuelle.OPERATION.index(AnalyseurLexical.token.upper())
    MachineVirtuelle.PILOP.append(idxOp)


def instruction() -> bool:
    return inst_cond() or inst_non_cond()

def inst_non_cond() -> bool:
    return lecture() or ecriture() or bloc() or inst_repe() or affectation()

def parse_inst_cond(firstPart: bool) -> None:
    if firstPart:
        MachineVirtuelle.P_CODE[MachineVirtuelle.CO] = MachineVirtuelle.OPERATION.index("ALSN")
        MachineVirtuelle.PILOP.append(MachineVirtuelle.CO+1)
        MachineVirtuelle.CO+=2
    else:
        MachineVirtuelle.P_CODE[MachineVirtuelle.PILOP.pop()] = MachineVirtuelle.CO+2
        MachineVirtuelle.P_CODE[MachineVirtuelle.CO] = MachineVirtuelle.OPERATION.index("ALLE")
        MachineVirtuelle.PILOP.append(MachineVirtuelle.CO+1)
        MachineVirtuelle.CO+=2
        MachineVirtuelle.P_CODE[MachineVirtuelle.PILOP.pop()] = MachineVirtuelle.CO
    

def inst_cond() -> bool:
    if AnalyseurLexical.chaine != AnalyseurLexical.KEYWORDS[7]: return False
    AnalyseurLexical.analex()
    if not exp(): return False
    parse_inst_cond(True)
    if AnalyseurLexical.chaine != AnalyseurLexical.KEYWORDS[8]: return AnalyseurLexical.erreur(3)
    AnalyseurLexical.analex()
    if inst_cond():
        parse_inst_cond(False)
        AnalyseurLexical.analex()
        return True
    if not inst_non_cond(): return False
    parse_inst_cond(False)
    AnalyseurLexical.analex()
    if AnalyseurLexical.chaine == AnalyseurLexical.KEYWORDS[9]:
        AnalyseurLexical.analex()
        if not instruction(): return False
    AnalyseurLexical.analex()
    return True

def parse_inst_repe(part: bool) -> bool:
    match part:
        case 1:
            MachineVirtuelle.PILOP.append(MachineVirtuelle.CO)
            MachineVirtuelle.CO+=1
        case 2:
            MachineVirtuelle.P_CODE[MachineVirtuelle.CO] = MachineVirtuelle.OPERATION.index("ALSN")
            MachineVirtuelle.PILOP.append(MachineVirtuelle.CO+1)
            MachineVirtuelle.CO+=2
        case 3:
            MachineVirtuelle.P_CODE[MachineVirtuelle.PILOP.pop()] = MachineVirtuelle.CO+2
            MachineVirtuelle.P_CODE[MachineVirtuelle.CO] = MachineVirtuelle.OPERATION.index("ALLE")
            MachineVirtuelle.P_CODE[MachineVirtuelle.CO+1] = MachineVirtuelle.PILOP.pop()
            MachineVirtuelle.CO+=2
    
def inst_repe():
    if AnalyseurLexical.chaine != AnalyseurLexical.KEYWORDS[10]: return False
    parse_inst_repe(1)
    AnalyseurLexical.analex()
    if not exp(): return False
    parse_inst_repe(2)
    if AnalyseurLexical.chaine != AnalyseurLexical.KEYWORDS[8]: return AnalyseurLexical.erreur(3)
    AnalyseurLexical.analex()
    if not instruction(): return False
    parse_inst_repe(3)
    return True


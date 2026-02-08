# ===== IMPORT =====

import TableSymboles
import AnalyseurLexical

# ===== VARIABLES GLOBALES =====

unilex=None


def anasynt():
    global unilex
    AnalyseurLexical.analex()
    unilex=AnalyseurLexical.token


def tester(symbole):
    global unilex
    if unilex==symbole:
        AnalyseurLexical.analex()
        unilex=AnalyseurLexical.token
    else:
        print("Erreur")
        return
    
def prog():
    #TODO !!!
    pass

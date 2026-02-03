# ===== CONSTANTES =====

LONG_MAX_CHAINE = 50
MAX_INTEGER = 2**63 - 1

# ===== VARIABLES GLOBALES =====

source = None        # fichier source
carlu = None         # caractère courant
num_ligne = 1        # numéro de ligne

nombre = None        # entier reconnu
chaine = ""          # chaîne reconnue
token = None         # unité lexicale courante

letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
numbers = "0123456789"
symboles = ";:=+-*/()<>."


def erreur(num_erreur: int) -> None:
    match num_erreur:
        case 1: print(f"Nombre trop grand à la ligne {num_ligne} !")
        case 2: print(f"Chaîne de caractère trop grande à la ligne {num_ligne} !")
    return 

def reco_symb() -> str:
    global carlu
    
    ligne_actuelle = num_ligne
    type = "null"
    match carlu: 
        case ";": type = "ptvrig"
        case ".": type = "pt"
        case "=": type = "eg"
        case "+": type = "plus"
        case "-": type = "moins"
        case "*": type = "mult"
        case "/": type = "divi"
        case "(": type = "parouv"
        case ")": type = "parfer"
        case "<":
            avancer()
            if ligne_actuelle < num_ligne: type = "inf"
            match carlu:
                case "=": type = "infeg"
                case ">": type = ""
        case ">":
            avancer()
            type = "supeg" if ligne_actuelle == num_ligne and carlu == "=" else "sup"
        case ":":
            avancer()
            type = "aff" if ligne_actuelle == num_ligne and carlu == "=" else "twopts"
    avancer()
    return type
    
        
    

def reco_entier() -> str:
    global nombre, carlu
    nombre = 0

    while carlu in numbers:
        nombre = nombre * 10 + int(carlu)
        if nombre > MAX_INTEGER:
            erreur(1)
        avancer()

    return "ent"


def reco_chaine() -> str:
    global chaine, carlu
    chaine = ""
    taille = 0

    avancer()  # sauter le "

    while carlu and carlu != '"':
        chaine += carlu
        taille += 1
        if taille > LONG_MAX_CHAINE:
            erreur(2)
            return
        avancer()

    avancer()  # sauter le "

    return "ch"


def reco_ident_ou_mot_reserve() -> str:
    global chaine, carlu
    chaine = ""

    while carlu and (carlu in letters or carlu in numbers or carlu == '_'):
        chaine += carlu
        avancer()

    return "id"


def lire_car() -> None:
    global source, carlu, num_ligne

    if not source:
        carlu = None
        return

    carlu = source.read(1)
    if carlu == '':
        carlu = None
    elif carlu == '\n':
        num_ligne += 1


def initialiser(nom_fichier) -> None:
    global source, num_ligne
    source = open(nom_fichier, 'r')
    num_ligne = 1
    lire_car()


def avancer() -> None:
    lire_car()


def fermer() -> None:
    global source
    if source:
        source.close()
        source = None


def sauter_separateurs() -> None:
    global carlu

    while carlu:

        # sauter séparateurs
        while carlu == ' ' or carlu == '\t' or carlu == '\n':
            avancer()
            if not carlu:
                return

        # sauter commentaire
        if carlu == '{':
            niveau = 1
            avancer()

            while carlu and niveau > 0:
                if carlu == '{':
                    niveau += 1
                elif carlu == '}':
                    niveau -= 1
                avancer()
            continue

        break


def analex() -> None:
    global token , carlu 
    sauter_separateurs()
    if not carlu:
        token="EOF"
        return 
    if carlu in numbers:
        token=reco_entier()
        return
    if carlu in letters:
        token=reco_ident_ou_mot_reserve()
        return 
    if carlu == '"':
        token=reco_chaine()
        return
    if carlu in symboles:
        token=reco_symb()
        return
    # gérer les autres cas (opérateurs, ponctuation, etc.)
    else : 
        token=carlu
        avancer()
        return  



initialiser("Code.minipascal")

while True:
    analex()
    print(token)
    if token == "EOF":
        break

fermer()




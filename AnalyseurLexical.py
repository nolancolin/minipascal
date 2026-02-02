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


def erreur(num_erreur: int) -> None:
    pass


def reco_entier():
    global nombre, carlu
    nombre = 0

    while carlu in numbers:
        nombre = nombre * 10 + int(carlu)
        if nombre > MAX_INTEGER:
            erreur(1)
        avancer()

    return "ent"


def reco_chaine():
    global chaine, carlu
    chaine = ""
    taille = 0

    avancer()  # sauter le "

    while carlu is not None and carlu != '"':
        chaine += carlu
        taille += 1
        if taille > LONG_MAX_CHAINE:
            erreur(2)
            return
        avancer()

    avancer()  # sauter le "

    return "ch"


def reco_ident_ou_mot_reserve():
    global chaine, carlu
    chaine = ""

    while carlu is not None and (carlu in letters or carlu in numbers or carlu == '_'):
        chaine += carlu
        avancer()

    return "id"


def lire_car():
    global source, carlu, num_ligne

    if source is None:
        carlu = None
        return

    carlu = source.read(1)
    if carlu == '':
        carlu = None
    elif carlu == '\n':
        num_ligne += 1


def initialiser(nom_fichier):
    global source, num_ligne
    source = open(nom_fichier, 'r')
    num_ligne = 1
    lire_car()


def avancer():
    lire_car()


def fermer():
    global source
    if source:
        source.close()
        source = None


def sauter_separateurs():
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

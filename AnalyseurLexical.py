# ===== CONSTANTES =====

LONG_MAX_CHAINE = 50
MAX_INTEGER = 2**63 -1

# ===== VARIABLES GLOBALES =====

source = None        # fichier source
carlu = None         # caractère courant
num_ligne = 1        # numéro de ligne


nombre = None        # entier reconnu
chaine = ""          # chaîne reconnue
token = None         # unité lexicale courante

letters = ['a','z','e','r','t','y','u','i','o','p','q','s','d','f','g','h','j','k','l','m','w','x','c','v','b','n']
numbers = ['0','1','2','3','4','5','6','7','8','9']

def erreur(num_erreur: int) -> None:
    pass
    

def reco_entier():
    nombre = 0
    while carlu in numbers:
        nombre = nombre * 10 + int(carlu)
        if nombre > MAX_INTEGER:
            erreur(int)                     # Il faut trouver un numéro tq ce numéro renvoie une erreur "nombre trop grand"
        carlu = source.read(1)
    return "ent"

def reco_chaine():
    chaine = ""
    taille = 0
    while carlu is not '"':
        carlu = source.read(1)
        chaine += carlu
        taille += 1
        if taille > LONG_MAX_CHAINE:
            erreur(int)                     # Il faut trouver un numéro tq ce numéro renvoie une erreur "string trop grand"
            return
    return "ch"

def reco_ident_ou__mot_reserve():
    while carlu in letters or carlu in numbers or carlu is '_':
        carlu = source.read(1)

def lire_car():
    global source , carlu , num_ligne
    
    if source is None:
         carlu = None
         return
    
    carlu=source.read(1)
    if carlu=='':
        carlu=None
    elif carlu=='\n':
        num_ligne+=1


def initialiser(nom_fichier):
    global source, carlu, num_ligne
    source = open(nom_fichier, 'r') as file 
    num_ligne = 1
    lire_car()

def avancer():
    lire_car()

def fermer():
     global source
     if source :
          source.close()
          source=None




def sauter_separateurs():
    global carlu

    while carlu and (carlu == ' ' or carlu == '\t' or carlu == '\n' or carlu == '{'):

        #sauter séparateurs 
        while carlu == ' ' or carlu == '\t' or carlu == '\n':
            avancer()

        # sauter commentaire 
        if carlu == '{':
            avancer() 
            while carlu and carlu != '}':
                avancer()
            if carlu == '}':
                avancer()



    

        


    
    

     
     
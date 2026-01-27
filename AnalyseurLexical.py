# ===== VARIABLES GLOBALES =====

source = None        # fichier source
carlu = None         # caractère courant
num_ligne = 1        # numéro de ligne


nombre = None        # entier reconnu
chaine = ""          # chaîne reconnue
token = None         # unité lexicale courante


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

    while carlu is not None and (carlu == ' ' or carlu == '\t' or carlu == '\n' or carlu == '{'):

        #sauter séparateurs 
        while carlu == ' ' or carlu == '\t' or carlu == '\n':
            avancer()

        # sauter commentaire 
        if carlu == '{':
            avancer() 
            while carlu is not None and carlu != '}':
                avancer()
            if carlu == '}':
                avancer()



    

        


    
    

     
     
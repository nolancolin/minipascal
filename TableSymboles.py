# ===== VARIABLES GLOBALES =====

ids={}



def search_id(nom):
    return nom in ids 

def add_id(nom):
    if not search_id(nom):
        ids[nom] = {}

def print_ids():
    print("Ids : ",end="")
    idsList = list(ids.keys())
    print(idsList[0],end="")
    for i in range(1,len(idsList)):
        print(", "+idsList[i],end="")
    print(".")
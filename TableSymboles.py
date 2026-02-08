# ===== VARIABLES GLOBALES =====

ids={}



def search_id(nom):
    return nom in ids 

def add_id(nom):
    if search_id(nom):
        return
    else:
        ids[nom]={}

def print_ids():
    for i in ids.keys():
        print(i)
import AnalyseurLexical, AnalyseurSyntaxique, MachineVirtuelle

nom_fichier = "Code.minipascal"

AnalyseurLexical.initialiser(nom_fichier)
if AnalyseurSyntaxique.anasynt():
    MachineVirtuelle.creer_fichier_code(nom_fichier)
    MachineVirtuelle.interpreterWithFile(nom_fichier)
    # MachineVirtuelle.interpreter()
AnalyseurLexical.fermer()
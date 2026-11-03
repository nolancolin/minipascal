"""Erreurs du compilateur et de la machine virtuelle, avec leur position dans le source."""


class ErreurMiniPascal(Exception):
    nom = "erreur"

    def __init__(self, message: str, ligne: int = 0, colonne: int = 0, longueur: int = 1) -> None:
        super().__init__(message)
        self.message = message
        self.ligne = ligne
        self.colonne = colonne
        self.longueur = max(1, longueur)   # nombre de ^ sous la partie fautive


class ErreurCompilation(ErreurMiniPascal):
    pass


class ErreurLexicale(ErreurCompilation):
    nom = "erreur lexicale"


class ErreurSyntaxique(ErreurCompilation):
    nom = "erreur syntaxique"


class ErreurSemantique(ErreurCompilation):
    nom = "erreur sémantique"


class ErreurExecution(ErreurMiniPascal):
    nom = "erreur d'exécution"

"""Exceptions du compilateur et de la machine virtuelle.

Toutes les erreurs de compilation portent la position (ligne, colonne) du
problème pour pouvoir afficher la ligne fautive avec un pointeur ``^``.
"""

from __future__ import annotations


class ErreurCompilation(Exception):
    """Erreur détectée avant l'exécution (lexicale, syntaxique, sémantique)."""

    categorie = "Erreur"

    def __init__(self, message: str, ligne: int = 0, colonne: int = 0) -> None:
        super().__init__(message)
        self.message = message
        self.ligne = ligne
        self.colonne = colonne

    def formater(self, source: str | None = None, nom_fichier: str | None = None) -> str:
        lieu = nom_fichier or "<source>"
        if self.ligne:
            lieu += f":{self.ligne}"
            if self.colonne:
                lieu += f":{self.colonne}"
        texte = f"{lieu}: {self.categorie} : {self.message}"
        if source is not None and self.ligne:
            lignes = source.splitlines()
            if 1 <= self.ligne <= len(lignes):
                fautive = lignes[self.ligne - 1]
                texte += f"\n  {fautive}"
                if self.colonne:
                    texte += f"\n  {' ' * (self.colonne - 1)}^"
        return texte


class ErreurLexicale(ErreurCompilation):
    categorie = "Erreur lexicale"


class ErreurSyntaxique(ErreurCompilation):
    categorie = "Erreur syntaxique"


class ErreurSemantique(ErreurCompilation):
    categorie = "Erreur sémantique"


class ErreurExecution(Exception):
    """Erreur levée par la machine virtuelle (division par zéro, etc.)."""

    def __init__(self, message: str, ligne: int = 0) -> None:
        super().__init__(message)
        self.message = message
        self.ligne = ligne

    def formater(self, nom_fichier: str | None = None) -> str:
        lieu = nom_fichier or "<programme>"
        if self.ligne:
            lieu += f":{self.ligne}"
        return f"{lieu}: Erreur d'exécution : {self.message}"

"""Analyseur lexical : transforme le texte source en suite d'unités lexicales.

Les noms des unités (``ent``, ``ch``, ``id``, ``mot_res``, ``ptvirg``, ``aff``...)
sont ceux du cours. Chaque unité connaît sa ligne et sa colonne.
"""

from __future__ import annotations

from dataclasses import dataclass

from .erreurs import ErreurLexicale

LONG_MAX_CHAINE = 50
MAX_INTEGER = 2**63 - 1

MOTS_RESERVES = frozenset({
    "PROGRAMME", "CONST", "VAR", "DEBUT", "FIN",
    "LIRE", "ECRIRE",
    "SI", "ALORS", "SINON",
    "TANTQUE", "FAIRE",
    "REPETER", "JUSQUA",
    "POUR",
    "ET", "OU", "NON", "MOD",
})

SYMBOLES_SIMPLES = {
    ";": "ptvirg", ".": "pt", ",": "virg", "=": "eg",
    "+": "plus", "-": "moins", "*": "mult", "/": "divi",
    "(": "parouv", ")": "parfer",
    "<": "inf", ">": "sup", ":": "twopts",
}
SYMBOLES_DOUBLES = {
    "<=": "infeg", ">=": "supeg", "<>": "diff", ":=": "aff",
}

CHIFFRES = "0123456789"


@dataclass(frozen=True)
class Token:
    type: str            # ent, ch, id, mot_res, EOF ou un nom de symbole
    texte: str           # lexème tel qu'écrit dans le source
    valeur: int | str | None
    ligne: int
    colonne: int

    @property
    def est_mot_res(self) -> bool:
        return self.type == "mot_res"

    def est(self, mot: str) -> bool:
        """Vrai si l'unité est le mot réservé ``mot``."""
        return self.type == "mot_res" and self.texte == mot

    def description(self) -> str:
        """Texte lisible utilisé dans les messages d'erreur."""
        match self.type:
            case "EOF":
                return "la fin du fichier"
            case "ent":
                return f"le nombre {self.texte}"
            case "ch":
                return f"la chaîne \"{self.valeur}\""
            case "id":
                return f"l'identificateur '{self.texte}'"
            case _:
                return f"'{self.texte}'"


class AnalyseurLexical:
    """Lit le source caractère par caractère et fournit les unités une à une."""

    def __init__(self, source: str) -> None:
        self.source = source
        self.pos = 0
        self.ligne = 1
        self.colonne = 1

    # ----- lecture de caractères -----

    def _courant(self) -> str:
        return self.source[self.pos] if self.pos < len(self.source) else ""

    def _suivant(self) -> str:
        return self.source[self.pos + 1] if self.pos + 1 < len(self.source) else ""

    def _avancer(self) -> None:
        if self.pos >= len(self.source):
            return
        if self.source[self.pos] == "\n":
            self.ligne += 1
            self.colonne = 1
        else:
            self.colonne += 1
        self.pos += 1

    def _sauter_separateurs(self) -> None:
        while True:
            car = self._courant()
            if car and car in " \t\r\n":
                self._avancer()
            elif car == "{":
                self._sauter_commentaire()
            else:
                return

    def _sauter_commentaire(self) -> None:
        ligne, colonne = self.ligne, self.colonne
        niveau = 0
        while True:
            car = self._courant()
            if not car:
                raise ErreurLexicale("commentaire '{' jamais refermé", ligne, colonne)
            if car == "{":
                niveau += 1
            elif car == "}":
                niveau -= 1
            self._avancer()
            if niveau == 0:
                return

    # ----- reconnaissance des unités -----

    def suivant(self) -> Token:
        """Renvoie la prochaine unité lexicale (``EOF`` à la fin, indéfiniment)."""
        self._sauter_separateurs()
        car = self._courant()
        if not car:
            return Token("EOF", "", None, self.ligne, self.colonne)
        if car in CHIFFRES:
            return self._entier()
        if car.isalpha():
            return self._identificateur()
        if car in "\"'":
            return self._chaine()
        return self._symbole()

    def _entier(self) -> Token:
        ligne, colonne = self.ligne, self.colonne
        debut = self.pos
        while self._courant() and self._courant() in CHIFFRES:
            self._avancer()
        texte = self.source[debut:self.pos]
        valeur = int(texte)
        if valeur > MAX_INTEGER:
            raise ErreurLexicale(f"nombre trop grand ({texte})", ligne, colonne)
        if self._courant().isalpha() or self._courant() == "_":
            raise ErreurLexicale(
                f"identificateur mal formé : '{texte}{self._courant()}...'", ligne, colonne
            )
        return Token("ent", texte, valeur, ligne, colonne)

    def _identificateur(self) -> Token:
        ligne, colonne = self.ligne, self.colonne
        debut = self.pos
        while self._courant() and (self._courant().isalnum() or self._courant() == "_"):
            self._avancer()
        texte = self.source[debut:self.pos]
        type_ = "mot_res" if texte in MOTS_RESERVES else "id"
        return Token(type_, texte, texte, ligne, colonne)

    def _chaine(self) -> Token:
        ligne, colonne = self.ligne, self.colonne
        delimiteur = self._courant()
        self._avancer()
        contenu = []
        while self._courant() != delimiteur:
            car = self._courant()
            if not car or car == "\n":
                raise ErreurLexicale("chaîne de caractères non terminée", ligne, colonne)
            contenu.append(car)
            if len(contenu) > LONG_MAX_CHAINE:
                raise ErreurLexicale(
                    f"chaîne trop longue (maximum {LONG_MAX_CHAINE} caractères)", ligne, colonne
                )
            self._avancer()
        self._avancer()
        valeur = "".join(contenu)
        return Token("ch", f"{delimiteur}{valeur}{delimiteur}", valeur, ligne, colonne)

    def _symbole(self) -> Token:
        ligne, colonne = self.ligne, self.colonne
        car = self._courant()
        double = car + self._suivant()
        if double in SYMBOLES_DOUBLES:
            self._avancer()
            self._avancer()
            return Token(SYMBOLES_DOUBLES[double], double, double, ligne, colonne)
        if car in SYMBOLES_SIMPLES:
            self._avancer()
            return Token(SYMBOLES_SIMPLES[car], car, car, ligne, colonne)
        raise ErreurLexicale(f"caractère inattendu {car!r}", ligne, colonne)

    def tous(self) -> list[Token]:
        """Toutes les unités jusqu'à ``EOF`` inclus (pratique pour les tests)."""
        unites = []
        while True:
            unite = self.suivant()
            unites.append(unite)
            if unite.type == "EOF":
                return unites

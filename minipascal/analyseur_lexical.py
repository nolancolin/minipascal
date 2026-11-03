"""Analyseur lexical : découpe le source en unités lexicales (ent, ch, id, mot_res, symboles)."""

from dataclasses import dataclass

from .erreurs import ErreurLexicale

# ===== CONSTANTES =====

LONG_MAX_CHAINE = 50
MAX_INTEGER = 2**63 - 1

KEYWORDS = {
    "PROGRAMME", "CONST", "VAR", "DEBUT", "FIN", "LIRE", "ECRIRE",
    "SI", "ALORS", "SINON", "TANTQUE", "FAIRE", "REPETER", "JUSQUA", "POUR",
    "ET", "OU", "NON", "MOD",
}

SYMBOLES = {
    ";": "ptvirg", ".": "pt", ",": "virg", "=": "eg", "+": "plus", "-": "moins",
    "*": "mult", "/": "divi", "(": "parouv", ")": "parfer", "<": "inf", ">": "sup",
    ":": "twopts",
}
SYMBOLES_DOUBLES = {"<=": "infeg", ">=": "supeg", "<>": "diff", ":=": "aff"}

CHIFFRES = "0123456789"


@dataclass(frozen=True)
class Token:
    type: str        # ent, ch, id, mot_res, EOF ou nom du symbole (ptvirg, aff, ...)
    texte: str       # tel qu'il est écrit dans le source
    valeur: int | str | None
    ligne: int
    colonne: int

    def est(self, mot: str) -> bool:
        return self.type == "mot_res" and self.texte == mot

    def description(self) -> str:
        match self.type:
            case "EOF": return "la fin du fichier"
            case "ent": return f"le nombre {self.texte}"
            case "ch": return f"la chaîne {self.texte}"
            case "id": return f"l'identificateur '{self.texte}'"
            case _: return f"'{self.texte}'"


class AnalyseurLexical:

    def __init__(self, source: str) -> None:
        self.source = source
        self.pos = 0
        self.num_ligne = 1
        self.num_colonne = 1
        self.carlu = source[0] if source else ""   # caractère courant, "" à la fin

    # ===== LECTURE =====

    def lire_car(self) -> None:
        if not self.carlu:
            return
        if self.carlu == "\n":
            self.num_ligne += 1
            self.num_colonne = 1
        else:
            self.num_colonne += 1
        self.pos += 1
        self.carlu = self.source[self.pos] if self.pos < len(self.source) else ""

    def car_suivant(self) -> str:
        return self.source[self.pos + 1 : self.pos + 2]

    def sauter_separateurs(self) -> None:
        while self.carlu:
            if self.carlu in " \t\r\n":
                self.lire_car()
            elif self.carlu == "{":
                self.sauter_commentaire()
            else:
                return

    def sauter_commentaire(self) -> None:
        ligne, colonne = self.num_ligne, self.num_colonne
        niveau = 0
        while True:
            if not self.carlu:
                raise ErreurLexicale("commentaire '{' jamais refermé", ligne, colonne)
            if self.carlu == "{":
                niveau += 1
            elif self.carlu == "}":
                niveau -= 1
            self.lire_car()
            if niveau == 0:
                return

    # ===== RECONNAISSANCE =====

    def analex(self) -> Token:
        """Renvoie l'unité lexicale suivante (EOF à la fin, autant de fois qu'on veut)."""
        self.sauter_separateurs()
        if not self.carlu:
            return Token("EOF", "", None, self.num_ligne, self.num_colonne)
        if self.carlu in CHIFFRES:
            return self.reco_entier()
        if self.carlu.isalpha():
            return self.reco_ident_ou_mot_reserve()
        if self.carlu in "\"'":
            return self.reco_chaine()
        return self.reco_symb()

    def reco_entier(self) -> Token:
        ligne, colonne, debut = self.num_ligne, self.num_colonne, self.pos
        while self.carlu and self.carlu in CHIFFRES:
            self.lire_car()
        texte = self.source[debut:self.pos]
        if int(texte) > MAX_INTEGER:
            raise ErreurLexicale("nombre trop grand (64 bits maximum)", ligne, colonne, len(texte))
        if self.carlu.isalpha() or self.carlu == "_":
            raise ErreurLexicale("un identificateur ne peut pas commencer par un chiffre",
                                 ligne, colonne, len(texte) + 1)
        return Token("ent", texte, int(texte), ligne, colonne)

    def reco_ident_ou_mot_reserve(self) -> Token:
        ligne, colonne, debut = self.num_ligne, self.num_colonne, self.pos
        while self.carlu and (self.carlu.isalnum() or self.carlu == "_"):
            self.lire_car()
        texte = self.source[debut:self.pos]
        return Token("mot_res" if texte in KEYWORDS else "id", texte, texte, ligne, colonne)

    def reco_chaine(self) -> Token:
        ligne, colonne = self.num_ligne, self.num_colonne
        delim = self.carlu
        self.lire_car()  # sauter le " ou le '
        chaine = ""
        while self.carlu != delim:
            if not self.carlu or self.carlu == "\n":
                raise ErreurLexicale("chaîne de caractères jamais refermée", ligne, colonne)
            chaine += self.carlu
            if len(chaine) > LONG_MAX_CHAINE:
                raise ErreurLexicale(f"chaîne trop longue ({LONG_MAX_CHAINE} caractères maximum)",
                                     ligne, colonne)
            self.lire_car()
        self.lire_car()  # sauter le délimiteur de fin
        return Token("ch", delim + chaine + delim, chaine, ligne, colonne)

    def reco_symb(self) -> Token:
        ligne, colonne = self.num_ligne, self.num_colonne
        double = self.carlu + self.car_suivant()
        if double in SYMBOLES_DOUBLES:
            self.lire_car()
            self.lire_car()
            return Token(SYMBOLES_DOUBLES[double], double, double, ligne, colonne)
        if self.carlu in SYMBOLES:
            symb = self.carlu
            self.lire_car()
            return Token(SYMBOLES[symb], symb, symb, ligne, colonne)
        raise ErreurLexicale(f"caractère inattendu {self.carlu!r}", ligne, colonne)

    def tous(self) -> list[Token]:
        unites = [self.analex()]
        while unites[-1].type != "EOF":
            unites.append(self.analex())
        return unites

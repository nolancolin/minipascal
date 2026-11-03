"""Analyseur syntaxique (descente récursive) et générateur de P-code.

Grammaire (voir aussi le README) :

    programme   = "PROGRAMME" id ";" [decl_const] [decl_var] bloc "."
    decl_const  = "CONST" id "=" (nombre | chaine) { "," id "=" (nombre | chaine) } ";"
    decl_var    = "VAR" id { "," id } ";"
    bloc        = "DEBUT" liste "FIN"
    liste       = instruction { ";" instruction }
    instruction = [ affectation | lecture | ecriture | bloc | si | tantque
                  | repeter | pour ]                      (l'instruction vide est permise)
    affectation = id ":=" expression
    lecture     = "LIRE" "(" id { "," id } ")"
    ecriture    = "ECRIRE" "(" [ arg { "," arg } ] ")"
    arg         = chaine | expression
    si          = "SI" expression "ALORS" instruction [ "SINON" instruction ]
    tantque     = "TANTQUE" expression "FAIRE" instruction
    repeter     = "REPETER" liste "JUSQUA" expression
    pour        = "POUR" id ":=" expression "JUSQUA" expression "FAIRE" instruction

    expression  = conjonction { "OU" conjonction }
    conjonction = negation { "ET" negation }
    negation    = "NON" negation | comparaison
    comparaison = somme [ ("=" | "<>" | "<" | "<=" | ">" | ">=") somme ]
    somme       = produit { ("+" | "-") produit }
    produit     = facteur { ("*" | "/" | "MOD") facteur }
    facteur     = nombre | id | "(" expression ")" | "-" facteur | "+" facteur

Le P-code est produit en même temps que l'analyse (traduction dirigée par la
syntaxe). Les sauts en avant sont complétés après coup (« backpatching »).
"""

from __future__ import annotations

from .analyseur_lexical import AnalyseurLexical, Token
from .erreurs import ErreurSemantique, ErreurSyntaxique
from .pcode import Instruction, Programme
from .table_symboles import Nature, Symbole, TableSymboles, Type

ATTENDUS = {
    "ptvirg": "';'", "pt": "'.'", "eg": "'='", "aff": "':='",
    "parouv": "'('", "parfer": "')'", "virg": "','",
    "id": "un identificateur", "ent": "un nombre",
}

RELATIONS = {
    "eg": "EGAL", "diff": "DIFF", "inf": "INF",
    "infeg": "INFE", "sup": "SUP", "supeg": "SUPE",
}

# Une instruction vide est reconnue quand on tombe sur l'un de ces symboles.
FIN_D_INSTRUCTION_VIDE = {"FIN", "SINON", "JUSQUA"}


class AnalyseurSyntaxique:
    def __init__(self, source: str) -> None:
        self.lexer = AnalyseurLexical(source)
        self.table = TableSymboles()
        self.code: list[Instruction] = []
        self.token: Token = self.lexer.suivant()
        self.ligne_precedente = self.token.ligne
        self._nb_boucles_pour = 0

    # ===== outils =====

    def avancer(self) -> Token:
        courant = self.token
        self.ligne_precedente = courant.ligne
        self.token = self.lexer.suivant()
        return courant

    def erreur(self, message: str, token: Token | None = None):
        t = token or self.token
        raise ErreurSyntaxique(message, t.ligne, t.colonne)

    def erreur_attendu(self, attendu: str):
        self.erreur(f"attendu : {attendu} ; trouvé : {self.token.description()}")

    def attendre(self, type_: str) -> Token:
        if self.token.type != type_:
            self.erreur_attendu(ATTENDUS.get(type_, type_))
        return self.avancer()

    def attendre_mot(self, mot: str) -> Token:
        if not self.token.est(mot):
            self.erreur_attendu(f"'{mot}'")
        return self.avancer()

    def emettre(self, op: str, arg: int | str | None = None, ligne: int | None = None) -> int:
        self.code.append(Instruction(op, arg, self.ligne_precedente if ligne is None else ligne))
        return len(self.code) - 1

    def patcher(self, index: int, cible: int) -> None:
        ancienne = self.code[index]
        self.code[index] = Instruction(ancienne.op, cible, ancienne.ligne)

    def ici(self) -> int:
        """Adresse de la prochaine instruction à émettre."""
        return len(self.code)

    def symbole(self, token: Token) -> Symbole:
        symbole = self.table.chercher(token.texte)
        if symbole is None:
            raise ErreurSemantique(
                f"l'identificateur '{token.texte}' n'est pas déclaré", token.ligne, token.colonne
            )
        return symbole

    def variable(self, token: Token) -> Symbole:
        """Symbole d'une variable (en écriture : refuse constantes et chaînes)."""
        symbole = self.symbole(token)
        if symbole.nature is Nature.CONSTANTE:
            raise ErreurSemantique(
                f"'{token.texte}' est une constante, on ne peut pas la modifier",
                token.ligne, token.colonne,
            )
        return symbole

    # ===== point d'entrée =====

    def compiler(self) -> Programme:
        self.programme()
        return Programme(self.code, list(self.table.noms), list(self.table.initiales))

    # ===== déclarations =====

    def programme(self) -> None:
        self.attendre_mot("PROGRAMME")
        self.attendre("id")
        self.attendre("ptvirg")
        if self.token.est("CONST"):
            self.decl_const()
        if self.token.est("VAR"):
            self.decl_var()
        self.bloc()
        self.attendre("pt")
        if self.token.type != "EOF":
            self.erreur("du texte suit le '.' final du programme")
        self.emettre("STOP")

    def decl_const(self) -> None:
        self.avancer()
        while True:
            nom = self.attendre("id")
            self.attendre("eg")
            if self.token.type == "ch":
                valeur = self.avancer()
                self.table.ajouter(nom.texte, Nature.CONSTANTE, Type.CH, valeur.valeur,
                                   nom.ligne, nom.colonne)
            else:
                signe = 1
                if self.token.type in ("plus", "moins"):
                    signe = -1 if self.avancer().type == "moins" else 1
                if self.token.type != "ent":
                    self.erreur_attendu("un nombre ou une chaîne")
                valeur = self.avancer()
                self.table.ajouter(nom.texte, Nature.CONSTANTE, Type.ENT, signe * valeur.valeur,
                                   nom.ligne, nom.colonne)
            if self.token.type != "virg":
                break
            self.avancer()
        self.attendre("ptvirg")

    def decl_var(self) -> None:
        self.avancer()
        while True:
            nom = self.attendre("id")
            self.table.ajouter(nom.texte, Nature.VARIABLE, Type.ENT, None, nom.ligne, nom.colonne)
            if self.token.type != "virg":
                break
            self.avancer()
        self.attendre("ptvirg")

    # ===== instructions =====

    def bloc(self) -> None:
        self.attendre_mot("DEBUT")
        self.liste_instructions()
        if not self.token.est("FIN"):
            self.erreur_attendu("';' ou 'FIN'")
        self.avancer()

    def liste_instructions(self) -> None:
        self.instruction()
        while self.token.type == "ptvirg":
            self.avancer()
            self.instruction()

    def instruction(self) -> None:
        t = self.token
        if t.type == "id":
            self.affectation()
        elif t.type == "ptvirg":
            return
        elif t.type == "mot_res":
            if t.texte in FIN_D_INSTRUCTION_VIDE:
                return
            instructions = {
                "LIRE": self.lecture, "ECRIRE": self.ecriture, "DEBUT": self.bloc,
                "SI": self.si, "TANTQUE": self.tantque,
                "REPETER": self.repeter, "POUR": self.pour,
            }
            if t.texte not in instructions:
                self.erreur_attendu("une instruction")
            instructions[t.texte]()
        else:
            self.erreur_attendu("une instruction")

    def affectation(self) -> None:
        nom = self.avancer()
        symbole = self.variable(nom)
        if symbole.type is not Type.ENT:
            raise ErreurSemantique(f"'{nom.texte}' n'est pas une variable entière",
                                   nom.ligne, nom.colonne)
        self.attendre("aff")
        self.emettre("EMPI", symbole.adresse, nom.ligne)
        self.expression()
        self.emettre("AFFE", ligne=nom.ligne)

    def lecture(self) -> None:
        self.avancer()
        self.attendre("parouv")
        while True:
            nom = self.attendre("id")
            symbole = self.variable(nom)
            self.emettre("EMPI", symbole.adresse, nom.ligne)
            self.emettre("LIRE", ligne=nom.ligne)
            if self.token.type != "virg":
                break
            self.avancer()
        self.attendre("parfer")

    def ecriture(self) -> None:
        mot = self.avancer()
        self.attendre("parouv")
        if self.token.type == "parfer":
            self.emettre("ECRL", ligne=mot.ligne)
        else:
            while True:
                self.argument_ecriture()
                if self.token.type != "virg":
                    break
                self.avancer()
        self.attendre("parfer")

    def argument_ecriture(self) -> None:
        t = self.token
        chaine = None
        if t.type == "ch":
            chaine = t.valeur
        elif t.type == "id":
            symbole = self.symbole(t)
            if symbole.type is Type.CH:
                chaine = symbole.valeur
        if chaine is None:
            self.expression()
            self.emettre("ECRE")
            return
        self.avancer()
        if self.token.type not in ("virg", "parfer"):
            raise ErreurSemantique(
                "une chaîne ne peut pas servir dans un calcul (seulement dans ECRIRE)",
                t.ligne, t.colonne,
            )
        self.emettre("ECRC", chaine, t.ligne)

    def si(self) -> None:
        self.avancer()
        self.expression()
        self.attendre_mot("ALORS")
        saut_faux = self.emettre("ALSN")
        self.instruction()
        if self.token.est("SINON"):
            saut_fin = self.emettre("ALLE")
            self.patcher(saut_faux, self.ici())
            self.avancer()
            self.instruction()
            self.patcher(saut_fin, self.ici())
        else:
            self.patcher(saut_faux, self.ici())

    def tantque(self) -> None:
        self.avancer()
        debut = self.ici()
        self.expression()
        self.attendre_mot("FAIRE")
        sortie = self.emettre("ALSN")
        self.instruction()
        self.emettre("ALLE", debut)
        self.patcher(sortie, self.ici())

    def repeter(self) -> None:
        self.avancer()
        debut = self.ici()
        self.liste_instructions()
        if not self.token.est("JUSQUA"):
            self.erreur_attendu("';' ou 'JUSQUA'")
        self.avancer()
        self.expression()
        self.emettre("ALSN", debut)

    def pour(self) -> None:
        mot = self.avancer()
        nom = self.attendre("id")
        compteur = self.variable(nom)
        if compteur.type is not Type.ENT:
            raise ErreurSemantique(f"'{nom.texte}' n'est pas une variable entière",
                                   nom.ligne, nom.colonne)
        self.attendre("aff")
        # La borne est évaluée une seule fois, dans un mot mémoire caché.
        self._nb_boucles_pour += 1
        limite = self.table.reserver(f"$limite{self._nb_boucles_pour}")
        self.emettre("EMPI", compteur.adresse, nom.ligne)
        self.expression()
        self.emettre("AFFE", ligne=nom.ligne)
        self.attendre_mot("JUSQUA")
        self.emettre("EMPI", limite, mot.ligne)
        self.expression()
        self.emettre("AFFE", ligne=mot.ligne)
        self.attendre_mot("FAIRE")
        debut = self.ici()
        self.emettre("EMPI", compteur.adresse, mot.ligne)
        self.emettre("CONT", ligne=mot.ligne)
        self.emettre("EMPI", limite, mot.ligne)
        self.emettre("CONT", ligne=mot.ligne)
        self.emettre("INFE", ligne=mot.ligne)
        sortie = self.emettre("ALSN", ligne=mot.ligne)
        self.instruction()
        self.emettre("EMPI", compteur.adresse, mot.ligne)
        self.emettre("EMPI", compteur.adresse, mot.ligne)
        self.emettre("CONT", ligne=mot.ligne)
        self.emettre("EMPI", 1, mot.ligne)
        self.emettre("ADDI", ligne=mot.ligne)
        self.emettre("AFFE", ligne=mot.ligne)
        self.emettre("ALLE", debut, mot.ligne)
        self.patcher(sortie, self.ici())

    # ===== expressions (une fonction par niveau de priorité) =====

    def expression(self) -> None:
        self.conjonction()
        while self.token.est("OU"):
            op = self.avancer()
            self.conjonction()
            self.emettre("OU", ligne=op.ligne)

    def conjonction(self) -> None:
        self.negation()
        while self.token.est("ET"):
            op = self.avancer()
            self.negation()
            self.emettre("ET", ligne=op.ligne)

    def negation(self) -> None:
        if self.token.est("NON"):
            op = self.avancer()
            self.negation()
            self.emettre("NON", ligne=op.ligne)
        else:
            self.comparaison()

    def comparaison(self) -> None:
        self.somme()
        if self.token.type in RELATIONS:
            op = self.avancer()
            self.somme()
            self.emettre(RELATIONS[op.type], ligne=op.ligne)

    def somme(self) -> None:
        self.produit()
        while self.token.type in ("plus", "moins"):
            op = self.avancer()
            self.produit()
            self.emettre("ADDI" if op.type == "plus" else "SOUS", ligne=op.ligne)

    def produit(self) -> None:
        self.facteur()
        while self.token.type in ("mult", "divi") or self.token.est("MOD"):
            op = self.avancer()
            self.facteur()
            nom = {"mult": "MULT", "divi": "DIVI"}.get(op.type, "MODU")
            self.emettre(nom, ligne=op.ligne)

    def facteur(self) -> None:
        t = self.token
        match t.type:
            case "ent":
                self.avancer()
                self.emettre("EMPI", t.valeur, t.ligne)
            case "id":
                symbole = self.symbole(t)
                if symbole.type is not Type.ENT:
                    raise ErreurSemantique(
                        f"la constante chaîne '{t.texte}' ne peut pas servir dans un calcul",
                        t.ligne, t.colonne,
                    )
                self.avancer()
                self.emettre("EMPI", symbole.adresse, t.ligne)
                self.emettre("CONT", ligne=t.ligne)
            case "parouv":
                self.avancer()
                self.expression()
                self.attendre("parfer")
            case "moins":
                self.avancer()
                self.facteur()
                self.emettre("MOIN", ligne=t.ligne)
            case "plus":
                self.avancer()
                self.facteur()
            case "ch":
                raise ErreurSemantique(
                    "une chaîne ne peut pas servir dans un calcul (seulement dans ECRIRE)",
                    t.ligne, t.colonne,
                )
            case _:
                self.erreur_attendu("une expression")


def compiler(source: str) -> Programme:
    """Compile un programme MiniPascal (texte) en P-code."""
    return AnalyseurSyntaxique(source).compiler()

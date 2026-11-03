"""Analyseur syntaxique par descente récursive, qui génère le P-code au fur et à mesure.

Chaque règle de la grammaire (voir le README) est une méthode. Pour les sauts vers
l'avant (SI, TANTQUE, POUR) on émet l'instruction sans destination et on la complète
une fois qu'on connaît l'adresse.
"""

from .analyseur_lexical import AnalyseurLexical, Token
from .erreurs import ErreurSemantique, ErreurSyntaxique
from .pcode import Instruction, Programme
from .table_symboles import NATURE_CONST, NATURE_VAR, TYPE_CH, TYPE_ENT, Symbole, TableSymboles

# ===== CONSTANTES =====

ATTENDUS = {
    "ptvirg": "';'", "pt": "'.'", "eg": "'='", "aff": "':='", "parouv": "'('",
    "parfer": "')'", "virg": "','", "id": "un identificateur",
}

OP_REL = {"eg": "EGAL", "diff": "DIFF", "inf": "INF", "infeg": "INFE", "sup": "SUP", "supeg": "SUPE"}
OP_ADD = {"plus": "ADDI", "moins": "SOUS"}
OP_MUL = {"mult": "MULT", "divi": "DIVI"}

# mots sur lesquels une instruction vide s'arrête (ex : "x := 1; FIN")
FIN_INSTRUCTION = {"FIN", "SINON", "JUSQUA"}


class AnalyseurSyntaxique:

    def __init__(self, source: str) -> None:
        self.lex = AnalyseurLexical(source)
        self.table = TableSymboles()
        self.p_code: list[Instruction] = []
        self.token = self.lex.analex()
        self.ligne_prec = self.token.ligne   # ligne du dernier token consommé
        self.nb_pour = 0

    # ===== OUTILS =====

    def avancer(self) -> Token:
        t = self.token
        self.ligne_prec = t.ligne
        self.token = self.lex.analex()
        return t

    def erreur(self, message: str, t: Token | None = None, classe=ErreurSyntaxique):
        t = t or self.token
        raise classe(message, t.ligne, t.colonne, len(t.texte))

    def erreur_attendu(self, attendu: str):
        self.erreur(f"attendu {attendu}, trouvé {self.token.description()}")

    def attendre(self, type_: str) -> Token:
        if self.token.type != type_:
            self.erreur_attendu(ATTENDUS.get(type_, type_))
        return self.avancer()

    def attendre_mot(self, mot: str, attendu: str | None = None) -> Token:
        if not self.token.est(mot):
            self.erreur_attendu(attendu or f"'{mot}'")
        return self.avancer()

    def emettre(self, op: str, arg=None, ligne: int | None = None) -> int:
        self.p_code.append(Instruction(op, arg, self.ligne_prec if ligne is None else ligne))
        return len(self.p_code) - 1

    def completer(self, adr: int, cible: int) -> None:
        """Complète le saut émis à l'adresse adr maintenant qu'on connaît sa destination."""
        instr = self.p_code[adr]
        self.p_code[adr] = Instruction(instr.op, cible, instr.ligne)

    def co(self) -> int:
        """Adresse de la prochaine instruction."""
        return len(self.p_code)

    def symbole(self, t: Token) -> Symbole:
        s = self.table.search_id(t.texte)
        if s is None:
            self.erreur(f"'{t.texte}' n'est pas déclaré", t, ErreurSemantique)
        return s

    def variable(self, t: Token) -> Symbole:
        """Identificateur dans lequel on va écrire : doit être une variable."""
        s = self.symbole(t)
        if s.nature == NATURE_CONST:
            self.erreur(f"'{t.texte}' est une constante, on ne peut pas la modifier", t,
                        ErreurSemantique)
        return s

    # ===== PROGRAMME ET DÉCLARATIONS =====

    def anasynt(self) -> Programme:
        self.prog()
        return Programme(self.p_code, self.table.noms_memoire, self.table.valeurs_initiales)

    def prog(self) -> None:
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
            self.erreur("rien ne doit suivre le '.' final")
        self.emettre("STOP")

    def decl_const(self) -> None:
        self.avancer()
        while True:
            nom = self.attendre("id")
            self.attendre("eg")
            if self.token.type == "ch":
                self.table.add_id(nom.texte, NATURE_CONST, TYPE_CH, self.avancer().valeur,
                                  nom.ligne, nom.colonne)
            else:
                signe = -1 if self.token.type == "moins" else 1
                if self.token.type in ("plus", "moins"):
                    self.avancer()
                if self.token.type != "ent":
                    self.erreur_attendu("un nombre ou une chaîne")
                self.table.add_id(nom.texte, NATURE_CONST, TYPE_ENT, signe * self.avancer().valeur,
                                  nom.ligne, nom.colonne)
            if self.token.type != "virg":
                break
            self.avancer()
        self.attendre("ptvirg")

    def decl_var(self) -> None:
        self.avancer()
        while True:
            nom = self.attendre("id")
            self.table.add_id(nom.texte, NATURE_VAR, TYPE_ENT, None, nom.ligne, nom.colonne)
            if self.token.type != "virg":
                break
            self.avancer()
        self.attendre("ptvirg")

    # ===== INSTRUCTIONS =====

    def bloc(self) -> None:
        self.attendre_mot("DEBUT")
        self.suite_instructions()
        self.attendre_mot("FIN", "';' ou 'FIN'")

    def suite_instructions(self) -> None:
        self.instruction()
        while self.token.type == "ptvirg":
            self.avancer()
            self.instruction()

    def instruction(self) -> None:
        t = self.token
        if t.type == "id":
            return self.affectation()
        if t.type == "ptvirg" or (t.type == "mot_res" and t.texte in FIN_INSTRUCTION):
            return   # instruction vide
        match t.texte if t.type == "mot_res" else None:
            case "LIRE": self.lecture()
            case "ECRIRE": self.ecriture()
            case "DEBUT": self.bloc()
            case "SI": self.inst_cond()
            case "TANTQUE": self.inst_repe()
            case "REPETER": self.inst_repeter()
            case "POUR": self.inst_pour()
            case _: self.erreur_attendu("une instruction")

    def affectation(self) -> None:
        nom = self.avancer()
        s = self.variable(nom)
        self.attendre("aff")
        self.emettre("EMPI", s.adrv, nom.ligne)
        self.exp()
        self.emettre("AFFE", ligne=nom.ligne)

    def lecture(self) -> None:
        self.avancer()
        self.attendre("parouv")
        while True:
            nom = self.attendre("id")
            self.emettre("EMPI", self.variable(nom).adrv, nom.ligne)
            self.emettre("LIRE", ligne=nom.ligne)
            if self.token.type != "virg":
                break
            self.avancer()
        self.attendre("parfer")

    def ecriture(self) -> None:
        mot = self.avancer()
        self.attendre("parouv")
        if self.token.type == "parfer":
            self.emettre("ECRL", ligne=mot.ligne)   # ECRIRE() : retour à la ligne
        else:
            self.ecr_exp()
            while self.token.type == "virg":
                self.avancer()
                self.ecr_exp()
        self.attendre("parfer")

    def ecr_exp(self) -> None:
        # une chaîne (littérale ou constante) est écrite telle quelle, le reste est calculé
        t = self.token
        chaine = None
        if t.type == "ch":
            chaine = t.valeur
        elif t.type == "id" and (s := self.symbole(t)).type == TYPE_CH:
            chaine = s.valeur
        if chaine is None:
            self.exp()
            self.emettre("ECRE")
            return
        self.avancer()
        if self.token.type not in ("virg", "parfer"):
            self.erreur("une chaîne ne peut pas entrer dans un calcul", t, ErreurSemantique)
        self.emettre("ECRC", chaine, t.ligne)

    def inst_cond(self) -> None:
        # SI exp ALORS inst [SINON inst]
        self.avancer()
        self.exp()
        self.attendre_mot("ALORS")
        saut_sinon = self.emettre("ALSN")
        self.instruction()
        if self.token.est("SINON"):
            saut_fin = self.emettre("ALLE")
            self.completer(saut_sinon, self.co())
            self.avancer()
            self.instruction()
            self.completer(saut_fin, self.co())
        else:
            self.completer(saut_sinon, self.co())

    def inst_repe(self) -> None:
        # TANTQUE exp FAIRE inst
        self.avancer()
        debut = self.co()
        self.exp()
        self.attendre_mot("FAIRE")
        sortie = self.emettre("ALSN")
        self.instruction()
        self.emettre("ALLE", debut)
        self.completer(sortie, self.co())

    def inst_repeter(self) -> None:
        # REPETER inst {; inst} JUSQUA exp
        self.avancer()
        debut = self.co()
        self.suite_instructions()
        self.attendre_mot("JUSQUA", "';' ou 'JUSQUA'")
        self.exp()
        self.emettre("ALSN", debut)

    def inst_pour(self) -> None:
        # POUR i := exp JUSQUA exp FAIRE inst
        mot = self.avancer()
        nom = self.attendre("id")
        i = self.variable(nom).adrv
        self.attendre("aff")
        # la borne est calculée une seule fois et rangée dans un mot caché
        self.nb_pour += 1
        borne = self.table.reserver_mot(f"$borne{self.nb_pour}")
        ligne = mot.ligne

        self.emettre("EMPI", i, ligne)
        self.exp()
        self.emettre("AFFE", ligne=ligne)
        self.attendre_mot("JUSQUA")
        self.emettre("EMPI", borne, ligne)
        self.exp()
        self.emettre("AFFE", ligne=ligne)
        self.attendre_mot("FAIRE")

        debut = self.co()   # tant que i <= borne
        for op, arg in [("EMPI", i), ("CONT", None), ("EMPI", borne), ("CONT", None), ("INFE", None)]:
            self.emettre(op, arg, ligne)
        sortie = self.emettre("ALSN", ligne=ligne)
        self.instruction()
        for op, arg in [("EMPI", i), ("EMPI", i), ("CONT", None), ("EMPI", 1), ("ADDI", None),
                        ("AFFE", None), ("ALLE", debut)]:   # i := i + 1 puis on reboucle
            self.emettre(op, arg, ligne)
        self.completer(sortie, self.co())

    # ===== EXPRESSIONS : une méthode par niveau de priorité, du plus faible au plus fort =====

    def exp(self) -> None:
        self.exp_et()
        while self.token.est("OU"):
            op = self.avancer()
            self.exp_et()
            self.emettre("OU", ligne=op.ligne)

    def exp_et(self) -> None:
        self.exp_non()
        while self.token.est("ET"):
            op = self.avancer()
            self.exp_non()
            self.emettre("ET", ligne=op.ligne)

    def exp_non(self) -> None:
        if self.token.est("NON"):
            op = self.avancer()
            self.exp_non()
            self.emettre("NON", ligne=op.ligne)
        else:
            self.exp_rel()

    def exp_rel(self) -> None:
        self.exp_arith()
        if self.token.type in OP_REL:
            op = self.avancer()
            self.exp_arith()
            self.emettre(OP_REL[op.type], ligne=op.ligne)

    def exp_arith(self) -> None:
        # la boucle (et pas la récursion) donne l'associativité à gauche : a - b - c = (a - b) - c
        self.terme()
        while self.token.type in OP_ADD:
            op = self.avancer()
            self.terme()
            self.emettre(OP_ADD[op.type], ligne=op.ligne)

    def terme(self) -> None:
        self.facteur()
        while self.token.type in OP_MUL or self.token.est("MOD"):
            op = self.avancer()
            self.facteur()
            self.emettre(OP_MUL.get(op.type, "MODU"), ligne=op.ligne)

    def facteur(self) -> None:
        t = self.token
        match t.type:
            case "ent":
                self.avancer()
                self.emettre("EMPI", t.valeur, t.ligne)
            case "id":
                s = self.symbole(t)
                if s.type == TYPE_CH:
                    self.erreur(f"'{t.texte}' est une chaîne, elle ne peut pas entrer dans un calcul",
                                t, ErreurSemantique)
                self.avancer()
                self.emettre("EMPI", s.adrv, t.ligne)
                self.emettre("CONT", ligne=t.ligne)
            case "parouv":
                self.avancer()
                self.exp()
                self.attendre("parfer")
            case "moins":
                self.avancer()
                self.facteur()
                self.emettre("MOIN", ligne=t.ligne)
            case "plus":
                self.avancer()
                self.facteur()
            case "ch":
                self.erreur("une chaîne ne peut pas entrer dans un calcul", t, ErreurSemantique)
            case _:
                self.erreur_attendu("une expression")


def compiler(source: str) -> Programme:
    source = source.removeprefix("﻿")   # BOM ajouté par certains éditeurs Windows
    try:
        return AnalyseurSyntaxique(source).anasynt()
    except RecursionError:
        raise ErreurSyntaxique("programme trop imbriqué (trop de parenthèses ou de blocs)") from None

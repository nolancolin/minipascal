"""Machine virtuelle à pile : exécute le P-code produit par le compilateur."""

import sys
from typing import Callable

from .erreurs import ErreurExecution
from .pcode import Instruction, Programme

# ===== CONSTANTES =====

ENTIER_MIN = -(2**63)
ENTIER_MAX = 2**63 - 1
MAX_ETAPES = 10_000_000   # garde-fou contre les boucles infinies

COMPARAISONS = {
    "EGAL": lambda a, b: a == b, "DIFF": lambda a, b: a != b,
    "INF": lambda a, b: a < b, "INFE": lambda a, b: a <= b,
    "SUP": lambda a, b: a > b, "SUPE": lambda a, b: a >= b,
}


def ecrire_console(texte: str) -> None:
    sys.stdout.write(texte)
    sys.stdout.flush()


def division(a: int, b: int) -> int:
    """Division entière tronquée vers zéro, comme en Pascal (Python, lui, arrondit vers -inf)."""
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


class MachineVirtuelle:

    def __init__(self, prog: Programme, entree: Callable[[], str] = input,
                 sortie: Callable[[str], None] = ecrire_console,
                 max_etapes: int | None = MAX_ETAPES,
                 trace: Callable[[int, Instruction, list[int]], None] | None = None) -> None:
        self.prog = prog
        self.entree = entree
        self.sortie = sortie
        self.max_etapes = max_etapes
        self.trace = trace
        self.pilex: list[int] = []                          # pile d'exécution
        self.memvar: list[int | None] = list(prog.valeurs_initiales)
        self.co = 0                                         # compteur ordinal
        self.etapes = 0

    # ===== PILE =====

    def depiler(self) -> int:
        if not self.pilex:
            raise ErreurExecution("pile vide, le P-code est incorrect", self.ligne())
        return self.pilex.pop()

    def depiler2(self) -> tuple[int, int]:
        b = self.depiler()
        return self.depiler(), b

    def empiler(self, valeur: int) -> None:
        if not ENTIER_MIN <= valeur <= ENTIER_MAX:
            raise ErreurExecution("dépassement de capacité (entiers sur 64 bits)", self.ligne())
        self.pilex.append(valeur)

    def adresse(self) -> int:
        adr = self.depiler()
        if not 0 <= adr < len(self.memvar):
            raise ErreurExecution(f"adresse mémoire invalide : {adr}", self.ligne())
        return adr

    def ligne(self) -> int:
        return self.prog.p_code[self.co].ligne if self.co < len(self.prog.p_code) else 0

    # ===== EXÉCUTION =====

    def executer(self) -> None:
        p_code = self.prog.p_code
        self.co = 0
        while 0 <= self.co < len(p_code):
            instr = p_code[self.co]
            if self.trace:
                self.trace(self.co, instr, self.pilex)
            self.etapes += 1
            if self.max_etapes and self.etapes > self.max_etapes:
                raise ErreurExecution(f"plus de {self.max_etapes} instructions exécutées, "
                                      "boucle infinie ?", instr.ligne)
            if instr.op == "STOP":
                return
            saut = self.executer_instruction(instr)
            self.co = self.co + 1 if saut is None else saut
        raise ErreurExecution("le programme s'est arrêté sans rencontrer STOP")

    def executer_instruction(self, instr: Instruction) -> int | None:
        """Exécute une instruction ; renvoie l'adresse de saut s'il y en a une."""
        match instr.op:
            case "EMPI":
                self.empiler(instr.arg)
            case "CONT":
                adr = self.adresse()
                if self.memvar[adr] is None:
                    raise ErreurExecution(f"'{self.prog.noms_memoire[adr]}' est utilisée "
                                          "avant d'avoir reçu une valeur", instr.ligne)
                self.empiler(self.memvar[adr])
            case "AFFE":
                valeur = self.depiler()
                self.memvar[self.adresse()] = valeur
            case "ADDI":
                a, b = self.depiler2()
                self.empiler(a + b)
            case "SOUS":
                a, b = self.depiler2()
                self.empiler(a - b)
            case "MULT":
                a, b = self.depiler2()
                self.empiler(a * b)
            case "DIVI" | "MODU":
                a, b = self.depiler2()
                if b == 0:
                    raise ErreurExecution("division par zéro", instr.ligne)
                q = division(a, b)
                self.empiler(q if instr.op == "DIVI" else a - q * b)
            case "MOIN":
                self.empiler(-self.depiler())
            case "EGAL" | "DIFF" | "INF" | "INFE" | "SUP" | "SUPE":
                a, b = self.depiler2()
                self.empiler(int(COMPARAISONS[instr.op](a, b)))
            case "ET":
                a, b = self.depiler2()
                self.empiler(int(a != 0 and b != 0))
            case "OU":
                a, b = self.depiler2()
                self.empiler(int(a != 0 or b != 0))
            case "NON":
                self.empiler(int(self.depiler() == 0))
            case "LIRE":
                self.memvar[self.adresse()] = self.lire_entier(instr.ligne)
            case "ECRE":
                self.sortie(str(self.depiler()))
            case "ECRC":
                self.sortie(instr.arg)
            case "ECRL":
                self.sortie("\n")
            case "ALLE":
                return instr.arg
            case "ALSN":   # aller si non : saute quand la condition vaut 0
                if self.depiler() == 0:
                    return instr.arg
            case _:
                raise ErreurExecution(f"instruction inconnue : {instr.op}", instr.ligne)
        return None

    def lire_entier(self, ligne: int) -> int:
        try:
            texte = self.entree().strip()
        except EOFError:
            raise ErreurExecution("LIRE attendait un nombre mais l'entrée est terminée", ligne) from None
        try:
            valeur = int(texte)
        except ValueError:
            raise ErreurExecution(f"LIRE attendait un nombre entier, pas {texte!r}", ligne) from None
        if not ENTIER_MIN <= valeur <= ENTIER_MAX:
            raise ErreurExecution("nombre lu trop grand (64 bits maximum)", ligne)
        return valeur

"""Machine virtuelle à pile qui exécute le P-code."""

from __future__ import annotations

import sys
from typing import Callable

from .erreurs import ErreurExecution
from .pcode import Instruction, Programme

ENTIER_MIN = -(2**63)
ENTIER_MAX = 2**63 - 1
MAX_ETAPES_DEFAUT = 10_000_000


def _ecrire_stdout(texte: str) -> None:
    sys.stdout.write(texte)
    sys.stdout.flush()


class MachineVirtuelle:
    def __init__(
        self,
        programme: Programme,
        entree: Callable[[], str] = input,
        sortie: Callable[[str], None] = _ecrire_stdout,
        max_etapes: int | None = MAX_ETAPES_DEFAUT,
        trace: Callable[[int, Instruction, list[int]], None] | None = None,
    ) -> None:
        self.programme = programme
        self.entree = entree
        self.sortie = sortie
        self.max_etapes = max_etapes
        self.trace = trace
        self.pile: list[int] = []
        self.memoire: list[int | None] = list(programme.initiales)
        self.pc = 0
        self.etapes = 0

    # ----- pile -----

    def _depiler(self) -> int:
        if not self.pile:
            raise ErreurExecution("pile vide (P-code incorrect)", self._ligne())
        return self.pile.pop()

    def _depiler2(self) -> tuple[int, int]:
        b = self._depiler()
        a = self._depiler()
        return a, b

    def _empiler(self, valeur: int) -> None:
        if not ENTIER_MIN <= valeur <= ENTIER_MAX:
            raise ErreurExecution("dépassement de capacité (entier sur 64 bits)", self._ligne())
        self.pile.append(valeur)

    def _ligne(self) -> int:
        code = self.programme.instructions
        return code[self.pc].ligne if 0 <= self.pc < len(code) else 0

    def _adresse(self, adresse: int) -> int:
        if not 0 <= adresse < len(self.memoire):
            raise ErreurExecution(f"adresse mémoire invalide : {adresse}", self._ligne())
        return adresse

    # ----- exécution -----

    def executer(self) -> None:
        code = self.programme.instructions
        self.pc = 0
        while 0 <= self.pc < len(code):
            instr = code[self.pc]
            if self.trace:
                self.trace(self.pc, instr, list(self.pile))
            self.etapes += 1
            if self.max_etapes is not None and self.etapes > self.max_etapes:
                raise ErreurExecution(
                    f"plus de {self.max_etapes} instructions exécutées "
                    "(boucle infinie ? voir --max-etapes)", instr.ligne,
                )
            if instr.op == "STOP":
                return
            saut = self._executer_instruction(instr)
            self.pc = saut if saut is not None else self.pc + 1
        raise ErreurExecution("le programme s'est terminé sans instruction STOP")

    def _executer_instruction(self, instr: Instruction) -> int | None:
        op = instr.op
        match op:
            case "EMPI":
                self._empiler(instr.arg)
            case "CONT":
                adresse = self._adresse(self._depiler())
                valeur = self.memoire[adresse]
                if valeur is None:
                    raise ErreurExecution(
                        f"la variable '{self.programme.noms_memoire[adresse]}' "
                        "est utilisée avant d'avoir reçu une valeur", instr.ligne,
                    )
                self._empiler(valeur)
            case "AFFE":
                valeur = self._depiler()
                adresse = self._adresse(self._depiler())
                self.memoire[adresse] = valeur
            case "ADDI":
                a, b = self._depiler2()
                self._empiler(a + b)
            case "SOUS":
                a, b = self._depiler2()
                self._empiler(a - b)
            case "MULT":
                a, b = self._depiler2()
                self._empiler(a * b)
            case "DIVI" | "MODU":
                a, b = self._depiler2()
                if b == 0:
                    raise ErreurExecution("division par zéro", instr.ligne)
                quotient = abs(a) // abs(b)
                if (a < 0) != (b < 0):
                    quotient = -quotient
                # Comme en Pascal : le quotient est tronqué vers zéro, le reste a le signe de a.
                self._empiler(quotient if op == "DIVI" else a - quotient * b)
            case "MOIN":
                self._empiler(-self._depiler())
            case "EGAL" | "DIFF" | "INF" | "INFE" | "SUP" | "SUPE":
                a, b = self._depiler2()
                resultat = {
                    "EGAL": a == b, "DIFF": a != b, "INF": a < b,
                    "INFE": a <= b, "SUP": a > b, "SUPE": a >= b,
                }[op]
                self._empiler(int(resultat))
            case "ET":
                a, b = self._depiler2()
                self._empiler(int(bool(a) and bool(b)))
            case "OU":
                a, b = self._depiler2()
                self._empiler(int(bool(a) or bool(b)))
            case "NON":
                self._empiler(int(not self._depiler()))
            case "LIRE":
                adresse = self._adresse(self._depiler())
                self.memoire[adresse] = self._lire_entier(instr.ligne)
            case "ECRE":
                self.sortie(str(self._depiler()))
            case "ECRC":
                self.sortie(instr.arg)
            case "ECRL":
                self.sortie("\n")
            case "ALLE":
                return instr.arg
            case "ALSN":
                if self._depiler() == 0:
                    return instr.arg
            case _:
                raise ErreurExecution(f"instruction inconnue : {op}", instr.ligne)
        return None

    def _lire_entier(self, ligne: int) -> int:
        try:
            texte = self.entree().strip()
        except EOFError:
            raise ErreurExecution("fin de l'entrée : LIRE attendait un nombre", ligne) from None
        try:
            valeur = int(texte)
        except ValueError:
            raise ErreurExecution(f"LIRE attendait un nombre entier, reçu {texte!r}", ligne) from None
        if not ENTIER_MIN <= valeur <= ENTIER_MAX:
            raise ErreurExecution(f"nombre trop grand : {texte}", ligne)
        return valeur

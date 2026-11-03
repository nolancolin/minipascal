"""MiniPascal : compilateur vers P-code et machine virtuelle à pile."""

from __future__ import annotations

from .analyseur_syntaxique import compiler
from .erreurs import (
    ErreurCompilation, ErreurExecution, ErreurLexicale, ErreurSemantique, ErreurSyntaxique,
)
from .machine_virtuelle import MachineVirtuelle
from .pcode import Instruction, Programme, ecrire_cod, lire_cod

__all__ = [
    "compiler", "executer", "MachineVirtuelle", "Programme", "Instruction",
    "ecrire_cod", "lire_cod",
    "ErreurCompilation", "ErreurLexicale", "ErreurSyntaxique", "ErreurSemantique",
    "ErreurExecution",
]


def executer(source: str, entree: str = "", **options) -> str:
    """Compile et exécute ``source`` ; renvoie tout ce que le programme a écrit.

    ``entree`` est le texte fourni à LIRE (une valeur par ligne).
    """
    lignes = iter(entree.splitlines())

    def lire() -> str:
        try:
            return next(lignes)
        except StopIteration:
            raise EOFError from None

    sortie: list[str] = []
    MachineVirtuelle(compiler(source), entree=lire, sortie=sortie.append, **options).executer()
    return "".join(sortie)

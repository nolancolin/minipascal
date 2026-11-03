"""MiniPascal : compilateur vers P-code et machine virtuelle à pile."""

from .analyseur_syntaxique import compiler
from .erreurs import (ErreurCompilation, ErreurExecution, ErreurLexicale, ErreurMiniPascal,
                      ErreurSemantique, ErreurSyntaxique)
from .machine_virtuelle import MachineVirtuelle
from .pcode import Instruction, Programme, ecrire_cod, lire_cod


def executer(source: str, entree: str = "", **options) -> str:
    """Compile et exécute source, avec entree comme clavier (une valeur par ligne).
    Renvoie tout ce que le programme a écrit."""
    lignes = iter(entree.splitlines())

    def lire() -> str:
        try:
            return next(lignes)
        except StopIteration:
            raise EOFError from None

    sortie: list[str] = []
    MachineVirtuelle(compiler(source), entree=lire, sortie=sortie.append, **options).executer()
    return "".join(sortie)

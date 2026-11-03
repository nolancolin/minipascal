"""Interface en ligne de commande : ``python -m minipascal programme.minipascal``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import compiler, lire_cod
from .erreurs import ErreurCompilation, ErreurExecution
from .machine_virtuelle import MAX_ETAPES_DEFAUT, MachineVirtuelle
from .pcode import Instruction, ecrire_cod


def construire_parseur() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="minipascal",
        description="Compile et exécute un programme MiniPascal.",
    )
    p.add_argument("fichier", nargs="?", default="Code.minipascal",
                   help="programme source .minipascal (défaut : Code.minipascal)")
    p.add_argument("-x", "--executer-cod", metavar="FICHIER.cod",
                   help="exécute directement un fichier de P-code déjà compilé")
    p.add_argument("-o", "--sortie", metavar="FICHIER.cod",
                   help="écrit le P-code dans ce fichier")
    p.add_argument("-l", "--listing", action="store_true",
                   help="affiche le P-code généré")
    p.add_argument("-c", "--compiler-seulement", action="store_true",
                   help="compile (et vérifie) sans exécuter")
    p.add_argument("-t", "--trace", action="store_true",
                   help="affiche chaque instruction exécutée avec l'état de la pile")
    p.add_argument("--max-etapes", type=int, default=MAX_ETAPES_DEFAUT, metavar="N",
                   help=f"nombre maximal d'instructions exécutées, 0 = illimité "
                        f"(défaut : {MAX_ETAPES_DEFAUT})")
    return p


def _trace(pc: int, instr: Instruction, pile: list[int]) -> None:
    print(f"[{pc:04d}] {str(instr):<18} pile={pile}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    for flux in (sys.stdout, sys.stderr):
        if hasattr(flux, "reconfigure"):
            flux.reconfigure(encoding="utf-8")

    args = construire_parseur().parse_args(argv)
    max_etapes = args.max_etapes or None
    nom = args.executer_cod or args.fichier
    source = None

    try:
        if args.executer_cod:
            programme = lire_cod(Path(args.executer_cod).read_text(encoding="utf-8"))
        else:
            source = Path(args.fichier).read_text(encoding="utf-8")
            programme = compiler(source)
    except OSError as e:
        print(f"minipascal: impossible de lire {nom} : {e.strerror}", file=sys.stderr)
        return 1
    except ErreurCompilation as e:
        print(e.formater(source, nom), file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"minipascal: fichier .cod invalide : {e}", file=sys.stderr)
        return 1

    if args.listing:
        print(ecrire_cod(programme), end="")
    if args.sortie:
        Path(args.sortie).write_text(ecrire_cod(programme), encoding="utf-8")
    if args.compiler_seulement:
        return 0

    machine = MachineVirtuelle(
        programme, max_etapes=max_etapes, trace=_trace if args.trace else None
    )
    try:
        machine.executer()
    except ErreurExecution as e:
        print(f"\n{e.formater(nom)}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nInterrompu.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())

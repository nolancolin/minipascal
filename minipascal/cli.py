"""Ligne de commande : minipascal programme.minipascal [options]"""

import argparse
import os
import sys
from pathlib import Path

from .analyseur_lexical import AnalyseurLexical
from .analyseur_syntaxique import AnalyseurSyntaxique
from .erreurs import ErreurCompilation, ErreurExecution, ErreurMiniPascal
from .machine_virtuelle import MAX_ETAPES, MachineVirtuelle
from .pcode import ecrire_cod, lire_cod

# ===== COULEURS =====

ROUGE, BLEU, CYAN, GRIS, GRAS = "1;31", "1;34", "36", "90", "1"
couleurs_actives = False


def c(code: str, texte: str) -> str:
    return f"\033[{code}m{texte}\033[0m" if couleurs_actives else texte


def activer_couleurs(choix: str) -> None:
    global couleurs_actives
    if choix == "auto":
        couleurs_actives = sys.stderr.isatty() and "NO_COLOR" not in os.environ
    else:
        couleurs_actives = choix == "oui"
    if couleurs_actives and os.name == "nt":
        os.system("")   # active les codes couleur ANSI dans la console Windows


# ===== AFFICHAGE =====

def formater_erreur(e: ErreurMiniPascal, source: str | None, fichier: str) -> str:
    """Erreur avec la ligne fautive soulignée, à la manière des compilateurs modernes :

    erreur sémantique : 'pi' est une constante, on ne peut pas la modifier
     --> exemple.minipascal:4:3
      |
    4 |   pi := 4
      |   ^^
    """
    lieu = fichier + "".join(f":{n}" for n in (e.ligne, e.colonne) if n)
    lignes = [c(ROUGE, e.nom) + c(GRAS, f" : {e.message}"), f" {c(BLEU, '-->')} {lieu}"]
    sources = source.splitlines() if source else []
    if 1 <= e.ligne <= len(sources):
        texte = sources[e.ligne - 1]
        num = str(e.ligne)
        marge = " " * len(num)
        lignes += [f"{marge} {c(BLEU, '|')}", f"{c(BLEU, num + ' |')} {texte}"]
        if e.colonne:
            # on garde les tabulations pour que le ^ tombe au bon endroit
            decalage = "".join("\t" if car == "\t" else " " for car in texte[:e.colonne - 1])
            lignes.append(f"{marge} {c(BLEU, '|')} {decalage}{c(ROUGE, '^' * e.longueur)}")
    return "\n".join(lignes)


def afficher_tokens(source: str) -> None:
    for t in AnalyseurLexical(source).tous():
        print(f"{c(GRIS, f'{t.ligne:>3}:{t.colonne:<3}')} {c(CYAN, f'{t.type:<8}')} {t.texte}")


def afficher_trace(co, instr, pilex) -> None:
    print(f"{c(GRIS, f'{co:04d}')}  {c(CYAN, f'{instr!s:<14}')} pile : {pilex}", file=sys.stderr)


def sortie_trace(texte: str) -> None:
    # en mode trace, ce qu'écrit le programme passe sur sa propre ligne pour rester lisible
    print(f"{'':6}{c(GRAS, '>> ' + repr(texte))}", file=sys.stderr)


# ===== PROGRAMME PRINCIPAL =====

def construire_parseur() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="minipascal", add_help=False,
        description="Compile un programme MiniPascal en P-code et l'exécute sur la machine virtuelle.",
        epilog="exemple : minipascal exemples/premiers.minipascal --listing",
    )
    p.add_argument_group("argument").add_argument(
        "fichier", help="programme .minipascal, ou fichier .cod déjà compilé")
    o = p.add_argument_group("options")
    o.add_argument("-l", "--listing", action="store_true", help="affiche le P-code généré")
    o.add_argument("-o", "--sortie", metavar="FICHIER.cod", help="enregistre le P-code")
    o.add_argument("-c", "--compiler", action="store_true", help="compile sans exécuter")
    o.add_argument("-t", "--trace", action="store_true",
                   help="montre chaque instruction exécutée et la pile")
    o.add_argument("--tokens", action="store_true", help="affiche les unités lexicales")
    o.add_argument("--table", action="store_true", help="affiche la table des symboles")
    o.add_argument("--max-etapes", type=int, default=MAX_ETAPES, metavar="N",
                   help=f"arrête après N instructions, 0 pour illimité (défaut : {MAX_ETAPES})")
    o.add_argument("--couleur", choices=["auto", "oui", "non"], default="auto",
                   help="couleurs dans le terminal (défaut : auto)")
    o.add_argument("-h", "--help", action="help", help="affiche cette aide")
    return p


def main(argv: list[str] | None = None) -> int:
    for flux in (sys.stdout, sys.stderr):
        if hasattr(flux, "reconfigure"):
            flux.reconfigure(encoding="utf-8")
    args = construire_parseur().parse_args(argv)
    activer_couleurs(args.couleur)

    source = None
    try:
        texte = Path(args.fichier).read_text(encoding="utf-8-sig")
        if args.fichier.endswith(".cod"):
            prog = lire_cod(texte)
        else:
            source = texte
            if args.tokens:
                afficher_tokens(source)
            analyseur = AnalyseurSyntaxique(source)
            prog = analyseur.anasynt()
            if args.table:
                print(analyseur.table.print_ids())
    except OSError as e:
        print(f"{c(ROUGE, 'erreur')} : impossible de lire {args.fichier} ({e.strerror})",
              file=sys.stderr)
        return 1
    except ErreurCompilation as e:
        print(formater_erreur(e, source, args.fichier), file=sys.stderr)
        return 1
    except RecursionError:
        print(f"{c(ROUGE, 'erreur')} : programme trop imbriqué", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"{c(ROUGE, 'erreur')} : fichier .cod invalide, {e}", file=sys.stderr)
        return 1

    if args.listing:
        print(ecrire_cod(prog), end="")
    if args.sortie:
        Path(args.sortie).write_text(ecrire_cod(prog), encoding="utf-8")
    if args.compiler:
        return 0

    options = {"trace": afficher_trace, "sortie": sortie_trace} if args.trace else {}
    vm = MachineVirtuelle(prog, max_etapes=args.max_etapes or None, **options)
    try:
        vm.executer()
    except ErreurExecution as e:
        sys.stdout.flush()
        print("\n" + formater_erreur(e, source, args.fichier), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\ninterrompu", file=sys.stderr)
        return 130
    return 0

"""Définition du P-code (langage de la machine à pile) et de son format texte ``.cod``.

Une instruction est un couple (opération, argument optionnel) ; les adresses de
saut sont des indices dans la liste d'instructions.

Format ``.cod`` (lisible et rechargeable) :

    ; MiniPascal P-code
    MOTS 2
    MOT 0 a = 10
    MOT 1 x
    CODE
    0000 EMPI 1      ; l.5
    ...
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

# opération -> (nombre d'opérandes, description)
OPERATIONS: dict[str, tuple[int, str]] = {
    "ADDI": (0, "dépile b, a ; empile a + b"),
    "SOUS": (0, "dépile b, a ; empile a - b"),
    "MULT": (0, "dépile b, a ; empile a * b"),
    "DIVI": (0, "dépile b, a ; empile a / b (division entière)"),
    "MODU": (0, "dépile b, a ; empile a MOD b"),
    "MOIN": (0, "dépile a ; empile -a"),
    "EGAL": (0, "dépile b, a ; empile 1 si a = b sinon 0"),
    "DIFF": (0, "dépile b, a ; empile 1 si a <> b sinon 0"),
    "INF":  (0, "dépile b, a ; empile 1 si a < b sinon 0"),
    "INFE": (0, "dépile b, a ; empile 1 si a <= b sinon 0"),
    "SUP":  (0, "dépile b, a ; empile 1 si a > b sinon 0"),
    "SUPE": (0, "dépile b, a ; empile 1 si a >= b sinon 0"),
    "ET":   (0, "dépile b, a ; empile 1 si a et b sont non nuls"),
    "OU":   (0, "dépile b, a ; empile 1 si a ou b est non nul"),
    "NON":  (0, "dépile a ; empile 1 si a = 0 sinon 0"),
    "EMPI": (1, "empile l'opérande (constante ou adresse)"),
    "CONT": (0, "dépile une adresse ; empile le contenu du mot mémoire"),
    "AFFE": (0, "dépile valeur puis adresse ; range la valeur à l'adresse"),
    "LIRE": (0, "dépile une adresse ; y range un entier lu au clavier"),
    "ECRE": (0, "dépile et écrit un entier"),
    "ECRC": (1, "écrit la chaîne donnée en opérande"),
    "ECRL": (0, "écrit un saut de ligne"),
    "ALLE": (1, "aller à l'adresse donnée"),
    "ALSN": (1, "dépile ; si 0 (faux), aller à l'adresse donnée"),
    "STOP": (0, "arrête la machine"),
}


@dataclass(frozen=True)
class Instruction:
    op: str
    arg: int | str | None = None
    ligne: int = 0                 # ligne du source (pour les erreurs d'exécution)

    def __str__(self) -> str:
        if self.arg is None:
            return self.op
        if isinstance(self.arg, str):
            return f"{self.op} {json.dumps(self.arg, ensure_ascii=False)}"
        return f"{self.op} {self.arg}"


@dataclass
class Programme:
    """Résultat de la compilation : code, et description de la mémoire."""

    instructions: list[Instruction] = field(default_factory=list)
    noms_memoire: list[str] = field(default_factory=list)
    initiales: list[int | None] = field(default_factory=list)

    def listing(self) -> str:
        return ecrire_cod(self)


def ecrire_cod(programme: Programme) -> str:
    lignes = ["; MiniPascal P-code", f"MOTS {len(programme.noms_memoire)}"]
    for adr, (nom, init) in enumerate(zip(programme.noms_memoire, programme.initiales)):
        valeur = f" = {init}" if init is not None else ""
        lignes.append(f"MOT {adr} {nom}{valeur}")
    lignes.append("CODE")
    for i, instr in enumerate(programme.instructions):
        commentaire = f"      ; l.{instr.ligne}" if instr.ligne else ""
        lignes.append(f"{i:04d} {instr}{commentaire}")
    return "\n".join(lignes) + "\n"


_RE_MOT = re.compile(r"^MOT\s+(\d+)\s+(\S+?)(?:\s*=\s*(-?\d+))?\s*$")
_RE_LIGNE = re.compile(r"l\.(\d+)")


def lire_cod(texte: str) -> Programme:
    """Recharge un programme écrit par :func:`ecrire_cod`."""
    programme = Programme()
    dans_code = False
    for numero, brut in enumerate(texte.splitlines(), start=1):
        ligne = brut.strip()
        if not ligne or ligne.startswith(";"):
            continue
        if not dans_code:
            if ligne == "CODE":
                dans_code = True
            elif ligne.startswith("MOTS"):
                continue
            elif m := _RE_MOT.match(ligne):
                if int(m.group(1)) != len(programme.noms_memoire):
                    raise ValueError(f"ligne {numero}: adresse mémoire inattendue")
                programme.noms_memoire.append(m.group(2))
                programme.initiales.append(int(m.group(3)) if m.group(3) is not None else None)
            else:
                raise ValueError(f"ligne {numero}: ligne non reconnue : {ligne!r}")
            continue

        morceaux = ligne.split(None, 2)
        if len(morceaux) < 2:
            raise ValueError(f"ligne {numero}: instruction invalide : {ligne!r}")
        op = morceaux[1]
        if op not in OPERATIONS:
            raise ValueError(f"ligne {numero}: opération inconnue : {op}")
        reste = morceaux[2] if len(morceaux) > 2 else ""
        arg: int | str | None = None
        queue = reste
        if OPERATIONS[op][0] == 1:
            if op == "ECRC":
                arg, fin = json.JSONDecoder().raw_decode(reste)
                queue = reste[fin:]
            else:
                partie = reste.split(";", 1)[0].strip()
                try:
                    arg = int(partie)
                except ValueError:
                    raise ValueError(f"ligne {numero}: opérande entier attendu pour {op}") from None
                queue = reste[len(partie):]
        m = _RE_LIGNE.search(queue)
        programme.instructions.append(Instruction(op, arg, int(m.group(1)) if m else 0))
    if not dans_code:
        raise ValueError("section CODE absente")
    return programme

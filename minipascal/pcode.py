"""Le P-code : jeu d'instructions de la machine à pile et format texte .cod.

Exemple de fichier .cod :

    ; MiniPascal P-code
    MOTS 2
    MOT 0 a = 10
    MOT 1 x
    CODE
    0000 EMPI 1      ; l.5
    0001 EMPI 0      ; l.5
    ...
"""

import json
import re
from dataclasses import dataclass, field

# nom -> nombre d'opérandes
OPERATIONS = {
    "ADDI": 0, "SOUS": 0, "MULT": 0, "DIVI": 0, "MODU": 0, "MOIN": 0,
    "EGAL": 0, "DIFF": 0, "INF": 0, "INFE": 0, "SUP": 0, "SUPE": 0,
    "ET": 0, "OU": 0, "NON": 0,
    "EMPI": 1, "CONT": 0, "AFFE": 0, "LIRE": 0,
    "ECRE": 0, "ECRC": 1, "ECRL": 0,
    "ALLE": 1, "ALSN": 1, "STOP": 0,
}


@dataclass(frozen=True)
class Instruction:
    op: str
    arg: int | str | None = None
    ligne: int = 0     # ligne du source, pour situer les erreurs d'exécution

    def __str__(self) -> str:
        if self.arg is None:
            return self.op
        if isinstance(self.arg, str):
            return f"{self.op} {json.dumps(self.arg, ensure_ascii=False)}"
        return f"{self.op} {self.arg}"


@dataclass
class Programme:
    p_code: list[Instruction] = field(default_factory=list)
    noms_memoire: list[str] = field(default_factory=list)
    valeurs_initiales: list[int | None] = field(default_factory=list)


def ecrire_cod(prog: Programme) -> str:
    lignes = ["; MiniPascal P-code", f"MOTS {len(prog.noms_memoire)}"]
    for adr, (nom, val) in enumerate(zip(prog.noms_memoire, prog.valeurs_initiales)):
        lignes.append(f"MOT {adr} {nom}" + (f" = {val}" if val is not None else ""))
    lignes.append("CODE")
    for i, instr in enumerate(prog.p_code):
        ligne = f"{i:04d} {instr}"
        if instr.ligne:
            ligne = f"{ligne:<24} ; l.{instr.ligne}"
        lignes.append(ligne)
    return "\n".join(lignes) + "\n"


RE_MOT = re.compile(r"MOT\s+(\d+)\s+(\S+?)(?:\s*=\s*(-?\d+))?")
RE_NUM_LIGNE = re.compile(r";\s*l\.(\d+)")


def lire_cod(texte: str) -> Programme:
    prog = Programme()
    dans_code = False
    for num, ligne in enumerate(texte.splitlines(), start=1):
        ligne = ligne.strip()
        if not ligne or ligne.startswith(";") or ligne.startswith("MOTS"):
            continue
        if not dans_code:
            if ligne == "CODE":
                dans_code = True
            elif (m := RE_MOT.fullmatch(ligne)) and int(m.group(1)) == len(prog.noms_memoire):
                prog.noms_memoire.append(m.group(2))
                prog.valeurs_initiales.append(int(m.group(3)) if m.group(3) else None)
            else:
                raise ValueError(f"ligne {num} : déclaration mémoire invalide : {ligne!r}")
            continue

        morceaux = ligne.split(None, 2)
        op = morceaux[1] if len(morceaux) > 1 else ""
        if op not in OPERATIONS:
            raise ValueError(f"ligne {num} : instruction inconnue : {ligne!r}")
        reste = morceaux[2] if len(morceaux) > 2 else ""
        arg = None
        if OPERATIONS[op] == 1:
            try:
                if op == "ECRC":
                    arg, fin = json.JSONDecoder().raw_decode(reste)
                    if not isinstance(arg, str):
                        raise ValueError
                else:
                    arg = int(reste.split(";")[0])
                    fin = len(reste.split(";")[0])
            except ValueError:
                raise ValueError(f"ligne {num} : opérande invalide pour {op}") from None
            reste = reste[fin:]
        m = RE_NUM_LIGNE.search(reste)
        prog.p_code.append(Instruction(op, arg, int(m.group(1)) if m else 0))
    if not dans_code:
        raise ValueError("section CODE absente")
    return prog

"""Table des symboles : constantes et variables du programme, et place de chacune en mémoire."""

from dataclasses import dataclass

from .erreurs import ErreurSemantique

# ===== CONSTANTES =====

NB_ID_MAX = 100

NATURE_CONST = "constante"
NATURE_VAR = "variable"

TYPE_ENT = "entier"
TYPE_CH = "chaîne"


@dataclass
class Symbole:
    nom: str
    nature: str
    type: str
    valeur: int | str | None   # None pour une variable
    adrv: int | None           # adresse en mémoire, None pour une constante chaîne


class TableSymboles:

    def __init__(self) -> None:
        self.ids: dict[str, Symbole] = {}
        # un mot mémoire par entier : son nom (pour les messages) et sa valeur de départ
        self.noms_memoire: list[str] = []
        self.valeurs_initiales: list[int | None] = []

    def search_id(self, nom: str) -> Symbole | None:
        return self.ids.get(nom)

    def add_id(self, nom: str, nature: str, type_: str, valeur=None, ligne=0, colonne=0) -> Symbole:
        if nom in self.ids:
            raise ErreurSemantique(f"'{nom}' est déjà déclaré", ligne, colonne, len(nom))
        if len(self.ids) == NB_ID_MAX:
            raise ErreurSemantique(f"trop d'identificateurs ({NB_ID_MAX} maximum)",
                                   ligne, colonne, len(nom))
        # les chaînes ne vont pas en mémoire : elles sont recopiées dans le code (ECRC)
        adrv = self.reserver_mot(nom, valeur) if type_ == TYPE_ENT else None
        self.ids[nom] = Symbole(nom, nature, type_, valeur, adrv)
        return self.ids[nom]

    def reserver_mot(self, nom: str, valeur: int | None = None) -> int:
        self.noms_memoire.append(nom)
        self.valeurs_initiales.append(valeur)
        return len(self.noms_memoire) - 1

    def print_ids(self) -> str:
        lignes = [f"{'nom':<12} {'nature':<10} {'type':<8} {'adresse':<8} valeur"]
        for s in self.ids.values():
            adrv = "-" if s.adrv is None else s.adrv
            valeur = "-" if s.valeur is None else repr(s.valeur) if s.type == TYPE_CH else s.valeur
            lignes.append(f"{s.nom:<12} {s.nature:<10} {s.type:<8} {adrv!s:<8} {valeur}")
        return "\n".join(lignes)

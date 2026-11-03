"""Table des symboles : constantes et variables déclarées par le programme."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .erreurs import ErreurSemantique

NB_ID_MAX = 100


class Nature(Enum):
    CONSTANTE = "constante"
    VARIABLE = "variable"


class Type(Enum):
    ENT = "entier"
    CH = "chaîne"


@dataclass
class Symbole:
    nom: str
    nature: Nature
    type: Type
    valeur: int | str | None   # valeur de la constante (None pour une variable)
    adresse: int | None        # adresse en mémoire ; None pour une constante chaîne


class TableSymboles:
    def __init__(self) -> None:
        self._symboles: dict[str, Symbole] = {}
        # noms[adresse] = nom du mot mémoire (sert aux messages d'erreur et au listing)
        self.noms: list[str] = []
        # valeurs initiales des mots mémoire (constantes) ; None = non initialisé
        self.initiales: list[int | None] = []

    def chercher(self, nom: str) -> Symbole | None:
        return self._symboles.get(nom)

    def ajouter(self, nom: str, nature: Nature, type_: Type, valeur: int | str | None,
                ligne: int = 0, colonne: int = 0) -> Symbole:
        if nom in self._symboles:
            raise ErreurSemantique(f"l'identificateur '{nom}' est déjà déclaré", ligne, colonne)
        if len(self._symboles) >= NB_ID_MAX:
            raise ErreurSemantique(
                f"trop d'identificateurs (maximum {NB_ID_MAX})", ligne, colonne
            )
        adresse = None
        if type_ is Type.ENT:
            adresse = self.reserver(nom, valeur if isinstance(valeur, int) else None)
        symbole = Symbole(nom, nature, type_, valeur, adresse)
        self._symboles[nom] = symbole
        return symbole

    def reserver(self, nom: str, initiale: int | None = None) -> int:
        """Réserve un mot mémoire et renvoie son adresse."""
        self.noms.append(nom)
        self.initiales.append(initiale)
        return len(self.noms) - 1

    def __iter__(self):
        return iter(self._symboles.values())

    def __str__(self) -> str:
        lignes = ["Table des identificateurs :"]
        for s in self:
            lignes.append(f"  {s.nom:<15} {s.nature.value:<10} {s.type.value:<7} "
                          f"adresse={s.adresse} valeur={s.valeur}")
        return "\n".join(lignes)

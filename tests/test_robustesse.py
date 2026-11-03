"""Fuzzing : on abîme les exemples au hasard et on vérifie que le compilateur ne plante jamais.

Un programme faux doit toujours donner une ErreurCompilation propre (jamais une exception
Python), et un programme qui compile doit soit s'exécuter, soit donner une ErreurExecution.
"""

import random
import unittest

from minipascal import ErreurCompilation, ErreurExecution, executer

from .outils import EXEMPLES

MORCEAUX = list(";.,=+-*/()<>:{}'\"") + [
    " ", "\n", "x", "12", ":=", "<>", "DEBUT", "FIN", "SI", "ALORS", "SINON", "TANTQUE",
    "FAIRE", "POUR", "JUSQUA", "REPETER", "ET", "NON", "MOD", "ECRIRE", "LIRE", "VAR",
]


def abimer(source: str, rng: random.Random) -> str:
    for _ in range(rng.randint(1, 4)):
        i = rng.randrange(len(source) + 1)
        match rng.choice(["supprimer", "inserer", "dupliquer"]):
            case "supprimer":
                source = source[:i] + source[i + rng.randint(1, 5):]
            case "inserer":
                source = source[:i] + rng.choice(MORCEAUX) + source[i:]
            case "dupliquer":
                source = source[:i] + source[i:i + rng.randint(1, 20)] * 2 + source[i + 20:]
    return source


class TestRobustesse(unittest.TestCase):

    def test_programmes_abimes(self):
        rng = random.Random(42)
        sources = [f.read_text(encoding="utf-8") for f in EXEMPLES.rglob("*.minipascal")]
        for essai in range(1500):
            source = abimer(rng.choice(sources), rng)
            try:
                executer(source, entree="7\n3\n5\n", max_etapes=20_000)
            except (ErreurCompilation, ErreurExecution):
                pass
            except Exception as e:
                self.fail(f"essai {essai} : {type(e).__name__}: {e}\n--- source ---\n{source}")


if __name__ == "__main__":
    unittest.main()

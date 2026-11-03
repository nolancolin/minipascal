import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from minipascal.cli import formater_erreur, main
from minipascal.erreurs import ErreurSemantique

from .outils import EXEMPLES


def lancer(*args: str) -> tuple[int, str, str]:
    sortie, erreurs = io.StringIO(), io.StringIO()
    with redirect_stdout(sortie), redirect_stderr(erreurs):
        code = main([*args, "--couleur", "non"])
    return code, sortie.getvalue(), erreurs.getvalue()


class TestLigneDeCommande(unittest.TestCase):

    def test_execution(self):
        code, sortie, _ = lancer(str(EXEMPLES / "bonjour.minipascal"))
        self.assertEqual((code, sortie), (0, "Bonjour le monde !\n"))

    def test_listing_sans_execution(self):
        code, sortie, _ = lancer(str(EXEMPLES / "bonjour.minipascal"), "-l", "-c")
        self.assertEqual(code, 0)
        self.assertIn('ECRC "Bonjour le monde !"', sortie)
        self.assertNotIn("Bonjour le monde !\n", sortie.split("CODE")[0])

    def test_tokens_et_table(self):
        _, sortie, _ = lancer(str(EXEMPLES / "pgcd.minipascal"), "--tokens", "--table", "-c")
        self.assertIn("mot_res  PROGRAMME", sortie)
        self.assertIn("variable", sortie)

    def test_compiler_dans_un_cod_puis_l_executer(self):
        with tempfile.TemporaryDirectory() as dossier:
            cod = str(Path(dossier) / "calculs.cod")
            self.assertEqual(lancer(str(EXEMPLES / "calculs.minipascal"), "-c", "-o", cod)[0], 0)
            code, sortie, _ = lancer(cod)
        self.assertEqual(code, 0)
        self.assertIn("2 + 3 * 4   = 14", sortie)

    def test_erreur_de_compilation(self):
        code, _, erreurs = lancer(str(EXEMPLES / "erreurs" / "modification_constante.minipascal"))
        self.assertEqual(code, 1)
        self.assertIn("erreur sémantique", erreurs)
        self.assertIn("modification_constante.minipascal:4:3", erreurs)

    def test_erreur_d_execution(self):
        code, _, erreurs = lancer(str(EXEMPLES / "erreurs" / "division_par_zero.minipascal"))
        self.assertEqual(code, 2)
        self.assertIn("division par zéro", erreurs)
        self.assertIn("ECRIRE(a / b)", erreurs)

    def test_fichier_absent(self):
        self.assertEqual(lancer("existe_pas.minipascal")[0], 1)

    def test_formatage_de_l_erreur(self):
        source = "PROGRAMME t;\nDEBUT\n\tvaleur := 1\nFIN."
        texte = formater_erreur(ErreurSemantique("pas déclaré", 3, 2, 6), source, "t.minipascal")
        self.assertEqual(texte, "erreur sémantique : pas déclaré\n"
                                " --> t.minipascal:3:2\n"
                                "  |\n"
                                "3 | \tvaleur := 1\n"
                                "  | \t^^^^^^")


if __name__ == "__main__":
    unittest.main()

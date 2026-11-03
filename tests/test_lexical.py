import unittest

from minipascal.analyseur_lexical import AnalyseurLexical
from minipascal.erreurs import ErreurLexicale


def types(source: str) -> list[str]:
    return [t.type for t in AnalyseurLexical(source).tous()]


class TestLexical(unittest.TestCase):

    def test_symboles_simples_et_doubles(self):
        self.assertEqual(
            types("< <= <> > >= : := = + - * / ( ) , ; ."),
            ["inf", "infeg", "diff", "sup", "supeg", "twopts", "aff", "eg", "plus", "moins",
             "mult", "divi", "parouv", "parfer", "virg", "ptvirg", "pt", "EOF"],
        )

    def test_inferieur_suivi_d_un_espace(self):
        # la première version renvoyait "null" pour un "<" suivi d'un espace
        self.assertEqual(types("a < b"), ["id", "inf", "id", "EOF"])

    def test_superieur_ne_mange_pas_le_caractere_suivant(self):
        # la première version sautait le caractère qui suit ">" ou ":"
        self.assertEqual(types("a>b"), ["id", "sup", "id", "EOF"])
        self.assertEqual(types("a>5"), ["id", "sup", "ent", "EOF"])

    def test_nombres_a_plusieurs_chiffres(self):
        t = AnalyseurLexical("12345").analex()
        self.assertEqual((t.type, t.valeur), ("ent", 12345))

    def test_mots_reserves_en_majuscules_seulement(self):
        self.assertEqual(types("SI x ALORS si"), ["mot_res", "id", "mot_res", "id", "EOF"])

    def test_chaines(self):
        a, b = AnalyseurLexical("\"abc\" 'd e'").tous()[:2]
        self.assertEqual((a.type, a.valeur, b.valeur), ("ch", "abc", "d e"))

    def test_commentaires_imbriques(self):
        self.assertEqual(types("a { x { y } z } b"), ["id", "id", "EOF"])

    def test_positions(self):
        a, b = AnalyseurLexical("a\n  bb").tous()[:2]
        self.assertEqual((a.ligne, a.colonne, b.ligne, b.colonne), (1, 1, 2, 3))

    def test_erreurs(self):
        for source in ["@", "{ jamais fermé", "'pas fini", "99999999999999999999",
                       "12abc", "'" + "x" * 51 + "'"]:
            with self.subTest(source=source), self.assertRaises(ErreurLexicale):
                AnalyseurLexical(source).tous()

    def test_eof_se_repete(self):
        lex = AnalyseurLexical("")
        self.assertEqual([lex.analex().type, lex.analex().type], ["EOF", "EOF"])


if __name__ == "__main__":
    unittest.main()

import random
import unittest

from minipascal import (ErreurExecution, ErreurLexicale, ErreurSemantique, ErreurSyntaxique,
                        MachineVirtuelle, compiler, ecrire_cod, executer, lire_cod)

from .outils import EXEMPLES, programme


def ecrire(expression: str) -> str:
    return executer(programme(f"ECRIRE({expression})"))


class TestExpressions(unittest.TestCase):

    def test_addition(self):
        # la première version plantait sur "+" (opération "PLUS" inexistante)
        self.assertEqual(ecrire("2 + 3"), "5")

    def test_nombres_a_plusieurs_chiffres(self):
        # la première version ne relisait que le premier chiffre dans le .cod
        self.assertEqual(ecrire("25"), "25")
        self.assertEqual(ecrire("1000 + 234"), "1234")

    def test_priorites(self):
        self.assertEqual(ecrire("2 + 3 * 4"), "14")
        self.assertEqual(ecrire("2 * 3 + 4"), "10")

    def test_associativite_a_gauche(self):
        self.assertEqual(ecrire("10 - 3 - 2"), "5")
        self.assertEqual(ecrire("100 / 5 / 2"), "10")

    def test_parentheses_et_moins_unaire(self):
        self.assertEqual(ecrire("(2 + 3) * 4"), "20")
        self.assertEqual(ecrire("-3 + 5"), "2")
        self.assertEqual(ecrire("- - 4"), "4")
        self.assertEqual(ecrire("2 * -3"), "-6")

    def test_division_tronquee_vers_zero(self):
        self.assertEqual(ecrire("7 / 2"), "3")
        self.assertEqual(ecrire("-7 / 2"), "-3")
        self.assertEqual(ecrire("7 / -2"), "-3")

    def test_mod_du_signe_du_dividende(self):
        self.assertEqual(ecrire("7 MOD 3"), "1")
        self.assertEqual(ecrire("-7 MOD 3"), "-1")
        self.assertEqual(ecrire("7 MOD -3"), "1")

    def test_comparaisons_et_logique(self):
        cas = {"3 < 5": "1", "5 <= 4": "0", "2 = 2": "1", "2 <> 2": "0", "4 >= 4": "1",
               "1 < 2 ET 2 < 3": "1", "1 > 2 OU 2 < 3": "1", "NON 0": "1", "NON 3 = 3": "0"}
        for expression, attendu in cas.items():
            with self.subTest(expression=expression):
                self.assertEqual(ecrire(expression), attendu)

    def test_expressions_aleatoires(self):
        # on compare le compilateur à un calcul fait directement en Python
        rng = random.Random(2026)

        def div(a, b):
            q = abs(a) // abs(b)
            return q if (a < 0) == (b < 0) else -q

        def generer(profondeur):
            if profondeur == 0 or rng.random() < 0.25:
                n = rng.randint(0, 30)
                return str(n), n
            texte_g, g = generer(profondeur - 1)
            texte_d, d = generer(profondeur - 1)
            op = rng.choice(["+", "-", "*", "/", "MOD"])
            if op in ("/", "MOD") and d == 0:
                op = "+"
            valeur = {"+": g + d, "-": g - d, "*": g * d,
                      "/": div(g, d) if d else 0, "MOD": g - div(g, d) * d if d else 0}[op]
            return f"({texte_g} {op} {texte_d})", valeur

        for _ in range(300):
            texte, attendu = generer(4)
            with self.subTest(expression=texte):
                self.assertEqual(ecrire(texte), str(attendu))


class TestInstructions(unittest.TestCase):

    def test_constantes_et_variables(self):
        self.assertEqual(executer(programme("x := a + 5; ECRIRE(x)", var="x", const="a = 10")), "15")

    def test_constante_negative(self):
        self.assertEqual(executer(programme("ECRIRE(a)", const="a = -3")), "-3")

    def test_ecrire_sans_argument_va_a_la_ligne(self):
        self.assertEqual(executer(programme("ECRIRE('a'); ECRIRE(); ECRIRE('b')")), "a\nb")

    def test_ecrire_plusieurs_arguments(self):
        source = programme("ECRIRE(m, 1, 'x', 2 + 3)", const="m = 'ab'")
        self.assertEqual(executer(source), "ab1x5")

    def test_lire(self):
        source = programme("LIRE(a, b); ECRIRE(a + b)", var="a, b")
        self.assertEqual(executer(source, entree="-4\n10\n"), "6")

    def test_si_sans_sinon(self):
        source = programme("LIRE(x); SI x > 0 ALORS ECRIRE('pos'); ECRIRE('!')", var="x")
        self.assertEqual(executer(source, entree="1"), "pos!")
        self.assertEqual(executer(source, entree="-1"), "!")

    def test_si_sinon(self):
        source = programme("LIRE(x); SI x > 0 ALORS ECRIRE('pos') SINON ECRIRE('neg')", var="x")
        self.assertEqual(executer(source, entree="5"), "pos")
        self.assertEqual(executer(source, entree="-5"), "neg")

    def test_sinon_du_si_le_plus_proche(self):
        corps = "LIRE(a, b); SI a > 0 ALORS SI b > 0 ALORS ECRIRE('1') SINON ECRIRE('2')"
        source = programme(corps, var="a, b")
        self.assertEqual(executer(source, entree="1\n1"), "1")
        self.assertEqual(executer(source, entree="1\n-1"), "2")
        self.assertEqual(executer(source, entree="-1\n1"), "")

    def test_tantque(self):
        corps = "i := 3; TANTQUE i > 0 FAIRE DEBUT ECRIRE(i); i := i - 1 FIN"
        self.assertEqual(executer(programme(corps, var="i")), "321")

    def test_tantque_jamais_execute(self):
        self.assertEqual(executer(programme("i := 0; TANTQUE i > 0 FAIRE ECRIRE('x')", var="i")), "")

    def test_repeter_au_moins_une_fois(self):
        corps = "i := 10; REPETER ECRIRE(i); i := i + 1 JUSQUA i > 5"
        self.assertEqual(executer(programme(corps, var="i")), "10")

    def test_pour(self):
        self.assertEqual(executer(programme("POUR i := 1 JUSQUA 4 FAIRE ECRIRE(i)", var="i")), "1234")

    def test_pour_borne_calculee_une_fois(self):
        corps = "n := 3; POUR i := 1 JUSQUA n FAIRE DEBUT n := n + 1; ECRIRE(i) FIN"
        self.assertEqual(executer(programme(corps, var="i, n")), "123")

    def test_pour_vide(self):
        self.assertEqual(executer(programme("POUR i := 5 JUSQUA 1 FAIRE ECRIRE(i)", var="i")), "")

    def test_pour_imbriques(self):
        corps = "POUR i := 1 JUSQUA 2 FAIRE POUR j := 1 JUSQUA 2 FAIRE ECRIRE(i * 10 + j, ' ')"
        self.assertEqual(executer(programme(corps, var="i, j")), "11 12 21 22 ")

    def test_instructions_vides(self):
        self.assertEqual(executer(programme("ECRIRE(1);;ECRIRE(2);")), "12")
        self.assertEqual(executer(programme("")), "")

    def test_blocs_imbriques_et_commentaires(self):
        self.assertEqual(executer(programme("{ un { vrai } commentaire } DEBUT DEBUT ECRIRE(7) FIN FIN")), "7")

    def test_bom_windows(self):
        self.assertEqual(executer("﻿" + programme("ECRIRE(1)")), "1")


class TestErreursCompilation(unittest.TestCase):

    def verifier(self, classe, source, contient="", ligne=None):
        with self.assertRaises(classe) as ctx:
            compiler(source)
        self.assertIn(contient, ctx.exception.message)
        if ligne is not None:
            self.assertEqual(ctx.exception.ligne, ligne)

    def test_point_virgule_manquant(self):
        source = "PROGRAMME t;\nVAR x;\nDEBUT\n  x := 1\n  x := 2\nFIN."
        self.verifier(ErreurSyntaxique, source, "';' ou 'FIN'", ligne=5)

    def test_point_final(self):
        self.verifier(ErreurSyntaxique, "PROGRAMME t;\nDEBUT\nFIN", "'.'")
        self.verifier(ErreurSyntaxique, "PROGRAMME t; DEBUT FIN. x", "rien ne doit suivre")

    def test_oublis(self):
        self.verifier(ErreurSyntaxique, programme("x := ;", var="x"), "une expression")
        self.verifier(ErreurSyntaxique, programme("ECRIRE(1"), "')'")
        self.verifier(ErreurSyntaxique, programme("TANTQUE 1 ECRIRE(1)"), "'FAIRE'")
        self.verifier(ErreurSyntaxique, programme("SI 1 ECRIRE(1)"), "'ALORS'")
        self.verifier(ErreurSyntaxique, programme("REPETER ECRIRE(1)"), "'JUSQUA'")

    def test_identificateur_non_declare(self):
        self.verifier(ErreurSemantique, programme("x := 1"), "n'est pas déclaré", ligne=3)
        self.verifier(ErreurSemantique, programme("ECRIRE(y)"), "'y'")

    def test_constantes_non_modifiables(self):
        self.verifier(ErreurSemantique, programme("c := 2", const="c = 1"), "constante")
        self.verifier(ErreurSemantique, programme("LIRE(c)", const="c = 1"), "constante")
        self.verifier(ErreurSemantique, programme("POUR c := 1 JUSQUA 2 FAIRE", const="c = 1"),
                      "constante")

    def test_double_declaration(self):
        self.verifier(ErreurSemantique, programme("", var="x, x"), "déjà déclaré")

    def test_chaine_dans_un_calcul(self):
        self.verifier(ErreurSemantique, programme("ECRIRE(m + 1)", const="m = 'a'"), "chaîne")
        self.verifier(ErreurSemantique, programme("ECRIRE(1 + 'a')"), "chaîne")
        self.verifier(ErreurSemantique, programme("x := m", var="x", const="m = 'a'"), "chaîne")

    def test_erreur_lexicale(self):
        self.verifier(ErreurLexicale, programme("ECRIRE(1 @ 2)"), "inattendu")

    def test_trop_imbrique(self):
        self.verifier(ErreurSyntaxique, programme("ECRIRE(" + "(" * 5000 + "1" + ")" * 5000 + ")"),
                      "imbriqué")


class TestExecution(unittest.TestCase):

    def verifier(self, source, contient, entree="", ligne=None, **options):
        with self.assertRaises(ErreurExecution) as ctx:
            executer(source, entree, **options)
        self.assertIn(contient, ctx.exception.message)
        if ligne is not None:
            self.assertEqual(ctx.exception.ligne, ligne)

    def test_division_par_zero(self):
        source = "PROGRAMME t;\nVAR a;\nDEBUT\n  a := 0;\n  ECRIRE(1 / a)\nFIN."
        self.verifier(source, "division par zéro", ligne=5)
        self.verifier(programme("ECRIRE(1 MOD 0)"), "division par zéro")

    def test_variable_non_initialisee(self):
        self.verifier(programme("ECRIRE(x)", var="x"), "'x'")

    def test_lire(self):
        self.verifier(programme("LIRE(x)", var="x"), "nombre entier", entree="abc")
        self.verifier(programme("LIRE(x)", var="x"), "entrée est terminée")

    def test_depassement_de_capacite(self):
        self.verifier(programme("x := 9223372036854775807; ECRIRE(x + 1)", var="x"), "dépassement")

    def test_boucle_infinie(self):
        self.verifier(programme("TANTQUE 1 FAIRE x := 1", var="x"), "boucle infinie", max_etapes=1000)


class TestFormatCod(unittest.TestCase):

    def test_aller_retour(self):
        source = programme("ECRIRE('a;b \"q\"', x + c); POUR x := 1 JUSQUA 3 FAIRE ECRIRE(x)",
                           var="x", const="c = -4")
        prog = compiler(source)
        relu = lire_cod(ecrire_cod(prog))
        self.assertEqual(relu.p_code, prog.p_code)
        self.assertEqual(relu.noms_memoire, prog.noms_memoire)
        self.assertEqual(relu.valeurs_initiales, prog.valeurs_initiales)

    def test_execution_d_un_cod(self):
        sortie = []
        prog = lire_cod(ecrire_cod(compiler(programme("ECRIRE(6 * 7)"))))
        MachineVirtuelle(prog, sortie=sortie.append).executer()
        self.assertEqual("".join(sortie), "42")

    def test_cod_invalides(self):
        for texte in ["", "CODE\n0000 BIDON", "CODE\n0000 EMPI x", "CODE\n0000 ECRC 5",
                      "n'importe quoi\nCODE"]:
            with self.subTest(texte=texte), self.assertRaises(ValueError):
                lire_cod(texte)


class TestExemples(unittest.TestCase):

    def lancer(self, nom, entree=""):
        return executer((EXEMPLES / f"{nom}.minipascal").read_text(encoding="utf-8"), entree)

    def test_tous_les_exemples_compilent(self):
        fichiers = list(EXEMPLES.glob("*.minipascal"))
        self.assertGreaterEqual(len(fichiers), 8)
        for f in fichiers:
            with self.subTest(exemple=f.name):
                compiler(f.read_text(encoding="utf-8"))

    def test_exemples_d_erreurs(self):
        for f in (EXEMPLES / "erreurs").glob("*.minipascal"):
            if f.stem == "division_par_zero":
                continue
            with self.subTest(exemple=f.name), self.assertRaises((ErreurSyntaxique, ErreurSemantique)):
                compiler(f.read_text(encoding="utf-8"))

    def test_resultats(self):
        self.assertEqual(self.lancer("factorielle", "10"), "n = 10! = 3628800\n")
        self.assertTrue(self.lancer("fibonacci", "10").endswith("0 1 1 2 3 5 8 13 21 34 \n"))
        self.assertIn("PGCD = 6", self.lancer("pgcd", "48\n18"))
        self.assertTrue(self.lancer("premiers", "30").endswith("2 3 5 7 11 13 17 19 23 29 \n"))
        self.assertIn("en 111 étapes", self.lancer("syracuse", "27"))
        self.assertIn("10 - 3 - 2  = 5", self.lancer("calculs"))


if __name__ == "__main__":
    unittest.main()

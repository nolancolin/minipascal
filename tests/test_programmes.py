import random
import unittest

from minipascal import (
    ErreurExecution, ErreurLexicale, ErreurSemantique, ErreurSyntaxique,
    compiler, ecrire_cod, executer, lire_cod,
)

from .outils import EXEMPLES, programme


def ecrire(expression: str) -> str:
    return executer(programme(f"ECRIRE({expression})"))


class TestExpressions(unittest.TestCase):
    def test_addition(self):
        # Le compilateur d'origine plantait sur "+" (opération "PLUS" inexistante).
        self.assertEqual(ecrire("2 + 3"), "5")

    def test_nombres_a_plusieurs_chiffres(self):
        # L'interpréteur d'origine ne lisait que le premier chiffre des opérandes.
        self.assertEqual(ecrire("25"), "25")
        self.assertEqual(ecrire("1000 + 234"), "1234")

    def test_priorite_de_la_multiplication(self):
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

    def test_division_entiere_tronquee_vers_zero(self):
        self.assertEqual(ecrire("7 / 2"), "3")
        self.assertEqual(ecrire("-7 / 2"), "-3")
        self.assertEqual(ecrire("7 / -2"), "-3")

    def test_mod_a_le_signe_du_dividende(self):
        self.assertEqual(ecrire("7 MOD 3"), "1")
        self.assertEqual(ecrire("-7 MOD 3"), "-1")
        self.assertEqual(ecrire("7 MOD -3"), "1")

    def test_comparaisons_et_logique(self):
        self.assertEqual(ecrire("3 < 5"), "1")
        self.assertEqual(ecrire("5 <= 4"), "0")
        self.assertEqual(ecrire("2 = 2"), "1")
        self.assertEqual(ecrire("2 <> 2"), "0")
        self.assertEqual(ecrire("1 < 2 ET 2 < 3"), "1")
        self.assertEqual(ecrire("1 > 2 OU 2 < 3"), "1")
        self.assertEqual(ecrire("NON 0"), "1")
        self.assertEqual(ecrire("NON 3 = 3"), "0")

    def test_expressions_aleatoires_contre_une_reference(self):
        rng = random.Random(2024)

        def tronc(a, b):
            q = abs(a) // abs(b)
            return -q if (a < 0) != (b < 0) else q

        def generer(profondeur):
            if profondeur == 0 or rng.random() < 0.25:
                n = rng.randint(0, 30)
                return str(n), n
            texte_g, val_g = generer(profondeur - 1)
            texte_d, val_d = generer(profondeur - 1)
            op = rng.choice(["+", "-", "*", "/", "MOD"])
            if op in ("/", "MOD") and val_d == 0:
                op = "+"
            val = {"+": lambda: val_g + val_d, "-": lambda: val_g - val_d,
                   "*": lambda: val_g * val_d, "/": lambda: tronc(val_g, val_d),
                   "MOD": lambda: val_g - tronc(val_g, val_d) * val_d}[op]()
            return f"({texte_g} {op} {texte_d})", val

        for _ in range(300):
            texte, attendu = generer(4)
            with self.subTest(expression=texte):
                self.assertEqual(ecrire(texte), str(attendu))


class TestInstructions(unittest.TestCase):
    def test_affectation_constantes_et_variables(self):
        source = programme("x := a + 5; ECRIRE(x)", var="x", const="a = 10")
        self.assertEqual(executer(source), "15")

    def test_ecrire_sans_argument_va_a_la_ligne(self):
        self.assertEqual(executer(programme("ECRIRE('a'); ECRIRE(); ECRIRE('b')")), "a\nb")

    def test_ecrire_plusieurs_arguments_et_chaine_constante(self):
        source = programme("ECRIRE(m, 1, 'x', 2 + 3)", const="m = 'ab'")
        self.assertEqual(executer(source), "ab1x5")

    def test_lire_nombres_negatifs(self):
        source = programme("LIRE(a, b); ECRIRE(a + b)", var="a, b")
        self.assertEqual(executer(source, entree="-4\n10\n"), "6")

    def test_si_sans_sinon(self):
        source = programme("LIRE(x); SI x > 0 ALORS ECRIRE('pos'); ECRIRE('!')", var="x")
        self.assertEqual(executer(source, entree="1"), "pos!")
        self.assertEqual(executer(source, entree="-1"), "!")

    def test_si_sinon(self):
        corps = "LIRE(x); SI x > 0 ALORS ECRIRE('pos') SINON ECRIRE('neg')"
        source = programme(corps, var="x")
        self.assertEqual(executer(source, entree="5"), "pos")
        self.assertEqual(executer(source, entree="-5"), "neg")

    def test_sinon_se_rattache_au_si_le_plus_proche(self):
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

    def test_repeter_s_execute_au_moins_une_fois(self):
        corps = "i := 10; REPETER ECRIRE(i); i := i + 1 JUSQUA i > 5"
        self.assertEqual(executer(programme(corps, var="i")), "10")

    def test_pour(self):
        corps = "POUR i := 1 JUSQUA 4 FAIRE ECRIRE(i)"
        self.assertEqual(executer(programme(corps, var="i")), "1234")

    def test_pour_borne_evaluee_une_seule_fois(self):
        corps = "n := 3; POUR i := 1 JUSQUA n FAIRE DEBUT n := n + 1; ECRIRE(i) FIN"
        self.assertEqual(executer(programme(corps, var="i, n")), "123")

    def test_pour_vide(self):
        self.assertEqual(executer(programme("POUR i := 5 JUSQUA 1 FAIRE ECRIRE(i)", var="i")), "")

    def test_pour_imbriques(self):
        corps = "POUR i := 1 JUSQUA 2 FAIRE POUR j := 1 JUSQUA 2 FAIRE ECRIRE(i * 10 + j, ' ')"
        self.assertEqual(executer(programme(corps, var="i, j")), "11 12 21 22 ")

    def test_instructions_vides_et_point_virgule_final(self):
        self.assertEqual(executer(programme("ECRIRE(1);;ECRIRE(2);")), "12")
        self.assertEqual(executer(programme("")), "")

    def test_blocs_imbriques(self):
        self.assertEqual(executer(programme("DEBUT DEBUT ECRIRE(7) FIN FIN")), "7")

    def test_commentaires(self):
        self.assertEqual(executer(programme("{ un { vrai } commentaire } ECRIRE(1)")), "1")


class TestErreursCompilation(unittest.TestCase):
    def assertErreur(self, classe, source, ligne=None, contient=""):
        with self.assertRaises(classe) as ctx:
            compiler(source)
        if ligne is not None:
            self.assertEqual(ctx.exception.ligne, ligne)
        self.assertIn(contient, ctx.exception.message)

    def test_point_virgule_manquant(self):
        source = "PROGRAMME t;\nVAR x;\nDEBUT\n  x := 1\n  x := 2\nFIN."
        self.assertErreur(ErreurSyntaxique, source, ligne=5, contient="';' ou 'FIN'")

    def test_point_final_manquant(self):
        self.assertErreur(ErreurSyntaxique, "PROGRAMME t;\nDEBUT\nFIN", contient="'.'")

    def test_texte_apres_le_point_final(self):
        self.assertErreur(ErreurSyntaxique, "PROGRAMME t; DEBUT FIN. x", contient="suit")

    def test_expression_manquante(self):
        self.assertErreur(ErreurSyntaxique, programme("x := ;", var="x"), contient="une expression")

    def test_parenthese_non_fermee(self):
        self.assertErreur(ErreurSyntaxique, programme("ECRIRE(1", var="x"), contient="')'")

    def test_faire_oublie(self):
        self.assertErreur(ErreurSyntaxique, programme("TANTQUE 1 ECRIRE(1)"), contient="'FAIRE'")

    def test_alors_oublie(self):
        self.assertErreur(ErreurSyntaxique, programme("SI 1 ECRIRE(1)"), contient="'ALORS'")

    def test_identificateur_non_declare(self):
        self.assertErreur(ErreurSemantique, programme("x := 1"), ligne=3, contient="n'est pas déclaré")

    def test_non_declare_dans_expression(self):
        self.assertErreur(ErreurSemantique, programme("ECRIRE(y)"), contient="'y'")

    def test_modification_d_une_constante(self):
        self.assertErreur(ErreurSemantique, programme("c := 2", const="c = 1"), contient="constante")

    def test_lire_dans_une_constante(self):
        self.assertErreur(ErreurSemantique, programme("LIRE(c)", const="c = 1"), contient="constante")

    def test_double_declaration(self):
        self.assertErreur(ErreurSemantique, programme("", var="x, x"), contient="déjà déclaré")

    def test_chaine_dans_un_calcul(self):
        self.assertErreur(ErreurSemantique, programme("ECRIRE(m + 1)", const="m = 'a'"),
                          contient="chaîne")
        self.assertErreur(ErreurSemantique, programme("ECRIRE(1 + 'a')"), contient="chaîne")

    def test_erreur_lexicale_remontee(self):
        self.assertErreur(ErreurLexicale, programme("ECRIRE(1 @ 2)"), contient="inattendu")

    def test_formatage_avec_pointeur(self):
        source = "PROGRAMME t;\nDEBUT\n  x := 1\nFIN."
        with self.assertRaises(ErreurSemantique) as ctx:
            compiler(source)
        texte = ctx.exception.formater(source, "prog.minipascal")
        self.assertIn("prog.minipascal:3:3", texte)
        self.assertIn("    x := 1\n    ^", texte)


class TestExecution(unittest.TestCase):
    def assertErreurExecution(self, source, contient, entree="", ligne=None, **options):
        with self.assertRaises(ErreurExecution) as ctx:
            executer(source, entree, **options)
        self.assertIn(contient, ctx.exception.message)
        if ligne is not None:
            self.assertEqual(ctx.exception.ligne, ligne)

    def test_division_par_zero(self):
        source = "PROGRAMME t;\nVAR a;\nDEBUT\n  a := 0;\n  ECRIRE(1 / a)\nFIN."
        self.assertErreurExecution(source, "division par zéro", ligne=5)

    def test_mod_par_zero(self):
        self.assertErreurExecution(programme("ECRIRE(1 MOD 0)"), "division par zéro")

    def test_variable_non_initialisee(self):
        self.assertErreurExecution(programme("ECRIRE(x)", var="x"), "'x'")

    def test_lire_refuse_le_texte(self):
        self.assertErreurExecution(programme("LIRE(x)", var="x"), "nombre entier", entree="abc")

    def test_lire_fin_d_entree(self):
        self.assertErreurExecution(programme("LIRE(x)", var="x"), "fin de l'entrée")

    def test_depassement_de_capacite(self):
        corps = "x := 9223372036854775807; ECRIRE(x + 1)"
        self.assertErreurExecution(programme(corps, var="x"), "dépassement")

    def test_boucle_infinie_arretee(self):
        corps = "TANTQUE 1 FAIRE x := 1"
        self.assertErreurExecution(programme(corps, var="x"), "boucle infinie", max_etapes=1000)


class TestFormatCod(unittest.TestCase):
    def test_aller_retour(self):
        source = programme(
            "ECRIRE('a;b \"q\"', x + c); POUR x := 1 JUSQUA 3 FAIRE ECRIRE(x)",
            var="x", const="c = -4",
        )
        compile_ = compiler(source)
        recharge = lire_cod(ecrire_cod(compile_))
        self.assertEqual(recharge.instructions, compile_.instructions)
        self.assertEqual(recharge.noms_memoire, compile_.noms_memoire)
        self.assertEqual(recharge.initiales, compile_.initiales)

    def test_execution_depuis_un_cod(self):
        from minipascal import MachineVirtuelle
        sortie = []
        programme_ = lire_cod(ecrire_cod(compiler(programme("ECRIRE(6 * 7)"))))
        MachineVirtuelle(programme_, sortie=sortie.append).executer()
        self.assertEqual("".join(sortie), "42")

    def test_cod_invalide(self):
        for texte in ["", "CODE\n0000 BIDON", "CODE\n0000 EMPI x", "n'importe quoi\nCODE"]:
            with self.subTest(texte=texte), self.assertRaises(ValueError):
                lire_cod(texte)


class TestExemples(unittest.TestCase):
    def lancer(self, nom, entree=""):
        return executer((EXEMPLES / f"{nom}.minipascal").read_text(encoding="utf-8"), entree)

    def test_tous_les_exemples_compilent(self):
        fichiers = [f for f in EXEMPLES.glob("*.minipascal")]
        self.assertGreaterEqual(len(fichiers), 8)
        for f in fichiers:
            with self.subTest(exemple=f.name):
                compiler(f.read_text(encoding="utf-8"))

    def test_exemples_d_erreurs_echouent_a_la_compilation(self):
        for f in (EXEMPLES / "erreurs").glob("*.minipascal"):
            if f.stem == "division_par_zero":
                continue
            with self.subTest(exemple=f.name), self.assertRaises(
                (ErreurSyntaxique, ErreurSemantique)
            ):
                compiler(f.read_text(encoding="utf-8"))

    def test_factorielle(self):
        self.assertEqual(self.lancer("factorielle", "10"), "n = 10! = 3628800\n")

    def test_fibonacci(self):
        self.assertTrue(self.lancer("fibonacci", "10").endswith("0 1 1 2 3 5 8 13 21 34 \n"))

    def test_pgcd(self):
        self.assertIn("PGCD = 6", self.lancer("pgcd", "48\n18"))

    def test_premiers(self):
        self.assertTrue(self.lancer("premiers", "30").endswith("2 3 5 7 11 13 17 19 23 29 \n"))

    def test_syracuse(self):
        self.assertIn("en 111 étapes", self.lancer("syracuse", "27"))

    def test_calculs(self):
        sortie = self.lancer("calculs")
        self.assertIn("2 + 3 * 4   = 14", sortie)
        self.assertIn("10 - 3 - 2  = 5", sortie)


if __name__ == "__main__":
    unittest.main()

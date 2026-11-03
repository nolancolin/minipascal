# MiniPascal : compilateur et machine virtuelle

Compilateur d'un petit langage inspiré de Pascal (mots-clés en français) vers un **P-code**,
exécuté par une **machine virtuelle à pile**. Projet de Compilation, L3 Informatique.

```
 source .minipascal ──► analyseur lexical ──► analyseur syntaxique ──► P-code ──► machine virtuelle
                         (unités lexicales)    + génération de code     (.cod)       (pile + mémoire)
                                  └──────────── table des symboles ────────┘
```

## Utilisation

Python 3.10 ou plus, aucune dépendance.

```bash
python -m minipascal exemples/factorielle.minipascal      # compile et exécute
python Main.py exemples/factorielle.minipascal            # même chose
```

| Option | Effet |
|---|---|
| `-l`, `--listing` | affiche le P-code généré |
| `-o FICHIER.cod` | écrit le P-code dans un fichier |
| `-x FICHIER.cod` | exécute un fichier `.cod` déjà compilé |
| `-c` | compile seulement (vérification) |
| `-t`, `--trace` | affiche chaque instruction exécutée et l'état de la pile |
| `--max-etapes N` | arrête après N instructions (défaut 10 000 000, `0` = illimité) |

Sans argument, `Main.py` compile `Code.minipascal` comme avant.

Les erreurs sont localisées et montrent la ligne fautive :

```
exemples/erreurs/modification_constante.minipascal:4:3: Erreur sémantique : 'pi' est une constante, on ne peut pas la modifier
    pi := 4
    ^
```

## Le langage

```pascal
PROGRAMME premiers;
CONST max = 50;
VAR i, d, premier;
DEBUT
  POUR i := 2 JUSQUA max FAIRE
  DEBUT
    premier := 1;
    d := 2;
    TANTQUE d * d <= i ET premier FAIRE
      SI i MOD d = 0 ALORS premier := 0 SINON d := d + 1;
    SI premier ALORS ECRIRE(i, " ")
  FIN;
  ECRIRE()
FIN.
```

* Types : entiers 64 bits, constantes chaînes (utilisables seulement dans `ECRIRE`).
* Mots réservés en majuscules : `PROGRAMME CONST VAR DEBUT FIN LIRE ECRIRE SI ALORS SINON TANTQUE FAIRE REPETER JUSQUA POUR ET OU NON MOD`.
* Commentaires `{ ... }`, imbriquables. Chaînes entre `"` ou `'` (50 caractères max).
* `ECRIRE(a, "texte", b+1)` écrit sans retour à la ligne ; `ECRIRE()` seul va à la ligne.
* Pas de booléen : une condition est un entier, `0` = faux, tout le reste = vrai ;
  les comparaisons et `ET`/`OU`/`NON` renvoient `0` ou `1` (sans évaluation paresseuse).
* Division entière tronquée vers zéro, `MOD` de même signe que le dividende (comme en Pascal).
* `POUR i := a JUSQUA b` évalue `b` une seule fois ; `REPETER ... JUSQUA c` s'exécute au moins une fois.

### Grammaire

```
programme   = "PROGRAMME" id ";" [decl_const] [decl_var] bloc "."
decl_const  = "CONST" id "=" (nombre | chaine) { "," id "=" (nombre | chaine) } ";"
decl_var    = "VAR" id { "," id } ";"
bloc        = "DEBUT" liste "FIN"
liste       = instruction { ";" instruction }          (instruction vide permise)
instruction = affectation | lecture | ecriture | bloc | si | tantque | repeter | pour
affectation = id ":=" expression
lecture     = "LIRE" "(" id { "," id } ")"
ecriture    = "ECRIRE" "(" [ (chaine | expression) { "," (chaine | expression) } ] ")"
si          = "SI" expression "ALORS" instruction [ "SINON" instruction ]
tantque     = "TANTQUE" expression "FAIRE" instruction
repeter     = "REPETER" liste "JUSQUA" expression
pour        = "POUR" id ":=" expression "JUSQUA" expression "FAIRE" instruction

expression  = conjonction { "OU" conjonction }
conjonction = negation { "ET" negation }
negation    = "NON" negation | comparaison
comparaison = somme [ ("=" | "<>" | "<" | "<=" | ">" | ">=") somme ]
somme       = produit { ("+" | "-") produit }
produit     = facteur { ("*" | "/" | "MOD") facteur }
facteur     = nombre | id | "(" expression ")" | "-" facteur | "+" facteur
```

Un niveau de priorité = une fonction dans `analyseur_syntaxique.py` ; l'associativité à gauche
vient des boucles `{ ... }`.

## Le P-code

La machine a une pile d'entiers et une mémoire de mots (variables, constantes, bornes de `POUR`).
Les adresses de saut sont des numéros d'instruction.

| Instruction | Effet |
|---|---|
| `EMPI n` | empile `n` (constante ou adresse) |
| `CONT` | dépile une adresse, empile le contenu |
| `AFFE` | dépile valeur puis adresse, range la valeur |
| `ADDI SOUS MULT DIVI MODU` | dépilent `b`, `a` ; empilent `a op b` |
| `MOIN` | négation |
| `EGAL DIFF INF INFE SUP SUPE` | comparaisons, empilent 0 ou 1 |
| `ET OU NON` | logique, empilent 0 ou 1 |
| `LIRE` | dépile une adresse, y range un entier lu |
| `ECRE` / `ECRC "s"` / `ECRL` | écrit un entier / une chaîne / un saut de ligne |
| `ALLE a` | saut inconditionnel |
| `ALSN a` | dépile ; saute si 0 (« aller si non ») |
| `STOP` | fin |

`python -m minipascal exemples/bonjour.minipascal -l` affiche le code complet avec les lignes du source.

## Organisation

```
minipascal/
  analyseur_lexical.py      unités lexicales avec ligne/colonne
  analyseur_syntaxique.py   descente récursive + génération de P-code
  table_symboles.py         constantes, variables, adresses mémoire
  pcode.py                  instructions, format .cod (écriture et relecture)
  machine_virtuelle.py      exécution (pile, mémoire, erreurs d'exécution)
  erreurs.py                exceptions avec position
  cli.py                    ligne de commande
exemples/                   programmes de démonstration (+ exemples/erreurs/)
tests/                      tests unitaires et de bout en bout
```

Tests : `python -m unittest discover -s tests -t .`

## Ce qui a changé par rapport à la première version

Corrigé :

* `+` faisait planter le compilateur (`'PLUS' is not in list`) ;
* les nombres à plusieurs chiffres étaient tronqués au premier chiffre à l'exécution ;
* pas de priorité des opérateurs et `a - b - c` était calculé `a - (b - c)` ;
* `SI`, `TANTQUE` n'étaient jamais exécutés (`ALLE`/`ALSN` absents de la machine) ;
  le `SINON` était toujours exécuté après le `ALORS`, et `TANTQUE` attendait `ALORS` au lieu de `FAIRE` ;
* `<`, `>`, `:` : le caractère suivant était avalé, `<` suivi d'un espace n'était pas reconnu ;
* `ECRIRE()` ne consommait pas la parenthèse fermante (erreur de syntaxe), le moins unaire et le `SI`
  sautaient un symbole de trop ;
* la division renvoyait un flottant (`7/2 = 3.5`) ;
* une erreur détectée dans une instruction provoquait un second message d'erreur, car on essayait
  les autres formes d'instruction ensuite (`lecture() or ecriture() or ...`) ; les erreurs lexicales
  n'arrêtaient pas l'analyse.

Ajouté : opérateurs de comparaison, `ET`/`OU`/`NON`/`MOD`, `REPETER`, `POUR`, `SINON`, instructions
vides, constantes négatives, erreurs avec ligne et colonne, détection des variables non initialisées
et du dépassement d'entier, format `.cod` rechargeable, trace, garde-fou contre les boucles infinies,
tests, exemples.

## Pistes pour aller plus loin

* **Procédures et fonctions** (pile d'appels, passage de paramètres, récursivité : `APPEL`, `RETOUR`).
* **Tableaux**, type booléen, réels, vraies variables chaînes.
* **Optimiseur** : calcul des constantes à la compilation, suppression des `EMPI/CONT` inutiles.
* **Plusieurs erreurs par compilation** (reprise sur erreur aux `;`), avertissements (variable jamais lue).
* **Autres cibles** : traduction vers C, Python, WebAssembly ou LLVM IR à partir du même P-code.
* **Outils** : débogueur pas à pas (points d'arrêt), REPL, coloration syntaxique VS Code, graphe du P-code.
* **Version web** : la machine virtuelle est assez petite pour être portée en JavaScript.

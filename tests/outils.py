from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
EXEMPLES = RACINE / "exemples"


def programme(corps: str, var: str = "", const: str = "") -> str:
    """Enveloppe ``corps`` dans un programme MiniPascal complet."""
    texte = "PROGRAMME t;\n"
    if const:
        texte += f"CONST {const};\n"
    if var:
        texte += f"VAR {var};\n"
    return texte + f"DEBUT\n{corps}\nFIN."

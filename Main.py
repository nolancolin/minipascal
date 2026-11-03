"""Point d'entrée sans installation : python Main.py programme.minipascal [options]"""

import sys

from minipascal.cli import main

if __name__ == "__main__":
    sys.exit(main())

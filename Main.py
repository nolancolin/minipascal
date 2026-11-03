"""Raccourci : ``python Main.py [programme.minipascal]`` (équivaut à ``python -m minipascal``)."""

import sys

from minipascal.cli import main

if __name__ == "__main__":
    sys.exit(main())

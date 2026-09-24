#!/usr/bin/env python3
"""Forward controlled evaluation requests and preserve the gateway exit code."""

from pathlib import Path
import runpy
import sys


def main():
    gateway = Path(__file__).resolve().parents[1] / "tools" / "eval-interface.py"
    namespace = runpy.run_path(str(gateway))
    return namespace["main"](sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())

"""Command-line entry point for gdt-coach.

No business logic is implemented yet; this only wires up the console
script so the package is runnable end-to-end.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from gdt_coach import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gdt-coach",
        description="gdt-coach command-line interface.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print the installed version and exit.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

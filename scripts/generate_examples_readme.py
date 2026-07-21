#!/usr/bin/env python3
"""Regenerate the captured CLI output blocks in examples/README.md.

Each example's command, real stdout, and exit code lives between a pair
of ``<!-- gdt-coach:example KEY -->`` / ``<!-- /gdt-coach:example -->``
markers in ``examples/README.md``, where KEY is an example file's stem
under ``examples/`` (e.g. ``valid_position`` for
``examples/valid_position.yaml``, or ``invalid_datum_reference_undefined``
for ``examples/invalid_datum_reference_undefined.csv``). This script is
the only place that produces that text: it runs the real CLI
(``gdt_coach.cli.main``, the same function the installed ``gdt-coach``
console script calls) against every example file in ``examples/``
(YAML or CSV -- see ``_EXAMPLE_EXTENSIONS``) and replaces each marked
region with a fresh capture, so the documentation can never silently
drift from real behavior.

Usage (from the repository root):

    python scripts/generate_examples_readme.py        # rewrite in place
    python scripts/generate_examples_readme.py --check # exit 1 if stale

``--check`` is what the test suite uses to fail the build if committed
documentation has drifted from real CLI output -- see
``tests/test_examples_readme.py``.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import re
import sys
from pathlib import Path

from gdt_coach.cli import main as _cli_main

_REPO_ROOT = Path(__file__).resolve().parent.parent
_EXAMPLES_DIR = _REPO_ROOT / "examples"
_README_PATH = _EXAMPLES_DIR / "README.md"

_MARKER_PATTERN = re.compile(
    r"(<!-- gdt-coach:example (?P<key>[\w-]+) -->\n).*?(\n<!-- /gdt-coach:example -->)",
    re.DOTALL,
)

_EXAMPLE_EXTENSIONS = (".yaml", ".csv")
"""Every extension an example file under examples/ may use. Add a new one
here (and nowhere else) when a new example input format is bundled."""


class ExamplesReadmeError(ValueError):
    """Raised when examples/README.md and examples/*.{yaml,csv} are out of sync."""


def discover_example_keys(examples_dir: Path) -> set[str]:
    """The stem of every example file under `examples_dir` (e.g. {"valid_position", ...}).

    Looks at every extension in `_EXAMPLE_EXTENSIONS` (currently YAML and
    CSV), so this stays generic as more example input formats are added.
    """
    return {
        path.stem
        for extension in _EXAMPLE_EXTENSIONS
        for path in examples_dir.glob(f"*{extension}")
    }


def documented_example_keys(readme_text: str) -> set[str]:
    """Every KEY named in a `<!-- gdt-coach:example KEY -->` marker in `readme_text`."""
    return {match.group("key") for match in _MARKER_PATTERN.finditer(readme_text)}


def diff_example_keys(documented: set[str], discovered: set[str]) -> tuple[set[str], set[str]]:
    """Return (missing, orphaned).

    `missing` has a YAML file but no doc block; `orphaned` is the reverse.
    """
    return discovered - documented, documented - discovered


def _run_cli(args: list[str]) -> tuple[str, int]:
    """Run gdt_coach.cli.main in-process, returning (stdout, exit_code)."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        exit_code = _cli_main(args)
    return buffer.getvalue().rstrip("\n"), exit_code


def _relative_example_path(key: str) -> str:
    """The `examples/<key><ext>` path for `key`, resolving its real extension.

    Generic over `_EXAMPLE_EXTENSIONS` so this doesn't need to change
    when a new example input format (beyond YAML/CSV) is added.
    """
    matches = [
        path
        for extension in _EXAMPLE_EXTENSIONS
        for path in _EXAMPLES_DIR.glob(f"{key}{extension}")
    ]
    if len(matches) != 1:
        raise ExamplesReadmeError(
            f"expected exactly one example file for key {key!r} under {_EXAMPLES_DIR}, "
            f"found {[str(match) for match in matches]}"
        )
    return f"examples/{matches[0].name}"


def _generated_block(key: str) -> str:
    relative_path = _relative_example_path(key)
    with contextlib.chdir(_REPO_ROOT):
        stdout, exit_code = _run_cli(["check", relative_path])
    return f"```\n$ gdt-coach check {relative_path}\n{stdout}\n```\n\nExit code: `{exit_code}`"


def regenerate(readme_text: str, examples_dir: Path = _EXAMPLES_DIR) -> str:
    """Return `readme_text` with every marked example block replaced by a fresh capture.

    Raises ExamplesReadmeError if examples/*.{yaml,csv} and the documented
    <!-- gdt-coach:example --> blocks are out of sync: a new example
    added without a doc block, or a doc block left behind for a
    deleted example.
    """
    documented = documented_example_keys(readme_text)
    discovered = discover_example_keys(examples_dir)
    missing, orphaned = diff_example_keys(documented, discovered)
    if missing or orphaned:
        raise ExamplesReadmeError(
            "examples/README.md is out of sync with examples/*.{yaml,csv} -- "
            f"missing doc block(s) for {sorted(missing)}, "
            f"orphaned doc block(s) for {sorted(orphaned)}"
        )

    def _replace(match: re.Match[str]) -> str:
        return f"{match.group(1)}{_generated_block(match.group('key'))}{match.group(3)}"

    return _MARKER_PATTERN.sub(_replace, readme_text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if regenerating would change examples/README.md, without writing.",
    )
    args = parser.parse_args(argv)

    original = _README_PATH.read_text(encoding="utf-8")
    try:
        regenerated = regenerate(original)
    except ExamplesReadmeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if args.check:
        if regenerated != original:
            print(
                "examples/README.md is out of date with real CLI output. "
                "Run `python scripts/generate_examples_readme.py` to update it.",
                file=sys.stderr,
            )
            return 1
        print("examples/README.md matches real CLI output.")
        return 0

    if regenerated != original:
        _README_PATH.write_text(regenerated, encoding="utf-8")
        print("examples/README.md regenerated.")
    else:
        print("examples/README.md already up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

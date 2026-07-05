"""Command-line entry point for gdt-coach."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from gdt_coach import __version__
from gdt_coach.ingest import load_drawing_from_yaml_file
from gdt_coach.ingest.exceptions import IngestError
from gdt_coach.models import Drawing
from gdt_coach.rules.base import Rule
from gdt_coach.rules.checks import (
    DuplicateDatumReferencesRule,
    FlatnessNoDatumReferencesRule,
    PositionRequiresDatumReferenceRule,
    ProjectedZoneRequiresPositionRule,
    StraightnessNoDatumReferencesRule,
)
from gdt_coach.rules.engine import RuleEngine
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.registry import RuleRegistry

# A dedicated registry is built per invocation (see `_build_registry`)
# rather than relying on the shared `default_registry`, so `check`
# behaves the same regardless of what else has run in the process.
_RULE_CLASSES: tuple[type[Rule], ...] = (
    FlatnessNoDatumReferencesRule,
    StraightnessNoDatumReferencesRule,
    DuplicateDatumReferencesRule,
    PositionRequiresDatumReferenceRule,
    ProjectedZoneRequiresPositionRule,
)


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

    subparsers = parser.add_subparsers(dest="command")
    check_parser = subparsers.add_parser(
        "check",
        help="Check a YAML drawing against the GD&T rule engine.",
    )
    check_parser.add_argument(
        "path",
        help="Path to a YAML drawing file.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    if args.command == "check":
        return _check(args.path)

    parser.print_help()
    return 0


def _build_registry() -> RuleRegistry:
    registry = RuleRegistry()
    for rule_cls in _RULE_CLASSES:
        registry.register(rule_cls)
    return registry


def _check(path: str) -> int:
    try:
        drawing = load_drawing_from_yaml_file(path)
    except (IngestError, OSError) as error:
        print(f"error: could not load {path!r}: {error}", file=sys.stderr)
        return 2

    findings = RuleEngine(registry=_build_registry()).run(drawing)
    _print_report(path, drawing, findings)

    return 1 if findings else 0


def _print_report(path: str, drawing: Drawing, findings: list[Finding]) -> None:
    print(f"Checked {path} -- drawing {drawing.id!r} ({drawing.title!r})")
    print(f"Rules run: {len(_RULE_CLASSES)}")
    print()

    if not findings:
        print("No findings.")
        return

    for finding in findings:
        print(_format_finding(finding))
        print()

    print(f"{len(findings)} finding(s): {_summarize_severities(findings)}")


def _format_finding(finding: Finding) -> str:
    lines = [f"[{finding.severity.value.upper()}] {finding.rule_id}: {finding.title}"]
    lines.append(f"  {finding.message}")

    locations = [
        f"{name}={value}"
        for name, value in (
            ("feature", finding.feature_id),
            ("dimension", finding.dimension_id),
            ("fcf", finding.fcf_id),
            ("datum", finding.datum_label),
        )
        if value is not None
    ]
    if locations:
        lines.append(f"  location: {' '.join(locations)}")

    return "\n".join(lines)


def _summarize_severities(findings: list[Finding]) -> str:
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.severity.value] = counts.get(finding.severity.value, 0) + 1
    return ", ".join(f"{count} {severity}" for severity, count in counts.items())


if __name__ == "__main__":
    raise SystemExit(main())

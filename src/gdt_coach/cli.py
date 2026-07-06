"""Command-line entry point for gdt-coach."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from gdt_coach import __version__
from gdt_coach.ingest import load_drawing_from_yaml_file
from gdt_coach.ingest.exceptions import IngestError
from gdt_coach.models import Drawing
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.checks import ALL_RULE_CLASSES
from gdt_coach.rules.engine import RuleEngine
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.registry import RuleRegistry
from gdt_coach.rules.standard import Standard


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
    check_parser.add_argument(
        "--category",
        dest="categories",
        action="append",
        metavar="CATEGORY",
        help=(
            "Only run rules in this category (repeatable). One of: "
            + ", ".join(category.value for category in RuleCategory)
        ),
    )
    check_parser.add_argument(
        "--standard",
        dest="standard",
        metavar="STANDARD",
        help=(
            "Only run rules for this standard. One of: "
            + ", ".join(standard.value for standard in Standard)
        ),
    )
    check_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Emit a JSON report instead of the plain-text report.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    if args.command == "check":
        return _check(
            args.path,
            categories=args.categories,
            standard=args.standard,
            json_output=args.json_output,
        )

    parser.print_help()
    return 0


def _build_registry() -> RuleRegistry:
    registry = RuleRegistry()
    for rule_cls in ALL_RULE_CLASSES:
        registry.register(rule_cls)
    return registry


def _parse_categories(values: list[str] | None) -> set[RuleCategory] | None:
    if values is None:
        return None
    try:
        return {RuleCategory(value) for value in values}
    except ValueError as error:
        valid = ", ".join(category.value for category in RuleCategory)
        message = f"invalid --category value ({error}); valid categories: {valid}"
        raise ValueError(message) from error


def _parse_standard(value: str | None) -> Standard | None:
    if value is None:
        return None
    try:
        return Standard(value)
    except ValueError as error:
        valid = ", ".join(standard.value for standard in Standard)
        raise ValueError(f"invalid --standard value ({error}); valid standards: {valid}") from error


def _count_matching_rules(
    registry: RuleRegistry,
    categories: set[RuleCategory] | None,
    standard: Standard | None,
) -> int:
    count = 0
    for rule in registry.all():
        if categories is not None and rule.category not in categories:
            continue
        if standard is not None and rule.standard != standard:
            continue
        count += 1
    return count


def _check(
    path: str,
    *,
    categories: list[str] | None = None,
    standard: str | None = None,
    json_output: bool = False,
) -> int:
    try:
        drawing = load_drawing_from_yaml_file(path)
    except (IngestError, OSError) as error:
        print(f"error: could not load {path!r}: {error}", file=sys.stderr)
        return 2

    try:
        parsed_categories = _parse_categories(categories)
        parsed_standard = _parse_standard(standard)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    registry = _build_registry()
    findings = RuleEngine(registry=registry).run(
        drawing, categories=parsed_categories, standard=parsed_standard
    )
    rules_run = _count_matching_rules(registry, parsed_categories, parsed_standard)

    if json_output:
        _print_json_report(path, drawing, findings, rules_run=rules_run)
    else:
        _print_report(path, drawing, findings, rules_run=rules_run)

    return 1 if findings else 0


def _count_by_severity(findings: list[Finding]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.severity.value] = counts.get(finding.severity.value, 0) + 1
    return counts


def _format_severity_counts(counts: dict[str, int]) -> str:
    return ", ".join(f"{count} {severity}" for severity, count in counts.items())


def _print_report(path: str, drawing: Drawing, findings: list[Finding], *, rules_run: int) -> None:
    print(f"Checked {path} -- drawing {drawing.id!r} ({drawing.title!r})")
    print(f"Rules run: {rules_run}")
    print()

    if not findings:
        print("No findings.")
        return

    for finding in findings:
        print(_format_finding(finding))
        print()

    counts = _count_by_severity(findings)
    print(f"{len(findings)} finding(s): {_format_severity_counts(counts)}")


def _print_json_report(
    path: str, drawing: Drawing, findings: list[Finding], *, rules_run: int
) -> None:
    report = {
        "path": path,
        "drawing": {"id": drawing.id, "title": drawing.title},
        "rules_run": rules_run,
        "findings": [finding.model_dump(mode="json") for finding in findings],
        "summary": {
            "finding_count": len(findings),
            "by_severity": _count_by_severity(findings),
        },
    }
    print(json.dumps(report, indent=2))


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


if __name__ == "__main__":
    raise SystemExit(main())

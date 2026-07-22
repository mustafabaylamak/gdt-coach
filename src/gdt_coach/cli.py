"""Command-line entry point for gdt-coach."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from gdt_coach import __version__
from gdt_coach.ingest import ALL_INPUT_ADAPTERS, AdapterRegistry
from gdt_coach.ingest.exceptions import IngestError, UnsupportedFormatError
from gdt_coach.models import Drawing
from gdt_coach.rules.audit_status import RuleAuditStatus
from gdt_coach.rules.base import Rule
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.checks import ALL_RULE_CLASSES
from gdt_coach.rules.engine import RuleEngine
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.registry import RuleRegistry
from gdt_coach.rules.severity import Severity
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
        help="Check one or more YAML/CSV drawings against the GD&T rule engine.",
    )
    check_parser.add_argument(
        "paths",
        nargs="+",
        metavar="path",
        help=(
            "One or more paths to check: a drawing file, or a directory "
            "(scanned non-recursively) of drawing files. More than one "
            "path, or any directory, switches to an aggregate batch report."
        ),
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
    output_format_group = check_parser.add_mutually_exclusive_group()
    output_format_group.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Emit a JSON report instead of the plain-text report.",
    )
    output_format_group.add_argument(
        "--markdown",
        dest="markdown_output",
        action="store_true",
        help="Emit a Markdown report instead of the plain-text report.",
    )

    rules_parser = subparsers.add_parser(
        "rules",
        help="Inspect the registered GD&T rule catalog (derived from the rule engine itself).",
    )
    rules_subparsers = rules_parser.add_subparsers(dest="rules_command", required=True)

    rules_list_parser = rules_subparsers.add_parser(
        "list",
        help="List every registered rule.",
    )
    rules_list_parser.add_argument(
        "--category",
        dest="categories",
        action="append",
        metavar="CATEGORY",
        help=(
            "Only list rules in this category (repeatable). One of: "
            + ", ".join(category.value for category in RuleCategory)
        ),
    )
    rules_list_parser.add_argument(
        "--standard",
        dest="standard",
        metavar="STANDARD",
        help=(
            "Only list rules for this standard. One of: "
            + ", ".join(standard.value for standard in Standard)
        ),
    )
    rules_list_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Emit JSON instead of the plain-text list.",
    )

    rules_show_parser = rules_subparsers.add_parser(
        "show",
        help="Show full detail (including the explanation) for one rule.",
    )
    rules_show_parser.add_argument(
        "rule_id",
        help="The rule id to show (e.g. position-requires-feature-of-size).",
    )
    rules_show_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Emit JSON instead of plain text.",
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
            args.paths,
            categories=args.categories,
            standard=args.standard,
            json_output=args.json_output,
            markdown_output=args.markdown_output,
        )

    if args.command == "rules":
        if args.rules_command == "list":
            return _rules_list(
                categories=args.categories,
                standard=args.standard,
                json_output=args.json_output,
            )
        return _rules_show(args.rule_id, json_output=args.json_output)

    parser.print_help()
    return 0


def _build_registry() -> RuleRegistry:
    registry = RuleRegistry()
    for rule_cls in ALL_RULE_CLASSES:
        registry.register(rule_cls)
    return registry


def _build_adapter_registry() -> AdapterRegistry:
    registry = AdapterRegistry()
    for adapter_cls in ALL_INPUT_ADAPTERS:
        registry.register(adapter_cls)
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


def _matching_rules(
    registry: RuleRegistry,
    categories: set[RuleCategory] | None,
    standard: Standard | None,
) -> list[Rule]:
    """Registered rules matching the given filters, sorted by id for deterministic output."""
    rules = registry.all()
    if categories is not None:
        rules = [rule for rule in rules if rule.category in categories]
    if standard is not None:
        rules = [rule for rule in rules if rule.standard == standard]
    return sorted(rules, key=lambda rule: rule.id)


def _has_open_standard_question(rule: Rule) -> bool:
    return rule.audit_status == RuleAuditStatus.INTERNALLY_AUDITED_WITH_OPEN_STANDARD_QUESTION


def _rule_summary(rule: Rule) -> dict[str, str | bool]:
    return {
        "id": rule.id,
        "title": rule.title,
        "category": rule.category.value,
        "standard": rule.standard.value,
        "severity": rule.severity.value,
        "audit_status": rule.audit_status.value,
        "has_open_standard_question": _has_open_standard_question(rule),
    }


def _rule_detail(rule: Rule) -> dict[str, str | bool | None]:
    detail: dict[str, str | bool | None] = dict(_rule_summary(rule))
    detail["explanation"] = rule.explanation
    detail["standard_question_note"] = rule.standard_question_note
    return detail


def _rules_list(
    *,
    categories: list[str] | None = None,
    standard: str | None = None,
    json_output: bool = False,
) -> int:
    try:
        parsed_categories = _parse_categories(categories)
        parsed_standard = _parse_standard(standard)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    rules = _matching_rules(_build_registry(), parsed_categories, parsed_standard)

    if json_output:
        print(json.dumps({"rules": [_rule_summary(rule) for rule in rules]}, indent=2))
    else:
        _print_rules_list(rules)

    return 0


def _print_rules_list(rules: list[Rule]) -> None:
    if not rules:
        print("No rules match the given filters.")
        return

    for rule in rules:
        open_question_marker = (
            "  [OPEN STANDARD QUESTION]" if _has_open_standard_question(rule) else ""
        )
        print(
            f"{rule.id}  [{rule.severity.value.upper()}]  "
            f"category={rule.category.value} standard={rule.standard.value} "
            f"audit={rule.audit_status.value}{open_question_marker}"
        )
        print(f"  {rule.title}")
        print()

    print(f"{len(rules)} rule(s).")


def _rules_show(rule_id: str, *, json_output: bool = False) -> int:
    try:
        rule = _build_registry().get(rule_id)
    except KeyError:
        print(f"error: no rule registered with id {rule_id!r}", file=sys.stderr)
        return 2

    if json_output:
        print(json.dumps(_rule_detail(rule), indent=2))
    else:
        _print_rule_detail(rule)

    return 0


def _print_rule_detail(rule: Rule) -> None:
    print(f"id: {rule.id}")
    print(f"title: {rule.title}")
    print(f"category: {rule.category.value}")
    print(f"standard: {rule.standard.value}")
    print(f"severity: {rule.severity.value.upper()}")
    print(f"audit status: {rule.audit_status.value}")
    print(f"open standard question: {'yes' if _has_open_standard_question(rule) else 'no'}")
    if rule.standard_question_note:
        print(f"standard question note: {rule.standard_question_note}")
    print()
    print(rule.explanation)
    print()
    print(
        "Internal audit status reflects gdt-coach's own review of this "
        "rule's implementation (see RULE_AUDIT.md). It is not an ASME "
        "Y14.5 certification and does not by itself verify conformance "
        "with the standard."
    )


# --- Per-file result model (Sprint 16) --------------------------------------


@dataclass(frozen=True)
class _FileCheckSuccess:
    """One file that loaded and was checked successfully."""

    path: str
    drawing: Drawing
    findings: list[Finding]
    rules_run: int

    @property
    def has_findings(self) -> bool:
        """Whether this file would exit 1 under the existing single-file semantics."""
        return bool(self.findings)


@dataclass(frozen=True)
class _FileCheckError:
    """One input (a supplied path, or a path discovered while expanding a directory)
    that could not be turned into a checked Drawing -- an expansion-time problem
    (missing path, empty directory) or a load-time one (unsupported extension,
    malformed input, failed domain validation)."""

    path: str
    error_type: str
    message: str


_FileCheckResult = _FileCheckSuccess | _FileCheckError


@dataclass(frozen=True)
class _ExpansionError:
    """An input path argument that couldn't be expanded into any file to check."""

    path: str
    error_type: str
    message: str


def _known_extensions(adapter_registry: AdapterRegistry) -> set[str]:
    """Every file extension any registered adapter claims, lower-cased.

    Never hardcodes a format's extensions -- directory scanning stays
    generic over whatever adapters happen to be registered, the same way
    ``AdapterRegistry.resolve`` already is for a single explicit file.
    """
    return {ext.lower() for adapter in adapter_registry.all() for ext in adapter.file_extensions}


def _expand_paths(
    paths: list[str], adapter_registry: AdapterRegistry
) -> list[Path | _ExpansionError]:
    """Expand CLI path arguments into concrete candidate files, in deterministic order.

    Each input argument becomes one of:
    - a directory: its immediate (non-recursive) children whose extension is
      known to `adapter_registry`, sorted by filename; an empty match is one
      `_ExpansionError` for the directory itself
    - an explicit file: itself, if it exists and its extension is supported;
      a missing path or an unsupported extension is one `_ExpansionError`
      each. Extension support is checked here via `adapter_registry.resolve`
      -- the same call `_load_one_file` makes -- so "is this extension
      supported" is never reimplemented, only invoked earlier.

    Files are deduplicated by resolved (absolute, symlink-resolved) identity,
    keeping only the first occurrence -- whether the duplicate came from two
    explicit arguments, two overlapping directories, or an explicit file also
    reachable through a directory argument.
    """
    known_extensions = _known_extensions(adapter_registry)
    seen: set[Path] = set()
    items: list[Path | _ExpansionError] = []

    for raw in paths:
        candidate = Path(raw)

        if candidate.is_dir():
            matches = sorted(
                (
                    child
                    for child in candidate.iterdir()
                    if child.is_file() and child.suffix.lower() in known_extensions
                ),
                key=lambda child: child.name,
            )
            if not matches:
                items.append(
                    _ExpansionError(
                        path=raw,
                        error_type="NoSupportedFilesError",
                        message=f"no supported input files found in directory {raw!r}",
                    )
                )
                continue
            for child in matches:
                key = child.resolve()
                if key in seen:
                    continue
                seen.add(key)
                items.append(child)
            continue

        if not candidate.exists():
            items.append(
                _ExpansionError(
                    path=raw,
                    error_type="PathNotFoundError",
                    message=f"path not found: {raw!r}",
                )
            )
            continue

        try:
            adapter_registry.resolve(candidate)
        except UnsupportedFormatError as error:
            items.append(
                _ExpansionError(path=raw, error_type="UnsupportedFormatError", message=str(error))
            )
            continue

        key = candidate.resolve()
        if key in seen:
            continue
        seen.add(key)
        items.append(candidate)

    return items


def _is_batch_mode(paths: list[str]) -> bool:
    """More than one path, or any single path that's a directory, is batch mode.

    A single directory that happens to expand to exactly one file still
    produces an aggregate batch report -- the *arguments* decide the mode,
    not how many files expansion happens to discover.
    """
    return len(paths) != 1 or Path(paths[0]).is_dir()


def _load_one_file(path: Path, adapter_registry: AdapterRegistry) -> Drawing:
    """Resolve and load `path` into a Drawing.

    Raises `IngestError` or `OSError` on failure -- shared, unmodified by
    Sprint 16, by both the single-file and batch-mode check paths, so
    resolve/load validation is never duplicated between them.
    """
    adapter = adapter_registry.resolve(path)
    return adapter.load(path)


def _check_one_file(
    path: Path,
    *,
    adapter_registry: AdapterRegistry,
    registry: RuleRegistry,
    categories: set[RuleCategory] | None,
    standard: Standard | None,
) -> _FileCheckResult:
    try:
        drawing = _load_one_file(path, adapter_registry)
    except (IngestError, OSError) as error:
        return _FileCheckError(path=str(path), error_type=type(error).__name__, message=str(error))

    findings = RuleEngine(registry=registry).run(drawing, categories=categories, standard=standard)
    rules_run = _count_matching_rules(registry, categories, standard)
    return _FileCheckSuccess(
        path=str(path), drawing=drawing, findings=findings, rules_run=rules_run
    )


# --- `check` dispatch --------------------------------------------------------


def _check(
    paths: list[str],
    *,
    categories: list[str] | None = None,
    standard: str | None = None,
    json_output: bool = False,
    markdown_output: bool = False,
) -> int:
    adapter_registry = _build_adapter_registry()
    registry = _build_registry()

    if _is_batch_mode(paths):
        return _check_batch(
            paths,
            adapter_registry=adapter_registry,
            registry=registry,
            categories=categories,
            standard=standard,
            json_output=json_output,
            markdown_output=markdown_output,
        )

    return _check_single_file(
        paths[0],
        adapter_registry=adapter_registry,
        registry=registry,
        categories=categories,
        standard=standard,
        json_output=json_output,
        markdown_output=markdown_output,
    )


def _check_single_file(
    path: str,
    *,
    adapter_registry: AdapterRegistry,
    registry: RuleRegistry,
    categories: list[str] | None,
    standard: str | None,
    json_output: bool,
    markdown_output: bool,
) -> int:
    """Single-file compatibility mode -- byte-identical to Sprint 15.

    Load-before-filter-parsing error precedence is preserved exactly (a
    missing/malformed file is reported even if a filter value is also
    invalid), which is why this isn't just a call into `_check_one_file`
    (that helper assumes filters are already parsed, since batch mode
    validates filters up front for all files at once -- see `_check_batch`).
    """
    try:
        path_obj = Path(path)
        drawing = _load_one_file(path_obj, adapter_registry)
    except (IngestError, OSError) as error:
        print(f"error: could not load {path!r}: {error}", file=sys.stderr)
        return 2

    try:
        parsed_categories = _parse_categories(categories)
        parsed_standard = _parse_standard(standard)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    findings = RuleEngine(registry=registry).run(
        drawing, categories=parsed_categories, standard=parsed_standard
    )
    rules_run = _count_matching_rules(registry, parsed_categories, parsed_standard)

    if json_output:
        _print_json_report(path, drawing, findings, rules_run=rules_run)
    elif markdown_output:
        _print_markdown_report(path, drawing, findings, rules_run=rules_run)
    else:
        _print_report(path, drawing, findings, rules_run=rules_run)

    return 1 if findings else 0


def _check_batch(
    paths: list[str],
    *,
    adapter_registry: AdapterRegistry,
    registry: RuleRegistry,
    categories: list[str] | None,
    standard: str | None,
    json_output: bool,
    markdown_output: bool,
) -> int:
    """Batch mode: filters are validated for all files up front (an invalid
    filter means no file is ever touched), then every resolved file is
    checked and reported, even if some fail -- partial failure never stops
    the rest of the batch from being processed."""
    try:
        parsed_categories = _parse_categories(categories)
        parsed_standard = _parse_standard(standard)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    items = _expand_paths(paths, adapter_registry)
    files_discovered = sum(1 for item in items if isinstance(item, Path))

    results: list[_FileCheckResult] = []
    for item in items:
        if isinstance(item, _ExpansionError):
            results.append(
                _FileCheckError(path=item.path, error_type=item.error_type, message=item.message)
            )
        else:
            results.append(
                _check_one_file(
                    item,
                    adapter_registry=adapter_registry,
                    registry=registry,
                    categories=parsed_categories,
                    standard=parsed_standard,
                )
            )

    if json_output:
        _print_batch_json_report(
            results, inputs_supplied=len(paths), files_discovered=files_discovered
        )
    elif markdown_output:
        _print_batch_markdown_report(
            results, inputs_supplied=len(paths), files_discovered=files_discovered
        )
    else:
        _print_batch_text_report(
            results, inputs_supplied=len(paths), files_discovered=files_discovered
        )

    return _batch_exit_code(results)


def _batch_exit_code(results: list[_FileCheckResult]) -> int:
    if any(isinstance(result, _FileCheckError) for result in results):
        return 2
    if any(isinstance(result, _FileCheckSuccess) and result.has_findings for result in results):
        return 1
    return 0


def _count_by_severity(findings: list[Finding]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.severity.value] = counts.get(finding.severity.value, 0) + 1
    return counts


def _aggregate_severity_counts(successes: list[_FileCheckSuccess]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in successes:
        for severity, count in _count_by_severity(result.findings).items():
            counts[severity] = counts.get(severity, 0) + count
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


# --- Batch reports (Sprint 16) -----------------------------------------------

_BATCH_TEXT_SEPARATOR = "=" * 70


def _print_batch_text_report(
    results: list[_FileCheckResult], *, inputs_supplied: int, files_discovered: int
) -> None:
    for result in results:
        print(_BATCH_TEXT_SEPARATOR)
        if isinstance(result, _FileCheckSuccess):
            _print_report(result.path, result.drawing, result.findings, rules_run=result.rules_run)
        else:
            print(f"Could not check {result.path!r}")
            print(f"error [{result.error_type}]: {result.message}")
        print()

    print(_BATCH_TEXT_SEPARATOR)
    _print_batch_summary_text(
        results, inputs_supplied=inputs_supplied, files_discovered=files_discovered
    )


def _print_batch_summary_text(
    results: list[_FileCheckResult], *, inputs_supplied: int, files_discovered: int
) -> None:
    successes = [result for result in results if isinstance(result, _FileCheckSuccess)]
    errors = [result for result in results if isinstance(result, _FileCheckError)]
    with_findings = [result for result in successes if result.has_findings]
    total_findings = sum(len(result.findings) for result in successes)
    severity_counts = _aggregate_severity_counts(successes)

    print("Summary")
    print(f"Input items supplied: {inputs_supplied}")
    print(f"Files discovered: {files_discovered}")
    print(f"Files checked: {len(successes)}")
    print(f"Files failed: {len(errors)}")
    print(f"Files with findings: {len(with_findings)}")
    print(f"Total findings: {total_findings}")
    if severity_counts:
        print(f"By severity: {_format_severity_counts(severity_counts)}")


def _batch_result_json(result: _FileCheckResult) -> dict[str, object]:
    if isinstance(result, _FileCheckSuccess):
        return {
            "path": result.path,
            "status": "checked",
            "drawing": {"id": result.drawing.id, "title": result.drawing.title},
            "rules_run": result.rules_run,
            "findings": [finding.model_dump(mode="json") for finding in result.findings],
        }
    return {
        "path": result.path,
        "status": "error",
        "error": {"type": result.error_type, "message": result.message},
    }


def _print_batch_json_report(
    results: list[_FileCheckResult], *, inputs_supplied: int, files_discovered: int
) -> None:
    successes = [result for result in results if isinstance(result, _FileCheckSuccess)]
    errors = [result for result in results if isinstance(result, _FileCheckError)]
    with_findings = [result for result in successes if result.has_findings]
    total_findings = sum(len(result.findings) for result in successes)

    report = {
        "results": [_batch_result_json(result) for result in results],
        "summary": {
            "inputs_supplied": inputs_supplied,
            "files_discovered": files_discovered,
            "files_checked": len(successes),
            "files_failed": len(errors),
            "files_with_findings": len(with_findings),
            "total_findings": total_findings,
            "severity_counts": _aggregate_severity_counts(successes),
        },
    }
    print(json.dumps(report, indent=2))


def _print_batch_markdown_report(
    results: list[_FileCheckResult], *, inputs_supplied: int, files_discovered: int
) -> None:
    successes = [result for result in results if isinstance(result, _FileCheckSuccess)]
    errors = [result for result in results if isinstance(result, _FileCheckError)]
    with_findings = [result for result in successes if result.has_findings]
    total_findings = sum(len(result.findings) for result in successes)
    severity_counts = _aggregate_severity_counts(successes)

    print("# GD&T Batch Check Report")
    print()
    print("## Summary")
    print()
    print("| Field | Value |")
    print("|---|---|")
    print(_markdown_table_row("Input items supplied", str(inputs_supplied)))
    print(_markdown_table_row("Files discovered", str(files_discovered)))
    print(_markdown_table_row("Files checked", str(len(successes))))
    print(_markdown_table_row("Files failed", str(len(errors))))
    print(_markdown_table_row("Files with findings", str(len(with_findings))))
    print(_markdown_table_row("Total findings", str(total_findings)))
    print()

    if severity_counts:
        print("| Severity | Count |")
        print("|---|---:|")
        for severity in _MARKDOWN_SEVERITY_ORDER:
            count = severity_counts.get(severity.value, 0)
            if count:
                print(_markdown_table_row(severity.value.title(), str(count)))
        print()

    print("## Results")
    print()
    for result in results:
        print(f"### `{_escape_markdown(result.path)}`")
        print()
        if isinstance(result, _FileCheckSuccess):
            _markdown_drawing_table(result.path, result.drawing, rules_run=result.rules_run)
            print()
            _markdown_severity_summary_table(result.findings)
            print()
            _markdown_findings_section(result.findings, heading_level=4)
            print()
        else:
            error_type = _escape_markdown(result.error_type)
            error_message = _escape_markdown(result.message)
            print(f"**Error ({error_type}):** {error_message}")
            print()


_MARKDOWN_SEVERITY_ORDER: tuple[Severity, ...] = (
    Severity.CRITICAL,
    Severity.ERROR,
    Severity.WARNING,
    Severity.INFO,
)


def _escape_markdown(value: str) -> str:
    """Neutralize Markdown-sensitive characters in externally-sourced text.

    Applied to every id/title/message pulled from drawing or finding data
    before it's embedded in the Markdown report, so a value containing
    ``|`` can't break a table row, a leading ``[`` can't be read as a link,
    and ``<``/``>`` can't be misread as inline HTML by a Markdown renderer.
    Newlines are collapsed to a space so every field stays on one line.
    """
    escaped = value.replace("\\", "\\\\")
    for char in ("`", "*", "_", "|", "<", ">", "["):
        escaped = escaped.replace(char, f"\\{char}")
    return escaped.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")


def _markdown_table_row(*cells: str) -> str:
    return "| " + " | ".join(_escape_markdown(cell) for cell in cells) + " |"


def _markdown_drawing_table(path: str, drawing: Drawing, *, rules_run: int) -> None:
    print("| Field | Value |")
    print("|---|---|")
    print(_markdown_table_row("Source", path))
    print(_markdown_table_row("Drawing ID", drawing.id))
    print(_markdown_table_row("Title", drawing.title))
    print(_markdown_table_row("Rules run", str(rules_run)))


def _markdown_severity_summary_table(findings: list[Finding]) -> None:
    print("| Severity | Count |")
    print("|---|---:|")
    counts = _count_by_severity(findings)
    for severity in _MARKDOWN_SEVERITY_ORDER:
        count = counts.get(severity.value, 0)
        if count:
            print(_markdown_table_row(severity.value.title(), str(count)))
    print(f"| **Total** | {len(findings)} |")


def _markdown_findings_section(findings: list[Finding], *, heading_level: int = 3) -> None:
    if not findings:
        print("No findings were found.")
        return

    heading_marker = "#" * heading_level
    for finding in findings:
        severity_label = finding.severity.value.upper()
        rule_id = _escape_markdown(finding.rule_id)
        print(f"{heading_marker} {severity_label} - {rule_id}")
        print()
        print(f"**Rule:** {_escape_markdown(finding.title)}")
        print()
        print(_escape_markdown(finding.message))

        locations = [
            f"{name}={_escape_markdown(value)}" for name, value in _finding_locator_pairs(finding)
        ]
        if locations:
            print()
            print(f"**Location:** {', '.join(locations)}")
        print()


def _print_markdown_report(
    path: str, drawing: Drawing, findings: list[Finding], *, rules_run: int
) -> None:
    print("# GD&T Check Report")
    print()
    print("## Drawing")
    print()
    _markdown_drawing_table(path, drawing, rules_run=rules_run)
    print()

    print("## Summary")
    print()
    _markdown_severity_summary_table(findings)
    print()

    print("## Findings")
    print()
    _markdown_findings_section(findings)


def _finding_locator_pairs(finding: Finding) -> list[tuple[str, str]]:
    """The finding's non-``None`` locator fields, in a fixed display order."""
    return [
        (name, value)
        for name, value in (
            ("feature", finding.feature_id),
            ("dimension", finding.dimension_id),
            ("fcf", finding.fcf_id),
            ("datum", finding.datum_label),
        )
        if value is not None
    ]


def _format_finding(finding: Finding) -> str:
    lines = [f"[{finding.severity.value.upper()}] {finding.rule_id}: {finding.title}"]
    lines.append(f"  {finding.message}")

    locations = [f"{name}={value}" for name, value in _finding_locator_pairs(finding)]
    if locations:
        lines.append(f"  location: {' '.join(locations)}")

    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())

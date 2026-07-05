"""Tests for the CLI, including the `check` command."""

from pathlib import Path

import pytest

from gdt_coach import __version__
from gdt_coach.cli import _format_finding, _summarize_severities, build_parser, main
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard

_EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def _finding(**overrides: object) -> Finding:
    defaults: dict[str, object] = {
        "rule_id": "r1",
        "title": "Title",
        "severity": Severity.WARNING,
        "standard": Standard.GENERAL,
        "category": RuleCategory.GENERAL,
        "message": "A message.",
    }
    defaults.update(overrides)
    return Finding.model_validate(defaults)


def test_version_flag(capsys: object) -> None:
    exit_code = main(["--version"])

    assert exit_code == 0


def test_no_args_prints_help(capsys: object) -> None:
    exit_code = main([])

    assert exit_code == 0


def test_build_parser_returns_parser() -> None:
    parser = build_parser()

    assert parser.prog == "gdt-coach"


def test_package_version_is_set() -> None:
    assert __version__ == "0.1.0"


def test_check_valid_example_exits_zero() -> None:
    path = _EXAMPLES_DIR / "valid_position.yaml"

    exit_code = main(["check", str(path)])

    assert exit_code == 0


def test_check_invalid_flatness_example_exits_one() -> None:
    path = _EXAMPLES_DIR / "invalid_flatness_with_datum.yaml"

    exit_code = main(["check", str(path)])

    assert exit_code == 1


def test_check_invalid_projected_zone_example_exits_one() -> None:
    path = _EXAMPLES_DIR / "invalid_projected_zone.yaml"

    exit_code = main(["check", str(path)])

    assert exit_code == 1


def test_check_malformed_yaml_exits_two(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("id: [unclosed", encoding="utf-8")

    exit_code = main(["check", str(bad_file)])

    assert exit_code == 2


def test_check_nonexistent_file_exits_two(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.yaml"

    exit_code = main(["check", str(missing)])

    assert exit_code == 2


def test_check_output_includes_rule_id_severity_message_and_location(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _EXAMPLES_DIR / "invalid_flatness_with_datum.yaml"

    main(["check", str(path)])

    out = capsys.readouterr().out
    assert "flatness-no-datum-references" in out
    assert "ERROR" in out
    assert "flatness must not reference any datum" in out
    assert "feature=feat-surface-1" in out
    assert "fcf=fcf-1" in out


def test_check_valid_example_reports_no_findings(capsys: pytest.CaptureFixture[str]) -> None:
    path = _EXAMPLES_DIR / "valid_position.yaml"

    main(["check", str(path)])

    out = capsys.readouterr().out
    assert "No findings." in out


def test_check_malformed_yaml_writes_error_to_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("id: [unclosed", encoding="utf-8")

    main(["check", str(bad_file)])

    captured = capsys.readouterr()
    assert "error" in captured.err.lower()
    assert captured.out == ""


def test_check_summary_includes_finding_count(capsys: pytest.CaptureFixture[str]) -> None:
    path = _EXAMPLES_DIR / "invalid_projected_zone.yaml"

    main(["check", str(path)])

    out = capsys.readouterr().out
    assert "1 finding(s)" in out


def test_format_finding_includes_rule_id_severity_and_message() -> None:
    finding = _finding(rule_id="r1", severity=Severity.ERROR, message="Something is wrong.")

    formatted = _format_finding(finding)

    assert "r1" in formatted
    assert "ERROR" in formatted
    assert "Something is wrong." in formatted


def test_format_finding_with_no_location_omits_location_line() -> None:
    finding = _finding()

    formatted = _format_finding(finding)

    assert "location:" not in formatted


def test_format_finding_with_partial_location() -> None:
    finding = _finding(feature_id="feat-1")

    formatted = _format_finding(finding)

    assert "location: feature=feat-1" in formatted
    assert "dimension=" not in formatted


def test_summarize_severities_counts_by_severity() -> None:
    findings = [
        _finding(severity=Severity.ERROR),
        _finding(severity=Severity.ERROR),
        _finding(severity=Severity.WARNING),
    ]

    summary = _summarize_severities(findings)

    assert "2 error" in summary
    assert "1 warning" in summary

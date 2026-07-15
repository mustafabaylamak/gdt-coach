"""Tests for the CLI, including the `check` command."""

import json
from pathlib import Path

import pytest

from gdt_coach import __version__
from gdt_coach.cli import (
    _count_by_severity,
    _format_finding,
    _format_severity_counts,
    build_parser,
    main,
)
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.checks import ALL_RULE_CLASSES
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


def test_count_by_severity_counts_by_severity() -> None:
    findings = [
        _finding(severity=Severity.ERROR),
        _finding(severity=Severity.ERROR),
        _finding(severity=Severity.WARNING),
    ]

    counts = _count_by_severity(findings)

    assert counts == {"error": 2, "warning": 1}


def test_format_severity_counts_renders_readable_summary() -> None:
    summary = _format_severity_counts({"error": 2, "warning": 1})

    assert "2 error" in summary
    assert "1 warning" in summary


# --- --category / --standard filters -------------------------------------


def test_check_category_filter_excludes_non_matching_rule(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _EXAMPLES_DIR / "invalid_flatness_with_datum.yaml"

    exit_code = main(["check", str(path), "--category", "tolerance"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Rules run: 2" in out  # TOLERANCE category: projected-zone-requires-position + POS.003
    assert "No findings." in out


def test_check_category_filter_still_catches_matching_rule(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _EXAMPLES_DIR / "invalid_flatness_with_datum.yaml"

    exit_code = main(["check", str(path), "--category", "feature_control_frame"])

    assert exit_code == 1
    out = capsys.readouterr().out
    assert "flatness-no-datum-references" in out


def test_check_category_filter_is_repeatable(capsys: pytest.CaptureFixture[str]) -> None:
    path = _EXAMPLES_DIR / "invalid_flatness_with_datum.yaml"

    exit_code = main(
        ["check", str(path), "--category", "feature_control_frame", "--category", "tolerance"]
    )

    assert exit_code == 1
    out = capsys.readouterr().out
    # union of feature_control_frame (13) + tolerance (2) = 15; the 3 DIMENSION
    # category rules (added in Sprint 9) are outside this union
    assert "Rules run: 15" in out


def test_check_standard_filter_narrows_rules_run(capsys: pytest.CaptureFixture[str]) -> None:
    path = _EXAMPLES_DIR / "valid_position.yaml"

    exit_code = main(["check", str(path), "--standard", "general"])

    assert exit_code == 0
    out = capsys.readouterr().out
    # GENERAL standard: fcf-duplicate-datum-references, datum-reference-must-be-defined,
    # related-dimension-must-be-defined, related-dimension-must-not-be-reference
    assert "Rules run: 4" in out


def test_check_invalid_category_exits_two_with_stderr_message(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _EXAMPLES_DIR / "valid_position.yaml"

    exit_code = main(["check", str(path), "--category", "bogus"])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "invalid --category value" in captured.err
    assert "drawing" in captured.err  # valid options are listed


def test_check_invalid_standard_exits_two_with_stderr_message(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _EXAMPLES_DIR / "valid_position.yaml"

    exit_code = main(["check", str(path), "--standard", "bogus"])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "invalid --standard value" in captured.err


# --- --json output ---------------------------------------------------------


def test_check_json_output_is_valid_json(capsys: pytest.CaptureFixture[str]) -> None:
    path = _EXAMPLES_DIR / "invalid_projected_zone.yaml"

    exit_code = main(["check", str(path), "--json"])

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["path"] == str(path)
    assert payload["drawing"] == {"id": "dwg-003", "title": "Threaded Plate"}
    assert payload["rules_run"] == 20
    assert payload["summary"] == {"finding_count": 1, "by_severity": {"error": 1}}
    assert len(payload["findings"]) == 1
    finding = payload["findings"][0]
    assert finding["rule_id"] == "projected-zone-requires-position"
    assert finding["severity"] == "error"
    assert finding["feature_id"] == "feat-hole-1"
    assert finding["fcf_id"] == "fcf-1"
    assert finding["dimension_id"] is None


def test_check_json_output_with_no_findings(capsys: pytest.CaptureFixture[str]) -> None:
    path = _EXAMPLES_DIR / "valid_position.yaml"

    exit_code = main(["check", str(path), "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["findings"] == []
    assert payload["summary"] == {"finding_count": 0, "by_severity": {}}


def test_check_json_output_respects_category_filter(capsys: pytest.CaptureFixture[str]) -> None:
    path = _EXAMPLES_DIR / "invalid_flatness_with_datum.yaml"

    exit_code = main(["check", str(path), "--json", "--category", "tolerance"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["rules_run"] == 2  # TOLERANCE: projected-zone-requires-position + POS.003
    assert payload["findings"] == []


def test_check_invalid_filter_with_json_flag_still_exits_two_plain_text(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Errors are always plain text on stderr, even with --json requested."""
    path = _EXAMPLES_DIR / "valid_position.yaml"

    exit_code = main(["check", str(path), "--json", "--category", "bogus"])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "invalid --category value" in captured.err


# --- `rules` subcommand -----------------------------------------------------


def test_rules_list_lists_every_rule(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["rules", "list"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert f"{len(ALL_RULE_CLASSES)} rule(s)." in out
    for rule_cls in ALL_RULE_CLASSES:
        assert rule_cls().id in out


def test_rules_list_output_is_deterministically_ordered(capsys: pytest.CaptureFixture[str]) -> None:
    ids_in_alphabetical_order = sorted(rule_cls().id for rule_cls in ALL_RULE_CLASSES)

    exit_code = main(["rules", "list"])

    assert exit_code == 0
    out = capsys.readouterr().out
    listed_ids = [line.split()[0] for line in out.splitlines() if "  [" in line]
    # Deterministic by construction (sorted by id), independent of
    # ALL_RULE_CLASSES declaration/registration order.
    assert listed_ids == ids_in_alphabetical_order


def test_rules_list_category_filter(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["rules", "list", "--category", "tolerance"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "2 rule(s)." in out
    assert "position-material-condition-requires-feature-of-size" in out
    assert "projected-zone-requires-position" in out
    assert "category=tolerance" in out
    assert "category=dimension" not in out


def test_rules_list_standard_filter(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["rules", "list", "--standard", "general"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "4 rule(s)." in out
    assert "standard=asme_y14.5_2018" not in out


def test_rules_list_combined_category_and_standard_filters(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        ["rules", "list", "--category", "feature_control_frame", "--standard", "general"]
    )

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "3 rule(s)." in out
    assert "datum-reference-must-be-defined" in out
    assert "fcf-duplicate-datum-references" in out
    assert "related-dimension-must-be-defined" in out


def test_rules_list_empty_filter_result_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    # No rule currently uses RuleCategory.DATUM.
    exit_code = main(["rules", "list", "--category", "datum"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "No rules match the given filters." in captured.out
    assert captured.err == ""


def test_rules_list_invalid_category_exits_two(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["rules", "list", "--category", "bogus"])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "invalid --category value" in captured.err


def test_rules_list_invalid_standard_exits_two(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["rules", "list", "--standard", "bogus"])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "invalid --standard value" in captured.err


def test_rules_list_json_output_is_valid_and_sorted(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["rules", "list", "--category", "tolerance", "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert [rule["id"] for rule in payload["rules"]] == [
        "position-material-condition-requires-feature-of-size",
        "projected-zone-requires-position",
    ]
    for rule in payload["rules"]:
        assert set(rule) == {"id", "title", "category", "standard", "severity"}
        assert rule["category"] == "tolerance"


def test_rules_list_json_empty_filter_result(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["rules", "list", "--category", "datum", "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"rules": []}


def test_rules_show_valid_rule(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["rules", "show", "position-requires-feature-of-size"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "id: position-requires-feature-of-size" in out
    assert "title: Position applies only to a Feature of Size" in out
    assert "category: feature_control_frame" in out
    assert "standard: asme_y14.5_2018" in out
    assert "severity: ERROR" in out
    assert "Feature of Size" in out  # explanation text is present


def test_rules_show_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["rules", "show", "position-requires-feature-of-size", "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == "position-requires-feature-of-size"
    assert payload["severity"] == "error"
    assert payload["category"] == "feature_control_frame"
    assert payload["standard"] == "asme_y14.5_2018"
    assert set(payload) == {"id", "title", "category", "standard", "severity", "explanation"}
    assert len(payload["explanation"]) > 0


def test_rules_show_unknown_rule_id_exits_two(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["rules", "show", "bogus-rule-id"])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "no rule registered with id 'bogus-rule-id'" in captured.err


def test_rules_show_unknown_rule_id_with_json_flag_still_plain_text_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["rules", "show", "bogus-rule-id", "--json"])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "no rule registered with id" in captured.err

"""Tests for the CLI, including the `check` command."""

import json
from pathlib import Path

import pytest

from gdt_coach import __version__
from gdt_coach.cli import (
    _count_by_severity,
    _escape_markdown,
    _finding_locator_pairs,
    _format_finding,
    _format_severity_counts,
    _markdown_table_row,
    _print_markdown_report,
    build_parser,
    main,
)
from gdt_coach.models import Drawing
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


def test_check_unsupported_extension_exits_two_with_stderr_message(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    unsupported_file = tmp_path / "drawing.pdf"
    unsupported_file.write_text("not actually a pdf", encoding="utf-8")

    exit_code = main(["check", str(unsupported_file)])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "no input adapter registered for file extension '.pdf'" in captured.err


# --- CSV end-to-end ---------------------------------------------------------


def test_check_csv_example_exits_one_with_expected_finding(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _EXAMPLES_DIR / "invalid_datum_reference_undefined.csv"

    exit_code = main(["check", str(path)])

    assert exit_code == 1
    out = capsys.readouterr().out
    assert "Rules run: 20" in out
    assert "datum-reference-must-be-defined" in out
    assert "feature=feat-hole-1" in out
    assert "fcf=fcf-1" in out
    assert "1 finding(s): 1 error" in out


def test_check_csv_json_output_is_valid_json(capsys: pytest.CaptureFixture[str]) -> None:
    path = _EXAMPLES_DIR / "invalid_datum_reference_undefined.csv"

    exit_code = main(["check", str(path), "--json"])

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["path"] == str(path)
    assert payload["drawing"] == {"id": "dwg-007", "title": "CSV Bracket"}
    assert payload["rules_run"] == 20
    assert len(payload["findings"]) == 1
    finding = payload["findings"][0]
    assert finding["rule_id"] == "datum-reference-must-be-defined"
    assert finding["severity"] == "error"
    assert finding["feature_id"] == "feat-hole-1"
    assert finding["fcf_id"] == "fcf-1"


def test_check_csv_malformed_content_exits_two(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.csv"
    bad_file.write_text("", encoding="utf-8")

    exit_code = main(["check", str(bad_file)])

    assert exit_code == 2


def test_check_csv_malformed_content_writes_error_to_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad_file = tmp_path / "bad.csv"
    bad_file.write_text("", encoding="utf-8")

    main(["check", str(bad_file)])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "error" in captured.err.lower()


def test_check_csv_uppercase_extension_resolves(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = _EXAMPLES_DIR / "invalid_datum_reference_undefined.csv"
    upper_path = tmp_path / "drawing.CSV"
    upper_path.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    exit_code = main(["check", str(upper_path)])

    assert exit_code == 1
    out = capsys.readouterr().out
    assert "datum-reference-must-be-defined" in out


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


# --- backward compatibility: default text / JSON output unchanged ----------


def test_check_default_text_output_is_unchanged(capsys: pytest.CaptureFixture[str]) -> None:
    """Adding --markdown must not change a single byte of the default text report."""
    path = _EXAMPLES_DIR / "invalid_flatness_with_datum.yaml"

    exit_code = main(["check", str(path)])

    assert exit_code == 1
    expected = (
        f"Checked {path} -- drawing 'dwg-002' ('Cover Plate')\n"
        "Rules run: 20\n"
        "\n"
        "[ERROR] flatness-no-datum-references: Flatness cannot reference datums\n"
        "  flatness feature control frame 'fcf-1' references datum(s) ['A'], "
        "but flatness must not reference any datum\n"
        "  location: feature=feat-surface-1 fcf=fcf-1\n"
        "\n"
        "1 finding(s): 1 error\n"
    )
    assert capsys.readouterr().out == expected


def test_check_json_output_key_set_is_unchanged(capsys: pytest.CaptureFixture[str]) -> None:
    path = _EXAMPLES_DIR / "valid_position.yaml"

    main(["check", str(path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == {"path", "drawing", "rules_run", "findings", "summary"}


# --- Markdown helper units ---------------------------------------------------


def test_escape_markdown_escapes_pipe_for_table_safety() -> None:
    assert _escape_markdown("a|b") == "a\\|b"


def test_escape_markdown_escapes_emphasis_and_code_markers() -> None:
    assert _escape_markdown("*bold* _em_ `code`") == "\\*bold\\* \\_em\\_ \\`code\\`"


def test_escape_markdown_escapes_angle_brackets_and_leading_bracket() -> None:
    assert _escape_markdown("<script>") == "\\<script\\>"
    assert _escape_markdown("[link](evil)") == "\\[link](evil)"


def test_escape_markdown_escapes_backslash_first() -> None:
    assert _escape_markdown("a\\b") == "a\\\\b"


def test_escape_markdown_collapses_newlines_to_spaces() -> None:
    assert _escape_markdown("line1\nline2\r\nline3") == "line1 line2 line3"


def test_markdown_table_row_escapes_each_cell() -> None:
    assert _markdown_table_row("a|b", "c") == "| a\\|b | c |"


def test_finding_locator_pairs_all_present() -> None:
    finding = _finding(feature_id="feat-1", dimension_id="dim-1", fcf_id="fcf-1", datum_label="A")

    assert _finding_locator_pairs(finding) == [
        ("feature", "feat-1"),
        ("dimension", "dim-1"),
        ("fcf", "fcf-1"),
        ("datum", "A"),
    ]


def test_finding_locator_pairs_none_present() -> None:
    finding = _finding()

    assert _finding_locator_pairs(finding) == []


def test_finding_locator_pairs_partial() -> None:
    finding = _finding(feature_id="feat-1", datum_label="A")

    assert _finding_locator_pairs(finding) == [("feature", "feat-1"), ("datum", "A")]


# --- --markdown output -------------------------------------------------------


def test_check_markdown_and_json_together_rejected_by_argparse(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _EXAMPLES_DIR / "valid_position.yaml"

    with pytest.raises(SystemExit) as exc_info:
        main(["check", str(path), "--json", "--markdown"])

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "not allowed with argument" in captured.err


def test_check_markdown_flag_order_also_rejected(capsys: pytest.CaptureFixture[str]) -> None:
    path = _EXAMPLES_DIR / "valid_position.yaml"

    with pytest.raises(SystemExit) as exc_info:
        main(["check", str(path), "--markdown", "--json"])

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "not allowed with argument" in captured.err


def test_check_markdown_no_findings_reports_clean_result(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _EXAMPLES_DIR / "valid_position.yaml"

    exit_code = main(["check", str(path), "--markdown"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert out.startswith("# GD&T Check Report\n")
    assert f"| Source | {_escape_markdown(str(path))} |" in out
    assert "| Drawing ID | dwg-001 |" in out
    assert "| Title | Mounting Bracket |" in out
    assert "| Rules run | 20 |" in out
    assert "## Summary" in out
    assert "| **Total** | 0 |" in out
    assert "## Findings" in out
    assert "No findings were found." in out
    assert "###" not in out  # no per-finding headings when there are no findings


def test_check_markdown_single_finding_includes_rule_and_location(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _EXAMPLES_DIR / "invalid_flatness_with_datum.yaml"

    exit_code = main(["check", str(path), "--markdown"])

    assert exit_code == 1
    out = capsys.readouterr().out
    assert "### ERROR - flatness-no-datum-references" in out
    assert "**Rule:** Flatness cannot reference datums" in out
    assert "flatness must not reference any datum" in out
    assert "**Location:** feature=feat-surface-1, fcf=fcf-1" in out
    assert "| Error | 1 |" in out
    assert "| **Total** | 1 |" in out


def test_check_markdown_multiple_severities_and_deterministic_ordering(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A drawing that trips both an ERROR and a WARNING rule.

    No single bundled example produces two different severities in one
    run, so this assembles a small drawing (flatness-with-datum for the
    ERROR, concentricity for the deprecated-characteristic WARNING) to
    exercise the Summary table's multi-row case and the Findings
    section's ordering guarantee.
    """
    drawing_file = tmp_path / "multi_severity.yaml"
    drawing_file.write_text(
        """
id: dwg-100
title: Multi-Severity Test
default_unit: mm

datums:
  - label: A
    feature_type: plane

features:
  - id: feat-surface-1
    feature_type: surface
    feature_control_frames:
      - id: fcf-1
        characteristic: flatness
        tolerance:
          upper_deviation: 0.05
          lower_deviation: 0.05
        datum_references:
          - datum_label: A
  - id: feat-bore-1
    feature_type: cylinder
    feature_of_size: true
    feature_control_frames:
      - id: fcf-2
        characteristic: concentricity
        tolerance:
          upper_deviation: 0.05
          lower_deviation: 0.05
        datum_references:
          - datum_label: A
""",
        encoding="utf-8",
    )

    exit_code = main(["check", str(drawing_file), "--markdown"])

    assert exit_code == 1
    out = capsys.readouterr().out
    assert "| Error | 1 |" in out
    assert "| Warning | 1 |" in out
    assert "| **Total** | 2 |" in out
    # Findings render in the same (engine registration) order the text/JSON
    # reports already use -- the ERROR (flatness) finding first.
    error_index = out.index("### ERROR - flatness-no-datum-references")
    warning_index = out.index("### WARNING - concentricity-symmetry-deprecated")
    assert error_index < warning_index


def test_check_markdown_absent_locator_fields_omit_location_line(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """This example's finding sets feature/fcf but never dimension/datum."""
    path = _EXAMPLES_DIR / "invalid_concentricity_deprecated.yaml"

    exit_code = main(["check", str(path), "--markdown"])

    assert exit_code == 1
    out = capsys.readouterr().out
    assert "**Location:** feature=feat-bore-1, fcf=fcf-1" in out
    assert "dimension=" not in out
    assert "datum=" not in out


def test_check_markdown_output_escapes_markdown_sensitive_message_text(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _EXAMPLES_DIR / "invalid_flatness_with_datum.yaml"

    main(["check", str(path), "--markdown"])

    out = capsys.readouterr().out
    # the real finding message embeds a Python list repr containing `[` and `'`;
    # `[` must be escaped so it can't be misread as a Markdown link opener
    assert "\\['A']" in out


def test_check_markdown_category_filter_narrows_rules_run(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _EXAMPLES_DIR / "invalid_flatness_with_datum.yaml"

    exit_code = main(["check", str(path), "--markdown", "--category", "tolerance"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "| Rules run | 2 |" in out
    assert "No findings were found." in out


def test_check_markdown_standard_filter_narrows_rules_run(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _EXAMPLES_DIR / "valid_position.yaml"

    exit_code = main(["check", str(path), "--markdown", "--standard", "general"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "| Rules run | 4 |" in out


def test_check_markdown_ingest_error_stays_plain_text_on_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Ingest/parse errors are always plain stderr text, even with --markdown."""
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("id: [unclosed", encoding="utf-8")

    exit_code = main(["check", str(bad_file), "--markdown"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert "error" in captured.err.lower()
    assert "#" not in captured.err  # no Markdown heading leaked into the error path


def test_check_markdown_invalid_filter_stays_plain_text_exit_two(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _EXAMPLES_DIR / "valid_position.yaml"

    exit_code = main(["check", str(path), "--markdown", "--category", "bogus"])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "invalid --category value" in captured.err


def test_print_markdown_report_finding_with_no_locators_omits_location_line(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """No rule in the current catalog produces a fully-locator-less finding,
    so this exercises the branch directly rather than via a real drawing."""
    drawing = Drawing(id="dwg-x", title="Unit Test Drawing")
    finding = _finding()

    _print_markdown_report("drawing.yaml", drawing, [finding], rules_run=1)

    out = capsys.readouterr().out
    assert "**Location:**" not in out
    assert "### WARNING - r1" in out
    assert "**Rule:** Title" in out
    assert "A message." in out


def test_check_markdown_csv_source_end_to_end(capsys: pytest.CaptureFixture[str]) -> None:
    path = _EXAMPLES_DIR / "invalid_datum_reference_undefined.csv"

    exit_code = main(["check", str(path), "--markdown"])

    assert exit_code == 1
    out = capsys.readouterr().out
    assert "| Drawing ID | dwg-007 |" in out
    assert "### ERROR - datum-reference-must-be-defined" in out
    assert "**Location:** feature=feat-hole-1, fcf=fcf-1" in out

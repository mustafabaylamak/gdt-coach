"""Tests for the CLI, including the `check` command."""

import json
from pathlib import Path

import pytest

from gdt_coach import __version__
from gdt_coach.cli import (
    _batch_exit_code,
    _build_adapter_registry,
    _count_by_severity,
    _escape_markdown,
    _expand_paths,
    _ExpansionError,
    _FileCheckError,
    _FileCheckSuccess,
    _finding_locator_pairs,
    _format_finding,
    _format_severity_counts,
    _is_batch_mode,
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


# =============================================================================
# Sprint 16: multi-file / directory ("batch") mode
# =============================================================================


def _copy_example(source_name: str, dest: Path) -> Path:
    """Copy a bundled example file's bytes into `dest` (a full destination path)."""
    dest.write_bytes((_EXAMPLES_DIR / source_name).read_bytes())
    return dest


# --- single-file mode is unaffected: additional backward-compat checks ------


def test_check_single_csv_text_output_is_unchanged(capsys: pytest.CaptureFixture[str]) -> None:
    path = _EXAMPLES_DIR / "invalid_datum_reference_undefined.csv"

    exit_code = main(["check", str(path)])

    assert exit_code == 1
    expected = (
        f"Checked {path} -- drawing 'dwg-007' ('CSV Bracket')\n"
        "Rules run: 20\n"
        "\n"
        "[ERROR] datum-reference-must-be-defined: Referenced datums must be defined\n"
        "  feature control frame 'fcf-1' references undefined datum(s) ['A']; "
        "no datum with that label is defined on this drawing\n"
        "  location: feature=feat-hole-1 fcf=fcf-1\n"
        "\n"
        "1 finding(s): 1 error\n"
    )
    assert capsys.readouterr().out == expected


def test_check_single_file_output_has_no_batch_markers(capsys: pytest.CaptureFixture[str]) -> None:
    """A lone file argument must never produce batch-shaped output."""
    path = _EXAMPLES_DIR / "valid_position.yaml"

    main(["check", str(path)])

    out = capsys.readouterr().out
    assert "Files discovered" not in out
    assert "Input items supplied" not in out
    assert "=" * 10 not in out


def test_check_single_file_json_has_no_batch_shape(capsys: pytest.CaptureFixture[str]) -> None:
    path = _EXAMPLES_DIR / "valid_position.yaml"

    main(["check", str(path), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert "results" not in payload
    assert "summary" in payload  # the existing single-file summary shape, not batch's


def test_check_single_file_markdown_has_no_batch_shape(capsys: pytest.CaptureFixture[str]) -> None:
    path = _EXAMPLES_DIR / "valid_position.yaml"

    main(["check", str(path), "--markdown"])

    out = capsys.readouterr().out
    assert out.startswith("# GD&T Check Report\n")
    assert "# GD&T Batch Check Report" not in out


# --- `_is_batch_mode` --------------------------------------------------------


def test_is_batch_mode_single_file_is_not_batch() -> None:
    assert _is_batch_mode([str(_EXAMPLES_DIR / "valid_position.yaml")]) is False


def test_is_batch_mode_multiple_files_is_batch() -> None:
    assert _is_batch_mode(["a.yaml", "b.yaml"]) is True


def test_is_batch_mode_single_directory_is_batch() -> None:
    assert _is_batch_mode([str(_EXAMPLES_DIR)]) is True


def test_is_batch_mode_single_missing_path_is_not_batch() -> None:
    """A single nonexistent path isn't a directory, so it stays single-file
    mode -- preserving the pre-Sprint-16 missing-file error path exactly."""
    assert _is_batch_mode(["does-not-exist.yaml"]) is False


# --- `_expand_paths` ----------------------------------------------------------


def test_expand_paths_multiple_explicit_files() -> None:
    a = _EXAMPLES_DIR / "valid_position.yaml"
    b = _EXAMPLES_DIR / "invalid_flatness_with_datum.yaml"
    registry = _build_adapter_registry()

    items = _expand_paths([str(a), str(b)], registry)

    assert items == [a, b]


def test_expand_paths_directory_input(tmp_path: Path) -> None:
    _copy_example("valid_position.yaml", tmp_path / "one.yaml")
    _copy_example("invalid_flatness_with_datum.yaml", tmp_path / "two.yaml")
    registry = _build_adapter_registry()

    items = _expand_paths([str(tmp_path)], registry)

    assert items == [tmp_path / "one.yaml", tmp_path / "two.yaml"]


def test_expand_paths_directory_with_yaml_and_csv(tmp_path: Path) -> None:
    _copy_example("valid_position.yaml", tmp_path / "a.yaml")
    _copy_example("invalid_datum_reference_undefined.csv", tmp_path / "b.csv")
    registry = _build_adapter_registry()

    items = _expand_paths([str(tmp_path)], registry)

    assert items == [tmp_path / "a.yaml", tmp_path / "b.csv"]


def test_expand_paths_case_insensitive_extension(tmp_path: Path) -> None:
    _copy_example("valid_position.yaml", tmp_path / "DRAWING.YAML")
    registry = _build_adapter_registry()

    items = _expand_paths([str(tmp_path)], registry)

    assert items == [tmp_path / "DRAWING.YAML"]


def test_expand_paths_mixed_explicit_file_and_directory(tmp_path: Path) -> None:
    explicit = _EXAMPLES_DIR / "valid_position.yaml"
    _copy_example("invalid_flatness_with_datum.yaml", tmp_path / "other.yaml")
    registry = _build_adapter_registry()

    items = _expand_paths([str(explicit), str(tmp_path)], registry)

    assert items == [explicit, tmp_path / "other.yaml"]


def test_expand_paths_deterministic_sorting_within_directory(tmp_path: Path) -> None:
    _copy_example("valid_position.yaml", tmp_path / "z.yaml")
    _copy_example("valid_position.yaml", tmp_path / "a.yaml")
    _copy_example("valid_position.yaml", tmp_path / "m.yaml")
    registry = _build_adapter_registry()

    items = _expand_paths([str(tmp_path)], registry)

    assert items == [tmp_path / "a.yaml", tmp_path / "m.yaml", tmp_path / "z.yaml"]


def test_expand_paths_duplicate_explicit_paths_deduplicated() -> None:
    path = _EXAMPLES_DIR / "valid_position.yaml"
    registry = _build_adapter_registry()

    items = _expand_paths([str(path), str(path)], registry)

    assert items == [path]


def test_expand_paths_same_file_direct_and_via_directory_deduplicated() -> None:
    explicit = _EXAMPLES_DIR / "valid_position.yaml"
    registry = _build_adapter_registry()

    items = _expand_paths([str(explicit), str(_EXAMPLES_DIR)], registry)

    assert items[0] == explicit
    assert items.count(explicit) == 1
    assert len(items) == 7  # the 7 bundled examples, no duplicate entry


def test_expand_paths_nested_directory_ignored(tmp_path: Path) -> None:
    _copy_example("valid_position.yaml", tmp_path / "top.yaml")
    nested = tmp_path / "nested"
    nested.mkdir()
    _copy_example("valid_position.yaml", nested / "inner.yaml")
    registry = _build_adapter_registry()

    items = _expand_paths([str(tmp_path)], registry)

    assert items == [tmp_path / "top.yaml"]


def test_expand_paths_missing_explicit_path_recorded_as_error(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.yaml"
    registry = _build_adapter_registry()

    items = _expand_paths([str(missing)], registry)

    assert len(items) == 1
    error = items[0]
    assert isinstance(error, _ExpansionError)
    assert error.path == str(missing)
    assert error.error_type == "PathNotFoundError"


def test_expand_paths_unsupported_explicit_file_recorded_as_error(tmp_path: Path) -> None:
    unsupported = tmp_path / "drawing.pdf"
    unsupported.write_text("not a real pdf", encoding="utf-8")
    registry = _build_adapter_registry()

    items = _expand_paths([str(unsupported)], registry)

    assert len(items) == 1
    error = items[0]
    assert isinstance(error, _ExpansionError)
    assert error.path == str(unsupported)
    assert error.error_type == "UnsupportedFormatError"


def test_expand_paths_empty_directory_recorded_as_error(tmp_path: Path) -> None:
    registry = _build_adapter_registry()

    items = _expand_paths([str(tmp_path)], registry)

    assert len(items) == 1
    error = items[0]
    assert isinstance(error, _ExpansionError)
    assert error.error_type == "NoSupportedFilesError"
    assert error.path == str(tmp_path)
    assert "no supported input files found in directory" in error.message


def test_expand_paths_directory_with_only_unsupported_files(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_text("junk", encoding="utf-8")
    registry = _build_adapter_registry()

    items = _expand_paths([str(tmp_path)], registry)

    assert len(items) == 1
    assert isinstance(items[0], _ExpansionError)
    assert items[0].error_type == "NoSupportedFilesError"


# --- `_batch_exit_code` ------------------------------------------------------


def test_batch_exit_code_all_success_no_findings() -> None:
    drawing = Drawing(id="d1", title="T1")
    results = [_FileCheckSuccess(path="a.yaml", drawing=drawing, findings=[], rules_run=20)]

    assert _batch_exit_code(results) == 0


def test_batch_exit_code_success_with_findings() -> None:
    drawing = Drawing(id="d1", title="T1")
    results = [
        _FileCheckSuccess(path="a.yaml", drawing=drawing, findings=[_finding()], rules_run=20)
    ]

    assert _batch_exit_code(results) == 1


def test_batch_exit_code_any_error_wins_over_findings() -> None:
    drawing = Drawing(id="d1", title="T1")
    results = [
        _FileCheckSuccess(path="a.yaml", drawing=drawing, findings=[_finding()], rules_run=20),
        _FileCheckError(path="b.yaml", error_type="PathNotFoundError", message="missing"),
    ]

    assert _batch_exit_code(results) == 2


# --- batch text output --------------------------------------------------------


def test_check_batch_directory_all_clean_text(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_example("valid_position.yaml", tmp_path / "a.yaml")

    exit_code = main(["check", str(tmp_path)])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "No findings." in out
    assert "Summary" in out
    assert "Input items supplied: 1" in out
    assert "Files discovered: 1" in out
    assert "Files checked: 1" in out
    assert "Files failed: 0" in out
    assert "Files with findings: 0" in out
    assert "Total findings: 0" in out


def test_check_batch_multiple_files_with_findings_text(
    capsys: pytest.CaptureFixture[str],
) -> None:
    a = _EXAMPLES_DIR / "valid_position.yaml"
    b = _EXAMPLES_DIR / "invalid_flatness_with_datum.yaml"

    exit_code = main(["check", str(a), str(b)])

    assert exit_code == 1
    out = capsys.readouterr().out
    assert "flatness-no-datum-references" in out
    assert "Files with findings: 1" in out
    assert "Total findings: 1" in out
    assert "By severity: 1 error" in out


def test_check_batch_partial_failure_text(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    good = _EXAMPLES_DIR / "valid_position.yaml"
    missing = tmp_path / "does-not-exist.yaml"

    exit_code = main(["check", str(good), str(missing)])

    assert exit_code == 2
    out = capsys.readouterr().out
    assert f"Could not check {str(missing)!r}" in out
    assert "PathNotFoundError" in out
    assert "Files checked: 1" in out
    assert "Files failed: 1" in out
    assert "No findings." in out  # the good file's own report still appears


def test_check_batch_continues_after_one_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "missing.yaml"
    good_a = _EXAMPLES_DIR / "valid_position.yaml"
    good_b = _EXAMPLES_DIR / "invalid_flatness_with_datum.yaml"

    exit_code = main(["check", str(missing), str(good_a), str(good_b)])

    assert exit_code == 2
    out = capsys.readouterr().out
    assert "PathNotFoundError" in out
    assert "dwg-001" in out  # good_a still checked despite missing coming first
    assert "flatness-no-datum-references" in out  # good_b still checked too
    assert "Files checked: 2" in out
    assert "Files failed: 1" in out


def test_check_batch_text_reports_rules_run_per_file(
    capsys: pytest.CaptureFixture[str],
) -> None:
    a = _EXAMPLES_DIR / "valid_position.yaml"
    b = _EXAMPLES_DIR / "invalid_flatness_with_datum.yaml"

    main(["check", str(a), str(b)])

    out = capsys.readouterr().out
    assert out.count("Rules run: 20") == 2


def test_check_batch_text_full_representative_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Full-shape check for batch text mode: the same file supplied twice
    dedups to one checked file, but still triggers batch mode (2 raw
    arguments) -- giving a short, fully deterministic report to compare
    byte-for-byte."""
    path = _EXAMPLES_DIR / "valid_position.yaml"

    exit_code = main(["check", str(path), str(path)])

    assert exit_code == 0
    separator = "=" * 70
    expected = (
        f"{separator}\n"
        f"Checked {path} -- drawing 'dwg-001' ('Mounting Bracket')\n"
        "Rules run: 20\n"
        "\n"
        "No findings.\n"
        "\n"
        f"{separator}\n"
        "Summary\n"
        "Input items supplied: 2\n"
        "Files discovered: 1\n"
        "Files checked: 1\n"
        "Files failed: 0\n"
        "Files with findings: 0\n"
        "Total findings: 0\n"
    )
    assert capsys.readouterr().out == expected


# --- batch JSON output ---------------------------------------------------------


def test_check_batch_json_all_success_schema(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_example("valid_position.yaml", tmp_path / "a.yaml")

    exit_code = main(["check", str(tmp_path), "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == {"results", "summary"}
    assert len(payload["results"]) == 1
    result = payload["results"][0]
    assert set(result) == {"path", "status", "drawing", "rules_run", "findings"}
    assert result["status"] == "checked"
    assert result["drawing"] == {"id": "dwg-001", "title": "Mounting Bracket"}
    assert result["rules_run"] == 20
    assert result["findings"] == []
    assert payload["summary"] == {
        "inputs_supplied": 1,
        "files_discovered": 1,
        "files_checked": 1,
        "files_failed": 0,
        "files_with_findings": 0,
        "total_findings": 0,
        "severity_counts": {},
    }


def test_check_batch_json_partial_failure_remains_parseable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    good = _EXAMPLES_DIR / "valid_position.yaml"
    missing = tmp_path / "does-not-exist.yaml"

    exit_code = main(["check", str(good), str(missing), "--json"])

    assert exit_code == 2
    payload = json.loads(capsys.readouterr().out)  # must not raise
    statuses = {result["path"]: result["status"] for result in payload["results"]}
    assert statuses[str(good)] == "checked"
    assert statuses[str(missing)] == "error"
    assert payload["summary"]["files_failed"] == 1
    assert payload["summary"]["files_checked"] == 1


def test_check_batch_json_error_entry_schema(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "does-not-exist.yaml"
    good = _EXAMPLES_DIR / "valid_position.yaml"

    main(["check", str(good), str(missing), "--json"])

    payload = json.loads(capsys.readouterr().out)
    error_result = next(result for result in payload["results"] if result["status"] == "error")
    assert set(error_result) == {"path", "status", "error"}
    assert set(error_result["error"]) == {"type", "message"}
    assert error_result["error"]["type"] == "PathNotFoundError"


def test_check_batch_json_result_ordering_matches_expansion(
    capsys: pytest.CaptureFixture[str],
) -> None:
    a = _EXAMPLES_DIR / "valid_position.yaml"
    b = _EXAMPLES_DIR / "invalid_flatness_with_datum.yaml"

    main(["check", str(b), str(a), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert [result["path"] for result in payload["results"]] == [str(b), str(a)]


def test_check_batch_json_severity_aggregation(capsys: pytest.CaptureFixture[str]) -> None:
    a = _EXAMPLES_DIR / "invalid_flatness_with_datum.yaml"  # 1 error
    b = _EXAMPLES_DIR / "invalid_concentricity_deprecated.yaml"  # 1 warning
    c = _EXAMPLES_DIR / "invalid_projected_zone.yaml"  # 1 error

    main(["check", str(a), str(b), str(c), "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["severity_counts"] == {"error": 2, "warning": 1}
    assert payload["summary"]["total_findings"] == 3


# --- batch Markdown output ------------------------------------------------------


def test_check_batch_markdown_all_success(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _copy_example("valid_position.yaml", tmp_path / "a.yaml")

    exit_code = main(["check", str(tmp_path), "--markdown"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert out.startswith("# GD&T Batch Check Report\n")
    assert "## Summary" in out
    assert "| Files checked | 1 |" in out
    assert "## Results" in out
    assert "### `" in out
    assert "No findings were found." in out


def test_check_batch_markdown_partial_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    good = _EXAMPLES_DIR / "valid_position.yaml"
    missing = tmp_path / "does-not-exist.yaml"

    exit_code = main(["check", str(good), str(missing), "--markdown"])

    assert exit_code == 2
    out = capsys.readouterr().out
    assert "**Error (PathNotFoundError):**" in out
    assert "| Files failed | 1 |" in out
    assert "| Files checked | 1 |" in out


def test_check_batch_markdown_finding_headings_nested_under_result(
    capsys: pytest.CaptureFixture[str],
) -> None:
    a = _EXAMPLES_DIR / "valid_position.yaml"
    b = _EXAMPLES_DIR / "invalid_flatness_with_datum.yaml"

    main(["check", str(a), str(b), "--markdown"])

    lines = capsys.readouterr().out.splitlines()
    assert "#### ERROR - flatness-no-datum-references" in lines
    assert "### ERROR - flatness-no-datum-references" not in lines


def test_check_batch_markdown_severity_summary_table(capsys: pytest.CaptureFixture[str]) -> None:
    a = _EXAMPLES_DIR / "invalid_flatness_with_datum.yaml"
    b = _EXAMPLES_DIR / "invalid_concentricity_deprecated.yaml"

    main(["check", str(a), str(b), "--markdown"])

    out = capsys.readouterr().out
    assert "| Error | 1 |" in out
    assert "| Warning | 1 |" in out


def test_check_batch_markdown_full_representative_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    path = _EXAMPLES_DIR / "valid_position.yaml"

    exit_code = main(["check", str(path), str(path), "--markdown"])

    assert exit_code == 0
    escaped_path = _escape_markdown(str(path))
    expected = (
        "# GD&T Batch Check Report\n"
        "\n"
        "## Summary\n"
        "\n"
        "| Field | Value |\n"
        "|---|---|\n"
        "| Input items supplied | 2 |\n"
        "| Files discovered | 1 |\n"
        "| Files checked | 1 |\n"
        "| Files failed | 0 |\n"
        "| Files with findings | 0 |\n"
        "| Total findings | 0 |\n"
        "\n"
        "## Results\n"
        "\n"
        f"### `{escaped_path}`\n"
        "\n"
        "| Field | Value |\n"
        "|---|---|\n"
        f"| Source | {escaped_path} |\n"
        "| Drawing ID | dwg-001 |\n"
        "| Title | Mounting Bracket |\n"
        "| Rules run | 20 |\n"
        "\n"
        "| Severity | Count |\n"
        "|---|---:|\n"
        "| **Total** | 0 |\n"
        "\n"
        "No findings were found.\n"
        "\n"
    )
    assert capsys.readouterr().out == expected


# --- filters apply across every file in a batch ---------------------------------


def test_check_batch_category_filter_applies_to_every_file(
    capsys: pytest.CaptureFixture[str],
) -> None:
    a = _EXAMPLES_DIR / "valid_position.yaml"
    b = _EXAMPLES_DIR / "invalid_flatness_with_datum.yaml"

    exit_code = main(["check", str(a), str(b), "--category", "tolerance", "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    for result in payload["results"]:
        assert result["rules_run"] == 2  # TOLERANCE category: same as single-file tests
        assert result["findings"] == []


def test_check_batch_standard_filter_applies_to_every_file(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # invalid_flatness_with_datum.yaml's only violation is standard
    # asme_y14.5_2018, so filtering to "general" silences it for both files --
    # same behavior `test_check_standard_filter_narrows_rules_run` already
    # established for a single file.
    a = _EXAMPLES_DIR / "valid_position.yaml"
    b = _EXAMPLES_DIR / "invalid_flatness_with_datum.yaml"

    exit_code = main(["check", str(a), str(b), "--standard", "general", "--json"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    for result in payload["results"]:
        assert result["rules_run"] == 4
        assert result["findings"] == []


def test_check_batch_invalid_filter_no_partial_checking(
    capsys: pytest.CaptureFixture[str],
) -> None:
    a = _EXAMPLES_DIR / "valid_position.yaml"
    b = _EXAMPLES_DIR / "invalid_flatness_with_datum.yaml"

    exit_code = main(["check", str(a), str(b), "--category", "bogus"])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert captured.out == ""  # no partial report -- nothing was checked
    assert "invalid --category value" in captured.err


# --- exit codes ----------------------------------------------------------------


def test_check_batch_exit_code_all_clean(tmp_path: Path) -> None:
    _copy_example("valid_position.yaml", tmp_path / "a.yaml")

    exit_code = main(["check", str(tmp_path)])

    assert exit_code == 0


def test_check_batch_exit_code_findings_only(capsys: pytest.CaptureFixture[str]) -> None:
    a = _EXAMPLES_DIR / "invalid_concentricity_deprecated.yaml"  # WARNING only, no load errors

    exit_code = main(["check", str(a), str(a), "--json"])  # dedups to one, still batch mode

    assert exit_code == 1


def test_check_batch_exit_code_any_load_error(tmp_path: Path) -> None:
    good = _EXAMPLES_DIR / "valid_position.yaml"
    missing = tmp_path / "does-not-exist.yaml"

    exit_code = main(["check", str(good), str(missing)])

    assert exit_code == 2


def test_check_batch_exit_code_directory_with_only_unsupported_files_is_two(
    tmp_path: Path,
) -> None:
    (tmp_path / "notes.txt").write_text("junk", encoding="utf-8")

    exit_code = main(["check", str(tmp_path)])

    assert exit_code == 2


def test_check_batch_malformed_file_discovered_via_directory_is_load_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A file that passes expansion (exists, supported extension) but fails
    to parse is a load-time error, not an expansion-time one -- exercised
    here since no bundled example is itself malformed."""
    _copy_example("valid_position.yaml", tmp_path / "good.yaml")
    (tmp_path / "bad.yaml").write_text("id: [unclosed", encoding="utf-8")

    exit_code = main(["check", str(tmp_path), "--json"])

    assert exit_code == 2
    payload = json.loads(capsys.readouterr().out)
    bad_result = next(r for r in payload["results"] if "bad.yaml" in r["path"])
    assert bad_result["status"] == "error"
    assert bad_result["error"]["type"] == "YamlParseError"
    good_result = next(r for r in payload["results"] if "good.yaml" in r["path"])
    assert good_result["status"] == "checked"

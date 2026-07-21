"""Tests for the example files in `examples/` (YAML and, since Sprint 14, CSV).

These exercise the full pipeline (input file -> Drawing -> RuleEngine)
end to end, without changing RuleEngine or wiring up a CLI. A fresh
RuleRegistry is used (rather than the shared default_registry) so this
test doesn't depend on whether other test modules have already
imported `gdt_coach.rules.checks`. `ALL_RULE_CLASSES` is the single
source of truth for "every concrete rule" -- see
`gdt_coach.rules.checks` and `tests/rules/checks/test_registration.py`.
"""

from pathlib import Path

from gdt_coach.ingest import load_drawing_from_csv_file, load_drawing_from_yaml_file
from gdt_coach.rules.checks import ALL_RULE_CLASSES
from gdt_coach.rules.engine import RuleEngine
from gdt_coach.rules.registry import RuleRegistry

_EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"


def _engine_with_all_rules() -> RuleEngine:
    registry = RuleRegistry()
    for rule_cls in ALL_RULE_CLASSES:
        registry.register(rule_cls)
    return RuleEngine(registry=registry)


def test_examples_directory_has_the_required_files() -> None:
    assert (_EXAMPLES_DIR / "valid_position.yaml").is_file()
    assert (_EXAMPLES_DIR / "invalid_flatness_with_datum.yaml").is_file()
    assert (_EXAMPLES_DIR / "invalid_projected_zone.yaml").is_file()
    assert (_EXAMPLES_DIR / "invalid_concentricity_deprecated.yaml").is_file()
    assert (_EXAMPLES_DIR / "invalid_position_without_feature_of_size.yaml").is_file()
    assert (_EXAMPLES_DIR / "invalid_position_related_dimension_wrong_role.yaml").is_file()
    assert (_EXAMPLES_DIR / "invalid_datum_reference_undefined.csv").is_file()


def test_valid_position_loads_and_passes_all_rules() -> None:
    drawing = load_drawing_from_yaml_file(_EXAMPLES_DIR / "valid_position.yaml")

    findings = _engine_with_all_rules().run(drawing)

    assert findings == []


def test_invalid_flatness_with_datum_loads_and_is_flagged() -> None:
    drawing = load_drawing_from_yaml_file(_EXAMPLES_DIR / "invalid_flatness_with_datum.yaml")

    findings = _engine_with_all_rules().run(drawing)

    assert [finding.rule_id for finding in findings] == ["flatness-no-datum-references"]


def test_invalid_projected_zone_loads_and_is_flagged() -> None:
    drawing = load_drawing_from_yaml_file(_EXAMPLES_DIR / "invalid_projected_zone.yaml")

    findings = _engine_with_all_rules().run(drawing)

    assert [finding.rule_id for finding in findings] == ["projected-zone-requires-position"]


def test_invalid_concentricity_deprecated_loads_and_is_flagged() -> None:
    drawing = load_drawing_from_yaml_file(_EXAMPLES_DIR / "invalid_concentricity_deprecated.yaml")

    findings = _engine_with_all_rules().run(drawing)

    assert [finding.rule_id for finding in findings] == ["concentricity-symmetry-deprecated"]
    assert findings[0].severity.value == "warning"


def test_invalid_position_without_feature_of_size_loads_and_is_flagged() -> None:
    drawing = load_drawing_from_yaml_file(
        _EXAMPLES_DIR / "invalid_position_without_feature_of_size.yaml"
    )

    findings = _engine_with_all_rules().run(drawing)

    assert [finding.rule_id for finding in findings] == ["position-requires-feature-of-size"]


def test_invalid_position_related_dimension_wrong_role_loads_and_is_flagged() -> None:
    drawing = load_drawing_from_yaml_file(
        _EXAMPLES_DIR / "invalid_position_related_dimension_wrong_role.yaml"
    )

    findings = _engine_with_all_rules().run(drawing)

    assert [finding.rule_id for finding in findings] == [
        "position-related-dimension-must-be-location"
    ]


def test_invalid_datum_reference_undefined_csv_loads_and_is_flagged() -> None:
    drawing = load_drawing_from_csv_file(_EXAMPLES_DIR / "invalid_datum_reference_undefined.csv")

    findings = _engine_with_all_rules().run(drawing)

    assert [finding.rule_id for finding in findings] == ["datum-reference-must-be-defined"]

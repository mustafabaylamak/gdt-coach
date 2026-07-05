"""Tests for the example YAML files in `examples/`.

These exercise the full pipeline (YAML -> Drawing -> RuleEngine) end to
end, without changing RuleEngine or wiring up a CLI. A fresh
RuleRegistry is used (rather than the shared default_registry) so this
test doesn't depend on whether other test modules have already
imported `gdt_coach.rules.checks`.
"""

from pathlib import Path

from gdt_coach.ingest import load_drawing_from_yaml_file
from gdt_coach.rules.checks import (
    DuplicateDatumReferencesRule,
    FlatnessNoDatumReferencesRule,
    PositionRequiresDatumReferenceRule,
    ProjectedZoneRequiresPositionRule,
    StraightnessNoDatumReferencesRule,
)
from gdt_coach.rules.engine import RuleEngine
from gdt_coach.rules.registry import RuleRegistry

_EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"


def _engine_with_all_rules() -> RuleEngine:
    registry = RuleRegistry()
    for rule_cls in (
        FlatnessNoDatumReferencesRule,
        StraightnessNoDatumReferencesRule,
        DuplicateDatumReferencesRule,
        PositionRequiresDatumReferenceRule,
        ProjectedZoneRequiresPositionRule,
    ):
        registry.register(rule_cls)
    return RuleEngine(registry=registry)


def test_examples_directory_has_the_required_files() -> None:
    assert (_EXAMPLES_DIR / "valid_position.yaml").is_file()
    assert (_EXAMPLES_DIR / "invalid_flatness_with_datum.yaml").is_file()
    assert (_EXAMPLES_DIR / "invalid_projected_zone.yaml").is_file()


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

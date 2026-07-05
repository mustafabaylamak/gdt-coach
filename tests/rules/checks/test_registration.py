"""Integration test: the five Sprint 3 rules register cleanly together.

Rule modules register themselves against `default_registry` as an
import side effect, so relying on import order/caching to test
registration is fragile. Instead this re-registers the already-imported
classes into the (test-isolated) `default_registry` directly, which
exercises the real invariants that matter: unique ids and complete
metadata across all five rules.
"""

from gdt_coach.models import Drawing, Feature, FeatureType
from gdt_coach.models.enums import GeometricCharacteristic
from gdt_coach.rules.checks import (
    DuplicateDatumReferencesRule,
    FlatnessNoDatumReferencesRule,
    PositionRequiresDatumReferenceRule,
    ProjectedZoneRequiresPositionRule,
    StraightnessNoDatumReferencesRule,
)
from gdt_coach.rules.engine import RuleEngine
from gdt_coach.rules.registry import RuleRegistry, default_registry

from .conftest import make_fcf, make_tolerance

_RULE_CLASSES = [
    FlatnessNoDatumReferencesRule,
    StraightnessNoDatumReferencesRule,
    DuplicateDatumReferencesRule,
    PositionRequiresDatumReferenceRule,
    ProjectedZoneRequiresPositionRule,
]


def test_all_five_rules_register_without_conflict() -> None:
    for rule_cls in _RULE_CLASSES:
        default_registry.register(rule_cls)

    assert len(default_registry) == 5
    assert {rule.id for rule in default_registry.all()} == {
        "flatness-no-datum-references",
        "straightness-no-datum-references",
        "fcf-duplicate-datum-references",
        "position-requires-datum-reference",
        "projected-zone-requires-position",
    }


def test_all_five_rules_have_non_empty_explanations() -> None:
    for rule_cls in _RULE_CLASSES:
        default_registry.register(rule_cls)

    for rule in default_registry.all():
        assert rule.explanation
        assert rule.title


def test_rule_engine_runs_all_five_rules_end_to_end() -> None:
    """RuleEngine (unchanged from Sprint 2) drives the five Sprint 3 rules."""
    registry = RuleRegistry()
    for rule_cls in _RULE_CLASSES:
        registry.register(rule_cls)

    bad_flatness = make_fcf(
        fcf_id="fcf-flatness",
        characteristic=GeometricCharacteristic.FLATNESS,
        datum_labels=["A"],
    )
    bad_position = make_fcf(
        fcf_id="fcf-position",
        characteristic=GeometricCharacteristic.POSITION,
        datum_labels=[],
    )
    bad_projected = make_fcf(
        fcf_id="fcf-projected",
        characteristic=GeometricCharacteristic.PERPENDICULARITY,
        datum_labels=["A"],
        tolerance=make_tolerance(projected_zone_height=5.0),
    )
    good_position = make_fcf(
        fcf_id="fcf-good",
        characteristic=GeometricCharacteristic.POSITION,
        datum_labels=["A", "B"],
    )
    feature = Feature(
        id="feat-1",
        feature_type=FeatureType.HOLE,
        feature_control_frames=[bad_flatness, bad_position, bad_projected, good_position],
    )
    drawing = Drawing(id="dwg-1", title="Integration drawing", features=[feature])

    findings = RuleEngine(registry=registry).run(drawing)

    assert {finding.rule_id for finding in findings} == {
        "flatness-no-datum-references",
        "position-requires-datum-reference",
        "projected-zone-requires-position",
    }
    assert len(findings) == 3

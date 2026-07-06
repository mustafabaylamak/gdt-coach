"""Integration test: the rules in ALL_RULE_CLASSES register cleanly together.

Rule modules register themselves against `default_registry` as an
import side effect, so relying on import order/caching to test
registration is fragile. Instead this re-registers the already-imported
classes into the (test-isolated) `default_registry` directly, which
exercises the real invariants that matter: unique ids and complete
metadata across every rule.

`ALL_RULE_CLASSES` (from `gdt_coach.rules.checks`) is the single source
of truth for "every concrete rule" -- this test (and the CLI) both
import it rather than each keeping their own list. Assertions below are
derived from `ALL_RULE_CLASSES` itself (its length, its rule ids)
rather than a hardcoded count, so this test doesn't need editing every
time a rule is added or removed.
"""

from gdt_coach.models import Drawing, Feature, FeatureType
from gdt_coach.models.enums import GeometricCharacteristic
from gdt_coach.rules.checks import ALL_RULE_CLASSES
from gdt_coach.rules.engine import RuleEngine
from gdt_coach.rules.registry import RuleRegistry, default_registry

from .conftest import make_fcf, make_tolerance


def _expected_rule_ids() -> set[str]:
    return {rule_cls().id for rule_cls in ALL_RULE_CLASSES}


def test_all_rules_register_without_conflict() -> None:
    for rule_cls in ALL_RULE_CLASSES:
        default_registry.register(rule_cls)

    assert len(default_registry) == len(ALL_RULE_CLASSES)
    assert {rule.id for rule in default_registry.all()} == _expected_rule_ids()


def test_all_rules_have_non_empty_explanations() -> None:
    for rule_cls in ALL_RULE_CLASSES:
        default_registry.register(rule_cls)

    for rule in default_registry.all():
        assert rule.explanation
        assert rule.title


def test_rule_engine_runs_all_rules_end_to_end() -> None:
    """RuleEngine (unchanged since Sprint 2) drives every registered rule."""
    registry = RuleRegistry()
    for rule_cls in ALL_RULE_CLASSES:
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

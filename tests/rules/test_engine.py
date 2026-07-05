"""Tests for the RuleEngine."""

from gdt_coach.models import Drawing
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.engine import RuleEngine
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.registry import RuleRegistry, default_registry
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard

from .conftest import RuleFactory


def _finding(rule_id: str) -> Finding:
    return Finding(
        rule_id=rule_id,
        title="t",
        severity=Severity.WARNING,
        standard=Standard.GENERAL,
        category=RuleCategory.GENERAL,
        message="m",
    )


def test_engine_runs_all_registered_rules(
    empty_drawing: Drawing, registry: RuleRegistry, rule_class_factory: RuleFactory
) -> None:
    registry.register(rule_class_factory(rule_id="r1", check_fn=lambda d: [_finding("r1")]))
    registry.register(rule_class_factory(rule_id="r2", check_fn=lambda d: [_finding("r2")]))
    engine = RuleEngine(registry=registry)

    findings = engine.run(empty_drawing)

    assert {f.rule_id for f in findings} == {"r1", "r2"}


def test_engine_collects_multiple_findings_from_one_rule(
    empty_drawing: Drawing, registry: RuleRegistry, rule_class_factory: RuleFactory
) -> None:
    registry.register(
        rule_class_factory(rule_id="r1", check_fn=lambda d: [_finding("r1"), _finding("r1")])
    )
    engine = RuleEngine(registry=registry)

    findings = engine.run(empty_drawing)

    assert len(findings) == 2


def test_engine_filters_by_category(
    empty_drawing: Drawing, registry: RuleRegistry, rule_class_factory: RuleFactory
) -> None:
    registry.register(
        rule_class_factory(
            rule_id="r1", category=RuleCategory.DATUM, check_fn=lambda d: [_finding("r1")]
        )
    )
    registry.register(
        rule_class_factory(
            rule_id="r2", category=RuleCategory.DIMENSION, check_fn=lambda d: [_finding("r2")]
        )
    )
    engine = RuleEngine(registry=registry)

    findings = engine.run(empty_drawing, categories={RuleCategory.DATUM})

    assert {f.rule_id for f in findings} == {"r1"}


def test_engine_filters_by_standard(
    empty_drawing: Drawing, registry: RuleRegistry, rule_class_factory: RuleFactory
) -> None:
    registry.register(
        rule_class_factory(
            rule_id="r1", standard=Standard.ASME_Y14_5_2018, check_fn=lambda d: [_finding("r1")]
        )
    )
    registry.register(
        rule_class_factory(
            rule_id="r2", standard=Standard.ISO_1101_2017, check_fn=lambda d: [_finding("r2")]
        )
    )
    engine = RuleEngine(registry=registry)

    findings = engine.run(empty_drawing, standard=Standard.ASME_Y14_5_2018)

    assert {f.rule_id for f in findings} == {"r1"}


def test_engine_combines_category_and_standard_filters(
    empty_drawing: Drawing, registry: RuleRegistry, rule_class_factory: RuleFactory
) -> None:
    registry.register(
        rule_class_factory(
            rule_id="r1",
            category=RuleCategory.DATUM,
            standard=Standard.ASME_Y14_5_2018,
            check_fn=lambda d: [_finding("r1")],
        )
    )
    registry.register(
        rule_class_factory(
            rule_id="r2",
            category=RuleCategory.DATUM,
            standard=Standard.ISO_1101_2017,
            check_fn=lambda d: [_finding("r2")],
        )
    )
    engine = RuleEngine(registry=registry)

    findings = engine.run(
        empty_drawing, categories={RuleCategory.DATUM}, standard=Standard.ASME_Y14_5_2018
    )

    assert {f.rule_id for f in findings} == {"r1"}


def test_engine_with_no_registered_rules_returns_empty(
    empty_drawing: Drawing, registry: RuleRegistry
) -> None:
    engine = RuleEngine(registry=registry)

    assert engine.run(empty_drawing) == []


def test_engine_defaults_to_the_shared_default_registry(empty_drawing: Drawing) -> None:
    engine = RuleEngine()

    assert engine._registry is default_registry

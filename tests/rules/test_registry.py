"""Tests for the RuleRegistry."""

import pytest

from gdt_coach.models import Drawing
from gdt_coach.rules.base import Rule
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.exceptions import DuplicateRuleIdError, InvalidRuleError
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.registry import RuleRegistry
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard

from .conftest import RuleFactory


def test_register_and_get(registry: RuleRegistry, rule_class_factory: RuleFactory) -> None:
    registry.register(rule_class_factory(rule_id="r1"))

    rule = registry.get("r1")

    assert rule.id == "r1"
    assert len(registry) == 1
    assert "r1" in registry


def test_register_returns_the_class_unchanged(
    registry: RuleRegistry, rule_class_factory: RuleFactory
) -> None:
    rule_cls = rule_class_factory(rule_id="r1")

    result = registry.register(rule_cls)

    assert result is rule_cls


def test_register_works_as_a_decorator(registry: RuleRegistry) -> None:
    @registry.register
    class ExampleRule(Rule):
        id = "example-rule"
        title = "Example rule"
        severity = Severity.INFO
        standard = Standard.GENERAL
        category = RuleCategory.GENERAL
        explanation = "Registered via the decorator form."

        def check(self, drawing: Drawing) -> list[Finding]:
            return []

    assert "example-rule" in registry
    assert registry.get("example-rule").title == "Example rule"


def test_duplicate_id_raises(registry: RuleRegistry, rule_class_factory: RuleFactory) -> None:
    registry.register(rule_class_factory(rule_id="dup"))

    with pytest.raises(DuplicateRuleIdError):
        registry.register(rule_class_factory(rule_id="dup"))


def test_get_unknown_id_raises_key_error(registry: RuleRegistry) -> None:
    with pytest.raises(KeyError):
        registry.get("does-not-exist")


@pytest.mark.parametrize("missing_field", ["id", "title", "severity", "standard", "category"])
def test_missing_metadata_raises(registry: RuleRegistry, missing_field: str) -> None:
    metadata: dict[str, object] = {
        "id": "incomplete",
        "title": "Incomplete",
        "severity": Severity.WARNING,
        "standard": Standard.GENERAL,
        "category": RuleCategory.GENERAL,
        "explanation": "Missing a required field.",
        "check": lambda self, drawing: [],
    }
    del metadata[missing_field]
    incomplete_cls = type("IncompleteRule", (Rule,), metadata)

    with pytest.raises(InvalidRuleError):
        registry.register(incomplete_cls)


def test_unregister_removes_a_rule(registry: RuleRegistry, rule_class_factory: RuleFactory) -> None:
    registry.register(rule_class_factory(rule_id="r1"))

    registry.unregister("r1")

    assert "r1" not in registry
    assert len(registry) == 0


def test_unregister_unknown_id_is_a_no_op(registry: RuleRegistry) -> None:
    registry.unregister("does-not-exist")

    assert len(registry) == 0


def test_clear_removes_all_rules(registry: RuleRegistry, rule_class_factory: RuleFactory) -> None:
    registry.register(rule_class_factory(rule_id="r1"))
    registry.register(rule_class_factory(rule_id="r2"))

    registry.clear()

    assert len(registry) == 0


def test_all_returns_independent_list(
    registry: RuleRegistry, rule_class_factory: RuleFactory
) -> None:
    registry.register(rule_class_factory(rule_id="r1"))

    rules = registry.all()
    rules.clear()

    assert len(registry) == 1


def test_filter_by_category(registry: RuleRegistry, rule_class_factory: RuleFactory) -> None:
    registry.register(rule_class_factory(rule_id="r1", category=RuleCategory.DATUM))
    registry.register(rule_class_factory(rule_id="r2", category=RuleCategory.DIMENSION))

    matched = registry.filter(category=RuleCategory.DATUM)

    assert [rule.id for rule in matched] == ["r1"]


def test_filter_by_standard(registry: RuleRegistry, rule_class_factory: RuleFactory) -> None:
    registry.register(rule_class_factory(rule_id="r1", standard=Standard.ASME_Y14_5_2018))
    registry.register(rule_class_factory(rule_id="r2", standard=Standard.ISO_1101_2017))

    matched = registry.filter(standard=Standard.ASME_Y14_5_2018)

    assert [rule.id for rule in matched] == ["r1"]


def test_filter_by_severity(registry: RuleRegistry, rule_class_factory: RuleFactory) -> None:
    registry.register(rule_class_factory(rule_id="r1", severity=Severity.CRITICAL))
    registry.register(rule_class_factory(rule_id="r2", severity=Severity.INFO))

    matched = registry.filter(severity=Severity.CRITICAL)

    assert [rule.id for rule in matched] == ["r1"]


def test_filter_with_no_criteria_returns_all(
    registry: RuleRegistry, rule_class_factory: RuleFactory
) -> None:
    registry.register(rule_class_factory(rule_id="r1"))
    registry.register(rule_class_factory(rule_id="r2"))

    matched = registry.filter()

    assert {rule.id for rule in matched} == {"r1", "r2"}

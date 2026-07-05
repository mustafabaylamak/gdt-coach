"""Shared fixtures for the rule engine test suite."""

from __future__ import annotations

from collections.abc import Callable, Generator

import pytest

from gdt_coach.models import Drawing
from gdt_coach.rules.base import Rule
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.registry import RuleRegistry, default_registry
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard

RuleFactory = Callable[..., type[Rule]]


@pytest.fixture(autouse=True)
def _isolate_default_registry() -> Generator[None, None, None]:
    """Prevent tests from leaking rules into the shared default registry."""
    default_registry.clear()
    yield
    default_registry.clear()


@pytest.fixture
def empty_drawing() -> Drawing:
    return Drawing(id="dwg-1", title="Test drawing")


@pytest.fixture
def registry() -> RuleRegistry:
    return RuleRegistry()


@pytest.fixture
def rule_class_factory() -> RuleFactory:
    """Build throwaway concrete Rule subclasses without repeating boilerplate."""

    def _make(
        *,
        rule_id: str = "test-rule",
        title: str = "Test rule",
        severity: Severity = Severity.WARNING,
        standard: Standard = Standard.GENERAL,
        category: RuleCategory = RuleCategory.GENERAL,
        explanation: str = "A rule used only in tests.",
        check_fn: Callable[[Drawing], list[Finding]] | None = None,
    ) -> type[Rule]:
        def check(self: Rule, drawing: Drawing) -> list[Finding]:
            if check_fn is not None:
                return check_fn(drawing)
            return []

        return type(
            "DummyRule",
            (Rule,),
            {
                "id": rule_id,
                "title": title,
                "severity": severity,
                "standard": standard,
                "category": category,
                "explanation": explanation,
                "check": check,
            },
        )

    return _make

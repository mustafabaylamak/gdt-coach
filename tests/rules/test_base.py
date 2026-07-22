"""Tests for the Rule abstract base class."""

import pytest

from gdt_coach.models import Drawing
from gdt_coach.rules.audit_status import RuleAuditStatus
from gdt_coach.rules.base import Rule
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard


def test_rule_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        Rule()  # type: ignore[abstract]


def test_concrete_rule_exposes_its_metadata() -> None:
    class ExampleRule(Rule):
        id = "example"
        title = "Example rule"
        severity = Severity.ERROR
        standard = Standard.ASME_Y14_5_2018
        category = RuleCategory.GENERAL
        explanation = "An example rule used only in tests."

        def check(self, drawing: Drawing) -> list[Finding]:
            return []

    rule = ExampleRule()

    assert rule.id == "example"
    assert rule.title == "Example rule"
    assert rule.severity == Severity.ERROR
    assert rule.standard == Standard.ASME_Y14_5_2018
    assert rule.category == RuleCategory.GENERAL
    assert rule.explanation


def test_concrete_rule_check_runs_against_a_drawing(empty_drawing: Drawing) -> None:
    class AlwaysFindsRule(Rule):
        id = "always-finds"
        title = "Always finds"
        severity = Severity.INFO
        standard = Standard.GENERAL
        category = RuleCategory.GENERAL
        explanation = "Always reports one finding, for testing."

        def check(self, drawing: Drawing) -> list[Finding]:
            return [
                Finding(
                    rule_id=self.id,
                    title=self.title,
                    severity=self.severity,
                    standard=self.standard,
                    category=self.category,
                    message=f"drawing {drawing.id} was checked",
                )
            ]

    findings = AlwaysFindsRule().check(empty_drawing)

    assert len(findings) == 1
    assert findings[0].rule_id == "always-finds"
    assert empty_drawing.id in findings[0].message


def test_rule_base_class_audit_status_default_is_not_audited() -> None:
    assert Rule.audit_status == RuleAuditStatus.NOT_AUDITED
    assert Rule.standard_question_note is None


def test_concrete_rule_not_declaring_audit_status_stays_not_audited() -> None:
    """A rule that says nothing about its audit status must read as
    NOT_AUDITED -- it must never silently inherit an audited-sounding
    value just by existing."""

    class UndeclaredAuditStatusRule(Rule):
        id = "undeclared-audit-status"
        title = "Undeclared audit status"
        severity = Severity.INFO
        standard = Standard.GENERAL
        category = RuleCategory.GENERAL
        explanation = "Deliberately does not declare audit_status, for testing."

        def check(self, drawing: Drawing) -> list[Finding]:
            return []

    rule = UndeclaredAuditStatusRule()

    assert rule.audit_status == RuleAuditStatus.NOT_AUDITED
    assert rule.standard_question_note is None


def test_subclass_missing_check_cannot_be_instantiated() -> None:
    class IncompleteRule(Rule):
        id = "incomplete"
        title = "Incomplete"
        severity = Severity.WARNING
        standard = Standard.GENERAL
        category = RuleCategory.GENERAL
        explanation = "Missing check()."

    with pytest.raises(TypeError):
        IncompleteRule()  # type: ignore[abstract]

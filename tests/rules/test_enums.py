"""Tests for rule engine enumerations."""

from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard


def test_severity_members() -> None:
    assert {member.value for member in Severity} == {"info", "warning", "error", "critical"}


def test_rule_category_members() -> None:
    assert {member.value for member in RuleCategory} == {
        "drawing",
        "feature",
        "datum",
        "dimension",
        "feature_control_frame",
        "tolerance",
        "general",
    }


def test_standard_members() -> None:
    assert {member.value for member in Standard} == {
        "asme_y14.5_2018",
        "asme_y14.5_2009",
        "iso_1101_2017",
        "general",
    }


def test_severity_compares_equal_to_plain_string() -> None:
    assert Severity.ERROR == "error"


def test_rule_category_compares_equal_to_plain_string() -> None:
    assert RuleCategory.DATUM == "datum"


def test_standard_compares_equal_to_plain_string() -> None:
    assert Standard.GENERAL == "general"

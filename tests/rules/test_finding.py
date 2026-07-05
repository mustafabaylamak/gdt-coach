"""Tests for the Finding model."""

import pytest
from pydantic import ValidationError

from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard


def _base_kwargs() -> dict[str, object]:
    return {
        "rule_id": "r1",
        "title": "Rule title",
        "severity": Severity.WARNING,
        "standard": Standard.GENERAL,
        "category": RuleCategory.GENERAL,
        "message": "Something is off.",
    }


def test_minimal_finding_defaults() -> None:
    finding = Finding(**_base_kwargs())

    assert finding.feature_id is None
    assert finding.dimension_id is None
    assert finding.fcf_id is None
    assert finding.datum_label is None


def test_finding_with_locators() -> None:
    finding = Finding(
        **_base_kwargs(),
        feature_id="feat-1",
        dimension_id="dim-1",
        fcf_id="fcf-1",
        datum_label="A",
    )

    assert finding.feature_id == "feat-1"
    assert finding.dimension_id == "dim-1"
    assert finding.fcf_id == "fcf-1"
    assert finding.datum_label == "A"


@pytest.mark.parametrize("field", ["rule_id", "title", "message"])
def test_blank_required_fields_rejected(field: str) -> None:
    kwargs = _base_kwargs()
    kwargs[field] = "   "

    with pytest.raises(ValidationError):
        Finding(**kwargs)


def test_all_severities_accepted() -> None:
    for severity in Severity:
        finding = Finding(**{**_base_kwargs(), "severity": severity})
        assert finding.severity == severity


def test_all_categories_accepted() -> None:
    for category in RuleCategory:
        finding = Finding(**{**_base_kwargs(), "category": category})
        assert finding.category == category


def test_all_standards_accepted() -> None:
    for standard in Standard:
        finding = Finding(**{**_base_kwargs(), "standard": standard})
        assert finding.standard == standard


def test_extra_fields_rejected() -> None:
    with pytest.raises(ValidationError):
        Finding(**_base_kwargs(), bogus_field=1)

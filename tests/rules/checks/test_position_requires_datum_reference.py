"""PASS/FAIL tests for PositionRequiresDatumReferenceRule."""

from gdt_coach.models.enums import GeometricCharacteristic
from gdt_coach.rules.checks.position_requires_datum_reference import (
    PositionRequiresDatumReferenceRule,
)

from .conftest import make_drawing_with_fcf, make_fcf


def test_pass_position_with_datum() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, datum_labels=["A", "B", "C"])
    drawing = make_drawing_with_fcf(fcf)

    findings = PositionRequiresDatumReferenceRule().check(drawing)

    assert findings == []


def test_pass_non_position_without_datum_is_ignored() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.FLATNESS, datum_labels=[])
    drawing = make_drawing_with_fcf(fcf)

    findings = PositionRequiresDatumReferenceRule().check(drawing)

    assert findings == []


def test_fail_position_without_datum() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, datum_labels=[])
    drawing = make_drawing_with_fcf(fcf, feature_id="feat-9")

    findings = PositionRequiresDatumReferenceRule().check(drawing)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "position-requires-datum-reference"
    assert finding.feature_id == "feat-9"
    assert finding.fcf_id == fcf.id

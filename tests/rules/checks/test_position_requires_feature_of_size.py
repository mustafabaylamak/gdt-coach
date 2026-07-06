"""PASS/FAIL tests for PositionRequiresFeatureOfSizeRule (POS.002)."""

from gdt_coach.models import Drawing
from gdt_coach.models.enums import GeometricCharacteristic
from gdt_coach.rules.checks.position_requires_feature_of_size import (
    PositionRequiresFeatureOfSizeRule,
)

from .conftest import make_drawing_with_fcf, make_fcf


def test_pass_position_on_feature_of_size() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, datum_labels=["A"])
    drawing = make_drawing_with_fcf(fcf, feature_of_size=True)

    findings = PositionRequiresFeatureOfSizeRule().check(drawing)

    assert findings == []


def test_pass_non_position_without_fos_is_ignored() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.PROFILE_OF_A_SURFACE, datum_labels=[])
    drawing = make_drawing_with_fcf(fcf, feature_of_size=False)

    findings = PositionRequiresFeatureOfSizeRule().check(drawing)

    assert findings == []


def test_pass_empty_drawing() -> None:
    findings = PositionRequiresFeatureOfSizeRule().check(Drawing(id="dwg-empty", title="Empty"))

    assert findings == []


def test_fail_position_without_feature_of_size() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, datum_labels=["A"])
    drawing = make_drawing_with_fcf(fcf, feature_id="feat-1", feature_of_size=False)

    findings = PositionRequiresFeatureOfSizeRule().check(drawing)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "position-requires-feature-of-size"
    assert finding.feature_id == "feat-1"
    assert finding.fcf_id == fcf.id

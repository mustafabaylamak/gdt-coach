"""PASS/FAIL tests for PositionMaterialConditionRequiresFeatureOfSizeRule (POS.003)."""

import pytest

from gdt_coach.models import Drawing
from gdt_coach.models.enums import GeometricCharacteristic, MaterialCondition
from gdt_coach.rules.checks.position_material_condition_requires_feature_of_size import (
    PositionMaterialConditionRequiresFeatureOfSizeRule,
)

from .conftest import make_drawing_with_fcf, make_fcf, make_tolerance


def test_pass_rfs_position_without_fos() -> None:
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.POSITION,
        datum_labels=["A"],
        tolerance=make_tolerance(),
    )
    drawing = make_drawing_with_fcf(fcf, feature_of_size=False)

    findings = PositionMaterialConditionRequiresFeatureOfSizeRule().check(drawing)

    assert findings == []


@pytest.mark.parametrize("modifier", [MaterialCondition.MMC, MaterialCondition.LMC])
def test_pass_modifier_on_feature_of_size(modifier: MaterialCondition) -> None:
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.POSITION,
        datum_labels=["A"],
        tolerance=make_tolerance(material_condition=modifier),
    )
    drawing = make_drawing_with_fcf(fcf, feature_of_size=True)

    findings = PositionMaterialConditionRequiresFeatureOfSizeRule().check(drawing)

    assert findings == []


def test_pass_form_characteristic_is_out_of_scope() -> None:
    """FORM.004 (form-mmc-requires-feature-of-size) owns straightness/flatness."""
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.FLATNESS,
        tolerance=make_tolerance(material_condition=MaterialCondition.MMC),
    )
    drawing = make_drawing_with_fcf(fcf, feature_of_size=False)

    findings = PositionMaterialConditionRequiresFeatureOfSizeRule().check(drawing)

    assert findings == []


def test_pass_empty_drawing() -> None:
    findings = PositionMaterialConditionRequiresFeatureOfSizeRule().check(
        Drawing(id="dwg-empty", title="Empty")
    )

    assert findings == []


@pytest.mark.parametrize("modifier", [MaterialCondition.MMC, MaterialCondition.LMC])
def test_fail_modifier_without_feature_of_size(modifier: MaterialCondition) -> None:
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.POSITION,
        datum_labels=["A"],
        tolerance=make_tolerance(material_condition=modifier),
    )
    drawing = make_drawing_with_fcf(fcf, feature_id="feat-1", feature_of_size=False)

    findings = PositionMaterialConditionRequiresFeatureOfSizeRule().check(drawing)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "position-material-condition-requires-feature-of-size"
    assert finding.feature_id == "feat-1"
    assert finding.fcf_id == fcf.id
    assert modifier.value in finding.message

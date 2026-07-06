"""PASS/FAIL tests for FormMmcRequiresFeatureOfSizeRule (FORM.004)."""

import pytest

from gdt_coach.models import Drawing
from gdt_coach.models.enums import GeometricCharacteristic, MaterialCondition
from gdt_coach.rules.checks.form_mmc_requires_feature_of_size import (
    FormMmcRequiresFeatureOfSizeRule,
)

from .conftest import make_drawing_with_fcf, make_fcf, make_tolerance


@pytest.mark.parametrize(
    "characteristic", [GeometricCharacteristic.STRAIGHTNESS, GeometricCharacteristic.FLATNESS]
)
def test_pass_rfs_form_tolerance_without_fos(characteristic: GeometricCharacteristic) -> None:
    fcf = make_fcf(characteristic=characteristic, tolerance=make_tolerance())
    drawing = make_drawing_with_fcf(fcf, feature_of_size=False)

    findings = FormMmcRequiresFeatureOfSizeRule().check(drawing)

    assert findings == []


@pytest.mark.parametrize(
    "characteristic", [GeometricCharacteristic.STRAIGHTNESS, GeometricCharacteristic.FLATNESS]
)
@pytest.mark.parametrize("modifier", [MaterialCondition.MMC, MaterialCondition.LMC])
def test_pass_modifier_on_feature_of_size(
    characteristic: GeometricCharacteristic, modifier: MaterialCondition
) -> None:
    fcf = make_fcf(
        characteristic=characteristic, tolerance=make_tolerance(material_condition=modifier)
    )
    drawing = make_drawing_with_fcf(fcf, feature_of_size=True)

    findings = FormMmcRequiresFeatureOfSizeRule().check(drawing)

    assert findings == []


def test_pass_non_form_characteristic_with_modifier_and_no_fos_is_ignored() -> None:
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.POSITION,
        datum_labels=["A"],
        tolerance=make_tolerance(material_condition=MaterialCondition.MMC),
    )
    drawing = make_drawing_with_fcf(fcf, feature_of_size=False)

    findings = FormMmcRequiresFeatureOfSizeRule().check(drawing)

    assert findings == []


def test_pass_empty_drawing() -> None:
    findings = FormMmcRequiresFeatureOfSizeRule().check(Drawing(id="dwg-empty", title="Empty"))

    assert findings == []


@pytest.mark.parametrize(
    "characteristic", [GeometricCharacteristic.STRAIGHTNESS, GeometricCharacteristic.FLATNESS]
)
@pytest.mark.parametrize("modifier", [MaterialCondition.MMC, MaterialCondition.LMC])
def test_fail_modifier_without_feature_of_size(
    characteristic: GeometricCharacteristic, modifier: MaterialCondition
) -> None:
    fcf = make_fcf(
        characteristic=characteristic, tolerance=make_tolerance(material_condition=modifier)
    )
    drawing = make_drawing_with_fcf(fcf, feature_id="feat-1", feature_of_size=False)

    findings = FormMmcRequiresFeatureOfSizeRule().check(drawing)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "form-mmc-requires-feature-of-size"
    assert finding.feature_id == "feat-1"
    assert finding.fcf_id == fcf.id
    assert modifier.value in finding.message

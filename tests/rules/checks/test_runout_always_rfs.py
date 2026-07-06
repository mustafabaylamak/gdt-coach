"""PASS/FAIL tests for RunoutAlwaysRfsRule (RUN.002)."""

import pytest

from gdt_coach.models import Drawing
from gdt_coach.models.enums import GeometricCharacteristic, MaterialCondition
from gdt_coach.rules.checks.runout_always_rfs import RunoutAlwaysRfsRule

from .conftest import make_drawing_with_fcf, make_fcf, make_tolerance

_RUNOUT_CHARACTERISTICS = [
    GeometricCharacteristic.CIRCULAR_RUNOUT,
    GeometricCharacteristic.TOTAL_RUNOUT,
]


@pytest.mark.parametrize("characteristic", _RUNOUT_CHARACTERISTICS)
def test_pass_rfs_runout(characteristic: GeometricCharacteristic) -> None:
    fcf = make_fcf(characteristic=characteristic, datum_labels=["A"], tolerance=make_tolerance())
    drawing = make_drawing_with_fcf(fcf)

    findings = RunoutAlwaysRfsRule().check(drawing)

    assert findings == []


def test_pass_non_runout_with_modifiers_is_ignored() -> None:
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.POSITION,
        datum_labels=["A"],
        tolerance=make_tolerance(material_condition=MaterialCondition.MMC),
    )
    drawing = make_drawing_with_fcf(fcf)

    findings = RunoutAlwaysRfsRule().check(drawing)

    assert findings == []


def test_pass_empty_drawing() -> None:
    findings = RunoutAlwaysRfsRule().check(Drawing(id="dwg-empty", title="Empty"))

    assert findings == []


@pytest.mark.parametrize("characteristic", _RUNOUT_CHARACTERISTICS)
def test_fail_runout_tolerance_with_material_condition(
    characteristic: GeometricCharacteristic,
) -> None:
    fcf = make_fcf(
        characteristic=characteristic,
        datum_labels=["A"],
        tolerance=make_tolerance(material_condition=MaterialCondition.MMC),
    )
    drawing = make_drawing_with_fcf(fcf, feature_id="feat-1")

    findings = RunoutAlwaysRfsRule().check(drawing)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "runout-always-rfs"
    assert finding.feature_id == "feat-1"
    assert finding.fcf_id == fcf.id
    assert "tolerance material condition" in finding.message
    assert "mmc" in finding.message


def test_fail_runout_datum_reference_with_material_condition() -> None:
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.TOTAL_RUNOUT,
        datum_labels=["A"],
        datum_material_conditions={"A": MaterialCondition.LMC},
        tolerance=make_tolerance(),
    )
    drawing = make_drawing_with_fcf(fcf)

    findings = RunoutAlwaysRfsRule().check(drawing)

    assert len(findings) == 1
    assert "datum 'A' material condition" in findings[0].message
    assert "lmc" in findings[0].message


def test_fail_reports_both_tolerance_and_datum_violations_in_one_finding() -> None:
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.CIRCULAR_RUNOUT,
        datum_labels=["A"],
        datum_material_conditions={"A": MaterialCondition.LMC},
        tolerance=make_tolerance(material_condition=MaterialCondition.MMC),
    )
    drawing = make_drawing_with_fcf(fcf)

    findings = RunoutAlwaysRfsRule().check(drawing)

    assert len(findings) == 1
    assert "tolerance material condition" in findings[0].message
    assert "datum 'A' material condition" in findings[0].message

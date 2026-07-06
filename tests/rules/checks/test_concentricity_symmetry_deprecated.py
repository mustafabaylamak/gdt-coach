"""PASS/FAIL tests for ConcentricitySymmetryDeprecatedRule (DEP.001)."""

import pytest

from gdt_coach.models import Drawing
from gdt_coach.models.enums import GeometricCharacteristic
from gdt_coach.rules.checks.concentricity_symmetry_deprecated import (
    ConcentricitySymmetryDeprecatedRule,
)
from gdt_coach.rules.severity import Severity

from .conftest import make_drawing_with_fcf, make_fcf


def test_pass_position_is_not_flagged() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, datum_labels=["A"])
    drawing = make_drawing_with_fcf(fcf)

    findings = ConcentricitySymmetryDeprecatedRule().check(drawing)

    assert findings == []


def test_pass_empty_drawing() -> None:
    findings = ConcentricitySymmetryDeprecatedRule().check(Drawing(id="dwg-empty", title="Empty"))

    assert findings == []


@pytest.mark.parametrize(
    "characteristic",
    [GeometricCharacteristic.CONCENTRICITY, GeometricCharacteristic.SYMMETRY],
)
def test_fail_deprecated_characteristic_is_flagged_as_warning(
    characteristic: GeometricCharacteristic,
) -> None:
    fcf = make_fcf(characteristic=characteristic, datum_labels=["A"])
    drawing = make_drawing_with_fcf(fcf, feature_id="feat-1")

    findings = ConcentricitySymmetryDeprecatedRule().check(drawing)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "concentricity-symmetry-deprecated"
    assert finding.severity == Severity.WARNING
    assert finding.feature_id == "feat-1"
    assert finding.fcf_id == fcf.id
    assert characteristic.value in finding.message


def test_fail_message_mentions_2018_and_edition_caveat() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.CONCENTRICITY, datum_labels=[])
    drawing = make_drawing_with_fcf(fcf)

    findings = ConcentricitySymmetryDeprecatedRule().check(drawing)

    assert len(findings) == 1
    assert "2018" in findings[0].message
    assert "earlier edition" in findings[0].message

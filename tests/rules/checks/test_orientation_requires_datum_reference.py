"""PASS/FAIL tests for OrientationRequiresDatumReferenceRule (ORI.001)."""

import pytest

from gdt_coach.models import Drawing
from gdt_coach.models.enums import GeometricCharacteristic
from gdt_coach.rules.checks.orientation_requires_datum_reference import (
    OrientationRequiresDatumReferenceRule,
)

from .conftest import make_drawing_with_fcf, make_fcf

_ORIENTATION_CHARACTERISTICS = [
    GeometricCharacteristic.ANGULARITY,
    GeometricCharacteristic.PERPENDICULARITY,
    GeometricCharacteristic.PARALLELISM,
]


@pytest.mark.parametrize("characteristic", _ORIENTATION_CHARACTERISTICS)
def test_pass_orientation_with_datum(characteristic: GeometricCharacteristic) -> None:
    fcf = make_fcf(characteristic=characteristic, datum_labels=["A"])
    drawing = make_drawing_with_fcf(fcf)

    findings = OrientationRequiresDatumReferenceRule().check(drawing)

    assert findings == []


def test_pass_non_orientation_without_datum_is_ignored() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.FLATNESS, datum_labels=[])
    drawing = make_drawing_with_fcf(fcf)

    findings = OrientationRequiresDatumReferenceRule().check(drawing)

    assert findings == []


def test_pass_empty_drawing() -> None:
    findings = OrientationRequiresDatumReferenceRule().check(Drawing(id="dwg-empty", title="Empty"))

    assert findings == []


@pytest.mark.parametrize("characteristic", _ORIENTATION_CHARACTERISTICS)
def test_fail_orientation_without_datum(characteristic: GeometricCharacteristic) -> None:
    fcf = make_fcf(characteristic=characteristic, datum_labels=[])
    drawing = make_drawing_with_fcf(fcf, feature_id="feat-9")

    findings = OrientationRequiresDatumReferenceRule().check(drawing)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "orientation-requires-datum-reference"
    assert finding.feature_id == "feat-9"
    assert finding.fcf_id == fcf.id
    assert characteristic.value in finding.message

"""PASS/FAIL tests for AngularityRelatedDimensionMustBeAngularRule."""

from gdt_coach.models import Drawing
from gdt_coach.models.enums import DimensionType, GeometricCharacteristic, Unit
from gdt_coach.rules.checks.angularity_related_dimension_must_be_angular import (
    AngularityRelatedDimensionMustBeAngularRule,
)

from .conftest import make_dimension, make_drawing_with_fcf, make_fcf


def test_pass_angular_related_dimension() -> None:
    angular_dim = make_dimension(
        dimension_id="dim-1", dimension_type=DimensionType.ANGULAR, unit=Unit.DEGREE
    )
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.ANGULARITY, related_dimension_ids=["dim-1"]
    )
    drawing = make_drawing_with_fcf(fcf, dimensions=[angular_dim])

    findings = AngularityRelatedDimensionMustBeAngularRule().check(drawing)

    assert findings == []


def test_pass_non_angularity_characteristic_ignored() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, related_dimension_ids=["dim-1"])
    drawing = make_drawing_with_fcf(fcf, dimensions=[make_dimension(dimension_id="dim-1")])

    findings = AngularityRelatedDimensionMustBeAngularRule().check(drawing)

    assert findings == []


def test_pass_unresolved_id_is_skipped_not_guessed() -> None:
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.ANGULARITY, related_dimension_ids=["dim-missing"]
    )
    drawing = make_drawing_with_fcf(fcf, dimensions=[])

    findings = AngularityRelatedDimensionMustBeAngularRule().check(drawing)

    assert findings == []


def test_pass_empty_related_dimension_ids() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.ANGULARITY, related_dimension_ids=[])
    drawing = make_drawing_with_fcf(fcf)

    findings = AngularityRelatedDimensionMustBeAngularRule().check(drawing)

    assert findings == []


def test_pass_empty_drawing() -> None:
    findings = AngularityRelatedDimensionMustBeAngularRule().check(
        Drawing(id="dwg-empty", title="Empty")
    )

    assert findings == []


def test_fail_non_angular_related_dimension() -> None:
    linear_dim = make_dimension(dimension_id="dim-1", dimension_type=DimensionType.LINEAR)
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.ANGULARITY, related_dimension_ids=["dim-1"]
    )
    drawing = make_drawing_with_fcf(fcf, feature_id="feat-1", dimensions=[linear_dim])

    findings = AngularityRelatedDimensionMustBeAngularRule().check(drawing)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "angularity-related-dimension-must-be-angular"
    assert finding.feature_id == "feat-1"
    assert finding.fcf_id == fcf.id
    assert "dim-1" in finding.message


def test_fail_non_angular_ids_reported_in_deterministic_sorted_order() -> None:
    dims = [
        make_dimension(dimension_id="dim-z", dimension_type=DimensionType.LINEAR),
        make_dimension(dimension_id="dim-a", dimension_type=DimensionType.LINEAR),
    ]
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.ANGULARITY,
        related_dimension_ids=["dim-z", "dim-a"],
    )
    drawing = make_drawing_with_fcf(fcf, dimensions=dims)

    findings = AngularityRelatedDimensionMustBeAngularRule().check(drawing)

    assert len(findings) == 1
    assert str(["dim-a", "dim-z"]) in findings[0].message

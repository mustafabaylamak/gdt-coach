"""PASS/FAIL tests for PositionRelatedDimensionMustBeLocationRule."""

from gdt_coach.models import Drawing, Feature, FeatureType
from gdt_coach.models.enums import DimensionRole, GeometricCharacteristic
from gdt_coach.rules.checks.position_related_dimension_must_be_location import (
    PositionRelatedDimensionMustBeLocationRule,
)

from .conftest import make_dimension, make_drawing_with_fcf, make_fcf


def test_pass_empty_related_dimension_ids() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, related_dimension_ids=[])
    drawing = make_drawing_with_fcf(fcf)

    findings = PositionRelatedDimensionMustBeLocationRule().check(drawing)

    assert findings == []


def test_pass_location_role_related_dimension() -> None:
    location_dim = make_dimension(dimension_id="dim-1", role=DimensionRole.LOCATION)
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, related_dimension_ids=["dim-1"])
    drawing = make_drawing_with_fcf(fcf, dimensions=[location_dim])

    findings = PositionRelatedDimensionMustBeLocationRule().check(drawing)

    assert findings == []


def test_pass_non_position_characteristic_ignored() -> None:
    other_dim = make_dimension(dimension_id="dim-1", role=DimensionRole.SIZE)
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.PROFILE_OF_A_SURFACE,
        related_dimension_ids=["dim-1"],
    )
    drawing = make_drawing_with_fcf(fcf, dimensions=[other_dim])

    findings = PositionRelatedDimensionMustBeLocationRule().check(drawing)

    assert findings == []


def test_pass_unresolved_id_is_skipped_not_guessed() -> None:
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.POSITION, related_dimension_ids=["dim-missing"]
    )
    drawing = make_drawing_with_fcf(fcf, dimensions=[])

    findings = PositionRelatedDimensionMustBeLocationRule().check(drawing)

    assert findings == []


def test_pass_related_id_defined_only_on_another_feature_is_not_resolved() -> None:
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.POSITION, related_dimension_ids=["dim-shared"]
    )
    feature_1 = Feature(id="feat-1", feature_type=FeatureType.HOLE, feature_control_frames=[fcf])
    feature_other = Feature(
        id="feat-other",
        feature_type=FeatureType.HOLE,
        dimensions=[make_dimension(dimension_id="dim-shared", role=DimensionRole.SIZE)],
    )
    drawing = Drawing(id="dwg-1", title="Test drawing", features=[feature_1, feature_other])

    findings = PositionRelatedDimensionMustBeLocationRule().check(drawing)

    assert findings == []


def test_pass_empty_drawing() -> None:
    findings = PositionRelatedDimensionMustBeLocationRule().check(
        Drawing(id="dwg-empty", title="Empty")
    )

    assert findings == []


def test_fail_wrong_role_related_dimension() -> None:
    size_dim = make_dimension(dimension_id="dim-1", role=DimensionRole.SIZE)
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, related_dimension_ids=["dim-1"])
    drawing = make_drawing_with_fcf(fcf, feature_id="feat-1", dimensions=[size_dim])

    findings = PositionRelatedDimensionMustBeLocationRule().check(drawing)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "position-related-dimension-must-be-location"
    assert finding.feature_id == "feat-1"
    assert finding.fcf_id == fcf.id
    assert "dim-1" in finding.message


def test_fail_default_role_other_is_rejected() -> None:
    # Default role is OTHER -- an un-classified dimension does not pass.
    default_dim = make_dimension(dimension_id="dim-1")
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, related_dimension_ids=["dim-1"])
    drawing = make_drawing_with_fcf(fcf, dimensions=[default_dim])

    findings = PositionRelatedDimensionMustBeLocationRule().check(drawing)

    assert len(findings) == 1


def test_fail_mixed_correct_and_wrong_roles_only_reports_wrong_ones() -> None:
    location_dim = make_dimension(dimension_id="dim-location", role=DimensionRole.LOCATION)
    size_dim = make_dimension(dimension_id="dim-size", role=DimensionRole.SIZE)
    orientation_dim = make_dimension(dimension_id="dim-orientation", role=DimensionRole.ORIENTATION)
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.POSITION,
        related_dimension_ids=["dim-location", "dim-size", "dim-orientation"],
    )
    drawing = make_drawing_with_fcf(fcf, dimensions=[location_dim, size_dim, orientation_dim])

    findings = PositionRelatedDimensionMustBeLocationRule().check(drawing)

    assert len(findings) == 1
    assert str(["dim-orientation", "dim-size"]) in findings[0].message
    assert "dim-location" not in findings[0].message


def test_fail_wrong_role_ids_reported_in_deterministic_sorted_order() -> None:
    dims = [
        make_dimension(dimension_id="dim-z", role=DimensionRole.SIZE),
        make_dimension(dimension_id="dim-a", role=DimensionRole.SIZE),
    ]
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.POSITION,
        related_dimension_ids=["dim-z", "dim-a"],
    )
    drawing = make_drawing_with_fcf(fcf, dimensions=dims)

    findings = PositionRelatedDimensionMustBeLocationRule().check(drawing)

    assert len(findings) == 1
    assert str(["dim-a", "dim-z"]) in findings[0].message


def test_fail_mixed_valid_and_unresolved_ids_only_reports_wrong_role() -> None:
    location_dim = make_dimension(dimension_id="dim-location", role=DimensionRole.LOCATION)
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.POSITION,
        related_dimension_ids=["dim-location", "dim-missing"],
    )
    drawing = make_drawing_with_fcf(fcf, dimensions=[location_dim])

    findings = PositionRelatedDimensionMustBeLocationRule().check(drawing)

    assert findings == []

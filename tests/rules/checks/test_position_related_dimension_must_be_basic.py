"""PASS/FAIL tests for PositionRelatedDimensionMustBeBasicRule."""

from gdt_coach.models import Drawing, Feature, FeatureType
from gdt_coach.models.enums import GeometricCharacteristic
from gdt_coach.rules.checks.position_related_dimension_must_be_basic import (
    PositionRelatedDimensionMustBeBasicRule,
)

from .conftest import make_dimension, make_drawing_with_fcf, make_fcf, make_tolerance


def test_pass_basic_related_dimension() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, related_dimension_ids=["dim-1"])
    drawing = make_drawing_with_fcf(fcf, dimensions=[make_dimension(dimension_id="dim-1")])

    findings = PositionRelatedDimensionMustBeBasicRule().check(drawing)

    assert findings == []


def test_pass_non_position_characteristic_ignored() -> None:
    non_basic_dim = make_dimension(dimension_id="dim-1", tolerance=make_tolerance())
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.PROFILE_OF_A_SURFACE,
        related_dimension_ids=["dim-1"],
    )
    drawing = make_drawing_with_fcf(fcf, dimensions=[non_basic_dim])

    findings = PositionRelatedDimensionMustBeBasicRule().check(drawing)

    assert findings == []


def test_pass_unresolved_id_is_skipped_not_guessed() -> None:
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.POSITION, related_dimension_ids=["dim-missing"]
    )
    drawing = make_drawing_with_fcf(fcf, dimensions=[])

    findings = PositionRelatedDimensionMustBeBasicRule().check(drawing)

    assert findings == []


def test_pass_empty_related_dimension_ids() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, related_dimension_ids=[])
    drawing = make_drawing_with_fcf(fcf)

    findings = PositionRelatedDimensionMustBeBasicRule().check(drawing)

    assert findings == []


def test_pass_empty_drawing() -> None:
    findings = PositionRelatedDimensionMustBeBasicRule().check(
        Drawing(id="dwg-empty", title="Empty")
    )

    assert findings == []


def test_pass_related_id_defined_only_on_another_feature_is_not_resolved() -> None:
    # dim-shared is non-basic, but declared on feat-other, not feat-1 --
    # related_dimension_ids resolves only against the owning feature's own
    # dimensions, so this id is unresolved from feat-1's FCF's point of
    # view, not a match.
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.POSITION, related_dimension_ids=["dim-shared"]
    )
    feature_1 = Feature(id="feat-1", feature_type=FeatureType.HOLE, feature_control_frames=[fcf])
    feature_other = Feature(
        id="feat-other",
        feature_type=FeatureType.HOLE,
        dimensions=[make_dimension(dimension_id="dim-shared", tolerance=make_tolerance())],
    )
    drawing = Drawing(id="dwg-1", title="Test drawing", features=[feature_1, feature_other])

    findings = PositionRelatedDimensionMustBeBasicRule().check(drawing)

    assert findings == []


def test_fail_non_basic_related_dimension() -> None:
    non_basic_dim = make_dimension(dimension_id="dim-1", tolerance=make_tolerance())
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, related_dimension_ids=["dim-1"])
    drawing = make_drawing_with_fcf(fcf, feature_id="feat-1", dimensions=[non_basic_dim])

    findings = PositionRelatedDimensionMustBeBasicRule().check(drawing)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "position-related-dimension-must-be-basic"
    assert finding.feature_id == "feat-1"
    assert finding.fcf_id == fcf.id
    assert "dim-1" in finding.message


def test_fail_mixed_valid_missing_and_non_basic_ids_only_reports_non_basic() -> None:
    basic_dim = make_dimension(dimension_id="dim-basic")
    non_basic_dim = make_dimension(dimension_id="dim-non-basic", tolerance=make_tolerance())
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.POSITION,
        related_dimension_ids=["dim-basic", "dim-non-basic", "dim-missing"],
    )
    drawing = make_drawing_with_fcf(fcf, dimensions=[basic_dim, non_basic_dim])

    findings = PositionRelatedDimensionMustBeBasicRule().check(drawing)

    assert len(findings) == 1
    assert str(["dim-non-basic"]) in findings[0].message
    assert "dim-missing" not in findings[0].message


def test_fail_non_basic_ids_reported_in_deterministic_sorted_order() -> None:
    dims = [
        make_dimension(dimension_id="dim-z", tolerance=make_tolerance()),
        make_dimension(dimension_id="dim-a", tolerance=make_tolerance()),
    ]
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.POSITION,
        related_dimension_ids=["dim-z", "dim-a"],
    )
    drawing = make_drawing_with_fcf(fcf, dimensions=dims)

    findings = PositionRelatedDimensionMustBeBasicRule().check(drawing)

    assert len(findings) == 1
    assert str(["dim-a", "dim-z"]) in findings[0].message

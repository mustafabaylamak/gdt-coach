"""PASS/FAIL tests for RelatedDimensionMustBeDefinedRule."""

from gdt_coach.models import Drawing, Feature, FeatureType
from gdt_coach.models.enums import GeometricCharacteristic
from gdt_coach.rules.checks.related_dimension_must_be_defined import (
    RelatedDimensionMustBeDefinedRule,
)

from .conftest import make_dimension, make_drawing_with_fcf, make_fcf


def test_pass_empty_related_dimension_ids() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, related_dimension_ids=[])
    drawing = make_drawing_with_fcf(fcf, dimensions=[make_dimension(dimension_id="dim-1")])

    findings = RelatedDimensionMustBeDefinedRule().check(drawing)

    assert findings == []


def test_pass_all_related_ids_defined() -> None:
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.POSITION,
        related_dimension_ids=["dim-1", "dim-2"],
    )
    drawing = make_drawing_with_fcf(
        fcf,
        dimensions=[make_dimension(dimension_id="dim-1"), make_dimension(dimension_id="dim-2")],
    )

    findings = RelatedDimensionMustBeDefinedRule().check(drawing)

    assert findings == []


def test_pass_empty_drawing() -> None:
    findings = RelatedDimensionMustBeDefinedRule().check(Drawing(id="dwg-empty", title="Empty"))

    assert findings == []


def test_fail_one_missing_id() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, related_dimension_ids=["dim-1"])
    drawing = make_drawing_with_fcf(fcf, feature_id="feat-1", dimensions=[])

    findings = RelatedDimensionMustBeDefinedRule().check(drawing)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "related-dimension-must-be-defined"
    assert finding.feature_id == "feat-1"
    assert finding.fcf_id == fcf.id
    assert "dim-1" in finding.message


def test_fail_mixed_valid_and_missing_ids() -> None:
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.POSITION,
        related_dimension_ids=["dim-1", "dim-2", "dim-3"],
    )
    drawing = make_drawing_with_fcf(fcf, dimensions=[make_dimension(dimension_id="dim-1")])

    findings = RelatedDimensionMustBeDefinedRule().check(drawing)

    assert len(findings) == 1
    assert str(["dim-2", "dim-3"]) in findings[0].message


def test_fail_related_id_defined_only_on_another_feature() -> None:
    # dim-shared exists on feat-other, not on feat-1 -- related_dimension_ids
    # resolves only against the owning feature's own dimensions, so this is
    # still an undefined reference from feat-1's FCF's point of view.
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.POSITION,
        related_dimension_ids=["dim-shared"],
    )
    feature_1 = Feature(
        id="feat-1",
        feature_type=FeatureType.HOLE,
        feature_control_frames=[fcf],
    )
    feature_other = Feature(
        id="feat-other",
        feature_type=FeatureType.HOLE,
        dimensions=[make_dimension(dimension_id="dim-shared")],
    )
    drawing = Drawing(id="dwg-1", title="Test drawing", features=[feature_1, feature_other])

    findings = RelatedDimensionMustBeDefinedRule().check(drawing)

    assert len(findings) == 1
    assert findings[0].feature_id == "feat-1"
    assert "dim-shared" in findings[0].message


def test_fail_missing_ids_reported_in_deterministic_sorted_order() -> None:
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.POSITION,
        related_dimension_ids=["dim-z", "dim-a", "dim-m"],
    )
    drawing = make_drawing_with_fcf(fcf, dimensions=[])

    findings = RelatedDimensionMustBeDefinedRule().check(drawing)

    assert len(findings) == 1
    assert str(["dim-a", "dim-m", "dim-z"]) in findings[0].message

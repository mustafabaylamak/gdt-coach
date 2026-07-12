"""PASS/FAIL tests for RelatedDimensionMustNotBeReferenceRule."""

from gdt_coach.models import Drawing
from gdt_coach.models.enums import GeometricCharacteristic
from gdt_coach.rules.checks.related_dimension_must_not_be_reference import (
    RelatedDimensionMustNotBeReferenceRule,
)

from .conftest import make_dimension, make_drawing_with_fcf, make_fcf


def test_pass_non_reference_related_dimension() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, related_dimension_ids=["dim-1"])
    drawing = make_drawing_with_fcf(fcf, dimensions=[make_dimension(dimension_id="dim-1")])

    findings = RelatedDimensionMustNotBeReferenceRule().check(drawing)

    assert findings == []


def test_pass_unresolved_id_is_skipped_not_guessed() -> None:
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.POSITION, related_dimension_ids=["dim-missing"]
    )
    drawing = make_drawing_with_fcf(fcf, dimensions=[])

    findings = RelatedDimensionMustNotBeReferenceRule().check(drawing)

    assert findings == []


def test_pass_empty_related_dimension_ids() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, related_dimension_ids=[])
    drawing = make_drawing_with_fcf(fcf)

    findings = RelatedDimensionMustNotBeReferenceRule().check(drawing)

    assert findings == []


def test_pass_empty_drawing() -> None:
    findings = RelatedDimensionMustNotBeReferenceRule().check(
        Drawing(id="dwg-empty", title="Empty")
    )

    assert findings == []


def test_fail_reference_related_dimension() -> None:
    reference_dim = make_dimension(dimension_id="dim-1", is_reference=True)
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, related_dimension_ids=["dim-1"])
    drawing = make_drawing_with_fcf(fcf, feature_id="feat-1", dimensions=[reference_dim])

    findings = RelatedDimensionMustNotBeReferenceRule().check(drawing)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "related-dimension-must-not-be-reference"
    assert finding.feature_id == "feat-1"
    assert finding.fcf_id == fcf.id
    assert "dim-1" in finding.message


def test_fail_reference_ids_reported_in_deterministic_sorted_order() -> None:
    dims = [
        make_dimension(dimension_id="dim-z", is_reference=True),
        make_dimension(dimension_id="dim-a", is_reference=True),
    ]
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.POSITION,
        related_dimension_ids=["dim-z", "dim-a"],
    )
    drawing = make_drawing_with_fcf(fcf, dimensions=dims)

    findings = RelatedDimensionMustNotBeReferenceRule().check(drawing)

    assert len(findings) == 1
    assert str(["dim-a", "dim-z"]) in findings[0].message

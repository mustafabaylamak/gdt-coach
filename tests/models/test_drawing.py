"""Tests for the Drawing domain model (aggregate root)."""

import pytest
from pydantic import ValidationError

from gdt_coach.models.datum import Datum
from gdt_coach.models.drawing import Drawing
from gdt_coach.models.enums import DatumFeatureType, FeatureType, Unit
from gdt_coach.models.feature import Feature


def test_minimal_drawing_defaults() -> None:
    drawing = Drawing(id="dwg-1", title="Bracket")

    assert drawing.number is None
    assert drawing.revision is None
    assert drawing.default_unit == Unit.MILLIMETER
    assert drawing.scale is None
    assert drawing.features == []
    assert drawing.datums == []


def test_drawing_with_features_and_datums() -> None:
    feature_a = Feature(id="feat-a", feature_type=FeatureType.PLANE)
    feature_b = Feature(id="feat-b", feature_type=FeatureType.HOLE)
    datum_a = Datum(label="A", feature_type=DatumFeatureType.PLANE)

    drawing = Drawing(
        id="dwg-2",
        title="Housing",
        number="DWG-1001",
        revision="B",
        default_unit=Unit.INCH,
        scale="1:2",
        features=[feature_a, feature_b],
        datums=[datum_a],
    )

    assert drawing.features == [feature_a, feature_b]
    assert drawing.datums == [datum_a]
    assert drawing.default_unit == Unit.INCH


def test_duplicate_feature_ids_rejected() -> None:
    with pytest.raises(ValidationError):
        Drawing(
            id="dwg-3",
            title="Bracket",
            features=[
                Feature(id="feat-x", feature_type=FeatureType.HOLE),
                Feature(id="feat-x", feature_type=FeatureType.SLOT),
            ],
        )


def test_duplicate_datum_labels_rejected() -> None:
    with pytest.raises(ValidationError):
        Drawing(
            id="dwg-4",
            title="Bracket",
            datums=[
                Datum(label="A", feature_type=DatumFeatureType.PLANE),
                Datum(label="A", feature_type=DatumFeatureType.AXIS),
            ],
        )


def test_extra_fields_rejected() -> None:
    with pytest.raises(ValidationError):
        Drawing(id="dwg-5", title="Bracket", bogus_field=1)

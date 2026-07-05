"""Tests for the Feature domain model."""

import pytest
from pydantic import ValidationError

from gdt_coach.models.dimension import Dimension
from gdt_coach.models.enums import (
    DimensionType,
    FeatureType,
    GeometricCharacteristic,
    Unit,
)
from gdt_coach.models.feature import Feature
from gdt_coach.models.feature_control_frame import FeatureControlFrame
from gdt_coach.models.tolerance import Tolerance


def test_minimal_feature_defaults() -> None:
    feature = Feature(id="feat-1", feature_type=FeatureType.HOLE)

    assert feature.name is None
    assert feature.quantity == 1
    assert feature.feature_of_size is False
    assert feature.dimensions == []
    assert feature.feature_control_frames == []


def test_feature_quantity_must_be_at_least_one() -> None:
    with pytest.raises(ValidationError):
        Feature(id="feat-2", feature_type=FeatureType.HOLE, quantity=0)


def test_feature_with_nested_dimensions_and_fcfs() -> None:
    dimension = Dimension(
        id="dim-1",
        dimension_type=DimensionType.DIAMETER,
        nominal_value=10.0,
        unit=Unit.MILLIMETER,
    )
    fcf = FeatureControlFrame(
        id="fcf-1",
        characteristic=GeometricCharacteristic.POSITION,
        tolerance=Tolerance(upper_deviation=0.1, lower_deviation=0.1),
    )

    feature = Feature(
        id="feat-3",
        feature_type=FeatureType.HOLE,
        name="Mounting hole",
        quantity=4,
        feature_of_size=True,
        dimensions=[dimension],
        feature_control_frames=[fcf],
    )

    assert feature.quantity == 4
    assert feature.dimensions == [dimension]
    assert feature.feature_control_frames == [fcf]


def test_all_feature_types_accepted() -> None:
    for feature_type in FeatureType:
        feature = Feature(id="feat", feature_type=feature_type)
        assert feature.feature_type == feature_type


def test_extra_fields_rejected() -> None:
    with pytest.raises(ValidationError):
        Feature(id="feat-4", feature_type=FeatureType.HOLE, bogus_field=1)

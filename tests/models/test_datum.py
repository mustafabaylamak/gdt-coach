"""Tests for the Datum domain model."""

import pytest
from pydantic import ValidationError

from gdt_coach.models.datum import Datum
from gdt_coach.models.enums import DatumFeatureType, MaterialCondition


def test_single_letter_label_valid() -> None:
    datum = Datum(label="A", feature_type=DatumFeatureType.PLANE)

    assert datum.label == "A"
    assert datum.referenced_feature_id is None
    assert datum.material_condition is None


def test_double_letter_label_valid() -> None:
    datum = Datum(label="AA", feature_type=DatumFeatureType.AXIS)

    assert datum.label == "AA"


@pytest.mark.parametrize(
    "invalid_label",
    ["a", "1", "ABC", "", "A1", "A-B"],
)
def test_invalid_labels_rejected(invalid_label: str) -> None:
    with pytest.raises(ValidationError):
        Datum(label=invalid_label, feature_type=DatumFeatureType.PLANE)


def test_referenced_feature_id_and_material_condition() -> None:
    datum = Datum(
        label="B",
        feature_type=DatumFeatureType.AXIS,
        referenced_feature_id="feature-1",
        material_condition=MaterialCondition.MMC,
    )

    assert datum.referenced_feature_id == "feature-1"
    assert datum.material_condition == MaterialCondition.MMC


def test_all_datum_feature_types_accepted() -> None:
    for feature_type in DatumFeatureType:
        datum = Datum(label="C", feature_type=feature_type)
        assert datum.feature_type == feature_type


def test_label_whitespace_is_stripped_before_validation() -> None:
    datum = Datum(label=" A ", feature_type=DatumFeatureType.PLANE)

    assert datum.label == "A"


def test_extra_fields_rejected() -> None:
    with pytest.raises(ValidationError):
        Datum(label="A", feature_type=DatumFeatureType.PLANE, bogus_field=1)

"""Tests for the FeatureControlFrame domain model and DatumReference."""

import pytest
from pydantic import ValidationError

from gdt_coach.models.enums import GeometricCharacteristic, MaterialCondition
from gdt_coach.models.feature_control_frame import DatumReference, FeatureControlFrame
from gdt_coach.models.tolerance import Tolerance


def _tolerance() -> Tolerance:
    return Tolerance(upper_deviation=0.1, lower_deviation=0.1)


def test_minimal_fcf_defaults() -> None:
    fcf = FeatureControlFrame(
        id="fcf-1",
        characteristic=GeometricCharacteristic.FLATNESS,
        tolerance=_tolerance(),
    )

    assert fcf.datum_references == []
    assert fcf.feature_id is None
    assert fcf.all_around is False
    assert fcf.all_over is False
    assert fcf.free_state is False
    assert fcf.statistical_tolerance is False


def test_fcf_with_ordered_datum_references() -> None:
    fcf = FeatureControlFrame(
        id="fcf-2",
        characteristic=GeometricCharacteristic.POSITION,
        tolerance=_tolerance(),
        datum_references=[
            DatumReference(datum_label="A"),
            DatumReference(datum_label="B", material_condition=MaterialCondition.MMC),
            DatumReference(datum_label="C"),
        ],
    )

    assert [ref.datum_label for ref in fcf.datum_references] == ["A", "B", "C"]
    assert fcf.datum_references[1].material_condition == MaterialCondition.MMC


def test_duplicate_datum_references_rejected() -> None:
    with pytest.raises(ValidationError):
        FeatureControlFrame(
            id="fcf-3",
            characteristic=GeometricCharacteristic.POSITION,
            tolerance=_tolerance(),
            datum_references=[
                DatumReference(datum_label="A"),
                DatumReference(datum_label="A"),
            ],
        )


def test_datum_reference_invalid_label_rejected() -> None:
    with pytest.raises(ValidationError):
        DatumReference(datum_label="a")


def test_datum_reference_default_material_condition() -> None:
    ref = DatumReference(datum_label="A")

    assert ref.material_condition == MaterialCondition.RFS


def test_all_geometric_characteristics_accepted() -> None:
    for characteristic in GeometricCharacteristic:
        fcf = FeatureControlFrame(id="fcf", characteristic=characteristic, tolerance=_tolerance())
        assert fcf.characteristic == characteristic


def test_boolean_modifiers() -> None:
    fcf = FeatureControlFrame(
        id="fcf-4",
        characteristic=GeometricCharacteristic.PROFILE_OF_A_SURFACE,
        tolerance=_tolerance(),
        all_around=True,
        all_over=False,
        free_state=True,
        statistical_tolerance=True,
    )

    assert fcf.all_around is True
    assert fcf.free_state is True
    assert fcf.statistical_tolerance is True


def test_extra_fields_rejected() -> None:
    with pytest.raises(ValidationError):
        FeatureControlFrame(
            id="fcf-5",
            characteristic=GeometricCharacteristic.FLATNESS,
            tolerance=_tolerance(),
            bogus_field=1,
        )

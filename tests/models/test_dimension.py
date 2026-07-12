"""Tests for the Dimension domain model."""

import pytest
from pydantic import ValidationError

from gdt_coach.models.dimension import Dimension
from gdt_coach.models.enums import DimensionRole, DimensionType, Unit
from gdt_coach.models.tolerance import Tolerance


def _tolerance() -> Tolerance:
    return Tolerance(upper_deviation=0.1, lower_deviation=0.1)


def test_linear_dimension_with_tolerance_is_not_basic() -> None:
    dimension = Dimension(
        id="dim-1",
        dimension_type=DimensionType.LINEAR,
        nominal_value=25.0,
        unit=Unit.MILLIMETER,
        tolerance=_tolerance(),
    )

    assert dimension.is_basic is False


def test_dimension_without_tolerance_is_basic() -> None:
    dimension = Dimension(
        id="dim-2",
        dimension_type=DimensionType.LINEAR,
        nominal_value=10.0,
        unit=Unit.MILLIMETER,
    )

    assert dimension.is_basic is True


def test_diameter_dimension_requires_positive_value() -> None:
    with pytest.raises(ValidationError):
        Dimension(
            id="dim-3",
            dimension_type=DimensionType.DIAMETER,
            nominal_value=0,
            unit=Unit.MILLIMETER,
        )


def test_radius_dimension_rejects_negative_value() -> None:
    with pytest.raises(ValidationError):
        Dimension(
            id="dim-4",
            dimension_type=DimensionType.RADIUS,
            nominal_value=-5,
            unit=Unit.MILLIMETER,
        )


def test_diameter_dimension_accepts_positive_value() -> None:
    dimension = Dimension(
        id="dim-5",
        dimension_type=DimensionType.DIAMETER,
        nominal_value=12.5,
        unit=Unit.MILLIMETER,
    )

    assert dimension.nominal_value == 12.5


def test_angular_dimension_requires_degree_unit() -> None:
    with pytest.raises(ValidationError):
        Dimension(
            id="dim-6",
            dimension_type=DimensionType.ANGULAR,
            nominal_value=45.0,
            unit=Unit.MILLIMETER,
        )


def test_angular_dimension_with_degree_unit_is_valid() -> None:
    dimension = Dimension(
        id="dim-7",
        dimension_type=DimensionType.ANGULAR,
        nominal_value=45.0,
        unit=Unit.DEGREE,
    )

    assert dimension.nominal_value == 45.0


@pytest.mark.parametrize("value", [360.1, -360.1, 720.0])
def test_angular_dimension_out_of_range_rejected(value: float) -> None:
    with pytest.raises(ValidationError):
        Dimension(
            id="dim-8",
            dimension_type=DimensionType.ANGULAR,
            nominal_value=value,
            unit=Unit.DEGREE,
        )


@pytest.mark.parametrize("value", [-360.0, 0.0, 360.0])
def test_angular_dimension_boundary_values_accepted(value: float) -> None:
    dimension = Dimension(
        id="dim-9",
        dimension_type=DimensionType.ANGULAR,
        nominal_value=value,
        unit=Unit.DEGREE,
    )

    assert dimension.nominal_value == value


def test_linear_dimension_cannot_use_degree_unit() -> None:
    with pytest.raises(ValidationError):
        Dimension(
            id="dim-10",
            dimension_type=DimensionType.LINEAR,
            nominal_value=10.0,
            unit=Unit.DEGREE,
        )


def test_reference_dimension_cannot_carry_tolerance() -> None:
    with pytest.raises(ValidationError):
        Dimension(
            id="dim-11",
            dimension_type=DimensionType.LINEAR,
            nominal_value=10.0,
            unit=Unit.MILLIMETER,
            tolerance=_tolerance(),
            is_reference=True,
        )


def test_reference_dimension_without_tolerance_is_valid() -> None:
    dimension = Dimension(
        id="dim-12",
        dimension_type=DimensionType.LINEAR,
        nominal_value=10.0,
        unit=Unit.MILLIMETER,
        is_reference=True,
    )

    assert dimension.is_reference is True
    assert dimension.is_basic is True


def test_linear_dimension_allows_negative_value_for_coordinates() -> None:
    dimension = Dimension(
        id="dim-13",
        dimension_type=DimensionType.LINEAR,
        nominal_value=-5.0,
        unit=Unit.MILLIMETER,
    )

    assert dimension.nominal_value == -5.0


def test_extra_fields_rejected() -> None:
    with pytest.raises(ValidationError):
        Dimension(
            id="dim-14",
            dimension_type=DimensionType.LINEAR,
            nominal_value=10.0,
            unit=Unit.MILLIMETER,
            bogus_field=1,
        )


def test_default_role_is_other() -> None:
    dimension = Dimension(
        id="dim-15",
        dimension_type=DimensionType.LINEAR,
        nominal_value=10.0,
        unit=Unit.MILLIMETER,
    )

    assert dimension.role == DimensionRole.OTHER


@pytest.mark.parametrize("role", list(DimensionRole))
def test_each_role_value_accepted(role: DimensionRole) -> None:
    dimension = Dimension(
        id="dim-16",
        dimension_type=DimensionType.LINEAR,
        nominal_value=10.0,
        unit=Unit.MILLIMETER,
        role=role,
    )

    assert dimension.role == role


def test_invalid_role_rejected() -> None:
    with pytest.raises(ValidationError):
        Dimension(
            id="dim-17",
            dimension_type=DimensionType.LINEAR,
            nominal_value=10.0,
            unit=Unit.MILLIMETER,
            role="reference",
        )


def test_role_not_inferred_from_dimension_type() -> None:
    # An ANGULAR dimension does not automatically get role=ORIENTATION,
    # and a DIAMETER dimension does not automatically get role=SIZE --
    # role is only ever what's explicitly declared.
    angular_dimension = Dimension(
        id="dim-18",
        dimension_type=DimensionType.ANGULAR,
        nominal_value=45.0,
        unit=Unit.DEGREE,
    )
    diameter_dimension = Dimension(
        id="dim-19",
        dimension_type=DimensionType.DIAMETER,
        nominal_value=10.0,
        unit=Unit.MILLIMETER,
    )

    assert angular_dimension.role == DimensionRole.OTHER
    assert diameter_dimension.role == DimensionRole.OTHER


def test_role_and_is_reference_are_independent() -> None:
    dimension = Dimension(
        id="dim-20",
        dimension_type=DimensionType.LINEAR,
        nominal_value=10.0,
        unit=Unit.MILLIMETER,
        role=DimensionRole.SIZE,
        is_reference=True,
    )

    assert dimension.role == DimensionRole.SIZE
    assert dimension.is_reference is True


def test_existing_yaml_shape_without_role_still_loads_unchanged() -> None:
    # Simulates a Dimension parsed from YAML/JSON authored before role
    # existed: no `role` key at all.
    dimension = Dimension.model_validate(
        {
            "id": "dim-21",
            "dimension_type": "diameter",
            "nominal_value": 10.0,
            "unit": "mm",
        }
    )

    assert dimension.role == DimensionRole.OTHER

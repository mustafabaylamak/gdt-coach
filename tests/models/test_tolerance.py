"""Tests for the Tolerance domain model."""

import pytest
from pydantic import ValidationError

from gdt_coach.models.enums import MaterialCondition, ToleranceZoneShape
from gdt_coach.models.tolerance import Tolerance


def test_symmetric_tolerance_defaults() -> None:
    tolerance = Tolerance(upper_deviation=0.1, lower_deviation=0.1)

    assert tolerance.is_symmetric
    assert tolerance.total_range == pytest.approx(0.2)
    assert tolerance.zone_shape == ToleranceZoneShape.LINEAR
    assert tolerance.material_condition == MaterialCondition.RFS
    assert tolerance.projected_zone_height is None


def test_asymmetric_tolerance_is_not_symmetric() -> None:
    tolerance = Tolerance(upper_deviation=0.2, lower_deviation=0.05)

    assert not tolerance.is_symmetric
    assert tolerance.total_range == pytest.approx(0.25)


def test_unilateral_tolerance_allows_zero_on_one_side() -> None:
    tolerance = Tolerance(upper_deviation=0.3, lower_deviation=0.0)

    assert tolerance.lower_deviation == 0.0


def test_zero_geometric_tolerance_at_mmc_is_valid() -> None:
    tolerance = Tolerance(
        upper_deviation=0.0,
        lower_deviation=0.0,
        material_condition=MaterialCondition.MMC,
    )

    assert tolerance.total_range == 0.0


def test_negative_upper_deviation_rejected() -> None:
    with pytest.raises(ValidationError):
        Tolerance(upper_deviation=-0.1, lower_deviation=0.1)


def test_negative_lower_deviation_rejected() -> None:
    with pytest.raises(ValidationError):
        Tolerance(upper_deviation=0.1, lower_deviation=-0.1)


def test_projected_zone_height_must_be_positive_when_present() -> None:
    with pytest.raises(ValidationError):
        Tolerance(upper_deviation=0.1, lower_deviation=0.1, projected_zone_height=0.0)


def test_projected_zone_height_accepts_positive_value() -> None:
    tolerance = Tolerance(upper_deviation=0.1, lower_deviation=0.1, projected_zone_height=12.0)

    assert tolerance.projected_zone_height == 12.0


def test_cylindrical_zone_shape() -> None:
    tolerance = Tolerance(
        upper_deviation=0.05,
        lower_deviation=0.05,
        zone_shape=ToleranceZoneShape.CYLINDRICAL,
    )

    assert tolerance.zone_shape == ToleranceZoneShape.CYLINDRICAL


def test_extra_fields_rejected() -> None:
    with pytest.raises(ValidationError):
        Tolerance(upper_deviation=0.1, lower_deviation=0.1, bogus_field=1)


def test_assignment_is_validated() -> None:
    tolerance = Tolerance(upper_deviation=0.1, lower_deviation=0.1)

    with pytest.raises(ValidationError):
        tolerance.upper_deviation = -1.0

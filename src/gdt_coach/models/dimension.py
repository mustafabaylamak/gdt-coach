"""Dimension domain model."""

from __future__ import annotations

from typing import Self

from pydantic import model_validator

from gdt_coach.models.base import GDTBaseModel
from gdt_coach.models.enums import DimensionRole, DimensionType, Unit
from gdt_coach.models.tolerance import Tolerance

_ANGULAR_UNITS = {Unit.DEGREE}
_SIZE_TYPES_REQUIRING_POSITIVE_VALUE = {DimensionType.DIAMETER, DimensionType.RADIUS}
_MAX_ANGLE_MAGNITUDE = 360.0


class Dimension(GDTBaseModel):
    """A dimensional value on a drawing (a size or a location)."""

    id: str
    dimension_type: DimensionType
    nominal_value: float
    unit: Unit
    tolerance: Tolerance | None = None
    is_reference: bool = False
    role: DimensionRole = DimensionRole.OTHER

    @property
    def is_basic(self) -> bool:
        """Basic (theoretically exact) dimensions carry no tolerance."""
        return self.tolerance is None

    @model_validator(mode="after")
    def _validate_consistency(self) -> Self:
        if self.dimension_type == DimensionType.ANGULAR:
            if self.unit not in _ANGULAR_UNITS:
                raise ValueError("angular dimensions must use an angular unit (degree)")
            if not (-_MAX_ANGLE_MAGNITUDE <= self.nominal_value <= _MAX_ANGLE_MAGNITUDE):
                raise ValueError("angular dimension magnitude must be within [-360, 360]")
        elif self.unit in _ANGULAR_UNITS:
            raise ValueError(f"{self.dimension_type} dimensions cannot use an angular unit")
        elif (
            self.dimension_type in _SIZE_TYPES_REQUIRING_POSITIVE_VALUE and self.nominal_value <= 0
        ):
            raise ValueError(f"{self.dimension_type} nominal value must be greater than zero")

        if self.is_reference and self.tolerance is not None:
            raise ValueError("a reference dimension cannot carry a tolerance")

        return self

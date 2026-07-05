"""Tolerance domain model."""

from __future__ import annotations

from pydantic import Field

from gdt_coach.models.base import GDTBaseModel
from gdt_coach.models.enums import MaterialCondition, ToleranceZoneShape


class Tolerance(GDTBaseModel):
    """A permissible amount of variation.

    Shared by :class:`~gdt_coach.models.dimension.Dimension` (a size
    tolerance) and :class:`~gdt_coach.models.feature_control_frame.FeatureControlFrame`
    (a geometric tolerance zone). A geometric tolerance zone has a single
    magnitude rather than a range, which is represented here as
    ``upper_deviation == lower_deviation``.
    """

    upper_deviation: float = Field(ge=0)
    lower_deviation: float = Field(ge=0)
    zone_shape: ToleranceZoneShape = ToleranceZoneShape.LINEAR
    material_condition: MaterialCondition = MaterialCondition.RFS
    projected_zone_height: float | None = Field(default=None, gt=0)

    @property
    def is_symmetric(self) -> bool:
        """Whether the upper and lower deviations are equal."""
        return self.upper_deviation == self.lower_deviation

    @property
    def total_range(self) -> float:
        """The full width of the tolerance range (upper + lower deviation)."""
        return self.upper_deviation + self.lower_deviation

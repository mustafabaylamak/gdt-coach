"""Feature domain model."""

from __future__ import annotations

from pydantic import Field

from gdt_coach.models.base import GDTBaseModel
from gdt_coach.models.dimension import Dimension
from gdt_coach.models.enums import FeatureType
from gdt_coach.models.feature_control_frame import FeatureControlFrame


class Feature(GDTBaseModel):
    """A physical feature of a part (e.g. a hole, surface, slot, or pin)."""

    id: str
    feature_type: FeatureType
    name: str | None = None
    quantity: int = Field(default=1, ge=1)
    feature_of_size: bool = False
    dimensions: list[Dimension] = Field(default_factory=list)
    feature_control_frames: list[FeatureControlFrame] = Field(default_factory=list)

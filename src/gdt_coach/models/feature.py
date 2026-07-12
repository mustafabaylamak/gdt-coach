"""Feature domain model."""

from __future__ import annotations

from pydantic import Field, field_validator

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

    @field_validator("dimensions")
    @classmethod
    def _validate_unique_dimension_ids(cls, value: list[Dimension]) -> list[Dimension]:
        ids = [dimension.id for dimension in value]
        duplicates = {i for i in ids if ids.count(i) > 1}
        if duplicates:
            raise ValueError(f"duplicate dimension ids within feature: {sorted(duplicates)}")
        return value

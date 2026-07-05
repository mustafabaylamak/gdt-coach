"""Drawing domain model — the aggregate root."""

from __future__ import annotations

from pydantic import Field, field_validator

from gdt_coach.models.base import GDTBaseModel
from gdt_coach.models.datum import Datum
from gdt_coach.models.enums import Unit
from gdt_coach.models.feature import Feature


class Drawing(GDTBaseModel):
    """An engineering drawing: the top-level container for features and datums."""

    id: str
    title: str
    number: str | None = None
    revision: str | None = None
    default_unit: Unit = Unit.MILLIMETER
    scale: str | None = None
    features: list[Feature] = Field(default_factory=list)
    datums: list[Datum] = Field(default_factory=list)

    @field_validator("features")
    @classmethod
    def _validate_unique_feature_ids(cls, value: list[Feature]) -> list[Feature]:
        ids = [feature.id for feature in value]
        duplicates = {i for i in ids if ids.count(i) > 1}
        if duplicates:
            raise ValueError(f"duplicate feature ids in drawing: {sorted(duplicates)}")
        return value

    @field_validator("datums")
    @classmethod
    def _validate_unique_datum_labels(cls, value: list[Datum]) -> list[Datum]:
        labels = [datum.label for datum in value]
        duplicates = {label for label in labels if labels.count(label) > 1}
        if duplicates:
            raise ValueError(f"duplicate datum labels in drawing: {sorted(duplicates)}")
        return value

"""FeatureControlFrame domain model."""

from __future__ import annotations

import re

from pydantic import Field, field_validator

from gdt_coach.models.base import GDTBaseModel
from gdt_coach.models.enums import GeometricCharacteristic, MaterialCondition
from gdt_coach.models.tolerance import Tolerance

_DATUM_LABEL_PATTERN = re.compile(r"^[A-Z]{1,2}$")


class DatumReference(GDTBaseModel):
    """A single ordered datum reference inside a feature control frame."""

    datum_label: str
    material_condition: MaterialCondition = MaterialCondition.RFS

    @field_validator("datum_label")
    @classmethod
    def _validate_datum_label(cls, value: str) -> str:
        if not _DATUM_LABEL_PATTERN.fullmatch(value):
            raise ValueError(f"datum label {value!r} must be one or two uppercase letters (A-Z)")
        return value


class FeatureControlFrame(GDTBaseModel):
    """A GD&T feature control frame: characteristic symbol, tolerance, and datum references."""

    id: str
    characteristic: GeometricCharacteristic
    tolerance: Tolerance
    datum_references: list[DatumReference] = Field(default_factory=list)
    feature_id: str | None = None
    all_around: bool = False
    all_over: bool = False
    free_state: bool = False
    statistical_tolerance: bool = False
    related_dimension_ids: list[str] = Field(default_factory=list)

    @field_validator("datum_references")
    @classmethod
    def _validate_unique_datum_labels(cls, value: list[DatumReference]) -> list[DatumReference]:
        labels = [ref.datum_label for ref in value]
        duplicates = {label for label in labels if labels.count(label) > 1}
        if duplicates:
            raise ValueError(
                f"duplicate datum references in feature control frame: {sorted(duplicates)}"
            )
        return value

    @field_validator("related_dimension_ids")
    @classmethod
    def _validate_related_dimension_ids(cls, value: list[str]) -> list[str]:
        if any(not dimension_id.strip() for dimension_id in value):
            raise ValueError("related_dimension_ids entries must be non-empty strings")
        duplicates = {dimension_id for dimension_id in value if value.count(dimension_id) > 1}
        if duplicates:
            raise ValueError(
                f"duplicate dimension ids in related_dimension_ids: {sorted(duplicates)}"
            )
        return value

"""Datum domain model."""

from __future__ import annotations

import re

from pydantic import field_validator

from gdt_coach.models.base import GDTBaseModel
from gdt_coach.models.enums import DatumFeatureType, MaterialCondition

_LABEL_PATTERN = re.compile(r"^[A-Z]{1,2}$")


class Datum(GDTBaseModel):
    """A datum feature reference (e.g. ``A``, ``B``) used to build a datum reference frame."""

    label: str
    feature_type: DatumFeatureType
    referenced_feature_id: str | None = None
    material_condition: MaterialCondition | None = None

    @field_validator("label")
    @classmethod
    def _validate_label(cls, value: str) -> str:
        if not _LABEL_PATTERN.fullmatch(value):
            raise ValueError(f"datum label {value!r} must be one or two uppercase letters (A-Z)")
        return value

"""Shared Pydantic base configuration for all gdt-coach domain models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class GDTBaseModel(BaseModel):
    """Base class shared by every domain model.

    Unknown fields are rejected and assignments are re-validated so that
    invalid state cannot be constructed, or mutated into existence, silently.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
    )

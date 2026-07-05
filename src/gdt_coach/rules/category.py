"""Rule categories used to group and filter rules."""

from __future__ import annotations

from enum import StrEnum


class RuleCategory(StrEnum):
    """The domain area a rule primarily inspects.

    Mirrors the domain model layer (:mod:`gdt_coach.models`) so rules
    can be grouped by the kind of object they check.
    """

    DRAWING = "drawing"
    FEATURE = "feature"
    DATUM = "datum"
    DIMENSION = "dimension"
    FEATURE_CONTROL_FRAME = "feature_control_frame"
    TOLERANCE = "tolerance"
    GENERAL = "general"

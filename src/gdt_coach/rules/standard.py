"""Standards a rule can be checking conformance against."""

from __future__ import annotations

from enum import StrEnum


class Standard(StrEnum):
    """The published standard (and edition) a rule enforces."""

    ASME_Y14_5_2018 = "asme_y14.5_2018"
    ASME_Y14_5_2009 = "asme_y14.5_2009"
    ISO_1101_2017 = "iso_1101_2017"
    GENERAL = "general"

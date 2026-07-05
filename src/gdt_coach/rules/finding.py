"""Finding domain model — a single reported rule violation instance."""

from __future__ import annotations

from pydantic import field_validator

from gdt_coach.models.base import GDTBaseModel
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard


class Finding(GDTBaseModel):
    """A single instance of a rule's check reported against a drawing.

    Carries a copy of its rule's metadata (``title``, ``severity``,
    ``standard``, ``category``) so a finding is self-contained and does
    not require looking the rule back up in a registry to be displayed
    or serialized. The locator fields identify which drawing element the
    finding is about; all are optional since not every rule targets a
    single element.
    """

    rule_id: str
    title: str
    severity: Severity
    standard: Standard
    category: RuleCategory
    message: str
    feature_id: str | None = None
    dimension_id: str | None = None
    fcf_id: str | None = None
    datum_label: str | None = None

    @field_validator("rule_id", "title", "message")
    @classmethod
    def _validate_not_blank(cls, value: str) -> str:
        if not value:
            raise ValueError("must not be blank")
        return value

"""Concrete GD&T rule checks.

Each module in this package defines exactly one
:class:`~gdt_coach.rules.base.Rule` subclass and registers itself
against :data:`gdt_coach.rules.registry.default_registry` via the
``@default_registry.register`` decorator. Importing
``gdt_coach.rules.checks`` (this package) is what makes that
registration happen — importing ``gdt_coach.rules`` alone does not,
keeping the rule engine infrastructure free of any concrete rule.
"""

from gdt_coach.rules.checks.duplicate_datum_references import DuplicateDatumReferencesRule
from gdt_coach.rules.checks.flatness_no_datum_references import FlatnessNoDatumReferencesRule
from gdt_coach.rules.checks.position_requires_datum_reference import (
    PositionRequiresDatumReferenceRule,
)
from gdt_coach.rules.checks.projected_zone_requires_position import (
    ProjectedZoneRequiresPositionRule,
)
from gdt_coach.rules.checks.straightness_no_datum_references import (
    StraightnessNoDatumReferencesRule,
)

__all__ = [
    "DuplicateDatumReferencesRule",
    "FlatnessNoDatumReferencesRule",
    "PositionRequiresDatumReferenceRule",
    "ProjectedZoneRequiresPositionRule",
    "StraightnessNoDatumReferencesRule",
]

"""Rule engine layer for gdt-coach.

Infrastructure only — no GD&T rules are implemented here. This package
provides what a concrete rule needs (a base class, severity/category/
standard taxonomies, a findings model) and the machinery to register
and run rules against a :class:`~gdt_coach.models.Drawing` (a registry
and an engine). A new rule is added by defining a
:class:`~gdt_coach.rules.base.Rule` subclass and registering it; none
of the classes in this package need to change.
"""

from gdt_coach.rules.base import Rule
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.engine import RuleEngine
from gdt_coach.rules.exceptions import DuplicateRuleIdError, InvalidRuleError, RuleError
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.registry import RuleRegistry, default_registry
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard

__all__ = [
    "DuplicateRuleIdError",
    "Finding",
    "InvalidRuleError",
    "Rule",
    "RuleCategory",
    "RuleEngine",
    "RuleError",
    "RuleRegistry",
    "Severity",
    "Standard",
    "default_registry",
]

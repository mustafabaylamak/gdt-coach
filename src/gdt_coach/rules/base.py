"""Rule base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from gdt_coach.models import Drawing
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard


class Rule(ABC):
    """A single, independently addable GD&T rule.

    Concrete subclasses declare their metadata as class attributes and
    implement :meth:`check`. Rules are stateless: one instance is
    created (by a :class:`~gdt_coach.rules.registry.RuleRegistry`) and
    reused for every drawing it evaluates. A new rule needs nothing
    beyond a module defining a ``Rule`` subclass and registering it —
    the base class, registry, and engine never need to change.
    """

    id: ClassVar[str]
    title: ClassVar[str]
    severity: ClassVar[Severity]
    standard: ClassVar[Standard]
    category: ClassVar[RuleCategory]
    explanation: ClassVar[str]

    @abstractmethod
    def check(self, drawing: Drawing) -> list[Finding]:
        """Evaluate this rule against ``drawing`` and return any findings."""
        raise NotImplementedError

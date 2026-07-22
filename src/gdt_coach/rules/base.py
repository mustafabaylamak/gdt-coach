"""Rule base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from gdt_coach.models import Drawing
from gdt_coach.rules.audit_status import RuleAuditStatus
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
    audit_status: ClassVar[RuleAuditStatus] = RuleAuditStatus.NOT_AUDITED
    """Defaults to NOT_AUDITED deliberately: a new rule that doesn't
    explicitly set this stays unaudited rather than silently inheriting
    an audited-sounding default. See ``RuleAuditStatus`` and
    ``RULE_AUDIT.md``."""
    standard_question_note: ClassVar[str | None] = None
    """Set only alongside ``INTERNALLY_AUDITED_WITH_OPEN_STANDARD_QUESTION`` --
    a concise, paraphrased description of the specific unresolved
    standard-scope question, never a clause number or quoted standard
    text."""

    @abstractmethod
    def check(self, drawing: Drawing) -> list[Finding]:
        """Evaluate this rule against ``drawing`` and return any findings."""
        raise NotImplementedError

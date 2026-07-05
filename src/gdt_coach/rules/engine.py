"""Rule engine — evaluates registered rules against a drawing."""

from __future__ import annotations

from gdt_coach.models import Drawing
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.registry import RuleRegistry, default_registry
from gdt_coach.rules.standard import Standard


class RuleEngine:
    """Runs a collection of registered rules against a drawing.

    The engine itself knows nothing about any specific rule; it only
    iterates whatever a :class:`~gdt_coach.rules.registry.RuleRegistry`
    hands it and concatenates the resulting findings.
    """

    def __init__(self, registry: RuleRegistry | None = None) -> None:
        self._registry = registry if registry is not None else default_registry

    def run(
        self,
        drawing: Drawing,
        *,
        categories: set[RuleCategory] | None = None,
        standard: Standard | None = None,
    ) -> list[Finding]:
        """Run applicable rules against ``drawing`` and collect their findings.

        ``categories`` and ``standard`` narrow which registered rules run;
        omitting them runs every registered rule.
        """
        findings: list[Finding] = []
        for rule in self._registry.all():
            if categories is not None and rule.category not in categories:
                continue
            if standard is not None and rule.standard != standard:
                continue
            findings.extend(rule.check(drawing))
        return findings

"""Rule registry — where concrete rules register themselves."""

from __future__ import annotations

from gdt_coach.rules.base import Rule
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.exceptions import DuplicateRuleIdError, InvalidRuleError
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard

_REQUIRED_METADATA_FIELDS = ("id", "title", "severity", "standard", "category", "explanation")


class RuleRegistry:
    """A collection of rules, keyed by their unique id.

    New rules register themselves independently of the engine and of
    each other: nothing here needs to change for a new rule to become
    available. A rule module only needs to call :meth:`register`
    against a registry instance (it also works as a class decorator).
    """

    def __init__(self) -> None:
        self._rules: dict[str, Rule] = {}

    def register(self, rule_cls: type[Rule]) -> type[Rule]:
        """Instantiate and register a rule class.

        Returns the class unchanged so this can be used as a decorator::

            @registry.register
            class MyRule(Rule):
                ...
        """
        rule = rule_cls()
        self._validate_metadata(rule)
        if rule.id in self._rules:
            raise DuplicateRuleIdError(f"a rule with id {rule.id!r} is already registered")
        self._rules[rule.id] = rule
        return rule_cls

    def unregister(self, rule_id: str) -> None:
        """Remove a rule by id, if present."""
        self._rules.pop(rule_id, None)

    def get(self, rule_id: str) -> Rule:
        """Look up a registered rule by id."""
        try:
            return self._rules[rule_id]
        except KeyError:
            raise KeyError(f"no rule registered with id {rule_id!r}") from None

    def all(self) -> list[Rule]:
        """Every registered rule, in registration order."""
        return list(self._rules.values())

    def filter(
        self,
        *,
        category: RuleCategory | None = None,
        standard: Standard | None = None,
        severity: Severity | None = None,
    ) -> list[Rule]:
        """Registered rules matching the given criteria (all optional)."""
        rules = self.all()
        if category is not None:
            rules = [rule for rule in rules if rule.category == category]
        if standard is not None:
            rules = [rule for rule in rules if rule.standard == standard]
        if severity is not None:
            rules = [rule for rule in rules if rule.severity == severity]
        return rules

    def clear(self) -> None:
        """Remove every registered rule."""
        self._rules.clear()

    def __len__(self) -> int:
        return len(self._rules)

    def __contains__(self, rule_id: object) -> bool:
        return rule_id in self._rules

    @staticmethod
    def _validate_metadata(rule: Rule) -> None:
        missing = [field for field in _REQUIRED_METADATA_FIELDS if not getattr(rule, field, None)]
        if missing:
            raise InvalidRuleError(
                f"rule {type(rule).__name__} is missing required metadata: {missing}"
            )


default_registry = RuleRegistry()
"""The shared registry used by the engine when no explicit registry is given."""

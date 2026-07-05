"""Exceptions raised by the rule engine layer."""

from __future__ import annotations


class RuleError(Exception):
    """Base class for rule engine errors."""


class InvalidRuleError(RuleError):
    """Raised when a rule is missing required metadata."""


class DuplicateRuleIdError(RuleError):
    """Raised when two rules are registered with the same id."""

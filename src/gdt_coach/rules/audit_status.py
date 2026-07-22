"""A rule's own internal-consistency audit status (RULE_AUDIT.md, Sprint 17)."""

from __future__ import annotations

from enum import StrEnum


class RuleAuditStatus(StrEnum):
    """How far a rule's own internal-consistency review has gone.

    This tracks whether a rule's implementation has been reviewed against
    its own stated title, explanation, and tests -- see ``RULE_AUDIT.md``
    for the full per-rule record. It says nothing about conformance to the
    literal ASME Y14.5 standard text: no value here is, or implies, an
    ASME certification, and none should ever be read as one.
    """

    NOT_AUDITED = "not_audited"
    """No internal-consistency review has been recorded for this rule yet.

    This is the base class default. A rule module must explicitly set a
    different value to claim otherwise -- a new rule that forgets to
    declare its audit status stays ``NOT_AUDITED``, never silently
    inherits an audited-sounding default.
    """

    INTERNALLY_AUDITED = "internally_audited"
    """Reviewed in RULE_AUDIT.md with no open standard-scope question."""

    INTERNALLY_AUDITED_WITH_OPEN_STANDARD_QUESTION = (
        "internally_audited_with_open_standard_question"
    )
    """Reviewed in RULE_AUDIT.md, but its scope boundary has a specific,
    named question that could not be confirmed without a licensed copy of
    the standard -- see the rule's own ``standard_question_note``."""

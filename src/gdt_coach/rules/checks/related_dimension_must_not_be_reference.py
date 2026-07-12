"""Rule: a related dimension must not be a reference dimension.

Limitation: this rule only evaluates related dimension ids that resolve
to a dimension on the same owning feature. An id with no match there is
reported by ``related-dimension-must-be-defined`` instead -- this rule
skips it rather than guessing at a dimension that doesn't exist, to
avoid a duplicate/noisy finding for the same underlying problem.
"""

from __future__ import annotations

from gdt_coach.models import Drawing
from gdt_coach.rules.base import Rule
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.registry import default_registry
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard


@default_registry.register
class RelatedDimensionMustNotBeReferenceRule(Rule):
    """A related dimension must not be a reference (for-information-only) dimension."""

    id = "related-dimension-must-not-be-reference"
    title = "Related dimensions must not be reference dimensions"
    severity = Severity.ERROR
    standard = Standard.GENERAL
    category = RuleCategory.DIMENSION
    explanation = (
        "A reference dimension is for information only and is not toleranced "
        "or enforced; it cannot be the dimension a feature control frame "
        "relies on to establish or support its tolerance."
    )

    def check(self, drawing: Drawing) -> list[Finding]:
        findings: list[Finding] = []
        for feature in drawing.features:
            dimensions_by_id = {dimension.id: dimension for dimension in feature.dimensions}
            for fcf in feature.feature_control_frames:
                reference_ids = sorted(
                    dimension_id
                    for dimension_id in fcf.related_dimension_ids
                    if dimension_id in dimensions_by_id
                    and dimensions_by_id[dimension_id].is_reference
                )
                if reference_ids:
                    findings.append(
                        Finding(
                            rule_id=self.id,
                            title=self.title,
                            severity=self.severity,
                            standard=self.standard,
                            category=self.category,
                            message=(
                                f"feature control frame {fcf.id!r} relates to reference "
                                f"dimension(s) {reference_ids}; a reference dimension "
                                "cannot establish or support a feature control frame"
                            ),
                            feature_id=feature.id,
                            fcf_id=fcf.id,
                        )
                    )
        return findings

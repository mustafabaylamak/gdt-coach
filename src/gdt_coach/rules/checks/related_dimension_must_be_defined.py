"""Rule: every related dimension id must match a dimension on the same feature."""

from __future__ import annotations

from gdt_coach.models import Drawing
from gdt_coach.rules.base import Rule
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.registry import default_registry
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard


@default_registry.register
class RelatedDimensionMustBeDefinedRule(Rule):
    """A feature control frame must not reference an undefined dimension id."""

    id = "related-dimension-must-be-defined"
    title = "Related dimensions must be defined"
    severity = Severity.ERROR
    standard = Standard.GENERAL
    category = RuleCategory.FEATURE_CONTROL_FRAME
    explanation = (
        "A feature control frame's related_dimension_ids names the dimensions "
        "that establish or support it. related_dimension_ids resolves only "
        "against the dimensions declared on the same owning feature -- a "
        "dimension id with no match there is a dangling reference and cannot "
        "be resolved."
    )

    def check(self, drawing: Drawing) -> list[Finding]:
        findings: list[Finding] = []
        for feature in drawing.features:
            defined_ids = {dimension.id for dimension in feature.dimensions}
            for fcf in feature.feature_control_frames:
                missing = sorted(set(fcf.related_dimension_ids) - defined_ids)
                if missing:
                    findings.append(
                        Finding(
                            rule_id=self.id,
                            title=self.title,
                            severity=self.severity,
                            standard=self.standard,
                            category=self.category,
                            message=(
                                f"feature control frame {fcf.id!r} references undefined "
                                f"dimension(s) {missing}; no dimension with that id is "
                                f"defined on feature {feature.id!r}"
                            ),
                            feature_id=feature.id,
                            fcf_id=fcf.id,
                        )
                    )
        return findings

"""Rule: a position tolerance's related dimensions must be basic.

Limitation: this rule only evaluates related dimension ids that resolve
to a dimension on the same owning feature. An id with no match there is
reported by ``related-dimension-must-be-defined`` instead -- this rule
skips it rather than guessing at a dimension that doesn't exist, to
avoid a duplicate/noisy finding for the same underlying problem.
"""

from __future__ import annotations

from gdt_coach.models import Drawing
from gdt_coach.models.enums import GeometricCharacteristic
from gdt_coach.rules.audit_status import RuleAuditStatus
from gdt_coach.rules.base import Rule
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.registry import default_registry
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard


@default_registry.register
class PositionRelatedDimensionMustBeBasicRule(Rule):
    """A position tolerance's related dimensions must be basic (theoretically exact)."""

    id = "position-related-dimension-must-be-basic"
    title = "Position-related dimensions must be basic"
    severity = Severity.ERROR
    standard = Standard.ASME_Y14_5_2018
    category = RuleCategory.DIMENSION
    explanation = (
        "A true position is established relative to basic (theoretically exact) "
        "dimensions. A dimension related to a position feature control frame "
        "that carries its own tolerance is not basic and cannot establish a "
        "true position."
    )
    audit_status = RuleAuditStatus.INTERNALLY_AUDITED

    def check(self, drawing: Drawing) -> list[Finding]:
        findings: list[Finding] = []
        for feature in drawing.features:
            dimensions_by_id = {dimension.id: dimension for dimension in feature.dimensions}
            for fcf in feature.feature_control_frames:
                if fcf.characteristic != GeometricCharacteristic.POSITION:
                    continue
                non_basic = sorted(
                    dimension_id
                    for dimension_id in fcf.related_dimension_ids
                    if dimension_id in dimensions_by_id
                    and not dimensions_by_id[dimension_id].is_basic
                )
                if non_basic:
                    findings.append(
                        Finding(
                            rule_id=self.id,
                            title=self.title,
                            severity=self.severity,
                            standard=self.standard,
                            category=self.category,
                            message=(
                                f"position feature control frame {fcf.id!r} relates to "
                                f"non-basic dimension(s) {non_basic}; a dimension "
                                "establishing a true position must be basic"
                            ),
                            feature_id=feature.id,
                            fcf_id=fcf.id,
                        )
                    )
        return findings

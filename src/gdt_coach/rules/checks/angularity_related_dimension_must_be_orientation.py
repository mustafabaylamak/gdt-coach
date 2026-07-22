"""Rule: an angularity tolerance's related dimensions must have an ORIENTATION role.

Limitation: this rule only evaluates related dimension ids that resolve
to a dimension on the same owning feature. An id with no match there is
reported by ``related-dimension-must-be-defined`` instead -- this rule
skips it rather than guessing at a dimension that doesn't exist, to
avoid a duplicate/noisy finding for the same underlying problem.

This is a semantic-role check, independent of
``angularity-related-dimension-must-be-angular`` (which checks the
dimension's numeric type/shape, i.e. ``dimension_type == ANGULAR``). A
dimension can be an angular value without being intended as the basic
orientation angle for this feature control frame, and role isn't
inferred from dimension_type, so the two checks evaluate different
facts and neither makes the other redundant.
"""

from __future__ import annotations

from gdt_coach.models import Drawing
from gdt_coach.models.enums import DimensionRole, GeometricCharacteristic
from gdt_coach.rules.audit_status import RuleAuditStatus
from gdt_coach.rules.base import Rule
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.registry import default_registry
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard


@default_registry.register
class AngularityRelatedDimensionMustBeOrientationRule(Rule):
    """An angularity tolerance's related dimensions must have role ORIENTATION."""

    id = "angularity-related-dimension-must-be-orientation"
    title = "Angularity-related dimensions must be orientation dimensions"
    severity = Severity.ERROR
    standard = Standard.ASME_Y14_5_2018
    category = RuleCategory.DIMENSION
    explanation = (
        "Angularity controls orientation relative to a basic angle -- a "
        "dimension whose role is to orient the feature, not to size or locate "
        "it. A dimension related to an angularity feature control frame whose "
        "role is not ORIENTATION cannot express the basic angle angularity "
        "requires."
    )
    audit_status = RuleAuditStatus.INTERNALLY_AUDITED

    def check(self, drawing: Drawing) -> list[Finding]:
        findings: list[Finding] = []
        for feature in drawing.features:
            dimensions_by_id = {dimension.id: dimension for dimension in feature.dimensions}
            for fcf in feature.feature_control_frames:
                if fcf.characteristic != GeometricCharacteristic.ANGULARITY:
                    continue
                non_orientation = sorted(
                    dimension_id
                    for dimension_id in fcf.related_dimension_ids
                    if dimension_id in dimensions_by_id
                    and dimensions_by_id[dimension_id].role != DimensionRole.ORIENTATION
                )
                if non_orientation:
                    findings.append(
                        Finding(
                            rule_id=self.id,
                            title=self.title,
                            severity=self.severity,
                            standard=self.standard,
                            category=self.category,
                            message=(
                                f"angularity feature control frame {fcf.id!r} relates to "
                                f"non-orientation dimension(s) {non_orientation}; angularity "
                                "requires a dimension with role ORIENTATION"
                            ),
                            feature_id=feature.id,
                            fcf_id=fcf.id,
                        )
                    )
        return findings

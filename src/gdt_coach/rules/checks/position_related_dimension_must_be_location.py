"""Rule: a position tolerance's related dimensions must have a LOCATION role.

Limitation: this rule only evaluates related dimension ids that resolve
to a dimension on the same owning feature. An id with no match there is
reported by ``related-dimension-must-be-defined`` instead -- this rule
skips it rather than guessing at a dimension that doesn't exist, to
avoid a duplicate/noisy finding for the same underlying problem.

This is a semantic-role check, independent of
``position-related-dimension-must-be-basic`` (which checks that the
dimension carries no tolerance). A dimension can be basic without being
a location dimension (e.g. a basic size), and vice versa, so the two
checks are not redundant.
"""

from __future__ import annotations

from gdt_coach.models import Drawing
from gdt_coach.models.enums import DimensionRole, GeometricCharacteristic
from gdt_coach.rules.base import Rule
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.registry import default_registry
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard


@default_registry.register
class PositionRelatedDimensionMustBeLocationRule(Rule):
    """A position tolerance's related dimensions must have role LOCATION."""

    id = "position-related-dimension-must-be-location"
    title = "Position-related dimensions must be location dimensions"
    severity = Severity.ERROR
    standard = Standard.ASME_Y14_5_2018
    category = RuleCategory.DIMENSION
    explanation = (
        "A true position is established relative to basic location dimensions "
        "-- dimensions whose role is to locate the feature, not to size it or "
        "orient it. A dimension related to a position feature control frame "
        "whose role is not LOCATION cannot establish a true position."
    )

    def check(self, drawing: Drawing) -> list[Finding]:
        findings: list[Finding] = []
        for feature in drawing.features:
            dimensions_by_id = {dimension.id: dimension for dimension in feature.dimensions}
            for fcf in feature.feature_control_frames:
                if fcf.characteristic != GeometricCharacteristic.POSITION:
                    continue
                non_location = sorted(
                    dimension_id
                    for dimension_id in fcf.related_dimension_ids
                    if dimension_id in dimensions_by_id
                    and dimensions_by_id[dimension_id].role != DimensionRole.LOCATION
                )
                if non_location:
                    findings.append(
                        Finding(
                            rule_id=self.id,
                            title=self.title,
                            severity=self.severity,
                            standard=self.standard,
                            category=self.category,
                            message=(
                                f"position feature control frame {fcf.id!r} relates to "
                                f"non-location dimension(s) {non_location}; a dimension "
                                "establishing a true position must have role LOCATION"
                            ),
                            feature_id=feature.id,
                            fcf_id=fcf.id,
                        )
                    )
        return findings

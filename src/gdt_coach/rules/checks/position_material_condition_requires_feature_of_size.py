"""Rule: MMC/LMC on a position tolerance requires a Feature of Size (POS.003).

Scope note: the audit that recommended this rule described it as
"MMC/LMC only on FOS tolerances," grouped in the position (POS) tier
as a sibling of position-requires-feature-of-size and
position-requires-datum-reference. It is scoped here specifically to
``characteristic == POSITION`` to match that tier placement and avoid
overlapping with form-mmc-requires-feature-of-size (which already
covers straightness/flatness). A broader version covering every
characteristic that can carry a material condition modifier was
explicitly out of scope for this sprint.

Limitation: like the other Feature-of-Size rules in this sprint, this
trusts :attr:`Feature.feature_of_size` as ground truth (default
``False``); no heuristic is used to infer it.
"""

from __future__ import annotations

from gdt_coach.models import Drawing
from gdt_coach.models.enums import GeometricCharacteristic, MaterialCondition
from gdt_coach.rules.audit_status import RuleAuditStatus
from gdt_coach.rules.base import Rule
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.registry import default_registry
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard


@default_registry.register
class PositionMaterialConditionRequiresFeatureOfSizeRule(Rule):
    """A position tolerance's MMC/LMC modifier requires a Feature of Size."""

    id = "position-material-condition-requires-feature-of-size"
    title = "MMC/LMC on position requires a Feature of Size"
    severity = Severity.ERROR
    standard = Standard.ASME_Y14_5_2018
    category = RuleCategory.TOLERANCE
    explanation = (
        "An MMC or LMC modifier on a position tolerance describes a bonus "
        "tolerance tied to the produced size of a Feature of Size. Applying "
        "that modifier to a position tolerance on a feature that is not a "
        "Feature of Size is meaningless -- there is no size to depart from."
    )
    audit_status = RuleAuditStatus.INTERNALLY_AUDITED

    def check(self, drawing: Drawing) -> list[Finding]:
        findings: list[Finding] = []
        for feature in drawing.features:
            for fcf in feature.feature_control_frames:
                if (
                    fcf.characteristic == GeometricCharacteristic.POSITION
                    and fcf.tolerance.material_condition != MaterialCondition.RFS
                    and not feature.feature_of_size
                ):
                    findings.append(
                        Finding(
                            rule_id=self.id,
                            title=self.title,
                            severity=self.severity,
                            standard=self.standard,
                            category=self.category,
                            message=(
                                f"position feature control frame {fcf.id!r} "
                                f"specifies material condition "
                                f"{fcf.tolerance.material_condition.value!r} on "
                                f"feature {feature.id!r}, which is not marked as a "
                                "Feature of Size"
                            ),
                            feature_id=feature.id,
                            fcf_id=fcf.id,
                        )
                    )
        return findings

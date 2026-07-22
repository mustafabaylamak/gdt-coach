"""Rule: a projected tolerance zone requires a position tolerance."""

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
class ProjectedZoneRequiresPositionRule(Rule):
    """A projected tolerance zone only applies to a position tolerance."""

    id = "projected-zone-requires-position"
    title = "Projected tolerance zone requires a position tolerance"
    severity = Severity.ERROR
    standard = Standard.ASME_Y14_5_2018
    category = RuleCategory.TOLERANCE
    explanation = (
        "A projected tolerance zone (the height projected above the surface) "
        "is only meaningful for a position tolerance; specifying it on any "
        "other characteristic is invalid."
    )
    audit_status = RuleAuditStatus.INTERNALLY_AUDITED_WITH_OPEN_STANDARD_QUESTION
    standard_question_note = (
        "Whether a projected tolerance zone is ever legitimately applied to "
        "an orientation characteristic (e.g. certain fastener contexts), "
        "rather than exclusively to position, has not been confirmed "
        "against a licensed copy of the standard."
    )

    def check(self, drawing: Drawing) -> list[Finding]:
        findings: list[Finding] = []
        for feature in drawing.features:
            for fcf in feature.feature_control_frames:
                if (
                    fcf.tolerance.projected_zone_height is not None
                    and fcf.characteristic != GeometricCharacteristic.POSITION
                ):
                    findings.append(
                        Finding(
                            rule_id=self.id,
                            title=self.title,
                            severity=self.severity,
                            standard=self.standard,
                            category=self.category,
                            message=(
                                f"feature control frame {fcf.id!r} specifies a projected "
                                f"tolerance zone but its characteristic is "
                                f"{fcf.characteristic.value!r}, not position"
                            ),
                            feature_id=feature.id,
                            fcf_id=fcf.id,
                        )
                    )
        return findings

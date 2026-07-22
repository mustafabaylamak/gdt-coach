"""Rule: position applies only to a Feature of Size (POS.002).

Limitation: this rule trusts :attr:`Feature.feature_of_size` as ground
truth (default ``False``). It does not infer FOS status from
``feature_type`` or any other heuristic -- a feature that is actually a
Feature of Size but left un-flagged will be reported as a false
violation.
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
class PositionRequiresFeatureOfSizeRule(Rule):
    """Position tolerance applies only to a Feature of Size, never a plain surface."""

    id = "position-requires-feature-of-size"
    title = "Position applies only to a Feature of Size"
    severity = Severity.ERROR
    standard = Standard.ASME_Y14_5_2018
    category = RuleCategory.FEATURE_CONTROL_FRAME
    explanation = (
        "Position tolerance locates the derived center point, axis, or center "
        "plane of a Feature of Size. Applying position to a feature that is not "
        "a Feature of Size (e.g. a plain surface) is a category error -- profile "
        "of a surface is the correct tool there."
    )
    audit_status = RuleAuditStatus.INTERNALLY_AUDITED

    def check(self, drawing: Drawing) -> list[Finding]:
        findings: list[Finding] = []
        for feature in drawing.features:
            for fcf in feature.feature_control_frames:
                if (
                    fcf.characteristic == GeometricCharacteristic.POSITION
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
                                f"position feature control frame {fcf.id!r} is on "
                                f"feature {feature.id!r}, which is not marked as a "
                                "Feature of Size"
                            ),
                            feature_id=feature.id,
                            fcf_id=fcf.id,
                        )
                    )
        return findings

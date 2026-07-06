"""Rule: straightness/flatness may use MMC/LMC only on a Feature of Size (FORM.004).

Limitation: this rule trusts :attr:`Feature.feature_of_size` as ground
truth. That field defaults to ``False`` and is not inferred from
``feature_type`` or anything else -- if a drawing under-declares a
feature that is actually a Feature of Size (e.g. leaves the flag unset
on a genuine cylindrical feature), this rule will report a false
violation. No heuristic is used to guess FOS status from
``feature_type``; per the sprint's requirements, the explicit field is
the only source of truth.
"""

from __future__ import annotations

from gdt_coach.models import Drawing
from gdt_coach.models.enums import GeometricCharacteristic, MaterialCondition
from gdt_coach.rules.base import Rule
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.registry import default_registry
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard

_FORM_CHARACTERISTICS_ALLOWING_MODIFIERS = {
    GeometricCharacteristic.STRAIGHTNESS,
    GeometricCharacteristic.FLATNESS,
}


@default_registry.register
class FormMmcRequiresFeatureOfSizeRule(Rule):
    """Straightness/flatness with MMC or LMC applies only to a Feature of Size."""

    id = "form-mmc-requires-feature-of-size"
    title = "Straightness/flatness may use MMC/LMC only on a Feature of Size"
    severity = Severity.ERROR
    standard = Standard.ASME_Y14_5_2018
    category = RuleCategory.FEATURE_CONTROL_FRAME
    explanation = (
        "Straightness and flatness are otherwise datum-less form tolerances, but "
        "ASME Y14.5 makes one exception: applied to the derived median line or "
        "median plane of a Feature of Size, they may carry an MMC or LMC "
        "material condition modifier. That modifier is meaningless on a form "
        "tolerance applied to a plain surface (not a Feature of Size)."
    )

    def check(self, drawing: Drawing) -> list[Finding]:
        findings: list[Finding] = []
        for feature in drawing.features:
            for fcf in feature.feature_control_frames:
                if (
                    fcf.characteristic in _FORM_CHARACTERISTICS_ALLOWING_MODIFIERS
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
                                f"{fcf.characteristic.value} feature control frame "
                                f"{fcf.id!r} specifies material condition "
                                f"{fcf.tolerance.material_condition.value!r} on "
                                f"feature {feature.id!r}, which is not marked as a "
                                "Feature of Size"
                            ),
                            feature_id=feature.id,
                            fcf_id=fcf.id,
                        )
                    )
        return findings

"""Rule: runout is always RFS, on both the tolerance and its datum references (RUN.002)."""

from __future__ import annotations

from gdt_coach.models import Drawing
from gdt_coach.models.enums import GeometricCharacteristic, MaterialCondition
from gdt_coach.rules.base import Rule
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.registry import default_registry
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard

_RUNOUT_CHARACTERISTICS = {
    GeometricCharacteristic.CIRCULAR_RUNOUT,
    GeometricCharacteristic.TOTAL_RUNOUT,
}


@default_registry.register
class RunoutAlwaysRfsRule(Rule):
    """Runout tolerances and their datum references never carry MMC/LMC."""

    id = "runout-always-rfs"
    title = "Runout is always RFS"
    severity = Severity.ERROR
    standard = Standard.ASME_Y14_5_2018
    category = RuleCategory.FEATURE_CONTROL_FRAME
    explanation = (
        "Runout characteristics (circular runout, total runout) are inherently "
        "regardless-of-feature-size: no material condition modifier is ever "
        "applied, neither to the runout tolerance value nor to any of its datum "
        "references."
    )

    def check(self, drawing: Drawing) -> list[Finding]:
        findings: list[Finding] = []
        for feature in drawing.features:
            for fcf in feature.feature_control_frames:
                if fcf.characteristic not in _RUNOUT_CHARACTERISTICS:
                    continue

                violations: list[str] = []
                if fcf.tolerance.material_condition != MaterialCondition.RFS:
                    violations.append(
                        f"tolerance material condition {fcf.tolerance.material_condition.value!r}"
                    )
                for ref in fcf.datum_references:
                    if ref.material_condition != MaterialCondition.RFS:
                        violations.append(
                            f"datum {ref.datum_label!r} material condition "
                            f"{ref.material_condition.value!r}"
                        )

                if violations:
                    findings.append(
                        Finding(
                            rule_id=self.id,
                            title=self.title,
                            severity=self.severity,
                            standard=self.standard,
                            category=self.category,
                            message=(
                                f"{fcf.characteristic.value} feature control frame "
                                f"{fcf.id!r} must be RFS everywhere, but found: "
                                f"{'; '.join(violations)}"
                            ),
                            feature_id=feature.id,
                            fcf_id=fcf.id,
                        )
                    )
        return findings

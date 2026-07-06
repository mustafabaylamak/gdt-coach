"""Rule: orientation tolerances require at least one datum reference (ORI.001)."""

from __future__ import annotations

from gdt_coach.models import Drawing
from gdt_coach.models.enums import GeometricCharacteristic
from gdt_coach.rules.base import Rule
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.registry import default_registry
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard

_ORIENTATION_CHARACTERISTICS = {
    GeometricCharacteristic.ANGULARITY,
    GeometricCharacteristic.PERPENDICULARITY,
    GeometricCharacteristic.PARALLELISM,
}


@default_registry.register
class OrientationRequiresDatumReferenceRule(Rule):
    """Orientation tolerances need a datum to be oriented relative to."""

    id = "orientation-requires-datum-reference"
    title = "Orientation tolerances require at least one datum"
    severity = Severity.ERROR
    standard = Standard.ASME_Y14_5_2018
    category = RuleCategory.FEATURE_CONTROL_FRAME
    explanation = (
        "Angularity, perpendicularity, and parallelism orient a feature relative "
        "to a datum reference frame. An orientation feature control frame with "
        "no datum references has nothing to orient the feature against."
    )

    def check(self, drawing: Drawing) -> list[Finding]:
        findings: list[Finding] = []
        for feature in drawing.features:
            for fcf in feature.feature_control_frames:
                if fcf.characteristic in _ORIENTATION_CHARACTERISTICS and not fcf.datum_references:
                    findings.append(
                        Finding(
                            rule_id=self.id,
                            title=self.title,
                            severity=self.severity,
                            standard=self.standard,
                            category=self.category,
                            message=(
                                f"{fcf.characteristic.value} feature control frame "
                                f"{fcf.id!r} has no datum references"
                            ),
                            feature_id=feature.id,
                            fcf_id=fcf.id,
                        )
                    )
        return findings

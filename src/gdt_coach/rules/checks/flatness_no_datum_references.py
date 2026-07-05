"""Rule: flatness must not reference any datum."""

from __future__ import annotations

from gdt_coach.models import Drawing
from gdt_coach.models.enums import GeometricCharacteristic
from gdt_coach.rules.base import Rule
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.registry import default_registry
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard


@default_registry.register
class FlatnessNoDatumReferencesRule(Rule):
    """Flatness is a form tolerance and must not reference a datum."""

    id = "flatness-no-datum-references"
    title = "Flatness cannot reference datums"
    severity = Severity.ERROR
    standard = Standard.ASME_Y14_5_2018
    category = RuleCategory.FEATURE_CONTROL_FRAME
    explanation = (
        "Flatness controls a surface only relative to itself. Per ASME Y14.5, "
        "form tolerances (flatness, straightness, circularity, cylindricity) "
        "never reference a datum; any datum reference on a flatness feature "
        "control frame is meaningless and must be removed."
    )

    def check(self, drawing: Drawing) -> list[Finding]:
        findings: list[Finding] = []
        for feature in drawing.features:
            for fcf in feature.feature_control_frames:
                if fcf.characteristic == GeometricCharacteristic.FLATNESS and fcf.datum_references:
                    labels = [ref.datum_label for ref in fcf.datum_references]
                    findings.append(
                        Finding(
                            rule_id=self.id,
                            title=self.title,
                            severity=self.severity,
                            standard=self.standard,
                            category=self.category,
                            message=(
                                f"flatness feature control frame {fcf.id!r} references "
                                f"datum(s) {labels}, but flatness must not reference "
                                "any datum"
                            ),
                            feature_id=feature.id,
                            fcf_id=fcf.id,
                        )
                    )
        return findings

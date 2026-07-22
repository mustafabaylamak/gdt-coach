"""Rule: cylindricity must not reference any datum."""

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
class CylindricityNoDatumReferencesRule(Rule):
    """Cylindricity is a form tolerance and must not reference a datum."""

    id = "cylindricity-no-datum-references"
    title = "Cylindricity cannot reference datums"
    severity = Severity.ERROR
    standard = Standard.ASME_Y14_5_2018
    category = RuleCategory.FEATURE_CONTROL_FRAME
    explanation = (
        "Cylindricity controls a cylindrical surface only relative to itself, "
        "combining circularity and straightness of the surface simultaneously. "
        "Per ASME Y14.5, form tolerances (flatness, straightness, circularity, "
        "cylindricity) never reference a datum; any datum reference on a "
        "cylindricity feature control frame is meaningless and must be removed."
    )
    audit_status = RuleAuditStatus.INTERNALLY_AUDITED

    def check(self, drawing: Drawing) -> list[Finding]:
        findings: list[Finding] = []
        for feature in drawing.features:
            for fcf in feature.feature_control_frames:
                if (
                    fcf.characteristic == GeometricCharacteristic.CYLINDRICITY
                    and fcf.datum_references
                ):
                    labels = [ref.datum_label for ref in fcf.datum_references]
                    findings.append(
                        Finding(
                            rule_id=self.id,
                            title=self.title,
                            severity=self.severity,
                            standard=self.standard,
                            category=self.category,
                            message=(
                                f"cylindricity feature control frame {fcf.id!r} "
                                f"references datum(s) {labels}, but cylindricity must "
                                "not reference any datum"
                            ),
                            feature_id=feature.id,
                            fcf_id=fcf.id,
                        )
                    )
        return findings

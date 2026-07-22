"""Rule: concentricity and symmetry were removed in ASME Y14.5-2018 (DEP.001).

Limitation: :class:`~gdt_coach.models.Drawing` has no field recording
which standard *edition* a drawing itself targets (only
:class:`~gdt_coach.rules.standard.Standard` exists, and that describes
a *rule's* target, not a drawing's). This rule therefore has no way to
tell whether a given drawing is meant to conform to ASME Y14.5-2018
(where these symbols are removed) or an earlier edition such as
2009 (where they are still valid). Rather than guess, it always flags
concentricity/symmetry usage at :attr:`Severity.WARNING` rather than
:attr:`Severity.ERROR`, and the finding message says so explicitly.
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

_DEPRECATED_CHARACTERISTICS = {
    GeometricCharacteristic.CONCENTRICITY,
    GeometricCharacteristic.SYMMETRY,
}
_MIGRATION_ADVICE = {
    GeometricCharacteristic.CONCENTRICITY: "position",
    GeometricCharacteristic.SYMMETRY: "position, or runout/profile",
}


@default_registry.register
class ConcentricitySymmetryDeprecatedRule(Rule):
    """Concentricity and symmetry were removed from ASME Y14.5 in the 2018 edition."""

    id = "concentricity-symmetry-deprecated"
    title = "Concentricity and symmetry are deprecated (ASME Y14.5-2018)"
    severity = Severity.WARNING
    standard = Standard.ASME_Y14_5_2018
    category = RuleCategory.FEATURE_CONTROL_FRAME
    explanation = (
        "ASME Y14.5-2018 removed the concentricity and symmetry characteristic "
        "symbols; position (for concentricity) or runout/profile (for symmetry) "
        "are the recommended replacements. This drawing has no recorded target "
        "standard edition, so this is reported as a warning rather than an error "
        "-- it does not apply if this drawing is intentionally authored to an "
        "earlier edition such as ASME Y14.5-2009, where these symbols are still "
        "valid."
    )
    audit_status = RuleAuditStatus.INTERNALLY_AUDITED

    def check(self, drawing: Drawing) -> list[Finding]:
        findings: list[Finding] = []
        for feature in drawing.features:
            for fcf in feature.feature_control_frames:
                if fcf.characteristic in _DEPRECATED_CHARACTERISTICS:
                    findings.append(
                        Finding(
                            rule_id=self.id,
                            title=self.title,
                            severity=self.severity,
                            standard=self.standard,
                            category=self.category,
                            message=(
                                f"feature control frame {fcf.id!r} uses "
                                f"{fcf.characteristic.value!r}, which was removed in "
                                "ASME Y14.5-2018 (consider "
                                f"{_MIGRATION_ADVICE[fcf.characteristic]} instead); "
                                "this warning does not apply if the drawing targets "
                                "an earlier edition"
                            ),
                            feature_id=feature.id,
                            fcf_id=fcf.id,
                        )
                    )
        return findings

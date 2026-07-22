"""Rule: every referenced datum must be defined on the drawing (SYN.003)."""

from __future__ import annotations

from gdt_coach.models import Drawing
from gdt_coach.rules.audit_status import RuleAuditStatus
from gdt_coach.rules.base import Rule
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.registry import default_registry
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard


@default_registry.register
class DatumReferenceMustBeDefinedRule(Rule):
    """A feature control frame must not reference an undefined datum."""

    id = "datum-reference-must-be-defined"
    title = "Referenced datums must be defined"
    severity = Severity.ERROR
    standard = Standard.GENERAL
    category = RuleCategory.FEATURE_CONTROL_FRAME
    explanation = (
        "A datum reference frame is built from datums declared on the drawing. "
        "A feature control frame that references a datum label with no matching "
        "datum defined anywhere on the drawing has a dangling reference and its "
        "datum reference frame cannot be established."
    )
    audit_status = RuleAuditStatus.INTERNALLY_AUDITED

    def check(self, drawing: Drawing) -> list[Finding]:
        defined_labels = {datum.label for datum in drawing.datums}
        findings: list[Finding] = []
        for feature in drawing.features:
            for fcf in feature.feature_control_frames:
                referenced_labels = {ref.datum_label for ref in fcf.datum_references}
                undefined = sorted(referenced_labels - defined_labels)
                if undefined:
                    findings.append(
                        Finding(
                            rule_id=self.id,
                            title=self.title,
                            severity=self.severity,
                            standard=self.standard,
                            category=self.category,
                            message=(
                                f"feature control frame {fcf.id!r} references undefined "
                                f"datum(s) {undefined}; no datum with that label is "
                                "defined on this drawing"
                            ),
                            feature_id=feature.id,
                            fcf_id=fcf.id,
                        )
                    )
        return findings

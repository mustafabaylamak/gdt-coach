"""Rule: a feature control frame must not repeat a datum reference."""

from __future__ import annotations

from gdt_coach.models import Drawing
from gdt_coach.rules.base import Rule
from gdt_coach.rules.category import RuleCategory
from gdt_coach.rules.finding import Finding
from gdt_coach.rules.registry import default_registry
from gdt_coach.rules.severity import Severity
from gdt_coach.rules.standard import Standard


@default_registry.register
class DuplicateDatumReferencesRule(Rule):
    """A single feature control frame must reference each datum at most once.

    Limitation: :class:`~gdt_coach.models.feature_control_frame.FeatureControlFrame`
    already enforces this at construction time (its own Pydantic
    validator rejects duplicate ``datum_references`` labels), so this
    condition is unreachable for any :class:`~gdt_coach.models.Drawing`
    built through the normal, validated constructors. This rule exists
    as defense-in-depth for data that reaches the engine without going
    through that validation — for example a future parser that uses
    ``model_construct()`` for speed, or a drawing tree assembled/mutated
    programmatically. See the corresponding test module for how that
    scenario is exercised.
    """

    id = "fcf-duplicate-datum-references"
    title = "Duplicate datum references in one feature control frame"
    severity = Severity.ERROR
    standard = Standard.GENERAL
    category = RuleCategory.FEATURE_CONTROL_FRAME
    explanation = (
        "A datum reference frame is built from distinct datums; listing the "
        "same datum more than once in a single feature control frame is "
        "contradictory and must be corrected."
    )

    def check(self, drawing: Drawing) -> list[Finding]:
        findings: list[Finding] = []
        for feature in drawing.features:
            for fcf in feature.feature_control_frames:
                labels = [ref.datum_label for ref in fcf.datum_references]
                duplicates = sorted({label for label in labels if labels.count(label) > 1})
                if duplicates:
                    findings.append(
                        Finding(
                            rule_id=self.id,
                            title=self.title,
                            severity=self.severity,
                            standard=self.standard,
                            category=self.category,
                            message=(
                                f"feature control frame {fcf.id!r} repeats datum "
                                f"reference(s) {duplicates}"
                            ),
                            feature_id=feature.id,
                            fcf_id=fcf.id,
                        )
                    )
        return findings

"""PASS/FAIL tests for DuplicateDatumReferencesRule.

Duplicate datum references within one feature control frame are already
rejected by `FeatureControlFrame`'s own Pydantic validator (see
`gdt_coach.models.feature_control_frame`), so normal, validated
construction can never produce the FAIL scenario this rule checks for.
The FAIL test below uses `model_construct()` at every level (FCF,
Feature, Drawing) to bypass validation entirely and build the
otherwise-impossible tree directly -- simulating data that reached the
rule engine without going through the domain model's normal validated
constructors.
"""

import pytest
from pydantic import ValidationError

from gdt_coach.models import Drawing, Feature, FeatureType, Unit
from gdt_coach.models.feature_control_frame import DatumReference, FeatureControlFrame
from gdt_coach.rules.checks.duplicate_datum_references import DuplicateDatumReferencesRule

from .conftest import make_drawing_with_fcf, make_fcf, make_tolerance


def test_pass_unique_datum_references() -> None:
    fcf = make_fcf(datum_labels=["A", "B", "C"])
    drawing = make_drawing_with_fcf(fcf)

    findings = DuplicateDatumReferencesRule().check(drawing)

    assert findings == []


def test_pass_no_datum_references() -> None:
    fcf = make_fcf(datum_labels=[])
    drawing = make_drawing_with_fcf(fcf)

    findings = DuplicateDatumReferencesRule().check(drawing)

    assert findings == []


def test_normal_construction_cannot_produce_duplicates() -> None:
    """Documents the limitation: the domain model already forbids this."""
    with pytest.raises(ValidationError, match="duplicate"):
        make_fcf(datum_labels=["A", "A"])


def test_fail_duplicate_datum_reference_bypassing_model_validation() -> None:
    fcf = FeatureControlFrame.model_construct(
        id="fcf-bad",
        characteristic=make_fcf().characteristic,
        tolerance=make_tolerance(),
        datum_references=[
            DatumReference(datum_label="A"),
            DatumReference(datum_label="A"),
        ],
        feature_id=None,
        all_around=False,
        all_over=False,
        free_state=False,
        statistical_tolerance=False,
    )
    feature = Feature.model_construct(
        id="feat-1",
        feature_type=FeatureType.HOLE,
        name=None,
        quantity=1,
        feature_of_size=False,
        dimensions=[],
        feature_control_frames=[fcf],
    )
    drawing = Drawing.model_construct(
        id="dwg-1",
        title="Test drawing",
        number=None,
        revision=None,
        default_unit=Unit.MILLIMETER,
        scale=None,
        features=[feature],
        datums=[],
    )

    findings = DuplicateDatumReferencesRule().check(drawing)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "fcf-duplicate-datum-references"
    assert finding.feature_id == "feat-1"
    assert finding.fcf_id == "fcf-bad"
    assert "A" in finding.message

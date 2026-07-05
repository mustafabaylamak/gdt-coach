"""PASS/FAIL tests for FlatnessNoDatumReferencesRule."""

from gdt_coach.models import Drawing
from gdt_coach.models.enums import GeometricCharacteristic
from gdt_coach.rules.checks.flatness_no_datum_references import FlatnessNoDatumReferencesRule

from .conftest import make_drawing_with_fcf, make_fcf


def test_pass_flatness_without_datums() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.FLATNESS, datum_labels=[])
    drawing = make_drawing_with_fcf(fcf)

    findings = FlatnessNoDatumReferencesRule().check(drawing)

    assert findings == []


def test_pass_non_flatness_with_datums_is_ignored() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, datum_labels=["A"])
    drawing = make_drawing_with_fcf(fcf)

    findings = FlatnessNoDatumReferencesRule().check(drawing)

    assert findings == []


def test_pass_empty_drawing() -> None:
    findings = FlatnessNoDatumReferencesRule().check(Drawing(id="dwg-empty", title="Empty"))

    assert findings == []


def test_fail_flatness_with_one_datum() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.FLATNESS, datum_labels=["A"])
    drawing = make_drawing_with_fcf(fcf, feature_id="feat-1")

    findings = FlatnessNoDatumReferencesRule().check(drawing)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "flatness-no-datum-references"
    assert finding.feature_id == "feat-1"
    assert finding.fcf_id == fcf.id
    assert "A" in finding.message


def test_fail_flatness_with_multiple_datums_is_one_finding() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.FLATNESS, datum_labels=["A", "B"])
    drawing = make_drawing_with_fcf(fcf)

    findings = FlatnessNoDatumReferencesRule().check(drawing)

    assert len(findings) == 1

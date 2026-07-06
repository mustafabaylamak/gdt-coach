"""PASS/FAIL tests for DatumReferenceMustBeDefinedRule (SYN.003)."""

from gdt_coach.models import Datum, Drawing
from gdt_coach.models.enums import DatumFeatureType, GeometricCharacteristic
from gdt_coach.rules.checks.datum_reference_must_be_defined import (
    DatumReferenceMustBeDefinedRule,
)

from .conftest import make_drawing_with_fcf, make_fcf


def _datum(label: str) -> Datum:
    return Datum(label=label, feature_type=DatumFeatureType.PLANE)


def test_pass_no_datum_references() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.FLATNESS, datum_labels=[])
    drawing = make_drawing_with_fcf(fcf)

    findings = DatumReferenceMustBeDefinedRule().check(drawing)

    assert findings == []


def test_pass_all_referenced_datums_defined() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, datum_labels=["A", "B"])
    drawing = make_drawing_with_fcf(fcf, datums=[_datum("A"), _datum("B"), _datum("C")])

    findings = DatumReferenceMustBeDefinedRule().check(drawing)

    assert findings == []


def test_pass_empty_drawing() -> None:
    findings = DatumReferenceMustBeDefinedRule().check(Drawing(id="dwg-empty", title="Empty"))

    assert findings == []


def test_fail_referenced_datum_not_defined() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, datum_labels=["A"])
    drawing = make_drawing_with_fcf(fcf, feature_id="feat-1")  # no datums defined at all

    findings = DatumReferenceMustBeDefinedRule().check(drawing)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "datum-reference-must-be-defined"
    assert finding.feature_id == "feat-1"
    assert finding.fcf_id == fcf.id
    assert "A" in finding.message


def test_fail_some_referenced_datums_undefined() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, datum_labels=["A", "B", "C"])
    drawing = make_drawing_with_fcf(fcf, datums=[_datum("A")])

    findings = DatumReferenceMustBeDefinedRule().check(drawing)

    assert len(findings) == 1
    assert str(["B", "C"]) in findings[0].message


def test_fail_undefined_datum_reported_once_per_fcf_not_per_label() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, datum_labels=["X", "Y"])
    drawing = make_drawing_with_fcf(fcf)

    findings = DatumReferenceMustBeDefinedRule().check(drawing)

    assert len(findings) == 1

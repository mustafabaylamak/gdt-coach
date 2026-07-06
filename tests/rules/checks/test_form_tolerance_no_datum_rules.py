"""Parametrized PASS/FAIL tests shared by the "form tolerance cannot
reference a datum" rules (flatness, straightness, circularity,
cylindricity -- all four ASME Y14.5 form tolerances).

All four rules check the exact same shape: a specific
`GeometricCharacteristic` must never carry datum references. Rather
than four near-identical test files (one per rule), this module runs
one set of test functions against all of them via
`pytest.mark.parametrize`. Adding another form-tolerance-no-datum rule
means adding one entry to `_CASES`, not a new test file -- this is
exactly the reuse this module was built for in Sprint 6, now exercised
by Sprint 7's circularity/cylindricity rules (the FORM.001 extension).
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from gdt_coach.models import Drawing
from gdt_coach.models.enums import GeometricCharacteristic
from gdt_coach.rules.base import Rule
from gdt_coach.rules.checks.circularity_no_datum_references import (
    CircularityNoDatumReferencesRule,
)
from gdt_coach.rules.checks.cylindricity_no_datum_references import (
    CylindricityNoDatumReferencesRule,
)
from gdt_coach.rules.checks.flatness_no_datum_references import FlatnessNoDatumReferencesRule
from gdt_coach.rules.checks.straightness_no_datum_references import (
    StraightnessNoDatumReferencesRule,
)

from .conftest import make_drawing_with_fcf, make_fcf


@dataclass(frozen=True)
class _NoDatumRuleCase:
    rule_cls: type[Rule]
    characteristic: GeometricCharacteristic
    rule_id: str


_CASES = [
    _NoDatumRuleCase(
        rule_cls=FlatnessNoDatumReferencesRule,
        characteristic=GeometricCharacteristic.FLATNESS,
        rule_id="flatness-no-datum-references",
    ),
    _NoDatumRuleCase(
        rule_cls=StraightnessNoDatumReferencesRule,
        characteristic=GeometricCharacteristic.STRAIGHTNESS,
        rule_id="straightness-no-datum-references",
    ),
    _NoDatumRuleCase(
        rule_cls=CircularityNoDatumReferencesRule,
        characteristic=GeometricCharacteristic.CIRCULARITY,
        rule_id="circularity-no-datum-references",
    ),
    _NoDatumRuleCase(
        rule_cls=CylindricityNoDatumReferencesRule,
        characteristic=GeometricCharacteristic.CYLINDRICITY,
        rule_id="cylindricity-no-datum-references",
    ),
]
_CASE_IDS = [case.rule_id for case in _CASES]


@pytest.mark.parametrize("case", _CASES, ids=_CASE_IDS)
def test_pass_without_datums(case: _NoDatumRuleCase) -> None:
    fcf = make_fcf(characteristic=case.characteristic, datum_labels=[])
    drawing = make_drawing_with_fcf(fcf)

    findings = case.rule_cls().check(drawing)

    assert findings == []


@pytest.mark.parametrize("case", _CASES, ids=_CASE_IDS)
def test_pass_other_characteristic_with_datums_is_ignored(case: _NoDatumRuleCase) -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.POSITION, datum_labels=["A"])
    drawing = make_drawing_with_fcf(fcf)

    findings = case.rule_cls().check(drawing)

    assert findings == []


@pytest.mark.parametrize("case", _CASES, ids=_CASE_IDS)
def test_pass_empty_drawing(case: _NoDatumRuleCase) -> None:
    findings = case.rule_cls().check(Drawing(id="dwg-empty", title="Empty"))

    assert findings == []


@pytest.mark.parametrize("case", _CASES, ids=_CASE_IDS)
def test_fail_with_one_datum(case: _NoDatumRuleCase) -> None:
    fcf = make_fcf(characteristic=case.characteristic, datum_labels=["A"])
    drawing = make_drawing_with_fcf(fcf, feature_id="feat-1")

    findings = case.rule_cls().check(drawing)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == case.rule_id
    assert finding.feature_id == "feat-1"
    assert finding.fcf_id == fcf.id
    assert "A" in finding.message


@pytest.mark.parametrize("case", _CASES, ids=_CASE_IDS)
def test_fail_with_multiple_datums_is_one_finding(case: _NoDatumRuleCase) -> None:
    fcf = make_fcf(characteristic=case.characteristic, datum_labels=["A", "B"])
    drawing = make_drawing_with_fcf(fcf)

    findings = case.rule_cls().check(drawing)

    assert len(findings) == 1

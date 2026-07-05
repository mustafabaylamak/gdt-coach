"""PASS/FAIL tests for ProjectedZoneRequiresPositionRule."""

from gdt_coach.models.enums import GeometricCharacteristic
from gdt_coach.rules.checks.projected_zone_requires_position import (
    ProjectedZoneRequiresPositionRule,
)

from .conftest import make_drawing_with_fcf, make_fcf, make_tolerance


def test_pass_position_with_projected_zone() -> None:
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.POSITION,
        datum_labels=["A"],
        tolerance=make_tolerance(projected_zone_height=10.0),
    )
    drawing = make_drawing_with_fcf(fcf)

    findings = ProjectedZoneRequiresPositionRule().check(drawing)

    assert findings == []


def test_pass_non_position_without_projected_zone() -> None:
    fcf = make_fcf(characteristic=GeometricCharacteristic.FLATNESS, datum_labels=[])
    drawing = make_drawing_with_fcf(fcf)

    findings = ProjectedZoneRequiresPositionRule().check(drawing)

    assert findings == []


def test_fail_projected_zone_on_non_position() -> None:
    fcf = make_fcf(
        characteristic=GeometricCharacteristic.PERPENDICULARITY,
        datum_labels=["A"],
        tolerance=make_tolerance(projected_zone_height=5.0),
    )
    drawing = make_drawing_with_fcf(fcf, feature_id="feat-2")

    findings = ProjectedZoneRequiresPositionRule().check(drawing)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "projected-zone-requires-position"
    assert finding.feature_id == "feat-2"
    assert "perpendicularity" in finding.message

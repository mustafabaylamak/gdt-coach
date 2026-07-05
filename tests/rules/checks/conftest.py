"""Shared drawing-building helpers for concrete rule check tests."""

from __future__ import annotations

from gdt_coach.models import Drawing, Feature, FeatureType
from gdt_coach.models.enums import GeometricCharacteristic
from gdt_coach.models.feature_control_frame import DatumReference, FeatureControlFrame
from gdt_coach.models.tolerance import Tolerance


def make_tolerance(
    *,
    upper: float = 0.1,
    lower: float = 0.1,
    projected_zone_height: float | None = None,
) -> Tolerance:
    return Tolerance(
        upper_deviation=upper,
        lower_deviation=lower,
        projected_zone_height=projected_zone_height,
    )


def make_fcf(
    *,
    fcf_id: str = "fcf-1",
    characteristic: GeometricCharacteristic = GeometricCharacteristic.FLATNESS,
    datum_labels: list[str] | None = None,
    tolerance: Tolerance | None = None,
) -> FeatureControlFrame:
    return FeatureControlFrame(
        id=fcf_id,
        characteristic=characteristic,
        tolerance=tolerance if tolerance is not None else make_tolerance(),
        datum_references=[DatumReference(datum_label=label) for label in (datum_labels or [])],
    )


def make_drawing_with_fcf(fcf: FeatureControlFrame, *, feature_id: str = "feat-1") -> Drawing:
    feature = Feature(id=feature_id, feature_type=FeatureType.HOLE, feature_control_frames=[fcf])
    return Drawing(id="dwg-1", title="Test drawing", features=[feature])

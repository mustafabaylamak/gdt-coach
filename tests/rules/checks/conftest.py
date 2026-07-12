"""Shared drawing-building helpers for concrete rule check tests."""

from __future__ import annotations

from gdt_coach.models import Datum, Dimension, Drawing, Feature, FeatureType
from gdt_coach.models.enums import DimensionType, GeometricCharacteristic, MaterialCondition, Unit
from gdt_coach.models.feature_control_frame import DatumReference, FeatureControlFrame
from gdt_coach.models.tolerance import Tolerance


def make_tolerance(
    *,
    upper: float = 0.1,
    lower: float = 0.1,
    material_condition: MaterialCondition = MaterialCondition.RFS,
    projected_zone_height: float | None = None,
) -> Tolerance:
    return Tolerance(
        upper_deviation=upper,
        lower_deviation=lower,
        material_condition=material_condition,
        projected_zone_height=projected_zone_height,
    )


def make_fcf(
    *,
    fcf_id: str = "fcf-1",
    characteristic: GeometricCharacteristic = GeometricCharacteristic.FLATNESS,
    datum_labels: list[str] | None = None,
    datum_material_conditions: dict[str, MaterialCondition] | None = None,
    tolerance: Tolerance | None = None,
    related_dimension_ids: list[str] | None = None,
) -> FeatureControlFrame:
    conditions = datum_material_conditions or {}
    return FeatureControlFrame(
        id=fcf_id,
        characteristic=characteristic,
        tolerance=tolerance if tolerance is not None else make_tolerance(),
        datum_references=[
            DatumReference(
                datum_label=label,
                material_condition=conditions.get(label, MaterialCondition.RFS),
            )
            for label in (datum_labels or [])
        ],
        related_dimension_ids=related_dimension_ids or [],
    )


def make_dimension(
    *,
    dimension_id: str = "dim-1",
    dimension_type: DimensionType = DimensionType.LINEAR,
    nominal_value: float = 10.0,
    unit: Unit = Unit.MILLIMETER,
    tolerance: Tolerance | None = None,
    is_reference: bool = False,
) -> Dimension:
    return Dimension(
        id=dimension_id,
        dimension_type=dimension_type,
        nominal_value=nominal_value,
        unit=unit,
        tolerance=tolerance,
        is_reference=is_reference,
    )


def make_drawing_with_fcf(
    fcf: FeatureControlFrame,
    *,
    feature_id: str = "feat-1",
    feature_of_size: bool = False,
    datums: list[Datum] | None = None,
    dimensions: list[Dimension] | None = None,
) -> Drawing:
    feature = Feature(
        id=feature_id,
        feature_type=FeatureType.HOLE,
        feature_of_size=feature_of_size,
        dimensions=dimensions or [],
        feature_control_frames=[fcf],
    )
    return Drawing(id="dwg-1", title="Test drawing", features=[feature], datums=datums or [])

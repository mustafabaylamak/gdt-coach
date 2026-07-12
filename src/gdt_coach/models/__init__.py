"""Domain model layer for gdt-coach.

Pydantic models describing the GD&T domain: drawings, features, datums,
dimensions, feature control frames, and tolerances. This layer is
intentionally inert — no parsing and no rule engine live here, only
data shape and the minimal validation needed to reject structurally
impossible data.
"""

from gdt_coach.models.datum import Datum
from gdt_coach.models.dimension import Dimension
from gdt_coach.models.drawing import Drawing
from gdt_coach.models.enums import (
    DatumFeatureType,
    DimensionRole,
    DimensionType,
    FeatureType,
    GeometricCharacteristic,
    MaterialCondition,
    ToleranceZoneShape,
    Unit,
)
from gdt_coach.models.feature import Feature
from gdt_coach.models.feature_control_frame import DatumReference, FeatureControlFrame
from gdt_coach.models.tolerance import Tolerance

__all__ = [
    "Datum",
    "DatumFeatureType",
    "DatumReference",
    "Dimension",
    "DimensionRole",
    "DimensionType",
    "Drawing",
    "Feature",
    "FeatureControlFrame",
    "FeatureType",
    "GeometricCharacteristic",
    "MaterialCondition",
    "Tolerance",
    "ToleranceZoneShape",
    "Unit",
]

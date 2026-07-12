"""Enumerations for GD&T domain concepts (ASME Y14.5)."""

from __future__ import annotations

from enum import StrEnum


class GeometricCharacteristic(StrEnum):
    """The fourteen geometric characteristic symbols defined by ASME Y14.5."""

    STRAIGHTNESS = "straightness"
    FLATNESS = "flatness"
    CIRCULARITY = "circularity"
    CYLINDRICITY = "cylindricity"
    PROFILE_OF_A_LINE = "profile_of_a_line"
    PROFILE_OF_A_SURFACE = "profile_of_a_surface"
    ANGULARITY = "angularity"
    PERPENDICULARITY = "perpendicularity"
    PARALLELISM = "parallelism"
    POSITION = "position"
    CONCENTRICITY = "concentricity"
    SYMMETRY = "symmetry"
    CIRCULAR_RUNOUT = "circular_runout"
    TOTAL_RUNOUT = "total_runout"


class MaterialCondition(StrEnum):
    """Material condition modifier applied to a tolerance or datum reference."""

    RFS = "rfs"
    MMC = "mmc"
    LMC = "lmc"


class DatumFeatureType(StrEnum):
    """The geometric type a datum feature simulates or is derived from."""

    PLANE = "plane"
    AXIS = "axis"
    POINT = "point"
    LINE = "line"
    CENTER_PLANE = "center_plane"


class FeatureType(StrEnum):
    """The kind of physical feature a part carries."""

    PLANE = "plane"
    CYLINDER = "cylinder"
    HOLE = "hole"
    PIN = "pin"
    SLOT = "slot"
    WIDTH = "width"
    SPHERE = "sphere"
    CONE = "cone"
    SURFACE = "surface"
    EDGE = "edge"
    PATTERN = "pattern"


class DimensionType(StrEnum):
    """The kind of value a dimension expresses."""

    LINEAR = "linear"
    ANGULAR = "angular"
    DIAMETER = "diameter"
    RADIUS = "radius"
    CHAMFER = "chamfer"
    ARC_LENGTH = "arc_length"


class DimensionRole(StrEnum):
    """What a dimension is used for on the drawing (independent of its type/shape).

    Deliberately excludes a REFERENCE member: ``Dimension.is_reference``
    is the existing, separate signal for informational/reference
    dimensions, and duplicating that concept here would create two
    fields that could disagree about the same fact.
    """

    SIZE = "size"
    LOCATION = "location"
    ORIENTATION = "orientation"
    OTHER = "other"


class ToleranceZoneShape(StrEnum):
    """The geometric shape of a tolerance zone."""

    LINEAR = "linear"
    CYLINDRICAL = "cylindrical"
    SPHERICAL = "spherical"
    TOTAL_WIDTH = "total_width"


class Unit(StrEnum):
    """Unit of measure for a dimension's nominal value."""

    MILLIMETER = "mm"
    INCH = "in"
    DEGREE = "deg"

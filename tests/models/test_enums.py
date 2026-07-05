"""Tests for GD&T enumerations."""

from gdt_coach.models.enums import (
    DatumFeatureType,
    DimensionType,
    FeatureType,
    GeometricCharacteristic,
    MaterialCondition,
    ToleranceZoneShape,
    Unit,
)


def test_geometric_characteristic_has_fourteen_symbols() -> None:
    assert len(GeometricCharacteristic) == 14


def test_geometric_characteristic_members_are_unique() -> None:
    values = [member.value for member in GeometricCharacteristic]

    assert len(values) == len(set(values))


def test_material_condition_members() -> None:
    assert {member.value for member in MaterialCondition} == {"rfs", "mmc", "lmc"}


def test_datum_feature_type_members() -> None:
    assert {member.value for member in DatumFeatureType} == {
        "plane",
        "axis",
        "point",
        "line",
        "center_plane",
    }


def test_feature_type_members() -> None:
    assert {member.value for member in FeatureType} == {
        "plane",
        "cylinder",
        "hole",
        "pin",
        "slot",
        "width",
        "sphere",
        "cone",
        "surface",
        "edge",
        "pattern",
    }


def test_dimension_type_members() -> None:
    assert {member.value for member in DimensionType} == {
        "linear",
        "angular",
        "diameter",
        "radius",
        "chamfer",
        "arc_length",
    }


def test_tolerance_zone_shape_members() -> None:
    assert {member.value for member in ToleranceZoneShape} == {
        "linear",
        "cylindrical",
        "spherical",
        "total_width",
    }


def test_unit_members() -> None:
    assert {member.value for member in Unit} == {"mm", "in", "deg"}


def test_str_enum_compares_equal_to_plain_string() -> None:
    assert GeometricCharacteristic.FLATNESS == "flatness"
    assert Unit.MILLIMETER == "mm"

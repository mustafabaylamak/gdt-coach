"""Tests for the YAML ingest loader."""

from pathlib import Path

import pytest

from gdt_coach.ingest.exceptions import DrawingValidationError, YamlParseError
from gdt_coach.ingest.yaml_loader import (
    load_drawing_from_yaml_file,
    load_drawing_from_yaml_string,
)
from gdt_coach.models.enums import (
    DatumFeatureType,
    DimensionType,
    FeatureType,
    GeometricCharacteristic,
    MaterialCondition,
    ToleranceZoneShape,
    Unit,
)

_MINIMAL_YAML = """
id: dwg-min
title: Minimal drawing
"""

_FULL_YAML = """
id: dwg-full
title: Full drawing
number: DWG-9
revision: C
default_unit: in
scale: "2:1"

datums:
  - label: A
    feature_type: plane
    material_condition: mmc

features:
  - id: feat-1
    feature_type: hole
    name: Test hole
    quantity: 2
    feature_of_size: true
    dimensions:
      - id: dim-1
        dimension_type: diameter
        nominal_value: 8.0
        unit: in
        tolerance:
          upper_deviation: 0.02
          lower_deviation: 0.01
    feature_control_frames:
      - id: fcf-1
        characteristic: position
        tolerance:
          upper_deviation: 0.3
          lower_deviation: 0.3
          zone_shape: cylindrical
          material_condition: mmc
          projected_zone_height: 5.0
        datum_references:
          - datum_label: A
            material_condition: mmc
        all_around: true
"""


def test_minimal_yaml_loads() -> None:
    drawing = load_drawing_from_yaml_string(_MINIMAL_YAML)

    assert drawing.id == "dwg-min"
    assert drawing.title == "Minimal drawing"
    assert drawing.default_unit == Unit.MILLIMETER
    assert drawing.features == []
    assert drawing.datums == []


def test_full_yaml_builds_the_whole_nested_tree() -> None:
    drawing = load_drawing_from_yaml_string(_FULL_YAML)

    assert drawing.number == "DWG-9"
    assert drawing.revision == "C"
    assert drawing.default_unit == Unit.INCH
    assert drawing.scale == "2:1"

    assert len(drawing.datums) == 1
    datum = drawing.datums[0]
    assert datum.label == "A"
    assert datum.feature_type == DatumFeatureType.PLANE
    assert datum.material_condition == MaterialCondition.MMC

    assert len(drawing.features) == 1
    feature = drawing.features[0]
    assert feature.feature_type == FeatureType.HOLE
    assert feature.quantity == 2
    assert feature.feature_of_size is True

    assert len(feature.dimensions) == 1
    dimension = feature.dimensions[0]
    assert dimension.dimension_type == DimensionType.DIAMETER
    assert dimension.nominal_value == 8.0
    assert dimension.unit == Unit.INCH
    assert dimension.tolerance is not None
    assert dimension.tolerance.upper_deviation == 0.02
    assert dimension.tolerance.lower_deviation == 0.01

    assert len(feature.feature_control_frames) == 1
    fcf = feature.feature_control_frames[0]
    assert fcf.characteristic == GeometricCharacteristic.POSITION
    assert fcf.tolerance.zone_shape == ToleranceZoneShape.CYLINDRICAL
    assert fcf.tolerance.material_condition == MaterialCondition.MMC
    assert fcf.tolerance.projected_zone_height == 5.0
    assert fcf.all_around is True
    assert len(fcf.datum_references) == 1
    assert fcf.datum_references[0].datum_label == "A"
    assert fcf.datum_references[0].material_condition == MaterialCondition.MMC


def test_empty_yaml_document_raises_parse_error() -> None:
    with pytest.raises(YamlParseError, match="empty"):
        load_drawing_from_yaml_string("")


def test_yaml_that_is_not_a_mapping_raises_parse_error() -> None:
    with pytest.raises(YamlParseError, match="mapping"):
        load_drawing_from_yaml_string("- 1\n- 2\n")


def test_malformed_yaml_raises_parse_error() -> None:
    with pytest.raises(YamlParseError, match="invalid YAML"):
        load_drawing_from_yaml_string("id: [unclosed")


def test_missing_required_field_raises_validation_error() -> None:
    with pytest.raises(DrawingValidationError):
        load_drawing_from_yaml_string("id: dwg-1\n")  # missing title


def test_unknown_field_raises_validation_error() -> None:
    with pytest.raises(DrawingValidationError):
        load_drawing_from_yaml_string("id: dwg-1\ntitle: X\nbogus_field: 1\n")


def test_invalid_enum_value_raises_validation_error() -> None:
    yaml_text = """
id: dwg-1
title: X
features:
  - id: feat-1
    feature_type: not_a_real_feature_type
"""
    with pytest.raises(DrawingValidationError):
        load_drawing_from_yaml_string(yaml_text)


def test_impossible_domain_data_still_rejected_through_yaml() -> None:
    """The domain model's own validators still run for YAML-sourced data."""
    yaml_text = """
id: dwg-1
title: X
features:
  - id: feat-1
    feature_type: hole
    feature_control_frames:
      - id: fcf-1
        characteristic: position
        tolerance:
          upper_deviation: -0.1
          lower_deviation: 0.1
"""
    with pytest.raises(DrawingValidationError):
        load_drawing_from_yaml_string(yaml_text)


def test_source_name_appears_in_error_message() -> None:
    with pytest.raises(YamlParseError, match="my-source"):
        load_drawing_from_yaml_string("", source_name="my-source")


def test_load_from_file_reads_and_parses(tmp_path: Path) -> None:
    yaml_file = tmp_path / "drawing.yaml"
    yaml_file.write_text(_MINIMAL_YAML, encoding="utf-8")

    drawing = load_drawing_from_yaml_file(yaml_file)

    assert drawing.id == "dwg-min"


def test_load_from_file_accepts_string_path(tmp_path: Path) -> None:
    yaml_file = tmp_path / "drawing.yaml"
    yaml_file.write_text(_MINIMAL_YAML, encoding="utf-8")

    drawing = load_drawing_from_yaml_file(str(yaml_file))

    assert drawing.id == "dwg-min"


def test_load_from_file_error_includes_file_path(tmp_path: Path) -> None:
    yaml_file = tmp_path / "bad.yaml"
    yaml_file.write_text("", encoding="utf-8")

    with pytest.raises(YamlParseError, match=r"bad\.yaml"):
        load_drawing_from_yaml_file(yaml_file)

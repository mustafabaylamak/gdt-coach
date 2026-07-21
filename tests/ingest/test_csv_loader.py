"""Tests for the narrow CSV ingest loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from gdt_coach.ingest.csv_loader import (
    load_drawing_from_csv_file,
    load_drawing_from_csv_string,
)
from gdt_coach.ingest.exceptions import CsvParseError, DrawingValidationError
from gdt_coach.models.enums import (
    DimensionRole,
    DimensionType,
    FeatureType,
    GeometricCharacteristic,
    MaterialCondition,
    Unit,
)

_MINIMAL_HEADER = "drawing_id,drawing_title,feature_id,feature_type"

_DIMENSION_HEADERS = (
    "dimension_id,dimension_type,dimension_nominal_value,dimension_unit,"
    "dimension_tolerance_upper,dimension_tolerance_lower,dimension_is_reference,dimension_role"
)
_FCF_HEADERS = (
    "fcf_id,fcf_characteristic,fcf_tolerance_upper,fcf_tolerance_lower,"
    "fcf_zone_shape,fcf_material_condition,fcf_projected_zone_height,fcf_datum_refs"
)


# --- valid parsing ------------------------------------------------------------


def test_valid_minimal_drawing() -> None:
    csv_text = f"{_MINIMAL_HEADER}\ndwg-1,Minimal,feat-1,hole\n"

    drawing = load_drawing_from_csv_string(csv_text)

    assert drawing.id == "dwg-1"
    assert drawing.title == "Minimal"
    assert drawing.default_unit == Unit.MILLIMETER
    assert drawing.datums == []
    assert len(drawing.features) == 1
    feature = drawing.features[0]
    assert feature.id == "feat-1"
    assert feature.feature_type == FeatureType.HOLE
    assert feature.quantity == 1
    assert feature.feature_of_size is False
    assert feature.dimensions == []
    assert feature.feature_control_frames == []


def test_feature_name_is_carried_through_when_set() -> None:
    csv_text = f"{_MINIMAL_HEADER},feature_name\ndwg-1,T,feat-1,hole,Mounting hole\n"

    drawing = load_drawing_from_csv_string(csv_text)

    assert drawing.features[0].name == "Mounting hole"


def test_dimension_role_defaults_when_blank() -> None:
    csv_text = (
        f"{_MINIMAL_HEADER},{_DIMENSION_HEADERS}\ndwg-1,T,feat-1,hole,dim-1,diameter,10.0,mm,,,,\n"
    )

    drawing = load_drawing_from_csv_string(csv_text)

    assert drawing.features[0].dimensions[0].role == DimensionRole.OTHER


def test_full_drawing_level_metadata() -> None:
    header = (
        "drawing_id,drawing_title,drawing_number,drawing_revision,"
        "drawing_default_unit,drawing_scale,feature_id,feature_type"
    )
    csv_text = f"{header}\ndwg-1,Full,DWG-9,B,in,2:1,feat-1,hole\n"

    drawing = load_drawing_from_csv_string(csv_text)

    assert drawing.number == "DWG-9"
    assert drawing.revision == "B"
    assert drawing.default_unit == Unit.INCH
    assert drawing.scale == "2:1"


def test_blank_optional_dimension_is_absent() -> None:
    csv_text = f"{_MINIMAL_HEADER},{_DIMENSION_HEADERS}\ndwg-1,T,feat-1,hole,,,,,,,,\n"

    drawing = load_drawing_from_csv_string(csv_text)

    assert drawing.features[0].dimensions == []


def test_blank_optional_fcf_is_absent() -> None:
    csv_text = f"{_MINIMAL_HEADER},{_FCF_HEADERS}\ndwg-1,T,feat-1,hole,,,,,,,,\n"

    drawing = load_drawing_from_csv_string(csv_text)

    assert drawing.features[0].feature_control_frames == []


def test_valid_dimension_fully_specified() -> None:
    csv_text = (
        f"{_MINIMAL_HEADER},{_DIMENSION_HEADERS}\n"
        "dwg-1,T,feat-1,hole,dim-1,diameter,10.0,mm,0.05,0.05,false,size\n"
    )

    drawing = load_drawing_from_csv_string(csv_text)

    dimension = drawing.features[0].dimensions[0]
    assert dimension.id == "dim-1"
    assert dimension.dimension_type == DimensionType.DIAMETER
    assert dimension.nominal_value == 10.0
    assert dimension.unit == Unit.MILLIMETER
    assert dimension.tolerance is not None
    assert dimension.tolerance.upper_deviation == 0.05
    assert dimension.tolerance.lower_deviation == 0.05
    assert dimension.is_reference is False
    assert dimension.role == DimensionRole.SIZE


def test_valid_reference_dimension_without_tolerance() -> None:
    csv_text = (
        f"{_MINIMAL_HEADER},{_DIMENSION_HEADERS}\n"
        "dwg-1,T,feat-1,hole,dim-1,diameter,10.0,mm,,,true,size\n"
    )

    drawing = load_drawing_from_csv_string(csv_text)

    dimension = drawing.features[0].dimensions[0]
    assert dimension.is_reference is True
    assert dimension.is_basic is True


def test_valid_basic_dimension_without_tolerance() -> None:
    csv_text = (
        f"{_MINIMAL_HEADER},{_DIMENSION_HEADERS}\n"
        "dwg-1,T,feat-1,hole,dim-1,linear,40.0,mm,,,,location\n"
    )

    drawing = load_drawing_from_csv_string(csv_text)

    dimension = drawing.features[0].dimensions[0]
    assert dimension.is_basic is True
    assert dimension.role == DimensionRole.LOCATION


def test_valid_fcf_fully_specified() -> None:
    csv_text = (
        f"{_MINIMAL_HEADER},{_FCF_HEADERS}\n"
        "dwg-1,T,feat-1,hole,fcf-1,position,0.25,0.25,cylindrical,mmc,5.0,A;B\n"
    )

    drawing = load_drawing_from_csv_string(csv_text)

    fcf = drawing.features[0].feature_control_frames[0]
    assert fcf.id == "fcf-1"
    assert fcf.characteristic == GeometricCharacteristic.POSITION
    assert fcf.tolerance.upper_deviation == 0.25
    assert fcf.tolerance.lower_deviation == 0.25
    assert fcf.tolerance.material_condition == MaterialCondition.MMC
    assert fcf.tolerance.projected_zone_height == 5.0
    assert [ref.datum_label for ref in fcf.datum_references] == ["A", "B"]


def test_semicolon_delimited_datum_references() -> None:
    csv_text = (
        f"{_MINIMAL_HEADER},{_FCF_HEADERS}\ndwg-1,T,feat-1,hole,fcf-1,flatness,0.1,0.1,,,,A;B;C\n"
    )

    drawing = load_drawing_from_csv_string(csv_text)

    fcf = drawing.features[0].feature_control_frames[0]
    assert [ref.datum_label for ref in fcf.datum_references] == ["A", "B", "C"]
    assert all(ref.material_condition == MaterialCondition.RFS for ref in fcf.datum_references)


def test_single_datum_reference_no_delimiter_needed() -> None:
    csv_text = (
        f"{_MINIMAL_HEADER},{_FCF_HEADERS}\ndwg-1,T,feat-1,hole,fcf-1,flatness,0.1,0.1,,,,A\n"
    )

    drawing = load_drawing_from_csv_string(csv_text)

    assert [
        ref.datum_label for ref in drawing.features[0].feature_control_frames[0].datum_references
    ] == ["A"]


# --- CSV-contract errors (CsvParseError) --------------------------------------


def test_empty_file_raises() -> None:
    with pytest.raises(CsvParseError, match="empty"):
        load_drawing_from_csv_string("")


def test_headers_only_no_data_rows_raises() -> None:
    with pytest.raises(CsvParseError, match="no data rows"):
        load_drawing_from_csv_string(f"{_MINIMAL_HEADER}\n")


def test_missing_required_headers_raises() -> None:
    with pytest.raises(CsvParseError, match="missing required CSV header"):
        load_drawing_from_csv_string("feature_id,feature_type\nfeat-1,hole\n")


def test_unknown_header_raises() -> None:
    with pytest.raises(CsvParseError, match="unknown CSV header"):
        load_drawing_from_csv_string(f"{_MINIMAL_HEADER},bogus_column\ndwg-1,T,feat-1,hole,x\n")


def test_inconsistent_drawing_metadata_across_rows_raises() -> None:
    csv_text = f"{_MINIMAL_HEADER}\ndwg-1,Title One,feat-1,hole\ndwg-1,Title Two,feat-2,hole\n"

    with pytest.raises(CsvParseError, match="does not match the first data row"):
        load_drawing_from_csv_string(csv_text)


def test_inconsistent_drawing_id_across_rows_raises() -> None:
    csv_text = f"{_MINIMAL_HEADER}\ndwg-1,T,feat-1,hole\ndwg-2,T,feat-2,hole\n"

    with pytest.raises(CsvParseError, match="does not match the first data row"):
        load_drawing_from_csv_string(csv_text)


def test_malformed_numeric_value_raises() -> None:
    csv_text = (
        f"{_MINIMAL_HEADER},{_DIMENSION_HEADERS}\n"
        "dwg-1,T,feat-1,hole,dim-1,diameter,not-a-number,mm,,,,\n"
    )

    with pytest.raises(CsvParseError, match="not a valid number"):
        load_drawing_from_csv_string(csv_text)


def test_malformed_tolerance_numeric_value_raises() -> None:
    csv_text = (
        f"{_MINIMAL_HEADER},{_FCF_HEADERS}\ndwg-1,T,feat-1,hole,fcf-1,position,oops,0.1,,,,\n"
    )

    with pytest.raises(CsvParseError, match="not a valid number"):
        load_drawing_from_csv_string(csv_text)


def test_malformed_boolean_value_raises() -> None:
    csv_text = f"{_MINIMAL_HEADER},feature_of_size\ndwg-1,T,feat-1,hole,maybe\n"

    with pytest.raises(CsvParseError, match="not a valid boolean"):
        load_drawing_from_csv_string(csv_text)


def test_malformed_dimension_is_reference_boolean_raises() -> None:
    csv_text = (
        f"{_MINIMAL_HEADER},{_DIMENSION_HEADERS}\n"
        "dwg-1,T,feat-1,hole,dim-1,diameter,10.0,mm,,,not-a-bool,\n"
    )

    with pytest.raises(CsvParseError, match="not a valid boolean"):
        load_drawing_from_csv_string(csv_text)


def test_malformed_feature_quantity_integer_raises() -> None:
    csv_text = f"{_MINIMAL_HEADER},feature_quantity\ndwg-1,T,feat-1,hole,many\n"

    with pytest.raises(CsvParseError, match="not a valid integer"):
        load_drawing_from_csv_string(csv_text)


def test_partial_dimension_fields_missing_type_raises() -> None:
    csv_text = f"{_MINIMAL_HEADER},{_DIMENSION_HEADERS}\ndwg-1,T,feat-1,hole,dim-1,,10.0,mm,,,,\n"

    with pytest.raises(CsvParseError, match="missing required field"):
        load_drawing_from_csv_string(csv_text)


def test_partial_dimension_tolerance_only_upper_raises() -> None:
    csv_text = (
        f"{_MINIMAL_HEADER},{_DIMENSION_HEADERS}\n"
        "dwg-1,T,feat-1,hole,dim-1,diameter,10.0,mm,0.05,,,\n"
    )

    with pytest.raises(CsvParseError, match="partially specified"):
        load_drawing_from_csv_string(csv_text)


def test_dimension_fields_set_without_dimension_id_raises() -> None:
    csv_text = (
        f"{_MINIMAL_HEADER},{_DIMENSION_HEADERS}\ndwg-1,T,feat-1,hole,,diameter,10.0,mm,,,,\n"
    )

    with pytest.raises(CsvParseError, match="dimension_id"):
        load_drawing_from_csv_string(csv_text)


def test_partial_fcf_fields_missing_characteristic_raises() -> None:
    csv_text = f"{_MINIMAL_HEADER},{_FCF_HEADERS}\ndwg-1,T,feat-1,hole,fcf-1,,0.1,0.1,,,,\n"

    with pytest.raises(CsvParseError, match="missing required field"):
        load_drawing_from_csv_string(csv_text)


def test_partial_fcf_fields_missing_tolerance_lower_raises() -> None:
    csv_text = f"{_MINIMAL_HEADER},{_FCF_HEADERS}\ndwg-1,T,feat-1,hole,fcf-1,position,0.1,,,,,\n"

    with pytest.raises(CsvParseError, match="missing required field"):
        load_drawing_from_csv_string(csv_text)


def test_fcf_fields_set_without_fcf_id_raises() -> None:
    csv_text = f"{_MINIMAL_HEADER},{_FCF_HEADERS}\ndwg-1,T,feat-1,hole,,position,0.1,0.1,,,,\n"

    with pytest.raises(CsvParseError, match="fcf_id"):
        load_drawing_from_csv_string(csv_text)


def test_invalid_delimited_datum_references_empty_segment_raises() -> None:
    csv_text = (
        f"{_MINIMAL_HEADER},{_FCF_HEADERS}\ndwg-1,T,feat-1,hole,fcf-1,position,0.1,0.1,,,,A;;B\n"
    )

    with pytest.raises(CsvParseError, match="invalid delimited datum references"):
        load_drawing_from_csv_string(csv_text)


def test_invalid_delimited_datum_references_trailing_delimiter_raises() -> None:
    csv_text = (
        f"{_MINIMAL_HEADER},{_FCF_HEADERS}\ndwg-1,T,feat-1,hole,fcf-1,position,0.1,0.1,,,,A;\n"
    )

    with pytest.raises(CsvParseError, match="invalid delimited datum references"):
        load_drawing_from_csv_string(csv_text)


def test_blank_feature_id_or_type_raises() -> None:
    csv_text = f"{_MINIMAL_HEADER}\ndwg-1,T,,hole\n"

    with pytest.raises(CsvParseError, match="'feature_id' and 'feature_type' are required"):
        load_drawing_from_csv_string(csv_text)


def test_missing_drawing_id_or_title_on_all_rows_raises() -> None:
    csv_text = f"{_MINIMAL_HEADER}\n,T,feat-1,hole\n"

    with pytest.raises(CsvParseError, match="required"):
        load_drawing_from_csv_string(csv_text)


# --- domain-model errors (DrawingValidationError, reusing existing validators) -


def test_duplicate_feature_ids_raises_drawing_validation_error() -> None:
    csv_text = f"{_MINIMAL_HEADER}\ndwg-1,T,feat-1,hole\ndwg-1,T,feat-1,pin\n"

    with pytest.raises(DrawingValidationError):
        load_drawing_from_csv_string(csv_text)


def test_invalid_feature_type_enum_raises_drawing_validation_error() -> None:
    csv_text = f"{_MINIMAL_HEADER}\ndwg-1,T,feat-1,not_a_real_type\n"

    with pytest.raises(DrawingValidationError):
        load_drawing_from_csv_string(csv_text)


def test_invalid_characteristic_enum_raises_drawing_validation_error() -> None:
    csv_text = (
        f"{_MINIMAL_HEADER},{_FCF_HEADERS}\n"
        "dwg-1,T,feat-1,hole,fcf-1,not_a_real_characteristic,0.1,0.1,,,,\n"
    )

    with pytest.raises(DrawingValidationError):
        load_drawing_from_csv_string(csv_text)


def test_invalid_dimension_role_enum_raises_drawing_validation_error() -> None:
    csv_text = (
        f"{_MINIMAL_HEADER},{_DIMENSION_HEADERS}\n"
        "dwg-1,T,feat-1,hole,dim-1,diameter,10.0,mm,,,,not_a_real_role\n"
    )

    with pytest.raises(DrawingValidationError):
        load_drawing_from_csv_string(csv_text)


def test_malformed_datum_label_raises_drawing_validation_error() -> None:
    # lowercase datum labels fail DatumReference's own existing validator
    csv_text = (
        f"{_MINIMAL_HEADER},{_FCF_HEADERS}\ndwg-1,T,feat-1,hole,fcf-1,flatness,0.1,0.1,,,,a\n"
    )

    with pytest.raises(DrawingValidationError):
        load_drawing_from_csv_string(csv_text)


# --- source_name / file loading ------------------------------------------------


def test_source_name_appears_in_error_message() -> None:
    with pytest.raises(CsvParseError, match="my-source"):
        load_drawing_from_csv_string("", source_name="my-source")


def test_load_from_file_reads_and_parses(tmp_path: Path) -> None:
    csv_file = tmp_path / "drawing.csv"
    csv_file.write_text(f"{_MINIMAL_HEADER}\ndwg-1,T,feat-1,hole\n", encoding="utf-8")

    drawing = load_drawing_from_csv_file(csv_file)

    assert drawing.id == "dwg-1"


def test_load_from_file_accepts_string_path(tmp_path: Path) -> None:
    csv_file = tmp_path / "drawing.csv"
    csv_file.write_text(f"{_MINIMAL_HEADER}\ndwg-1,T,feat-1,hole\n", encoding="utf-8")

    drawing = load_drawing_from_csv_file(str(csv_file))

    assert drawing.id == "dwg-1"


def test_load_from_file_error_includes_file_path(tmp_path: Path) -> None:
    csv_file = tmp_path / "bad.csv"
    csv_file.write_text("", encoding="utf-8")

    with pytest.raises(CsvParseError, match=r"bad\.csv"):
        load_drawing_from_csv_file(csv_file)

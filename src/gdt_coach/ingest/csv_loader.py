"""CSV loader: turns a narrow, intentionally limited CSV contract into a Drawing.

This is purely a translation layer, like ``yaml_loader.py``: it parses
CSV rows into a plain dict and hands that to ``Drawing.model_validate``,
which already knows how to build the nested tree and enforce the domain
model's own validation. No GD&T semantics are added here.

**The CSV contract (Sprint 14) is deliberately narrow, not YAML-equivalent:**

- One CSV file represents exactly one ``Drawing``. Every row must
  repeat the same drawing-level columns (``drawing_id``, ``drawing_title``,
  and the optional ``drawing_number``/``drawing_revision``/
  ``drawing_default_unit``/``drawing_scale``); a mismatch across rows is
  a hard error, not a "last one wins" merge.
- One row represents exactly one ``Feature``.
- Each row may specify **zero or one** ``Dimension`` (columns prefixed
  ``dimension_``) and **zero or one** ``FeatureControlFrame`` (columns
  prefixed ``fcf_``). A blank ``dimension_id``/``fcf_id`` means that
  nested object is absent for this row.
- Datum references on an FCF are a single semicolon-delimited field
  (``fcf_datum_refs``, e.g. ``"A;B;C"``); every reference gets
  ``material_condition: rfs`` -- CSV cannot express a per-datum
  material condition modifier.

**Explicitly unsupported in Sprint 14** (rejected as an unknown/missing
header or simply inexpressible, never approximated):

- more than one Dimension or FeatureControlFrame per feature
- ``related_dimension_ids``
- composite/multi-segment feature control frames
- ``Datum`` declarations (a CSV-sourced ``Drawing`` always has
  ``datums == []``; any datum label referenced via ``fcf_datum_refs``
  will correctly be flagged as undefined by the existing
  ``datum-reference-must-be-defined`` rule -- that is expected, not a
  bug)
- the FCF boolean modifiers ``all_around``/``all_over``/``free_state``/
  ``statistical_tolerance`` (always ``False``)
- any geometry, or any relationship not explicitly stated in a column

Malformed or ambiguous input raises :class:`CsvParseError` (a CSV-contract
problem :class:`~gdt_coach.models.Drawing` has no way to know about) or
:class:`DrawingValidationError` (a domain-shape problem -- a bad enum
value, a duplicate feature id, a malformed datum label -- that
``Drawing``'s own validators already catch, so it is not re-implemented
here).
"""

from __future__ import annotations

import csv
import io
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from gdt_coach.ingest.exceptions import CsvParseError, DrawingValidationError
from gdt_coach.models import Drawing

_DRAWING_METADATA_HEADERS = (
    "drawing_id",
    "drawing_title",
    "drawing_number",
    "drawing_revision",
    "drawing_default_unit",
    "drawing_scale",
)
_FEATURE_HEADERS = (
    "feature_id",
    "feature_type",
    "feature_name",
    "feature_quantity",
    "feature_of_size",
)
_DIMENSION_HEADERS = (
    "dimension_id",
    "dimension_type",
    "dimension_nominal_value",
    "dimension_unit",
    "dimension_tolerance_upper",
    "dimension_tolerance_lower",
    "dimension_is_reference",
    "dimension_role",
)
_FCF_HEADERS = (
    "fcf_id",
    "fcf_characteristic",
    "fcf_tolerance_upper",
    "fcf_tolerance_lower",
    "fcf_zone_shape",
    "fcf_material_condition",
    "fcf_projected_zone_height",
    "fcf_datum_refs",
)

_ALL_HEADERS = frozenset(
    _DRAWING_METADATA_HEADERS + _FEATURE_HEADERS + _DIMENSION_HEADERS + _FCF_HEADERS
)
_REQUIRED_HEADERS = frozenset({"drawing_id", "drawing_title", "feature_id", "feature_type"})

_TRUE_VALUES = frozenset({"true", "1"})
_FALSE_VALUES = frozenset({"false", "0"})


def _get(row: dict[str, str], header: str) -> str:
    return (row.get(header) or "").strip()


def _parse_float(value: str, *, field: str, row_number: int) -> float:
    try:
        return float(value)
    except ValueError as error:
        raise CsvParseError(
            f"row {row_number}: {field!r} is not a valid number: {value!r}"
        ) from error


def _parse_int(value: str, *, field: str, row_number: int, default: int) -> int:
    if not value:
        return default
    try:
        return int(value)
    except ValueError as error:
        raise CsvParseError(
            f"row {row_number}: {field!r} is not a valid integer: {value!r}"
        ) from error


def _parse_bool(value: str, *, field: str, row_number: int, default: bool) -> bool:
    normalized = value.lower()
    if not normalized:
        return default
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    valid = sorted(_TRUE_VALUES | _FALSE_VALUES)
    raise CsvParseError(
        f"row {row_number}: {field!r} is not a valid boolean: {value!r} (expected {valid})"
    )


def _parse_datum_refs(raw: str, *, row_number: int) -> list[dict[str, str]]:
    if not raw:
        return []
    labels = [segment.strip() for segment in raw.split(";")]
    if any(not label for label in labels):
        raise CsvParseError(
            f"row {row_number}: invalid delimited datum references {raw!r} -- "
            "empty label between/around ';' separators"
        )
    return [{"datum_label": label} for label in labels]


def _parse_dimension(row: dict[str, str], row_number: int) -> dict[str, Any] | None:
    dimension_id = _get(row, "dimension_id")
    other_headers = _DIMENSION_HEADERS[1:]
    if not dimension_id:
        filled = [header for header in other_headers if _get(row, header)]
        if filled:
            raise CsvParseError(
                f"row {row_number}: dimension field(s) {filled} are set but "
                "'dimension_id' is blank -- a Dimension needs an id, or leave "
                "every dimension_* column blank to omit it"
            )
        return None

    dimension_type = _get(row, "dimension_type")
    unit = _get(row, "dimension_unit")
    nominal_raw = _get(row, "dimension_nominal_value")
    missing = [
        name
        for name, value in (
            ("dimension_type", dimension_type),
            ("dimension_unit", unit),
            ("dimension_nominal_value", nominal_raw),
        )
        if not value
    ]
    if missing:
        raise CsvParseError(
            f"row {row_number}: dimension {dimension_id!r} is missing required field(s): {missing}"
        )

    upper_raw = _get(row, "dimension_tolerance_upper")
    lower_raw = _get(row, "dimension_tolerance_lower")
    tolerance: dict[str, Any] | None = None
    if upper_raw or lower_raw:
        if not (upper_raw and lower_raw):
            raise CsvParseError(
                f"row {row_number}: dimension {dimension_id!r} has a partially specified "
                "tolerance -- dimension_tolerance_upper and dimension_tolerance_lower must "
                "both be set (toleranced) or both blank (basic dimension)"
            )
        tolerance = {
            "upper_deviation": _parse_float(
                upper_raw, field="dimension_tolerance_upper", row_number=row_number
            ),
            "lower_deviation": _parse_float(
                lower_raw, field="dimension_tolerance_lower", row_number=row_number
            ),
        }

    data: dict[str, Any] = {
        "id": dimension_id,
        "dimension_type": dimension_type,
        "nominal_value": _parse_float(
            nominal_raw, field="dimension_nominal_value", row_number=row_number
        ),
        "unit": unit,
        "is_reference": _parse_bool(
            _get(row, "dimension_is_reference"),
            field="dimension_is_reference",
            row_number=row_number,
            default=False,
        ),
    }
    if tolerance is not None:
        data["tolerance"] = tolerance
    role = _get(row, "dimension_role")
    if role:
        data["role"] = role
    return data


def _parse_fcf(row: dict[str, str], row_number: int) -> dict[str, Any] | None:
    fcf_id = _get(row, "fcf_id")
    other_headers = _FCF_HEADERS[1:]
    if not fcf_id:
        filled = [header for header in other_headers if _get(row, header)]
        if filled:
            raise CsvParseError(
                f"row {row_number}: fcf field(s) {filled} are set but 'fcf_id' is blank -- "
                "a FeatureControlFrame needs an id, or leave every fcf_* column blank to omit it"
            )
        return None

    characteristic = _get(row, "fcf_characteristic")
    upper_raw = _get(row, "fcf_tolerance_upper")
    lower_raw = _get(row, "fcf_tolerance_lower")
    missing = [
        name
        for name, value in (
            ("fcf_characteristic", characteristic),
            ("fcf_tolerance_upper", upper_raw),
            ("fcf_tolerance_lower", lower_raw),
        )
        if not value
    ]
    if missing:
        raise CsvParseError(
            f"row {row_number}: fcf {fcf_id!r} is missing required field(s): {missing}"
        )

    tolerance: dict[str, Any] = {
        "upper_deviation": _parse_float(
            upper_raw, field="fcf_tolerance_upper", row_number=row_number
        ),
        "lower_deviation": _parse_float(
            lower_raw, field="fcf_tolerance_lower", row_number=row_number
        ),
    }
    zone_shape = _get(row, "fcf_zone_shape")
    if zone_shape:
        tolerance["zone_shape"] = zone_shape
    material_condition = _get(row, "fcf_material_condition")
    if material_condition:
        tolerance["material_condition"] = material_condition
    projected_raw = _get(row, "fcf_projected_zone_height")
    if projected_raw:
        tolerance["projected_zone_height"] = _parse_float(
            projected_raw, field="fcf_projected_zone_height", row_number=row_number
        )

    return {
        "id": fcf_id,
        "characteristic": characteristic,
        "tolerance": tolerance,
        "datum_references": _parse_datum_refs(_get(row, "fcf_datum_refs"), row_number=row_number),
    }


def _parse_feature(row: dict[str, str], row_number: int) -> dict[str, Any]:
    feature_id = _get(row, "feature_id")
    feature_type = _get(row, "feature_type")
    if not feature_id or not feature_type:
        raise CsvParseError(f"row {row_number}: 'feature_id' and 'feature_type' are required")

    data: dict[str, Any] = {
        "id": feature_id,
        "feature_type": feature_type,
        "quantity": _parse_int(
            _get(row, "feature_quantity"),
            field="feature_quantity",
            row_number=row_number,
            default=1,
        ),
        "feature_of_size": _parse_bool(
            _get(row, "feature_of_size"),
            field="feature_of_size",
            row_number=row_number,
            default=False,
        ),
    }
    name = _get(row, "feature_name")
    if name:
        data["name"] = name

    dimension = _parse_dimension(row, row_number)
    if dimension is not None:
        data["dimensions"] = [dimension]

    fcf = _parse_fcf(row, row_number)
    if fcf is not None:
        data["feature_control_frames"] = [fcf]

    return data


def _validate_headers(fieldnames: Sequence[str] | None, text: str, source_name: str) -> None:
    if not text.strip() or not fieldnames:
        raise CsvParseError(f"{source_name}: CSV file is empty")

    unknown_headers = set(fieldnames) - _ALL_HEADERS
    if unknown_headers:
        raise CsvParseError(f"{source_name}: unknown CSV header(s): {sorted(unknown_headers)}")

    missing_headers = _REQUIRED_HEADERS - set(fieldnames)
    if missing_headers:
        raise CsvParseError(
            f"{source_name}: missing required CSV header(s): {sorted(missing_headers)}"
        )


def _parse_rows(
    rows: list[dict[str, str]], source_name: str
) -> tuple[tuple[str, ...], list[dict[str, Any]]]:
    """Parse every row into a Feature dict, checking drawing-level metadata stays consistent.

    Returns (drawing_metadata, features), where drawing_metadata is the
    raw (unparsed) tuple of `_DRAWING_METADATA_HEADERS` values taken
    from the first row.
    """
    drawing_metadata: tuple[str, ...] | None = None
    features: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows, start=2):  # row 1 is the header line
        current_metadata = tuple(_get(row, header) for header in _DRAWING_METADATA_HEADERS)
        if drawing_metadata is None:
            drawing_metadata = current_metadata
        elif current_metadata != drawing_metadata:
            raise CsvParseError(
                f"{source_name}: row {row_number}: drawing-level metadata "
                f"{dict(zip(_DRAWING_METADATA_HEADERS, current_metadata, strict=True))} "
                "does not match the first data row's "
                f"{dict(zip(_DRAWING_METADATA_HEADERS, drawing_metadata, strict=True))} "
                "-- every row must carry the same drawing-level values"
            )
        features.append(_parse_feature(row, row_number))

    assert drawing_metadata is not None  # rows is non-empty, so the loop ran at least once
    return drawing_metadata, features


def _drawing_data_from_metadata(
    drawing_metadata: tuple[str, ...], features: list[dict[str, Any]], source_name: str
) -> dict[str, Any]:
    (
        drawing_id,
        drawing_title,
        drawing_number,
        drawing_revision,
        drawing_default_unit,
        drawing_scale,
    ) = drawing_metadata
    if not drawing_id or not drawing_title:
        raise CsvParseError(
            f"{source_name}: 'drawing_id' and 'drawing_title' are required on every row"
        )

    data: dict[str, Any] = {"id": drawing_id, "title": drawing_title, "features": features}
    if drawing_number:
        data["number"] = drawing_number
    if drawing_revision:
        data["revision"] = drawing_revision
    if drawing_default_unit:
        data["default_unit"] = drawing_default_unit
    if drawing_scale:
        data["scale"] = drawing_scale
    return data


def load_drawing_from_csv_string(text: str, *, source_name: str = "<string>") -> Drawing:
    """Parse a CSV document (as text) into a validated :class:`Drawing`.

    Raises :class:`CsvParseError` for a violation of the CSV contract
    itself (missing/unknown headers, an empty file, inconsistent
    drawing-level metadata, malformed numeric/boolean values, a
    partially specified Dimension/FeatureControlFrame, or an invalid
    delimited datum-reference list), and :class:`DrawingValidationError`
    if the resulting data parses but does not satisfy the ``Drawing``
    schema (e.g. a bad enum value or a duplicate feature id).
    """
    reader = csv.DictReader(io.StringIO(text))
    _validate_headers(reader.fieldnames, text, source_name)

    rows = list(reader)
    if not rows:
        raise CsvParseError(
            f"{source_name}: CSV file has no data rows (a Drawing's id and title are "
            "read from row data, so at least one row is required)"
        )

    drawing_metadata, features = _parse_rows(rows, source_name)
    data = _drawing_data_from_metadata(drawing_metadata, features, source_name)

    try:
        return Drawing.model_validate(data)
    except ValidationError as error:
        raise DrawingValidationError(f"{source_name}: {error}") from error


def load_drawing_from_csv_file(path: str | Path) -> Drawing:
    """Read `path` and parse it into a validated :class:`Drawing`."""
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    return load_drawing_from_csv_string(text, source_name=str(file_path))

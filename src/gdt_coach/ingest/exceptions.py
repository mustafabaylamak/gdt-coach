"""Exceptions raised by the ingest layer."""

from __future__ import annotations


class IngestError(Exception):
    """Base class for errors raised while loading a Drawing from an input file."""


class YamlParseError(IngestError):
    """Raised when the input is not valid YAML, or not a YAML mapping."""


class CsvParseError(IngestError):
    """Raised when the input does not satisfy the CSV ingest contract.

    Covers CSV-contract-specific problems that ``Drawing.model_validate``
    has no way to know about: missing/unknown headers, an empty file,
    inconsistent drawing-level metadata across rows, malformed numeric
    or boolean values (CSV cells are always strings), partially
    specified Dimension/FeatureControlFrame fields, and invalid
    semicolon-delimited datum references. Domain-shape problems (a bad
    enum value, a duplicate feature id, a malformed datum label) are
    deliberately left to ``Drawing``'s own validators and surface as
    ``DrawingValidationError`` instead, to avoid duplicating that logic
    here.
    """


class DrawingValidationError(IngestError):
    """Raised when parsed input data does not satisfy the Drawing schema."""


class UnsupportedFormatError(IngestError):
    """Raised when no registered InputAdapter supports a given file's extension."""


class DuplicateFormatIdError(IngestError):
    """Raised when two InputAdapters are registered with the same format_id."""


class DuplicateFileExtensionError(IngestError):
    """Raised when two InputAdapters claim the same file extension."""

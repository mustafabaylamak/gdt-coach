"""Exceptions raised by the YAML ingest layer."""

from __future__ import annotations


class IngestError(Exception):
    """Base class for errors raised while loading a Drawing from an input file."""


class YamlParseError(IngestError):
    """Raised when the input is not valid YAML, or not a YAML mapping."""


class DrawingValidationError(IngestError):
    """Raised when parsed YAML data does not satisfy the Drawing schema."""


class UnsupportedFormatError(IngestError):
    """Raised when no registered InputAdapter supports a given file's extension."""


class DuplicateFormatIdError(IngestError):
    """Raised when two InputAdapters are registered with the same format_id."""


class DuplicateFileExtensionError(IngestError):
    """Raised when two InputAdapters claim the same file extension."""

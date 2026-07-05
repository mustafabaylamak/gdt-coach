"""Exceptions raised by the YAML ingest layer."""

from __future__ import annotations


class IngestError(Exception):
    """Base class for errors raised while loading a Drawing from an input file."""


class YamlParseError(IngestError):
    """Raised when the input is not valid YAML, or not a YAML mapping."""


class DrawingValidationError(IngestError):
    """Raised when parsed YAML data does not satisfy the Drawing schema."""

"""Ingest layer for gdt-coach.

Converts a structured input document into a validated
:class:`gdt_coach.models.Drawing`. This is purely a translation layer:
it does not run the rule engine and does not know about GD&T semantics
beyond what ``Drawing`` itself already validates.

YAML (:class:`~gdt_coach.ingest.adapter.YamlInputAdapter`) is the only
implemented input format. :class:`~gdt_coach.ingest.adapter.InputAdapter`
and :class:`~gdt_coach.ingest.adapter.AdapterRegistry` are dispatch
infrastructure for future formats (CSV, PDF, DXF, ...), not an
implementation of any of them.
"""

from gdt_coach.ingest.adapter import (
    ALL_INPUT_ADAPTERS,
    AdapterRegistry,
    InputAdapter,
    YamlInputAdapter,
)
from gdt_coach.ingest.exceptions import (
    DrawingValidationError,
    DuplicateFileExtensionError,
    DuplicateFormatIdError,
    IngestError,
    UnsupportedFormatError,
    YamlParseError,
)
from gdt_coach.ingest.yaml_loader import (
    load_drawing_from_yaml_file,
    load_drawing_from_yaml_string,
)

__all__ = [
    "ALL_INPUT_ADAPTERS",
    "AdapterRegistry",
    "DrawingValidationError",
    "DuplicateFileExtensionError",
    "DuplicateFormatIdError",
    "IngestError",
    "InputAdapter",
    "UnsupportedFormatError",
    "YamlInputAdapter",
    "YamlParseError",
    "load_drawing_from_yaml_file",
    "load_drawing_from_yaml_string",
]

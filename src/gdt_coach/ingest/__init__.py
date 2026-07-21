"""Ingest layer for gdt-coach.

Converts a structured input document into a validated
:class:`gdt_coach.models.Drawing`. This is purely a translation layer:
it does not run the rule engine and does not know about GD&T semantics
beyond what ``Drawing`` itself already validates.

YAML (:class:`~gdt_coach.ingest.adapter.YamlInputAdapter`) is the
expressive, native format -- it mirrors the domain model directly and
supports everything ``Drawing`` can express. CSV
(:class:`~gdt_coach.ingest.adapter.CsvInputAdapter`, Sprint 14) is a
second, intentionally narrow format for simple drawings; it is not a
technical-drawing replacement and does not imply readiness for PDF or
any other unstructured format -- see ``csv_loader.py`` for its exact,
documented limitations. :class:`~gdt_coach.ingest.adapter.InputAdapter`
and :class:`~gdt_coach.ingest.adapter.AdapterRegistry` are dispatch
infrastructure, not a promise about what any given format can express.
"""

from gdt_coach.ingest.adapter import (
    ALL_INPUT_ADAPTERS,
    AdapterRegistry,
    CsvInputAdapter,
    InputAdapter,
    YamlInputAdapter,
)
from gdt_coach.ingest.csv_loader import (
    load_drawing_from_csv_file,
    load_drawing_from_csv_string,
)
from gdt_coach.ingest.exceptions import (
    CsvParseError,
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
    "CsvInputAdapter",
    "CsvParseError",
    "DrawingValidationError",
    "DuplicateFileExtensionError",
    "DuplicateFormatIdError",
    "IngestError",
    "InputAdapter",
    "UnsupportedFormatError",
    "YamlInputAdapter",
    "YamlParseError",
    "load_drawing_from_csv_file",
    "load_drawing_from_csv_string",
    "load_drawing_from_yaml_file",
    "load_drawing_from_yaml_string",
]

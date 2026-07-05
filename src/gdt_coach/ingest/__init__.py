"""YAML ingest layer for gdt-coach.

Converts a structured YAML document into a validated
:class:`gdt_coach.models.Drawing`. This is purely a translation layer:
it does not run the rule engine and does not know about GD&T semantics
beyond what ``Drawing`` itself already validates.
"""

from gdt_coach.ingest.exceptions import DrawingValidationError, IngestError, YamlParseError
from gdt_coach.ingest.yaml_loader import (
    load_drawing_from_yaml_file,
    load_drawing_from_yaml_string,
)

__all__ = [
    "DrawingValidationError",
    "IngestError",
    "YamlParseError",
    "load_drawing_from_yaml_file",
    "load_drawing_from_yaml_string",
]

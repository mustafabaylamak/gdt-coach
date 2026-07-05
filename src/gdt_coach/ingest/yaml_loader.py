"""YAML loader: turns a YAML document into a validated Drawing.

This is purely a translation layer. It parses YAML text into a plain
dict and hands it to :meth:`Drawing.model_validate`, which already
knows how to build the full nested tree (features, dimensions, feature
control frames, tolerances, datums) and enforce the domain model's own
validation. No GD&T semantics are added here.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from gdt_coach.ingest.exceptions import DrawingValidationError, YamlParseError
from gdt_coach.models import Drawing


def load_drawing_from_yaml_string(text: str, *, source_name: str = "<string>") -> Drawing:
    """Parse a YAML document (as text) into a validated :class:`Drawing`.

    Raises :class:`YamlParseError` if ``text`` is not valid YAML or does
    not parse to a mapping, and :class:`DrawingValidationError` if it
    parses but does not satisfy the ``Drawing`` schema.
    """
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise YamlParseError(f"{source_name}: invalid YAML: {error}") from error

    if data is None:
        raise YamlParseError(f"{source_name}: YAML document is empty")
    if not isinstance(data, dict):
        raise YamlParseError(
            f"{source_name}: YAML document must be a mapping, got {type(data).__name__}"
        )

    try:
        return Drawing.model_validate(data)
    except ValidationError as error:
        raise DrawingValidationError(f"{source_name}: {error}") from error


def load_drawing_from_yaml_file(path: str | Path) -> Drawing:
    """Read ``path`` and parse it into a validated :class:`Drawing`."""
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    return load_drawing_from_yaml_string(text, source_name=str(file_path))

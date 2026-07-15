"""InputAdapter abstraction — the ingest-layer analog of Rule.

Each supported input format is an ``InputAdapter`` subclass declaring
minimal metadata (``format_id``, ``file_extensions``) and implementing
``load(path) -> Drawing``. This is dispatch infrastructure only: it
lets a future input format be added without changing CLI dispatch,
``RuleEngine``, ``RuleRegistry``, or any domain model -- the same way
adding a new ``Rule`` never touches the rule engine.

YAML (``YamlInputAdapter``) is the only implemented adapter today. It
is a thin wrapper around the existing, unchanged
:func:`gdt_coach.ingest.yaml_loader.load_drawing_from_yaml_file` --
no YAML parsing or validation logic is duplicated here.

Deliberately not done here: a formal intermediate representation
between raw input and ``Drawing``. ``load()`` returns a ``Drawing``
directly; that's sufficient with one adapter and would be premature to
generalize before a second real importer (CSV, PDF, DXF, ...) exists
to prove out what a shared intermediate shape would actually need to
carry.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

from gdt_coach.ingest.exceptions import (
    DuplicateFileExtensionError,
    DuplicateFormatIdError,
    UnsupportedFormatError,
)
from gdt_coach.ingest.yaml_loader import load_drawing_from_yaml_file
from gdt_coach.models import Drawing


class InputAdapter(ABC):
    """A single input format's translation into a Drawing.

    Concrete subclasses declare their metadata as class attributes and
    implement :meth:`load`. Adapters are stateless: one instance is
    created (by an :class:`AdapterRegistry`) and reused for every path
    it loads.
    """

    format_id: ClassVar[str]
    file_extensions: ClassVar[tuple[str, ...]]

    @abstractmethod
    def load(self, path: Path) -> Drawing:
        """Load `path` and return a validated Drawing, or raise an IngestError subclass."""
        raise NotImplementedError


class YamlInputAdapter(InputAdapter):
    """Adapts the existing YAML ingest functions to the InputAdapter interface."""

    format_id = "yaml"
    file_extensions = (".yaml", ".yml")

    def load(self, path: Path) -> Drawing:
        return load_drawing_from_yaml_file(path)


def _normalize_extension(extension: str) -> str:
    """Lowercase an extension and ensure a leading dot, so lookup is case-insensitive
    and tolerant of an adapter declaring extensions with or without the dot."""
    normalized = extension.strip().lower()
    if normalized and not normalized.startswith("."):
        normalized = f".{normalized}"
    return normalized


class AdapterRegistry:
    """A collection of input adapters, resolved by normalized file extension.

    Resolution is a plain dict lookup keyed by extension, so which
    adapter handles a given extension never depends on registration
    order -- only on which extensions were declared, which is itself
    validated (duplicates rejected) at registration time.
    """

    def __init__(self) -> None:
        self._adapters_by_extension: dict[str, InputAdapter] = {}
        self._format_ids: set[str] = set()

    def register(self, adapter_cls: type[InputAdapter]) -> type[InputAdapter]:
        """Instantiate and register an adapter class.

        Returns the class unchanged so this can be used as a decorator,
        mirroring :meth:`~gdt_coach.rules.registry.RuleRegistry.register`.
        """
        adapter = adapter_cls()
        if adapter.format_id in self._format_ids:
            raise DuplicateFormatIdError(
                f"an adapter with format_id {adapter.format_id!r} is already registered"
            )

        normalized_extensions = [_normalize_extension(ext) for ext in adapter.file_extensions]
        for extension in normalized_extensions:
            existing = self._adapters_by_extension.get(extension)
            if existing is not None:
                raise DuplicateFileExtensionError(
                    f"file extension {extension!r} is already claimed by adapter "
                    f"{existing.format_id!r}; cannot also register it for "
                    f"{adapter.format_id!r}"
                )

        self._format_ids.add(adapter.format_id)
        for extension in normalized_extensions:
            self._adapters_by_extension[extension] = adapter
        return adapter_cls

    def resolve(self, path: Path) -> InputAdapter:
        """The adapter registered for `path`'s file extension.

        Raises UnsupportedFormatError if no adapter claims that
        extension (case-insensitive).
        """
        extension = _normalize_extension(path.suffix)
        adapter = self._adapters_by_extension.get(extension)
        if adapter is None:
            supported = ", ".join(sorted(self._adapters_by_extension)) or "(none registered)"
            raise UnsupportedFormatError(
                f"no input adapter registered for file extension {path.suffix!r} "
                f"(path: {path}); supported extensions: {supported}"
            )
        return adapter

    def all(self) -> list[InputAdapter]:
        """Every registered adapter, once each, regardless of how many extensions it claims."""
        seen: dict[str, InputAdapter] = {}
        for adapter in self._adapters_by_extension.values():
            seen[adapter.format_id] = adapter
        return list(seen.values())

    def __len__(self) -> int:
        return len(self.all())


ALL_INPUT_ADAPTERS: tuple[type[InputAdapter], ...] = (YamlInputAdapter,)
"""The single source of truth for "every input adapter that exists" -- mirrors
:data:`gdt_coach.rules.checks.ALL_RULE_CLASSES`. Adding a new adapter means:
write its module (or add it here directly, at this scale), add it to this
tuple, and write its tests -- nothing else needs to change.
"""

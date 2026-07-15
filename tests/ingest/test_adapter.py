"""Tests for the InputAdapter abstraction and AdapterRegistry."""

from __future__ import annotations

from pathlib import Path

import pytest

from gdt_coach.ingest.adapter import (
    ALL_INPUT_ADAPTERS,
    AdapterRegistry,
    InputAdapter,
    YamlInputAdapter,
)
from gdt_coach.ingest.exceptions import (
    DuplicateFileExtensionError,
    DuplicateFormatIdError,
    UnsupportedFormatError,
    YamlParseError,
)
from gdt_coach.ingest.yaml_loader import load_drawing_from_yaml_file
from gdt_coach.models import Drawing

_EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"


class _FakeAdapter(InputAdapter):
    """A minimal concrete InputAdapter for registry tests, independent of YAML."""

    format_id = "fake"
    file_extensions = ("fake",)  # deliberately no leading dot, to exercise normalization

    def load(self, path: Path) -> Drawing:
        return Drawing(id="fake", title="Fake")


class _OtherFakeAdapter(InputAdapter):
    format_id = "other-fake"
    file_extensions = (".fake",)  # same normalized extension as _FakeAdapter's "fake"

    def load(self, path: Path) -> Drawing:
        return Drawing(id="other-fake", title="Other Fake")


class _DuplicateFormatIdAdapter(InputAdapter):
    format_id = "fake"  # collides with _FakeAdapter
    file_extensions = (".different",)

    def load(self, path: Path) -> Drawing:
        return Drawing(id="dup", title="Dup")


# --- InputAdapter is abstract ------------------------------------------------


def test_input_adapter_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        InputAdapter()  # type: ignore[abstract]


# --- YamlInputAdapter ---------------------------------------------------------


def test_yaml_adapter_metadata() -> None:
    adapter = YamlInputAdapter()

    assert adapter.format_id == "yaml"
    assert adapter.file_extensions == (".yaml", ".yml")


def test_yaml_adapter_equivalent_to_direct_loader() -> None:
    path = _EXAMPLES_DIR / "valid_position.yaml"

    via_adapter = YamlInputAdapter().load(path)
    via_direct_call = load_drawing_from_yaml_file(path)

    assert via_adapter == via_direct_call


def test_yaml_adapter_raises_the_same_errors_as_the_direct_loader(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("id: [unclosed", encoding="utf-8")

    with pytest.raises(YamlParseError):
        YamlInputAdapter().load(bad_file)
    with pytest.raises(YamlParseError):
        load_drawing_from_yaml_file(bad_file)


# --- AdapterRegistry: registration and resolution ----------------------------


def test_register_and_resolve_by_extension() -> None:
    registry = AdapterRegistry()
    registry.register(YamlInputAdapter)

    adapter = registry.resolve(Path("drawing.yaml"))

    assert adapter.format_id == "yaml"


def test_resolve_is_case_insensitive() -> None:
    registry = AdapterRegistry()
    registry.register(YamlInputAdapter)

    assert registry.resolve(Path("DRAWING.YAML")).format_id == "yaml"
    assert registry.resolve(Path("drawing.Yml")).format_id == "yaml"
    assert registry.resolve(Path("drawing.YML")).format_id == "yaml"


def test_extension_without_leading_dot_is_normalized() -> None:
    registry = AdapterRegistry()
    registry.register(_FakeAdapter)

    # _FakeAdapter declares "fake" (no dot); resolution must still work for a
    # real path, which always has a dotted suffix.
    assert registry.resolve(Path("thing.fake")).format_id == "fake"
    assert registry.resolve(Path("thing.FAKE")).format_id == "fake"


def test_resolve_unsupported_extension_raises() -> None:
    registry = AdapterRegistry()
    registry.register(YamlInputAdapter)

    with pytest.raises(UnsupportedFormatError, match=r"\.pdf"):
        registry.resolve(Path("drawing.pdf"))


def test_resolve_unsupported_extension_lists_supported_extensions() -> None:
    registry = AdapterRegistry()
    registry.register(YamlInputAdapter)

    with pytest.raises(UnsupportedFormatError, match=r"\.yaml.*\.yml|\.yml.*\.yaml"):
        registry.resolve(Path("drawing.csv"))


def test_resolve_with_no_adapters_registered_raises() -> None:
    registry = AdapterRegistry()

    with pytest.raises(UnsupportedFormatError, match="none registered"):
        registry.resolve(Path("drawing.yaml"))


# --- AdapterRegistry: duplicate detection ------------------------------------


def test_duplicate_format_id_rejected() -> None:
    registry = AdapterRegistry()
    registry.register(_FakeAdapter)

    with pytest.raises(DuplicateFormatIdError, match="fake"):
        registry.register(_DuplicateFormatIdAdapter)


def test_duplicate_file_extension_rejected() -> None:
    registry = AdapterRegistry()
    registry.register(_FakeAdapter)  # claims "fake" -> normalized ".fake"

    with pytest.raises(DuplicateFileExtensionError, match=r"\.fake"):
        registry.register(_OtherFakeAdapter)  # claims ".fake" too


def test_duplicate_extension_registration_does_not_replace_the_first_adapter() -> None:
    registry = AdapterRegistry()
    registry.register(_FakeAdapter)

    with pytest.raises(DuplicateFileExtensionError):
        registry.register(_OtherFakeAdapter)

    # The rejected registration must not have partially applied.
    assert registry.resolve(Path("thing.fake")).format_id == "fake"
    assert len(registry) == 1


# --- AdapterRegistry: enumeration --------------------------------------------


def test_all_returns_one_entry_per_adapter_not_per_extension() -> None:
    registry = AdapterRegistry()
    registry.register(YamlInputAdapter)  # claims two extensions: .yaml and .yml

    all_adapters = registry.all()

    assert len(all_adapters) == 1
    assert len(registry) == 1
    assert all_adapters[0].format_id == "yaml"


def test_registration_order_does_not_affect_resolution() -> None:
    registry_a = AdapterRegistry()
    registry_a.register(_FakeAdapter)

    registry_b = AdapterRegistry()
    registry_b.register(_FakeAdapter)

    assert (
        registry_a.resolve(Path("x.fake")).format_id == registry_b.resolve(Path("x.fake")).format_id
    )


# --- ALL_INPUT_ADAPTERS -------------------------------------------------------


def test_all_input_adapters_contains_yaml_adapter() -> None:
    assert YamlInputAdapter in ALL_INPUT_ADAPTERS


def test_all_input_adapters_register_without_conflict() -> None:
    registry = AdapterRegistry()
    for adapter_cls in ALL_INPUT_ADAPTERS:
        registry.register(adapter_cls)

    assert len(registry) == len(ALL_INPUT_ADAPTERS)

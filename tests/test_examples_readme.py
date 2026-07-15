"""Tests for the examples/README.md drift guard (scripts/generate_examples_readme.py).

`scripts/` is not part of the installable `gdt_coach` package (see
ARCHITECTURE.md#layout), so it's imported here via an explicit
`sys.path` entry rather than a normal package import.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import generate_examples_readme as gen  # noqa: E402
import pytest  # noqa: E402

_EXAMPLES_DIR = _REPO_ROOT / "examples"
_README_PATH = _EXAMPLES_DIR / "README.md"


def test_examples_readme_matches_real_cli_output() -> None:
    """The drift guard itself: regenerating must not change the committed file.

    If this fails, examples/README.md has drifted from real CLI output --
    run `python scripts/generate_examples_readme.py` to fix it.
    """
    original = _README_PATH.read_text(encoding="utf-8")

    regenerated = gen.regenerate(original)

    assert regenerated == original


def test_generator_cli_check_mode_passes_against_committed_repo() -> None:
    """The actual entry point contributors/CI run, not just the underlying function."""
    exit_code = gen.main(["--check"])

    assert exit_code == 0


def test_every_example_yaml_has_a_documented_block() -> None:
    documented = gen.documented_example_keys(_README_PATH.read_text(encoding="utf-8"))
    discovered = gen.discover_example_keys(_EXAMPLES_DIR)

    missing, orphaned = gen.diff_example_keys(documented, discovered)

    assert missing == set()
    assert orphaned == set()


def test_regenerate_is_idempotent() -> None:
    original = _README_PATH.read_text(encoding="utf-8")

    once = gen.regenerate(original)
    twice = gen.regenerate(once)

    assert once == twice


# --- Unit tests for the pure helpers, independent of the real repo ---------


def test_diff_example_keys_reports_missing() -> None:
    missing, orphaned = gen.diff_example_keys(documented=set(), discovered={"foo"})

    assert missing == {"foo"}
    assert orphaned == set()


def test_diff_example_keys_reports_orphaned() -> None:
    missing, orphaned = gen.diff_example_keys(documented={"foo"}, discovered=set())

    assert missing == set()
    assert orphaned == {"foo"}


def test_diff_example_keys_reports_nothing_when_in_sync() -> None:
    missing, orphaned = gen.diff_example_keys(documented={"foo", "bar"}, discovered={"foo", "bar"})

    assert missing == set()
    assert orphaned == set()


def test_documented_example_keys_extracts_every_marker() -> None:
    text = (
        "intro\n"
        "<!-- gdt-coach:example alpha -->\nold content\n<!-- /gdt-coach:example -->\n"
        "middle\n"
        "<!-- gdt-coach:example beta -->\nold content\n<!-- /gdt-coach:example -->\n"
    )

    assert gen.documented_example_keys(text) == {"alpha", "beta"}


def test_discover_example_keys_matches_real_examples_dir() -> None:
    keys = gen.discover_example_keys(_EXAMPLES_DIR)

    assert "valid_position" in keys
    assert "invalid_position_related_dimension_wrong_role" in keys
    assert all(not key.endswith(".yaml") for key in keys)


# --- Detecting drift: a mangled (stale) copy must not regenerate as itself --


def test_regenerate_detects_a_stale_rule_count() -> None:
    original = _README_PATH.read_text(encoding="utf-8")
    stale = original.replace("Rules run: 20", "Rules run: 14", 1)
    assert stale != original  # sanity check the substitution actually did something

    regenerated = gen.regenerate(stale)

    assert regenerated != stale
    assert regenerated == original


def test_regenerate_detects_a_stale_finding_message() -> None:
    original = _README_PATH.read_text(encoding="utf-8")
    stale = original.replace("No findings.", "Some findings.", 1)
    assert stale != original

    regenerated = gen.regenerate(stale)

    assert regenerated != stale
    assert regenerated == original


def test_regenerate_raises_when_a_yaml_file_is_undocumented(tmp_path: Path) -> None:
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    (examples_dir / "undocumented.yaml").write_text("id: x\ntitle: x\n", encoding="utf-8")
    readme_text = "no markers here at all\n"

    with pytest.raises(gen.ExamplesReadmeError, match="missing doc block"):
        gen.regenerate(readme_text, examples_dir=examples_dir)


def test_regenerate_raises_when_a_documented_example_no_longer_exists(tmp_path: Path) -> None:
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    readme_text = "<!-- gdt-coach:example ghost -->\nold content\n<!-- /gdt-coach:example -->\n"

    with pytest.raises(gen.ExamplesReadmeError, match="orphaned doc block"):
        gen.regenerate(readme_text, examples_dir=examples_dir)


def test_main_write_mode_updates_a_stale_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Use the real examples/ dir for CLI execution, but point the generator
    # at a scratch copy of the README so this test never writes to the repo.
    scratch_readme = tmp_path / "README.md"
    real_readme_text = _README_PATH.read_text(encoding="utf-8")
    scratch_readme.write_text(
        real_readme_text.replace("Rules run: 20", "Rules run: 14", 1), encoding="utf-8"
    )
    monkeypatch.setattr(gen, "_README_PATH", scratch_readme)

    exit_code = gen.main([])

    assert exit_code == 0
    assert scratch_readme.read_text(encoding="utf-8") == real_readme_text


def test_main_check_mode_fails_on_a_stale_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scratch_readme = tmp_path / "README.md"
    real_readme_text = _README_PATH.read_text(encoding="utf-8")
    scratch_readme.write_text(
        real_readme_text.replace("Rules run: 20", "Rules run: 14", 1), encoding="utf-8"
    )
    monkeypatch.setattr(gen, "_README_PATH", scratch_readme)

    exit_code = gen.main(["--check"])

    assert exit_code == 1
    # --check must not have written anything
    assert scratch_readme.read_text(encoding="utf-8") != real_readme_text

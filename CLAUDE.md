# CLAUDE.md

Guidance for Claude Code (or other AI agents) working in this repository.

## Project state

This is a bare scaffold. No business logic has been implemented. Do not
invent product behavior — check `PROJECT.md` for scope, and if it still
says "TBD", ask before assuming requirements.

## Structure

- `src/gdt_coach/` — package code (src layout). Import as `gdt_coach`.
- `tests/` — pytest tests, mirrors `src/gdt_coach/` structure.
- `docs/` — extended documentation.
- `scripts/` — standalone dev/maintenance scripts, not part of the package.

## Conventions

- Python 3.11+, fully type-annotated, `mypy --strict` must pass.
- Formatting/linting via Ruff; run `ruff format .` and `ruff check --fix .`
  before committing. Do not hand-format — let Ruff own style.
- Prefer `pathlib.Path` over `os.path` (enforced by the `PTH` Ruff ruleset).
- New modules need corresponding tests in `tests/`.

## Commands

```bash
pip install -e ".[dev]"   # install package + dev tools
pre-commit install        # enable git hooks
ruff check .               # lint
ruff format .              # format
mypy src                   # type-check
pytest                      # test with coverage
```

## Before finishing a change

1. `ruff check . && ruff format --check .`
2. `mypy src`
3. `pytest`

All three must pass; CI (`.github/workflows/ci.yml`) runs the same checks.

## Git

- Only commit when explicitly asked.
- Never force-push, amend published commits, or bypass hooks (`--no-verify`).

# ARCHITECTURE.md

## Current state

No business logic exists yet. This document describes the technical
scaffolding only.

## Layout

- `src/gdt_coach/` — the installable package (src layout, keeps the
  package importable only from its installed form, avoiding accidental
  imports from a repo-root copy).
- `tests/` — pytest suite, mirrors the package layout.
- `docs/` — project documentation beyond the top-level `*.md` files.
- `scripts/` — one-off or maintenance scripts not part of the package.

## Tooling

| Concern       | Tool         | Config location         |
|---------------|--------------|--------------------------|
| Packaging     | Hatchling    | `pyproject.toml`         |
| Linting       | Ruff         | `pyproject.toml`         |
| Formatting    | Ruff format  | `pyproject.toml`         |
| Type checking | Mypy (strict)| `pyproject.toml`         |
| Testing       | Pytest       | `pyproject.toml`         |
| Git hooks     | pre-commit   | `.pre-commit-config.yaml`|
| CI            | GitHub Actions | `.github/workflows/ci.yml` |

## Entry points

- `gdt_coach.cli:main` is registered as the `gdt-coach` console script.
  It currently only supports `--version` and `--help`.

## Decisions to be made

- Runtime dependencies and third-party integrations.
- Module boundaries once business logic is introduced.
- Data storage / persistence approach, if any.

Update this document as real architecture decisions are made.

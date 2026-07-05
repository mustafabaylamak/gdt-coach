# ROADMAP.md

## Phase 0 — Scaffold (done)

- [x] `src` layout package with console script entry point
- [x] Ruff (lint + format), Mypy (strict), Pytest + coverage
- [x] pre-commit hooks
- [x] GitHub Actions CI (lint, type-check, test on 3.11–3.13)
- [x] Baseline docs (README, PROJECT, ARCHITECTURE, ROADMAP, CLAUDE)

## Phase 1 — Define scope

- [x] Decide runtime dependencies (Pydantic v2 for domain models)
- [x] Draft initial architecture in `ARCHITECTURE.md`
- [ ] Fill in `PROJECT.md` with real goals, users, and success criteria

## Sprint 1 — Domain model (done)

- [x] Pydantic domain models: `Drawing`, `Feature`, `Datum`, `Dimension`,
      `FeatureControlFrame`, `Tolerance`, plus supporting enumerations
- [x] Minimal validation for structurally impossible data only (no GD&T
      rule logic, no parsing, no rule engine)
- [x] Comprehensive unit tests (72 tests, 100% coverage on `models/`)

## Sprint 2 — Rule engine infrastructure (done)

- [x] `Rule` abstract base class (id, title, severity, standard,
      category, explanation, `check()`)
- [x] `Finding` model, `Severity`/`RuleCategory`/`Standard` enums
- [x] `RuleRegistry` (register/unregister/get/filter, duplicate-id and
      missing-metadata validation) and `RuleEngine` (runs registered
      rules against a `Drawing`, with category/standard filtering)
- [x] Comprehensive unit tests (116 tests total, 100% coverage on
      `rules/`); still no concrete GD&T rules and no YAML parsing

## Phase 2 — First business logic

- [ ] Parsing: turn a source drawing into `gdt_coach.models` objects
- [ ] First concrete GD&T rules registered against the Sprint 2 engine

## Later

- [ ] Packaging/release process (versioning, changelog, publishing)
- [ ] Documentation site (if needed)

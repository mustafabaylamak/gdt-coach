# ROADMAP.md

## Phase 0 — Scaffold (done)

- [x] `src` layout package with console script entry point
- [x] Ruff (lint + format), Mypy (strict), Pytest + coverage
- [x] pre-commit hooks
- [x] GitHub Actions CI (lint, type-check, test on 3.11–3.13)
- [x] Baseline docs (README, PROJECT, ARCHITECTURE, ROADMAP)

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

## Sprint 3 — First five GD&T rules (done)

- [x] `gdt_coach.rules.checks` package: one module per rule, each
      self-registering against `default_registry`
- [x] Rules: flatness/straightness cannot reference datums, no
      duplicate datum references in one FCF, position requires a
      datum reference, projected zone requires position
- [x] `RuleEngine` unchanged; rules integrate through the existing
      registry/engine API
- [x] Comprehensive PASS/FAIL unit tests per rule plus an end-to-end
      registry+engine integration test (139 tests total, 100% coverage
      on `rules/checks/`); still no YAML parsing and no CLI wiring

## Sprint 4 — YAML ingest (done)

- [x] `gdt_coach.ingest` package: `load_drawing_from_yaml_string` /
      `load_drawing_from_yaml_file`, translating YAML directly into
      `Drawing.model_validate()` with no added GD&T semantics
- [x] `YamlParseError` / `DrawingValidationError` (`IngestError` base)
      for malformed YAML vs. domain-model validation failures
- [x] `examples/`: `valid_position.yaml`,
      `invalid_flatness_with_datum.yaml`, `invalid_projected_zone.yaml`
      (the "invalid" ones load into a valid `Drawing` but are flagged
      by the Sprint 3 rules — ingest and rule-checking stay decoupled)
- [x] Comprehensive tests (156 tests total, 100% coverage on
      `ingest/`), including an end-to-end YAML -> Drawing -> RuleEngine
      test per example; `RuleEngine` unchanged, no CLI wiring

## Sprint 5 — CLI check command (done)

- [x] `gdt-coach check <path>`: loads a YAML drawing via
      `gdt_coach.ingest`, runs the five Sprint 3 rules through the
      unchanged `RuleEngine`, and prints a plain-text report (rule id,
      severity, title, message, and location when available)
- [x] Exit codes: `0` no findings, `1` one or more findings, `2` YAML
      load/validation failure (malformed YAML, missing file, or a
      `Drawing` that fails validation)
- [x] Comprehensive tests (169 tests total): exit codes for all three
      example files plus malformed/missing YAML, output-content checks,
      and direct unit tests of the report formatting helpers
- [x] `RuleEngine` unchanged; no new GD&T rules; no Markdown/HTML report

## Phase 2 — First business logic

- [ ] More GD&T rules (orientation, form beyond straightness/flatness,
      runout, profile, tolerance-value sanity checks, ...)
- [ ] Markdown/HTML/JSON report output for `gdt-coach check`

## Later

- [ ] Packaging/release process (versioning, changelog, publishing)
- [ ] Documentation site (if needed)

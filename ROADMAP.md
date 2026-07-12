# ROADMAP.md

## Implemented

### Project scaffold

- `src` layout package with a console script entry point
- Ruff (lint + format), Mypy (strict), Pytest + coverage
- pre-commit hooks
- GitHub Actions CI (lint, type-check, test on Python 3.11–3.13)

### Domain model

- Pydantic v2 models: `Drawing`, `Feature`, `Datum`, `Dimension`,
  `FeatureControlFrame`, `Tolerance`, plus supporting enumerations
- Validation limited to structurally impossible data (negative
  tolerances, zero-diameter holes, duplicate datum labels, mismatched
  dimension type/unit) — no GD&T interpretation rules at the model
  level

### Rule engine

- `Rule` abstract base class (`id`, `title`, `severity`, `standard`,
  `category`, `explanation`, `check()`)
- `Finding` model, `Severity`/`RuleCategory`/`Standard` enums
- `RuleRegistry` (register/unregister/get/filter, duplicate-id and
  missing-metadata validation) and `RuleEngine` (runs registered rules
  against a `Drawing`, with category/standard filtering)
- `ALL_RULE_CLASSES` as the single source of truth for which concrete
  rules exist, used by both the CLI and the test suite

### GD&T rules (14 total)

- Form: flatness/straightness/circularity/cylindricity cannot
  reference datums; straightness/flatness MMC only on a Feature of Size
- Orientation: requires at least one datum
- Position: requires a datum reference, requires a Feature of Size,
  MMC/LMC requires a Feature of Size, projected tolerance zone requires
  position
- Runout: always RFS
- Datum structure: no duplicate datum references in one feature control
  frame, referenced datums must be defined on the drawing
- Standard edition: concentricity/symmetry flagged as deprecated under
  ASME Y14.5-2018

See `ARCHITECTURE.md#concrete-rules` for the full table with rule IDs,
categories, and standards, plus documented limitations per rule.

### YAML ingest

- `load_drawing_from_yaml_string` / `load_drawing_from_yaml_file`,
  translating YAML directly into `Drawing.model_validate()` with no
  added GD&T semantics
- `YamlParseError` / `DrawingValidationError` (`IngestError` base) for
  malformed YAML vs. domain-model validation failures

### CLI

- `gdt-coach check <path>`: loads a YAML drawing, runs the rule engine,
  and prints a report
- `--category` (repeatable) / `--standard` filters, delegating directly
  to `RuleEngine.run(categories=, standard=)`
- `--json` output mode alongside the default plain-text report
- Exit codes: `0` no findings, `1` one or more findings, `2` input
  couldn't be checked (malformed YAML, missing file, failed validation,
  or an invalid filter value)

### Testing

- 242 tests, 99% line coverage, run on every push via CI
- PASS/FAIL coverage for every rule, including documented limitations
  (e.g. a rule verified against data assembled via `model_construct()`
  to exercise a branch that normal validation makes otherwise
  unreachable)

### `FeatureControlFrame` → `Dimension` linkage

- `FeatureControlFrame.related_dimension_ids: list[str]`, default `[]`,
  declaring which `Dimension`(s) establish or support a feature control
  frame (e.g. the basic location dimensions a position tolerance
  applies to)
- Structural validation only: every id must be a non-empty string, no
  duplicate ids within one `FeatureControlFrame`
- Deliberately does not check that referenced ids exist elsewhere on
  the `Drawing` — that's cross-object referential integrity, left to
  the rule layer, same as datum label references
- Backward-compatible: optional field with an empty-list default, so
  every existing YAML drawing still validates unchanged
- See `ARCHITECTURE.md#dimension-linkage` for the full design and
  validation-boundary rationale

## Planned

- More GD&T rules: additional orientation/form checks, profile,
  tolerance-value sanity checks
- A `FeatureControlFrame` → `Dimension` link (small model change) to
  unlock rules like "position requires basic location dimensions"
- A composite/multi-segment `FeatureControlFrame` representation
  (larger model change) to unlock composite-tolerancing rules
- Markdown/HTML report output for `gdt-coach check` (JSON is done)
- A documented target standard edition on `Drawing`, to make the
  concentricity/symmetry deprecation check a hard error instead of a
  warning where appropriate

## Under consideration

- A formal JSON Schema for `Finding`/`Drawing` as an integration
  contract, once an external consumer needs one
- Auto-discovery for `gdt_coach.rules.checks` (scanning for `Rule`
  subclasses instead of a hand-maintained list), once the rule count
  makes the current approach unwieldy
- A versioned wire schema for YAML input, if the domain model changes
  in ways that would otherwise break existing files
- Packaging/release process (versioning, changelog, PyPI publishing)
- Other input formats (PDF/DXF/CAD/image) — a substantial undertaking,
  not scoped yet

See `PROJECT.md` for goals, non-goals, and success criteria.

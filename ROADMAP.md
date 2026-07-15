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
  tolerances, zero-diameter holes, duplicate datum labels, duplicate
  dimension ids within one feature, mismatched dimension type/unit) —
  no GD&T interpretation rules at the model level

### Rule engine

- `Rule` abstract base class (`id`, `title`, `severity`, `standard`,
  `category`, `explanation`, `check()`)
- `Finding` model, `Severity`/`RuleCategory`/`Standard` enums
- `RuleRegistry` (register/unregister/get/filter, duplicate-id and
  missing-metadata validation) and `RuleEngine` (runs registered rules
  against a `Drawing`, with category/standard filtering)
- `ALL_RULE_CLASSES` as the single source of truth for which concrete
  rules exist, used by both the CLI and the test suite

### GD&T rules (20 total)

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
- Dimension structure: related dimensions must be defined on the same
  feature, position-related dimensions must be basic, related
  dimensions must not be reference dimensions, angularity-related
  dimensions must be angular
- Dimension role: position-related dimensions must have role LOCATION,
  angularity-related dimensions must have role ORIENTATION

Run `gdt-coach rules list` for the live catalog (id, category,
standard, severity) and `gdt-coach rules show <id>` for a rule's full
explanation — see `ARCHITECTURE.md#concrete-rules` for what replaced
the old hand-maintained table, and documented per-rule limitations.

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
- `gdt-coach rules list [--category]... [--standard] [--json]` and
  `gdt-coach rules show <rule_id> [--json]` (Sprint 12): a live rule
  catalog derived entirely from `ALL_RULE_CLASSES`, sorted by id for
  deterministic output, reusing `check`'s own category/standard
  parsing. Exit codes: `0` on a successful list/show (including an
  empty filter result), `2` for an invalid `--category`/`--standard`
  value or an unknown rule id

### Testing

- 340 tests, 99% line coverage, run on every push via CI
- PASS/FAIL coverage for every rule, including documented limitations
  (e.g. a rule verified against data assembled via `model_construct()`
  to exercise a branch that normal validation makes otherwise
  unreachable)

### Examples & documentation drift guard

- Six bundled example YAML drawings under `examples/`, one clean and
  five each demonstrating a distinct rule (including a `WARNING`, and
  one exercising `related_dimension_ids` + `Dimension.role`)
- `scripts/generate_examples_readme.py` regenerates the captured
  command/output/exit-code blocks in `examples/README.md` from the
  real CLI; `tests/test_examples_readme.py` runs it in `--check` mode
  as part of the normal test suite, failing the build if committed
  documentation ever drifts from real behavior again
- Closes a real regression: the documented rule count and example
  output silently went stale for three sprints (Sprint 8–10) with
  nothing catching it — see `ARCHITECTURE.md#documentation-drift-guard`

### `FeatureControlFrame` → `Dimension` linkage

- `FeatureControlFrame.related_dimension_ids: list[str]`, default `[]`,
  declaring which `Dimension`(s) establish or support a feature control
  frame (e.g. the basic location dimensions a position tolerance
  applies to)
- Structural validation only: every id must be a non-empty string, no
  duplicate ids within one `FeatureControlFrame`
- `Dimension.id` is unique within its owning `Feature` (not
  drawing-wide) — enforced on `Feature.dimensions`, since
  `related_dimension_ids` resolution only ever looks at the same
  feature's dimensions and needs that lookup to be unambiguous
- Deliberately does not check that referenced ids exist elsewhere on
  the `Drawing` — that's cross-object referential integrity, left to
  the rule layer, same as datum label references
- Backward-compatible: optional field with an empty-list default, so
  every existing YAML drawing still validates unchanged
- See `ARCHITECTURE.md#dimension-linkage` for the full design and
  validation-boundary rationale

### Dimension-aware rules (added on `related_dimension_ids`)

- `related-dimension-must-be-defined`: every related dimension id must
  resolve against the owning feature's own dimensions
- `position-related-dimension-must-be-basic`: a position FCF's related
  dimensions must be basic (no tolerance)
- `related-dimension-must-not-be-reference`: a related dimension must
  not be a reference (for-information-only) dimension
- `angularity-related-dimension-must-be-angular`: an angularity FCF's
  related dimensions must be angular dimensions
- `position-related-dimension-must-be-location`: a position FCF's
  related dimensions must have role `LOCATION`
- `angularity-related-dimension-must-be-orientation`: an angularity
  FCF's related dimensions must have role `ORIENTATION`
- All six skip dimension ids that don't resolve rather than guessing
  about a dimension that may not exist; `related-dimension-must-be-defined`
  is the rule responsible for reporting those

### `Dimension.role`

- `Dimension.role: DimensionRole`, default `DimensionRole.OTHER`,
  declaring what a dimension is used for: `SIZE`, `LOCATION`,
  `ORIENTATION`, or `OTHER`
- Deliberately excludes a `REFERENCE` member — `Dimension.is_reference`
  already owns that signal, so the two fields never need to be kept in
  sync with each other
- Never inferred from `dimension_type`: an `ANGULAR` dimension isn't
  automatically `ORIENTATION`, a `DIAMETER` dimension isn't
  automatically `SIZE` — an un-classified dimension defaults to `OTHER`
  rather than being guessed
- Backward-compatible: optional field with a concrete default, so every
  existing YAML/JSON `Dimension` still validates unchanged
- See `ARCHITECTURE.md#dimension-role` for the full design and why it's
  a separate field from `dimension_type` and `is_reference`

## Planned

- More GD&T rules: additional orientation/form checks, profile,
  tolerance-value sanity checks
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

# ARCHITECTURE.md

## Current state

Sprint 1 added the domain model layer (`gdt_coach.models`). Sprint 2
added the rule engine *infrastructure* (`gdt_coach.rules`): a rule base
class, a registry, an engine, and the findings/severity/category/
standard vocabulary. Sprint 3 added the first five concrete GD&T rules
under `gdt_coach.rules.checks`. Sprint 4 adds a YAML ingest layer
(`gdt_coach.ingest`) that loads a `Drawing` from a YAML file. There is
still no CLI wiring to actually run the engine, and no other input
format (PDF/DXF/CAD) is supported.

## Layout

- `src/gdt_coach/` — the installable package (src layout, keeps the
  package importable only from its installed form, avoiding accidental
  imports from a repo-root copy).
  - `models/` — Pydantic domain models (`Drawing`, `Feature`, `Datum`,
    `Dimension`, `FeatureControlFrame`, `Tolerance`, and their
    enumerations). See "Domain model" below.
  - `rules/` — the rule engine: `Rule` base class, `Finding` model,
    `RuleRegistry`, `RuleEngine`, and the `Severity`/`RuleCategory`/
    `Standard` enums. See "Rule engine" below.
    - `checks/` — concrete `Rule` subclasses, one module per rule. See
      "Concrete rules" below.
  - `ingest/` — YAML loading: turns a YAML document into a validated
    `Drawing`. See "Ingest layer" below.
- `tests/` — pytest suite, mirrors the package layout (`tests/models/`
  mirrors `src/gdt_coach/models/`, `tests/rules/` mirrors
  `src/gdt_coach/rules/`, `tests/rules/checks/` mirrors
  `src/gdt_coach/rules/checks/`, `tests/ingest/` mirrors
  `src/gdt_coach/ingest/`).
- `examples/` — sample YAML drawings used by `tests/ingest/` and as
  reference documentation; not shipped as part of the installed
  package.
- `docs/` — project documentation beyond the top-level `*.md` files.
- `scripts/` — one-off or maintenance scripts not part of the package.

## Domain model

`gdt_coach.models` holds the GD&T domain shape as Pydantic v2 models,
based on ASME Y14.5 concepts:

- `Drawing` — aggregate root: title/number/revision/default unit, plus
  the `Feature` and `Datum` collections. Rejects duplicate feature ids
  and duplicate datum labels within the same drawing.
- `Feature` — a physical feature of a part (hole, slot, pin, ...),
  holding its own `Dimension` and `FeatureControlFrame` lists.
- `Datum` — a lettered datum feature reference (`A`, `B`, ...) and the
  geometric type it simulates (plane, axis, point, line, center plane).
- `Dimension` — a nominal value with a unit and an optional `Tolerance`
  (absence of a tolerance means the dimension is basic/theoretically
  exact). Cross-checks type/unit/value consistency (e.g. an angular
  dimension must use degrees; a diameter must be positive).
- `FeatureControlFrame` — characteristic symbol + `Tolerance` + ordered
  `DatumReference` list (a small nested model pairing a datum label
  with its own material condition modifier), plus common frame
  modifiers (`all_around`, `all_over`, `free_state`,
  `statistical_tolerance`).
- `Tolerance` — shared by `Dimension` (a size tolerance range) and
  `FeatureControlFrame` (a geometric tolerance zone, represented as
  `upper_deviation == lower_deviation`), plus zone shape, material
  condition, and optional projected-zone height.
- `enums.py` — `GeometricCharacteristic` (the 14 ASME symbols),
  `MaterialCondition`, `DatumFeatureType`, `FeatureType`,
  `DimensionType`, `ToleranceZoneShape`, `Unit`. All are `enum.StrEnum`.

All models inherit `GDTBaseModel` (`models/base.py`), which forbids
unknown fields and re-validates on attribute assignment
(`extra="forbid"`, `validate_assignment=True`).

### Validation philosophy

Model validators only reject data that is *structurally impossible*
(negative tolerance, a diameter of zero, duplicate datum labels,
mismatched dimension type/unit). They never encode GD&T interpretation
rules (e.g. "flatness cannot reference a datum") — that belongs to a
future rule engine that operates on a fully-assembled `Drawing`.
Referential integrity between id fields (`Feature.id`,
`Datum.referenced_feature_id`, `FeatureControlFrame.feature_id`) is
intentionally not enforced yet, for the same reason.

## Rule engine

`gdt_coach.rules` is infrastructure only — it defines how a rule looks
and how rules are run, not any actual GD&T rule:

- `Rule` (`base.py`) — abstract base class. A concrete rule declares
  six class attributes (`id`, `title`, `severity`, `standard`,
  `category`, `explanation`) and implements `check(self, drawing:
  Drawing) -> list[Finding]`. Rules are stateless: one instance is
  created and reused for every drawing it evaluates.
- `Finding` (`finding.py`) — a Pydantic model for one reported
  violation: a copy of the rule's `title`/`severity`/`standard`/
  `category` (so a finding is self-contained without looking the rule
  back up), a `message`, and optional locator fields (`feature_id`,
  `dimension_id`, `fcf_id`, `datum_label`) identifying which drawing
  element it's about.
- `RuleRegistry` (`registry.py`) — a keyed collection of rule
  instances. `register()` instantiates a `Rule` subclass, validates
  that all six metadata fields are present (raising `InvalidRuleError`
  if not) and that its `id` is unique (raising `DuplicateRuleIdError`
  if not), then stores it. It doubles as a class decorator
  (`@registry.register`). `filter()` narrows by category/standard/
  severity. A module-level `default_registry` is used when no explicit
  registry is supplied.
- `RuleEngine` (`engine.py`) — runs every rule in a registry (or a
  `categories`/`standard`-filtered subset) against one `Drawing` and
  concatenates the findings. The engine has no knowledge of any
  specific rule.

**Extensibility**: a new rule is a new `Rule` subclass in its own
module, registered with `@default_registry.register` (or any other
registry instance). Nothing in `base.py`, `registry.py`, or `engine.py`
needs to change for that rule to start running.

## Concrete rules

`gdt_coach.rules.checks` holds the first five deterministic GD&T rules,
one module per rule, each self-registering against `default_registry`
via `@default_registry.register`. Importing `gdt_coach.rules.checks`
(the package `__init__.py` imports every rule module) is what makes
that registration happen — importing `gdt_coach.rules` alone still
does not, so the infrastructure package stays free of any concrete
rule. This resolves the "where do rules live / how do they get
imported" question left open after Sprint 2.

| Rule | id | Category | Standard |
|---|---|---|---|
| Flatness cannot reference datums | `flatness-no-datum-references` | `FEATURE_CONTROL_FRAME` | ASME Y14.5-2018 |
| Straightness cannot reference datums | `straightness-no-datum-references` | `FEATURE_CONTROL_FRAME` | ASME Y14.5-2018 |
| No duplicate datum references in one FCF | `fcf-duplicate-datum-references` | `FEATURE_CONTROL_FRAME` | GENERAL |
| Position must reference at least one datum | `position-requires-datum-reference` | `FEATURE_CONTROL_FRAME` | ASME Y14.5-2018 |
| Projected zone requires position | `projected-zone-requires-position` | `TOLERANCE` | ASME Y14.5-2018 |

All five are `Severity.ERROR` and purely deterministic: every field
they inspect (`characteristic`, `datum_references`,
`tolerance.projected_zone_height`) is always present and unambiguous
on a constructed `Drawing`, so none of them has a genuinely
indeterminate case given the current domain model. There is also no
"indeterminate" finding concept in the architecture yet (`Severity` has
no `UNKNOWN`/`INDETERMINATE` member, and `Rule.check` must return a
concrete `list[Finding]`) — adding one is future work if a later rule
genuinely needs it.

**Known limitation**: `fcf-duplicate-datum-references` duplicates a
check the domain model already performs.
`FeatureControlFrame.datum_references` has its own Pydantic validator
that rejects duplicate labels at construction time (Sprint 1), so this
rule's FAIL branch is unreachable for any `Drawing` built through
normal, validated constructors — it only fires against a tree
assembled via `model_construct()` (see
`tests/rules/checks/test_duplicate_datum_references.py`), simulating
data that bypassed validation (e.g. a future parser optimizing for
speed). It is kept as defense-in-depth rather than removed, since the
rule engine should not have to trust that every `Drawing` it ever
receives was built the "normal" way.

## Ingest layer

`gdt_coach.ingest` is a thin translation layer: it turns YAML text into
a plain dict (via `yaml.safe_load`) and hands that straight to
`Drawing.model_validate()`. It adds no GD&T semantics and no extra
validation of its own — every check that runs is either "is this valid
YAML" or a check `Drawing` (and its nested models) already performs.

- `yaml_loader.py` — `load_drawing_from_yaml_string(text, *,
  source_name=...)` and `load_drawing_from_yaml_file(path)`. Both
  return a `Drawing` or raise.
- `exceptions.py` — `YamlParseError` (not valid YAML, or not a mapping,
  or an empty document) and `DrawingValidationError` (parses fine but
  fails `Drawing`'s validation — wraps the underlying Pydantic
  `ValidationError`). Both subclass `IngestError`.

**YAML schema**: the YAML mirrors `gdt_coach.models` field names and
nesting directly (`Drawing` -> `features`/`datums` ->
`dimensions`/`feature_control_frames` -> `tolerance`/
`datum_references`) — there is no separate/versioned wire schema to
keep in sync. Enum fields (`feature_type`, `dimension_type`,
`characteristic`, `unit`, `zone_shape`, `material_condition`, ...) use
the same lowercase string values as each enum's `.value` (e.g.
`characteristic: position`, `unit: mm`). Because `GDTBaseModel` sets
`extra="forbid"`, an unrecognized YAML key is a validation error rather
than being silently ignored. See `examples/*.yaml` for complete
drawings and the README for a field-by-field walkthrough.

**Deliberately not done here**: running the rule engine (the loader
only builds a `Drawing`; nothing calls `RuleEngine`), CLI wiring, and
any non-YAML input format (PDF/DXF/CAD).

## Tooling

| Concern       | Tool         | Config location         |
|---------------|--------------|--------------------------|
| Packaging     | Hatchling    | `pyproject.toml`         |
| Domain models | Pydantic v2  | `pyproject.toml` (dependency), `src/gdt_coach/models/` |
| Rule engine   | stdlib only  | `src/gdt_coach/rules/`   |
| YAML ingest   | PyYAML       | `pyproject.toml` (dependency), `src/gdt_coach/ingest/` |
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

- Whether `gdt_coach.rules.checks` needs auto-discovery (e.g. scanning
  the package for `Rule` subclasses) once there are enough rules that
  hand-maintaining `checks/__init__.py`'s import list becomes tedious.
- Whether/where cross-model referential integrity (dangling
  `feature_id`, etc.) gets checked — plausibly as rules themselves
  rather than special-cased in the engine.
- CLI wiring to actually run `RuleEngine` against a drawing and print
  `Finding`s (and to call `gdt_coach.ingest` to build that drawing).
- Whether a versioned wire schema (e.g. a `schema_version` field, or
  YAML that doesn't mirror `gdt_coach.models` 1:1) is needed once the
  domain model changes in ways that would otherwise break existing
  YAML files.
- Other input formats (PDF/DXF/CAD) — explicitly out of scope for now.
- Data storage / persistence approach, if any.

Update this document as real architecture decisions are made.

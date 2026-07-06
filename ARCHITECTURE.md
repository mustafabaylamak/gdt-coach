# ARCHITECTURE.md

## Current state

Sprint 1 added the domain model layer (`gdt_coach.models`). Sprint 2
added the rule engine *infrastructure* (`gdt_coach.rules`): a rule base
class, a registry, an engine, and the findings/severity/category/
standard vocabulary. Sprint 3 added the first five concrete GD&T rules
under `gdt_coach.rules.checks`. Sprint 4 added a YAML ingest layer
(`gdt_coach.ingest`) that loads a `Drawing` from a YAML file. Sprint 5
wired all of this into the CLI: `gdt-coach check <path>` loads a YAML
drawing, runs the rule engine, and prints a report. Sprint 6 hardened
that wiring: one canonical `ALL_RULE_CLASSES` tuple replaces four
separate hardcoded rule lists, and `check` gained `--category`/
`--standard` filters and a `--json` output mode. No other input format
(PDF/DXF/CAD) is supported, and there is no Markdown/HTML report output.

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

`gdt_coach.rules.checks` holds 14 deterministic GD&T rules (5 from
Sprint 3, 9 from Sprint 7), one module per rule, each self-registering
against `default_registry` via `@default_registry.register`. Importing
`gdt_coach.rules.checks` (the package `__init__.py` imports every rule
module) is what makes that registration happen — importing
`gdt_coach.rules` alone still does not, so the infrastructure package
stays free of any concrete rule. This resolves the "where do rules
live / how do they get imported" question left open after Sprint 2.

`checks/__init__.py` also exposes `ALL_RULE_CLASSES` — a plain
`tuple[type[Rule], ...]` listing every rule class. This is the single
source of truth for "every concrete rule that exists": the CLI
(`cli.py`) and the tests that need to enumerate all rules
(`tests/rules/checks/test_registration.py`,
`tests/ingest/test_examples.py`) all import this tuple instead of each
keeping their own copy of the rule-class list, which is what Sprints
3–5 had actually done (four separate hardcoded lists of the same five
classes, found during a Sprint 5 architecture review and fixed in
Sprint 6). Adding rule #6 now means: write its module, add one line to
`checks/__init__.py`'s imports and `ALL_RULE_CLASSES` tuple, and write
its test — nothing else needs to change. There is still no
auto-discovery (e.g. scanning the package for `Rule` subclasses);
that's deferred until the hand-maintained list itself becomes the
bottleneck.

### Sprint 3 rules

| Rule | id | Category | Standard |
|---|---|---|---|
| Flatness cannot reference datums | `flatness-no-datum-references` | `FEATURE_CONTROL_FRAME` | ASME Y14.5-2018 |
| Straightness cannot reference datums | `straightness-no-datum-references` | `FEATURE_CONTROL_FRAME` | ASME Y14.5-2018 |
| No duplicate datum references in one FCF | `fcf-duplicate-datum-references` | `FEATURE_CONTROL_FRAME` | GENERAL |
| Position must reference at least one datum | `position-requires-datum-reference` | `FEATURE_CONTROL_FRAME` | ASME Y14.5-2018 |
| Projected zone requires position | `projected-zone-requires-position` | `TOLERANCE` | ASME Y14.5-2018 |

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

### Sprint 7 rules

Selected from a 30-rule ASME Y14.5 roadmap via an architecture audit
that checked every proposed rule against the actual domain model (not
just the roadmap's assumptions) and picked the 8 highest-value items
implementable with zero model changes and zero heuristics. The
`FORM.001` roadmap item ("form tolerances take no datums") was already
half-implemented in Sprint 3 (flatness, straightness); Sprint 7
completes it with circularity and cylindricity, reusing the Sprint 6
parametrized test module (`test_form_tolerance_no_datum_rules.py`) for
all four rather than writing bespoke files.

| Rule | id | Category | Standard | Severity |
|---|---|---|---|---|
| Referenced datums must be defined | `datum-reference-must-be-defined` | `FEATURE_CONTROL_FRAME` | GENERAL | ERROR |
| Concentricity/symmetry deprecated | `concentricity-symmetry-deprecated` | `FEATURE_CONTROL_FRAME` | ASME Y14.5-2018 | WARNING |
| Circularity cannot reference datums | `circularity-no-datum-references` | `FEATURE_CONTROL_FRAME` | ASME Y14.5-2018 | ERROR |
| Cylindricity cannot reference datums | `cylindricity-no-datum-references` | `FEATURE_CONTROL_FRAME` | ASME Y14.5-2018 | ERROR |
| Straightness/flatness MMC only on FOS | `form-mmc-requires-feature-of-size` | `FEATURE_CONTROL_FRAME` | ASME Y14.5-2018 | ERROR |
| Orientation requires ≥1 datum | `orientation-requires-datum-reference` | `FEATURE_CONTROL_FRAME` | ASME Y14.5-2018 | ERROR |
| Position applies only to a Feature of Size | `position-requires-feature-of-size` | `FEATURE_CONTROL_FRAME` | ASME Y14.5-2018 | ERROR |
| MMC/LMC on position requires a Feature of Size | `position-material-condition-requires-feature-of-size` | `TOLERANCE` | ASME Y14.5-2018 | ERROR |
| Runout is always RFS | `runout-always-rfs` | `FEATURE_CONTROL_FRAME` | ASME Y14.5-2018 | ERROR |

**Scope decision**: `position-material-condition-requires-feature-of-size`
(POS.003, "MMC/LMC only on FOS tolerances" in the roadmap) is scoped to
`characteristic == POSITION` only, matching its placement in the
roadmap's position-tolerance tier, rather than generalized across
every characteristic that can carry a material modifier. This avoids
overlapping with `form-mmc-requires-feature-of-size` (which already
owns straightness/flatness); a broader version was out of scope for
this sprint.

**Known limitations** (documented per-rule in each module's docstring,
not guessed around):

- `concentricity-symmetry-deprecated` is `Severity.WARNING`, not
  `ERROR`, because `Drawing` has no field recording which standard
  *edition* it targets. The rule cannot tell an ASME Y14.5-2018 drawing
  (where these symbols are removed) from a 2009 one (where they are
  still valid), so it always fires and says so in the message rather
  than silently assuming 2018.
- `form-mmc-requires-feature-of-size`, `position-requires-feature-of-size`,
  and `position-material-condition-requires-feature-of-size` all trust
  `Feature.feature_of_size` as ground truth. It defaults to `False` and
  is not inferred from `feature_type` or anything else — a genuine
  Feature of Size left un-flagged in the source data will produce a
  false-positive finding. No heuristic (e.g. guessing FOS-ness from
  `feature_type in {HOLE, CYLINDER, ...}`) was introduced to paper over
  this, per this sprint's explicit requirement.

All 14 rules are purely deterministic given the current domain model
(no genuinely indeterminate case), and there is still no
"indeterminate" finding concept in the architecture (`Severity` has no
`UNKNOWN`/`INDETERMINATE` member, and `Rule.check` must return a
concrete `list[Finding]`) — adding one is future work if a later rule
genuinely needs it.

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

**Deliberately not done here**: any non-YAML input format (PDF/DXF/CAD).
The ingest layer itself still only builds a `Drawing` and never calls
`RuleEngine` — that wiring lives in the CLI (see "Entry points" below).

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

`gdt_coach.cli:main` is registered as the `gdt-coach` console script,
built with `argparse` subparsers.

- `gdt-coach --version` / `gdt-coach --help` — unchanged since Sprint 0.
- `gdt-coach check <path> [--category CATEGORY]... [--standard STANDARD] [--json]`
  — the only place in the codebase that wires the ingest layer to the
  rule engine:
  1. `gdt_coach.ingest.load_drawing_from_yaml_file(path)` loads the
     `Drawing`. `IngestError` or `OSError` (e.g. a missing file) is
     caught, printed to stderr, and maps to **exit code 2**.
  2. `--category` (repeatable) and `--standard` are parsed into a
     `set[RuleCategory] | None` and `Standard | None` and passed
     straight through to the existing `RuleEngine.run(categories=,
     standard=)` parameters (unchanged since Sprint 2) — the CLI adds
     no filtering logic of its own beyond converting strings to enum
     members. An invalid value (not a real category/standard) is
     caught, an error listing the valid options is printed to stderr,
     and this also maps to **exit code 2**.
  3. A `RuleRegistry` is built and populated from `ALL_RULE_CLASSES`
     *inside the CLI module* per invocation, not via the shared
     `default_registry` — `check` doesn't depend on what else in the
     process may have imported or cleared the global registry.
     `RuleEngine` itself is unchanged.
  4. By default, output is the plain-text report: one block per
     finding (rule id, severity, title, message, and any of
     `feature`/`dimension`/`fcf`/`datum` that are set), followed by a
     per-severity summary count. `--json` instead prints one JSON
     object (`path`, `drawing`, `rules_run`, `findings` — each
     `Finding.model_dump(mode="json")` — and `summary`); errors are
     always plain text on stderr regardless of `--json`, since a
     load/filter failure means there is no report to format.
  5. **Exit code 0** if there are no findings, **exit code 1** if there
     are any (severity is not currently weighed — any finding at all
     means exit 1), **exit code 2** for any load or filter-value error.
- There is no Markdown/HTML report output yet — only plain-text and
  JSON as described above.

## Decisions to be made

- Whether `gdt_coach.rules.checks` needs true auto-discovery (e.g.
  scanning the package for `Rule` subclasses) once hand-maintaining
  `ALL_RULE_CLASSES` and `checks/__init__.py`'s import list itself
  becomes tedious — deferred again in Sprint 7 (now 14 rules) as still
  manageable by hand; revisit once the list is meaningfully larger.
- Whether/where cross-model referential integrity (dangling
  `feature_id`, etc.) gets checked — plausibly as rules themselves
  rather than special-cased in the engine. Sprint 7's
  `datum-reference-must-be-defined` is exactly this pattern applied to
  dangling datum labels; the same approach could extend to
  `Datum.referenced_feature_id` and `FeatureControlFrame.feature_id`.
- A link from `FeatureControlFrame` to the `Dimension`(s) that locate
  or orient it (e.g. `related_dimension_ids: list[str] | None`) — a
  small model change identified by the Sprint 7 audit that would
  unlock rules like "position requires basic location dimensions" or
  "angularity requires a basic angle," neither implementable now
  without an ambiguous heuristic across multiple dimensions/FCFs on one
  `Feature`.
- A composite/multi-segment `FeatureControlFrame` representation — a
  major model change (also identified by the Sprint 7 audit) needed
  for any composite-tolerancing rule (e.g. "lower segment tolerance
  tighter than upper segment"); `FeatureControlFrame` currently has
  exactly one tolerance and one datum reference list, with no concept
  of segments at all.
- Whether `Drawing` should record which standard *edition* it targets.
  `concentricity-symmetry-deprecated` (Sprint 7) needs this to avoid
  false positives on drawings intentionally authored to ASME
  Y14.5-2009 or ISO 1101, and currently works around the gap by using
  `Severity.WARNING` instead of `ERROR` and saying so in the message.
- Whether exit code 1 should ever distinguish by severity (e.g. only
  `ERROR`/`CRITICAL` findings fail the process, `WARNING`/`INFO` don't)
  — currently any finding at all produces exit code 1.
- Markdown/HTML report output (JSON is done as of Sprint 6), for
  consumption by CI or other tooling instead of the human-readable
  terminal report.
- A formal JSON Schema (Pydantic can generate one via
  `model_json_schema()`) as an integration contract for `Finding`/
  `Drawing`, once something external actually needs to consume
  `--json` output against a fixed contract.
- Whether a versioned wire schema (e.g. a `schema_version` field, or
  YAML that doesn't mirror `gdt_coach.models` 1:1) is needed once the
  domain model changes in ways that would otherwise break existing
  YAML files.
- A documented policy on paraphrasing vs. quoting ASME Y14.5/ISO 1101
  in rule `explanation` text — no verbatim standard text exists today,
  but nothing currently stops a future rule from copying it in.
- Other input formats (PDF/DXF/CAD) — explicitly out of scope for now.
- Data storage / persistence approach, if any.

Update this document as real architecture decisions are made.

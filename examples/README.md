# Examples

Seven runnable drawings: six YAML (one clean, five each demonstrating a
distinct rule, including one `WARNING`-severity example and one
demonstrating the Sprint 9/10 dimension-aware rules) and one CSV
(Sprint 14 — see "CSV example" below for what that format is and, more
importantly, isn't). Every
`<!-- gdt-coach:example KEY --> ... <!-- /gdt-coach:example -->` block
below is a real, generated capture of `gdt-coach check` run against
these exact files, never hand-written — see "Keeping this file
accurate" at the bottom for how that's enforced.

Install the package first (see the root [README.md](../README.md#installation)):

```bash
pip install -e ".[dev]"
```

Then, from the repository root:

```bash
gdt-coach check examples/<file>.yaml
```

## `valid_position.yaml` — clean drawing

A position tolerance with a full three-datum reference frame, on a
feature correctly marked as a Feature of Size. Also demonstrates
correct use of the Sprint 8-10 dimension-linkage fields: the position
FCF's `related_dimension_ids` points to a basic dimension explicitly
marked `role: location`, and the hole's own diameter is marked
`role: size`. Passes every rule in the current rule set.

<!-- gdt-coach:example valid_position -->
```
$ gdt-coach check examples/valid_position.yaml
Checked examples/valid_position.yaml -- drawing 'dwg-001' ('Mounting Bracket')
Rules run: 20

No findings.
```

Exit code: `0`
<!-- /gdt-coach:example -->

## `invalid_flatness_with_datum.yaml` — form tolerance with a datum

Flatness is a form tolerance and must never reference a datum. This
file loads into a perfectly valid `Drawing` — the domain model doesn't
enforce GD&T semantics, only the rule engine does.

<!-- gdt-coach:example invalid_flatness_with_datum -->
```
$ gdt-coach check examples/invalid_flatness_with_datum.yaml
Checked examples/invalid_flatness_with_datum.yaml -- drawing 'dwg-002' ('Cover Plate')
Rules run: 20

[ERROR] flatness-no-datum-references: Flatness cannot reference datums
  flatness feature control frame 'fcf-1' references datum(s) ['A'], but flatness must not reference any datum
  location: feature=feat-surface-1 fcf=fcf-1

1 finding(s): 1 error
```

Exit code: `1`
<!-- /gdt-coach:example -->

## `invalid_projected_zone.yaml` — projected zone on the wrong characteristic

A projected tolerance zone is only meaningful on a position tolerance;
here it's applied to perpendicularity instead.

<!-- gdt-coach:example invalid_projected_zone -->
```
$ gdt-coach check examples/invalid_projected_zone.yaml
Checked examples/invalid_projected_zone.yaml -- drawing 'dwg-003' ('Threaded Plate')
Rules run: 20

[ERROR] projected-zone-requires-position: Projected tolerance zone requires a position tolerance
  feature control frame 'fcf-1' specifies a projected tolerance zone but its characteristic is 'perpendicularity', not position
  location: feature=feat-hole-1 fcf=fcf-1

1 finding(s): 1 error
```

Exit code: `1`
<!-- /gdt-coach:example -->

## `invalid_concentricity_deprecated.yaml` — deprecated characteristic (warning, not error)

Concentricity was removed from ASME Y14.5 in the 2018 edition. This is
the only bundled example that produces a `WARNING` instead of an
`ERROR` — the rule can't tell whether this drawing intentionally
targets an earlier edition (where concentricity is still valid), so it
warns rather than asserting a hard violation.

<!-- gdt-coach:example invalid_concentricity_deprecated -->
```
$ gdt-coach check examples/invalid_concentricity_deprecated.yaml
Checked examples/invalid_concentricity_deprecated.yaml -- drawing 'dwg-004' ('Sleeve Bearing')
Rules run: 20

[WARNING] concentricity-symmetry-deprecated: Concentricity and symmetry are deprecated (ASME Y14.5-2018)
  feature control frame 'fcf-1' uses 'concentricity', which was removed in ASME Y14.5-2018 (consider position instead); this warning does not apply if the drawing targets an earlier edition
  location: feature=feat-bore-1 fcf=fcf-1

1 finding(s): 1 warning
```

Exit code: `1`
<!-- /gdt-coach:example -->

Any finding at all produces exit code 1, regardless of severity — see
[ARCHITECTURE.md](../ARCHITECTURE.md#entry-points). That applies here
too: a `WARNING` still produces a nonzero exit code.

## `invalid_position_without_feature_of_size.yaml` — position on a non-FOS feature

Position tolerance locates the derived center point, axis, or center
plane of a **Feature of Size**. This feature has a correctly-defined
datum reference (so the datum-related rules pass) but isn't marked as a
Feature of Size.

<!-- gdt-coach:example invalid_position_without_feature_of_size -->
```
$ gdt-coach check examples/invalid_position_without_feature_of_size.yaml
Checked examples/invalid_position_without_feature_of_size.yaml -- drawing 'dwg-005' ('Locating Slot Plate')
Rules run: 20

[ERROR] position-requires-feature-of-size: Position applies only to a Feature of Size
  position feature control frame 'fcf-1' is on feature 'feat-slot-1', which is not marked as a Feature of Size
  location: feature=feat-slot-1 fcf=fcf-1

1 finding(s): 1 error
```

Exit code: `1`
<!-- /gdt-coach:example -->

## `invalid_position_related_dimension_wrong_role.yaml` — position related to a non-location dimension

A position tolerance's `related_dimension_ids` must point to a
dimension whose `role` is `location`
(`position-related-dimension-must-be-location`, Sprint 10). Here the
related dimension is basic and not a reference dimension — it would
pass `position-related-dimension-must-be-basic` and
`related-dimension-must-not-be-reference` — but its declared `role` is
`size`, not `location`, so this is the one rule it violates.

<!-- gdt-coach:example invalid_position_related_dimension_wrong_role -->
```
$ gdt-coach check examples/invalid_position_related_dimension_wrong_role.yaml
Checked examples/invalid_position_related_dimension_wrong_role.yaml -- drawing 'dwg-006' ('Bracket Arm')
Rules run: 20

[ERROR] position-related-dimension-must-be-location: Position-related dimensions must be location dimensions
  position feature control frame 'fcf-1' relates to non-location dimension(s) ['dim-2']; a dimension establishing a true position must have role LOCATION
  location: feature=feat-hole-1 fcf=fcf-1

1 finding(s): 1 error
```

Exit code: `1`
<!-- /gdt-coach:example -->

## `invalid_datum_reference_undefined.csv` — CSV example, and what CSV can't do

CSV (Sprint 14) is a second, **intentionally narrow** input format —
not a technical-drawing replacement, and its existence doesn't imply
readiness for PDF or any other unstructured format. It cannot declare
`Datum` objects, so a CSV-sourced `Drawing` always has `datums == []`.
This file's position tolerance references datum `A` via
`fcf_datum_refs` — a real, well-formed reference — but because CSV has
no way to *define* that datum, `datum-reference-must-be-defined` (an
existing, YAML-format-agnostic rule) correctly flags it as undefined.
This is expected: the limitation is rejected loudly by an existing
rule, not silently approximated. See the root
[README.md](../README.md#csv-input-a-second-narrow-format) for the
full CSV contract and what it deliberately does not support.

<!-- gdt-coach:example invalid_datum_reference_undefined -->
```
$ gdt-coach check examples/invalid_datum_reference_undefined.csv
Checked examples/invalid_datum_reference_undefined.csv -- drawing 'dwg-007' ('CSV Bracket')
Rules run: 20

[ERROR] datum-reference-must-be-defined: Referenced datums must be defined
  feature control frame 'fcf-1' references undefined datum(s) ['A']; no datum with that label is defined on this drawing
  location: feature=feat-hole-1 fcf=fcf-1

1 finding(s): 1 error
```

Exit code: `1`
<!-- /gdt-coach:example -->

## Try the filters and JSON output yourself

```bash
# Only run rules in one category
gdt-coach check examples/invalid_flatness_with_datum.yaml --category tolerance

# Machine-readable output
gdt-coach check examples/invalid_position_without_feature_of_size.yaml --json
```

See the root [README.md](../README.md) for the full CLI reference and
[ARCHITECTURE.md](../ARCHITECTURE.md#concrete-rules) for every rule's
id, category, standard, and documented limitations.

## Keeping this file accurate

Every `<!-- gdt-coach:example KEY --> ... <!-- /gdt-coach:example -->`
block above is generated, not hand-written: it's the real stdout and
exit code of `gdt-coach check` run against the matching example file
under `examples/` (YAML or CSV), produced by running the actual CLI
(`gdt_coach.cli.main`, the same function the installed console script
calls). Regenerate it after any change that could affect a rule's
output (a new rule, a changed message, a new example file):

```bash
python scripts/generate_examples_readme.py
```

`tests/test_examples_readme.py` runs the same regeneration in "check"
mode (`python scripts/generate_examples_readme.py --check`) as part of
the normal test suite, so CI fails if this file is ever out of sync
with real CLI behavior — this is the guardrail against the same
documentation drift recurring silently.

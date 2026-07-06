# Examples

Five runnable YAML drawings, one clean and four each demonstrating a
different rule. All output below is a real, unedited capture of
`gdt-coach check` run against these exact files — run any command
yourself to reproduce it.

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
feature correctly marked as a Feature of Size. Passes all 14 rules.

```
$ gdt-coach check examples/valid_position.yaml
Checked examples/valid_position.yaml -- drawing 'dwg-001' ('Mounting Bracket')
Rules run: 14

No findings.
```

Exit code: `0`

## `invalid_flatness_with_datum.yaml` — form tolerance with a datum

Flatness is a form tolerance and must never reference a datum. This
file loads into a perfectly valid `Drawing` — the domain model doesn't
enforce GD&T semantics, only the rule engine does.

```
$ gdt-coach check examples/invalid_flatness_with_datum.yaml
Checked examples/invalid_flatness_with_datum.yaml -- drawing 'dwg-002' ('Cover Plate')
Rules run: 14

[ERROR] flatness-no-datum-references: Flatness cannot reference datums
  flatness feature control frame 'fcf-1' references datum(s) ['A'], but flatness must not reference any datum
  location: feature=feat-surface-1 fcf=fcf-1

1 finding(s): 1 error
```

Exit code: `1`

## `invalid_projected_zone.yaml` — projected zone on the wrong characteristic

A projected tolerance zone is only meaningful on a position tolerance;
here it's applied to perpendicularity instead.

```
$ gdt-coach check examples/invalid_projected_zone.yaml
Checked examples/invalid_projected_zone.yaml -- drawing 'dwg-003' ('Threaded Plate')
Rules run: 14

[ERROR] projected-zone-requires-position: Projected tolerance zone requires a position tolerance
  feature control frame 'fcf-1' specifies a projected tolerance zone but its characteristic is 'perpendicularity', not position
  location: feature=feat-hole-1 fcf=fcf-1

1 finding(s): 1 error
```

Exit code: `1`

## `invalid_concentricity_deprecated.yaml` — deprecated characteristic (warning, not error)

Concentricity was removed from ASME Y14.5 in the 2018 edition. This is
the only bundled example that produces a `WARNING` instead of an
`ERROR` — the rule can't tell whether this drawing intentionally
targets an earlier edition (where concentricity is still valid), so it
warns rather than asserting a hard violation.

```
$ gdt-coach check examples/invalid_concentricity_deprecated.yaml
Checked examples/invalid_concentricity_deprecated.yaml -- drawing 'dwg-004' ('Sleeve Bearing')
Rules run: 14

[WARNING] concentricity-symmetry-deprecated: Concentricity and symmetry are deprecated (ASME Y14.5-2018)
  feature control frame 'fcf-1' uses 'concentricity', which was removed in ASME Y14.5-2018 (consider position instead); this warning does not apply if the drawing targets an earlier edition
  location: feature=feat-bore-1 fcf=fcf-1

1 finding(s): 1 warning
```

Exit code: `1` (any finding at all produces exit code 1, regardless of
severity — see [ARCHITECTURE.md](../ARCHITECTURE.md#entry-points))

## `invalid_position_without_feature_of_size.yaml` — position on a non-FOS feature

Position tolerance locates the derived center point, axis, or center
plane of a **Feature of Size**. This feature has a correctly-defined
datum reference (so the datum-related rules pass) but isn't marked as a
Feature of Size.

```
$ gdt-coach check examples/invalid_position_without_feature_of_size.yaml
Checked examples/invalid_position_without_feature_of_size.yaml -- drawing 'dwg-005' ('Locating Slot Plate')
Rules run: 14

[ERROR] position-requires-feature-of-size: Position applies only to a Feature of Size
  position feature control frame 'fcf-1' is on feature 'feat-slot-1', which is not marked as a Feature of Size
  location: feature=feat-slot-1 fcf=fcf-1

1 finding(s): 1 error
```

Exit code: `1`

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

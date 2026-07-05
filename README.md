# gdt-coach

> Domain model, rule engine infrastructure, a first set of five GD&T
> rules, and a YAML loader so far — no CLI wiring yet.

## Requirements

- Python 3.11+

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

## Usage

```bash
gdt-coach --version
```

The GD&T domain model is available as a library:

```python
from gdt_coach.models import Datum, DatumFeatureType, Drawing, Feature, FeatureType

drawing = Drawing(
    id="dwg-1",
    title="Bracket",
    features=[Feature(id="feat-1", feature_type=FeatureType.HOLE)],
    datums=[Datum(label="A", feature_type=DatumFeatureType.PLANE)],
)
```

See [ARCHITECTURE.md](ARCHITECTURE.md#domain-model) for what each model
represents.

Importing `gdt_coach.rules.checks` registers the first five GD&T rules
(datum-reference checks for flatness, straightness, and position, plus
a projected-tolerance-zone check) against the shared registry; running
the engine then checks a drawing against all of them:

```python
import gdt_coach.rules.checks  # noqa: F401  (side effect: registers the rules)
from gdt_coach.rules import RuleEngine

findings = RuleEngine().run(drawing)
for finding in findings:
    print(finding.severity, finding.title, finding.message)
```

See [ARCHITECTURE.md](ARCHITECTURE.md#rule-engine) for how the registry
and engine fit together, and
[ARCHITECTURE.md](ARCHITECTURE.md#concrete-rules) for what each of the
five rules checks.

A `Drawing` can also be loaded from a YAML file instead of being built
by hand in Python:

```python
from gdt_coach.ingest import load_drawing_from_yaml_file

drawing = load_drawing_from_yaml_file("examples/valid_position.yaml")
```

### YAML format

The YAML mirrors the domain model directly: each mapping key is a
`gdt_coach.models` field name, nested the same way the models nest
(`Drawing` → `features`/`datums` → `dimensions`/
`feature_control_frames` → `tolerance`/`datum_references`). Enum fields
use the same lowercase value as the Python enum (e.g.
`characteristic: position`, `unit: mm`, `feature_type: hole`) — see
[enums.py](src/gdt_coach/models/enums.py) for every enum's exact
values. Unknown keys are rejected (the domain model forbids extra
fields), and every validation rule from Sprint 1 (e.g. a diameter must
be positive, tolerances can't be negative) still applies to
YAML-sourced data.

```yaml
id: dwg-001              # Drawing.id (required)
title: Mounting Bracket   # Drawing.title (required)
number: DWG-1001          # optional
revision: A               # optional
default_unit: mm          # optional, default: mm
scale: "1:1"               # optional

datums:                    # list[Datum], optional
  - label: A                # one or two uppercase letters
    feature_type: plane      # plane | axis | point | line | center_plane

features:                   # list[Feature], optional
  - id: feat-hole-1
    feature_type: hole        # hole | cylinder | plane | pin | slot | ...
    quantity: 4                # default: 1
    dimensions:                 # list[Dimension], optional
      - id: dim-1
        dimension_type: diameter # linear | angular | diameter | radius | ...
        nominal_value: 10.0
        unit: mm
        tolerance:                # optional; omit for a basic dimension
          upper_deviation: 0.05
          lower_deviation: 0.05
    feature_control_frames:       # list[FeatureControlFrame], optional
      - id: fcf-1
        characteristic: position   # one of the 14 ASME Y14.5 symbols
        tolerance:
          upper_deviation: 0.25
          lower_deviation: 0.25
          zone_shape: cylindrical    # linear | cylindrical | spherical | total_width
          material_condition: mmc     # rfs | mmc | lmc
        datum_references:
          - datum_label: A
          - datum_label: B
          - datum_label: C
```

See [examples/](examples/) for three complete drawings:
`valid_position.yaml` passes all five Sprint 3 rules;
`invalid_flatness_with_datum.yaml` and `invalid_projected_zone.yaml`
each load into a perfectly valid `Drawing` but are flagged by one rule
when the engine runs against them — loading a YAML file never runs the
rule engine on its own.

## Development

```bash
ruff check .          # lint
ruff format .         # format
mypy src              # type-check
pytest                # test (with coverage)
```

## Project layout

```
gdt-coach/
├── src/gdt_coach/     # importable package (src layout)
│   ├── models/        # GD&T domain models (Pydantic)
│   ├── rules/         # rule engine (base class, registry, engine)
│   │   └── checks/    # concrete GD&T rules, one module per rule
│   └── ingest/        # YAML loader (YAML -> Drawing)
├── tests/             # pytest test suite
├── examples/          # sample YAML drawings (valid and rule-invalid)
├── docs/              # project documentation
├── scripts/           # developer/maintenance scripts
├── .github/workflows/ # CI pipelines
├── pyproject.toml     # packaging, tool, and dependency config
└── .pre-commit-config.yaml
```

See [PROJECT.md](PROJECT.md), [ARCHITECTURE.md](ARCHITECTURE.md), and
[ROADMAP.md](ROADMAP.md) for project intent, design, and planned work.

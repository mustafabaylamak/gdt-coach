# gdt-coach

> Domain model, rule engine infrastructure, and a first set of five
> GD&T rules so far — no CLI wiring and no parsing yet.

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
│   └── rules/         # rule engine (base class, registry, engine)
│       └── checks/    # concrete GD&T rules, one module per rule
├── tests/             # pytest test suite
├── docs/              # project documentation
├── scripts/           # developer/maintenance scripts
├── .github/workflows/ # CI pipelines
├── pyproject.toml     # packaging, tool, and dependency config
└── .pre-commit-config.yaml
```

See [PROJECT.md](PROJECT.md), [ARCHITECTURE.md](ARCHITECTURE.md), and
[ROADMAP.md](ROADMAP.md) for project intent, design, and planned work.

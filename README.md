# gdt-coach

> Domain model and rule engine infrastructure only so far — no GD&T
> rules and no parsing yet.

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

The rule engine can run rules against a drawing, but no concrete GD&T
rule ships yet — this only demonstrates the wiring:

```python
from gdt_coach.rules import Rule, RuleCategory, RuleEngine, Severity, Standard, default_registry


@default_registry.register
class ExampleRule(Rule):
    id = "example-rule"
    title = "Example rule"
    severity = Severity.INFO
    standard = Standard.GENERAL
    category = RuleCategory.GENERAL
    explanation = "Placeholder rule demonstrating registration."

    def check(self, drawing):
        return []


findings = RuleEngine().run(drawing)
```

See [ARCHITECTURE.md](ARCHITECTURE.md#rule-engine) for how the
registry and engine fit together.

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
├── tests/             # pytest test suite
├── docs/              # project documentation
├── scripts/           # developer/maintenance scripts
├── .github/workflows/ # CI pipelines
├── pyproject.toml     # packaging, tool, and dependency config
└── .pre-commit-config.yaml
```

See [PROJECT.md](PROJECT.md), [ARCHITECTURE.md](ARCHITECTURE.md), and
[ROADMAP.md](ROADMAP.md) for project intent, design, and planned work.

# Contributing to gdt-coach

Thanks for considering a contribution. This project favors small,
independent, well-tested changes over large ones — see
[ARCHITECTURE.md](ARCHITECTURE.md) before making structural changes,
so new code fits the existing layering (domain model / rule engine /
concrete rules / ingest / CLI stay decoupled from each other).

## Setup

```bash
git clone https://github.com/mustafabaylamak/gdt-coach.git
cd gdt-coach
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

## Conventions

- Python 3.11+, fully type-annotated; `mypy --strict` must pass on
  `src/`.
- Formatting and linting are handled by Ruff — run `ruff format .` and
  `ruff check --fix .` rather than hand-formatting.
- Prefer `pathlib.Path` over `os.path` (enforced by Ruff's `PTH`
  rules).
- New modules need corresponding tests under `tests/`, mirroring the
  `src/gdt_coach/` layout.
- Rules must be deterministic against the current domain model. If a
  rule can't be verified without guessing (missing or ambiguous data),
  document that as a known limitation on the rule rather than adding a
  heuristic.

## Adding a new GD&T rule

1. Add a module under `src/gdt_coach/rules/checks/`, following the
   pattern of an existing rule (e.g.
   `src/gdt_coach/rules/checks/runout_always_rfs.py`): a `Rule`
   subclass with `id`, `title`, `severity`, `standard`, `category`,
   `explanation`, and a `check(self, drawing) -> list[Finding]` method,
   decorated with `@default_registry.register`.
2. Add it to `ALL_RULE_CLASSES` in
   `src/gdt_coach/rules/checks/__init__.py` — this is the single place
   that enumerates every rule; nothing else needs to change.
3. Write PASS and FAIL tests under `tests/rules/checks/`. If your rule
   checks the same shape as an existing one (e.g. "characteristic X
   must/must not reference datums"), extend the matching parametrized
   test module instead of writing a new bespoke file — see
   `tests/rules/checks/test_form_tolerance_no_datum_rules.py`.
4. Add the rule to the table in `ARCHITECTURE.md#concrete-rules` and to
   `ROADMAP.md` if it closes out a planned item.

Do not modify `RuleEngine`, `RuleRegistry`, or the domain model to add
a rule — if you find yourself needing to, that's a sign the rule needs
a model change first (see "Decisions to be made" in
[ARCHITECTURE.md](ARCHITECTURE.md)), which is a separate, larger
discussion.

## Before opening a pull request

All of the following must pass (CI runs the same checks):

```bash
ruff check . && ruff format --check .
mypy src
pytest
```

- Keep test coverage where it is — don't remove or weaken tests to make
  a change pass.
- Describe *why* the change is needed, not just what it does — this
  matters especially for a new rule (cite the ASME Y14.5 concept in
  your own words; don't paste verbatim text from the standard).
- Avoid force-pushing, amending published commits, or bypassing
  pre-commit hooks (`--no-verify`) on shared branches.

## Reporting bugs / requesting rules

Use the issue templates — a bug report or a new-rule request each ask
for the specific information needed to act on it (a minimal YAML
reproduction for bugs; the ASME Y14.5 clause and expected behavior for
rule requests).

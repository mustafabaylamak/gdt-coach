# PROJECT.md

## What this is

`gdt-coach` is a deterministic rule engine that checks GD&T (Geometric
Dimensioning and Tolerancing) callouts on a drawing against ASME Y14.5
rules. A drawing is described in YAML, loaded into a typed domain model,
and checked against a registry of independent rules; each violation is
reported as a `Finding` with a rule id, severity, and location. It is a
library and a CLI (`gdt-coach check`), not a GUI application or a CAD
plugin.

It is not a CAD system, a geometry/tolerance-stack-up analysis tool, or
a certified compliance checker — see "Non-goals" below.

## Goals

- Catch common, well-defined GD&T authoring mistakes automatically and
  explain *why* each one is wrong, in terms an engineer would recognize
  from the standard (not just "invalid input").
- Keep the rule set genuinely deterministic and testable: every rule
  operates on explicit domain-model fields, never on a heuristic guess,
  and every rule ships with PASS/FAIL tests.
- Keep the domain model (`gdt_coach.models`), the rule engine
  (`gdt_coach.rules`), and concrete rules (`gdt_coach.rules.checks`)
  cleanly separable, so a new rule never requires touching the engine
  or the model.
- Make it easy to add a new rule: one module, one registration line,
  one test file.

## Non-goals

- **Not a CAD system.** `gdt-coach` has no geometry engine, no 3D
  model, and no concept of physical part shape — only the symbolic
  GD&T data a drawing's YAML representation declares.
- **Not a full ASME Y14.5 implementation.** The rule set is real but
  partial (20 rules as of this writing); it does not cover composite
  tolerancing, datum degrees-of-freedom accounting, or every
  characteristic/modifier combination in the standard.
- **Not a certified or legally authoritative compliance tool.** A clean
  `gdt-coach check` run is not proof a drawing conforms to ASME Y14.5;
  it means the implemented rules found no violations.
- **No image, PDF, DXF, or native CAD file ingestion (yet).** The only
  input format today is the YAML schema described in `README.md`.
- **No tolerance stack-up analysis, no manufacturability analysis, no
  cost estimation.** Purely GD&T-callout validation.

## Stakeholders / users

- Mechanical/manufacturing engineers who want a fast, scriptable
  sanity check on GD&T callouts before a drawing goes to review or to a
  supplier.
- Educators and students working through ASME Y14.5, who want concrete,
  explained feedback on practice drawings.
- Contributors who want to add a new rule: the project is structured
  specifically to make that a small, self-contained change.

## Success criteria

- A rule is only added when it is fully deterministic against the
  current domain model — no heuristic guessing when data is missing or
  ambiguous. If a rule can't be verified without guessing, that's
  documented as a known limitation, not implemented as a heuristic.
- The full check suite (Ruff, Mypy strict, Pytest) passes on every
  change; new rules and new domain-model fields ship with PASS/FAIL
  tests.
- The layering holds over time: adding a rule never requires changing
  `RuleEngine`, `RuleRegistry`, or the domain model; adding an input
  format never requires changing the rule engine or CLI reporting.

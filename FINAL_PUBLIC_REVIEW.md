# FINAL_PUBLIC_REVIEW.md

An assessment of `gdt-coach` as if reviewing it as a senior engineer at
Siemens Digital Industries Software evaluating whether an open-source
GD&T tool is worth adopting, contributing to, or pointing a team at.

## Strengths

- **The layering is real, not aspirational.** Domain model, rule
  engine, concrete rules, ingest, and CLI are genuinely decoupled —
  `RuleEngine` has zero knowledge of any specific rule, and a new rule
  never touches the engine, registry, or domain model. This was
  verified, not just claimed: adding the last 9 rules touched only
  `rules/checks/` and its tests.
- **Deterministic-by-design, with the discipline to prove it.** Every
  rule is checked against explicit domain-model fields; where a rule
  *could* be approximated with a heuristic (e.g. guessing
  Feature-of-Size status from `feature_type`), the project explicitly
  declined and documented the resulting limitation instead. That's a
  harder, more honest engineering choice than it looks.
- **Test discipline is genuinely strong for the project's size.** 242
  tests, 99% line coverage, PASS/FAIL cases per rule, and tests that
  exercise otherwise-unreachable defense-in-depth branches
  (`model_construct()` to simulate data that bypassed validation). Mypy
  strict and Ruff are enforced in CI, not just available locally.
- **The project caught and fixed its own architectural debt.** The
  `ALL_RULE_CLASSES` single-source-of-truth pattern exists because an
  earlier state (four separate hardcoded rule lists) was found via
  self-audit and consolidated — a healthier signal than a project that
  never looks back at its own decisions.
- **Documentation is honest about scope.** Known limitations are
  attached to individual rules, not buried; `PROJECT.md` states
  non-goals as plainly as goals. Nothing in the current documentation
  overstates what the tool does.

## Weaknesses

- **YAML-only input is the biggest practical adoption barrier.** No
  real-world drawing — CAD-exported or otherwise — exists as
  `gdt-coach`'s YAML today. Until there's a path from a real drawing
  format to this schema, the tool's audience is limited to people
  willing to hand-author YAML, which is a small fraction of the actual
  target users (manufacturing/mechanical engineers).
- **14 rules is a real but partial slice of ASME Y14.5.** Composite
  tolerancing isn't modeled at all (not a missing rule — the domain
  model has no concept of a multi-segment feature control frame), and
  datum degrees-of-freedom accounting doesn't exist. A user's first
  impression after trying a few real drawings will likely be "this
  didn't catch X" for a wide range of X.
- **Correctness depends on data the tool can't verify.**
  Feature-of-Size rules trust a boolean the source data must set
  correctly; there's no cross-check, so a user who doesn't understand
  this dependency will get confidently-wrong results (false positives)
  without any signal that something upstream was mis-declared.
- **No schema versioning story.** The YAML mirrors the domain model
  1:1 with no `schema_version` field; a future breaking model change
  has no defined migration path for existing YAML files. Fine at the
  current scale, a real risk once anyone depends on the format.
- **Single-maintainer project, no CHANGELOG, no release process yet.**
  Version is pinned at `0.1.0` with no tagged releases. Not a defect,
  but a real signal to anyone evaluating whether to depend on this
  today.
- **No coverage-reporting service.** Coverage is measured and enforced
  informally (99%, checked locally/in CI output) but not surfaced as a
  public badge via Codecov or similar — a small credibility gap for a
  project whose main selling point is engineering rigor.

## Remaining improvements

In roughly the order they'd matter to a prospective adopter:

1. Some path from a real drawing (even a constrained one — a
   structured PDF or a specific CAD export) to the YAML schema. This is
   the single highest-leverage next step for real-world relevance.
2. The two domain-model gaps already tracked in `ROADMAP.md`
   (`FeatureControlFrame` → `Dimension` link; composite/multi-segment
   FCF support) — both block entire categories of otherwise-reasonable
   rules.
3. A `schema_version` field on `Drawing`, before the YAML format has
   external users depending on it.
4. A coverage badge (Codecov or equivalent) wired into CI.
5. A `CHANGELOG.md` and a first tagged release once the rule set and
   YAML schema feel stable enough to version meaningfully.

## Readiness score: 7/10

This is a well-engineered, honestly-scoped early-stage project — the
code quality, test discipline, and documentation honesty are well above
what's typical for a repo at this stage. It is not yet broadly useful
in production terms: the practical ceiling is capped by YAML-only input
and a rule set that covers a real but modest slice of ASME Y14.5. That
combination — strong engineering, narrow current scope — is exactly
what "7" is meant to capture: worth a serious look, worth contributing
to, not yet a tool to build a workflow around.

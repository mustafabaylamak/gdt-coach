# PUBLIC_RELEASE_PLAN.md

Audit of the `gdt-coach` repository ahead of its first public GitHub
release. This document only records findings and intended changes —
nothing has been modified yet. See `PUBLIC_RELEASE_CHECKLIST.md` (created
in a later phase) for the final go/no-go list, and `FINAL_PUBLIC_REVIEW.md`
for the overall quality assessment.

## Method

Reviewed every tracked file (`git ls-files`, 79 files at audit time):
source (`src/`), tests (`tests/`), all markdown, `.github/workflows/ci.yml`,
`.pre-commit-config.yaml`, `.gitignore`, `pyproject.toml`, `examples/`,
`docs/README.md`, `scripts/README.md`. Searched for AI/assistant-tool
references, `TODO`/`FIXME`/`HACK` markers, debug prints, commented-out
code, leaked local file paths, dead links, and cross-checked documented
claims (rule count, rule IDs) against actual code output.

## Findings

### 1. No AI-specific artifacts remain in tracked files

A repo-wide case-insensitive search for `claude|anthropic|chatgpt|copilot|
ai-generated|ai-assisted|llm-generated` returned zero matches. `CLAUDE.md`
was already removed in an earlier cleanup pass, and no other file
references an AI coding tool or assistant-specific workflow.
**No action needed here** — noted for completeness since it was
explicitly in scope to check.

### 2. `ARCHITECTURE.md` is written as a development diary, not an architecture doc

The file narrates the project's internal development history ("Sprint 1
added...", "Sprint 6 hardened...", "found during a Sprint 5 architecture
review and fixed in Sprint 6", "identified by the Sprint 7 audit"). This
is accurate history, but it's an internal, session-by-session account of
*how* the code was built, not a description of *what it is now* — the
thing a new reader (contributor or employer) actually needs. It also
implicitly reveals an iterative, agent-driven development process that
doesn't need to be part of the public architecture narrative.

**Plan:** Rewrite `ARCHITECTURE.md` to describe the current architecture
in the present tense, with no "Sprint N" numbering. Content is
technically sound and stays (domain model, rule engine, concrete rules
table, ingest layer, entry points, known limitations, open decisions) —
only the historical framing changes. Genuine engineering rationale
currently expressed as "Sprint N found X" becomes "X is a known
limitation" / "X was intentionally deferred," stated directly.

### 3. `ROADMAP.md` is a sprint-numbered changelog

Same issue as #2, more structurally: the whole document is organized as
`## Sprint 1`, `## Sprint 2`, ... `## Sprint 7`, each with a meta-narrative
about what was found/fixed in which sprint. A roadmap should tell a
reader what exists and what's planned, not replay development sessions.

**Plan:** Restructure into `## Implemented` (grouped by capability: domain
model, rule engine, GD&T rules, YAML ingest, CLI) and `## Planned` /
`## Under consideration` (the genuine open items: more rules, Markdown/HTML
output, the two known model gaps). Drop sprint numbers and internal
meta-commentary about audits/reviews of the roadmap itself.

### 4. `PROJECT.md` is completely stale

It still reads: *"`gdt-coach` is currently a bare project scaffold... no
business logic exists yet"*, with Goals/Non-goals/Stakeholders/Success
criteria all marked `TBD`. This was accurate at the very first commit and
has not been touched since — it now flatly contradicts the rest of the
repository (14 rules, a CLI, YAML ingest, 240 passing tests).

**Plan:** Rewrite with real content: what the project is, who it's for,
explicit non-goals (no PDF/DXF/CAD/image ingestion yet, no CAD geometry
engine, not a certified compliance tool), and success criteria stated
honestly (deterministic, testable rule coverage growing over time).

### 5. `docs/README.md` and `scripts/README.md` are stale placeholders

Both still say "once there is business logic to document" / "None exist
yet" — true at the initial scaffold, no longer true (or in `scripts/`'s
case, still true and fine to say plainly without the leftover phrasing).

**Plan:** Reword `docs/README.md` to reflect that `ARCHITECTURE.md`,
`ROADMAP.md`, and `PROJECT.md` already cover current documentation needs
and this directory is reserved for future deep-dive material (ADRs,
design notes). Reword `scripts/README.md` to state plainly that no
scripts exist yet, without the "once there is business logic" framing.
Keep both directories — they document intended structure and cost
nothing to keep.

### 6. Incorrect Homepage URL in `pyproject.toml`

```toml
[project.urls]
Homepage = "https://github.com/mustafad/gdt-coach"
```

The actual repository is `https://github.com/mustafabaylamak/gdt-coach`
(confirmed via `git remote get-url origin`). This is a broken link today
— anyone installing the package and following the Homepage link gets a
404 or someone else's namespace.

**Plan:** Fix the URL. Also tighten `description = "GDT Coach"` (currently
just the product name, not a description) to a real one-line summary, and
consider bumping `Development Status :: 2 - Pre-Alpha` to
`3 - Alpha` — the project has working, tested functionality now, which
"Pre-Alpha" undersells; "Alpha" is accurate given the API isn't stable
and scope is still narrow (no image/CAD ingestion, 14 rules).

### 7. No `LICENSE` file, despite `pyproject.toml` declaring one

`pyproject.toml` has `license = { text = "MIT" }`, but there is no
`LICENSE` file in the repository. This is a real gap: GitHub won't show a
license badge, `pip`/PyPI tooling that inspects the license field will be
inconsistent with the actual repo contents, and it's the single most
commonly-flagged omission in "is this repo ready for public release"
reviews.

**Plan:** Add a standard MIT `LICENSE` file (author: Mustafa D.
Abaylamak, matching `pyproject.toml`'s existing declared license — not
proposing a license change, just making the file match the
already-declared choice).

### 8. No standalone `CONTRIBUTING.md`

Contribution guidance currently lives as a `## Contributing` section
inside `README.md`. This works, but Phase 5 of this release process
expects `CONTRIBUTING.md` to exist as its own file (GitHub also
specifically recognizes and surfaces a top-level `CONTRIBUTING.md` when
someone opens an issue or PR — a README section doesn't get that
treatment).

**Plan:** Extract the existing "Contributing" content into a standalone
`CONTRIBUTING.md`, expand it slightly (how to run the full check suite,
how to add a new rule, PR expectations), and leave a one-line pointer in
`README.md` instead of duplicating the content.

### 9. No `.github/ISSUE_TEMPLATE/` or `.github/pull_request_template.md`

Neither exists. For a public repo expecting outside contributors, basic
templates reduce low-quality/incomplete issues and PRs and are a
standard signal of an actively-maintained project.

**Plan:** Add `.github/ISSUE_TEMPLATE/bug_report.md`,
`.github/ISSUE_TEMPLATE/feature_request.md`, `.github/ISSUE_TEMPLATE/config.yml`,
and `.github/pull_request_template.md`.

### 10. README lacks the structure a public-facing engineering README needs

Current `README.md` is competent *reference* documentation (setup, CLI
usage, YAML format) but has no on-ramp for a first-time visitor: no
explanation of what GD&T is or why a rule-checking tool for it is useful,
no architecture diagram, no explicit limitations section, no license
section, and the "Contributing" section duplicates what's moving to
`CONTRIBUTING.md`. Minor wording issue: phrases like "so far" and "14
GD&T rules... so far" read like an internal status update rather than a
description of a release.

**Plan:** Full rewrite per Phase 3 (see below); this is the single
biggest content change in this release-prep pass.

### 11. Example coverage is narrow relative to the actual rule set

`examples/` has 3 files (1 valid, 2 invalid), authored when only 5 rules
existed. They still work correctly against all 14 current rules (verified
— `valid_position.yaml` passes clean, each invalid file trips exactly one
rule), but they only ever demonstrate 2 of the 14 rules
(`flatness-no-datum-references`, `projected-zone-requires-position`).
Nothing demonstrates the newer Feature-of-Size rules, the 2018-deprecation
warning, or a `WARNING`-severity finding (all current examples are
`ERROR`).

**Plan (Phase 4):** Add two more invalid examples: one triggering
`concentricity-symmetry-deprecated` (to show a `WARNING`-severity
finding, not just `ERROR`), and one triggering a Feature-of-Size rule
(e.g. `position-requires-feature-of-size`). Document all five example
files and their exact `gdt-coach check` output in a new
`examples/README.md`, with output captured from an actual run, not
written by hand.

### 12. No repository description or topics set on GitHub

Confirmed via `gh repo view`: `description` is empty, `repositoryTopics`
is `null`. An empty description is one of the first things a visitor
sees on the repo page and on GitHub search.

**Plan (Phase 6):** Set both via `gh repo edit` — description matching
the README's one-line summary, topics covering the actual domain
(`gdt`, `geometric-dimensioning-and-tolerancing`, `asme-y14-5`, `cad`,
`quality-engineering`, `python`, `pydantic`). No fabricated capability
keywords (no `ocr`, `computer-vision`, `machine-learning` — none of that
exists yet).

### 13. No badges

No CI status, license, or Python-version badges in `README.md`. Adding
CI and license badges is accurate (the workflow and license both exist
for real) and standard practice; not adding a coverage-percentage badge
since no coverage service (Codecov etc.) is wired up — a badge for that
would imply infrastructure that doesn't exist.

**Plan:** Add a CI badge (points at the real `ci.yml` workflow), a
license badge, and a Python-version badge to the top of `README.md`.

### 14. What is *not* a finding (checked, found clean)

- No `TODO`/`FIXME`/`XXX`/`HACK` markers anywhere in tracked files.
- No debug `print()` statements outside `cli.py` (where `print` is the
  actual reporting mechanism, not debug output), no `pdb`/`breakpoint()`
  calls, no commented-out code blocks.
- No leaked local filesystem paths (`C:\Users\...`) or personal email
  addresses in tracked files.
- No trailing whitespace or tab/space inconsistencies (pre-commit hooks
  already enforce this).
- `enums.py`/`GD&T`/`Feature of Size` terminology capitalization is
  consistent across the docs that reference it.
- All markdown links in `README.md` (relative file paths and
  `ARCHITECTURE.md#anchor` links) resolve correctly — verified each
  target file/heading exists.
- Rule count and rule IDs documented in `ARCHITECTURE.md` (14 rules,
  specific IDs) match actual runtime output from
  `gdt_coach.rules.checks.ALL_RULE_CLASSES` exactly.
- `.gitignore`, `.pre-commit-config.yaml`, and `.github/workflows/ci.yml`
  are clean, standard, and require no changes.

## Summary of planned changes (by phase)

| Phase | Files touched |
|---|---|
| 2 (cleanup) | `ARCHITECTURE.md`, `ROADMAP.md`, `PROJECT.md`, `docs/README.md`, `scripts/README.md` rewritten/reworded; `pyproject.toml` URL/description fixed |
| 3 (README) | `README.md` fully rewritten; `CONTRIBUTING.md` created |
| 4 (demo) | 2 new files in `examples/`; new `examples/README.md` |
| 5 (consistency) | Cross-check pass, no new files expected beyond fixing any contradiction found |
| 6 (GitHub polish) | `LICENSE` created; `.github/ISSUE_TEMPLATE/*`, `.github/pull_request_template.md` created; GitHub repo description/topics set via `gh` |
| 7 (verification) | No files changed; Ruff/Mypy/Pytest run |
| 8 (checklist) | `PUBLIC_RELEASE_CHECKLIST.md` created |
| 9 (final review) | `FINAL_PUBLIC_REVIEW.md` created |
| 10 (publish) | Single commit, push, then flip GitHub visibility to public |

No source code (`src/gdt_coach/`) or test (`tests/`) changes are planned
— the audit found the codebase itself clean. This is a documentation and
repository-hygiene pass only.

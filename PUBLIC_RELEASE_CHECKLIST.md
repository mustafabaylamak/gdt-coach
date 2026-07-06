# PUBLIC_RELEASE_CHECKLIST.md

Everything below was verified before this repository was made public.
Checked items were confirmed during this release-prep pass, not
assumed.

## Content and hygiene

- [x] No AI-assistant-specific artifacts or references anywhere in
      tracked files (searched for `claude|anthropic|chatgpt|copilot|
      ai-generated|ai-assisted` across all files — zero matches)
- [x] No `TODO`/`FIXME`/`XXX`/`HACK` markers in tracked files
- [x] No debug `print()`/`pdb`/`breakpoint()` calls, no commented-out
      code blocks
- [x] No leaked local filesystem paths or personal email addresses in
      tracked files
- [x] No internal development-process narrative left in public docs
      (removed "Sprint N" framing from `ARCHITECTURE.md`/`ROADMAP.md`;
      see `PUBLIC_RELEASE_PLAN.md` for what that looked like before)
- [x] `PROJECT.md` rewritten — no longer describes the project as a
      "bare scaffold" with `TBD` goals
- [x] `docs/README.md` / `scripts/README.md` placeholder wording
      updated to reflect current reality

## Documentation

- [x] `README.md`: overview, motivation, architecture diagram,
      installation, quick start, project structure, example
      validation, limitations, roadmap, contributing, license
- [x] `ARCHITECTURE.md`, `ROADMAP.md`, `PROJECT.md`, `CONTRIBUTING.md`
      cross-checked for consistency — no contradicting rule counts,
      test counts, or claims; no large duplicated content blocks
- [x] Every internal markdown link and anchor link verified to resolve
      to a real file/heading
- [x] `pyproject.toml` `Homepage` URL corrected (was pointing at the
      wrong GitHub namespace)
- [x] No exaggerated claims: this is explicitly documented as a
      partial rule set (14 rules), YAML-only input, not a CAD system,
      not a certified compliance tool

## License and legal

- [x] `LICENSE` file added (MIT), matching `pyproject.toml`'s already-
      declared `license` field — not a new decision, just a missing
      file now present
- [x] No verbatim ASME Y14.5/ISO 1101 standard text quoted anywhere;
      all rule explanations are original paraphrase (spot-checked
      during the architecture audit that selected the current rule
      set, and re-confirmed here)

## Demo / examples

- [x] `examples/` has 5 YAML drawings: 1 clean, 4 each demonstrating a
      distinct rule (including one `WARNING`-severity example, not just
      `ERROR`)
- [x] `examples/README.md` documents every example with its exact
      command and real, captured output (re-run during this pass, not
      hand-written)
- [x] Every example has a corresponding automated test asserting its
      expected finding(s)

## GitHub configuration

- [x] `.gitignore`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`
      reviewed — already clean, no changes needed
- [x] `.github/ISSUE_TEMPLATE/` added (bug report, rule request, and a
      config pointing blank/question issues at Discussions)
- [x] `.github/pull_request_template.md` added
- [x] GitHub repository description and topics set
      (`gh repo edit --description ... --add-topic ...`)
- [x] GitHub Discussions enabled (the issue template config links to
      it; verified it wasn't a dead link before publishing)

## Quality gates

- [x] `ruff check .` — clean
- [x] `ruff format --check .` — clean
- [x] `mypy src` (strict) — clean, 38 source files
- [x] `pytest` — 242 tests passed, 99% line coverage
- [x] No test was removed or weakened to make this pass

## Before clicking "Publish"

- [ ] Final read of `FINAL_PUBLIC_REVIEW.md` — confirm the readiness
      score and remaining-improvements list are acceptable to ship with
- [ ] Confirm you (the repository owner) are comfortable with the full
      git history becoming public — this release-prep pass cleaned up
      *current* file contents, it did not rewrite history
- [ ] Repository visibility changed from Private to Public

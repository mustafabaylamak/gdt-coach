## What this changes and why

<!-- What does this PR do, and why does it matter? If it fixes an issue, link it. -->

## Type of change

- [ ] Bug fix
- [ ] New rule
- [ ] New feature (ingest format, CLI flag, etc.)
- [ ] Documentation
- [ ] Other (describe above)

## Checklist

- [ ] `ruff check . && ruff format --check .` passes
- [ ] `mypy src` passes
- [ ] `pytest` passes, and coverage wasn't reduced
- [ ] New code has corresponding tests (PASS and FAIL cases for a new rule)
- [ ] Docs updated if this changes user-facing behavior (`README.md`),
      architecture (`ARCHITECTURE.md`), or scope (`ROADMAP.md`/`PROJECT.md`)

## If this adds a new rule

- [ ] Rule is fully deterministic against the current domain model (no
      heuristics for missing/ambiguous data — documented as a known
      limitation instead)
- [ ] Added to `ALL_RULE_CLASSES` in `src/gdt_coach/rules/checks/__init__.py`
- [ ] Added to the rule table in `ARCHITECTURE.md#concrete-rules`
- [ ] Standard reference is paraphrased, not quoted verbatim from ASME
      Y14.5/ISO 1101

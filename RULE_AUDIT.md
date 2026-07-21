# RULE_AUDIT.md — Sprint 17 rule audit

## What this is, and what it is not

This is a **formal internal-consistency and assumption audit** of every
GD&T rule `gdt-coach` currently ships. For each rule it checks: does
the implementation actually do what its own title/explanation/severity
claim; what domain-model fields does it trust as ground truth; how does
it behave when data is missing or ambiguous; what are its plausible
false-positive and false-negative scenarios; do its tests exercise
meaningful engineering scenarios (not just line/branch coverage); and
does it behave consistently with structurally similar rules.

**This is not an ASME Y14.5 certification audit.** No clause numbers,
section references, or standard wording appear anywhere in this
document or were used to produce it — nobody performing this audit has
a licensed copy of ASME Y14.5-2018 to cite against. Where a rule's
correctness genuinely hinges on an exact reading of the standard this
project doesn't have in hand, that is marked explicitly as **"requires
licensed-standard verification"** rather than guessed at. Passing this
audit means: the rule is internally consistent, its assumptions are
documented, and its tests cover meaningful scenarios — it does not mean
the rule has been checked against the literal standard text.

## Authoritative rule set

The audit's scope is `gdt_coach.rules.checks.ALL_RULE_CLASSES` — the
same single source of truth the CLI and the test suite already use —
not a hand-maintained list. Verified at audit time:

```
>>> from gdt_coach.rules.checks import ALL_RULE_CLASSES
>>> len(ALL_RULE_CLASSES)
20
```

All 20 registered rule ids, in the deterministic sorted order used
throughout this document:

```
angularity-related-dimension-must-be-angular
angularity-related-dimension-must-be-orientation
circularity-no-datum-references
concentricity-symmetry-deprecated
cylindricity-no-datum-references
datum-reference-must-be-defined
fcf-duplicate-datum-references
flatness-no-datum-references
form-mmc-requires-feature-of-size
orientation-requires-datum-reference
position-material-condition-requires-feature-of-size
position-related-dimension-must-be-basic
position-related-dimension-must-be-location
position-requires-datum-reference
position-requires-feature-of-size
projected-zone-requires-position
related-dimension-must-be-defined
related-dimension-must-not-be-reference
runout-always-rfs
straightness-no-datum-references
```

Every rule below corresponds to exactly one entry in this list, and
every entry in this list has exactly one audit row below — there is no
audit entry for a rule that isn't registered, and no registered rule
without an audit entry.

## Audit summary

| Result | Count |
|---|---:|
| Internally consistent | 17 |
| Test gaps found | 3 |
| Documentation mismatches found | 0 |
| Logic issues found | 0 |
| Requires licensed-standard verification | 2 |

("Requires licensed-standard verification" is an independent flag, not
a fifth mutually-exclusive result — both flagged rules are otherwise
internally consistent; the flag means their *scope boundary*, not their
implementation, is the open question.)

## Cross-cutting findings

**Model fields commonly trusted as authoritative, never inferred:**
- `Feature.feature_of_size` (default `False`) — trusted by
  `form-mmc-requires-feature-of-size`, `position-requires-feature-of-size`,
  `position-material-condition-requires-feature-of-size`
- `Dimension.role` (default `OTHER`) — trusted by
  `position-related-dimension-must-be-location`,
  `angularity-related-dimension-must-be-orientation`
- `Dimension.is_reference` (default `False`) — trusted by
  `related-dimension-must-not-be-reference`
- `Drawing.datums` — the definitional source of "which datums exist,"
  trusted by `datum-reference-must-be-defined`

None of these are inferred from any other field (e.g. `feature_type`
never implies `feature_of_size`; `dimension_type` never implies
`role`). This is a deliberate, repository-wide policy (see
`PROJECT.md`'s success criteria: "no heuristic guessing when data is
missing or ambiguous"), not an oversight — the audit confirms every
rule that touches these fields honors it, with no exceptions found.

**Recurring missing/ambiguous-data behavior:** every one of the six
`related_dimension_ids`-based rules silently skips an id that doesn't
resolve to a dimension on the same owning feature, rather than
guessing at a nonexistent dimension's properties — that case is
`related-dimension-must-be-defined`'s to report. This is consistent
across all six with no exceptions.

**Shared false-positive risk:** any drawing that under-declares
`feature_of_size` or `Dimension.role` on a feature/dimension that is
*actually* a Feature of Size / actually plays that role will produce a
false violation from the rules that trust those fields. This is already
documented per-rule (see `ARCHITECTURE.md`'s "Known limitations") and
confirmed, not newly discovered, by this audit.

**Shared false-negative risk — catalog scope gaps (not defects in any
one rule):**
- No rule requires a runout (`circular_runout`/`total_runout`)
  feature control frame to carry any datum reference at all, unlike
  the parallel treatment `position-requires-datum-reference` and
  `orientation-requires-datum-reference` give their own characteristics.
  A runout FCF with zero datum references currently produces no
  finding from any rule.
- No rule checks whether `circularity`/`cylindricity` characteristics
  carry an MMC/LMC modifier — `form-mmc-requires-feature-of-size`
  explicitly (and, per its own docstring, deliberately) scopes itself
  to straightness/flatness only.
- `profile_of_a_line`/`profile_of_a_surface` characteristics are not
  covered by any rule. This is treated as intentional, not a gap:
  profile tolerances are legitimately used both with and without a
  datum reference frame depending on design intent, so a
  "profile-requires-datum" rule would be guessing at something the
  domain model has no way to disambiguate — consistent with this
  project's policy against heuristic inference.

**Rules limited by lack of geometry:** none of the 20 rules attempt any
geometric reasoning (tolerance stack-up, physical clearance, actual
feasibility) — this isn't a per-rule limitation so much as the
project's stated non-goal (`PROJECT.md`: "not a CAD system... no
tolerance stack-up analysis"). No rule claims otherwise.

**Rules limited by explicit user-supplied semantics:** six rules (the
`feature_of_size`, `role`, and `is_reference` list above) are only as
accurate as the source drawing's own explicit flags — this is the
single largest category of false-positive risk in the current rule set,
concentrated entirely in data the domain model requires the drawing
author to state directly rather than lets the tool infer.

**Unused enum members (not a defect):** of `RuleCategory`'s seven
values, only `dimension`, `feature_control_frame`, and `tolerance` are
currently used by any rule (`datum`, `drawing`, `feature`, and
`general` are unused). Of `Standard`'s four values, only
`asme_y14.5_2018` and `general` are used (`asme_y14.5_2009` and
`iso_1101_2017` are unused). Of `Severity`'s four values, only `error`
and `warning` are used (`critical` and `info` are unused — every rule
but `concentricity-symmetry-deprecated` is `error`). None of this is a
bug: `gdt-coach rules list --standard iso_1101_2017` correctly and
intentionally returns an empty, non-error result today (the same
already-accepted pattern the existing test
`test_rules_list_empty_filter_result_exits_zero` documents for
`RuleCategory.DATUM`). These are reserved for rules that don't exist
yet, not evidence of missing coverage.

---

## Per-rule audit

### `angularity-related-dimension-must-be-angular`

- **Title:** Angularity-related dimensions must be angular
- **Category:** `dimension` · **Standard:** `asme_y14.5_2018`
- **Implementation summary:** For every `ANGULARITY` feature control
  frame, resolves each `related_dimension_ids` entry against the owning
  feature's own `dimensions`; flags any that resolve to a dimension
  whose `dimension_type != ANGULAR`.
- **Domain fields trusted:** `FeatureControlFrame.related_dimension_ids`,
  `Dimension.dimension_type` (the latter is internally validated by the
  domain model itself — an `ANGULAR` dimension must use a degree unit —
  so this isn't "guessable" author-supplied data in the same sense as
  `feature_of_size`/`role`).
- **Missing/ambiguous-data behavior:** an id that doesn't resolve on the
  owning feature is silently skipped (reported by
  `related-dimension-must-be-defined` instead).
- **PASS scenario covered by tests:** an angular dimension related to an
  angularity FCF; a non-angularity characteristic with a non-angular
  related dimension (ignored); an unresolved id (skipped).
- **FAIL scenario covered by tests:** a `LINEAR` dimension related to an
  angularity FCF (one finding, correct `feature_id`/`fcf_id`/message);
  multiple non-angular ids reported in sorted order.
- **False-positive risk:** none identified — `dimension_type` is
  authoritative, internally validated data, not a heuristic.
- **False-negative risk:** an unresolved id is invisible to this rule by
  design (see above); no risk beyond that documented hand-off.
- **Model limitations:** none beyond `related-dimension-must-be-defined`'s
  own scope.
- **Audit result:** test gap found — this rule's test file had no case
  proving a `related_dimension_ids` entry matching a same-named
  dimension declared on a *different* feature is correctly treated as
  unresolved, unlike three sibling rules in this family which already
  have exactly that test.
- **Changes made:** added
  `test_pass_related_id_defined_only_on_another_feature_is_not_resolved`
  to `tests/rules/checks/test_angularity_related_dimension_must_be_angular.py`,
  mirroring the existing test in
  `test_related_dimension_must_be_defined.py`.

### `angularity-related-dimension-must-be-orientation`

- **Title:** Angularity-related dimensions must be orientation dimensions
- **Category:** `dimension` · **Standard:** `asme_y14.5_2018`
- **Implementation summary:** For every `ANGULARITY` FCF, resolves each
  related dimension id against the owning feature; flags any that
  resolve to a dimension whose `role != ORIENTATION`.
- **Domain fields trusted:** `Dimension.role` (default `OTHER`, never
  inferred from `dimension_type` — an angular-typed dimension is not
  assumed to be an orientation dimension).
- **Missing/ambiguous-data behavior:** unresolved ids skipped (same
  hand-off as above); an unclassified dimension (`role == OTHER`) is
  treated as wrong, not skipped.
- **PASS scenario covered by tests:** `role == ORIENTATION`; a
  non-angularity characteristic (ignored); an unresolved id; a
  same-named dimension declared on a *different* feature (correctly not
  resolved).
- **FAIL scenario covered by tests:** `role == SIZE`; the default role
  `OTHER` explicitly rejected; mixed correct/wrong roles report only the
  wrong ones; sorted-order multi-id reporting; a mix of one valid
  wrong-role id and one unresolved id reports only the wrong-role one.
- **False-positive risk:** a genuine orientation dimension left
  un-classified (`role` never set) will be reported as a violation —
  already documented in `ARCHITECTURE.md`.
- **False-negative risk:** none beyond the documented unresolved-id
  hand-off.
- **Model limitations:** `Dimension.role` trust, as above.
- **Audit result:** internally consistent.
- **Changes made:** none.

### `circularity-no-datum-references`

- **Title:** Circularity cannot reference datums
- **Category:** `feature_control_frame` · **Standard:** `asme_y14.5_2018`
- **Implementation summary:** Flags any `CIRCULARITY` feature control
  frame with one or more datum references.
- **Domain fields trusted:** `FeatureControlFrame.characteristic`,
  `.datum_references` — both structural, unambiguous fields; there is
  no missing-data case for a purely structural presence check.
- **Missing/ambiguous-data behavior:** not applicable — `datum_references`
  defaults to an empty list, never `None`, so the truthiness check is
  always well-defined.
- **PASS scenario covered by tests:** no datum references; a different
  characteristic (`POSITION`) with datum references (correctly not
  flagged, since that combination is legitimate); an empty drawing.
- **FAIL scenario covered by tests:** one datum reference (one finding,
  correct locators); multiple datum references (still exactly one
  finding, not one per datum).
- **False-positive risk:** none identified.
- **False-negative risk:** none within stated scope.
- **Model limitations:** none.
- **Audit result:** internally consistent.
- **Changes made:** none.

### `concentricity-symmetry-deprecated`

- **Title:** Concentricity and symmetry are deprecated (ASME Y14.5-2018)
- **Category:** `feature_control_frame` · **Standard:** `asme_y14.5_2018`
- **Severity:** `warning` (the only `WARNING`-severity rule in the
  catalog; every other rule is `error`).
- **Implementation summary:** Flags any FCF using `CONCENTRICITY` or
  `SYMMETRY`, at `WARNING` rather than `ERROR`.
- **Domain fields trusted:** `FeatureControlFrame.characteristic`.
- **Missing/ambiguous-data behavior:** `Drawing` has no field recording
  which standard *edition* it targets, so this rule cannot tell a
  2018-target drawing (where these symbols are removed) from an
  earlier-edition one (where they remain valid). It always fires, at
  `WARNING`, and its message says so explicitly rather than silently
  assuming 2018 — already documented in both the module docstring and
  `ARCHITECTURE.md`.
- **PASS scenario covered by tests:** `POSITION` is not flagged; empty
  drawing.
- **FAIL scenario covered by tests:** both `CONCENTRICITY` and
  `SYMMETRY`, parametrized, asserting `WARNING` severity explicitly; a
  dedicated test asserting the message mentions both "2018" and the
  "earlier edition" caveat.
- **False-positive risk:** fires for a drawing legitimately targeting an
  earlier edition — inherent to the missing-edition-field limitation,
  softened by using `WARNING` instead of `ERROR` specifically because of
  this.
- **False-negative risk:** none within stated scope.
- **Model limitations:** no target-standard-edition field on `Drawing`
  (already the single most thoroughly documented limitation in the
  codebase, predating this audit).
- **Audit result:** internally consistent.
- **Changes made:** none.

### `cylindricity-no-datum-references`

- **Title:** Cylindricity cannot reference datums
- **Category:** `feature_control_frame` · **Standard:** `asme_y14.5_2018`
- **Implementation summary / fields / behavior:** identical shape to
  `circularity-no-datum-references` above, scoped to `CYLINDRICITY`.
- **PASS/FAIL scenario coverage:** identical to `circularity-no-datum-references`
  (shared parametrized test module).
- **False-positive / false-negative risk:** none identified.
- **Model limitations:** none.
- **Audit result:** internally consistent.
- **Changes made:** none.

### `datum-reference-must-be-defined`

- **Title:** Referenced datums must be defined
- **Category:** `feature_control_frame` · **Standard:** `general`
- **Implementation summary:** For every FCF, set-differences its
  referenced datum labels against `{datum.label for datum in
  drawing.datums}`; flags any left over, sorted.
- **Domain fields trusted:** `Drawing.datums` — definitional: a datum
  "exists" on a drawing if and only if it is declared there.
- **Missing/ambiguous-data behavior:** not applicable — this is exactly
  the rule that reports a missing datum, and it does so directly rather
  than trusting anything else. A CSV-sourced `Drawing` always has
  `datums == []` (by the CSV ingest contract), so this rule correctly
  and predictably fires for any CSV drawing that references a datum
  label at all — demonstrated by the bundled
  `invalid_datum_reference_undefined.csv` example.
- **PASS scenario covered by tests:** no datum references; every
  referenced datum defined; empty drawing.
- **FAIL scenario covered by tests:** one undefined datum; a mix of
  defined and undefined (only the undefined ones reported); multiple
  undefined labels on one FCF collapsed into one finding (not one per
  label); sorted-order reporting.
- **False-positive risk:** none — `Drawing.datums` is ground truth by
  construction, not inferred or guessed.
- **False-negative risk:** does not check `Datum.referenced_feature_id`
  consistency — deliberately out of scope (referential integrity beyond
  the label itself is a separate concern, per `ARCHITECTURE.md`'s
  ingest-layer documentation).
- **Model limitations:** none beyond the stated scope.
- **Audit result:** internally consistent (the best-tested rule in the
  related-object family; no gap found).
- **Changes made:** none.

### `fcf-duplicate-datum-references`

- **Title:** Duplicate datum references in one feature control frame
- **Category:** `feature_control_frame` · **Standard:** `general`
- **Implementation summary:** Flags any FCF whose datum reference labels
  contain a duplicate.
- **Domain fields trusted:** `FeatureControlFrame.datum_references`.
- **Missing/ambiguous-data behavior:** not applicable.
- **PASS scenario covered by tests:** unique datum references; no datum
  references.
- **FAIL scenario covered by tests:** a duplicate-label FCF built via
  `model_construct()` (bypassing normal Pydantic validation), asserting
  exactly one finding with correct locators; a companion test explicitly
  documents that normal, validated construction *cannot* produce this
  condition (`FeatureControlFrame`'s own validator already rejects
  duplicate labels at construction time).
- **False-positive / false-negative risk:** none — this rule is
  defense-in-depth for data that reaches the engine without going
  through normal validated construction (e.g. a future parser using
  `model_construct()` for speed), not a scenario reachable through any
  currently-shipped ingest path (YAML or CSV).
- **Model limitations:** already the second-most thoroughly documented
  limitation in the codebase (predates this audit); confirmed accurate.
- **Audit result:** internally consistent.
- **Changes made:** none.

### `flatness-no-datum-references`

- **Title:** Flatness cannot reference datums
- **Category:** `feature_control_frame` · **Standard:** `asme_y14.5_2018`
- **Implementation summary / fields / behavior:** identical shape to
  `circularity-no-datum-references`, scoped to `FLATNESS`.
- **PASS/FAIL scenario coverage:** identical (shared parametrized test
  module).
- **False-positive / false-negative risk:** none identified.
- **Model limitations:** none.
- **Audit result:** internally consistent.
- **Changes made:** none.

### `form-mmc-requires-feature-of-size`

- **Title:** Straightness/flatness may use MMC/LMC only on a Feature of Size
- **Category:** `feature_control_frame` · **Standard:** `asme_y14.5_2018`
- **Implementation summary:** For `STRAIGHTNESS`/`FLATNESS` FCFs whose
  tolerance carries a non-`RFS` material condition, flags the FCF if the
  owning feature is not marked `feature_of_size`.
- **Domain fields trusted:** `Feature.feature_of_size` (default `False`,
  never inferred) — documented in both the module docstring and
  `ARCHITECTURE.md`.
- **Missing/ambiguous-data behavior:** a genuine Feature of Size left
  un-flagged produces a false violation; no heuristic is used to guess
  FOS-ness from `feature_type`.
- **PASS scenario covered by tests:** RFS without FOS; MMC and LMC both
  tested *with* FOS (the legitimate exception case); a non-form
  characteristic (`POSITION`) with a modifier and no FOS (correctly
  ignored — out of this rule's scope); empty drawing.
- **FAIL scenario covered by tests:** MMC/LMC without FOS, for both
  `STRAIGHTNESS` and `FLATNESS`.
- **False-positive risk:** FOS under-declaration (documented).
- **False-negative risk:** `CIRCULARITY`/`CYLINDRICITY` carrying an
  MMC/LMC modifier is never checked by this rule (by explicit,
  documented design — see the module docstring) or by any other rule.
  Not a title/behavior mismatch (the title says "straightness/flatness"
  and means it), but a real catalog scope gap — see cross-cutting
  findings.
- **Model limitations:** `feature_of_size` trust, as above.
- **Audit result:** internally consistent; **requires licensed-standard
  verification** — general GD&T practice supports restricting this
  MMC-on-FOS exception to straightness (of a derived median line/axis)
  and flatness (of a derived median plane), but whether circularity and
  cylindricity are correctly excluded, or whether the exact standard
  text draws this boundary differently, cannot be confirmed without a
  licensed copy of ASME Y14.5-2018.
- **Changes made:** added a parametrized non-triggering test
  (`test_pass_circularity_or_cylindricity_with_modifier_is_out_of_scope`)
  to `tests/rules/checks/test_form_mmc_requires_feature_of_size.py`,
  explicitly documenting today's scope boundary in a test rather than
  leaving it implicit.

### `orientation-requires-datum-reference`

- **Title:** Orientation tolerances require at least one datum
- **Category:** `feature_control_frame` · **Standard:** `asme_y14.5_2018`
- **Implementation summary:** For FCFs with characteristic in
  `{ANGULARITY, PERPENDICULARITY, PARALLELISM}`, flags any with zero
  datum references.
- **Domain fields trusted:** `FeatureControlFrame.characteristic`,
  `.datum_references`.
- **Missing/ambiguous-data behavior:** not applicable — structural
  presence check.
- **PASS scenario covered by tests:** each of the three orientation
  characteristics with a datum reference (parametrized); a non-orientation
  characteristic with no datum reference (ignored); empty drawing.
- **FAIL scenario covered by tests:** each of the three characteristics
  with zero datum references (parametrized), correct locators and
  characteristic name in the message.
- **False-positive / false-negative risk:** none identified.
- **Model limitations:** none.
- **Audit result:** internally consistent.
- **Changes made:** none.

### `position-material-condition-requires-feature-of-size`

- **Title:** MMC/LMC on position requires a Feature of Size
- **Category:** `tolerance` · **Standard:** `asme_y14.5_2018`
- **Implementation summary:** For `POSITION` FCFs with a non-`RFS`
  material condition, flags the FCF if the owning feature is not
  `feature_of_size`.
- **Domain fields trusted:** `Feature.feature_of_size`, as above.
- **Missing/ambiguous-data behavior:** same FOS-trust limitation as the
  other two FOS-dependent rules.
- **PASS scenario covered by tests:** RFS without FOS; MMC and LMC with
  FOS; a form characteristic (`FLATNESS`) with a modifier and no FOS
  explicitly asserted out of scope (with a comment naming the sibling
  rule that owns it); empty drawing.
- **FAIL scenario covered by tests:** MMC/LMC without FOS, both
  modifiers.
- **False-positive risk:** FOS under-declaration (documented).
- **False-negative risk:** none within stated scope.
- **Model limitations:** FOS trust, as above.
- **Audit result:** internally consistent — this rule's own docstring
  already explains precisely why it is scoped to `POSITION` only
  (avoiding overlap with `form-mmc-requires-feature-of-size`), and the
  audit confirms the implementation matches that stated scope exactly.
- **Changes made:** none.

### `position-related-dimension-must-be-basic`

- **Title:** Position-related dimensions must be basic
- **Category:** `dimension` · **Standard:** `asme_y14.5_2018`
- **Implementation summary:** For `POSITION` FCFs, resolves each related
  dimension id against the owning feature; flags any that resolve to a
  non-basic dimension (`Dimension.is_basic` is `False`, i.e. it carries
  a tolerance).
- **Domain fields trusted:** `Dimension.is_basic` — a computed property
  (`tolerance is None`), not author-supplied boolean data, so this is
  not subject to the same under-declaration risk as `feature_of_size`/
  `role`; it is always accurate for whatever tolerance data exists.
- **Missing/ambiguous-data behavior:** unresolved ids skipped, same
  hand-off as the rest of this family.
- **PASS scenario covered by tests:** a basic related dimension; a
  non-position characteristic with a non-basic related dimension
  (ignored); an unresolved id (skipped); empty related-dimension-ids
  list; empty drawing.
- **FAIL scenario covered by tests:** a non-basic (toleranced) related
  dimension; a mix of basic, non-basic, and unresolved ids reporting
  only the non-basic one; sorted-order multi-id reporting.
- **False-positive / false-negative risk:** none beyond the documented
  unresolved-id hand-off — `is_basic` cannot itself be under-declared,
  unlike `feature_of_size`/`role`.
- **Model limitations:** none beyond the shared `related_dimension_ids`
  scope note.
- **Audit result:** test gap found — same gap as
  `angularity-related-dimension-must-be-angular`: no test proving a
  same-named dimension on a *different* feature is correctly treated as
  unresolved.
- **Changes made:** added
  `test_pass_related_id_defined_only_on_another_feature_is_not_resolved`
  to `tests/rules/checks/test_position_related_dimension_must_be_basic.py`.

### `position-related-dimension-must-be-location`

- **Title:** Position-related dimensions must be location dimensions
- **Category:** `dimension` · **Standard:** `asme_y14.5_2018`
- **Implementation summary:** For `POSITION` FCFs, resolves each related
  dimension id against the owning feature; flags any whose `role !=
  LOCATION`.
- **Domain fields trusted:** `Dimension.role` (default `OTHER`, never
  inferred).
- **Missing/ambiguous-data behavior:** unresolved ids skipped; default
  role `OTHER` treated as wrong, not skipped.
- **PASS scenario covered by tests:** `role == LOCATION`; a
  non-position characteristic (ignored); an unresolved id; a same-named
  dimension declared on a *different* feature (correctly not resolved);
  a mix of one valid location id and one unresolved id (only the
  unresolved one is silent, no finding); empty related-dimension-ids;
  empty drawing.
- **FAIL scenario covered by tests:** `role == SIZE`; default role
  `OTHER` explicitly rejected; a mix of location/size/orientation roles
  reporting only the wrong two; sorted-order multi-id reporting.
- **False-positive risk:** a genuine location dimension left
  un-classified — documented in `ARCHITECTURE.md`.
- **False-negative risk:** none beyond the unresolved-id hand-off.
- **Model limitations:** `Dimension.role` trust, as above; the rule's
  own docstring already explains why this check is independent of
  (not redundant with) `position-related-dimension-must-be-basic` —
  confirmed accurate by this audit.
- **Audit result:** internally consistent (this is the reference
  implementation for cross-feature-resolution test coverage in this
  rule family — the two rules found with a test gap now match it).
- **Changes made:** none.

### `position-requires-datum-reference`

- **Title:** Position tolerance must reference at least one datum
- **Category:** `feature_control_frame` · **Standard:** `asme_y14.5_2018`
- **Implementation summary:** Flags any `POSITION` FCF with zero datum
  references.
- **Domain fields trusted:** `FeatureControlFrame.characteristic`,
  `.datum_references`.
- **Missing/ambiguous-data behavior:** not applicable.
- **PASS scenario covered by tests:** position with datum references; a
  non-position characteristic with no datum references (ignored).
- **FAIL scenario covered by tests:** position with zero datum
  references, correct locators.
- **False-positive / false-negative risk:** none identified.
- **Model limitations:** none.
- **Audit result:** internally consistent.
- **Changes made:** none.

### `position-requires-feature-of-size`

- **Title:** Position applies only to a Feature of Size
- **Category:** `feature_control_frame` · **Standard:** `asme_y14.5_2018`
- **Implementation summary:** Flags any `POSITION` FCF on a feature not
  marked `feature_of_size`.
- **Domain fields trusted:** `Feature.feature_of_size`, as above.
- **Missing/ambiguous-data behavior:** FOS under-declaration risk, as
  above.
- **PASS scenario covered by tests:** position on a genuine FOS; a
  non-position characteristic (`PROFILE_OF_A_SURFACE`, chosen to match
  this rule's own explanation text, which names profile-of-a-surface as
  the correct alternative tool) without FOS, ignored; empty drawing.
- **FAIL scenario covered by tests:** position without FOS, correct
  locators.
- **False-positive risk:** FOS under-declaration (documented).
- **False-negative risk:** none within stated scope.
- **Model limitations:** FOS trust, as above.
- **Audit result:** internally consistent.
- **Changes made:** none.

### `projected-zone-requires-position`

- **Title:** Projected tolerance zone requires a position tolerance
- **Category:** `tolerance` · **Standard:** `asme_y14.5_2018`
- **Implementation summary:** Flags any FCF with a non-`None`
  `tolerance.projected_zone_height` whose `characteristic != POSITION`.
- **Domain fields trusted:** `Tolerance.projected_zone_height`,
  `FeatureControlFrame.characteristic`.
- **Missing/ambiguous-data behavior:** not applicable — presence of a
  projected zone height is an explicit, unambiguous field.
- **PASS scenario covered by tests:** position with a projected zone; a
  non-position characteristic with no projected zone.
- **FAIL scenario covered by tests:** a projected zone on
  `PERPENDICULARITY`, correct locators and characteristic name in the
  message; the multi-FCF, mixed-violation scenario for this rule is
  additionally exercised at the integration level in
  `tests/rules/checks/test_registration.py::test_rule_engine_runs_all_rules_end_to_end`
  (a drawing with four FCFs, only one of which trips this rule, verified
  alongside two other rules firing on their own FCFs and a fourth clean
  FCF producing nothing).
- **False-positive / false-negative risk:** none identified beyond the
  scope question below.
- **Model limitations:** none.
- **Audit result:** internally consistent; **requires licensed-standard
  verification** — restricting projected tolerance zones to `POSITION`
  matches the most common application (a projected zone for a
  press-fit/threaded hole's position tolerance), but whether the
  standard also permits a projected zone on certain orientation
  characteristics in specific fastener contexts cannot be confirmed
  without a licensed copy of ASME Y14.5-2018.
- **Changes made:** none (existing coverage, including the integration
  test, judged adequate; only the scope question is flagged).

### `related-dimension-must-be-defined`

- **Title:** Related dimensions must be defined
- **Category:** `feature_control_frame` · **Standard:** `general`
- **Implementation summary:** For every FCF, set-differences its
  `related_dimension_ids` against the *owning feature's own*
  `dimensions` (not drawing-wide); flags any left over.
- **Domain fields trusted:** `Feature.dimensions` — scoped per-feature,
  matching `Dimension.id`'s own uniqueness contract (unique within its
  owning feature, not drawing-wide, per `ROADMAP.md`'s "Dimension
  linkage" design notes).
- **Missing/ambiguous-data behavior:** not applicable — this is the rule
  that reports the missing case directly.
- **PASS scenario covered by tests:** empty related-dimension-ids; all
  ids defined; empty drawing.
- **FAIL scenario covered by tests:** one missing id; mixed valid and
  missing ids (only missing reported); **a dimension id that exists but
  only on a *different* feature — explicitly proven still unresolved
  from the referencing feature's point of view**, directly exercising
  the per-feature (not drawing-wide) scoping this rule depends on;
  sorted-order reporting.
- **False-positive / false-negative risk:** none — this rule is the
  reference implementation for the per-feature dimension-scoping
  contract every other dimension-aware rule in the catalog also relies
  on, and its own test suite is the one that directly proves that
  scoping is correct rather than assuming it.
- **Model limitations:** none.
- **Audit result:** internally consistent.
- **Changes made:** none.

### `related-dimension-must-not-be-reference`

- **Title:** Related dimensions must not be reference dimensions
- **Category:** `dimension` · **Standard:** `general`
- **Implementation summary:** For every FCF, resolves each related
  dimension id against the owning feature; flags any that resolve to a
  dimension with `is_reference == True`.
- **Domain fields trusted:** `Dimension.is_reference` (default `False`).
  Unlike `feature_of_size`/`role`, this field is partially
  self-checking: the domain model already forbids a reference dimension
  from also carrying a tolerance, so an under-declared reference
  dimension is the only realistic false-positive vector, not an
  internally contradictory one.
- **Missing/ambiguous-data behavior:** unresolved ids skipped, same
  hand-off as the rest of the family.
- **PASS scenario covered by tests:** a non-reference related dimension;
  an unresolved id; empty related-dimension-ids; empty drawing.
- **FAIL scenario covered by tests:** a reference-dimension related id;
  sorted-order multi-id reporting.
- **False-positive risk:** a genuine reference dimension left
  un-flagged (`is_reference` not set) would not itself cause a false
  positive here — the risk runs the other way (a non-reference
  dimension incorrectly marked `is_reference=True` would false-positive
  this rule), which is the same class of author-data-quality risk as
  the other trusted-flag rules.
- **False-negative risk:** none beyond the unresolved-id hand-off.
- **Model limitations:** `is_reference` trust, as above.
- **Audit result:** test gap found — same gap as the other two: no test
  proving a same-named dimension on a *different* feature is correctly
  treated as unresolved.
- **Changes made:** added
  `test_pass_related_id_defined_only_on_another_feature_is_not_resolved`
  to `tests/rules/checks/test_related_dimension_must_not_be_reference.py`.

### `runout-always-rfs`

- **Title:** Runout is always RFS
- **Category:** `feature_control_frame` · **Standard:** `asme_y14.5_2018`
- **Implementation summary:** For FCFs with characteristic in
  `{CIRCULAR_RUNOUT, TOTAL_RUNOUT}`, flags a non-`RFS` material
  condition on either the tolerance itself or any of its datum
  references, collecting every violation into one finding's message
  rather than one finding per violation.
- **Domain fields trusted:** `Tolerance.material_condition`,
  `DatumReference.material_condition`.
- **Missing/ambiguous-data behavior:** not applicable — both fields
  default to `RFS`, so an author who says nothing about material
  condition is automatically compliant, which is the correct default
  for this rule specifically.
- **PASS scenario covered by tests:** both runout characteristics at RFS
  (parametrized); a non-runout characteristic with modifiers (ignored);
  empty drawing.
- **FAIL scenario covered by tests:** a non-RFS tolerance-level
  modifier (parametrized over both characteristics); a non-RFS
  datum-reference-level modifier; both violations on the same FCF
  reported together in one finding's message.
- **False-positive / false-negative risk:** none identified for this
  rule's own stated scope (enforcing RFS-everywhere on a runout FCF).
  See the cross-cutting findings for the separate observation that no
  rule requires a runout FCF to carry a datum reference at all — that
  is a catalog gap, not a defect of this rule, which never claims to
  check for datum presence.
- **Model limitations:** none.
- **Audit result:** internally consistent (the most thoroughly tested
  rule in the FOS/material-condition group).
- **Changes made:** none.

### `straightness-no-datum-references`

- **Title:** Straightness cannot reference datums
- **Category:** `feature_control_frame` · **Standard:** `asme_y14.5_2018`
- **Implementation summary / fields / behavior:** identical shape to
  `circularity-no-datum-references`, scoped to `STRAIGHTNESS`.
- **PASS/FAIL scenario coverage:** identical (shared parametrized test
  module).
- **False-positive / false-negative risk:** none identified.
- **Model limitations:** none.
- **Audit result:** internally consistent.
- **Changes made:** none.

---

## A note on the "multiple features / unrelated FCFs" scenario check

Every rule in this catalog follows the same two-level iteration —
`for feature in drawing.features: for fcf in
feature.feature_control_frames:` — with no shared mutable state between
iterations, so a violation on one feature/FCF cannot influence the
finding reported for another. Most individual rule test files prove the
"an unrelated FCF must not trigger" half of this directly (a
differently-characteristic'd or already-compliant FCF on its own,
single-FCF drawing produces no finding); the "many objects on one
drawing, only some of which should fire" half is proven once, at the
integration level, in
`test_registration.py::test_rule_engine_runs_all_rules_end_to_end`
(four FCFs on one feature, three different rules firing on three of
them, the fourth producing nothing) — deliberately not duplicated
per-rule, since doing so ~17 more times would exercise the same trivial
loop-and-append pattern the language itself already guarantees, adding
test count without adding confidence.

The one place this judgment call does *not* apply is the six
`related_dimension_ids`-resolution rules, where `Dimension.id` is
scoped *per-feature* rather than drawing-wide (see `ROADMAP.md`'s
"Dimension linkage" notes) — an implementation that accidentally
resolved dimension ids drawing-wide instead of per-feature would be a
real, plausible bug, not a hypothetical one. That specific
cross-feature scoping is what the three added tests (see above) now
prove directly for the three rules that didn't already have it.

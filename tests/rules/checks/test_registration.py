"""Integration test: the rules in ALL_RULE_CLASSES register cleanly together.

Rule modules register themselves against `default_registry` as an
import side effect, so relying on import order/caching to test
registration is fragile. Instead this re-registers the already-imported
classes into the (test-isolated) `default_registry` directly, which
exercises the real invariants that matter: unique ids and complete
metadata across every rule.

`ALL_RULE_CLASSES` (from `gdt_coach.rules.checks`) is the single source
of truth for "every concrete rule" -- this test (and the CLI) both
import it rather than each keeping their own list. Assertions below are
derived from `ALL_RULE_CLASSES` itself (its length, its rule ids)
rather than a hardcoded count, so this test doesn't need editing every
time a rule is added or removed.
"""

from gdt_coach.models import Datum, Drawing, Feature, FeatureType
from gdt_coach.models.enums import DatumFeatureType, GeometricCharacteristic
from gdt_coach.rules.audit_status import RuleAuditStatus
from gdt_coach.rules.checks import ALL_RULE_CLASSES
from gdt_coach.rules.engine import RuleEngine
from gdt_coach.rules.registry import RuleRegistry, default_registry

from .conftest import make_fcf, make_tolerance

# The exact rule ids RULE_AUDIT.md records as having a known, unresolved
# standard-scope question (Sprint 17). This set is the single source of
# truth the tests below check every rule's own declared metadata against
# -- if a rule's audit_status/standard_question_note ever drifts from
# this, or this set drifts from RULE_AUDIT.md, a test here fails instead
# of the two silently disagreeing.
_EXPECTED_OPEN_STANDARD_QUESTION_RULE_IDS = frozenset(
    {
        "form-mmc-requires-feature-of-size",
        "projected-zone-requires-position",
    }
)


def _expected_rule_ids() -> set[str]:
    return {rule_cls().id for rule_cls in ALL_RULE_CLASSES}


def test_all_rules_register_without_conflict() -> None:
    for rule_cls in ALL_RULE_CLASSES:
        default_registry.register(rule_cls)

    assert len(default_registry) == len(ALL_RULE_CLASSES)
    assert {rule.id for rule in default_registry.all()} == _expected_rule_ids()


def test_all_rules_have_non_empty_explanations() -> None:
    for rule_cls in ALL_RULE_CLASSES:
        default_registry.register(rule_cls)

    for rule in default_registry.all():
        assert rule.explanation
        assert rule.title


# --- Sprint 18: rule audit-status metadata invariants -----------------------


def test_no_registered_rule_remains_not_audited() -> None:
    """Every one of the 20 currently registered rules has been through the
    Sprint 17 internal-consistency audit (RULE_AUDIT.md) and explicitly
    declares a status other than the NOT_AUDITED base-class default."""
    statuses = {rule_cls().id: rule_cls().audit_status for rule_cls in ALL_RULE_CLASSES}

    not_audited = {
        rule_id for rule_id, status in statuses.items() if status == RuleAuditStatus.NOT_AUDITED
    }

    assert not_audited == set()


def test_all_current_rules_explicitly_declare_an_audit_status() -> None:
    """Every rule's own class body sets `audit_status` -- none rely on
    (accidentally or otherwise) inheriting the base class default, since
    a future rule that forgets to declare one should read as NOT_AUDITED,
    not silently pass as consistent with the rest of the catalog."""
    for rule_cls in ALL_RULE_CLASSES:
        assert "audit_status" in vars(rule_cls), (
            f"{rule_cls.__name__} does not explicitly declare audit_status in its own class body"
        )


def test_exactly_the_expected_rules_have_an_open_standard_question() -> None:
    open_question_ids = {
        rule_cls().id
        for rule_cls in ALL_RULE_CLASSES
        if rule_cls().audit_status == RuleAuditStatus.INTERNALLY_AUDITED_WITH_OPEN_STANDARD_QUESTION
    }

    assert open_question_ids == set(_EXPECTED_OPEN_STANDARD_QUESTION_RULE_IDS)


def test_every_open_standard_question_rule_has_a_non_empty_note() -> None:
    for rule_cls in ALL_RULE_CLASSES:
        rule = rule_cls()
        if rule.audit_status == RuleAuditStatus.INTERNALLY_AUDITED_WITH_OPEN_STANDARD_QUESTION:
            assert rule.standard_question_note, (
                f"{rule.id} is flagged with an open standard question but has "
                "no standard_question_note"
            )


def test_every_non_open_question_rule_has_no_note() -> None:
    """A rule that is NOT_AUDITED or INTERNALLY_AUDITED with no open
    question must not carry a standard_question_note -- a note implies a
    specific, named open question, so an audit_status/note combination
    that doesn't agree is a contradiction, not a valid state."""
    for rule_cls in ALL_RULE_CLASSES:
        rule = rule_cls()
        if rule.audit_status != RuleAuditStatus.INTERNALLY_AUDITED_WITH_OPEN_STANDARD_QUESTION:
            assert rule.standard_question_note is None, (
                f"{rule.id} has audit_status {rule.audit_status!r} but still "
                f"carries a standard_question_note: {rule.standard_question_note!r}"
            )


def test_rule_engine_runs_all_rules_end_to_end() -> None:
    """RuleEngine (unchanged since Sprint 2) drives every registered rule.

    The feature is marked `feature_of_size=True` and datums A/B are
    defined so this drawing is otherwise clean with respect to the
    Sprint 7 rules (position-requires-feature-of-size,
    datum-reference-must-be-defined, etc.) -- isolating exactly the
    three originally-intended violations below. Coverage for the
    Sprint 7 rules themselves lives in their own test modules.
    """
    registry = RuleRegistry()
    for rule_cls in ALL_RULE_CLASSES:
        registry.register(rule_cls)

    bad_flatness = make_fcf(
        fcf_id="fcf-flatness",
        characteristic=GeometricCharacteristic.FLATNESS,
        datum_labels=["A"],
    )
    bad_position = make_fcf(
        fcf_id="fcf-position",
        characteristic=GeometricCharacteristic.POSITION,
        datum_labels=[],
    )
    bad_projected = make_fcf(
        fcf_id="fcf-projected",
        characteristic=GeometricCharacteristic.PERPENDICULARITY,
        datum_labels=["A"],
        tolerance=make_tolerance(projected_zone_height=5.0),
    )
    good_position = make_fcf(
        fcf_id="fcf-good",
        characteristic=GeometricCharacteristic.POSITION,
        datum_labels=["A", "B"],
    )
    feature = Feature(
        id="feat-1",
        feature_type=FeatureType.HOLE,
        feature_of_size=True,
        feature_control_frames=[bad_flatness, bad_position, bad_projected, good_position],
    )
    datums = [
        Datum(label="A", feature_type=DatumFeatureType.PLANE),
        Datum(label="B", feature_type=DatumFeatureType.PLANE),
    ]
    drawing = Drawing(id="dwg-1", title="Integration drawing", features=[feature], datums=datums)

    findings = RuleEngine(registry=registry).run(drawing)

    assert {finding.rule_id for finding in findings} == {
        "flatness-no-datum-references",
        "position-requires-datum-reference",
        "projected-zone-requires-position",
    }
    assert len(findings) == 3

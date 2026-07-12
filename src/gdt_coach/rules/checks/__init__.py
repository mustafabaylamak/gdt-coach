"""Concrete GD&T rule checks.

Each module in this package defines exactly one
:class:`~gdt_coach.rules.base.Rule` subclass and registers itself
against :data:`gdt_coach.rules.registry.default_registry` via the
``@default_registry.register`` decorator. Importing
``gdt_coach.rules.checks`` (this package) is what makes that
registration happen — importing ``gdt_coach.rules`` alone does not,
keeping the rule engine infrastructure free of any concrete rule.

``ALL_RULE_CLASSES`` is the single source of truth for "every concrete
rule that currently exists." Anything that needs to enumerate the
rules (the CLI, tests) should import this tuple rather than listing the
rule classes itself, so adding or removing a rule only ever means
touching this file and the rule's own module.
"""

from gdt_coach.rules.base import Rule
from gdt_coach.rules.checks.angularity_related_dimension_must_be_angular import (
    AngularityRelatedDimensionMustBeAngularRule,
)
from gdt_coach.rules.checks.circularity_no_datum_references import (
    CircularityNoDatumReferencesRule,
)
from gdt_coach.rules.checks.concentricity_symmetry_deprecated import (
    ConcentricitySymmetryDeprecatedRule,
)
from gdt_coach.rules.checks.cylindricity_no_datum_references import (
    CylindricityNoDatumReferencesRule,
)
from gdt_coach.rules.checks.datum_reference_must_be_defined import (
    DatumReferenceMustBeDefinedRule,
)
from gdt_coach.rules.checks.duplicate_datum_references import DuplicateDatumReferencesRule
from gdt_coach.rules.checks.flatness_no_datum_references import FlatnessNoDatumReferencesRule
from gdt_coach.rules.checks.form_mmc_requires_feature_of_size import (
    FormMmcRequiresFeatureOfSizeRule,
)
from gdt_coach.rules.checks.orientation_requires_datum_reference import (
    OrientationRequiresDatumReferenceRule,
)
from gdt_coach.rules.checks.position_material_condition_requires_feature_of_size import (
    PositionMaterialConditionRequiresFeatureOfSizeRule,
)
from gdt_coach.rules.checks.position_related_dimension_must_be_basic import (
    PositionRelatedDimensionMustBeBasicRule,
)
from gdt_coach.rules.checks.position_requires_datum_reference import (
    PositionRequiresDatumReferenceRule,
)
from gdt_coach.rules.checks.position_requires_feature_of_size import (
    PositionRequiresFeatureOfSizeRule,
)
from gdt_coach.rules.checks.projected_zone_requires_position import (
    ProjectedZoneRequiresPositionRule,
)
from gdt_coach.rules.checks.related_dimension_must_be_defined import (
    RelatedDimensionMustBeDefinedRule,
)
from gdt_coach.rules.checks.related_dimension_must_not_be_reference import (
    RelatedDimensionMustNotBeReferenceRule,
)
from gdt_coach.rules.checks.runout_always_rfs import RunoutAlwaysRfsRule
from gdt_coach.rules.checks.straightness_no_datum_references import (
    StraightnessNoDatumReferencesRule,
)

ALL_RULE_CLASSES: tuple[type[Rule], ...] = (
    FlatnessNoDatumReferencesRule,
    StraightnessNoDatumReferencesRule,
    CircularityNoDatumReferencesRule,
    CylindricityNoDatumReferencesRule,
    DuplicateDatumReferencesRule,
    PositionRequiresDatumReferenceRule,
    ProjectedZoneRequiresPositionRule,
    DatumReferenceMustBeDefinedRule,
    ConcentricitySymmetryDeprecatedRule,
    FormMmcRequiresFeatureOfSizeRule,
    OrientationRequiresDatumReferenceRule,
    PositionRequiresFeatureOfSizeRule,
    PositionMaterialConditionRequiresFeatureOfSizeRule,
    RunoutAlwaysRfsRule,
    RelatedDimensionMustBeDefinedRule,
    PositionRelatedDimensionMustBeBasicRule,
    RelatedDimensionMustNotBeReferenceRule,
    AngularityRelatedDimensionMustBeAngularRule,
)

__all__ = [
    "ALL_RULE_CLASSES",
    "AngularityRelatedDimensionMustBeAngularRule",
    "CircularityNoDatumReferencesRule",
    "ConcentricitySymmetryDeprecatedRule",
    "CylindricityNoDatumReferencesRule",
    "DatumReferenceMustBeDefinedRule",
    "DuplicateDatumReferencesRule",
    "FlatnessNoDatumReferencesRule",
    "FormMmcRequiresFeatureOfSizeRule",
    "OrientationRequiresDatumReferenceRule",
    "PositionMaterialConditionRequiresFeatureOfSizeRule",
    "PositionRelatedDimensionMustBeBasicRule",
    "PositionRequiresDatumReferenceRule",
    "PositionRequiresFeatureOfSizeRule",
    "ProjectedZoneRequiresPositionRule",
    "RelatedDimensionMustBeDefinedRule",
    "RelatedDimensionMustNotBeReferenceRule",
    "RunoutAlwaysRfsRule",
    "StraightnessNoDatumReferencesRule",
]

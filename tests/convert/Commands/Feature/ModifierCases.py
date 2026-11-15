from interchange.enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.enums.EnumValues import ValueKind
from interchange.features.FeatureContract import FeatureDef
from interchange.features.FeatureKinds import (
    CombineFeature,
    FilletFeature,
    ScaleFeature,
    ShellFeature,
)
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordParameter import ParameterValue

# legacy modifier cases need a valid length so prerequisite failure remains the observed boundary
KAmount = ParameterValue(1.0, ValueKind.KLength, "mm")

# operand and kind combinations must exercise qualification gaps using actual typed definitions
KModifierSpecs: dict[str, tuple[FeatureKind, FeatureDef, tuple[str, ...]]] = {
    "CombineEmpty": (FeatureKind.KBoolean, CombineFeature(), ()),
    "CombineOne": (FeatureKind.KBoolean, CombineFeature(), ("extrude",)),
    "CombineRepeated": (FeatureKind.KBoolean, CombineFeature(), ("extrude", "extrude")),
    "CombineReference": (FeatureKind.KBoolean, CombineFeature(), ("sketch", "extrude")),
    "CombineInactive": (FeatureKind.KBoolean, CombineFeature(), ("extrude", "other")),
    "CombineBadOperation": (
        FeatureKind.KBoolean,
        CombineFeature(BooleanOp.KCreate),
        ("extrude", "other"),
    ),
    "CombineValid": (FeatureKind.KBoolean, CombineFeature(), ("extrude", "other")),
    "CombineCut": (
        FeatureKind.KBoolean,
        CombineFeature(BooleanOp.KCutOperation),
        ("extrude", "other"),
    ),
    "FilletEmpty": (FeatureKind.KFillet, FilletFeature(KAmount), ()),
    "ShellReference": (FeatureKind.KShell, ShellFeature(KAmount), ("sketch",)),
    "ScaleEmpty": (FeatureKind.KScale, ScaleFeature(SpaceVector(1.0, 1.0, 1.0)), ()),
    "MismatchedKind": (FeatureKind.KScale, CombineFeature(), ("extrude",)),
}

# prerequisite refusals must remain separate from structurally complete but unqualified boolean cases
KModifierCases = tuple(
    NameValue
    for NameValue in KModifierSpecs
    if NameValue not in ("CombineValid", "CombineCut")
)

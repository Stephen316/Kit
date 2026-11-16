import pytest as Pytest

from convert.Formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.Formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Vocabulary.FeatureDefaults import (
    FeatureDefaults,
)
from tests.Convert.Formats.FusionCodec.Documents.PartFeatures.BodyTests import (
    KBodyCases,
)
from tests.Convert.Formats.FusionCodec.Documents.PartFeatures.FamilyCases import (
    FamilySpec,
)
from tests.Convert.Formats.FusionCodec.Documents.PartFeatures.LoftTests import (
    KLoftCases,
)
from tests.Convert.Formats.FusionCodec.Documents.PartFeatures.SweepTests import (
    KSweepCases,
)

# the required cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KRequired: tuple[tuple[str, str], ...] = (
    ("ASMRecipe", "m_Recipe"),
    ("DRBody", "operIdTypeMap"),
    ("DRPoint", "param"),
    ("DRPoint", "point3d"),
    ("DRPoint", "tangentPointData"),
    ("DRVector", "line3d"),
    ("DRVector", "param"),
    ("DRVector", "tangentPointData"),
    ("DcChamferFeature", "primaryIDRowIndexMap"),
    ("DcCombineFeature", "occDR2FeatIdMap"),
    ("DcDraftFeature", "m_facePickPoint"),
    ("DcIntParameter", "value"),
    ("DcMoveMatrix", "moveTransform"),
    ("DcPatternBaseData", "occOperationIdsMap"),
    ("DcPatternOccurrence", "occTagId"),
    ("DcRectangularPatternData", "deducedDir"),
    ("DcSplitFeature", "occDR2FeatIdMap"),
    ("DcSweepFeature", "profileNormal"),
    ("ETCachedCircleArc", "rCachedGeometry"),
    ("ETCachedLineSeg3d", "rCachedGeometry"),
    ("ETCachedPoint3d", "rCachedGeometry"),
    ("OccurrenceDataRef", "OccurrenceACTRef"),
    ("OccurrenceDataRef", "cachedTransform"),
    ("SketchCurveEntityRecipe", "secondaryTag"),
    ("SketchEntityRecipe", "sketchId"),
    ("SketchEntityRecipe", "tag"),
)

# the drop cases cases must remain explicit so native document reconstruction exercises the intended compatibility boundary
KDropCases: tuple[tuple[tuple[KPartFeature, ...], str, str], ...] = (
    (KSweepCases["SweepBend"], "DcSweepFeature", "profileNormal"),
    (KSweepCases["SweepBend"], "DcSweepToolBody", "isAlongDistanceParameterValid"),
    (KLoftCases["LoftRects"], "DcLoftSectionData", "sectionType"),
    (KLoftCases["LoftRects"], "DcLoftFeature", "booleanOperation"),
    (KBodyCases["BodyRectPattern"][0], "DcRectangularPatternData", "deducedDir"),
    (KBodyCases["BodyRectPattern"][0], "DcRectangularPatternData", "computeType"),
)


# the neutral contract needs boundary coverage so stored document relationships remain consistent
def TestNeutral() -> None:
    for ClassName, Fields in FeatureDefaults().items():
        for FieldName, Value in Fields.items():
            assert not isinstance(Value, dict), ClassName + "." + FieldName
            assert not Value, ClassName + "." + FieldName


# the required contract needs boundary coverage so stored document relationships remain consistent
@Pytest.mark.parametrize(("ClassName", "FieldName"), KRequired)
def TestRequired(ClassName: str, FieldName: str) -> None:
    assert FieldName not in FeatureDefaults()[ClassName]


# the miss raises contract needs boundary coverage so stored document relationships remain consistent
@Pytest.mark.parametrize(("Features", "ClassName", "FieldName"), KDropCases)
def TestMissRaises(
    Features: tuple[KPartFeature, ...],
    ClassName: str,
    FieldName: str,
    MonkeyPatch: Pytest.MonkeyPatch,
) -> None:
    Original = AuthorState.Change

    # shared skip field setup keeps fixtures consistent so native document reconstruction failures identify the intended compatibility boundary
    def SkipField(Author: AuthorState, RoleName: str, **Fields: object) -> None:
        Remaining = {
            Named: Value for Named, Value in Fields.items() if Named != FieldName
        }
        _ = Original(Author, RoleName, **Remaining)

    MonkeyPatch.setattr(AuthorState, "Change", SkipField)
    Message = "Authored " + ClassName + " lacks required fields: " + FieldName
    with Pytest.raises(ValueError, match=Message):
        _ = EmitDocument(FamilySpec(Features))

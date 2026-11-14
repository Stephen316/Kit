import pytest as Pytest

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.PartFeature import (
    KPartFeature,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Vocabulary.FeatureDefaults import (
    FeatureDefaults,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.BodyTests import (
    KBodyCases,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.FamilyCases import (
    FamilySpec,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.LoftTests import (
    KLoftCases,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.SweepTests import (
    KSweepCases,
)

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
KDropCases: tuple[tuple[tuple[KPartFeature, ...], str, str], ...] = (
    (KSweepCases["SweepBend"], "DcSweepFeature", "profileNormal"),
    (KSweepCases["SweepBend"], "DcSweepToolBody", "isAlongDistanceParameterValid"),
    (KLoftCases["LoftRects"], "DcLoftSectionData", "sectionType"),
    (KLoftCases["LoftRects"], "DcLoftFeature", "booleanOperation"),
    (KBodyCases["BodyRectPattern"][0], "DcRectangularPatternData", "deducedDir"),
    (KBodyCases["BodyRectPattern"][0], "DcRectangularPatternData", "computeType"),
)


def TestNeutral() -> None:
    for ClassName, Fields in FeatureDefaults().items():
        for FieldName, Value in Fields.items():
            assert not isinstance(Value, dict), ClassName + "." + FieldName
            assert not Value, ClassName + "." + FieldName


@Pytest.mark.parametrize(("ClassName", "FieldName"), KRequired)
def TestRequired(ClassName: str, FieldName: str) -> None:
    assert FieldName not in FeatureDefaults()[ClassName]


@Pytest.mark.parametrize(("Features", "ClassName", "FieldName"), KDropCases)
def TestMissRaises(
    Features: tuple[KPartFeature, ...],
    ClassName: str,
    FieldName: str,
    MonkeyPatch: Pytest.MonkeyPatch,
) -> None:
    Original = AuthorState.Change

    def SkipField(Author: AuthorState, RoleName: str, **Fields: object) -> None:
        Remaining = {
            Named: Value for Named, Value in Fields.items() if Named != FieldName
        }
        _ = Original(Author, RoleName, **Remaining)

    MonkeyPatch.setattr(AuthorState, "Change", SkipField)
    Message = "Authored " + ClassName + " lacks required fields: " + FieldName
    with Pytest.raises(ValueError, match=Message):
        _ = EmitDocument(FamilySpec(Features))

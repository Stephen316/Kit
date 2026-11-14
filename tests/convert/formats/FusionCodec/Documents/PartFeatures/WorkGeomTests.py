from sys import version_info as PythonVersion

from pytest import mark as MarkTests

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.DocumentCodec.PartFeatures.SolvePart import SolvePart
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.EntityCodec.Model.OptionalValue import OptionalValue
from convert.formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe
from convert.formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue
from convert.formats.Fusion.EntityCodec.Recipes.Model.VertexRecipe import VertexRecipe
from tests.convert.formats.FusionCodec.Documents.PartFeatures.FamilyCases import (
    FamilySpec,
    KFamilyCases,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.PartCases import (
    KOracleRoot,
)
from tests.convert.formats.FusionCodec.Documents.PartFeatures.PartRecords import (
    PartRecords,
)

KWorkFields: dict[str, tuple[str, ...]] = {
    "DcWorkAxis": ("creationType", "featureBaseName", "featureUserName"),
    "DcWorkPoint": ("creationType", "chainPropagation", "pointOnPathType"),
    "WorkAxis": ("userName", "line", "lowerParam", "upperParam", "lineThickness"),
    "WorkPoint": ("userName", "id", "point", "lineThickness"),
    "DRVector": ("axisTrackType", "line3d", "param", "refType", "trackingType"),
    "DRPoint": ("boundingboxIndex", "param", "point3d", "refType", "trackingType"),
}


def WorkPayloads(Model: DocumentModel) -> list[object]:
    Found: list[object] = []
    for Fields in PartRecords(Model, "ASMRecipe"):
        Stored = Fields["m_Recipe"]
        if not isinstance(Stored, OptionalValue):
            continue
        Recipe = Stored.Value
        if not isinstance(Recipe, RecipeValue):
            continue
        Payload = Recipe.Payload
        IsAxis = isinstance(Payload, EdgeRecipe) and Payload.ReferenceFaceIndex == 0
        if IsAxis or isinstance(Payload, VertexRecipe):
            Found.append(Payload)
    return Found


def WorkShape(Model: DocumentModel) -> dict[str, list[object]]:
    Shape: dict[str, list[object]] = {
        ClassName: [
            tuple(Fields[NameValue] for NameValue in Names)
            for Fields in PartRecords(Model, ClassName)
            if Fields.get("isOrigin") is not True
        ]
        for ClassName, Names in KWorkFields.items()
    }
    Tracking = [Fields["trackingType"] for Fields in PartRecords(Model, "BrepRef")]
    Shape["BrepRef"] = [Value for Value in (33, 513) if Value in Tracking]
    Shape["ASMRecipe"] = WorkPayloads(Model)
    return Shape


def TestWorkState() -> None:
    _, Stages = SolvePart(FamilySpec(KFamilyCases["ConstructionSet"][0]))
    assert [Stage.StateId for Stage in Stages] == [4, 4, 4, 4]
    assert [Stage.Operations for Stage in Stages] == [
        (300, 301, 302),
        (303,),
        (304,),
        (305,),
    ]
    assert all(Stage.After == Stages[0].After for Stage in Stages)


@MarkTests.skipif(
    PythonVersion < (3, 14), reason="native Fusion control requires ZIP Zstandard"
)
def TestWorkNative() -> None:
    Features = KFamilyCases["ConstructionSet"][0]
    Authored = ReadDocument(EmitDocument(FamilySpec(Features)))
    Control = (KOracleRoot / "Controls" / "ConstructionSet.f3d").read_bytes()
    Native = ReadDocument(Control)
    Expected = WorkShape(Native)
    assert all(Expected[ClassName] for ClassName in KWorkFields)
    assert WorkShape(Authored) == Expected

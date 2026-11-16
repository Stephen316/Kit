from pathlib import Path as FilePath

from pytest import mark as TestMarks, raises as RaisesError

from tests.Convert.Formats.FusionCodec.Features.ForgeFeature import ForgeFeature
from tests.Convert.Formats.FusionCodec.Parameters.RebuildFeatures import RebuildFeatures

# feature root needs a stable location so native document reconstruction resolves inputs independently of the caller working directory
KFeatureRoot = (
    FilePath(__file__).resolve().parents[5] / "re/Fusion/LocalOracle/Features"
)


# the schema shift contract needs boundary coverage so stored document relationships remain consistent
@TestMarks.parametrize(
    ("FileName", "ClassGuid"),
    (
        ("circle_sketch.f3d", "A2052F46-21B4-4AAA-9AF1-C371F0AB6CAB"),
        ("extrude_07mm.f3d", "2EDC2536-D95B-4469-8ACA-DC07124D9C43"),
    ),
)
def TestSchemaShift(FileName: str, ClassGuid: str) -> None:
    Altered = ForgeFeature(KFeatureRoot / FileName, ClassGuid, ShiftSchema=True)
    with RaisesError(
        ValueError, match="^Unsupported Fusion feature class or inheritance version$"
    ):
        _ = RebuildFeatures(Altered)


# the feature tail contract needs boundary coverage so stored document relationships remain consistent
@TestMarks.parametrize(
    ("FileName", "ClassGuid"),
    (
        ("circle_sketch.f3d", "8DA771B7-52ED-42FC-94E2-2353FE141373"),
        ("extrude_07mm.f3d", "DD405BC2-D673-44F0-8833-5CB2A1C186C7"),
    ),
)
def TestFeatureTail(FileName: str, ClassGuid: str) -> None:
    Altered = ForgeFeature(KFeatureRoot / FileName, ClassGuid)
    with RaisesError(ValueError, match="^Unexplained trailing Fusion feature bytes$"):
        _ = RebuildFeatures(Altered)

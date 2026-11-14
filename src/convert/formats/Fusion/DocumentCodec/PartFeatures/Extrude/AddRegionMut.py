from math import hypot as Hypotenuse

from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Profile.SketchPlan import (
    SketchPlan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import SpanStart
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ToolSlab import (
    ToolLabels,
    ToolSlab,
)
from convert.formats.Fusion.DocumentCodec.Rectangle.RectangleTag import RectangleTag


def RegionTags(
    Feature: ExtrudeSpec, Sketched: SketchPlan, Operation: int
) -> list[dict[str, object]]:
    LoopValue = ToolSlab(Feature, Operation).Loops[0]
    TagList: list[dict[str, object]] = []
    for Label, Segment in zip(ToolLabels(Feature, Operation), Sketched.Edges):
        SpanValue = next(Value for Value in LoopValue if Value.Label == Label)
        Direction = 0
        if Segment.StartIndex is not None:
            Start, Point = SpanStart(SpanValue), Sketched.PointsCm[Segment.StartIndex]
            Direction = int(Hypotenuse(Start[0] - Point[0], Start[1] - Point[1]) > 1e-7)
        TagList.append(RectangleTag(Segment.CurveTag, Direction))
    return TagList


def AddRegionMut(
    Author: AuthorState,
    Prefix: str,
    TagList: list[dict[str, object]],
    Owner: str = "",
) -> None:
    Reference = Author.Reference
    MainRole = Owner or Prefix + "feature"
    AddNodeMut(Author, Prefix + "profile", "ModelDataRef", MainRole)
    AddNodeMut(Author, Prefix + "region", "SketchRegionRef", MainRole)
    Author.Allocate(Prefix + "region_recipe", "SketchRegionRecipe")
    Author.Change(
        Prefix + "profile", dataRefs=[Reference(Prefix + "region")], trackingType=65
    )
    ScopeValue = [
        Author.MakeGroup(
            "PassiveScopeValue",
            dict(
                assetId=Author.AssetId,
                scopeEntityIdentifier=str(Author.Roles[Prefix + "sketch"]),
                scopeIdType=1,
                segmentId=Author.Policy.DesignSegmentId,
            ),
        )
    ]
    Author.Change(
        Prefix + "region",
        rRecipe=Reference(Prefix + "region_recipe"),
        rScope=ScopeValue,
        trackingType=65,
    )
    Recipe = {"first": TagList, "second": True}
    RecipeData = [
        Author.MakeGroup(
            "SkRegionRecipeDataValue",
            dict(faceRecipe=[Recipe], originalFaceRecipes=[]),
        )
    ]
    Author.Change(
        Prefix + "region_recipe",
        rSketchRegionRef=Reference(Prefix + "region"),
        skRegionRecipe=[RecipeData],
    )

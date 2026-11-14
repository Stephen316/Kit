from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Profile.SketchPlan import (
    SketchEdge,
    SketchPlan,
)
from convert.formats.Fusion.DocumentCodec.Rectangle.RectangleTag import RectangleTag

KFirstCurveTag = 3


def Neighbours(
    Sketched: SketchPlan, Segment: SketchEdge, Point: int | None
) -> list[int]:
    if Point is None:
        return []
    return [
        Other.CurveTag
        for Other in Sketched.Edges
        if Other is not Segment and Point in (Other.StartIndex, Other.FinishIndex)
    ]


def AddSeedsMut(
    Author: AuthorState, Prefix: str, Sketched: SketchPlan, Order: tuple[int, ...]
) -> list[dict[str, object]]:
    Pairs: list[dict[str, object]] = []
    for Index, Place in enumerate(Order):
        Segment = Sketched.Edges[Place]
        SeedRole = Prefix + "seed" + str(Index)
        Author.Allocate(SeedRole, "SketchCurveProgenitor", NamedPairs=[])
        Author.Allocate(SeedRole + "_recipe", "SketchCurveRecipe")
        Author.Change(SeedRole, rRecipe=Author.Reference(SeedRole + "_recipe"))
        Author.Change(
            SeedRole + "_recipe",
            profileEdgeTagData=dict(
                version=0,
                sketchTags=[RectangleTag(Segment.CurveTag, 1)],
                startAdjacentPrimaryTagIds=Neighbours(
                    Sketched, Segment, Segment.StartIndex
                ),
                endAdjacentPrimaryTagIds=Neighbours(
                    Sketched, Segment, Segment.FinishIndex
                ),
            ),
        )
        Pairs.append(
            {"first": Author.Reference(SeedRole), "second": KFirstCurveTag + Index}
        )
    return Pairs

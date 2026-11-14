from math import cos as Cosine, radians as Radians, sin as SineOf
from typing import TypeAlias

from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Design.PartNodes import (
    AddNodeMut,
    PartScope,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Hole.AddHoleRefs import (
    AddPlaceMut,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ArcCurve import ArcCurve
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import (
    LineCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Pattern.PlaneFrame import (
    PointOf,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Profile.SketchPlan import (
    SketchEdge,
    SketchPlan,
)

KPathTracking = 5
KPathSketch: TypeAlias = tuple[SketchPlan, int]
KVertexNames = (
    ("EdgeEndVertexProgenitor", "_end"),
    ("EdgeStartVertexProgenitor", "_start"),
)


def AddPointSeedMut(
    Author: AuthorState, RoleName: str, Sketch: int, TagValue: int
) -> None:
    Author.Allocate(RoleName, "EntityProgenitor")
    Recipe: dict[str, object] = {"sketchId": Sketch, "tag": TagValue}
    Author.Allocate(RoleName + "_recipe", "SketchEntityRecipe", Fields=Recipe)
    Author.Change(RoleName, m_entityRecipe=Author.Reference(RoleName + "_recipe"))


def AddCurveRecipe(
    Author: AuthorState, RoleName: str, Sketch: int, Segment: SketchEdge
) -> None:
    Recipe: dict[str, object] = dict(secondaryTag=0, sketchId=Sketch)
    Recipe["tag"] = Segment.CurveTag
    Author.Allocate(RoleName, "SketchCurveEntityRecipe", Fields=Recipe)


def AddEdgeSeedMut(
    Author: AuthorState, RoleName: str, Segment: SketchEdge, Drawn: KPathSketch
) -> dict[str, object] | None:
    PathPlan, Sketch = Drawn
    Named: list[dict[str, object]] = [
        {"name": NameValue, "metatype": "StrongRefMetaType", "role": RoleName + Suffix}
        for NameValue, Suffix in KVertexNames
    ]
    Author.Allocate(RoleName, "EntityProgenitor", NamedPairs=Named)
    AddCurveRecipe(Author, RoleName + "_recipe", Sketch, Segment)
    Author.Change(RoleName, m_entityRecipe=Author.Reference(RoleName + "_recipe"))
    for Place, Suffix in (
        (Segment.StartIndex, "_start"),
        (Segment.FinishIndex, "_end"),
    ):
        TagValue = PathPlan.PointTags[Place or 0]
        AddPointSeedMut(Author, RoleName + Suffix, Sketch, TagValue)
    return Author.Reference(RoleName)


def CurveCache(Segment: SketchEdge) -> tuple[str, dict[str, object]]:
    Curve = Segment.Curve
    if isinstance(Curve, LineCurve):
        Start = (Curve.StartMm[0] / 10.0, Curve.StartMm[1] / 10.0, 0.0)
        Finish = (Curve.FinishMm[0] / 10.0, Curve.FinishMm[1] / 10.0, 0.0)
        Shift = (Finish[0] - Start[0], Finish[1] - Start[1], 0.0)
        Geometry: dict[str, object] = {
            "startPoint": PointOf(Start),
            "displacement": PointOf(Shift),
        }
        return "ETCachedLineSeg3d", Geometry
    if not isinstance(Curve, ArcCurve):
        raise ValueError("Fusion sweep paths hold lines and arcs")
    Angle = Radians(Curve.StartDegrees)
    Geometry = dict[str, object](
        center=PointOf((Curve.CenterMm[0] / 10.0, Curve.CenterMm[1] / 10.0, 0.0)),
        normal=PointOf((0.0, 0.0, 1.0)),
        refVec=PointOf((Cosine(Angle) + 0.0, SineOf(Angle) + 0.0, 0.0)),
        radius=Curve.RadiusMm / 10.0,
        startAngle=0.0,
        endAngle=Radians(Curve.SweepDegrees),
    )
    return "ETCachedCircleArc", Geometry


def AddPathRefMut(
    Author: AuthorState, Prefix: str, Index: int, Drawn: KPathSketch
) -> str:
    Reference, Segment = Author.Reference, Drawn[0].Edges[Index]
    RoleName, SeedName = Prefix + "path_ref" + str(Index), Prefix + "path_cache"
    AddNodeMut(Author, RoleName, "EntityDataRef", Prefix + "feature")
    Sketch = Drawn[1]
    AddCurveRecipe(Author, RoleName + "_recipe", Sketch, Segment)
    ClassName, Geometry = CurveCache(Segment)
    Author.Allocate(
        RoleName + "_cache", ClassName, Fields={"rCachedGeometry": Geometry}
    )
    SeedName += str(Index)
    Author.Change(
        RoleName + "_cache",
        progenitor=AddEdgeSeedMut(Author, SeedName, Segment, Drawn),
        startPtProgenitor=Reference(SeedName + "_start"),
        endPtProgenitor=Reference(SeedName + "_end"),
    )
    Author.Change(
        RoleName,
        rRecipe=Reference(RoleName + "_recipe"),
        rScope=PartScope(Author),
        caches=[Reference(RoleName + "_cache")],
        trackingType=KPathTracking,
    )
    return RoleName


def AddPathMut(Author: AuthorState, Prefix: str, Drawn: KPathSketch) -> list[str]:
    AddPlaceMut(Author, Prefix, ("path", "ModelDataRef"), {})
    RefRoles = [
        AddPathRefMut(Author, Prefix, Index, Drawn)
        for Index in range(len(Drawn[0].Edges))
    ]
    Author.Change(
        Prefix + "path",
        dataRefs=[Author.Reference(RoleName) for RoleName in RefRoles],
        trackingType=KPathTracking,
    )
    return [Prefix + "path", *RefRoles]

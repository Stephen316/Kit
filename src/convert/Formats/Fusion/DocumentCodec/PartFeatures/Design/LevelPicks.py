from math import atan2 as ArcTangent, cos as Cosine, sin as SineOf

from convert.Formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundChain import (
    KUsePlace,
    ShapeUsers,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundGroup import (
    GroupPlans,
    IsWithCap,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundEdges import ArcSense
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundPlan import (
    RoundPlan,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Brep.SpaceMath import (
    KSpaceVector,
    SubVector,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Design.RoofRecipe import (
    KRimOrders,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Design.SelectRecipe import (
    PickFace,
    PickVertex,
    RecipeTags,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.History.DraftEdges import (
    EdgeLabel,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.History.FaceKey import (
    FaceLabelOf,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Pattern.PlaneFrame import PointOf
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.BuildShape import (
    BuildShape,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import ShapeBody
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import (
    KShapeEdge,
    ShapeUse,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.PrismSolid import (
    PrismSolid,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    IsFullCircle,
)
from convert.Formats.Fusion.EntityCodec.Recipes.Model.EdgeRecipe import EdgeRecipe
from convert.Formats.Fusion.EntityCodec.Recipes.Model.RecipeValue import RecipeValue
from convert.Formats.Fusion.EntityCodec.Recipes.Model.VertexRecipe import VertexRecipe

# the level pick shape must stay shared so design feature construction uses one contract for compatible values
KLevelPick = tuple[RecipeValue, str, dict[str, object]]

# full angle must remain consistent across callers so modeling operations retain their document and timeline ownership
KFullAngle = 6.283185307179586


# the neighbour label contract needs a shared interpretation so modeling operations retain their document and timeline ownership
def NeighbourLabel(
    Shape: ShapeBody,
    Users: dict[KShapeEdge, list[KUsePlace]],
    PlanValue: RoundPlan,
    UseIndex: int,
) -> FaceLabel:
    LoopValue = Shape.Faces[PlanValue.CapIndex].Loops[PlanValue.LoopIndex]
    EdgeValue = LoopValue[UseIndex % len(LoopValue)].Edge
    Others = [Place[0] for Place in Users[EdgeValue] if Place[0] != PlanValue.CapIndex]
    return FaceLabelOf(Shape.Faces[Others[0]])


# the rim recipe contract needs a shared interpretation so modeling operations retain their document and timeline ownership
def RimRecipe(
    RimLabel: FaceLabel, WallValue: FaceLabel, CapValue: FaceLabel
) -> RecipeValue:
    Sides = (PickFace(1), PickFace(2))
    Loose = EdgeRecipe(0, -1, (), (), -1)
    Corner = VertexRecipe(-1, Sides, (Loose,), KRimOrders)
    Payload = EdgeRecipe(0, -1, Sides, (Corner,), -1)
    return RecipeValue(3, RecipeTags([RimLabel, WallValue, CapValue]), (), Payload)


# the bare recipe contract needs a shared interpretation so modeling operations retain their document and timeline ownership
def BareRecipe(WallValue: FaceLabel, CapValue: FaceLabel) -> RecipeValue:
    Payload = EdgeRecipe(-1, -1, (PickFace(0), PickFace(1)), (), -1)
    return RecipeValue(3, RecipeTags([WallValue, CapValue]), (), Payload)


# the side recipe contract needs a shared interpretation so modeling operations retain their document and timeline ownership
def SideRecipe(Labels: list[FaceLabel]) -> RecipeValue:
    Payload = EdgeRecipe(
        -1,
        -1,
        (PickFace(0), PickFace(1)),
        (PickVertex((0, 1, 2)), PickVertex((3, 1, 0))),
        -1,
    )
    return RecipeValue(3, RecipeTags(Labels), (), Payload)


# the arc cache contract needs a shared interpretation so modeling operations retain their document and timeline ownership
def ArcCache(
    SpanValue: ArcSpan, Start: KSpaceVector, Sense: float
) -> dict[str, object]:
    Angle = ArcTangent(
        Start[1] - SpanValue.CenterCm[1], Start[0] - SpanValue.CenterCm[0]
    )
    Sweep = abs(SpanValue.SweepAngle)
    if IsFullCircle(SpanValue):
        Angle, Sweep = Angle + KFullAngle / 2.0, KFullAngle
    return dict[str, object](
        center=PointOf((SpanValue.CenterCm[0], SpanValue.CenterCm[1], Start[2])),
        normal=PointOf((0.0, 0.0, Sense)),
        refVec=PointOf((Cosine(Angle) + 0.0, SineOf(Angle) + 0.0, 0.0)),
        radius=SpanValue.RadiusCm,
        startAngle=0.0,
        endAngle=Sweep,
    )


# link cache must resolve unambiguously so modeling operations retain their document and timeline ownership
def LinkCache(
    UseValue: ShapeUse, EdgeEnds: tuple[KSpaceVector, KSpaceVector], WithCap: bool
) -> tuple[str, dict[str, object]]:
    EdgeValue = UseValue.Edge
    if isinstance(EdgeValue, LevelEdge) and isinstance(EdgeValue.Span, ArcSpan):
        Sense = ArcSense(EdgeValue.Span, UseValue) * (1.0 if WithCap else -1.0)
        Circle = ArcCache(EdgeValue.Span, EdgeEnds[0], Sense)
        return "ETCachedCircleArc", {"rCachedGeometry": Circle}
    Geometry: dict[str, object] = {
        "startPoint": PointOf(EdgeEnds[0]),
        "displacement": PointOf(SubVector(EdgeEnds[1], EdgeEnds[0])),
    }
    return "ETCachedLineSeg3d", {"rCachedGeometry": Geometry}


# link pick must resolve unambiguously so modeling operations retain their document and timeline ownership
def LinkPick(
    Shape: ShapeBody,
    Users: dict[KShapeEdge, list[KUsePlace]],
    PlanValue: RoundPlan,
    Place: tuple[int, bool],
) -> KLevelPick:
    Index, WithCap = Place
    LinkValue = PlanValue.Links[Index]
    UseValue = Shape.Faces[PlanValue.CapIndex].Loops[PlanValue.LoopIndex][
        LinkValue.UseIndex
    ]
    WallValue = FaceLabelOf(Shape.Faces[LinkValue.WallIndex])
    CapValue = FaceLabelOf(Shape.Faces[PlanValue.CapIndex])
    EdgeEnds = (LinkValue.Start, LinkValue.Finish)
    if not WithCap:
        EdgeEnds = (LinkValue.Finish, LinkValue.Start)
    CacheClass, Cache = LinkCache(UseValue, EdgeEnds, WithCap)
    if PlanValue.Closed and len(PlanValue.Links) == 1:
        RimLabel = EdgeLabel(Shape, UseValue.Edge)
        if RimLabel is None:
            return BareRecipe(WallValue, CapValue), CacheClass, Cache
        return RimRecipe(RimLabel, WallValue, CapValue), CacheClass, Cache
    Opening = NeighbourLabel(Shape, Users, PlanValue, LinkValue.UseIndex - 1)
    Closing = NeighbourLabel(Shape, Users, PlanValue, LinkValue.UseIndex + 1)
    return SideRecipe([WallValue, CapValue, Opening, Closing]), CacheClass, Cache


# the level picks contract needs a shared interpretation so modeling operations retain their document and timeline ownership
def LevelPicks(
    Solid: PrismSolid, Points: tuple[tuple[float, float], ...], LevelCm: float
) -> list[KLevelPick]:
    Shape = BuildShape(Solid)
    Users = ShapeUsers(Shape)
    Placed = tuple((PointCm[0], PointCm[1], LevelCm) for PointCm in Points)
    Numbered: list[tuple[int, KLevelPick]] = []
    for PlanValue in GroupPlans(Shape, Placed):
        for Index, Number in enumerate(PlanValue.Numbers):
            LinkValue = PlanValue.Links[Index]
            WithCap = IsWithCap(Shape, PlanValue, LinkValue, Solid.Blends)
            Picked = LinkPick(Shape, Users, PlanValue, (Index, WithCap))
            Numbered.append((Number, Picked))

    # ordering by entry 0 must stay deterministic so design feature construction resolves equivalent inputs consistently
    return [Entry[1] for Entry in sorted(Numbered, key=lambda Entry: Entry[0])]

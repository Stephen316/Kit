from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.EdgeRound import EdgeRound
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundEdges import (
    ArcSense,
    CornerFrame,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundMass import (
    KMassKeys,
    LineMass,
    RingMass,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundPlan import RoundPlan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.SectionMoments import (
    SectionMoments,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import ShapeBody
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan


def LinkMass(
    Shape: ShapeBody,
    PlanValue: RoundPlan,
    Frames: list[CornerFrame],
    Context: tuple[int, EdgeRound],
) -> dict[str, float]:
    Index, Round = Context
    UseValue = Shape.Faces[PlanValue.CapIndex].Loops[PlanValue.LoopIndex][
        PlanValue.Links[Index].UseIndex
    ]
    EdgeValue = UseValue.Edge
    if isinstance(EdgeValue, LevelEdge) and isinstance(EdgeValue.Span, ArcSpan):
        Turning = (PlanValue.Sense, ArcSense(EdgeValue.Span, UseValue))
        return RingMass(EdgeValue.Span, Frames[Index], Turning, Round)
    Closing = Frames[(Index + 1) % len(Frames)]
    return LineMass((Frames[Index], Closing), PlanValue.Sense, Round)


def PlanMass(
    Shape: ShapeBody, PlanValue: RoundPlan, Frames: list[CornerFrame], Round: EdgeRound
) -> dict[str, float]:
    Total = dict.fromkeys((*KMassKeys, "area"), 0.0)
    for Index in range(len(PlanValue.Links)):
        Piece = LinkMass(Shape, PlanValue, Frames, (Index, Round))
        for KeyValue in KMassKeys:
            Total[KeyValue] -= PlanValue.Sense * Piece[KeyValue]
        Total["area"] += Piece["area"]
    if not PlanValue.Closed:
        Total["area"] -= 2.0 * PlanValue.Sense * SectionMoments(Round)[(0, 0)]
    return Total

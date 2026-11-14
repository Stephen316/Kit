from dataclasses import replace as ReplaceValue

from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.EdgeRound import EdgeRound
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.FreeEdge import FreeEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.FreeFace import FreeFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundChain import (
    KUsePlace,
    ShapeUsers,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundGroup import (
    GroupPlans,
    PlanLegs,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundEdges import (
    CornerFrame,
    CrossEdge,
    FrameAt,
    LinkEdges,
    MitreFrame,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundFrame import (
    CapNormal,
    SideNormal,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundMass import (
    KMassKeys,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundPlan import (
    RoundPlan,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundSum import PlanMass
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundSurface import (
    LinkSurface,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundTrim import (
    InsertCross,
    JointEdge,
    SwapFaces,
    TrimEdge,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.SpaceMath import (
    DotProduct,
    KSpaceVector,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.CapFace import CapFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import (
    KShapeFace,
    ShapeBody,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import (
    KShapeEdge,
    ShapeUse,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.WallFace import WallFace
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.FaceLabel import FaceLabel
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan

KUsers = dict[KShapeEdge, list[KUsePlace]]
KSwaps = dict[KShapeEdge, KShapeEdge]


def ChainFrames(
    Shape: ShapeBody, PlanValue: RoundPlan, Round: EdgeRound
) -> list[CornerFrame]:
    CapValue = Shape.Faces[PlanValue.CapIndex]
    if not isinstance(CapValue, CapFace):
        raise ValueError("Fusion edge rounds need a cap face")
    Points: list[KSpaceVector] = [LinkValue.Start for LinkValue in PlanValue.Links]
    if not PlanValue.Closed:
        Points.append(PlanValue.Links[-1].Finish)
    Frames: list[CornerFrame] = []
    for Index, Point in enumerate(Points):
        WallValue = LinkWall(Shape, PlanValue, min(Index, len(PlanValue.Links) - 1))
        AxisSet = (SideNormal(WallValue, Point), CapNormal(CapValue))
        if not PlanValue.Mitres[Index]:
            Frames.append(FrameAt(Point, AxisSet, PlanValue.Sense, Round))
            continue
        Incoming = SideNormal(LinkWall(Shape, PlanValue, Index - 1), Point)
        Sides = (Incoming, AxisSet[0])
        Context = (PlanValue.Sense, Round)
        Frames.append(MitreFrame(Point, Sides, AxisSet[1], Context))
    return Frames


def LinkWall(Shape: ShapeBody, PlanValue: RoundPlan, Index: int) -> WallFace:
    WallValue = Shape.Faces[PlanValue.Links[Index].WallIndex]
    if not isinstance(WallValue, WallFace):
        raise ValueError("Fusion edge rounds need side faces")
    return WallValue


def TrimMut(
    Swaps: KSwaps, EdgeValue: KShapeEdge, Point: KSpaceVector, Target: KSpaceVector
) -> None:
    Swaps[EdgeValue] = TrimEdge(Swaps.get(EdgeValue, EdgeValue), Point, Target)


def JointTrimMut(
    Swaps: KSwaps, Users: KUsers, PlanValue: RoundPlan, Frames: list[CornerFrame]
) -> None:
    Count = len(PlanValue.Links)
    if PlanValue.Closed and Count == 1:
        return
    for Index in range(0 if PlanValue.Closed else 1, Count):
        Walls = {PlanValue.Links[Index - 1].WallIndex, PlanValue.Links[Index].WallIndex}
        Frame = Frames[Index]
        TrimMut(
            Swaps, JointEdge(Users, Walls, Frame.Point), Frame.Point, Frame.WallPoint
        )


def CheckSquare(FaceValue: KShapeFace, Frame: CornerFrame) -> None:
    if not isinstance(FaceValue, WallFace) or not isinstance(FaceValue.Span, LineSpan):
        raise ValueError("Fusion edge rounds need flat end faces")
    Facing = DotProduct(SideNormal(FaceValue, Frame.Point), Frame.Heading)
    if abs(abs(Facing) - 1.0) > 1e-9:
        raise ValueError("Fusion edge rounds need end faces square to the edge")


def EndTrimMut(
    Swaps: KSwaps,
    Context: tuple[ShapeBody, KUsers, RoundPlan],
    Frames: list[CornerFrame],
) -> list[tuple[int, CornerFrame]]:
    Shape, Users, PlanValue = Context
    if PlanValue.Closed:
        return []
    LoopValue = Shape.Faces[PlanValue.CapIndex].Loops[PlanValue.LoopIndex]
    EndList: list[tuple[int, CornerFrame]] = []
    for LinkValue, Frame, Direction in (
        (PlanValue.Links[0], Frames[0], -1),
        (PlanValue.Links[-1], Frames[-1], 1),
    ):
        CapEdge = LoopValue[(LinkValue.UseIndex + Direction) % len(LoopValue)].Edge
        Others = [
            Place[0] for Place in Users[CapEdge] if Place[0] != PlanValue.CapIndex
        ]
        CheckSquare(Shape.Faces[Others[0]], Frame)
        RiseValue = JointEdge(Users, {LinkValue.WallIndex, Others[0]}, Frame.Point)
        TrimMut(Swaps, CapEdge, Frame.Point, Frame.CapPoint)
        TrimMut(Swaps, RiseValue, Frame.Point, Frame.WallPoint)
        EndList.append((Others[0], Frame))
    return EndList


def BlendLoops(
    Edges: tuple[FreeEdge, FreeEdge], Crosses: list[FreeEdge], Index: int
) -> tuple[tuple[ShapeUse, ...], ...]:
    CapEdge, WallEdge = Edges
    if not Crosses:
        return ((ShapeUse(CapEdge, False),), (ShapeUse(WallEdge, True),))
    return (
        (
            ShapeUse(CapEdge, False),
            ShapeUse(Crosses[Index], True),
            ShapeUse(WallEdge, True),
            ShapeUse(Crosses[(Index + 1) % len(Crosses)], False),
        ),
    )


def BlendFacesMut(
    Shape: ShapeBody,
    PlanValue: RoundPlan,
    Context: tuple[EdgeRound, list[CornerFrame]],
    Replace: dict[tuple[int, KShapeEdge], ShapeUse],
) -> list[KShapeFace]:
    Round, Frames = Context
    LoopValue = Shape.Faces[PlanValue.CapIndex].Loops[PlanValue.LoopIndex]
    Single = PlanValue.Closed and len(PlanValue.Links) == 1
    Crosses = [] if Single else [CrossEdge(Frame, Round.Rounded) for Frame in Frames]
    Faces: list[KShapeFace] = []
    for Index, LinkValue in enumerate(PlanValue.Links):
        UseValue = LoopValue[LinkValue.UseIndex]
        Closing = Frames[(Index + 1) % len(Frames)]
        Edges = LinkEdges(UseValue, Frames[Index], Closing)
        Replace[(PlanValue.CapIndex, UseValue.Edge)] = ShapeUse(Edges[0], True)
        Replace[(LinkValue.WallIndex, UseValue.Edge)] = ShapeUse(Edges[1], False)
        Surface, Reversed = LinkSurface(UseValue, Frames[Index], Round, PlanValue.Sense)
        Label = FaceLabel(str(PlanValue.Numbers[Index] + 1), (Round.Operation,))
        Loops = BlendLoops(Edges, Crosses, Index)
        Faces.append(FreeFace(Surface, Reversed, Label, Loops))
    return Faces


def ApplyPlan(
    Shape: ShapeBody,
    Users: KUsers,
    PlanValue: RoundPlan,
    Round: EdgeRound,
) -> tuple[ShapeBody, dict[str, float]]:
    Frames = ChainFrames(Shape, PlanValue, Round)
    Swaps: KSwaps = {}
    JointTrimMut(Swaps, Users, PlanValue, Frames)
    EndList = EndTrimMut(Swaps, (Shape, Users, PlanValue), Frames)
    Replace: dict[tuple[int, KShapeEdge], ShapeUse] = {}
    Added = BlendFacesMut(Shape, PlanValue, (Round, Frames), Replace)
    Faces = SwapFaces(Shape.Faces, Swaps, Replace)
    for EndIndex, Frame in EndList:
        Faces[EndIndex] = InsertCross(
            Faces[EndIndex], Frame, CrossEdge(Frame, Round.Rounded)
        )
    Change = PlanMass(Shape, PlanValue, Frames, Round)
    return ReplaceValue(Shape, Faces=(*Faces, *Added)), Change


def ApplyRounds(
    Shape: ShapeBody, Rounds: tuple[EdgeRound, ...]
) -> tuple[ShapeBody, dict[str, float]]:
    Delta = dict.fromkeys((*KMassKeys, "area"), 0.0)
    for Round in Rounds:
        for PlanValue in GroupPlans(Shape, Round.PointsCm):
            Legged = PlanLegs(Shape, PlanValue, Round)
            Shape, Change = ApplyPlan(Shape, ShapeUsers(Shape), PlanValue, Legged)
            for KeyValue, Value in Change.items():
                Delta[KeyValue] += Value
    return Shape, Delta

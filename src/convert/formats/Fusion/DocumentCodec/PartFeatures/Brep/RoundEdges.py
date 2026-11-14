from dataclasses import dataclass as MakeDataClass
from math import acos as ArcCosine

from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.EdgeRound import EdgeRound
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.FreeCurves import (
    ArcEdge,
    EllipseEdge,
    LineEdge,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.FreeEdge import FreeEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.SpaceMath import (
    AddVector,
    CrossProduct,
    DotProduct,
    KSpaceVector,
    ScaleVector,
    SubVector,
    UnitVector,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import ShapeUse
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan


@MakeDataClass(frozen=True, slots=True)
class CornerFrame:
    Point: KSpaceVector
    CapPoint: KSpaceVector
    WallPoint: KSpaceVector
    Middle: KSpaceVector
    Heading: KSpaceVector
    SideAxis: KSpaceVector
    CapAxis: KSpaceVector
    Mitre: bool = False


def FrameAt(
    Point: KSpaceVector,
    AxisSet: tuple[KSpaceVector, KSpaceVector],
    Sense: float,
    Round: EdgeRound,
) -> CornerFrame:
    SideAxis, CapAxis = AxisSet
    CapPoint = SubVector(Point, ScaleVector(SideAxis, Sense * Round.CapCm))
    WallPoint = SubVector(Point, ScaleVector(CapAxis, Sense * Round.WallCm))
    Middle = SubVector(WallPoint, ScaleVector(SideAxis, Sense * Round.CapCm))
    Heading = ScaleVector(CrossProduct(CapAxis, SideAxis), Sense)
    return CornerFrame(Point, CapPoint, WallPoint, Middle, Heading, SideAxis, CapAxis)


def MitreFrame(
    Point: KSpaceVector,
    Sides: tuple[KSpaceVector, KSpaceVector],
    CapAxis: KSpaceVector,
    Context: tuple[float, EdgeRound],
) -> CornerFrame:
    Incoming, Outgoing = Sides
    Sense, Round = Context
    Spread = Sense * Round.CapCm / (1.0 + DotProduct(Incoming, Outgoing))
    CapPoint = SubVector(Point, ScaleVector(AddVector(Incoming, Outgoing), Spread))
    WallPoint = SubVector(Point, ScaleVector(CapAxis, Sense * Round.WallCm))
    Middle = SubVector(CapPoint, ScaleVector(CapAxis, Sense * Round.WallCm))
    Heading = ScaleVector(CrossProduct(CapAxis, Outgoing), Sense)
    return CornerFrame(
        Point, CapPoint, WallPoint, Middle, Heading, Outgoing, CapAxis, True
    )


def CrossEdge(Frame: CornerFrame, Rounded: bool) -> FreeEdge:
    if not Rounded:
        return LineEdge(Frame.CapPoint, Frame.WallPoint)
    if Frame.Mitre:
        return EllipseEdge(Frame.Middle, Frame.CapPoint, Frame.WallPoint)
    First = SubVector(Frame.CapPoint, Frame.Middle)
    Second = SubVector(Frame.WallPoint, Frame.Middle)
    Normal = UnitVector(CrossProduct(First, Second))
    TurnValue = DotProduct(UnitVector(First), UnitVector(Second))
    Sweep = ArcCosine(max(-1.0, min(1.0, TurnValue)))
    return ArcEdge(Frame.Middle, Normal, Frame.CapPoint, Sweep, Frame.WallPoint)


def ArcSense(SpanValue: ArcSpan, UseValue: ShapeUse) -> float:
    return 1.0 if (SpanValue.SweepAngle > 0) == UseValue.Forward else -1.0


def LinkEdges(
    UseValue: ShapeUse, Opening: CornerFrame, Closing: CornerFrame
) -> tuple[FreeEdge, FreeEdge]:
    EdgeValue = UseValue.Edge
    if not isinstance(EdgeValue, LevelEdge):
        raise ValueError("Fusion edge rounds need horizontal body edges")
    SpanValue = EdgeValue.Span
    if not isinstance(SpanValue, ArcSpan):
        return (
            LineEdge(Opening.CapPoint, Closing.CapPoint),
            LineEdge(Opening.WallPoint, Closing.WallPoint),
        )
    Normal = (0.0, 0.0, ArcSense(SpanValue, UseValue))
    Sweep = abs(SpanValue.SweepAngle)
    Edges: list[FreeEdge] = []
    for Start, Finish in (
        (Opening.CapPoint, Closing.CapPoint),
        (Opening.WallPoint, Closing.WallPoint),
    ):
        Center = (SpanValue.CenterCm[0], SpanValue.CenterCm[1], Start[2])
        Edges.append(ArcEdge(Center, Normal, Start, Sweep, Finish))
    return Edges[0], Edges[1]


def ChamferNormal(Frame: CornerFrame, Round: EdgeRound) -> KSpaceVector:
    return UnitVector(
        AddVector(
            ScaleVector(Frame.SideAxis, Round.WallCm),
            ScaleVector(Frame.CapAxis, Round.CapCm),
        )
    )

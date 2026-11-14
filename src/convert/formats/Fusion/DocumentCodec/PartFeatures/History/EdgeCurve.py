from math import cos as Cosine, hypot as Hypotenuse, pi as KPiValue, sin as SineOf

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Geometry.StraightNode import StraightNode
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.FreeEdge import FreeEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import KShapeEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    IsFullCircle,
    SpanFinish,
    SpanLength,
    SpanStart,
)

KSpacePoint = tuple[float, float, float]


def EdgeEnds(EdgeValue: KShapeEdge) -> tuple[KSpacePoint, KSpacePoint]:
    if isinstance(EdgeValue, FreeEdge):
        return EdgeValue.StartCm, EdgeValue.FinishCm
    if isinstance(EdgeValue, LevelEdge):
        Start, Finish = SpanStart(EdgeValue.Span), SpanFinish(EdgeValue.Span)
        if IsFullCircle(EdgeValue.Span):
            Finish = Start
        return (*Start, EdgeValue.LevelCm), (*Finish, EdgeValue.LevelCm)
    Summit = EdgeValue.TopCm or EdgeValue.PointCm
    return (*EdgeValue.PointCm, EdgeValue.LowerCm), (*Summit, EdgeValue.UpperCm)


def SpaceLength(Start: KSpacePoint, Finish: KSpacePoint) -> float:
    return Hypotenuse(Finish[0] - Start[0], Finish[1] - Start[1], Finish[2] - Start[2])


def EdgeCurve(EdgeValue: KShapeEdge) -> tuple[StraightNode | EllipseNode, float, float]:
    if isinstance(EdgeValue, FreeEdge):
        return EdgeValue.Curve, EdgeValue.LowerParam, EdgeValue.UpperParam
    Prefix = EntityPrefix(-1, -1)
    Start, Finish = EdgeEnds(EdgeValue)
    if not isinstance(EdgeValue, LevelEdge):
        Reach = SpaceLength(Start, Finish)
        Heading = tuple(
            (Finish[AxisValue] - Start[AxisValue]) / Reach for AxisValue in range(3)
        )
        Direction = (Heading[0], Heading[1], Heading[2])
        return StraightNode(Prefix, Start, Direction, 0.0, Reach), 0.0, Reach
    SpanValue = EdgeValue.Span
    Length = SpanLength(SpanValue)
    if isinstance(SpanValue, LineSpan):
        Heading = tuple(
            (Finish[AxisValue] - Start[AxisValue]) / Length for AxisValue in range(3)
        )
        return (
            StraightNode(
                Prefix, Start, (Heading[0], Heading[1], Heading[2]), 0.0, Length
            ),
            0.0,
            Length,
        )
    Sense = 1.0 if SpanValue.SweepAngle > 0 else -1.0
    Middle = SpanValue.StartAngle + SpanValue.SweepAngle / 2.0
    HalfValue = abs(SpanValue.SweepAngle) / 2.0
    if IsFullCircle(SpanValue):
        Middle, HalfValue = SpanValue.StartAngle + KPiValue, KPiValue
    Major = (
        SpanValue.RadiusCm * Cosine(Middle),
        SpanValue.RadiusCm * SineOf(Middle),
        0.0,
    )
    Center = (SpanValue.CenterCm[0], SpanValue.CenterCm[1], EdgeValue.LevelCm)
    Curve = EllipseNode(Prefix, Center, (0.0, 0.0, Sense), Major, 1.0, None, None)
    return Curve, -HalfValue, HalfValue

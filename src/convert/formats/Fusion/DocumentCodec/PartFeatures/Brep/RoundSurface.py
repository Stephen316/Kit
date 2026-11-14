from math import (
    atan2 as ArcTangent,
    cos as Cosine,
    hypot as Hypotenuse,
    pi as KHalfTurn,
    sin as SineOf,
)

from convert.formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.formats.Fusion.BrepCodec.Journal.Round.TorusNode import TorusNode
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.EdgeRound import EdgeRound
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.FreeFace import (
    KFreeSurface,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.RoundEdges import (
    ArcSense,
    ChamferNormal,
    CornerFrame,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.SpaceMath import (
    AddVector,
    KSpaceVector,
    ScaleVector,
    SubVector,
    UnitVector,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import ShapeUse
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.ArcSpan import ArcSpan
from convert.formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    IsFullCircle,
)

KUpward = (0.0, 0.0, 1.0)


def MiddleAxis(
    SpanValue: ArcSpan, UseValue: ShapeUse, Point: KSpaceVector
) -> KSpaceVector:
    Opening = ArcTangent(
        Point[1] - SpanValue.CenterCm[1], Point[0] - SpanValue.CenterCm[0]
    )
    Angle = Opening + ArcSense(SpanValue, UseValue) * abs(SpanValue.SweepAngle) / 2.0
    if IsFullCircle(SpanValue):
        Angle = Opening + KHalfTurn
    return (Cosine(Angle) + 0.0, SineOf(Angle) + 0.0, 0.0)


def LineSurface(Frame: CornerFrame, Round: EdgeRound, Sense: float) -> KFreeSurface:
    Prefix = EntityPrefix(-1, -1)
    if not Round.Rounded:
        Normal = ChamferNormal(Frame, Round)
        return PlaneNode(
            Prefix, Frame.CapPoint, Normal, Frame.Heading, False, None, None, None, None
        )
    Radius = Round.CapCm
    Offset = SubVector(Frame.Point, Frame.Middle)
    if Frame.Mitre:
        Offset = ScaleVector(AddVector(Frame.SideAxis, Frame.CapAxis), Sense)
    Major = ScaleVector(UnitVector(Offset), Radius)
    return ConeNode(
        Prefix,
        Frame.Middle,
        Frame.Heading,
        Major,
        1.0,
        None,
        None,
        0.0,
        1.0,
        Radius,
        False,
        None,
        None,
        None,
        None,
    )


def RingCone(SpanValue: ArcSpan, Frame: CornerFrame, Middle: KSpaceVector) -> ConeNode:
    Center = SpanValue.CenterCm
    Points = sorted((Frame.CapPoint, Frame.WallPoint), key=lambda Value: Value[2])
    Radii = [Hypotenuse(Value[0] - Center[0], Value[1] - Center[1]) for Value in Points]
    Slope = ArcTangent(Radii[1] - Radii[0], Points[1][2] - Points[0][2])
    return ConeNode(
        EntityPrefix(-1, -1),
        (Center[0], Center[1], Points[0][2]),
        KUpward,
        ScaleVector(Middle, Radii[0]),
        1.0,
        None,
        None,
        SineOf(Slope),
        Cosine(Slope),
        Radii[0],
        False,
        None,
        None,
        None,
        None,
    )


def RingSurface(
    UseValue: ShapeUse, Frame: CornerFrame, Round: EdgeRound
) -> KFreeSurface:
    EdgeValue = UseValue.Edge
    if not isinstance(EdgeValue, LevelEdge) or not isinstance(EdgeValue.Span, ArcSpan):
        raise ValueError("Fusion edge round rings need circular edges")
    SpanValue = EdgeValue.Span
    Middle = MiddleAxis(SpanValue, UseValue, Frame.Point)
    if not Round.Rounded:
        return RingCone(SpanValue, Frame, Middle)
    Center = SpanValue.CenterCm
    Major = Hypotenuse(Frame.Middle[0] - Center[0], Frame.Middle[1] - Center[1])
    if Major <= Round.CapCm:
        raise ValueError("Fusion edge round radius is too large for this circle")
    return TorusNode(
        EntityPrefix(-1, -1),
        (Center[0], Center[1], Frame.Middle[2]),
        KUpward,
        Major,
        Round.CapCm,
        Middle,
        False,
        None,
        None,
        None,
        None,
    )


def LinkSurface(
    UseValue: ShapeUse, Frame: CornerFrame, Round: EdgeRound, Sense: float
) -> tuple[KFreeSurface, bool]:
    EdgeValue = UseValue.Edge
    if isinstance(EdgeValue, LevelEdge) and isinstance(EdgeValue.Span, ArcSpan):
        Surface = RingSurface(UseValue, Frame, Round)
        if Round.Rounded:
            return Surface, Sense < 0
        return Surface, EdgeValue.Span.SweepAngle < 0
    return LineSurface(Frame, Round, Sense), Round.Rounded and Sense < 0

from convert.Formats.Fusion.DocumentCodec.PartFeatures.Brep.SpaceMath import (
    KSpaceTolerance,
    KSpaceVector,
    ScaleVector,
    UnitVector,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.History.EdgeCurve import (
    EdgeEnds,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.CapFace import CapFace
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import ShapeBody
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import (
    KShapeEdge,
    ShapeUse,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.WallFace import WallFace
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    SpanHeading,
)


# the side normal contract needs a shared interpretation so edge and face relationships survive parametric feature construction
def SideNormal(WallValue: WallFace, PointCm: KSpaceVector) -> KSpaceVector:
    SpanValue = WallValue.Span
    if isinstance(SpanValue, LineSpan):
        HeadX, HeadY = SpanHeading(SpanValue, False)
        return (HeadY, 0.0 - HeadX, 0.0)
    Radial = UnitVector(
        (PointCm[0] - SpanValue.CenterCm[0], PointCm[1] - SpanValue.CenterCm[1], 0.0)
    )
    return Radial if SpanValue.SweepAngle > 0 else ScaleVector(Radial, -1.0)


# the cap normal contract needs a shared interpretation so edge and face relationships survive parametric feature construction
def CapNormal(CapValue: CapFace) -> KSpaceVector:
    return (0.0, 0.0, 1.0 if CapValue.Upward else -1.0)


# the use ends contract needs a shared interpretation so edge and face relationships survive parametric feature construction
def UseEnds(UseValue: ShapeUse) -> tuple[KSpaceVector, KSpaceVector]:
    Start, Finish = EdgeEnds(UseValue.Edge)
    return (Start, Finish) if UseValue.Forward else (Finish, Start)


# wall of needs an explicit validity boundary so edge and face relationships survive parametric feature construction
def WallOf(
    Shape: ShapeBody,
    Users: dict[KShapeEdge, list[tuple[int, int, int]]],
    EdgeValue: KShapeEdge,
    CapIndex: int,
) -> int:
    Places = [Place[0] for Place in Users[EdgeValue] if Place[0] != CapIndex]
    if len(Places) != 1:
        raise ValueError("Fusion edge rounds need edges between two faces")
    WallValue = Shape.Faces[Places[0]]
    if not isinstance(WallValue, WallFace) or WallValue.RoofSpan is not None:
        raise ValueError("Fusion edge rounds need vertical side faces")
    return Places[0]


# edge sense needs an explicit validity boundary so edge and face relationships survive parametric feature construction
def EdgeSense(CapValue: CapFace, WallValue: WallFace) -> float:
    AtTop = abs(WallValue.UpperCm - CapValue.LevelCm) < KSpaceTolerance
    Bottom = abs(WallValue.LowerCm - CapValue.LevelCm) < KSpaceTolerance
    if not AtTop and not Bottom:
        raise ValueError("Fusion edge rounds need side faces that meet the cap")
    return 1.0 if AtTop == CapValue.Upward else -1.0

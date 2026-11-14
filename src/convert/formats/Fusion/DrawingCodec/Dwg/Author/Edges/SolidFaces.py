from math import tan as Tangent

from interchange.brep.surfaces.BrepSurfaces import (
    BrepSurface,
    ConeSurface,
    CylinderSurface,
    PlaneSurface,
)
from interchange.geometry.models.VectorSpace import SpaceVector

from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.EdgeVectors import (
    KFullTurn,
    Length,
    Minus,
    TurnAngle,
    UnitVector,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.PathPoints import (
    IsWhole,
    RoundPoint,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Edges.SolidParts import (
    FlatArc,
    FlatFace,
    FlatLine,
    KEdgePath,
    KPointPair,
    KPointTriple,
    LinePath,
    RingBound,
    RoundFace,
    RoundPath,
    SeamBound,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Views.ViewFrame import (
    Cross,
    DotProduct,
    Scaled,
)

KLinkGap = 1e-6
KFrame = tuple[KPointTriple, KPointTriple, KPointTriple, KPointTriple]


def PointOf(Value: SpaceVector) -> KPointTriple:
    return (Value.x, Value.y, Value.z)


def MakeFrame(
    Origin: SpaceVector, Normal: SpaceVector, Reference: SpaceVector
) -> KFrame:
    Along = UnitVector(PointOf(Normal))
    Toward = PointOf(Reference)
    XAxis = UnitVector(Minus(Toward, Scaled(Along, DotProduct(Toward, Along))))
    return (PointOf(Origin), Along, XAxis, Cross(Along, XAxis))


def FlatPoint(Frame: KFrame, Point: KPointTriple) -> KPointPair:
    Offset = Minus(Point, Frame[0])
    return (DotProduct(Offset, Frame[2]), DotProduct(Offset, Frame[3]))


def FlatBound(Frame: KFrame, Curve: KEdgePath) -> FlatLine | FlatArc:
    Checked = (
        (Curve.Start, Curve.Finish) if isinstance(Curve, LinePath) else (Curve.Center,)
    )
    if any(
        abs(DotProduct(Minus(Point, Frame[0]), Frame[1])) > KLinkGap
        for Point in Checked
    ):
        raise ValueError("Authored DWG view face edge leaves its plane")
    if isinstance(Curve, LinePath):
        return FlatLine(FlatPoint(Frame, Curve.Start), FlatPoint(Frame, Curve.Finish))
    if Length(Cross(Curve.Normal, Frame[1])) > KLinkGap:
        raise ValueError("Authored DWG view face arc leaves its plane")
    Center = FlatPoint(Frame, Curve.Center)
    if IsWhole(Curve):
        return FlatArc(Center, Curve.Radius, 0.0, KFullTurn)
    Opening = TurnAngle(
        Minus(RoundPoint(Curve, Curve.Opening), Curve.Center), Frame[2], Frame[3]
    )
    if DotProduct(Curve.Normal, Frame[1]) < 0:
        Opening = (Opening - Curve.Sweep) % KFullTurn
    return FlatArc(Center, Curve.Radius, Opening, Curve.Sweep)


def RingOf(Frame: KFrame, Curve: RoundPath) -> tuple[RingBound, float]:
    Offset = Minus(Curve.Center, Frame[0])
    Height = DotProduct(Offset, Frame[1])
    if (
        Length(Minus(Offset, Scaled(Frame[1], Height))) > KLinkGap
        or Length(Cross(Curve.Normal, Frame[1])) > KLinkGap
    ):
        raise ValueError("Authored DWG view round face arc is not coaxial")
    if IsWhole(Curve):
        return RingBound(Height, 0.0, KFullTurn), Curve.Radius
    Opening = TurnAngle(
        Minus(RoundPoint(Curve, Curve.Opening), Curve.Center), Frame[2], Frame[3]
    )
    if DotProduct(Curve.Normal, Frame[1]) < 0:
        Opening = (Opening - Curve.Sweep) % KFullTurn
    return RingBound(Height, Opening, Curve.Sweep), Curve.Radius


def SeamOf(Frame: KFrame, Curve: LinePath) -> SeamBound:
    Heights: list[float] = []
    Angles: list[float] = []
    for Point in (Curve.Start, Curve.Finish):
        Offset = Minus(Point, Frame[0])
        Height = DotProduct(Offset, Frame[1])
        Heights.append(Height)
        if Length(Minus(Offset, Scaled(Frame[1], Height))) > KLinkGap:
            Angles.append(TurnAngle(Offset, Frame[2], Frame[3]))
    Spread = max(Angles) - min(Angles) if Angles else 0.0
    if not Angles or min(Spread, KFullTurn - Spread) > KLinkGap:
        raise ValueError("Authored DWG view round face line is not a generator")
    return SeamBound(Angles[0], min(Heights), max(Heights))


def PickSlope(
    Choices: tuple[float, ...], Radius: float, Rings: list[tuple[RingBound, float]]
) -> float:
    Fitting = [
        Slope
        for Slope in Choices
        if all(
            abs(Radius + Slope * Bound.Height - Measured) <= KLinkGap
            for Bound, Measured in Rings
        )
    ]
    if len(set(Fitting)) != 1:
        raise ValueError("Authored DWG view round face does not fit its arcs")
    return Fitting[0]


def MakeRound(
    FaceIndex: int,
    Surface: CylinderSurface | ConeSurface,
    Bounds: tuple[KEdgePath, ...],
) -> RoundFace:
    Frame = MakeFrame(Surface.origin, Surface.axis, Surface.reference_direction)
    Rings = [RingOf(Frame, Curve) for Curve in Bounds if isinstance(Curve, RoundPath)]
    Seams = [SeamOf(Frame, Curve) for Curve in Bounds if isinstance(Curve, LinePath)]
    Choices: tuple[float, ...] = (0.0,)
    if isinstance(Surface, ConeSurface):
        Choices = (Tangent(Surface.half_angle), -Tangent(Surface.half_angle))
    Slope = PickSlope(Choices, Surface.radius, Rings)
    return RoundFace(
        FaceIndex,
        *Frame,
        Surface.radius,
        Slope,
        tuple(Bound for Bound, _ in Rings),
        tuple(Seams),
    )


def MakeFace(
    FaceIndex: int, Surface: BrepSurface, Bounds: tuple[KEdgePath, ...]
) -> FlatFace | RoundFace:
    if isinstance(Surface, PlaneSurface):
        Frame = MakeFrame(Surface.origin, Surface.normal, Surface.reference_direction)
        return FlatFace(*Frame, tuple(FlatBound(Frame, Curve) for Curve in Bounds))
    if isinstance(Surface, (CylinderSurface, ConeSurface)):
        return MakeRound(FaceIndex, Surface, Bounds)
    raise ValueError(
        f"Authored DWG view edges do not cover {type(Surface).__name__} faces"
    )

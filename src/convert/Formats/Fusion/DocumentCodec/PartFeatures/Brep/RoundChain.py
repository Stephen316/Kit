from dataclasses import dataclass as MakeDataClass
from math import atan2 as ArcTangent, hypot as Hypotenuse, pi as KHalfTurn

from convert.Formats.Fusion.DocumentCodec.PartFeatures.Brep.SpaceMath import (
    KSpaceTolerance,
    KSpaceVector,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.LevelEdge import LevelEdge
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeBody import ShapeBody
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.ShapeUse import (
    KShapeEdge,
    ShapeUse,
)
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Shape.CapFace import CapFace
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.LineSpan import LineSpan
from convert.Formats.Fusion.DocumentCodec.PartFeatures.Solid.SpanMath import (
    IsFullCircle,
)

# the use place shape must stay shared so feature geometry uses one contract for compatible values
KUsePlace = tuple[int, int, int]


# chain seed needs an explicit state contract so edge and face relationships survive parametric feature construction
@MakeDataClass(frozen=True, slots=True)
class ChainSeed:
    CapIndex: int
    LoopIndex: int
    UseIndex: int


# the shape users contract needs a shared interpretation so edge and face relationships survive parametric feature construction
def ShapeUsers(Shape: ShapeBody) -> dict[KShapeEdge, list[KUsePlace]]:
    Users: dict[KShapeEdge, list[KUsePlace]] = {}
    for FaceIndex, FaceValue in enumerate(Shape.Faces):
        for LoopIndex, LoopValue in enumerate(FaceValue.Loops):
            for UseIndex, UseValue in enumerate(LoopValue):
                Place = (FaceIndex, LoopIndex, UseIndex)
                Users.setdefault(UseValue.Edge, []).append(Place)
    return Users


# the on line decision must stay consistent so edge and face relationships survive parametric feature construction
def IsOnLine(SpanValue: LineSpan, PointCm: tuple[float, float]) -> bool:
    DeltaX = SpanValue.FinishCm[0] - SpanValue.StartCm[0]
    DeltaY = SpanValue.FinishCm[1] - SpanValue.StartCm[1]
    Length = Hypotenuse(DeltaX, DeltaY)
    OffsetX, OffsetY = (
        PointCm[0] - SpanValue.StartCm[0],
        PointCm[1] - SpanValue.StartCm[1],
    )
    Along = (OffsetX * DeltaX + OffsetY * DeltaY) / Length
    Across = (OffsetY * DeltaX - OffsetX * DeltaY) / Length
    return abs(Across) < KSpaceTolerance and -KSpaceTolerance < Along < Length + 1e-7


# the on level decision must stay consistent so edge and face relationships survive parametric feature construction
def IsOnLevel(EdgeValue: KShapeEdge, PointCm: KSpaceVector) -> bool:
    if not isinstance(EdgeValue, LevelEdge):
        return False
    if abs(EdgeValue.LevelCm - PointCm[2]) > KSpaceTolerance:
        return False
    SpanValue, FlatPoint = EdgeValue.Span, (PointCm[0], PointCm[1])
    if isinstance(SpanValue, LineSpan):
        return IsOnLine(SpanValue, FlatPoint)
    OffsetX, OffsetY = (
        FlatPoint[0] - SpanValue.CenterCm[0],
        FlatPoint[1] - SpanValue.CenterCm[1],
    )
    if abs(Hypotenuse(OffsetX, OffsetY) - SpanValue.RadiusCm) > KSpaceTolerance:
        return False
    if IsFullCircle(SpanValue):
        return True
    TurnValue = (ArcTangent(OffsetY, OffsetX) - SpanValue.StartAngle) * (
        1.0 if SpanValue.SweepAngle > 0 else -1.0
    )
    TurnValue = TurnValue % (2.0 * KHalfTurn)
    return (
        TurnValue <= abs(SpanValue.SweepAngle) + 1e-9
        or TurnValue >= 2.0 * KHalfTurn - 1e-9
    )


# find seed must resolve unambiguously so edge and face relationships survive parametric feature construction
def FindSeed(Shape: ShapeBody, PointCm: KSpaceVector) -> ChainSeed:
    for FaceIndex, FaceValue in enumerate(Shape.Faces):
        if not isinstance(FaceValue, CapFace):
            continue
        for LoopIndex, LoopValue in enumerate(FaceValue.Loops):
            for UseIndex, UseValue in enumerate(LoopValue):
                if IsOnLevel(UseValue.Edge, PointCm):
                    return ChainSeed(FaceIndex, LoopIndex, UseIndex)
    raise ValueError("Fusion edge rounds need a point on a horizontal body edge")


# the seed uses contract needs a shared interpretation so edge and face relationships survive parametric feature construction
def SeedUses(Shape: ShapeBody, SeedValue: ChainSeed) -> tuple[ShapeUse, ...]:
    return Shape.Faces[SeedValue.CapIndex].Loops[SeedValue.LoopIndex]

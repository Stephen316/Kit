from math import hypot as Hypot, sqrt as SquareRoot

from convert.geometry.Extrude.Polygon.RingPredicates import RingTurn, ToRingGrid
from convert.geometry.Extrude.Trimmed.TrimAngles import IsOnTrimArc
from convert.geometry.Extrude.Trimmed.TrimOperand import TrimOperand
from interchange.geometry.models.GeometryCurves import ArcGeometry
from interchange.geometry.models.VectorPlane import PlaneVector


# exact discriminant signs retain tangent contacts without tolerance based root guessing
def GetArcLineHits(
    ArcValue: ArcGeometry, LineValue: TrimOperand, Tolerance: float
) -> tuple[PlaneVector, ...]:
    (Start, Finish, Center, RadiusPoint), _ = ToRingGrid(
        (
            LineValue.Start,
            LineValue.Finish,
            ArcValue.center,
            PlaneVector(ArcValue.radius, 0.0),
        )
    )
    LineDelta = (Finish[0] - Start[0], Finish[1] - Start[1])
    Shift = (Center[0] - Start[0], Center[1] - Start[1])
    Magnitude = LineDelta[0] ** 2 + LineDelta[1] ** 2
    RadiusSquared = RadiusPoint[0] ** 2
    SquareSpan = RadiusSquared * Magnitude
    Discriminant = SquareSpan - RingTurn((0, 0), LineDelta, Shift) ** 2
    if Discriminant < 0:
        return ()
    Axial = (LineDelta[0] * Shift[0] + LineDelta[1] * Shift[1]) / Magnitude
    DeltaX = LineValue.Finish.x - LineValue.Start.x
    DeltaY = LineValue.Finish.y - LineValue.Start.y
    Length = Hypot(DeltaX, DeltaY)
    Spread = SquareRoot(Discriminant / SquareSpan) * ArcValue.radius / Length
    Margin = Tolerance / Length
    Points = (
        PlaneVector(
            LineValue.Start.x + Ratio * DeltaX, LineValue.Start.y + Ratio * DeltaY
        )
        for Ratio in (Axial - Spread, Axial + Spread)
        if -Margin <= Ratio <= 1.0 + Margin
    )
    return tuple(Point for Point in Points if IsOnTrimArc(ArcValue, Point, Tolerance))

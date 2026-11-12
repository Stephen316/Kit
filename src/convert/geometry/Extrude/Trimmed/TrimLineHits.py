from convert.geometry.Extrude.Polygon.RingPredicates import (
    HasCrossing,
    IsOnSegment,
    RingTurn,
    ToRingGrid,
)
from convert.geometry.Extrude.Trimmed.TrimOperand import TrimOperand
from interchange.geometry.models.VectorPlane import PlaneVector


# binary rational predicates distinguish exact straight intersections from nearby extensions
def GetLineHits(First: TrimOperand, Second: TrimOperand) -> tuple[PlaneVector, ...]:
    Points = (First.Start, First.Finish, Second.Start, Second.Finish)
    (Start, Finish, Other, Final), _ = ToRingGrid(Points)
    if not HasCrossing(Start, Finish, Other, Final):
        return ()
    FirstDelta = (Finish[0] - Start[0], Finish[1] - Start[1])
    SecondDelta = (Final[0] - Other[0], Final[1] - Other[1])
    Denominator = RingTurn((0, 0), FirstDelta, SecondDelta)
    if Denominator:
        Shift = (Other[0] - Start[0], Other[1] - Start[1])
        Fraction = RingTurn((0, 0), Shift, SecondDelta) / Denominator
        return (
            PlaneVector(
                First.Start.x + Fraction * (First.Finish.x - First.Start.x),
                First.Start.y + Fraction * (First.Finish.y - First.Start.y),
            ),
        )
    AxisIndex = 0 if FirstDelta[0] else 1
    LowerA, UpperA = sorted((Start[AxisIndex], Finish[AxisIndex]))
    LowerB, UpperB = sorted((Other[AxisIndex], Final[AxisIndex]))
    if min(UpperA, UpperB) > max(LowerA, LowerB):
        raise ValueError("Extrude trim has overlapping collinear lines")
    return tuple(
        Point
        for Point, GridPointValue in zip(Points[:2], (Start, Finish))
        if IsOnSegment(Other, Final, GridPointValue)
    )

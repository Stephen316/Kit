# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import fsum as SumFloats, hypot as Hypot, isfinite as IsFinite

from convert.geometry.Extrude.Polygon.RingPredicates import (
    KGridPoint,
    HasCrossing,
    RingTurn,
    ToRingGrid,
)
from interchange.brep.topology.BrepMath import IsFinitePlane
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.VectorPlane import PlaneVector


# traversal preserves the source endpoint coordinates while accepting reversed line directions
def ReadPrismRing(Profile: tuple[LineGeometry, ...]) -> tuple[PlaneVector, ...]:
    if not 3 <= len(Profile) <= 64:
        raise ValueError("Extrude prism requires three to sixty four profile sides")
    if any(
        not IsFinitePlane(LineValue.start)
        or not IsFinitePlane(LineValue.end)
        or LineValue.start == LineValue.end
        for LineValue in Profile
    ):
        raise ValueError("Extrude prism requires finite nonzero profile sides")
    First = Profile[0]
    Points = [First.start, First.end]
    for LineValue in Profile[1:]:
        if LineValue.start == Points[-1]:
            Points.append(LineValue.end)
        elif LineValue.end == Points[-1]:
            Points.append(LineValue.start)
        else:
            raise ValueError("Extrude prism profile does not connect in source order")
    if Points.pop() != Points[0]:
        raise ValueError("Extrude prism profile does not close")
    if len({(PointValue.x, PointValue.y) for PointValue in Points}) != len(Points):
        raise ValueError("Extrude prism profile repeats a vertex")
    return tuple(Points)


# exact simplicity checks prevent intersecting cap loops and duplicate planar side carriers
def CheckSimpleRing(Points: tuple[KGridPoint, ...]) -> None:
    Count = len(Points)
    for Index, First in enumerate(Points):
        Following = (Index + 1) % Count
        Second = Points[Following]
        if RingTurn(Points[Index - 1], First, Second) == 0:
            raise ValueError("Extrude prism profile has adjacent collinear sides")
        for Other in range(Index + 2, Count):
            if Index == 0 and Other == Count - 1:
                continue
            if HasCrossing(First, Second, Points[Other], Points[(Other + 1) % Count]):
                raise ValueError("Extrude prism profile intersects itself")


# exact signed area and stable lengths supply analytic measures for either winding
def MeasureRing(
    Points: tuple[PlaneVector, ...],
) -> tuple[tuple[PlaneVector, ...], float, float]:
    RingGrid, Scale = ToRingGrid(Points)
    CheckSimpleRing(RingGrid)
    TwiceArea = sum(
        RingTurn(RingGrid[0], RingGrid[Index - 1], RingGrid[Index])
        for Index in range(2, len(RingGrid))
    )
    try:
        PlanarArea = abs(TwiceArea) / (2 * Scale**2)
        Perimeter = SumFloats(
            Hypot(First.x - Second.x, First.y - Second.y)
            for First, Second in zip(Points, Points[1:] + Points[:1])
        )
    except OverflowError as ErrorInfo:
        raise ValueError(
            "Extrude prism profile measures exceed floating range"
        ) from ErrorInfo
    if not (
        IsFinite(PlanarArea)
        and PlanarArea > 0
        and IsFinite(Perimeter)
        and Perimeter > 0
    ):
        raise ValueError("Extrude prism requires positive finite profile measures")
    Oriented = Points if TwiceArea > 0 else Points[:1] + Points[:0:-1]
    return Oriented, PlanarArea, Perimeter

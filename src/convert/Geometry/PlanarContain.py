from itertools import combinations as Pairs, pairwise as Adjacent
from math import hypot as Hypot, isfinite as IsFinite

from convert.Geometry.Extrude.Polygon.PrismRing import CheckSimpleRing
from convert.Geometry.Extrude.Polygon.RingPredicates import (
    HasCrossing,
    KGridPoint,
    RingTurn,
    ToRingGrid,
)
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.Topology.BrepMath import IsFiniteSpace
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector

# the proof must bound its pairwise work even for large native payloads
KRingPointLimit = 128

# the geometric fallback leaves materially nonplanar boundaries outside this proof
KPlaneTolerance = 1e-7


# dropping the dominant normal coordinate preserves containment on the entire plane
def ProjectRings(
    Rings: tuple[tuple[SpaceVector, ...], ...], Plane: PlaneSurface
) -> tuple[tuple[PlaneVector, ...], ...] | None:
    Normal = (Plane.normal.x, Plane.normal.y, Plane.normal.z)
    Length = Hypot(*Normal)
    if not IsFinite(Length) or Length == 0 or not IsFiniteSpace(Plane.origin):
        return None
    Magnitudes = tuple(abs(Value) for Value in Normal)
    DropAxis = Magnitudes.index(max(Magnitudes))
    FirstAxis, OtherAxis = (Index for Index in range(3) if Index != DropAxis)
    UnitNormal = tuple(Value / Length for Value in Normal)
    Origin = (Plane.origin.x, Plane.origin.y, Plane.origin.z)
    Projected: list[tuple[PlaneVector, ...]] = []
    for RingValue in Rings:
        Points: list[PlaneVector] = []
        for Point in RingValue:
            if not IsFiniteSpace(Point):
                return None
            Coordinates = (Point.x, Point.y, Point.z)
            Distance = sum(
                (Value - BaseValue) * Weight
                for Value, BaseValue, Weight in zip(Coordinates, Origin, UnitNormal)
            )
            if not abs(Distance) <= KPlaneTolerance:
                return None
            Points.append(PlaneVector(Coordinates[FirstAxis], Coordinates[OtherAxis]))
        Projected.append(tuple(Points))
    return tuple(Projected)


# all boundaries need one exact grid so cross ring comparisons share a scale
def ReadRingGrid(
    Rings: tuple[tuple[PlaneVector, ...], ...],
) -> tuple[tuple[KGridPoint, ...], ...] | None:
    GridPoints, _ = ToRingGrid(
        tuple(Point for RingValue in Rings for Point in RingValue)
    )
    Result: list[tuple[KGridPoint, ...]] = []
    Cursor = 0
    for RingValue in Rings:
        Boundary = GridPoints[Cursor : Cursor + len(RingValue)]
        Cursor += len(RingValue)
        if len(set(Boundary)) != len(Boundary):
            return None
        try:
            CheckSimpleRing(Boundary)
        except ValueError:
            return None
        Result.append(Boundary)
    return tuple(Result)


# after contact is excluded winding distinguishes an enclosed point on either orientation
def IsInsideRing(Point: KGridPoint, RingValue: tuple[KGridPoint, ...]) -> bool:
    Winding = 0
    for First, Second in Adjacent((*RingValue, RingValue[0])):
        TurnValue = RingTurn(First, Second, Point)
        if First[1] <= Point[1] < Second[1] and TurnValue > 0:
            Winding += 1
        elif Second[1] <= Point[1] < First[1] and TurnValue < 0:
            Winding -= 1
    return Winding != 0


# a single material boundary must enclose every disjoint hole without touching it
def FindRingHost(GridRings: tuple[tuple[KGridPoint, ...], ...]) -> int | None:
    Hosts: list[list[int]] = [[] for _ in GridRings]
    for (FirstId, FirstRing), (OtherId, OtherRing) in Pairs(enumerate(GridRings), 2):
        if any(
            HasCrossing(First, Second, Third, Fourth)
            for First, Second in Adjacent((*FirstRing, FirstRing[0]))
            for Third, Fourth in Adjacent((*OtherRing, OtherRing[0]))
        ):
            return None
        if IsInsideRing(FirstRing[0], OtherRing):
            Hosts[FirstId].append(OtherId)
        elif IsInsideRing(OtherRing[0], FirstRing):
            Hosts[OtherId].append(FirstId)
    Outside = [Index for Index, Parents in enumerate(Hosts) if not Parents]
    if len(Outside) != 1:
        return None
    (OuterIndex,) = Outside
    if any(Parents != [OuterIndex] for Parents in Hosts if Parents):
        return None
    return OuterIndex


# boundary roles can only change when every saved ring participates in one containment proof
def FindPlanarOuter(
    Rings: tuple[tuple[SpaceVector, ...], ...], Plane: PlaneSurface
) -> int | None:
    if (
        len(Rings) < 2
        or any(len(RingValue) < 3 for RingValue in Rings)
        or sum(map(len, Rings)) > KRingPointLimit
    ):
        return None
    Projected = ProjectRings(Rings, Plane)
    GridRings = ReadRingGrid(Projected) if Projected is not None else None
    return FindRingHost(GridRings) if GridRings is not None else None

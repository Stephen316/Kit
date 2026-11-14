from fractions import Fraction
from typing import Mapping as KMapping

from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import (
    CageGraph,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CappedShape import (
    CappedShape,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleKnots import (
    KCellAdds,
    KCornerSteps,
    KEndCount,
    KKnotMap,
    RegionKnots,
    BaseKnots,
    CornerPoint,
    FacePoint,
    CornerKnots,
    IsAlongU,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineKnot import SplineKnot

KSideUse = tuple[int, PatchCell, int, bool]
KSpokeHit = tuple[int, int, bool, Fraction]


def CellOwners(Shape: CappedShape) -> dict[int, tuple[int, PatchCell]]:
    return {
        CellValue.Face: (Region, CellValue)
        for Region, Cells in enumerate(Shape.Regions)
        for CellValue in Cells
    }


def SideUses(
    Graph: CageGraph, Owners: dict[int, tuple[int, PatchCell]], LinkIndex: int
) -> tuple[KSideUse, KSideUse]:
    Found: list[KSideUse] = []
    for Entry in (LinkIndex, Graph.Links[LinkIndex].Opposite):
        FaceIndex = Graph.Links[Entry].FaceIndex
        Region, CellValue = Owners[FaceIndex]
        Found.append(
            (Region, CellValue, Graph.Loops[FaceIndex].index(Entry), Entry == LinkIndex)
        )
    return Found[0], Found[1]


def CellCross(
    Graph: CageGraph, FaceIndex: int, SideIndex: int, Levels: dict[int, int]
) -> list[Fraction]:
    Found: set[Fraction] = set()
    for Corner, LinkIndex in enumerate(Graph.Loops[FaceIndex]):
        Vertex = Graph.Links[LinkIndex].VertexIndex
        if Vertex not in Levels:
            continue
        Origin = KCornerSteps[Corner][0 if SideIndex in (0, 2) else 1]
        for Value in CornerKnots(Levels[Vertex]):
            if 0 < Value < 1:
                Place = Value if Origin == 0 else 1 - Value
                Found.add(Place if SideIndex in (0, 1) else 1 - Place)
    return sorted(Found)


def SpokeAdds(
    Graph: CageGraph,
    Levels: dict[int, int],
    Target: KSideUse,
    Source: KSideUse,
    Scale: int,
    Reach: Fraction,
) -> list[tuple[int, bool, Fraction]]:
    Found: list[tuple[int, bool, Fraction]] = []
    Region, CellValue, SideIndex, Outward = Target
    for Place in CellCross(Graph, Source[1].Face, Source[2], Levels):
        Distance = Place if Source[3] else 1 - Place
        if Distance > Reach:
            continue
        Along = Distance if Outward else 1 - Distance
        First, Second = KCornerSteps[SideIndex], KCornerSteps[(SideIndex + 1) % 4]
        Point = FacePoint(
            CellValue,
            Scale,
            (1 - Along) * First[0] + Along * Second[0],
            (1 - Along) * First[1] + Along * Second[1],
        )
        AlongU = IsAlongU(CellValue, Scale, SideIndex)
        Found.append((Region, AlongU, Point[0] if AlongU else Point[1]))
    return Found


def SpokeHits(
    Graph: CageGraph, Shape: CappedShape, Scale: int, Levels: dict[int, int]
) -> list[KSpokeHit]:
    Owners = CellOwners(Shape)
    Found: list[KSpokeHit] = []
    for Vertex, Level in Levels.items():
        Reach = Fraction(4, 2 ** (Level + 1))
        for LinkIndex in Graph.Fans[Vertex]:
            SidePair = SideUses(Graph, Owners, LinkIndex)
            for Target, Source in (SidePair, SidePair[::-1]):
                for Region, AlongU, Value in SpokeAdds(
                    Graph, Levels, Target, Source, Scale, Reach
                ):
                    Period = Shape.Periods[Region][0 if AlongU else 1]
                    Placed = Value % Period if Period else Value
                    Found.append((Region, Target[1].Face, AlongU, Placed))
    return Found


def SpokeKnots(
    BaseMaps: list[tuple[KKnotMap, KKnotMap]], HitList: list[KSpokeHit]
) -> list[tuple[KKnotMap, KKnotMap]]:
    Result = [(dict(KnotsU), dict(KnotsV)) for KnotsU, KnotsV in BaseMaps]
    for Region, _, AlongU, Value in HitList:
        _ = Result[Region][0 if AlongU else 1].setdefault(Value, 1)
    return Result


def CellAdds(HitList: list[KSpokeHit], Region: int) -> KCellAdds:
    Found: dict[int, list[tuple[bool, Fraction]]] = {}
    for Owner, FaceIndex, AlongU, Value in HitList:
        if Owner == Region:
            Found.setdefault(FaceIndex, []).append((AlongU, Value))
    return {FaceIndex: tuple(Entries) for FaceIndex, Entries in Found.items()}


def CellRange(
    Cells: tuple[PatchCell, ...], Scale: int, AxisIndex: int
) -> tuple[Fraction, Fraction]:
    Values = [
        CornerPoint(CellValue, Scale, Corner)[AxisIndex]
        for CellValue in Cells
        for Corner in range(4)
    ]
    return (min(Values), max(Values))


def PlanKnots(
    Graph: CageGraph, Shape: CappedShape, Scale: int, Levels: dict[int, int]
) -> tuple[RegionKnots, ...]:
    BaseMaps = [BaseKnots(Graph, Cells, Scale, Levels) for Cells in Shape.Regions]
    HitList = SpokeHits(Graph, Shape, Scale, Levels)
    Final = SpokeKnots(BaseMaps, HitList)
    return tuple(
        RegionKnots(
            Final[Region][0],
            Final[Region][1],
            CellAdds(HitList, Region),
            CellRange(Cells, Scale, 0),
            CellRange(Cells, Scale, 1),
        )
        for Region, Cells in enumerate(Shape.Regions)
    )


def InnerKnots(
    Knots: KMapping[Fraction, int], Bounds: tuple[Fraction, Fraction]
) -> list[tuple[Fraction, int]]:
    return sorted(
        (Value, Count)
        for Value, Count in Knots.items()
        if Bounds[0] < Value < Bounds[1]
    )


def KnotVector(
    Knots: KMapping[Fraction, int], Bounds: tuple[Fraction, Fraction]
) -> tuple[SplineKnot, ...]:
    Inner = [
        SplineKnot(float(Value), Count) for Value, Count in InnerKnots(Knots, Bounds)
    ]
    return (
        (SplineKnot(float(Bounds[0]), KEndCount),)
        + tuple(Inner)
        + (SplineKnot(float(Bounds[1]), KEndCount),)
    )


def FullKnots(
    Knots: KMapping[Fraction, int], Bounds: tuple[Fraction, Fraction]
) -> tuple[Fraction, ...]:
    Found = [Bounds[0]] * (KEndCount + 1)
    for Value, Count in InnerKnots(Knots, Bounds):
        Found += [Value] * Count
    return tuple(Found + [Bounds[1]] * (KEndCount + 1))

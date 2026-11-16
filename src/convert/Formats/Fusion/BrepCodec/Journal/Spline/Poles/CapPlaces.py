from collections import Counter as CountValues
from dataclasses import dataclass as MakeDataClass
from fractions import Fraction
from typing import Mapping as KMapping

from convert.Formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import (
    CageGraph,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Poles.CapHook import (
    KCapKey,
    KSectorKnots,
    SpokeKey,
)
from convert.Formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleKnots import (
    KEndCount,
    RegionKnots,
    BaseKnots,
    CornerPoint,
    MergeMut,
)

# the pole place shape must stay shared so spline pole reconstruction uses one contract for compatible values
KPolePlace = tuple[int, int]

# reach spans must remain consistent across callers so neighboring patches retain consistent subdivision boundaries
KReachSpans = 4

# narrow spans must remain consistent across callers so neighboring patches retain consistent subdivision boundaries
KNarrowSpans = 2


# face plan needs an explicit state contract so neighboring patches retain consistent subdivision boundaries
@MakeDataClass(frozen=True, slots=True)
class FacePlan:
    Region: int
    Cells: tuple[PatchCell, ...]
    Knots: RegionKnots
    FullU: tuple[Fraction, ...]
    FullV: tuple[Fraction, ...]


# corner use needs an explicit state contract so neighboring patches retain consistent subdivision boundaries
@MakeDataClass(frozen=True, slots=True)
class CornerUse:
    FaceIndex: int
    Vertex: int
    Sector: int
    Valence: int
    PointU: Fraction
    PointV: Fraction
    SignU: int
    SignV: int
    AlongI: bool


# the corner uses contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def CornerUses(
    Graph: CageGraph, PlanValue: FacePlan, Scale: int, Levels: KMapping[int, int]
) -> list[CornerUse]:
    Found: list[CornerUse] = []
    for CellValue in PlanValue.Cells:
        for Corner, LinkIndex in enumerate(Graph.Loops[CellValue.Face]):
            Vertex = Graph.Links[LinkIndex].VertexIndex
            if Vertex not in Levels:
                continue
            Point = CornerPoint(CellValue, Scale, Corner)
            Following = CornerPoint(CellValue, Scale, Corner + 1)
            Opposite = CornerPoint(CellValue, Scale, Corner + 2)
            Found.append(
                CornerUse(
                    CellValue.Face,
                    Vertex,
                    Graph.Fans[Vertex].index(LinkIndex),
                    len(Graph.Fans[Vertex]),
                    Point[0],
                    Point[1],
                    1 if Opposite[0] > Point[0] else -1,
                    1 if Opposite[1] > Point[1] else -1,
                    Following[0] != Point[0],
                )
            )
    return Found


# the side index contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def SideIndex(
    KnotList: tuple[Fraction, ...], PoleSpot: int, Value: Fraction, SignValue: int
) -> int:
    Count = KnotList.count(Value)
    Arguments = KnotList[PoleSpot + 1 : PoleSpot + 4]
    if Count == 0 or any(SignValue * (Entry - Value) < 0 for Entry in Arguments):
        return -1
    if SignValue > 0:
        return PoleSpot - KnotList.index(Value) + 4 - Count
    LastSpot = len(KnotList) - 1 - KnotList[::-1].index(Value)
    return LastSpot - PoleSpot - Count


# the arg distances contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def ArgDistances(
    KnotList: tuple[Fraction, ...], PoleSpot: int, Value: Fraction, SignValue: int
) -> list[Fraction]:
    return sorted(
        SignValue * (Entry - Value) for Entry in KnotList[PoleSpot + 1 : PoleSpot + 4]
    )


# the axis indices contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def AxisIndices(
    KnotList: tuple[Fraction, ...], Value: Fraction, SignValue: int, Reach: Fraction
) -> dict[int, int]:
    Found: dict[int, int] = {}
    for PoleSpot in range(len(KnotList) - 4):
        Index = SideIndex(KnotList, PoleSpot, Value, SignValue)
        if (
            Index >= 0
            and ArgDistances(KnotList, PoleSpot, Value, SignValue)[0] <= Reach
        ):
            Found[PoleSpot] = Index
    return Found


# the cap spacing contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def CapSpacing(Scale: int, Level: int) -> Fraction:
    return Scale * Fraction(1, 2 ** (Level + 1))


# the near spots contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def NearSpots(
    KnotList: tuple[Fraction, ...], Value: Fraction, SignValue: int, EdgeReach: Fraction
) -> dict[int, list[Fraction]]:
    Found: dict[int, list[Fraction]] = {}
    for PoleSpot in range(len(KnotList) - 4):
        Distances = ArgDistances(KnotList, PoleSpot, Value, SignValue)
        if 0 <= Distances[0] < EdgeReach:
            Found[PoleSpot] = Distances
    return Found


# the base mask contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def BaseMask(
    BaseLists: tuple[tuple[Fraction, ...], tuple[Fraction, ...]],
    UseList: list[CornerUse],
    Spacing: Fraction,
) -> set[KPolePlace]:
    EdgeReach = KNarrowSpans * Spacing
    Found: set[KPolePlace] = set()
    for CornerInfo in UseList:
        SpotsU = NearSpots(BaseLists[0], CornerInfo.PointU, CornerInfo.SignU, EdgeReach)
        SpotsV = NearSpots(BaseLists[1], CornerInfo.PointV, CornerInfo.SignV, EdgeReach)
        for Column, DistancesU in SpotsU.items():
            for RowIndex, DistancesV in SpotsV.items():
                if DistancesU[1] < EdgeReach or DistancesV[1] < EdgeReach:
                    Found.add((RowIndex, Column))
    return Found


# the corner groups contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def CornerGroups(
    Graph: CageGraph, PlanValue: FacePlan, Scale: int, Levels: KMapping[int, int]
) -> dict[tuple[int, Fraction, Fraction], list[CornerUse]]:
    Found: dict[tuple[int, Fraction, Fraction], list[CornerUse]] = {}
    for CornerInfo in CornerUses(Graph, PlanValue, Scale, Levels):
        GroupKey = (CornerInfo.Vertex, CornerInfo.PointU, CornerInfo.PointV)
        Found.setdefault(GroupKey, []).append(CornerInfo)
    return Found


# the key operation needs a consistent construction rule so neighboring patches retain consistent subdivision boundaries
def PlaceKey(
    BaseLists: tuple[tuple[Fraction, ...], tuple[Fraction, ...]],
    Place: KPolePlace,
    UseList: list[CornerUse],
) -> KCapKey:
    for CornerInfo in UseList:
        IndexU = SideIndex(BaseLists[0], Place[1], CornerInfo.PointU, CornerInfo.SignU)
        IndexV = SideIndex(BaseLists[1], Place[0], CornerInfo.PointV, CornerInfo.SignV)
        if IndexU >= 0 and IndexV >= 0:
            IndexI, IndexJ = (IndexU, IndexV) if CornerInfo.AlongI else (IndexV, IndexU)
            return SpokeKey(CornerInfo.Sector, CornerInfo.Valence, IndexI, IndexJ)
    raise ValueError("Fusion Form cap places found a cap pole outside its sectors")


# the own list contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def OwnList(
    FullList: tuple[Fraction, ...], OwnMap: KMapping[Fraction, int]
) -> tuple[Fraction, ...]:
    Found: list[Fraction] = []
    for Value in FullList:
        IsEnd = Value in (FullList[0], FullList[-1])
        if Found.count(Value) < (KEndCount + 1 if IsEnd else OwnMap.get(Value, 0)):
            Found.append(Value)
    return tuple(Found)


# the cell ranges contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def CellRanges(
    CellValue: PatchCell, Scale: int
) -> tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]]:
    Points = [CornerPoint(CellValue, Scale, Corner) for Corner in range(4)]
    PlacesU = [Point[0] for Point in Points]
    PlacesV = [Point[1] for Point in Points]
    return (min(PlacesU), max(PlacesU)), (min(PlacesV), max(PlacesV))


# the range edge contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def RangeEdge(Bounds: tuple[Fraction, Fraction], SignValue: int) -> Fraction:
    return Bounds[0] if SignValue > 0 else Bounds[1]


# the on strip decision must stay consistent so neighboring patches retain consistent subdivision boundaries
def IsOnStrip(
    CellValue: PatchCell, Scale: int, CornerInfo: CornerUse, AlongU: bool
) -> bool:
    RangeU, RangeV = CellRanges(CellValue, Scale)
    if not AlongU:
        RangeU, RangeV = RangeV, RangeU
    PointU, PointV = (CornerInfo.PointU, CornerInfo.PointV)
    SignU, SignV = (CornerInfo.SignU, CornerInfo.SignV)
    if not AlongU:
        PointU, PointV, SignU, SignV = PointV, PointU, SignV, SignU
    return (
        RangeEdge(RangeV, SignV) == PointV
        and SignU * (RangeEdge(RangeU, SignU) - PointU) >= 0
    )


# the strip list contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def StripList(
    Graph: CageGraph,
    PlanValue: FacePlan,
    Scale: int,
    Context: tuple[list[CornerUse], dict[int, int], bool],
) -> tuple[Fraction, ...]:
    UseList, Levels, AlongU = Context
    Cells = tuple(
        CellValue
        for CellValue in PlanValue.Cells
        if any(
            IsOnStrip(CellValue, Scale, CornerInfo, AlongU) for CornerInfo in UseList
        )
    )
    OwnedU, OwnedV = BaseKnots(Graph, Cells, Scale, Levels)
    Owned = OwnedU if AlongU else OwnedV
    for FaceIndex in sorted({CellValue.Face for CellValue in Cells}):
        for AddsAlongU, Value in PlanValue.Knots.CellAdds.get(FaceIndex, ()):
            if AddsAlongU == AlongU:
                MergeMut(Owned, Value, 1)
    return OwnList(PlanValue.FullU if AlongU else PlanValue.FullV, Owned)


# the own lists contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def OwnLists(
    Graph: CageGraph,
    PlanValue: FacePlan,
    Scale: int,
    Context: tuple[list[CornerUse], dict[int, int]],
) -> tuple[tuple[Fraction, ...], tuple[Fraction, ...]]:
    UseList, Levels = Context
    return (
        StripList(Graph, PlanValue, Scale, (UseList, Levels, True)),
        StripList(Graph, PlanValue, Scale, (UseList, Levels, False)),
    )


# the sector knots contract needs a shared interpretation so neighboring patches retain consistent subdivision boundaries
def SectorKnots(
    KnotList: tuple[Fraction, ...], Value: Fraction, SignValue: int
) -> KSectorKnots:
    Counts = CountValues(
        SignValue * (Entry - Value)
        for Entry in KnotList
        if SignValue * (Entry - Value) >= 0
    )
    return tuple(sorted(Counts.items()))

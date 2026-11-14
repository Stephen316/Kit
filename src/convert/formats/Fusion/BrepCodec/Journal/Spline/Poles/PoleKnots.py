from dataclasses import dataclass as MakeDataClass
from fractions import Fraction
from typing import Mapping as KMapping

from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import (
    CageGraph,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell

KKnotMap = dict[Fraction, int]
KCellAdds = KMapping[int, tuple[tuple[bool, Fraction], ...]]
KFacePoint = tuple[Fraction, Fraction]
KCornerSteps = ((0, 0), (1, 0), (1, 1), (0, 1))
KEndCount = 3
KCornerSharp = 3
KCreaseSharp = 2


@MakeDataClass(frozen=True, slots=True)
class RegionKnots:
    KnotsU: KMapping[Fraction, int]
    KnotsV: KMapping[Fraction, int]
    CellAdds: KCellAdds
    RangeU: tuple[Fraction, Fraction]
    RangeV: tuple[Fraction, Fraction]


def SharpCount(Graph: CageGraph, Vertex: int) -> int:
    return sum(1 for LinkIndex in Graph.Fans[Vertex] if Graph.Creased[LinkIndex])


def SectorSizes(Graph: CageGraph, Vertex: int) -> list[int]:
    FanLinks = Graph.Fans[Vertex]
    Marks = [
        Place for Place, LinkIndex in enumerate(FanLinks) if Graph.Sharp[LinkIndex]
    ]
    return [
        (Marks[(Index + 1) % len(Marks)] - MarkPlace) % len(FanLinks) or len(FanLinks)
        for Index, MarkPlace in enumerate(Marks)
    ] or [len(FanLinks)]


def IsCapPoint(Graph: CageGraph, Vertex: int) -> bool:
    Count = SharpCount(Graph, Vertex)
    if not Graph.Inside[Vertex] or Count >= KCornerSharp:
        return False
    if Count == KCreaseSharp:
        return any(
            SizeValue != KCreaseSharp for SizeValue in SectorSizes(Graph, Vertex)
        )
    return len(Graph.Fans[Vertex]) != 4 or Count == 1


def IsCornerPoint(Graph: CageGraph, Vertex: int) -> bool:
    return Graph.Inside[Vertex] and SharpCount(Graph, Vertex) >= KCornerSharp


def IsFixedPoint(Graph: CageGraph, Vertex: int) -> bool:
    if not IsCornerPoint(Graph, Vertex):
        return False
    return any(SizeValue != 1 for SizeValue in SectorSizes(Graph, Vertex))


def FixedLevel(Graph: CageGraph, Vertex: int) -> int:
    Heads = (Graph.Heads[LinkIndex] for LinkIndex in Graph.Fans[Vertex])
    if any(
        IsCapPoint(Graph, HeadVertex) or IsCornerPoint(Graph, HeadVertex)
        for HeadVertex in Heads
    ):
        return 2
    return 1


def FixedPoints(Graph: CageGraph) -> dict[int, int]:
    return {
        Vertex: FixedLevel(Graph, Vertex)
        for Vertex in range(len(Graph.Fans))
        if IsFixedPoint(Graph, Vertex)
    }


def FixedKnots(Level: int) -> tuple[tuple[Fraction, int], ...]:
    return tuple((Fraction(1, 2**Power), 1) for Power in range(1, Level + 2))


def CapPoints(Graph: CageGraph) -> dict[int, int]:
    Capped = frozenset(
        Vertex for Vertex in range(len(Graph.Fans)) if IsCapPoint(Graph, Vertex)
    )
    return {
        Vertex: (
            2
            if any(Graph.Heads[LinkIndex] in Capped for LinkIndex in Graph.Fans[Vertex])
            else 1
        )
        for Vertex in sorted(Capped)
    }


def CornerKnots(Level: int) -> KKnotMap:
    Spacing = Fraction(1, 2 ** (Level + 1))
    Found: KKnotMap = {Fraction(0): 2, Spacing: 2, 2 * Spacing: 2}
    for Power in range(1, Level):
        Found[Fraction(1, 2**Power)] = max(Found.get(Fraction(1, 2**Power), 0), 1)
    return Found


def MergeMut(Target: KKnotMap, Value: Fraction, Count: int) -> None:
    Target[Value] = max(Target.get(Value, 0), Count)


def FacePoint(
    CellValue: PatchCell, Scale: int, PointS: Fraction, PointT: Fraction
) -> KFacePoint:
    PlaceU = PointS * Scale - Fraction(CellValue.Offset[1])
    PlaceV = PointT * Scale - Fraction(CellValue.Offset[0])
    for _ in range(CellValue.Offset[2] % 4):
        PlaceU, PlaceV = -PlaceV, PlaceU
    return (PlaceU, PlaceV)


def CornerPoint(CellValue: PatchCell, Scale: int, Corner: int) -> KFacePoint:
    StepPair = KCornerSteps[Corner % 4]
    return FacePoint(CellValue, Scale, Fraction(StepPair[0]), Fraction(StepPair[1]))


def IsAlongU(CellValue: PatchCell, Scale: int, SideIndex: int) -> bool:
    return (
        CornerPoint(CellValue, Scale, SideIndex)[0]
        != CornerPoint(CellValue, Scale, SideIndex + 1)[0]
    )


def CellLines(
    Graph: CageGraph, CellValue: PatchCell, Scale: int, Levels: dict[int, int]
) -> list[tuple[bool, Fraction, int]]:
    Found: list[tuple[bool, Fraction, int]] = []
    for Corner, LinkIndex in enumerate(Graph.Loops[CellValue.Face]):
        Vertex = Graph.Links[LinkIndex].VertexIndex
        if Vertex in Levels:
            Marks = tuple(CornerKnots(Levels[Vertex]).items())
        elif IsFixedPoint(Graph, Vertex):
            Marks = FixedKnots(FixedLevel(Graph, Vertex))
        else:
            continue
        StepS, StepT = KCornerSteps[Corner]
        for Value, Count in Marks:
            PlaceS = Value if StepS == 0 else 1 - Value
            PlaceT = Value if StepT == 0 else 1 - Value
            LineS = FacePoint(CellValue, Scale, PlaceS, Fraction(0))
            LineT = FacePoint(CellValue, Scale, Fraction(0), PlaceT)
            SideU = LineS[0] == FacePoint(CellValue, Scale, PlaceS, Fraction(1))[0]
            Found.append((SideU, LineS[0] if SideU else LineS[1], Count))
            SideV = LineT[1] == FacePoint(CellValue, Scale, Fraction(1), PlaceT)[1]
            Found.append((not SideV, LineT[0] if not SideV else LineT[1], Count))
    return Found


def BaseKnots(
    Graph: CageGraph, Cells: tuple[PatchCell, ...], Scale: int, Levels: dict[int, int]
) -> tuple[KKnotMap, KKnotMap]:
    KnotsU: KKnotMap = {}
    KnotsV: KKnotMap = {}
    for CellValue in Cells:
        for Corner in range(4):
            Point = CornerPoint(CellValue, Scale, Corner)
            MergeMut(KnotsU, Point[0], 1)
            MergeMut(KnotsV, Point[1], 1)
        for AlongU, Value, Count in CellLines(Graph, CellValue, Scale, Levels):
            MergeMut(KnotsU if AlongU else KnotsV, Value, Count)
    return KnotsU, KnotsV

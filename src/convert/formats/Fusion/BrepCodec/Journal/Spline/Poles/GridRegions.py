from collections import Counter as CountValues
from fractions import Fraction

from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import (
    CageGraph,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CappedShape import (
    CappedShape,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.PatchCell import PatchCell
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapPlaces import (
    KPolePlace,
    FacePlan,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.GridPoles import (
    KGridPlace,
    KPoleGrid,
    BaseGrid,
    CreaseLines,
    GridPlaces,
    SideGrips,
    SplitGrid,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleKnots import (
    KEndCount,
    RegionKnots,
    CornerPoint,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleLines import KKnotList
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleRows import KPoleRow
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface

KAxisMap = tuple[tuple[int, int, Fraction], tuple[int, int, Fraction]]


def CenterPole(Knots: KKnotList, Value: int) -> int:
    for Index in range(len(Knots) - 4):
        if Knots[Index + 1] == Knots[Index + 2] == Knots[Index + 3] == Value:
            return Index
    for Index in range(len(Knots) - 4):
        if Knots[Index + 1] < Knots[Index + 2] == Value < Knots[Index + 3]:
            return Index
    raise ValueError("Fusion Form grid poles found no pole at a crease vertex")


def CreaseGrid(
    Surface: TsplineSurface, Graph: CageGraph, Places: tuple[KGridPlace, ...]
) -> tuple[KKnotList, KKnotList, KPoleGrid]:
    Limits = (max(Place[0] for Place in Places), max(Place[1] for Place in Places))
    BaseGrips = BaseGrid(Surface, Places, Limits)
    KnotsU, KnotsV, GridRows = SplitGrid(
        BaseGrips, Limits, CreaseLines(Graph, Places, Limits)
    )
    Fixed: dict[KGridPlace, int] = {}
    for Vertex, Sides in SideGrips(Surface, Places, Limits).items():
        Column = CenterPole(KnotsU, Places[Vertex][0])
        RowIndex = CenterPole(KnotsV, Places[Vertex][1])
        Owner = PrimaryGrip(Surface, Vertex)
        Fixed[(Column, RowIndex)] = Owner
        for (StepU, StepV), GripIndex in Sides:
            Fixed[(Column + StepU, RowIndex + StepV)] = GripIndex
    return (
        KnotsU,
        KnotsV,
        [
            [
                (
                    (None, {Fixed[(Column, RowIndex)]: 1.0})
                    if (Column, RowIndex) in Fixed
                    else Entry
                )
                for Column, Entry in enumerate(RowValue)
            ]
            for RowIndex, RowValue in enumerate(GridRows)
        ],
    )


def PrimaryGrip(Surface: TsplineSurface, Vertex: int) -> int:
    Mapping = Surface.Mapping
    if Mapping is None:
        return Vertex
    for GripIndex, Owner in enumerate(Mapping.Owners):
        if Owner.IsPrimary and Owner.VertexIndex == Vertex:
            return GripIndex
    raise ValueError("Fusion Form grid poles found a vertex without a primary grip")


def CellAxes(
    Graph: CageGraph, Places: tuple[KGridPlace, ...], CellValue: PatchCell, Scale: int
) -> KAxisMap:
    Loops = Graph.Loops[CellValue.Face]
    Points = [Places[Graph.Links[LinkIndex].VertexIndex] for LinkIndex in Loops]
    Found: dict[int, tuple[int, int, Fraction]] = {}
    for Corner in (1, 3):
        Global = (Points[Corner][0] - Points[0][0], Points[Corner][1] - Points[0][1])
        First, Other = CornerPoint(CellValue, Scale, 0), CornerPoint(
            CellValue, Scale, Corner
        )
        Local = (Other[0] - First[0], Other[1] - First[1])
        AxisFace = 0 if Local[0] != 0 else 1
        AxisGlobal = 0 if Global[0] != 0 else 1
        SignValue = 1 if (Local[AxisFace] > 0) == (Global[AxisGlobal] > 0) else -1
        Shift = First[AxisFace] - SignValue * Scale * Points[0][AxisGlobal]
        Found[AxisFace] = (AxisGlobal, SignValue, Shift)
    return (Found[0], Found[1])


def RegionRange(
    Graph: CageGraph,
    Places: tuple[KGridPlace, ...],
    Cells: tuple[PatchCell, ...],
    AxisGlobal: int,
) -> tuple[int, int]:
    Values = [
        Places[Graph.Links[LinkIndex].VertexIndex][AxisGlobal]
        for CellValue in Cells
        for LinkIndex in Graph.Loops[CellValue.Face]
    ]
    return (min(Values), max(Values))


def SubRange(Knots: KKnotList, Bounds: tuple[int, int]) -> tuple[int, int]:
    Lower, Upper = Fraction(Bounds[0]), Fraction(Bounds[1])
    if Knots.count(Lower) < KEndCount or Knots.count(Upper) < KEndCount:
        raise ValueError("Fusion Form grid poles need regions bounded by creases")
    return (Knots.index(Lower) + Knots.count(Lower) - 4, Knots.index(Upper) - 1)


def FaceKnots(
    Knots: KKnotList,
    SpanPair: tuple[int, int],
    AxisInfo: tuple[int, int, Fraction],
    Scale: int,
) -> KKnotList:
    Inner = Knots[SpanPair[0] + 1 : SpanPair[1] + 4]
    Values = tuple(
        AxisInfo[1] * Scale * Value + AxisInfo[2]
        for Value in (Inner[0],) + Inner + (Inner[-1],)
    )
    return Values if AxisInfo[1] > 0 else tuple(reversed(Values))


def RegionGrid(
    GridRows: KPoleGrid,
    Spans: tuple[tuple[int, int], tuple[int, int]],
    AxisTable: KAxisMap,
) -> dict[KPolePlace, KPoleRow]:
    Columns = range(Spans[0][0], Spans[0][1] + 1)
    RowRange = range(Spans[1][0], Spans[1][1] + 1)
    Ordered = [list(Columns), list(RowRange)]
    for AxisFace in range(2):
        if AxisTable[AxisFace][1] < 0:
            Ordered[AxisTable[AxisFace][0]].reverse()
    Found: dict[KPolePlace, KPoleRow] = {}
    for FaceRow, Second in enumerate(Ordered[AxisTable[1][0]]):
        for FaceColumn, First in enumerate(Ordered[AxisTable[0][0]]):
            Place = (First, Second) if AxisTable[0][0] == 0 else (Second, First)
            Found[(FaceRow, FaceColumn)] = GridRows[Place[1]][Place[0]][1]
    return Found


def GridPlan(
    Region: int, Cells: tuple[PatchCell, ...], FullU: KKnotList, FullV: KKnotList
) -> FacePlan:
    InnerU = CountValues(Value for Value in FullU if FullU[0] < Value < FullU[-1])
    InnerV = CountValues(Value for Value in FullV if FullV[0] < Value < FullV[-1])
    return FacePlan(
        Region,
        Cells,
        RegionKnots(
            dict(InnerU),
            dict(InnerV),
            {},
            (FullU[0], FullU[-1]),
            (FullV[0], FullV[-1]),
        ),
        FullU,
        FullV,
    )


def GridGrids(
    Surface: TsplineSurface, Graph: CageGraph, Shape: CappedShape, Scale: int
) -> tuple[tuple[FacePlan, ...], list[dict[KPolePlace, KPoleRow]]]:
    Places = GridPlaces(Surface)
    GlobalU, GlobalV, PoleGrid = CreaseGrid(Surface, Graph, Places)
    KnotsGlobal = (GlobalU, GlobalV)
    Plans: list[FacePlan] = []
    Grids: list[dict[KPolePlace, KPoleRow]] = []
    for Region, Cells in enumerate(Shape.Regions):
        AxisTable = CellAxes(Graph, Places, Cells[0], Scale)
        Spans = (
            SubRange(KnotsGlobal[0], RegionRange(Graph, Places, Cells, 0)),
            SubRange(KnotsGlobal[1], RegionRange(Graph, Places, Cells, 1)),
        )
        FullU = FaceKnots(
            KnotsGlobal[AxisTable[0][0]], Spans[AxisTable[0][0]], AxisTable[0], Scale
        )
        FullV = FaceKnots(
            KnotsGlobal[AxisTable[1][0]], Spans[AxisTable[1][0]], AxisTable[1], Scale
        )
        Plans.append(GridPlan(Region, Cells, FullU, FullV))
        Grids.append(RegionGrid(PoleGrid, Spans, AxisTable))
    return tuple(Plans), Grids

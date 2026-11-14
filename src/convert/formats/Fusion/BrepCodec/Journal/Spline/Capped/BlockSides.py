from dataclasses import dataclass as MakeDataClass
from typing import Mapping as KMapping

from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.BlockGrid import (
    BlockGrid,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import (
    CageGraph,
)

KPoint = tuple[int, int]
KSideKey = tuple[int, int, int]
KSideEntry = tuple[int, int, int]
KStep = tuple[KPoint, KPoint, KPoint]
KCornerSteps = ((0, 0), (1, 0), (1, 1), (0, 1))
KSplitSeam = "Fusion Form capped layout has no seam rule for a split closed seam"


@MakeDataClass(frozen=True, slots=True)
class GridFrame:
    Region: int
    Grid: BlockGrid
    Sides: KMapping[KSideKey, KSideEntry]
    Corners: KMapping[KPoint, int]
    Seams: tuple[bool, bool]


@MakeDataClass(frozen=True, slots=True)
class SideUse:
    Region: int
    Side: int
    Start: KPoint
    Final: KPoint
    Links: tuple[int, ...]
    StartVertex: int
    FinalVertex: int
    Cells: tuple[tuple[int, int], ...]
    Closure: int


def ReducePoint(GridValue: BlockGrid, Point: KPoint) -> KPoint:
    return (
        Point[0] % GridValue.Width if GridValue.WrapsU else Point[0],
        Point[1] % GridValue.Height if GridValue.WrapsV else Point[1],
    )


def CellSides(Graph: CageGraph, GridValue: BlockGrid) -> dict[KSideKey, KSideEntry]:
    Found: dict[KSideKey, KSideEntry] = {}
    for FaceIndex, Place in zip(GridValue.Faces, GridValue.Places):
        for LocalSide, LinkIndex in enumerate(Graph.Loops[FaceIndex]):
            BlockSide = (LocalSide + Place[2]) % 4
            Found[(Place[0], Place[1], BlockSide)] = (LinkIndex, FaceIndex, LocalSide)
    return Found


def SeamPairs(GridValue: BlockGrid, AxisIndex: int) -> list[tuple[KSideKey, KSideKey]]:
    Width, Height = GridValue.Width, GridValue.Height
    if AxisIndex == 0:
        return [((Width - 1, Index, 1), (0, Index, 3)) for Index in range(Height)]
    return [((Index, Height - 1, 2), (Index, 0, 0)) for Index in range(Width)]


def IsSeamAxis(
    Graph: CageGraph,
    Sides: KMapping[KSideKey, KSideEntry],
    GridValue: BlockGrid,
    AxisIndex: int,
) -> bool:
    return all(
        First in Sides
        and Second in Sides
        and Graph.Links[Sides[First][0]].EdgeIndex
        == Graph.Links[Sides[Second][0]].EdgeIndex
        for First, Second in SeamPairs(GridValue, AxisIndex)
    )


def ReadFrame(Graph: CageGraph, GridValue: BlockGrid, Region: int) -> GridFrame:
    Sides = CellSides(Graph, GridValue)
    Corners: dict[KPoint, int] = {}
    for SideKey, SideEntry in Sides.items():
        StepU, StepV = KCornerSteps[SideKey[2]]
        Point = ReducePoint(GridValue, (SideKey[0] + StepU, SideKey[1] + StepV))
        Corners[Point] = Graph.Links[SideEntry[0]].VertexIndex
    Seams = (
        IsSeamAxis(Graph, Sides, GridValue, 0),
        IsSeamAxis(Graph, Sides, GridValue, 1),
    )
    return GridFrame(Region, GridValue, Sides, Corners, Seams)


def FrameCorners(Frame: GridFrame) -> frozenset[int]:
    Width, Height = Frame.Grid.Width, Frame.Grid.Height
    return frozenset(
        Frame.Corners[ReducePoint(Frame.Grid, Point)]
        for Point in ((0, 0), (Width, 0), (Width, Height), (0, Height))
    )


def SideSteps(GridValue: BlockGrid, BlockSide: int) -> list[KStep]:
    Width, Height = GridValue.Width, GridValue.Height
    if BlockSide == 0:
        return [((Index, 0), (Index + 1, 0), (Index, 0)) for Index in range(Width)]
    if BlockSide == 1:
        return [
            ((Width, Index), (Width, Index + 1), (Width - 1, Index))
            for Index in range(Height)
        ]
    if BlockSide == 2:
        return [
            ((Index + 1, Height), (Index, Height), (Index, Height - 1))
            for Index in reversed(range(Width))
        ]
    return [
        ((0, Index + 1), (0, Index), (0, Index)) for Index in reversed(range(Height))
    ]


def IsSeamSide(Frame: GridFrame, BlockSide: int) -> bool:
    return Frame.Seams[1 - BlockSide % 2]


def SeamShift(Frame: GridFrame, BlockSide: int, Closure: int) -> int:
    if not IsSeamSide(Frame, BlockSide):
        return 0
    if Closure == 1:
        return {1: -1, 3: 1}.get(BlockSide, 0)
    return -1 if BlockSide in (1, 2) else 0


def WindowCell(
    Frame: GridFrame, CellPoint: KPoint, BlockSide: int, Shift: int
) -> tuple[int, int]:
    BaseCell, BaseSide = CellPoint, BlockSide
    if Shift:
        Width, Height = Frame.Grid.Width, Frame.Grid.Height
        BaseCell = (
            (Width - 1 - CellPoint[0], CellPoint[1])
            if BlockSide % 2
            else (CellPoint[0], Height - 1 - CellPoint[1])
        )
        BaseSide = (BlockSide + 2) % 4
    SideEntry = Frame.Sides[(BaseCell[0], BaseCell[1], BaseSide)]
    return SideEntry[1], SideEntry[2]


def UseClosure(GridValue: BlockGrid, BlockSide: int, Steps: list[KStep]) -> int:
    Along = BlockSide % 2
    IsWrapped = GridValue.WrapsV if Along else GridValue.WrapsU
    Period = GridValue.Height if Along else GridValue.Width
    return 2 if IsWrapped and len(Steps) == Period else 0


def SideClosure(Frame: GridFrame, BlockSide: int, Steps: list[KStep]) -> int:
    if UseClosure(Frame.Grid, BlockSide, Steps) == 2:
        return 2
    First = Frame.Corners[ReducePoint(Frame.Grid, Steps[0][0])]
    Final = Frame.Corners[ReducePoint(Frame.Grid, Steps[-1][1])]
    return 1 if First == Final else 0


def MakeUse(
    Frame: GridFrame, BlockSide: int, Steps: list[KStep], Shift: int
) -> SideUse:
    GridValue = Frame.Grid
    ShiftU = Shift * GridValue.Width if BlockSide % 2 else 0
    ShiftV = 0 if BlockSide % 2 else Shift * GridValue.Height
    First, Final = Steps[0][0], Steps[-1][1]
    return SideUse(
        Frame.Region,
        BlockSide,
        (First[0] + ShiftU, First[1] + ShiftV),
        (Final[0] + ShiftU, Final[1] + ShiftV),
        tuple(Frame.Sides[(Entry[2][0], Entry[2][1], BlockSide)][0] for Entry in Steps),
        Frame.Corners[ReducePoint(GridValue, First)],
        Frame.Corners[ReducePoint(GridValue, Final)],
        tuple(sorted(WindowCell(Frame, Entry[2], BlockSide, Shift) for Entry in Steps)),
        SideClosure(Frame, BlockSide, Steps),
    )


def SideUses(Frame: GridFrame, BlockSide: int, Breaks: frozenset[int]) -> list[SideUse]:
    Steps = SideSteps(Frame.Grid, BlockSide)
    Groups: list[list[KStep]] = []
    for Entry in Steps:
        if not Groups or Frame.Corners[ReducePoint(Frame.Grid, Entry[0])] in Breaks:
            Groups.append([])
        Groups[-1].append(Entry)
    Closure = SideClosure(Frame, BlockSide, Steps)
    if Closure == 1 and len(Groups) > 1 and IsSeamSide(Frame, BlockSide):
        raise ValueError(KSplitSeam)
    Shift = SeamShift(Frame, BlockSide, Closure)
    return [MakeUse(Frame, BlockSide, Group, Shift) for Group in Groups]


def RegionLoop(Frame: GridFrame, Breaks: frozenset[int]) -> tuple[SideUse, ...]:
    return tuple(
        UseValue
        for BlockSide in range(4)
        for UseValue in SideUses(Frame, BlockSide, Breaks)
    )

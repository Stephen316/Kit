from typing import Mapping as KMapping

from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.SolveCaps import SolveCaps
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import (
    CageGraph,
    ReadGraph,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CappedLayout import (
    CappedLayout,
    KnotScale,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CappedShape import (
    CappedShape,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapHook import (
    KCapHook,
    KCapKey,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapFrames import (
    CapFrame,
    FrameRows,
    RegionFrames,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapPlaces import (
    KPolePlace,
    FacePlan,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapRequests import (
    CapRequests,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.FaceNets import MeshLevels
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.FixedPoles import FixedRows
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.GridPoles import IsCompound
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.GridRegions import GridGrids
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleKnots import (
    KFacePoint,
    CapPoints,
    CornerPoint,
    FixedPoints,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleLines import (
    CurveRows,
    SurfacePoint,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleMesh import (
    MeshFromCage,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleRows import (
    KIndexedRow,
    KPoleRow,
    FreezeRow,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleSpans import (
    KNetTable,
    PoleRow,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.SpokeKnots import (
    FullKnots,
    KnotVector,
    PlanKnots,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilCurve import (
    StencilCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilFace import (
    StencilFace,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.StencilTable import (
    StencilTable,
)
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface

KGridRows = dict[KPolePlace, KIndexedRow]
KCurveShape = tuple[tuple[float, ...], tuple[int, ...], int]


def FacePlans(
    Graph: CageGraph, Shape: CappedShape, Scale: int, Levels: KMapping[int, int]
) -> tuple[FacePlan, ...]:
    Knots = PlanKnots(Graph, Shape, Scale, dict(Levels))
    return tuple(
        FacePlan(
            Region,
            Cells,
            Knots[Region],
            FullKnots(Knots[Region].KnotsU, Knots[Region].RangeU),
            FullKnots(Knots[Region].KnotsV, Knots[Region].RangeV),
        )
        for Region, Cells in enumerate(Shape.Regions)
    )


def PlainRows(
    NetTable: KNetTable,
    PlanValue: FacePlan,
    Scale: int,
    CapSpots: frozenset[KPolePlace],
) -> dict[KPolePlace, KPoleRow]:
    Found: dict[KPolePlace, KPoleRow] = {}
    for RowIndex in range(len(PlanValue.FullV) - 4):
        for Column in range(len(PlanValue.FullU) - 4):
            if (RowIndex, Column) in CapSpots:
                continue
            RowValue = PoleRow(
                NetTable,
                PlanValue.Cells,
                Scale,
                PlanValue.FullU,
                PlanValue.FullV,
                (RowIndex, Column),
            )
            if RowValue is None:
                raise ValueError(
                    "Fusion Form pole engine found a pole with no polynomial span"
                )
            Found[(RowIndex, Column)] = RowValue
    return Found


def CapRows(
    Frames: tuple[CapFrame, ...],
    Answers: dict[int, KMapping[KCapKey, KPoleRow]],
    Context: tuple[KNetTable, FacePlan, int],
) -> dict[KPolePlace, KPoleRow]:
    Found: dict[KPolePlace, KPoleRow] = {}
    for Frame in Frames:
        Found.update(FrameRows(Frame, Answers[Frame.Vertex], Context))
    return Found


def CapSpots(Frames: tuple[CapFrame, ...]) -> frozenset[KPolePlace]:
    return frozenset(Place for Frame in Frames for Place in Frame.Places)


def IndexGrids(
    Plans: tuple[FacePlan, ...], Grids: list[dict[KPolePlace, KPoleRow]]
) -> tuple[list[KPoleRow], list[KGridRows], list[StencilFace]]:
    RowList: list[KPoleRow] = []
    Indexed: list[KGridRows] = []
    Faces: list[StencilFace] = []
    for PlanValue, GridValue in zip(Plans, Grids):
        CountU, CountV = len(PlanValue.FullU) - 4, len(PlanValue.FullV) - 4
        Start = len(RowList)
        Places = [
            (RowIndex, Column) for RowIndex in range(CountV) for Column in range(CountU)
        ]
        RowList += [GridValue[Place] for Place in Places]
        Indexed.append(
            {
                Place: (Start + Offset, GridValue[Place])
                for Offset, Place in enumerate(Places)
            }
        )
        Knots = PlanValue.Knots
        Faces.append(
            StencilFace(
                PlanValue.Region,
                KnotVector(Knots.KnotsU, Knots.RangeU),
                KnotVector(Knots.KnotsV, Knots.RangeV),
                tuple(range(Start, Start + len(Places))),
            )
        )
    return RowList, Indexed, Faces


def PlacedRows(
    RowList: list[KPoleRow], Entries: list[KIndexedRow]
) -> tuple[list[KPoleRow], tuple[int, ...]]:
    Grown = list(RowList)
    Indices: list[int] = []
    for Index, RowValue in Entries:
        if Index is None:
            Grown.append(RowValue)
            Index = len(Grown) - 1
        Indices.append(Index)
    return Grown, tuple(Indices)


def VertexPlace(
    Graph: CageGraph, Plans: tuple[FacePlan, ...], Scale: int, Vertex: int
) -> tuple[int, KFacePoint] | None:
    for PlanValue in Plans:
        for CellValue in PlanValue.Cells:
            for Corner, LinkIndex in enumerate(Graph.Loops[CellValue.Face]):
                if Graph.Links[LinkIndex].VertexIndex == Vertex:
                    return PlanValue.Region, CornerPoint(CellValue, Scale, Corner)
    return None


def LineEntries(
    Shape: CappedShape, Plans: tuple[FacePlan, ...], Indexed: list[KGridRows]
) -> tuple[list[KIndexedRow], list[KCurveShape]]:
    Entries: list[KIndexedRow] = []
    Curves: list[KCurveShape] = []
    for CurveValue in Shape.Curves:
        Knots, Counts, Poles = CurveRows(
            Plans[CurveValue.Region], Indexed[CurveValue.Region], CurveValue
        )
        Curves.append((Knots, Counts, len(Poles)))
        Entries += Poles
    return Entries, Curves


def PointEntries(
    Graph: CageGraph,
    Shape: CappedShape,
    Plans: tuple[FacePlan, ...],
    Indexed: list[KGridRows],
    Scale: int,
) -> list[KIndexedRow]:
    Entries: list[KIndexedRow] = []
    for Vertex in Shape.Points:
        Found = VertexPlace(Graph, Plans, Scale, Vertex)
        if Found is None:
            raise ValueError(
                "Fusion Form pole engine found a vertex outside every face"
            )
        Region, Point = Found
        Entries.append(SurfacePoint(Plans[Region], Indexed[Region], Point[0], Point[1]))
    return Entries


def SolveGrids(
    Surface: TsplineSurface, Graph: CageGraph, Shape: CappedShape, CapSolver: KCapHook
) -> tuple[tuple[FacePlan, ...], list[dict[KPolePlace, KPoleRow]]]:
    Scale = KnotScale(Surface)
    if IsCompound(Surface):
        return GridGrids(Surface, Graph, Shape, Scale)
    Levels = CapPoints(Graph)
    Fixed = FixedPoints(Graph)
    MeshValue = MeshFromCage(Surface, Graph)
    Depth = max([*Levels.values(), *Fixed.values()], default=0) + 1
    NetTable = MeshLevels(MeshValue, Depth)
    Plans = FacePlans(Graph, Shape, Scale, Levels)
    Frames = [RegionFrames(Graph, PlanValue, Scale, Levels) for PlanValue in Plans]
    Requests = CapRequests(Graph, Plans, (NetTable, MeshValue, Scale), Levels, Frames)
    Answers = {Vertex: CapSolver(Request) for Vertex, Request in Requests.items()}
    Grids: list[dict[KPolePlace, KPoleRow]] = []
    for PlanValue in Plans:
        Pinned = FixedRows(Graph, PlanValue, (MeshValue, Scale), frozenset(Fixed))
        Skips = CapSpots(Frames[PlanValue.Region]) | frozenset(Pinned)
        Grids.append(
            PlainRows(NetTable, PlanValue, Scale, Skips)
            | Pinned
            | CapRows(Frames[PlanValue.Region], Answers, (NetTable, PlanValue, Scale))
        )
    return Plans, Grids


def BuildTable(
    Surface: TsplineSurface, CapSolver: KCapHook = SolveCaps
) -> StencilTable:
    Graph = ReadGraph(Surface)
    Shape = CappedLayout(Surface)
    Plans, Grids = SolveGrids(Surface, Graph, Shape, CapSolver)
    RowList, Indexed, Faces = IndexGrids(Plans, Grids)
    CurveEntries, CurveShapes = LineEntries(Shape, Plans, Indexed)
    RowList, CurveIndices = PlacedRows(RowList, CurveEntries)
    RowList, PointIndices = PlacedRows(
        RowList, PointEntries(Graph, Shape, Plans, Indexed, KnotScale(Surface))
    )
    Curves: list[StencilCurve] = []
    Start = 0
    for Knots, Counts, PoleCount in CurveShapes:
        Curves.append(
            StencilCurve(Knots, Counts, CurveIndices[Start : Start + PoleCount])
        )
        Start += PoleCount
    return StencilTable(
        len(Surface.Grips),
        tuple(FreezeRow(RowValue) for RowValue in RowList),
        tuple(Faces),
        tuple(Curves),
        PointIndices,
    )

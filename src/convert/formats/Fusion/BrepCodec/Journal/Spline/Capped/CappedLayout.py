from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.BlockGrid import (
    GridCells,
    PlaceBlock,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.BlockSides import (
    FrameCorners,
    GridFrame,
    ReadFrame,
    RegionLoop,
    SideUse,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageBlocks import (
    GroupBlocks,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CageGraph import (
    CageGraph,
    ReadGraph,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CappedShape import (
    CappedCurve,
    CappedEdge,
    CappedFace,
    CappedShape,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.DrawLines import (
    DrawLines,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.EdgePlans import (
    EdgeBounds,
    EdgePlan,
    IsReversed,
    PlanConvexity,
    PlanEdges,
    PlanPoints,
    PlanRange,
    PlanWindows,
    UseTrace,
    WideUse,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormUse,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.PoleKnots import (
    KCreaseSharp,
    IsCapPoint,
    IsCornerPoint,
    SharpCount,
)
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.TSplineCodec.Validation.CheckSurface import CheckSurface


def KnotScale(Surface: TsplineSurface) -> int:
    Intervals = {EdgeValue.KnotInterval for EdgeValue in Surface.Topology.Edges}
    if len(Intervals) != 1:
        raise ValueError("Fusion Form capped layout needs one shared knot interval")
    Interval = float(next(iter(Intervals)))
    if Interval <= 0.0 or not Interval.is_integer():
        raise ValueError("Fusion Form capped layout needs a whole knot interval")
    return int(Interval)


def ReadFrames(Graph: CageGraph) -> tuple[GridFrame, ...]:
    Drawn = DrawLines(Graph)
    return tuple(
        ReadFrame(Graph, PlaceBlock(Graph, Faces, Drawn), Region)
        for Region, Faces in enumerate(GroupBlocks(Graph, Drawn))
    )


def EdgeLabels(
    Plans: tuple[EdgePlan, ...], Scale: int, FaceCount: int
) -> tuple[str, ...]:
    Labels: list[str] = []
    Counter = FaceCount
    for PlanValue in Plans:
        IsTagged = bool(PlanWindows(PlanValue, Scale))
        Counter += 1 if IsTagged else 0
        Labels.append(str(Counter) if IsTagged else "")
    return tuple(Labels)


def LayoutEdge(
    Graph: CageGraph,
    PlanValue: EdgePlan,
    WidePlans: tuple[EdgePlan, ...],
    Scale: int,
    Places: dict[int, int],
    Label: str,
) -> CappedEdge:
    CurveIndex = WideUse(WidePlans, PlanValue.Maker)[0]
    return CappedEdge(
        Places[PlanValue.Maker.StartVertex],
        Places[PlanValue.Maker.FinalVertex],
        CurveIndex,
        PlanConvexity(Graph, PlanValue),
        Label,
        PlanWindows(PlanValue, Scale),
        EdgeBounds(PlanValue, WidePlans[CurveIndex], Scale),
    )


def LayoutEdges(
    Graph: CageGraph,
    Plans: tuple[EdgePlan, ...],
    WidePlans: tuple[EdgePlan, ...],
    Scale: int,
    FaceCount: int,
) -> tuple[CappedEdge, ...]:
    Places = {Vertex: Place for Place, Vertex in enumerate(PlanPoints(Plans))}
    Labels = EdgeLabels(Plans, Scale, FaceCount)
    return tuple(
        LayoutEdge(Graph, PlanValue, WidePlans, Scale, Places, Labels[EdgeIndex])
        for EdgeIndex, PlanValue in enumerate(Plans)
    )


def PlanCurve(PlanValue: EdgePlan, Scale: int) -> CappedCurve:
    Lower, Upper = PlanRange(PlanValue, Scale)
    Maker = PlanValue.Maker
    return CappedCurve(
        Maker.Region, Maker.Side, Lower, Upper, Maker.Closure, Maker.Links
    )


def WideTrace(
    WidePlans: tuple[EdgePlan, ...], UseValue: SideUse, Scale: int
) -> BsCurve:
    CurveIndex, Outer = WideUse(WidePlans, UseValue)
    return UseTrace(WidePlans[CurveIndex], Outer, Scale)


def LoopUses(
    LoopValue: tuple[SideUse, ...],
    Plans: tuple[EdgePlan, ...],
    WidePlans: tuple[EdgePlan, ...],
    Scale: int,
) -> tuple[FormUse, ...]:
    Owners = {
        UseValue: EdgeIndex
        for EdgeIndex, PlanValue in enumerate(Plans)
        for UseValue in PlanValue.Users
    }
    return tuple(
        FormUse(
            Owners[UseValue],
            IsReversed(Plans[Owners[UseValue]], UseValue),
            WideTrace(WidePlans, UseValue, Scale),
            0.0,
        )
        for UseValue in LoopValue
    )


def LayoutFaces(
    Graph: CageGraph,
    Loops: tuple[tuple[SideUse, ...], ...],
    Plans: tuple[EdgePlan, ...],
    WidePlans: tuple[EdgePlan, ...],
    Scale: int,
) -> tuple[CappedFace, ...]:
    IsOpen = any(Graph.Open)
    return tuple(
        CappedFace(
            Region,
            LoopUses(Loops[Region], Plans, WidePlans, Scale),
            str(Region + 1),
            IsOpen,
            False if IsOpen else None,
        )
        for Region in reversed(range(len(Loops)))
    )


def CreaseEnds(Surface: TsplineSurface, Graph: CageGraph) -> frozenset[int]:
    Mapping = Surface.Mapping
    Owners: frozenset[int] = (
        frozenset(Compound.VertexIndex for Compound in Mapping.Compounds)
        if Mapping is not None
        else frozenset()
    )
    return frozenset(
        Vertex
        for Vertex, FanLinks in enumerate(Graph.Fans)
        if Vertex not in Owners
        and sum(1 for LinkIndex in FanLinks if Graph.Creased[LinkIndex]) == 1
    )


def IsDartPoint(Graph: CageGraph, Vertex: int) -> bool:
    return Graph.Regular[Vertex] and SharpCount(Graph, Vertex) == 1


def IsHubPoint(Graph: CageGraph, Vertex: int) -> bool:
    if IsDartPoint(Graph, Vertex):
        return False
    return IsCapPoint(Graph, Vertex) or IsCornerPoint(Graph, Vertex)


def IsDartCovered(Graph: CageGraph, Vertex: int) -> bool:
    for LinkIndex in Graph.Fans[Vertex]:
        HeadVertex = Graph.Heads[LinkIndex]
        if IsHubPoint(Graph, HeadVertex):
            return True
        if (
            not Graph.Creased[LinkIndex]
            and SharpCount(Graph, HeadVertex) >= KCreaseSharp
        ):
            return True
    return False


def CheckDarts(Surface: TsplineSurface, Graph: CageGraph) -> None:
    if len(Surface.Grips) > len(Surface.Topology.Vertices):
        return
    for Vertex in range(len(Graph.Fans)):
        if IsDartPoint(Graph, Vertex) and not IsDartCovered(Graph, Vertex):
            raise ValueError(
                "Fusion Form dart rule needs a cap point or crease next to the dart"
            )


def FramePeriods(Frame: GridFrame, Scale: int) -> tuple[int, int]:
    GridValue = Frame.Grid
    return (
        GridValue.Width * Scale if GridValue.WrapsU else 0,
        GridValue.Height * Scale if GridValue.WrapsV else 0,
    )


def CappedLayout(Surface: TsplineSurface) -> CappedShape:
    CheckSurface(Surface)
    Scale = KnotScale(Surface)
    Graph = ReadGraph(Surface)
    CheckDarts(Surface, Graph)
    Frames = ReadFrames(Graph)
    Corners = frozenset(Vertex for Frame in Frames for Vertex in FrameCorners(Frame))
    Breaks = Corners | CreaseEnds(Surface, Graph)
    Loops = tuple(RegionLoop(Frame, Breaks) for Frame in Frames)
    Plans = PlanEdges(Graph, Loops)
    WidePlans = PlanEdges(Graph, tuple(RegionLoop(Frame, Corners) for Frame in Frames))
    return CappedShape(
        PlanPoints(Plans),
        tuple(PlanCurve(PlanValue, Scale) for PlanValue in WidePlans),
        LayoutEdges(Graph, Plans, WidePlans, Scale, len(Frames)),
        LayoutFaces(Graph, Loops, Plans, WidePlans, Scale),
        tuple(GridCells(Frame.Grid, Scale) for Frame in Frames),
        tuple(FramePeriods(Frame, Scale) for Frame in Frames),
    )

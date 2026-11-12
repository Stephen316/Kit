from convert.geometry.Extrude.Polygon.PrismFrame import PlacePrismPoint
from convert.geometry.Extrude.Trimmed.TrimEdge import GetEdgeTol, MakeTrimRim
from convert.geometry.Extrude.Trimmed.TrimOperand import KTrimUse
from convert.geometry.Revolve.SweepVector import OffsetVector
from interchange.brep.curves.BrepCurves import BrepCurve, LineCurve
from interchange.brep.topology.BrepTopology import BrepEdge, BrepVertex
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector


# rim and rail ordering gives cap and side topology a common edge index
def BuildTrimEdges(
    Prefix: str,
    FrameValue: Transform,
    Points: tuple[PlaneVector, ...],
    RingUses: tuple[KTrimUse, ...],
    LowerMm: float,
    UpperMm: float,
    Tolerance: float,
) -> tuple[tuple[BrepVertex, ...], tuple[BrepCurve, ...], tuple[BrepEdge, ...]]:
    Count = len(Points)
    Stations = (LowerMm, UpperMm)
    Vertices = tuple(
        BrepVertex(
            f"{Prefix}-vertex-{Layer * Count + Index}",
            PlacePrismPoint(FrameValue, Point, Height),
            tolerance=Tolerance,
        )
        for Layer, Height in enumerate(Stations)
        for Index, Point in enumerate(Points)
    )
    Curves: list[BrepCurve] = []
    Edges: list[BrepEdge] = []
    for Layer, Height in enumerate(Stations):
        LayerBase = Layer * Count
        for Index, (Operand, Reversed) in enumerate(RingUses):
            First, Second = (
                Vertices[LayerBase + Index],
                Vertices[LayerBase + (Index + 1) % Count],
            )
            if Reversed:
                First, Second = Second, First
            Curve, EdgeValue = MakeTrimRim(
                f"{Prefix}-rim-{LayerBase + Index}",
                Operand,
                FrameValue,
                Height,
                First,
                Second,
                Tolerance,
            )
            Curves.append(Curve)
            Edges.append(EdgeValue)
    Depth = UpperMm - LowerMm
    for Index, First in enumerate(Vertices[:Count]):
        Second = Vertices[Count + Index]
        Identity = f"{Prefix}-rail-{Index}"
        Curve = LineCurve(f"{Identity}-curve", First.point, FrameValue.z_axis)
        Finish = OffsetVector(First.point, FrameValue.z_axis, Depth)
        Accuracy = GetEdgeTol(First, Second, First.point, Finish, Tolerance)
        Curves.append(Curve)
        Edges.append(
            BrepEdge(
                Identity, First.id, Second.id, Curve.id, 0.0, Depth, tolerance=Accuracy
            )
        )
    return Vertices, tuple(Curves), tuple(Edges)

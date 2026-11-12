from interchange.brep.topology.BrepTopology import BrepEdge
from collections.abc import Callable

from convert.adapters.freecad.BrepGraph import ModelGraph
from convert.adapters.freecad.CurvedRing import CurvedRingArea
from convert.adapters.freecad.PlanarArc import ArcInPlane
from convert.geometry.Revolve.SweepVector import DotVector, OffsetVector
from interchange.brep.curves.BrepCurves import CircleCurve, LineCurve
from interchange.brep.surfaces.BrepSurfaces import PlaneSurface
from interchange.brep.topology.BrepTopology import BrepFace, BrepLoop
from interchange.geometry.models.GeometryCurves import ArcGeometry, LineGeometry
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector

# stable frame typing keeps qualification identical to the emitted geometry records
KFrameFactory = Callable[
    [SpaceVector, SpaceVector, str],
    tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ],
]


# planar caps keep the exact oriented intervals of all proven line and circle edges
def CapRingArea(
    Graph: ModelGraph,
    FaceValue: BrepFace,
    Surface: PlaneSurface,
    LoopValue: BrepLoop,
    Tolerance: float,
    MakeFrame: KFrameFactory,
) -> float | None:
    if not LoopValue.outer:
        return None
    FrameValue = MakeFrame(
        Surface.normal, Surface.reference_direction, f"plane surface {Surface.id}"
    )
    Normal, PlaneX, PlaneY = (SpaceVector(*AxisValue) for AxisValue in FrameValue)
    Allowed = max(
        Tolerance,
        FaceValue.tolerance,
        1e-07,
        *(
            Graph.edges[Graph.coedges[Identity].edge_id].tolerance
            for Identity in LoopValue.coedge_ids
        ),
    )
    Geometries: list[tuple[LineGeometry | ArcGeometry, bool]] = []
    for CoedgeId in LoopValue.coedge_ids:
        Coedge = Graph.coedges[CoedgeId]
        EdgeValue = Graph.edges[Coedge.edge_id]
        if Coedge.pcurve_id or EdgeValue.degenerate:
            return None
        Curve = Graph.curves[EdgeValue.curve_id]
        if isinstance(Curve, LineCurve):
            Origin = OffsetVector(Curve.origin, Surface.origin, -1.0)
            First = OffsetVector(Origin, Curve.direction, EdgeValue.start_parameter)
            Finish = OffsetVector(Origin, Curve.direction, EdgeValue.end_parameter)
            if not all(
                abs(DotVector(Normal, Point)) <= Allowed for Point in (First, Finish)
            ):
                return None
            LineValue = LineGeometry(
                PlaneVector(DotVector(First, PlaneX), DotVector(First, PlaneY)),
                PlaneVector(DotVector(Finish, PlaneX), DotVector(Finish, PlaneY)),
            )
            Geometries.append((LineValue, Coedge.reversed))
        elif isinstance(Curve, CircleCurve):
            ArcValue = ReadRingArc(
                Curve, EdgeValue, Surface, (Normal, PlaneX, PlaneY), Allowed, MakeFrame
            )
            if ArcValue is None:
                return None
            Geometry, IsReversed = ArcValue
            Geometries.append((Geometry, IsReversed != Coedge.reversed))
        else:
            return None
    return CurvedRingArea(tuple(Geometries), Allowed)


# circular coedges retain their orientation while being projected into the cap plane
def ReadRingArc(
    Curve: CircleCurve,
    EdgeValue: BrepEdge,
    Surface: PlaneSurface,
    PlaneFrame: tuple[SpaceVector, SpaceVector, SpaceVector],
    Allowed: float,
    MakeFrame: KFrameFactory,
) -> tuple[ArcGeometry, bool] | None:
    CircleFrame = MakeFrame(
        Curve.axis, Curve.reference_direction, f"circle curve {Curve.id}"
    )
    CircleAxis, CircleX, CircleY = (
        SpaceVector(*AxisValue) for AxisValue in CircleFrame
    )
    ArcValue = ArcInPlane(
        Curve,
        EdgeValue,
        Surface.origin,
        PlaneFrame,
        (CircleAxis, CircleX, CircleY),
        Allowed,
    )
    return ArcValue

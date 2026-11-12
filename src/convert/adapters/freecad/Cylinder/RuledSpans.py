from math import isfinite as IsFinite

from convert.adapters.freecad.BrepGraph import ModelGraph
from convert.adapters.freecad.Cylinder.CylinderArc import ReadCylinderArc
from convert.adapters.freecad.Cylinder.CylinderFrame import KAxisTolerance
from convert.adapters.freecad.Cylinder.CylinderQuad import IsCylinderQuad
from convert.adapters.freecad.Cylinder.CylinderRail import ReadCylRail
from convert.adapters.freecad.Cylinder.CylinderSpan import CylinderSpan
from interchange.brep.curves.BrepCurves import CircleCurve, LineCurve
from interchange.brep.surfaces.BrepSurfaces import ConeSurface, CylinderSurface
from interchange.brep.topology.BrepTopology import BrepEdge
from interchange.geometry.models.VectorSpace import SpaceVector


# the trimmed arc radii set the angular tolerance even when the carrier starts at an apex
def IsRuledSpans(
    Graph: ModelGraph,
    Surface: CylinderSurface | ConeSurface,
    AxisValue: SpaceVector,
    Edges: tuple[BrepEdge, ...],
    Directions: tuple[tuple[int, int], ...],
    Pairs: tuple[tuple[str, str], ...],
    Allowed: float,
) -> bool:
    ArcRadii = tuple(
        Curve.radius
        for EdgeValue in Edges
        if isinstance((Curve := Graph.curves[EdgeValue.curve_id]), CircleCurve)
    )
    if len(ArcRadii) != 2 or any(
        not IsFinite(Radius) or Radius <= 0.0 for Radius in ArcRadii
    ):
        return False
    AngleTol = max(KAxisTolerance, Allowed / min(ArcRadii))
    Spans: list[CylinderSpan] = []
    for EdgeValue, Order, PairValue in zip(Edges, Directions, Pairs):
        if EdgeValue.degenerate:
            return False
        Curve = Graph.curves[EdgeValue.curve_id]
        Bounds = EdgeValue.start_parameter, EdgeValue.end_parameter
        Params = Bounds[Order[0]], Bounds[Order[1]]
        Vertices = (
            Graph.vertices[PairValue[0]].point,
            Graph.vertices[PairValue[1]].point,
        )
        if not all(map(IsFinite, Params)):
            return False
        if isinstance(Curve, CircleCurve):
            SpanValue = ReadCylinderArc(
                Curve, Surface, AxisValue, Params, Vertices, Allowed, AngleTol
            )
        elif isinstance(Curve, LineCurve):
            SpanValue = ReadCylRail(
                Curve, Surface, AxisValue, Params, Vertices, Allowed
            )
        else:
            return False
        if SpanValue is None:
            return False
        Spans.append(SpanValue)
    return IsCylinderQuad(tuple(Spans), Allowed, AngleTol)
